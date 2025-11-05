# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE smoothed over 4 quarters)
# ROE is quarterly data, so forward-fill to daily frequency then shift
quality_roe = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
# Monthly data, so forward-fill to daily frequency then shift
growth_revenue = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: Value (Inverse P/E Ratio)
# Handle P/E <= 0 by replacing with a small positive number to avoid division by zero or negative values
value_pe = (1 / pe_ratio.where(pe_ratio > 0, 0.001)).shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
momentum_rank = momentum.rank(axis=1, pct=True)
quality_roe_rank = quality_roe.rank(axis=1, pct=True)
growth_revenue_rank = growth_revenue.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
value_pe_rank = value_pe.rank(axis=1, pct=True)
# Combine factors with meaningful weights (summing to 1.0)
combined_factor = (momentum_rank * 0.25 +
                   quality_roe_rank * 0.20 +
                   growth_revenue_rank * 0.20 +
                   institutional_flow_rank * 0.20 +
                   value_pe_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20
# P/E Ratio filter: P/E between 5 and 25 to focus on reasonably valued growth/quality stocks
pe_filter = (pe_ratio.shift(1) > 5) & (pe_ratio.shift(1) < 25)
# Positive ROE filter: Ensure the company is profitable
roe_positive_filter = roe.ffill().shift(1) > 0
# Apply all filters to the combined factor
filtered_factor = combined_factor[liquidity_filter & price_filter & pe_filter & roe_positive_filter]
# 5. Select stocks
# Select the top 10 stocks with the highest combined factor scores
position = filtered_factor.is_largest(10)
# 6. Run backtest
# Backtest with quarterly rebalancing and an 8% stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.08)