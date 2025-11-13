# Track 3: Statistical Testing Pipeline - Quick Reference

## Installation

```bash
pip install pymannkendall>=1.4.2
# Other dependencies (scipy, matplotlib, numpy) already in requirements.txt
```

## Quick Start

### 1. Mann-Whitney U Test (Group Comparison)

```python
from src.analysis.statistical import mann_whitney_test

# Compare two groups
hybrid_sharpe = [0.5, 0.52, 0.55, 0.53, 0.54]
fg_only_sharpe = [0.45, 0.47, 0.46, 0.48, 0.44]

result = mann_whitney_test(hybrid_sharpe, fg_only_sharpe)
print(f"Significant: {result.significant}")
print(f"p-value: {result.p_value:.4f}")
print(f"Effect size: {result.effect_size:.3f}")
```

### 2. Mann-Kendall Trend Detection

```python
from src.analysis.statistical import detect_trend

# Detect trend in time series
sharpe_over_time = [0.5, 0.51, 0.52, 0.53, 0.55, 0.57]
result = detect_trend(sharpe_over_time)

print(f"Trend: {result.trend}")  # 'increasing', 'decreasing', or 'no trend'
print(f"Significant: {result.significant}")
print(f"Sen's slope: {result.slope:.4f}")
```

### 3. Visualizations

```python
from src.visualization import ExperimentVisualizer
from pathlib import Path

# Initialize visualizer
viz = ExperimentVisualizer(Path("output/plots"))

# Learning curves
group_data = {
    'Hybrid': [0.5, 0.52, 0.55, ...],
    'FG-Only': [0.45, 0.47, 0.46, ...]
}
viz.plot_learning_curves(group_data, save_name="learning_curves.png")

# Distribution comparison
viz.plot_distribution_comparison(group_data, save_name="distributions.png")

# Novelty vs performance
novelty_scores = [0.3, 0.32, 0.35, ...]
sharpe_ratios = [0.5, 0.52, 0.55, ...]
viz.plot_novelty_vs_performance(
    novelty_scores, sharpe_ratios,
    group_name="Hybrid",
    save_name="novelty_scatter.png"
)

# Trend analysis
from src.analysis.statistical import detect_trend
trend_result = detect_trend(group_data['Hybrid'])
viz.plot_trend_analysis(
    group_data['Hybrid'],
    trend_result,
    save_name="trend_analysis.png"
)
```

### 4. HTML Reports

```python
from src.reporting import HTMLReportGenerator
from pathlib import Path

# Initialize generator
generator = HTMLReportGenerator(Path("output/reports"))

# Generate comprehensive report
report_path = generator.generate_report(
    title="Experiment Results",
    phase="Phase 1",
    executive_summary="<p>Key findings...</p>",
    statistical_results={
        'mann_whitney': mw_results,
        'mann_kendall': mk_results
    },
    image_paths=[img1, img2, img3],
    group_comparisons={
        'Hybrid': {'n': 100, 'median_sharpe': 0.55, ...},
        'FG-Only': {'n': 100, 'median_sharpe': 0.48, ...}
    },
    recommendations="<p>Recommendations...</p>"
)

print(f"Report saved to: {report_path}")
```

## Advanced Usage

### Pairwise Comparisons

```python
from src.analysis.statistical import MannWhitneyAnalyzer

groups = {
    'Hybrid': [0.5, 0.52, 0.55, ...],
    'FG-Only': [0.45, 0.47, 0.46, ...],
    'LLM-Only': [0.48, 0.50, 0.49, ...]
}

# Compare all pairs
results = MannWhitneyAnalyzer.compare_all_pairs(groups)

for (g1, g2), result in results.items():
    print(f"{g1} vs {g2}: p={result.p_value:.4f}")
```

### Trend Analysis by Group

```python
from src.analysis.statistical import MannKendallAnalyzer

group_data = {
    'Hybrid': [0.5, 0.52, 0.55, ...],
    'FG-Only': [0.45, 0.47, 0.46, ...],
    'LLM-Only': [0.48, 0.50, 0.49, ...]
}

# Detect trends for all groups
trends = MannKendallAnalyzer.detect_trends_by_group(group_data)

for group_name, result in trends.items():
    print(f"{group_name}: {result.trend} (p={result.p_value:.4f})")
```

### Sliding Window Trend Analysis

```python
from src.analysis.statistical import MannKendallAnalyzer

values = [0.5, 0.51, 0.52, ...]  # 100 iterations

# Analyze trends in windows
windows = MannKendallAnalyzer.sliding_window_trends(
    values,
    window_size=20,
    step_size=10
)

for start, end, result in windows:
    print(f"Window [{start}:{end}]: {result.trend}")
```

### Comparative Trends Visualization

```python
from src.visualization import ExperimentVisualizer
from src.analysis.statistical import MannKendallAnalyzer

viz = ExperimentVisualizer(Path("output"))

# Detect trends
trends = MannKendallAnalyzer.detect_trends_by_group(group_data)

# Plot comparative trends
viz.plot_comparative_trends(
    group_data,
    trends,
    title="Learning Trends Comparison",
    save_name="comparative_trends.png"
)
```

## Result Objects

### MannWhitneyResult

```python
result = mann_whitney_test(group1, group2)

# Attributes:
result.statistic       # U-statistic
result.p_value         # p-value
result.significant     # True if p < alpha
result.effect_size     # Rank-biserial correlation
result.group1_median   # Median of group 1
result.group2_median   # Median of group 2
result.group1_n        # Sample size group 1
result.group2_n        # Sample size group 2
result.test_type       # 'two-sided', 'greater', 'less'

# String representation:
print(result)  # Human-readable summary
```

### MannKendallResult

```python
result = detect_trend(values)

# Attributes:
result.trend          # 'increasing', 'decreasing', 'no trend'
result.p_value        # p-value
result.significant    # True if p < alpha
result.tau            # Kendall's tau
result.slope          # Sen's slope
result.z_score        # Normalized test statistic

# String representation:
print(result)  # Human-readable summary
```

## Common Patterns

### Complete Analysis Workflow

```python
from src.analysis.statistical import (
    MannWhitneyAnalyzer,
    MannKendallAnalyzer
)
from src.visualization import ExperimentVisualizer
from src.reporting import HTMLReportGenerator
from pathlib import Path

# 1. Prepare data
groups = {
    'Hybrid': [...],
    'FG-Only': [...],
    'LLM-Only': [...]
}

# 2. Statistical tests
mw_results = MannWhitneyAnalyzer.compare_all_pairs(groups)
mk_results = MannKendallAnalyzer.detect_trends_by_group(groups)

# 3. Visualizations
viz = ExperimentVisualizer(Path("output/plots"))
image_paths = [
    viz.plot_learning_curves(groups),
    viz.plot_distribution_comparison(groups),
    viz.plot_comparative_trends(groups, mk_results)
]

# 4. Generate report
generator = HTMLReportGenerator(Path("output/reports"))
report = generator.generate_report(
    title="Experiment Results",
    phase="Phase 1",
    executive_summary="...",
    statistical_results={'mann_whitney': mw_results, 'mann_kendall': mk_results},
    image_paths=image_paths,
    group_comparisons=compute_stats(groups),
    recommendations="..."
)
```

## Error Handling

### Common Errors

```python
# Empty data
try:
    result = mann_whitney_test([], [1, 2, 3])
except ValueError as e:
    print(e)  # "Both groups must contain at least one value"

# Insufficient data
try:
    result = detect_trend([1.0, 2.0])
except ValueError as e:
    print(e)  # "Need at least 3 values for trend detection"

# Invalid values
try:
    result = mann_whitney_test([1, 2, np.nan], [4, 5, 6])
except ValueError as e:
    print(e)  # "Groups contain NaN or infinite values"
```

## Performance Tips

1. **Use pairwise comparisons efficiently:**
   ```python
   # Good: Single call for all pairs
   results = MannWhitneyAnalyzer.compare_all_pairs(groups)

   # Less efficient: Multiple individual calls
   result1 = mann_whitney_test(group1, group2)
   result2 = mann_whitney_test(group1, group3)
   # ...
   ```

2. **Choose appropriate window sizes:**
   ```python
   # For 100 iterations:
   windows = MannKendallAnalyzer.sliding_window_trends(
       values,
       window_size=20,  # 20% of data
       step_size=5      # 5% step
   )
   ```

3. **Batch visualizations:**
   ```python
   viz = ExperimentVisualizer(output_dir)
   # All plots use same instance, avoiding re-initialization
   ```

## Testing

```bash
# Run all Track 3 tests
python3 -m pytest tests/analysis/statistical/ tests/visualization/ tests/reporting/ -v

# Run specific test file
python3 -m pytest tests/analysis/statistical/test_mann_whitney.py -v

# Run with coverage
python3 -m pytest tests/analysis/statistical/ --cov=src/analysis/statistical
```

## Demo

```bash
# Run complete demo
PYTHONPATH=/mnt/c/Users/jnpi/documents/finlab python3 examples/track3_statistical_pipeline_demo.py

# Output will be in: output/track3_demo/
```

## API Reference

### Statistical Module
- `mann_whitney_test(group1, group2, alternative='two-sided', alpha=0.05)`
- `MannWhitneyAnalyzer.compare_groups(group1, group2, alternative, alpha)`
- `MannWhitneyAnalyzer.compare_all_pairs(groups, alternative, alpha)`
- `detect_trend(values, alpha=0.05)`
- `MannKendallAnalyzer.detect_trend(values, alpha)`
- `MannKendallAnalyzer.detect_trends_by_group(group_data, alpha)`
- `MannKendallAnalyzer.sliding_window_trends(values, window_size, step_size, alpha)`

### Visualization Module
- `ExperimentVisualizer(output_dir)`
- `.plot_learning_curves(group_data, title, ylabel, save_name, ...)`
- `.plot_distribution_comparison(group_data, title, save_name, ...)`
- `.plot_novelty_vs_performance(novelty, sharpe, group_name, save_name, ...)`
- `.plot_trend_analysis(values, trend_result, title, save_name, ...)`
- `.plot_comparative_trends(group_data, trend_results, title, save_name, ...)`

### Reporting Module
- `HTMLReportGenerator(output_dir)`
- `.generate_report(title, phase, executive_summary, statistical_results, image_paths, group_comparisons, recommendations, output_filename)`
- `.generate_quick_summary(mann_whitney_results, mann_kendall_results, output_filename)`

---

For detailed documentation, see `TRACK3_COMPLETION_SUMMARY.md`
