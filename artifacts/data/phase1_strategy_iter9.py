"""
Champion Momentum Builder
=========================

A momentum strategy designed to capture strong trends while managing drawdowns and avoiding overtrading, aiming for high Sharpe ratio.

Strategy Type: momentum
Rebalancing: W-FRI
Generated from YAML specification
"""

def strategy(data):
    """
    Champion Momentum Builder

    This strategy was auto-generated from a YAML specification.

    Strategy Parameters:
    - Type: momentum
    - Rebalancing: W-FRI    """

    # ========================================================================
    # Load Base Data
    # ========================================================================
    close = data.get('price:收盤價')
    volume = data.get('price:成交股數')
    # ========================================================================
    # Load Technical Indicators
    # ========================================================================    ema_50 = data.get('close')  # EMA (period=50)    ema_200 = data.get('close')  # EMA (period=200)    rsi_14 = data.get('close')  # RSI (period=14)    atr_14 = data.get('high') - data.get('low')  # ATR (period=14)
    # ========================================================================
    # Custom Calculations
    # ========================================================================    trend_strength = ema_50 / ema_200  #     volatility_adjusted_rsi = rsi_14 / (atr_14 / close)  # 
    # ========================================================================
    # Entry Conditions
    # ========================================================================
    # Threshold-based filters    filter_1 = (trend_strength > 1.05)  # Price is in a strong uptrend (50-day EMA significantly above 200-day EMA).    filter_2 = (volatility_adjusted_rsi > 2.5)  # RSI indicates strong upward momentum, adjusted for volatility to avoid whipsaws.    filter_3 = (rsi_14 < 70)  # Avoid entering when RSI is already overbought, to reduce immediate pullback risk.
    # Combine threshold filters    threshold_mask = filter_1 & filter_2 & filter_3
    # No ranking rules - use threshold mask only
    entry_mask = threshold_mask
    # ========================================================================
    # Position Sizing
    # ========================================================================
    # Volatility-weighted (inverse volatility)
    returns = close.pct_change()
    volatility = returns.rolling(60).std()
    inv_vol = 1.0 / volatility
    weights = inv_vol[entry_mask]
    weights = weights / weights.sum(axis=1).values.reshape(-1, 1)
    position = weights
    # Apply maximum position size limit
    position = position.clip(upper=0.08)
    position = position / position.sum(axis=1).values.reshape(-1, 1)
    return position
