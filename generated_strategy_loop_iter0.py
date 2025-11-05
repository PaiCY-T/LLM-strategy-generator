
def strategy(data):
    # LLM-generated strategy with fundamental factors
    roe = data.get('fundamental_features:ROE稅後')
    revenue_growth = data.get('fundamental_features:營收成長率')
    return (roe > 18) & (revenue_growth > 0.15)
