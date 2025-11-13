import pandas as pd

def strategy(data):
    # 1. Load necessary data (shifted to prevent look-ahead bias)
    close = data.get('etl:adj_close').shift(1)
    trading_value = data.get('price:成交金額').shift(1)
    net_profit_margin = data.get('fundamental_features:稅後淨利率').shift(1)
    pe_ratio = data.get('price_earning_ratio:本益比').shift(1)
    revenue_mom = data.get('monthly_revenue:上月比較增減(%)').shift(1)
    
    # 2. Liquidity Filter: Ensure average daily trading value is above 150M TWD
    # Using 20-day rolling mean for robustness
    liquidity_filter = trading_value.rolling(20).mean() > 150_000_000 
    
    # 3. Price Momentum: Calculate 20-day momentum (current price vs. 20 days ago)
    # Using adjusted close for accurate returns
    momentum_20d = (close / close.shift(20) - 1).fillna(0)
    
    # 4. Moving Average Crossover for trend confirmation
    # Short-term (10-day) and Long-term (60-day) Simple Moving Averages
    ma_short = close.rolling(10).mean()
    ma_long = close.rolling(60).mean()
    
    # 5. Trend Filter: Short MA crosses above Long MA, indicating an uptrend
    trend_filter = (ma_short > ma_long).fillna(False)
    
    # 6. Profitability Filter: Use Net Profit Margin to select fundamentally strong companies
    # Filter for companies with positive and relatively high net profit margins
    profitability_filter = (net_profit_margin > 5) # Increased threshold for higher quality
    
    # 7. Valuation Filter: Incorporate PE Ratio to avoid overvalued stocks
    # Select stocks with a reasonable PE ratio (e.g., between 5 and 30)
    # Also, ensure PE is not negative (meaning losses)
    valuation_filter = (pe_ratio > 5) & (pe_ratio < 30) 
    
    # 8. Revenue Momentum Filter: Look for companies with growing revenue
    # Filter for positive month-over-month revenue growth
    revenue_growth_filter = (revenue_mom > 0)
    
    # 9. Combine all filters
    # The champion strategy relied on strong momentum and low drawdown.
    # We preserve momentum (momentum_20d > 0.05 for stronger signal) and trend.
    # We add profitability, valuation, and revenue growth for fundamental strength,
    # aiming to enhance Sharpe and maintain low drawdown by selecting higher-quality companies.
    
    # Strong buy signal: positive momentum, strong uptrend, liquid, profitable, reasonable valuation, and revenue growth
    # Rank momentum to pick the top performers among qualifying stocks
    
    # Ensure all conditions are met AND apply a strong momentum threshold
    combined_filter = (
        liquidity_filter & 
        trend_filter & 
        profitability_filter & 
        valuation_filter & 
        revenue_growth_filter &
        (momentum_20d > 0.05) # Increased momentum threshold for better performance
    )
    
    # 10. Select top N stocks based on momentum from the filtered universe
    # This step helps to focus on the strongest signals among the qualified stocks.
    # Rank momentum only for stocks that pass the combined filter
    filtered_momentum = momentum_20d[combined_filter]
    
    # Select top 10 stocks by momentum from the filtered list
    # Use .rank(ascending=False) to get higher ranks for higher momentum
    position = filtered_momentum.rank(axis=1, ascending=False) <= 10
    
    # Handle cases where no stocks meet the criteria
    position = position.fillna(False)
    
    return position