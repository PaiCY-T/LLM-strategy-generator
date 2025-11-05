# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')

# 2. Calculate factors

# Factor 1: Price Momentum (20-day returns)
# Shift by 1 to avoid look-ahead bias
momentum_factor = close.pct_change(20).shift(1)

# Factor 2: Revenue Growth (Year-over-Year)
# Shift by 1 to avoid look-ahead bias
revenue_growth_factor = revenue_yoy.shift(1)

# Factor 3: Foreign Investor Accumulation (5-day rolling sum of net buy)
# A positive value indicates net buying by foreign investors.
# Shift by 1 to avoid look-ahead bias
foreign_flow_factor = foreign_net_buy.rolling(5).sum().shift(1)

# Factor 4: RSI for momentum confirmation
# Shift by 1 to avoid look-ahead bias
rsi_value = rsi.shift(1)

# 3. Combine factors
# We'll combine momentum, revenue growth, and foreign flow.
# Fill NaN values with 0 for combination, assuming missing data means no contribution to the factor.
combined_factor = (
    momentum_factor.fillna(0) * 0.4 +
    revenue_growth_factor.fillna(0) * 0.3 +
    foreign_flow_factor.fillna(0) * 0.3
)

# 4. Apply filters
# Filter 1: Liquidity filter - Average daily trading value over 20 days must be > 50 million TWD
# Shift by 1 to avoid look-ahead bias
avg_trading_value = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value > 50_000_000

# Filter 2: Price filter - Close price must be greater than 10 TWD to avoid penny stocks
# Shift by 1 to avoid look-ahead bias
price_filter = close.shift(1) > 10

# Filter 3: RSI filter - RSI between 50 and 75 for healthy momentum, avoiding overbought conditions
rsi_momentum_filter = (rsi_value > 50) & (rsi_value < 75)

# Combine all filters
all_filters = liquidity_filter & price_filter & rsi_momentum_filter

# 5. Select stocks
# Apply all filters to the combined factor. Stocks not passing filters will have NaN.
filtered_factor = combined_factor[all_filters]

# Select the top 10 stocks based on the filtered combined factor.
# is_largest will automatically handle NaN values by excluding them from selection.
position = filtered_factor.is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)