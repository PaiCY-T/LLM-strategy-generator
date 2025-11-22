# 1. Load data
close = data.get('etl:adj_close')  # ✅ Use adjusted data for price filter
trading_value = data.get('price:成交金額')  # OK for liquidity filter
pb_ratio = data.get('price_earning_ratio:股價淨值比')  # Underused: Price-to-Book Ratio
pe_ratio = data.get('price_earning_ratio:本益比')  # Underused: Price-to-Earnings Ratio
market_cap = data.get('etl:market_value')  # Underused: Market Capitalization
bvps = data.get('fundamental_features:每股淨值')  # Underused: Book Value Per Share
# 2. Calculate factors
# Factor 1: Inverse Price-to-Book Ratio (Value)
# Lower P/B is better, so take inverse. Forward fill and shift to avoid look-ahead.
inverse_pb = (1 / pb_ratio).ffill().shift(1)
# Factor 2: Inverse Price-to-Earnings Ratio (Value/Earnings Yield)
# Lower P/E is better, so take inverse. Forward fill and shift to avoid look-ahead.
inverse_pe = (1 / pe_ratio).ffill().shift(1)
# Factor 3: Small Market Cap (Size)
# Smaller market cap is better, so take inverse. Shift to avoid look-ahead.
small_cap = (1 / market_cap).shift(1)
# Factor 4: Book Value Per Share (Quality/Value)
# Higher BVPS is better. Forward fill and shift to avoid look-ahead.
bvps_factor = bvps.ffill().shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
inverse_pb_rank = inverse_pb.rank(axis=1, pct=True)
inverse_pe_rank = inverse_pe.rank(axis=1, pct=True)
small_cap_rank = small_cap.rank(axis=1, pct=True)
bvps_rank = bvps_factor.rank(axis=1, pct=True)
# Combine with weights. Prioritize value factors (P/B, P/E) and then size and BVPS.
combined_factor = (inverse_pb_rank * 0.30 +
                   inverse_pe_rank * 0.30 +
                   small_cap_rank * 0.20 +
                   bvps_rank * 0.20)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 40M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 40_000_000
# Price filter: Stock price > 15 TWD to avoid penny stocks
price_filter = close.shift(1) > 15
# Market Cap filter: Target small to mid-cap stocks (1B to 50B TWD)
market_cap_filter = (market_cap.shift(1) > 1_000_000_000) & \
                    (market_cap.shift(1) < 50_000_000_000)
# P/B Ratio filter: Avoid extremely high P/B (e.g., > 3) and negative P/B
pb_filter = (pb_ratio.ffill().shift(1) > 0.1) & (pb_ratio.ffill().shift(1) < 3)
# P/E Ratio filter: Avoid negative P/E (loss-making) and extremely high P/E (e.g., > 30)
pe_filter = (pe_ratio.ffill().shift(1) > 5) & (pe_ratio.ffill().shift(1) < 30)
# Apply all filters to the combined factor
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & pb_filter & pe_filter]
# 5. Select stocks
# Select the top 10 stocks based on the filtered combined factor
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)