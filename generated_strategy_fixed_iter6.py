# 1. Load data
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits
trading_value = data.get('price:成交金額')  # OK for liquidity filter
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)') # Monthly Revenue YoY
roe = data.get('fundamental_features:ROE稅後') # Return on Equity (4Q smoothed)
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)') # Foreign Net Buy
rsi = data.indicator('RSI') # Relative Strength Index
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Revenue Growth (monthly data aligned to daily)
revenue_growth = revenue_yoy.ffill().shift(1)
# Factor 3: Quality (ROE with 4-quarter smoothing)
quality = roe.rolling(4).mean().shift(1)
# Factor 4: Institutional Flow (10-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(10).sum().shift(1)
# Factor 5: RSI (momentum/reversal signal)
rsi_signal = rsi.shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
revenue_rank = revenue_growth.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
rsi_rank = rsi_signal.rank(axis=1, pct=True)
# Assign weights: Momentum (0.3), Revenue (0.2), Quality (0.2), Institutional Flow (0.2), RSI (0.1)
combined_factor = (momentum_rank * 0.3 +
                   revenue_rank * 0.2 +
                   quality_rank * 0.2 +
                   flow_rank * 0.2 +
                   rsi_rank * 0.1)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 40M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 40_000_000
# Price filter: Adjusted close price > 15 TWD
price_filter = close.shift(1) > 15
# RSI filter: Avoid extremely overbought/oversold conditions
rsi_filter = (rsi_signal > 20) & (rsi_signal < 80)
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
# Quarterly rebalancing with an 8% stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.08)