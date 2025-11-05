# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality & Growth (Combined ROE and Monthly Revenue YoY)
# ROE (4-quarter average, forward-filled)
roe_4q_avg = roe.rolling(4).mean().ffill().shift(1)
# Monthly Revenue YoY (forward-filled)
revenue_growth = revenue_yoy.ffill().shift(1)
# Combine ROE and Revenue Growth (simple average for now, will normalize later)
quality_growth = (roe_4q_avg + revenue_growth) / 2
# Factor 3: Institutional Flow (20-day sum of Foreign Net Buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 4: Value (Inverse P/E Ratio, forward-filled)
# Add a small epsilon to avoid division by zero if P/E is 0
value_factor = (1 / (pe_ratio.ffill().shift(1) + 0.001))
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_growth_rank = quality_growth.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
# Combine with weights
combined_factor = (momentum_rank * 0.30 +
                   quality_growth_rank * 0.30 +
                   flow_rank * 0.25 +
                   value_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Close price > 20 TWD
price_filter = close.shift(1) > 20
# RSI filter: Avoid overbought/oversold conditions (30 < RSI < 70)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# P/E Ratio filter: Avoid extremely low P/E ratios (potential distress)
pe_filter = pe_ratio.ffill().shift(1) > 5
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter & pe_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)