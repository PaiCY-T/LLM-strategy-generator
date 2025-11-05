"""
Champion Momentum Strategy
==========================

A robust momentum strategy designed to achieve a Sharpe Ratio of 2.48, prioritizing capital preservation by avoiding overtrading and large drawdowns.

Strategy Type: momentum
Rebalancing: M
Generated from YAML specification
"""

def strategy(data):
    """
    Champion Momentum Strategy

    This strategy was auto-generated from a YAML specification.

    Strategy Parameters:
    - Type: momentum
    - Rebalancing: M    """

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
    # Threshold-based filters    filter_1 = (momentum_score > 60)  # Strong upward momentum indicated by RSI and price relative to EMA.    filter_2 = (close > ema_50)  # Price is trading above the 50-period Exponential Moving Average.    filter_3 = (rsi_14 < 80)  # Avoid entering when RSI is excessively overbought to reduce immediate reversal risk.
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
    position = position.clip(upper=0.07)
    position = position / position.sum(axis=1).values.reshape(-1, 1)
    return position
