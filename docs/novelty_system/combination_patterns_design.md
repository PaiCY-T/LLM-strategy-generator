# Combination Pattern Detection Design

## Objective
Identify novel combinations of factors that exceed Factor Graph template patterns.

## Pattern Categories

### 1. Cross-Domain Combinations
**Definition**: Combining factors from different data domains

**Examples**:
- Price + Revenue: `close > ma20 & revenue > prev_revenue`
- Price + Fundamentals: `close > ma20 & pe_ratio < 15`
- Technical + Fundamental: `momentum > 0 & roe > 0.15`

**Novelty Scoring**:
- Single domain (price only): 0.0-0.3
- Two domains (price + revenue): 0.4-0.6
- Three+ domains: 0.7-1.0

**Detection Method**:
```python
domains = {
    'price': ['price:收盤價', 'price:開盤價', ...],
    'revenue': ['monthly_revenue:當月營收', ...],
    'fundamental': ['fundamental_features:本益比', ...],
    'technical': ['indicator:ma_*', 'indicator:momentum', ...]
}

def count_domains(factors: Set[str]) -> int:
    active_domains = set()
    for factor in factors:
        for domain, patterns in domains.items():
            if matches_any(factor, patterns):
                active_domains.add(domain)
    return len(active_domains)
```

### 2. Multi-Timeframe Combinations
**Definition**: Using multiple time periods simultaneously

**Examples**:
- Triple MA: `ma20 > ma60 > ma200` (3 timeframes)
- Fast + Slow: `ma5 > ma20 & ma20 > ma60` (2 timeframes)

**Novelty Scoring**:
- Single timeframe: 0.0-0.3
- Two timeframes: 0.4-0.6
- Three+ timeframes: 0.7-1.0

**Detection Method**:
Extract all MA/rolling periods, count unique periods

### 3. Complex Weighting Patterns
**Definition**: Non-uniform factor weighting

**Examples**:
- Multiplicative: `score = factor_a * 0.6 + factor_b * 0.4`
- Dynamic: `weight = revenue / ma20`
- Conditional: `weight = 1.0 if condition else 0.5`

**Novelty Scoring**:
- Equal weights: 0.0-0.2
- Simple weights (0.5, 0.5): 0.3-0.5
- Complex weights: 0.6-1.0

**Detection Method**:
- Parse multiplication operations: `*\s*[\d.]+`
- Parse weight variables: `weight\s*=`
- Count conditional weighting: `if.*else`

### 4. Non-Linear Combinations
**Definition**: Ratios, products, differences beyond linear sums

**Examples**:
- Ratio: `close / revenue`
- Product: `momentum * volume`
- Difference: `ma20 - ma60`

**Novelty Scoring**:
- Linear only (AND/OR): 0.0-0.3
- One non-linear op: 0.4-0.6
- Multiple non-linear: 0.7-1.0

**Detection Method**:
```python
non_linear_ops = {
    'division': r'\/(?!\*)',  # Division (not /*/)
    'multiplication': r'\*(?!\/)',  # Multiplication (not /*/)
    'subtraction': r'\-',  # Subtraction
    'power': r'\*\*',  # Exponentiation
}
```

## Template Baseline

**Factor Graph Templates** typically use:
- Single domain (price)
- Single timeframe (MA20 or MA60)
- Linear AND/OR combinations
- No complex weighting

**Example Template**:
```python
close = data.get('price:收盤價')
ma20 = close.average(20)
cond = ma20.is_largest(100)  # Simple ranking
```

## Combination Complexity Score Algorithm

```python
def calculate_combination_complexity(strategy_code: str) -> float:
    # 1. Cross-domain score (40% weight)
    domains = count_active_domains(strategy_code)
    domain_score = min(domains / 3.0, 1.0)  # Max at 3 domains

    # 2. Multi-timeframe score (30% weight)
    timeframes = count_unique_timeframes(strategy_code)
    timeframe_score = min(timeframes / 3.0, 1.0)  # Max at 3 timeframes

    # 3. Weighting complexity (15% weight)
    has_weights = detect_custom_weighting(strategy_code)
    weight_score = 1.0 if has_weights else 0.0

    # 4. Non-linear operations (15% weight)
    nonlinear_count = count_nonlinear_ops(strategy_code)
    nonlinear_score = min(nonlinear_count / 3.0, 1.0)  # Max at 3 ops

    # Weighted combination
    complexity = (
        0.40 * domain_score +
        0.30 * timeframe_score +
        0.15 * weight_score +
        0.15 * nonlinear_score
    )

    return clip(complexity, 0.0, 1.0)
```

## Edge Cases

1. **Empty Strategy**: Return 0.0
2. **Single Factor**: Return 0.0 (no combination)
3. **Template-Like**: Return 0.0-0.2
4. **Highly Complex**: Return 0.8-1.0

## Validation

Test on known strategies:
- Champion (Sharpe 2.48): Expected 0.6-0.8 (moderate complexity)
- Template strategies: Expected 0.0-0.3 (low complexity)
- Novel LLM strategies: Expected 0.5-1.0 (variable)
