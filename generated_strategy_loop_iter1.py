# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
volume = data.get('price:成交股數')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')

# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)

# Factor 2: Quality (ROE, 4-quarter average)
# ffill() to align quarterly data to daily, then shift(1)
quality = roe.ffill().rolling(window=4, min_periods=1).mean().shift(1)

# Factor 3: Revenue Growth (Monthly YoY, 3-month average)
# ffill() to align monthly data to daily, then shift(1)
revenue_growth = revenue_yoy.ffill().rolling(window=3, min_periods=1).mean().shift(1)

# Factor 4: Institutional Buying Strength (20-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(window=20, min_periods=1).sum().shift(1)

# Factor 5: RSI Divergence (Simple RSI filter, not a continuous factor)
# This will be used as an additional filter rather than a continuous factor for combination

# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
revenue_growth_rank = revenue_growth.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)

# Combine with weights. Higher weight on momentum and quality.
combined_factor = (momentum_rank * 0.40 +
                   quality_rank * 0.30 +
                   revenue_growth_rank * 0.15 +
                   institutional_flow_rank * 0.15)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50 million TWD
liquidity_filter = trading_value.rolling(window=20, min_periods=1).mean().shift(1) > 50_000_000

# Price filter: Close price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20

# Volume filter: Average daily volume over 20 days > 500,000 shares
volume_filter = volume.rolling(window=20, min_periods=1).mean().shift(1) > 500_000

# RSI filter: RSI not overbought (below 70) and not oversold (above 30)
rsi_filter = (rsi.shift(1) < 70) & (rsi.shift(1) > 30)

# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & volume_filter & rsi_filter]

# 5. Select stocks
# Select top 10 stocks based on the filtered combined factor
position = filtered_factor.is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)