# 🔧 PROBLÈMES À RÉGLER — CryptoScanner Pro

**Status**: 2026-05-01 — Session macro-data-fixes  
**Priorité**: Haute

---

## 🔴 CRITIQUES

### 1. Données Macro Vides sur Hetzner
**Symptôme**: Les blocs Fear & Greed, Dominance, etc. restent vides sur `/macro`  
**Endpoint**: `http://46.225.234.71/api/market_info` retourne `{}`  
**Cause Probable**: 
- APIs externes (Fear & Greed, CoinGecko Global) ne répondent pas depuis Hetzner
- OU le code n'a pas été bien déployé (need to verify file timestamps)
- OU redémarrage PM2 incomplet (need longer wait time)

**À Faire**:
- [ ] Vérifier que les 3 fichiers (news_macro.py, indices_engine.py, scanner_engine.py) sont bien sur Hetzner
- [ ] Vérifier les timestamps du fichier (dernière modif = maintenant?)
- [ ] Tester les APIs directement depuis Hetzner avec curl + User-Agent
- [ ] Augmenter timeout PM2 startup (actuellement 10s, peut-être insuffisant)
- [ ] Vérifier les logs PM2 pour erreurs de connexion API

**Fichiers à Vérifier**:
- `/root/cryptoscanner/scanner_engine.py` (ligne 725+)
- `/root/cryptoscanner/news_macro.py` (ligne 1131+)
- `/root/cryptoscanner/indices_engine.py` (ligne 106+)

---

### 2. Alertes Telegram Ne S'Envoient Pas
**Symptôme**: `Done: 0 email(s), 0 Telegram(s)` dans Morning Brief logs  
**Variables**: TG_TOKEN et TG_CHAT existent  
**Cause Probable**:
- Aucun signal critique détecté (normal si pas d'alertes)
- OU fonction `_send_telegram()` échoue silencieusement
- OU token Telegram invalide/bot suspendu

**À Faire**:
- [ ] Vérifier que TG_TOKEN et TG_CHAT sont valides
- [ ] Tester l'envoi manuel via API Telegram
- [ ] Ajouter du logging dans `_send_telegram()` pour debug
- [ ] Vérifier les logs d'erreur PM2 pour exceptions non-catchées

**Code**: `news_macro.py` ligne 250+, `daily_report.py` ligne ~

---

## 🟡 IMPORTANTES

### 3. Netlinking Données Macro ↔️ Frontend
**Symptôme**: API retourne les données mais le JavaScript ne les affiche pas  
**Endpoint**: `/api/macro/all` retourne complètement ✓ mais `/macro` affiche vides  
**Cause Probable**:
- Erreur JavaScript dans le template (éléments non-remplis)
- Cache navigateur stale
- SocketIO ne transmet pas les données en temps réel

**À Faire**:
- [ ] Ouvrir F12 Console sur `/macro` et chercher les erreurs JS
- [ ] Forcer Ctrl+Shift+Delete + Ctrl+F5 pour clean cache
- [ ] Vérifier que les IDs HTML matchent les variablesJS:
  - `id="fg-val"` vs JS `document.getElementById('fg-val')`
  - `id="btc-dom"` vs JS `document.getElementById('btc-dom')`
- [ ] Tester si SocketIO `macro_update` arrive au navigateur

---

## 🟢 OPTIONNELS

### 4. Améliorer Resilience Réseau Hetzner
**Symptôme**: APIs externes timeout/refuse même avec retry  
**Cause**: ISP blocking, datacenter firewall, rate-limiting  

**À Faire**:
- [ ] Tester avec proxies publics (CORS-anywhere, allorigins)
- [ ] Implémenter circuit-breaker (stop après N failures)
- [ ] Cache plus long (actuellement 30-60 min, augmenter à 24h)
- [ ] Fallback data: si API échoue, servir données cached old (même stale)

---

## 📋 CHECKLIST DÉPLOIEMENT

Avant de déployer la prochaine fois:

- [ ] Vérifier que `git status` est clean (aucun fichier oublié)
- [ ] Tester localement avant de pusher
- [ ] Vérifier les fichiers sur Hetzner après copy:
  ```bash
  ls -lah /root/cryptoscanner/scanner_engine.py
  ls -lah /root/cryptoscanner/news_macro.py
  ```
- [ ] Attendre 10s après `pm2 restart` avant tester
- [ ] Vérifier `/api/market_info` BEFORE accessing `/macro`
- [ ] Ouvrir F12 et chercher les erreurs JS

---

## 🎯 PROCHAINES ÉTAPES

1. **Debug Session** (30 min):
   - SSH to Hetzner + verify files
   - Test APIs directly
   - Check browser console

2. **If Still Broken** (1h):
   - Implement circuit-breaker + fallback cache
   - Add detailed logging
   - Test with proxy/CDN for API calls

3. **If Network Confirmed Down**:
   - Implement offline mode (serve cached data indefinitely)
   - Alert user that external APIs are unavailable

---

**Last Updated**: 2026-05-01 14:30  
**By**: Orchestrateur CryptoScanner Pro  
**Session**: macro-data-fixes-v2
