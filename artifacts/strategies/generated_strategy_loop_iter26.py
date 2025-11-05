# 1. Load data
close = data.get('price:收盤價')
pe_ratio = data.get('price_earning_ratio:本益比')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
three_forces = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
trading_value = data.get('price:成交金額')

# 2. Calculate factors
# Momentum: 20-day percentage change
momentum = close.pct_change(20).shift(1)

# Value: Inverse of P/E ratio.
# Cap P/E at 50 to avoid extremely high P/E stocks.
# Replace non-positive P/E with a large number (e.g., 1000) before inverting,
# so they receive a low rank (undesirable).
pe_capped = pe_ratio.where(pe_ratio > 0, 1000).clip(upper=50)
value_factor = (1 / pe_capped).shift(1)

# Growth: Monthly Revenue YoY growth
growth_factor = revenue_yoy.shift(1)

# Institutional Flow: 5-day average of three main forces net buy/sell
flow_factor = three_forces.rolling(5).mean().shift(1)

# 3. Rank factors
# Higher momentum is better
rank_momentum = momentum.rank(axis=1, ascending=True)
# Higher inverse P/E (lower P/E) is better
rank_value = value_factor.rank(axis=1, ascending=True)
# Higher growth is better
rank_growth = growth_factor.rank(axis=1, ascending=True)
# Higher net flow is better
rank_flow = flow_factor.rank(axis=1, ascending=True)

# Combine ranks with equal weighting
combined_rank = rank_momentum + rank_value + rank_growth + rank_flow

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50 million TWD
avg_trading_value = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value > 50_000_000

# Price filter: Stock price > 10 TWD
price_filter = close.shift(1) > 10

# P/E filter: P/E ratio between 5 and 50 (inclusive)
pe_valid_filter = (pe_ratio.shift(1) >= 5) & (pe_ratio.shift(1) <= 50)

# Combine all filters
final_filter = liquidity_filter & price_filter & pe_valid_filter

# 5. Select stocks
# Select 8 stocks with the highest combined rank after applying filters
position = combined_rank[final_filter].is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)