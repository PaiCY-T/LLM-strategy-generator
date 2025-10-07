# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('etl:monthly_revenue:revenue_yoy')
pb_ratio = data.get('fundamental_features:股價淨值比')
net_profit_margin = data.get('fundamental_features:稅後淨利率')
trading_value = data.get('price:成交金額')

# 2. Calculate factors
# Momentum factor: 60-day price change
momentum = close.pct_change(60).shift(1)

# Revenue growth factor: Monthly revenue YoY
# Since revenue_yoy is monthly, we need to forward fill to daily data
revenue_growth_factor = revenue_yoy.ffill().shift(1)

# Value factor: Inverse of P/B ratio
# Lower P/B is better, so we use 1/PB
value_factor = (1 / pb_ratio).shift(1)

# Profitability factor: Net Profit Margin
profitability_factor = net_profit_margin.shift(1)

# 3. Combine factors
# Normalize factors to a 0-1 range (or similar) for combination
# For simplicity, we'll just combine them directly, assuming their scales are somewhat comparable or we want to emphasize certain ones.
# A more robust approach would involve rank normalization or z-scoring.
combined_factor = (momentum * 0.3) + (revenue_growth_factor * 0.3) + (value_factor * 0.2) + (profitability_factor * 0.2)

# 4. Apply filters
# Liquidity filter: Average daily trading value over the last 20 days must be greater than 100 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 100_000_000

# Price filter: Stock price must be above 10 TWD
price_filter = close.shift(1) > 10

# Combine all filters
all_filters = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters and then select the top 10 stocks based on the combined factor
position = combined_factor[all_filters].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)