# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
three_forces = data.get('three_main_forces_buy_sell_summary')
operating_margin = data.get('fundamental_features:營業利益率') # Added for new quality filter

# 2. Calculate factors
# Momentum factor: 20-day percentage change
momentum = close.pct_change(20).shift(1)
momentum_rank = momentum.rank(axis=1, pct=True)

# Value factor: Inverse of Price-to-Book ratio
# Higher inverse P/B means lower P/B, indicating better value
value = (1 / pb_ratio).shift(1)
value_rank = value.rank(axis=1, pct=True)

# Quality factor: Return on Equity (ROE)
# Using ROE directly as a quality indicator (raw, window=1, as per preservation requirements)
quality_roe = roe.shift(1)
quality_roe_rank = quality_roe.rank(axis=1, pct=True)

# Institutional Buying factor: 5-day average of three main forces net buy/sell
institutional_flow = three_forces.rolling(5).mean().shift(1)
institutional_flow_rank = institutional_flow.rank(axis=1, pct=True)

# 3. Combine factors
# Adjusting weights by ±5% maximum from an assumed equal weight of 0.25 for each factor
# (e.g., 0.25 * 0.05 = 0.0125, so max change is +/- 0.0125)
# Slightly increased momentum and quality, slightly decreased value and institutional flow
combined_factor = (
    momentum_rank * 0.26 +  # Weight adjusted by +0.01 from 0.25
    value_rank * 0.24 +     # Weight adjusted by -0.01 from 0.25
    quality_roe_rank * 0.26 + # Weight adjusted by +0.01 from 0.25
    institutional_flow_rank * 0.24 # Weight adjusted by -0.01 from 0.25
)

# 4. Apply filters
# Price filter: Preserve the critical requirement of price > 10 TWD
price_filter = close.shift(1) > 10

# Liquidity filter: Preserve the critical requirement for average trading value
# Avoid increasing threshold as per previous iteration feedback
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# New Quality filter: Require operating margin to be positive (e.g., > 5%)
# This is a complementary quality filter as per exploration suggestions
operating_margin_filter = operating_margin.shift(1) > 0.05

# Combine all filters
total_filter = price_filter & liquidity_filter & operating_margin_filter

# 5. Select stocks
# Selecting 9 stocks, within the 6-12 range, slightly different from template's 8
position = combined_factor[total_filter].is_largest(9)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)