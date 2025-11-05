# 1. Load data
close = data.get('price:收盤價') # Loaded for completeness, though not directly used in position logic
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
rsi = data.indicator('RSI')
foreign_strength = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')

# 2. Calculate factors and filters (all shifted by 1 to avoid look-ahead bias)

# Liquidity Filter: Average daily trading value over 20 days must be greater than 50 million TWD
# This ensures we only consider sufficiently liquid stocks.
liquidity_filter = (trading_value.rolling(20).mean().shift(1) > 50_000_000)

# Fundamental Filter: Monthly Revenue YoY growth must be positive and strong (e.g., > 10%)
# This identifies companies with growing top-line performance.
revenue_growth_filter = (revenue_yoy.shift(1) > 10)

# Technical Filter: RSI in a neutral to slightly oversold range (30-70)
# This avoids buying extremely overbought stocks and allows for some momentum.
rsi_filter = (rsi.shift(1).between(30, 70))

# Institutional Filter: Foreign investor buying strength must be positive (net buying)
# This indicates institutional interest and potential upward pressure.
foreign_strength_filter = (foreign_strength.shift(1) > 0)

# 3. Combine all filters
# Stocks must pass all criteria to be considered for selection.
combined_filter = liquidity_filter & revenue_growth_filter & rsi_filter & foreign_strength_filter

# 4. Select stocks
# Among the stocks that pass all combined filters, we select the top 8
# based on their Monthly Revenue YoY growth. This prioritizes growth within the filtered set.
filtered_revenue_yoy = revenue_yoy.shift(1)[combined_filter]
position = filtered_revenue_yoy.is_largest(8)

# 5. Run backtest
# The strategy is rebalanced quarterly (resample="Q") with a 8% stop-loss.
report = sim(position, resample="Q", upload=False, stop_loss=0.08)