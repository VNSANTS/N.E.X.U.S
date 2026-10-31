"""Command line interface for the N.E.X.U.S. local learning core."""
import argparse
import json
from .engine import LearningEngine


def main():
    parser = argparse.ArgumentParser(description="N.E.X.U.S. local learning core")
    parser.add_argument("--db", default="nexus_learning.db", help="SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("stats")
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
    args = parser.parse_args()
    engine = LearningEngine(args.db)

    if args.command == "init":
        result = {"initialized": True, "database": args.db}
    elif args.command == "stats":
        result = engine.stats()
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
    else:
        result = engine.consolidation_report()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
