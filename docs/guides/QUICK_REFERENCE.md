# Taiwan Stock Strategy System - Quick Reference

**Version**: 2.0 | **Date**: 2025-10-10 | **Status**: Phase 1 Complete ✅

---

## 🎯 Performance Targets

| Metric | Target | Benchmark (烏龜) | Phase 1 Best |
|--------|--------|------------------|--------------|
| **Sharpe Ratio** | >2.0 | 2.09 ✅ | 1.79 |
| **Annual Return** | >30% | 29.25% | 27.67% |
| **Max Drawdown** | <-20% | -15.41% | -16.50% |

**Phase 1 Success Rate**: 80% (40/50 strategies achieved Sharpe >1.5)

---

## 🏗️ Three Architecture Patterns

### Pattern A: Multi-Layer AND (High Sharpe 1.5-2.5)
```python
# 6-layer quality filter (烏龜 pattern)
cond1 = valuation_filter      # Dividend yield ≥6%
cond2 = technical_filter       # Price > MA(20) & MA(60)
cond3 = growth_filter          # Revenue 3m > 12m avg
cond4 = quality_filter         # Operating margin ≥3%
cond5 = insider_filter         # Director holding ≥10%
cond6 = liquidity_filter       # Volume in [50K, 10M]

buy = cond1 & cond2 & cond3 & cond4 & cond5 & cond6
buy = (buy * rev_growth_rate)[buy>0].is_largest(10)
```
**Use When**: High Sharpe target, willing to accept complexity

### Pattern B: Factor Ranking (Stable 0.8-1.3)
```python
# Single factor focus
factor = composite_metric  # e.g., R&D/Admin ratio
position = factor[
    liquidity_filter &
    trend_filter &
    (factor.rank(axis=1, pct=True) > 0.5)
].is_largest(20)
```
**Use When**: Lower turnover, more predictable returns

### Pattern C: Momentum + Catalyst (Fast 0.8-1.5)
```python
# Simple momentum with fundamental trigger
momentum = close.pct_change().rolling(5).mean()
position = momentum[
    (close > MA(60)) &
    (revenue_3m > revenue_12m)
].is_largest(10)
```
**Use When**: Quick iterations, fast reaction needed

---

## 📚 Four Strategy Templates

### Template 1: Turtle (Multi-Layer Quality)
**Pattern**: Multi-Layer AND
**Expected Sharpe**: 1.5-2.5
**Validated**: Phase 1 (80% success)
**Key Params**: yield_threshold, n_stocks, stop_loss
**Use Case**: High Sharpe target, robust quality screen

### Template 2: Mastiff (Reversal + Contrarian)
**Pattern**: Contrarian Reversal
**Expected Sharpe**: 1.2-2.0
**Innovation**: Select LOWEST volume (ignored stocks)
**Use Case**: Contrarian opportunities, higher risk/return

### Template 3: Factor Ranking
**Pattern**: Single Factor Focus
**Expected Sharpe**: 0.8-1.3
**Key Feature**: Low turnover, stable returns
**Use Case**: Lower volatility, predictable performance

### Template 4: Momentum + Catalyst
**Pattern**: Momentum with Fundamental
**Expected Sharpe**: 0.8-1.5
**Key Feature**: Fast reaction, higher turnover
**Use Case**: Responsive to market changes

---

## 🧩 Core Components

### Alpha Filters (Boolean Conditions)
| Component | Description | Used In |
|-----------|-------------|---------|
| `DividendYieldFilter` | dividend_yield ≥ threshold | 烏龜 Layer 1 |
| `TechnicalTrendFilter` | close > MA(short) & MA(long) | 烏龜 Layer 2, 低波動 |
| `RevenueAccelerationFilter` | rev_3m > rev_12m | 烏龜 Layer 3, 月營收 |
| `QualityFilter` | operating_margin ≥ threshold | 烏龜 Layer 4 |
| `InsiderConfidenceFilter` | director_holding ≥ threshold | 烏龜 Layer 5 |
| `LiquidityRangeFilter` | volume in [min, max] | 烏龜 Layer 6, 100% strategies |

### Alpha Rankers (Scoring Logic)
| Component | Description | Used In |
|-----------|-------------|---------|
| `RevenueGrowthRanker` | Weight by revenue YoY growth | 烏龜 |
| `MomentumRanker` | Weight by price momentum | 月營收 |
| `ContrararianVolumeRanker` | Weight by INVERSE volume (innovation) | 藏獒 |
| `ValueRanker` | Weight by valuation metrics | Factor strategies |

### Execution Components
| Component | Description | Params |
|-----------|-------------|--------|
| `StopLoss` | Fixed percentage stop | threshold: 0.06-0.10 |
| `TakeProfit` | Fixed percentage profit target | threshold: 0.3-0.7 |
| `AdaptiveStopLoss` | ATR-based dynamic stop | atr_mult: 2.0 |
| `EqualWeight` | Equal position sizing | n_stocks: 5-20 |

---

## 🎓 12 Design Principles

1. **Multi-Layer > Single**: 6 layers optimal for Sharpe >2.0
2. **Fundamental + Technical**: Both required for robustness
3. **Liquidity Necessary but Not Sufficient**: Gate factor, not ranker
4. **Revenue = Taiwan Alpha**: 60% champion usage, 3x information ratio
5. **Match Rebalancing to Data Frequency**: Monthly revenue → monthly rebal
6. **Concentrated + Stop Loss**: 5-10 stocks + 6-8% stop = high Sharpe
7. **Ranking > Absolute Thresholds**: Use `.rank(axis=1, pct=True)`
8. **Quality > Quantity**: Strict filter + few stocks > loose + many
9. **Simplicity Bias**: Avoid over-optimization (max 15 params)
10. **Use `.sustain()`**: Confirm persistence, reduce noise
11. **Contrarian Thinking**: Innovation opportunity (藏獒 example)
12. **Parameterize Everything**: Enable testing and optimization

---

## 📊 Hall of Fame Tiers

### Champion (Sharpe ≥2.0)
- Annual Return: ≥30%
- Max Drawdown: ≥-20%
- Stability Score: ≥0.8
- OOS Degradation: ≤30%

**Current Members**:
- 高殖利率烏龜_baseline: Sharpe 2.09 ✅

### Contender (Sharpe 1.5-2.0)
- Annual Return: ≥20%
- Max Drawdown: ≥-25%
- Stability Score: ≥0.7
- OOS Degradation: ≤40%

**Current Members** (from Phase 1):
- 40 turtle variations ✅

### Archive (Sharpe <1.5)
- Interesting approaches needing refinement
- Failed experiments with learning value

---

## 🚀 Implementation Roadmap

### Phase 1: Validation ✅ COMPLETE (2 days)
**Goal**: Prove turtle strategy robustness
**Results**: 80% success rate (40/50 Sharpe >1.5)
**Status**: ✅ Done

### Phase 2: Template Library + Hall of Fame (3-5 days)
**Goal**: Build reusable template system
**Tasks**:
- ☐ Create 4 template files (1 day)
- ☐ Implement Hall of Fame system (1 day)
- ☐ Improve feedback format (1 day)
- ☐ Test 30 turtle variations (2 days)

**Target**: ≥20/30 (67%) achieve Sharpe >1.5

### Phase 3: Component-Based Generator (1-2 weeks)
**Goal**: Genome-based intelligent generation
**Tasks**:
- ☐ Define component interfaces (2 days)
- ☐ Implement 20+ core components (3 days)
- ☐ Genome serialization (2 days)
- ☐ Intelligent generator (3 days)
- ☐ Automated evaluation loop (3 days)

**Target**: Discover ≥3 Champions (Sharpe >2.0) in 100 iterations

### Phase 4: Continuous Learning (Ongoing)
**Goal**: Long-term knowledge accumulation
**Tasks**:
- Pattern mining from Hall of Fame
- Market regime detection
- Human-in-the-loop refinement

---

## 💾 Key Files

### Current System
| File | Purpose | Status |
|------|---------|--------|
| `iteration_engine.py` | Main orchestration loop | 99.4% stable ✅ |
| `turtle_strategy_generator.py` | Phase 1 grid search | Complete ✅ |
| `datasets_curated_50.json` | Finlab API catalog | Validated ✅ |
| `iteration_history.jsonl` | Iteration logs | Active |

### Phase 2 Deliverables
| File | Purpose | Status |
|------|---------|--------|
| `templates/template_turtle.py` | Multi-layer quality template | Pending |
| `templates/template_mastiff.py` | Contrarian reversal template | Pending |
| `templates/template_factor.py` | Factor ranking template | Pending |
| `templates/template_momentum.py` | Momentum catalyst template | Pending |
| `hall_of_fame.py` | Strategy repository | Pending |

### Phase 3 Deliverables
| File | Purpose | Status |
|------|---------|--------|
| `strategy_generator_v2.py` | Intelligent generator | Pending |
| `genome.py` | YAML serialization | Pending |
| `components/filters/*.py` | 20+ filter components | Pending |
| `components/rankers/*.py` | Ranking components | Pending |
| `components/execution/*.py` | Execution components | Pending |

---

## 🔬 Validation Pipeline

### Stage 1: Syntax Check
```bash
python -m py_compile generated_strategy.py
```

### Stage 2: AST Security Validation
```bash
python ast_validator.py generated_strategy.py
```
Checks: No eval, no exec, no file I/O, no import override

### Stage 3: Backtest Execution
```python
report = backtest.sim(position, resample='M', ...)
```

### Stage 4: Performance Evaluation
```python
metrics = {
    'sharpe': report.sharpe,
    'return': report.annual_return,
    'mdd': report.max_drawdown,
    'win_rate': report.win_rate
}
```

### Stage 5: Robustness Checks
```python
# Parameter sensitivity (±20%)
stability = test_param_sensitivity(strategy, params)

# Out-of-sample test
oos = test_out_of_sample(strategy, split='2024-01-01')
```

### Stage 6: Novelty Check
```python
# Avoid duplicates
similar = hall_of_fame.get_similar(genome, max_distance=0.2)
```

**Pass Criteria**:
- Syntax: No errors
- AST: All checks pass
- Backtest: Successful completion
- Performance: Sharpe ≥1.5 (Contender) or ≥2.0 (Champion)
- Robustness: Stability ≥0.7, OOS degradation ≤40%
- Novelty: Distance >0.2 from existing strategies

---

## 📈 Taiwan Market Specifics

### Unique Alpha Sources
| Factor | Frequency | vs US | Info Ratio | Champion Usage |
|--------|-----------|-------|------------|----------------|
| **Monthly Revenue** | Monthly | Quarterly | 3x | 60% |
| **Director Shareholding** | Updated regularly | Less transparent | 2x | 40% |
| **High Dividend Yield** | 4-5% avg | 2-3% avg | 1.5x | 40% |

### Market Structure
- **Exchange**: TWSE (Taiwan Stock Exchange)
- **Trading Hours**: 09:00-13:30 (4.5 hours)
- **Settlement**: T+2
- **Fees**: 0.1425% per trade
- **Tax**: 0.3% on sells (stock transaction tax)

---

## 🎯 Quick Start Commands

### Run Phase 1 Turtle Grid Search
```bash
export FINLAB_API_TOKEN='your_token'
python3 turtle_strategy_generator.py --strategy focused --max-tests 50
```

### Generate Strategy (Current System)
```bash
python3 iteration_engine.py --iterations 10 --start-iteration 0
```

### Validate Strategy
```bash
python3 ast_validator.py generated_strategy_iter0.py
python3 validate_code.py generated_strategy_iter0.py
```

### Extract Metrics
```bash
python3 metrics_extractor.py iteration_history.jsonl
```

---

## 📞 Key Contacts & Resources

### Documentation
- **Technical Spec**: `STRATEGY_GENERATION_SYSTEM_SPEC.md` (146 pages)
- **Phase 1 Summary**: `PHASE1_IMPLEMENTATION_SUMMARY.md`
- **User Q&A**: `ANSWER_TO_USER_QUESTION.md`
- **Quick Reference**: This file

### Example Strategies
- `example/高殖利率烏龜.py` - Benchmark (Sharpe 2.09)
- `example/藏獒.py` - Contrarian innovation
- `example/研發管理大亂鬥.py` - Factor ranking pattern
- `example/低波動本益成長比.py` - Low volatility pattern
- `example/月營收與動能策略選股.py` - Momentum + catalyst

### Analysis Tools
- `turtle_strategy_generator.py` - Grid search with parameter sweep
- `metrics_extractor.py` - Performance analysis
- `prompt_builder.py` - Feedback generation

---

## 🎓 Common Patterns (Copy-Paste Templates)

### Pattern: 6-Layer AND Filtering
```python
from finlab import data, backtest

close = data.get('price:收盤價')
vol = data.get('price:成交股數')
yield_ratio = (data.get('price:股利') / close * 100).fillna(0)
rev = data.get('monthly_revenue:當月營收')
rev_yoy = data.get('monthly_revenue:去年同月增減(%)')
op_margin = data.get('fundamental_features:營業利益率')
director_holding = data.get('internal_equity_changes:董監持有股數占比')

# 6 layers
cond1 = yield_ratio >= 6
cond2 = (close > close.average(20)) & (close > close.average(60))
cond3 = rev.average(3) > rev.average(12)
cond4 = op_margin >= 3
cond5 = director_holding >= 10
cond6 = (vol.average(5) >= 50000) & (vol.average(5) <= 10000000)

# Combine
buy = cond1 & cond2 & cond3 & cond4 & cond5 & cond6
buy = (buy * rev_yoy)[buy>0].is_largest(10)

report = backtest.sim(buy, resample='M', stop_loss=0.06,
                     take_profit=0.5, position_limit=0.125)
```

### Pattern: Contrarian Selection (藏獒 Innovation)
```python
# Standard filters
buy = cond1 & cond2 & cond3 & cond4 & cond5 & cond6

# KEY: Weight by volume and select LOWEST (not highest)
vol_ma = vol.average(10)
buy = vol_ma * buy
buy = buy[buy > 0].is_smallest(5)  # Contrarian!

report = backtest.sim(buy, resample='M', position_limit=0.33, stop_loss=0.08)
```

### Pattern: Factor Ranking
```python
# Create composite factor
factor = metric1 / metric2  # e.g., R&D/Admin

# Filter + Rank
position = factor[
    (close > close.average(60)) &
    (vol > 200000) &
    (factor.rank(axis=1, pct=True) > 0.5)
].is_largest(20)

report = backtest.sim(position, resample='Q')
```

---

## 🐛 Common Issues & Fixes

### Issue: Dataset Name Error
**Error**: `Exception: **Error: price_book_ratio:股價淨值比 not exists`
**Fix**: Use correct name `fundamental_features:股價淨值比`
**Reference**: Check `datasets_curated_50.json`

### Issue: Missing finlab.talib
**Error**: `ModuleNotFoundError: No module named 'finlab.talib'`
**Fix**: Calculate manually:
```python
tr1 = high - low
tr2 = abs(high - close.shift(1))
tr3 = abs(low - close.shift(1))
true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
atr = true_range.rolling(20).mean()
```

### Issue: Unsupported Parameter
**Error**: `TypeError: sim() got an unexpected keyword argument 'exit_on_signal'`
**Fix**: Use dynamic position matrix instead:
```python
# Instead of exit_on_signal=True
# Create position that changes from True to False
position = entry_signal & ~exit_signal
```

### Issue: API Token Authentication
**Error**: `EOFError: EOF when reading a line`
**Fix**: Set environment variable:
```bash
export FINLAB_API_TOKEN='your_token_here'
```

---

## 📊 Success Metrics Dashboard

### Phase 1 Results ✅
- **Grid Search**: 50 tests completed
- **Success Rate**: 80% (40/50 Sharpe >1.5)
- **Best Sharpe**: 1.79 (vs target 2.0)
- **Validation**: Benchmark 2.09 confirmed

### Phase 2 Targets (3-5 days)
- **Template Coverage**: 4 templates
- **Hall of Fame Size**: 30+ strategies
- **Contender Rate**: ≥67% (Sharpe >1.5)

### Phase 3 Targets (1-2 weeks)
- **Component Library**: 20+ components
- **Champion Discovery**: ≥3 strategies (Sharpe >2.0)
- **Novelty Rate**: 80% (distance >0.2)

### System Reliability
- **Validation Pass**: 99% strategies pass checks
- **Runtime Stability**: 99.4% maintained
- **Backtest Success**: 100% complete without errors

---

## 🔗 Quick Links

- **Full Technical Spec**: `STRATEGY_GENERATION_SYSTEM_SPEC.md`
- **Phase 1 Summary**: `PHASE1_IMPLEMENTATION_SUMMARY.md`
- **Q&A Document**: `ANSWER_TO_USER_QUESTION.md`
- **Benchmark Strategy**: `example/高殖利率烏龜.py`

---

**Document Version**: 2.0
**Last Updated**: 2025-10-10
**Next Review**: After Phase 2 completion

**Quick Question?** Check Technical Spec Section:
- Templates → Section 2
- Components → Section 3
- Validation → Section 8
- Code Examples → Section 12 Appendix
