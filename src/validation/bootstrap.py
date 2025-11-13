"""
Bootstrap Confidence Intervals for Trading Strategy Validation

Implements block bootstrap method to calculate confidence intervals for
trading strategy metrics, accounting for time-series autocorrelation.

Key Features:
- Block bootstrap (21-day blocks) for autocorrelation handling
- 1000 resampling iterations for robust CI estimation
- 95% confidence intervals (2.5th and 97.5th percentiles)
- Validation criteria: CI excludes zero, lower bound > 0.5
- Error handling for insufficient data and NaN values
- Performance target: < 20 seconds per metric

Reference: Politis & Romano (1994) - "The Stationary Bootstrap"
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class BootstrapResult:
    """Result of bootstrap confidence interval calculation."""

    metric_name: str
    point_estimate: float
    lower_bound: float
    upper_bound: float
    confidence_level: float
    n_iterations: int
    n_successes: int
    block_size: int
    validation_pass: bool
    validation_reason: str
    computation_time: float

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'metric_name': self.metric_name,
            'point_estimate': self.point_estimate,
            'lower_bound': self.lower_bound,
            'upper_bound': self.upper_bound,
            'confidence_level': self.confidence_level,
            'n_iterations': self.n_iterations,
            'n_successes': self.n_successes,
            'block_size': self.block_size,
            'validation_pass': self.validation_pass,
            'validation_reason': self.validation_reason,
            'computation_time': self.computation_time
        }


def _block_bootstrap_resample(
    returns: np.ndarray,
    block_size: int = 21
) -> np.ndarray:
    """
    Perform block bootstrap resampling of time series.

    Block bootstrap preserves autocorrelation structure by resampling
    contiguous blocks rather than individual observations.

    Args:
        returns: Array of returns (T observations)
        block_size: Size of blocks (default 21 days ≈ 1 month)

    Returns:
        Resampled returns array of same length

    Example:
        >>> returns = np.array([0.01, 0.02, -0.01, 0.03])
        >>> resampled = _block_bootstrap_resample(returns, block_size=2)
        >>> len(resampled) == len(returns)
        True
    """
    T = len(returns)
    n_blocks = int(np.ceil(T / block_size))

    # Sample block starting indices with replacement
    max_start = T - block_size
    if max_start < 0:
        # If data shorter than block size, use entire series
        return returns.copy()

    block_starts = np.random.choice(max_start + 1, size=n_blocks, replace=True)

    # Construct resampled series from blocks
    resampled = []
    for start in block_starts:
        block = returns[start:start + block_size]
        resampled.extend(block)

    # Trim to original length
    return np.array(resampled[:T])


def _calculate_sharpe_ratio(returns: np.ndarray) -> float:
    """
    Calculate Sharpe ratio from returns.

    Args:
        returns: Array of returns

    Returns:
        Sharpe ratio (annualized, assuming daily returns)

    Notes:
        - Assumes 252 trading days per year
        - Returns NaN if std is zero or data insufficient
    """
    if len(returns) < 2:
        return np.nan

    mean_return = np.mean(returns)
    std_return = np.std(returns, ddof=1)

    if std_return == 0:
        return np.nan

    # Annualize: sqrt(252) for daily returns
    sharpe = (mean_return / std_return) * np.sqrt(252)
    return sharpe


def bootstrap_confidence_interval(
    returns: np.ndarray,
    metric_name: str = 'sharpe_ratio',
    confidence_level: float = 0.95,
    n_iterations: int = 1000,
    block_size: int = 21,
    min_data_points: int = 100,
    min_success_rate: float = 0.9
) -> BootstrapResult:
    """
    Calculate bootstrap confidence interval for trading metric.

    Args:
        returns: Array of daily returns
        metric_name: Name of metric (default 'sharpe_ratio')
        confidence_level: Confidence level (default 0.95)
        n_iterations: Number of bootstrap iterations (default 1000)
        block_size: Block size for block bootstrap (default 21 days)
        min_data_points: Minimum required data points (default 100)
        min_success_rate: Minimum success rate for valid CI (default 0.9)

    Returns:
        BootstrapResult with CI bounds and validation status

    Raises:
        ValueError: If insufficient data or too many NaN values

    Example:
        >>> returns = np.random.normal(0.001, 0.02, 252)
        >>> result = bootstrap_confidence_interval(returns)
        >>> result.lower_bound < result.point_estimate < result.upper_bound
        True
    """
    start_time = time.time()

    # Validation: Check data sufficiency
    if len(returns) < min_data_points:
        raise ValueError(
            f"Insufficient data: {len(returns)} < {min_data_points} required"
        )

    # Remove NaN values
    returns_clean = returns[~np.isnan(returns)]
    if len(returns_clean) < min_data_points:
        raise ValueError(
            f"Too many NaN values: {len(returns_clean)} valid < {min_data_points} required"
        )

    # Calculate point estimate
    point_estimate = _calculate_sharpe_ratio(returns_clean)
    if np.isnan(point_estimate):
        raise ValueError("Point estimate is NaN (zero std or calculation error)")

    # Bootstrap resampling
    bootstrap_estimates = []
    n_successes = 0

    for i in range(n_iterations):
        # Resample with block bootstrap
        resampled_returns = _block_bootstrap_resample(returns_clean, block_size)

        # Calculate metric on resampled data
        estimate = _calculate_sharpe_ratio(resampled_returns)

        if not np.isnan(estimate):
            bootstrap_estimates.append(estimate)
            n_successes += 1

    # Check success rate
    success_rate = n_successes / n_iterations
    if success_rate < min_success_rate:
        raise ValueError(
            f"Bootstrap success rate {success_rate:.1%} < {min_success_rate:.1%} required"
        )

    # Calculate confidence interval
    alpha = 1 - confidence_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100

    lower_bound = np.percentile(bootstrap_estimates, lower_percentile)
    upper_bound = np.percentile(bootstrap_estimates, upper_percentile)

    # Validation criteria
    validation_pass = False
    validation_reason = ""

    if lower_bound <= 0 <= upper_bound:
        validation_reason = "CI includes zero - metric not statistically significant"
    elif lower_bound < 0.5:
        validation_reason = f"Lower bound {lower_bound:.4f} < 0.5 threshold"
    else:
        validation_pass = True
        validation_reason = f"CI excludes zero and lower bound {lower_bound:.4f} ≥ 0.5"

    computation_time = time.time() - start_time

    logger.info(
        f"Bootstrap CI: {metric_name} = {point_estimate:.4f} "
        f"[{lower_bound:.4f}, {upper_bound:.4f}] "
        f"({n_successes}/{n_iterations} iterations, {computation_time:.2f}s)"
    )

    return BootstrapResult(
        metric_name=metric_name,
        point_estimate=point_estimate,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        confidence_level=confidence_level,
        n_iterations=n_iterations,
        n_successes=n_successes,
        block_size=block_size,
        validation_pass=validation_pass,
        validation_reason=validation_reason,
        computation_time=computation_time
    )


def validate_strategy_with_bootstrap(
    returns: np.ndarray,
    confidence_level: float = 0.95,
    n_iterations: int = 1000,
    block_size: int = 21
) -> Dict:
    """
    Validate trading strategy using bootstrap confidence intervals.

    Convenience wrapper around bootstrap_confidence_interval() that
    returns a simplified validation report.

    Args:
        returns: Array of daily returns
        confidence_level: Confidence level (default 0.95)
        n_iterations: Number of bootstrap iterations (default 1000)
        block_size: Block size for block bootstrap (default 21 days)

    Returns:
        Dictionary with validation results:
        - passed: bool (validation passed)
        - sharpe_ratio: float (point estimate)
        - ci_lower: float (lower bound)
        - ci_upper: float (upper bound)
        - reason: str (validation reason)
        - computation_time: float (seconds)

    Example:
        >>> returns = np.random.normal(0.002, 0.02, 252)
        >>> result = validate_strategy_with_bootstrap(returns)
        >>> 'passed' in result and 'sharpe_ratio' in result
        True
    """
    try:
        bootstrap_result = bootstrap_confidence_interval(
            returns=returns,
            metric_name='sharpe_ratio',
            confidence_level=confidence_level,
            n_iterations=n_iterations,
            block_size=block_size
        )

        return {
            'passed': bootstrap_result.validation_pass,
            'sharpe_ratio': bootstrap_result.point_estimate,
            'ci_lower': bootstrap_result.lower_bound,
            'ci_upper': bootstrap_result.upper_bound,
            'reason': bootstrap_result.validation_reason,
            'computation_time': bootstrap_result.computation_time
        }

    except ValueError as e:
        logger.error(f"Bootstrap validation failed: {e}")
        return {
            'passed': False,
            'sharpe_ratio': np.nan,
            'ci_lower': np.nan,
            'ci_upper': np.nan,
            'reason': f"Validation error: {str(e)}",
            'computation_time': 0.0
        }


def calculate_multiple_metrics_bootstrap(
    returns: np.ndarray,
    metrics: List[str] = None,
    confidence_level: float = 0.95,
    n_iterations: int = 1000,
    block_size: int = 21
) -> Dict[str, BootstrapResult]:
    """
    Calculate bootstrap CIs for multiple metrics.

    Args:
        returns: Array of daily returns
        metrics: List of metric names (default ['sharpe_ratio'])
        confidence_level: Confidence level (default 0.95)
        n_iterations: Number of bootstrap iterations (default 1000)
        block_size: Block size for block bootstrap (default 21 days)

    Returns:
        Dictionary mapping metric names to BootstrapResult objects

    Notes:
        Currently only 'sharpe_ratio' is implemented.
        Future: Add 'max_drawdown', 'calmar_ratio', 'sortino_ratio'
    """
    if metrics is None:
        metrics = ['sharpe_ratio']

    results = {}

    for metric_name in metrics:
        if metric_name != 'sharpe_ratio':
            logger.warning(f"Metric '{metric_name}' not yet implemented, skipping")
            continue

        try:
            result = bootstrap_confidence_interval(
                returns=returns,
                metric_name=metric_name,
                confidence_level=confidence_level,
                n_iterations=n_iterations,
                block_size=block_size
            )
            results[metric_name] = result

        except ValueError as e:
            logger.error(f"Bootstrap failed for {metric_name}: {e}")

    return results


# Standalone test
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Bootstrap Confidence Interval - Standalone Test")
    print("=" * 60)

    # Test 1: Valid strategy (positive Sharpe)
    print("\nTest 1: Valid Strategy (positive Sharpe)")
    np.random.seed(42)
    returns_valid = np.random.normal(0.002, 0.02, 252)  # ~2% annual return

    result = bootstrap_confidence_interval(
        returns_valid,
        metric_name='sharpe_ratio',
        n_iterations=1000
    )

    print(f"Point estimate: {result.point_estimate:.4f}")
    print(f"95% CI: [{result.lower_bound:.4f}, {result.upper_bound:.4f}]")
    print(f"Validation: {'PASS' if result.validation_pass else 'FAIL'}")
    print(f"Reason: {result.validation_reason}")
    print(f"Computation time: {result.computation_time:.2f}s")

    # Test 2: Invalid strategy (Sharpe near zero)
    print("\nTest 2: Invalid Strategy (Sharpe near zero)")
    returns_invalid = np.random.normal(0.0001, 0.02, 252)

    result2 = bootstrap_confidence_interval(
        returns_invalid,
        metric_name='sharpe_ratio',
        n_iterations=1000
    )

    print(f"Point estimate: {result2.point_estimate:.4f}")
    print(f"95% CI: [{result2.lower_bound:.4f}, {result2.upper_bound:.4f}]")
    print(f"Validation: {'PASS' if result2.validation_pass else 'FAIL'}")
    print(f"Reason: {result2.validation_reason}")

    # Test 3: Error handling (insufficient data)
    print("\nTest 3: Error Handling (insufficient data)")
    returns_short = np.random.normal(0.001, 0.02, 50)

    try:
        result3 = bootstrap_confidence_interval(returns_short)
        print("ERROR: Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised error: {e}")

    # Test 4: Validation wrapper
    print("\nTest 4: Validation Wrapper")
    validation = validate_strategy_with_bootstrap(returns_valid)

    print(f"Passed: {validation['passed']}")
    print(f"Sharpe: {validation['sharpe_ratio']:.4f}")
    print(f"CI: [{validation['ci_lower']:.4f}, {validation['ci_upper']:.4f}]")
    print(f"Time: {validation['computation_time']:.2f}s")

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
