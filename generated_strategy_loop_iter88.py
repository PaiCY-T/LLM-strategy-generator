# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum_factor = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
# Forward-fill quarterly ROE to daily, then calculate 4-quarter average
quality_factor = roe.ffill().rolling(4).mean().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
# Forward-fill monthly revenue growth to daily
growth_factor = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of foreign net buy)
institutional_flow_factor = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: Value (Inverse P/E Ratio)
# Forward-fill P/E ratio to daily, then calculate inverse
# Handle potential division by zero or negative P/E by replacing inf/-inf with NaN
inverse_pe_factor = (1 / pe_ratio.ffill()).replace([float('inf'), -float('inf')], float('nan')).shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum_factor.rank(axis=1, pct=True)
quality_rank = quality_factor.rank(axis=1, pct=True)
growth_rank = growth_factor.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow_factor.rank(axis=1, pct=True)
inverse_pe_rank = inverse_pe_factor.rank(axis=1, pct=True)
# Combine with meaningful weights
combined_factor = (momentum_rank * 0.25 +
                   quality_rank * 0.25 +
                   growth_rank * 0.20 +
                   institutional_flow_rank * 0.20 +
                   inverse_pe_rank * 0.10)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD
price_filter = close.shift(1) > 20
# P/E Ratio filter: P/E between 5 and 30 (avoiding extremely high/low/negative P/E)
pe_valid_filter = (pe_ratio.ffill().shift(1) > 5) & (pe_ratio.ffill().shift(1) < 30)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & pe_valid_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)