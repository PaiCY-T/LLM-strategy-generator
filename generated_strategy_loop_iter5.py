def strategy(data):
    # Load necessary data, ensuring no look-ahead bias with .shift(1)
    close = data.get('etl:adj_close')
    trading_value = data.get('price:成交金額')
    operating_margin = data.get('fundamental_features:營業利益率')
    pb_ratio = data.get('price_earning_ratio:股價淨值比')
    market_value = data.get('etl:market_value')
    roe = data.get('fundamental_features:ROE稅後')
    revenue_growth = data.get('fundamental_features:營收成長率')

    # 1. Liquidity Filter: Average daily trading value > 150M TWD
    # Shift(1) to avoid look-ahead bias on current day's trading value
    liquidity_filter = (trading_value.shift(1).rolling(20).mean() > 150_000_000).fillna(False)

    # 2. Price Momentum: Short-term momentum with a slight twist
    # Calculate 20-day momentum (close price change)
    momentum_20d = (close.shift(1) / close.shift(21) - 1).rank(axis=1, pct=True)

    # 3. Quality/Profitability: Combine Operating Margin and ROE
    # Higher operating margin indicates better operational efficiency
    # High ROE indicates strong profitability
    quality_score = (operating_margin.shift(1).rank(axis=1, pct=True) * 0.5 +
                     roe.shift(1).rank(axis=1, pct=True) * 0.5)

    # 4. Value Factor: PB Ratio (lower is better)
    # Invert PB ratio for ranking (lower PB means higher rank)
    value_score = (1 / pb_ratio.shift(1)).rank(axis=1, pct=True)

    # 5. Growth Factor: Revenue Growth
    # Prioritize companies with positive and strong revenue growth
    growth_filter = (revenue_growth.shift(1) > 0.1).fillna(False) # Require at least 10% growth

    # Combine factors using a weighted approach and cross-sectional ranking
    # Emphasize momentum and quality, with value as a supporting factor
    # Filter for growth before ranking
    combined_score = (momentum_20d * 0.4 + quality_score * 0.3 + value_score * 0.3)
    
    # Apply growth and liquidity filters
    filtered_score = combined_score[growth_filter & liquidity_filter]

    # Select top 5% of stocks based on the combined score
    # Ensure a minimum number of stocks are selected if available
    position = filtered_score.rank(axis=1, pct=True) > 0.95
    
    # Ensure at least 5 stocks are selected if possible, to prevent empty portfolios
    # This part requires careful handling to avoid non-vectorized operations if not supported
    # For FinLab, we usually rely on the top % selection to implicitly handle this.
    # If a specific number of stocks is needed, a more complex selection logic might be required.
    # For now, we stick to the top 5% based on rank.

    return position