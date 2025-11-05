# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
market_cap = data.get('etl:market_value')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
quality = roe.ffill().rolling(4).mean().shift(1)
# Factor 3: Revenue Growth (monthly data aligned to daily)
revenue_growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (10-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(10).sum().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
revenue_rank = revenue_growth.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.25 +
                   revenue_rank * 0.25 +
                   flow_rank * 0.20)
# 4. Apply filters
# Liquidity filter: Average daily trading value > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Stock price > 20 TWD
price_filter = close.shift(1) > 20
# Market Cap filter: Market capitalization > 10B TWD
market_cap_filter = market_cap.shift(1) > 10_000_000_000
# RSI filter: RSI between 30 and 70 (avoiding extreme overbought/oversold)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & rsi_filter]
# 5. Select stocks (top 10 based on combined factor score)
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)