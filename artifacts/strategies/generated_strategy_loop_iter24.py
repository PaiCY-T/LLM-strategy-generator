# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
pe_ratio = data.get('price_earning_ratio:本益比')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy_sell = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')

# 2. Calculate factors
# Factor 1: Short-term Momentum (20-day returns)
momentum = close.pct_change(20).shift(1)

# Factor 2: Inverse P/E Ratio (Value)
# Handle potential division by zero or negative P/E by replacing inf/-inf with NaN
inverse_pe = (1 / pe_ratio).replace([float('inf'), -float('inf')], float('nan')).shift(1)
# Fill NaN values with 0, effectively giving stocks with invalid P/E a low score
inverse_pe = inverse_pe.fillna(0)

# Factor 3: Monthly Revenue YoY Growth
growth = revenue_yoy.shift(1)

# Factor 4: Foreign Investor Net Buying (5-day average)
foreign_flow = foreign_net_buy_sell.rolling(5).mean().shift(1)

# 3. Combine factors
# Rank each factor across stocks for each day (higher rank is better)
# Using pct=True to normalize ranks between 0 and 1
ranked_momentum = momentum.rank(axis=1, pct=True)
ranked_inverse_pe = inverse_pe.rank(axis=1, pct=True)
ranked_growth = growth.rank(axis=1, pct=True)
ranked_foreign_flow = foreign_flow.rank(axis=1, pct=True)

# Combine ranks into a composite score with weighted averages
# Weights: Momentum (0.3), Value (0.2), Growth (0.3), Foreign Flow (0.2)
composite_score = (
    ranked_momentum * 0.3 +
    ranked_inverse_pe * 0.2 +
    ranked_growth * 0.3 +
    ranked_foreign_flow * 0.2
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be greater than 30 million TWD
liquidity_filter = (trading_value.rolling(20).mean().shift(1) > 30_000_000)

# Price filter: Only consider stocks with a close price greater than 10 TWD to avoid penny stocks
price_filter = (close.shift(1) > 10)

# Combine all filters
combined_filter = liquidity_filter & price_filter

# Apply filters to the composite score
filtered_score = composite_score[combined_filter]

# 5. Select stocks
# Select the top 8 stocks based on the filtered composite score
position = filtered_score.is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)