# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
market_cap = data.get('etl:market_value') # For market cap filter
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
# Shift by 1 to avoid look-ahead bias
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
# ROE is quarterly, so forward-fill to daily frequency, then smooth, then shift
quality = roe.ffill().rolling(4).mean().shift(1)
# Factor 3: Revenue Growth (monthly data aligned to daily)
# Monthly Revenue YoY is monthly, so forward-fill to daily frequency, then shift
growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of foreign net buy)
# Sum over 20 days, then shift
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1] across all stocks for each day
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
growth_rank = growth.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
# Combine normalized factors with meaningful weights summing to 1.0
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.25 +
                   growth_rank * 0.25 +
                   flow_rank * 0.20)
# 4. Apply filters
# Liquidity filter: Average trading value over 20 days > 70M TWD
# Shift by 1 to avoid look-ahead bias
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD to avoid penny stocks
# Shift by 1 to avoid look-ahead bias
price_filter = close.shift(1) > 20
# Market Cap filter: Market Cap > 5 Billion TWD for larger, more stable companies
# Market cap is typically updated less frequently, so forward-fill, then shift
market_cap_filter = market_cap.ffill().shift(1) > 5_000_000_000
# Apply all filters to the combined factor
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter]
# 5. Select stocks
# Select the top 10 stocks based on the filtered combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
# Backtest with quarterly rebalancing and an 8% stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.08)