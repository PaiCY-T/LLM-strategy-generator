# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')

# 2. Calculate factors

# Factor 1: Smoothed Monthly Revenue YoY Growth
# Calculate 3-month rolling average of YoY growth, then shift to avoid look-ahead.
# min_periods=1 ensures calculation even with fewer data points at the start.
factor_revenue_growth = revenue_yoy.rolling(3, min_periods=1).mean().shift(1)

# Factor 2: Foreign Investor Buying Strength
# Use the strength indicator directly, shifted to avoid look-ahead.
factor_foreign_strength = foreign_strength.shift(1)

# Factor 3: Price Momentum (60-day returns)
# Calculate 60-day percentage change in close price, then shift to avoid look-ahead.
momentum = close.pct_change(60)
factor_momentum = momentum.shift(1)

# Rank factors to normalize them before combining.
# Ranking ensures each factor contributes equally regardless of its scale.
factor_revenue_growth_rank = factor_revenue_growth.rank(axis=1, pct=True)
factor_foreign_strength_rank = factor_foreign_strength.rank(axis=1, pct=True)
factor_momentum_rank = factor_momentum.rank(axis=1, pct=True)

# 3. Combine factors
# Simple average of the ranked factors.
# We fill NaN values with 0 before combining, assuming missing data means no strong signal.
combined_factor = (
    factor_revenue_growth_rank.fillna(0) +
    factor_foreign_strength_rank.fillna(0) +
    factor_momentum_rank.fillna(0)
) / 3

# 4. Apply filters

# Filter 1: Liquidity Filter - Average daily trading value over 20 days > 50 million TWD
# Shifted to avoid look-ahead.
avg_trading_value = trading_value.rolling(20, min_periods=1).mean().shift(1)
liquidity_filter = avg_trading_value > 50_000_000

# Filter 2: Price Filter - Close price must be above 10 TWD to avoid penny stocks.
# Shifted to avoid look-ahead.
price_filter = close.shift(1) > 10

# Filter 3: Positive Revenue Growth - Only consider stocks with positive smoothed revenue growth.
# This acts as a fundamental quality filter.
positive_revenue_growth_filter = factor_revenue_growth > 0

# Combine all filters using logical AND.
all_filters = liquidity_filter & price_filter & positive_revenue_growth_filter

# 5. Select stocks
# Apply all filters to the combined factor and select the top 10 stocks with the highest factor values.
position = combined_factor[all_filters].is_largest(10)

# 6. Run backtest
# The backtest is run quarterly (resample="Q") with a stop-loss of 8%.
report = sim(position, resample="Q", upload=False, stop_loss=0.08)