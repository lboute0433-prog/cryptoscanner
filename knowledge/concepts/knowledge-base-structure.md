---
title: "Knowledge Base Structure"
aliases: [kb-structure, knowledge-pillars, wiki-structure]
tags: [architecture, knowledge-management, organization]
sources:
  - "daily/2026-04-23.md"
created: 2026-04-23
updated: 2026-04-23
---

# Knowledge Base Structure

A three-pillar directory layout (`concepts/`, `connections/`, `qa/`) backed by a master index and append-only build log. The structure is designed for index-guided retrieval by an LLM rather than vector similarity search, making it effective at personal knowledge base scale (50–500 articles) without RAG infrastructure.

## Key Points

- `knowledge/index.md` is the primary retrieval mechanism: the LLM reads it first, selects relevant articles, then reads those in full
- `concepts/` holds atomic knowledge articles — one file per distinct piece of knowledge
- `connections/` holds synthesis articles that reveal non-obvious relationships between 2+ concepts
- `qa/` stores filed query answers, creating a compounding loop where every question makes future queries smarter
- `knowledge/log.md` is append-only — a chronological record of every compile, query, and lint operation

## Details

The index-guided approach outperforms embedding-based RAG at personal KB scale because the LLM understands what a question is *really asking*, whereas cosine similarity finds words that are similar. The LLM reads the structured index (a markdown table with one-line summaries) and selects the 3–10 most relevant articles to read in full before synthesizing an answer.

Article format is standardized: YAML frontmatter (title, aliases, tags, sources, created, updated) followed by sections in a fixed order: core explanation, Key Points, Details, Related Concepts, Sources. All cross-references use Obsidian-style `[[wikilinks]]` with full relative paths from the `knowledge/` directory. This makes the knowledge base compatible with Obsidian for graph view and backlink navigation.

The structure scales to approximately 2,000 articles / 2M tokens before the index itself becomes too large for a context window. At that point, hybrid RAG (keyword + semantic) would be needed as a retrieval layer.

## Related Concepts

- [[concepts/memory-compiler-architecture]] — The LLM compiler writes articles into this structure
- [[concepts/hook-system]] — SessionStart injects `index.md` into every conversation
- [[concepts/daily-log-format]] — Source logs that feed articles in this structure

## Sources

- [[daily/2026-04-23.md]] — Structure verified during initialization; `concepts/`, `connections/`, `qa/` directories confirmed in place
