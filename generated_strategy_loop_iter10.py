# 1. Load data
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits, used for price filter
trading_value = data.get('price:成交金額')  # OK for liquidity filter
market_value = data.get('etl:market_value') # Adjusted market cap, used for size filter
# Underused/rare factors prioritized for diversity
net_profit_margin = data.get('fundamental_features:稅後淨利率') # Quality factor
pe_ratio = data.get('price_earning_ratio:本益比') # Value factor
revenue_mom_change = data.get('monthly_revenue:上月比較增減(%)') # Short-term growth momentum
inv_trust_strength = data.get('institutional_investors_trading_summary:投信買賣超股數') # Domestic institutional sentiment
# 2. Calculate factors
# Factor 1: Quality - Smoothed Net Profit Margin (4-quarter average)
# Higher net profit margin is better
quality_factor = net_profit_margin.ffill().rolling(4).mean().shift(1)
# Factor 2: Value - Inverse P/E Ratio (lower P/E is better, so inverse makes higher better)
# Filter out negative P/E (loss-making) later
value_factor = (1 / pe_ratio).shift(1)
# Factor 3: Short-term Growth Momentum - Monthly Revenue MoM Change
# Higher MoM change is better
growth_momentum_factor = revenue_mom_change.ffill().shift(1)
# Factor 4: Domestic Institutional Conviction - Sum of Investment Trust Strength over 5 days
# Higher strength indicates stronger conviction
institutional_conviction_factor = inv_trust_strength.rolling(5).sum().shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks
quality_rank = quality_factor.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
growth_momentum_rank = growth_momentum_factor.rank(axis=1, pct=True)
institutional_conviction_rank = institutional_conviction_factor.rank(axis=1, pct=True)
# Combine with unique weights, emphasizing quality and value, then growth and institutional flow
combined_factor = (quality_rank * 0.35 +
                   value_rank * 0.30 +
                   growth_momentum_rank * 0.20 +
                   institutional_conviction_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 70M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000
# Price filter: Stock price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20
# Market cap filter: Market capitalization > 10 Billion TWD to focus on mid-large caps
market_cap_filter = market_value.shift(1) > 10_000_000_000
# P/E Ratio filter: P/E must be positive (profitable) and not excessively high (< 30)
pe_filter = (pe_ratio.shift(1) > 0) & (pe_ratio.shift(1) < 30)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & pe_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
# Quarterly rebalancing with an 8% stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.08)