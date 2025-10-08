# 1. Load data
close = data.get('price:收盤價')
eps = data.get('fundamental_features:EPS')
pe_ratio = data.get('price_earning_ratio:本益比')
foreign_net_buy = data.get('foreign_main_force_buy_sell_summary')
trading_value = data.get('price:成交金額')

# 2. Calculate factors

# Factor 1: Short-term Momentum
# Calculate 5-day percentage change in close price
momentum = close.pct_change(5)
momentum_factor = momentum.shift(1)

# Factor 2: EPS Growth (Year-over-Year, assuming quarterly EPS)
# Calculate 4-period (approx. 1 year) percentage change in EPS
eps_growth = eps.pct_change(4)
eps_growth_factor = eps_growth.shift(1)

# Factor 3: Foreign Investor Accumulation
# Calculate 20-day sum of foreign investor net buy/sell volume
foreign_accumulation = foreign_net_buy.rolling(20).sum()
foreign_factor = foreign_accumulation.shift(1)

# Factor 4: Value (Inverse P/E Ratio)
# Lower P/E is generally considered better for value.
# We use inverse P/E so that higher values indicate better value.
# Handle potential division by zero or negative P/E by replacing inf/-inf with NaN.
inverse_pe = (1 / pe_ratio).replace([float('inf'), -float('inf')], float('nan'))
value_factor = inverse_pe.shift(1)

# 3. Combine factors
# Rank factors to normalize them before combining.
# Higher rank indicates a stronger signal for buying.
rank_momentum = momentum_factor.rank(axis=1, pct=True)
rank_eps_growth = eps_growth_factor.rank(axis=1, pct=True)
rank_foreign = foreign_factor.rank(axis=1, pct=True)
rank_value = value_factor.rank(axis=1, pct=True)

# Combine ranked factors with predefined weights
# Weights: Momentum (0.3), EPS Growth (0.3), Foreign Flow (0.2), Value (0.2)
combined_factor = (
    rank_momentum * 0.3 +
    rank_eps_growth * 0.3 +
    rank_foreign * 0.2 +
    rank_value * 0.2
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be above 50 million TWD
avg_trading_value = trading_value.rolling(20).mean()
liquidity_filter = avg_trading_value.shift(1) > 50_000_000

# 5. Select stocks
# Apply the liquidity filter and then select the top 10 stocks based on the combined factor
position = combined_factor[liquidity_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)