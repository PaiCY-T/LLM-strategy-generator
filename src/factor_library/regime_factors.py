"""
Regime classification factors for market state identification.

This module implements factors that identify market regimes (trending vs mean-reverting)
to help adapt strategy behavior to current market conditions.
"""

import pandas as pd
from typing import Dict, Any


def efficiency_ratio(
    close: pd.DataFrame,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate Efficiency Ratio for regime classification.

    Perry Kaufman's Efficiency Ratio measures how efficiently price moves
    from point A to point B. High ER indicates trending market, low ER
    indicates choppy/mean-reverting market.

    Formula:
        ER = |net_change| / sum(|price_changes|)

        Where:
        - net_change = close[-1] - close[-period]
        - sum(|price_changes|) = sum of absolute bar-to-bar changes

    ER Interpretation:
        ER → 1.0: Strong trend (net change ≈ total movement)
        ER → 0.0: Mean reverting/choppy (net change ≈ 0)

    Signal Mapping:
        ER ≥ 0.7  → signal = 1.0  (strong trending)
        ER ≥ 0.5  → signal = 0.5  (moderate trend)
        ER ≥ 0.3  → signal = 0.0  (neutral)
        ER ≥ 0.1  → signal = -0.5 (moderate mean reversion)
        ER < 0.1  → signal = -1.0 (strong mean reversion/choppy)

    Parameters:
        close: DataFrame of closing prices (stocks as columns)
        params: {
            'er_period': int = 10,  # Lookback period for ER calculation
        }

    Returns:
        {
            'signal': DataFrame with regime signals in [-1, 1] range,
                     1.0 = trending, -1.0 = mean-reverting
            'metadata': {
                'efficiency_ratio': DataFrame with raw ER values [0, 1],
                'net_change': DataFrame with net price changes,
                'volatility': DataFrame with price volatility
            }
        }

    Raises:
        ValueError: If er_period < 2 (insufficient data for calculation)

    Examples:
        >>> close = pd.DataFrame({'AAPL': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]})
        >>> params = {'er_period': 10}
        >>> result = efficiency_ratio(close, params)
        >>> result['metadata']['efficiency_ratio'].iloc[-1, 0]
        1.0  # Perfect uptrend

        >>> close = pd.DataFrame({'stock': [100, 105, 100, 105, 100, 105, 100, 105, 100, 105]})
        >>> result = efficiency_ratio(close, params)
        >>> result['signal'].iloc[-1, 0]
        -1.0  # Strong mean reversion (choppy)
    """
    # Extract and validate parameters
    er_period = params.get('er_period', 10)

    if er_period < 2:
        raise ValueError(f"er_period must be >= 2, got {er_period}")

    # Calculate rolling net change (absolute value)
    # net_change = |close[t] - close[t-period]|
    net_change = close.diff(er_period).abs()

    # Calculate rolling volatility (sum of absolute bar-to-bar changes)
    # volatility = sum(|close[i] - close[i-1]|) over period
    volatility = close.diff().abs().rolling(window=er_period).sum()

    # Calculate Efficiency Ratio
    # ER = net_change / volatility
    # Handle division by zero: when volatility = 0 (constant price), set ER = 0
    # Preserve NaN for insufficient data
    er = pd.DataFrame(index=close.index, columns=close.columns, dtype=float)

    for col in close.columns:
        net = net_change[col]
        vol = volatility[col]

        # Calculate ER with division by zero handling
        er_col = pd.Series(index=close.index, dtype=float)

        # Where volatility > 0, calculate ER
        mask_valid = vol > 0
        er_col[mask_valid] = net[mask_valid] / vol[mask_valid]

        # Where volatility = 0 (constant price, not NaN), set ER = 0
        mask_zero = (vol == 0.0) & vol.notna()
        er_col[mask_zero] = 0.0

        # Where volatility is NaN (insufficient data), keep as NaN
        # This happens automatically since er_col starts as NaN

        er[col] = er_col

    # Generate signals based on ER thresholds
    signal = pd.DataFrame(index=close.index, columns=close.columns, dtype=float)

    for col in close.columns:
        er_col = er[col]
        sig = pd.Series(index=er_col.index, dtype=float)

        # Only apply signal mapping where ER is not NaN
        valid_mask = er_col.notna()

        # Apply signal mapping based on ER ranges (only for valid ER values)
        sig[valid_mask & (er_col >= 0.7)] = 1.0   # Strong trending

        mask_moderate_trend = valid_mask & (er_col >= 0.5) & (er_col < 0.7)
        sig[mask_moderate_trend] = 0.5  # Moderate trend

        mask_neutral = valid_mask & (er_col >= 0.3) & (er_col < 0.5)
        sig[mask_neutral] = 0.0  # Neutral

        mask_moderate_mr = valid_mask & (er_col >= 0.1) & (er_col < 0.3)
        sig[mask_moderate_mr] = -0.5  # Moderate mean reversion

        mask_strong_mr = valid_mask & (er_col < 0.1)
        sig[mask_strong_mr] = -1.0  # Strong mean reversion (choppy)

        # Where ER is NaN, signal remains NaN (from initial Series creation)

        signal[col] = sig

    return {
        'signal': signal,
        'metadata': {
            'efficiency_ratio': er,
            'net_change': net_change,
            'volatility': volatility
        }
    }
