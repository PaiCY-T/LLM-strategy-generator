# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('etl:monthly_revenue:revenue_yoy')
roe = data.get('fundamental_features:ROE稅後')
pe_ratio = data.get('fundamental_features:本益比')
trading_value = data.get('price:成交金額')

# 2. Calculate factors

# Factor 1: Price Momentum (20-day return)
momentum = close.pct_change(20).shift(1)

# Factor 2: Revenue Growth (YoY)
# Shift revenue_yoy by 1 to avoid look-ahead bias
revenue_growth_factor = revenue_yoy.shift(1)

# Factor 3: Return on Equity (ROE)
# Shift ROE by 1 to avoid look-ahead bias
roe_factor = roe.shift(1)

# Factor 4: Inverse P/E Ratio (Value)
# Handle potential division by zero or negative P/E ratios
inverse_pe = (1 / pe_ratio).replace([float('inf'), -float('inf')], 0).shift(1)
# Normalize inverse_pe to be positive for ranking
inverse_pe = inverse_pe.where(inverse_pe > 0, 0)


# 3. Combine factors
# We want high momentum, high revenue growth, high ROE, and low PE (high inverse PE)
# Normalize factors to a similar scale if necessary, but for simple multiplication,
# we can assume relative magnitudes will drive selection.
# Let's give more weight to fundamental factors.
combined_factor = (
    momentum * 0.2
    + revenue_growth_factor * 0.3
    + roe_factor * 0.3
    + inverse_pe * 0.2
)

# 4. Apply filters
# Filter 1: Liquidity filter (average daily trading value > 50 million TWD over 20 days)
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Filter 2: Price filter (close price > 10 TWD)
price_filter = close.shift(1) > 10

# Combine filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters and then select the top 10 stocks based on the combined factor
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)