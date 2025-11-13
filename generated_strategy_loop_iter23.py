# 1. Load data
close = data.get('etl:adj_close')
trading_value = data.get('price:成交金額')
market_value = data.get('etl:market_value')
# Underused factors for diversity
pb_ratio = data.get('price_earning_ratio:股價淨值比')
monthly_revenue = data.get('monthly_revenue:當月營收')
adj_volume = data.get('etl:adj_close_volume')
margin_ratio = data.get('etl:margin_trading_short_sales:margin_ratio')
# 2. Calculate factors with proper look-ahead prevention
# Factor 1: Inverse Price-to-Book Ratio (Value)
# Use .ffill() for quarterly data and .shift(1)
inverse_pb = (1 / pb_ratio.ffill()).shift(1)
# Factor 2: Monthly Revenue Momentum (Growth)
# Use .ffill() for monthly data, calculate MoM change, and .shift(1)
revenue_mom = monthly_revenue.ffill().pct_change(1).shift(1)
# Factor 3: Volume Momentum (Activity/Technical)
# Calculate 10-day percentage change in adjusted volume and .shift(1)
volume_momentum = adj_volume.pct_change(10).shift(1)
# Factor 4: Margin Ratio Change (Sentiment/Risk)
# Calculate 5-day change in margin ratio and .shift(1)
margin_ratio_change = margin_ratio.diff(5).shift(1)
# 3. Normalize factors and combine
# Normalize each factor to percentile ranks [0, 1]
inverse_pb_rank = inverse_pb.rank(axis=1, pct=True)
revenue_mom_rank = revenue_mom.rank(axis=1, pct=True)
volume_momentum_rank = volume_momentum.rank(axis=1, pct=True)
margin_ratio_change_rank = margin_ratio_change.rank(axis=1, pct=True)
# Combine factors with diverse weights
# Prioritizing underused fundamental and growth factors
combined_factor = (inverse_pb_rank * 0.35 +
                   revenue_mom_rank * 0.30 +
                   volume_momentum_rank * 0.20 +
                   margin_ratio_change_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average trading value over 20 days
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 40_000_000
# Price filter: Avoid penny stocks
price_filter = close.shift(1) > 15
# Market Cap filter: Avoid very small cap stocks (using underused market_value)
market_cap_filter = market_value.shift(1) > 8_000_000_000
# P/B Ratio filter: Exclude extremely high P/B stocks (using underused pb_ratio)
pb_filter = pb_ratio.ffill().shift(1) < 5
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & pb_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)