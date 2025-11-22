def strategy(data):
    # 1. Load data - ALWAYS use adjusted data for price!
    close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits
    trading_value = data.get('price:成交金額')  # OK for liquidity filter
    pe_ratio = data.get('price_earning_ratio:本益比')
    pb_ratio = data.get('price_earning_ratio:股價淨值比')
    market_cap = data.get('etl:market_value')
    mfi = data.indicator('MFI')

    # 2. Calculate factors with .shift(1) to prevent look-ahead bias
    # Price Momentum: 1-month return
    momentum_1m = close.pct_change(20).shift(1)

    # 3-month momentum (new factor to enhance returns)
    momentum_3m = close.pct_change(60).shift(1)

    # Moving Average Crossover (Smoothing): Short-term MA over Long-term MA
    # Using 10-day and 60-day MA for trend identification
    ma_short = close.rolling(window=10).mean().shift(1)
    ma_long = close.rolling(window=60).mean().shift(1)
    ma_crossover = ma_short > ma_long

    # Value Factor: Low PE ratio
    # Applying a rank-based filter to select relatively cheaper stocks
    ranked_pe = pe_ratio.rank(axis=1, ascending=True).shift(1)
    low_pe = ranked_pe < 0.2 * ranked_pe.shape[1] # Top 20% lowest PE

    # Quality Factor: ROE (Return on Equity)
    # Using ROE from fundamental features, shifted to avoid look-ahead
    # Validate field before using
    roe_field = 'fundamental_features:ROE'
    if roe_field in VALID_FIELDS:
        roe = data.get(roe_field).shift(1)
    else:
        # Fallback or skip if field not found
        print(f"Warning: {roe_field} not found in catalog. Skipping ROE filter.")
        roe = pd.DataFrame(True, index=close.index, columns=close.columns) # Effectively disable filter

    high_roe = roe > 0.15 # ROE > 15%

    # Liquidity Filter: Average daily trading value > 150M TWD
    # Calculate 20-day average trading value
    avg_trading_value = trading_value.rolling(window=20).mean().shift(1)
    liquid_stocks = avg_trading_value > 150_000_000

    # Combine factors for selection
    # Enhance momentum by combining 1m and 3m momentum
    # Add ROE as a quality filter and low PE as a value filter
    # The champion strategy relied heavily on price momentum and MA.
    # We add 3-month momentum and quality/value filters to potentially
    # capture more robust trends and fundamental strength.
    
    # Selection criteria:
    # 1. Positive 1-month momentum
    # 2. Positive 3-month momentum
    # 3. Short-term MA above Long-term MA (uptrend)
    # 4. High ROE (quality)
    # 5. Low PE (value)
    # 6. Sufficient liquidity
    
    # Combine momentum factors
    momentum_combined = (momentum_1m > 0) & (momentum_3m > 0)

    # Final selection
    # Using `&` for boolean Series combination
    selection = momentum_combined & ma_crossover & high_roe & low_pe & liquid_stocks

    # 4. Filter out NaN values that might arise from calculations
    selection = selection.fillna(False)

    # 5. Determine position: Long 1 unit for selected stocks
    position = selection.astype(float)

    return position