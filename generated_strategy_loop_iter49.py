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
# ROE is quarterly, so ffill then smooth
quality = roe.ffill().rolling(4).mean().shift(1)
# Factor 3: Revenue Growth (monthly data aligned to daily)
revenue_growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (10-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(10).sum().shift(1)
# Factor 5: Value (Inverse P/E Ratio)
# P/E is quarterly, so ffill
value_factor = (1 / pe_ratio).ffill().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
revenue_rank = revenue_growth.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
# Combine with weights summing to 1.0
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.20 +
                   revenue_rank * 0.20 +
                   flow_rank * 0.20 +
                   value_rank * 0.10)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 80M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 80_000_000
# Price filter: Close price > 15 TWD
price_filter = close.shift(1) > 15
# P/E Ratio filter: P/E between 8 and 30 (avoiding extreme value/growth traps)
pe_filter = (pe_ratio.ffill().shift(1) > 8) & (pe_ratio.ffill().shift(1) < 30)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & pe_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)