# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Long-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality & Growth (ROE and Monthly Revenue YoY)
# ROE: 4-quarter average, forward-filled
quality_roe = roe.rolling(4).mean().ffill().shift(1)
# Revenue Growth: forward-filled
growth_revenue = revenue_yoy.ffill().shift(1)
# Combine quality and growth (simple average for now, will normalize later)
quality_growth = (quality_roe + growth_revenue) / 2
# Factor 3: Institutional Buying Pressure (20-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 4: Value (Inverse P/E Ratio)
value_factor = (1 / pe_ratio).ffill().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_growth_rank = quality_growth.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
# Combine with weights
combined_factor = (momentum_rank * 0.30 +
                   quality_growth_rank * 0.30 +
                   institutional_flow_rank * 0.25 +
                   value_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Close price > 20 TWD
price_filter = close.shift(1) > 20
# P/E Ratio filter: P/E between 5 and 30 (avoiding negative P/E and extremely high P/E)
pe_filter = (pe_ratio.ffill().shift(1) > 5) & (pe_ratio.ffill().shift(1) < 30)
# RSI filter: RSI between 30 and 70 (avoiding overbought/oversold conditions)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & pe_filter & rsi_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)