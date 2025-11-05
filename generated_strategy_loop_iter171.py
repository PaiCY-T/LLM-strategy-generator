# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
pe_ratio = data.get('price_earning_ratio:本益比')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Medium-term Price Momentum (60-day returns)
momentum_factor = close.pct_change(60).shift(1)
# Factor 2: Quality (4-quarter smoothed ROE)
# ROE is quarterly, so ffill then shift
quality_factor = roe.ffill().rolling(4).mean().shift(1)
# Factor 3: Value (Inverse P/E Ratio)
# P/E is usually quarterly/monthly, ffill then shift
value_factor = (1 / pe_ratio).ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of Foreign Net Buy)
# Foreign net buy is daily, so just rolling sum then shift
institutional_flow_factor = foreign_net_buy.rolling(20).sum().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum_factor.rank(axis=1, pct=True)
quality_rank = quality_factor.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow_factor.rank(axis=1, pct=True)
# Combine with weights
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.30 +
                   value_rank * 0.20 +
                   institutional_flow_rank * 0.20)
# 4. Apply filters
# Mandatory Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Mandatory Price filter: Close price > 15 TWD
price_filter = close.shift(1) > 15
# Optional RSI filter: Avoid extreme overbought/oversold conditions
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter]
# 5. Select stocks
# Select top 10 stocks based on the filtered combined factor
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)