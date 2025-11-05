# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
rsi = data.indicator('RSI')
eps = data.get('financial_statement:每股盈餘')

# 2. Calculate factors
# Factor 1: Short-term Reversal (Negative 5-day momentum)
# We want to buy stocks that have recently underperformed.
returns_5d = close.pct_change(5)
factor_reversal = (-returns_5d).shift(1)

# Factor 2: Revenue Growth (Monthly Revenue YoY)
# Higher YoY growth is generally positive.
factor_growth = revenue_yoy.shift(1)

# Factor 3: RSI (Oversold indicator)
# We want to identify stocks that might be oversold (low RSI).
# (100 - RSI) will be higher for stocks with lower RSI values.
factor_rsi_oversold = (100 - rsi).shift(1)

# Factor 4: EPS (Earnings Per Share)
# A basic measure of profitability.
factor_eps = eps.shift(1)

# 3. Combine factors
# Combine factors with a weighted average.
# Give more weight to growth and short-term reversal,
# and less to RSI and EPS to balance the strategy.
combined_factor = (
    factor_reversal * 0.35 +
    factor_growth * 0.35 +
    factor_rsi_oversold * 0.15 +
    factor_eps * 0.15
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be above 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Stock price must be above 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
all_filters = liquidity_filter & price_filter

# 5. Select stocks
# Apply the combined filters to the factor and select the top 10 stocks
position = combined_factor[all_filters].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)