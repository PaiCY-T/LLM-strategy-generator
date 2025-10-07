# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('etl:monthly_revenue:revenue_yoy')
foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')

# 2. Calculate factors
# Momentum factor (20-day returns)
returns = close.pct_change(20)
momentum_factor = returns.shift(1)

# ROE factor (higher is better)
roe_factor = roe.shift(1)

# Revenue YoY growth factor (higher is better)
revenue_yoy_factor = revenue_yoy.shift(1)

# Foreign investor buying strength factor (higher is better)
foreign_strength_factor = foreign_strength.shift(1)

# 3. Combine factors
# Normalize factors (optional, but good practice for combining)
# For simplicity, we'll combine directly, assuming similar scales or that relative ranks matter more.
# A more robust approach would involve ranking or z-scoring.

# Combine factors with weights
# Prioritize momentum and fundamental strength
combined_factor = (
    momentum_factor * 0.4 +
    roe_factor * 0.3 +
    revenue_yoy_factor * 0.2 +
    foreign_strength_factor * 0.1
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Stock price must be above 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Volume filter: Average daily volume over 20 days > 100,000 shares
avg_volume = volume.rolling(20).mean().shift(1)
volume_filter = avg_volume > 100_000

# Combine all filters
all_filters = liquidity_filter & price_filter & volume_filter

# 5. Select stocks
# Apply filters to the combined factor
filtered_factor = combined_factor[all_filters]

# Select the top 10 stocks based on the filtered combined factor
position = filtered_factor.is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)