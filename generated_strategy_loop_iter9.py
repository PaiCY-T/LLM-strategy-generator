# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_flow = data.get('foreign_main_force_buy_sell_summary')

# 2. Calculate factors
# Momentum factor: 20-day percentage change in close price
returns_20d = close.pct_change(20)
momentum_factor = returns_20d.shift(1)

# Revenue Growth factor: Monthly Revenue Year-over-Year growth
# This data is typically released monthly, shift(1) ensures using the last available value.
revenue_growth_factor = revenue_yoy.shift(1)

# Foreign Investor Flow factor: 5-day rolling sum of foreign investor net buy/sell
# A positive value indicates net buying by foreign investors.
foreign_flow_smoothed = foreign_flow.rolling(5).sum()
foreign_flow_factor = foreign_flow_smoothed.shift(1)

# 3. Combine factors
# Rank each factor across all stocks for each day, then sum the ranks.
# Higher values are generally better for all these factors.
ranked_momentum = momentum_factor.rank(axis=1, ascending=True)
ranked_revenue_growth = revenue_growth_factor.rank(axis=1, ascending=True)
ranked_foreign_flow = foreign_flow_factor.rank(axis=1, ascending=True)

# Sum the ranks to create a combined score
combined_rank_factor = ranked_momentum + ranked_revenue_growth + ranked_foreign_flow

# 4. Apply filters
# Liquidity filter: Average daily trading value over the past 20 days must exceed 50 million TWD
avg_trading_value = trading_value.rolling(20).mean()
liquidity_filter = (avg_trading_value.shift(1) > 50_000_000)

# 5. Select stocks
# Apply the liquidity filter to the combined factor
filtered_factor = combined_rank_factor[liquidity_filter]

# Select the top 8 stocks with the highest combined rank score
position = filtered_factor.is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)