# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
rsi = data.indicator('RSI')
market_cap = data.get('etl:market_value')
# 2. Calculate factors
# Factor 1: Long-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
# ffill for quarterly data, then rolling mean for smoothing, then shift for look-ahead bias
quality = roe.ffill().rolling(4).mean().shift(1)
# Factor 3: Institutional Flow (10-day sum of foreign net buying)
institutional_flow = foreign_net_buy.rolling(10).sum().shift(1)
# Factor 4: Value (Inverse P/E Ratio)
# ffill for quarterly/monthly data, then inverse, then shift
value_factor = (1 / pe_ratio).ffill().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
# Combine with weights
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.25 +
                   flow_rank * 0.25 +
                   value_rank * 0.20)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20
# RSI filter: Avoid extreme overbought/oversold conditions (30 < RSI < 70)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Market Cap filter: Focus on mid-large cap stocks (> 10 Billion TWD)
market_cap_filter = market_cap.shift(1) > 10_000_000_000
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter & market_cap_filter]
# 5. Select stocks
# Select top 12 stocks based on the combined factor score
position = filtered_factor.is_largest(12)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)