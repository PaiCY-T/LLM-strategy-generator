# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
investment_trust_net_buy_sell = data.get('investment_trust_buy_sell_summary')
roe = data.get('fundamental_features:ROE稅後')

# 2. Calculate factors

# Factor 1: Short-term Momentum (20-day returns)
returns_20d = close.pct_change(20)
momentum_factor = returns_20d.shift(1)

# Factor 2: Value (P/B ratio)
# Lower P/B is generally better for value. We negate it so higher values mean better value.
value_factor = (-pb_ratio).shift(1)

# Factor 3: Investment Trust Flow Strength
# Calculate a 10-day rolling sum of net buy/sell to capture sustained institutional interest
it_flow_sum_10d = investment_trust_net_buy_sell.rolling(10).sum()
it_flow_factor = it_flow_sum_10d.shift(1)

# Factor 4: Quality (ROE)
# Higher ROE indicates better quality.
quality_factor = roe.shift(1)

# 3. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Close price > 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine filters
combined_filter = liquidity_filter & price_filter

# 4. Combine and rank factors
# Rank each factor across stocks on each day (axis=1).
# pct=True normalizes ranks to a 0-1 range.
ranked_momentum = momentum_factor.rank(axis=1, pct=True)
ranked_value = value_factor.rank(axis=1, pct=True)
ranked_it_flow = it_flow_factor.rank(axis=1, pct=True)
ranked_quality = quality_factor.rank(axis=1, pct=True)

# Combine ranked factors with equal weights
# We can adjust weights if needed, but for a first try, equal weights are a good starting point.
combined_factor = (ranked_momentum + ranked_value + ranked_it_flow + ranked_quality) / 4

# 5. Select stocks
# Apply the combined filter to the combined factor before selecting the largest
filtered_factor = combined_factor[combined_filter]

# Select the top 8 stocks based on the combined factor
position = filtered_factor.is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)