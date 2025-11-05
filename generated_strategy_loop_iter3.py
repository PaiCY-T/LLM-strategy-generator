# 1. Load data - ALWAYS use adjusted data for price!
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits
trading_value = data.get('price:成交金額')  # OK for liquidity filter
# Underused Fundamental Factors (Quality & Prudence)
operating_margin = data.get('fundamental_features:營業利益率')
net_profit_margin = data.get('fundamental_features:稅後淨利率')
debt_ratio = data.get('fundamental_features:負債比率')
# Underused Valuation Factor
pb_ratio = data.get('price_earning_ratio:股價淨值比')
# Underused Institutional Flow Factor
broker_balance_index = data.get('etl:broker_transactions:balance_index')
# Underused Technical Indicator
mfi = data.indicator('MFI', 14) # Money Flow Index with 14 periods
# 2. Calculate factors (all shifted by 1 to prevent look-ahead bias)
# Factor 1: Profitability (Quality) - Average of Operating and Net Profit Margins
# Use ffill for quarterly data and then shift
profitability_factor = ((operating_margin.ffill() + net_profit_margin.ffill()) / 2).shift(1)
# Factor 2: Financial Prudence (Inverse of Debt Ratio)
# Lower debt ratio is better, so 100 - debt_ratio (assuming percentage)
prudence_factor = (100 - debt_ratio.ffill()).shift(1)
# Factor 3: Value (Inverse of Price-to-Book Ratio)
# Lower P/B is better, so 1 / PB
value_factor = (1 / pb_ratio.ffill()).shift(1)
# Factor 4: Smart Money Concentration (Broker Balance Index)
# Higher index indicates more concentrated smart money holdings
broker_concentration_factor = broker_balance_index.shift(1)
# Factor 5: Money Flow Strength (MFI)
# Higher MFI indicates buying pressure
mfi_strength_factor = mfi.shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
profitability_rank = profitability_factor.rank(axis=1, pct=True)
prudence_rank = prudence_factor.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
broker_concentration_rank = broker_concentration_factor.rank(axis=1, pct=True)
mfi_strength_rank = mfi_strength_factor.rank(axis=1, pct=True)
# Combine with unique weights, emphasizing quality and value
combined_factor = (profitability_rank * 0.25 +
                   prudence_rank * 0.20 +
                   value_rank * 0.25 +
                   broker_concentration_rank * 0.15 +
                   mfi_strength_rank * 0.15)
# 4. Apply filters (differentiating from common patterns)
# Liquidity filter: Average daily trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Stock price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20
# P/B Ratio sanity filter: Avoid extremely low P/B (potential distress) or extremely high P/B
pb_filter = (pb_ratio.ffill().shift(1) > 0.5) & (pb_ratio.ffill().shift(1) < 10)
# Debt Ratio sanity filter: Avoid companies with excessively high debt
debt_filter = debt_ratio.ffill().shift(1) < 150 # Debt ratio below 150%
# Apply all filters