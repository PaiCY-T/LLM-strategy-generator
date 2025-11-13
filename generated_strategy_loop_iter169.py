# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
market_cap = data.get('etl:market_value')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Long-term Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)
# Factor 2: Quality (ROE with 4-quarter smoothing)
# ROE is quarterly, so ffill then shift to align with daily data and avoid look-ahead
quality_roe = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY, ffill then shift)
# Monthly revenue is monthly, so ffill then shift
growth_revenue = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of foreign net buy)
# Foreign net buy is daily, so rolling sum then shift
institutional_flow = foreign_net_buy.rolling(20).sum().shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
momentum_rank = momentum.rank(axis=1, pct=True)
quality_roe_rank = quality_roe.rank(axis=1, pct=True)
growth_revenue_rank = growth_revenue.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)
# Combine with meaningful weights (summing to 1.0)
combined_factor = (momentum_rank * 0.30 +
                   quality_roe_rank * 0.25 +
                   growth_revenue_rank * 0.25 +
                   institutional_flow_rank * 0.20)
# 4. Apply filters
# Mandatory Liquidity filter: Average daily trading value > 50M TWD over 20 days
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Mandatory Price filter: Close price > 15 TWD (avoid penny stocks)
price_filter = close.shift(1) > 15
# Optional Market Cap filter: Market cap > 10 Billion TWD (focus on mid-large caps)
market_cap_filter = market_cap.shift(1) > 10_000_000_000
# Optional RSI filter: RSI between 30 and 70 (avoid extreme overbought/oversold conditions)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Combine all filters
all_filters = liquidity_filter & price_filter & market_cap_filter & rsi_filter
# Apply filters to the combined factor
filtered_factor = combined_factor[all_filters]
# 5. Select stocks
# Select top 10 stocks based on the filtered combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)