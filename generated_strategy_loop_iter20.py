# 1. Load data
close = data.get('etl:adj_close')
trading_value = data.get('price:成交金額')
market_value = data.get('etl:market_value')
bvps = data.get('fundamental_features:每股淨值')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
monthly_revenue = data.get('monthly_revenue:當月營收')
investment_trust_strength = data.get('institutional_investors_trading_summary:投信買賣超股數')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Book Value Per Share (BVPS) Growth - Underused fundamental
# Look for companies with increasing BVPS over the past year (4 quarters)
bvps_growth = bvps.ffill().pct_change(4).shift(1)
# Factor 2: Inverse Price-to-Book Ratio (Value) - Underused fundamental
# Lower P/B is better for value, so use 1/P/B
inverse_pb = (1 / pb_ratio).ffill().shift(1)
# Factor 3: Monthly Revenue Momentum - Underused high-frequency fundamental
# Look for strong short-term momentum in current monthly revenue (3-month growth)
revenue_momentum = monthly_revenue.ffill().pct_change(3).shift(1)
# Factor 4: Investment Trust Buying Strength - Less common institutional flow
# Indicates domestic institutional conviction
it_strength_factor = investment_trust_strength.shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
bvps_growth_rank = bvps_growth.rank(axis=1, pct=True)
inverse_pb_rank = inverse_pb.rank(axis=1, pct=True)
revenue_momentum_rank = revenue_momentum.rank(axis=1, pct=True)
it_strength_rank = it_strength_factor.rank(axis=1, pct=True)
# Combine with diverse weights
combined_factor = (bvps_growth_rank * 0.30 +
                   inverse_pb_rank * 0.30 +
                   revenue_momentum_rank * 0.25 +
                   it_strength_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average trading value over 20 days > 40M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 40_000_000
# Price filter: Stock price > 15 TWD to avoid penny stocks
price_filter = close.shift(1) > 15
# Market Cap filter: Market value > 8B TWD to focus on mid-large caps
market_cap_filter = market_value.shift(1) > 8_000_000_000
# RSI filter: Avoid extremely overbought conditions (RSI < 70)
rsi_filter = rsi.shift(1) < 70
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & rsi_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)