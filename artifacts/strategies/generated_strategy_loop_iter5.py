# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
investment_trust_net_buy = data.get('institutional_investors_trading_summary:投信買賣超股數')
rsi = data.indicator('RSI', timeperiod=14)

# 2. Calculate factors
# Momentum factor: 20-day percentage change
momentum = close.pct_change(20).shift(1)

# Revenue growth factor: Monthly revenue YoY growth
# Fill NaN with 0 to ensure ranking works for new companies or missing data
rev_growth = revenue_yoy.shift(1).fillna(0)

# Investment Trust Flow factor: 5-day rolling sum of net buy/sell
# A positive value indicates institutional buying interest
it_flow = investment_trust_net_buy.rolling(5).sum().shift(1).fillna(0)

# Contrarian RSI factor: Lower RSI (oversold) is better.
# We use (100 - RSI) so higher values indicate more oversold conditions.
contrarian_rsi = (100 - rsi).shift(1)

# 3. Combine factors
# Rank each factor to normalize their contributions
ranked_momentum = momentum.rank(axis=1, pct=True)
ranked_rev_growth = rev_growth.rank(axis=1, pct=True)
ranked_it_flow = it_flow.rank(axis=1, pct=True)
ranked_contrarian_rsi = contrarian_rsi.rank(axis=1, pct=True)

# Combine ranked factors with weights
# Weights: Momentum (0.2), Revenue Growth (0.3), Institutional Flow (0.3), Contrarian RSI (0.2)
combined_factor = (
    ranked_momentum * 0.2 +
    ranked_rev_growth * 0.3 +
    ranked_it_flow * 0.3 +
    ranked_contrarian_rsi * 0.2
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be > 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Stock price must be greater than 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
all_filters = liquidity_filter & price_filter

# 5. Select stocks
# Select the top 10 stocks based on the combined factor, applying all filters
position = combined_factor[all_filters].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)