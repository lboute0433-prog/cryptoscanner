# 🧠 Learning Log - Trading & Development Insights

**Purpose**: Document discoveries, patterns, and lessons learned  
**Updated**: Continuously (whenever you learn something important)  
**Connected To**: Code, Metrics, Strategy improvements

---

## 📋 How to Use This Log

1. **After every significant observation**: Add an entry
2. **Format**: Date | Discovery | Evidence | Action Taken
3. **Tag it**: Add #trading, #monitoring, #incident, #optimization
4. **Link it**: Link to code changes or strategy notes
5. **Review**: Weekly to identify patterns

---

## 🔍 Learning Entries

### 2026-04-29: Lightweight-Charts Evaluation (Déféré Phase 5+)
**Discovery**: TradingView lightweight-charts est puissante pour charting financier (HTML5 canvas, ~50KB)  
**Evidence**: Analyse repo Github + documentation complète  
**Market Context**: Planning Phase 5 (Morning Brief dashboard)  
**Implication**: Utile pour UI trader-friendly, MAIS pas critique pour MVP (Grafana couvre tout)  
**Action Taken**: Gardé en mémoire pour Phase 5+, non prioritaire maintenant  
**Status**: Validated, Deferred to Phase 5+  
**Links**: [[01-Project-Overview]], [[04-Grafana-Setup-FR]]

**Évaluation**:
- Performance: Excellente (canvas vs Grafana)
- Intégration React: Simple (~5-6h)
- Priorité MVP: Basse (Grafana suffit)
- Usefulness: Moyenne (nice-to-have pour Morning Brief)

**Follow-up**: Revenir en Phase 5 quand stratégie validée en live

---

### 2026-04-29: Obsidian + Claude Integration Ready
**Discovery**: MCP Tools connected to Obsidian vault  
**Implication**: Documentation → Code pipeline now active  
**Action**: Start capturing learnings in structured format

**Metrics**: 
- Slack time between discovery & implementation: < 1 hour now

**Next**: Document all future learnings here → I'll read → Code updates

---

### Template: Learning Entry (Copy & Paste)

```markdown
### YYYY-MM-DD: [Observation Title]
**Discovery**: [What did you observe?]
**Evidence**: [Data/metrics that prove it]
**Market Context**: [What was happening in markets?]
**Implication**: [Why does this matter?]
**Action Taken**: [What code/metric changed?]
**Status**: Validated / Testing / Hypothesis
**Links**: [[Strategy Name]], [[Incident Report]], [[Code PR]]

**Metrics Impact**:
- [Metric A]: Before → After
- [Metric B]: Before → After

**Follow-up**: [What to test next?]
```

---

## 🎯 Active Learning Topics

### Topic 1: Execution Quality (Slippage & Latency)

**Current Understanding**:
- Slippage increases with order size
- API latency spikes during market open
- Kraken more volatile than IB

**Hypothesis to Test**:
- Does slippage correlate with VIX?
- Can we predict latency spikes?
- Should we reduce order size during spikes?

**Related Metrics**:
- `trading_slippage_avg_bps`
- `trading_api_latency`
- `market_volatility`

**Decision Log**:
- Decided to add SlippageHigh alert (> 5bps) ✅
- Decided to monitor latency by venue ✅
- Next: Compare slippage across venues

---

### Topic 2: Risk Management (Drawdown & Leverage)

**Current Understanding**:
- Drawdown > 25% is ruin risk
- Leverage > 90% is danger zone
- Position correlation matters

**Hypothesis to Test**:
- Does drawdown recover faster at certain times?
- What's optimal leverage for this strategy?
- Should we scale size based on drawdown?

**Related Metrics**:
- `trading_drawdown_pct_*`
- `trading_leverage_utilization_pct`
- `trading_correlation`

**Decision Log**:
- Set DrawdownCritical alert at 25% ✅
- Set LeverageHigh alert at 90% ✅
- Next: Test optimal leverage levels

---

### Topic 3: Strategy Performance (SimpleMomentum Tuning)

**Current Parameters**:
- Window: 20 (momentum lookback)
- Threshold: 0.05 (entry signal)
- Max Positions: 5

**Backtest Results**:
- Sharpe: 1.2
- Win Rate: 52%
- Drawdown: 18%

**Hypotheses to Test**:
- Does window=30 work better in trends?
- Does lower threshold improve win rate?
- Should we limit max positions?

**Related Notes**: [[11-SimpleMomentum]]

---

## 📊 Metrics & Learnings Connection

### Hypothesis: "Slippage increases with volatility"

**Test Method**:
1. Record in Learning Log (you do this)
2. I read it via MCP
3. I add metric query to verify
4. Create dashboard panel to monitor
5. Update alert thresholds based on data

**Result**: Knowledge → Metrics → Monitoring → Action

---

## 🔗 Learning → Code Pipeline

### Example: Slippage Discovery
```
Observation (this log):
"Slippage > 5bps when VIX > 25"

I read it:
→ Create MetricsRecorder for volatility
→ Add SlippageHigh alert (> 5bps for 15m)
→ Create dashboard panel
→ Add to [[11-SimpleMomentum]] params

You see result:
→ ALERTS CENTER shows SlippageHigh firing
→ Review [[04-Grafana-Setup]] for action
→ Reduce position size when alert fires

Outcome: Knowledge → Code → Monitoring → Trading Improvement
```

---

## 🎓 Learning Categories

### #trading
Market behavior, strategy insights, execution patterns

### #monitoring
Metrics, alerts, dashboard improvements

### #architecture  
System design decisions, tech choices

### #incident
When something goes wrong, log it here

### #optimization
Performance improvements, efficiency gains

### #bug
Bugs found and fixed

### #decision
Important decisions made and why

---

## 📈 Pattern Recognition

### Question: What patterns have emerged?

**Execution Quality**:
- Latency spikes at market open (+300-500ms)
- Slippage higher in low-liquidity pairs
- Kraken slower than IB in evening (UTC+0)

**Risk**:
- Drawdowns faster in high-volatility markets
- Recovery slower with high leverage
- Correlated positions amplify drawdown

**Strategy**:
- Momentum works in trending markets
- Struggles in choppy/range-bound markets
- Win rate stable, but position sizing critical

---

## 🚀 Next Steps for Learning

1. **Daily**: Spend 5-10 min reviewing metrics
2. **When curious**: Add observation + hypothesis
3. **Weekly**: Look for patterns across entries
4. **Monthly**: Review if hypotheses validated
5. **Quarterly**: Update strategy based on learnings

---

## 📚 Related Documentation

- [[11-SimpleMomentum]] - Strategy details
- [[04-Grafana-Setup]] - How to monitor learnings
- [[24-Incident-Reports]] - When something breaks
- [[20-Development-Roadmap]] - What to test next

---

**Remember**: Every learning here helps both you AND Claude improve the system! 🚀
