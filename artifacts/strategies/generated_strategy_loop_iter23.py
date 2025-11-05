# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
trading_value = data.get('price:成交金額') # For liquidity filter

# Fundamental/Quality data
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')

# Institutional data
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')

# 2. Calculate factors with proper shifting to avoid look-ahead bias

# Factor 1: Long-term Momentum
# Calculate 60-day percentage change and shift by 1 day
momentum_factor = close.pct_change(60).shift(1)

# Factor 2: Return on Equity (Quality)
# Use ROE directly as suggested by previous iteration feedback (avoid smoothing).
# Shift by 1 day to ensure no look-ahead.
roe_factor = roe.shift(1)

# Factor 3: Monthly Revenue YoY Growth (Growth)
# Shift by 1 day.
revenue_yoy_factor = revenue_yoy.shift(1)

# Factor 4: Foreign Investor Net Buy (Institutional Flow)
# Calculate a rolling sum of foreign net buy over 5 days to smooth out daily noise.
# Shift by 1 day.
foreign_flow_factor = foreign_net_buy.rolling(5).sum().shift(1)

# 3. Combine factors
# Normalize factors using rank() for equal contribution and handle different scales.
# Higher momentum is better, higher ROE is better, higher revenue growth is better, higher foreign flow is better.

ranked_momentum = momentum_factor.rank(axis=1, pct=True)
ranked_roe = roe_factor.rank(axis=1, pct=True)
ranked_revenue_yoy = revenue_yoy_factor.rank(axis=1, pct=True)
ranked_foreign_flow = foreign_flow_factor.rank(axis=1, pct=True)

# Combine factors with weights.
# Adhering to the "Adjust weights ONLY by ±5% maximum" if there were existing weights.
# For this new set of factors, we start with a balanced distribution (0.25 each)
# and adjust slightly within the ±5% range to fine-tune.
combined_factor = (
    ranked_momentum * 0.28 +    # Slightly increased weight for momentum (0.25 + 0.03)
    ranked_roe * 0.28 +         # Slightly increased weight for quality (0.25 + 0.03)
    ranked_revenue_yoy * 0.22 + # Slightly decreased weight for growth (0.25 - 0.03)
    ranked_foreign_flow * 0.22  # Slightly decreased weight for institutional flow (0.25 - 0.03)
)

# 4. Apply filters (CRITICAL for quality)
# CRITICAL PRESERVATION: Preserve the exact price filter from the champion strategy.
price_filter = close.shift(1) > 10

# Preserve the liquidity filter. Avoid increasing the threshold based on past regressions.
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Add a complementary quality filter: Ensure positive ROE.
# This helps to filter out companies that are not profitable.
positive_roe_filter = roe.shift(1) > 0

# Combine all filters
all_filters = liquidity_filter & price_filter & positive_roe_filter

# 5. Select stocks using is_largest()
# Select 10 stocks, which is within the recommended 6-12 range.
position = combined_factor[all_filters].is_largest(10)

# 6. Run backtest with sim()
report = sim(position, resample="Q", upload=False, stop_loss=0.08)