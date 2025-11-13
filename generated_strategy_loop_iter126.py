# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI') # Technical indicator
# 2. Calculate factors
# Factor 1: Medium-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality & Growth (Smoothed ROE + Monthly Revenue YoY)
# ROE is quarterly, so smooth over 4 quarters and ffill to daily frequency
smoothed_roe = roe.rolling(4).mean().ffill().shift(1)
# Revenue YoY is monthly, so ffill to daily frequency
revenue_growth = revenue_yoy.ffill().shift(1)
# Combine ROE and Revenue Growth for a Quality/Growth factor
quality_growth = (smoothed_roe + revenue_growth) / 2 # Simple average
# Factor 3: Institutional Flow (10-day sum of Foreign Net Buy)
institutional_flow = foreign_net_buy.rolling(10).sum().shift(1)
# Factor 4: RSI Reversal (Lower RSI indicates oversold, potential bounce)
# Shift RSI to avoid look-ahead bias
rsi_shifted = rsi.shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_growth_rank = quality_growth.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
# For RSI, lower value is better for reversal, so we invert the rank
rsi_reversal_rank = 1 - rsi_shifted.rank(axis=1, pct=True)
# Combine with weights
combined_factor = (momentum_rank * 0.30 +
                   quality_growth_rank * 0.30 +
                   flow_rank * 0.25 +
                   rsi_reversal_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD
price_filter = close.shift(1) > 20
# RSI range filter: Avoid extreme overbought/oversold conditions (RSI between 20 and 80)
rsi_filter = (rsi_shifted > 20) & (rsi_shifted < 80)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)