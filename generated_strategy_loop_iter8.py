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

# Factor 2: Revenue YoY growth (shifted to align with trading decisions)
# Monthly revenue data is usually released after the month ends, so shift by 2 to be safe
# Assuming revenue_yoy is already aligned to the end of the month it refers to
# We need to use the previous month's data for current month's decision
revenue_growth_factor = revenue_yoy.shift(2)

# Factor 3: ROE (shifted to avoid look-ahead bias, assuming quarterly data)
# Financial statements are usually released after the quarter ends.
# A shift of 60 days (approx 2 months) might be reasonable for quarterly data.
roe_factor = roe.shift(60)

# Factor 4: Inverse of P/E ratio (lower P/E is better)
# Add a small epsilon to avoid division by zero or very large numbers for P/E close to zero
inverse_pe = (1 / (pe_ratio + 0.01)).shift(1)

# 3. Combine factors
# Normalize factors to a 0-1 range (optional, but good practice for combining)
# For simplicity, we'll combine them directly, assuming their scales are somewhat comparable
# or that the 'is_largest' function will handle relative rankings.

# We want high momentum, high revenue growth, high ROE, and low P/E (high inverse P/E)
combined_factor = (momentum * 0.3) + (revenue_growth_factor * 0.3) + (roe_factor * 0.2) + (inverse_pe * 0.2)

# 4. Apply filters
# Liquidity filter: Average daily trading value over the last 20 days must be > 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Close price must be above 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Volume filter: Average daily volume over the last 20 days must be > 100,000 shares
volume_filter = volume.rolling(20).mean().shift(1) > 100_000

# Combine all filters
all_filters = liquidity_filter & price_filter & volume_filter

# 5. Select stocks
# Apply filters to the combined factor and then select the top 10 stocks
position = combined_factor[all_filters].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)