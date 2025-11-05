# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
market_cap = data.get('etl:market_value')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Long-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
# ROE is quarterly, so ffill and then smooth
quality = roe.ffill().rolling(4).mean().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
# Monthly data, so ffill to daily frequency
growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
growth_rank = growth.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
# Combine with meaningful weights
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.30 +
                   growth_rank * 0.20 +
                   flow_rank * 0.20)
# 4. Apply filters
# Mandatory Liquidity filter: Average daily trading value > 50M TWD over 20 days
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Mandatory Price filter: Close price > 20 TWD
price_filter = close.shift(1) > 20
# Market Cap filter: Market value > 10B TWD (focus on mid-large cap)
market_cap_filter = market_cap.shift(1) > 10_000_000_000
# RSI filter: Avoid extreme overbought/oversold conditions (RSI between 30 and 70)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & rsi_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
# Backtest with quarterly rebalancing and an 8% stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.08)