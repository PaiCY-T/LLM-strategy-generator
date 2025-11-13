# Factor Diversity Analyzer - Usage Examples

## Basic Usage

```python
from src.analysis.novelty.factor_diversity import calculate_factor_diversity

# Analyze a strategy
strategy_code = """
close = data.get('price:收盤價')
ma20 = close.average(20)
ma60 = close.average(60)
volume = data.get('price:成交量')
cond = (ma20 > ma60) & (volume > volume.average(20))
"""

score, details = calculate_factor_diversity(strategy_code)

print(f"Diversity Score: {score:.3f}")
print(f"Factors Found: {details['factors']}")
print(f"Unique Count: {details['unique_count']}")
print(f"Deviation: {details['deviation_score']:.3f}")
print(f"Rarity: {details['rarity_score']:.3f}")
```

## With Template Baseline

```python
from src.analysis.novelty.factor_diversity import FactorDiversityAnalyzer

# Define template strategies (Factor Graph templates)
templates = [
    """
close = data.get('price:收盤價')
ma20 = close.average(20)
""",
    """
revenue = data.get('monthly_revenue:當月營收')
revenue_growth = revenue.diff()
"""
]

# Create analyzer with templates
analyzer = FactorDiversityAnalyzer(template_codes=templates)

# Analyze a novel strategy
novel_strategy = """
pe = data.get('fundamental_features:本益比')
pb = data.get('fundamental_features:股價淨值比')
roe = data.get('fundamental_features:股東權益報酬率')
cond = (pe < 15) & (pb < 1.5) & (roe > 0.15)
"""

score, details = analyzer.calculate_diversity(novel_strategy)

print(f"Novelty Score: {score:.3f}")
print(f"Template Deviation: {details['deviation_score']:.3f}")
print(f"Factor Rarity: {details['rarity_score']:.3f}")
```

## Example Output

```
Diversity Score: 0.652
Factors Found: ['dataset:fundamental_features:本益比',
                'dataset:fundamental_features:股價淨值比',
                'dataset:fundamental_features:股東權益報酬率',
                'logic:and_2']
Unique Count: 4
Unique Count Score: 0.200  (4/20 max expected)
Deviation Score: 0.950     (very different from templates)
Rarity Score: 0.850        (uses rare factors)
Final Score: 0.652         (40% * 0.2 + 40% * 0.95 + 20% * 0.85)
```

## Interpretation

- **Score < 0.3**: Strategy uses mostly template factors (low novelty)
- **Score 0.3-0.7**: Strategy has moderate novelty (some new factors)
- **Score > 0.7**: Strategy is highly novel (many rare/unique factors)

## Components

1. **Unique Factor Count (40% weight)**: Measures how many distinct factors used
   - Normalized by MAX_EXPECTED_FACTORS (20)
   - More factors = higher score

2. **Template Deviation (40% weight)**: Cosine distance from template vectors
   - 0.0 = identical to templates
   - 1.0 = completely orthogonal (different factors)

3. **Factor Rarity (20% weight)**: Inverse Document Frequency (IDF)
   - Factors never seen in templates = 1.0
   - Common factors = low score
