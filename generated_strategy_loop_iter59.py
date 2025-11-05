# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
market_cap = data.get('etl:market_value')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
# Forward-fill quarterly data to daily, then shift
quality = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
# Forward-fill monthly data to daily, then shift
growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of foreign net buying)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: Value (Inverse P/E Ratio, lower P/E is better)
# Forward-fill quarterly data to daily, then shift
# Handle potential division by zero or negative P/E by replacing with NaN
value_factor_raw = pe_ratio.ffill().shift(1)
# Replace non-positive P/E with NaN to avoid issues with inverse or ranking
value_factor_raw = value_factor_raw.mask(value_factor_raw <= 0)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
growth_rank = growth.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
# For value, lower P/E is better, so we invert the rank (1 - rank)
value_rank = 1 - value_factor_raw.rank(axis=1, pct=True)
# Combine with weights
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.25 +
                   growth_rank * 0.20 +
                   flow_rank * 0.15 +
                   value_rank * 0.10)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 75M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 75_000_000
# Price filter: Close price > 20 TWD
price_filter = close.shift(1) > 20
# Market Cap filter: Market cap > 15B TWD
market_cap_filter = market_cap.shift(1) > 15_000_000_000
# P/E Ratio filter: P/E between 5 and 30 (avoid extreme values)
pe_filter = (value_factor_raw > 5) & (value_factor_raw < 30)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & pe_filter]
# 5. Select stocks
# Select top 12 stocks based on the combined factor score
position = filtered_factor.is_largest(12)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)