# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
market_cap = data.get('etl:market_value')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Mid-term Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality & Growth (Combined ROE and Monthly Revenue YoY)
# ROE: Use 4-quarter average, forward-fill, then shift
roe_smoothed = roe.rolling(4, min_periods=1).mean().ffill().shift(1)
# Revenue Growth: Forward-fill, then shift
revenue_growth = revenue_yoy.ffill().shift(1)
# Factor 3: Institutional Buying Strength (20-day sum of foreign net buy)
# Sum foreign net buy over 20 days, then shift
institutional_flow = foreign_net_buy.rolling(20, min_periods=1).sum().shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks
momentum_rank = momentum.rank(axis=1, pct=True)
roe_rank = roe_smoothed.rank(axis=1, pct=True)
revenue_rank = revenue_growth.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
# Combine ROE and Revenue Growth ranks for a 'Fundamental' factor
fundamental_rank = (roe_rank + revenue_rank) / 2
# Combine all normalized factors with weights
# Weights: Momentum (0.35), Fundamental (0.30), Institutional Flow (0.35)
combined_factor = (momentum_rank * 0.35 +
                   fundamental_rank * 0.30 +
                   institutional_flow_rank * 0.35)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20, min_periods=1).mean().shift(1) > 50_000_000
# Price filter: Close price > 15 TWD
price_filter = close.shift(1) > 15
# Market Cap filter: Market value > 5 Billion TWD
market_cap_filter = market_cap.shift(1) > 5_000_000_000
# RSI filter: RSI between 30 and 70 (avoid extreme overbought/oversold)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Combine all filters
all_filters = liquidity_filter & price_filter & market_cap_filter & rsi_filter
# Apply all filters to the combined factor
filtered_factor = combined_factor[all_filters]
# 5. Select stocks
# Select top 12 stocks based on the filtered combined factor score
position = filtered_factor.is_largest(12)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)