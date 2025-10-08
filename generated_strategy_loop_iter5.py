# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
rsi = data.get('indicator:RSI')
foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')

# 2. Calculate factors
# Factor 1: Price Momentum (60-day return)
price_momentum = close.pct_change(60).shift(1)

# Factor 2: Monthly Revenue YoY Growth
# Revenue data is monthly, use ffill to carry forward the last available monthly value.
revenue_growth_factor = revenue_yoy.ffill().shift(1)

# Factor 3: RSI Strength
# Higher RSI generally indicates stronger momentum.
rsi_factor = rsi.shift(1)

# Factor 4: Foreign Investor Buying Strength
# Higher strength indicates more foreign buying.
foreign_strength_factor = foreign_strength.shift(1)

# 3. Combine factors
# Rank each factor and sum the ranks to create a composite score.
# Ensure all factors are 'higher is better' before ranking.
# Handle potential NaNs before ranking by filling with a neutral value or letting rank handle it.
# Using pct=True for percentile ranks.
combined_factor = (
    price_momentum.rank(axis=1, pct=True) +
    revenue_growth_factor.rank(axis=1, pct=True) +
    rsi_factor.rank(axis=1, pct=True) +
    foreign_strength_factor.rank(axis=1, pct=True)
)

# 4. Apply filters
# Liquidity filter: Average trading value over 20 days > 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Close price > 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
all_filters = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters to the combined factor and select the top 9 stocks.
position = combined_factor[all_filters].is_largest(9)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)