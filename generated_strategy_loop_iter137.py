# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
market_cap = data.get('etl:market_value')
# 2. Calculate factors
# Factor 1: Medium-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
# ffill() for quarterly data, then shift(1)
quality_roe = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
# ffill() for monthly data, then shift(1)
growth_revenue = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Accumulation (20-day sum of foreign net buy)
inst_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: Value (Inverse P/E Ratio)
# ffill() for quarterly data, then shift(1)
# Handle potential division by zero or negative P/E by replacing with NaN, then rank handles it.
value_factor = (1 / pe_ratio.replace([0, -0], float('nan'))).ffill().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_roe_rank = quality_roe.rank(axis=1, pct=True)
growth_revenue_rank = growth_revenue.rank(axis=1, pct=True)
inst_flow_rank = inst_flow.rank(axis=1, pct=True)
value_factor_rank = value_factor.rank(axis=1, pct=True)
# Combine with meaningful weights
combined_factor = (momentum_rank * 0.30 +
                   quality_roe_rank * 0.20 +
                   growth_revenue_rank * 0.20 +
                   inst_flow_rank * 0.20 +
                   value_factor_rank * 0.10)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 75M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 75_000_000
# Price filter: Close price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20
# Market Cap filter: Market Cap > 10 Billion TWD for larger, more stable companies
market_cap_filter = market_cap.shift(1) > 10_000_000_000
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter]
# 5. Select stocks (top 10 based on combined factor score)
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)