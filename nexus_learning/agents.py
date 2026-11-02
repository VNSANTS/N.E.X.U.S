"""Bounded, deterministic product-agent supervision (not Codex profiles)."""
from dataclasses import dataclass
import re
import unicodedata
from urllib.parse import urlsplit
from .engine import now, uid
from .model_router import ModelRouter


@dataclass(frozen=True)
class AgentSpec:
    id: str
    role: str
    max_steps: int = 1
    allowed_tools: tuple = ()


@dataclass(frozen=True)
class AgentResult:
    agent_id: str
    status: str
    summary: str
    context: tuple = ()


@dataclass(frozen=True)
class TaskEnvelope:
    id: str
    parent_id: str
    agent_id: str
    operation: str
    allowed_context: tuple
    max_steps: int = 1


class ProductSupervisor:
    """Coordinates bounded specialists sequentially; model output cannot delegate."""
    AGENTS = (
        AgentSpec("orchestrator", "Coordinates one user request"),
        AgentSpec("researcher", "Discovers attributed source metadata", allowed_tools=("research.search",)),
        AgentSpec("analyst", "Compares evidence, uncertainty and contradictions"),
        AgentSpec("architect", "Plans bounded task stages and dependencies"),
        AgentSpec("developer", "Prepares technical improvement proposals"),
        AgentSpec("reviewer", "Checks provenance, risks and result structure"),
        AgentSpec("knowledge_manager", "Organizes sources, claims and review states",
                  allowed_tools=("knowledge.read",)),
    )

    def __init__(self, engine):
        self.engine = engine
        with engine.db() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS api_activity(
              id TEXT PRIMARY KEY,user_id TEXT NOT NULL,event TEXT NOT NULL,
              details TEXT NOT NULL,created_at TEXT NOT NULL)""")

    def record(self, owner_id, event, details):
        import json
        with self.engine.db() as c:
            c.execute("INSERT INTO api_activity VALUES(?,?,?,?,?)",
                      (uid("act"), owner_id, event, json.dumps(details, sort_keys=True), now()))

    def roster(self):
        return [{"id": x.id, "role": x.role, "max_steps": x.max_steps,
                 "allowed_tools": list(x.allowed_tools)} for x in self.AGENTS]

    def prepare_request(self, owner_id, session_id, query, retriever):
        """Run bounded deterministic specialists; no hidden model calls or network access."""
        parent = uid("agt")
        self.record(owner_id, "agent.started", {"agent": "orchestrator", "task_id": parent,
                                                   "session_id": session_id})
        memory_task = TaskEnvelope(uid("sub"), parent, "knowledge_manager", "retrieve_context",
                                   ("query", "active_memories", "validated_claims"))
        self.record(owner_id, "agent.delegated", {"agent": memory_task.agent_id,
                                                     "task_id": memory_task.id,
                                                     "parent_id": parent,
                                                     "operation": memory_task.operation,
                                                     "max_steps": memory_task.max_steps})
        memory = retriever.retrieve(query)
        self.record(owner_id, "agent.completed", {"agent": "knowledge_manager", "task_id": memory_task.id,
                                                      "context_items": len(memory)})
        route = ("research_candidate" if ModelRouter().classify(query) == "RESEARCH"
                 else "conversation")
        planner_task = TaskEnvelope(uid("sub"), parent, "architect", "classify_request",
                                    ("user_request",))
        self.record(owner_id, "agent.delegated", {"agent": planner_task.agent_id,
                                                     "task_id": planner_task.id,
                                                     "parent_id": parent,
                                                     "operation": planner_task.operation,
                                                     "route": route})
        if route == "research_candidate":
            research_task = TaskEnvelope(uid("sub"), parent, "researcher", "search_with_approval",
                                         ("user_request", "public_web_sources"))
            self.record(owner_id, "agent.delegated", {"agent": research_task.agent_id,
                "task_id": research_task.id, "parent_id": parent,
                "operation": research_task.operation, "requires_owner_confirmation": True})
        else:
            research_task = None
        self.record(owner_id, "agent.completed", {"agent": "architect", "route": route,
                                                      "steps": 1})
        return {"task_id": parent, "route": route, "memory": memory,
                "research_task_id": research_task.id if research_task else None}

    def analyze_sources(self, owner_id, parent_id, sources):
        """Assess source diversity and metadata without asserting factual agreement."""
        task_id = uid("sub")
        self.record(owner_id, "agent.delegated", {"agent": "analyst", "task_id": task_id,
            "parent_id": parent_id, "operation": "assess_source_coverage",
            "source_count": len(sources)})
        hosts = set()
        dated = 0
        for source in sources:
            try:
                host = (urlsplit(source.get("url", "")).hostname or "").lower()
                if host:
                    hosts.add(host.removeprefix("www."))
            except (TypeError, ValueError):
                continue
            if source.get("publication_date"):
                dated += 1
        result = {"source_count": len(sources), "distinct_domains": len(hosts),
                  "dated_sources": dated,
                  "coverage_warning": "single-domain" if sources and len(hosts) < 2 else None}
        self.record(owner_id, "agent.completed", {"agent": "analyst", "task_id": task_id,
            **result})
        return result

    def review_response(self, owner_id, text, max_chars, sources=()):
        accepted = isinstance(text, str) and bool(text.strip()) and len(text) <= max_chars
        cited = []
        reason = "Response shape accepted"
        if accepted and sources:
            cited = [int(value) for value in re.findall(r"\[S(\d+)\]", text, flags=re.I)]
            accepted = bool(cited) and all(1 <= value <= len(sources) for value in cited)
            reason = "Source citations accepted" if accepted else "Research answer lacks valid source citations"
        result = AgentResult("reviewer", "completed" if accepted else "rejected",
                             reason if accepted else (reason if sources else "Response failed bounded validation"),
                             tuple(sorted(set(cited))))
        self.record(owner_id, "agent.reviewed", {"agent": result.agent_id, "status": result.status,
                                                   "citation_count": len(result.context),
                                                   "source_count": len(sources)})
        return result
