"""
Turtle Strategy Factors Module
================================

Turtle strategy-related factors extracted from TurtleTemplate.
Provides reusable ATR calculation, breakout detection, dual MA filtering, and ATR-based stop-loss.

Architecture: Phase 2.0+ Factor Graph System (Matrix-Native)
Source: Extracted from src/templates/turtle_template.py

Available Factors:
-----------------
1. ATRFactor: Average True Range calculation for volatility measurement
2. BreakoutFactor: N-day high/low breakout detection for entry signals
3. DualMAFilterFactor: Dual moving average filter for trend confirmation
4. ATRStopLossFactor: ATR-based stop loss calculation for risk management

Usage Example (Phase 2.0):
--------------------------
    from src.factor_library.turtle_factors import (
        create_atr_factor,
        create_breakout_factor,
        create_dual_ma_filter_factor,
        create_atr_stop_loss_factor
    )
    from src.factor_graph.finlab_dataframe import FinLabDataFrame
    from finlab import data

    # Create factors with custom parameters
    atr = create_atr_factor(atr_period=20)
    breakout = create_breakout_factor(entry_window=20)
    ma_filter = create_dual_ma_filter_factor(short_ma=20, long_ma=60)
    stop_loss = create_atr_stop_loss_factor(atr_multiplier=2.0)

    # Execute factors on FinLabDataFrame container
    container = FinLabDataFrame(data_module=data)
    container = atr.execute(container)
    container = breakout.execute(container)
    container = ma_filter.execute(container)
    container = stop_loss.execute(container)
"""

from typing import Dict, Any
import pandas as pd
import numpy as np

from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.finlab_dataframe import FinLabDataFrame


# ============================================================================
# Factor Logic Functions
# ============================================================================

def _atr_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """
    Calculate Average True Range (ATR) for volatility measurement (Matrix-Native Phase 2.0).

    ATR measures market volatility by computing the average of true ranges
    over a specified period. True Range is the maximum of:
    - Current high - Current low
    - Abs(Current high - Previous close)
    - Abs(Current low - Previous close)

    Args:
        container: FinLabDataFrame container with 'high', 'low', 'close' matrices
        parameters: Dictionary with 'atr_period' (int)

    Modifies:
        Adds 'atr' matrix to container (Dates×Symbols)

    Implementation:
        1. Get high, low, close matrices from container
        2. Calculate true range for each period
        3. Apply rolling mean over atr_period
        4. Add ATR matrix to container

    Example:
        atr_period=20, TR=[2.5, 3.0, 2.0, 2.8, 3.2]
        → atr = mean(last 20 TR values) = 2.7

    Phase 2.0 Changes:
        - Input: FinLabDataFrame container (not DataFrame)
        - Works with Dates×Symbols matrices (not columns)
        - Modifies container in-place (no return)
    """
    atr_period = parameters['atr_period']

    # Get price matrices from container
    high = container.get_matrix('high')
    low = container.get_matrix('low')
    close = container.get_matrix('close')

    # Calculate previous close for true range calculation
    prev_close = close.shift(1)

    # Calculate three components of true range
    high_low = high - low
    high_prev_close = np.abs(high - prev_close)
    low_prev_close = np.abs(low - prev_close)

    # True range is the maximum of the three components
    true_range = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)

    # ATR is the rolling mean of true range
    atr = true_range.rolling(window=atr_period).mean()

    # Add ATR matrix to container
    container.add_matrix('atr', atr)


def _breakout_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """
    Detect N-day high/low breakout signals for entry (Matrix-Native Phase 2.0).

    A breakout occurs when:
    - Long signal: Current close > highest high of previous N days
    - Short signal: Current close < lowest low of previous N days

    Args:
        container: FinLabDataFrame container with 'high', 'low', 'close' matrices
        parameters: Dictionary with 'entry_window' (int)

    Modifies:
        Adds 'breakout_signal' matrix to container (Dates×Symbols, values: 1=long, -1=short, 0=none)

    Implementation:
        1. Get high, low, close matrices from container
        2. Calculate N-day highest high: high.rolling(entry_window).max()
        3. Calculate N-day lowest low: low.rolling(entry_window).min()
        4. Long breakout: close > N-day high
        5. Short breakout: close < N-day low
        6. Signal: 1 for long, -1 for short, 0 for no signal
        7. Add breakout_signal matrix to container

    Example:
        entry_window=20, close=105, 20-day high=103, 20-day low=95
        → breakout_signal=1 (long breakout)

    Phase 2.0 Changes:
        - Input: FinLabDataFrame container (not DataFrame)
        - Works with Dates×Symbols matrices (not columns)
        - Modifies container in-place (no return)
    """
    entry_window = parameters['entry_window']

    # Get price matrices from container
    high = container.get_matrix('high')
    low = container.get_matrix('low')
    close = container.get_matrix('close')

    # Calculate N-day highest high and lowest low
    n_day_high = high.rolling(window=entry_window).max()
    n_day_low = low.rolling(window=entry_window).min()

    # Detect breakouts
    long_breakout = close > n_day_high.shift(1)  # Current close > previous N-day high
    short_breakout = close < n_day_low.shift(1)  # Current close < previous N-day low

    # Create signal matrix: 1 for long, -1 for short, 0 for none
    breakout_signal = pd.DataFrame(0, index=close.index, columns=close.columns)
    breakout_signal[long_breakout] = 1
    breakout_signal[short_breakout] = -1

    # Add breakout_signal matrix to container
    container.add_matrix('breakout_signal', breakout_signal)


def _dual_ma_filter_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """
    Apply dual moving average filter for trend confirmation (Matrix-Native Phase 2.0).

    Creates a boolean filter that is True when price is above both
    short-term and long-term moving averages, indicating a strong uptrend.

    Args:
        container: FinLabDataFrame container with 'close' matrix
        parameters: Dictionary with 'short_ma' (int) and 'long_ma' (int)

    Modifies:
        Adds 'dual_ma_filter' matrix to container (Dates×Symbols, boolean)

    Implementation:
        1. Get close price matrix from container
        2. Calculate short-term MA: close.rolling(short_ma).mean()
        3. Calculate long-term MA: close.rolling(long_ma).mean()
        4. Filter: (close > short_ma) & (close > long_ma)
        5. Add dual_ma_filter matrix to container

    Example:
        short_ma=20, long_ma=60, close=105, MA(20)=102, MA(60)=100
        → dual_ma_filter=True (price above both MAs)

    Phase 2.0 Changes:
        - Input: FinLabDataFrame container (not DataFrame)
        - Works with Dates×Symbols matrices (not columns)
        - Modifies container in-place (no return)
    """
    short_ma = parameters['short_ma']
    long_ma = parameters['long_ma']

    # Get close price matrix from container
    close = container.get_matrix('close')

    # Calculate short-term and long-term moving averages
    ma_short = close.rolling(window=short_ma).mean()
    ma_long = close.rolling(window=long_ma).mean()

    # Create filter: price must be above both MAs
    dual_ma_filter = (close > ma_short) & (close > ma_long)

    # Add dual_ma_filter matrix to container
    container.add_matrix('dual_ma_filter', dual_ma_filter)


def _atr_stop_loss_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """
    Calculate ATR-based stop loss levels for risk management (Matrix-Native Phase 2.0).

    Stop loss is calculated as:
    - Long position: entry_price - (ATR * atr_multiplier)
    - Short position: entry_price + (ATR * atr_multiplier)

    This adaptive stop loss adjusts to market volatility, providing
    tighter stops in low volatility and wider stops in high volatility.

    Args:
        container: FinLabDataFrame container with 'close', 'atr', 'positions' matrices
        parameters: Dictionary with 'atr_multiplier' (float)

    Modifies:
        Adds 'stop_loss_level' matrix to container (Dates×Symbols)

    Implementation:
        1. Get close, atr, positions matrices from container
        2. Identify position direction from 'positions' matrix (1=long, -1=short, 0=none)
        3. Calculate stop distance: ATR * atr_multiplier
        4. Long stop: close - stop_distance
        5. Short stop: close + stop_distance
        6. No position: NaN
        7. Add stop_loss_level matrix to container

    Example:
        atr_multiplier=2.0, close=100, atr=2.5, position=1 (long)
        → stop_loss_level = 100 - (2.5 * 2.0) = 95.0

    Phase 2.0 Changes:
        - Input: FinLabDataFrame container (not DataFrame)
        - Works with Dates×Symbols matrices (not columns)
        - Modifies container in-place (no return)
    """
    atr_multiplier = parameters['atr_multiplier']

    # Get matrices from container
    close = container.get_matrix('close')
    atr = container.get_matrix('atr')
    positions = container.get_matrix('positions')

    # Calculate stop distance based on ATR
    stop_distance = atr * atr_multiplier

    # Initialize stop loss matrix with NaN
    stop_loss_level = pd.DataFrame(np.nan, index=close.index, columns=close.columns)

    # Calculate stop loss for long positions (position > 0)
    long_positions = positions > 0
    stop_loss_level[long_positions] = close[long_positions] - stop_distance[long_positions]

    # Calculate stop loss for short positions (position < 0)
    short_positions = positions < 0
    stop_loss_level[short_positions] = close[short_positions] + stop_distance[short_positions]

    # Add stop_loss_level matrix to container
    container.add_matrix('stop_loss_level', stop_loss_level)


# ============================================================================
# Factor Classes
# ============================================================================

class ATRFactor(Factor):
    """
    Average True Range (ATR) factor for volatility measurement.

    Calculates ATR as the rolling mean of true ranges over a specified period.
    ATR is a fundamental measure of market volatility, essential for position
    sizing and stop loss calculation in the Turtle trading system.

    Category: RISK
    Inputs: ["high", "low", "close"]
    Outputs: ["atr"]
    Parameters:
        - atr_period (int): Lookback period for ATR calculation
          Common values: 14 (original Turtle), 20 (1 month), 30 (1.5 months)

    Example:
        >>> atr = ATRFactor(atr_period=20)
        >>> data = pd.DataFrame({
        ...     "high": [102, 104, 103, 105, 107],
        ...     "low": [98, 100, 99, 101, 103],
        ...     "close": [100, 102, 101, 103, 105]
        ... })
        >>> result = atr.execute(data)
        >>> "atr" in result.columns
        True
    """

    def __init__(self, atr_period: int = 20):
        """
        Initialize ATRFactor.

        Args:
            atr_period: Lookback period for ATR calculation (default: 20)
        """
        super().__init__(
            id=f"atr_{atr_period}",
            name=f"ATR ({atr_period}d)",
            category=FactorCategory.RISK,
            inputs=["high", "low", "close"],
            outputs=["atr"],
            logic=_atr_logic,
            parameters={"atr_period": atr_period},
            description=f"Average True Range over {atr_period} periods for volatility measurement"
        )


class BreakoutFactor(Factor):
    """
    N-day breakout detection factor for entry signals.

    Detects when price breaks out of an N-day trading range:
    - Long signal: Close > N-day high (breakout to upside)
    - Short signal: Close < N-day low (breakout to downside)

    This is a core entry mechanism in the Turtle trading system,
    capturing momentum at the beginning of new trends.

    Category: ENTRY
    Inputs: ["high", "low", "close"]
    Outputs: ["breakout_signal"]
    Parameters:
        - entry_window (int): N-day lookback for breakout detection
          Common values: 20 (1 month), 55 (original Turtle entry)

    Example:
        >>> breakout = BreakoutFactor(entry_window=20)
        >>> data = pd.DataFrame({
        ...     "high": [102, 104, 103, 105, 107],
        ...     "low": [98, 100, 99, 101, 103],
        ...     "close": [100, 102, 101, 103, 105]
        ... })
        >>> result = breakout.execute(data)
        >>> "breakout_signal" in result.columns
        True
    """

    def __init__(self, entry_window: int = 20):
        """
        Initialize BreakoutFactor.

        Args:
            entry_window: N-day lookback for breakout detection (default: 20)
        """
        super().__init__(
            id=f"breakout_{entry_window}",
            name=f"Breakout ({entry_window}d)",
            category=FactorCategory.ENTRY,
            inputs=["high", "low", "close"],
            outputs=["breakout_signal"],
            logic=_breakout_logic,
            parameters={"entry_window": entry_window},
            description=f"{entry_window}-day breakout detection for entry signals"
        )


class DualMAFilterFactor(Factor):
    """
    Dual moving average filter for trend confirmation.

    Creates a boolean filter that is True when price is above both
    short-term and long-term moving averages, ensuring trades are
    taken only in the direction of the prevailing trend.

    Category: MOMENTUM
    Inputs: ["close"]
    Outputs: ["dual_ma_filter"]
    Parameters:
        - short_ma (int): Short-term moving average period
          Common values: 10-30 days
        - long_ma (int): Long-term moving average period
          Common values: 40-80 days

    Example:
        >>> ma_filter = DualMAFilterFactor(short_ma=20, long_ma=60)
        >>> data = pd.DataFrame({"close": [100, 102, 101, 103, 105]})
        >>> result = ma_filter.execute(data)
        >>> "dual_ma_filter" in result.columns
        True
    """

    def __init__(self, short_ma: int = 20, long_ma: int = 60):
        """
        Initialize DualMAFilterFactor.

        Args:
            short_ma: Short-term MA period (default: 20)
            long_ma: Long-term MA period (default: 60)
        """
        super().__init__(
            id=f"dual_ma_filter_{short_ma}_{long_ma}",
            name=f"Dual MA Filter ({short_ma}d/{long_ma}d)",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["dual_ma_filter"],
            logic=_dual_ma_filter_logic,
            parameters={"short_ma": short_ma, "long_ma": long_ma},
            description=f"Dual moving average filter using {short_ma}-day and {long_ma}-day MAs"
        )


class ATRStopLossFactor(Factor):
    """
    ATR-based stop loss calculation for risk management.

    Calculates adaptive stop loss levels based on ATR (Average True Range),
    providing volatility-adjusted risk control. Stop loss distance adjusts
    automatically to market conditions:
    - Tight stops in low volatility
    - Wide stops in high volatility

    Category: EXIT
    Inputs: ["close", "atr", "positions"]
    Outputs: ["stop_loss_level"]
    Parameters:
        - atr_multiplier (float): Multiplier for ATR to set stop distance
          Common values: 2.0 (original Turtle), 1.5 (tighter), 3.0 (wider)

    Note:
        Requires 'positions' column indicating current position direction:
        - 1 or positive: Long position
        - -1 or negative: Short position
        - 0: No position

    Example:
        >>> stop_loss = ATRStopLossFactor(atr_multiplier=2.0)
        >>> data = pd.DataFrame({
        ...     "close": [100, 102, 101, 103, 105],
        ...     "atr": [2.0, 2.1, 2.0, 2.2, 2.1],
        ...     "positions": [1, 1, 1, 1, 1]
        ... })
        >>> result = stop_loss.execute(data)
        >>> "stop_loss_level" in result.columns
        True
    """

    def __init__(self, atr_multiplier: float = 2.0):
        """
        Initialize ATRStopLossFactor.

        Args:
            atr_multiplier: Multiplier for ATR to set stop distance (default: 2.0)
        """
        # Convert float multiplier to string-safe format for ID (replace . with _)
        id_multiplier = str(atr_multiplier).replace('.', '_')
        super().__init__(
            id=f"atr_stop_loss_{id_multiplier}",
            name=f"ATR Stop Loss ({atr_multiplier}x)",
            category=FactorCategory.EXIT,
            inputs=["close", "atr", "positions"],
            outputs=["stop_loss_level"],
            logic=_atr_stop_loss_logic,
            parameters={"atr_multiplier": atr_multiplier},
            description=f"ATR-based stop loss with {atr_multiplier}x multiplier"
        )


# ============================================================================
# Factory Functions
# ============================================================================

def create_atr_factor(atr_period: int = 20) -> Factor:
    """
    Create an ATR factor with custom period.

    Factory function for creating ATRFactor instances with
    configurable ATR period.

    Args:
        atr_period: Lookback period for ATR calculation
            Common values: 14 (original Turtle), 20 (1 month), 30 (1.5 months)

    Returns:
        Factor: Configured ATRFactor instance

    Example:
        >>> atr = create_atr_factor(atr_period=20)
        >>> atr.parameters
        {'atr_period': 20}
    """
    return ATRFactor(atr_period=atr_period)


def create_breakout_factor(entry_window: int = 20) -> Factor:
    """
    Create a breakout factor with custom entry window.

    Factory function for creating BreakoutFactor instances with
    configurable entry window.

    Args:
        entry_window: N-day lookback for breakout detection
            Common values: 20 (1 month), 55 (original Turtle entry)

    Returns:
        Factor: Configured BreakoutFactor instance

    Example:
        >>> breakout = create_breakout_factor(entry_window=20)
        >>> breakout.parameters
        {'entry_window': 20}
    """
    return BreakoutFactor(entry_window=entry_window)


def create_dual_ma_filter_factor(short_ma: int = 20, long_ma: int = 60) -> Factor:
    """
    Create a dual MA filter factor with custom periods.

    Factory function for creating DualMAFilterFactor instances with
    configurable short-term and long-term MA periods.

    Args:
        short_ma: Short-term moving average period
            Common values: 10-30 days
        long_ma: Long-term moving average period
            Common values: 40-80 days

    Returns:
        Factor: Configured DualMAFilterFactor instance

    Example:
        >>> ma_filter = create_dual_ma_filter_factor(short_ma=20, long_ma=60)
        >>> ma_filter.parameters
        {'short_ma': 20, 'long_ma': 60}
    """
    return DualMAFilterFactor(short_ma=short_ma, long_ma=long_ma)


def create_atr_stop_loss_factor(atr_multiplier: float = 2.0) -> Factor:
    """
    Create an ATR stop loss factor with custom multiplier.

    Factory function for creating ATRStopLossFactor instances with
    configurable ATR multiplier.

    Args:
        atr_multiplier: Multiplier for ATR to set stop distance
            Common values: 2.0 (original Turtle), 1.5 (tighter), 3.0 (wider)

    Returns:
        Factor: Configured ATRStopLossFactor instance

    Example:
        >>> stop_loss = create_atr_stop_loss_factor(atr_multiplier=2.0)
        >>> stop_loss.parameters
        {'atr_multiplier': 2.0}
    """
    return ATRStopLossFactor(atr_multiplier=atr_multiplier)
