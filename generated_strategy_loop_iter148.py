# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Long-term Price Momentum (60-day returns)
momentum_factor = close.pct_change(60).shift(1)
# Factor 2: Quality (4-quarter average ROE)
# ROE is quarterly, so ffill to daily and take 4-quarter rolling average
quality_roe = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
# Monthly revenue, so ffill to daily
growth_revenue = revenue_yoy.ffill().shift(1)
# Factor 4: Value (Inverse P/E Ratio)
# P/E is daily, but can have NaNs, ffill and inverse
value_factor = (1 / pe_ratio).ffill().shift(1)
# Factor 5: Institutional Flow (20-day sum of Foreign Net Buy)
institutional_flow_factor = foreign_net_buy.rolling(20).sum().shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1] for each day
momentum_rank = momentum_factor.rank(axis=1, pct=True)
quality_roe_rank = quality_roe.rank(axis=1, pct=True)
growth_revenue_rank = growth_revenue.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow_factor.rank(axis=1, pct=True)
# Combine all normalized factors with meaningful weights
# Emphasize momentum, quality, and institutional flow, with a touch of value
combined_factor = (momentum_rank * 0.30 +
                   quality_roe_rank * 0.25 +
                   growth_revenue_rank * 0.20 +
                   value_rank * 0.10 +
                   institutional_flow_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD (avoid penny stocks)
price_filter = close.shift(1) > 20
# RSI filter: RSI between 30 and 70 (avoiding extreme overbought/oversold conditions)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters to the combined factor
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter]
# 5. Select stocks
# Select the top 10 stocks based on the filtered combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)