# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
foreign_strength = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
# ROE is quarterly, so ffill to daily and then smooth
quality = roe.ffill().rolling(4).mean().shift(1)
# Factor 3: Institutional Flow (20-day average of Foreign Buying Strength)
flow = foreign_strength.rolling(20).mean().shift(1)
# Factor 4: Value (Inverse P/E Ratio)
# Add a small epsilon to avoid division by zero if P/E is exactly 0
value = (1 / (pe_ratio + 0.001)).shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
flow_rank = flow.rank(axis=1, pct=True)
value_rank = value.rank(axis=1, pct=True)
# Combine with meaningful weights
combined_factor = (momentum_rank * 0.35 +
                   quality_rank * 0.30 +
                   flow_rank * 0.20 +
                   value_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Close price > 15 TWD
price_filter = close.shift(1) > 15
# RSI filter: Avoid extreme overbought/oversold conditions (RSI between 30 and 70)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# P/E ratio filter: Avoid negative P/E and extremely high P/E (0 < P/E < 30)
pe_filter = (pe_ratio.shift(1) > 0) & (pe_ratio.shift(1) < 30)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter & pe_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)