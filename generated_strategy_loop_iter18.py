# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
eps = data.get('fundamental_features:EPS')
rsi = data.get('indicator:RSI')

# 2. Calculate factors
# Factor 1: Momentum (20-day return)
returns_20d = close.pct_change(20)
momentum_factor = returns_20d.shift(1)

# Factor 2: Revenue YoY Growth
# Use the revenue_yoy directly as a growth factor
revenue_growth_factor = revenue_yoy.shift(1)

# Factor 3: EPS YoY Growth (assuming EPS is quarterly, so 4 periods for YoY comparison)
eps_growth = eps.pct_change(4)
eps_growth_factor = eps_growth.shift(1)

# Factor 4: RSI (Inverse for oversold condition)
# We want to favor stocks that are oversold (low RSI).
# So, (100 - RSI) will give higher values for lower RSI.
rsi_inverse_factor = (100 - rsi).shift(1)

# 3. Combine factors
# Assign weights to each factor.
# Prioritize momentum and fundamental growth, with a smaller weight for oversold RSI.
combined_factor = (
    momentum_factor * 0.45 +
    revenue_growth_factor * 0.25 +
    eps_growth_factor * 0.20 +
    rsi_inverse_factor * 0.10
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be above 10 million TWD
avg_trading_value = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value > 10_000_000

# Price filter: Stock price must be above 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
all_filters = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters to the combined factor, then select the top 10 stocks
position = combined_factor[all_filters].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)