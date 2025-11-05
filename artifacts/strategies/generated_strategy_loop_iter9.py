# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
eps = data.get('financial_statement:每股盈餘')
rsi = data.indicator('RSI')

# 2. Calculate factors
# Factor 1: 20-day price momentum
returns_20d = close.pct_change(20)
factor_momentum = returns_20d.shift(1)

# Factor 2: Monthly Revenue Year-over-Year growth
# This dataset is already a growth rate, so we just shift it.
factor_revenue_growth = revenue_yoy.shift(1)

# Factor 3: Annual EPS Growth (assuming EPS is reported quarterly, 4 periods = 1 year)
eps_growth_annual = eps.pct_change(4)
factor_eps_growth = eps_growth_annual.shift(1)

# Factor 4: Inverse RSI for mean reversion (buy oversold)
# Lower RSI (e.g., below 30) indicates oversold. By using (100 - RSI),
# higher values will correspond to more oversold conditions, which we want to rank higher.
factor_rsi_inverse = (100 - rsi).shift(1)

# 3. Combine factors
# Assign weights to the factors.
# We prioritize growth and momentum, with a component for mean reversion.
combined_factor = (
    factor_momentum * 0.35 +
    factor_revenue_growth * 0.30 +
    factor_eps_growth * 0.20 +
    factor_rsi_inverse * 0.15
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over the past 20 days must be > 50 million TWD
# Shift trading_value by 1 day before calculating rolling mean to avoid look-ahead bias
avg_trading_value_20d = trading_value.shift(1).rolling(20).mean()
liquidity_filter = avg_trading_value_20d > 50_000_000

# Price filter: Stock price must be above 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
all_filters = liquidity_filter & price_filter

# 5. Select stocks
# Apply the filters to the combined factor and then select the top 10 stocks
# (between 6 and 12 stocks as per requirements)
position = combined_factor[all_filters].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)