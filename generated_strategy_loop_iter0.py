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
# Use the latest available revenue_yoy for each month
revenue_growth_factor = revenue_yoy.ffill().shift(1)

# Factor 3: Value (Inverse P/B ratio)
# Lower P/B is better, so we use 1/PB
value_factor = (1 / pb_ratio).shift(1)

# Factor 4: Profitability (Net Profit Margin)
profitability_factor = net_profit_margin.shift(1)

# 3. Combine factors
# Normalize factors to a 0-1 scale (or rank them) before combining if their scales differ significantly.
# For simplicity, we'll combine them directly here, assuming relative magnitudes are somewhat comparable
# or that the selection method (is_largest) will handle it.
# A more robust approach would involve ranking or min-max scaling.

# Let's give more weight to momentum and revenue growth
combined_factor = (
    momentum * 0.35 +
    revenue_growth_factor * 0.35 +
    value_factor * 0.15 +
    profitability_factor * 0.15
)

# 4. Apply filters
# Filter 1: Liquidity filter (average daily trading value > 50 million TWD over 20 days)
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Filter 2: Price filter (stock price > 10 TWD)
price_filter = close.shift(1) > 10

# Combine filters
overall_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply the overall filter and then select the top 10 stocks based on the combined factor
position = combined_factor[overall_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)