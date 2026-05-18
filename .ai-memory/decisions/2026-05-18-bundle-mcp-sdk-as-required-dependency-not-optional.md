# Bundle mcp SDK as required dependency, not optional

_Decided: 2026-05-18T19:55:15Z_

Tested with [project.optional-dependencies] mcp = ['mcp>=1.2.0'] first, but the console-script entry point 'repo-memory-mcp' would fail at runtime without the optional install. Cleaner UX to make it required — adds ~3 sub-deps but install is a single 'pip install repo-memory'.
