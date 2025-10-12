# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
net_profit_margin = data.get('fundamental_features:稅後淨利率')
trading_value = data.get('price:成交金額')

# 2. Calculate factors

# Factor 1: Momentum (20-day returns)
momentum = close.pct_change(20).shift(1)

# Factor 2: Revenue Growth (YoY)
# Use a 3-month average for stability
avg_revenue_yoy = revenue_yoy.rolling(3).mean().shift(1)

# Factor 3: Value (Inverse P/B ratio)
# Lower P/B is better, so we use 1/PB
# Add a small constant to avoid division by zero and handle negative P/B if any
value = (1 / (pb_ratio + 0.001)).shift(1)

# Factor 4: Profitability (Net Profit Margin)
profitability = net_profit_margin.shift(1)

# 3. Combine factors
# Normalize factors to a 0-1 range (or similar) to combine them effectively
# For simplicity, we'll just sum them, assuming they are somewhat comparable or we want to give equal weight.
# A more robust approach would involve rank normalization or z-scoring.

# We want high momentum, high revenue growth, high value (low PB), high profitability
# So, we sum them up.
combined_factor = momentum + avg_revenue_yoy + value + profitability

# 4. Apply filters
# Filter 1: Liquidity filter (average daily trading value over 20 days > 50 million TWD)
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Filter 2: Price filter (stock price > 10 TWD to avoid penny stocks)
price_filter = close.shift(1) > 10

# Combine filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply the combined filter to the combined factor
filtered_factor = combined_factor[final_filter]

# Select the top 10 stocks based on the filtered combined factor
position = filtered_factor.is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)