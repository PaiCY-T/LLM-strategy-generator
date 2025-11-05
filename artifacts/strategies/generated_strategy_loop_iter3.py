# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
roe = data.get('fundamental_features:ROE稅後')
pe_ratio = data.get('price_earning_ratio:本益比')
trading_value = data.get('price:成交金額')

# 2. Calculate factors
# Factor 1: Revenue YoY growth momentum
# Use a 3-month average of YoY growth to smooth out monthly fluctuations
# Shift by 1 to avoid look-ahead bias
revenue_momentum = revenue_yoy.rolling(3).mean().shift(1)

# Factor 2: ROE (Return on Equity)
# Use the latest available ROE, shifted by 1 to avoid look-ahead
roe_factor = roe.shift(1)

# Factor 3: Inverse of P/E ratio (value factor)
# Lower P/E is generally better, so we use 1/PE. Handle potential division by zero or negative P/E.
# Shift by 1 to avoid look-ahead bias
inverse_pe = (1 / pe_ratio).replace([float('inf'), -float('inf')], 0).shift(1)

# 3. Combine factors
# Normalize factors to a 0-1 range (optional, but good practice for combining)
# For simplicity, we'll combine directly, assuming their scales are somewhat comparable or that the ranking will handle it.
# We'll give more weight to fundamental factors.
combined_factor = (revenue_momentum * 0.4) + (roe_factor * 0.4) + (inverse_pe * 0.2)

# 4. Apply filters
# Liquidity filter: Average daily trading value over the last 20 days must be above 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Close price must be above 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply the combined filter and then select the top 10 stocks based on the combined factor
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)