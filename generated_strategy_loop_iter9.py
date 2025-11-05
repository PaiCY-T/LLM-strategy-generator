# 1. Load data
close = data.get('etl:adj_close')
trading_value = data.get('price:成交金額')
market_value = data.get('etl:market_value')
net_profit_margin = data.get('fundamental_features:稅後淨利率')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
revenue_mom = data.get('monthly_revenue:上月比較增減(%)')
broker_balance_index = data.get('etl:broker_transactions:balance_index')
# 2. Calculate factors
# Factor 1: Quality - Smoothed Net Profit Margin (4-quarter average)
# Prioritizes 'fundamental_features:稅後淨利率' from underused list
quality_factor = net_profit_margin.ffill().shift(1).rolling(window=4, min_periods=1).mean()
# Factor 2: Value - Inverse Price-to-Book Ratio
# Prioritizes 'fundamental_features:股價淨值比' from underused list
# Invert so higher values are better (lower P/B)
value_factor = (1 / pb_ratio).ffill().shift(1)
# Factor 3: Growth Momentum - Monthly Revenue MoM
# Prioritizes 'monthly_revenue:上月比較增減(%)' from underused list
growth_factor = revenue_mom.ffill().shift(1)
# Factor 4: Institutional Conviction - Smoothed Broker Balance Index
# Uses 'etl:broker_transactions:balance_index' for structural diversity
conviction_factor = broker_balance_index.shift(1).rolling(window=20, min_periods=5).mean()
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks
quality_rank = quality_factor.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
growth_rank = growth_factor.rank(axis=1, pct=True)
conviction_rank = conviction_factor.rank(axis=1, pct=True)
# Combine with unique weights
combined_factor = (quality_rank * 0.30 +
                   value_rank * 0.25 +
                   growth_rank * 0.25 +
                   conviction_rank * 0.20)
# 4. Apply diverse filters
# Liquidity filter: Higher threshold than common patterns
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 75_000_000
# Price filter: Higher threshold to avoid penny stocks
price_filter = close.shift(1) > 20
# Market Cap filter: Focus on larger companies
market_cap_filter = market_value.shift(1) > 10_000_000_000 # 10 Billion TWD
# P/B Ratio guardrail: Exclude extremely overvalued stocks
pb_guardrail = pb_ratio.ffill().shift(1) < 3.0
# Profitability guardrail: Exclude unprofitable companies
profitability_guardrail = net_profit_margin.ffill().shift(1) > 0.0
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & pb_guardrail & profitability_guardrail]
# 5. Select stocks
# Select top 10 stocks for diversification
position = filtered_factor.is_largest(10)
# 6. Run backtest
# Use quarterly rebalancing and a standard stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.08)