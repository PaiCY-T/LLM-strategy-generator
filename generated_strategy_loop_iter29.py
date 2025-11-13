# 1. Load data
close = data.get('etl:adj_close')
trading_value = data.get('price:成交金額')
market_value = data.get('etl:market_value')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
investment_trust_strength = data.get('institutional_investors_trading_summary:投信買賣超股數')
mfi = data.indicator('MFI')
pe_ratio = data.get('price_earning_ratio:本益比')
# 2. Calculate factors
# Factor 1: Value (Inverse P/B Ratio) - Prioritizing underused fundamental_features:股價淨值比
# Handle potential division by zero or negative P/B by setting to NaN or a very low rank later
pb_ratio_shifted = pb_ratio.ffill().shift(1)
value_factor = 1 / pb_ratio_shifted
# Replace inf with NaN for ranking
value_factor = value_factor.replace([float('inf'), -float('inf')], float('nan'))
# Factor 2: Growth (Monthly Revenue YoY) - Prioritizing underused monthly_revenue
growth_factor = revenue_yoy.ffill().shift(1)
# Factor 3: Institutional Conviction (Investment Trust Strength) - Prioritizing underused institutional data
conviction_factor = investment_trust_strength.ffill().shift(1)
# Factor 4: Money Flow Momentum (MFI) - Using a less common technical indicator for ranking
mfi_factor = mfi.shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks
value_rank = value_factor.rank(axis=1, pct=True)
growth_rank = growth_factor.rank(axis=1, pct=True)
conviction_rank = conviction_factor.rank(axis=1, pct=True)
mfi_rank = mfi_factor.rank(axis=1, pct=True)
# Combine with diverse weights, emphasizing underused factors
combined_factor = (value_rank * 0.30 +
                   growth_rank * 0.25 +
                   conviction_rank * 0.25 +
                   mfi_rank * 0.20)
# 4. Apply diverse filters
# Liquidity filter: Higher threshold than common patterns
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 100_000_000
# Price filter: Avoid very low-priced stocks
price_filter = close.shift(1) > 15
# Market Cap filter: Focus on mid-to-large caps, using 'etl:market_value' as a filter, not a ranking factor
market_cap_filter = market_value.shift(1) > 10_000_000_000 # 10 Billion TWD
# Valuation filter (P/E): Avoid extremely overvalued stocks and negative P/E
pe_ratio_shifted = pe_ratio.ffill().shift(1)
pe_filter = (pe_ratio_shifted < 30) & (pe_ratio_shifted > 0)
# P/B filter: Ensure positive P/B for value factor validity
pb_filter_positive = pb_ratio_shifted > 0
# Apply all filters
filtered_factor = combined_factor[liquidity_filter &