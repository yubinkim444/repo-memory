# repo-memory

> **Shared, git-tracked working memory for AI agents that share a codebase.**
> What one Claude / Cursor / Cline learns about your repo, the next one
> picks up automatically. No database. No SaaS. Just files in your repo.

[![PyPI](https://img.shields.io/pypi/v/repo-memory)](https://pypi.org/project/repo-memory/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![MCP](https://img.shields.io/badge/MCP-server-7c3aed)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green)]()

---

## The problem

Every AI session that touches your repo starts from zero. It re-greps the
same files. It re-discovers the same conventions. It re-asks the same
questions you already answered three sessions ago. Multi-user / multi-tool
makes it worse: your teammate's Cursor and your Claude Code learn the same
codebase independently.

There is `CLAUDE.md` / `.cursorrules` for **rules** the human writes. But
there is nothing for **facts** an agent verified — "the auth middleware
lives at `src/auth/middleware.py:42`", "PR #387 chose httpx over requests
because of HTTP/2", "don't run migrations during peak hours".

`repo-memory` is that nothing. A `.ai-memory/` directory you commit to
your repo. Every AI tool reads from it, writes to it. Git is the database.

---

## Layout

```
your-repo/
├── .ai-memory/
│   ├── README.md           # explains the convention
│   ├── facts.jsonl         # append-only structured facts with evidence
│   ├── decisions/          # one markdown per non-trivial decision
│   │   └── 2026-05-19-pick-httpx.md
│   └── gotchas.md          # one-line "watch out for X" notes
├── src/
└── README.md
```

Pure files. Sync over git. No daemon, no DB, no auth. Works offline.

---

## Install

```bash
pip install repo-memory
# or
uvx repo-memory --help
```

Python ≥3.10. Depends only on the official `mcp` SDK (for the MCP server).

---

## Quick start

```bash
cd your-repo
repo-memory init                              # creates .ai-memory/
repo-memory add-fact "Auth middleware lives in src/auth/middleware.py" \
                     --file src/auth/middleware.py --lines 42-180 --tool grep
repo-memory add-decision "Use httpx not requests" \
                         --body "HTTP/2 + async support; we already use anyio."
repo-memory add-gotcha "Don't run migrations during 9-11am UTC peak"

repo-memory show                              # render everything as Markdown
repo-memory list-facts --tag auth
```

Then commit `.ai-memory/` like any other file:

```bash
git add .ai-memory/
git commit -m "memory: record auth middleware location + httpx decision"
git push
```

Anyone else (human or AI) who pulls the repo now sees those facts/decisions
immediately.

---

## LLM & AI Agent Readable Specification

> **For agents discovering this repo through search or MCP indexing.**

### Identity
- **name**: `repo-memory`
- **purpose**: read/write a structured, git-tracked memory store about the
  current codebase so multiple AI agents (and humans) don't re-learn it.
- **transport**: CLI (`repo-memory`) and MCP stdio (`repo-memory-mcp`).
- **storage**: plain files under `.ai-memory/` in the repo. Sync = git.

### When to call which tool

| Tool | When |
|------|------|
| `get_repo_memory` | At the **start** of any task on this repo. |
| `add_fact` | After you verify a non-obvious fact (location, behavior, convention). Include `evidence` so the next agent can re-verify cheaply. |
| `add_decision` | After a non-trivial choice (architecture, library, trade-off). Body should explain *why*, not just *what*. |
| `add_gotcha` | After a surprise that wasted your time. |
| `list_facts` | When you want only facts in a specific area (`tag`, `source_file`). |

### Recommended agent workflow

```
1. agent.call("get_repo_memory")            -> absorb prior context
2. ...do task, run tools, verify things...
3. agent.call("add_fact", claim, evidence)  -> for each new fact
4. agent.call("add_decision", title, body)  -> if a choice was made
5. session ends, human commits .ai-memory/   -> shared via git
```

### MCP server install

Add to your client config (Claude Desktop / Cursor / Cline):

```json
{
  "mcpServers": {
    "repo-memory": {
      "command": "uvx",
      "args": ["repo-memory-mcp", "--repo", "/abs/path/to/the/repo"]
    }
  }
}
```

Or set `REPO_MEMORY_ROOT` env var instead of `--repo`.

Exposes 5 tools: `get_repo_memory`, `add_fact`, `list_facts`,
`add_decision`, `add_gotcha`.

---

## Why git, not a database

- **Zero infra.** No service to host, no account to create, no API key
  to rotate.
- **Already authoritative.** Git history is the single source of truth.
  `git blame` tells you which agent added which fact and when.
- **Works offline.** Plane, train, conference WiFi — all fine.
- **PR review.** Suspicious or wrong facts get filtered through normal
  code review.
- **Per-repo scope.** A fact about repo A doesn't leak into repo B; the
  store is local to the repo.

---

## Schema (for tooling authors)

`facts.jsonl` — one JSON object per line:

```json
{
  "id": "abc123def456",
  "ts": "2026-05-19T18:00:00Z",
  "claim": "Auth middleware lives in src/auth/middleware.py",
  "evidence": {
    "file": "src/auth/middleware.py",
    "lines": "42-180",
    "tool": "grep",
    "command": "rg 'def authenticate' src/",
    "verified_at": "2026-05-19T18:00:00Z"
  },
  "tags": ["auth"],
  "added_by": "claude-opus-4.7"
}
```

Append-only. Stale entries stay. Readers consult `verified_at` and
re-verify if they want.

---

## CLI reference

| Command | Effect |
|---------|--------|
| `repo-memory init` | Create `.ai-memory/` skeleton. |
| `repo-memory show [--limit N]` | Print everything as one Markdown doc. |
| `repo-memory add-fact "<claim>" [--file F --lines L --tool T --command C --tag T --by AGENT]` | Append a fact. |
| `repo-memory list-facts [--tag T] [--source-file F] [--since ISO] [--limit N] [--json]` | List/filter facts. |
| `repo-memory add-decision "<title>" [--body MD]` | Write a decision file. |
| `repo-memory list-decisions` | List decision file paths. |
| `repo-memory add-gotcha "<note>"` | Append a one-line gotcha. |

All commands take `--root PATH` if your CWD isn't the repo root.

---

## License

MIT © yubinkim444
