# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
rsi = data.get('indicator:RSI')
three_main_forces_net_buy_sell = data.get('three_main_forces_buy_sell_summary')

# 2. Calculate factors
# Factor 1: Price Momentum (20-day returns)
returns_20d = close.pct_change(20)
factor_momentum = returns_20d.shift(1)

# Factor 2: Monthly Revenue Growth YoY
# Higher revenue growth is generally positive
factor_revenue_growth = revenue_yoy.shift(1)

# Factor 3: RSI Momentum
# Higher RSI (e.g., > 50) indicates stronger buying pressure/momentum
factor_rsi = rsi.shift(1)

# Factor 4: Institutional Buying Strength
# Sum of net buy/sell from foreign investors, investment trusts, and dealers
factor_institutional_flow = three_main_forces_net_buy_sell.shift(1)

# 3. Combine factors
# Normalize factors using rank (percentile rank) to ensure they have similar scales
ranked_momentum = factor_momentum.rank(axis=1, pct=True)
ranked_revenue = factor_revenue_growth.rank(axis=1, pct=True)
ranked_rsi = factor_rsi.rank(axis=1, pct=True)
ranked_institutional = factor_institutional_flow.rank(axis=1, pct=True)

# Combine ranked factors with weighted average
# Assigning weights based on perceived importance
combined_factor = (
    ranked_momentum * 0.35 +
    ranked_revenue * 0.15 +
    ranked_rsi * 0.25 +
    ranked_institutional * 0.25
)

# 4. Apply filters
# Liquidity filter: Average trading value over the past 20 days must be above 50 million TWD
avg_trading_value = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value > 50_000_000

# Price filter: Filter out stocks with a close price below 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Select the top 10 stocks based on the combined factor after applying filters
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)