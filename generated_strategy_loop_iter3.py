# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
pe_ratio = data.get('price_earning_ratio:本益比')
foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')

# 2. Calculate factors

# Factor 1: Momentum (20-day returns)
# Calculate 20-day percentage change in close price
returns_20d = close.pct_change(20)
# Shift forward to avoid look-ahead bias
factor_momentum = returns_20d.shift(1)

# Factor 2: Value (Inverse P/E ratio)
# Calculate inverse P/E ratio; higher is better (lower P/E)
# Handle potential division by zero or negative P/E by replacing inf/-inf with NaN
factor_value = (1 / pe_ratio).shift(1)
factor_value = factor_value.replace([float('inf'), -float('inf')], float('nan'))

# Factor 3: Foreign Investor Strength
# Use foreign investor buying strength directly
factor_foreign_strength = foreign_strength.shift(1)

# 3. Combine factors
# Rank each factor across stocks for each day (axis=1)
# Higher momentum is better (ascending=True for returns)
ranked_momentum = factor_momentum.rank(axis=1, ascending=True)
# Higher inverse P/E is better (ascending=True for inverse P/E)
ranked_value = factor_value.rank(axis=1, ascending=True)
# Higher foreign strength is better (ascending=True for strength)
ranked_foreign_strength = factor_foreign_strength.rank(axis=1, ascending=True)

# Combine ranks by summing them. Stocks with higher combined ranks are preferred.
combined_factor = ranked_momentum + ranked_value + ranked_foreign_strength

# 4. Apply filters

# Liquidity filter: Average daily trading value over 20 days must be above 50 million TWD
avg_trading_value = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value > 50_000_000

# P/E ratio filter: Filter out stocks with P/E outside a reasonable range (e.g., 5 to 50)
# This helps to exclude unprofitable companies or those with extremely high valuations
pe_filter = (pe_ratio.shift(1) > 5) & (pe_ratio.shift(1) < 50)

# Combine all filters
# Ensure that the combined_factor itself is not NaN for a stock to be considered
final_filter = liquidity_filter & pe_filter & combined_factor.notna()

# 5. Select stocks
# Apply the combined filter and then select the top 8 stocks based on the combined factor
# The number of stocks selected is between 6 and 12, as required.
position = combined_factor[final_filter].is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)