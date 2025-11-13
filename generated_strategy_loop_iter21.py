# 1. Load data
close = data.get('etl:adj_close')
trading_value = data.get('price:成交金額')
market_value = data.get('etl:market_value')
book_value_per_share = data.get('fundamental_features:每股淨值')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
investment_trust_strength = data.get('institutional_investors_trading_summary:投信買賣超股數')
cci = data.indicator('CCI')
atr = data.indicator('ATR')
# 2. Calculate factors
# Factor 1: Value (Book Value Per Share) - Higher BVPS is generally better
# Use ffill for quarterly data and shift to prevent look-ahead bias
bvps_factor = book_value_per_share.ffill().shift(1)
# Factor 2: Growth (Monthly Revenue Year-over-Year Growth) - Higher growth is better
# Use ffill for monthly data and shift to prevent look-ahead bias
revenue_growth_factor = revenue_yoy.ffill().shift(1)
# Factor 3: Institutional Conviction (Investment Trust Strength) - Higher strength indicates more buying
# Use ffill for potentially lower frequency data and shift
it_strength_factor = investment_trust_strength.ffill().shift(1)
# Factor 4: Short-term Momentum/Trend (Commodity Channel Index) - Higher positive CCI indicates stronger upward momentum
cci_factor = cci.shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
bvps_rank = bvps_factor.rank(axis=1, pct=True)
revenue_growth_rank = revenue_growth_factor.rank(axis=1, pct=True)
it_strength_rank = it_strength_factor.rank(axis=1, pct=True)
cci_rank = cci_factor.rank(axis=1, pct=True)
# Combine with unique weights
combined_factor = (bvps_rank * 0.25 +
                   revenue_growth_rank * 0.30 +
                   it_strength_rank * 0.25 +
                   cci_rank * 0.20)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be above 40M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 40_000_000
# Price filter: Stock price must be above 15 TWD to avoid penny stocks
price_filter = close.shift(1) > 15
# Market Cap filter: Market value must be above 10B TWD to avoid micro