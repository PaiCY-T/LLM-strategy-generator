# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
roe = data.get('fundamental_features:ROE稅後')
pe_ratio = data.get('price_earning_ratio:本益比')
trading_value = data.get('price:成交金額')

# 2. Calculate factors

# Factor 1: Momentum (20-day return)
momentum = close.pct_change(20).shift(1)

# Factor 2: Revenue YoY growth
# Monthly data, need to forward fill to align with daily price data
revenue_yoy_daily = revenue_yoy.ffill().shift(1)

# Factor 3: ROE (Trailing 4 quarters average)
# Quarterly data, need to forward fill to align with daily price data
roe_avg = roe.rolling(window=4, min_periods=1).mean().ffill().shift(1)

# Factor 4: Inverse P/E Ratio (Value factor)
# Lower P/E is better, so take inverse
inverse_pe = (1 / pe_ratio).replace([float('inf'), -float('inf')], 0).shift(1)

# 3. Combine factors
# Normalize factors to a 0-1 range (or rank) before combining if their scales differ significantly.
# For simplicity, we'll combine directly here, assuming relative magnitudes are somewhat comparable or will be handled by ranking later.
# We'll give more weight to momentum and revenue growth, and less to ROE and inverse PE.
combined_factor = (momentum * 0.4 +
                   revenue_yoy_daily * 0.3 +
                   roe_avg * 0.2 +
                   inverse_pe * 0.1)

# 4. Apply filters
# Liquidity filter: Average daily trading value over the last 20 days must be greater than 100 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 100_000_000

# Price filter: Close price must be above 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
all_filters = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters and then select the top 10 stocks based on the combined factor
position = combined_factor[all_filters].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)