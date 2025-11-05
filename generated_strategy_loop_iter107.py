# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
market_cap = data.get('etl:market_value')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
# ROE is quarterly, so ffill and then apply rolling mean
quality = roe.ffill().rolling(4).mean().shift(1)
# Factor 3: Institutional Flow (20-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 4: Value (Inverse of P/E Ratio)
# Handle potential zero or negative PE ratios by replacing with NaN before inverse
pe_ratio_filtered = pe_ratio.replace([0, -float('inf'), float('inf')], float('nan'))
value_factor = (1 / pe_ratio_filtered).ffill().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
# Combine with weights summing to 1.0
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.25 +
                   flow_rank * 0.25 +
                   value_rank * 0.20)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Close price > 15 TWD
price_filter = close.shift(1) > 15
# Market Cap filter: Market capitalization > 5 Billion TWD
market_cap_filter = market_cap.shift(1) > 5_000_000_000
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter]
# 5. Select stocks (top 10)
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)