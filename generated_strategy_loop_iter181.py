# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
market_cap = data.get('etl:market_value')
# 2. Calculate factors
# Factor 1: Long-term Momentum (60-day returns)
momentum_factor = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE) - 4-quarter rolling average, forward-filled, then shifted
quality_factor = roe.rolling(4, min_periods=1).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY) - Forward-filled, then shifted
growth_factor = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of Foreign Net Buy) - Fill NaN with 0, then sum, then shifted
foreign_flow_factor = foreign_net_buy.fillna(0).rolling(20).sum().shift(1)
# Factor 5: RSI Reversal (Inverse RSI, favoring lower RSI for potential rebound, within a healthy range)
# We calculate (100 - RSI) so lower RSI values result in higher factor scores.
rsi_reversal_factor = (100 - rsi).shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum_factor.rank(axis=1, pct=True)
quality_rank = quality_factor.rank(axis=1, pct=True)
growth_rank = growth_factor.rank(axis=1, pct=True)
foreign_flow_rank = foreign_flow_factor.rank(axis=1, pct=True)
rsi_reversal_rank = rsi_reversal_factor.rank(axis=1, pct=True)
# Combine normalized factors with meaningful weights
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.20 +
                   growth_rank * 0.20 +
                   foreign_flow_rank * 0.15 +
                   rsi_reversal_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD (avoiding penny stocks)
price_filter = close.shift(1) > 20
# RSI health filter: RSI between 30 and 70 (avoiding extreme overbought/oversold conditions)
rsi_healthy_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Market Cap filter: Market Cap > 10 Billion TWD (focus on larger, more stable companies)
market_cap_filter = market_cap.shift(1) > 10_000_000_000
# Combine all filters
all_filters = liquidity_filter & price_filter & rsi_healthy_filter & market_cap_filter
# Apply filters to the combined factor
filtered_factor = combined_factor[all_filters]
# 5. Select stocks
# Select top 10 stocks based on the filtered combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
# Backtest with quarterly rebalancing and an 8% stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.08)