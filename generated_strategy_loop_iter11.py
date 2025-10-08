# 1. Load data
close = data.get('price:收盤價')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')
trading_value = data.get('price:成交金額')

# 2. Calculate factors

# Momentum Factor: 60-day percentage change, then rank
momentum_returns = close.pct_change(60)
momentum_factor = momentum_returns.rank(axis=1, pct=True).shift(1)

# Value Factor: Inverse of P/B ratio, then rank (lower P/B is better)
# Handle potential inf/-inf from division by zero or negative P/B
# Replace non-positive P/B with NaN to exclude them from ranking
pb_ratio_filtered = pb_ratio.mask(pb_ratio <= 0)
value_factor = pb_ratio_filtered.rank(axis=1, ascending=False, pct=True).shift(1)

# Institutional Strength Factor: 20-day average of foreign investor strength, then rank
inst_strength_smoothed = foreign_strength.rolling(20).mean()
inst_strength_factor = inst_strength_smoothed.rank(axis=1, pct=True).shift(1)

# 3. Combine factors
# Assign weights to each factor
# Momentum (0.4), Value (0.3), Institutional Strength (0.3)
combined_factor = (
    momentum_factor * 0.4 +
    value_factor * 0.3 +
    inst_strength_factor * 0.3
)

# 4. Apply filters
# Liquidity Filter: Average daily trading value over 20 days must be > 50 million TWD
avg_trading_value = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value > 50_000_000

# Price Filter: Stock price must be above 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
all_filters = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters and select the top 8 stocks based on the combined factor
position = combined_factor[all_filters].is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)