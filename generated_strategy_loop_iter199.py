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
# ffill for quarterly data, then shift to avoid look-ahead
quality = roe.rolling(4).mean().ffill().shift(1)
# Factor 3: Growth (Monthly Revenue YoY)
# ffill for monthly data, then shift to avoid look-ahead
growth = revenue_yoy.ffill().shift(1)
# Factor 4: Institutional Flow (20-day sum of Foreign Net Buy)
flow = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 5: Value (Inverse P/E Ratio)
# ffill for quarterly data, then shift. Handle non-positive P/E ratios.
inverse_pe = (1 / pe_ratio).ffill().shift(1)
# Set inverse_pe to NaN if original PE was non-positive (to avoid inf or negative value factors)
inverse_pe[pe_ratio.ffill().shift(1) <= 0] = None
value = inverse_pe
# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
growth_rank = growth.rank(axis=1, pct=True)
flow_rank = flow.rank(axis=1, pct=True)
value_rank = value.rank(axis=1, pct=True)
# Combine with weighted average. Weights sum to 1.0.
combined_factor = (momentum_rank * 0.25 +
                   quality_rank * 0.25 +
                   growth_rank * 0.20 +
                   flow_rank * 0.20 +
                   value_rank * 0.10)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 75M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 75_000_000
# Price filter: Close price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20
# Market Cap filter: Market cap > 10 Billion TWD for mid-large cap focus
market_cap_filter = market_cap.shift(1) > 10_000_000_000
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter]
# 5. Select stocks
# Select top 12 stocks based on the combined factor score
position = filtered_factor.is_largest(12)
# 6. Run backtest
# Backtest with quarterly rebalancing and an 8% stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.08)