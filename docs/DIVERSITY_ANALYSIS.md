# Diversity Analysis

**Version**: 1.0.0
**Date**: 2025-11-03
**Status**: Production Ready

---

## 1. Overview

The Diversity Analysis module measures portfolio diversity across multiple dimensions to prevent correlated failures and ensure robust learning signals in Phase 3. Low diversity indicates strategies may fail simultaneously during market regime changes.

### Purpose

Diversity analysis provides:
- **Factor Diversity**: Measures variety in trading signals used
- **Correlation Analysis**: Detects correlated returns between strategies
- **Risk Diversity**: Evaluates variation in risk profiles
- **Overall Diversity Score**: 0-100 composite metric for decision-making

### Why Diversity Matters for Phase 3

Phase 3 (Population-Based Learning) requires diverse strategies to:
- **Explore solution space**: Different strategies probe different market inefficiencies
- **Provide learning signal**: Diverse failures teach different lessons
- **Prevent correlated losses**: Portfolio shouldn't collapse during single regime shift
- **Enable ensemble learning**: Uncorrelated strategies combine better

**Risk**: Low diversity (score < 40) may lead to:
- Narrow pattern recognition (overfitting)
- Simultaneous strategy failures
- Insufficient learning signal for Phase 3

---

## 2. Diversity Metrics

### 2.1 Factor Diversity (Jaccard Distance)

**Purpose**: Measure variety in trading factors used across strategies

**Method**: Jaccard similarity between factor sets

**Formula**:
```
Jaccard Similarity = |A ∩ B| / |A ∪ B|
Jaccard Distance = 1 - Jaccard Similarity
```

**Example**:
```
Strategy 1 factors: {momentum, volume, PE_ratio}
Strategy 2 factors: {momentum, RSI, revenue_growth}

Intersection: {momentum} → size = 1
Union: {momentum, volume, PE_ratio, RSI, revenue_growth} → size = 5

Jaccard Similarity = 1 / 5 = 0.20
Jaccard Distance = 1 - 0.20 = 0.80 (High diversity)
```

**Thresholds**:
- **Good**: ≥0.5 (strategies use different factor combinations)
- **Marginal**: 0.3-0.5 (some overlap acceptable)
- **Insufficient**: <0.3 (strategies too similar)

**Implementation**:
```python
from src.analysis.diversity_analyzer import DiversityAnalyzer

analyzer = DiversityAnalyzer()
factor_sets = [
    analyzer.extract_factors(strategy_file)
    for strategy_file in strategy_files
]
factor_diversity = analyzer.calculate_factor_diversity(factor_sets)
print(f"Factor Diversity: {factor_diversity:.3f}")
```

---

### 2.2 Correlation (Average Pairwise)

**Purpose**: Detect correlated returns between strategies

**Method**: Average pairwise correlation using Sharpe ratios as proxy

**Formula**:
```
For strategies i and j:
correlation_proxy = 1 / (1 + CV)

where CV = std(sharpe_ratios) / mean(sharpe_ratios)
```

**Interpretation**:
- **Low correlation (<0.3)**: Excellent diversification
- **Moderate correlation (0.3-0.8)**: Acceptable diversification
- **High correlation (>0.8)**: Strategies may fail together

**Thresholds**:
- **Good**: <0.8 (strategies have independent returns)
- **Marginal**: 0.8-0.9 (monitor closely)
- **Insufficient**: >0.9 (correlated failures likely)

**Note**: Since individual strategy returns aren't available, we use Sharpe ratio variance as a correlation proxy. Lower variance in Sharpe ratios suggests higher correlation.

**Implementation**:
```python
correlation = analyzer.calculate_return_correlation(
    validation_results,
    strategy_indices
)
print(f"Average Correlation: {correlation:.3f}")
```

---

### 2.3 Risk Diversity (Coefficient of Variation)

**Purpose**: Measure variation in risk profiles (drawdown characteristics)

**Method**: Coefficient of variation of maximum drawdowns

**Formula**:
```
CV = std(max_drawdowns) / mean(max_drawdowns)
```

**Interpretation**:
- **High CV (>0.3)**: Strategies have diverse risk profiles
- **Moderate CV (0.2-0.3)**: Acceptable variation
- **Low CV (<0.2)**: Similar risk profiles (may break together)

**Thresholds**:
- **Good**: ≥0.3 (varied risk-return profiles)
- **Marginal**: 0.2-0.3 (some variation)
- **Insufficient**: <0.2 (homogeneous risk)

**Implementation**:
```python
risk_diversity = analyzer.calculate_risk_diversity(
    validation_results,
    strategy_indices
)
print(f"Risk Diversity: {risk_diversity:.3f}")
```

**Data Limitation**: Current validation JSON doesn't include per-strategy drawdowns, so this metric may return 0.0. Future work should add `max_drawdown` field to each strategy in validation results.

---

## 3. Overall Diversity Score

### 3.1 Calculation

The diversity score combines all three metrics into a 0-100 scale:

**Formula**:
```python
diversity_score = (
    factor_diversity * 0.5 +      # 50% weight (most important)
    (1 - avg_correlation) * 0.3 +  # 30% weight (inverted - lower is better)
    risk_diversity * 0.2            # 20% weight (least critical)
) * 100
```

**Rationale**:
- **Factor diversity** weighted highest (50%): Most actionable signal for mutations
- **Correlation** weighted medium (30%): Important but proxy-based (less precise)
- **Risk diversity** weighted lowest (20%): Nice-to-have but not critical

### 3.2 Interpretation

| Diversity Score | Recommendation | Meaning |
|-----------------|----------------|---------|
| **≥60** | SUFFICIENT | Strong diversity across factors, returns, and risk profiles |
| **40-59** | MARGINAL | Acceptable diversity but requires close monitoring |
| **<40** | INSUFFICIENT | Low diversity may lead to correlated failures |

### 3.3 Example Calculation

```
Given:
  factor_diversity = 0.45
  avg_correlation = 0.50
  risk_diversity = 0.15

Calculation:
  diversity_score = (0.45 * 0.5 + (1-0.50) * 0.3 + 0.15 * 0.2) * 100
                  = (0.225 + 0.150 + 0.030) * 100
                  = 0.405 * 100
                  = 40.5

Recommendation: MARGINAL (just meets conditional threshold)
```

---

## 4. Usage

### 4.1 Running Diversity Analysis

**Command**:
```bash
python3 scripts/analyze_diversity.py \
    --validation-results phase2_validated_results_20251101_132244.json \
    --duplicate-report duplicate_report.json \
    --output diversity_report.md
```

**Output Files**:
1. `diversity_report.md` - Human-readable Markdown report
2. `diversity_report.json` - Machine-readable JSON metrics
3. `diversity_report_correlation_heatmap.png` - Correlation visualization
4. `diversity_report_factor_usage.png` - Factor usage chart

### 4.2 Programmatic Usage

```python
from src.analysis.diversity_analyzer import DiversityAnalyzer
from pathlib import Path

# Initialize analyzer
analyzer = DiversityAnalyzer()

# Prepare inputs
strategy_files = [Path(f"generated_strategy_iter{i}.py") for i in [0, 2, 5, 9]]
validation_results = {...}  # Load from JSON
exclude_indices = [3, 7]    # Duplicates

# Run analysis
report = analyzer.analyze_diversity(
    strategy_files=strategy_files,
    validation_results=validation_results,
    exclude_indices=exclude_indices
)

# Access results
print(f"Diversity Score: {report.diversity_score:.1f}/100")
print(f"Recommendation: {report.recommendation}")
print(f"Factor Diversity: {report.factor_diversity:.3f}")
print(f"Avg Correlation: {report.avg_correlation:.3f}")
print(f"Risk Diversity: {report.risk_diversity:.3f}")

# Check warnings
for warning in report.warnings:
    print(f"⚠️  {warning}")
```

### 4.3 Integration with Decision Framework

```python
from src.analysis.decision_framework import DecisionFramework

# Load all reports
validation_results = load_json('validation_results.json')
duplicate_report = load_json('duplicate_report.json')
diversity_report = load_json('diversity_report.json')

# Evaluate Phase 3 decision
framework = DecisionFramework()
decision = framework.evaluate(
    validation_results=validation_results,
    duplicate_report=duplicate_report,
    diversity_report=diversity_report
)

print(f"Decision: {decision.decision}")
print(f"Diversity Score: {decision.diversity_score:.1f}/100")
# Output:
# Decision: CONDITIONAL_GO
# Diversity Score: 19.2/100
```

---

## 5. Interpretation Guide

### 5.1 High Factor Diversity (≥0.5)

**Indicators**:
- Strategies use different data sources (technical, fundamental, sentiment)
- Low overlap in factor combinations
- Mutations explore diverse solution space

**Action**: Maintain current mutation strategy

### 5.2 Low Factor Diversity (<0.5)

**Indicators**:
- Strategies cluster around similar factors
- Limited exploration of factor space
- Mutations converge to local optimum

**Actions**:
1. Increase mutation diversity rates
2. Seed population with diverse templates
3. Add factor diversity bonus to fitness function

### 5.3 High Correlation (>0.8)

**Indicators**:
- Strategies have similar return patterns
- Portfolio may collapse during regime shift
- Limited ensemble benefits

**Actions**:
1. Review for duplicate strategies (>95% similarity)
2. Add correlation penalty to fitness function
3. Force minimum Jaccard distance between strategies

### 5.4 Insufficient Risk Diversity (<0.3)

**Indicators**:
- Strategies have similar drawdown profiles
- Portfolio lacks defensive strategies
- Limited risk-return trade-off options

**Actions**:
1. Add risk-seeking and risk-averse strategy archetypes
2. Mutate exit rules more aggressively
3. Vary position sizing and stop-loss parameters

---

## 6. Troubleshooting

### 6.1 Risk Diversity Always 0.0

**Symptom**: `risk_diversity` metric returns 0.0

**Cause**: Validation JSON doesn't include per-strategy `max_drawdown` field

**Current Behavior**: `DiversityAnalyzer` returns 0.0 with warning when data insufficient

**Workaround**: None (data limitation)

**Future Fix**: Modify validation system to save `max_drawdown` per strategy:
```python
# In template_validator.py
strategy_result = {
    "strategy_index": idx,
    "sharpe_ratio": sharpe,
    "max_drawdown": backtest_result.mdd,  # ADD THIS
    ...
}
```

### 6.2 Factor Extraction Fails

**Symptom**: `extract_factors()` returns empty set

**Possible Causes**:
1. Strategy file has syntax errors
2. Strategy doesn't use `data.get()` calls
3. Strategy uses non-standard factor access

**Solution**:
```python
# Check strategy file syntax
import ast
with open(strategy_file, 'r') as f:
    code = f.read()
try:
    ast.parse(code)
    print("Syntax OK")
except SyntaxError as e:
    print(f"Syntax error: {e}")

# Manually inspect factor usage
grep 'data.get' generated_strategy_iter0.py
```

### 6.3 Low Diversity Score Despite Visual Differences

**Symptom**: Strategies look different but diversity score <40

**Possible Causes**:
1. Different code but using same core factors
2. High correlation in returns (different logic, similar outcomes)
3. Jaccard distance misinterprets factor aliases

**Investigation**:
```bash
# Check factor overlap
python3 scripts/analyze_diversity.py \
    --validation-results validation_results.json \
    --output diversity_report.md \
    --verbose

# Review factor details in JSON
jq '.factors.usage_distribution' diversity_report.json
```

---

## 7. Visualizations

### 7.1 Correlation Heatmap

**File**: `diversity_report_correlation_heatmap.png`

**Interpretation**:
- **Dark blue**: Low correlation (good diversity)
- **Red**: High correlation (potential concern)
- **Diagonal**: Always 1.0 (self-correlation)

**Example**:
```
Strategy 0  Strategy 2  Strategy 5  Strategy 9
    1.0        0.45       0.62       0.38    (Strategy 0)
    0.45       1.0        0.55       0.72    (Strategy 2)
    0.62       0.55       1.0        0.48    (Strategy 5)
    0.38       0.72       0.48       1.0     (Strategy 9)

Avg Correlation: 0.54 (Good diversity)
```

### 7.2 Factor Usage Chart

**File**: `diversity_report_factor_usage.png`

**Interpretation**:
- Shows top 15 most-used factors across portfolio
- High bars = factor used by many strategies (potential correlation source)
- Flat distribution = good factor diversity

**Example**:
```
momentum_20:     ████████████ (4 strategies)
volume_filter:   ████████ (3 strategies)
RSI_14:          ████████ (3 strategies)
PE_ratio:        ████ (2 strategies)
revenue_growth:  ████ (2 strategies)
...
```

---

## 8. Best Practices

### 8.1 When to Run Diversity Analysis

**Required**:
- After Phase 2 completion (before Phase 3 decision)
- When creating strategy ensembles
- After major mutation parameter changes

**Optional**:
- Mid-Phase 3 to check diversity degradation
- Before portfolio rebalancing
- After adding new strategy templates

### 8.2 Interpreting Warnings

```python
# Example warnings from diversity report
warnings = [
    "Low factor diversity detected: 0.083 < 0.5",
    "Low risk diversity detected: 0.000 < 0.3"
]
```

**Warning Types**:
1. **Low factor diversity**: Most critical - adjust mutations immediately
2. **High correlation**: Medium priority - review duplicate detection
3. **Low risk diversity**: Low priority - data limitation (see 6.1)

### 8.3 Combining with Other Metrics

Diversity is ONE input to Phase 3 decision:

| Metric | Weight | Status Example |
|--------|--------|----------------|
| Unique Strategies | CRITICAL | 4 ≥ 3 ✅ |
| Diversity Score | HIGH | 19.2 < 40 ⚠️ |
| Avg Correlation | CRITICAL | 0.50 < 0.8 ✅ |
| Validation Fixed | CRITICAL | True ✅ |

**Decision**: CONDITIONAL_GO (diversity marginal but not blocking)

---

## 9. API Reference

### 9.1 DiversityAnalyzer Class

```python
class DiversityAnalyzer:
    """Main diversity analysis class."""

    def analyze_diversity(
        self,
        strategy_files: List[Path],
        validation_results: Dict,
        exclude_indices: Optional[List[int]] = None,
        original_indices: Optional[List[int]] = None
    ) -> DiversityReport:
        """Run full diversity analysis.

        Args:
            strategy_files: List of strategy file paths
            validation_results: Validation results dict
            exclude_indices: Strategy indices to exclude (e.g., duplicates)
            original_indices: Original indices in population (for non-sequential)

        Returns:
            DiversityReport with all metrics and recommendations
        """

    def extract_factors(self, strategy_path: Path) -> Set[str]:
        """Extract factor names from strategy file using AST parsing."""

    def calculate_factor_diversity(self, factor_sets: List[Set[str]]) -> float:
        """Calculate Jaccard distance between factor sets."""

    def calculate_return_correlation(
        self,
        validation_results: Dict,
        strategy_indices: List[int]
    ) -> float:
        """Calculate average pairwise correlation using Sharpe ratios."""

    def calculate_risk_diversity(
        self,
        validation_results: Dict,
        strategy_indices: List[int]
    ) -> float:
        """Calculate coefficient of variation of max drawdowns."""
```

### 9.2 DiversityReport Dataclass

```python
@dataclass
class DiversityReport:
    """Diversity analysis results."""

    total_strategies: int
    excluded_strategies: List[int]
    factor_diversity: float          # 0-1, higher is better
    avg_correlation: float            # 0-1, lower is better
    risk_diversity: float             # 0-1, higher is better
    diversity_score: float            # 0-100, higher is better
    warnings: List[str]
    recommendation: str               # "SUFFICIENT", "MARGINAL", "INSUFFICIENT"
    factor_details: Optional[Dict]
```

---

## 10. References

### 10.1 Key Documents

- [VALIDATION_FRAMEWORK.md](VALIDATION_FRAMEWORK.md) - Statistical validation
- [PHASE3_GO_CRITERIA.md](PHASE3_GO_CRITERIA.md) - Decision criteria
- [DIVERSITY_ANALYZER.md](DIVERSITY_ANALYZER.md) - Existing quick reference

### 10.2 Related Code

- `src/analysis/diversity_analyzer.py` - Core implementation
- `scripts/analyze_diversity.py` - CLI tool
- `tests/analysis/test_diversity_analyzer.py` - Test suite

### 10.3 Academic References

- Politis & Romano (1994) - Stationary Bootstrap for time series
- Jaccard (1912) - Similarity coefficient for set comparison
- Markowitz (1952) - Portfolio theory and diversification

---

**Document Version**: 1.0.0
**Created**: 2025-11-03
**Author**: AI Assistant (Technical Writer Persona)
