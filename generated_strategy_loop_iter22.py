# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
three_forces = data.get('three_main_forces_buy_sell_summary')
pe_ratio = data.get('price_earning_ratio:本益比')

# 2. Calculate factors
# Factor 1: Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)

# Factor 2: Revenue Growth (YoY growth)
# Use as a filter: positive revenue growth
revenue_growth_signal = (revenue_yoy.shift(1) > 0)

# Factor 3: Institutional Net Buying
# Use as a filter: positive net buying from three main forces
three_forces_signal = (three_forces.shift(1) > 0)

# Factor 4: P/E Ratio (for filtering)
pe_ratio_val = pe_ratio.shift(1)

# 3. Apply filters
# Filter 1: Liquidity filter (average daily trading value > 20M TWD)
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 20_000_000

# Filter 2: P/E Ratio filter (P/E between 5 and 30, exclude negative/zero/NaN)
pe_filter = (pe_ratio_val > 5) & (pe_ratio_val < 30)

# Combine all filters
final_filter = liquidity_filter & pe_filter & revenue_growth_signal & three_forces_signal

# 4. Select stocks
# Select top 8 stocks based on momentum, after applying all filters
position = momentum[final_filter].is_largest(8)

# 5. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)