# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
market_value = data.get('etl:market_value')
# 2. Calculate factors
# Factor 1: Long-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
# ROE is quarterly, so ffill and then smooth
quality = roe.ffill().rolling(4).mean().shift(1)
# Factor 3: Institutional Buying Pressure (20-day sum of foreign net buys)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 4: RSI Reversal/Value (inverted RSI rank to favor oversold/less overbought)
# Lower RSI values will get higher scores after inversion
rsi_factor = rsi.shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
# Invert RSI rank: 1 - rank gives higher scores to lower RSI values
rsi_inverted_rank = 1 - rsi_factor.rank(axis=1, pct=True)
# Combine with intelligent weights
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.30 +
                   flow_rank * 0.25 +
                   rsi_inverted_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Stock price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20
# Market Cap filter: Market value > 10 Billion TWD for mid-large caps
market_cap_filter = market_value.ffill().shift(1) > 10_000_000_000
# RSI filter: Avoid extremely overbought stocks (RSI < 75)
rsi_overbought_filter = rsi.shift(1) < 75
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & rsi_overbought_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)