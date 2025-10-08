# 1. Load data
close = data.get('price:收盤價')
pe_ratio = data.get('price_earning_ratio:本益比')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_flow = data.get('foreign_main_force_buy_sell_summary')
trading_value = data.get('price:成交金額')

# 2. Calculate factors
# Momentum factor: 60-day percentage change in close price
momentum = close.pct_change(60).shift(1)

# P/E Ratio factor: Inverse P/E, where lower P/E is generally better for value.
# We use negative P/E and rank it, so lower P/E values get higher ranks.
pe_factor = (-pe_ratio).shift(1)

# Revenue Growth factor: Monthly Revenue YoY growth
revenue_factor = revenue_yoy.shift(1)

# Foreign Investor Net Buy factor: Sum of net buy volume over the past 20 trading days
foreign_flow_factor = foreign_flow.rolling(20).sum().shift(1)

# 3. Apply filters (liquidity filter)
# Calculate the average trading value over the past 20 days
avg_trading_value_20d = trading_value.rolling(20).mean().shift(1)
# Filter for stocks with average daily trading value greater than 10 million TWD
liquidity_filter = avg_trading_value_20d > 10_000_000

# 4. Combine factors
# Rank each factor across all stocks for each day to normalize them
rank_momentum = momentum.rank(axis=1, pct=True)
rank_pe = pe_factor.rank(axis=1, pct=True)
rank_revenue = revenue_factor.rank(axis=1, pct=True)
rank_foreign_flow = foreign_flow_factor.rank(axis=1, pct=True)

# Combine the ranked factors into a single composite score. Higher score indicates a stronger buy signal.
combined_score = rank_momentum + rank_pe + rank_revenue + rank_foreign_flow

# 5. Select stocks
# Apply the liquidity filter and then select the top 10 stocks based on the combined score
position = combined_score[liquidity_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)