# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
pe_ratio = data.get('price_earning_ratio:本益比')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')

# 2. Calculate factors

# Factor 1: Momentum (60-day returns)
# Calculate 60-day percentage change in close price and shift by 1 to avoid look-ahead bias.
momentum = close.pct_change(60).shift(1)

# Factor 2: Value (Inverse P/E ratio)
# Calculate inverse P/E. Handle division by zero (inf), negative P/E (negative earnings),
# and cap extreme values to prevent a single stock from dominating the factor.
pe_factor = (1 / pe_ratio).replace([float('inf'), -float('inf')], float('nan'))
pe_factor = pe_factor.mask(pe_factor < 0, float('nan')) # Filter out stocks with negative P/E (negative earnings)
pe_factor = pe_factor.clip(upper=0.2) # Cap inverse P/E at 0.2 (equivalent to P/E of 5). This gives more weight to lower P/E stocks.
pe_factor = pe_factor.shift(1) # Shift by 1 to avoid look-ahead bias.

# Factor 3: Foreign Investor Net Buying Flow (5-day average)
# Calculate the 5-day rolling average of foreign investor net buying/selling volume.
foreign_flow = foreign_net_buy.rolling(5).mean().shift(1) # Shift by 1 to avoid look-ahead bias.

# 3. Combine factors
# Sum the normalized factors. Stocks with NaN in any factor will have a NaN combined factor,
# effectively excluding them from selection.
combined_factor = momentum + pe_factor + foreign_flow

# 4. Apply filters
# Liquidity filter: Ensure average daily trading value over the past 20 days is above 50 million TWD.
# Shift by 1 to ensure the filter is based on past data.
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# 5. Select stocks
# Apply the liquidity filter to the combined factor, then select the top 8 stocks
# with the highest combined factor score.
position = combined_factor[liquidity_filter].is_largest(8)

# 6. Run backtest
# Execute the backtest with quarterly rebalancing and a 8% stop-loss.
report = sim(position, resample="Q", upload=False, stop_loss=0.08)