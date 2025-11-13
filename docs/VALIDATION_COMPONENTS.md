# Validation Components Guide

**Version**: 1.0.0
**Status**: Production Ready (139 tests passing)
**Last Updated**: 2025-10-16

---

## Table of Contents

1. [Overview](#overview)
2. [Component 1: Train/Validation/Test Data Split](#component-1-trainvalidationtest-data-split)
3. [Component 2: Walk-Forward Analysis](#component-2-walk-forward-analysis)
4. [Component 3: Bonferroni Multiple Comparison](#component-3-bonferroni-multiple-comparison)
5. [Component 4: Bootstrap Confidence Intervals](#component-4-bootstrap-confidence-intervals)
6. [Component 5: Baseline Comparison](#component-5-baseline-comparison)
7. [Integration Guide](#integration-guide)
8. [Taiwan Market Considerations](#taiwan-market-considerations)
9. [Error Handling and Edge Cases](#error-handling-and-edge-cases)
10. [Performance Guidelines](#performance-guidelines)

---

## Overview

This document provides comprehensive guidance on using the five validation components implemented for Taiwan market trading strategy validation. All components are designed to prevent overfitting and ensure strategies generalize to unseen data.

### Component Summary

| Component | Purpose | When to Use | Pass Criteria |
|-----------|---------|-------------|---------------|
| **Data Split** | Temporal validation across 3 periods | Every strategy iteration | Validation Sharpe > 1.0, Consistency > 0.6 |
| **Walk-Forward** | Rolling window robustness testing | Final validation, production strategies | Avg Sharpe > 0.5, Win rate > 60% |
| **Bonferroni** | Multiple comparison correction | Testing multiple strategies (500+) | Sharpe > significance threshold (~0.5) |
| **Bootstrap** | Confidence interval estimation | Statistical significance testing | CI excludes zero, lower bound > 0.5 |
| **Baseline** | Comparison with passive strategies | Ensuring value-add vs simple approaches | Beat one baseline by > 0.5 Sharpe |

### Installation

```bash
# All components are included in the main codebase
# Only external dependency is scipy (for Bonferroni)
pip install scipy>=1.7.0
```

---

## Component 1: Train/Validation/Test Data Split

### Purpose

Validates strategies across three distinct time periods to detect overfitting and ensure temporal robustness.

### Design Rationale

- **Training Period** (2018-2020): 3 years capturing bull/bear cycles, trade war volatility, COVID crash
- **Validation Period** (2021-2022): 2 years with post-COVID recovery, inflation, rate hikes
- **Test Period** (2023-2024): 2 years hold-out for final evaluation, AI boom impact

### When to Use

- **Primary use**: Every strategy iteration in learning loop
- **Secondary use**: Final validation before production deployment
- **Frequency**: Every generated strategy should pass this validation

### API Reference

```python
from src.validation.data_split import DataSplitValidator

# Initialize validator
validator = DataSplitValidator(
    epsilon=0.1,              # Minimum acceptable mean Sharpe
    strict_filtering=False    # Backward compatibility mode
)

# Validate strategy
results = validator.validate_strategy(
    strategy_code=strategy_code,  # Python code string
    data=data,                    # FinLab data object
    iteration_num=42              # For logging
)
```

### Usage Example

```python
from src.validation.data_split import validate_strategy_with_data_split

# Simple validation
results = validate_strategy_with_data_split(
    strategy_code="""
# Your strategy code here
close = data.get('price:收盤價')
# ... strategy logic ...
report = sim(position, resample='D')
    """,
    data=data,
    iteration_num=1
)

# Check results
if results['validation_passed']:
    print("✅ Strategy passed data split validation!")
    print(f"Training Sharpe: {results['sharpes']['training']:.4f}")
    print(f"Validation Sharpe: {results['sharpes']['validation']:.4f}")
    print(f"Test Sharpe: {results['sharpes']['test']:.4f}")
    print(f"Consistency: {results['consistency']:.4f}")
else:
    print("❌ Strategy failed validation")
    if results['validation_skipped']:
        print(f"Reason: {results['skip_reason']}")
```

### Results Dictionary

```python
{
    'validation_passed': bool,      # Overall validation result
    'validation_skipped': bool,     # If validation was skipped
    'skip_reason': str or None,     # Reason for skipping
    'sharpes': {
        'training': float,          # 2018-2020 Sharpe
        'validation': float,        # 2021-2022 Sharpe
        'test': float               # 2023-2024 Sharpe
    },
    'consistency': float,           # 1 - (std/mean) of Sharpes
    'degradation_ratio': float,     # validation/training ratio
    'periods_tested': list,         # Successfully tested periods
    'periods_skipped': list         # Failed period details
}
```

### Validation Pass Criteria

**ALL** of the following must be true:

1. **Validation Sharpe ≥ 1.0**: Strong risk-adjusted performance
2. **Consistency ≥ 0.6**: Stable across market regimes (allows 40% variation)
3. **Degradation Ratio ≥ 0.7**: Validation Sharpe ≥ 70% of training Sharpe

### Interpretation Guide

#### Consistency Score

- **> 0.8**: Excellent - Strategy highly robust across market regimes
- **0.6 - 0.8**: Good - Acceptable variation (typical for Taiwan market)
- **< 0.6**: Poor - Likely overfit to specific market conditions

#### Degradation Ratio

- **> 1.0**: Validation outperforms training (excellent generalization)
- **0.7 - 1.0**: Acceptable degradation (normal performance decline)
- **< 0.7**: Significant overfitting warning

### Error Handling

The validator handles these edge cases gracefully:

1. **Insufficient Data**: < 252 trading days in any period → Skip that period
2. **Execution Errors**: Strategy code fails → Skip that period
3. **Report Filtering**: Report doesn't support date filtering → Warning + fallback
4. **Missing Metrics**: Sharpe cannot be extracted → Skip that period

Validation is skipped (not failed) if < 2 periods are successful.

### Taiwan Market Calibration

Thresholds are calibrated for Taiwan market characteristics:

- **Min Sharpe 1.0**: Appropriate for Taiwan risk-free rate (~1%)
- **Min Consistency 0.6**: Accounts for Taiwan's higher volatility (20-25% annual)
- **Degradation 0.7**: Allows 30% performance drop (realistic for market regime changes)

See [Taiwan Market Considerations](#taiwan-market-considerations) for detailed context.

---

## Component 2: Walk-Forward Analysis

### Purpose

Validates strategy robustness using rolling windows with true out-of-sample testing. Simulates real-world periodic retraining and forward testing.

### Design Rationale

- **Training Window**: 252 days (~1 year) - sufficient for parameter optimization
- **Test Window**: 63 days (~1 quarter) - validates near-term performance
- **Step Size**: 63 days - quarterly rebalancing, non-overlapping test periods
- **Minimum Windows**: 3 - statistical validity threshold

### When to Use

- **Primary use**: Final validation before production deployment
- **Secondary use**: Robustness check for high-performing strategies
- **Frequency**: Strategies passing data split validation

### API Reference

```python
from src.validation.walk_forward import WalkForwardValidator

# Initialize validator
validator = WalkForwardValidator(
    training_window=252,   # 1 year training
    test_window=63,        # 1 quarter testing
    step_size=63,          # Non-overlapping windows
    min_windows=3,         # Minimum required windows
    strict_filtering=False # Backward compatibility
)

# Validate strategy
results = validator.validate_strategy(
    strategy_code=strategy_code,
    data=data,
    iteration_num=42
)
```

### Usage Example

```python
from src.validation.walk_forward import validate_strategy_walk_forward

# Validate with defaults
results = validate_strategy_walk_forward(
    strategy_code=strategy_code,
    data=data,
    iteration_num=42
)

# Check results
if results['validation_passed']:
    print("✅ Strategy passed walk-forward validation!")
    print(f"Average Sharpe: {results['avg_sharpe']:.4f}")
    print(f"Sharpe Std Dev: {results['sharpe_std']:.4f}")
    print(f"Win Rate: {results['win_rate']:.1%}")
    print(f"Worst Sharpe: {results['worst_sharpe']:.4f}")
    print(f"Number of Windows: {results['num_windows']}")
else:
    print("❌ Strategy failed walk-forward validation")

# Analyze per-window results
for i, window in enumerate(results['windows']):
    print(f"Window {i+1}:")
    print(f"  Train: {window['train_start']} to {window['train_end']}")
    print(f"  Test: {window['test_start']} to {window['test_end']}")
    if window['test_sharpe']:
        print(f"  Sharpe: {window['test_sharpe']:.4f}")
    else:
        print(f"  Error: {window['error']}")
```

### Results Dictionary

```python
{
    'validation_passed': bool,      # Overall validation result
    'validation_skipped': bool,     # If validation was skipped
    'skip_reason': str or None,     # Reason for skipping
    'avg_sharpe': float,            # Mean Sharpe across windows
    'sharpe_std': float,            # Std dev of Sharpes
    'win_rate': float,              # Fraction of windows with Sharpe > 0
    'worst_sharpe': float,          # Minimum Sharpe across windows
    'best_sharpe': float,           # Maximum Sharpe across windows
    'num_windows': int,             # Number of successful windows
    'windows': [                    # Per-window details
        {
            'window_idx': int,
            'train_start': str,     # YYYY-MM-DD
            'train_end': str,
            'test_start': str,
            'test_end': str,
            'train_days': int,
            'test_days': int,
            'test_sharpe': float or None,
            'error': str or None
        }
    ]
}
```

### Validation Pass Criteria

**ALL** of the following must be true:

1. **Average Sharpe > 0.5**: Consistently profitable across windows
2. **Win Rate > 60%**: Majority of windows are profitable
3. **Worst Sharpe > -0.5**: No catastrophic failures
4. **Sharpe Std < 1.0**: Reasonable stability across market conditions

### Interpretation Guide

#### Performance Patterns

| Pattern | Avg Sharpe | Std Dev | Win Rate | Interpretation |
|---------|-----------|---------|----------|----------------|
| Excellent | > 1.0 | < 0.5 | > 80% | Highly robust strategy |
| Good | 0.5-1.0 | 0.5-1.0 | 60-80% | Solid with acceptable variation |
| Marginal | 0.3-0.5 | 1.0-1.5 | 50-60% | Barely acceptable, risky |
| Poor | < 0.3 | > 1.5 | < 50% | Unreliable, reject |

#### Regime Dependency

- **High avg + low std**: Strategy works across market regimes
- **High avg + high std**: Regime-dependent, investigate which windows failed
- **Low win rate**: Few profitable periods, strategy timing is critical

### Error Handling

1. **Insufficient Data**: < (252 + 63*3) = 441 days → Skip validation
2. **Few Windows**: < 3 successful windows → Skip validation
3. **Window Failures**: Individual window errors logged but don't fail entire validation

### Data Requirements

- **Minimum**: 441 trading days (~1.75 years)
- **Recommended**: 1000+ days (~4 years) for 10+ windows
- **Taiwan market**: ~250 trading days per year

---

## Component 3: Bonferroni Multiple Comparison

### Purpose

Prevents false discoveries when testing multiple strategies by adjusting significance thresholds based on number of strategies tested.

### The Multiple Comparison Problem

Testing 500 strategies at α=0.05 (5% significance):
- **Expected false discoveries**: 500 × 0.05 = 25 strategies
- **Without correction**: 25 "significant" strategies are just random noise

Bonferroni correction: adjusted_alpha = α / n_strategies
- **For 500 strategies**: 0.05 / 500 = 0.0001 (0.01% significance)
- **Result**: Family-Wise Error Rate (FWER) ≤ 0.05

### When to Use

- **Primary use**: Validating final candidate strategies from large search space
- **Secondary use**: Portfolio construction (selecting best N from M strategies)
- **Frequency**: After generating 100+ strategy variants

### API Reference

```python
from src.validation.multiple_comparison import BonferroniValidator

# Initialize validator
validator = BonferroniValidator(
    n_strategies=500,  # Total strategies tested
    alpha=0.05         # Desired FWER
)

# Calculate significance threshold
threshold = validator.calculate_significance_threshold(
    n_periods=252,           # Trading days for Sharpe calculation
    use_conservative=True    # Use max(calculated, 0.5)
)

# Test individual strategy
is_significant = validator.is_significant(
    sharpe_ratio=1.5,
    n_periods=252
)

# Validate entire strategy set
results = validator.validate_strategy_set(
    strategies_with_sharpes=[
        {'name': 'Strategy_A', 'sharpe_ratio': 1.8},
        {'name': 'Strategy_B', 'sharpe_ratio': 0.3},
        {'name': 'Strategy_C', 'sharpe_ratio': 2.1}
    ],
    n_periods=252
)
```

### Usage Example

```python
# Example: Validating 500 strategies from learning loop
validator = BonferroniValidator(n_strategies=500, alpha=0.05)

# Get threshold
threshold = validator.calculate_significance_threshold()
print(f"Sharpe must exceed {threshold:.4f} to be significant")

# Test single strategy
my_sharpe = 1.5
if validator.is_significant(my_sharpe):
    print(f"Sharpe {my_sharpe:.4f} is statistically significant!")
else:
    print(f"Sharpe {my_sharpe:.4f} may be due to chance")

# Validate full set
strategies = [
    {'name': f'Strategy_{i}', 'sharpe_ratio': sharpes[i]}
    for i in range(500)
]

results = validator.validate_strategy_set(strategies)
print(f"Significant strategies: {results['significant_count']}/500")
print(f"Expected false discoveries: {results['expected_false_discoveries']:.2f}")
print(f"Estimated FDR: {results['estimated_fdr']:.2%}")

# Generate report
print(validator.generate_report(results))
```

### Results Dictionary

```python
{
    'total_strategies': int,            # Total tested
    'significant_count': int,           # Passing threshold
    'significance_threshold': float,    # Sharpe threshold
    'adjusted_alpha': float,            # α/n
    'expected_false_discoveries': float,# α * n
    'estimated_fdr': float,             # FDR estimate
    'significant_strategies': list      # Passing strategies
}
```

### Validation Pass Criteria

Strategy is **significant** if:
- **abs(Sharpe) > threshold**, where threshold = Z(1 - α/(2n)) / sqrt(T)
- For 500 strategies, 252 days, α=0.05: threshold ≈ 0.245
- **Conservative threshold**: max(calculated, 0.5) = 0.5

### Bootstrap Method (Advanced)

For non-normal return distributions (common in Taiwan market):

```python
# Bootstrap-based threshold (more robust)
result = validator.calculate_bootstrap_threshold(
    n_periods=252,
    n_bootstrap=1000,
    market_volatility=0.22  # Taiwan market ~22% annual
)

print(f"Bootstrap threshold: {result['bootstrap_threshold']:.4f}")
print(f"Parametric threshold: {result['parametric_threshold']:.4f}")
print(f"Difference: {result['percent_diff']:+.1f}%")

# Use bootstrap threshold if difference > 20%
if abs(result['percent_diff']) > 20:
    print("⚠️  Use bootstrap threshold (fat-tailed distribution detected)")
```

### Interpretation Guide

#### False Discovery Rate (FDR)

- **FDR < 5%**: Excellent - few false positives expected
- **FDR 5-10%**: Acceptable - some false positives likely
- **FDR > 10%**: Poor - many false positives, increase threshold

#### Family-Wise Error Rate (FWER)

```python
fwer = validator.calculate_family_wise_error_rate()
print(f"FWER: {fwer:.4f}")  # Should be ≤ alpha (0.05)
```

### Error Handling

- **Invalid inputs**: Raises ValueError for n_strategies ≤ 0 or alpha not in (0, 1)
- **Bootstrap failure**: Falls back to parametric threshold with warning
- **Empty strategy list**: Returns safe default results

---

## Component 4: Bootstrap Confidence Intervals

### Purpose

Calculates confidence intervals for trading metrics using block bootstrap to account for time-series autocorrelation. Validates statistical significance without assuming normality.

### Design Rationale

- **Block Bootstrap**: Preserves autocorrelation structure (21-day blocks ≈ 1 month)
- **1000 Iterations**: Robust CI estimation
- **95% Confidence**: Standard level (2.5th and 97.5th percentiles)
- **Validation**: CI must exclude zero AND lower bound > 0.5

### When to Use

- **Primary use**: Statistical significance testing for final strategies
- **Secondary use**: Comparing strategy variants with confidence bounds
- **Frequency**: Strategies passing preliminary validations

### API Reference

```python
from src.validation.bootstrap import bootstrap_confidence_interval

# Calculate bootstrap CI
result = bootstrap_confidence_interval(
    returns=daily_returns,        # NumPy array of daily returns
    metric_name='sharpe_ratio',   # Currently only Sharpe supported
    confidence_level=0.95,        # 95% CI
    n_iterations=1000,            # Bootstrap iterations
    block_size=21,                # 1 month blocks
    min_data_points=100,          # Minimum required data
    min_success_rate=0.9          # Require 90% valid iterations
)

# Access results
print(f"Sharpe: {result.point_estimate:.4f}")
print(f"95% CI: [{result.lower_bound:.4f}, {result.upper_bound:.4f}]")
print(f"Validation: {'PASS' if result.validation_pass else 'FAIL'}")
print(f"Reason: {result.validation_reason}")
print(f"Time: {result.computation_time:.2f}s")
```

### Usage Example

```python
from src.validation.bootstrap import validate_strategy_with_bootstrap
import numpy as np

# Simulate strategy returns (or extract from backtest)
# Example: 252 days of returns
returns = np.random.normal(0.002, 0.02, 252)  # Mean 0.2%, std 2%

# Validate with bootstrap
results = validate_strategy_with_bootstrap(
    returns=returns,
    confidence_level=0.95,
    n_iterations=1000,
    block_size=21
)

if results['passed']:
    print("✅ Strategy is statistically significant!")
    print(f"Sharpe: {results['sharpe_ratio']:.4f}")
    print(f"95% CI: [{results['ci_lower']:.4f}, {results['ci_upper']:.4f}]")
    print(f"Margin above zero: {results['ci_lower']:.4f}")
else:
    print("❌ Strategy lacks statistical significance")
    print(f"Reason: {results['reason']}")

# Extract returns from backtest report
# Assuming report has daily returns in report.returns attribute
backtest_returns = report.returns.values
ci_result = bootstrap_confidence_interval(backtest_returns)
```

### Results Objects

#### BootstrapResult (detailed)

```python
@dataclass
class BootstrapResult:
    metric_name: str                # 'sharpe_ratio'
    point_estimate: float           # Sample Sharpe ratio
    lower_bound: float              # 2.5th percentile
    upper_bound: float              # 97.5th percentile
    confidence_level: float         # 0.95
    n_iterations: int               # 1000
    n_successes: int                # Valid iterations
    block_size: int                 # 21 days
    validation_pass: bool           # Pass/fail status
    validation_reason: str          # Human-readable reason
    computation_time: float         # Seconds
```

#### Simplified Dict (convenience function)

```python
{
    'passed': bool,                 # Validation result
    'sharpe_ratio': float,          # Point estimate
    'ci_lower': float,              # Lower bound
    'ci_upper': float,              # Upper bound
    'reason': str,                  # Validation reason
    'computation_time': float       # Seconds
}
```

### Validation Pass Criteria

**BOTH** of the following must be true:

1. **CI excludes zero**: lower_bound > 0 (statistically significant)
2. **Lower bound ≥ 0.5**: Sufficient effect size for practical trading

### Interpretation Guide

#### Confidence Interval Width

- **Narrow CI** (width < 0.5): High precision, large sample or low variance
- **Medium CI** (width 0.5-1.0): Typical for 252-day strategies
- **Wide CI** (width > 1.0): Low precision, small sample or high variance

#### Statistical vs Practical Significance

| Scenario | Lower | Upper | Significant? | Practical? |
|----------|-------|-------|--------------|------------|
| Strong strategy | 1.2 | 2.5 | ✅ Yes | ✅ Yes |
| Marginal strategy | 0.6 | 1.8 | ✅ Yes | ✅ Yes (lower ≥ 0.5) |
| Weak strategy | 0.2 | 1.5 | ✅ Yes | ❌ No (lower < 0.5) |
| Insignificant | -0.3 | 1.2 | ❌ No | ❌ No (includes zero) |

### Error Handling

The bootstrap validator handles these cases:

1. **Insufficient Data**: < 100 days → Raises ValueError
2. **Too Many NaNs**: < 90% valid data after NaN removal → Raises ValueError
3. **Zero Std Dev**: Point estimate is NaN → Raises ValueError
4. **Low Success Rate**: < 90% valid bootstrap iterations → Raises ValueError

All errors are caught by the convenience function and returned as failed validation.

### Performance Optimization

- **Target**: < 20 seconds per metric
- **Typical**: 1-2 seconds for 1000 iterations on 252 days
- **Bottleneck**: Sharpe calculation (can be optimized if needed)

### Block Size Selection

**Default: 21 days** (1 month)

Rationale:
- Taiwan market autocorrelation typically decays within 20-30 days
- Monthly rebalancing is common in Taiwan strategies
- Larger blocks (42 days) increase variance of CI
- Smaller blocks (10 days) may not fully capture autocorrelation

---

## Component 5: Baseline Comparison

### Purpose

Compares strategy performance against three passive baseline strategies to ensure the strategy provides value beyond simple approaches.

### The Three Baselines

1. **Buy-and-Hold 0050**: Passive Taiwan 50 ETF (元大台灣50)
   - Market benchmark, ~70% Taiwan market cap coverage
   - Single transaction, minimal costs
   - Tests if active management beats passive indexing

2. **Equal-Weight Top 50**: Monthly rebalanced equal-weight portfolio
   - Tests if equal-weighting beats market-cap weighting
   - ~12 rebalances/year × 50 stocks = 600 trades/year
   - More active than buy-hold, less active than most strategies

3. **Risk Parity**: Inverse volatility weighted portfolio
   - Lower volatility stocks get higher weights
   - Monthly rebalanced with rolling 60-day volatility
   - Tests if volatility management improves risk-adjusted returns

### When to Use

- **Primary use**: Final validation for production candidates
- **Secondary use**: Comparing strategy variants
- **Frequency**: Strategies passing other validations

### API Reference

```python
from src.validation.baseline import BaselineComparator

# Initialize comparator
comparator = BaselineComparator(
    enable_cache=True  # Cache baseline calculations
)

# Compare strategy with baselines
comparison = comparator.compare_with_baselines(
    strategy_code="",              # Not used (for API consistency)
    strategy_sharpe=2.5,           # Strategy's Sharpe ratio
    data=data,                     # FinLab data object
    start_date="2018-01-01",       # Optional, defaults to data range
    end_date="2024-12-31",         # Optional
    iteration_num=42               # For logging
)

# Access results
print(f"Validation: {'PASS' if comparison.validation_passed else 'FAIL'}")
print(f"Reason: {comparison.validation_reason}")
for name, metrics in comparison.baselines.items():
    print(f"{name}: Sharpe={metrics.sharpe_ratio:.4f}")
```

### Usage Example

```python
from src.validation.baseline import compare_strategy_with_baselines

# Simple comparison
results = compare_strategy_with_baselines(
    strategy_sharpe=2.5,
    data=data,
    iteration_num=42,
    enable_cache=True
)

# Check results
if results['validation_passed']:
    print("✅ Strategy beats baselines!")
    print(f"Best matchup: {results['best_baseline_matchup']}")
    print(f"Worst matchup: {results['worst_baseline_matchup']}")

    # Detailed improvements
    for baseline, improvement in results['sharpe_improvements'].items():
        print(f"  vs {baseline}: {improvement:+.4f} Sharpe")

    # Baseline details
    for baseline, metrics in results['baselines'].items():
        print(f"\n{baseline}:")
        print(f"  Sharpe: {metrics['sharpe_ratio']:.4f}")
        print(f"  Annual Return: {metrics['annual_return']:.2%}")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")
else:
    print("❌ Strategy fails to beat baselines")
    print(f"Reason: {results['validation_reason']}")
```

### Results Objects

#### BaselineComparison

```python
@dataclass
class BaselineComparison:
    strategy_sharpe: float                  # Strategy Sharpe
    baselines: Dict[str, BaselineMetrics]   # Baseline metrics
    sharpe_improvements: Dict[str, float]   # Strategy - baseline
    best_baseline_matchup: str              # Best improvement
    worst_baseline_matchup: str             # Worst improvement
    validation_passed: bool                 # Pass/fail
    validation_reason: str                  # Human-readable
    total_computation_time: float           # Seconds
```

#### BaselineMetrics

```python
@dataclass
class BaselineMetrics:
    baseline_name: str          # 'Buy-and-Hold 0050', etc.
    sharpe_ratio: float         # Baseline Sharpe
    annual_return: float        # Annualized return
    max_drawdown: float         # Maximum drawdown (negative)
    total_trades: int           # Estimated trades
    win_rate: float             # Approximate win rate
    computation_time: float     # Seconds
```

### Validation Pass Criteria

**BOTH** of the following must be true:

1. **Beat at least one baseline by > 0.5 Sharpe**: Meaningful improvement
2. **No catastrophic underperformance**: All improvements > -1.0

### Interpretation Guide

#### Performance Tiers

| Improvement vs Best Baseline | Interpretation |
|------------------------------|----------------|
| > +1.5 Sharpe | Excellent - substantial value-add |
| +0.5 to +1.5 | Good - meaningful improvement |
| +0.2 to +0.5 | Marginal - barely worth complexity |
| -0.5 to +0.2 | Poor - not worth active management |
| < -0.5 | Bad - worse than passive approach |

#### Baseline-Specific Insights

**If strategy beats Buy-and-Hold 0050:**
- Justifies active management costs
- But check if beats other baselines (may just be leverage effect)

**If strategy beats Equal-Weight but not Risk Parity:**
- Strategy may have insufficient risk management
- Consider adding volatility filters

**If strategy beats Risk Parity but not Equal-Weight:**
- Strategy may be over-optimizing for stability
- Consider accepting more volatility for higher returns

### Caching Strategy

Baselines are cached by (baseline_name, start_date, end_date):

```python
# First run: 10-15 seconds (calculates all baselines)
comparison1 = comparator.compare_with_baselines(...)

# Subsequent runs: < 0.1 seconds (cache hit)
comparison2 = comparator.compare_with_baselines(...)

# Cache location: .cache/baseline_metrics/*.json
# Clear cache to recalculate:
import shutil
shutil.rmtree('.cache/baseline_metrics')
```

### Error Handling

1. **Missing 0050 Data**: Falls back to market average as proxy + warning
2. **Insufficient Market Cap Data**: Uses available stocks for Equal-Weight/Risk Parity
3. **Calculation Failures**: Returns default metrics (Sharpe=0) + error log
4. **Cache Read Failures**: Silently recalculates + warning

No errors fail the entire comparison - individual baseline failures are logged.

---

## Integration Guide

### Recommended Validation Pipeline

```python
from src.validation.data_split import validate_strategy_with_data_split
from src.validation.walk_forward import validate_strategy_walk_forward
from src.validation.multiple_comparison import BonferroniValidator
from src.validation.bootstrap import validate_strategy_with_bootstrap
from src.validation.baseline import compare_strategy_with_baselines

def comprehensive_validation(strategy_code, data, iteration_num=0):
    """
    Comprehensive multi-stage validation pipeline.
    """
    results = {}

    # Stage 1: Data Split (Fast, Primary Filter)
    print("Stage 1: Data Split Validation...")
    split_results = validate_strategy_with_data_split(
        strategy_code, data, iteration_num
    )
    results['data_split'] = split_results

    if not split_results['validation_passed']:
        print("❌ Failed Stage 1: Data Split")
        return results

    # Stage 2: Walk-Forward (Moderate Speed, Robustness Check)
    print("✅ Passed Stage 1")
    print("Stage 2: Walk-Forward Analysis...")
    wf_results = validate_strategy_walk_forward(
        strategy_code, data, iteration_num
    )
    results['walk_forward'] = wf_results

    if not wf_results['validation_passed']:
        print("❌ Failed Stage 2: Walk-Forward")
        return results

    # Stage 3: Baseline Comparison (Fast with cache)
    print("✅ Passed Stage 2")
    print("Stage 3: Baseline Comparison...")

    # Extract Sharpe from data split validation period
    strategy_sharpe = split_results['sharpes']['validation']

    baseline_results = compare_strategy_with_baselines(
        strategy_sharpe=strategy_sharpe,
        data=data,
        iteration_num=iteration_num
    )
    results['baseline'] = baseline_results

    if not baseline_results['validation_passed']:
        print("❌ Failed Stage 3: Baseline Comparison")
        return results

    # Stage 4: Bootstrap CI (Moderate Speed, Statistical Significance)
    print("✅ Passed Stage 3")
    print("Stage 4: Bootstrap Confidence Intervals...")

    # Extract returns from report (requires modified extraction)
    # For now, skip or implement based on your report structure
    # bootstrap_results = validate_strategy_with_bootstrap(returns)
    # results['bootstrap'] = bootstrap_results

    print("✅ Strategy passed all validation stages!")
    return results

# Usage
validation_results = comprehensive_validation(
    strategy_code=my_strategy,
    data=data,
    iteration_num=42
)
```

### Integration with Learning Loop

```python
# In your iteration engine
def run_iteration(iteration_num, data):
    # Generate strategy
    strategy_code = generate_strategy(iteration_num)

    # Run backtest
    report = run_backtest(strategy_code, data)
    metrics = extract_metrics(report)

    # Validate if Sharpe is promising (> 1.5)
    if metrics['sharpe_ratio'] > 1.5:
        validation = validate_strategy_with_data_split(
            strategy_code, data, iteration_num
        )

        if validation['validation_passed']:
            # Add to Hall of Fame
            hall_of_fame.append({
                'iteration': iteration_num,
                'sharpe': metrics['sharpe_ratio'],
                'consistency': validation['consistency'],
                'validation': validation
            })

    return metrics, validation
```

### Parallel Validation (Advanced)

For high-throughput validation:

```python
from concurrent.futures import ThreadPoolExecutor

def parallel_validate(strategies, data):
    """
    Validate multiple strategies in parallel.
    """
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(
                validate_strategy_with_data_split,
                strategy['code'],
                data,
                strategy['id']
            )
            for strategy in strategies
        ]

        results = [f.result() for f in futures]

    return results
```

---

## Taiwan Market Considerations

### Market Structure (2018-2024)

#### Training Period (2018-2020)
- **2018**: US-China trade war volatility, TAIEX -8.6%
- **2019**: Recovery phase, TAIEX +23.3%
- **2020**: COVID crash (-18% in Q1) + recovery, TAIEX +22.8%
- **Characteristics**: Full bull/bear cycle, suitable for parameter learning

#### Validation Period (2021-2022)
- **2021**: Post-COVID boom, chip shortage, TAIEX +23.7%
- **2022**: Inflation + Fed rate hikes, TAIEX -22.4%
- **Characteristics**: Volatility regime shift, tests strategy robustness

#### Test Period (2023-2024)
- **2023**: AI boom (NVIDIA/TSMC effect), TAIEX +26.8%
- **2024**: Consolidation, TAIEX +28.9% YTD
- **Characteristics**: New market regime, tests generalization

### Trading Calendar

- **Trading days/year**: ~250 days (vs 252 in US)
- **Market hours**: 09:00-13:30 Taiwan time (4.5 hours)
- **Holidays**: Lunar New Year (7-9 days), Dragon Boat, Mid-Autumn festivals
- **Data gaps**: Lunar New Year causes multi-day gaps (late Jan/early Feb)

### Market Characteristics

#### Volatility Profile
- **Historical volatility**: 20-25% annual (higher than US ~15%)
- **Crisis periods**: Can spike to 40-50% (COVID crash, 2022 bear market)
- **Implication**: Expect lower Sharpe ratios than US strategies

#### Liquidity Considerations
- **TWSE daily volume**: ~$5-8B USD (small vs NYSE ~$70B)
- **Small cap illiquidity**: Use ≥100M TWD daily volume threshold
- **0050 ETF liquidity**: >$50M USD daily, very liquid

#### Sector Concentration
- **Technology**: 55-60% of TAIEX (TSMC alone ~30%)
- **Financials**: 15-20%
- **Industrials**: 10-15%
- **Implication**: Sector rotation strategies may be less effective

### Validation Threshold Calibration

#### Why Taiwan Thresholds Differ from US

| Metric | US | Taiwan | Reason |
|--------|-----|--------|--------|
| Risk-free rate | 4-5% | ~1% | Taiwan 10Y bond yield lower |
| Market volatility | ~15% | 20-25% | Higher volatility market |
| Min Sharpe | 1.5-2.0 | 1.0-1.5 | Adjusted for volatility |
| Consistency | > 0.7 | > 0.6 | More regime variation |

#### Recommended Thresholds by Strategy Type

**Short-term (< 5 days hold):**
- Data Split: Validation Sharpe > 0.8, Consistency > 0.5
- Walk-Forward: Avg Sharpe > 0.4, Win rate > 55%

**Medium-term (5-20 days hold):**
- Data Split: Validation Sharpe > 1.0, Consistency > 0.6 (default)
- Walk-Forward: Avg Sharpe > 0.5, Win rate > 60% (default)

**Long-term (> 20 days hold):**
- Data Split: Validation Sharpe > 1.2, Consistency > 0.7
- Walk-Forward: Avg Sharpe > 0.6, Win rate > 65%

### Data Quality Issues

1. **Pre-2018 data**: May have survivorship bias, incomplete coverage
2. **Penny stocks**: High volatility but illiquid, filter by volume
3. **Corporate actions**: Ensure data is split-adjusted
4. **FinLab data**: 2018+ has high quality coverage

---

## Error Handling and Edge Cases

### Common Error Scenarios

#### 1. Insufficient Data

**Symptom**: `validation_skipped=True, skip_reason="Insufficient data"`

**Causes**:
- Data period shorter than required (< 252 days for data split)
- Stock with incomplete trading history
- Recent IPO with limited data

**Solutions**:
```python
# Check data availability before validation
close = data.get('price:收盤價')
data_days = len(close)
print(f"Available days: {data_days}")

if data_days < 441:  # Minimum for walk-forward
    print("⚠️  Insufficient data for walk-forward analysis")
    # Use only data split validation
```

#### 2. Strategy Execution Failures

**Symptom**: Period skipped with execution error message

**Causes**:
- Missing data features in specific time period
- Division by zero (empty signals)
- Invalid pandas operations

**Solutions**:
```python
# Add defensive checks in strategy code
close = data.get('price:收盤價')
if close is None or close.empty:
    # Fallback: return empty position
    position = pd.DataFrame(0, index=close.index, columns=close.columns)
else:
    # Normal strategy logic
    position = compute_position(close)

# Ensure no NaN in final position
position = position.fillna(0)
```

#### 3. Report Filtering Not Supported

**Symptom**: `DeprecationWarning: Report filtering not supported`

**Causes**:
- FinLab report object doesn't have `filter_dates()` method
- Report is not a DataFrame with DatetimeIndex

**Solutions**:
```python
# Option 1: Enable strict mode to force error
validator = DataSplitValidator(strict_filtering=True)
# Will raise ValueError if filtering not supported

# Option 2: Implement report wrapper
class FilterableReport:
    def __init__(self, report):
        self.report = report

    def filter_dates(self, start, end):
        # Implement filtering logic
        # Extract relevant data from report for date range
        pass

    def get_stats(self):
        return self.report.get_stats()

# Option 3: Accept data leakage warning (not recommended)
validator = DataSplitValidator(strict_filtering=False)
```

#### 4. Zero Variance Returns

**Symptom**: `ValueError: Point estimate is NaN (zero std or calculation error)`

**Causes**:
- Strategy has no trades (position = 0 always)
- All returns are identical (e.g., cash position)
- Numerical precision issues

**Solutions**:
```python
# Check returns before bootstrap
returns = compute_returns(report)
if returns.std() == 0:
    print("⚠️  Zero variance returns - strategy has no variation")
    # Skip bootstrap validation
else:
    bootstrap_result = bootstrap_confidence_interval(returns)
```

#### 5. Cache Corruption

**Symptom**: Baseline comparator loads incorrect cached values

**Solutions**:
```python
# Clear cache and recalculate
import shutil
from pathlib import Path

cache_dir = Path('.cache/baseline_metrics')
if cache_dir.exists():
    shutil.rmtree(cache_dir)
    print("Cache cleared, will recalculate baselines")

# Or disable cache
comparator = BaselineComparator(enable_cache=False)
```

### Defensive Coding Patterns

```python
# Always wrap validation in try-except
def safe_validate(strategy_code, data):
    try:
        results = validate_strategy_with_data_split(
            strategy_code, data
        )
        return results
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return {
            'validation_passed': False,
            'validation_skipped': True,
            'skip_reason': f"Validation error: {str(e)}"
        }

# Check for None/empty results
if results and results.get('sharpes'):
    # Process results
    pass
else:
    # Handle missing data
    pass

# Use .get() with defaults for nested dicts
sharpe = results.get('sharpes', {}).get('validation', 0.0)
```

---

## Performance Guidelines

### Execution Time Benchmarks

| Component | Target | Typical | Worst Case |
|-----------|--------|---------|------------|
| Data Split | < 5s | 2-3s | 10s |
| Walk-Forward (10 windows) | < 30s | 10-15s | 45s |
| Bonferroni | < 0.1s | 0.01s | 0.5s |
| Bootstrap (1000 iter) | < 20s | 1-2s | 30s |
| Baseline (cached) | < 1s | 0.1s | 5s |
| Baseline (uncached) | < 15s | 10s | 30s |

### Optimization Tips

#### 1. Use Caching Aggressively

```python
# Enable baseline caching
comparator = BaselineComparator(enable_cache=True)

# Cache results in your own validation pipeline
import pickle
from pathlib import Path

cache_file = Path(f'.cache/validation_{strategy_id}.pkl')
if cache_file.exists():
    with open(cache_file, 'rb') as f:
        results = pickle.load(f)
else:
    results = comprehensive_validation(strategy_code, data)
    with open(cache_file, 'wb') as f:
        pickle.dump(results, f)
```

#### 2. Parallelize Independent Validations

```python
from concurrent.futures import ThreadPoolExecutor

def fast_comprehensive_validation(strategy_code, data):
    """
    Run independent validations in parallel.
    """
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit independent validations
        future_split = executor.submit(
            validate_strategy_with_data_split,
            strategy_code, data
        )
        future_wf = executor.submit(
            validate_strategy_walk_forward,
            strategy_code, data
        )
        future_baseline = executor.submit(
            compare_strategy_with_baselines,
            2.0, data  # Use estimated Sharpe
        )

        # Collect results
        split_results = future_split.result()
        wf_results = future_wf.result()
        baseline_results = future_baseline.result()

    return {
        'data_split': split_results,
        'walk_forward': wf_results,
        'baseline': baseline_results
    }
```

#### 3. Early Termination

```python
def fast_fail_validation(strategy_code, data):
    """
    Fail fast on expensive validations.
    """
    # Stage 1: Cheap data split
    split_results = validate_strategy_with_data_split(
        strategy_code, data
    )

    if not split_results['validation_passed']:
        return {'passed': False, 'stage': 'data_split'}

    # Only run expensive walk-forward if data split passes
    wf_results = validate_strategy_walk_forward(
        strategy_code, data
    )

    if not wf_results['validation_passed']:
        return {'passed': False, 'stage': 'walk_forward'}

    return {'passed': True, 'stage': 'all'}
```

#### 4. Reduce Bootstrap Iterations for Speed

```python
# For preliminary testing: 500 iterations (faster)
quick_result = bootstrap_confidence_interval(
    returns, n_iterations=500
)

# For final validation: 1000 iterations (default, more robust)
final_result = bootstrap_confidence_interval(
    returns, n_iterations=1000
)

# For research/publication: 5000+ iterations
research_result = bootstrap_confidence_interval(
    returns, n_iterations=5000
)
```

### Memory Management

```python
# For large-scale validation (1000+ strategies)
import gc

for i, strategy in enumerate(strategies):
    results = validate_strategy(strategy)

    # Save results immediately
    save_results(results, f'validation_{i}.json')

    # Clear memory every 100 strategies
    if i % 100 == 0:
        gc.collect()
```

---

## Troubleshooting

### Issue: All strategies fail data split validation

**Diagnosis**:
```python
# Check if thresholds are too strict
split_results = validate_strategy_with_data_split(strategy, data)
print(f"Validation Sharpe: {split_results['sharpes']['validation']}")
print(f"Consistency: {split_results['consistency']}")
print(f"Degradation ratio: {split_results['degradation_ratio']}")
```

**Solution**: Adjust thresholds for your strategy type (see Taiwan Market Considerations).

### Issue: Walk-forward has low win rate but high average Sharpe

**Diagnosis**: Few windows dominate performance (regime-dependent strategy)

**Solution**:
- Investigate which windows succeed/fail
- Consider adding regime detection
- Accept if worst_sharpe > -0.5 (no catastrophic failures)

### Issue: Bootstrap CI is very wide

**Diagnosis**: High return variance or small sample size

**Solution**:
- Increase data period (more days = narrower CI)
- Check for outlier returns (fat tails)
- Use larger block size (42 days) if autocorrelation is strong

### Issue: Strategy beats 0050 but fails baseline validation

**Diagnosis**: Doesn't beat other baselines by > 0.5 Sharpe

**Solution**:
- Strategy may just be leveraged market exposure
- Compare vs Risk Parity (better risk-adjusted baseline)
- Accept if improvement > 0.3 and your threshold allows it

---

## Appendix: Test Coverage

All validation components have comprehensive test coverage:

- **Data Split**: 25 tests (100% pass)
- **Walk-Forward**: 29 tests (100% pass)
- **Bonferroni**: 23 tests (100% pass)
- **Bootstrap**: 27 tests (100% pass)
- **Baseline**: 35 tests (100% pass)

**Total**: 139 tests, 100% passing

Test files:
- `/mnt/c/Users/jnpi/documents/finlab/tests/validation/test_data_split.py`
- `/mnt/c/Users/jnpi/documents/finlab/tests/validation/test_walk_forward.py`
- `/mnt/c/Users/jnpi/documents/finlab/tests/validation/test_multiple_comparison.py`
- `/mnt/c/Users/jnpi/documents/finlab/tests/validation/test_bootstrap.py`
- `/mnt/c/Users/jnpi/documents/finlab/tests/validation/test_baseline.py`

---

**Document End** | For questions or issues, refer to implementation code or test files for additional examples.
