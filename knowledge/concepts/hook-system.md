---
title: "Hook System"
aliases: [claude-hooks, session-hooks, automatic-capture]
tags: [hooks, automation, claude-code, capture]
sources:
  - "daily/2026-04-23.md"
  - "daily/test-setup.md"
created: 2026-04-23
updated: 2026-04-23
---

# Hook System

A three-layer automatic capture system integrated with Claude Code that intercepts conversation events (session start, session end, pre-compaction) and converts raw conversation transcripts into daily log entries — without requiring manual user action.

## Key Points

- Three hooks: `SessionStart` (injects knowledge into context), `SessionEnd` (extracts conversation to daily log), `PreCompact` (captures context before summarization discards it)
- Configured in `.claude/settings.json` using the `hooks` key; Claude Code executes these automatically
- `session-end.py` and `pre-compact.py` spawn `flush.py` as a fully detached background process to survive after Claude Code's hook process exits
- Recursion guard: hooks check `CLAUDE_INVOKED_BY` env var to prevent flush.py from re-triggering itself
- Both `PreCompact` and `SessionEnd` are needed because long sessions may trigger multiple auto-compactions before closing

## Details

`SessionStart` is a pure local I/O hook: it reads `knowledge/index.md` and the most recent daily log, then outputs a JSON payload with `additionalContext` that Claude Code injects into the session context. This means every conversation starts with the knowledge base index visible, enabling immediate retrieval without an explicit query. The hook runs in under 1 second with no API calls.

`SessionEnd` and `PreCompact` share the same architecture: read the JSONL transcript path from stdin, copy the raw transcript to a temp file, and spawn `flush.py` as a detached process. The detachment strategy differs by OS: Windows uses `CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS` flags; Mac/Linux uses `start_new_session=True`. This ensures `flush.py` continues running after the hook process exits.

Hook configuration uses empty `matcher: ""` to catch all events, with a `timeout` in seconds for each hook command. Commands use relative paths from the project root and are invoked via `uv run python hooks/<script>.py`.

## Related Concepts

- [[concepts/memory-compiler-architecture]] — Hooks are the intake layer of the compilation pipeline
- [[concepts/daily-log-format]] — Hooks produce entries in this format via `flush.py`
- [[concepts/knowledge-base-structure]] — `SessionStart` reads `knowledge/index.md` to inject context
- [[concepts/uv-dependency-management]] — Hook commands use `uv run` to ensure the correct virtual environment

## Sources

- [[daily/2026-04-23.md]] — Hook system configured during initialization; `.claude/settings.json` created with SessionStart, SessionEnd, PreCompact hooks
- [[daily/test-setup.md]] — End-to-end setup validated: hooks activated and pipeline confirmed functional
