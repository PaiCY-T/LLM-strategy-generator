# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
roe = data.get('fundamental_features:ROE稅後')
pe_ratio = data.get('price_earning_ratio:本益比')

# 2. Calculate factors
# Factor 1: Price Momentum (20-day returns)
momentum = close.pct_change(20).shift(1)

# Factor 2: Revenue Growth (YoY)
# Shift revenue_yoy by 1 to avoid look-ahead bias
revenue_growth_factor = revenue_yoy.shift(1)

# Factor 3: ROE (Return on Equity)
# Shift ROE by 1 to avoid look-ahead bias
roe_factor = roe.shift(1)

# Factor 4: Inverse P/E Ratio (Value factor)
# Lower P/E is generally better, so use inverse
inverse_pe_factor = (1 / pe_ratio).shift(1)

# 3. Combine factors
# Normalize factors (optional, but good practice for combining)
# For simplicity, we'll combine directly, assuming similar scales or that relative ranks matter more.
# Higher momentum, higher revenue growth, higher ROE, lower P/E are generally good.
combined_factor = (
    momentum * 0.4 +
    revenue_growth_factor * 0.2 +
    roe_factor * 0.2 +
    inverse_pe_factor * 0.2
)

# 4. Apply filters
# Liquidity filter: Average daily trading volume over the last 20 days > 1,000,000 shares
avg_volume = volume.rolling(20).mean().shift(1)
liquidity_filter = avg_volume > 1_000_000

# Price filter: Close price must be above 10 (to avoid penny stocks)
price_filter = close.shift(1) > 10

# Combine all filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply the combined filter and then select the top 8 stocks based on the combined factor
position = combined_factor[final_filter].is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)