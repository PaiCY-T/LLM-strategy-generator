# 1. Load data - ALWAYS use adjusted data for price!
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits
trading_value = data.get('price:成交金額')  # OK for liquidity filter
market_cap = data.get('price:總市值') # Underused: Total Market Cap
net_profit_margin_raw = data.get('fundamental_features:稅後淨利率') # Underused: Net Profit Margin
book_value_per_share_raw = data.get('fundamental_features:每股淨值') # Underused: Book Value Per Share
revenue_mom_raw = data.get('monthly_revenue:上月比較增減(%)') # Underused: Monthly Revenue MoM
adj_volume = data.get('etl:adj_close_volume') # Underused: Adjusted Close Volume
# 2. Calculate factors
# Factor 1: Quality - Smoothed Net Profit Margin
# Use 4-quarter rolling average for stability
quality_factor = net_profit_margin_raw.ffill().rolling(window=4, min_periods=1).mean().shift(1)
# Factor 2: Value - Inverse Price-to-Book Ratio
# Calculate P/B using adjusted close and book value per share
# Then take the inverse, higher is better for value
pb_ratio = close.shift(1) / book_value_per_share_raw.ffill().shift(1)
value_factor = (1 / pb_ratio)
# Factor 3: Short-term Growth Momentum - Monthly Revenue MoM
# Already a percentage, forward fill and shift
growth_factor = revenue_mom_raw.ffill().shift(1)
# Factor 4: Volume Momentum - Ratio of short-term to long-term average volume
# Indicates increasing interest/accumulation
short_term_volume_avg = adj_volume.rolling(window=20).mean().shift(1)
long_term_volume_avg = adj_volume.rolling(window=60).mean().shift(1)
volume_momentum_factor = short_term_volume_avg / long_term_volume_avg - 1
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
quality_rank = quality_factor.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
growth_rank = growth_factor.rank(axis=1, pct=True)
volume_momentum_rank = volume_momentum_factor.rank(axis=1, pct=True)
# Combine with diverse weights
combined_factor = (quality_rank * 0.30 +
                   value_rank * 0.25 +
                   growth_rank * 0.25 +
                   volume_momentum_rank * 0.20)
# 4. Apply filters for risk management and liquidity
# Liquidity filter: Average daily trading value > 100M TWD (higher threshold)
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 100_000_000
# Price filter: Stock price > 15 TWD (slightly higher minimum price)
price_filter = close.shift(1) > 15
# Market Cap filter: Market capitalization > 10 Billion TWD (target larger companies)
market_cap_filter = market_cap.shift(1) > 10_000_000_000
# P/B Ratio filter: Avoid extremely overvalued stocks by P/B (P/B < 3)
pb_filter = pb_ratio < 3
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & pb_filter]
# 5. Select stocks
# Select top 8 stocks (fewer stocks for higher conviction)
position = filtered_factor.is_largest(8)
# 6. Run backtest
# Quarterly rebalancing with a tighter stop loss of 5%
report = sim(position, resample="Q", upload=False, stop_loss=0.05)