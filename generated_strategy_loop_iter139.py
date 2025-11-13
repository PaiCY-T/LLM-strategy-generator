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
momentum_60d = close.pct_change(60).shift(1)
# Factor 2: Quality (4-quarter average ROE)
roe_smoothed = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
revenue_growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Buying Pressure (20-day sum of Foreign Net Buy)
foreign_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: Value (Inverse P/E Ratio)
# Handle potential division by zero or negative P/E by filtering later.
# For now, calculate inverse, then shift and ffill.
inverse_pe = (1 / pe_ratio.ffill()).shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum_60d.rank(axis=1, pct=True)
roe_rank = roe_smoothed.rank(axis=1, pct=True)
revenue_rank = revenue_growth.rank(axis=1, pct=True)
foreign_flow_rank = foreign_flow.rank(axis=1, pct=True)
inverse_pe_rank = inverse_pe.rank(axis=1, pct=True)
# Combine with weights (summing to 1.0)
# Weights: Momentum (0.25), Quality (ROE 0.20), Growth (Revenue 0.15), Institutional Flow (0.25), Value (0.15)
combined_factor = (momentum_rank * 0.25 +
                   roe_rank * 0.20 +
                   revenue_rank * 0.15 +
                   foreign_flow_rank * 0.25 +
                   inverse_pe_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 75M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 75_000_000
# Price filter: Close price > 20 TWD (avoid penny stocks)
price_filter = close.shift(1) > 20
# RSI filter: RSI between 30 and 70 (avoiding extreme overbought/oversold conditions)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# P/E Ratio filter: P/E between 5 and 30 (avoiding extremely cheap/expensive or loss-making companies)
pe_filter = (pe_ratio.ffill().shift(1) > 5) & (pe_ratio.ffill().shift(1) < 30)
# Apply all filters to the combined factor
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter & pe_filter]
# 5. Select stocks
# Select top 15 stocks based on the filtered combined factor score
position = filtered_factor.is_largest(15)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)