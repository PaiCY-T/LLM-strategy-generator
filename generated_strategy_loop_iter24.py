# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
pe_ratio = data.get('price_earning_ratio:本益比')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('foreign_main_force_buy_sell_summary')

# 2. Calculate factors

# Factor 1: Momentum (60-day returns)
# Calculate 60-day percentage change in close price
momentum = close.pct_change(60)
# Rank momentum values across stocks for normalization
momentum_rank = momentum.rank(axis=1, pct=True)
# Shift forward to avoid look-ahead bias
momentum_factor = momentum_rank.shift(1)

# Factor 2: Value/Growth (Inverse P/E and Revenue YoY)
# Filter P/E to exclude negative or extremely high values (0 to 50)
pe_filtered = pe_ratio.where((pe_ratio > 0) & (pe_ratio < 50))
# Calculate inverse P/E (lower P/E is better, so inverse makes higher values better)
inv_pe = 1 / pe_filtered
# Rank inverse P/E values
inv_pe_rank = inv_pe.rank(axis=1, pct=True)

# Rank Monthly Revenue YoY growth
revenue_yoy_rank = revenue_yoy.rank(axis=1, pct=True)

# Combine inverse P/E and Revenue YoY with equal weights
value_growth_factor = (inv_pe_rank * 0.5 + revenue_yoy_rank * 0.5).shift(1)

# Factor 3: Institutional Flow (5-day average of foreign net buy)
# Calculate a 5-day moving average of foreign investor net buy/sell
foreign_flow_smoothed = foreign_net_buy.rolling(5).mean()
# Rank the smoothed foreign flow
foreign_flow_rank = foreign_flow_smoothed.rank(axis=1, pct=True)
# Shift forward
foreign_flow_factor = foreign_flow_rank.shift(1)

# 3. Combine factors (weighted average of ranked factors)
# Assign weights to each factor
combined_factor = (momentum_factor * 0.4 + value_growth_factor * 0.3 + foreign_flow_factor * 0.3)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be greater than 10 million NTD
avg_trading_value = trading_value.rolling(20).mean()
liquidity_filter = (avg_trading_value > 10_000_000).shift(1)

# Fundamental filter: P/E ratio must be positive and less than 40
pe_valid_filter = (pe_ratio > 0) & (pe_ratio < 40)
# Shift the P/E filter forward
pe_valid_filter = pe_valid_filter.shift(1)

# Combine all filters
final_filter = liquidity_filter & pe_valid_filter

# 5. Select stocks
# Select the top 10 stocks based on the combined factor, after applying all filters
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)