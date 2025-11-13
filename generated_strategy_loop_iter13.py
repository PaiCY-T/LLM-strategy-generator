# 1. Load data
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits, used for price filter
trading_value = data.get('price:成交金額')  # OK for liquidity filter
market_value = data.get('etl:market_value') # Underused, used for market cap filter
# Underused factors for diversity
pe_ratio = data.get('price_earning_ratio:本益比')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
revenue_mom_change = data.get('monthly_revenue:上月比較增減(%)')
adj_volume = data.get('etl:adj_close_volume')
# 2. Calculate factors
# Factor 1: Inverse P/E Ratio (Value) - Prioritize underused
# Handle potential division by zero or negative P/E by replacing inf/-inf with NaN
inverse_pe = (1 / pe_ratio).replace([float('inf'), -float('inf')], float('nan'))
inverse_pe = inverse_pe.ffill().shift(1)
# Factor 2: Inverse P/B Ratio (Value) - Prioritize underused
# Handle potential division by zero or negative P/B by replacing inf/-inf with NaN
inverse_pb = (1 / pb_ratio).replace([float('inf'), -float('inf')], float('nan'))
inverse_pb = inverse_pb.ffill().shift(1)
# Factor 3: Monthly Revenue MoM Change (Growth) - Prioritize underused
revenue_growth_factor = revenue_mom_change.ffill().shift(1)
# Factor 4: Volume Momentum (Demand/Interest) - Prioritize underused
# Ratio of short-term average volume to long-term average volume
short_avg_volume = adj_volume.rolling(5).mean()
long_avg_volume = adj_volume.rolling(20).mean()
volume_momentum = (short_avg_volume / long_avg_volume - 1).shift(1)
# 3. Combine factors (normalize first!)
inverse_pe_rank = inverse_pe.rank(axis=1, pct=True)
inverse_pb_rank = inverse_pb.rank(axis=1, pct=True)
revenue_growth_rank = revenue_growth_factor.rank(axis=1, pct=True)
volume_momentum_rank = volume_momentum.rank(axis=1, pct=True)
# Combine with diverse weights, emphasizing underused value and growth factors
combined_factor = (inverse_pe_rank * 0.30 +
                   inverse_pb_rank * 0.30 +
                   revenue_growth_rank * 0.25 +
                   volume_momentum_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average trading value over 20 days, slightly higher threshold
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 40_000_000
# Price filter: Avoid penny stocks, slightly higher threshold
price_filter = close.shift(1) > 15
# Market Cap filter: Target larger companies, underused as a filter
market_cap_filter = market_value.shift(1) > 8_000_000_000
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter]
# 5. Select stocks
# Select top 10 stocks
position = filtered_factor.is_largest(10)
# 6. Run backtest
# Use quarterly rebalancing and a slightly higher stop loss for structural diversity
report = sim(position, resample="Q", upload=False, stop_loss=0.10)