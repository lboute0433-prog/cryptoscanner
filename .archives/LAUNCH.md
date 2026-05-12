# 🚀 LANCEMENT — Heatmap OI+Volume sur Hetzner

**Status:** ✅ PRÊT POUR LE DÉPLOIEMENT  
**Date:** 2026-05-04  
**Cible:** Hetzner VPS (46.225.234.71)

---

## ✅ Ce qui est prêt

### Fichiers Application
- ✅ `app_local_complete.py` — Application Flask complète (29 KB)
- ✅ `heatmap_engine.py` — Moteur de calcul (11 KB)
- ✅ `schema.sql` — Schéma SQLite (737 B)

### Scripts de Déploiement
- ✅ `deploy_to_hetzner.sh` — Déploiement automatisé (6.3 KB)
- ✅ `verify_deployment.sh` — Vérification post-déploiement (4.3 KB)

### Tests
- ✅ `test_heatmap_local.py` — 15/15 tests ✓
- ✅ Syntaxe Python vérifiée ✓
- ✅ Structure de données validée ✓

### Documentation
- ✅ `README_DEPLOYMENT.md` — Guide complet
- ✅ `DEPLOYMENT_AUTOMATION.md` — Détails techniques
- ✅ `FINAL_SUMMARY.md` — Résumé du projet
- ✅ `DELIVERABLES.md` — Inventaire complet

---

## 🎯 Instructions de Lancement (3 minutes)

### Depuis votre machine locale :

```bash
# 1. Naviguer au répertoire du projet
cd C:\Users\loyan\Documents\Antigravity\cryptoscanner

# 2. Lancer le déploiement automatisé
bash deploy_to_hetzner.sh

# Le script va:
#   ✅ Vérifier la connexion SSH
#   ✅ Créer les répertoires sur le serveur
#   ✅ Uploader les fichiers via SCP
#   ✅ Vérifier la syntaxe Python
#   ✅ Installer/configurer PM2
#   ✅ Démarrer l'application
#   ✅ Tester les endpoints API
#   ✅ Afficher le statut et les logs
```

### Après le déploiement :

```bash
# 3. Vérifier que tout fonctionne
bash verify_deployment.sh 46.225.234.71

# Le script vérifie:
#   ✅ Connectivité SSH
#   ✅ Statut du processus PM2
#   ✅ Endpoints API (/api/heatmap/all, /api/heatmap/BTC)
#   ✅ Port 5000 actif
#   ✅ Fichiers présents
#   ✅ Dépendances Python
#   ✅ Logs récents
```

---

## 🌐 Accès après déploiement

### Dashboard
```
http://46.225.234.71:5000
```
- Table interactive de 6 cryptos (BTC, ETH, SOL, XRP, DOGE, ADA)
- Cliquer sur une crypto pour voir le graphique
- Lignes de prix en surimpression (bleu/orange/rouge)
- Données en temps réel depuis Binance FAPI

### API Endpoints
```
GET http://46.225.234.71:5000/api/heatmap/all
GET http://46.225.234.71:5000/api/heatmap/BTC
GET http://46.225.234.71:5000/api/heatmap/ETH
...etc
```

---

## 📋 Checklist Pré-Déploiement

Avant de lancer, vérifier:

- [ ] Vous êtes sur votre machine locale (pas le sandbox)
- [ ] Clé SSH configurée (`~/.ssh/id_rsa` ou équivalent)
- [ ] Accès SSH à Hetzner disponible: `ssh root@46.225.234.71`
- [ ] Fichiers présents:
  ```bash
  ls -lh app_local_complete.py heatmap_engine.py schema.sql
  ```
- [ ] Scripts exécutables:
  ```bash
  ls -lh deploy_to_hetzner.sh verify_deployment.sh
  ```
- [ ] Bash shell disponible (Linux/Mac/WSL/Git Bash)

---

## 🔧 En cas de problème

### SSH ne fonctionne pas
```bash
# Tester la connexion
ssh root@46.225.234.71

# Si clé spéciale
ssh -i ~/.ssh/votre_cle root@46.225.234.71

# Si vous avez un mot de passe en lieu et place d'une clé
# Exécuter: bash deploy_to_hetzner.sh
# et entrer le mot de passe quand demandé
```

### Erreur lors du déploiement
```bash
# Afficher les commandes en détail
bash -x deploy_to_hetzner.sh

# Ou lancer manuellement (voir HEATMAP_DEPLOYMENT_GUIDE.md)
```

### Vérifier après déploiement
```bash
# Voir le statut
ssh root@46.225.234.71 "pm2 status"

# Voir les logs
ssh root@46.225.234.71 "pm2 logs heatmap"

# Tester l'API
curl http://46.225.234.71:5000/api/heatmap/all
```

---

## 📊 Ce qui va se passer

### Phase 1: Préparation (30 secondes)
```
✓ Vérification SSH
✓ Création répertoires
```

### Phase 2: Upload (30 secondes)
```
✓ app_local_complete.py
✓ heatmap_engine.py
✓ schema.sql
```

### Phase 3: Vérification (10 secondes)
```
✓ Syntaxe Python
✓ PM2 disponible
```

### Phase 4: Démarrage (20 secondes)
```
✓ PM2 lance l'app
✓ Application écoute port 5000
```

### Phase 5: Test (10 secondes)
```
✓ API endpoints répondent
✓ Données valides
```

**Temps total: ~2 minutes** ⏱️

---

## 📈 Résultats attendus

Après le déploiement réussi, vous devriez voir:

```
✅ DEPLOYMENT COMPLETE

📊 Dashboard: https://46.225.234.71:5000
📡 API Endpoints:
   • https://46.225.234.71:5000/api/heatmap/all
   • https://46.225.234.71:5000/api/heatmap/<symbol>

🔧 Useful Commands:
   • View logs:     ssh root@46.225.234.71 'pm2 logs heatmap'
   • Stop process:  ssh root@46.225.234.71 'pm2 stop heatmap'
   • Restart:       ssh root@46.225.234.71 'pm2 restart heatmap'
```

---

## 🎯 Après le déploiement

### Étape 1: Tester (immédiat)
```bash
# Depuis votre navigateur ou curl
curl http://46.225.234.71:5000/api/heatmap/all

# Devrait retourner JSON avec données des 6 cryptos
```

### Étape 2: Vérifier les logs (1 minute)
```bash
ssh root@46.225.234.71 "pm2 logs heatmap --lines 20"

# Devrait montrer des messages "Flask running" sans erreurs
```

### Étape 3: Accéder au dashboard (dans navigateur)
```
http://46.225.234.71:5000
```
- Table avec 6 cryptos visible à gauche
- Cliquer sur BTC, ETH, etc.
- Graphique candlestick apparaît à droite
- Lignes de prix overlay visibles

### Étape 4: Monitorer (24 heures)
```bash
# Vérifier régulièrement
watch -n 60 'curl -s http://46.225.234.71:5000/api/heatmap/all | head -50'

# Ou via PM2
ssh root@46.225.234.71 "pm2 monitor"
```

---

## 🔐 Configuration pour la Production

Une fois déployé, envisager:

### Court terme (cette semaine)
- [ ] Activer HTTPS/SSL via nginx
- [ ] Ajouter authentification `cs_token`
- [ ] Configurer rate limiting
- [ ] Monitorer logs Binance API

### Moyen terme (semaine prochaine)
- [ ] Intégrer dans main `app.py`
- [ ] WebSocket pour mises à jour temps réel
- [ ] Alertes sur pics d'intensité
- [ ] Dashboard avancé

### Long terme (après)
- [ ] PostgreSQL pour historique OI
- [ ] Mobile responsive improvements
- [ ] Découverte dynamique symbols Binance
- [ ] Cache Redis

---

## 📞 Support Rapide

| Problème | Solution |
|----------|----------|
| SSH timeout | Vérifier clé SSH + firewall |
| Files not found | Exécuter depuis bon répertoire |
| Python error | Exécuter `python3 -m py_compile app_local_complete.py` |
| Port 5000 busy | `pm2 kill all` ou attendre |
| API no response | `pm2 logs heatmap` pour diagnostiquer |

**Plus de détails:** Voir `DEPLOYMENT_AUTOMATION.md`

---

## 🎬 Commandes Clés

```bash
# Avant déploiement
ssh root@46.225.234.71 "echo OK"      # Tester SSH

# Pendant déploiement
bash deploy_to_hetzner.sh               # Lance le déploiement

# Après déploiement
bash verify_deployment.sh               # Vérifie tout

# Pour monitorer
ssh root@46.225.234.71 "pm2 logs heatmap"  # Logs en temps réel
ssh root@46.225.234.71 "pm2 status"        # Statut
ssh root@46.225.234.71 "pm2 monitor"       # Dashboard PM2

# Pour redémarrer
ssh root@46.225.234.71 "pm2 restart heatmap"

# Pour arrêter
ssh root@46.225.234.71 "pm2 stop heatmap"
```

---

## 🚀 Ready to Launch!

Tout est prêt. À partir de votre machine locale:

```bash
cd C:\Users\loyan\Documents\Antigravity\cryptoscanner
bash deploy_to_hetzner.sh
```

**Durée:** ~2 minutes  
**Résultat:** Application en production sur Hetzner  
**Prochaine étape:** Vérifier avec `bash verify_deployment.sh`

---

**Status:** ✅ PRÊT  
**Date:** 2026-05-04  
**Heure:** À tout moment
**Go/No-Go:** **GO** 🚀

Bonne chance! 🎯
