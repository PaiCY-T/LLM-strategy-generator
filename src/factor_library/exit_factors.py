"""
Exit Factors Module
===================

Exit strategy-related factors extracted from Phase 1 Exit Mutation Framework.
Provides reusable exit mechanisms for stop-loss, profit targets, time-based exits,
volatility stops, and composite exit logic.

Architecture: Phase 2.0+ Factor Graph System
Source: Extracted from src/mutation/exit_mutator.py and Phase 1 validation

Available Factors:
-----------------
1. TrailingStopFactor: Trailing stop loss that follows price
2. TimeBasedExitFactor: Exit positions after N periods
3. VolatilityStopFactor: Volatility-based stop using standard deviation
4. ProfitTargetFactor: Fixed profit target exit
5. CompositeExitFactor: Combines multiple exit signals with OR logic

Usage Example:
-------------
    from src.factor_library.exit_factors import (
        create_trailing_stop_factor,
        create_time_based_exit_factor,
        create_profit_target_factor,
        create_composite_exit_factor
    )

    # Create individual exit factors
    trailing = create_trailing_stop_factor(trail_percent=0.10, activation_profit=0.05)
    time_exit = create_time_based_exit_factor(max_holding_periods=20)
    profit = create_profit_target_factor(target_percent=0.30)

    # Combine into composite exit
    composite = create_composite_exit_factor(
        exit_signals=["trailing_stop_signal", "time_exit_signal", "profit_target_signal"]
    )

    # Execute factors on data with positions
    data = pd.DataFrame({
        "close": [100, 102, 104, 103, 105],
        "positions": [True, True, True, True, True],
        "entry_price": [100, 100, 100, 100, 100],
        "entry_date": pd.date_range("2023-01-01", periods=5)
    })
    result = trailing.execute(data)
    result = time_exit.execute(result)
    result = profit.execute(result)
    result = composite.execute(result)
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np

from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory


# ============================================================================
# Factor Logic Functions
# ============================================================================

def _trailing_stop_logic(data: pd.DataFrame, parameters: Dict[str, Any]) -> pd.DataFrame:
    """
    Calculate trailing stop loss signal that follows price.

    A trailing stop follows the price upward, locking in profits while allowing
    the position to remain open during uptrends. The stop is triggered when
    price falls by a specified percentage from its highest point since entry.

    Args:
        data: DataFrame containing 'close', 'positions', 'entry_price' columns
        parameters: Dictionary with:
            - trail_percent (float): Trailing stop percentage (e.g., 0.10 = 10%)
            - activation_profit (float): Minimum profit to activate trailing (e.g., 0.05 = 5%)

    Returns:
        DataFrame with new 'trailing_stop_signal' column added (boolean)

    Implementation:
        1. Calculate highest price since entry for each position
        2. Activate trailing only when profit >= activation_profit
        3. Stop triggered when: current_price < highest_price * (1 - trail_percent)
        4. Signal: True when stop is triggered, False otherwise

    Example:
        trail_percent=0.10, activation_profit=0.05
        entry_price=100, highest=110 (10% profit, trailing activated)
        stop_level=110 * 0.90 = 99
        current_price=98 → trailing_stop_signal=True (exit)
    """
    trail_percent = parameters['trail_percent']
    activation_profit = parameters['activation_profit']

    # Initialize tracking columns if not present
    if 'highest_price' not in data.columns:
        data['highest_price'] = data['close'].copy()

    # Initialize signal column
    data['trailing_stop_signal'] = False

    # Calculate for each position
    for idx in range(len(data)):
        if idx == 0:
            continue

        current_pos = data['positions'].iloc[idx]
        prev_pos = data['positions'].iloc[idx - 1]
        current_price = data['close'].iloc[idx]

        if current_pos:
            # Update highest price for active positions
            if prev_pos:
                # Continuing position: update highest
                data.loc[data.index[idx], 'highest_price'] = max(
                    data['highest_price'].iloc[idx - 1],
                    current_price
                )
            else:
                # New position: reset highest to current price
                data.loc[data.index[idx], 'highest_price'] = current_price

            # Check if trailing stop should be activated
            entry_price = data['entry_price'].iloc[idx]
            highest_price = data['highest_price'].iloc[idx]
            current_profit = (highest_price / entry_price - 1) if entry_price > 0 else 0

            if current_profit >= activation_profit:
                # Trailing stop activated: check if triggered
                stop_level = highest_price * (1 - trail_percent)
                if current_price < stop_level:
                    data.loc[data.index[idx], 'trailing_stop_signal'] = True

    return data


def _time_based_exit_logic(data: pd.DataFrame, parameters: Dict[str, Any]) -> pd.DataFrame:
    """
    Exit positions after holding for N periods (time-based exit).

    Implements maximum holding period logic to prevent positions from
    being held indefinitely. Exits when holding period exceeds threshold.

    Args:
        data: DataFrame containing 'positions', 'entry_date' columns
        parameters: Dictionary with 'max_holding_periods' (int)

    Returns:
        DataFrame with new 'time_exit_signal' column added (boolean)

    Implementation:
        1. Calculate holding days for each position
        2. Exit when: holding_days >= max_holding_periods
        3. Signal: True when time threshold exceeded, False otherwise

    Example:
        max_holding_periods=20
        entry_date="2023-01-01", current_date="2023-01-25"
        holding_days=24 > 20 → time_exit_signal=True (exit)
    """
    max_holding_periods = parameters['max_holding_periods']

    # Initialize signal column
    data['time_exit_signal'] = False

    # Calculate holding periods
    if 'entry_date' in data.columns and data.index.name == 'date' or isinstance(data.index, pd.DatetimeIndex):
        # If we have datetime index, calculate days directly
        for idx in range(len(data)):
            if data['positions'].iloc[idx]:
                entry_date = data['entry_date'].iloc[idx]
                current_date = data.index[idx]
                if pd.notna(entry_date):
                    holding_days = (current_date - entry_date).days
                    if holding_days >= max_holding_periods:
                        data.loc[data.index[idx], 'time_exit_signal'] = True
    else:
        # If no datetime index, use row count as proxy for periods
        holding_periods = 0
        for idx in range(len(data)):
            current_pos = data['positions'].iloc[idx]
            if idx > 0:
                prev_pos = data['positions'].iloc[idx - 1]
                if current_pos and prev_pos:
                    holding_periods += 1
                elif current_pos and not prev_pos:
                    holding_periods = 0
            else:
                holding_periods = 0 if current_pos else 0

            if current_pos and holding_periods >= max_holding_periods:
                data.loc[data.index[idx], 'time_exit_signal'] = True

    return data


def _volatility_stop_logic(data: pd.DataFrame, parameters: Dict[str, Any]) -> pd.DataFrame:
    """
    Calculate volatility-based stop loss using standard deviation.

    Uses standard deviation of price changes as a measure of volatility
    to set dynamic stop loss levels. Higher volatility → wider stops.

    Args:
        data: DataFrame containing 'close', 'positions' columns
        parameters: Dictionary with:
            - std_period (int): Lookback period for standard deviation
            - std_multiplier (float): Multiplier for stop distance (e.g., 2.0 = 2 std devs)

    Returns:
        DataFrame with new 'volatility_stop_signal' column added (boolean)

    Implementation:
        1. Calculate rolling standard deviation of returns
        2. Calculate stop level: entry_price - (std * std_multiplier)
        3. Exit when: current_price < stop_level
        4. Signal: True when stop is triggered, False otherwise

    Example:
        std_period=20, std_multiplier=2.0
        std(returns)=0.02, entry_price=100
        stop_level=100 - (100 * 0.02 * 2.0) = 96
        current_price=95 → volatility_stop_signal=True (exit)
    """
    std_period = parameters['std_period']
    std_multiplier = parameters['std_multiplier']

    # Calculate returns standard deviation
    returns = data['close'].pct_change()
    volatility = returns.rolling(window=std_period).std()

    # Initialize signal column
    data['volatility_stop_signal'] = False

    # Calculate for each position
    for idx in range(len(data)):
        if data['positions'].iloc[idx] and idx > 0:
            current_price = data['close'].iloc[idx]
            current_vol = volatility.iloc[idx]

            # Get entry price (assume it's in the data or use current price as fallback)
            if 'entry_price' in data.columns:
                entry_price = data['entry_price'].iloc[idx]
            else:
                # If no entry_price, use first price of position
                entry_price = current_price

            if pd.notna(current_vol) and entry_price > 0:
                # Calculate stop level based on volatility
                stop_distance = entry_price * current_vol * std_multiplier
                stop_level = entry_price - stop_distance

                if current_price < stop_level:
                    data.loc[data.index[idx], 'volatility_stop_signal'] = True

    return data


def _profit_target_logic(data: pd.DataFrame, parameters: Dict[str, Any]) -> pd.DataFrame:
    """
    Calculate fixed profit target exit signal.

    Exits positions when profit reaches a specified percentage target,
    locking in gains at predetermined levels.

    Args:
        data: DataFrame containing 'close', 'positions', 'entry_price' columns
        parameters: Dictionary with 'target_percent' (float, e.g., 0.30 = 30%)

    Returns:
        DataFrame with new 'profit_target_signal' column added (boolean)

    Implementation:
        1. Calculate current profit: (current_price / entry_price - 1)
        2. Exit when: profit >= target_percent
        3. Signal: True when target reached, False otherwise

    Example:
        target_percent=0.30
        entry_price=100, current_price=135
        profit=0.35 > 0.30 → profit_target_signal=True (exit)
    """
    target_percent = parameters['target_percent']

    # Initialize signal column
    data['profit_target_signal'] = False

    # Calculate profit for all rows at once (vectorized)
    current_price = data['close']
    entry_price = data['entry_price']
    positions = data['positions']

    # Calculate profit where entry_price > 0
    profit = (current_price / entry_price - 1).where(entry_price > 0, 0)

    # Set signal where positions are active and profit >= target
    data['profit_target_signal'] = positions & (profit >= target_percent)

    return data


def _composite_exit_logic(data: pd.DataFrame, parameters: Dict[str, Any]) -> pd.DataFrame:
    """
    Combine multiple exit signals with OR logic.

    Creates a composite exit signal that triggers when ANY of the
    specified exit conditions are met. This allows for multi-layered
    exit strategies with different risk management approaches.

    Args:
        data: DataFrame containing exit signal columns
        parameters: Dictionary with 'exit_signals' (List[str]) - list of exit signal column names

    Returns:
        DataFrame with new 'final_exit_signal' column added (boolean)

    Implementation:
        1. Validate all exit signal columns exist
        2. Combine with OR logic: any signal True → final signal True
        3. Signal: True if ANY exit condition is met, False otherwise

    Example:
        exit_signals=["trailing_stop_signal", "time_exit_signal", "profit_target_signal"]
        trailing=False, time=True, profit=False
        → final_exit_signal=True (exit due to time)
    """
    exit_signals = parameters['exit_signals']

    # Validate all signals exist
    missing_signals = [sig for sig in exit_signals if sig not in data.columns]
    if missing_signals:
        raise ValueError(f"Missing exit signal columns: {missing_signals}")

    # Combine with OR logic
    data['final_exit_signal'] = False
    for signal in exit_signals:
        data['final_exit_signal'] = data['final_exit_signal'] | data[signal]

    return data


# ============================================================================
# Factor Classes
# ============================================================================

class TrailingStopFactor(Factor):
    """
    Trailing stop loss factor that follows price.

    A trailing stop follows the price upward, locking in profits while allowing
    the position to remain open during uptrends. The stop is triggered when
    price falls by a specified percentage from its highest point since entry.

    Category: EXIT
    Inputs: ["close", "positions", "entry_price"]
    Outputs: ["trailing_stop_signal"]
    Parameters:
        - trail_percent (float): Trailing stop percentage (e.g., 0.10 = 10%)
        - activation_profit (float): Minimum profit to activate trailing (e.g., 0.05 = 5%)

    Example:
        >>> trailing_stop = TrailingStopFactor(trail_percent=0.10, activation_profit=0.05)
        >>> data = pd.DataFrame({
        ...     "close": [100, 105, 110, 108, 95],
        ...     "positions": [True, True, True, True, True],
        ...     "entry_price": [100, 100, 100, 100, 100]
        ... })
        >>> result = trailing_stop.execute(data)
        >>> "trailing_stop_signal" in result.columns
        True
    """

    def __init__(self, trail_percent: float = 0.10, activation_profit: float = 0.05):
        """
        Initialize TrailingStopFactor.

        Args:
            trail_percent: Trailing stop percentage (default: 0.10 = 10%)
            activation_profit: Minimum profit to activate trailing (default: 0.05 = 5%)
        """
        super().__init__(
            id=f"trailing_stop_{int(trail_percent*100)}pct",
            name=f"Trailing Stop ({trail_percent*100:.0f}%)",
            category=FactorCategory.EXIT,
            inputs=["close", "positions", "entry_price"],
            outputs=["trailing_stop_signal"],
            logic=_trailing_stop_logic,
            parameters={"trail_percent": trail_percent, "activation_profit": activation_profit},
            description=f"Trailing stop loss at {trail_percent*100:.0f}% from highest price, activated after {activation_profit*100:.0f}% profit"
        )


class TimeBasedExitFactor(Factor):
    """
    Time-based exit factor with maximum holding period.

    Implements maximum holding period logic to prevent positions from
    being held indefinitely. Exits when holding period exceeds threshold.

    Category: EXIT
    Inputs: ["positions", "entry_date"]
    Outputs: ["time_exit_signal"]
    Parameters:
        - max_holding_periods (int): Maximum holding periods before exit (e.g., 20 days)

    Example:
        >>> time_exit = TimeBasedExitFactor(max_holding_periods=20)
        >>> data = pd.DataFrame({
        ...     "positions": [True, True, True],
        ...     "entry_date": pd.to_datetime(["2023-01-01", "2023-01-01", "2023-01-01"])
        ... }, index=pd.date_range("2023-01-01", periods=3))
        >>> result = time_exit.execute(data)
        >>> "time_exit_signal" in result.columns
        True
    """

    def __init__(self, max_holding_periods: int = 20):
        """
        Initialize TimeBasedExitFactor.

        Args:
            max_holding_periods: Maximum holding periods before exit (default: 20)
        """
        super().__init__(
            id=f"time_exit_{max_holding_periods}d",
            name=f"Time Exit ({max_holding_periods}d)",
            category=FactorCategory.EXIT,
            inputs=["positions", "entry_date"],
            outputs=["time_exit_signal"],
            logic=_time_based_exit_logic,
            parameters={"max_holding_periods": max_holding_periods},
            description=f"Exit positions after {max_holding_periods} holding periods"
        )


class VolatilityStopFactor(Factor):
    """
    Volatility-based stop loss using standard deviation.

    Uses standard deviation of price changes as a measure of volatility
    to set dynamic stop loss levels. Higher volatility → wider stops.

    Category: EXIT
    Inputs: ["close", "positions"]
    Outputs: ["volatility_stop_signal"]
    Parameters:
        - std_period (int): Lookback period for standard deviation (e.g., 20)
        - std_multiplier (float): Multiplier for stop distance (e.g., 2.0 = 2 std devs)

    Example:
        >>> vol_stop = VolatilityStopFactor(std_period=20, std_multiplier=2.0)
        >>> data = pd.DataFrame({
        ...     "close": [100, 102, 98, 95, 90],
        ...     "positions": [True, True, True, True, True]
        ... })
        >>> result = vol_stop.execute(data)
        >>> "volatility_stop_signal" in result.columns
        True
    """

    def __init__(self, std_period: int = 20, std_multiplier: float = 2.0):
        """
        Initialize VolatilityStopFactor.

        Args:
            std_period: Lookback period for standard deviation (default: 20)
            std_multiplier: Multiplier for stop distance (default: 2.0)
        """
        # Convert float to string without decimal point for ID
        mult_str = str(std_multiplier).replace(".", "_")
        super().__init__(
            id=f"volatility_stop_{std_period}_{mult_str}std",
            name=f"Volatility Stop ({std_multiplier}x{std_period}d STD)",
            category=FactorCategory.EXIT,
            inputs=["close", "positions"],
            outputs=["volatility_stop_signal"],
            logic=_volatility_stop_logic,
            parameters={"std_period": std_period, "std_multiplier": std_multiplier},
            description=f"Volatility-based stop using {std_multiplier}x {std_period}-day standard deviation"
        )


class ProfitTargetFactor(Factor):
    """
    Fixed profit target exit factor.

    Exits positions when profit reaches a specified percentage target,
    locking in gains at predetermined levels.

    Category: EXIT
    Inputs: ["close", "positions", "entry_price"]
    Outputs: ["profit_target_signal"]
    Parameters:
        - target_percent (float): Profit target percentage (e.g., 0.30 = 30%)

    Example:
        >>> profit_target = ProfitTargetFactor(target_percent=0.30)
        >>> data = pd.DataFrame({
        ...     "close": [100, 110, 120, 130, 135],
        ...     "positions": [True, True, True, True, True],
        ...     "entry_price": [100, 100, 100, 100, 100]
        ... })
        >>> result = profit_target.execute(data)
        >>> "profit_target_signal" in result.columns
        True
    """

    def __init__(self, target_percent: float = 0.30):
        """
        Initialize ProfitTargetFactor.

        Args:
            target_percent: Profit target percentage (default: 0.30 = 30%)
        """
        super().__init__(
            id=f"profit_target_{int(target_percent*100)}pct",
            name=f"Profit Target ({target_percent*100:.0f}%)",
            category=FactorCategory.EXIT,
            inputs=["close", "positions", "entry_price"],
            outputs=["profit_target_signal"],
            logic=_profit_target_logic,
            parameters={"target_percent": target_percent},
            description=f"Exit when profit reaches {target_percent*100:.0f}%"
        )


class CompositeExitFactor(Factor):
    """
    Composite exit factor combining multiple exit signals.

    Creates a composite exit signal that triggers when ANY of the
    specified exit conditions are met. This allows for multi-layered
    exit strategies with different risk management approaches.

    Category: EXIT
    Inputs: List of exit signal columns (dynamic based on parameters)
    Outputs: ["final_exit_signal"]
    Parameters:
        - exit_signals (List[str]): List of exit signal column names to combine

    Example:
        >>> composite = CompositeExitFactor(
        ...     exit_signals=["trailing_stop_signal", "time_exit_signal", "profit_target_signal"]
        ... )
        >>> data = pd.DataFrame({
        ...     "trailing_stop_signal": [False, False, True, False, False],
        ...     "time_exit_signal": [False, False, False, True, False],
        ...     "profit_target_signal": [False, False, False, False, True]
        ... })
        >>> result = composite.execute(data)
        >>> "final_exit_signal" in result.columns
        True
    """

    def __init__(self, exit_signals: List[str]):
        """
        Initialize CompositeExitFactor.

        Args:
            exit_signals: List of exit signal column names to combine
        """
        # Create unique ID from signal names
        signal_id = "_".join([sig.replace("_signal", "") for sig in exit_signals])

        super().__init__(
            id=f"composite_exit_{signal_id}",
            name=f"Composite Exit ({len(exit_signals)} signals)",
            category=FactorCategory.EXIT,
            inputs=exit_signals,
            outputs=["final_exit_signal"],
            logic=_composite_exit_logic,
            parameters={"exit_signals": exit_signals},
            description=f"Composite exit combining {len(exit_signals)} signals with OR logic"
        )


# ============================================================================
# Factory Functions
# ============================================================================

def create_trailing_stop_factor(
    trail_percent: float = 0.10,
    activation_profit: float = 0.05
) -> Factor:
    """
    Create a trailing stop factor with custom parameters.

    Factory function for creating TrailingStopFactor instances with
    configurable trailing percentage and activation profit.

    Args:
        trail_percent: Trailing stop percentage (default: 0.10 = 10%)
        activation_profit: Minimum profit to activate trailing (default: 0.05 = 5%)

    Returns:
        Factor: Configured TrailingStopFactor instance

    Example:
        >>> trailing_stop = create_trailing_stop_factor(trail_percent=0.10, activation_profit=0.05)
        >>> trailing_stop.parameters
        {'trail_percent': 0.1, 'activation_profit': 0.05}
    """
    return TrailingStopFactor(trail_percent=trail_percent, activation_profit=activation_profit)


def create_time_based_exit_factor(max_holding_periods: int = 20) -> Factor:
    """
    Create a time-based exit factor with custom holding period.

    Factory function for creating TimeBasedExitFactor instances with
    configurable maximum holding period.

    Args:
        max_holding_periods: Maximum holding periods before exit (default: 20)

    Returns:
        Factor: Configured TimeBasedExitFactor instance

    Example:
        >>> time_exit = create_time_based_exit_factor(max_holding_periods=20)
        >>> time_exit.parameters
        {'max_holding_periods': 20}
    """
    return TimeBasedExitFactor(max_holding_periods=max_holding_periods)


def create_volatility_stop_factor(
    std_period: int = 20,
    std_multiplier: float = 2.0
) -> Factor:
    """
    Create a volatility stop factor with custom parameters.

    Factory function for creating VolatilityStopFactor instances with
    configurable standard deviation period and multiplier.

    Args:
        std_period: Lookback period for standard deviation (default: 20)
        std_multiplier: Multiplier for stop distance (default: 2.0)

    Returns:
        Factor: Configured VolatilityStopFactor instance

    Example:
        >>> vol_stop = create_volatility_stop_factor(std_period=20, std_multiplier=2.0)
        >>> vol_stop.parameters
        {'std_period': 20, 'std_multiplier': 2.0}
    """
    return VolatilityStopFactor(std_period=std_period, std_multiplier=std_multiplier)


def create_profit_target_factor(target_percent: float = 0.30) -> Factor:
    """
    Create a profit target factor with custom target percentage.

    Factory function for creating ProfitTargetFactor instances with
    configurable profit target percentage.

    Args:
        target_percent: Profit target percentage (default: 0.30 = 30%)

    Returns:
        Factor: Configured ProfitTargetFactor instance

    Example:
        >>> profit_target = create_profit_target_factor(target_percent=0.30)
        >>> profit_target.parameters
        {'target_percent': 0.3}
    """
    return ProfitTargetFactor(target_percent=target_percent)


def create_composite_exit_factor(exit_signals: List[str]) -> Factor:
    """
    Create a composite exit factor combining multiple signals.

    Factory function for creating CompositeExitFactor instances that
    combine multiple exit signals with OR logic.

    Args:
        exit_signals: List of exit signal column names to combine

    Returns:
        Factor: Configured CompositeExitFactor instance

    Example:
        >>> composite = create_composite_exit_factor(
        ...     exit_signals=["trailing_stop_signal", "time_exit_signal", "profit_target_signal"]
        ... )
        >>> composite.parameters
        {'exit_signals': ['trailing_stop_signal', 'time_exit_signal', 'profit_target_signal']}
    """
    return CompositeExitFactor(exit_signals=exit_signals)
