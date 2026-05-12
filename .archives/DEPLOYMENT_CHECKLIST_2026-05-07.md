# 🚀 DEPLOYMENT CHECKLIST — Phase 2 to Hetzner

**Date:** 2026-05-07  
**Status:** Ready for Deployment  
**Target:** Hetzner Production Server  

---

## 📋 FILES TO UPLOAD

### **Core Application Files**

#### Backend (Python/Flask)
- [ ] `app.py` — Main Flask application (modified: +400 lines for APIs)
- [ ] `security.py` — Security headers & auth (modified: CSP fix for TradingView)
- [ ] `db.py` — Database functions (no changes)
- [ ] `config.py` — Configuration (no changes)
- [ ] `ccxt_wrapper.py` — Multi-exchange manager (Phase 1)

#### Phase 2 Engines
- [ ] `indicators_engine.py` — 50+ technical indicators (NEW)
- [ ] `pattern_recognition.py` — 15 candlestick patterns (NEW)
- [ ] `scanner_engine.py` — Integration layer (modified: +290 lines)
- [ ] `smart_signals_v2.py` — Multi-timeframe signal engine (NEW)
- [ ] `smart_signals.py` — Legacy smart signals v1 (keep for fallback)

#### Existing Engines (No Changes, Keep as-is)
- [ ] `news_macro.py`
- [ ] `cot_engine.py`
- [ ] `ai_provider.py`
- [ ] `daily_report.py`
- [ ] `lexique.py`
- [ ] `backtest_engine.py`
- [ ] `forex_engine.py`
- [ ] `indices_engine.py`
- [ ] `cvd_engine.py`

#### Frontend
- [ ] `templates/index.html` — Dashboard (modified: +311 lines for indicators panel)

#### Configuration & Database
- [ ] `.env` — Environment variables (update with production keys)
- [ ] `requirements.txt` — Python dependencies

---

### **Testing Files (Optional for Production)**

These are for verification only - don't need to run on production server:

- [ ] `test_phase2_indicators.py` (573 lines, 37 tests)
- [ ] `test_phase2_patterns.py` (567 lines, 28 tests)
- [ ] `test_phase2_api_performance.py` (639 lines, 26 tests)
- [ ] `test_phase2_integration.py` (405 lines, 21 tests)
- [ ] `test_phase2_edge_cases.py` (450 lines, 39 tests)
- [ ] `test_phase2_smart_signals.py` (355 lines, 27 tests)
- [ ] `test_smart_signals_integration.py` (273 lines, 13 tests)

---

### **Documentation Files (Reference Only)**

- [ ] `PHASE2_COMPLETE_FINAL_2026-05-07.md`
- [ ] `PHASE2_FINAL_SUMMARY_2026-05-07.md`
- [ ] `PHASE2_STATUS_2026-05-07_TASK4_COMPLETE.md`
- [ ] `PROGRESS_OBSIDIAN_2026-05-07.md` (updated)
- [ ] `DEPLOYMENT_CHECKLIST_2026-05-07.md` (this file)

---

## 🔧 DEPLOYMENT STEPS

### 1. **Pre-Deployment Verification**
- [ ] All tests pass locally (307 tests, 100%)
- [ ] No console errors in browser
- [ ] TradingView widget loads (CSP fixed)
- [ ] Indicators panel displays correctly
- [ ] API endpoints respond correctly

### 2. **Upload Files to Hetzner**

**Via SFTP/SCP:**
```bash
# Core application files
scp app.py user@server:/app/
scp security.py user@server:/app/
scp indicators_engine.py user@server:/app/
scp pattern_recognition.py user@server:/app/
scp scanner_engine.py user@server:/app/
scp smart_signals_v2.py user@server:/app/
scp templates/index.html user@server:/app/templates/
```

**Or Git Pull (Recommended):**
```bash
cd /app
git pull origin master
```

### 3. **Restart Services on Hetzner**

```bash
# Restart Flask application
sudo systemctl restart cryptoscanner

# Or if using gunicorn/nginx
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Verify status
sudo systemctl status cryptoscanner
```

### 4. **Post-Deployment Verification**

- [ ] Application loads at https://cryptoscanner.com
- [ ] Dashboard displays without errors
- [ ] ANALYSE TECHNIQUE AUTOMATIQUE section visible
- [ ] Indicators load and update
- [ ] API endpoints respond (/api/indicators/all, etc.)
- [ ] TradingView widget loads
- [ ] No CSP errors in console
- [ ] Database migrations applied (if any)

---

## 📊 PHASE 2 STATS FOR DEPLOYMENT

```
Total Code Lines:        3,500+
Total Test Coverage:     307 tests (100% passing)
Performance:             <500ms per symbol
Backward Compatible:     YES
Breaking Changes:        NONE
Database Changes:        NONE
Configuration Changes:   CSP header only
```

---

## 🔐 PRODUCTION CONFIGURATION

**Update these on production server:**

1. **Environment Variables (.env)**
   - CCXT API keys (for exchanges)
   - Database path
   - Telegram tokens
   - Email credentials

2. **Security Headers (already fixed in security.py)**
   - CSP now allows TradingView
   - X-Frame-Options set to SAMEORIGIN
   - frame-src allows TradingView

3. **Database**
   - Backup existing database before deployment
   - No migrations needed for Phase 2

---

## ✅ DEPLOYMENT VERIFICATION CHECKLIST

After deploying to Hetzner, verify:

- [ ] **Frontend:** Dashboard loads without errors
- [ ] **Indicators Panel:** "ANALYSE TECHNIQUE AUTOMATIQUE" displays
- [ ] **Indicators Load:** Grid shows 50+ indicators with values
- [ ] **Patterns Display:** Support/Resistance zones show
- [ ] **Signal Calculation:** Final signal displays (BULLISH/BEARISH/NEUTRAL)
- [ ] **API Endpoints:** Test in curl/Postman:
  - [ ] `GET /api/indicators/all?symbol=BTC&timeframe=1h`
  - [ ] `GET /api/indicators/custom?symbol=BTC&indicators=RSI,MACD`
  - [ ] `GET /api/patterns/detect?symbol=BTC&lookback=100`
  - [ ] `POST /api/indicators/save`
- [ ] **TradingView Widget:** Loads on GRAPHIQUE tab
- [ ] **Database:** No errors in logs
- [ ] **Performance:** Response times acceptable
- [ ] **Logs:** No exceptions or warnings

---

## 🔄 ROLLBACK PLAN

If issues occur:

1. **Git Rollback:**
   ```bash
   git revert <commit-hash>
   git push origin master
   ```

2. **Database Rollback:**
   - No database changes in Phase 2, safe to rollback

3. **Application Restart:**
   ```bash
   sudo systemctl restart cryptoscanner
   ```

---

## 📞 SUPPORT CONTACTS

- **Error Logs:** `/var/log/cryptoscanner/`
- **Database:** SQLite at configured path
- **API Documentation:** See Phase 2 summary docs

---

## 🎯 NEXT PHASE

**Phase 2.5 (Planned for Next Session):**
- Custom OHLCV chart (replace TradingView widget)
- Indicator overlays on chart
- Multi-timeframe selector
- Interactive zoom/pan
- Zero TradingView dependency

---

**Deployment Date:** 2026-05-08  
**Estimated Deployment Time:** 15-30 minutes  
**Rollback Time:** <5 minutes  

✅ **Ready for Production Deployment**

