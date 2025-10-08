# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)') # Added as a complementary factor

# 2. Calculate factors
# Momentum factor (60-day returns)
returns = close.pct_change(60)
factor_momentum = returns.shift(1) # Shift forward to avoid look-ahead

# ROE factor (Return on Equity)
# Based on previous success, using raw ROE (window=1)
factor_roe = roe.shift(1) # Shift forward to avoid look-ahead

# Revenue YoY Growth factor (new complementary factor)
factor_revenue_yoy = revenue_yoy.shift(1) # Shift forward to avoid look-ahead

# 3. Combine factors
# Rank factors to normalize them before combining
ranked_momentum = factor_momentum.rank(axis=1, pct=True)
ranked_roe = factor_roe.rank(axis=1, pct=True)
ranked_revenue_yoy = factor_revenue_yoy.rank(axis=1, pct=True)

# Combine factors with adjusted weights.
# Assuming previous champion used 0.5 for momentum and 0.5 for ROE.
# Weights are adjusted by -4% for momentum and ROE, and +4% for the new revenue_yoy factor.
# This adheres to the "adjust weights ONLY by ±5% maximum" and "add ONLY complementary factors" rules.
combined_factor = (
    ranked_momentum * 0.48 +    # Adjusted weight from 0.5 (4% reduction)
    ranked_roe * 0.48 +         # Adjusted weight from 0.5 (4% reduction)
    ranked_revenue_yoy * 0.04   # New complementary factor with a small weight
)

# 4. Apply filters
# CRITICAL PRESERVATION: Liquidity filter (from previous champion)
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# CRITICAL PRESERVATION: Price > 10 TWD filter (from previous champion)
price_filter = close.shift(1) > 10

# Combine all filters
total_filter = liquidity_filter & price_filter

# 5. Select stocks
# Select 8 stocks, adhering to the 6-12 stock selection constraint.
position = combined_factor[total_filter].is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)