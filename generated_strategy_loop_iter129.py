# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum_factor = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
quality_factor = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY, forward-filled)
growth_factor = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day cumulative foreign net buy)
inst_flow_factor = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: Value (Inverse P/E ratio)
value_factor = (1 / pe_ratio).shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks
momentum_rank = momentum_factor.rank(axis=1, pct=True)
quality_rank = quality_factor.rank(axis=1, pct=True)
growth_rank = growth_factor.rank(axis=1, pct=True)
inst_flow_rank = inst_flow_factor.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
# Combine ranks with meaningful weights
combined_factor = (momentum_rank * 0.35 +
                   quality_rank * 0.20 +
                   growth_rank * 0.20 +
                   inst_flow_rank * 0.15 +
                   value_rank * 0.10)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD
price_filter = close.shift(1) > 20
# P/E Ratio filter: Avoid extremely high or very low/negative P/E ratios
pe_filter = (pe_ratio.shift(1) < 30) & (pe_ratio.shift(1) > 5)
# Apply all filters
all_filters = liquidity_filter & price_filter & pe_filter
filtered_factor = combined_factor[all_filters]
# 5. Select stocks
# Select top 10 stocks based on the filtered combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)