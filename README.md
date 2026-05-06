# CryptoScanner Pro

Application de scanning crypto avec orchestration API Mix et système de mémoire français.

---

## 🚀 Lancer en Local

### Prérequis
- Python 3.11+
- pip ou uv
- `.venv` configuré

### Démarrage rapide
```bash
# Activer venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\Activate.ps1  # Windows

# Installer dépendances
pip install -r requirements.txt

# Lancer app
python app.py
```

Puis accéder à `http://localhost:5000`

---

## 📁 Structure

```
racine/
├── CLAUDE.md              ← Instructions système (lire en premier!)
├── agent.md               ← Guide agents ICA
│
├── app.py                 ← Application principale
├── config.py              ← Configuration
├── wsgi.py                ← WSGI server
├── *.py                   ← Moteurs (scanner, analysis, IA, etc.)
├── requirements.txt       ← Dépendances Python
│
├── docs/                  ← 📚 Documentation complète
│   ├── GUIDE-OBSIDIAN.md
│   ├── CONVENTION-FRANCAIS.md
│   ├── PROTOCOLE-SESSION.md
│   ├── README-COMPLET.md
│   └── ...
│
├── scripts_dev/           ← 🔧 Scripts développement/debug
│   ├── check_schema.py
│   ├── debloquer_admin.py
│   └── ...
│
├── memory/                ← 💾 Mémoire partagée (archives, contexte)
├── references/            ← 📝 Fiches utilisateur (articles, données, idées)
├── directives/            ← 📋 SOPs opérationnelles
├── templates/             ← 🎨 Frontend (HTML/CSS/JS)
├── .claude/               ← 🤖 Agents, rules, commands
│
└── [autres dossiers applicatifs]
```

---

## 📚 Documentation

**Commencer par** : 
- `CLAUDE.md` — Instructions orchestrateur (système complet)
- `docs/GUIDE-OBSIDIAN.md` — Configuration Obsidian + mémoire
- `docs/CONVENTION-FRANCAIS.md` — Règles français

**Navigation** : `docs/INDEX-MEMOIRE.md`

---

## ⚙️ Stack

| Composant | Tech |
|-----------|------|
| Backend | Python 3.11, Flask, SocketIO |
| Frontend | HTML/CSS/JS |
| DB | SQLite |
| APIs | CoinGecko, Binance (gratuites) |
| IA | Groq (principal) + Anthropic (fallback) |

---

## 📦 Scripts principaux

| Script | Rôle |
|--------|------|
| `app.py` | Application Flask + routes |
| `scanner_engine.py` | Scanner multi-exchange |
| `ai_provider.py` | Couche IA unifiée |
| `indices_engine.py` | Indices macro + fallback |
| `smart_signals.py` | Signaux de trading |
| `morning_brief.py` | Morning Brief quotidien |
| `security.py` | Auth + rôles |

---

## 🚢 Production (Hetzner)

- **Serveur**: `46.225.234.71`
- **Manager**: PM2 + Gunicorn eventlet
- **API Mix**: Phase 3 opérationnel ✅
- **Coût**: $0 (APIs gratuites)

---

**Créé** : 2026-04-24
**Dernière mise à jour** : 2026-04-24 (nettoyage structure)
