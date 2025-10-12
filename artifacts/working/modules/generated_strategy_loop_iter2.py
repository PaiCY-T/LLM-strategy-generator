# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
volume = data.get('price:成交股數')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
roe = data.get('fundamental_features:ROE稅後')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
rsi = data.indicator('RSI')

# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)

# Factor 2: Revenue Growth (monthly data aligned to daily, 3-month average)
revenue_growth = revenue_yoy.ffill().rolling(3).mean().shift(1)

# Factor 3: Quality (ROE with 4-quarter smoothing)
quality = roe.ffill().rolling(4).mean().shift(1)

# Factor 4: Institutional Flow (20-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)

# Factor 5: Value (Inverse of P/E ratio, capped to avoid outliers)
# Cap P/E ratio to prevent extremely low values from dominating
pe_capped = pe_ratio.shift(1).clip(upper=30)
value = (1 / pe_capped)

# Factor 6: RSI Reversal (RSI below 30 indicates oversold)
# This factor will be used as a filter or given a small weight
rsi_oversold = (rsi.shift(1) < 30).astype(float)

# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
revenue_rank = revenue_growth.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
value_rank = value.rank(axis=1, pct=True)

# Combine with meaningful weights
combined_factor = (momentum_rank * 0.30 +
                   revenue_rank * 0.20 +
                   quality_rank * 0.20 +
                   flow_rank * 0.15 +
                   value_rank * 0.15)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Close price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20

# P/E ratio filter: P/E between 5 and 25 for reasonable valuation
pe_filter = (pe_ratio.shift(1) > 5) & (pe_ratio.shift(1) < 25)

# Volume filter: Average daily volume over 20 days > 1,000,000 shares
volume_filter = volume.rolling(20).mean().shift(1) > 1_000_000

# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & pe_filter & volume_filter]

# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)