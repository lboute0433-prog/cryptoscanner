---
title: "Connection: Hook System and Compilation Pipeline"
connects:
  - "concepts/hook-system"
  - "concepts/memory-compiler-architecture"
  - "concepts/daily-log-format"
sources:
  - "daily/2026-04-23.md"
created: 2026-04-23
updated: 2026-04-23
---

# Connection: Hook System and Compilation Pipeline

## The Connection

The hook system and the compilation pipeline form a continuous, automated loop: hooks capture conversation data, `flush.py` converts it to daily log entries, and `compile.py` transforms those logs into knowledge articles — all without explicit user action.

## Key Insight

The hooks do not call `compile.py` directly. Instead, they spawn `flush.py`, which acts as an intelligent intermediary: it extracts conversation content, decides what's worth saving, appends to the daily log, and *then* — only once per day, only after 6 PM, only if the log has changed — triggers compilation. This staged design means compilation is batched (once daily, not once per session), keeping API costs predictable even for high-frequency users.

The `SessionStart` hook creates the reverse flow: it reads the already-compiled `knowledge/index.md` and injects it into the new session's context. This closes the loop — the output of yesterday's compilation becomes the input context for today's conversations.

## Evidence

- `session-end.py` and `pre-compact.py` both spawn `flush.py` as a detached background process; `flush.py` contains the `COMPILE_AFTER_HOUR = 18` check that gates compilation
- `session-start.py` reads `knowledge/index.md` and outputs it as `additionalContext` in the SessionStart JSON payload
- The deduplication check in `flush.py` (`last-flush.json`, 60-second window) prevents double-writes when both `PreCompact` and `SessionEnd` fire in quick succession during a long session

## Related Concepts

- [[concepts/hook-system]] — Defines the three hook types and their individual roles
- [[concepts/memory-compiler-architecture]] — The compilation side of this pipeline
- [[concepts/daily-log-format]] — The intermediary format connecting hooks to compilation
- [[concepts/knowledge-base-structure]] — The final output that loops back into `SessionStart`
