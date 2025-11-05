# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
foreign_strength = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
eps = data.get('financial_statement:每股盈餘')
rsi = data.indicator('RSI')

# 2. Calculate factors
# Factor 1: Price Momentum (20-day returns)
returns_20d = close.pct_change(20)
# Rank and shift to avoid look-ahead bias
factor_momentum = returns_20d.rank(axis=1, pct=True).shift(1)

# Factor 2: Foreign Investor Buying Strength
# Higher strength indicates more foreign buying, which is generally positive.
# Rank and shift
factor_foreign_strength = foreign_strength.rank(axis=1, pct=True).shift(1)

# Factor 3: EPS (Earnings Per Share)
# Higher EPS indicates better fundamental performance.
# Rank and shift
factor_eps = eps.rank(axis=1, pct=True).shift(1)

# Factor 4: Relative Strength Index (RSI)
# We want to select stocks with healthy momentum but not extremely overbought.
# Ranking RSI will give a relative measure of its level.
# Rank and shift
factor_rsi = rsi.rank(axis=1, pct=True).shift(1)

# 3. Combine factors
# Assign weights to each factor. All factors are positively correlated with desired outcome.
combined_factor = (
    factor_momentum * 0.35 +
    factor_foreign_strength * 0.30 +
    factor_eps * 0.20 +
    factor_rsi * 0.15
)

# 4. Apply filters
# Filter 1: Liquidity filter - Average daily trading value over 20 days must be above 50 million TWD.
avg_trading_value_20d = trading_value.rolling(20).mean()
liquidity_filter = (avg_trading_value_20d > 50_000_000).shift(1) # Shift the filter itself

# Filter 2: Price filter - Stock price must be above 10 TWD to avoid penny stocks.
price_filter = (close > 10).shift(1) # Shift the filter itself

# Combine all filters
all_filters = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters to the combined factor, then select the top 10 stocks.
position = combined_factor[all_filters].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)