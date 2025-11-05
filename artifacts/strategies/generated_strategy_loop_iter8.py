# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
foreign_strength = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
eps = data.get('financial_statement:每股盈餘')
rsi = data.indicator('RSI')

# 2. Calculate factors
# Factor 1: Short-term Momentum (20-day returns)
# Higher returns indicate stronger momentum
momentum_factor = close.pct_change(20).shift(1)

# Factor 2: Foreign Investor Buying Strength (smoothed)
# Smooth foreign strength over 5 days to reduce noise and capture trend
# Higher strength indicates more institutional buying interest
foreign_strength_factor = foreign_strength.rolling(5).mean().shift(1)

# Factor 3: EPS Growth (Year-over-Year)
# Calculate EPS growth over 4 quarters (assuming quarterly EPS data)
# Clip extreme growth values to prevent outliers from dominating the factor
eps_growth_raw = eps.pct_change(4)
eps_growth_factor = eps_growth_raw.clip(lower=-0.5, upper=1.0).shift(1) # Clip between -50% and +100% growth

# Factor 4: RSI (Relative Strength Index)
# RSI values typically range from 0-100. Higher values (e.g., > 50) indicate stronger buying pressure/momentum.
rsi_factor = rsi.shift(1)

# 3. Combine factors
# Fill NaN values for factors: 0 for momentum, foreign strength, and EPS growth (no signal)
# 50 for RSI (neutral value)
momentum_factor = momentum_factor.fillna(0)
foreign_strength_factor = foreign_strength_factor.fillna(0)
eps_growth_factor = eps_growth_factor.fillna(0)
rsi_factor = rsi_factor.fillna(50)

# Combine factors using a weighted sum.
# Scale RSI to be in a similar range (0-1) as other percentage-based factors.
combined_factor = (
    momentum_factor * 0.4 +
    foreign_strength_factor * 0.3 +
    eps_growth_factor * 0.2 +
    (rsi_factor / 100) * 0.1
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be greater than 50 million TWD
avg_trading_value = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value > 50_000_000

# Price filter: Stock price must be greater than 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
all_filters = liquidity_filter & price_filter

# 5. Select stocks
# Apply the combined filters to the factor and select the top 8 stocks with the highest factor values
position = combined_factor[all_filters].is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)