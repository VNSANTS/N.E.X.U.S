"""Command line interface for the N.E.X.U.S. local learning core."""
import argparse
import json
from .engine import LearningEngine
from .ingestion import DocumentIngestor
from .providers.mock import MockProvider
from .runtime import TaskRuntime
from .crossref import CrossrefClient


def main():
    parser = argparse.ArgumentParser(description="N.E.X.U.S. local learning core")
    parser.add_argument("--db", default="nexus_learning.db", help="SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("stats")
    p = sub.add_parser("serve", help="Run the local authenticated web app and API")
    p.add_argument("--host", choices=["127.0.0.1"], default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p = sub.add_parser("worker", help="Run the local allowlisted worker")
    p.add_argument("--poll", type=float, default=1.0)
    p.add_argument("--once", action="store_true")
    p = sub.add_parser("memory-add")
    p.add_argument("kind", choices=["episodic", "semantic", "procedural"])
    p.add_argument("title")
    p.add_argument("content")
    p = sub.add_parser("memory-list")
    p.add_argument("--kind", choices=["episodic", "semantic", "procedural"])
    p.add_argument("--query", default="")
    p = sub.add_parser("memory-archive")
    p.add_argument("memory_id")
    p = sub.add_parser("source-add")
    p.add_argument("uri")
    p.add_argument("--title", default="")
    p = sub.add_parser("claim-add")
    p.add_argument("claim")
    p.add_argument("--source", action="append", default=[])
    p = sub.add_parser("claim-review")
    p.add_argument("claim_id")
    p.add_argument("state", choices=["proposed", "under_review", "validated", "disputed", "stale", "rejected"])
    p.add_argument("rationale")
    p.add_argument("--confidence", type=float)
    p = sub.add_parser("claim-list")
    p.add_argument("--state", choices=["proposed", "under_review", "validated", "disputed", "stale", "rejected"])
    p = sub.add_parser("task-add")
    p.add_argument("title")
    for field in ("relevance", "uncertainty", "impact", "novelty", "cost", "sensitivity"):
        p.add_argument("--" + field, type=float, default=0)
    sub.add_parser("task-list")
    sub.add_parser("consolidate")
    p = sub.add_parser("runtime-once", help="Run one offline test conversation")
    p.add_argument("message")
    p = sub.add_parser("ingest-file")
    p.add_argument("path")
    p = sub.add_parser("document-search")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)
    p = sub.add_parser("research-search", help="Search scholarly metadata through Crossref")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--mailto", default=None, help="Optional contact email for Crossref polite pool")
    args = parser.parse_args()
    if args.command == "serve":
        from .serve import serve
        argv = ["--host", args.host, "--port", str(args.port)]
        argv.extend(["--db", args.db])
        serve(argv)
        return
    engine = LearningEngine(args.db)
    ingestor = DocumentIngestor(engine) if args.command in {"ingest-file", "document-search"} else None

    if args.command == "init":
        result = {"initialized": True, "database": args.db}
    elif args.command == "stats":
        result = engine.stats()
    elif args.command == "worker":
        from .worker import LocalWorker, TaskQueue
        from .learning_cycles import LearningCycleService
        from .envfile import load_local_env
        import os
        load_local_env()
        queue = TaskQueue(engine)
        from .discovery import build_research_service
        from .providers.adapters import provider_from_env
        from .provider_budget import BudgetedProvider, ProviderBudget
        tavily_enabled = os.environ.get("NEXUS_TAVILY_ENABLED", "false").lower() == "true"
        selected_provider = provider_from_env()
        if getattr(selected_provider, "provider_name", "") in {"gemini", "groq", "openrouter"}:
            selected_provider = BudgetedProvider(selected_provider, ProviderBudget(engine))
        cycles = LearningCycleService(
            engine, queue,
            research_enabled=os.environ.get("NEXUS_RESEARCH_ENABLED", "false").strip().lower() == "true",
            research_service=build_research_service(engine, tavily_enabled=tavily_enabled),
            provider=selected_provider)
        worker = LocalWorker(queue, cycles=cycles)
        if args.once:
            result = {"processed": worker.run_once()}
        else:
            try:
                worker.run_forever(poll_seconds=max(.1, min(args.poll, 60)))
            except KeyboardInterrupt:
                worker.stop()
            return
    elif args.command == "memory-add":
        result = {"id": engine.add_memory(args.kind, args.title, args.content)}
    elif args.command == "memory-list":
        result = engine.search_memories(args.query, memory_type=args.kind)
    elif args.command == "memory-archive":
        result = {"archived": engine.archive_memory(args.memory_id)}
    elif args.command == "source-add":
        result = {"id": engine.add_source(args.uri, title=args.title)}
    elif args.command == "claim-add":
        result = {"id": engine.propose_claim(args.claim, args.source)}
    elif args.command == "claim-review":
        engine.review_claim(args.claim_id, args.state, args.rationale, args.confidence)
        result = {"updated": args.claim_id, "state": args.state}
    elif args.command == "claim-list":
        result = engine.list_claims(args.state)
    elif args.command == "task-add":
        fields = ("relevance", "uncertainty", "impact", "novelty", "cost", "sensitivity")
        result = {"id": engine.add_task(args.title, **{k: getattr(args, k) for k in fields})}
    elif args.command == "task-list":
        result = engine.prioritized_tasks()
    elif args.command == "ingest-file":
        result = ingestor.ingest_file(args.path)
    elif args.command == "document-search":
        result = ingestor.search(args.query, args.limit)
    elif args.command == "research-search":
        result = CrossrefClient(mailto=args.mailto).search(args.query, args.limit)
    elif args.command == "runtime-once":
        runtime = TaskRuntime(engine, MockProvider())
        result = runtime.run(runtime.submit(args.message))
    else:
        result = engine.consolidation_report()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
