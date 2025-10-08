# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
roe = data.get('fundamental_features:ROE稅後')
pe_ratio = data.get('price_earning_ratio:本益比')
market_value = data.get('market_value')

# 2. Calculate factors
# Factor 1: Price Momentum (20-day return)
momentum = close.pct_change(20).shift(1)

# Factor 2: Revenue Growth (YoY)
# Monthly revenue data is usually reported with a lag, so shift by 30 days (approx 1 month)
# to ensure it's available before the trading decision.
revenue_growth_factor = revenue_yoy.shift(30)

# Factor 3: ROE (Return on Equity)
# Fundamental data is typically quarterly and reported with a lag. Shift by 90 days (approx 3 months).
roe_factor = roe.shift(90)

# Factor 4: Inverse P/E Ratio (Value)
# Lower P/E is generally better for value. Shift by 90 days.
inverse_pe_factor = (1 / pe_ratio).shift(90)

# 3. Combine factors
# Normalize factors to a 0-1 range (or similar) before combining,
# though for simple multiplication/addition, raw values can sometimes work.
# Here, we'll just combine them directly, assuming their scales are somewhat compatible
# or that the selection method (is_largest) will handle relative rankings.
# We'll give more weight to momentum and revenue growth.
combined_factor = (momentum * 0.4) + (revenue_growth_factor * 0.3) + (roe_factor * 0.2) + (inverse_pe_factor * 0.1)

# 4. Apply filters
# Filter 1: Liquidity filter (average daily trading value > 50 million TWD)
trading_value = data.get('price:成交金額')
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Filter 2: Market Cap Filter (only consider stocks with market cap > 10 billion TWD)
market_cap_filter = market_value.shift(1) > 10_000_000_000

# Filter 3: Price filter (close price > 10 TWD to avoid penny stocks)
price_filter = close.shift(1) > 10

# Combine all filters
all_filters = liquidity_filter & market_cap_filter & price_filter

# 5. Select stocks
# Apply filters and then select the top 10 stocks based on the combined factor
position = combined_factor[all_filters].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)