# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
market_cap = data.get('etl:market_value')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum_factor = close.pct_change(60).shift(1)
# Factor 2: Quality (4-quarter smoothed ROE)
# ROE is quarterly, so ffill to daily frequency and then shift
quality_factor = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
# Monthly revenue, so ffill to daily frequency and then shift
growth_factor = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Buying Pressure (20-day sum of foreign net buy)
institutional_flow_factor = foreign_net_buy.rolling(20).sum().shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
momentum_rank = momentum_factor.rank(axis=1, pct=True)
quality_rank = quality_factor.rank(axis=1, pct=True)
growth_rank = growth_factor.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow_factor.rank(axis=1, pct=True)
# Combine factors with meaningful weights
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.25 +
                   growth_rank * 0.25 +
                   institutional_flow_rank * 0.20)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Close price > 15 TWD to avoid penny stocks
price_filter = close.shift(1) > 15
# Market Cap filter: Market value > 10B TWD for mid-to-large cap focus
# Market cap might have gaps, so ffill before shifting
market_cap_filter = market_cap.ffill().shift(1) > 10_000_000_000
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)