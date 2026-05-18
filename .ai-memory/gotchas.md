# Gotchas

_Append short notes about non-obvious traps._

- _2026-05-18T19:55:15Z_ — PyPI new-account limit: ~6 new projects per 24h rolling window. Hit it on 2026-05-19 trying to publish promptlocker as 5th new project — 429 'Too many new projects created'. Plan publishes in batches.

- _2026-05-18T19:55:15Z_ — Smithery CLI 'mcp publish' only accepts HTTPS URLs or .mcpb bundles — NOT GitHub repo URLs. For stdio + PyPI MCPs, must use Web UI deploy flow that reads smithery.yaml.

- _2026-05-18T19:55:15Z_ — awesome-mcp-servers (punkpeye) has a glama-check bot gate — PRs without Glama quality score get rejected. Submit to Glama FIRST, wait for score, then open the awesome PR with the score badge included.
