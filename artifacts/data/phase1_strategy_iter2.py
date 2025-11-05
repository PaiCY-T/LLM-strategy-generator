"""
Champion Momentum Strategy
==========================

A robust momentum strategy designed to capture strong trends while managing risk, aiming for a high Sharpe Ratio.

Strategy Type: momentum
Rebalancing: W-FRI
Generated from YAML specification
"""

def strategy(data):
    """
    Champion Momentum Strategy

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
    # ========================================================================    rsi_14 = data.get('RSI_14')  # RSI (period=14)    ema_50 = data.get('EMA_50')  # EMA (period=50)    atr_14 = data.get('ATR_14')  # ATR (period=14)
    # ========================================================================
    # Custom Calculations
    # ========================================================================    momentum_score = rsi_14 * (close / ema_50)  # 
    # ========================================================================
    # Entry Conditions
    # ========================================================================
    # Threshold-based filters    filter_1 = (rsi_14 > 60)  # Strong upward momentum indicated by RSI    filter_2 = (close > ema_50)  # Price is above the 50-day Exponential Moving Average, confirming an uptrend    filter_3 = (momentum_score > 1.05)  # Momentum score indicates price is outperforming the EMA trend
    # Liquidity filters    liquidity_filter_volume = volume.rolling(20).mean() > 50000000
    # Combine threshold filters    threshold_mask = filter_1 & filter_2 & filter_3    threshold_mask = threshold_mask & liquidity_filter_volume
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
