# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
eps = data.get('fundamental_features:EPS')
pe_ratio = data.get('price_earning_ratio:本益比')
foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')
rsi = data.get('indicator:RSI')

# 2. Calculate factors

# Factor 1: Value/Growth Factor (EPS and P/E ratio)
# Rank EPS (higher is better) and P/E (lower is better)
eps_rank = eps.rank(axis=1, pct=True)
pe_rank = pe_ratio.rank(axis=1, pct=True, ascending=False)
factor_value_growth = (eps_rank + pe_rank) / 2
factor_value_growth = factor_value_growth.shift(1)

# Factor 2: Foreign Investor Buying Strength
# Rank foreign investor buying strength (higher is better)
factor_foreign_strength = foreign_strength.rank(axis=1, pct=True)
factor_foreign_strength = factor_foreign_strength.shift(1)

# Factor 3: RSI Momentum Factor
# Calculate the change in RSI over 5 days to capture momentum
rsi_momentum = rsi.diff(5)
factor_rsi_momentum = rsi_momentum.rank(axis=1, pct=True)
factor_rsi_momentum = factor_rsi_momentum.shift(1)

# 3. Combine factors
# Assign weights to each factor
combined_factor = (
    factor_value_growth * 0.4 +
    factor_foreign_strength * 0.3 +
    factor_rsi_momentum * 0.3
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be above 10 million NTD
avg_trading_value = trading_value.rolling(20).mean()
liquidity_filter = avg_trading_value > 10_000_000

# Price filter: Stock price must be above 10 NTD to avoid penny stocks
price_filter = close > 10

# Combine all filters
total_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters and select the top 10 stocks based on the combined factor
position = combined_factor[total_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)