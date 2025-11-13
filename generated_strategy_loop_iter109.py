# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
market_cap = data.get('etl:market_value')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Medium-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
# ROE is quarterly, so ffill to daily and then smooth
quality = roe.ffill().rolling(4).mean().shift(1)
# Factor 3: Growth (Monthly Revenue YoY, forward-filled)
revenue_growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: RSI Reversal (low RSI indicates oversold, potential bounce)
# We want to buy stocks with relatively low RSI, so rank it inversely
rsi_factor = (100 - rsi).shift(1) # Lower RSI means higher score after inversion
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
revenue_rank = revenue_growth.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
rsi_rank = rsi_factor.rank(axis=1, pct=True)
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.20 +
                   revenue_rank * 0.20 +
                   flow_rank * 0.15 +
                   rsi_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Close price > 15 TWD
price_filter = close.shift(1) > 15
# Market Cap filter: Market value > 10 Billion TWD (focus on mid-large caps)
market_cap_filter = market_cap.shift(1) > 10_000_000_000
# RSI range filter: Avoid extremely overbought/oversold conditions (RSI between 30 and 70)
rsi_range_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & rsi_range_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)