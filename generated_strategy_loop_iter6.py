# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
roe = data.get('fundamental_features:ROE稅後')
pe_ratio = data.get('price_earning_ratio:本益比')

# 2. Calculate factors
# Momentum factor (20-day return)
returns_20d = close.pct_change(20).shift(1)

# Revenue growth factor (YoY)
revenue_growth_factor = revenue_yoy.shift(1)

# ROE factor
roe_factor = roe.shift(1)

# Inverse P/E ratio factor (lower P/E is better)
# Handle potential division by zero or negative P/E
inverse_pe_factor = (1 / pe_ratio).replace([float('inf'), -float('inf')], 0).shift(1)

# 3. Combine factors
# Normalize factors (simple min-max normalization for illustration, though Finlab often handles this implicitly)
# For simplicity, we'll combine directly, assuming relative ranking is what matters.
# Higher returns, higher revenue growth, higher ROE, lower PE are generally better.
combined_factor = (
    returns_20d * 0.3 +
    revenue_growth_factor * 0.3 +
    roe_factor * 0.2 +
    inverse_pe_factor * 0.2
)

# 4. Apply filters
# Liquidity filter: average daily trading value over 20 days > 50 million TWD
trading_value = data.get('price:成交金額')
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: stock price > 10 TWD
price_filter = close.shift(1) > 10

# Combine filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters and select the top 10 stocks based on the combined factor
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)