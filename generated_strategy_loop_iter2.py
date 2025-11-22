# 1. Load data - ALWAYS use adjusted data for price!
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits
trading_value = data.get('price:成交金額')  # OK for liquidity filter
pe_ratio = data.get('price_earning_ratio:本益比')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
market_cap = data.get('etl:market_value')
mfi = data.indicator('MFI')
# 2. Calculate factors with .shift(1) to prevent look-ahead bias
# Factor 1: Inverse P/E Ratio (Value factor, prioritizing underused)
# Handle potential zero/negative P/E and cap extreme values
pe_ratio_shifted = pe_ratio.ffill().shift(1)
inverse_pe = (1 / pe_ratio_shifted).replace([float('inf'), -float('inf')], np.nan)
# Filter out P/E values that are too high or negative before ranking
inverse_pe = inverse_pe[(pe_ratio_shifted > 5) & (pe_ratio_shifted < 30)]
# Factor 2: Inverse P/B Ratio (Value factor, prioritizing underused)
# Handle potential zero/negative P/B and cap extreme values
pb_ratio_shifted = pb_ratio.ffill().shift(1)
inverse_pb = (1 / pb_ratio_shifted).replace([float('inf'), -float('inf')], np.nan)
# Filter out P/B values that are too high or negative before ranking
inverse_pb = inverse_pb[(pb_ratio_shifted > 0.5) & (pb_ratio_shifted < 3)]
# Factor 3: Money Flow Index (MFI) (Technical factor, less common than RSI/MACD)
mfi_shifted = mfi.shift(1)
# Factor 4: Inverse Market Cap (Size factor, prioritizing underused)
# Favors smaller companies for potential higher growth and less correlation
market_cap_shifted = market_cap.shift(1)
inverse_market_cap = (1 / market_cap_shifted).replace([float('inf'), -float('inf')], np.nan)
# Filter out extremely small market caps if needed, but for diversity, we'll keep it broad.
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
inverse_pe_rank = inverse_pe.rank(axis=1, pct=True)
inverse_pb_rank = inverse_pb.rank(axis=1, pct=True)
mfi_rank = mfi_shifted.rank(axis=1, pct=True)
inverse_market_cap_rank = inverse_market_cap.rank(axis=1, pct=True)
# Combine with weights. Prioritize value factors, then MFI, then inverse market cap.
combined_factor = (inverse_pe_rank * 0.35 +
                   inverse_pb_rank * 0.35 +
                   mfi_rank * 0.20 +
                   inverse_market_cap_rank * 0.10)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 40M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 40_000_000
# Price filter: Stock price > 15 TWD to avoid penny stocks
price_filter = close.shift(1) > 15
# MFI filter: Ensure positive money flow (MFI > 30)
mfi_positive_flow_filter = mfi_shifted > 30
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & mfi_positive_flow_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)