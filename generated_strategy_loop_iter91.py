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
# Factor 2: Quality (ROE with 4-quarter smoothing)
# Forward-fill monthly/quarterly data to daily frequency, then shift
roe_smoothed = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
# Forward-fill monthly data to daily frequency, then shift
revenue_growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of Foreign Net Buy)
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: Value (Inverse of P/E Ratio)
# Add a small epsilon to avoid division by zero if P/E is exactly 0.
value_factor = (1 / (pe_ratio.ffill().shift(1) + 0.001))
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
roe_rank = roe_smoothed.rank(axis=1, pct=True)
revenue_rank = revenue_growth.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
# Combine with meaningful weights
# Emphasize momentum, quality, and institutional flow, with some value
combined_factor = (momentum_rank * 0.30 +
                   roe_rank * 0.20 +
                   revenue_rank * 0.20 +
                   flow_rank * 0.20 +
                   value_rank * 0.10)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Close price > 15 TWD to avoid penny stocks
price_filter = close.shift(1) > 15
# P/E Ratio filter: P/E between 5 and 30 to avoid extremely cheap or expensive stocks
pe_filter = (pe_ratio.ffill().shift(1) > 5) & (pe_ratio.ffill().shift(1) < 30)
# Combine all filters
all_filters = liquidity_filter & price_filter & pe_filter
filtered_factor = combined_factor[all_filters]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)