# 1. Load data
close = data.get('price:收盤價')
price_change_percent = data.get('price:漲跌百分比')
eps = data.get('financial_statement:每股盈餘')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
trading_value = data.get('price:成交金額')

# 2. Calculate factors
# Factor 1: Price Momentum (60-day cumulative percentage change)
momentum = price_change_percent.rolling(60).sum()
momentum_factor = momentum.shift(1)

# Factor 2: Earnings Yield (EPS / Close Price)
# Handle potential division by zero or NaN in close price
# Replace infinite values with NaN before calculating
earnings_yield = (eps / close).replace([float('inf'), -float('inf')], float('nan'))
earnings_yield_factor = earnings_yield.shift(1)

# Factor 3: Foreign Investor Net Buy (20-day smoothed sum)
# Sum foreign net buy over 20 days to capture sustained institutional interest
foreign_net_buy_sum = foreign_net_buy.rolling(20).sum()
foreign_net_buy_factor = foreign_net_buy_sum.shift(1)

# 3. Combine factors
# Rank each factor to put them on a comparable scale (0-1)
ranked_momentum = momentum_factor.rank(axis=1, pct=True)
ranked_earnings_yield = earnings_yield_factor.rank(axis=1, pct=True)
ranked_foreign_net_buy = foreign_net_buy_factor.rank(axis=1, pct=True)

# Combine ranked factors with weighted average
# Give more weight to momentum and earnings yield, less to foreign net buy
combined_factor = (ranked_momentum * 0.4 + ranked_earnings_yield * 0.4 + ranked_foreign_net_buy * 0.2)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be above 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Only consider stocks with a close price above 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply the combined filter to the combined factor and select the top 8 stocks
position = combined_factor[final_filter].is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)