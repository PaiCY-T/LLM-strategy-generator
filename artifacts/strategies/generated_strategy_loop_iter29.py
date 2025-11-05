# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
three_forces = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')

# 2. Calculate factors
# Factor 1: 20-day Momentum
# We want to identify stocks with recent upward price movement.
momentum = close.pct_change(20)

# Factor 2: Monthly Revenue YoY Growth
# Strong revenue growth indicates fundamental strength.
# revenue_yoy is already a percentage change.

# Factor 3: Three Main Forces Net Buy/Sell
# Positive institutional flow suggests smart money accumulation.
# three_forces is already a net volume.

# To combine factors robustly, we rank them across all stocks for each day.
# Higher rank means better performance for that factor.
momentum_rank = momentum.rank(axis=1, pct=True)
revenue_rank = revenue_yoy.rank(axis=1, pct=True)
institutional_rank = three_forces.rank(axis=1, pct=True)

# Combine ranked factors by summing them.
# Shift the combined factor forward by one day to prevent look-ahead bias.
combined_factor = (momentum_rank + revenue_rank + institutional_rank).shift(1)

# 3. Apply filters
# Filter 1: Liquidity filter
# Ensure sufficient trading volume for easy entry/exit.
# Average daily trading value over 20 days must be greater than 10 million TWD.
avg_trading_value = trading_value.rolling(20).mean()
liquidity_filter = (avg_trading_value > 10_000_000).shift(1)

# Filter 2: Price filter
# Exclude very low-priced stocks, which can be volatile or distressed.
# Stock price must be greater than 10 TWD.
price_filter = (close > 10).shift(1)

# Filter 3: RSI filter (avoiding overbought conditions)
# Ensure stocks are not excessively overbought (RSI < 70).
rsi_filter = (rsi < 70).shift(1)

# Combine all filters
all_filters = liquidity_filter & price_filter & rsi_filter

# 4. Select stocks
# Apply all filters to the combined factor and then select the top 10 stocks
# based on the highest combined factor score.
position = combined_factor[all_filters].is_largest(10)

# 5. Run backtest
# Set resampling to quarterly ('Q') and a stop-loss of 8%.
report = sim(position, resample="Q", upload=False, stop_loss=0.08)