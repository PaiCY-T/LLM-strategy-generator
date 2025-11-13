# Phase 2 Validation Framework - Remediation Plan

**Date**: 2025-10-31
**Status**: ACTIONABLE - Based on Gemini 2.5 Pro Technical Review
**Priority**: P0 BLOCKING for Production Deployment

---

## Executive Summary

Following critical analysis by Gemini 2.5 Pro, this remediation plan addresses three critical flaws identified in the Phase 2 Validation Framework:

1. **Statistically unsound returns synthesis** → Replace with proper equity curve extraction
2. **Arbitrary 0.5 threshold** → Establish empirical Taiwan market benchmark
3. **Superficial test coverage** → Add integration, statistical, and failure mode tests

**Good News**: Codebase analysis reveals finlab Report objects **already expose equity curve** via `report.equity` attribute. This means **Option C (equity curve differentiation) is viable** - no architectural changes needed!

---

## Critical Discovery: Equity Curve is Available!

### Evidence from Codebase

**File**: `src/validation/metric_validator.py:375-383`

```python
elif hasattr(report, 'equity') and report.equity is not None:
    # Calculate returns from equity curve
    try:
        equity = report.equity
        if isinstance(equity, (pd.Series, pd.DataFrame)):
            if isinstance(equity, pd.DataFrame):
                equity = equity.iloc[:, 0]  # Take first column if DataFrame
            daily_returns = equity.pct_change().dropna()
            audit_trail['extraction_warnings'].append("Daily returns calculated from report.equity")
    except Exception as e:
        audit_trail['extraction_warnings'].append(f"Failed to calculate returns from equity: {e}")
```

**Implication**: We can extract actual returns from equity curve, **eliminating the need for synthesis**!

### Additional Fallback Options

The codebase shows multi-layered extraction (from `src/validation/metric_validator.py:359-385`):

1. **Primary**: `report.returns` (direct returns series)
2. **Secondary**: `report.daily_returns` (alternative attribute name)
3. **Tertiary**: Calculate from `report.position` (position changes)
4. **Quaternary**: Calculate from `report.equity` (equity curve differentiation)

---

## Remediation Plan: Three Phases

### Phase 1: Statistical Validity (P0 CRITICAL - 8-12 hours)

**Blocking Priority** - Must complete before production deployment

#### Task 1.1: Replace Returns Synthesis with Equity Curve Extraction (4-6 hours)

**Current Flawed Code** (`src/validation/integration.py:495-517`):
```python
def _extract_returns_from_report(self, report, sharpe_ratio, total_return, n_days=252):
    # FLAWED: Synthesizes i.i.d. normal returns
    if sharpe_ratio > 0 and total_return > 0:
        mean_return = total_return / n_days
        std_return = (mean_return / sharpe_ratio) * np.sqrt(252)
        synthetic_returns = np.random.normal(mean_return, std_return, n_days)
        return synthetic_returns
    return None
```

**New Robust Implementation**:
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

    Multi-layered extraction strategy:
    1. Try report.returns (direct)
    2. Try report.daily_returns (alternative attribute)
    3. Calculate from report.equity (equity curve pct_change)
    4. Calculate from report.position (position value changes)
    5. FAIL with clear error (synthesis removed)

    Args:
        report: finlab backtest Report object
        sharpe_ratio: Fallback for validation (not used for extraction)
        total_return: Fallback for validation (not used for extraction)
        n_days: Expected minimum trading days (default 252 = 1 year)

    Returns:
        np.ndarray of daily returns, or None if extraction fails

    Raises:
        ValueError: If all extraction methods fail
    """
    import pandas as pd

    # Method 1: Direct returns attribute
    if hasattr(report, 'returns') and report.returns is not None:
        returns = np.array(report.returns)
        if len(returns) >= n_days:
            return returns
        else:
            raise ValueError(
                f"Insufficient data: {len(returns)} days < minimum {n_days} days required"
            )

    # Method 2: Alternative returns attribute
    if hasattr(report, 'daily_returns') and report.daily_returns is not None:
        returns = np.array(report.daily_returns)
        if len(returns) >= n_days:
            return returns
        else:
            raise ValueError(
                f"Insufficient data: {len(returns)} days < minimum {n_days} days required"
            )

    # Method 3: Calculate from equity curve (MOST LIKELY TO WORK)
    if hasattr(report, 'equity') and report.equity is not None:
        equity = report.equity

        # Handle DataFrame vs Series
        if isinstance(equity, pd.DataFrame):
            equity = equity.iloc[:, 0]  # Take first column

        if isinstance(equity, pd.Series):
            # Calculate percentage changes (daily returns)
            daily_returns = equity.pct_change().dropna()
            returns = daily_returns.values

            if len(returns) >= n_days:
                return returns
            else:
                raise ValueError(
                    f"Insufficient data: {len(returns)} days < minimum {n_days} days required"
                )

    # Method 4: Calculate from position values
    if hasattr(report, 'position') and report.position is not None:
        position = report.position
        if isinstance(position, pd.DataFrame):
            # Sum across all positions to get total portfolio value
            total_value = position.sum(axis=1)
            daily_returns = total_value.pct_change().dropna()
            returns = daily_returns.values

            if len(returns) >= n_days:
                return returns
            else:
                raise ValueError(
                    f"Insufficient data: {len(returns)} days < minimum {n_days} days required"
                )

    # All methods failed - this is a critical error
    available_attrs = [attr for attr in dir(report) if not attr.startswith('_')][:20]
    raise ValueError(
        f"Failed to extract returns from finlab Report. "
        f"Tried: returns, daily_returns, equity, position. "
        f"Available attributes: {available_attrs}. "
        f"Cannot proceed with bootstrap validation."
    )
```

**Testing**:
- Unit test with mock Report objects (equity, returns, position)
- Integration test with real finlab Report from backtest
- Edge case test: Short history (<252 days) should raise ValueError

**Deliverables**:
1. Updated `src/validation/integration.py`
2. New test file: `test_returns_extraction_robust.py`
3. Documentation: Updated docstrings

---

#### Task 1.2: Implement Proper Stationary Bootstrap (3-4 hours)

**Replace simple block bootstrap with Politis & Romano stationary bootstrap**

**Current Simple Block Bootstrap**:
```python
# Current approach (too simplistic)
block_len = 21
start = np.random.randint(0, n)
block = returns[start:start+block_len]
```

**New Stationary Bootstrap Implementation**:
```python
def stationary_bootstrap(
    returns: np.ndarray,
    n_iterations: int = 1000,
    avg_block_size: int = 21,
    confidence_level: float = 0.95
) -> Tuple[float, float, float]:
    """
    Stationary bootstrap for Sharpe ratio confidence intervals.

    Implements Politis & Romano (1994) stationary bootstrap that:
    - Preserves temporal structure (autocorrelation, volatility clustering)
    - Uses geometric block lengths (more flexible than fixed blocks)
    - Handles circular wrapping for block continuation

    Args:
        returns: Daily returns series (np.ndarray)
        n_iterations: Number of bootstrap iterations (default 1000)
        avg_block_size: Average block size in days (default 21 = ~1 month)
        confidence_level: Confidence level for CI (default 0.95)

    Returns:
        Tuple[point_estimate, ci_lower, ci_upper]

    References:
        Politis, D.N. and Romano, J.P. (1994). "The stationary bootstrap."
        Journal of the American Statistical Association, 89(428), 1303-1313.
    """
    n = len(returns)
    if n < 252:
        raise ValueError(
            f"Insufficient data for bootstrap: {n} days < 252 days minimum. "
            f"Bootstrap on short history produces unreliable confidence intervals."
        )

    bootstrap_sharpes = []

    for _ in range(n_iterations):
        resampled = []

        # Resample until we have n returns
        while len(resampled) < n:
            # Random starting point
            start_idx = np.random.randint(0, n)

            # Geometric block length (stationary bootstrap key feature)
            block_len = min(
                np.random.geometric(1.0 / avg_block_size),
                n  # Cap at series length
            )

            # Extract block with circular wrapping
            indices = (np.arange(block_len) + start_idx) % n
            resampled.extend(returns[indices])

        # Trim to exact length
        resampled_returns = np.array(resampled[:n])

        # Calculate Sharpe ratio for this bootstrap sample
        if len(resampled_returns) > 0 and np.std(resampled_returns) > 0:
            mean_return = np.mean(resampled_returns)
            std_return = np.std(resampled_returns)
            # Annualize: Sharpe = (mean * 252) / (std * sqrt(252))
            sharpe = (mean_return / std_return) * np.sqrt(252)
            bootstrap_sharpes.append(sharpe)

    # Calculate point estimate and confidence intervals
    bootstrap_sharpes = np.array(bootstrap_sharpes)
    point_estimate = np.mean(bootstrap_sharpes)

    # Percentile method for CI
    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_sharpes, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_sharpes, 100 * (1 - alpha / 2))

    return point_estimate, ci_lower, ci_upper
```

**Integration into BootstrapIntegrator**:
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
    avg_block_size: int = 21,  # Renamed from block_size
    iteration_num: int = 0
) -> Dict[str, Any]:
    """Validate strategy with stationary bootstrap confidence intervals."""

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

    # Extract actual returns from Report object
    try:
        returns = self._extract_returns_from_report(
            report=result.report,
            sharpe_ratio=result.sharpe_ratio,
            total_return=result.total_return,
            n_days=252  # Minimum 1 year required
        )
    except ValueError as e:
        return {
            'validation_passed': False,
            'error': str(e),
            'sharpe_ratio': result.sharpe_ratio,
            'iteration_num': iteration_num
        }

    # Perform stationary bootstrap
    try:
        point_estimate, ci_lower, ci_upper = stationary_bootstrap(
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

    # Validation criteria: CI excludes zero AND lower bound > 0.5
    validation_passed = (ci_lower > 0) and (ci_lower >= 0.5)

    return {
        'validation_passed': validation_passed,
        'sharpe_ratio': point_estimate,
        'sharpe_ratio_original': result.sharpe_ratio,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'confidence_level': confidence_level,
        'n_iterations': n_iterations,
        'n_days': len(returns),
        'avg_block_size': avg_block_size,
        'iteration_num': iteration_num,
        'validation_reason': (
            f"CI [{ci_lower:.3f}, {ci_upper:.3f}] excludes zero and lower bound ≥ 0.5"
            if validation_passed else
            f"CI [{ci_lower:.3f}, {ci_upper:.3f}] does not meet criteria"
        )
    }
```

**Testing**:
- Statistical validation: Compare against `scipy.stats.bootstrap`
- Test with known returns series (e.g., S&P 500 historical data)
- Verify CI coverage rates match confidence level
- Edge case: <252 days should raise ValueError
- Stress test: 1000 iterations performance benchmark

---

#### Task 1.3: Establish Empirical Taiwan Market Threshold (2-3 hours)

**Research & Implementation**

**Step 1: Research Taiwan Passive Benchmarks** (1 hour)
- Historical Sharpe ratio of 0050.TW (Yuanta Taiwan 50 ETF)
- Analysis period: 2018-01-01 to 2024-12-31 (7 years)
- Calculate rolling 3-year Sharpe ratios
- Identify market regime variations

**Step 2: Implement Dynamic Threshold** (1-2 hours)

```python
class DynamicThresholdCalculator:
    """Calculate dynamic Sharpe ratio threshold based on Taiwan market benchmarks."""

    def __init__(
        self,
        benchmark_ticker: str = "0050.TW",
        lookback_years: int = 3,
        margin: float = 0.2
    ):
        """
        Initialize dynamic threshold calculator.

        Args:
            benchmark_ticker: Taiwan benchmark ETF (default: 0050.TW)
            lookback_years: Rolling window for benchmark Sharpe (default: 3 years)
            margin: Required improvement over benchmark (default: 0.2)
        """
        self.benchmark_ticker = benchmark_ticker
        self.lookback_years = lookback_years
        self.margin = margin
        self._cached_threshold = None
        self._cache_timestamp = None

    def get_threshold(self, current_date: Optional[str] = None) -> float:
        """
        Calculate current dynamic threshold.

        Returns threshold = max(benchmark_sharpe + margin, 0.0)

        The floor of 0.0 ensures strategy has positive risk-adjusted returns.

        Args:
            current_date: Date for threshold calculation (default: today)

        Returns:
            float: Dynamic Sharpe ratio threshold
        """
        # Implementation would fetch benchmark data and calculate
        # For now, use conservative static threshold pending data access

        # TODO: Implement actual benchmark fetching
        # benchmark_sharpe = self._calculate_benchmark_sharpe(current_date)
        # return max(benchmark_sharpe + self.margin, 0.0)

        # Temporary: Use 0.5 as conservative floor
        # This should be replaced with actual benchmark calculation
        return 0.5

    def _calculate_benchmark_sharpe(self, end_date: str) -> float:
        """
        Calculate benchmark Sharpe ratio over lookback period.

        Args:
            end_date: End date for calculation

        Returns:
            float: Benchmark Sharpe ratio
        """
        # Fetch benchmark data (0050.TW)
        # Calculate returns over lookback_years
        # Calculate Sharpe ratio
        # Return result
        pass
```

**Integration into BonferroniIntegrator**:
```python
class BonferroniIntegrator:
    def __init__(
        self,
        n_strategies: int = 20,
        alpha: float = 0.05,
        use_dynamic_threshold: bool = True
    ):
        from src.validation.multiple_comparison import BonferroniValidator

        self.validator = BonferroniValidator(n_strategies, alpha)
        self.n_strategies = n_strategies
        self.alpha = alpha

        # Dynamic threshold calculator
        if use_dynamic_threshold:
            self.threshold_calc = DynamicThresholdCalculator(
                benchmark_ticker="0050.TW",
                lookback_years=3,
                margin=0.2
            )
        else:
            self.threshold_calc = None

    def validate_single_strategy(
        self,
        sharpe_ratio: float,
        n_periods: int = 252,
        use_conservative: bool = True
    ) -> Dict[str, Any]:
        """Validate single strategy with dynamic or conservative threshold."""

        result = self.validator.validate(sharpe_ratio, n_periods)

        if use_conservative:
            if self.threshold_calc:
                # Dynamic threshold
                dynamic_threshold = self.threshold_calc.get_threshold()
                significance_threshold = max(result['significance_threshold'], dynamic_threshold)
            else:
                # Static conservative threshold
                significance_threshold = max(result['significance_threshold'], 0.5)
        else:
            significance_threshold = result['significance_threshold']

        validation_passed = sharpe_ratio > significance_threshold

        return {
            'validation_passed': validation_passed,
            'sharpe_ratio': sharpe_ratio,
            'significance_threshold': significance_threshold,
            'adjusted_alpha': self.alpha / self.n_strategies,
            'n_strategies': self.n_strategies,
            'validation_reason': (
                f"Sharpe {sharpe_ratio:.3f} > threshold {significance_threshold:.3f}"
                if validation_passed else
                f"Sharpe {sharpe_ratio:.3f} ≤ threshold {significance_threshold:.3f}"
            )
        }
```

**Deliverables**:
1. Research report: Taiwan market benchmark analysis
2. Implementation: `src/validation/dynamic_threshold.py`
3. Integration: Updated `BonferroniIntegrator`
4. Tests: `test_dynamic_threshold.py`

---

### Phase 2: Integration Testing (P0 CRITICAL - 6-10 hours)

**Blocking Priority** - Must complete before production deployment

#### Task 2.1: E2E Pipeline Tests (3-5 hours)

**Test File**: `test_validation_pipeline_e2e.py`

```python
"""
End-to-end integration tests for validation pipeline.

Tests complete flow: Strategy execution → Report generation → All 5 validators → HTML report
"""

def test_full_validation_pipeline_real_strategy():
    """Test complete pipeline with real finlab execution."""

    # Use actual finlab data and sim
    from finlab import data
    from finlab.backtest import sim

    # Simple momentum strategy (known to work)
    strategy_code = '''
close = data.get("price:收盤價")
returns_20d = close.pct_change(20)
position = returns_20d.rank(axis=1, ascending=False) <= 30
report = sim(position, resample="Q", upload=False, mae_mfe_window=5, position_limit=0.5)
'''

    # Initialize all integrators
    validation_integrator = ValidationIntegrator()
    baseline_integrator = BaselineIntegrator()
    bootstrap_integrator = BootstrapIntegrator()
    bonferroni_integrator = BonferroniIntegrator(n_strategies=20)
    report_generator = ValidationReportGenerator(project_name="E2E Test")

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

    assert result.success, f"Strategy execution failed: {result.error_message}"
    assert result.sharpe_ratio is not None

    # Run all 5 validators
    oos_result = validation_integrator.validate_out_of_sample(
        strategy_code=strategy_code,
        data=data,
        sim=sim
    )

    wf_result = validation_integrator.validate_walk_forward(
        strategy_code=strategy_code,
        data=data,
        sim=sim
    )

    baseline_result = baseline_integrator.compare_with_baselines(
        strategy_code=strategy_code,
        data=data,
        sim=sim
    )

    bootstrap_result = bootstrap_integrator.validate_with_bootstrap(
        strategy_code=strategy_code,
        data=data,
        sim=sim,
        n_iterations=1000
    )

    bonferroni_result = bonferroni_integrator.validate_single_strategy(
        sharpe_ratio=result.sharpe_ratio
    )

    # All validators should return results
    assert 'validation_passed' in oos_result
    assert 'validation_passed' in wf_result
    assert 'validation_passed' in baseline_result
    assert 'validation_passed' in bootstrap_result
    assert 'validation_passed' in bonferroni_result

    # Generate comprehensive report
    report_generator.add_strategy_validation(
        strategy_name="E2E_Momentum_Test",
        iteration_num=0,
        out_of_sample_results=oos_result,
        walk_forward_results=wf_result,
        baseline_results=baseline_result,
        bootstrap_results=bootstrap_result,
        bonferroni_results=bonferroni_result
    )

    # Export reports
    html_report = report_generator.to_html()
    json_report = report_generator.to_json()

    assert len(html_report) > 1000, "HTML report too short"
    assert "E2E_Momentum_Test" in html_report

    import json
    json_data = json.loads(json_report)
    assert json_data['summary']['total_strategies'] == 1

    print("✅ Full E2E pipeline test PASSED")


def test_validation_with_5strategy_subset():
    """Test with 5 diverse strategies from Phase 2 dataset."""
    # Load 5 strategies from phase2_backtest_results.json
    # Run full validation pipeline
    # Verify all results are consistent
    pass


def test_validation_failure_modes():
    """Test pipeline with strategies that should fail validation."""

    # Strategy with negative Sharpe
    # Strategy with high volatility
    # Strategy with severe drawdown
    # Verify validators correctly reject these
    pass
```

**Deliverables**:
1. `test_validation_pipeline_e2e.py` with 5+ test scenarios
2. Test execution on 5-strategy subset
3. Verification against manual review

---

#### Task 2.2: Statistical Validation Tests (2-3 hours)

**Verify bootstrap implementation against trusted libraries**

**Test File**: `test_bootstrap_statistical_validity.py`

```python
"""
Statistical validation tests for bootstrap implementation.

Compares our stationary bootstrap against scipy.stats.bootstrap to verify:
1. CI coverage rates match specified confidence level
2. Point estimates are unbiased
3. CI widths are reasonable
"""

def test_bootstrap_vs_scipy():
    """Compare our bootstrap against scipy.stats.bootstrap."""

    # Generate known returns series
    np.random.seed(42)
    n_days = 500
    mean_daily = 0.0005  # 12.5% annual
    std_daily = 0.015    # 23.7% annual vol
    returns = np.random.normal(mean_daily, std_daily, n_days)

    # Calculate true Sharpe
    true_sharpe = (mean_daily / std_daily) * np.sqrt(252)

    # Our implementation
    from src.validation.integration import stationary_bootstrap
    our_point, our_lower, our_upper = stationary_bootstrap(
        returns, n_iterations=1000, avg_block_size=21
    )

    # scipy.stats.bootstrap (for comparison)
    from scipy import stats

    def sharpe_statistic(sample, axis):
        mean = np.mean(sample, axis=axis)
        std = np.std(sample, axis=axis)
        return (mean / std) * np.sqrt(252)

    scipy_result = stats.bootstrap(
        (returns,),
        sharpe_statistic,
        n_resamples=1000,
        confidence_level=0.95,
        method='percentile'
    )

    # Verify results are similar (within 20% due to random resampling)
    assert abs(our_point - scipy_result.bootstrap_distribution.mean()) / scipy_result.bootstrap_distribution.mean() < 0.2
    assert abs(our_lower - scipy_result.confidence_interval.low) / scipy_result.confidence_interval.low < 0.3
    assert abs(our_upper - scipy_result.confidence_interval.high) / scipy_result.confidence_interval.high < 0.3

    print(f"Our bootstrap: {our_point:.3f} [{our_lower:.3f}, {our_upper:.3f}]")
    print(f"Scipy: {scipy_result.bootstrap_distribution.mean():.3f} [{scipy_result.confidence_interval.low:.3f}, {scipy_result.confidence_interval.high:.3f}]")
    print("✅ Bootstrap statistical validity test PASSED")


def test_coverage_rate():
    """Verify 95% CI actually covers true parameter 95% of the time."""

    # Run 100 bootstrap experiments
    # Count how many times CI contains true Sharpe
    # Should be ~95 out of 100
    pass
```

---

### Phase 3: Robustness & Performance (P1 HIGH - 6-8 hours)

**Highly Recommended** - Significantly reduces operational risk

#### Task 3.1: Performance Benchmarks (2-3 hours)

**Test File**: `test_validation_performance.py`

```python
def test_20strategy_dataset_performance():
    """Benchmark full validation on 20-strategy production dataset."""

    import time

    # Load 20 strategies from phase2_backtest_results.json
    # Run full validation pipeline on each
    # Measure total time

    # Target: <60 seconds total overhead per strategy
    # (Bootstrap ~5s + others ~10s + reporting ~5s = ~20s total)
    pass


def test_100strategy_stress_test():
    """Stress test with 100 synthetic strategies."""

    # Generate 100 strategy variations
    # Monitor memory usage over time
    # Check for memory leaks
    # Verify performance doesn't degrade
    pass


def test_html_report_scalability():
    """Test HTML generation with 1000+ strategies."""

    # Generate report with 1000 mock validation results
    # Verify HTML renders correctly
    # Check file size is reasonable (<5MB)
    # Verify browser can load it
    pass
```

---

#### Task 3.2: Chaos Testing (2-3 hours)

**Test File**: `test_validation_failure_modes.py`

```python
def test_network_timeout_baseline_fetch():
    """Test behavior when baseline data fetch times out."""

    # Mock network failure for baseline ETF data
    # Verify system handles gracefully
    # Check error message is clear
    pass


def test_malformed_yaml_config():
    """Test with invalid configuration files."""

    # Invalid bootstrap parameters
    # Invalid threshold settings
    # Verify clear error messages
    pass


def test_concurrent_strategy_execution():
    """Test parallel validation of multiple strategies."""

    # Run 5 strategies in parallel
    # Verify no race conditions
    # Check baseline cache integrity
    pass


def test_nan_inf_in_returns():
    """Test with corrupted returns data."""

    # Returns with NaN values
    # Returns with inf values
    # Verify graceful error handling
    pass
```

---

## Summary: Implementation Checklist

### Phase 1: Statistical Validity (P0 - 8-12 hours)

- [ ] Task 1.1: Replace returns synthesis with equity curve extraction (4-6h)
  - [ ] Implement robust `_extract_returns_from_report()` with 4 fallback methods
  - [ ] Add minimum 252-day data requirement
  - [ ] Unit tests for extraction with mock Reports
  - [ ] Integration test with real finlab Report

- [ ] Task 1.2: Implement stationary bootstrap (3-4h)
  - [ ] Code Politis & Romano stationary bootstrap
  - [ ] Integrate into `BootstrapIntegrator.validate_with_bootstrap()`
  - [ ] Statistical validation vs scipy.stats.bootstrap
  - [ ] Coverage rate test (95% CI should cover true parameter 95% of time)

- [ ] Task 1.3: Establish empirical threshold (2-3h)
  - [ ] Research Taiwan 0050.TW historical Sharpe ratios
  - [ ] Implement `DynamicThresholdCalculator`
  - [ ] Integrate into `BonferroniIntegrator`
  - [ ] Document threshold justification

### Phase 2: Integration Testing (P0 - 6-10 hours)

- [ ] Task 2.1: E2E pipeline tests (3-5h)
  - [ ] Test with real finlab execution (momentum strategy)
  - [ ] Test with 5-strategy subset from Phase 2 dataset
  - [ ] Test failure modes (negative Sharpe, high vol strategies)
  - [ ] Verify HTML/JSON report generation

- [ ] Task 2.2: Statistical validation tests (2-3h)
  - [ ] Bootstrap vs scipy comparison
  - [ ] Coverage rate verification
  - [ ] Known returns series validation

- [ ] Task 2.3: Regression tests (1-2h)
  - [ ] Identify existing validation client code
  - [ ] Run client tests against new framework
  - [ ] Verify backward compatibility

### Phase 3: Robustness & Performance (P1 - 6-8 hours)

- [ ] Task 3.1: Performance benchmarks (2-3h)
  - [ ] 20-strategy dataset benchmark (<60s per strategy target)
  - [ ] 100-strategy stress test
  - [ ] HTML report scalability (1000+ strategies)
  - [ ] Memory leak detection

- [ ] Task 3.2: Chaos testing (2-3h)
  - [ ] Network timeout handling
  - [ ] Malformed config handling
  - [ ] Concurrent execution tests
  - [ ] NaN/inf data handling

- [ ] Task 3.3: Monitoring integration (2h)
  - [ ] Add comprehensive logging
  - [ ] Add performance metrics
  - [ ] Add error alerting hooks

---

## Timeline

**Minimum Production Readiness** (P0 only):
- Phase 1: 8-12 hours
- Phase 2: 6-10 hours
- **Total**: 14-22 hours

**Recommended Production Readiness** (P0 + P1):
- Phase 1: 8-12 hours
- Phase 2: 6-10 hours
- Phase 3: 6-8 hours
- **Total**: 20-30 hours

---

## Success Criteria

Before claiming "production ready":

1. **Statistical Validity**
   - [ ] Returns extracted from actual equity curve (no synthesis)
   - [ ] Stationary bootstrap validates against scipy
   - [ ] Coverage rates match confidence levels
   - [ ] Threshold based on empirical Taiwan market data

2. **Integration Testing**
   - [ ] E2E test with real finlab passes
   - [ ] 5-strategy subset validated successfully
   - [ ] Failure modes tested and handled gracefully

3. **Performance**
   - [ ] <60s overhead per strategy on 20-strategy dataset
   - [ ] No memory leaks in stress test
   - [ ] HTML report scales to 1000+ strategies

4. **Robustness**
   - [ ] All chaos tests pass
   - [ ] Clear error messages for all failure modes
   - [ ] Concurrent execution safe

---

**Status**: READY TO EXECUTE
**Next Action**: Begin Phase 1, Task 1.1 (Returns Extraction)
**Estimated Completion**: 14-22 hours for minimum viable production deployment
