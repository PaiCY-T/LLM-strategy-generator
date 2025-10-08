# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
roe = data.get('fundamental_features:ROE稅後')
pe_ratio = data.get('price_earning_ratio:本益比')
trading_value = data.get('price:成交金額')

# 2. Calculate factors

# Factor 1: Momentum (20-day returns)
momentum = close.pct_change(20).shift(1)

# Factor 2: Revenue Growth (YoY)
# We need to forward fill revenue_yoy as it's monthly data
revenue_growth_factor = revenue_yoy.ffill().shift(1)

# Factor 3: ROE (lagged by a quarter to ensure data availability)
# Assuming ROE is quarterly, we shift by 60 trading days (approx a quarter)
roe_factor = roe.shift(60)

# Factor 4: Inverse P/E Ratio (Value factor)
# Lower P/E is better, so we take the inverse
# Add a small epsilon to avoid division by zero if PE is 0, and handle negative PEs (unprofitable companies)
inverse_pe = (1 / (pe_ratio + 0.001)).replace([float('inf'), -float('inf')], 0).shift(1)
# For negative P/E, we want to penalize, so set to 0 or a very small number
inverse_pe[pe_ratio <= 0] = 0


# 3. Combine factors
# Normalize factors to a 0-1 range (optional but good practice for combining)
# For simplicity, we'll just combine them directly, assuming their scales are somewhat comparable or we want to emphasize certain factors.
# We want high momentum, high revenue growth, high ROE, and low PE (high inverse PE)
combined_factor = (
    momentum * 0.3 +
    revenue_growth_factor * 0.3 +
    roe_factor * 0.2 +
    inverse_pe * 0.2
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over the last 20 days > 100 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 100_000_000

# Price filter: Close price must be above 10 TWD to avoid penny stocks
price_filter = (close.shift(1) > 10)

# Volume filter: Average daily volume over the last 20 days > 100000 shares
avg_volume = volume.rolling(20).mean().shift(1)
volume_filter = avg_volume > 100000

# Combine all filters
final_filter = liquidity_filter & price_filter & volume_filter

# 5. Select stocks
# Apply the filter to the combined factor and then select the top 8 stocks
position = combined_factor[final_filter].is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)