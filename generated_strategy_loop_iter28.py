# 1. Load data
close = data.get('etl:adj_close')  # Adjusted for dividends/splits, used for filters
trading_value = data.get('price:成交金額')  # Used for liquidity filter
market_value = data.get('etl:market_value')  # Used for market cap filter
monthly_revenue_yoy = data.get('monthly_revenue:去年同月增減(%)') # Underused factor: Monthly Revenue YoY Growth
book_value_per_share = data.get('fundamental_features:每股淨值') # Underused factor: Book Value Per Share
foreign_strength = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)') # Less common institutional factor: Foreign Buying Strength
mfi = data.indicator('MFI') # Less common technical indicator: Money Flow Index
# 2. Calculate factors
# Factor 1: Monthly Revenue Growth Momentum (MRGM)
# Captures short-term fundamental growth, forward-fill and shift to avoid look-ahead
mrgm_factor = monthly_revenue_yoy.ffill().shift(1)
# Factor 2: Book Value Growth (BVG)
# Captures fundamental quality/value growth over 4 quarters, forward-fill and shift
book_value_per_share_ffill = book_value_per_share.ffill()
bvg_factor = book_value_per_share_ffill.pct_change(4).shift(1)
# Factor 3: Foreign Buying Strength (FBS)
# Captures institutional conviction and smart money flow, forward-fill and shift
fbs_factor = foreign_strength.ffill().shift(1)
# Factor 4: Money Flow Index (MFI)
# Captures buying/selling pressure based on price and volume, shifted
mfi_factor = mfi.shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
mrgm_rank = mrgm_factor.rank(axis=1, pct=True)
bvg_rank = bvg_factor.rank(axis=1, pct=True)
fbs_rank = fbs_factor.rank(axis=1, pct=True)
mfi_rank = mfi_factor.rank(axis=1, pct=True)
# Combine with diverse weights, emphasizing underused fundamental and institutional factors
combined_factor = (mrgm_rank * 0.30 +
                   bvg_rank * 0.25 +
                   fbs_rank * 0.25 +
                   mfi_rank * 0.20)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Stock price > 20 TWD to avoid penny stocks
price_filter = close.shift(1) > 20
# Market Cap filter: Market value > 10 Billion TWD to focus on mid-large caps (underused factor used as filter)
market_cap_filter = market_value.shift(1) > 10_000_000_000
# MFI range filter: MFI between 20 and 80 to avoid extreme overbought/oversold conditions
mfi_range_filter = (mfi.shift(1) > 20) & (mfi.shift(1) < 80)
# Apply all filters to the combined factor
filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & mfi_range_filter]
# 5. Select stocks
# Select the top 10 stocks based on the filtered combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
# Backtest with quarterly rebalancing and an 8% stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.08)