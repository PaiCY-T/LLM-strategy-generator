# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Long-term Momentum (60-day returns)
momentum_60d = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
roe_smoothed = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY, forward-filled)
revenue_growth_ffill = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of Foreign Net Buy)
institutional_flow_20d = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: RSI for potential reversal/avoiding overbought
rsi_factor = rsi.shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum_60d.rank(axis=1, pct=True)
roe_rank = roe_smoothed.rank(axis=1, pct=True)
revenue_growth_rank = revenue_growth_ffill.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow_20d.rank(axis=1, pct=True)
# For RSI, we want lower values (e.g., oversold) to rank higher for a potential bounce.
# So, we take (1 - rank) to invert the percentile ranking.
rsi_inverse_rank = (1 - rsi_factor.rank(axis=1, pct=True))
# Combine with meaningful weights
# Weights: Momentum (0.3), Quality (0.25), Growth (0.2), Institutional Flow (0.15), Inverse RSI (0.1)
combined_factor = (momentum_rank * 0.30 +
                   roe_rank * 0.25 +
                   revenue_growth_rank * 0.20 +
                   institutional_flow_rank * 0.15 +
                   rsi_inverse_rank * 0.10)
# 4. Apply filters
# Liquidity filter: Average trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Close price > 20 TWD (avoid penny stocks)
price_filter = close.shift(1) > 20
# RSI range filter: Avoid extremely overbought (>70) or extremely oversold (<30) stocks
# This helps focus on stocks in a healthier trading range, or those just entering oversold.
rsi_range_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_range_filter]
# 5. Select stocks
# Select top 10 stocks based on the filtered combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)