# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_main_force = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')

# 2. Calculate factors

# Factor 1: Momentum (60-day returns)
returns_60d = close.pct_change(60)
# Shift forward to avoid look-ahead bias
factor_momentum = returns_60d.shift(1)

# Factor 2: Growth (Monthly Revenue YoY)
# Monthly data, so shifting by 1 day is sufficient for daily strategy
factor_growth = revenue_yoy.shift(1)

# Factor 3: Institutional Flow (5-day average of foreign investor net buy/sell)
# Smooth out daily noise and shift forward
factor_foreign_flow = foreign_main_force.rolling(5).mean().shift(1)

# 3. Combine factors
# Rank each factor to normalize their scales before combining
ranked_momentum = factor_momentum.rank(axis=1, pct=True)
ranked_growth = factor_growth.rank(axis=1, pct=True)
ranked_foreign_flow = factor_foreign_flow.rank(axis=1, pct=True)

# Combine the ranked factors. Higher values are better.
combined_factor = ranked_momentum + ranked_growth + ranked_foreign_flow

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be greater than 10 million TWD
avg_trading_value = trading_value.rolling(20).mean()
liquidity_filter = (avg_trading_value.shift(1) > 10_000_000)

# 5. Select stocks
# Apply the liquidity filter and then select the top 8 stocks based on the combined factor
position = combined_factor[liquidity_filter].is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)