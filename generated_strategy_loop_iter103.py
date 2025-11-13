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
# Factor 2: Quality (ROE with 4-quarter smoothing)
quality = roe.ffill().rolling(4).mean().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Accumulation (20-day sum of Foreign Net Buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
growth_rank = growth.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.25 +
                   growth_rank * 0.25 +
                   flow_rank * 0.20)
# 4. Apply filters
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
price_filter = close.shift(1) > 15
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70) # Avoid extreme overbought/oversold
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter]
# 5. Select stocks
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)