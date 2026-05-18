# .ai-memory/

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
