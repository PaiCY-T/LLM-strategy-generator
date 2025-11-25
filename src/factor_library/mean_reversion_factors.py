"""
Mean Reversion Factors - RSI, RVOL, Bollinger %B (Spec B P1).

This module provides mean reversion factor calculations using TA-Lib
for technical indicator computation.

Factors:
- RSI Factor: Relative Strength Index for overbought/oversold detection
- RVOL Factor: Relative Volume for volume anomaly detection
- Bollinger %B Factor: Bollinger Bands percentage for price positioning

All factors follow the functional interface:
    result = factor_func(close_data, parameters) -> Dict[str, pd.DataFrame]

No look-ahead bias: Calculations use only past data (TTPT validated).
"""

import logging
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def rsi_factor(
    close: pd.DataFrame,
    parameters: Dict[str, Any]
) -> Dict[str, pd.DataFrame]:
    """RSI Mean Reversion Factor using TA-Lib.

    Calculates RSI and converts it to a trading signal in [-1, 1] range.
    Oversold (RSI < 30) generates positive signal (buy).
    Overbought (RSI > 70) generates negative signal (sell).

    Parameters:
        close: DataFrame of close prices (Dates x Symbols)
        parameters: Dict with:
            - rsi_period (int): RSI calculation period (default: 14)
            - oversold_threshold (float): Oversold threshold (default: 30)
            - overbought_threshold (float): Overbought threshold (default: 70)

    Returns:
        Dict with:
            - 'rsi': DataFrame of RSI values [0, 100]
            - 'signal': DataFrame of trading signals [-1, 1]
                - Positive signal for oversold (buy opportunity)
                - Negative signal for overbought (sell opportunity)

    Example:
        >>> close = pd.DataFrame({'2330': [100, 101, 102, ...], ...})
        >>> result = rsi_factor(close, {'rsi_period': 14})
        >>> rsi = result['rsi']
        >>> signal = result['signal']

    Note:
        Signal mapping: signal = (50 - RSI) / 50
        - RSI = 0 → signal = 1.0 (maximum buy)
        - RSI = 50 → signal = 0.0 (neutral)
        - RSI = 100 → signal = -1.0 (maximum sell)
    """
    # Extract parameters with defaults
    rsi_period = parameters.get('rsi_period', 14)
    oversold_threshold = parameters.get('oversold_threshold', 30)
    overbought_threshold = parameters.get('overbought_threshold', 70)

    logger.debug(
        f"Computing RSI factor: period={rsi_period}, "
        f"oversold={oversold_threshold}, overbought={overbought_threshold}"
    )

    # Calculate RSI for each column
    rsi_df = _calculate_rsi(close, rsi_period)

    # Calculate signal from RSI
    # Linear mapping: (50 - RSI) / 50
    # RSI 0 → signal 1.0 (oversold = buy)
    # RSI 50 → signal 0.0 (neutral)
    # RSI 100 → signal -1.0 (overbought = sell)
    signal = (50 - rsi_df) / 50

    # Clip signal to [-1, 1] (should already be in range, but ensure)
    signal = signal.clip(-1.0, 1.0)

    return {
        'rsi': rsi_df,
        'signal': signal
    }


def _calculate_rsi(close: pd.DataFrame, period: int) -> pd.DataFrame:
    """Calculate RSI for each column in DataFrame.

    Uses the standard RSI calculation:
    1. Calculate price changes
    2. Separate gains and losses
    3. Calculate exponential moving average of gains/losses
    4. RSI = 100 - (100 / (1 + RS))

    Args:
        close: DataFrame of close prices
        period: RSI calculation period

    Returns:
        DataFrame of RSI values [0, 100]
    """
    try:
        # Try to use TA-Lib if available (faster, more accurate)
        import talib
        return close.apply(lambda x: talib.RSI(x.values, timeperiod=period))
    except ImportError:
        logger.debug("TA-Lib not available, using pandas implementation")
        return _calculate_rsi_pandas(close, period)


def _calculate_rsi_pandas(close: pd.DataFrame, period: int) -> pd.DataFrame:
    """Pure pandas RSI implementation (fallback when TA-Lib unavailable).

    Uses Wilder's smoothing (EMA with alpha = 1/period).

    Args:
        close: DataFrame of close prices
        period: RSI calculation period

    Returns:
        DataFrame of RSI values [0, 100]
    """
    # Calculate price changes
    delta = close.diff()

    # Separate gains and losses
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)

    # Calculate Wilder's smoothed average (EMA with alpha = 1/period)
    # This is the traditional RSI calculation method
    alpha = 1.0 / period

    avg_gains = gains.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    avg_losses = losses.ewm(alpha=alpha, adjust=False, min_periods=period).mean()

    # Calculate RS and RSI
    rs = avg_gains / avg_losses

    # Handle division by zero (when avg_losses = 0)
    rs = rs.replace([np.inf, -np.inf], np.nan)

    # RSI = 100 - (100 / (1 + RS))
    rsi = 100 - (100 / (1 + rs))

    # When avg_losses = 0 and avg_gains > 0, RSI = 100
    # When avg_losses = 0 and avg_gains = 0, RSI = 50 (neutral)
    mask_no_loss = avg_losses == 0
    mask_no_gain = avg_gains == 0

    rsi = rsi.where(~(mask_no_loss & ~mask_no_gain), 100.0)
    rsi = rsi.where(~(mask_no_loss & mask_no_gain), 50.0)

    return rsi


def rvol_factor(
    volume: pd.DataFrame,
    parameters: Dict[str, Any]
) -> Dict[str, pd.DataFrame]:
    """RVOL (Relative Volume) Factor.

    Calculates relative volume compared to moving average.
    High RVOL indicates unusual volume activity.

    Parameters:
        volume: DataFrame of trading volume (Dates x Symbols)
        parameters: Dict with:
            - rvol_period (int): Moving average period (default: 20)
            - high_rvol_threshold (float): High volume threshold (default: 2.0)
            - low_rvol_threshold (float): Low volume threshold (default: 0.5)

    Returns:
        Dict with:
            - 'rvol': DataFrame of relative volume ratios
            - 'signal': DataFrame of volume signals [-1, 1]
                - Positive for high volume (potential breakout)
                - Negative for low volume (caution)

    Example:
        >>> result = rvol_factor(volume, {'rvol_period': 20})
        >>> rvol = result['rvol']
    """
    # Extract parameters with defaults
    rvol_period = parameters.get('rvol_period', 20)
    high_threshold = parameters.get('high_rvol_threshold', 2.0)
    low_threshold = parameters.get('low_rvol_threshold', 0.5)

    logger.debug(
        f"Computing RVOL factor: period={rvol_period}, "
        f"high_thresh={high_threshold}, low_thresh={low_threshold}"
    )

    # Calculate moving average of volume
    ma_volume = volume.rolling(window=rvol_period, min_periods=1).mean()

    # Calculate relative volume
    rvol = volume / ma_volume

    # Handle division by zero
    rvol = rvol.replace([np.inf, -np.inf], np.nan)

    # Calculate signal based on RVOL
    # High RVOL (> 2.0) → positive signal (volume confirmation)
    # Low RVOL (< 0.5) → negative signal (low conviction)
    # Normal RVOL → neutral

    signal = pd.DataFrame(0.0, index=volume.index, columns=volume.columns)

    # High volume: signal = min(1.0, (rvol - high_threshold) / high_threshold)
    high_mask = rvol > high_threshold
    signal = signal.where(~high_mask, ((rvol - high_threshold) / high_threshold).clip(0, 1))

    # Low volume: signal = max(-1.0, (rvol - low_threshold) / low_threshold)
    low_mask = rvol < low_threshold
    signal = signal.where(~low_mask, ((rvol - low_threshold) / low_threshold).clip(-1, 0))

    return {
        'rvol': rvol,
        'signal': signal
    }


def bollinger_percentb_factor(
    close: pd.DataFrame,
    parameters: Dict[str, Any]
) -> Dict[str, pd.DataFrame]:
    """Bollinger %B Factor for mean reversion.

    Calculates Bollinger %B (percentage of price within bands).
    Values near 0 indicate oversold, values near 1 indicate overbought.

    Parameters:
        close: DataFrame of close prices (Dates x Symbols)
        parameters: Dict with:
            - bb_period (int): Bollinger Bands period (default: 20)
            - bb_std (float): Standard deviation multiplier (default: 2.0)

    Returns:
        Dict with:
            - 'percentb': DataFrame of %B values (typically 0-1, can exceed)
            - 'signal': DataFrame of trading signals [-1, 1]
                - Positive for %B < 0.2 (oversold = buy)
                - Negative for %B > 0.8 (overbought = sell)

    Note:
        %B = (Close - Lower Band) / (Upper Band - Lower Band)
        - %B = 0 when price at lower band
        - %B = 0.5 when price at middle band
        - %B = 1 when price at upper band
    """
    bb_period = parameters.get('bb_period', 20)
    bb_std = parameters.get('bb_std', 2.0)

    logger.debug(f"Computing Bollinger %B: period={bb_period}, std={bb_std}")

    # Calculate middle band (SMA)
    middle_band = close.rolling(window=bb_period, min_periods=1).mean()

    # Calculate standard deviation
    rolling_std = close.rolling(window=bb_period, min_periods=1).std()

    # Calculate upper and lower bands
    upper_band = middle_band + (bb_std * rolling_std)
    lower_band = middle_band - (bb_std * rolling_std)

    # Calculate %B
    band_width = upper_band - lower_band
    percentb = (close - lower_band) / band_width

    # Handle division by zero
    percentb = percentb.replace([np.inf, -np.inf], np.nan)

    # Calculate signal
    # %B < 0.2 → oversold → positive signal
    # %B > 0.8 → overbought → negative signal
    # Linear interpolation between 0.2 and 0.8

    signal = (0.5 - percentb) * 2  # Maps 0→1, 0.5→0, 1→-1
    signal = signal.clip(-1.0, 1.0)

    return {
        'percentb': percentb,
        'upper_band': upper_band,
        'lower_band': lower_band,
        'middle_band': middle_band,
        'signal': signal
    }
