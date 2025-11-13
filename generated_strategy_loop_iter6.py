# 1. Load data - ALWAYS use adjusted data for price!
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits
trading_value = data.get('price:成交金額')  # OK for liquidity filter
# Underused/Rare Factors
gross_margin = data.get('fundamental_features:營業毛利率')
pe_ratio = data.get('price_earning_ratio:本益比')
revenue_mom_change = data.get('monthly_revenue:上月比較增減(%)')
rsi = data.indicator('RSI')
# 2. Calculate factors with .shift(1) and .ffill()
# Factor 1: Quality - Smoothed Gross Profit Margin (4-quarter average)
# Use .ffill() for quarterly data, then .shift(1)
smoothed_gross_margin = gross_margin.ffill().rolling(window=4, min_periods=1).mean().shift(1)
# Factor 2: Value - Inverse P/E Ratio
# Handle potential division by zero or negative P/E by replacing inf with 0
inverse_pe = (1 / pe_ratio.ffill()).replace([float('inf'), -float('inf')], 0).shift(1)
# Factor 3: Growth - Monthly Revenue MoM Change
# Use .ffill() for monthly data, then .shift(1)
revenue_growth_factor = revenue_mom_change.ffill().shift(1)
# Factor 4: Technical - RSI Reversal (Lower RSI implies more oversold, higher potential for reversal)
# Use (100 - RSI) to rank oversold stocks higher
rsi_reversal_factor = (100 - rsi).shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
gross_margin_rank = smoothed_gross_margin.rank(axis=1, pct=True)
inverse_pe_rank = inverse_pe.rank(axis=1, pct=True)
revenue_growth_rank = revenue_growth_factor.rank(axis=1, pct=True)
rsi_reversal_rank = rsi_reversal_factor.rank(axis=1, pct=True)
# Combine with diverse weights, prioritizing underused fundamentals and short-term growth
combined_factor = (gross_margin_rank * 0.35 +
                   inverse_pe_rank * 0.25 +
                   revenue_growth_rank * 0.25 +
                   rsi_reversal_rank * 0.15)
# 4. Apply filters for liquidity, price, and fundamental sanity
# Liquidity filter: Average trading value over 20 days > 60M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 60_000_000
# Price filter: Stock price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20
# P/E Ratio filter: P/E between 5 and 30 (reasonable valuation range)
pe_filter = (pe_ratio.ffill().shift(1) > 5) & (pe_ratio.ffill().shift(1) < 30)
# Gross Margin filter: Ensure positive gross margin
positive_gross_margin_filter = smoothed_gross_margin > 0
# Apply all filters