# 1. Load data
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits, used for price filter
trading_value = data.get('price:成交金額')  # OK for liquidity filter
net_profit_margin = data.get('fundamental_features:稅後淨利率')  # Underused: Quality factor
revenue_mom_change = data.get('monthly_revenue:上月比較增減(%)')  # Underused: Short-term growth momentum
pe_ratio = data.get('price_earning_ratio:本益比')  # Underused: Valuation factor
adj_volume = data.get('etl:adj_close_volume')  # Underused: Volume confirmation
market_cap = data.get('price:總市值')  # Underused: Market cap filter
# 2. Calculate factors
# Factor 1: Quality (Net Profit Margin, 4-quarter average)
# Use .ffill() for quarterly data to align to daily frequency
quality_factor = net_profit_margin.ffill().rolling(4).mean().shift(1)
# Factor 2: Short-term Growth Momentum (Monthly Revenue MoM Change)
# Use .ffill() for monthly data to align to daily frequency
growth_factor = revenue_mom_change.ffill().shift(1)
# Factor 3: Value (Inverse P/E Ratio)
# Handle potential non-positive P/E ratios to avoid division by zero or negative values
pe_ratio_filtered = pe_ratio.ffill().where(pe_ratio.ffill() > 0)
value_factor = (1 / pe_ratio_filtered).shift(1)
# Clip extreme inverse P/E values to prevent outliers from dominating
value_factor = value_factor.clip(lower=0, upper=0.1) # Corresponds to P/E >= 10
# Factor 4: Volume Momentum (Ratio of short-term to long-term average volume)
short_vol_avg = adj_volume.rolling(5).mean()
long_vol_avg = adj_volume.rolling(20).mean()
# Avoid division by zero or very small long_vol_avg
volume_momentum = (short_vol_avg / long_vol_avg).where(long_vol_avg > 0).shift(1)
# 3. Combine factors (normalize first!)
quality_rank = quality_factor.rank(axis=1, pct=True)
growth_rank = growth_factor.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
volume_momentum_rank = volume_momentum.rank(axis=1, pct=True)
# Combine with diverse weights
combined_factor = (quality_rank * 0.35 +
                   growth_rank * 0.30 +
                   value_rank * 0.20 +
                   volume_momentum_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value > 40 million TWD over 20 days
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 40_000_000
# Price filter: Stock price > 15 TWD
price_filter = close.shift(1) > 15
# Market Cap filter: Total market value > 8 billion TWD (using an underused factor)
market_cap_filter = market_cap.shift(1) > 8_000_000_000
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
# Rebalance quarterly, with a slightly different stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.07)