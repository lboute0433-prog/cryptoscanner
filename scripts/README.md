# 🔧 Scripts

Scripts utilitaires pour développement, API Mix, et maintenance.

---

## 📦 API Mix (Production)

| Composant | Rôle |
|-----------|------|
| `api_mix/` | Orchestration API (CoinGecko, Binance, fallbacks) |
| `compile.py` | Compiler assets |
| `flush.py` | Vider cache/logs |
| `query.py` | Query helpers |
| `utils.py` | Utilitaires partagés |
| `config.py` | Configuration scripts |

**Status**: Production sur Hetzner via PM2 ✅

---

## 🔧 Développement (Local uniquement)

| Script | Fonction |
|--------|----------|
| `check_schema.py` | Vérifier schéma DB |
| `debloquer_admin.py` | Créer/débloquer admin |
| `inject_login_modal.py` | Test modal login |
| `inject_skeleton_states.py` | Test UI loading states |
| `upgrade_user.py` | Upgrade rôle utilisateur |

**Usage** (depuis racine):
```bash
python scripts/debloquer_admin.py
```

**⚠️ Important**: Ces scripts modifient DB/frontend. Local uniquement, ne jamais lancer en production.

---

**Créé**: 2026-04-24
**Structure**: Production + Development clairement séparés
