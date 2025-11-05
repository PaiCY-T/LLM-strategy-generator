# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
foreign_strength = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')

# 2. Calculate factors
# Factor 1: Price Momentum (20-day returns)
returns_20d = close.pct_change(20)
momentum_factor = returns_20d.shift(1)

# Factor 2: Foreign Investor Buying Strength
# Use the strength directly as a factor
foreign_strength_factor = foreign_strength.shift(1)

# Factor 3: Monthly Revenue Year-over-Year Growth
revenue_growth_factor = revenue_yoy.shift(1)

# 3. Combine factors
# Normalize factors to a 0-1 range for better combination, then combine with weights
# For simplicity, Finlab's ranking methods often handle scale differences implicitly.
# Let's combine directly and rely on is_largest for ranking.
combined_factor = (momentum_factor * 0.4) + \
                  (foreign_strength_factor * 0.3) + \
                  (revenue_growth_factor * 0.3)

# 4. Apply filters
# Filter 1: Liquidity Filter (Average daily trading value > 50 million TWD)
avg_trading_value_20d = trading_value.rolling(20).mean()
liquidity_filter = (avg_trading_value_20d.shift(1) > 50_000_000)

# Filter 2: Price Filter (Close price > 10 TWD to avoid penny stocks)
price_filter = (close.shift(1) > 10)

# Combine all filters
total_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters to the combined factor and select the top 10 stocks
position = combined_factor[total_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)