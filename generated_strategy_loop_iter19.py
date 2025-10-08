# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
invest_trust_net_buy = data.get('investment_trust_buy_sell_summary')
rsi = data.get('indicator:RSI')

# 2. Calculate factors

# Factor 1: Price Momentum (20-day returns)
momentum = close.pct_change(20)
momentum_factor = momentum.shift(1)
momentum_factor_ranked = momentum_factor.rank(axis=1, pct=True)

# Factor 2: Revenue Growth (YoY)
# Shift forward to ensure data is known before trading
revenue_growth_factor = revenue_yoy.shift(1)
# Rank to normalize its scale
revenue_growth_factor_ranked = revenue_growth_factor.rank(axis=1, pct=True)

# Factor 3: Investment Trust Net Buy (Ranked)
# Shift forward to ensure data is known before trading
invest_trust_factor = invest_trust_net_buy.shift(1)
# Rank to normalize its scale
invest_trust_factor_ranked = invest_trust_factor.rank(axis=1, pct=True)

# Factor 4: RSI Strength
# Shift forward to ensure data is known before trading
rsi_factor = rsi.shift(1)
# Scale RSI (0-100) to (0-1) for combination
rsi_factor_scaled = rsi_factor / 100

# 3. Combine factors with weights
# Assigning weights to each ranked/scaled factor
combined_factor = (
    momentum_factor_ranked * 0.35 +
    revenue_growth_factor_ranked * 0.25 +
    invest_trust_factor_ranked * 0.25 +
    rsi_factor_scaled * 0.15
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be above 10 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 10_000_000

# Price filter: Stock price must be above 10 TWD
price_filter = close.shift(1) > 10

# Combine all filters
overall_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters and select the top 10 stocks based on the combined factor
position = combined_factor[overall_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)