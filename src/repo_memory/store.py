"""Core store — read/write the `.ai-memory/` directory layout.

Layout:
    .ai-memory/
    ├── README.md               # explains the convention to humans + AI
    ├── facts.jsonl             # append-only structured facts
    ├── decisions/              # one .md file per decision
    │   └── 2026-05-19-auth-flow.md
    └── gotchas.md              # "things to watch out for" cheat sheet
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

MEMORY_DIR = ".ai-memory"
FACTS_FILE = "facts.jsonl"
DECISIONS_DIR = "decisions"
GOTCHAS_FILE = "gotchas.md"
README_FILE = "README.md"

CLAUDE_MD_NAMES = ("CLAUDE.md", "AGENTS.md")  # update whichever exists; create CLAUDE.md by default
SECTION_BEGIN = "<!-- BEGIN: repo-memory -->"
SECTION_END = "<!-- END: repo-memory -->"
CLAUDE_MD_SECTION = f"""\
{SECTION_BEGIN}
## Shared AI Memory (`.ai-memory/`)

Before starting any non-trivial task in this repo, check:
- `.ai-memory/facts.jsonl` — verified facts about this codebase
- `.ai-memory/decisions/` — markdown decision records (why we did X)
- `.ai-memory/gotchas.md` — known traps and surprises

When you verify a non-obvious fact, make a non-trivial decision, or hit a
gotcha, record it via `repo-memory add-fact / add-decision / add-gotcha`
(or the matching MCP tool) so the next session/agent doesn't redo the work.

Tool: https://github.com/yubinkim444/repo-memory
{SECTION_END}
"""

README_TEMPLATE = """# .ai-memory/

> Shared, git-tracked working memory for AI agents (Claude Code, Cursor,
> Cline, anyone) that operate on this repository. Commit it. Pull others'
> contributions. Treat it as ground truth.

## Files

| File / Dir | What it holds |
|------------|---------------|
| `facts.jsonl`     | Append-only structured facts about this codebase, with evidence. |
| `decisions/*.md`  | One markdown per significant decision made while working here. |
| `gotchas.md`      | Quick "watch out for X" notes that don't fit elsewhere. |

## For AI agents reading this

1. **At the start of any task**, run `repo-memory show` (or open the files
   above) and absorb existing facts/decisions. Skip what you already
   re-verified independently.
2. **When you verify a non-obvious fact** (file location, behavior,
   convention, gotcha), add it via `repo-memory add-fact "..."` with
   evidence pointing at the file/lines/command that proved it.
3. **When you make a non-trivial decision** (architecture, choice between
   approaches, trade-off), append a brief note via
   `repo-memory add-decision "..."`.
4. **Never overwrite** anything; the store is append-only. Stale entries
   stay — readers should consult `verified_at` timestamps and re-verify
   if too old.

## CLI

```bash
repo-memory init           # bootstrap .ai-memory/ in this repo
repo-memory show           # print everything as Markdown
repo-memory add-fact "..." --file src/x.py --lines 42-50
repo-memory add-decision "Use httpx over requests"
repo-memory add-gotcha "Don't run migrations during peak hours"
repo-memory list-facts --tag auth
```

## MCP server

```bash
repo-memory-mcp            # speaks MCP over stdio; exposes read/write tools
```

Add to your Claude Desktop / Cursor / Cline config:

```json
{
  "mcpServers": {
    "repo-memory": {
      "command": "uvx",
      "args": ["repo-memory-mcp", "--repo", "/abs/path/to/this/repo"]
    }
  }
}
```
"""


@dataclass
class Fact:
    id: str
    ts: str
    claim: str
    evidence: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    added_by: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _memdir(root: Path) -> Path:
    return root / MEMORY_DIR


def is_initialized(root: Path) -> bool:
    return _memdir(root).is_dir()


def init(root: Path, *, update_claude_md: bool = True) -> Path:
    """Bootstrap `<root>/.ai-memory/` with the standard layout.

    If `update_claude_md` is True (default), also adds a discoverability
    section to the repo's CLAUDE.md (or AGENTS.md if it exists instead),
    creating CLAUDE.md if neither exists. Idempotent — re-running won't
    clobber or duplicate anything.
    """
    base = _memdir(root)
    base.mkdir(parents=True, exist_ok=True)
    (base / DECISIONS_DIR).mkdir(exist_ok=True)
    readme = base / README_FILE
    if not readme.exists():
        readme.write_text(README_TEMPLATE, encoding="utf-8")
    facts = base / FACTS_FILE
    if not facts.exists():
        facts.touch()
    gotchas = base / GOTCHAS_FILE
    if not gotchas.exists():
        gotchas.write_text("# Gotchas\n\n_Append short notes about non-obvious traps._\n", encoding="utf-8")

    if update_claude_md:
        ensure_claude_md_section(root)

    return base


def ensure_claude_md_section(root: Path) -> Path | None:
    """Append the repo-memory discoverability section to CLAUDE.md (or
    AGENTS.md if that exists instead). Idempotent. Returns the touched
    path, or None if the section was already present."""
    target: Path | None = None
    for name in CLAUDE_MD_NAMES:
        candidate = root / name
        if candidate.exists():
            target = candidate
            break
    if target is None:
        target = root / CLAUDE_MD_NAMES[0]  # create CLAUDE.md by default

    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    if SECTION_BEGIN in existing and SECTION_END in existing:
        return None
    prefix = existing.rstrip() + "\n\n" if existing.strip() else ""
    target.write_text(prefix + CLAUDE_MD_SECTION, encoding="utf-8")
    return target


def add_fact(root: Path, claim: str, evidence: dict | None = None,
             tags: list[str] | None = None, added_by: str | None = None) -> Fact:
    init(root)
    fact = Fact(
        id=uuid.uuid4().hex[:12],
        ts=_now(),
        claim=claim.strip(),
        evidence=evidence or {},
        tags=tags or [],
        added_by=added_by,
    )
    with (_memdir(root) / FACTS_FILE).open("a", encoding="utf-8") as f:
        f.write(json.dumps(fact.__dict__, ensure_ascii=False) + "\n")
    return fact


def list_facts(root: Path, *, tag: str | None = None, source_file: str | None = None,
               since: str | None = None, limit: int | None = None) -> list[Fact]:
    path = _memdir(root) / FACTS_FILE
    if not path.exists():
        return []
    out: list[Fact] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        f = Fact(**{k: data.get(k) for k in ("id", "ts", "claim", "evidence", "tags", "added_by")})
        f.evidence = f.evidence or {}
        f.tags = f.tags or []
        if tag and tag not in f.tags:
            continue
        if source_file and (f.evidence or {}).get("file") != source_file:
            continue
        if since and f.ts < since:
            continue
        out.append(f)
    if limit:
        out = out[-limit:]
    return out


def _slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "decision"


def add_decision(root: Path, title: str, body: str = "") -> Path:
    init(root)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    name = f"{date}-{_slug(title)}.md"
    path = _memdir(root) / DECISIONS_DIR / name
    # Avoid clobber on same day, same slug
    n = 1
    while path.exists():
        n += 1
        path = _memdir(root) / DECISIONS_DIR / f"{date}-{_slug(title)}-{n}.md"
    content = f"# {title.strip()}\n\n_Decided: {_now()}_\n\n{body.strip()}\n"
    path.write_text(content, encoding="utf-8")
    return path


def list_decisions(root: Path) -> list[Path]:
    d = _memdir(root) / DECISIONS_DIR
    if not d.exists():
        return []
    return sorted(d.glob("*.md"))


def add_gotcha(root: Path, note: str) -> None:
    init(root)
    path = _memdir(root) / GOTCHAS_FILE
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n- _{_now()}_ — {note.strip()}\n")


def render(root: Path, *, fact_limit: int | None = 50) -> str:
    """Render the whole .ai-memory/ as one markdown document for an LLM prompt."""
    if not is_initialized(root):
        return "_(no .ai-memory yet — run `repo-memory init`)_"

    parts: list[str] = []
    parts.append(f"# Memory snapshot for `{root.name}`\n")
    parts.append(f"_Rendered at {_now()}._\n")

    facts = list_facts(root, limit=fact_limit)
    parts.append(f"## Facts ({len(facts)})\n")
    if facts:
        for f in facts:
            ev = f.evidence or {}
            ev_str = ""
            if ev.get("file"):
                lines = ev.get("lines")
                ev_str = f" — `{ev['file']}`{':' + str(lines) if lines else ''}"
                if ev.get("verified_at"):
                    ev_str += f" (verified {ev['verified_at']})"
            tags = " ".join(f"#{t}" for t in f.tags)
            parts.append(f"- **{f.claim}**{ev_str}  {tags}".rstrip() + "  _\\<{}>_".format(f.id))
    else:
        parts.append("_(empty)_")

    parts.append("\n## Decisions\n")
    decs = list_decisions(root)
    if decs:
        for p in decs:
            parts.append(f"### {p.stem}\n")
            parts.append(p.read_text(encoding="utf-8").strip() + "\n")
    else:
        parts.append("_(none yet)_")

    parts.append("\n## Gotchas\n")
    gotchas_path = _memdir(root) / GOTCHAS_FILE
    if gotchas_path.exists():
        parts.append(gotchas_path.read_text(encoding="utf-8").strip())
    else:
        parts.append("_(none yet)_")

    return "\n".join(parts) + "\n"
