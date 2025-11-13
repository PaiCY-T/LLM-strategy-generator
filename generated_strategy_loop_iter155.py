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
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (4-quarter smoothed ROE)
quality = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY, forward-filled)
growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (10-day sum of Foreign Net Buy)
institutional_flow = foreign_net_buy.rolling(10).sum().shift(1)
# Factor 5: Value (Inverse of P/E Ratio)
value = (1 / pe_ratio).shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
growth_rank = growth.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
value_rank = value.rank(axis=1, pct=True)
# Combine with meaningful weights
combined_factor = (momentum_rank * 0.25 +
                   quality_rank * 0.20 +
                   growth_rank * 0.20 +
                   institutional_flow_rank * 0.20 +
                   value_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD
price_filter = close.shift(1) > 20
# P/E Ratio filter: Avoid extreme value traps (PE < 5) or excessively overvalued stocks (PE > 30)
pe_filter = (pe_ratio.shift(1) > 5) & (pe_ratio.shift(1) < 30)
# RSI filter: Avoid extreme overbought/oversold conditions (RSI between 35 and 65)
rsi_filter = (rsi.shift(1) > 35) & (rsi.shift(1) < 65)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & pe_filter & rsi_filter]
# 5. Select stocks (top 12 stocks)
position = filtered_factor.is_largest(12)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)