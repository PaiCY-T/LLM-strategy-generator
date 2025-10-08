# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
roe = data.get('fundamental_features:ROE稅後')
net_profit_margin = data.get('fundamental_features:稅後淨利率')
trading_value = data.get('price:成交金額')

# 2. Calculate factors
# Factor 1: Momentum (20-day returns)
momentum = close.pct_change(20).shift(1)

# Factor 2: Revenue Growth (YoY)
# Convert monthly revenue_yoy to daily by forward filling and then shifting
revenue_growth_factor = revenue_yoy.ffill().shift(1)

# Factor 3: Profitability (ROE and Net Profit Margin)
# Use a rolling average for fundamental data to smooth out quarterly updates
roe_factor = roe.rolling(window=60, min_periods=1).mean().shift(1)
net_profit_margin_factor = net_profit_margin.rolling(window=60, min_periods=1).mean().shift(1)

# 3. Combine factors
# Normalize factors (optional, but good practice for combining different scales)
# For simplicity, we'll combine them directly, assuming they are somewhat comparable or we want to emphasize certain ones.
# We want high momentum, high revenue growth, high ROE, and high net profit margin.
combined_factor = (momentum * 0.3) + (revenue_growth_factor * 0.3) + (roe_factor * 0.2) + (net_profit_margin_factor * 0.2)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be greater than 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Close price must be above 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Volume filter: Average daily volume over 20 days must be greater than 100,000 shares
volume_filter = volume.rolling(20).mean().shift(1) > 100_000

# Combine all filters
all_filters = liquidity_filter & price_filter & volume_filter

# 5. Select stocks
# Apply filters to the combined factor and select the top 10 stocks
position = combined_factor[all_filters].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)