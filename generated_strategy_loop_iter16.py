# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')
roe = data.get('fundamental_features:ROE稅後') # Added ROE as a quality factor

# 2. Calculate factors

# Momentum factor: 20-day price change
momentum_factor = close.pct_change(20).shift(1)

# Value factor: Inverse of P/B ratio. Lower P/B is better.
# Shifted forward to avoid look-ahead bias.
value_factor = (1 / pb_ratio).shift(1)

# Institutional buying strength factor: Foreign investor strength
# Shifted forward to avoid look-ahead bias.
institutional_factor = foreign_strength.shift(1)

# Quality factor: Return on Equity (ROE)
# Using raw ROE as per previous learning (avoid smoothing).
# Shifted forward to avoid look-ahead bias.
quality_factor = roe.shift(1)

# 3. Combine factors
# Weights adjusted slightly from a hypothetical equal weighting (0.25 each)
# to explore fine-tuning within the ±5% maximum adjustment constraint.
# Momentum is often a strong driver, so slightly higher weight.
# Value and Institutional flow are also important. Quality provides a baseline.
combined_factor = (
    momentum_factor * 0.30 +  # Adjusted from 0.25 by +5%
    value_factor * 0.20 +     # Adjusted from 0.25 by -5%
    institutional_factor * 0.25 + # Kept at 0.25
    quality_factor * 0.25     # Kept at 0.25
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be > 50 million TWD.
# This preserves the critical filter from previous successes.
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Close price must be greater than 10 TWD.
# This preserves the critical filter from previous successes (filters penny stocks).
price_filter = close.shift(1) > 10

# Combine all filters
# Ensure all conditions are met for a stock to be considered.
all_filters = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters to the combined factor and select the top 8 stocks.
# The number of stocks is within the 6-12 range.
position = combined_factor[all_filters].is_largest(8)

# 6. Run backtest
# Backtest with quarterly rebalancing and a stop loss of 8%.
report = sim(position, resample="Q", upload=False, stop_loss=0.08)