# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
market_cap = data.get('etl:market_value')
# 2. Calculate factors
# Factor 1: Long-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality & Growth (Combined ROE and Revenue YoY)
# ROE (4-quarter average, forward-filled to daily frequency)
quality_roe = roe.rolling(4).mean().ffill().shift(1)
# Revenue Growth (forward-filled monthly data to daily frequency)
growth_revenue = revenue_yoy.ffill().shift(1)
# Factor 3: Institutional Flow (20-day sum of foreign net buying)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 4: RSI Strength (Higher RSI indicates stronger momentum, but not overbought)
# We use RSI directly as a strength indicator, assuming values in the mid-range (e.g., 50-70) are desirable.
rsi_strength = rsi.shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
momentum_rank = momentum.rank(axis=1, pct=True)
quality_roe_rank = quality_roe.rank(axis=1, pct=True)
growth_revenue_rank = growth_revenue.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
rsi_strength_rank = rsi_strength.rank(axis=1, pct=True)
# Combine Quality and Growth into a single fundamental factor rank
fundamental_rank = (quality_roe_rank * 0.6 + growth_revenue_rank * 0.4)
# Combine all normalized factors with meaningful weights
# Weights: Momentum (0.3), Fundamental (0.3), Institutional Flow (0.25), RSI Strength (0.15)
combined_factor = (momentum_rank * 0.30 +
                   fundamental_rank * 0.30 +
                   institutional_flow_rank * 0.25 +
                   rsi_strength_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Close price > 15 TWD to avoid penny stocks
price_filter = close.shift(1) > 15
# Market Cap filter: Market value > 10 Billion TWD to focus on mid-large caps
market_cap_filter = market_cap.shift(1) > 10_000_000_000
# RSI range filter: Avoid extremely overbought (>70) or oversold (<30) stocks
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters
all_filters = liquidity_filter & price_filter & market_cap_filter & rsi_filter
filtered_factor = combined_factor[all_filters]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)