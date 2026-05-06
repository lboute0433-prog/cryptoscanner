---
title: "Memory Compiler Architecture"
aliases: [knowledge-compiler, llm-kb-compiler]
tags: [architecture, knowledge-management, automation]
sources:
  - "daily/2026-04-23.md"
  - "daily/test-setup.md"
created: 2026-04-23
updated: 2026-04-24
---

# Memory Compiler Architecture

An automated pipeline that converts raw AI conversation logs into a structured, queryable knowledge base. The system treats daily conversation logs as source code and uses an LLM as a compiler to extract, organize, and cross-reference knowledge without manual curation.

## Key Points

- Daily conversation logs (`daily/`) are immutable source material — append-only, never edited after creation
- The LLM acts as the compiler: it reads logs, decides what's worth preserving, and writes structured articles
- The compiled knowledge base (`knowledge/`) is entirely LLM-owned; humans read it but rarely edit directly
- Compilation is incremental: SHA-256 hashes in `state.json` track which logs have already been processed
- End-of-day auto-compilation triggers when `flush.py` detects it's past 6 PM and the daily log has changed
- Runtime state files (`state.json`, `last-flush.json`) and lint reports are excluded from git to prevent merge conflicts across machines

## Details

The architecture follows the "compiler analogy": `daily/` is source code, the LLM is the compiler, and `knowledge/` is the executable. This separation of concerns means raw context (messy, verbose, conversational) stays in the daily logs while structured knowledge (factual, concise, cross-linked) lives in the compiled articles.

Compilation uses the Claude Agent SDK's async streaming `query()` with `permission_mode="acceptEdits"`, allowing the LLM to autonomously read daily logs and write knowledge files without human approval of each file operation. The system tracks cost per compilation ($0.45–0.65 per log) and cumulative totals in `state.json`.

The auto-compile mechanism eliminates the need for cron jobs: `flush.py` (spawned as a detached background process by session hooks) checks the time after each session ends and triggers `compile.py` if conditions are met.

## Related Concepts

- [[concepts/hook-system]] — Hooks feed conversation data into the daily log, which triggers compilation
- [[concepts/knowledge-base-structure]] — The compiled output lives in this three-pillar structure
- [[concepts/daily-log-format]] — The source format that the compiler reads

## Sources

- [[daily/2026-04-23.md]] — System initialized; architecture overview extracted during setup session
- [[daily/test-setup.md]] — Pipeline validé end-to-end : compile.py a généré 5 articles au premier lancement, confirmant le fonctionnement de l'architecture
