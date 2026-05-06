# 📚 Documentation CryptoScanner Pro

Tous les guides, conventions, et protocoles pour utiliser le système.

---

## 🎯 Par Cas d'Usage

### Je veux lancer l'appli en local
→ Voir `../README.md` + `../CLAUDE.md`

### Je veux configurer Obsidian
→ Lire `GUIDE-OBSIDIAN.md`

### Je veux créer des fiches (articles, données, idées)
→ Lire `PROTOCOLE-SESSION.md` + `CONVENTION-FRANCAIS.md`

### Je veux comprendre les conventions
→ Lire `CONVENTION-FRANCAIS.md`

### Je veux l'historique complet des sessions
→ Voir `INDEX-MEMOIRE.md` → Memory → Archives

### Je veux la doc technique complète
→ Lire `README-COMPLET.md` + `CRYPTOSCANNER_DOC.md`

### Je veux voir l'état du projet (production)
→ Lire `PROJET_STATUT.md` (mis à jour 2026-05-02)

---

## 📄 Fichiers

| Fichier | Contenu |
|---------|---------|
| `CLAUDE.md` | Instructions orchestrateur (à la racine, pas ici) |
| `GUIDE-OBSIDIAN.md` | Configuration Obsidian vault |
| `PROTOCOLE-SESSION.md` | Comment utiliser le système memory (/recall, /archive) |
| `CONVENTION-FRANCAIS.md` | Règles 100% français pour markdown |
| `INDEX-MEMOIRE.md` | Navigation mémoire partagée (archives, contexte) |
| `README-COMPLET.md` | Documentation technique complète |
| `CRYPTOSCANNER_DOC.md` | Spécifications techniques détaillées |
| `CryptoScanner-Commandes.md` | Commandes disponibles |
| `DEPLOYMENT_INSTRUCTIONS.txt` | Instructions déploiement production |
| `AGENTS.md` | Description des agents du système |
| `PLAN_EMAIL_ACCES_IA.md` | Plan pour email + accès IA |
| `PROJET_STATUT.md` | Status courant du projet |

---

## 🔄 Workflow Standard

```
Session commence
    ↓
Lire GUIDE-OBSIDIAN.md (si première fois)
    ↓
Utiliser /recall cryptoscanner
    ↓
Lire PROTOCOLE-SESSION.md
    ↓
Créer fiches dans references/
    ↓
Lancer /archive à la fin
    ↓
Utiliser CONVENTION-FRANCAIS.md pour tout nouveau markdown
```

---

## 💡 Notes Importantes

- **Tous les fichiers markdown doivent être 100% français** (voir `CONVENTION-FRANCAIS.md`)
- **La mémoire se charge avec `/recall cryptoscanner`** (voir `PROTOCOLE-SESSION.md`)
- **Toujours archiver avec `/archive`** avant fin de session
- **Les scripts_dev/** contiennent des outils debug (ne pas lancer en production)

---

**Créé** : 2026-04-24
**Langue** : Français
**Objectif** : Navigation claire de toute la documentation système
