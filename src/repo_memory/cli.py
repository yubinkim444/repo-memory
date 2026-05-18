"""repo-memory CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import store


def _parse_lines(spec: str | None) -> str | None:
    if not spec:
        return None
    return spec.strip()


def _add_root_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument("--root", type=Path, default=Path("."),
                   help="Repository root (default: current directory).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="repo-memory",
        description="Shared, git-tracked memory for AI agents on this repo.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Bootstrap .ai-memory/ in this repo.")
    _add_root_arg(p_init)
    p_init.add_argument("--no-claude-md", action="store_true",
                        help="Skip auto-adding the repo-memory section to CLAUDE.md / AGENTS.md.")

    p_show = sub.add_parser("show", help="Render the entire memory as Markdown.")
    _add_root_arg(p_show)
    p_show.add_argument("--limit", type=int, default=50, help="Max facts to render (default 50).")

    p_add_fact = sub.add_parser("add-fact", help="Append a structured fact.")
    _add_root_arg(p_add_fact)
    p_add_fact.add_argument("claim", help="The factual claim itself.")
    p_add_fact.add_argument("--file", help="Source file the fact is about.")
    p_add_fact.add_argument("--lines", help="Lines like '42' or '42-50'.")
    p_add_fact.add_argument("--tool", help="Tool that verified it (grep, read, bash, etc.).")
    p_add_fact.add_argument("--command", help="Exact command, if reproducible.")
    p_add_fact.add_argument("--tag", action="append", default=[], help="Tag (can pass multiple).")
    p_add_fact.add_argument("--by", help="Agent identifier (optional).")

    p_list_facts = sub.add_parser("list-facts", help="List facts, with optional filters.")
    _add_root_arg(p_list_facts)
    p_list_facts.add_argument("--tag")
    p_list_facts.add_argument("--source-file")
    p_list_facts.add_argument("--since", help="ISO timestamp (UTC).")
    p_list_facts.add_argument("--limit", type=int)
    p_list_facts.add_argument("--json", action="store_true", help="Emit JSON instead of table.")

    p_add_dec = sub.add_parser("add-decision", help="Add a decision document.")
    _add_root_arg(p_add_dec)
    p_add_dec.add_argument("title")
    p_add_dec.add_argument("--body", default="", help="Decision body (Markdown).")

    p_list_dec = sub.add_parser("list-decisions", help="List decision files.")
    _add_root_arg(p_list_dec)

    p_gotcha = sub.add_parser("add-gotcha", help="Append a one-line gotcha note.")
    _add_root_arg(p_gotcha)
    p_gotcha.add_argument("note")

    args = parser.parse_args(argv)
    root = args.root.resolve()

    if args.cmd == "init":
        path = store.init(root, update_claude_md=not args.no_claude_md)
        print(f"✓ initialised {path}")
        if not args.no_claude_md:
            cmd_path = root / "CLAUDE.md"
            agents_path = root / "AGENTS.md"
            updated = agents_path if agents_path.exists() and store.SECTION_BEGIN in agents_path.read_text(encoding="utf-8") else cmd_path
            print(f"  + ensured discoverability section in {updated.relative_to(root) if updated.exists() else updated.name}")
        return 0

    if args.cmd == "show":
        print(store.render(root, fact_limit=args.limit))
        return 0

    if args.cmd == "add-fact":
        evidence: dict = {}
        if args.file:
            evidence["file"] = args.file
        if args.lines:
            evidence["lines"] = _parse_lines(args.lines)
        if args.tool:
            evidence["tool"] = args.tool
        if args.command:
            evidence["command"] = args.command
        if evidence:
            evidence["verified_at"] = store._now()
        f = store.add_fact(root, args.claim, evidence=evidence, tags=args.tag, added_by=args.by)
        print(f"✓ added fact {f.id}: {f.claim}")
        return 0

    if args.cmd == "list-facts":
        facts = store.list_facts(
            root, tag=args.tag, source_file=args.source_file,
            since=args.since, limit=args.limit,
        )
        if args.json:
            print(json.dumps([f.__dict__ for f in facts], indent=2, ensure_ascii=False))
        else:
            for f in facts:
                ev = f.evidence or {}
                where = f" [{ev.get('file')}{':' + str(ev.get('lines')) if ev.get('lines') else ''}]" if ev.get('file') else ""
                tags = " " + " ".join(f"#{t}" for t in f.tags) if f.tags else ""
                print(f"{f.id}  {f.ts}  {f.claim}{where}{tags}")
        return 0

    if args.cmd == "add-decision":
        path = store.add_decision(root, args.title, args.body)
        print(f"✓ wrote decision: {path.relative_to(root)}")
        return 0

    if args.cmd == "list-decisions":
        for p in store.list_decisions(root):
            print(p.relative_to(root))
        return 0

    if args.cmd == "add-gotcha":
        store.add_gotcha(root, args.note)
        print("✓ appended gotcha")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
