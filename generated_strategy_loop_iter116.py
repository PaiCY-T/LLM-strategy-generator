# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Medium-term Price Momentum (60-day returns)
momentum_factor = close.pct_change(60).shift(1)
# Factor 2: Quality (4-quarter average ROE)
quality_factor = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
growth_factor = revenue_yoy.ffill().shift(1)
# Factor 4: Value (Inverse P/E Ratio)
# Handle division by zero or negative P/E by replacing with NaN, then fill with median or 0 before inverse
inverse_pe_ratio = (1 / pe_ratio).replace([float('inf'), -float('inf')], float('nan')).fillna(0).shift(1)
# Factor 5: Institutional Flow (10-day sum of Foreign Net Buy)
institutional_flow_factor = foreign_net_buy.rolling(10).sum().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum_factor.rank(axis=1, pct=True)
quality_rank = quality_factor.rank(axis=1, pct=True)
growth_rank = growth_factor.rank(axis=1, pct=True)
value_rank = inverse_pe_ratio.rank(axis=1, pct=True)
flow_rank = institutional_flow_factor.rank(axis=1, pct=True)
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.25 +
                   growth_rank * 0.20 +
                   value_rank * 0.15 +
                   flow_rank * 0.10)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD
price_filter = close.shift(1) > 20
# P/E Ratio filter: P/E between 5 and 25 (avoiding extreme value/growth)
pe_filter = (pe_ratio.shift(1) > 5) & (pe_ratio.shift(1) < 25)
# RSI filter: RSI between 35 and 65 (avoiding extreme overbought/oversold, allowing some trend)
rsi_filter = (rsi.shift(1) > 35) & (rsi.shift(1) < 65)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & pe_filter & rsi_filter]
# 5. Select stocks
# Select top 12 stocks based on the combined factor score
position = filtered_factor.is_largest(12)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)