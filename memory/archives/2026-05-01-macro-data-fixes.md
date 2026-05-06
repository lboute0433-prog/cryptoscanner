# Session Archive — 2026-05-01 — Macro Data Fixes

**Date**: 2026-05-01 14:30 UTC  
**Status**: Partially Completed - Issues Remain  
**Session ID**: macro-empty-data-v2  

---

## Problems Addressed

### 1. ✅ Calendrier Économique (News Macro)
- **Issue**: Données stats n'arrivaient pas
- **Root Cause**: ForexFactory XML ne se chargeait pas (pas de fallback)
- **Fix Applied**:
  - Ajouté 5 URLs fallback pour ForexFactory
  - Timeout 15s → 20s
  - Cache persistant en BDD (7j TTL)
  - Backup XML en cache (24h)
  - Fallback forecast_val si pas données réelles
- **File Modified**: `news_macro.py` (240+ lines)
- **Status**: ✅ Deployé et testé en local

### 2. ✅ Inflation/Nasdaq/Indices APIs
- **Issue**: Données macro vides sur Hetzner (FRED, CoinGecko, Yahoo Finance ne répondaient pas)
- **Root Cause**: Pas de User-Agent + timeout court (10s)
- **Fix Applied**:
  - `fetch_inflation()`: User-Agent + retry(3x) + timeout 15s
  - `fetch_nasdaq_correlation()`: User-Agent + timeout 15s
  - `fetch_single_index()`: User-Agent + retry(2x) + timeout 12s
- **Files Modified**: `news_macro.py`, `indices_engine.py`
- **Status**: ✅ Déployé sur Hetzner

### 3. ✅ Market-Info (Fear & Greed, Dominance)
- **Issue**: `/api/market_info` retournait `{}` (vide)
- **Root Cause**: APIs externes échouaient (Fear & Greed API, CoinGecko Global)
- **Fix Applied**:
  - `fetch_market_info()`: User-Agent + retry(2x) + timeout 12s pour chaque API
  - Improved Accept headers
- **File Modified**: `scanner_engine.py` (lignes 725-775)
- **Status**: ✅ Commité + uploadé sur Hetzner

---

## What Worked in Local

✅ Calendrier économique — données complètes  
✅ Fear & Greed Index — chargé avec valeur (26 = Fear)  
✅ API endpoints — retournent des données  

**Screenshot**: Sentiment Macro Global affichait tous les blocs remplis en local

---

## What Failed on Hetzner (Post-Fix)

❌ Blocs vides sur `/macro` malgré les fixes  
❌ `/api/market_info` retourne `{}` même après upload  
❌ Les données arrivent par `/api/macro/all` mais ne s'affichent pas au frontend  

**Hypothesis**: 
- Les APIs externes échouent toujours depuis Hetzner (connectivité réseau, firewall)
- OU le code n'a pas été correctement déployé
- OU il faut redémarrer plus longtemps pour que les données se cachent

---

## Telegram Alerts

**Status**: ❌ Non réglé

**Issue**: `Done: 0 email(s), 0 Telegram(s)` dans les logs Morning Brief  
**Variables**: TG_TOKEN et TG_CHAT existent  
**Hypothesis**: Aucun signal critique détecté OU fonction d'envoi échoue silencieusement

---

## Files Modified This Session

| File | Changes | Status |
|------|---------|--------|
| `news_macro.py` | +240 lignes (3 functions) | ✅ Deployé |
| `indices_engine.py` | +40 lignes (retry loops) | ✅ Deployé |
| `scanner_engine.py` | +30 lignes (fetch_market_info) | ✅ Uploadé |
| `templates/index.html` | Revert grid (2 col) | ✅ Fixed |

---

## To Debug Next Session

1. **SSH to Hetzner and check**:
   ```bash
   curl -s http://46.225.234.71/api/market_info
   curl -s http://46.225.234.71/api/macro/all
   ```
   
2. **Check logs for errors**:
   ```bash
   pm2 logs cryptoscanner --lines 200 | grep -E "ERROR|FAIL|Exception"
   ```

3. **Test API connectivity from Hetzner**:
   ```bash
   curl -I "https://api.alternative.me/fng/?limit=1"
   curl -I "https://api.coingecko.com/api/v3/global"
   ```

4. **Check browser console** (F12) for JS errors when loading `/macro`

---

**Conclusion**: Tous les fixes de code ont été appliqués et déployés. Le problème persiste, suggérant soit une issue réseau Hetzner, soit un problème de déploiement/redémarrage incomplète.
