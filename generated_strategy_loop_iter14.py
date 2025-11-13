# 1. Load data - ALWAYS use adjusted data for price!
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits
trading_value = data.get('price:成交金額')  # OK for liquidity filter
market_value = data.get('etl:market_value') # Adjusted market capitalization
# Underused fundamental factors
net_profit_margin = data.get('fundamental_features:稅後淨利率') # Quality
revenue_mom = data.get('monthly_revenue:上月比較增減(%)') # Short-term Growth
pe_ratio = data.get('price_earning_ratio:本益比') # Value
# Underused volume factor
adj_volume = data.get('etl:adj_close_volume') # Adjusted volume
# 2. Calculate factors
# Factor 1: Quality - Smoothed Net Profit Margin (4-quarter average)
# Use ffill() for quarterly data, then shift(1) to prevent look-ahead bias
quality_factor = net_profit_margin.ffill().rolling(window=4, min_periods=1).mean().shift(1)
# Factor 2: Short-term Growth - Monthly Revenue MoM
# Use ffill() for monthly data, then shift(1)
growth_factor = revenue_mom.ffill().shift(1)
# Factor 3: Value - Inverse P/E Ratio
# Use ffill() for quarterly data, then shift(1)
# Filter out non-positive P/E ratios to avoid division by zero or negative values
pe_factor = pe_ratio.ffill().shift(1)
inverse_pe = 1 / pe_factor
# Replace infinite values (from P/E=0) with NaN and ensure only positive P/E contribute to value
inverse_pe = inverse_pe.replace([float('inf'), -float('inf')], float('nan'))
inverse_pe[pe_factor <= 0] = float('nan')
# Factor 4: Volume Momentum - 5-day percentage change of 20-day average volume
# Shift(1) for daily data
volume_momentum = adj_volume.rolling(20).mean().pct_change(5).shift(1)
# 3. Combine factors (normalize first!)
quality_rank = quality_factor.rank(axis=1, pct=True)
growth_rank = growth_factor.rank(axis=1, pct=True)
inverse_pe_rank = inverse_pe.rank(axis=1, pct=True)
volume_momentum_rank = volume_momentum.rank(axis=1, pct=True)
# Combine with diverse weights
# Prioritize quality and value, with growth and volume as supporting signals
combined_factor = (quality_rank * 0.35 +
                   inverse_pe_rank * 0.30 +
                   growth_rank * 0.20 +
                   volume_momentum_rank * 0.15)
# 4. Apply filters (using different thresholds for diversity)
# Liquidity filter: Average daily trading value > 70M TWD (higher than common 30-50M)
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD (higher than common 10 TWD)
price_filter = close.shift(1) > 20
# Market Cap filter: Market value > 10 Billion TWD (targeting mid-large caps)
market_cap_filter = market_value.shift(1) > 10_000_000_000
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter]
# 5. Select stocks
# Select top 10 stocks (a common, diversified portfolio size)
position = filtered_factor.is_largest(10)
# 6. Run backtest
# Use a tighter stop loss (0.05) for different risk profile
report = sim(position, resample="Q", upload=False, stop_loss=0.05)