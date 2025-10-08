# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
three_main_forces = data.get('three_main_forces_buy_sell_summary')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)') # Added complementary factor for growth

# 2. Calculate factors
# Momentum factor (60-day return)
momentum = close.pct_change(60).shift(1)

# ROE factor (fundamental quality/value)
# Preserving raw ROE as per previous iteration learning (avoid smoothing)
roe_factor = roe.shift(1)

# Institutional buying factor (three main forces net buy/sell)
three_main_forces_factor = three_main_forces.shift(1)

# Revenue growth factor (new complementary factor)
revenue_yoy_factor = revenue_yoy.shift(1)

# 3. Apply filters
# ABSOLUTE REQUIREMENT: Preserve price filter > 10 TWD
price_filter = close > 10

# ABSOLUTE REQUIREMENT: Preserve liquidity filter (avoid increasing threshold)
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Filter for positive ROE and positive revenue growth
roe_positive_filter = roe_factor > 0
revenue_yoy_positive_filter = revenue_yoy_factor > 0

# Combine all filters
combined_filters = price_filter & liquidity_filter & roe_positive_filter & revenue_yoy_positive_filter

# 4. Normalize and combine factors
# Rank factors to combine them effectively
momentum_rank = momentum.rank(axis=1, pct=True)
roe_rank = roe_factor.rank(axis=1, pct=True)
three_main_forces_rank = three_main_forces_factor.rank(axis=1, pct=True)
revenue_yoy_rank = revenue_yoy_factor.rank(axis=1, pct=True)

# Combine factors with adjusted weights (within ±5% of assumed equal weights for 4 factors)
# Original assumed equal weight for 4 factors: 0.25
# Adjusting weights:
# Momentum: 0.25 + 0.05 = 0.30 (Increased slightly)
# ROE: 0.25 - 0.05 = 0.20 (Decreased slightly)
# Three Main Forces: 0.25 + 0.05 = 0.30 (Increased slightly)
# Revenue YoY: 0.25 - 0.05 = 0.20 (Decreased slightly for the new factor)
combined_factor = (
    momentum_rank * 0.30 +
    roe_rank * 0.20 +
    three_main_forces_rank * 0.30 +
    revenue_yoy_rank * 0.20
)

# 5. Select stocks
# Apply combined filters and select the top 8 stocks
position = combined_factor[combined_filters].is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)