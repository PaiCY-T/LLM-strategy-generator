# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
eps = data.get('fundamental_features:EPS')
rsi = data.get('indicator:RSI')

# 2. Calculate factors
# Factor 1: 20-day Price Momentum
momentum = close.pct_change(20)
momentum_factor = momentum.shift(1)

# Factor 2: Monthly Revenue YoY Growth
growth_factor = revenue_yoy.shift(1)

# Factor 3: Earnings Per Share (EPS) Rank
# Rank EPS cross-sectionally to normalize its value
eps_rank = eps.rank(axis=1, pct=True)
eps_factor = eps_rank.shift(1)

# Factor 4: Inverse RSI (favoring oversold conditions)
# A lower RSI value (e.g., < 30) indicates oversold.
# (100 - RSI) will give higher values for lower RSI, making it a "buy" signal.
rsi_inverse = (100 - rsi)
rsi_factor = rsi_inverse.shift(1)

# 3. Combine factors
# Rank each shifted factor cross-sectionally to ensure equal weighting and normalization
momentum_rank_shifted = momentum_factor.rank(axis=1, pct=True)
growth_rank_shifted = growth_factor.rank(axis=1, pct=True)
rsi_rank_shifted = rsi_factor.rank(axis=1, pct=True)

# Combine the ranked factors. EPS factor is already ranked.
# We give equal weight to momentum, growth, EPS strength, and oversold RSI.
combined_factor = (momentum_rank_shifted + growth_rank_shifted + eps_factor + rsi_rank_shifted) / 4

# 4. Apply filters
# Filter 1: Liquidity filter (average daily trading value over 20 days > 50 million TWD)
avg_trading_value = trading_value.rolling(20).mean()
liquidity_filter = (avg_trading_value > 50_000_000).shift(1)

# Filter 2: Price filter (close price > 10 TWD)
price_filter = (close > 10).shift(1)

# Combine all filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply the combined filter and select the top 10 stocks based on the combined factor
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)