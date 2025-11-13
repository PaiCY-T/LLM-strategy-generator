# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
market_value = data.get('etl:market_value')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Medium-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE 4-quarter average)
# ROE is quarterly, need to ffill to daily frequency
quality = roe.ffill().rolling(4).mean().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
# Revenue YoY is monthly, need to ffill to daily frequency
growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of foreign net buying)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: Value (Inverse P/E Ratio)
# Cap P/E at 50 to avoid extreme values, and ensure it's positive.
# A lower P/E is better for value, so we want to rank (1/PE) higher.
pe_capped = pe_ratio.clip(lower=1, upper=50).shift(1)
value_factor = 1 / pe_capped
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
growth_rank = growth.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
# Combine Quality and Growth into a single factor for simplicity
quality_growth_combined_rank = (quality_rank * 0.6 + growth_rank * 0.4)
# Combined factor with weights
combined_factor = (momentum_rank * 0.30 +
                   quality_growth_combined_rank * 0.30 +
                   flow_rank * 0.25 +
                   value_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Close price > 20 TWD
price_filter = close.shift(1) > 20
# Market Cap filter: Market value > 10 Billion TWD
market_cap_filter = market_value.shift(1) > 10_000_000_000
# RSI filter: RSI between 30 and 70 (avoid extreme overbought/oversold conditions)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters
all_filters = liquidity_filter & price_filter & market_cap_filter & rsi_filter
filtered_factor = combined_factor[all_filters]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)