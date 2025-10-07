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

# Factor 2: Revenue YoY growth (shifted by 1 month, then 1 day)
# Monthly data needs careful shifting. Finlab handles monthly data alignment.
# We shift by 1 to avoid look-ahead from the current month's revenue announcement.
revenue_growth_factor = revenue_yoy.shift(1)

# Factor 3: ROE (shifted by 1 quarter, then 1 day)
# Quarterly data needs careful shifting. Finlab handles quarterly data alignment.
# We shift by 1 to avoid look-ahead from the current quarter's ROE announcement.
roe_factor = roe.shift(1)

# Factor 4: Inverse P/E ratio (lower P/E is better, so 1/PE)
# Add a small constant to avoid division by zero if PE is 0, and handle negative P/E.
# For negative P/E, we can set it to NaN or a very low value to exclude it.
inverse_pe = (1 / pe_ratio.replace([0, -0], 0.000001)).replace([float('inf'), -float('inf')], 0).shift(1)
# Filter out extremely high inverse_pe values that might result from very low positive P/E,
# or set negative P/E to NaN.
inverse_pe[pe_ratio <= 0] = None # Exclude stocks with non-positive P/E
inverse_pe = inverse_pe.clip(upper=0.1) # Cap inverse PE to prevent outliers from dominating

# 3. Combine factors
# Normalize factors if necessary, but for this simple combination, direct multiplication/addition can work.
# We'll give more weight to momentum and revenue growth.
combined_factor = (momentum * 0.4 + revenue_growth_factor * 0.3 + roe_factor * 0.2 + inverse_pe * 0.1)

# 4. Apply filters
# Liquidity filter: Average daily trading value over the last 20 days must be > 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Close price must be above 10 TWD (to avoid penny stocks)
price_filter = close.shift(1) > 10

# Volume filter: Average daily volume over the last 20 days must be > 100,000 shares
avg_volume = volume.rolling(20).mean().shift(1)
volume_filter = avg_volume > 100_000

# Combine all filters
all_filters = liquidity_filter & price_filter & volume_filter

# 5. Select stocks
# Apply filters and then select the top 10 stocks based on the combined factor
position = combined_factor[all_filters].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)