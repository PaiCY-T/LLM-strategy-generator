# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
eps = data.get('fundamental_features:EPS')
foreign_net_buy = data.get('foreign_main_force_buy_sell_summary')

# 2. Calculate factors

# Factor 1: 20-day Momentum
# Calculate the percentage change over the last 20 trading days.
returns_20d = close.pct_change(20)
momentum_factor = returns_20d.shift(1)

# Factor 2: Monthly Revenue YoY Growth
# This dataset already provides the year-over-year growth rate for monthly revenue.
# Finlab handles the alignment of monthly data to daily timestamps by forward-filling.
revenue_growth_factor = revenue_yoy.shift(1)

# Factor 3: EPS Growth (Trailing 4 quarters)
# Assuming EPS is reported quarterly, pct_change(4) calculates the year-over-year growth for EPS.
eps_growth = eps.pct_change(4)
eps_growth_factor = eps_growth.shift(1)

# Factor 4: Foreign Investor Net Buy (5-day average)
# Calculate the 5-day moving average of net buying by foreign investors.
# A positive value indicates net buying, suggesting institutional interest.
foreign_flow_factor = foreign_net_buy.rolling(5).mean().shift(1)

# 3. Combine factors
# Rank factors to normalize their scales and reduce the impact of extreme outliers.
# Ranking by percentile (pct=True) ensures values are between 0 and 1.
rank_momentum = momentum_factor.rank(axis=1, pct=True)
rank_revenue = revenue_growth_factor.rank(axis=1, pct=True)
rank_eps = eps_growth_factor.rank(axis=1, pct=True)
rank_foreign_flow = foreign_flow_factor.rank(axis=1, pct=True)

# Combine the ranked factors with specific weights.
# Higher weights are given to momentum and revenue growth, which are often strong drivers.
# Foreign investor flow is also critical in the Taiwan market.
combined_factor = (
    rank_momentum * 0.35 +
    rank_revenue * 0.25 +
    rank_eps * 0.20 +
    rank_foreign_flow * 0.20
)

# 4. Apply filters

# Liquidity filter: Ensure sufficient trading volume.
# Average daily trading value over the last 20 days must be above 50 million TWD.
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Exclude very low-priced stocks (penny stocks) which can be volatile.
# Stock price must be above 10 TWD.
price_filter = close.shift(1) > 10

# Combine all filters. A stock must pass both liquidity and price criteria.
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Select the top 10 stocks that have the highest combined factor score
# after applying the liquidity and price filters.
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
# Execute the backtest with quarterly rebalancing and a 8% stop-loss.
report = sim(position, resample="Q", upload=False, stop_loss=0.08)