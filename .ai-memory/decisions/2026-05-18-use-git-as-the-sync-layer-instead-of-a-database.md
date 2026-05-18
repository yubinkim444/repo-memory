# Use git as the sync layer instead of a database

_Decided: 2026-05-18T19:55:15Z_

Considered SQLite-backed alternatives (longhand, alcove, etc.) but chose plain files committed to the repo. Reasoning: zero infra, no daemon, PR review filters wrong facts, git history is audit trail, per-repo scope is automatic, works offline. Trade-off: no real-time sync (need git pull). For 95% of use cases, the file approach is sufficient and dramatically simpler.
