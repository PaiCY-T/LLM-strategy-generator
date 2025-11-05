# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
quality = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY, forward-filled)
growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: Value (P/E Ratio, lower is better)
value_factor = pe_ratio.ffill().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
growth_rank = growth.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True, ascending=False) # Lower P/E gets higher rank
combined_factor = (momentum_rank * 0.25 +
                   quality_rank * 0.25 +
                   growth_rank * 0.20 +
                   flow_rank * 0.20 +
                   value_rank * 0.10)
# 4. Apply filters
# Liquidity filter: Average daily trading value > 75M TWD over 20 days
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 75_000_000
# Price filter: Stock price > 20 TWD
price_filter = close.shift(1) > 20
# P/E Ratio filter: P/E between 0 and 40 (avoid negative or excessively high P/E)
pe_filter = (pe_ratio.ffill().shift(1) > 0) & (pe_ratio.ffill().shift(1) < 40)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & pe_filter]
# 5. Select stocks (top 15)
position = filtered_factor.is_largest(15)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)