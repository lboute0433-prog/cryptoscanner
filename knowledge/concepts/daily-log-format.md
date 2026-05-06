---
title: "Daily Log Format"
aliases: [conversation-log, daily-capture, session-log]
tags: [format, logging, conventions]
sources:
  - "daily/2026-04-23.md"
created: 2026-04-23
updated: 2026-04-23
---

# Daily Log Format

The standardized format for capturing AI coding session content in `daily/YYYY-MM-DD.md` files. Logs are immutable source material — append-only, never edited after the fact — and serve as the raw input for knowledge base compilation.

## Key Points

- Files are named `YYYY-MM-DD.md` (ISO 8601 date) for easy chronological access and automatic date-based deduplication
- One file per day; multiple sessions within a day are separated by `### Session (HH:MM) - Brief Title` headers
- Each session captures: Context, Key Exchanges, Decisions Made, Lessons Learned, and Action Items
- `flush.py` generates log entries automatically from JSONL conversation transcripts; manual editing is for corrections only
- Logs are never modified after `flush.py` writes them — treat them as append-only source records

## Details

The format is designed to be produced automatically by `flush.py` (via the Claude Agent SDK) and consumed automatically by `compile.py`. The five sections map directly to compilation targets: Key Exchanges and Lessons Learned become concept article content; Decisions Made become the basis for connection articles; Action Items are left in the log for human follow-up but not compiled into the knowledge base.

JSONL transcript parsing follows a specific pattern: each line is a JSON object with a `message` key containing `role` (`"user"` or `"assistant"`) and `content` (a string or list of `{"type": "text", "text": "..."}` blocks). `flush.py` handles both content shapes when extracting conversation text.

The daily log is also the compilation trigger: `flush.py` checks its SHA-256 hash against `state.json` after each session to determine whether end-of-day auto-compilation is needed.

## Related Concepts

- [[concepts/memory-compiler-architecture]] — The compiler reads daily logs as its source input
- [[concepts/hook-system]] — Hooks produce daily log entries via `flush.py`
- [[concepts/knowledge-base-structure]] — Compiled output from daily logs lives here

## Sources

- [[daily/2026-04-23.md]] — First daily log entry; format established during initialization session
