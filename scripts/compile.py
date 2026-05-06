"""
Compile daily conversation logs into structured knowledge articles.

This is the "LLM compiler" - it reads daily logs (source code) and produces
organized knowledge articles (the executable).

Usage:
    uv run python compile.py                    # compile new/changed logs only
    uv run python compile.py --all              # force recompile everything
    uv run python compile.py --file daily/2026-04-01.md  # compile a specific log
    uv run python compile.py --dry-run          # show what would be compiled
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from config import AGENTS_FILE, CONCEPTS_DIR, CONNECTIONS_DIR, DAILY_DIR, KNOWLEDGE_DIR, REFERENCES_DIR, now_iso
from utils import (
    file_hash,
    list_raw_files,
    list_wiki_articles,
    load_state,
    read_wiki_index,
    save_state,
)

# ── Paths for the LLM to use ──────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent


async def compile_daily_log(log_path: Path, state: dict) -> float:
    """Compile a single daily log into knowledge articles.

    Returns the API cost of the compilation.
    """
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        query,
    )

    log_content = log_path.read_text(encoding="utf-8")
    schema = AGENTS_FILE.read_text(encoding="utf-8")
    wiki_index = read_wiki_index()

    # Read references if they exist
    references_context = ""
    if REFERENCES_DIR.exists():
        ref_parts = []
        for ref_file in sorted(REFERENCES_DIR.rglob("*.md")):
            if ref_file.name != "sources.md":  # Skip the index file
                try:
                    content = ref_file.read_text(encoding="utf-8")
                    rel_path = ref_file.relative_to(REFERENCES_DIR)
                    ref_parts.append(f"### {rel_path}\n{content}")
                except Exception:
                    pass
        if ref_parts:
            references_context = "## Personal References\n\n" + "\n\n".join(ref_parts)

    # Read existing articles for context
    existing_articles_context = ""
    existing = {}
    for article_path in list_wiki_articles():
        rel = article_path.relative_to(KNOWLEDGE_DIR)
        existing[str(rel)] = article_path.read_text(encoding="utf-8")

    if existing:
        parts = []
        for rel_path, content in existing.items():
            parts.append(f"### {rel_path}\n```markdown\n{content}\n```")
        existing_articles_context = "\n\n".join(parts)

    timestamp = now_iso()

    prompt = f"""Tu es un compilateur de connaissances. Ton rôle est de lire un journal de conversation quotidien
et d'extraire les connaissances dans des articles wiki structurés.

**Langue: Tous les articles DOIVENT être écrits en FRANÇAIS.** Pas de compromis.

## Schéma (AGENTS.md)

{schema}

## Index Wiki Actuel

{wiki_index}

## Articles Wiki Existants

{existing_articles_context if existing_articles_context else "(Aucun article existant pour l'instant)"}

{references_context}

## Journal Quotidien à Compiler

**Fichier:** {log_path.name}

{log_content}

## Ta Tâche

Lis le journal quotidien ci-dessus et compile-le en articles wiki en suivant le schéma exactement.

Intègre également le contenu des Références Personnelles si elles sont pertinentes.

### Règles:

1. **Extrais les concepts clés** - Identifie 3-7 concepts distincts dignes de leur propre article
2. **Crée des articles de concepts** dans `knowledge/concepts/` - Un fichier .md par concept
   - Utilise le format exact de AGENTS.md (frontmatter YAML + sections)
   - Inclus `sources:` dans le frontmatter pointant vers le fichier quotidien/références
   - Utilise `[[concepts/slug]]` wikilinks pour lier les concepts connexes
   - Écris en style encyclopédique - neutre, complet
   - **ÉCRIS EN FRANÇAIS**
3. **Crée des articles de connexion** dans `knowledge/connections/` si ce journal révèle des
   relations non-évidentes entre 2+ concepts existants
4. **Met à jour les articles existants** si ce journal ajoute de nouvelles infos à des concepts déjà dans le wiki
   - Lis l'article existant, ajoute la nouvelle info, ajoute la source au frontmatter
5. **Met à jour knowledge/index.md** - Ajoute les nouvelles entrées au tableau
   - Chaque entrée: `| [[path/slug]] | Résumé d'une ligne | source-file | {timestamp[:10]} |`
6. **Ajoute à knowledge/log.md** - Ajoute une entrée horodatée:
   ```
   ## [{timestamp}] compile | {log_path.name}
   - Source: daily/{log_path.name}
   - Articles créés: [[concepts/x]], [[concepts/y]]
   - Articles mis à jour: [[concepts/z]] (si applicable)
   ```

### File paths:
- Write concept articles to: {CONCEPTS_DIR}
- Write connection articles to: {CONNECTIONS_DIR}
- Update index at: {KNOWLEDGE_DIR / 'index.md'}
- Append log at: {KNOWLEDGE_DIR / 'log.md'}

### Quality standards:
- Every article must have complete YAML frontmatter
- Every article must link to at least 2 other articles via [[wikilinks]]
- Key Points section should have 3-5 bullet points
- Details section should have 2+ paragraphs
- Related Concepts section should have 2+ entries
- Sources section should cite the daily log with specific claims extracted
"""

    cost = 0.0

    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                cwd=str(ROOT_DIR),
                system_prompt={"type": "preset", "preset": "claude_code"},
                allowed_tools=["Read", "Write", "Edit", "Glob", "Grep"],
                permission_mode="acceptEdits",
                max_turns=30,
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        pass  # compilation output - LLM writes files directly
            elif isinstance(message, ResultMessage):
                cost = message.total_cost_usd or 0.0
                print(f"  Cost: ${cost:.4f}")
    except Exception as e:
        print(f"  Error: {e}")
        return 0.0

    # Update state
    rel_path = log_path.name
    state.setdefault("ingested", {})[rel_path] = {
        "hash": file_hash(log_path),
        "compiled_at": now_iso(),
        "cost_usd": cost,
    }
    state["total_cost"] = state.get("total_cost", 0.0) + cost
    save_state(state)

    return cost


def main():
    parser = argparse.ArgumentParser(description="Compile daily logs into knowledge articles")
    parser.add_argument("--all", action="store_true", help="Force recompile all logs")
    parser.add_argument("--file", type=str, help="Compile a specific daily log file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be compiled")
    args = parser.parse_args()

    state = load_state()

    # Determine which files to compile
    if args.file:
        target = Path(args.file)
        if not target.is_absolute():
            target = DAILY_DIR / target.name
        if not target.exists():
            # Try resolving relative to project root
            target = ROOT_DIR / args.file
        if not target.exists():
            print(f"Error: {args.file} not found")
            sys.exit(1)
        to_compile = [target]
    else:
        all_logs = list_raw_files()
        if args.all:
            to_compile = all_logs
        else:
            to_compile = []
            for log_path in all_logs:
                rel = log_path.name
                prev = state.get("ingested", {}).get(rel, {})
                if not prev or prev.get("hash") != file_hash(log_path):
                    to_compile.append(log_path)

    if not to_compile:
        print("Nothing to compile - all daily logs are up to date.")
        return

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Files to compile ({len(to_compile)}):")
    for f in to_compile:
        print(f"  - {f.name}")

    if args.dry_run:
        return

    # Compile each file sequentially
    total_cost = 0.0
    for i, log_path in enumerate(to_compile, 1):
        print(f"\n[{i}/{len(to_compile)}] Compiling {log_path.name}...")
        cost = asyncio.run(compile_daily_log(log_path, state))
        total_cost += cost
        print(f"  Done.")

    articles = list_wiki_articles()
    print(f"\nCompilation complete. Total cost: ${total_cost:.2f}")
    print(f"Knowledge base: {len(articles)} articles")


if __name__ == "__main__":
    main()
