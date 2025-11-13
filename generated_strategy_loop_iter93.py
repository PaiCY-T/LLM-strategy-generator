# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Long-term Price Momentum (60-day returns)
# Captures sustained upward price movement.
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE, 4-quarter smoothed)
# Measures profitability and management effectiveness, smoothed to reduce noise.
quality = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
# Indicates company's top-line growth, forward-filled for daily alignment.
growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (10-day sum of Foreign Net Buy)
# Reflects smart money accumulation, indicating positive sentiment.
institutional_flow = foreign_net_buy.rolling(10).sum().shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks to ensure comparability.
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
growth_rank = growth.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
# Combine factors with intelligent weights.
# Momentum and Quality are given higher weights as they are often strong drivers.
# Growth and Institutional Flow provide additional confirmation.
combined_factor = (momentum_rank * 0.35 +
                   quality_rank * 0.25 +
                   growth_rank * 0.25 +
                   institutional_flow_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 70M TWD.
# Ensures tradability and avoids illiquid stocks.
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD.
# Avoids penny stocks, which are often highly volatile and speculative.
price_filter = close.shift(1) > 20
# RSI filter: Avoid extreme overbought/oversold conditions (30 < RSI < 70).
# Helps to select stocks that are not at immediate reversal points,
# focusing on healthy trends or consolidating phases.
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters to the combined factor.
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter]
# 5. Select stocks
# Select the top 10 stocks based on the filtered combined factor score.
# This provides a diversified portfolio of high-conviction stocks.
position = filtered_factor.is_largest(10)
# 6. Run backtest
# Execute the backtest with quarterly rebalancing and an 8% stop loss.
# Quarterly rebalancing aligns with fundamental data updates and reduces transaction costs.
# Stop loss is a critical risk management component.
report = sim(position, resample="Q", upload=False, stop_loss=0.08)