# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
trading_value = data.get('price:成交金額')
eps = data.get('fundamental_features:EPS')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
rsi = data.get('indicator:RSI')

# 2. Calculate factors
# Factor 1: EPS Rank (higher EPS is better)
# We use a 4-quarter average for EPS to smooth out quarterly fluctuations
eps_avg = eps.rolling(4, min_periods=1).mean()
factor_eps = eps_avg.rank(axis=1, pct=True).shift(1)

# Factor 2: Revenue YoY Growth Rank (higher growth is better)
factor_revenue_growth = revenue_yoy.rank(axis=1, pct=True).shift(1)

# Factor 3: RSI (Inverse Rank - lower RSI is better for potential rebound, avoiding overbought)
# We want stocks that are not extremely overbought, so a lower RSI is preferred.
# (100 - RSI) makes lower RSI values result in higher factor values.
factor_rsi = (100 - rsi).rank(axis=1, pct=True).shift(1)

# 3. Combine factors
# Assign weights to the factors.
# Emphasize fundamental strength (EPS, Revenue Growth) and a balanced RSI.
combined_factor = (
    factor_eps * 0.4 +
    factor_revenue_growth * 0.4 +
    factor_rsi * 0.2
)

# 4. Apply filters
# Filter 1: Liquidity filter - average daily trading value over 20 days must be above 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Filter 2: Price filter - ensure price is above a certain threshold to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
total_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply the combined filter to the factor and select the top 8 stocks
position = combined_factor[total_filter].is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)