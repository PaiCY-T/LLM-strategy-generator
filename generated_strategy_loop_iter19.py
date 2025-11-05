# 1. Load data
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits
trading_value = data.get('price:成交金額')  # OK for liquidity filter
pe_ratio = data.get('price_earning_ratio:本益比')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
market_value = data.get('etl:market_value')
# 2. Calculate factors
# Factor 1: Inverse P/E Ratio (Value factor, lower P/E is better)
# Handle potential division by zero or negative P/E by replacing inf/-inf with NaN
pe_ratio_inv = (1 / pe_ratio.ffill().shift(1)).replace([float('inf'), -float('inf')], float('nan'))
# Factor 2: Inverse P/B Ratio (Value factor, lower P/B is better)
# Handle potential division by zero or negative P/B by replacing inf/-inf with NaN
pb_ratio_inv = (1 / pb_ratio.ffill().shift(1)).replace([float('inf'), -float('inf')], float('nan'))
# Factor 3: Monthly Revenue Growth (Growth factor)
revenue_growth = revenue_yoy.ffill().shift(1)
# Factor 4: Inverse Market Cap (Size factor, favoring smaller/mid-cap)
# Handle potential division by zero by replacing inf/-inf with NaN
market_cap_inv = (1 / market_value.shift(1)).replace([float('inf'), -float('inf')], float('nan'))
# 3. Combine factors (normalize first!)
pe_rank = pe_ratio_inv.rank(axis=1, pct=True)
pb_rank = pb_ratio_inv.rank(axis=1, pct=True)
revenue_rank = revenue_growth.rank(axis=1, pct=True)
market_cap_rank = market_cap_inv.rank(axis=1, pct=True)
# Combine with unique weights, emphasizing value and growth
combined_factor = (pe_rank * 0.35 +
                   pb_rank * 0.30 +
                   revenue_rank * 0.25 +
                   market_cap_rank * 0.10)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 40M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 40_000_000
# Price filter: Stock price > 15 TWD
price_filter = close.shift(1) > 15
# Market Cap filter: Filter out micro-caps (< 1 Billion TWD) and mega-caps (> 100 Billion TWD)
# This aims to target mid-cap stocks for a unique risk