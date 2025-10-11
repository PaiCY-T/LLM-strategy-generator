# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
volume = data.get('price:成交股數')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
pe_ratio = data.get('price_earning_ratio:本益比')

# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)

# Factor 2: Quality (ROE, 4-quarter average)
# Use .ffill() for quarterly data
quality = roe.ffill().rolling(4).mean().shift(1)

# Factor 3: Revenue Growth (monthly YoY, 3-month average)
# Use .ffill() for monthly data
revenue_growth = revenue_yoy.ffill().rolling(3).mean().shift(1)

# Factor 4: Institutional Buying Strength (20-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)

# Factor 5: Value (Inverse of P/E ratio)
# Cap P/E ratio to avoid extreme values and take inverse for value factor
value_factor = (1 / pe_ratio.mask(pe_ratio <= 0)).shift(1)

# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
revenue_growth_rank = revenue_growth.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)

# Combine with weights
combined_factor = (momentum_rank * 0.30 +
                   quality_rank * 0.25 +
                   revenue_growth_rank * 0.20 +
                   institutional_flow_rank * 0.15 +
                   value_rank * 0.10)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Close price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20

# RSI filter: RSI between 30 and 70 to avoid extreme overbought/oversold conditions
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)

# P/E Ratio filter: P/E ratio less than 30 for reasonable valuation
pe_filter = pe_ratio.shift(1) < 30

# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter & pe_filter]

# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)