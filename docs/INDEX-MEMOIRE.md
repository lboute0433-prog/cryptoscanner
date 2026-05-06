# 📑 Index Principal — CryptoScanner Pro

**Accueil du système** — Commencez ici pour naviguer.

## 🚀 État du Projet

[[memory/contexte]] — **À LIRE EN PREMIER** : où en sommes-nous, Phase 3 live, API Mix opérationnel

## 📚 Documentation

- [[CONVENTION-FRANCAIS]] — Règles 100% français
- [[PROTOCOLE-SESSION]] — Comment utiliser le système memory
- [[GUIDE-OBSIDIAN]] — Configuration Obsidian

## 💾 Mémoire du Projet

### Archives Immuables
[[memory/archives/2026-04-24-phase3-harmonisation-francais]] — Dernière session (Phase 3 + harmonisation français)

### État Courant
[[memory/contexte]] — Snapshot actuel du projet

## 📝 Vos Fiches Personnelles

### Articles & Analyses
[[references/articles/EXEMPLE]] — Template pour créer vos articles

Vos articles ici :
- Cliquez sur "Créer un nouveau fichier" dans `references/articles/`

### Données & Métriques
[[references/donnees/EXEMPLE]] — Template pour vos données

Vos données ici :
- Cliquez sur "Créer un nouveau fichier" dans `references/donnees/`

### Idées & Brainstorm
[[references/idees/EXEMPLE]] — Template pour vos idées

Vos idées ici :
- Cliquez sur "Créer un nouveau fichier" dans `references/idees/`

## 🔧 Technique

### Stack Production
- **Serveur** : Hetzner VPS (46.225.234.71)
- **Backend** : Python 3.12, Flask, SocketIO
- **APIs** : CoinGecko + Binance (gratuites)
- **Manager** : PM2 + Gunicorn eventlet

### État Live
✅ Production Hetzner opérationnelle
✅ APIManager chargé et fonctionnel  
✅ Endpoints retournent données
✅ Coût: $0 (100% APIs gratuites)

## 📋 Checklist — Prochaines Étapes

### Immédiat
- [ ] Reconfigurer Obsidian (voir [[GUIDE-OBSIDIAN]])
- [ ] Créer premières fiches dans `references/`
- [ ] Lancer `/recall cryptoscanner` en session suivante

### Court Terme (Production)
- [ ] Configurer SMTP (emails)
- [ ] Configurer SSL/HTTPS + domaine
- [ ] Passer à venv propre sur Hetzner

### Moyen Terme
- [ ] Phase 2 Extended (CoinMarketCap, Glassnode fallbacks)
- [ ] Load testing (100+ users)

---

## 🎯 Utilisation du Système

### Début de Session
```
/recall cryptoscanner
```
→ Claude charge contexte + fiches

### Pendant la Session
- Créer fiches dans `references/`
- Claude les utilise pour contextualiser

### Fin de Session
```
/archive
```
→ Claude sauvegarde tout

---

**Créé** : 2026-04-24
**Langue** : Français
**Objective** : Point d'entrée principal du système
