# 1. Load data
close = data.get('etl:adj_close')
trading_value = data.get('price:成交金額')
pb_ratio_raw = data.get('price_earning_ratio:股價淨值比')
revenue_yoy_raw = data.get('monthly_revenue:去年同月增減(%)')
it_strength_raw = data.get('institutional_investors_trading_summary:投信買賣超股數')
market_cap_raw = data.get('etl:market_value')
roe_raw = data.get('fundamental_features:ROE稅後')
atr = data.indicator('ATR')
# 2. Calculate factors
# Factor 1: Inverse Price-to-Book Ratio (Value)
# Fill forward for quarterly data, then shift to avoid look-ahead bias
pb_ratio = pb_ratio_raw.ffill()
# Replace zero or infinite P/B with NaN to avoid division errors, then inverse
inverse_pb = (1 / pb_ratio.replace([0, float('inf'), -float('inf')], float('nan'))).shift(1)
# Factor 2: Monthly Revenue Growth Year-over-Year (Growth Momentum)
# Fill forward for monthly data, then shift
revenue_yoy = revenue_yoy_raw.ffill().shift(1)
# Factor 3: Investment Trust Buying Strength (Institutional Conviction)
# Fill forward for monthly/weekly data, then shift
it_strength = it_strength_raw.ffill().shift(1)
# Factor 4: Inverse Market Capitalization (Small Cap Bias)
# Shift to avoid look-ahead bias
market_cap = market_cap_raw
# Replace zero or infinite market cap with NaN, then inverse
inverse_market_cap = (1 / market_cap.replace([0, float('inf'), -float('inf')], float('nan'))).shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks
inverse_pb_rank = inverse_pb.rank(axis=1, pct=True)
revenue_yoy_rank = revenue_yoy.rank(axis=1, pct=True)
it_strength_rank = it_strength.rank(axis=1, pct=True)
inverse_market_cap_rank = inverse_market_cap.rank(axis=1, pct=True)
# Combine with unique weights
combined_factor = (inverse_pb_rank * 0.30 +
                   revenue_yoy_rank * 0.25 +
                   it_strength_rank * 0.25 +
                   inverse_market_cap_rank * 0.20)
# 4. Apply filters
# Liquidity filter: Average trading value over 60 days > 75M TWD
liquidity_