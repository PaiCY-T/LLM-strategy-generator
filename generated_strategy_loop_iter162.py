# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
pe_ratio = data.get('price_earning_ratio:本益比')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Medium-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality & Growth (Smoothed ROE and Monthly Revenue YoY)
# ROE is quarterly, so ffill and then smooth over 4 quarters
smoothed_roe = roe.ffill().rolling(4).mean().shift(1)
# Revenue YoY is monthly, so ffill
revenue_growth = revenue_yoy.ffill().shift(1)
# Combine ROE and Revenue Growth for a Quality-Growth factor
quality_growth = (smoothed_roe * 0.6 + revenue_growth * 0.4)
# Factor 3: Value (Inverse P/E Ratio)
# A higher inverse P/E means a lower P/E, indicating better value.
inverse_pe = (1 / pe_ratio).shift(1)
# Factor 4: Institutional Flow (20-day cumulative Foreign Net Buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_growth_rank = quality_growth.rank(axis=1, pct=True)
inverse_pe_rank = inverse_pe.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
# Combine with weights summing to 1.0
combined_factor = (momentum_rank * 0.30 +
                   quality_growth_rank * 0.30 +
                   inverse_pe_rank * 0.20 +
                   institutional_flow_rank * 0.20)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Close price > 15 TWD
price_filter = close.shift(1) > 15
# P/E Ratio filter: P/E < 30 (avoid extremely overvalued stocks)
pe_filter = pe_ratio.shift(1) < 30
# RSI filter: RSI between 30 and 70 (avoid extreme overbought/oversold conditions)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Combine all filters
all_filters = liquidity_filter & price_filter & pe_filter & rsi_filter
filtered_factor = combined_factor[all_filters]
# 5. Select stocks
# Select top 10 stocks based on the filtered combined factor
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)