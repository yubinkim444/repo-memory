"""MCP server — exposes repo-memory read/write as tools for any
MCP-compatible agent (Claude Desktop, Cursor, Cline, etc.)."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from . import store

_REPO_ROOT: Path = Path(os.getenv("REPO_MEMORY_ROOT", os.getcwd())).resolve()

mcp = FastMCP("repo-memory")


@mcp.tool()
def get_repo_memory(fact_limit: int = 50) -> str:
    """Return the entire `.ai-memory/` of the current repo as a Markdown document
    ready to drop into your LLM context. Call this **before** starting any task
    in this repo so you don't redo work other agents already verified.

    Args:
        fact_limit: cap on number of facts (default 50, most recent first).
    """
    return store.render(_REPO_ROOT, fact_limit=fact_limit)


@mcp.tool()
def add_fact(claim: str, file: str | None = None, lines: str | None = None,
             tool: str | None = None, command: str | None = None,
             tags: list[str] | None = None) -> str:
    """Record a structured fact you just verified about this codebase, so the
    next agent (or your next session) doesn't have to re-verify it.

    Args:
        claim: the factual statement (one sentence).
        file: source file path (relative to repo root) that proves the claim.
        lines: line range like '42' or '42-50'.
        tool: name of tool used to verify ('grep', 'read', 'bash', etc.).
        command: exact command if reproducible.
        tags: optional tags for later filtering.
    """
    evidence: dict = {}
    if file:    evidence["file"] = file
    if lines:   evidence["lines"] = lines
    if tool:    evidence["tool"] = tool
    if command: evidence["command"] = command
    if evidence:
        evidence["verified_at"] = store._now()
    f = store.add_fact(_REPO_ROOT, claim, evidence=evidence, tags=tags or [])
    return f"fact_id={f.id}; {len(store.list_facts(_REPO_ROOT))} total facts"


@mcp.tool()
def list_facts(tag: str | None = None, source_file: str | None = None,
               since: str | None = None, limit: int = 20) -> list[dict]:
    """List recorded facts, optionally filtered. Useful when you want only
    facts relevant to a specific area before reading them."""
    facts = store.list_facts(_REPO_ROOT, tag=tag, source_file=source_file,
                             since=since, limit=limit)
    return [f.__dict__ for f in facts]


@mcp.tool()
def add_decision(title: str, body: str = "") -> str:
    """Record a non-trivial decision made while working in this repo
    (architecture choice, trade-off, deprecation, etc.) as a markdown file
    under `.ai-memory/decisions/`.

    Args:
        title: one-line headline of the decision.
        body: full markdown explanation — context, options considered,
              reasoning, who/when.
    """
    path = store.add_decision(_REPO_ROOT, title, body)
    return f"wrote {path.relative_to(_REPO_ROOT)}"


@mcp.tool()
def add_gotcha(note: str) -> str:
    """Append a one-line 'watch out for X' note to `.ai-memory/gotchas.md`.
    Use for surprises that wasted your time and might trip the next agent."""
    store.add_gotcha(_REPO_ROOT, note)
    return "appended"


def main() -> None:
    global _REPO_ROOT
    parser = argparse.ArgumentParser(prog="repo-memory-mcp",
                                     description="MCP server for repo-memory.")
    parser.add_argument("--repo", type=Path, default=None,
                        help="Repo root (default: $REPO_MEMORY_ROOT or cwd).")
    args = parser.parse_args()
    if args.repo:
        _REPO_ROOT = args.repo.resolve()
    mcp.run()


if __name__ == "__main__":
    main()
