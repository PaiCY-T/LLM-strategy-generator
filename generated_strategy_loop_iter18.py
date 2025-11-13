# 1. Load data - ALWAYS use adjusted data for price!
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits
trading_value = data.get('price:成交金額')  # OK for liquidity filter
market_value = data.get('etl:market_value') # For market cap filter
# Underused/diverse factors
pb_ratio = data.get('price_earning_ratio:股價淨值比') # Prioritize: Underused valuation
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)') # Prioritize: Underused growth
mfi = data.indicator('MFI') # Less common technical indicator
investment_trust_strength = data.get('institutional_investors_trading_summary:投信買賣超股數') # Underused institutional conviction
# 2. Calculate factors
# Factor 1: Value (Inverse P/B Ratio) - Higher is better (lower P/B)
# Handle potential division by zero or negative P/B
inverse_pb = (1 / pb_ratio.ffill().shift(1)).replace([float('inf'), -float('inf')], float('nan'))
# Factor 2: Monthly Revenue Growth Year-over-Year
revenue_growth = revenue_yoy.ffill().shift(1)
# Factor 3: Money Flow Index (MFI) - Measures buying/selling pressure
# MFI is typically 0-100. Higher values indicate stronger buying pressure.
money_flow = mfi.shift(1)
# Factor 4: Investment Trust Buying Strength - Domestic institutional conviction
# Higher values indicate stronger conviction from investment trusts.
trust_strength = investment_trust_strength.ffill().shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
inverse_pb_rank = inverse_pb.rank(axis=1, pct=True)
revenue_growth_rank = revenue_growth.rank(axis=1, pct=True)
money_flow_rank = money_flow.rank(axis=1, pct=True)
trust_strength_rank = trust_strength.rank(axis=1, pct=True)
# Combine with diverse weights
# Prioritize value and growth, balance with technical and institutional conviction
combined_factor = (inverse_pb_rank * 0.35 +
                   revenue_growth_rank * 0.30 +
                   money_flow_rank * 0.20 +
                   trust_strength_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 40M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 40_000_000
# Price filter: Stock price > 15 TWD (avoid penny stocks)
price_filter = close.shift(1) > 15
# Market Cap filter: Market value > 3 Billion TWD (avoid micro-caps)
market_cap_filter = market_value.shift(1) > 3_000_000_000
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter]
# 5. Select stocks (select top 15 stocks)
position = filtered_factor.is_largest(15)
# 6. Run backtest with quarterly rebalancing and 8% stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.08)