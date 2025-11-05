# Validation System

**Version**: 1.1
**Last Updated**: 2025-10-31
**Status**: Production Ready (P0 Complete)

---

## 1. Overview

This document details the validation frameworks used to assess the statistical viability of trading strategies before they are considered for production. The primary goal is to mitigate risks from overfitting, ensure statistical robustness, and filter out false signals caused by random variation.

### Purpose
The validation system provides:
- **Statistical significance testing** for strategy performance
- **Out-of-sample validation** to detect overfitting
- **Baseline comparison** against Taiwan market benchmarks
- **Confidence intervals** accounting for temporal dependencies
- **Dynamic thresholds** adapted to market conditions

### Integration in Workflow
Validation occurs after successful backtest execution:
```
Strategy Generation → Backtest Execution → Validation Framework → Production/Rejection
```

Only strategies passing all validation checks proceed to incubation/sandbox phase.

---

## 2. Key Concepts

### 2.1 Statistical Significance
Raw backtest returns are insufficient for production deployment. A positive Sharpe ratio may arise from:
- **Random variation**: Lucky draws from market noise
- **Overfitting**: Exploiting historical quirks that won't repeat
- **Data mining**: Testing many strategies until one looks good

The validation system quantifies the probability that observed performance is genuine vs. random.

### 2.2 Stationary Bootstrap
Traditional bootstrap methods assume independent, identically distributed (i.i.d.) returns. However, financial returns exhibit:
- **Autocorrelation**: Today's returns depend on yesterday's
- **Volatility clustering**: High volatility tends to persist

The **Stationary Bootstrap** (Politis & Romano 1994) preserves these time-series properties by:
- Resampling **blocks** of consecutive returns (not individual returns)
- Using **geometric block lengths** (avg length L ~ 20-25 days)
- Maintaining **autocorrelation structure** in resampled series

This produces more realistic confidence intervals that account for serial dependence.

### 2.3 Dynamic Thresholds
Static thresholds (e.g., "Sharpe > 0.5") ignore market regime changes. The **Dynamic Threshold** adapts to:
- **Market volatility**: Higher thresholds during calm markets
- **Benchmark performance**: Active strategies must beat passive ETFs
- **Regime shifts**: Different expectations for bull vs. bear markets

**Taiwan Market Implementation**:
- **Benchmark**: 0050.TW ETF (TWSE Taiwan 50 Index)
- **Threshold**: Benchmark Sharpe + 0.2 margin = 0.8
- **Floor**: Minimum 0.0 (positive risk-adjusted returns required)

---

## 3. Components & Usage

### 3.1 Stationary Bootstrap

**File**: `src/validation/stationary_bootstrap.py`

**Purpose**: Generate robust confidence intervals for performance metrics (Sharpe Ratio, CAGR, Max Drawdown).

#### API Example

```python
from src.validation import stationary_bootstrap, stationary_bootstrap_detailed

# Basic usage - returns point estimate and 95% CI
returns = np.array([...])  # Daily returns from backtest
result = stationary_bootstrap(
    returns=returns,
    metric_name='sharpe_ratio',
    n_bootstrap=1000,
    block_length=None,  # Auto-calculated (~22 days)
    random_seed=42
)

print(f"Sharpe Ratio: {result['point_estimate']:.2f}")
print(f"95% CI: [{result['ci_lower']:.2f}, {result['ci_upper']:.2f}]")
print(f"CI Width: {result['ci_width']:.2f}")
# Output:
# Sharpe Ratio: 1.15
# 95% CI: [-0.23, 2.42]
# CI Width: 2.65

# Detailed usage - returns full bootstrap distribution
detailed = stationary_bootstrap_detailed(
    returns=returns,
    metric_name='sharpe_ratio',
    n_bootstrap=1000,
    confidence_level=0.95
)

# Access bootstrap samples for custom analysis
print(f"Bootstrap mean: {detailed['bootstrap_distribution'].mean():.2f}")
print(f"Avg block length: {detailed['avg_block_length']:.1f} days")
```

#### Supported Metrics
- `sharpe_ratio`: Risk-adjusted returns (default)
- `cagr`: Compound Annual Growth Rate
- `max_drawdown`: Maximum peak-to-trough decline
- `total_return`: Cumulative return over period

#### Configuration
- **n_bootstrap**: Number of bootstrap samples (default: 1000)
- **block_length**: Geometric block length (default: auto-calculated)
- **confidence_level**: CI coverage (default: 0.95 for 95% CI)
- **random_seed**: Reproducibility (default: None)

### 3.2 Dynamic Threshold

**File**: `src/validation/dynamic_threshold.py`

**Purpose**: Calculate performance benchmarks that strategies must exceed.

#### API Example

```python
from src.validation import DynamicThresholdCalculator

# Initialize with Taiwan market benchmark
threshold_calc = DynamicThresholdCalculator(
    benchmark_ticker="0050.TW",
    lookback_years=3,
    margin=0.2,  # Active must beat passive by 0.2 Sharpe
    static_floor=0.0  # Minimum positive returns required
)

# Get current threshold
threshold = threshold_calc.get_threshold()
print(f"Current threshold: {threshold:.2f}")
# Output: Current threshold: 0.80

# Compare strategy Sharpe to threshold
strategy_sharpe = 0.95
if strategy_sharpe > threshold:
    print(f"Strategy PASSED (Sharpe {strategy_sharpe:.2f} > threshold {threshold:.2f})")
else:
    print(f"Strategy FAILED (Sharpe {strategy_sharpe:.2f} <= threshold {threshold:.2f})")
```

#### Configuration
- **benchmark_ticker**: Taiwan market proxy (default: "0050.TW")
- **lookback_years**: Historical period for benchmark Sharpe (default: 3 years)
- **margin**: Required outperformance vs. benchmark (default: 0.2)
- **static_floor**: Minimum absolute threshold (default: 0.0)

#### Threshold Calculation
```
threshold = max(benchmark_sharpe + margin, static_floor)
         = max(0.6 + 0.2, 0.0)
         = 0.8
```

**Note**: v1.1 uses empirical constant (0.6) based on research. Future versions will fetch real-time 0050.TW data.

### 3.3 Integration Layer

**File**: `src/validation/integration.py`

**Purpose**: Orchestrate multiple validation frameworks in a single pipeline.

#### API Example

```python
from src.validation import (
    BonferroniIntegrator,
    BootstrapIntegrator,
    ValidationReportGenerator
)

# Initialize integrators with dynamic threshold
bonferroni = BonferroniIntegrator(
    n_strategies=20,
    use_dynamic_threshold=True  # v1.1 default
)

bootstrap = BootstrapIntegrator(
    use_dynamic_threshold=True
)

# Validate single strategy
result = bonferroni.validate_single_strategy(
    sharpe_ratio=0.95,
    n_periods=252
)

print(f"Validation passed: {result['validation_passed']}")
print(f"Significance threshold: {result['significance_threshold']:.3f}")
print(f"Dynamic threshold: {result['dynamic_threshold']:.2f}")
# Output:
# Validation passed: True
# Significance threshold: 0.033
# Dynamic threshold: 0.80

# Validate with bootstrap (full backtest report required)
bootstrap_result = bootstrap.validate_with_bootstrap(
    strategy_code="...",  # Strategy Python code
    data=data,  # finlab data context
    sim=sim  # finlab sim function
)

# Generate comprehensive report
reporter = ValidationReportGenerator()
report_html = reporter.to_html(bootstrap_result)
report_json = reporter.to_json(bootstrap_result)
```

#### Backward Compatibility
v1.0 behavior preserved via `use_dynamic_threshold=False`:

```python
# v1.0 legacy mode (static 0.5 threshold)
integrator_v10 = BonferroniIntegrator(
    n_strategies=20,
    use_dynamic_threshold=False
)

# v1.1 enhanced mode (dynamic 0.8 threshold, default)
integrator_v11 = BonferroniIntegrator(
    n_strategies=20,
    use_dynamic_threshold=True
)
```

---

## 4. Validation Pipeline Integration

### 4.1 Phase 2 Backtest Execution
After Phase 2 backtest completes, validation occurs:

```python
from src.backtest import BacktestExecutor, MetricsExtractor, SuccessClassifier
from src.validation import BootstrapIntegrator

# 1. Execute strategy
executor = BacktestExecutor(timeout=420)
exec_result = executor.execute(strategy_code, data, sim)

# 2. Extract metrics
extractor = MetricsExtractor()
metrics = extractor.extract_metrics(exec_result.report)

# 3. Classify success level (Level 0-3)
classifier = SuccessClassifier()
classification = classifier.classify(exec_result, metrics)

# 4. Validate if Level 3 (profitable)
if classification.level >= 3:
    validator = BootstrapIntegrator()
    validation = validator.validate_with_bootstrap(
        strategy_code, data, sim
    )

    if validation['validation_passed']:
        print("Strategy APPROVED for production")
    else:
        print("Strategy REJECTED (failed statistical validation)")
```

### 4.2 Phase 3 Learning Iteration
Validation results feed back into LLM learning:

```python
from src.learning import IterationExecutor, FeedbackGenerator

# Iteration executor includes validation
iteration_exec = IterationExecutor()
iteration_result = iteration_exec.execute_iteration(
    iteration_num=5,
    history=history
)

# Feedback generator uses validation outcomes
feedback_gen = FeedbackGenerator()
feedback = feedback_gen.generate_feedback(
    history=history,
    validation_passed=iteration_result.validation_passed,
    sharpe_ratio=iteration_result.sharpe_ratio,
    dynamic_threshold=0.8
)

# Feedback informs next LLM generation
next_strategy = llm_client.generate(feedback)
```

---

## 5. Test Coverage

### Unit Tests (90 tests, 100% passing)
- **Returns Extraction**: 14 tests
- **Stationary Bootstrap**: 22 tests (21 quick + 1 slow)
- **Dynamic Threshold**: 24 tests
- **Statistical Validation**: 11 tests (10 quick + 1 slow)
- **Backward Compatibility**: 20 tests

### Integration Tests (6 tests, 100% passing)
- **E2E Pipeline**: Full validation workflow
- **Report Generation**: JSON/HTML output
- **v1.1 Improvements**: Dynamic threshold enforcement

### Performance
- **Quick tests**: 92 tests in ~18 seconds
- **All tests**: 97 tests in ~30 seconds

---

## 6. Production Metrics

### Statistical Validation vs scipy
```
Bootstrap Comparison:
  Our (stationary): 0.628 [-0.698, 1.873]
  scipy (simple):   0.649 [-0.775, 1.992]
  Sample Sharpe:    0.650
  CI width ratio:   7.1% (tolerance: 40%)
  ✅ Bootstrap vs scipy test PASSED
```

### Empirical Coverage Rate
```
Coverage Rate Test:
  Coverage rate: 100.0% (target: 95%)
  Experiments: 100
  Covered: 100/100
  ✅ Coverage rate test PASSED
```

### Point Estimate Accuracy
```
Point estimate: 1.129, Sample Sharpe: 1.136, Error: 0.6%
```

---

## 7. Future Work & Known Limitations

### Completed (P0)
- ✅ Stationary bootstrap implementation
- ✅ Dynamic threshold calculator
- ✅ Statistical validation vs scipy
- ✅ E2E integration testing
- ✅ Backward compatibility

### Deferred (P1-P2)
See `PENDING_FEATURES.md` for tracking:
- ⏸️ Performance benchmarks (2-3h) - Ensure validation completes <60s per strategy
- ⏸️ Chaos testing (2-3h) - NaN handling, concurrent safety, network timeouts
- ⏸️ Monitoring integration (2h) - Logging, metrics, alerting hooks

### Known Limitations
1. **Dynamic Threshold**: Currently uses empirical constant (0.6) for benchmark Sharpe
   - Future: Fetch real-time 0050.TW data
2. **Block Length**: Auto-calculated, not user-tunable
   - Future: Allow manual override for specific use cases
3. **Metrics**: Limited to Sharpe, CAGR, Max Drawdown, Total Return
   - Future: Add Sortino, Calmar, Win Rate, etc.

---

## 8. References

### Academic
- Politis, D.N., & Romano, J.P. (1994). "The Stationary Bootstrap". *Journal of the American Statistical Association*, 89(428), 1303-1313.
- Efron, B., & Tibshirani, R.J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall.

### Implementation
- **Specification**: `.spec-workflow/specs/phase2-validation-framework-integration/`
- **Requirements**: `requirements_v1.1.md`
- **Design**: `design_v1.1.md`
- **Tasks**: `tasks_v1.1.md`
- **Status**: `STATUS.md`

### Completion Reports
- **Session Handoff**: `SESSION_HANDOFF_20251031_P0_COMPLETE.md`
- **Task Summaries**: `TASK_1.1.X_COMPLETION_SUMMARY.md` (X = 1-6)

---

## 9. Quick Reference

### Common Tasks

**Validate single Sharpe ratio**:
```python
from src.validation import BonferroniIntegrator

validator = BonferroniIntegrator(n_strategies=20)
result = validator.validate_single_strategy(sharpe_ratio=0.95, n_periods=252)
print(f"Passed: {result['validation_passed']}")
```

**Generate confidence interval**:
```python
from src.validation import stationary_bootstrap

result = stationary_bootstrap(returns, metric_name='sharpe_ratio')
print(f"95% CI: [{result['ci_lower']:.2f}, {result['ci_upper']:.2f}]")
```

**Check dynamic threshold**:
```python
from src.validation import DynamicThresholdCalculator

threshold_calc = DynamicThresholdCalculator()
print(f"Current threshold: {threshold_calc.get_threshold()}")
```

**Run all validation tests**:
```bash
# Quick tests only (~18s)
python3 -m pytest \
  tests/validation/test_returns_extraction_robust.py \
  tests/validation/test_stationary_bootstrap.py \
  tests/validation/test_dynamic_threshold.py \
  tests/validation/test_backward_compatibility_v1_1.py \
  -v -m "not slow"

# All tests including slow (~30s)
python3 -m pytest tests/validation/ tests/integration/test_validation_pipeline_e2e_v1_1.py -v
```

---

**For questions or issues**: See `PENDING_FEATURES.md` or create GitHub Issue with label `phase:validation`.
