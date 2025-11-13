# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
market_value = data.get('etl:market_value')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
# Use .ffill() for quarterly data and .shift(1) for look-ahead bias
quality = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Revenue Growth (monthly data aligned to daily)
# Use .ffill() for monthly data and .shift(1) for look-ahead bias
growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Conviction (20-day sum of foreign net buying)
institutional_conviction = foreign_net_buy.rolling(20).sum().shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
growth_rank = growth.rank(axis=1, pct=True)
institutional_conviction_rank = institutional_conviction.rank(axis=1, pct=True)
# Combine with meaningful weights summing to 1.0
combined_factor = (momentum_rank * 0.35 +
                   quality_rank * 0.25 +
                   growth_rank * 0.25 +
                   institutional_conviction_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20
# Market Cap filter: Market value > 10 Billion TWD for mid-large caps
market_cap_filter = market_value.shift(1) > 10_000_000_000
# RSI filter: Avoid extreme overbought/oversold conditions (RSI between 30 and 70)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & rsi_filter]
# 5. Select stocks
# Select top 15 stocks based on the combined factor score
position = filtered_factor.is_largest(15)
# 6. Run backtest
# Backtest with quarterly rebalancing and an 8% stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.08)