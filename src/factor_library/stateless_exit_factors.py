"""
Stateless Exit Factors Module
==============================

Stateless exit strategy factors that do NOT require positions or entry_price matrices.
These factors use rolling window approximations to work within the Factor Graph's
to_pipeline() execution stage, which runs before sim() generates position state.

Architecture: Phase 2.0+ Factor Graph System (Matrix-Native)
Motivation: Resolves architectural time-sequence contradiction where EXIT factors
            need positions/entry_price but to_pipeline() executes before sim()

Available Factors:
-----------------
1. RollingTrailingStopFactor: Trailing stop using rolling max as proxy for highest price
2. RollingProfitTargetFactor: Profit target using rolling min as proxy for entry price

Key Differences from Stateful EXIT Factors:
-------------------------------------------
- **Stateful** (exit_factors.py): Requires positions, entry_price from sim() execution
- **Stateless** (this file): Only requires OHLCV data, works in to_pipeline() stage

Trade-offs:
----------
✅ Pros:
  - Compatible with Factor Graph architecture (no state dependencies)
  - Can execute in to_pipeline() before sim()
  - Suitable for template strategies and mutation system
  - Low implementation complexity

⚠️ Limitations:
  - Approximations based on rolling windows (not exact entry tracking)
  - Accuracy depends on lookback_periods parameter tuning
  - May produce false signals if holding time > lookback window
  - Less precise than stateful versions for long-term positions

Usage Example (Phase 2.0):
--------------------------
    from src.factor_library.stateless_exit_factors import (
        create_rolling_trailing_stop_factor,
        create_rolling_profit_target_factor
    )
    from src.factor_graph.finlab_dataframe import FinLabDataFrame
    from finlab import data

    # Create stateless exit factors
    trailing = create_rolling_trailing_stop_factor(
        trail_percent=0.10,
        lookback_periods=20
    )
    profit = create_rolling_profit_target_factor(
        target_percent=0.30,
        lookback_periods=20
    )

    # Execute factors on FinLabDataFrame container (no positions needed!)
    container = FinLabDataFrame(data_module=data)
    container.add_matrix('close', data.get('price:收盤價'))

    container = trailing.execute(container)
    container = profit.execute(container)

    # Exit signals are available
    trailing_signal = container.get_matrix('rolling_trailing_stop_signal')
    profit_signal = container.get_matrix('rolling_profit_target_signal')
"""

from typing import Dict, Any
import pandas as pd

from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.finlab_dataframe import FinLabDataFrame


# ============================================================================
# Factor Logic Functions
# ============================================================================

def _rolling_trailing_stop_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """
    Calculate trailing stop loss signal using rolling window approximation (Stateless).

    Unlike the stateful TrailingStopFactor which tracks exact highest price since entry,
    this uses a rolling window to approximate "highest price in recent periods".

    Approximation Strategy:
        rolling_high ≈ highest_since_entry (when holding_time <= lookback)

        For positions held longer than lookback, the approximation degrades because
        rolling_high resets every lookback periods, potentially using stale data.

    Args:
        container: FinLabDataFrame container with 'close' matrix
        parameters: Dictionary with:
            - trail_percent (float): Trailing stop percentage (e.g., 0.10 = 10%)
            - lookback_periods (int): Rolling window size (e.g., 20 = ~1 month)

    Modifies:
        Adds 'rolling_trailing_stop_signal' matrix to container (Dates×Symbols, boolean)

    Implementation:
        1. Calculate rolling highest price: rolling_high = close.rolling(lookback).max()
        2. Calculate stop level: stop_level = rolling_high * (1 - trail_percent)
        3. Generate exit signal: exit when close < stop_level
        4. Signal: True when stop is triggered, False otherwise

    Example:
        trail_percent=0.10, lookback_periods=20

        Day 1-20: close = [100, 102, 105, 103, 101, ...]
        Day 20: rolling_high = 105
                stop_level = 105 * 0.90 = 94.5
                close = 101 > 94.5 → signal = False (no exit)

        Day 21: close = 93
                rolling_high = 105 (still from window)
                stop_level = 94.5
                close = 93 < 94.5 → signal = True (EXIT!)

    Accuracy Notes:
        - Best for short-term strategies (holding < lookback periods)
        - Degrades for long-term positions (holding > lookback periods)
        - Recommended lookback: 10-20 for weekly/monthly strategies

    Phase 2.0 Changes:
        - Input: FinLabDataFrame container (not DataFrame)
        - Works with Dates×Symbols matrices (not columns)
        - Fully vectorized pandas operations
        - Modifies container in-place (no return)
    """
    trail_percent = parameters['trail_percent']
    lookback = parameters['lookback_periods']

    # Get close price matrix from container
    close = container.get_matrix('close')

    # Calculate rolling highest price (vectorized across all symbols)
    # min_periods=1 ensures we get values even in the initial window
    rolling_high = close.rolling(window=lookback, min_periods=1).max()

    # Calculate stop level: highest * (1 - trail_percent)
    stop_level = rolling_high * (1 - trail_percent)

    # Generate exit signal: True when price falls below stop level
    # This is a boolean Dates×Symbols matrix
    exit_signal = close < stop_level

    # Add exit signal matrix to container
    container.add_matrix('rolling_trailing_stop_signal', exit_signal)


def _rolling_profit_target_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """
    Calculate profit target exit signal using rolling window approximation (Stateless).

    Unlike the stateful ProfitTargetFactor which uses exact entry_price,
    this uses rolling minimum as a proxy for "recent entry price".

    Approximation Strategy:
        rolling_low ≈ entry_price (when entry is near the recent low point)

        This works well in trending markets where entries tend to occur near
        local lows. Accuracy degrades in choppy/ranging markets.

    Args:
        container: FinLabDataFrame container with 'close' matrix
        parameters: Dictionary with:
            - target_percent (float): Profit target percentage (e.g., 0.30 = 30%)
            - lookback_periods (int): Rolling window size (e.g., 20 = ~1 month)

    Modifies:
        Adds 'rolling_profit_target_signal' matrix to container (Dates×Symbols, boolean)

    Implementation:
        1. Calculate rolling lowest price: rolling_low = close.rolling(lookback).min()
        2. Estimate profit: approx_profit = (close / rolling_low) - 1
        3. Generate exit signal: exit when approx_profit >= target_percent
        4. Signal: True when target is reached, False otherwise

    Example:
        target_percent=0.30, lookback_periods=20

        Day 1-20: close = [100, 98, 95, 97, 100, 105, ...]
        Day 20: rolling_low = 95
                close = 105
                approx_profit = (105/95 - 1) = 0.105 = 10.5%
                10.5% < 30% → signal = False (no exit)

        Day 25: rolling_low = 95 (still in window)
                close = 125
                approx_profit = (125/95 - 1) = 0.316 = 31.6%
                31.6% > 30% → signal = True (EXIT! Take profit)

    Accuracy Notes:
        - Best when entries occur near rolling lows (trend-following strategies)
        - Works well in trending markets (clear highs/lows)
        - Less accurate in ranging/choppy markets
        - Recommended lookback: match expected holding period

    Phase 2.0 Changes:
        - Input: FinLabDataFrame container (not DataFrame)
        - Works with Dates×Symbols matrices (not columns)
        - Fully vectorized pandas operations
        - Modifies container in-place (no return)
    """
    target_percent = parameters['target_percent']
    lookback = parameters['lookback_periods']

    # Get close price matrix from container
    close = container.get_matrix('close')

    # Calculate rolling lowest price (vectorized across all symbols)
    # min_periods=1 ensures we get values even in the initial window
    rolling_low = close.rolling(window=lookback, min_periods=1).min()

    # Calculate approximate profit using rolling low as entry price proxy
    # Where rolling_low is 0 or NaN, profit will be NaN (handled by comparison)
    approx_profit = (close / rolling_low) - 1

    # Generate exit signal: True when approximate profit >= target
    # NaN values will be False (safe default)
    exit_signal = approx_profit >= target_percent

    # Add exit signal matrix to container
    container.add_matrix('rolling_profit_target_signal', exit_signal)


# ============================================================================
# Factor Classes
# ============================================================================

class RollingTrailingStopFactor(Factor):
    """
    Stateless trailing stop factor using rolling window approximation.

    Uses rolling maximum price as a proxy for "highest price since entry"
    to implement trailing stop logic without requiring position state.

    Category: EXIT
    Inputs: ["close"]
    Outputs: ["rolling_trailing_stop_signal"]
    Parameters:
        - trail_percent (float): Trailing stop percentage (e.g., 0.10 = 10%)
        - lookback_periods (int): Rolling window size (e.g., 20 periods)

    Comparison with Stateful TrailingStopFactor:
        Stateful: Exact highest_since_entry tracking per position
        Stateless: Rolling max approximation (resets every lookback periods)

    Example:
        >>> trailing = RollingTrailingStopFactor(
        ...     trail_percent=0.10,
        ...     lookback_periods=20
        ... )
        >>> container = FinLabDataFrame(data_module=data)
        >>> container.add_matrix('close', close_data)
        >>> container = trailing.execute(container)
        >>> signal = container.get_matrix('rolling_trailing_stop_signal')
    """

    def __init__(self, trail_percent: float = 0.10, lookback_periods: int = 20):
        """
        Initialize RollingTrailingStopFactor.

        Args:
            trail_percent: Trailing stop percentage (default: 0.10 = 10%)
            lookback_periods: Rolling window size in periods (default: 20)
        """
        super().__init__(
            id=f"rolling_trailing_stop_{int(trail_percent*100)}pct_{lookback_periods}d",
            name=f"Rolling Trailing Stop ({trail_percent*100:.0f}%, {lookback_periods}d)",
            category=FactorCategory.EXIT,
            inputs=["close"],
            outputs=["rolling_trailing_stop_signal"],
            logic=_rolling_trailing_stop_logic,
            parameters={"trail_percent": trail_percent, "lookback_periods": lookback_periods},
            description=f"Stateless trailing stop at {trail_percent*100:.0f}% from rolling {lookback_periods}-day high"
        )


class RollingProfitTargetFactor(Factor):
    """
    Stateless profit target factor using rolling window approximation.

    Uses rolling minimum price as a proxy for "entry price"
    to implement profit target logic without requiring position state.

    Category: EXIT
    Inputs: ["close"]
    Outputs: ["rolling_profit_target_signal"]
    Parameters:
        - target_percent (float): Profit target percentage (e.g., 0.30 = 30%)
        - lookback_periods (int): Rolling window size (e.g., 20 periods)

    Comparison with Stateful ProfitTargetFactor:
        Stateful: Exact entry_price tracking per position
        Stateless: Rolling min approximation (assumes entry near local low)

    Example:
        >>> profit_target = RollingProfitTargetFactor(
        ...     target_percent=0.30,
        ...     lookback_periods=20
        ... )
        >>> container = FinLabDataFrame(data_module=data)
        >>> container.add_matrix('close', close_data)
        >>> container = profit_target.execute(container)
        >>> signal = container.get_matrix('rolling_profit_target_signal')
    """

    def __init__(self, target_percent: float = 0.30, lookback_periods: int = 20):
        """
        Initialize RollingProfitTargetFactor.

        Args:
            target_percent: Profit target percentage (default: 0.30 = 30%)
            lookback_periods: Rolling window size in periods (default: 20)
        """
        super().__init__(
            id=f"rolling_profit_target_{int(target_percent*100)}pct_{lookback_periods}d",
            name=f"Rolling Profit Target ({target_percent*100:.0f}%, {lookback_periods}d)",
            category=FactorCategory.EXIT,
            inputs=["close"],
            outputs=["rolling_profit_target_signal"],
            logic=_rolling_profit_target_logic,
            parameters={"target_percent": target_percent, "lookback_periods": lookback_periods},
            description=f"Stateless profit target at {target_percent*100:.0f}% from rolling {lookback_periods}-day low"
        )


# ============================================================================
# Factory Functions
# ============================================================================

def create_rolling_trailing_stop_factor(
    trail_percent: float = 0.10,
    lookback_periods: int = 20
) -> Factor:
    """
    Create a stateless rolling trailing stop factor with custom parameters.

    Factory function for creating RollingTrailingStopFactor instances with
    configurable trailing percentage and lookback window.

    Args:
        trail_percent: Trailing stop percentage (default: 0.10 = 10%)
        lookback_periods: Rolling window size in periods (default: 20)

    Returns:
        Factor: Configured RollingTrailingStopFactor instance

    Example:
        >>> trailing_stop = create_rolling_trailing_stop_factor(
        ...     trail_percent=0.10,
        ...     lookback_periods=20
        ... )
        >>> trailing_stop.parameters
        {'trail_percent': 0.1, 'lookback_periods': 20}
    """
    return RollingTrailingStopFactor(
        trail_percent=trail_percent,
        lookback_periods=lookback_periods
    )


def create_rolling_profit_target_factor(
    target_percent: float = 0.30,
    lookback_periods: int = 20
) -> Factor:
    """
    Create a stateless rolling profit target factor with custom parameters.

    Factory function for creating RollingProfitTargetFactor instances with
    configurable profit target and lookback window.

    Args:
        target_percent: Profit target percentage (default: 0.30 = 30%)
        lookback_periods: Rolling window size in periods (default: 20)

    Returns:
        Factor: Configured RollingProfitTargetFactor instance

    Example:
        >>> profit_target = create_rolling_profit_target_factor(
        ...     target_percent=0.30,
        ...     lookback_periods=20
        ... )
        >>> profit_target.parameters
        {'target_percent': 0.3, 'lookback_periods': 20}
    """
    return RollingProfitTargetFactor(
        target_percent=target_percent,
        lookback_periods=lookback_periods
    )
