# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality & Growth (Combined ROE and Monthly Revenue YoY)
# Smooth ROE over 4 quarters and forward-fill
roe_smoothed = roe.rolling(4).mean().ffill().shift(1)
# Forward-fill monthly revenue YoY
revenue_growth = revenue_yoy.ffill().shift(1)
# Combine ROE and Revenue Growth (simple average for now, normalization will handle scale)
quality_growth_factor = (roe_smoothed + revenue_growth) / 2
# Factor 3: Institutional Accumulation (20-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_growth_rank = quality_growth_factor.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
# Combine with weights
combined_factor = (momentum_rank * 0.40 +
                   quality_growth_rank * 0.35 +
                   flow_rank * 0.25)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 75M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 75_000_000
# Price filter: Close price > 20 TWD
price_filter = close.shift(1) > 20
# RSI filter: Avoid overbought/oversold conditions (30 < RSI < 70)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)