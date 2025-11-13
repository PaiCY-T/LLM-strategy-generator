def strategy(data):
    # Load necessary data
    close = data.get('etl:adj_close')
    trading_value = data.get('price:成交金額')
    operating_margin = data.get('fundamental_features:營業利益率')
    pb_ratio = data.get('price_earning_ratio:股價淨值比')
    roe = data.get('fundamental_features:ROE稅後')
    revenue_growth_yoy = data.get('fundamental_features:營收成長率') # Year-over-year revenue growth

    # 1. Liquidity Filter: Ensure sufficient trading volume
    # Preserve champion's liquidity requirement (>150M TWD average daily trading value)
    liquidity_filter = trading_value.rolling(window=20).mean().shift(1) > 150_000_000

    # 2. Price Momentum: Short-term price strength (relative to 60-day average)
    # Champion uses price momentum; refine with relative strength
    # Calculate 20-day and 60-day simple moving averages
    ma20 = close.rolling(window=20).mean().shift(1)
    ma60 = close.rolling(window=60).mean().shift(1)

    # Momentum condition: Current price above short-term MA, and short-term MA above long-term MA
    # This indicates strong upward trend and avoids whipsaws
    momentum_filter = (close.shift(1) > ma20) & (ma20 > ma60)

    # 3. Quality Filter (ROE and Operating Margin): Preserve champion's quality focus
    # High ROE: Companies effectively generating profit from equity
    # High Operating Margin: Companies with efficient core operations
    # Shifted to prevent look-ahead bias
    quality_filter = (roe.shift(1) > 0.15) & (operating_margin.shift(1) > 0.05)

    # 4. Value Filter (PB Ratio): Introduce a value component to balance momentum
    # Low PB ratio suggests undervaluation relative to book value
    # Avoid extremely low PB (potential value traps) and extremely high PB
    pb_filter = (pb_ratio.shift(1) > 0.5) & (pb_ratio.shift(1) < 3)

    # 5. Growth Filter (Revenue Growth): Add a growth component for future potential
    # Positive year-over-year revenue growth indicates expanding business
    growth_filter = revenue_growth_yoy.shift(1) > 0.10 # At least 10% YoY growth

    # Combine all filters
    # The champion likely uses cross-sectional ranking implicitly with price momentum.
    # Here, we combine filters to select top-performing stocks.
    # The `&` operator implicitly performs cross-sectional filtering by selecting stocks that meet all conditions.
    selection = liquidity_filter & momentum_filter & quality_filter & pb_filter & growth_filter

    # Rank selected stocks by a composite score for final position sizing or selection
    # For simplicity and to maintain champion's structure, we'll return a boolean series.
    # If a position series with weights is needed, further ranking/weighting would be applied here.

    # Ensure no NaN values in the final selection
    position = selection.fillna(False)

    return position