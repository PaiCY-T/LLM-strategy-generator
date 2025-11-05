# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
market_value = data.get('etl:market_value')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Long-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality & Growth (Smoothed ROE and Monthly Revenue YoY)
# Smoothed ROE (4-quarter average, forward-filled)
quality_roe = roe.rolling(4).mean().ffill().shift(1)
# Monthly Revenue YoY (forward-filled)
growth_revenue = revenue_yoy.ffill().shift(1)
# Combine quality and growth into one factor
quality_growth = quality_roe + growth_revenue
# Factor 3: Institutional Buying Strength (20-day sum of Foreign Net Buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_growth_rank = quality_growth.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
# Combine with weights. Sum of weights should be 1.0
combined_factor = (momentum_rank * 0.40 +
                   quality_growth_rank * 0.30 +
                   institutional_flow_rank * 0.30)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 75M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 75_000_000
# Price filter: Close price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20
# Market Cap filter: Market value > 10 Billion TWD (mid to large cap)
market_cap_filter = market_value.ffill().shift(1) > 10_000_000_000
# RSI filter: RSI between 30 and 70 (avoiding extreme overbought/oversold)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & rsi_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)