"""Command line entry point for independent Wiki libraries."""
import argparse
import json
import os
from pathlib import Path
import sys

from .agent import run_wiki_role
from .integrations.model import load_env_file
from .tools.core import ToolContext
from .tools.research_wiki import get_stats, init_wiki
from .tools.wiki import read_wiki, resolve_wiki_root, search_wiki


def main():
    parser = argparse.ArgumentParser(description="Curate and search a local research Wiki")
    parser.add_argument("--wiki-root", type=Path, help="Library directory (or WIKI_AGENT_WIKI_ROOT)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("stats")
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--view", choices=["titles", "abstracts"], default="titles")
    search.add_argument("--strategy", choices=["auto", "lexical", "hybrid"], default="auto")
    read = sub.add_parser("read")
    read.add_argument("wiki_path")
    ingest = sub.add_parser("ingest")
    ingest.add_argument("pdf", type=Path)
    ingest.add_argument("--project", type=Path, help="Workspace (default: PDF parent)")
    ingest.add_argument("--project-evidence", action="store_true")
    ingest.add_argument("--source", action="append", default=[])
    ingest.add_argument("--force", action="store_true")
    ingest.add_argument("--no-relations", action="store_true")
    ingest.add_argument("--model")
    ingest.add_argument("--max-iterations", type=int, default=300)
    args = parser.parse_args()
    load_env_file(Path.cwd() / ".env")
    if args.command == "ingest":
        pdf = args.pdf.expanduser().resolve()
        project = args.project.expanduser().resolve() if args.project else pdf.parent
        load_env_file(project / ".env")
        if not pdf.is_relative_to(project):
            parser.error("PDF must be inside --project; copy it into that workspace first")
    if args.wiki_root:
        os.environ["WIKI_AGENT_WIKI_ROOT"] = str(args.wiki_root.expanduser().resolve())
    elif not os.environ.get("WIKI_AGENT_WIKI_ROOT"):
        os.environ["WIKI_AGENT_WIKI_ROOT"] = str((Path.cwd() / "research-wiki").resolve())
    root = resolve_wiki_root()
    ctx = ToolContext(Path.cwd())
    try:
        if args.command == "init":
            init_wiki(str(root), separate_origins=True)
            result = {"wiki_root": str(root), "status": "initialized"}
        elif args.command == "stats":
            get_stats(str(root))
            return 0
        elif args.command in {"search", "read"}:
            response = (search_wiki(ctx, args.query, view=args.view, strategy=args.strategy)
                        if args.command == "search" else read_wiki(ctx, args.wiki_path))
            print(response.output)
            return int(response.is_error)
        else:
            result = run_wiki_role(project, "Curate the assigned PDF into the research Wiki.",
                paper_path=pdf.relative_to(project).as_posix(), wiki_root=root,
                project_evidence=args.project_evidence, source_paths=args.source,
                force=args.force, complete_relations=not args.no_relations,
                model=args.model, max_iterations=args.max_iterations,
                on_progress=lambda action, details: print(action, file=sys.stderr))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(isinstance(result, dict) and result.get("status") == "failed")
    except (OSError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
