# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
pe_ratio = data.get('price_earning_ratio:本益比')
foreign_net_buy_sell = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')

# 2. Calculate factors

# Factor 1: Momentum (20-day returns)
# Calculate 20-day percentage change in close price
momentum = close.pct_change(20).shift(1)

# Factor 2: Valuation (Inverse P/E ratio)
# Cap P/E ratio to a reasonable range (e.g., 5 to 50) to avoid extreme outliers
# and handle negative P/E (loss-making companies) by setting a floor.
pe_ratio_capped = pe_ratio.mask(pe_ratio > 50, 50).mask(pe_ratio < 5, 5)
# Calculate inverse P/E; higher value means lower P/E (better for value)
inverse_pe = (1 / pe_ratio_capped).shift(1)

# Factor 3: Foreign Investor Net Buying Flow
# Calculate the sum of foreign investor net buy/sell over the last 5 days
foreign_flow = foreign_net_buy_sell.rolling(5).sum().shift(1)

# 3. Combine factors
# To combine factors with different scales, we rank them percentile-wise (0-1).
# Higher ranks are generally better for all chosen factors.
rank_momentum = momentum.rank(axis=1, pct=True)
rank_inverse_pe = inverse_pe.rank(axis=1, pct=True)
rank_foreign_flow = foreign_flow.rank(axis=1, pct=True)

# Combine the ranked factors by averaging them.
combined_factor = (rank_momentum + rank_inverse_pe + rank_foreign_flow) / 3

# 4. Apply filters

# Liquidity filter: Average daily trading value over the last 20 days must be above 50 million TWD.
avg_trading_value = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value > 50_000_000

# Ensure all factor components are not NaN for a valid score.
valid_factors_data = momentum.notna() & inverse_pe.notna() & foreign_flow.notna()

# 5. Select stocks
# Apply all filters to the combined factor.
filtered_factor = combined_factor[liquidity_filter & valid_factors_data]

# Select the top 8 stocks based on the combined factor score.
position = filtered_factor.is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)