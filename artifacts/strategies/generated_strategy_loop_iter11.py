# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy_sell = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
eps = data.get('financial_statement:每股盈餘')

# 2. Calculate factors
# Momentum factor: 20-day returns
returns = close.pct_change(20).shift(1)

# Revenue Growth factor: Monthly Revenue YoY
# The monthly data will be forward-filled to daily, then shifted.
revenue_growth_factor = revenue_yoy.shift(1)

# Foreign Investor Flow factor: 5-day rolling sum of net buy/sell
foreign_flow_factor = foreign_net_buy_sell.rolling(5).sum().shift(1)

# EPS Growth factor: Year-over-year EPS change (using 4 quarters ago for comparison)
# Assuming EPS is quarterly, we compare current EPS with EPS from 4 quarters ago.
# We need to align EPS data to daily and then shift.
eps_growth = (eps.pct_change(4).shift(1)).fillna(0) # Fill NaN from pct_change initially

# 3. Combine factors
# Rank each factor across stocks for each day to normalize their scales (percentile rank 0-1)
rank_returns = returns.rank(axis=1, pct=True)
rank_revenue_growth = revenue_growth_factor.rank(axis=1, pct=True)
rank_foreign_flow = foreign_flow_factor.rank(axis=1, pct=True)
rank_eps_growth = eps_growth.rank(axis=1, pct=True)

# Combine ranked factors with weights
# Assigning weights based on perceived importance: momentum, growth, institutional flow.
combined_factor = (
    rank_returns * 0.35 +
    rank_revenue_growth * 0.25 +
    rank_eps_growth * 0.25 +
    rank_foreign_flow * 0.15
)

# 4. Apply filters
# Liquidity filter: 20-day average trading value > 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Exclude stocks with very low prices (e.g., below 10 TWD)
# Low price stocks can be highly volatile and illiquid.
price_filter = close.shift(1) > 10

# Combine all filters
all_filters = liquidity_filter & price_filter

# 5. Select stocks
# Select top 10 stocks based on the combined factor, applying all filters
position = combined_factor[all_filters].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)