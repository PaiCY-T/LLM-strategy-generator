"""
Exit Factors Module
===================

Exit strategy-related factors extracted from Phase 1 Exit Mutation Framework.
Provides reusable exit mechanisms for stop-loss, profit targets, time-based exits,
volatility stops, and composite exit logic.

Architecture: Phase 2.0+ Factor Graph System (Matrix-Native)
Source: Extracted from src/mutation/exit_mutator.py and Phase 1 validation

Available Factors:
-----------------
1. TrailingStopFactor: Trailing stop loss that follows price
2. TimeBasedExitFactor: Exit positions after N periods
3. VolatilityStopFactor: Volatility-based stop using standard deviation
4. ProfitTargetFactor: Fixed profit target exit
5. CompositeExitFactor: Combines multiple exit signals with OR logic

Usage Example (Phase 2.0):
--------------------------
    from src.factor_library.exit_factors import (
        create_trailing_stop_factor,
        create_time_based_exit_factor,
        create_profit_target_factor,
        create_composite_exit_factor
    )
    from src.factor_graph.finlab_dataframe import FinLabDataFrame
    from finlab import data

    # Create individual exit factors
    trailing = create_trailing_stop_factor(trail_percent=0.10, activation_profit=0.05)
    time_exit = create_time_based_exit_factor(max_holding_periods=20)
    profit = create_profit_target_factor(target_percent=0.30)

    # Combine into composite exit
    composite = create_composite_exit_factor(
        exit_signals=["trailing_stop_signal", "time_exit_signal", "profit_target_signal"]
    )

    # Execute factors on FinLabDataFrame container
    container = FinLabDataFrame(data_module=data)
    # ... add positions, entry_price, entry_date matrices ...
    container = trailing.execute(container)
    container = time_exit.execute(container)
    container = profit.execute(container)
    container = composite.execute(container)
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np

from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.finlab_dataframe import FinLabDataFrame


# ============================================================================
# Factor Logic Functions
# ============================================================================

def _trailing_stop_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """
    Calculate trailing stop loss signal that follows price (Matrix-Native Phase 2.0).

    A trailing stop follows the price upward, locking in profits while allowing
    the position to remain open during uptrends. The stop is triggered when
    price falls by a specified percentage from its highest point since entry.

    Args:
        container: FinLabDataFrame container with 'close', 'positions', 'entry_price' matrices
        parameters: Dictionary with:
            - trail_percent (float): Trailing stop percentage (e.g., 0.10 = 10%)
            - activation_profit (float): Minimum profit to activate trailing (e.g., 0.05 = 5%)

    Modifies:
        Adds 'trailing_stop_signal' matrix to container (Dates×Symbols, boolean)

    Implementation:
        1. For each symbol, track highest price during position runs
        2. Activate trailing only when profit >= activation_profit
        3. Stop triggered when: current_price < highest_price * (1 - trail_percent)
        4. Signal: True when stop is triggered, False otherwise

    Example:
        trail_percent=0.10, activation_profit=0.05
        entry_price=100, highest=110 (10% profit, trailing activated)
        stop_level=110 * 0.90 = 99
        current_price=98 → trailing_stop_signal=True (exit)

    Phase 2.0 Changes:
        - Input: FinLabDataFrame container (not DataFrame)
        - Works with Dates×Symbols matrices (not columns)
        - Vectorized per-symbol with position run tracking
        - Modifies container in-place (no return)
    """
    trail_percent = parameters['trail_percent']
    activation_profit = parameters['activation_profit']

    # Get matrices from container
    close = container.get_matrix('close')
    positions = container.get_matrix('positions')
    entry_price = container.get_matrix('entry_price')

    # Initialize output matrices
    highest_price = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    trailing_stop_signal = pd.DataFrame(False, index=close.index, columns=close.columns)

    # Process each symbol independently
    for symbol in close.columns:
        close_col = close[symbol]
        pos_col = positions[symbol]
        entry_col = entry_price[symbol]

        # Track highest price for this symbol
        highest_col = close_col.copy()

        # Detect position changes
        prev_pos = pos_col.shift(1).fillna(False)
        new_position = pos_col & ~prev_pos  # Position starts
        continuing_position = pos_col & prev_pos  # Position continues

        # Calculate cummax within position runs
        # Reset cummax at new positions
        for idx in range(1, len(close_col)):
            if pos_col.iloc[idx]:
                if new_position.iloc[idx]:
                    # New position: reset to current price
                    highest_col.iloc[idx] = close_col.iloc[idx]
                elif continuing_position.iloc[idx]:
                    # Continuing: update to max
                    highest_col.iloc[idx] = max(highest_col.iloc[idx-1], close_col.iloc[idx])

        highest_price[symbol] = highest_col

        # Calculate profit and check trailing stop
        current_profit = (highest_col / entry_col - 1).where(entry_col > 0, 0)

        # Trailing stop activated when profit >= activation_profit
        trailing_activated = pos_col & (current_profit >= activation_profit)

        # Stop level
        stop_level = highest_col * (1 - trail_percent)

        # Signal: trailing activated AND price below stop level
        trailing_stop_signal[symbol] = trailing_activated & (close_col < stop_level)

    # Add matrices to container
    container.add_matrix('trailing_stop_signal', trailing_stop_signal)


def _time_based_exit_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """
    Exit positions after holding for N periods (Matrix-Native Phase 2.0).

    Implements maximum holding period logic to prevent positions from
    being held indefinitely. Exits when holding period exceeds threshold.

    Args:
        container: FinLabDataFrame container with 'positions', 'entry_date' matrices
        parameters: Dictionary with 'max_holding_periods' (int)

    Modifies:
        Adds 'time_exit_signal' matrix to container (Dates×Symbols, boolean)

    Implementation:
        1. Calculate holding days for each position
        2. Exit when: holding_days >= max_holding_periods
        3. Signal: True when time threshold exceeded, False otherwise

    Example:
        max_holding_periods=20
        entry_date="2023-01-01", current_date="2023-01-25"
        holding_days=24 > 20 → time_exit_signal=True (exit)

    Phase 2.0 Changes:
        - Input: FinLabDataFrame container (not DataFrame)
        - Works with Dates×Symbols matrices (not columns)
        - Vectorized per-symbol with date calculations
        - Modifies container in-place (no return)
    """
    max_holding_periods = parameters['max_holding_periods']

    # Get matrices from container
    positions = container.get_matrix('positions')
    entry_date = container.get_matrix('entry_date')

    # Initialize output matrix
    time_exit_signal = pd.DataFrame(False, index=positions.index, columns=positions.columns)

    # Check if index is datetime
    if isinstance(positions.index, pd.DatetimeIndex):
        # Vectorized calculation: current_date - entry_date
        for date_idx in positions.index:
            holding_days = (date_idx - entry_date.loc[date_idx]).dt.days
            time_exit_signal.loc[date_idx] = positions.loc[date_idx] & (holding_days >= max_holding_periods)
    else:
        # Use row count as proxy for holding periods
        # Process each symbol independently
        for symbol in positions.columns:
            pos_col = positions[symbol]

            # Count consecutive position days
            holding_periods = 0
            for idx in range(len(pos_col)):
                if pos_col.iloc[idx]:
                    if idx > 0 and pos_col.iloc[idx-1]:
                        holding_periods += 1
                    else:
                        holding_periods = 0

                    if holding_periods >= max_holding_periods:
                        time_exit_signal[symbol].iloc[idx] = True
                else:
                    holding_periods = 0

    # Add matrix to container
    container.add_matrix('time_exit_signal', time_exit_signal)


def _volatility_stop_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """
    Calculate volatility-based stop loss using standard deviation (Matrix-Native Phase 2.0).

    Uses standard deviation of price changes as a measure of volatility
    to set dynamic stop loss levels. Higher volatility → wider stops.

    Args:
        container: FinLabDataFrame container with 'close', 'positions', 'entry_price' matrices
        parameters: Dictionary with:
            - std_period (int): Lookback period for standard deviation
            - std_multiplier (float): Multiplier for stop distance (e.g., 2.0 = 2 std devs)

    Modifies:
        Adds 'volatility_stop_signal' matrix to container (Dates×Symbols, boolean)

    Implementation:
        1. Calculate rolling standard deviation of returns
        2. Calculate stop level: entry_price - (entry_price * std * std_multiplier)
        3. Exit when: current_price < stop_level
        4. Signal: True when stop is triggered, False otherwise

    Example:
        std_period=20, std_multiplier=2.0
        std(returns)=0.02, entry_price=100
        stop_level=100 - (100 * 0.02 * 2.0) = 96
        current_price=95 → volatility_stop_signal=True (exit)

    Phase 2.0 Changes:
        - Input: FinLabDataFrame container (not DataFrame)
        - Works with Dates×Symbols matrices (not columns)
        - Fully vectorized operations
        - Modifies container in-place (no return)
    """
    std_period = parameters['std_period']
    std_multiplier = parameters['std_multiplier']

    # Get matrices from container
    close = container.get_matrix('close')
    positions = container.get_matrix('positions')
    entry_price = container.get_matrix('entry_price')

    # Calculate returns standard deviation (vectorized)
    returns = close.pct_change()
    volatility = returns.rolling(window=std_period).std()

    # Calculate stop level based on volatility (vectorized)
    stop_distance = entry_price * volatility * std_multiplier
    stop_level = entry_price - stop_distance

    # Signal: position active AND current price below stop level
    volatility_stop_signal = positions & (close < stop_level) & (entry_price > 0)

    # Add matrix to container
    container.add_matrix('volatility_stop_signal', volatility_stop_signal)


def _profit_target_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """
    Calculate fixed profit target exit signal (Matrix-Native Phase 2.0).

    Exits positions when profit reaches a specified percentage target,
    locking in gains at predetermined levels.

    Args:
        container: FinLabDataFrame container with 'close', 'positions', 'entry_price' matrices
        parameters: Dictionary with 'target_percent' (float, e.g., 0.30 = 30%)

    Modifies:
        Adds 'profit_target_signal' matrix to container (Dates×Symbols, boolean)

    Implementation:
        1. Calculate current profit: (current_price / entry_price - 1)
        2. Exit when: profit >= target_percent
        3. Signal: True when target reached, False otherwise

    Example:
        target_percent=0.30
        entry_price=100, current_price=135
        profit=0.35 > 0.30 → profit_target_signal=True (exit)

    Phase 2.0 Changes:
        - Input: FinLabDataFrame container (not DataFrame)
        - Works with Dates×Symbols matrices (not columns)
        - Fully vectorized operations
        - Modifies container in-place (no return)
    """
    target_percent = parameters['target_percent']

    # Get matrices from container
    close = container.get_matrix('close')
    entry_price = container.get_matrix('entry_price')
    positions = container.get_matrix('positions')

    # Calculate profit where entry_price > 0 (vectorized)
    profit = (close / entry_price - 1).where(entry_price > 0, 0)

    # Set signal where positions are active and profit >= target
    profit_target_signal = positions & (profit >= target_percent)

    # Add matrix to container
    container.add_matrix('profit_target_signal', profit_target_signal)


def _composite_exit_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """
    Combine multiple exit signals with OR logic (Matrix-Native Phase 2.0).

    Creates a composite exit signal that triggers when ANY of the
    specified exit conditions are met. This allows for multi-layered
    exit strategies with different risk management approaches.

    Args:
        container: FinLabDataFrame container with multiple exit signal matrices
        parameters: Dictionary with 'exit_signals' (List[str]) - list of exit signal matrix names

    Modifies:
        Adds 'final_exit_signal' matrix to container (Dates×Symbols, boolean)

    Implementation:
        1. Validate all exit signal matrices exist
        2. Combine with OR logic: any signal True → final signal True
        3. Signal: True if ANY exit condition is met, False otherwise

    Example:
        exit_signals=["trailing_stop_signal", "time_exit_signal", "profit_target_signal"]
        trailing=False, time=True, profit=False
        → final_exit_signal=True (exit due to time)

    Phase 2.0 Changes:
        - Input: FinLabDataFrame container (not DataFrame)
        - Works with Dates×Symbols matrices (not columns)
        - Fully vectorized OR operation
        - Modifies container in-place (no return)
    """
    exit_signals = parameters['exit_signals']

    # Validate all signals exist
    missing_signals = [sig for sig in exit_signals if not container.has_matrix(sig)]
    if missing_signals:
        available = container.list_matrices()
        raise ValueError(
            f"Missing exit signal matrices: {missing_signals}. "
            f"Available matrices: {available}"
        )

    # Get first signal to initialize shape
    final_exit_signal = container.get_matrix(exit_signals[0]).copy()

    # Combine all signals with OR logic (vectorized)
    for signal in exit_signals[1:]:
        signal_matrix = container.get_matrix(signal)
        final_exit_signal = final_exit_signal | signal_matrix

    # Add matrix to container
    container.add_matrix('final_exit_signal', final_exit_signal)


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
