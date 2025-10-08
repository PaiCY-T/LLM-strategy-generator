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

# Factor 2: Volume surge (current volume vs. 60-day average)
avg_volume = volume.rolling(60).mean()
volume_surge = (volume / avg_volume).shift(1)

# Factor 3: Revenue YoY growth
# Monthly revenue data needs to be aligned with daily price data.
# We'll use the last available monthly revenue for each day.
revenue_yoy_daily = revenue_yoy.ffill().shift(1)

# Factor 4: ROE (Return on Equity)
# Fundamental data is usually quarterly, so ffill and shift.
roe_daily = roe.ffill().shift(1)

# Factor 5: Inverse P/E ratio (value factor)
# Lower P/E is generally better, so we take the inverse or negative.
# We also handle potential division by zero or negative P/E.
inverse_pe = (1 / pe_ratio).replace([float('inf'), -float('inf')], 0).shift(1)
# Cap inverse_pe to avoid outliers if P/E is very close to zero
inverse_pe = inverse_pe.clip(upper=0.1) # Assuming P/E won't be less than 10

# 3. Combine factors
# Normalize factors to a 0-1 range or rank them before combining if distributions vary widely.
# For simplicity, we'll combine directly, assuming relative scales are somewhat comparable or will be handled by ranking later.

# We want high momentum, high volume surge, high revenue growth, high ROE, and high inverse P/E (low P/E).
# Let's give more weight to fundamental factors and momentum.
combined_factor = (
    momentum * 0.3 +
    volume_surge * 0.1 +
    revenue_yoy_daily * 0.2 +
    roe_daily * 0.2 +
    inverse_pe * 0.2
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over the last 20 days must be above 50 million TWD.
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Ensure stock price is above a certain threshold (e.g., 10 TWD) to avoid penny stocks.
price_filter = close.shift(1) > 10

# Combine all filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply the filter and then select the top 10 stocks based on the combined factor.
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)