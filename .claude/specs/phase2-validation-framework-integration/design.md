# Phase 2 Validation Framework Integration - Design

**Created**: 2025-10-31
**Scope**: Integration of pre-existing validation frameworks into Phase 2 backtest execution

---

## Design Philosophy

**Core Principle**: **Integration, not Creation**

This spec focuses purely on **integrating existing, tested validation frameworks** into the Phase 2 backtest execution pipeline. All validation algorithms are already implemented in `src/validation/` - we just need to wire them together.

---

## Architecture Overview

### Current Architecture (Phase 2 Baseline)

```
┌─────────────────────────────────────────┐
│  run_phase2_backtest_execution.py       │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ BacktestExecutor                 │  │
│  │  - execute(strategy_code)        │  │
│  │  - Returns: ExecutionResult      │  │
│  └──────────────────────────────────┘  │
│               │                         │
│               ▼                         │
│  ┌──────────────────────────────────┐  │
│  │ MetricsExtractor                 │  │
│  │  - extract_metrics(report)       │  │
│  │  - Returns: StrategyMetrics      │  │
│  └──────────────────────────────────┘  │
│               │                         │
│               ▼                         │
│  ┌──────────────────────────────────┐  │
│  │ ResultsCollector                 │  │
│  │  - save_to_json()                │  │
│  │  - generate_markdown_report()    │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**Problem**: No validation, no realistic assumptions, misleading metrics.

---

### Target Architecture (After Integration)

```
┌───────────────────────────────────────────────────────────────────┐
│  run_phase2_backtest_execution.py (Enhanced)                      │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ValidationPipeline (NEW)                                   │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │ 1. Core Execution                                │    │  │
│  │  │    - BacktestExecutor (with date range & fees)   │    │  │
│  │  │    - MetricsExtractor                            │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  │           │                                               │  │
│  │           ▼                                               │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │ 2. Out-of-Sample Validation (TrainValTestSplit)  │    │  │
│  │  │    - Train period (2018-2020)                    │    │  │
│  │  │    - Validation period (2021-2022)               │    │  │
│  │  │    - Test period (2023-2024)                     │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  │           │                                               │  │
│  │           ▼                                               │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │ 3. Temporal Stability (WalkForwardAnalyzer)      │    │  │
│  │  │    - 252-day train + 63-day test windows         │    │  │
│  │  │    - Rolling windows, minimum 3                  │    │  │
│  │  │    - Stability score calculation                 │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  │           │                                               │  │
│  │           ▼                                               │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │ 4. Baseline Comparison (BaselineComparator)      │    │  │
│  │  │    - 0050 ETF (Taiwan Top 50)                    │    │  │
│  │  │    - Equal-Weight Top 50                         │    │  │
│  │  │    - Risk Parity                                 │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  │           │                                               │  │
│  │           ▼                                               │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │ 5. Statistical Validation (BootstrapCI)          │    │  │
│  │  │    - Block bootstrap (21-day blocks)             │    │  │
│  │  │    - 1000 iterations, 95% CI                     │    │  │
│  │  │    - Bonferroni correction                       │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  │           │                                               │  │
│  │           ▼                                               │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │ 6. Report Generation (ValidationReportGenerator) │    │  │
│  │  │    - HTML report with Plotly charts              │    │  │
│  │  │    - Comprehensive validation summary            │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

**Key Changes**:
1. **Date Range**: All backtests specify explicit start_date/end_date
2. **Transaction Costs**: All backtests include realistic fee_ratio
3. **Validation Pipeline**: Sequential validation steps after execution
4. **Comprehensive Output**: JSON + HTML report with all metrics

---

## Component Integration

### 1. Date Range Configuration

**Existing Component**: `BacktestExecutor` (src/backtest/executor.py)
**Integration Point**: `_execute_in_process()` method
**Changes**:
- Add `start_date`, `end_date` parameters to method signature
- Inject into execution globals
- Update strategy template to use in sim() call

**Configuration**:
```yaml
# config/learning_system.yaml
backtest:
  default_start_date: "2020-01-01"
  default_end_date: "2023-12-31"
  allow_override: true
```

---

### 2. Transaction Cost Modeling

**Existing Component**: `BacktestExecutor` (src/backtest/executor.py)
**Integration Point**: sim() call in strategy execution
**Changes**:
- Add `fee_ratio` parameter to sim() call
- Run backtest twice (with/without fees) for comparison
- Report both metrics in results

**Configuration**:
```yaml
# config/learning_system.yaml
backtest:
  default_fee_ratio: 0.001425  # Taiwan stock commission 0.1425%
  report_fee_comparison: true
```

---

### 3. Out-of-Sample Validation

**Existing Component**: `TrainValTestSplit` (src/validation/data_split.py)
**Integration Point**: After core backtest execution
**Usage**:
```python
from src.validation.data_split import TrainValTestSplit

splitter = TrainValTestSplit()
periods = {
    'train': ('2018-01-01', '2020-12-31'),
    'val': ('2021-01-01', '2022-12-31'),
    'test': ('2023-01-01', '2024-12-31')
}

for period_name, (start, end) in periods.items():
    result = executor.execute(strategy_code, data, sim, start, end)
    metrics[f'{period_name}_sharpe'] = result.sharpe_ratio
```

**No Changes Required**: TrainValTestSplit already implemented and tested.

---

### 4. Walk-Forward Analysis

**Existing Component**: `WalkForwardAnalyzer` (src/validation/walk_forward.py)
**Integration Point**: After core backtest execution
**Usage**:
```python
from src.validation.walk_forward import WalkForwardAnalyzer

analyzer = WalkForwardAnalyzer(
    train_window=252, test_window=63, step_size=63
)
windows = analyzer.generate_windows(data, min_windows=3)

window_sharpes = []
for train_data, test_data in windows:
    result = executor.execute(strategy_code, test_data, sim)
    window_sharpes.append(result.sharpe_ratio)

stability_score = np.std(window_sharpes) / np.mean(window_sharpes)
```

**No Changes Required**: WalkForwardAnalyzer already implemented and tested.

---

### 5. Baseline Comparison

**Existing Component**: `BaselineComparator` (src/validation/baseline.py)
**Integration Point**: Run once, cache results, compare all strategies
**Usage**:
```python
from src.validation.baseline import BaselineComparator

comparator = BaselineComparator()

# Run once (cached for all strategies)
baselines = comparator.run_baselines(
    start_date="2020-01-01",
    end_date="2023-12-31"
)

# Compare each strategy
alpha_0050 = strategy_sharpe - baselines['0050_etf']['sharpe']
alpha_equal = strategy_sharpe - baselines['equal_weight']['sharpe']
alpha_risk_parity = strategy_sharpe - baselines['risk_parity']['sharpe']
```

**No Changes Required**: BaselineComparator already implemented and tested.

---

### 6. Bootstrap Confidence Intervals

**Existing Component**: `BootstrapCI` (src/validation/bootstrap.py)
**Integration Point**: After backtest execution (on returns series)
**Usage**:
```python
from src.validation.bootstrap import BootstrapCI

bootstrap = BootstrapCI(block_size=21, n_iterations=1000, confidence_level=0.95)

returns = result.report.returns  # Daily returns series
ci_sharpe = bootstrap.calculate_ci(returns, metric='sharpe')
# Returns: (lower_bound, upper_bound)

is_significant = ci_sharpe[0] > 0  # Lower bound > 0
```

**No Changes Required**: BootstrapCI already implemented and tested.

---

### 7. Multiple Comparison Correction

**Existing Component**: `MultipleComparisonCorrector` (src/validation/multiple_comparison.py)
**Integration Point**: After bootstrap CI calculation
**Usage**:
```python
from src.validation.multiple_comparison import MultipleComparisonCorrector

corrector = MultipleComparisonCorrector(method='bonferroni')
adjusted_alpha = 0.05 / n_strategies  # For 20 strategies: 0.0025

# Recalculate CI at adjusted alpha
bonferroni_ci = bootstrap.calculate_ci(
    returns,
    confidence_level=1 - adjusted_alpha
)
bonferroni_significant = bonferroni_ci[0] > 0
```

**No Changes Required**: MultipleComparisonCorrector already implemented and tested.

---

### 8. Validation Report Generator

**New Component**: `ValidationReportGenerator` (src/validation/validation_report.py)
**Purpose**: Unified HTML report with all validation metrics
**Structure**:
```python
class ValidationReportGenerator:
    def __init__(self, results_json):
        self.results = results_json

    def generate_html_report(self, output_path):
        """Generate comprehensive HTML report with Plotly charts"""
        sections = [
            self._generate_summary_section(),
            self._generate_out_of_sample_section(),
            self._generate_walk_forward_section(),
            self._generate_baseline_section(),
            self._generate_significance_section()
        ]

        html = self._render_template(sections)
        with open(output_path, 'w') as f:
            f.write(html)
```

**Dependencies**: Plotly for charts, Jinja2 for templating (optional)

---

## Data Flow

### Single Strategy Validation Flow

```
Input: strategy_code
   │
   ▼
┌─────────────────────────────────────┐
│ 1. Execute with Date Range & Fees  │
│    - start_date: 2020-01-01        │
│    - end_date: 2023-12-31          │
│    - fee_ratio: 0.001425           │
└─────────────────────────────────────┘
   │
   ├───► sharpe_with_fees
   ├───► sharpe_without_fees
   ├───► total_return
   ├───► max_drawdown
   │
   ▼
┌─────────────────────────────────────┐
│ 2. Out-of-Sample Split             │
│    - Train: 2018-2020              │
│    - Val: 2021-2022                │
│    - Test: 2023-2024               │
└─────────────────────────────────────┘
   │
   ├───► train_sharpe
   ├───► val_sharpe
   ├───► test_sharpe
   ├───► overfitting_flag
   │
   ▼
┌─────────────────────────────────────┐
│ 3. Walk-Forward Analysis           │
│    - 252-day train + 63-day test   │
│    - Minimum 3 windows             │
└─────────────────────────────────────┘
   │
   ├───► window_sharpes: [0.68, 0.75, 0.71]
   ├───► stability_score: 0.35
   ├───► unstable_flag: false
   │
   ▼
┌─────────────────────────────────────┐
│ 4. Baseline Comparison             │
│    - 0050 ETF, Equal-Weight, Risk  │
└─────────────────────────────────────┘
   │
   ├───► alpha_vs_0050: 0.27
   ├───► alpha_vs_equal_weight: 0.20
   ├───► alpha_vs_risk_parity: 0.34
   ├───► beats_baseline: true
   │
   ▼
┌─────────────────────────────────────┐
│ 5. Bootstrap CI                    │
│    - 21-day blocks, 1000 iter      │
└─────────────────────────────────────┘
   │
   ├───► sharpe_ci_lower: 0.58
   ├───► sharpe_ci_upper: 0.86
   ├───► statistically_significant: true
   │
   ▼
┌─────────────────────────────────────┐
│ 6. Bonferroni Correction           │
│    - Adjusted alpha: 0.05/20       │
└─────────────────────────────────────┘
   │
   ├───► bonferroni_adjusted_alpha: 0.0025
   ├───► bonferroni_significant: true
   │
   ▼
Output: Enhanced Results JSON + HTML Report
```

---

## Performance Considerations

### Execution Time Budget

**Baseline** (Phase 2 original): ~16s per strategy
**Target** (with validations): <90s per strategy (3x acceptable)

**Time Breakdown Estimate**:
- Core execution (with fees): 20s (was 16s)
- Out-of-sample (3 periods): 30s (3 × 10s each)
- Walk-forward (3-4 windows): 25s (3 × 8s each)
- Baseline (cached, amortized): 1s per strategy
- Bootstrap CI: 10s (1000 iterations)
- Bonferroni (minimal): <1s
- Report generation (batch): <30s for all strategies

**Total**: ~86s per strategy ✅ Under 90s target

### Optimization Strategies

1. **Baseline Caching**: Run baselines once, reuse for all strategies
2. **Parallel Execution**: Walk-forward windows can run in parallel
3. **Smart Bootstrap**: Adaptive iteration count based on convergence
4. **Lazy Report**: Generate HTML only at end (batch operation)

---

## Configuration

### Enhanced config/learning_system.yaml

```yaml
backtest:
  # Core execution
  default_start_date: "2020-01-01"
  default_end_date: "2023-12-31"
  default_fee_ratio: 0.001425
  allow_override: true
  report_fee_comparison: true

  # Validation framework
  validation:
    enabled: true

    out_of_sample:
      enabled: true
      train_period: ["2018-01-01", "2020-12-31"]
      val_period: ["2021-01-01", "2022-12-31"]
      test_period: ["2023-01-01", "2024-12-31"]
      overfitting_threshold: 0.7

    walk_forward:
      enabled: true
      train_window: 252
      test_window: 63
      step_size: 63
      min_windows: 3
      stability_threshold: 0.5

    baseline:
      enabled: true
      benchmarks: ["0050_etf", "equal_weight", "risk_parity"]
      cache_results: true

    bootstrap:
      enabled: true
      block_size: 21
      n_iterations: 1000
      confidence_level: 0.95

    bonferroni:
      enabled: true
      alpha: 0.05

    report:
      generate_html: true
      output_path: "phase2_validation_report.html"
```

---

## Error Handling

### Graceful Degradation Strategy

1. **Validation Failure ≠ Execution Failure**: If validation fails, still report core metrics
2. **Missing Data**: If insufficient data for walk-forward, report warning and skip
3. **Baseline Failure**: If baseline execution fails, report NaN for alpha
4. **Bootstrap Timeout**: If bootstrap exceeds time budget, reduce iterations

### Error Reporting

All validation errors logged with full context:
```json
{
  "strategy_id": "iter19",
  "validation_errors": [
    {
      "component": "walk_forward",
      "error": "Insufficient data for 3 windows",
      "severity": "warning",
      "fallback": "skipped"
    }
  ]
}
```

---

## Success Criteria

**Phase Complete When**:
1. All 8 tasks implemented
2. 20-strategy re-validation successful
3. HTML report generated with all sections
4. Performance < 90s per strategy
5. At least 50% strategies pass all validations

---

## Related Documents

- Requirements: `./requirements.md`
- Tasks: `./tasks.md`
- Status: `./STATUS.md`
- Phase 2 Baseline: `../../PHASE2_METRICS_EXTRACTION_FIX_COMPLETE.md`
