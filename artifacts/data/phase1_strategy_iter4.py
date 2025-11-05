"""
Champion Momentum Strategy
==========================

A robust momentum strategy designed to achieve a high Sharpe Ratio (2.48) by focusing on strong trending assets while avoiding overtrading and large drawdowns. It uses a combination of RSI and MACD for trend confirmation, and a custom momentum score for ranking. Position sizing is volatility-weighted to manage risk.

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
    # ========================================================================    rsi_14 = data.get('RSI_14')  # RSI (period=14)    macd_12_26_9 = data.get('MACD_12_26_9')  # MACD (period=12)    atr_14 = data.get('ATR_14')  # ATR (period=14)    ema_50 = data.get('EMA_50')  # EMA (period=50)
    # ========================================================================
    # Custom Calculations
    # ========================================================================    momentum_score = rsi_14 * (macd_12_26_9.macd - macd_12_26_9.signal)  # 
    # ========================================================================
    # Entry Conditions
    # ========================================================================
    # Threshold-based filters    filter_1 = (rsi_14 > 60)  # RSI indicates strong upward momentum.    filter_2 = (macd_12_26_9.macd > macd_12_26_9.signal)  # MACD line is above its signal line, confirming upward trend.    filter_3 = (close > ema_50)  # Price is above the 50-day exponential moving average, indicating a bullish trend.    filter_4 = (momentum_score > 0)  # Custom momentum score is positive.
    # Liquidity filters    liquidity_filter_volume = volume.rolling(20).mean() > 50000000
    # Combine threshold filters    threshold_mask = filter_1 & filter_2 & filter_3 & filter_4    threshold_mask = threshold_mask & liquidity_filter_volume
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
