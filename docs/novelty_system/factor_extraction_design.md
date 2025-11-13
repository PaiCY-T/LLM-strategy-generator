# Factor Extraction Design

## Objective
Extract factor usage patterns from Python strategy code to measure novelty.

## Factor Categories

### 1. Dataset Factors
**Pattern**: `data.get('dataset_name:column_name')`
**Examples**:
- `data.get('price:收盤價')` → factor: "dataset:price:收盤價"
- `data.get('monthly_revenue:當月營收')` → factor: "dataset:monthly_revenue:當月營收"

**Extraction Method**: Regex `data\.get\(['"]([^'"]+)['"]\)`

### 2. Technical Indicators
**Patterns**:
- Moving Average: `.average(period)` → factor: "indicator:ma_{period}"
- Rolling: `.rolling(window)` → factor: "indicator:rolling_{window}"
- Shift: `.shift(lag)` → factor: "indicator:shift_{lag}"
- Momentum: `.diff()` → factor: "indicator:momentum"

**Extraction Method**: Multiple regex patterns for each indicator type

### 3. Selection Methods
**Patterns**:
- Ranking: `.is_largest(n)`, `.is_smallest(n)` → factor: "selection:ranking"
- Quantile: `.quantile(q)` → factor: "selection:quantile_{q}"

### 4. Combination Logic
**Patterns**:
- AND combinations: `cond1 & cond2` → factor: "logic:and_combination"
- OR combinations: `cond1 | cond2` → factor: "logic:or_combination"

## Template Baseline

**Factor Graph Templates** (located in `strategies/factor_graph_templates/`):
- Template strategies use 10-15 common factors
- Most common factors: price:收盤價, monthly_revenue:當月營收, MA(20), MA(60)

**Novelty Scoring**:
- Strategy using template factors → low novelty (0.0-0.3)
- Strategy using novel factors → high novelty (0.7-1.0)

## Algorithm

```python
def calculate_factor_diversity(strategy_code: str, template_vectors: List[Dict]) -> float:
    # 1. Extract factors from strategy
    strategy_factors = extract_factors(strategy_code)

    # 2. Calculate unique factor count (normalized)
    unique_count = len(strategy_factors) / MAX_EXPECTED_FACTORS  # e.g., 20

    # 3. Calculate template deviation
    strategy_vector = build_factor_vector(strategy_factors)
    template_vectors_avg = average_vectors(template_vectors)
    deviation = cosine_distance(strategy_vector, template_vectors_avg)

    # 4. Calculate factor rarity (IDF)
    rarity_scores = [idf(factor) for factor in strategy_factors]
    avg_rarity = mean(rarity_scores)

    # 5. Weighted combination
    diversity_score = 0.4 * unique_count + 0.4 * deviation + 0.2 * avg_rarity

    return clip(diversity_score, 0.0, 1.0)
```

## Edge Cases

1. **Empty Strategy**: Return 0.0
2. **Identical to Template**: Return 0.0
3. **All Novel Factors**: Return 1.0
4. **Malformed Code**: Log warning, return 0.0
