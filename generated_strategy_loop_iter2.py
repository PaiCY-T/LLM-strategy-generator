# 1. Load data
# Price data for liquidity filter
trading_value = data.get('price:成交金額')

# Fundamental data for growth factor
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')

# Technical indicator for momentum/overbought condition
rsi = data.get('indicator:RSI')

# Institutional data for smart money flow
foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')

# 2. Calculate factors and apply look-ahead bias prevention
# Shift all factors by 1 day to ensure data is available before trading decision
revenue_yoy_shifted = revenue_yoy.shift(1)
rsi_shifted = rsi.shift(1)
foreign_strength_shifted = foreign_strength.shift(1)
trading_value_shifted = trading_value.shift(1)

# 3. Apply filters
# Liquidity filter: Average daily trading value over the last 20 days must be above 50 million TWD
avg_trading_value = trading_value_shifted.rolling(20).mean()
liquidity_filter = avg_trading_value > 50_000_000

# Fundamental filter: Positive Year-over-Year revenue growth
fundamental_filter = revenue_yoy_shifted > 0

# Technical filter: RSI below 60 (not overbought, potential for upward movement)
technical_filter = rsi_shifted < 60

# Institutional filter: Positive foreign investor buying strength
institutional_filter = foreign_strength_shifted > 0

# Combine all filters
combined_filters = liquidity_filter & fundamental_filter & technical_filter & institutional_filter

# 4. Select stocks
# From the stocks that pass all filters, select the top 10 with the highest revenue YoY growth
# We use revenue_yoy_shifted as the ranking factor
factor_to_rank = revenue_yoy_shifted[combined_filters]

# Select the top 10 stocks
position = factor_to_rank.is_largest(10)

# 5. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)