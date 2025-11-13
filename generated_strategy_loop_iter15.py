# 1. Load data
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits
trading_value = data.get('price:成交金額')  # OK for liquidity filter
market_value = data.get('etl:market_value') # Market capitalization
net_profit_margin = data.get('fundamental_features:稅後淨利率') # Underused: Quality
pe_ratio = data.get('price_earning_ratio:本益比') # Underused: Value
pb_ratio = data.get('price_earning_ratio:股價淨值比') # Underused: Value
revenue_mom = data.get('monthly_revenue:上月比較增減(%)') # Underused: Growth
adj_close_volume = data.get('etl:adj_close_volume') # Underused: Volume
# 2. Calculate factors with .shift(1) and .ffill()
# Factor 1: Smoothed Net Profit Margin (Quality)
# Use 4-quarter rolling average for stability
quality_factor = net_profit_margin.ffill().rolling(window=4, min_periods=1).mean().shift(1)
# Factor 2: Inverse P/E Ratio (Value)
# Handle potential division by zero or negative P/E with a small epsilon
value_pe_factor = (1 / (pe_ratio.ffill().shift(1) + 1e-6))
# Factor 3: Monthly Revenue MoM (Growth)
growth_factor = revenue_mom.ffill().shift(1)
# Factor 4: Volume Momentum (Liquidity/Interest)
# Calculate 60-day volume change to capture sustained interest
volume_momentum_factor = adj_close_volume.pct_change(60).shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks
quality_rank = quality_factor.rank(axis=1, pct=True)
value_pe_rank = value_pe_factor.rank(axis=1, pct=True)
growth_rank = growth_factor.rank(axis=1, pct=True)
volume_momentum_rank = volume_momentum_factor.rank(axis=1, pct=True)
# Combine with unique weights. Prioritize quality and value, with growth and volume as confirmation.
combined_factor = (quality_rank * 0.35 +
                   value_pe_rank * 0.30 +
                   growth_rank * 0.20 +
                   volume_momentum_rank * 0.15)
# 4. Apply filters for structural diversity
# Liquidity filter: Higher threshold than common patterns
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 75_000_000
# Price filter: Higher minimum price to avoid penny stocks
price_filter = close.shift(1) > 25
# Market Cap filter: Focus on larger, more stable companies
market_cap_filter = market_value.shift(1) > 15_000_000_000
# P/E Ratio filter: Avoid extremely high or negative P/E ratios (distressed or speculative)
pe_filter = (pe_ratio.ffill().shift(1) > 5) & (pe_ratio.ffill().shift(1) < 30)
# P/B Ratio filter: Avoid extremely low or high P/B ratios
pb_filter = (pb_ratio.ffill().shift(1) > 0.8) & (pb_ratio.ffill().shift(1) < 4)
# Quality filter: Ensure positive net profit margin
positive_profit_filter = quality_factor > 0
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & pe_filter & pb_filter & positive_profit_filter]
# 5. Select stocks
# Select top 10 stocks based on the filtered combined factor
position = filtered_factor.is_largest(10)
# 6. Run backtest with quarterly rebalancing and 8% stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.08)