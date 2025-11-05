# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
market_cap = data.get('etl:market_value')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Long-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Fundamental Quality (4-quarter average ROE)
# ROE is quarterly, so forward-fill to daily and then shift
smoothed_roe = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Fundamental Growth (Monthly Revenue YoY)
# Revenue is monthly, so forward-fill to daily and then shift
revenue_growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Buying Pressure (20-day sum of foreign net buy)
inst_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: RSI (as a positive momentum indicator, avoiding extremes)
# We will filter for mid-range RSI later, so higher values within that range are better
rsi_strength = rsi.shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
smoothed_roe_rank = smoothed_roe.rank(axis=1, pct=True)
revenue_growth_rank = revenue_growth.rank(axis=1, pct=True)
inst_flow_rank = inst_flow.rank(axis=1, pct=True)
rsi_strength_rank = rsi_strength.rank(axis=1, pct=True)
# Combine fundamental factors into a single fundamental score
fundamental_score_rank = (smoothed_roe_rank * 0.6 + revenue_growth_rank * 0.4)
# Combine all ranked factors with meaningful weights
combined_factor = (momentum_rank * 0.30 +
                   fundamental_score_rank * 0.30 +
                   inst_flow_rank * 0.25 +
                   rsi_strength_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Close price > 15 TWD (avoid penny stocks)
price_filter = close.shift(1) > 15
# Market Cap filter: Market cap > 10B TWD (focus on mid-large cap)
market_cap_filter = market_cap.ffill().shift(1) > 10_000_000_000
# RSI range filter: RSI between 30 and 70 (avoid extreme overbought/oversold conditions)
rsi_range_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters to the combined factor
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & rsi_range_filter]
# 5. Select stocks
# Select the top 10 stocks based on the filtered combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
# Backtest with quarterly rebalancing and an 8% stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.08)