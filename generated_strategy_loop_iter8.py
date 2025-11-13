# 1. Load data
close = data.get('etl:adj_close')
trading_value = data.get('price:成交金額')
market_value = data.get('etl:market_value')
net_profit_margin_raw = data.get('fundamental_features:稅後淨利率')
pe_ratio_raw = data.get('price_earning_ratio:本益比')
revenue_mom_raw = data.get('monthly_revenue:上月比較增減(%)')
adj_volume_raw = data.get('etl:adj_close_volume')
# 2. Calculate factors
# Factor 1: Quality (Smoothed Net Profit Margin)
# Use 4-quarter rolling mean for stability and ffill for daily alignment
quality_factor = net_profit_margin_raw.ffill().rolling(4).mean().shift(1)
# Factor 2: Value (Inverse P/E Ratio)
# Invert P/E for a "cheapness" factor, ffill for daily alignment
# Handle potential division by zero or negative P/E with filters later
value_factor = (1 / pe_ratio_raw.ffill()).shift(1)
# Factor 3: Growth Momentum (Smoothed Monthly Revenue MoM)
# Use 3-month rolling mean for stability and ffill for daily alignment
growth_factor = revenue_mom_raw.ffill().rolling(3).mean().shift(1)
# Factor 4: Volume Momentum (Current Volume vs. Long-term Average Volume)
# Compare current adjusted volume to its 60-day moving average
volume_momentum = (adj_volume_raw / adj_volume_raw.rolling(60).mean()).shift(1)
# 3. Combine factors (normalize first!)
quality_rank = quality_factor.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
growth_rank = growth_factor.rank(axis=1, pct=True)
volume_rank = volume_momentum.rank(axis=1, pct=True)
# Combine with diverse weights
combined_factor = (quality_rank * 0.30 +
                   value_rank * 0.25 +
                   growth_rank * 0.25 +
                   volume_rank * 0.20)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Stock price > 20 TWD
price_filter = close.shift(1) > 20
# Market Cap filter: Market value > 10 Billion TWD (focus on larger companies)
market_cap_filter = market_value.shift(1) > 10_000_000_000
# P/E Ratio filter: P/E between 5 and 30 (avoiding extreme values and non-profitable companies)
pe_filter = (pe_ratio_raw.ffill().shift(1) > 5) & (pe_ratio_raw.ffill().shift(1) < 30)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & pe_filter]
# 5. Select stocks
# Select top 12 stocks based on the combined factor score
position = filtered_factor.is_largest(12)
# 6. Run backtest
# Quarterly rebalancing with an 8% stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.08)