# 1. Load data
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits
trading_value = data.get('price:成交金額')  # OK for liquidity filter
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
roe = data.get('fundamental_features:ROE稅後')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI') # Technical indicator
# 2. Calculate factors
# Factor 1: Price Momentum (30-day returns)
momentum = close.pct_change(30).shift(1)
# Factor 2: Revenue Growth (monthly data aligned to daily)
revenue_growth = revenue_yoy.ffill().shift(1)
# Factor 3: Quality (ROE with 4-quarter smoothing)
quality = roe.rolling(4).mean().shift(1)
# Factor 4: Institutional Flow (10-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(10).sum().shift(1)
# Factor 5: Oversold Indicator (RSI < 40) - inverted for ranking
oversold_indicator = (rsi.shift(1) < 40).astype(int) # Higher value means more oversold
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
revenue_rank = revenue_growth.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
oversold_rank = oversold_indicator.rank(axis=1, pct=True) # Rank the oversold signal
# Assign weights - focus on momentum, quality, and institutional flow, with a boost for oversold conditions
combined_factor = (momentum_rank * 0.30 +
                   revenue_rank * 0.20 +
                   quality_rank * 0.30 +
                   flow_rank * 0.15 +
                   oversold_rank * 0.05) # Small weight for oversold signal
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 40M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 40_000_000
# Price filter: Adjusted close price > 15 TWD
price_filter = close.shift(1) > 15
# RSI filter: Avoid extremely overbought stocks (RSI < 75)
rsi_filter = rsi.shift(1) < 75
# Combine all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)