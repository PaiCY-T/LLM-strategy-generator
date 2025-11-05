# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_strength = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')

# 2. Calculate factors
# Factor 1: Short-term Momentum (10-day percentage change)
returns_10d = close.pct_change(10)
momentum_factor = returns_10d.shift(1)

# Factor 2: Revenue Growth (Monthly Revenue YoY)
# Revenue YoY is already a growth rate, use it directly.
revenue_growth_factor = revenue_yoy.shift(1)

# Factor 3: Foreign Investor Strength
# Positive values indicate foreign buying interest.
foreign_strength_factor = foreign_strength.shift(1)

# 3. Combine factors
# Rank each factor to normalize them across stocks for combination
ranked_momentum = momentum_factor.rank(axis=1, pct=True)
ranked_revenue_growth = revenue_growth_factor.rank(axis=1, pct=True)
ranked_foreign_strength = foreign_strength_factor.rank(axis=1, pct=True)

# Combine factors with weighted average.
# Giving more weight to price momentum and fundamental growth.
combined_factor = (ranked_momentum * 0.40 + ranked_revenue_growth * 0.35 + ranked_foreign_strength * 0.25)

# 4. Apply filters
# Filter 1: Liquidity filter (average daily trading value > 50 million TWD)
avg_trading_value_20d = trading_value.rolling(20).mean()
liquidity_filter = (avg_trading_value_20d.shift(1) > 50_000_000)

# Filter 2: RSI filter (avoid extremely overbought or oversold conditions)
# Select stocks where RSI is between 30 and 60, suggesting healthy momentum without being overextended.
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 60)

# Combine all filters
final_filter = liquidity_filter & rsi_filter

# 5. Select stocks
# Apply the combined filter and then select the top 10 stocks based on the combined factor score.
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)