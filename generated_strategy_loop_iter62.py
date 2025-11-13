# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
# 2. Calculate factors
# Factor 1: Long-term Price Momentum (60-day returns)
momentum_factor = close.pct_change(60).shift(1)
# Factor 2: Quality (4-quarter average ROE)
# Use .ffill() for quarterly data to align to daily frequency
roe_factor = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
# Use .ffill() for monthly data to align to daily frequency
revenue_growth_factor = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of Foreign Net Buy)
foreign_flow_factor = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: Value (Inverse P/E Ratio)
# Use .ffill() for fundamental data to align to daily frequency
value_factor = (1 / pe_ratio).ffill().shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
momentum_rank = momentum_factor.rank(axis=1, pct=True)
roe_rank = roe_factor.rank(axis=1, pct=True)
revenue_rank = revenue_growth_factor.rank(axis=1, pct=True)
foreign_flow_rank = foreign_flow_factor.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
# Combine with meaningful weights
combined_factor = (momentum_rank * 0.25 +
                   roe_rank * 0.20 +
                   revenue_rank * 0.20 +
                   foreign_flow_rank * 0.20 +
                   value_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20
# Valuation filter: P/E Ratio < 25 to avoid extremely overvalued stocks
pe_filter = pe_ratio.ffill().shift(1) < 25
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & pe_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)