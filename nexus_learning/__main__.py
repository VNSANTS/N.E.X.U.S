"""Command line entry point: python -m nexus_learning."""
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

    p = sub.add_parser("source-add")
    p.add_argument("uri")
    p.add_argument("--title", default="")

    p = sub.add_parser("claim-add")
    p.add_argument("claim")
    p.add_argument("--source", action="append", default=[])

    p = sub.add_parser("task-add")
    p.add_argument("title")
    p.add_argument("--relevance", type=float, default=0)
    p.add_argument("--uncertainty", type=float, default=0)
    p.add_argument("--impact", type=float, default=0)
    p.add_argument("--novelty", type=float, default=0)
    p.add_argument("--cost", type=float, default=0)
    p.add_argument("--sensitivity", type=float, default=0)

    sub.add_parser("task-list")
    args = parser.parse_args()
    engine = LearningEngine(args.db)

    if args.command == "init":
        result = {"initialized": True, "database": args.db}
    elif args.command == "stats":
        result = engine.stats()
    elif args.command == "memory-add":
        result = {"id": engine.add_memory(args.kind, args.title, args.content)}
    elif args.command == "memory-list":
        result = engine.search_memories(memory_type=args.kind)
    elif args.command == "source-add":
        result = {"id": engine.add_source(args.uri, title=args.title)}
    elif args.command == "claim-add":
        result = {"id": engine.propose_claim(args.claim, args.source)}
    elif args.command == "task-add":
        values = {key: getattr(args, key) for key in
                  ("relevance", "uncertainty", "impact", "novelty", "cost", "sensitivity")}
        result = {"id": engine.add_task(args.title, **values)}
    else:
        result = engine.prioritized_tasks()

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
