"""
Stationary Bootstrap for Financial Time Series

Implements Politis & Romano (1994) stationary bootstrap that preserves
temporal structure in financial returns while maintaining better statistical
properties than simple block bootstrap.

Key Features:
- Geometric block lengths (more flexible than fixed blocks)
- Circular wrapping for block continuation
- Preserves autocorrelation and volatility clustering
- Better suited for financial time series than simple bootstrap

Reference:
    Politis, D.N. and Romano, J.P. (1994). "The stationary bootstrap."
    Journal of the American Statistical Association, 89(428), 1303-1313.
"""

import numpy as np
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


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
    - Provides better coverage rates than simple block bootstrap

    Algorithm:
        For each bootstrap iteration:
        1. Start with empty resampled series
        2. While len(resampled) < n:
           a. Pick random start index
           b. Draw block length from Geometric(1/avg_block_size)
           c. Extract block with circular wrapping
           d. Append to resampled series
        3. Trim to exactly n elements
        4. Calculate Sharpe ratio on resampled series
        5. Aggregate results: point estimate (mean) and CI (percentiles)

    Args:
        returns: Daily returns series (np.ndarray)
        n_iterations: Bootstrap iterations (default 1000)
        avg_block_size: Average block size in days (default 21 ≈ 1 month)
        confidence_level: CI confidence level (default 0.95)

    Returns:
        Tuple[point_estimate, ci_lower, ci_upper]
        - point_estimate: Mean of bootstrap Sharpe ratios
        - ci_lower: Lower percentile of bootstrap distribution
        - ci_upper: Upper percentile of bootstrap distribution

    Raises:
        ValueError: If insufficient data (<252 days) or invalid parameters

    Example:
        >>> returns = np.random.randn(500) * 0.01  # 500 days of returns
        >>> point_est, ci_lower, ci_upper = stationary_bootstrap(returns)
        >>> print(f"Sharpe: {point_est:.3f} [{ci_lower:.3f}, {ci_upper:.3f}]")

    References:
        Politis, D.N. and Romano, J.P. (1994). "The stationary bootstrap."
        JASA, 89(428), 1303-1313.
    """
    n = len(returns)

    # Validation
    if n < 252:
        raise ValueError(
            f"Insufficient data for bootstrap: {n} days < 252 minimum. "
            f"Bootstrap on short history produces unreliable CIs."
        )

    if avg_block_size < 1:
        raise ValueError(f"avg_block_size must be >= 1, got {avg_block_size}")

    if not 0 < confidence_level < 1:
        raise ValueError(f"confidence_level must be in (0, 1), got {confidence_level}")

    if n_iterations < 100:
        raise ValueError(f"n_iterations must be >= 100 for reliable CIs, got {n_iterations}")

    bootstrap_sharpes = []

    for _ in range(n_iterations):
        resampled = []

        while len(resampled) < n:
            # Random starting point (uniform over entire series)
            start_idx = np.random.randint(0, n)

            # Geometric block length (key feature of stationary bootstrap)
            # p = 1/avg_block_size gives E[block_len] = avg_block_size
            block_len = min(
                np.random.geometric(1.0 / avg_block_size),
                n  # Cap at series length
            )

            # Extract block with circular wrapping
            # Circular wrapping allows blocks to wrap around the end of the series
            indices = (np.arange(block_len) + start_idx) % n
            resampled.extend(returns[indices])

        # Trim to exact length (will be slightly longer due to block addition)
        resampled_returns = np.array(resampled[:n])

        # Calculate Sharpe ratio on resampled data
        if len(resampled_returns) > 0 and np.std(resampled_returns) > 0:
            mean_ret = np.mean(resampled_returns)
            std_ret = np.std(resampled_returns, ddof=1)
            sharpe = (mean_ret / std_ret) * np.sqrt(252)  # Annualized
            bootstrap_sharpes.append(sharpe)

    # Handle edge case: all bootstrap iterations failed
    if len(bootstrap_sharpes) == 0:
        raise ValueError(
            "All bootstrap iterations failed (zero std or invalid data). "
            "Check input returns for validity."
        )

    # Point estimate and confidence intervals
    bootstrap_sharpes = np.array(bootstrap_sharpes)
    point_estimate = np.mean(bootstrap_sharpes)

    # Percentile method for CI
    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_sharpes, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_sharpes, 100 * (1 - alpha / 2))

    logger.debug(
        f"Stationary bootstrap complete: "
        f"point={point_estimate:.4f}, "
        f"CI=[{ci_lower:.4f}, {ci_upper:.4f}], "
        f"n_iterations={n_iterations}, "
        f"avg_block_size={avg_block_size}"
    )

    return point_estimate, ci_lower, ci_upper


def stationary_bootstrap_detailed(
    returns: np.ndarray,
    n_iterations: int = 1000,
    avg_block_size: int = 21,
    confidence_level: float = 0.95
) -> dict:
    """
    Stationary bootstrap with detailed diagnostics.

    Same as stationary_bootstrap() but returns additional diagnostic information
    useful for debugging and validation.

    Args:
        returns: Daily returns series
        n_iterations: Bootstrap iterations
        avg_block_size: Average block size
        confidence_level: CI confidence level

    Returns:
        Dictionary with:
        - point_estimate: Mean of bootstrap Sharpe ratios
        - ci_lower: Lower CI bound
        - ci_upper: Upper CI bound
        - bootstrap_distribution: Full array of bootstrap Sharpe ratios
        - original_sharpe: Sharpe ratio of original returns
        - n_valid_iterations: Number of successful iterations
        - avg_actual_block_size: Mean block size used
    """
    n = len(returns)

    if n < 252:
        raise ValueError(f"Insufficient data: {n} days < 252 minimum")

    bootstrap_sharpes = []
    actual_block_sizes = []

    for _ in range(n_iterations):
        resampled = []
        iteration_blocks = []

        while len(resampled) < n:
            start_idx = np.random.randint(0, n)
            block_len = min(np.random.geometric(1.0 / avg_block_size), n)
            iteration_blocks.append(block_len)

            indices = (np.arange(block_len) + start_idx) % n
            resampled.extend(returns[indices])

        actual_block_sizes.append(np.mean(iteration_blocks))

        resampled_returns = np.array(resampled[:n])

        if len(resampled_returns) > 0 and np.std(resampled_returns) > 0:
            mean_ret = np.mean(resampled_returns)
            std_ret = np.std(resampled_returns, ddof=1)
            sharpe = (mean_ret / std_ret) * np.sqrt(252)
            bootstrap_sharpes.append(sharpe)

    if len(bootstrap_sharpes) == 0:
        raise ValueError("All bootstrap iterations failed")

    bootstrap_sharpes = np.array(bootstrap_sharpes)
    point_estimate = np.mean(bootstrap_sharpes)

    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_sharpes, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_sharpes, 100 * (1 - alpha / 2))

    # Calculate original Sharpe ratio
    original_mean = np.mean(returns)
    original_std = np.std(returns, ddof=1)
    original_sharpe = (original_mean / original_std) * np.sqrt(252) if original_std > 0 else np.nan

    return {
        'point_estimate': point_estimate,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'bootstrap_distribution': bootstrap_sharpes,
        'original_sharpe': original_sharpe,
        'n_valid_iterations': len(bootstrap_sharpes),
        'avg_actual_block_size': np.mean(actual_block_sizes),
        'confidence_level': confidence_level,
        'n_iterations': n_iterations,
        'avg_block_size': avg_block_size
    }


__all__ = [
    'stationary_bootstrap',
    'stationary_bootstrap_detailed'
]
