# Append-only facts, no edit or delete API

_Decided: 2026-05-18T19:55:15Z_

Considered allowing fact deletion via id. Rejected: stale entries are still useful (with verified_at timestamp the reader can re-verify or skip). Edits/deletes would require sync conflict resolution. Keep the model boring: append-only, like JSONL itself.
