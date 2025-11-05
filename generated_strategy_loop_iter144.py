# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
market_cap = data.get('etl:market_value')
# 2. Calculate factors
# Factor 1: Long-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality & Growth (Smoothed ROE and recent Revenue Growth)
# ROE is quarterly, revenue_yoy is monthly, ffill to daily
smoothed_roe = roe.ffill().rolling(4).mean()
recent_revenue_growth = revenue_yoy.ffill().rolling(3).mean()
quality_growth = (smoothed_roe + recent_revenue_growth).shift(1)
# Factor 3: Institutional Buying Strength (20-day cumulative foreign net buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 4: RSI Strength (using RSI directly, higher values indicate strength)
rsi_factor = rsi.shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_growth_rank = quality_growth.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
rsi_rank = rsi_factor.rank(axis=1, pct=True)
# Combine with meaningful weights
combined_factor = (momentum_rank * 0.30 +
                   quality_growth_rank * 0.30 +
                   institutional_flow_rank * 0.25 +
                   rsi_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20
# Market Cap filter: Market value > 10 Billion TWD for mid-large caps
market_cap_filter = market_cap.shift(1) > 10_000_000_000
# RSI range filter: RSI between 30 and 70 to avoid extreme overbought/oversold conditions
rsi_range_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & rsi_range_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)