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
# Factor 2: Quality & Value (ROE and Inverse P/E)
# Use 4-quarter average for ROE, forward-fill and shift
quality_roe = roe.rolling(4).mean().ffill().shift(1)
# Inverse P/E for value, forward-fill and shift
value_inv_pe = (1 / pe_ratio).ffill().shift(1)
# Combine quality and value
quality_value_factor = quality_roe * 0.6 + value_inv_pe * 0.4
# Factor 3: Growth (Monthly Revenue YoY)
# Forward-fill monthly data to daily, then shift
growth_revenue = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of Foreign Net Buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_value_rank = quality_value_factor.rank(axis=1, pct=True)
growth_rank = growth_revenue.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
# Combine with meaningful weights
combined_factor = (momentum_rank * 0.30 +
                   quality_value_rank * 0.30 +
                   growth_rank * 0.25 +
                   institutional_flow_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Close price > 20 TWD
price_filter = close.shift(1) > 20
# Market Cap filter: Market capitalization > 5B TWD
market_cap_filter = market_cap.shift(1) > 5_000_000_000
# P/E Ratio filter: Avoid extremely high P/E ratios (e.g., > 40)
pe_filter = pe_ratio.ffill().shift(1) < 40
# Apply all filters
all_filters = liquidity_filter & price_filter & market_cap_filter & pe_filter
filtered_factor = combined_factor[all_filters]
# 5. Select stocks
# Select top 15 stocks based on the combined factor score
position = filtered_factor.is_largest(15)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)