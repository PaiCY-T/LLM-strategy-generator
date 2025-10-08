# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy_sell = data.get('foreign_main_force_buy_sell_summary')
market_value = data.get('market_value')
rsi = data.get('indicator:RSI')

# 2. Calculate factors
# Factor 1: Short-term Momentum (10-day returns)
momentum_factor = close.pct_change(10).shift(1)

# Factor 2: Revenue Growth (YoY)
# Revenue YoY is already a growth rate, shift it directly
revenue_growth_factor = revenue_yoy.shift(1)

# Factor 3: Foreign Investor Net Buy/Sell relative to Market Value
# Normalize foreign net buy/sell by market value to account for company size
# Add a small epsilon to market_value to avoid division by zero
epsilon = 1e-9
foreign_flow_factor = (foreign_net_buy_sell / (market_value + epsilon)).shift(1)

# Factor 4: RSI (Higher RSI indicates stronger momentum)
rsi_factor = rsi.shift(1)

# 3. Combine factors
# Rank each factor to normalize them between 0 and 1
ranked_momentum = momentum_factor.rank(axis=1, pct=True)
ranked_revenue_growth = revenue_growth_factor.rank(axis=1, pct=True)
ranked_foreign_flow = foreign_flow_factor.rank(axis=1, pct=True)
ranked_rsi = rsi_factor.rank(axis=1, pct=True)

# Combine factors with weights. Higher values are generally better for these factors.
# Assign weights based on perceived importance.
combined_factor = (
    ranked_momentum * 0.35 +
    ranked_revenue_growth * 0.30 +
    ranked_foreign_flow * 0.20 +
    ranked_rsi * 0.15
)

# 4. Apply filters
# Filter 1: Liquidity filter (average daily trading value over 20 days > 50M TWD)
liquidity_filter = (trading_value.rolling(20).mean().shift(1) > 50_000_000)

# Filter 2: Price filter (stock price > 20 TWD to avoid very low-priced stocks)
price_filter = (close.shift(1) > 20)

# Combine all filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters and select the top 10 stocks based on the combined factor
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)