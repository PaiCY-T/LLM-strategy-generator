# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Long-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (Smoothed ROE)
# Use 4-quarter average ROE, forward-fill to daily, then shift
quality_roe = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
# Forward-fill monthly data to daily, then shift
growth_revenue = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Buying Pressure (20-day sum of Foreign Net Buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_roe_rank = quality_roe.rank(axis=1, pct=True)
growth_revenue_rank = growth_revenue.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
# Combine with intelligent weights
# Momentum (0.35), Quality (0.25), Growth (0.25), Institutional Flow (0.15)
combined_factor = (momentum_rank * 0.35 +
                   quality_roe_rank * 0.25 +
                   growth_revenue_rank * 0.25 +
                   institutional_flow_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 75M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 75_000_000
# Price filter: Close price > 20 TWD
price_filter = close.shift(1) > 20
# RSI filter: Avoid extreme overbought/oversold conditions (RSI between 30 and 70)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter]
# 5. Select stocks
# Select top 12 stocks based on the combined factor score
position = filtered_factor.is_largest(12)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)