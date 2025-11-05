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
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
roe_smoothed = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
revenue_growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of Foreign Net Buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: Value (Inverse P/E Ratio)
inverse_pe = (1 / pe_ratio).ffill().shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks
momentum_rank = momentum.rank(axis=1, pct=True)
roe_rank = roe_smoothed.rank(axis=1, pct=True)
revenue_rank = revenue_growth.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
inverse_pe_rank = inverse_pe.rank(axis=1, pct=True)
# Combine fundamental factors (ROE and Revenue Growth) into a single score
fundamental_strength_rank = (roe_rank * 0.6 + revenue_rank * 0.4)
# Combine all normalized factors with weights summing to 1.0
combined_factor = (momentum_rank * 0.30 +
                   fundamental_strength_rank * 0.30 +
                   flow_rank * 0.25 +
                   inverse_pe_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Close price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20
# RSI filter: Avoid extreme overbought/oversold conditions (RSI between 30 and 70)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# P/E Ratio filter: P/E must be positive and not excessively high (e.g., 5 to 30)
# This helps filter out companies with losses (negative P/E) or extremely speculative valuations.
pe_filter = (pe_ratio.ffill().shift(1) > 5) & (pe_ratio.ffill().shift(1) < 30)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter & pe_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)