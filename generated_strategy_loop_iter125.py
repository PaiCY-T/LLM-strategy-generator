# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
market_cap = data.get('etl:market_value')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum_60d = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE, 4-quarter average)
quality_roe = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
growth_revenue = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (Foreign Net Buy, 20-day sum)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: Value (Inverse P/E Ratio)
value_pe = (1 / pe_ratio).ffill().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum_60d.rank(axis=1, pct=True)
quality_rank = quality_roe.rank(axis=1, pct=True)
growth_rank = growth_revenue.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
value_rank = value_pe.rank(axis=1, pct=True)
# Combine with weighted average
combined_factor = (momentum_rank * 0.25 +
                   quality_rank * 0.20 +
                   growth_rank * 0.20 +
                   flow_rank * 0.20 +
                   value_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD
price_filter = close.shift(1) > 20
# Market Cap filter: Market capitalization > 10 Billion TWD
market_cap_filter = market_cap.shift(1) > 10_000_000_000
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter]
# 5. Select stocks
# Select top 15 stocks based on the combined factor score
position = filtered_factor.is_largest(15)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)