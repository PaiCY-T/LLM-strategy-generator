# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
pe_ratio = data.get('price_earning_ratio:本益比')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
market_cap = data.get('etl:market_value')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Fundamental Quality (4-quarter average ROE)
# Use ffill for quarterly data, then shift
quality = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Value (Inverse of P/E Ratio)
# Use ffill for quarterly/monthly data, then shift
value = (1 / pe_ratio).ffill().shift(1)
# Factor 4: Institutional Accumulation (20-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
value_rank = value.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
# Combine with weighted average. Weights sum to 1.0
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.30 +
                   value_rank * 0.20 +
                   flow_rank * 0.20)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 60M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 60_000_000
# Price filter: Close price > 20 TWD
price_filter = close.shift(1) > 20
# Market Cap filter: Market capitalization > 10 Billion TWD (avoid small caps)
market_cap_filter = market_cap.shift(1) > 10_000_000_000
# P/E Ratio filter: P/E between 5 and 30 (avoid extreme values)
pe_filter = (pe_ratio.ffill().shift(1) > 5) & (pe_ratio.ffill().shift(1) < 30)
# Apply all filters
all_filters = liquidity_filter & price_filter & market_cap_filter & pe_filter
filtered_factor = combined_factor[all_filters]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)