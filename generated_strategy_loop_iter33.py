# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
market_cap = data.get('etl:market_value')
# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
# ROE is quarterly, so forward-fill then shift
quality_roe = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
# Monthly revenue, so forward-fill then shift
growth_revenue = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of Foreign Net Buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: Value (Inverse of P/E Ratio)
# P/E can have NaNs, forward-fill then shift
value_pe = (1 / pe_ratio).ffill().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_roe_rank = quality_roe.rank(axis=1, pct=True)
growth_revenue_rank = growth_revenue.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
value_pe_rank = value_pe.rank(axis=1, pct=True)
# Combine quality and growth into a single factor for weighting
quality_growth_rank = (quality_roe_rank * 0.5 + growth_revenue_rank * 0.5)
# Combined factor with weights
# Momentum: 0.3
# Quality/Growth: 0.3
# Institutional Flow: 0.25
# Value: 0.15
combined_factor = (momentum_rank * 0.3 +
                   quality_growth_rank * 0.3 +
                   institutional_flow_rank * 0.25 +
                   value_pe_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Close price > 20 TWD (avoid penny stocks)
price_filter = close.shift(1) > 20
# Market Cap filter: Market Cap > 10 Billion TWD (focus on mid-large caps)
market_cap_filter = market_cap.ffill().shift(1) > 10_000_000_000
# P/E Ratio filter: P/E < 30 (avoid extremely overvalued stocks, but allow growth)
pe_filter = pe_ratio.ffill().shift(1) < 30
# Combine all filters
all_filters = liquidity_filter & price_filter & market_cap_filter & pe_filter
filtered_factor = combined_factor[all_filters]
# 5. Select stocks
position = filtered_factor.is_largest(10) # Select top 10 stocks
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)