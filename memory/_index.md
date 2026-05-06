---
tags: [type/index]
---

# Index — Mémoire CryptoScanner Pro

## Framework ICA

- [[ICA]] — Framework complet (la bible)
- [[I]] — Pilier Instruction (qui + comment)
- [[C]] — Pilier Connaissance (ce que tu sais)
- [[A]] — Pilier Action (ce que tu fais)

## Projets

- [[cryptoscanner/contexte|CryptoScanner Pro]] — Application Flask trading/crypto
  - [[cryptoscanner/historique|Historique]]
  - Data : [[cryptoscanner/data/stack|Stack technique]] · [[cryptoscanner/data/roadmap|Roadmap]] · [[cryptoscanner/data/bugs|Bugs connus]] · [[cryptoscanner/data/sources|Sources de données]] · [[cryptoscanner/data/roles|Rôles et accès]]
  - Agents : [[debugger/notes|Debugger]] · [[feature/notes|Feature]] · [[scanner/notes|Scanner]] · [[analyse/notes|Analyse]] · [[morning-brief/notes|Morning Brief]] · [[rapport/notes|Rapport]]

## Notes personnelles

- [[notes/todo|Todo]] — Ce que tu veux faire lors de la prochaine session
- [[notes/idees|Idées]] — Idées futures et fonctionnalités à explorer
- [[notes/instructions|Instructions]] — Consignes spéciales pour Claude

## Archives

- [2026-04-11 14h00 — CryptoScanner Audit + Migration PostgreSQL](archives/2026-04-11-14h00-cryptoscanner-audit-migration-postgresql.md)
- [2026-04-11 16h00 — CryptoScanner Morning Brief COT + Telegram](archives/2026-04-11-16h00-cryptoscanner-morning-brief-cot-telegram.md)
- [2026-04-11 20h00 — CryptoScanner UI Fixes · Audit · Alertes Macro](archives/2026-04-11-20h00-cryptoscanner-ui-fixes-audit-alerts.md)
- [2026-04-12 12h00 — CryptoScanner Hero · Dashboard · Top Movers](archives/2026-04-12-12h00-cryptoscanner-hero-dashboard-movers.md)
- [2026-04-12 15h00 — CryptoScanner Telegram Retrace RSI + Multi-niveaux](archives/2026-04-12-15h00-cryptoscanner-telegram-retrace-multilevel.md)
- [2026-04-12 18h00 — CryptoScanner Canal FREE + Bot /start + /lier](archives/2026-04-12-18h00-cryptoscanner-canal-free-bot-start.md)
- [2026-04-12 20h00 — CryptoScanner Verif.md : Bugs + Features](archives/2026-04-12-20h00-cryptoscanner-verif-bugs-features.md)
- [2026-04-12 22h00 — CryptoScanner verif.md #4 : Paramètres Plateforme Admin](archives/2026-04-12-22h00-cryptoscanner-verif-4-params-plateforme.md)
- [2026-04-13 14h00 — CryptoScanner Fixes bugs + Wallet Tracker Phase 1 + GitHub](archives/2026-04-13-14h00-cryptoscanner-fixes-wallet-tracker-github.md)
- [2026-04-13 18h00 — CryptoScanner Fix Funding Rate CROWDED POSITIONS](archives/2026-04-13-18h00-cryptoscanner-fix-funding-rate.md)
- [2026-04-14 14h00 — CryptoScanner Fix 4 bugs (inscription, investor, forex, signaux)](archives/2026-04-14-14h00-cryptoscanner-fix-bugs-inscription-investor-forex-signals.md)
- [2026-04-14 18h00 — CryptoScanner Whale Scanner + Fix Inscription 500 + Fix Analyse Investisseur](archives/2026-04-14-18h00-cryptoscanner-whale-scanner-inscription-investisseur.md)
- [2026-04-23 — Memory Compiler Setup](archives/2026-04-23-memory-compiler-setup.md)
- [2026-04-24 — References + Obsidian Integration](archives/2026-04-24-references-obsidian-integration.md)
- [2026-04-24 — API Mix Phase 1b](archives/2026-04-24-api-mix-phase1b.md)
- [2026-04-24 — API Mix Phase 3 Production](archives/2026-04-24-api-mix-phase3-production.md)
- [2026-04-24 — Phase 3 Harmonisation Français](archives/2026-04-24-phase3-harmonisation-francais.md)
- [2026-05-01 — Macro Data Fixes](archives/2026-05-01-macro-data-fixes.md)
- [2026-05-02 — Ticker Dashboard + HTTPS + Bug Fixes](archives/2026-05-02-ticker-https-bug-fixes.md)
- [2026-05-02 (Suite) — Debug Systématique /api/market_info](archives/2026-05-02-debug-api-market-info.md)
  - Diagnostic Phase 1-4 : root cause identification (start_runtime_services jamais appelé)
  - Fix appliqué : Déplacement appel à fin du fichier app.py
  - Secondary fix : _get_session() → get_session() sed replacement
- [2026-05-04 — Inscription + Emails + Hetzner Links](archives/2026-05-04-inscription-emails-hetzner.md)
  - app.py corrompu → validé (2277 lignes)
  - Inscription async (< 1s)
  - Emails async + timeout réduit
  - Tous liens → Hetzner 46.225.234.71
  - SMTP firewall EN ATTENTE config externe
- **[2026-05-05 — Morning Brief Redesign + Root Cause Debug (COMPLÉTÉE)](archives/2026-05-05-morning-brief-redesign-fix.md)**
  - Redesign Morning Brief (Approche C Interactive Pro+) ✅ Déployé
  - Diagnostic complet : Timing issue + CoinGecko 429 rate limit identifiés ✅
  - Fix Phase 1 appliqué : parsing virgule + merger logic ✅
  - Fix Phase 2 requise : Cache fallback pour 429 (URGENT)
  - Memory système mis à jour : contexte.md, TASKS.md, archives
  
  **Découverte clé:** Le problème n'est pas les "variations zéro" mais:
  1. Scanner cache pas prêt quand brief généré (timing)
  2. CoinGecko 429 rate limit sans fallback → data['prices'] vide
  
  **Next:** Implémenter `/tmp/brief-cache.json` + retry logic
