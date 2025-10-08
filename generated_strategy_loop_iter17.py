# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
pe_ratio = data.get('price_earning_ratio:本益比')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('foreign_main_force_buy_sell_summary')

# 2. Calculate factors
# All factors are shifted by 1 to avoid look-ahead bias.

# Factor 1: Value (Inverse P/E Rank)
# Clip P/E ratio to focus on reasonable positive values for ranking stability.
# Lower P/E is better, so rank ascending.
pe_ratio_shifted = pe_ratio.shift(1)
pe_ratio_capped = pe_ratio_shifted.clip(lower=1, upper=50)
pe_rank = pe_ratio_capped.rank(axis=1, ascending=True)

# Factor 2: Growth (Revenue YoY Rank)
# Clip revenue YoY to handle extreme outliers.
# Higher revenue growth is better, so rank descending.
revenue_yoy_shifted = revenue_yoy.shift(1)
revenue_yoy_capped = revenue_yoy_shifted.clip(lower=-50, upper=100)
revenue_rank = revenue_yoy_capped.rank(axis=1, ascending=False)

# Factor 3: Institutional Flow (Foreign Investor Net Buy Rank)
# Smooth out daily foreign net buy with a 5-day rolling mean.
# Higher net buy is better, so rank descending.
foreign_flow_raw = foreign_net_buy.shift(1)
foreign_flow_smoothed = foreign_flow_raw.rolling(5).mean()
foreign_flow_rank = foreign_flow_smoothed.rank(axis=1, ascending=False)

# 3. Combine factors
# Sum the ranks. A lower combined rank indicates better value, better growth, and stronger foreign buying.
combined_rank = pe_rank + revenue_rank + foreign_flow_rank

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be above 50 million TWD.
avg_trading_value = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value > 50_000_000

# 5. Select stocks
# Apply the liquidity filter to the combined rank and select the 10 stocks with the lowest combined rank.
# We select 10 stocks, which is within the 6-12 stock range.
position = combined_rank[liquidity_filter].is_smallest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)