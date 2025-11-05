# 1. Load data
close = data.get('etl:adj_close')
trading_value = data.get('price:成交金額')
market_value = data.get('etl:market_value')
# Underused factors and related data
pb_ratio = data.get('price_earning_ratio:股價淨值比')
pe_ratio = data.get('price_earning_ratio:本益比')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_strength = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
mfi = data.indicator('MFI')
# 2. Calculate factors
# Factor 1: Inverted Price-to-Book Ratio (Value Factor)
# Filter out non-positive P/B ratios, then invert. Lower P/B is better for value.
# Cap P/B to avoid extreme values before inverting.
pb_ratio_clean = pb_ratio.ffill().shift(1).clip(lower=0.5, upper=100)
inverted_pb = 1 / pb_ratio_clean
# Factor 2: Monthly Revenue Year-over-Year Growth (Growth Factor)
revenue_growth_factor = revenue_yoy.ffill().shift(1)
# Factor 3: Foreign Buying Strength (Institutional Conviction Factor)
foreign_strength_factor = foreign_strength.ffill().shift(1)
# Factor 4: Money Flow Index (Volume-weighted Technical Momentum)
mfi_factor = mfi.shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks
inverted_pb_rank = inverted_pb.rank(axis=1, pct=True)
revenue_growth_rank = revenue_growth_factor.rank(axis=1, pct=True)
foreign_strength_rank = foreign_strength_factor.rank(axis=1, pct=True)
mfi_rank = mfi_factor.rank(axis=1, pct=True)
# Combine with diverse weights
combined_factor = (inverted_pb_rank * 0.30 +
                   revenue_growth_rank * 0.30 +
                   foreign_strength_rank * 0.25 +
                   mfi_rank * 0.15)
# 4. Apply diverse filters
# Liquidity filter: Higher threshold to target more liquid stocks
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 75_000_000
# Price filter: Avoid very low-priced stocks
price_filter = close.shift(1) > 20
# Market Cap filter: Target mid-to-large cap stocks
market_cap_filter = market_value.shift(1) > 10_000_000_000
# P/E Ratio filter: Avoid extremely overvalued or negative P/E stocks
pe_ratio_shifted = pe_ratio.ffill().shift(1)
pe_ratio_filter = (pe_ratio_shifted > 5) & (pe_ratio_shifted < 35)
# MFI range filter: Avoid extreme overbought/oversold conditions
mfi_range_filter = (mfi.shift(1) > 20) & (mfi.shift(1) < 80)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & pe_ratio_filter & mfi_range_filter]
# 5. Select stocks
position = filtered_factor.is_largest(10)