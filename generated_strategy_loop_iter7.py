# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
roe = data.get('fundamental_features:ROE稅後')
foreign_net_buy = data.get('foreign_main_force_buy_sell_summary')

# 2. Calculate factors

# Factor 1: Momentum (60-day returns)
returns_60d = close.pct_change(60)
momentum_factor = returns_60d.shift(1)

# Factor 2: Value (Inverse P/B ratio)
# Replace non-positive P/B ratios with a small positive number to avoid division by zero or negative values.
# Fill NaN with a small positive number as well, so it doesn't interfere with inversion.
pb_ratio_cleaned = pb_ratio.mask(pb_ratio <= 0, 0.001).fillna(0.001)
value_factor = (1 / pb_ratio_cleaned).shift(1)

# Factor 3: Quality (ROE)
# Fill NaN ROE with 0, assuming missing ROE indicates poor quality for ranking.
quality_factor = roe.fillna(0).shift(1)

# Factor 4: Institutional Flow (Foreign Investor Net Buy normalized by average trading value)
# Calculate average trading value, handle potential division by zero by replacing 0 with a small number.
avg_trading_value_20d = trading_value.rolling(20).mean()
avg_trading_value_20d_safe = avg_trading_value_20d.replace(0, 1e-9).fillna(1e-9) # Replace 0 and NaN with a small number
foreign_flow_factor = (foreign_net_buy / avg_trading_value_20d_safe).shift(1)
# Fill infinite values (if any) and NaNs with 0, assuming no flow is neutral for ranking.
foreign_flow_factor = foreign_flow_factor.replace([float('inf'), -float('inf')], 0).fillna(0)


# 3. Combine factors using ranks
# Rank each factor across stocks for each day to ensure comparability.
momentum_rank = momentum_factor.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
quality_rank = quality_factor.rank(axis=1, pct=True)
foreign_flow_rank = foreign_flow_factor.rank(axis=1, pct=True)

# Combine ranks with predefined weights.
combined_factor = (momentum_rank * 0.35 +
                   value_rank * 0.25 +
                   quality_rank * 0.20 +
                   foreign_flow_rank * 0.20)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be greater than 50 million TWD.
liquidity_filter = avg_trading_value_20d.shift(1) > 50_000_000

# P/B ratio filter: P/B must be positive and not excessively high (e.g., less than 100).
# This helps remove outliers or companies with unusual P/B values.
pb_filter = (pb_ratio.shift(1) > 0) & (pb_ratio.shift(1) < 100)

# Combine all filters
final_filter = liquidity_filter & pb_filter

# 5. Select stocks
# Apply the combined filter, then fill NaN values in the combined factor with a very small number
# before selecting the largest to ensure only filtered stocks are considered for selection.
position = combined_factor[final_filter].fillna(-1e9).is_largest(10) # Select 10 stocks (between 6-12)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)