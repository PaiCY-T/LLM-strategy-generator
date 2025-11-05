# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
pe_ratio = data.get('price_earning_ratio:本益比')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
rsi = data.indicator('RSI')

# 2. Calculate factors (all shifted by 1 to avoid look-ahead bias)
# Momentum Factor: Higher 20-day return is considered better
momentum = close.pct_change(20).shift(1)

# Value Factor: Lower P/E ratio is considered better. We use negative P/E for ranking
# so that lower P/E values get a higher rank.
value_factor = (-pe_ratio).shift(1)

# Growth Factor: Higher Monthly Revenue YoY growth is considered better
growth_factor = revenue_yoy.shift(1)

# 3. Combine factors using ranks
# Rank each factor across all stocks for each day
momentum_rank = momentum.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
growth_rank = growth_factor.rank(axis=1, pct=True)

# Sum the ranks to create a combined score. Higher sum indicates a better stock.
combined_factor = (momentum_rank + value_rank + growth_rank)

# 4. Apply filters (all shifted by 1 to avoid look-ahead bias)
# Liquidity Filter: Average daily trading value over 20 days must be above 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# P/E Ratio Filter: P/E ratio must be between 5 and 50 (inclusive)
# This filters out extremely cheap (potentially distressed) and extremely expensive stocks.
pe_filter = (pe_ratio.shift(1) >= 5) & (pe_ratio.shift(1) <= 50)

# Price Filter: Stock price must be above 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# RSI Filter: RSI must be below 70 to avoid extremely overbought conditions
rsi_filter = rsi.shift(1) < 70

# Combine all filters
total_filter = liquidity_filter & pe_filter & price_filter & rsi_filter

# 5. Select stocks
# Apply the combined filter to the combined factor and select the top 10 stocks
# with the highest combined factor score.
position = combined_factor[total_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)