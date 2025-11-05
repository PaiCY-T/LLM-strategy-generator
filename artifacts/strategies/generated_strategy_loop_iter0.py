# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
net_profit_margin = data.get('fundamental_features:稅後淨利率')
trading_value = data.get('price:成交金額')

# 2. Calculate factors

# Factor 1: Momentum (20-day returns)
momentum = close.pct_change(20).shift(1)

# Factor 2: Revenue YoY growth
# Monthly revenue data needs to be aligned with daily price data.
# We'll use forward fill to carry the latest monthly revenue YoY to daily data.
revenue_yoy_daily = revenue_yoy.ffill().shift(1)

# Factor 3: Value (inverse of P/B ratio)
# Lower P/B is generally better for value, so we take the inverse.
value_factor = (1 / pb_ratio).shift(1)

# Factor 4: Profitability (Net Profit Margin)
profitability = net_profit_margin.shift(1)

# 3. Combine factors
# We'll normalize factors before combining to give them equal weight
# and handle potential scale differences.
# A simple normalization is rank-based.
momentum_rank = momentum.rank(axis=1, pct=True)
revenue_yoy_rank = revenue_yoy_daily.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
profitability_rank = profitability.rank(axis=1, pct=True)

# Combine ranks. Higher combined rank is better.
combined_factor = (momentum_rank * 0.3 +
                   revenue_yoy_rank * 0.3 +
                   value_rank * 0.2 +
                   profitability_rank * 0.2)

# 4. Apply filters
# Filter 1: Liquidity filter (average daily trading value > 100 million TWD over 20 days)
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 100_000_000

# Filter 2: Price filter (close price > 10 TWD)
price_filter = close.shift(1) > 10

# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter]

# 5. Select stocks
# Select the top 10 stocks based on the filtered combined factor
position = filtered_factor.is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)