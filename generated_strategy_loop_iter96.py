# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
# 2. Calculate factors
# Factor 1: Long-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE smoothed over 4 quarters)
# ffill() for quarterly data, then shift(1)
quality_roe = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue Year-over-Year)
# ffill() for monthly data, then shift(1)
growth_revenue = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Buying Pressure (20-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: Value (Inverse of P/E Ratio)
# ffill() for monthly/quarterly data, then shift(1)
value_pe = (1 / pe_ratio).ffill().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_roe_rank = quality_roe.rank(axis=1, pct=True)
growth_revenue_rank = growth_revenue.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
value_pe_rank = value_pe.rank(axis=1, pct=True)
# Combine quality and growth into a single factor
quality_growth_rank = (quality_roe_rank * 0.6 + growth_revenue_rank * 0.4)
# Combine all normalized factors with weights
combined_factor = (momentum_rank * 0.30 +
                   quality_growth_rank * 0.25 +
                   institutional_flow_rank * 0.25 +
                   value_pe_rank * 0.20)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 75M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 75_000_000
# Price filter: Stock price > 20 TWD
price_filter = close.shift(1) > 20
# P/E Ratio filter: P/E between 5 and 30 (avoid negative P/E and extremely high P/E)
pe_filter = (pe_ratio.ffill().shift(1) > 5) & (pe_ratio.ffill().shift(1) < 30)
# Positive ROE filter: Ensure companies are profitable
roe_positive_filter = roe.ffill().shift(1) > 0
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & pe_filter & roe_positive_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)