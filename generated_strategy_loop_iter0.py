# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
rsi = data.get('indicator:RSI')
foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')

# 2. Calculate factors

# Factor 1: 20-day Price Momentum
# Calculate 20-day percentage change in close price
momentum_20d = close.pct_change(20)
factor_momentum = momentum_20d.shift(1)

# Factor 2: Monthly Revenue Year-over-Year Growth
# Use the provided revenue_yoy directly as a growth factor
factor_revenue_growth = revenue_yoy.shift(1)

# Factor 3: Inverse RSI (Contrarian signal: lower RSI implies oversold, potential buy)
# RSI typically ranges from 0-100. (100 - RSI) will be higher for lower RSI values.
factor_inverse_rsi = (100 - rsi).shift(1)

# Factor 4: Foreign Investor Buying Strength
# Use the provided foreign investor strength directly
factor_foreign_strength = foreign_strength.shift(1)

# 3. Combine factors
# Combine the factors with equal weights.
# All factors are designed such that a higher value is desirable for buying.
combined_factor = (
    factor_momentum * 0.25 +
    factor_revenue_growth * 0.25 +
    factor_inverse_rsi * 0.25 +
    factor_foreign_strength * 0.25
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over the last 20 days must be above 50 million TWD.
# This ensures we only trade sufficiently liquid stocks.
avg_trading_value_20d = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value_20d > 50_000_000

# 5. Select stocks
# Apply the liquidity filter to the combined factor
filtered_factor = combined_factor[liquidity_filter]

# Select the top 10 stocks with the highest combined factor score
position = filtered_factor.is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)