# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
eps = data.get('financial_statement:每股盈餘')
rsi = data.indicator('RSI')

# 2. Calculate factors
# Factor 1: Medium-term Momentum (60-day percentage change)
momentum = close.pct_change(60)
momentum = momentum.shift(1)

# Factor 2: Monthly Revenue YoY Growth
# This dataset already provides YoY growth, so we use it directly.
revenue_growth_factor = revenue_yoy.shift(1)

# Factor 3: EPS Growth (Year-over-Year, assuming quarterly EPS)
# Compares current EPS with EPS from 4 quarters ago.
eps_growth = eps.pct_change(4)
eps_growth = eps_growth.shift(1)

# Factor 4: Inverse RSI (Lower RSI values indicate oversold, which can be a buy signal)
# We want to rank stocks with lower RSI higher, so we use 100 - RSI.
inverse_rsi = 100 - rsi
inverse_rsi = inverse_rsi.shift(1)

# 3. Combine factors
# We combine the factors with weights. Higher weights for fundamental growth and momentum.
# Fill NaN values with 0 for combination, as they represent missing data for the factor.
combined_factor = (
    momentum.fillna(0) * 0.35 +
    revenue_growth_factor.fillna(0) * 0.30 +
    eps_growth.fillna(0) * 0.25 +
    inverse_rsi.fillna(0) * 0.10
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be greater than 50 million TWD.
liquidity_filter = trading_value.rolling(20).mean() > 50_000_000
liquidity_filter = liquidity_filter.shift(1)

# Price filter: Average close price over 20 days must be greater than 10 TWD to avoid penny stocks.
price_filter = close.rolling(20).mean() > 10
price_filter = price_filter.shift(1)

# Combine all filters
all_filters = liquidity_filter & price_filter

# 5. Select stocks
# Apply the combined filters to the combined factor.
# Then, select the top 10 stocks based on the filtered factor.
filtered_factor = combined_factor[all_filters]
position = filtered_factor.is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)