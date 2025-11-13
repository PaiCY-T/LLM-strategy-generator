# Phase 2 Validation Framework Integration - Requirements

**Created**: 2025-10-31
**Owner**: FinLab Backtesting System
**Priority**: P0-P1 (Critical for Production Deployment)

---

## Executive Summary

After completing Phase 2 backtest execution (20 strategies, 100% success rate), critical analysis revealed misleading performance metrics due to lack of proper validation. This spec addresses integration of existing validation frameworks to ensure accurate, production-ready performance assessment.

**Key Problem**: 401% average return reported, but spans 18.5 years = only 8.8% CAGR (vs Taiwan market 4.4% CAGR). No out-of-sample testing, no baseline comparison, no transaction costs modeled.

**Key Solution**: All required validation frameworks already exist in `src/validation/`, just need integration into Phase 2 execution pipeline.

---

## Background & Context

### Discovery Process (2025-10-31)

**Phase 2 Completion**:
- Successfully executed 20 strategies with metrics extraction
- Fixed NaN metrics bug using finlab `report.get_stats()` API
- Achieved 100% execution success rate
- Results: `PHASE2_METRICS_EXTRACTION_FIX_COMPLETE.md`, `phase2_backtest_results.json`

**Critical Review** (via `mcp__zen__challenge` + Gemini 2.5 Pro):
1. **Missing Date Range**: Strategies use entire dataset (2007-2025, 18.5 years)
2. **Misleading Metrics**: 401% return / 18.5 years = 8.8% CAGR (not impressive vs market)
3. **No Out-of-Sample**: Risk of reporting overfitted results
4. **No Baseline**: Cannot determine if strategies beat market
5. **No Transaction Costs**: Unrealistic assumption

**Validation Framework Discovery** (via `mcp__zen__thinkdeep`):
- Found 6 pre-implemented validation tools in `src/validation/`:
  - `data_split.py` - Train/validation/test split
  - `walk_forward.py` - Rolling window analysis
  - `baseline.py` - 0050 ETF, Equal-Weight, Risk Parity benchmarks
  - `bootstrap.py` - Block bootstrap confidence intervals
  - `multiple_comparison.py` - Bonferroni correction
  - `backtest_validator.py` - Configuration validation
- **All tools complete and tested, just not integrated**

---

## Requirements

### REQ-1: Explicit Backtest Date Range (P0 CRITICAL)

**Problem**: Strategies currently have no date range specification, using entire available dataset (2007-2025).

**Requirement**:
- All backtest executions MUST specify explicit `start_date` and `end_date`
- Default range: 2018-01-01 to 2024-12-31 (7 years, supports all validation frameworks)
- Date range MUST be configurable via YAML configuration
- Generated strategy code MUST inject date range into `sim()` calls
- **Rationale**: 7-year range supports out-of-sample split (2018-2020 train, 2021-2022 val, 2023-2024 test) and walk-forward analysis (requires minimum 441 trading days)

**Acceptance Criteria**:
- AC-1.1: All strategies specify explicit date range in `sim()` call
- AC-1.2: Date range configurable via `config/learning_system.yaml`
- AC-1.3: Default range covers representative market conditions (bull, bear, volatile)
- AC-1.4: Execution time remains <30s per strategy with specified range

**Success Metrics**:
- 100% of strategies have explicit date range in code
- Reported performance metrics aligned with specified period length

---

### REQ-2: Transaction Cost Modeling (P0 CRITICAL)

**Problem**: Current backtests assume zero transaction costs, producing unrealistic performance.

**Requirement**:
- All backtests MUST include realistic transaction cost modeling
- Default fee ratio: 0.003 (0.3% per round-trip, accounts for commission + securities transaction tax)
- **Taiwan Market Reality**:
  - Commission: 0.1425% (券商手續費)
  - Securities Transaction Tax: 0.3% (證券交易稅) - largest component
  - Bid-ask spread: ~0.05-0.1% (depending on liquidity)
  - Total realistic cost: 0.45-0.6% per round-trip
  - Conservative default: 0.3% (fee_ratio=0.003)
- Report metrics both with and without transaction costs
- Fee ratio MUST be configurable via YAML

**Acceptance Criteria**:
- AC-2.1: `fee_ratio` parameter included in all `sim()` calls
- AC-2.2: Results JSON includes `sharpe_with_fees` and `sharpe_without_fees`
- AC-2.3: `sharpe_with_fees` < `sharpe_without_fees` (sanity check)
- AC-2.4: Fee ratio configurable via YAML with sensible default

**Success Metrics**:
- Performance metrics account for realistic trading costs
- Strategies remain profitable after fees (sharpe_with_fees > 0.5)

---

### REQ-3: Out-of-Sample Validation (P1 HIGH)

**Problem**: No temporal train/test split, risk of reporting overfitted performance.

**Requirement**:
- All strategies MUST be tested on out-of-sample data
- Data split: Train (2018-2020) → Validation (2021-2022) → Test (2023-2024)
- Test period performance MUST be reported separately
- Flag strategies with significant train/test performance degradation

**Acceptance Criteria**:
- AC-3.1: Each strategy tested on three time periods
- AC-3.2: Results JSON includes `train_sharpe`, `val_sharpe`, `test_sharpe`
- AC-3.3: Overfitting flag when `test_sharpe < 0.7 * train_sharpe`
- AC-3.4: Execution time remains reasonable (<2 minutes per strategy)

**Success Metrics**:
- Test period Sharpe within 70% of train period Sharpe (stable strategies)
- Overfitted strategies identified and flagged

**Leverage**: `src/validation/data_split.py` (TrainValTestSplit class)

---

### REQ-4: Temporal Stability Testing (P1 HIGH)

**Problem**: No validation that strategies work across different market conditions.

**Requirement**:
- All strategies MUST pass walk-forward analysis
- Configuration: 252-day train + 63-day test windows, rolling
- Minimum 3 windows for statistical validity
- Calculate stability score across windows

**Acceptance Criteria**:
- AC-4.1: Walk-forward analysis performed on all strategies
- AC-4.2: Results include `stability_score` (CV of window Sharpes)
- AC-4.3: Flag strategies with `stability_score > 0.5` (unstable)
- AC-4.4: Report Sharpe for each individual window

**Success Metrics**:
- Stability score < 0.5 for production-ready strategies
- Consistent performance across multiple market regimes

**Leverage**: `src/validation/walk_forward.py` (WalkForwardAnalyzer class)

---

### REQ-5: Baseline Comparison (P1 HIGH)

**Problem**: No benchmark comparison to determine if strategies beat passive investing.

**Requirement**:
- All strategies MUST be compared against market baselines
- Baselines: Buy-and-Hold 0050 ETF, Equal-Weight Top 50, Risk Parity
- Calculate Sharpe improvement (NOT traditional alpha) for each baseline
- **Metric Definition**: `sharpe_improvement = strategy_sharpe - baseline_sharpe`
- **Note**: This is NOT financial alpha (excess return over beta-adjusted market return), but simpler Sharpe difference for practical comparison
- Require positive sharpe_improvement vs at least one baseline for "PROFITABLE" classification

**Acceptance Criteria**:
- AC-5.1: Three baselines executed for comparison period
- AC-5.2: Results include `sharpe_improvement_vs_0050`, `sharpe_improvement_vs_equal_weight`, `sharpe_improvement_vs_risk_parity`
- AC-5.3: Classification Level 3 (PROFITABLE) requires `sharpe_improvement > 0` vs best baseline
- AC-5.4: Baseline results cached for reuse across strategies

**Success Metrics**:
- Strategies beat at least one passive baseline
- Sharpe improvement > 0.2 for high-quality strategies (meaningful outperformance)

**Leverage**: `src/validation/baseline.py` (BaselineComparator class)

---

### REQ-6: Statistical Significance Testing (P2 MEDIUM)

**Problem**: No statistical validation that performance is not due to luck.

**Requirement**:
- Calculate bootstrap confidence intervals for key metrics
- Configuration: Block bootstrap, 21-day blocks, 1000 iterations, 95% CI
- Report confidence intervals for Sharpe ratio, total return, max drawdown
- Flag strategies with confidence intervals including zero

**Acceptance Criteria**:
- AC-6.1: Bootstrap CI calculated for all strategies
- AC-6.2: Results include `sharpe_ci_lower`, `sharpe_ci_upper`
- AC-6.3: Flag strategies where CI includes 0 (not statistically significant)
- AC-6.4: Bootstrap execution time < 1 minute per strategy

**Success Metrics**:
- Confidence intervals exclude zero for production strategies
- Statistical significance at 95% confidence level

**Leverage**: `src/validation/bootstrap.py` (BootstrapCI class)

---

### REQ-7: Multiple Comparison Correction (P2 MEDIUM)

**Problem**: Testing 20+ strategies increases false discovery rate.

**Requirement**:
- Apply multiple comparison correction to all strategy tests
- Method: Bonferroni correction
- Adjusted alpha: 0.05 / n_strategies
- Flag strategies significant at adjusted alpha level

**Acceptance Criteria**:
- AC-7.1: Bonferroni correction applied to all tests
- AC-7.2: Adjusted alpha calculated correctly
- AC-7.3: Results include `bonferroni_significant` boolean
- AC-7.4: Report both unadjusted and adjusted significance

**Success Metrics**:
- False discovery rate controlled at 5% family-wise
- Statistically robust strategy selection

**Leverage**: `src/validation/multiple_comparison.py` (MultipleComparisonCorrector class)

---

### REQ-8: Comprehensive Validation Reporting (P2 MEDIUM)

**Problem**: Validation results scattered across multiple outputs.

**Requirement**:
- Generate unified HTML validation report
- Include all validation metrics and visualizations
- Interactive charts using Plotly
- Report MUST be self-contained (single HTML file)

**Acceptance Criteria**:
- AC-8.1: Single HTML report with all validation metrics
- AC-8.2: Sections: out-of-sample, walk-forward, baseline, bootstrap CI, Bonferroni
- AC-8.3: Interactive Plotly charts: Sharpe distribution, in-sample vs out-of-sample, baseline comparison
- AC-8.4: Report generation time < 30 seconds

**Success Metrics**:
- All validation metrics included in single report
- Report viewable in any web browser without dependencies

---

## Non-Functional Requirements

### NFR-1: Performance

- Validation framework integration MUST NOT increase execution time excessively
- Target: <300 seconds (5 minutes) per strategy including all validations
- **Realistic Breakdown**:
  - Out-of-sample (3 periods): ~75s
  - Walk-forward (3-4 windows): ~80s
  - Bootstrap (1000 iterations): ~50s
  - Baseline comparison (cached): ~2s
  - Total: ~207s average, 300s conservative buffer
- Validation tools MUST use cached results where possible
- **Optimization Strategies**: Baseline caching, parallel walk-forward windows, adaptive bootstrap iterations

### NFR-2: Reliability

- Validation framework MUST handle edge cases gracefully
- Failed validations MUST NOT block strategy execution
- Validation errors MUST be logged with full context

### NFR-3: Maintainability

- Validation configuration MUST be centralized in YAML
- Validation modules MUST be independently testable
- Code MUST reuse existing `src/validation/` implementations

### NFR-4: Usability

- Validation reports MUST be human-readable
- Validation failures MUST include actionable recommendations
- Validation metrics MUST be clearly documented

---

## Dependencies

**Required Completions**:
- Phase 2 backtest execution (COMPLETE ✅)
- Metrics extraction fix (COMPLETE ✅)
- 20-strategy validation dataset (COMPLETE ✅)

**Existing Infrastructure** (Ready to Use):
- `src/validation/data_split.py` ✅
- `src/validation/walk_forward.py` ✅
- `src/validation/baseline.py` ✅
- `src/validation/bootstrap.py` ✅
- `src/validation/multiple_comparison.py` ✅
- `src/validation/backtest_validator.py` ✅

---

## Out of Scope

- Creating new validation algorithms (all exist)
- UI/dashboard for validation results (HTML report sufficient)
- Real-time validation during strategy generation
- Validation result persistence in database

---

## Success Criteria

**Phase Complete When**:
1. ✅ All 8 tasks completed
2. ✅ All P0 and P1 requirements met
3. ✅ 20-strategy re-validation with all frameworks
4. ✅ HTML validation report generated
5. ✅ Performance metrics realistic and defendable

**Quality Gate**:
- At least 50% of strategies pass all validations
- Test period Sharpe > 0.5 for production strategies
- Alpha > 0 vs at least one baseline
- Statistical significance with Bonferroni correction
