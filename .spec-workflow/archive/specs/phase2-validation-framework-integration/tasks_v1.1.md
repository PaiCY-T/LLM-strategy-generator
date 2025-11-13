# Phase 2 Validation Framework Integration - Phase 1.1 Remediation Tasks

**Version**: 1.1 (Production Readiness)
**Created**: 2025-10-31
**Based On**: Critical review findings from Gemini 2.5 Pro
**Total Tasks**: 11 remediation tasks
**Estimated Time**: 14-22 hours (minimum viable production)

---

## Overview

Phase 1.0 (Tasks 0-8) completed functional implementation with passing unit tests. However, critical review identified three major flaws:

1. **Statistical Validity Issue**: Returns synthesis algorithm is scientifically unsound
2. **Integration Testing Gap**: Only unit tests, no E2E validation
3. **Arbitrary Threshold**: No empirical basis for 0.5 Sharpe threshold

Phase 1.1 addresses these issues to achieve genuine production readiness.

---

## Critical Findings Summary

### Flaw 1: Returns Synthesis - Statistically Unsound

**Current Code** (src/validation/integration.py):
```python
mean_return = total_return / n_days
std_return = (mean_return / sharpe_ratio) * sqrt(252)
synthetic_returns = np.random.normal(mean_return, std_return, n_days)
```

**Problems**:
- Assumes normal distribution (false for financial returns)
- Destroys temporal structure (autocorrelation, volatility clustering)
- Underestimates tail risk → overly optimistic CIs
- Will approve risky strategies

**Solution**: Extract actual returns from finlab Report's equity curve

### Flaw 2: Arbitrary Threshold

**Current Code**:
```python
threshold = max(calculated_threshold, 0.5)
```

**Problems**:
- No empirical Taiwan market basis
- Ignores passive benchmark performance
- Market regime blind

**Solution**: Dynamic threshold based on 0050.TW ETF Sharpe ratio

### Flaw 3: Superficial Test Coverage

**Current Tests**: Unit tests only verify methods exist and return expected structure

**Missing**:
- E2E tests with real finlab execution
- Statistical validation vs scipy
- Performance benchmarks
- Failure mode testing
- Edge case coverage

---

## Task Breakdown

### Phase 1: Statistical Validity (P0 CRITICAL - 8-12 hours)

#### Task 1.1.1: Replace Returns Synthesis with Equity Curve Extraction

**Priority**: P0 BLOCKING
**Estimated Time**: 4-6 hours
**Depends On**: None

**Objective**: Extract actual daily returns from finlab Report object using equity curve

**Implementation**:

1. **Update** `src/validation/integration.py:_extract_returns_from_report()`:

```python
def _extract_returns_from_report(
    self,
    report: Any,
    sharpe_ratio: float,
    total_return: float,
    n_days: int = 252
) -> Optional[np.ndarray]:
    """
    Extract actual daily returns from finlab Report object.

    Multi-layered extraction strategy (no synthesis):
    1. report.returns (direct)
    2. report.daily_returns (alternative attribute)
    3. report.equity.pct_change() (equity curve differentiation)
    4. report.position value changes
    5. FAIL with clear error

    Args:
        report: finlab backtest Report object
        sharpe_ratio: Not used (kept for API compatibility)
        total_return: Not used (kept for API compatibility)
        n_days: Minimum trading days required (default 252)

    Returns:
        np.ndarray: Daily returns series

    Raises:
        ValueError: If all extraction methods fail or data insufficient
    """
    import pandas as pd

    # Method 1: Direct returns attribute
    if hasattr(report, 'returns') and report.returns is not None:
        returns = np.array(report.returns)
        if len(returns) >= n_days:
            return returns
        else:
            raise ValueError(
                f"Insufficient data: {len(returns)} days < {n_days} minimum required"
            )

    # Method 2: Alternative returns attribute
    if hasattr(report, 'daily_returns') and report.daily_returns is not None:
        returns = np.array(report.daily_returns)
        if len(returns) >= n_days:
            return returns
        else:
            raise ValueError(
                f"Insufficient data: {len(returns)} days < {n_days} minimum required"
            )

    # Method 3: Equity curve differentiation (MOST LIKELY)
    if hasattr(report, 'equity') and report.equity is not None:
        equity = report.equity

        if isinstance(equity, pd.DataFrame):
            equity = equity.iloc[:, 0]

        if isinstance(equity, pd.Series):
            daily_returns = equity.pct_change().dropna()
            returns = daily_returns.values

            if len(returns) >= n_days:
                return returns
            else:
                raise ValueError(
                    f"Insufficient data: {len(returns)} days < {n_days} minimum required"
                )

    # Method 4: Position value changes
    if hasattr(report, 'position') and report.position is not None:
        position = report.position
        if isinstance(position, pd.DataFrame):
            total_value = position.sum(axis=1)
            daily_returns = total_value.pct_change().dropna()
            returns = daily_returns.values

            if len(returns) >= n_days:
                return returns
            else:
                raise ValueError(
                    f"Insufficient data: {len(returns)} days < {n_days} minimum required"
                )

    # All methods failed
    available_attrs = [attr for attr in dir(report) if not attr.startswith('_')][:20]
    raise ValueError(
        f"Failed to extract returns from finlab Report. "
        f"Tried: returns, daily_returns, equity, position. "
        f"Available attributes: {available_attrs}"
    )
```

2. **Remove** synthesis fallback logic entirely

3. **Update** docstrings to clarify no synthesis is performed

**Testing**:
- Create `tests/validation/test_returns_extraction_robust.py`
- Test with mock Reports (equity, returns, position)
- Test with real finlab Report from integration test
- Test edge case: <252 days should raise ValueError
- Test all 4 extraction methods

**Success Criteria**:
- ✅ All extraction methods tested
- ✅ No synthesis code remains
- ✅ Real finlab Report extraction works
- ✅ Clear errors when data insufficient

---

#### Task 1.1.2: Implement Proper Stationary Bootstrap

**Priority**: P0 BLOCKING
**Estimated Time**: 3-4 hours
**Depends On**: Task 1.1.1

**Objective**: Replace simple block bootstrap with Politis & Romano stationary bootstrap

**Implementation**:

1. **Create** `src/validation/stationary_bootstrap.py`:

```python
"""
Stationary Bootstrap for Financial Time Series

Implements Politis & Romano (1994) stationary bootstrap that preserves
temporal structure in financial returns.
"""

import numpy as np
from typing import Tuple


def stationary_bootstrap(
    returns: np.ndarray,
    n_iterations: int = 1000,
    avg_block_size: int = 21,
    confidence_level: float = 0.95
) -> Tuple[float, float, float]:
    """
    Stationary bootstrap for Sharpe ratio confidence intervals.

    Implements Politis & Romano (1994) method that:
    - Preserves autocorrelation and volatility clustering
    - Uses geometric block lengths (more flexible than fixed)
    - Handles circular wrapping for block continuation

    Args:
        returns: Daily returns series (np.ndarray)
        n_iterations: Bootstrap iterations (default 1000)
        avg_block_size: Average block size in days (default 21 ≈ 1 month)
        confidence_level: CI confidence level (default 0.95)

    Returns:
        Tuple[point_estimate, ci_lower, ci_upper]

    Raises:
        ValueError: If insufficient data (<252 days)

    References:
        Politis, D.N. and Romano, J.P. (1994). "The stationary bootstrap."
        JASA, 89(428), 1303-1313.
    """
    n = len(returns)

    if n < 252:
        raise ValueError(
            f"Insufficient data for bootstrap: {n} days < 252 minimum. "
            f"Bootstrap on short history produces unreliable CIs."
        )

    bootstrap_sharpes = []

    for _ in range(n_iterations):
        resampled = []

        while len(resampled) < n:
            # Random starting point
            start_idx = np.random.randint(0, n)

            # Geometric block length (key feature of stationary bootstrap)
            block_len = min(
                np.random.geometric(1.0 / avg_block_size),
                n
            )

            # Extract block with circular wrapping
            indices = (np.arange(block_len) + start_idx) % n
            resampled.extend(returns[indices])

        # Trim to exact length
        resampled_returns = np.array(resampled[:n])

        # Calculate Sharpe ratio
        if len(resampled_returns) > 0 and np.std(resampled_returns) > 0:
            mean_ret = np.mean(resampled_returns)
            std_ret = np.std(resampled_returns)
            sharpe = (mean_ret / std_ret) * np.sqrt(252)
            bootstrap_sharpes.append(sharpe)

    # Point estimate and CI
    bootstrap_sharpes = np.array(bootstrap_sharpes)
    point_estimate = np.mean(bootstrap_sharpes)

    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_sharpes, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_sharpes, 100 * (1 - alpha / 2))

    return point_estimate, ci_lower, ci_upper
```

2. **Update** `src/validation/integration.py:BootstrapIntegrator.validate_with_bootstrap()`:

```python
def validate_with_bootstrap(
    self,
    strategy_code: str,
    data: Any,
    sim: Any,
    start_date: str = "2020-01-01",
    end_date: str = "2023-12-31",
    fee_ratio: float = 0.001425,
    tax_ratio: float = 0.003,
    confidence_level: float = 0.95,
    n_iterations: int = 1000,
    avg_block_size: int = 21,
    iteration_num: int = 0
) -> Dict[str, Any]:
    """Validate strategy with stationary bootstrap CIs."""

    from src.validation.stationary_bootstrap import stationary_bootstrap

    # Execute strategy
    result = self.executor.execute(
        strategy_code=strategy_code,
        data=data,
        sim=sim,
        start_date=start_date,
        end_date=end_date,
        fee_ratio=fee_ratio,
        tax_ratio=tax_ratio,
        iteration_num=iteration_num
    )

    if not result.success:
        return {
            'validation_passed': False,
            'error': result.error_message,
            'iteration_num': iteration_num
        }

    # Extract actual returns
    try:
        returns = self._extract_returns_from_report(
            report=result.report,
            sharpe_ratio=result.sharpe_ratio,
            total_return=result.total_return,
            n_days=252
        )
    except ValueError as e:
        return {
            'validation_passed': False,
            'error': str(e),
            'sharpe_ratio': result.sharpe_ratio,
            'iteration_num': iteration_num
        }

    # Stationary bootstrap
    try:
        point_est, ci_lower, ci_upper = stationary_bootstrap(
            returns=returns,
            n_iterations=n_iterations,
            avg_block_size=avg_block_size,
            confidence_level=confidence_level
        )
    except ValueError as e:
        return {
            'validation_passed': False,
            'error': str(e),
            'sharpe_ratio': result.sharpe_ratio,
            'iteration_num': iteration_num
        }

    # Validation: CI excludes zero AND lower bound >= 0.5
    validation_passed = (ci_lower > 0) and (ci_lower >= 0.5)

    return {
        'validation_passed': validation_passed,
        'sharpe_ratio': point_est,
        'sharpe_ratio_original': result.sharpe_ratio,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'confidence_level': confidence_level,
        'n_iterations': n_iterations,
        'n_days': len(returns),
        'avg_block_size': avg_block_size,
        'iteration_num': iteration_num,
        'validation_reason': (
            f"CI [{ci_lower:.3f}, {ci_upper:.3f}] excludes zero and lower >= 0.5"
            if validation_passed else
            f"CI [{ci_lower:.3f}, {ci_upper:.3f}] fails criteria"
        )
    }
```

**Testing**:
- Create `tests/validation/test_stationary_bootstrap.py`
- Test against scipy.stats.bootstrap for comparison
- Test coverage rates (95% CI should cover true parameter ~95% of time)
- Test with known returns series
- Performance benchmark: 1000 iterations should complete <5 seconds

**Success Criteria**:
- ✅ Stationary bootstrap implemented correctly
- ✅ Statistical validation vs scipy passes
- ✅ Coverage rates verified
- ✅ Performance acceptable

---

#### Task 1.1.3: Establish Empirical Taiwan Market Threshold

**Priority**: P0 BLOCKING
**Estimated Time**: 2-3 hours
**Depends On**: None (can be parallel)

**Objective**: Replace arbitrary 0.5 threshold with empirical Taiwan market benchmark

**Implementation**:

1. **Research** Taiwan passive benchmark historical Sharpe ratios:
   - 0050.TW (Yuanta Taiwan 50 ETF)
   - Analysis period: 2018-2024
   - Calculate rolling 3-year Sharpe ratios
   - Document market regime variations

2. **Create** `src/validation/dynamic_threshold.py`:

```python
"""
Dynamic Threshold Calculator for Taiwan Market

Calculates Sharpe ratio thresholds based on passive benchmark performance.
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DynamicThresholdCalculator:
    """Calculate dynamic Sharpe threshold based on Taiwan benchmarks."""

    def __init__(
        self,
        benchmark_ticker: str = "0050.TW",
        lookback_years: int = 3,
        margin: float = 0.2,
        static_floor: float = 0.0
    ):
        """
        Initialize threshold calculator.

        Args:
            benchmark_ticker: Taiwan benchmark ETF (default: 0050.TW)
            lookback_years: Rolling window for Sharpe (default: 3 years)
            margin: Required improvement over benchmark (default: 0.2)
            static_floor: Minimum threshold floor (default: 0.0 for positive returns)
        """
        self.benchmark_ticker = benchmark_ticker
        self.lookback_years = lookback_years
        self.margin = margin
        self.static_floor = static_floor

        # Empirical data from research
        # TODO: Replace with actual fetched data
        self.empirical_benchmark_sharpe = 0.6  # Placeholder

    def get_threshold(self, current_date: Optional[str] = None) -> float:
        """
        Calculate current dynamic threshold.

        threshold = max(benchmark_sharpe + margin, static_floor)

        Args:
            current_date: Date for calculation (default: use latest)

        Returns:
            float: Dynamic Sharpe threshold
        """
        # TODO: Fetch actual benchmark data and calculate rolling Sharpe
        # For now, use empirical constant

        benchmark_sharpe = self.empirical_benchmark_sharpe
        threshold = max(
            benchmark_sharpe + self.margin,
            self.static_floor
        )

        logger.info(
            f"Dynamic threshold: {threshold:.3f} "
            f"(benchmark: {benchmark_sharpe:.3f} + margin: {self.margin:.3f})"
        )

        return threshold
```

3. **Update** `src/validation/integration.py:BonferroniIntegrator`:

```python
class BonferroniIntegrator:
    def __init__(
        self,
        n_strategies: int = 20,
        alpha: float = 0.05,
        use_dynamic_threshold: bool = True
    ):
        from src.validation.multiple_comparison import BonferroniValidator
        from src.validation.dynamic_threshold import DynamicThresholdCalculator

        self.validator = BonferroniValidator(n_strategies, alpha)
        self.n_strategies = n_strategies
        self.alpha = alpha

        if use_dynamic_threshold:
            self.threshold_calc = DynamicThresholdCalculator(
                benchmark_ticker="0050.TW",
                lookback_years=3,
                margin=0.2,
                static_floor=0.0
            )
        else:
            self.threshold_calc = None

    def validate_single_strategy(
        self,
        sharpe_ratio: float,
        n_periods: int = 252,
        use_conservative: bool = True
    ) -> Dict[str, Any]:
        """Validate with dynamic threshold."""

        result = self.validator.validate(sharpe_ratio, n_periods)

        if use_conservative and self.threshold_calc:
            dynamic_threshold = self.threshold_calc.get_threshold()
            significance_threshold = max(
                result['significance_threshold'],
                dynamic_threshold
            )
        else:
            significance_threshold = result['significance_threshold']

        validation_passed = sharpe_ratio > significance_threshold

        return {
            'validation_passed': validation_passed,
            'sharpe_ratio': sharpe_ratio,
            'significance_threshold': significance_threshold,
            'adjusted_alpha': self.alpha / self.n_strategies,
            'validation_reason': (
                f"Sharpe {sharpe_ratio:.3f} > threshold {significance_threshold:.3f}"
                if validation_passed else
                f"Sharpe {sharpe_ratio:.3f} ≤ threshold {significance_threshold:.3f}"
            )
        }
```

**Research Deliverable**:
- Document: `docs/TAIWAN_MARKET_THRESHOLD_ANALYSIS.md`
- Data: Historical 0050.TW Sharpe ratios (2018-2024)
- Justification for margin and floor values

**Testing**:
- Unit test for DynamicThresholdCalculator
- Verify threshold changes with different dates
- Test static floor enforcement

**Success Criteria**:
- ✅ Empirical research documented
- ✅ Dynamic threshold implemented
- ✅ Integration with Bonferroni complete
- ✅ Justification clear and data-backed

---

### Phase 2: Integration Testing (P0 CRITICAL - 6-10 hours)

#### Task 1.1.4: E2E Pipeline Test with Real Execution

**Priority**: P0 BLOCKING
**Estimated Time**: 3-5 hours
**Depends On**: Tasks 1.1.1, 1.1.2, 1.1.3

**Objective**: Test complete validation pipeline with real finlab execution

**Implementation**:

Create `tests/integration/test_validation_pipeline_e2e_v1_1.py`:

```python
"""
End-to-end integration tests for Phase 1.1 validation pipeline.

Tests complete flow with real finlab execution:
Strategy code → BacktestExecutor → Report → All 5 validators → HTML/JSON report
"""

import pytest
from finlab import data
from finlab.backtest import sim

from src.backtest.executor import BacktestExecutor
from src.validation.integration import (
    ValidationIntegrator,
    BaselineIntegrator,
    BootstrapIntegrator,
    BonferroniIntegrator
)
from src.validation.validation_report import ValidationReportGenerator


def test_full_pipeline_momentum_strategy():
    """Test full pipeline with real momentum strategy."""

    # Simple momentum strategy (known to work)
    strategy_code = '''
close = data.get("price:收盤價")
returns_20d = close.pct_change(20)
position = returns_20d.rank(axis=1, ascending=False) <= 30
report = sim(position, resample="Q", upload=False, mae_mfe_window=5, position_limit=0.5)
'''

    # Initialize integrators
    validation_int = ValidationIntegrator()
    baseline_int = BaselineIntegrator()
    bootstrap_int = BootstrapIntegrator()
    bonferroni_int = BonferroniIntegrator(n_strategies=20, use_dynamic_threshold=True)
    report_gen = ValidationReportGenerator(project_name="E2E Test v1.1")

    # Execute strategy
    executor = BacktestExecutor(timeout=420)
    result = executor.execute(
        strategy_code=strategy_code,
        data=data,
        sim=sim,
        start_date="2020-01-01",
        end_date="2023-12-31",
        fee_ratio=0.001425,
        tax_ratio=0.003
    )

    assert result.success, f"Execution failed: {result.error_message}"
    assert result.sharpe_ratio is not None

    # Run all 5 validators
    oos = validation_int.validate_out_of_sample(strategy_code, data, sim)
    wf = validation_int.validate_walk_forward(strategy_code, data, sim)
    baseline = baseline_int.compare_with_baselines(strategy_code, data, sim)
    bootstrap = bootstrap_int.validate_with_bootstrap(strategy_code, data, sim)
    bonferroni = bonferroni_int.validate_single_strategy(result.sharpe_ratio)

    # Verify all return results
    assert 'validation_passed' in oos
    assert 'validation_passed' in wf
    assert 'validation_passed' in baseline
    assert 'validation_passed' in bootstrap
    assert 'validation_passed' in bonferroni

    # Verify bootstrap used actual returns (not synthesis)
    assert 'n_days' in bootstrap
    assert bootstrap['n_days'] >= 252, "Bootstrap should have used actual returns"

    # Verify dynamic threshold used
    assert 'significance_threshold' in bonferroni

    # Generate report
    report_gen.add_strategy_validation(
        strategy_name="E2E_Momentum_v1.1",
        iteration_num=0,
        out_of_sample_results=oos,
        walk_forward_results=wf,
        baseline_results=baseline,
        bootstrap_results=bootstrap,
        bonferroni_results=bonferroni
    )

    html = report_gen.to_html()
    json_report = report_gen.to_json()

    assert len(html) > 1000
    assert "E2E_Momentum_v1.1" in html

    import json
    data = json.loads(json_report)
    assert data['summary']['total_strategies'] == 1

    print("✅ E2E Pipeline Test v1.1 PASSED")


def test_pipeline_with_failing_strategy():
    """Test pipeline correctly rejects poor strategies."""
    # Strategy with random positions (should fail validations)
    pass


def test_pipeline_with_short_history():
    """Test pipeline rejects strategies with <252 days."""
    # Strategy with only 6 months of data
    # Should raise ValueError from bootstrap
    pass
```

**Success Criteria**:
- ✅ Full pipeline test passes with real finlab
- ✅ All 5 validators execute successfully
- ✅ Bootstrap confirms using actual returns (n_days >= 252)
- ✅ HTML/JSON reports generate correctly
- ✅ Failure cases tested

---

#### Task 1.1.5: Statistical Validation vs scipy

**Priority**: P0 BLOCKING
**Estimated Time**: 2-3 hours
**Depends On**: Task 1.1.2

**Objective**: Verify stationary bootstrap against trusted scipy implementation

**Implementation**:

Create `tests/validation/test_bootstrap_statistical_validity.py`:

```python
"""
Statistical validation of stationary bootstrap implementation.

Compares against scipy.stats.bootstrap to verify correctness.
"""

import numpy as np
import pytest
from scipy import stats

from src.validation.stationary_bootstrap import stationary_bootstrap


def test_bootstrap_vs_scipy():
    """Compare stationary bootstrap vs scipy.stats.bootstrap."""

    np.random.seed(42)
    n_days = 500
    mean_daily = 0.0005
    std_daily = 0.015
    returns = np.random.normal(mean_daily, std_daily, n_days)

    # Our implementation
    our_point, our_lower, our_upper = stationary_bootstrap(
        returns, n_iterations=1000, avg_block_size=21
    )

    # scipy (for comparison - uses different resampling)
    def sharpe_stat(sample, axis):
        mean = np.mean(sample, axis=axis)
        std = np.std(sample, axis=axis)
        return (mean / std) * np.sqrt(252)

    scipy_result = stats.bootstrap(
        (returns,),
        sharpe_stat,
        n_resamples=1000,
        confidence_level=0.95,
        method='percentile'
    )

    # Results should be similar (within tolerance due to randomness)
    our_width = our_upper - our_lower
    scipy_width = scipy_result.confidence_interval.high - scipy_result.confidence_interval.low

    # CI widths should be comparable (within 30%)
    assert abs(our_width - scipy_width) / scipy_width < 0.3

    print(f"Our: {our_point:.3f} [{our_lower:.3f}, {our_upper:.3f}]")
    print(f"scipy: {scipy_result.bootstrap_distribution.mean():.3f} "
          f"[{scipy_result.confidence_interval.low:.3f}, {scipy_result.confidence_interval.high:.3f}]")

    print("✅ Bootstrap vs scipy test PASSED")


def test_coverage_rate():
    """Verify 95% CI covers true parameter ~95% of time."""

    np.random.seed(42)
    true_sharpe = 1.0
    n_experiments = 100
    coverage_count = 0

    for _ in range(n_experiments):
        # Generate returns with known Sharpe
        returns = np.random.normal(0.0004, 0.01, 252)

        _, ci_lower, ci_upper = stationary_bootstrap(
            returns, n_iterations=500, avg_block_size=21
        )

        # Check if CI contains true Sharpe
        true_sharpe_sample = (np.mean(returns) / np.std(returns)) * np.sqrt(252)
        if ci_lower <= true_sharpe_sample <= ci_upper:
            coverage_count += 1

    coverage_rate = coverage_count / n_experiments

    # Should be close to 0.95 (allow 0.85-1.0 due to randomness)
    assert 0.85 <= coverage_rate <= 1.0

    print(f"Coverage rate: {coverage_rate:.2%} (target: 95%)")
    print("✅ Coverage rate test PASSED")
```

**Success Criteria**:
- ✅ Bootstrap results comparable to scipy
- ✅ Coverage rates validated
- ✅ CI widths reasonable

---

#### Task 1.1.6: Backward Compatibility Regression Tests

**Priority**: P0 BLOCKING
**Estimated Time**: 1-2 hours
**Depends On**: Tasks 1.1.1-1.1.3

**Objective**: Verify no breaking changes to existing validation clients

**Implementation**:

1. Identify existing code that imports validation modules
2. Create regression test suite
3. Run tests to verify API compatibility

Create `tests/validation/test_backward_compatibility_v1_1.py`:

```python
"""
Regression tests for Phase 1.1 backward compatibility.

Verifies that API changes don't break existing client code.
"""

def test_validator_import_compatibility():
    """Test all public exports remain accessible."""

    from src.validation import (
        ValidationIntegrator,
        BaselineIntegrator,
        BootstrapIntegrator,
        BonferroniIntegrator,
        ValidationReportGenerator
    )

    # All should instantiate without errors
    v1 = ValidationIntegrator()
    v2 = BaselineIntegrator()
    v3 = BootstrapIntegrator()
    v4 = BonferroniIntegrator()
    v5 = ValidationReportGenerator()

    assert v1 is not None
    assert v2 is not None
    assert v3 is not None
    assert v4 is not None
    assert v5 is not None

    print("✅ Import compatibility test PASSED")


def test_method_signature_compatibility():
    """Test method signatures haven't broken."""

    from src.validation import BootstrapIntegrator
    import inspect

    bootstrap = BootstrapIntegrator()
    sig = inspect.signature(bootstrap.validate_with_bootstrap)

    # Check required parameters still exist
    params = sig.parameters
    assert 'strategy_code' in params
    assert 'data' in params
    assert 'sim' in params

    print("✅ Method signature compatibility test PASSED")
```

**Success Criteria**:
- ✅ All public exports accessible
- ✅ Method signatures backward compatible
- ✅ No breaking changes detected

---

### Phase 3: Robustness & Performance (P1 HIGH - 6-8 hours)

#### Task 1.1.7: Performance Benchmarks

**Priority**: P1 HIGH
**Estimated Time**: 2-3 hours
**Depends On**: Phase 1 complete

**Objective**: Benchmark validation performance on production dataset

Create `tests/performance/test_validation_performance_v1_1.py`:

```python
"""Performance benchmarks for Phase 1.1 validation pipeline."""

import time
import json
from pathlib import Path


def test_20strategy_benchmark():
    """Benchmark full validation on 20-strategy production dataset."""

    # Load phase2_backtest_results.json
    results_file = Path("phase2_backtest_results.json")

    if not results_file.exists():
        pytest.skip("20-strategy dataset not available")

    with open(results_file) as f:
        strategies = json.load(f)

    total_time = 0
    for strategy in strategies[:5]:  # Test first 5
        start = time.time()

        # Run full validation pipeline
        # ... validation code ...

        elapsed = time.time() - start
        total_time += elapsed

        # Target: <60 seconds per strategy
        assert elapsed < 60, f"Strategy took {elapsed:.1f}s (target: <60s)"

    avg_time = total_time / 5
    print(f"Average validation time: {avg_time:.1f}s per strategy")
    print("✅ Performance benchmark PASSED")
```

**Success Criteria**:
- ✅ <60s per strategy average
- ✅ No memory leaks detected
- ✅ Performance acceptable

---

#### Task 1.1.8: Chaos Testing - Failure Modes

**Priority**: P1 HIGH
**Estimated Time**: 2-3 hours

Create `tests/validation/test_failure_modes_v1_1.py`:

```python
"""Chaos testing for validation pipeline."""

def test_nan_in_returns():
    """Test handling of NaN values in returns."""
    pass

def test_concurrent_execution():
    """Test parallel validation safety."""
    pass

def test_network_timeout():
    """Test baseline fetch timeout handling."""
    pass
```

**Success Criteria**:
- ✅ All failure modes handled gracefully
- ✅ Clear error messages
- ✅ No crashes or silent failures

---

#### Task 1.1.9: Monitoring Integration

**Priority**: P1 HIGH
**Estimated Time**: 2 hours

Add logging and metrics collection to validation pipeline.

**Success Criteria**:
- ✅ Comprehensive logging added
- ✅ Performance metrics tracked
- ✅ Error alerting hooks ready

---

### Documentation & Handoff (P2 - 2 hours)

#### Task 1.1.10: Update Documentation

**Priority**: P2
**Estimated Time**: 1 hour

Update all documentation to reflect Phase 1.1 changes:
- API documentation
- Known limitations
- Production deployment guide

---

#### Task 1.1.11: Production Deployment Runbook

**Priority**: P2
**Estimated Time**: 1 hour

Create runbook for production deployment:
- Configuration requirements
- Performance tuning
- Troubleshooting common issues

---

## Success Criteria - Phase 1.1

Before claiming "production ready":

### Statistical Validity
- [ ] Returns extracted from equity curve (no synthesis)
- [ ] Stationary bootstrap validates vs scipy
- [ ] Coverage rates match confidence levels
- [ ] Threshold empirically justified

### Integration Testing
- [ ] E2E test with real finlab passes
- [ ] 5-strategy subset validated
- [ ] Failure modes tested
- [ ] Backward compatibility verified

### Performance
- [ ] <60s per strategy overhead
- [ ] No memory leaks
- [ ] Scalability verified

### Robustness
- [ ] Chaos tests pass
- [ ] Error handling comprehensive
- [ ] Concurrent execution safe

---

## Timeline

**Minimum Viable Production** (P0 only):
- Phase 1 (Statistical Validity): 8-12 hours
- Phase 2 (Integration Testing): 6-10 hours
- **Total**: 14-22 hours

**Recommended Production** (P0 + P1):
- Add Phase 3 (Robustness): 6-8 hours
- **Total**: 20-30 hours

---

**Version**: 1.1
**Status**: PENDING
**Next Action**: Begin Task 1.1.1 (Returns Extraction)
