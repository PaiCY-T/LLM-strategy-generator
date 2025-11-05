# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
foreign_strength = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
eps = data.get('financial_statement:每股盈餘')
rsi = data.indicator('RSI')

# 2. Calculate raw factors
# Momentum factor: 20-day returns
raw_momentum = close.pct_change(20)

# Foreign investor strength factor: higher strength is better
raw_foreign_strength = foreign_strength

# EPS growth factor: Year-over-Year growth (assuming EPS is quarterly)
raw_eps_growth = eps.pct_change(4)

# RSI factor: lower RSI indicates oversold or potential for mean reversion (higher factor value for lower RSI)
raw_rsi_factor = 100 - rsi

# 3. Shift factors to avoid look-ahead bias
momentum_factor = raw_momentum.shift(1)
foreign_strength_factor = raw_foreign_strength.shift(1)
eps_growth_factor = raw_eps_growth.shift(1)
rsi_factor = raw_rsi_factor.shift(1)

# 4. Rank factors to normalize their scales before combining
# Fill NaNs with 0 before ranking to ensure all stocks participate in ranking
momentum_rank = momentum_factor.fillna(0).rank(axis=1, pct=True)
foreign_strength_rank = foreign_strength_factor.fillna(0).rank(axis=1, pct=True)
eps_growth_rank = eps_growth_factor.fillna(0).rank(axis=1, pct=True)
rsi_rank = rsi_factor.fillna(0).rank(axis=1, pct=True)

# 5. Combine factors with weights
combined_factor = (momentum_rank * 0.35) + \
                  (foreign_strength_rank * 0.25) + \
                  (eps_growth_rank * 0.20) + \
                  (rsi_rank * 0.20)

# 6. Apply filters
# Liquidity filter: average trading value over 20 days must be greater than 50M TWD
avg_trading_value = trading_value.rolling(20).mean()
liquidity_filter = (avg_trading_value.shift(1) > 50_000_000)

# Price filter: close price must be greater than 10 TWD to avoid penny stocks
price_filter = (close.shift(1) > 10)

# Combine all filters
final_filter = liquidity_filter & price_filter

# 7. Select stocks
# Select the top 10 stocks based on the combined factor, applying the filters
position = combined_factor[final_filter].is_largest(10)

# 8. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)