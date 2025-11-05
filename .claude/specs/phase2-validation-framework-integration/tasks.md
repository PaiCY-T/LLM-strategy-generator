# Phase 2 Validation Framework Integration - Implementation Tasks

**Total Tasks**: 9 tasks (added Task 0 for validation framework verification)
**Estimated Time**: 16-24 hours (realistic estimate accounting for integration complexity)
**Priority**: P0 (3 tasks including Task 0) → P1 (3 tasks) → P2 (3 tasks)

---

## Task Organization

Tasks are organized by priority to ensure critical validations are implemented first:

- **P0 Critical** (3 tasks): Must complete before other tasks (includes validation verification)
- **P1 High** (3 tasks): Required for accurate performance assessment
- **P2 Medium** (3 tasks): Quality improvements and comprehensive reporting

---

## P0 Critical Tasks

### Task 0: Verify Validation Framework Compatibility

**Priority**: P0 CRITICAL (NEW - Must complete FIRST)
**Estimated Time**: 1.5-2 hours
**Requirements**: Infrastructure verification

**Problem**: Validation frameworks in `src/validation/` were built for generic backtesting, not tested with finlab API specifically.

**Files to Check**:
- `src/validation/data_split.py`
- `src/validation/walk_forward.py`
- `src/validation/baseline.py`
- `src/validation/bootstrap.py`
- `src/validation/multiple_comparison.py`

**Implementation Steps**:
1. Create test script `test_validation_compatibility.py`:
   ```python
   import finlab
   from finlab import data
   from finlab.backtest import sim
   from src.validation.data_split import TrainValTestSplit
   from src.validation.walk_forward import WalkForwardAnalyzer
   from src.validation.baseline import BaselineComparator
   from src.validation.bootstrap import BootstrapCI

   # Test with simple strategy
   close = data.get('price:收盤價')
   position = close > close.shift(20)

   # Test data_split compatibility
   splitter = TrainValTestSplit()
   # ... verify it works with finlab data structures

   # Test walk_forward compatibility
   analyzer = WalkForwardAnalyzer()
   # ... verify window generation works

   # Test baseline compatibility
   comparator = BaselineComparator()
   # ... verify baseline execution works

   # Test bootstrap compatibility
   bootstrap = BootstrapCI()
   # ... verify CI calculation works with finlab returns
   ```

2. Run compatibility tests and document any API mismatches
3. Create adapter layer if needed to bridge finlab ↔ validation frameworks
4. Document required data format conversions

**Testing**:
- All validation frameworks successfully execute with finlab backtests
- No import errors or API incompatibilities
- Data format conversions documented

**Success Criteria**:
- ✅ All 5 validation frameworks verified compatible with finlab
- ✅ Adapter layer created if needed
- ✅ Integration blockers identified and resolved

---

### Task 1: Add Explicit Backtest Date Range Configuration

**Priority**: P0 CRITICAL (After Task 0)
**Estimated Time**: 2-3 hours (realistic accounting for testing and edge cases)
**Requirements**: REQ-1 (all ACs)

**Problem**: Strategies currently use entire dataset (2007-2025, 18.5 years), producing misleading long-term metrics.

**Files to Modify**:
- `src/backtest/executor.py` (modify `_execute_in_process()` method)
- Strategy generation modules (inject date range into generated code)
- `config/learning_system.yaml` (add date range config section)

**Implementation Steps**:
1. Add date range parameters to `BacktestExecutor._execute_in_process()`:
   ```python
   def _execute_in_process(strategy_code, data, sim, result_queue,
                          start_date=None, end_date=None):
   ```

2. Inject date range into sim() call in execution globals:
   ```python
   execution_globals = {
       "data": data,
       "sim": sim,
       "start_date": start_date or "2018-01-01",  # UPDATED: 7-year range
       "end_date": end_date or "2024-12-31",      # UPDATED: supports all validations
       # ...
   }
   ```

3. Update strategy template to use date range:
   ```python
   # In generated strategy code
   report = sim(
       position,
       start_date=start_date,
       end_date=end_date,
       resample="Q",
       # ...
   )
   ```

4. Add YAML configuration:
   ```yaml
   backtest:
     default_start_date: "2018-01-01"  # UPDATED: supports out-of-sample split
     default_end_date: "2024-12-31"    # UPDATED: 7-year range
     # Rationale: 2018-2020 train, 2021-2022 val, 2023-2024 test
   ```

**Testing**:
- Verify all strategies specify explicit date range in sim() call
- Verify date range configurable via YAML
- Verify execution time remains <30s per strategy with 7-year range
- Test edge cases: missing dates, invalid ranges, timezone issues

**Success Criteria**:
- ✅ 100% of strategies have explicit date range
- ✅ Metrics aligned with specified period (7 years for full validation support)

---

### Task 2: Add Transaction Cost Modeling

**Priority**: P0 CRITICAL (After Task 0)
**Estimated Time**: 1.5-2 hours (realistic including dual-run comparison logic)
**Requirements**: REQ-2 (all ACs)

**Problem**: Backtests assume zero transaction costs, producing unrealistic performance.

**Files to Modify**:
- `src/backtest/executor.py` (add fee_ratio parameter)
- `run_phase2_backtest_execution.py` (report with/without fees)
- `config/learning_system.yaml` (add fee configuration)

**Implementation Steps**:
1. Add fee_ratio parameter to sim() call:
   ```python
   # In _execute_in_process()
   fee_ratio = execution_globals.get("fee_ratio", 0.003)  # UPDATED: 0.3% realistic

   # In strategy template
   report = sim(
       position,
       start_date=start_date,
       end_date=end_date,
       fee_ratio=fee_ratio,  # UPDATED: 0.3% accounts for commission + tax
       # ...
   )
   ```

2. Extract metrics with and without fees:
   ```python
   # After backtest execution
   sharpe_with_fees = stats.get('daily_sharpe', float("nan"))

   # Re-run without fees for comparison
   report_no_fees = sim(position, fee_ratio=0, ...)
   sharpe_without_fees = report_no_fees.get_stats().get('daily_sharpe')
   ```

3. Add YAML configuration with Taiwan market explanation:
   ```yaml
   backtest:
     default_fee_ratio: 0.003  # UPDATED: 0.3% realistic
     # Taiwan market costs:
     # - Commission: 0.1425% (券商手續費)
     # - Securities Tax: 0.3% (證券交易稅)
     # - Bid-ask spread: ~0.05-0.1%
     # Total: ~0.45-0.6% per round-trip
     # Conservative default: 0.3%
     report_fee_comparison: true
   ```

4. Update results JSON schema:
   ```json
   {
     "sharpe_ratio": 0.72,
     "sharpe_with_fees": 0.62,  # UPDATED: realistic fee impact
     "sharpe_without_fees": 0.72,
     "fee_impact": -0.10  # UPDATED: ~14% degradation typical
   }
   ```

**Testing**:
- Verify fee_ratio applied correctly
- Verify sharpe_with_fees < sharpe_without_fees (sanity check)
- Verify fee impact is realistic (~10-20% Sharpe degradation)
- Verify configurable via YAML
- Test with various turnover rates

**Success Criteria**:
- ✅ All strategies include realistic transaction costs
- ✅ Fee ratio reflects Taiwan market reality (0.3%)
- ✅ Fee impact clearly reported and realistic

---

## P1 High Priority Tasks

### Task 3: Integrate Out-of-Sample Validation

**Priority**: P1 HIGH
**Estimated Time**: 40-60 minutes
**Requirements**: REQ-3 (all ACs)

**Problem**: No train/test split, risk of reporting overfitted performance.

**Files to Modify**:
- `run_phase2_backtest_execution.py` (add validation workflow)
- Results JSON schema (add split metrics)

**Implementation Steps**:
1. Import existing validation module:
   ```python
   from src.validation.data_split import TrainValTestSplit
   ```

2. Configure data split:
   ```python
   splitter = TrainValTestSplit()
   periods = {
       'train': ('2018-01-01', '2020-12-31'),  # 3 years
       'val': ('2021-01-01', '2022-12-31'),    # 2 years
       'test': ('2023-01-01', '2024-12-31')    # 2 years
   }
   ```

3. Run strategy on each period:
   ```python
   for period_name, (start, end) in periods.items():
       result = executor.execute(
           strategy_code, data, sim,
           start_date=start, end_date=end
       )
       metrics[f'{period_name}_sharpe'] = result.sharpe_ratio
   ```

4. Calculate overfitting flag:
   ```python
   overfitting_ratio = metrics['test_sharpe'] / metrics['train_sharpe']
   is_overfitted = overfitting_ratio < 0.7
   ```

5. Update results JSON:
   ```json
   {
     "train_sharpe": 0.85,
     "val_sharpe": 0.78,
     "test_sharpe": 0.72,
     "overfitting_flag": false,
     "overfitting_ratio": 0.85
   }
   ```

**Testing**:
- Verify three period results differ (not identical)
- Verify overfitting flag triggers correctly
- Verify execution time < 2 minutes per strategy

**Success Criteria**:
- ✅ Test period Sharpe within 70% of train Sharpe
- ✅ Overfitted strategies identified

**Leverage**: `src/validation/data_split.py` (TrainValTestSplit class - already implemented)

---

### Task 4: Integrate Walk-Forward Analysis

**Priority**: P1 HIGH
**Estimated Time**: 45-60 minutes
**Requirements**: REQ-4 (all ACs)

**Problem**: No validation of temporal stability across market conditions.

**Files to Modify**:
- `run_phase2_backtest_execution.py` (add walk-forward workflow)
- Results JSON schema (add stability metrics)

**Implementation Steps**:
1. Import existing validation module:
   ```python
   from src.validation.walk_forward import WalkForwardAnalyzer
   ```

2. Configure walk-forward windows:
   ```python
   analyzer = WalkForwardAnalyzer(
       train_window=252,  # 1 year training
       test_window=63,    # 3 months test
       step_size=63       # Roll forward 3 months
   )
   ```

3. Execute walk-forward analysis:
   ```python
   windows = analyzer.generate_windows(data, min_windows=3)
   window_sharpes = []

   for i, (train_data, test_data) in enumerate(windows):
       result = executor.execute(strategy_code, test_data, sim)
       window_sharpes.append(result.sharpe_ratio)
   ```

4. Calculate stability score:
   ```python
   import numpy as np
   stability_score = np.std(window_sharpes) / np.mean(window_sharpes)
   is_unstable = stability_score > 0.5
   ```

5. Update results JSON:
   ```json
   {
     "walk_forward": {
       "window_sharpes": [0.68, 0.75, 0.71, 0.69],
       "mean_sharpe": 0.71,
       "stability_score": 0.35,
       "unstable_flag": false
     }
   }
   ```

**Testing**:
- Verify minimum 3 windows executed
- Verify stability score calculation correct
- Verify unstable flag triggers at threshold

**Success Criteria**:
- ✅ Stability score < 0.5 for production strategies
- ✅ Consistent performance across windows

**Leverage**: `src/validation/walk_forward.py` (WalkForwardAnalyzer class - already implemented)

---

### Task 5: Integrate Baseline Comparison

**Priority**: P1 HIGH
**Estimated Time**: 40-50 minutes
**Requirements**: REQ-5 (all ACs)

**Problem**: No benchmark to determine if strategies beat passive investing.

**Files to Modify**:
- `run_phase2_backtest_execution.py` (add baseline comparison)
- Results JSON schema (add alpha metrics)

**Implementation Steps**:
1. Import existing validation module:
   ```python
   from src.validation.baseline import BaselineComparator
   ```

2. Execute baselines (cache results):
   ```python
   comparator = BaselineComparator()
   baselines = comparator.run_baselines(
       start_date="2020-01-01",
       end_date="2023-12-31"
   )
   # Returns: {
   #   '0050_etf': {'sharpe': 0.45, 'return': 1.85},
   #   'equal_weight': {'sharpe': 0.52, 'return': 2.10},
   #   'risk_parity': {'sharpe': 0.38, 'return': 1.62}
   # }
   ```

3. Calculate sharpe_improvement for each strategy:
   ```python
   strategy_sharpe = result.sharpe_ratio
   sharpe_improvement_0050 = strategy_sharpe - baselines['0050_etf']['sharpe']
   sharpe_improvement_equal = strategy_sharpe - baselines['equal_weight']['sharpe']
   sharpe_improvement_risk_parity = strategy_sharpe - baselines['risk_parity']['sharpe']

   best_improvement = max(sharpe_improvement_0050, sharpe_improvement_equal, sharpe_improvement_risk_parity)
   beats_baseline = best_improvement > 0
   ```

4. Update classification logic:
   ```python
   # Level 3 (PROFITABLE) now requires sharpe_improvement > 0
   if sharpe > 0.5 and beats_baseline:
       classification = "Level 3: PROFITABLE"
   ```

5. Update results JSON:
   ```json
   {
     "sharpe_ratio": 0.72,
     "sharpe_improvement_vs_0050": 0.27,
     "sharpe_improvement_vs_equal_weight": 0.20,
     "sharpe_improvement_vs_risk_parity": 0.34,
     "best_sharpe_improvement": 0.34,
     "beats_baseline": true
   }
   ```

**Testing**:
- Verify baselines executed once (cached)
- Verify alpha calculation correct
- Verify classification updated

**Success Criteria**:
- ✅ Strategies beat at least one baseline
- ✅ Sharpe improvement > 0.2 for high-quality strategies

**Leverage**: `src/validation/baseline.py` (BaselineComparator class - already implemented)

---

## P2 Medium Priority Tasks

### Task 6: Integrate Bootstrap Confidence Intervals

**Priority**: P2 MEDIUM
**Estimated Time**: 30-45 minutes
**Requirements**: REQ-6 (all ACs)

**Problem**: No statistical validation of performance significance.

**Files to Modify**:
- `run_phase2_backtest_execution.py` (add bootstrap CI)
- Results JSON schema (add CI metrics)

**Implementation Steps**:
1. Import existing validation module:
   ```python
   from src.validation.bootstrap import BootstrapCI
   ```

2. Configure bootstrap:
   ```python
   bootstrap = BootstrapCI(
       block_size=21,     # 21-day blocks
       n_iterations=1000,
       confidence_level=0.95
   )
   ```

3. Calculate confidence intervals:
   ```python
   # Extract returns from backtest result
   returns = result.report.returns  # Daily returns series

   ci_sharpe = bootstrap.calculate_ci(returns, metric='sharpe')
   ci_return = bootstrap.calculate_ci(returns, metric='total_return')
   ci_drawdown = bootstrap.calculate_ci(returns, metric='max_drawdown')

   # Returns: (lower_bound, upper_bound)
   ```

4. Check statistical significance:
   ```python
   is_significant = ci_sharpe[0] > 0  # Lower bound > 0
   ```

5. Update results JSON:
   ```json
   {
     "sharpe_ratio": 0.72,
     "sharpe_ci_lower": 0.58,
     "sharpe_ci_upper": 0.86,
     "statistically_significant": true,
     "bootstrap_iterations": 1000
   }
   ```

**Testing**:
- Verify CI bounds reasonable (lower < mean < upper)
- Verify significance flag correct
- Verify execution time < 1 minute per strategy

**Success Criteria**:
- ✅ CI excludes zero for production strategies
- ✅ 95% confidence level achieved

**Leverage**: `src/validation/bootstrap.py` (BootstrapCI class - already implemented)

---

### Task 7: Integrate Multiple Comparison Correction

**Priority**: P2 MEDIUM
**Estimated Time**: 25-35 minutes
**Requirements**: REQ-7 (all ACs)

**Problem**: Testing 20+ strategies inflates false discovery rate.

**Files to Modify**:
- `run_phase2_backtest_execution.py` (add Bonferroni correction)
- Results JSON schema (add significance flags)

**Implementation Steps**:
1. Import existing validation module:
   ```python
   from src.validation.multiple_comparison import MultipleComparisonCorrector
   ```

2. Calculate adjusted alpha:
   ```python
   corrector = MultipleComparisonCorrector(method='bonferroni')
   n_strategies = 20
   adjusted_alpha = 0.05 / n_strategies  # 0.0025 for 20 strategies
   ```

3. Apply correction to each strategy:
   ```python
   # Check if CI excludes zero at adjusted alpha level
   # For 95% CI → 0.05 alpha → 0.0025 adjusted
   # Need 99.75% CI for Bonferroni with 20 tests

   bonferroni_ci = bootstrap.calculate_ci(
       returns,
       confidence_level=1 - adjusted_alpha
   )
   bonferroni_significant = bonferroni_ci[0] > 0
   ```

4. Update results JSON:
   ```json
   {
     "sharpe_ci_lower": 0.58,
     "sharpe_ci_upper": 0.86,
     "statistically_significant": true,
     "bonferroni_adjusted_alpha": 0.0025,
     "bonferroni_significant": true
   }
   ```

**Testing**:
- Verify adjusted alpha calculated correctly
- Verify significance more conservative than unadjusted
- Verify correct for different n_strategies

**Success Criteria**:
- ✅ Family-wise error rate controlled at 5%
- ✅ Robust significance testing

**Leverage**: `src/validation/multiple_comparison.py` (MultipleComparisonCorrector - already implemented)

---

### Task 8: Create Comprehensive Validation Report Generator

**Priority**: P2 MEDIUM
**Estimated Time**: 60-90 minutes
**Requirements**: REQ-8 (all ACs)

**Problem**: Validation results scattered, hard to interpret.

**Files to Create**:
- `src/validation/validation_report.py` (new file)

**Files to Modify**:
- `run_phase2_backtest_execution.py` (call report generator)

**Implementation Steps**:
1. Create ValidationReportGenerator class:
   ```python
   class ValidationReportGenerator:
       def __init__(self, results_json):
           self.results = results_json

       def generate_html_report(self, output_path):
           """Generate comprehensive HTML report with Plotly charts"""
           pass
   ```

2. Implement report sections:
   ```python
   def _generate_summary_section(self):
       # Overall statistics
       # Success rates, avg metrics, etc.

   def _generate_out_of_sample_section(self):
       # Train/val/test breakdown
       # Scatter plot: train vs test Sharpe

   def _generate_walk_forward_section(self):
       # Stability analysis
       # Timeline of window Sharpes

   def _generate_baseline_section(self):
       # Alpha vs each baseline
       # Bar chart comparison

   def _generate_significance_section(self):
       # Bootstrap CIs
       # Bonferroni results
   ```

3. Create Plotly visualizations:
   ```python
   import plotly.graph_objects as go

   # Sharpe distribution histogram
   fig1 = go.Figure(data=[go.Histogram(x=sharpe_ratios)])

   # In-sample vs out-of-sample scatter
   fig2 = go.Figure(data=[go.Scatter(
       x=train_sharpes, y=test_sharpes,
       mode='markers', name='Strategies'
   )])

   # Baseline comparison bar chart
   fig3 = go.Figure(data=[go.Bar(
       x=['0050 ETF', 'Equal Weight', 'Risk Parity', 'Avg Strategy'],
       y=[baseline_sharpes + [avg_strategy_sharpe]]
   )])
   ```

4. Generate self-contained HTML:
   ```python
   html_template = """
   <!DOCTYPE html>
   <html>
   <head>
       <title>Phase 2 Validation Report</title>
       <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
   </head>
   <body>
       <h1>Phase 2 Validation Report</h1>
       {summary_section}
       {out_of_sample_section}
       {walk_forward_section}
       {baseline_section}
       {significance_section}
   </body>
   </html>
   """
   ```

5. Integrate into execution pipeline:
   ```python
   # In run_phase2_backtest_execution.py
   from src.validation.validation_report import ValidationReportGenerator

   # After all strategies executed
   report_gen = ValidationReportGenerator(results)
   report_gen.generate_html_report('phase2_validation_report.html')
   ```

**Testing**:
- Verify all sections included
- Verify charts render correctly
- Verify report generation < 30 seconds

**Success Criteria**:
- ✅ Single HTML file with all metrics
- ✅ Interactive charts work in browser
- ✅ Report self-contained (no external dependencies)

**Leverage**: Plotly for charts, Jinja2 for templating (optional)

---

## Task Dependencies

**Dependency Graph**:
```
Task 1 (Date Range) ──┐
                      ├──> Task 3 (Out-of-Sample)
Task 2 (Fees) ────────┤
                      ├──> Task 4 (Walk-Forward)
                      │
                      ├──> Task 5 (Baseline)
                      │
                      └──> Task 6 (Bootstrap CI) ──┐
                                                    ├──> Task 7 (Bonferroni)
                                                    │
                           All Tasks ───────────────┴──> Task 8 (Report)
```

**Execution Strategy**:
1. **Wave 1** (P0): Tasks 1, 2 in PARALLEL (30-45 min)
2. **Wave 2** (P1): Tasks 3, 4, 5 in PARALLEL (40-60 min)
3. **Wave 3** (P2): Tasks 6, 7 in PARALLEL (30-45 min)
4. **Wave 4** (P2): Task 8 SEQUENTIAL (60-90 min)

**Total Time**: 16-24 hours (realistic estimate including Task 0 verification + integration complexity)

---

## Testing Strategy

### Unit Testing
- Test each validation module independently
- Mock backtest results for fast testing
- Verify edge cases (zero trades, NaN metrics)

### Integration Testing
- Run complete validation pipeline on sample strategy
- Verify all metrics present in results JSON
- Verify report generation succeeds

### Regression Testing
- Re-run 20-strategy dataset with all validations
- Compare new metrics to baseline (Phase 2 original)
- Verify realistic performance degradation with fees

### Performance Testing
- Measure execution time per strategy
- Target: <90 seconds per strategy (3x baseline acceptable)
- Identify and optimize bottlenecks

---

## Success Metrics

**Completion Criteria**:
- [ ] All 8 tasks completed
- [ ] All unit tests passing
- [ ] 20-strategy re-validation successful
- [ ] HTML report generated
- [ ] Performance target met (<90s per strategy)

**Quality Gates**:
- [ ] At least 50% of strategies pass all validations
- [ ] Test period Sharpe > 0.5 for production strategies
- [ ] Alpha > 0 vs at least one baseline
- [ ] Statistical significance with Bonferroni correction
- [ ] Stability score < 0.5 for production strategies

**Documentation**:
- [ ] README updated with validation framework usage
- [ ] Validation report interpretation guide created
- [ ] Configuration options documented
