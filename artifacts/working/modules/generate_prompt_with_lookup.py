"""Generate prompt template with validated dataset keys from mapping."""

from dataset_lookup import DatasetLookup


def generate_prompt_template():
    """Generate prompt template with correct dataset keys."""

    lookup = DatasetLookup()

    # Get key dataset categories
    price_datasets = lookup.get_category('price')
    fundamental_datasets = lookup.get_category('fundamental')[:20]  # Top 20
    revenue_datasets = lookup.get_category('monthly_revenue')[:8]  # Top 8
    institutional_datasets = lookup.get_category('institutional')[:10]
    margin_datasets = lookup.get_category('margin')[:8]

    template = f"""You are an expert quantitative trading strategy developer for Taiwan stock market.

## CRITICAL: Use ONLY These Verified Dataset Keys

### Price Data ({len(price_datasets)} datasets)
"""
    for ds in price_datasets:
        template += f"- {ds['key']} - {ds['name']} ({ds['type']})\n"

    template += f"\n### Monthly Revenue Data ({len(revenue_datasets)} datasets) - ⚠️ CORRECTED KEYS\n"
    for ds in revenue_datasets:
        template += f"- {ds['key']} - {ds['name']} ({ds['type']})\n"

    template += f"\n### Fundamental Features ({len(fundamental_datasets)} datasets)\n"
    for ds in fundamental_datasets:
        template += f"- {ds['key']} - {ds['name']} ({ds['type']})\n"

    template += f"\n### Institutional Investors ({len(institutional_datasets)} datasets)\n"
    for ds in institutional_datasets:
        template += f"- {ds['key']} - {ds['name']} ({ds['type']})\n"

    template += f"\n### Margin Trading ({len(margin_datasets)} datasets)\n"
    for ds in margin_datasets:
        template += f"- {ds['key']} - {ds['name']} ({ds['type']})\n"

    # Get monthly revenue keys for examples
    revenue_keys = lookup.get_monthly_revenue_keys()

    template += f"""
## Code Requirements

Your generated code MUST follow these requirements:

1. **Data Loading**: Use EXACT keys from the list above with `data.get('key')`
2. **Factor Calculation**: Create factor signals using pandas operations
3. **Position DataFrame**: Generate boolean DataFrame named `position`
4. **Backtesting**: Call `report = sim(position, resample="Q", upload=False, stop_loss=0.08)`
5. **No Imports**: Do NOT include any import statements
6. **Shift Forward**: Use `.shift(1)` or higher to avoid look-ahead bias
7. **Valid Syntax**: Must be syntactically correct Python/pandas code

## Strategy Template with CORRECT Keys

```python
# 1. Load data using VERIFIED keys
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
trading_value = data.get('price:成交金額')

# Monthly revenue with CORRECT key (NOT etl:monthly_revenue:revenue_yoy!)
revenue_yoy = data.get('{revenue_keys['revenue_yoy']}')  # ✅ CORRECT

# Fundamental data
roe = data.get('fundamental_features:ROE稅後')
pe_ratio = data.get('fundamental_features:本益比')

# 2. Calculate factors
# Momentum factor
momentum = close.pct_change(20).shift(1)

# Revenue growth factor (align monthly to daily)
revenue_growth = revenue_yoy.ffill().shift(1)

# ROE factor (align quarterly to daily)
roe_factor = roe.ffill().shift(1)

# Value factor
value_factor = (1 / pe_ratio).replace([float('inf'), -float('inf')], 0).shift(1)

# 3. Combine factors
combined_factor = (
    momentum * 0.3 +
    revenue_growth * 0.3 +
    roe_factor * 0.2 +
    value_factor * 0.2
)

# 4. Apply filters
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
price_filter = close.shift(1) > 10
final_filter = liquidity_filter & price_filter

# 5. Select stocks
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)
```

## IMPORTANT: Common Dataset Key Errors to AVOID

❌ WRONG: `data.get('etl:monthly_revenue:revenue_yoy')`
✅ CORRECT: `data.get('{revenue_keys['revenue_yoy']}')`

❌ WRONG: `data.get('monthly_revenue')`
✅ CORRECT: `data.get('monthly_revenue:當月營收')`

## Previous Iteration Feedback

{{history}}

## Your Task

Generate a complete, executable Finlab trading strategy that:
1. Uses ONLY dataset keys from the verified list above
2. Combines 2-4 factors with clear logic
3. Includes liquidity and price filtering
4. Selects 8-12 stocks
5. If previous iterations failed with "not exists" errors, use different datasets

Return ONLY the Python code in ```python blocks. No explanations.
"""

    return template


if __name__ == '__main__':
    template = generate_prompt_template()

    # Save to file
    with open('prompt_template_validated.txt', 'w', encoding='utf-8') as f:
        f.write(template)

    print("✅ Generated prompt_template_validated.txt")
    print(f"   Template length: {len(template)} chars")

    # Show monthly revenue section
    print("\n月營收數據集部分:")
    lines = template.split('\n')
    in_revenue = False
    for line in lines:
        if 'Monthly Revenue Data' in line:
            in_revenue = True
        elif in_revenue and line.startswith('###'):
            break
        elif in_revenue:
            print(line)
