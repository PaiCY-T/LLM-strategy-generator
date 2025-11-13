# Diversity Analysis Quick Reference

## Overview
The diversity analysis script (`scripts/analyze_diversity.py`) assesses strategy portfolio diversity across three dimensions:
1. **Factor Diversity**: How different are the trading factors used?
2. **Return Correlation**: How correlated are strategy returns?
3. **Risk Diversity**: How varied are the risk profiles?

## Quick Start

### Basic Analysis
```bash
python3 scripts/analyze_diversity.py \
  --validation-results phase2_validated_results_20251101_060315.json \
  --output diversity_report.md
```

### With Duplicate Exclusion
```bash
python3 scripts/analyze_diversity.py \
  --validation-results validation_results.json \
  --duplicate-report duplicate_report.json \
  --output diversity_report.md
```

## Command-Line Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--validation-results` | Yes | - | Path to validation results JSON file |
| `--duplicate-report` | No | None | Path to duplicate report JSON |
| `--strategy-dir` | No | Current dir | Directory containing strategy files |
| `--output` | No | diversity_report.md | Output path for Markdown report |
| `--verbose` | No | False | Enable verbose logging |

## Output Files

The script generates 4 files:

1. **Markdown Report** (`diversity_report.md`)
   - Human-readable comprehensive analysis
   - Recommendations and next steps
   - Embedded visualizations

2. **JSON Report** (`diversity_report.json`)
   - Machine-readable structured data
   - All metrics and warnings
   - Factor usage distribution

3. **Correlation Heatmap** (`diversity_report_correlation_heatmap.png`)
   - Visual correlation matrix
   - Color-coded (blue=low, red=high)
   - Strategy indices labeled

4. **Factor Usage Chart** (`diversity_report_factor_usage.png`)
   - Horizontal bar chart
   - Top 15 most used factors
   - Usage count displayed

## Understanding the Diversity Score

### Score Calculation
```
Diversity Score = (Factor Diversity × 0.5 +
                   (1 - Correlation) × 0.3 +
                   Risk Diversity × 0.2) × 100
```

### Recommendations

| Score Range | Recommendation | Meaning |
|-------------|----------------|---------|
| 60-100 | **SUFFICIENT** | Portfolio has good diversity |
| 40-59 | **MARGINAL** | Consider adding more diverse strategies |
| 0-39 | **INSUFFICIENT** | Portfolio lacks diversity, action needed |

### Component Metrics

**Factor Diversity** (0-1, higher is better)
- Measures how different factor combinations are
- Calculated using Jaccard distance
- Threshold: >0.5 recommended

**Average Correlation** (0-1, lower is better)
- Estimates strategy return correlation
- Uses Sharpe ratio as proxy
- Threshold: <0.8 recommended

**Risk Diversity** (0-1, higher is better)
- Measures variation in risk profiles
- Coefficient of variation of max drawdowns
- Threshold: >0.3 recommended

## Interpreting Results

### Example: INSUFFICIENT Diversity
```
Diversity Score: 27.6/100
Recommendation: INSUFFICIENT

Metrics:
- Factor Diversity: 0.252 (Low)
- Average Correlation: 0.500 (Moderate)
- Risk Diversity: 0.000 (Low)

Interpretation:
- Strategies use similar factor combinations
- Risk profiles are nearly identical
- Portfolio vulnerable to correlated losses
- Action: Add more diverse strategies
```

### Example: SUFFICIENT Diversity
```
Diversity Score: 75.3/100
Recommendation: SUFFICIENT

Metrics:
- Factor Diversity: 0.678 (Good)
- Average Correlation: 0.412 (Good)
- Risk Diversity: 0.534 (Good)

Interpretation:
- Strategies use diverse factor combinations
- Returns are not highly correlated
- Risk profiles are varied
- Action: Monitor and maintain diversity
```

## Common Use Cases

### 1. Post-Evolution Analysis
After running evolution, check if validated strategies are diverse:
```bash
python3 scripts/analyze_diversity.py \
  --validation-results phase2_validated_results.json \
  --output post_evolution_diversity.md
```

### 2. Portfolio Rebalancing
Identify redundant strategies before portfolio construction:
```bash
# First find duplicates
python3 scripts/detect_duplicates.py \
  --validation-results validation_results.json \
  --output duplicate_report.json

# Then analyze diversity excluding duplicates
python3 scripts/analyze_diversity.py \
  --validation-results validation_results.json \
  --duplicate-report duplicate_report.json \
  --output portfolio_diversity.md
```

### 3. Continuous Monitoring
Track diversity over time:
```bash
# Generate timestamped reports
timestamp=$(date +%Y%m%d_%H%M%S)
python3 scripts/analyze_diversity.py \
  --validation-results latest_validation.json \
  --output "diversity_${timestamp}.md"
```

## Troubleshooting

### Issue: "No strategy files found"
**Cause**: Strategy files not in current directory
**Solution**: Use `--strategy-dir` to specify location
```bash
python3 scripts/analyze_diversity.py \
  --validation-results validation_results.json \
  --strategy-dir /path/to/strategies \
  --output diversity_report.md
```

### Issue: "No validated strategies found"
**Cause**: All strategies failed validation
**Solution**: Check validation results, may need to adjust thresholds

### Issue: "Visualization libraries not available"
**Cause**: matplotlib/seaborn not installed
**Solution**: Install dependencies (optional) or continue without visualizations
```bash
pip install matplotlib seaborn
```

### Issue: Chinese characters display incorrectly
**Cause**: System font doesn't support Chinese
**Solution**: Non-blocking, report still generated correctly

## Testing

Run the test suite:
```bash
python3 scripts/test_analyze_diversity.py
```

Expected output:
```
============================================================
Testing scripts/analyze_diversity.py (Task 3.2)
============================================================

Test 1: Basic execution without duplicate report...
✓ Test 1 passed

Test 2: Execution with duplicate report...
✓ Test 2 passed

Test 3: Error handling for missing validation file...
✓ Test 3 passed

Test 4: Help output...
✓ Test 4 passed

Test 5: Validate report contents...
✓ Test 5 passed

============================================================
Test Results: 5 passed, 0 failed
============================================================

✓ All tests passed!
```

## Integration with Other Tools

### With Duplicate Detection (Task 2.2)
```bash
# Step 1: Detect duplicates
python3 scripts/detect_duplicates.py \
  --validation-results validation_results.json \
  --output duplicate_report.json

# Step 2: Analyze diversity excluding duplicates
python3 scripts/analyze_diversity.py \
  --validation-results validation_results.json \
  --duplicate-report duplicate_report.json \
  --output diversity_report.md
```

### With Validation Framework
```bash
# Step 1: Run validation
python3 run_phase2_with_validation.py

# Step 2: Analyze diversity of validated strategies
python3 scripts/analyze_diversity.py \
  --validation-results phase2_validated_results_*.json \
  --output diversity_report.md
```

## Advanced Usage

### Custom Thresholds
Modify thresholds in the DiversityAnalyzer class:
```python
# src/analysis/diversity_analyzer.py
def _generate_recommendation(self, diversity_score: float) -> str:
    if diversity_score >= 70:  # Changed from 60
        return "SUFFICIENT"
    elif diversity_score >= 50:  # Changed from 40
        return "MARGINAL"
    else:
        return "INSUFFICIENT"
```

### Batch Processing
Analyze multiple validation results:
```bash
for file in phase2_validated_results_*.json; do
    output="diversity_$(basename $file .json).md"
    python3 scripts/analyze_diversity.py \
      --validation-results "$file" \
      --output "$output"
done
```

### JSON Report Parsing
Extract diversity score programmatically:
```python
import json

with open('diversity_report.json', 'r') as f:
    report = json.load(f)

score = report['diversity_score']
recommendation = report['recommendation']

print(f"Diversity: {score:.1f}/100 ({recommendation})")
```

## Best Practices

1. **Always exclude duplicates**: Use `--duplicate-report` when available
2. **Run after validation**: Only analyze validated strategies
3. **Monitor trends**: Track diversity over time
4. **Act on warnings**: Address low diversity proactively
5. **Review visualizations**: Heatmap reveals correlation patterns
6. **Check factor usage**: Identify overused/underused factors
7. **Document decisions**: Keep diversity reports for audit trail

## Performance Tips

1. **Large portfolios**: Analysis scales linearly with strategy count
2. **Visualization**: Matplotlib adds ~0.5s overhead
3. **Verbose mode**: Use only for debugging
4. **Batch processing**: Run analyses in parallel for multiple files

## Related Documentation

- **Task 3.1**: DiversityAnalyzer implementation
- **Task 2.2**: Duplicate detection
- **Validation Framework**: Strategy validation system
- **REQ-3**: Diversity analysis requirements

---

**Version**: 1.0
**Last Updated**: 2025-11-01
**Related Task**: 3.2 (validation-framework-critical-fixes)
