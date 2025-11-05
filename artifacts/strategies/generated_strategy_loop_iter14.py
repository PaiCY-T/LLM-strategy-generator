# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
rsi = data.indicator('RSI')
foreign_strength = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')

# 2. Calculate factors

# Factor 1: Fundamental Growth (Monthly Revenue YoY)
# Higher revenue growth is better
factor_rev_growth = revenue_yoy.shift(1)

# Factor 2: Technical Momentum (RSI Trend)
# Calculate the 5-day average of RSI, then its 5-day change to capture momentum in RSI itself.
# Higher positive change indicates strengthening momentum.
rsi_avg = rsi.rolling(5).mean()
factor_rsi_momentum = rsi_avg.diff(5).shift(1)

# Factor 3: Institutional Flow (Foreign Investor Strength)
# Higher foreign investor strength indicates institutional buying interest.
factor_foreign_flow = foreign_strength.shift(1)

# 3. Combine factors
# Rank factors to normalize them before combining
factor_rev_rank = factor_rev_growth.rank(axis=1, pct=True)
factor_rsi_rank = factor_rsi_momentum.rank(axis=1, pct=True)
factor_foreign_rank = factor_foreign_flow.rank(axis=1, pct=True)

# Combine factors with weighted average
# Giving more weight to fundamental growth, then institutional flow, then technical momentum
combined_factor = (factor_rev_rank * 0.45 + factor_foreign_rank * 0.35 + factor_rsi_rank * 0.20)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be above 20 million TWD
avg_trading_value = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value > 20_000_000

# Price filter: Stock price must be above 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20

# Combine all filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters and select the top 8 stocks based on the combined factor
position = combined_factor[final_filter].is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)