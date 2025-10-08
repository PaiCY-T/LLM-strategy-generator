# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_flow = data.get('foreign_main_force_buy_sell_summary')

# 2. Calculate factors

# Factor 1: Medium-term Momentum (60-day returns)
# Higher returns indicate stronger momentum.
momentum = close.pct_change(60).shift(1)

# Factor 2: Revenue Growth (Monthly YoY)
# Higher YoY growth indicates stronger fundamental growth.
# Finlab handles the alignment of monthly data to daily frequency.
revenue_growth_factor = revenue_yoy.shift(1)

# Factor 3: Foreign Investor Flow Strength (20-day sum of net buy/sell)
# A positive sum indicates accumulation by foreign investors.
foreign_flow_strength = foreign_flow.rolling(20).sum().shift(1)

# Normalize factors by ranking them across all stocks for each day
# This helps in combining factors with different scales.
momentum_rank = momentum.rank(axis=1, pct=True)
revenue_growth_rank = revenue_growth_factor.rank(axis=1, pct=True)
foreign_flow_rank = foreign_flow_strength.rank(axis=1, pct=True)

# 3. Combine factors
# Assign weights to each ranked factor.
# Momentum and Revenue Growth are given higher weights, Foreign Flow a moderate weight.
combined_factor = (momentum_rank * 0.4 +
                   revenue_growth_rank * 0.4 +
                   foreign_flow_rank * 0.2)

# 4. Apply filters

# Liquidity filter: Average daily trading value over the last 20 days must be above 100 million TWD.
# This ensures we only trade sufficiently liquid stocks.
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 100_000_000

# Price filter: Stock price must be above 10 TWD to avoid penny stocks.
price_filter = close.shift(1) > 10

# Combine all filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Select the top 10 stocks based on the combined factor after applying all filters.
# The number of stocks is within the 6-12 range.
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)