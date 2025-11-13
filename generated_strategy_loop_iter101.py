# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
market_cap = data.get('etl:market_value')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
# ffill() for quarterly data, then shift(1)
quality_roe = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Revenue Growth (monthly data aligned to daily)
# ffill() for monthly data, then shift(1)
revenue_growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks
momentum_rank = momentum.rank(axis=1, pct=True)
quality_roe_rank = quality_roe.rank(axis=1, pct=True)
revenue_growth_rank = revenue_growth.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
# Combine with meaningful weights
combined_factor = (momentum_rank * 0.35 +
                   quality_roe_rank * 0.25 +
                   revenue_growth_rank * 0.25 +
                   institutional_flow_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Close price > 15 TWD
price_filter = close.shift(1) > 15
# Market Cap filter: Market capitalization > 5B TWD
market_cap_filter = market_cap.ffill().shift(1) > 5_000_000_000
# P/E Ratio filter: P/E between 0 and 30 (avoid negative/extremely high P/E)
pe_ratio_filter = (pe_ratio.ffill().shift(1) > 0) & (pe_ratio.ffill().shift(1) < 30)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & pe_ratio_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)