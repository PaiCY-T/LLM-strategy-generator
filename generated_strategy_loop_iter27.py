# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
pe_ratio = data.get('price_earning_ratio:本益比')
foreign_net_buy_sell = data.get('foreign_main_force_buy_sell_summary')

# 2. Calculate factors

# Factor 1: Momentum (60-day returns)
# Calculate 60-day percentage change in close price
momentum = close.pct_change(60)
# Rank stocks by momentum across the market (axis=1)
momentum_factor = momentum.rank(axis=1, pct=True)
# Shift forward to avoid look-ahead bias
momentum_factor = momentum_factor.shift(1)

# Factor 2: Value (Inverse P/E ratio)
# Calculate inverse P/E. Handle potential division by zero or negative P/E by replacing inf with NaN.
inverse_pe = 1 / pe_ratio
inverse_pe = inverse_pe.replace([float('inf'), -float('inf')], float('nan'))
# Rank stocks by inverse P/E (higher inverse P/E means lower P/E, thus better value)
value_factor = inverse_pe.rank(axis=1, pct=True)
# Shift forward
value_factor = value_factor.shift(1)

# Factor 3: Growth (Monthly Revenue YoY)
# Use Monthly Revenue YoY directly as a growth indicator
# Rank stocks by revenue YoY growth
growth_factor = revenue_yoy.rank(axis=1, pct=True)
# Shift forward
growth_factor = growth_factor.shift(1)

# Factor 4: Institutional Flow (Foreign Investor Net Buy/Sell, 5-day sum)
# Sum foreign net buy/sell over 5 days to smooth out daily fluctuations
foreign_flow_sum = foreign_net_buy_sell.rolling(5).sum()
# Rank stocks by foreign institutional flow
flow_factor = foreign_flow_sum.rank(axis=1, pct=True)
# Shift forward
flow_factor = flow_factor.shift(1)

# 3. Combine factors
# Assign weights to each factor. Weights sum to 1.
# This combination emphasizes momentum and growth, with value and institutional flow as supporting factors.
combined_factor = (
    momentum_factor * 0.35 +
    value_factor * 0.15 +
    growth_factor * 0.30 +
    flow_factor * 0.20
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be greater than 10 million TWD
avg_trading_value = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value > 10_000_000

# Price filter: Close price must be greater than 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
total_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply the combined filter to the combined factor, then select the top 10 stocks
# The number of stocks selected is within the 6-12 range.
position = combined_factor[total_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)