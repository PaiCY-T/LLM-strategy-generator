# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
roe = data.get('fundamental_features:ROE稅後')
pe_ratio = data.get('price_earning_ratio:本益比')
trading_value = data.get('price:成交金額')

# 2. Calculate factors
# Factor 1: Revenue YoY growth momentum
revenue_momentum = revenue_yoy.rolling(3).mean().shift(1)

# Factor 2: ROE stability and level
# High ROE is good, but we also want stability.
# Let's use the current ROE and its standard deviation over a period.
roe_mean = roe.rolling(4).mean().shift(1) # Average ROE over 4 quarters
roe_std = roe.rolling(4).std().shift(1) # Standard deviation of ROE over 4 quarters
# We want high mean ROE and low std ROE, so a factor could be mean / (std + small_epsilon)
# To avoid division by zero or very small numbers, add a small epsilon
small_epsilon = 0.001
roe_factor = roe_mean / (roe_std + small_epsilon)
roe_factor = roe_factor.where(roe_mean > 0, 0) # Only consider positive ROE

# Factor 3: Inverse P/E ratio (value factor)
# Lower P/E is generally better, so we use 1/P/E
inverse_pe = (1 / pe_ratio).shift(1)
inverse_pe = inverse_pe.where(pe_ratio > 0, 0) # Only consider positive P/E ratios

# Factor 4: Price momentum
price_momentum = close.pct_change(60).shift(1) # 3-month momentum

# 3. Combine factors
# Normalize factors to a 0-1 range (or similar) for better combination, though not strictly necessary for ranking
# For simplicity, let's just combine them directly, assuming their scales are somewhat comparable or we rely on ranking.
# We want high revenue growth, high ROE factor, high inverse PE (low PE), and positive price momentum.
combined_factor = (
    revenue_momentum.rank(axis=1, pct=True) * 0.25 +
    roe_factor.rank(axis=1, pct=True) * 0.25 +
    inverse_pe.rank(axis=1, pct=True) * 0.25 +
    price_momentum.rank(axis=1, pct=True) * 0.25
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over the last 20 days must be above 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Stock price must be above 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Volume filter: Average daily volume over the last 20 days must be above 100,000 shares
volume_filter = volume.rolling(20).mean().shift(1) > 100_000

# Combine all filters
all_filters = liquidity_filter & price_filter & volume_filter

# 5. Select stocks
# Apply filters to the combined factor
filtered_factor = combined_factor[all_filters]

# Select the top 10 stocks based on the filtered factor
position = filtered_factor.is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)