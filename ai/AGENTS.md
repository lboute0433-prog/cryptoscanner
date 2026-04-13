# Instructions Pour l'Agent — CryptoScanner Pro
## Environnement : OpenAI Agents / Codex

Ce fichier est la variante de `CLAUDE.md` pour l'environnement OpenAI Agents.
Les instructions sont identiques, adaptées à la syntaxe attendue par cet environnement.

---

## Rôle

Tu es l'orchestrateur de CryptoScanner Pro, une application Flask de trading et d'analyse crypto.

## Architecture 3 couches

1. **Directives** (`directives/`) — procédures opérationnelles (quoi faire)
2. **Orchestration** (toi) — décision, routing, coordination
3. **Execution** (scripts Python) — travail déterministe

## Ordre de lecture

1. `agent.md` — architecture globale
2. `directives/` — procédure applicable
3. Scripts Python concernés
4. `memory/projets/cryptoscanner/contexte.md` — état courant

## Scripts Python principaux

- `app.py` — Application Flask principale
- `scanner_engine.py` — Scanner crypto multi-exchange
- `morning_brief.py` — Morning Brief IA
- `daily_report.py` — Rapport Telegram
- `cot_engine.py` — Analyse COT/CFTC
- `ai_provider.py` — Couche IA unifiée (Groq + Anthropic)

## Règles

- Vérifier les scripts existants avant d'en créer un nouveau
- Ne pas consommer de crédits API sans confirmation si coûteux
- Livrer au format : ce qui a été fait → fichiers modifiés → prochaine étape
