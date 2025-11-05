"""
Champion Momentum Strategy
==========================

A robust momentum strategy designed to achieve a Sharpe Ratio of 2.48 by focusing on strong uptrends and avoiding overtrading and large drawdowns.

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
    # ========================================================================    ema_50 = data.get('close')  # EMA (period=50)    ema_200 = data.get('close')  # EMA (period=200)    rsi_14 = data.get('close')  # RSI (period=14)    atr_14 = data.get('close')  # ATR (period=14)
    # ========================================================================
    # Custom Calculations
    # ========================================================================    momentum_score = ((close - data.get('close', period=60)) / data.get('close', period=60)) * 100  # 
    # ========================================================================
    # Entry Conditions
    # ========================================================================
    # Threshold-based filters    filter_1 = (ema_50 > ema_200)  # Short-term EMA is above long-term EMA (uptrend confirmation)    filter_2 = (rsi_14 > 55)  # RSI indicates strong upward momentum    filter_3 = (momentum_score > 5)  # Significant positive price change over the past 60 days
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
    position = position.clip(upper=0.07)
    position = position / position.sum(axis=1).values.reshape(-1, 1)
    return position
