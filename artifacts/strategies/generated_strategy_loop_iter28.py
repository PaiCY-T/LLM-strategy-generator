# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
foreign_strength = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
eps = data.get('financial_statement:每股盈餘')
rsi = data.indicator('RSI')

# 2. Calculate factors
# Factor 1: Short-term Momentum (10-day returns)
momentum = close.pct_change(10)
factor_momentum = momentum.shift(1)

# Factor 2: Foreign Investor Strength (5-day sum of strength)
# A positive sum indicates consistent foreign buying interest
foreign_strength_sum = foreign_strength.rolling(5).sum()
factor_foreign = foreign_strength_sum.shift(1)

# Factor 3: EPS Growth (Year-over-Year)
# Assuming EPS is reported quarterly, pct_change(4) calculates YoY growth
eps_growth = eps.pct_change(4)
factor_eps_growth = eps_growth.shift(1)

# Factor 4: RSI (Relative Strength Index)
# Higher RSI values (e.g., > 60) often indicate strong buying pressure or overbought conditions.
# We'll use it as a strength indicator.
factor_rsi = rsi.shift(1)

# 3. Combine factors
# Rank factors to normalize their scales before combining
ranked_momentum = factor_momentum.rank(axis=1, pct=True)
ranked_foreign = factor_foreign.rank(axis=1, pct=True)
ranked_eps_growth = factor_eps_growth.rank(axis=1, pct=True)
ranked_rsi = factor_rsi.rank(axis=1, pct=True)

# Combine factors with equal weights
combined_factor = (ranked_momentum + ranked_foreign + ranked_eps_growth + ranked_rsi) / 4

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be greater than 50 million TWD
avg_trading_value = trading_value.rolling(20).mean()
liquidity_filter = avg_trading_value.shift(1) > 50_000_000

# Price filter: Close price must be greater than 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
all_filters = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters to the combined factor and then select the top 8 stocks
position = combined_factor[all_filters].is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)