# Diversity Analyzer Documentation

**Module**: `src/analysis/diversity_analyzer.py`
**Task ID**: 3.1
**Specification**: validation-framework-critical-fixes
**Author**: AI Assistant
**Date**: 2025-11-01

## Overview

The DiversityAnalyzer module provides comprehensive analysis of strategy diversity across multiple dimensions. It is designed to help evaluate whether a population of trading strategies has sufficient diversity for robust portfolio construction and risk management.

## Key Features

- **Factor Diversity Analysis**: Analyzes which market data factors are used by each strategy
- **Return Correlation Analysis**: Measures similarity of strategy returns
- **Risk Profile Analysis**: Evaluates diversity of risk profiles across strategies
- **AST-based Factor Extraction**: Safely extracts factors without code execution
- **Comprehensive Reporting**: Generates detailed reports with actionable recommendations
- **Edge Case Handling**: Gracefully handles missing data, malformed files, and edge cases

## Installation

No additional dependencies required beyond standard data science libraries:
- numpy (for numerical calculations)
- Python standard library (ast, logging, pathlib, dataclasses)

## Quick Start

```python
from src.analysis.diversity_analyzer import DiversityAnalyzer

# Initialize analyzer
analyzer = DiversityAnalyzer()

# Run analysis
report = analyzer.analyze_diversity(
    strategy_files=['strategy1.py', 'strategy2.py', 'strategy3.py'],
    validation_results={'population': [...]},
    exclude_indices=[5]  # Optional: exclude duplicates
)

# Check results
print(f"Diversity Score: {report.diversity_score:.1f}")
print(f"Recommendation: {report.recommendation}")
```

## API Reference

### DiversityAnalyzer Class

Main class for performing diversity analysis.

#### Methods

##### `analyze_diversity(strategy_files, validation_results, exclude_indices=None)`

Main entry point for diversity analysis.

**Parameters:**
- `strategy_files` (List[str|Path]): List of strategy file paths
- `validation_results` (Dict): Validation results containing strategy metrics
  - Must have 'population' or 'strategies' key with list of strategy dicts
  - Each strategy should have 'metrics' dict with 'sharpe_ratio' and 'max_drawdown'
- `exclude_indices` (Optional[List[int]]): Indices of strategies to exclude (e.g., duplicates)

**Returns:**
- `DiversityReport`: Comprehensive diversity report

**Example:**
```python
report = analyzer.analyze_diversity(
    strategy_files=['iter0.py', 'iter1.py', 'iter2.py'],
    validation_results={
        'population': [
            {'metrics': {'sharpe_ratio': 0.8, 'max_drawdown': -0.2}},
            {'metrics': {'sharpe_ratio': 0.6, 'max_drawdown': -0.3}},
            {'metrics': {'sharpe_ratio': 0.9, 'max_drawdown': -0.15}}
        ]
    },
    exclude_indices=[1]  # Exclude second strategy
)
```

##### `extract_factors(strategy_path)`

Extract factor names from strategy file using AST parsing.

**Parameters:**
- `strategy_path` (Path): Path to strategy Python file

**Returns:**
- `Set[str]`: Set of factor names used by the strategy

**Example:**
```python
factors = analyzer.extract_factors(Path('strategy.py'))
print(f"Factors: {factors}")
# Output: {'price:收盤價', 'price:成交金額', 'fundamental_features:ROE稅後', ...}
```

##### `calculate_factor_diversity(factor_sets)`

Calculate factor diversity using Jaccard distance.

**Parameters:**
- `factor_sets` (List[Set[str]]): List of factor sets, one per strategy

**Returns:**
- `float`: Average Jaccard distance (0-1, higher is more diverse)

**Example:**
```python
factor_sets = [
    {'factor_a', 'factor_b'},
    {'factor_b', 'factor_c'},
    {'factor_c', 'factor_d'}
]
diversity = analyzer.calculate_factor_diversity(factor_sets)
print(f"Factor diversity: {diversity:.4f}")
```

##### `calculate_return_correlation(validation_results, strategy_indices)`

Calculate average pairwise return correlation.

**Parameters:**
- `validation_results` (Dict): Validation results with strategy metrics
- `strategy_indices` (List[int]): Indices of strategies to include

**Returns:**
- `float`: Average correlation (0-1, lower indicates more diversity)

##### `calculate_risk_diversity(validation_results, strategy_indices)`

Calculate risk profile diversity using coefficient of variation.

**Parameters:**
- `validation_results` (Dict): Validation results with strategy metrics
- `strategy_indices` (List[int]): Indices of strategies to include

**Returns:**
- `float`: Coefficient of variation (0-1, higher is more diverse)

### DiversityReport Class

Dataclass containing comprehensive diversity analysis results.

**Attributes:**
- `total_strategies` (int): Total number of strategies analyzed
- `excluded_strategies` (List[int]): Indices of excluded strategies
- `factor_diversity` (float): Factor diversity score (0-1)
- `avg_correlation` (float): Average correlation (0-1)
- `risk_diversity` (float): Risk diversity score (0-1)
- `diversity_score` (float): Overall diversity score (0-100)
- `warnings` (List[str]): List of warning messages
- `recommendation` (str): "SUFFICIENT", "MARGINAL", or "INSUFFICIENT"
- `factor_details` (Optional[Dict]): Detailed factor analysis

## Diversity Metrics Explained

### 1. Factor Diversity (0-1, higher is better)

Measures how different the market data factors used by strategies are.

**Calculation:**
- Extracts factors from each strategy using AST parsing
- Computes pairwise Jaccard similarity between factor sets
- Returns average Jaccard distance: 1 - average(similarity)

**Interpretation:**
- **< 0.5**: Low diversity (warning) - strategies use similar factors
- **0.5-0.7**: Moderate diversity
- **> 0.7**: High diversity - strategies use diverse factors

**Example:**
```
Strategy A: {price, volume, RSI}
Strategy B: {price, volume, MACD}
Strategy C: {ROE, revenue, earnings}

Jaccard(A,B) = 2/4 = 0.5  (high similarity)
Jaccard(A,C) = 0/6 = 0.0  (no similarity)
Jaccard(B,C) = 0/6 = 0.0  (no similarity)

Average similarity = (0.5 + 0.0 + 0.0) / 3 = 0.167
Factor diversity = 1 - 0.167 = 0.833 (high)
```

### 2. Average Correlation (0-1, lower is better)

Measures similarity of strategy returns.

**Calculation:**
- Uses Sharpe ratio as proxy for returns (when time series unavailable)
- Computes coefficient of variation (CV) across strategies
- Maps CV to correlation: correlation = 1 / (1 + CV)

**Interpretation:**
- **> 0.8**: High correlation (warning) - strategies behave similarly
- **0.5-0.8**: Moderate correlation
- **< 0.5**: Low correlation (good) - strategies behave differently

**Note:** This is a proxy measure since we don't have full return time series. For more accurate correlation analysis, use actual return series when available.

### 3. Risk Diversity (0-1, higher is better)

Measures diversity of risk profiles across strategies.

**Calculation:**
- Extracts max drawdown for each strategy
- Computes coefficient of variation: CV = std(drawdowns) / mean(drawdowns)
- Normalizes to 0-1 range

**Interpretation:**
- **< 0.3**: Low diversity (warning) - similar risk profiles
- **0.3-0.5**: Moderate diversity
- **> 0.5**: High diversity - varied risk profiles

### 4. Overall Diversity Score (0-100)

Weighted combination of the three metrics.

**Formula:**
```python
score = (
    factor_diversity * 0.5 +        # 50% weight (most important)
    (1 - avg_correlation) * 0.3 +   # 30% weight
    risk_diversity * 0.2             # 20% weight
) * 100
```

**Recommendations:**
- **>= 60**: SUFFICIENT - Population has good diversity
- **40-59**: MARGINAL - Diversity could be improved
- **< 40**: INSUFFICIENT - Poor diversity, action needed

## Usage Examples

### Example 1: Basic Analysis

```python
from src.analysis.diversity_analyzer import DiversityAnalyzer
import json

# Load data
with open('validation_results.json', 'r') as f:
    validation_results = json.load(f)

strategy_files = [
    'strategy_0.py',
    'strategy_1.py',
    'strategy_2.py',
    'strategy_3.py',
    'strategy_4.py'
]

# Analyze
analyzer = DiversityAnalyzer()
report = analyzer.analyze_diversity(
    strategy_files=strategy_files,
    validation_results=validation_results
)

# Print results
print(f"Diversity Score: {report.diversity_score:.2f} / 100")
print(f"Recommendation: {report.recommendation}")
```

### Example 2: Excluding Duplicate Strategies

```python
from src.analysis.diversity_analyzer import DiversityAnalyzer
from src.analysis.duplicate_detector import DuplicateDetector

# Detect duplicates
duplicate_detector = DuplicateDetector()
duplicate_groups = duplicate_detector.find_duplicates(
    strategy_files=strategy_files,
    validation_results=validation_results
)

# Extract indices to exclude (keep first of each group)
exclude_indices = []
for group in duplicate_groups:
    if len(group.member_indices) > 1:
        exclude_indices.extend(group.member_indices[1:])

# Analyze diversity excluding duplicates
diversity_analyzer = DiversityAnalyzer()
report = diversity_analyzer.analyze_diversity(
    strategy_files=strategy_files,
    validation_results=validation_results,
    exclude_indices=exclude_indices
)

print(f"Total strategies (after removing duplicates): {report.total_strategies}")
print(f"Diversity score: {report.diversity_score:.2f}")
```

### Example 3: Detailed Factor Analysis

```python
from pathlib import Path
from src.analysis.diversity_analyzer import DiversityAnalyzer

analyzer = DiversityAnalyzer()

# Analyze factors for each strategy
for i, strategy_file in enumerate(strategy_files):
    factors = analyzer.extract_factors(Path(strategy_file))
    print(f"\nStrategy {i}:")
    print(f"  Factors: {len(factors)}")
    for factor in sorted(factors):
        print(f"    - {factor}")
```

### Example 4: Monitoring Diversity Over Time

```python
from src.analysis.diversity_analyzer import DiversityAnalyzer
import json

analyzer = DiversityAnalyzer()
diversity_history = []

# Analyze each generation
for gen in range(20):
    # Load generation data
    with open(f'generation_{gen}.json', 'r') as f:
        validation_results = json.load(f)

    population = validation_results['population']
    strategy_files = [f'strategy_{gen}_{i}.py' for i in range(len(population))]

    # Analyze diversity
    report = analyzer.analyze_diversity(
        strategy_files=strategy_files,
        validation_results=validation_results
    )

    diversity_history.append({
        'generation': gen,
        'score': report.diversity_score,
        'factor_diversity': report.factor_diversity,
        'avg_correlation': report.avg_correlation,
        'risk_diversity': report.risk_diversity
    })

# Plot diversity trends
import matplotlib.pyplot as plt
generations = [h['generation'] for h in diversity_history]
scores = [h['score'] for h in diversity_history]

plt.plot(generations, scores)
plt.xlabel('Generation')
plt.ylabel('Diversity Score')
plt.title('Diversity Evolution Over Time')
plt.show()
```

## Warnings

The analyzer generates warnings for the following conditions:

1. **Low factor diversity** (< 0.5): Strategies use similar factors
2. **High correlation** (> 0.8): Strategies behave similarly
3. **Low risk diversity** (< 0.3): Strategies have similar risk profiles
4. **Insufficient strategies** (< 3): Too few strategies for meaningful analysis

**Example warning output:**
```
Warnings:
  - Low factor diversity detected: 0.147 < 0.5
  - High correlation detected: 0.823 > 0.8
  - Low risk diversity detected: 0.082 < 0.3
```

## Error Handling

The analyzer gracefully handles various error conditions:

1. **Missing files**: Logs warning and continues with available files
2. **Syntax errors**: Logs error and skips problematic file
3. **Missing metrics**: Uses default values and adds warning
4. **Empty factor sets**: Handles in Jaccard calculation
5. **Insufficient data**: Returns appropriate default values

## Best Practices

1. **Minimum Strategy Count**: Use at least 5 strategies for meaningful analysis
2. **Exclude Duplicates**: Always run duplicate detection first and exclude duplicates
3. **Monitor Over Time**: Track diversity scores across generations to detect degradation
4. **Combine Metrics**: Don't rely on overall score alone - examine individual metrics
5. **Act on Warnings**: Address specific warnings (low factor diversity, high correlation, etc.)
6. **Validate Results**: Manually inspect strategies with very high/low diversity scores

## Integration Points

The DiversityAnalyzer integrates with:

1. **DuplicateDetector** (Task 2.1): Exclude duplicate strategies before analysis
2. **Validation Framework**: Uses validation results for metrics
3. **Population Manager**: Can guide selection/mutation decisions
4. **Reporting System**: Provides input for generation reports

## Limitations

1. **Correlation Proxy**: Uses Sharpe ratio as proxy when actual returns unavailable
   - For more accurate correlation, provide actual return time series
2. **Factor Extraction**: Only detects `data.get()` and `data.indicator()` calls
   - Custom factor extraction may be needed for non-standard patterns
3. **Static Analysis**: Cannot detect runtime factor usage
   - Only analyzes static code structure

## Performance

- **Factor Extraction**: O(n * m) where n = strategies, m = avg file size
- **Diversity Calculation**: O(n²) for pairwise comparisons
- **Memory Usage**: Minimal (only stores factor sets and metrics)
- **Typical Runtime**: < 1 second for 20 strategies

## Testing

Run the test suite:

```bash
python test_diversity_analyzer.py
```

Run usage examples:

```bash
PYTHONPATH=/path/to/finlab python examples/diversity_analyzer_usage.py
```

## Troubleshooting

### Issue: "No module named 'src'"
**Solution**: Set PYTHONPATH to project root:
```bash
export PYTHONPATH=/path/to/finlab
```

### Issue: "Insufficient strategies for diversity analysis"
**Solution**: Provide at least 2 strategies (recommend 5+)

### Issue: "Failed to extract factors"
**Solution**: Check strategy file has valid Python syntax and uses `data.get()` calls

### Issue: Zero diversity score
**Solution**: Check that strategies actually use different factors - may indicate all strategies are too similar

## References

- **Specification**: `.spec-workflow/specs/validation-framework-critical-fixes/`
- **Task Details**: `.spec-workflow/specs/validation-framework-critical-fixes/tasks.md` (Task 3.1)
- **Related Modules**:
  - `src/analysis/duplicate_detector.py` (Task 2.1)
  - `src/validation/`
  - `src/population/`

## Support

For issues or questions:
1. Check this documentation
2. Review usage examples in `examples/diversity_analyzer_usage.py`
3. Run test suite to verify installation
4. Check validation results format matches expected structure

---

**Last Updated**: 2025-11-01
**Version**: 1.0
**Status**: Complete
