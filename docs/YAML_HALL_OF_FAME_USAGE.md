# YAML Hall of Fame Usage Guide

## Quick Start

### Installation

```bash
pip install pyyaml
```

### Basic Usage

```python
from src.repository.hall_of_fame_yaml import HallOfFameRepository, StrategyGenome

# Initialize repository
repo = HallOfFameRepository()

# Create a strategy genome
genome = StrategyGenome(
    iteration_num=1,
    code="""
close = data.get('price:收盤價')
ma20 = close.average(20)
ma50 = close.average(50)
buy = (close > ma20) & (ma20 > ma50)
""",
    parameters={
        'n_stocks': 20,
        'ma_short': 20,
        'ma_long': 50
    },
    metrics={
        'sharpe_ratio': 2.3,
        'annual_return': 0.25,
        'max_drawdown': 0.15
    },
    success_patterns={
        'trend_following': True,
        'moving_average_crossover': True
    }
)

# Add to repository
success, message = repo.add_strategy(genome)
print(message)
# Output: Strategy added to champions tier (Sharpe: 2.30, ID: iter1_20251016T152717_2.30) | novelty: 1.000

# Retrieve champions
champions = repo.get_champions(limit=10)
for champ in champions:
    print(f"{champ.genome_id}: Sharpe {champ.metrics['sharpe_ratio']:.2f}")

# Get statistics
stats = repo.get_statistics()
print(stats)
# Output: {'champions': 1, 'contenders': 0, 'archive': 0, 'total': 1, ...}
```

---

## API Reference

### HallOfFameRepository

#### Initialization

```python
repo = HallOfFameRepository(
    base_path="hall_of_fame",  # Storage directory
    test_mode=False             # Enable for testing (disables security checks)
)
```

#### Adding Strategies

```python
success, message = repo.add_strategy(genome)
```

**Returns**:
- `success: bool` - True if added, False if duplicate or error
- `message: str` - Status message with details

**Automatic Features**:
- Novelty scoring (rejects duplicates < 0.2 similarity)
- Tier classification based on Sharpe ratio
- YAML file creation
- Vector caching for performance

#### Retrieving Strategies

```python
# Get top champions (Sharpe ≥ 2.0)
champions = repo.get_champions(limit=10, sort_by='sharpe_ratio')

# Get top contenders (Sharpe 1.5-2.0)
contenders = repo.get_contenders(limit=20, sort_by='sharpe_ratio')

# Get archived strategies (Sharpe < 1.5)
archive = repo.get_archive(limit=50, sort_by='sharpe_ratio')
```

#### Repository Statistics

```python
stats = repo.get_statistics()
# Returns: {
#     'champions': 15,
#     'contenders': 42,
#     'archive': 128,
#     'total': 185,
#     'total_backups': 3,
#     'storage_format': 'YAML'
# }
```

### StrategyGenome

#### Creating a Genome

```python
genome = StrategyGenome(
    iteration_num=100,           # Required: iteration number
    code="...",                  # Required: Python strategy code
    parameters={...},            # Required: parameter dict
    metrics={...},               # Required: must include 'sharpe_ratio'
    success_patterns={...},      # Optional: extracted patterns
    timestamp="2025-10-16T...",  # Optional: auto-generated if omitted
    genome_id="iter100_..."      # Optional: auto-generated if omitted
)
```

#### Serialization

```python
# To YAML string
yaml_str = genome.to_yaml()

# To dictionary
data_dict = genome.to_dict()

# Save to file
success = genome.save_to_file(Path('champions/genome.yaml'))

# Load from YAML string
genome = StrategyGenome.from_yaml(yaml_str)

# Load from file
genome = StrategyGenome.load_from_file(Path('champions/genome.yaml'))
```

---

## YAML File Format

### Example YAML File

```yaml
genome_id: iter1_20251016T152717_2.30
iteration_num: 1
timestamp: 2025-10-16T15:27:17.123456
code: |
  close = data.get('price:收盤價')
  ma20 = close.average(20)
  ma50 = close.average(50)
  buy = (close > ma20) & (ma20 > ma50)
parameters:
  n_stocks: 20
  ma_short: 20
  ma_long: 50
metrics:
  sharpe_ratio: 2.3
  annual_return: 0.25
  max_drawdown: 0.15
success_patterns:
  trend_following: true
  moving_average_crossover: true
```

### File Naming Convention

- Format: `{genome_id}.yaml`
- Example: `iter1_20251016T152717_2.30.yaml`

### Directory Structure

```
hall_of_fame/
├── champions/        # Sharpe ≥ 2.0
│   ├── iter5_20251016_120000_2.50.yaml
│   └── iter12_20251016_130000_2.30.yaml
├── contenders/       # Sharpe 1.5-2.0
│   ├── iter3_20251016_110000_1.80.yaml
│   └── iter8_20251016_115000_1.65.yaml
├── archive/          # Sharpe < 1.5
│   └── iter2_20251016_105000_1.20.yaml
└── backup/           # Failed serializations
    └── iter10_20251016_140000_2.10_failed.yaml
```

---

## Novelty Scoring

### How It Works

The repository automatically calculates novelty scores for new strategies:

1. **Factor Vector Extraction**: Analyzes strategy code for:
   - Dataset usage (e.g., `price:收盤價`, `monthly_revenue:當月營收`)
   - Technical indicators (MA, rolling windows, shifts)
   - Filter patterns (AND/OR combinations)
   - Selection methods (is_largest, is_smallest, rank)
   - Weighting patterns

2. **Cosine Distance**: Compares new strategy to all existing strategies
   - 0.0 = Identical (duplicate)
   - 1.0 = Completely different (novel)

3. **Duplicate Rejection**: Strategies with novelty < 0.2 are rejected

### Example

```python
# First strategy - completely novel
genome1 = StrategyGenome(
    iteration_num=1,
    code="close = data.get('price:收盤價')\nma = close.average(20)",
    parameters={'ma_period': 20},
    metrics={'sharpe_ratio': 2.3}
)
success, msg = repo.add_strategy(genome1)
# Output: True, "...novelty: 1.000"

# Second strategy - identical code
genome2 = StrategyGenome(
    iteration_num=2,
    code="close = data.get('price:收盤價')\nma = close.average(20)",  # Same!
    parameters={'ma_period': 20},
    metrics={'sharpe_ratio': 2.4}
)
success, msg = repo.add_strategy(genome2)
# Output: False, "Duplicate strategy rejected (novelty: 0.000, threshold: 0.2)..."
```

---

## Error Handling

### Backup on Failure

If YAML serialization fails, the genome is automatically backed up:

```
hall_of_fame/backup/{genome_id}_failed.yaml
```

The backup file includes error metadata:

```yaml
genome_id: iter10_20251016_140000_2.10
iteration_num: 10
# ... normal fields ...
_backup_metadata:
  intended_tier: champions
  error_message: "Serialization error: ..."
  backup_timestamp: "2025-10-16T14:00:00.123456"
  stack_trace: "Traceback (most recent call last): ..."
```

### Validation Errors

```python
# Missing required field
genome = StrategyGenome(
    iteration_num=1,
    code="...",
    parameters={},
    metrics={}  # Missing 'sharpe_ratio'!
)
success, msg = repo.add_strategy(genome)
# Output: False, "Metrics must include 'sharpe_ratio'"
```

---

## Performance Considerations

### Vector Caching

The repository caches factor vectors for performance:

```python
# First strategy: O(n) - extracts and caches vector
repo.add_strategy(genome1)

# Subsequent strategies: O(1) - uses cached vectors
repo.add_strategy(genome2)  # Fast!
repo.add_strategy(genome3)  # Fast!
```

### Performance Targets

- **Add Strategy**: <2s per strategy
- **Novelty Scoring**: <500ms for 100 strategies
- **Retrieve Champions**: <100ms (from cache)

---

## Comparison: JSON vs YAML

### JSON System (Existing)

```python
from src.repository.hall_of_fame import HallOfFameRepository, StrategyGenome

genome = StrategyGenome(
    template_name="TurtleTemplate",  # Template-based
    parameters={...},
    metrics={...},
    created_at="2025-01-10 12:00:00",  # Custom format
    strategy_code="...",
    success_patterns={...}
)
```

**Files**: `{genome_id}.json`

### YAML System (New)

```python
from src.repository.hall_of_fame_yaml import HallOfFameRepository, StrategyGenome

genome = StrategyGenome(
    iteration_num=100,          # Iteration-based
    code="...",
    parameters={...},
    metrics={...},
    timestamp="2025-10-16T15:27:17",  # ISO 8601
    success_patterns={...}
)
```

**Files**: `{genome_id}.yaml`

### Key Differences

| Feature | JSON System | YAML System |
|---------|-------------|-------------|
| **Format** | JSON | YAML |
| **Readability** | Good | Excellent |
| **Timestamp** | Custom format | ISO 8601 |
| **Identification** | template_name | iteration_num |
| **Code field** | strategy_code | code |
| **File extension** | .json | .yaml |

---

## Best Practices

### 1. Always Include Success Patterns

```python
genome = StrategyGenome(
    ...,
    success_patterns={
        'trend_following': True,
        'mean_reversion': False,
        'moving_average_periods': [20, 50],
        'key_datasets': ['price:收盤價', 'monthly_revenue:當月營收']
    }
)
```

### 2. Use Descriptive Parameters

```python
parameters = {
    'n_stocks': 20,
    'ma_short': 20,
    'ma_long': 50,
    'revenue_threshold': 1.05,
    'stop_loss': 0.06
}
```

### 3. Include Comprehensive Metrics

```python
metrics = {
    'sharpe_ratio': 2.3,        # Required
    'annual_return': 0.25,
    'max_drawdown': 0.15,
    'win_rate': 0.58,
    'profit_factor': 1.85,
    'total_trades': 120
}
```

### 4. Check Return Status

```python
success, message = repo.add_strategy(genome)
if not success:
    logger.warning(f"Failed to add strategy: {message}")
    # Handle duplicate or error
```

---

## Troubleshooting

### PyYAML Not Installed

```
RuntimeError: PyYAML not installed. Install with: pip install pyyaml
```

**Solution**:
```bash
pip install pyyaml
```

### Duplicate Rejected

```
Duplicate strategy rejected (novelty: 0.000, threshold: 0.2). Similar to strategy iter5_...
```

**Causes**:
- Identical or very similar code
- Same dataset usage patterns
- Same technical indicators

**Solution**:
- Modify strategy code to increase diversity
- Use different datasets
- Change indicator parameters

### Path Security Violation

```
ValueError: Security violation: base_path '../../etc' resolves to...
```

**Cause**: Attempted path traversal outside working directory

**Solution**:
- Use relative paths within project directory
- Or enable test_mode for testing: `HallOfFameRepository(test_mode=True)`

---

## Advanced Usage

### Custom Sorting

```python
# Sort by annual return instead of Sharpe
champions = repo.get_champions(limit=10, sort_by='annual_return')

# Sort by max drawdown (best = lowest)
from operator import itemgetter
champions = sorted(
    repo.get_champions(limit=100),
    key=lambda g: g.metrics.get('max_drawdown', 1.0)
)[:10]
```

### Filtering by Metric Range

```python
# Get high-Sharpe, high-return strategies
champions = repo.get_champions(limit=100)
high_performers = [
    c for c in champions
    if c.metrics.get('sharpe_ratio', 0) >= 2.5
    and c.metrics.get('annual_return', 0) >= 0.30
]
```

### Analyzing Success Patterns

```python
# Find common patterns among champions
champions = repo.get_champions(limit=50)
pattern_counts = {}

for champ in champions:
    if champ.success_patterns:
        for pattern, value in champ.success_patterns.items():
            if value:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

# Most common patterns
top_patterns = sorted(
    pattern_counts.items(),
    key=lambda x: x[1],
    reverse=True
)[:5]

print("Top 5 success patterns among champions:")
for pattern, count in top_patterns:
    print(f"  {pattern}: {count}/{len(champions)} ({count/len(champions)*100:.1f}%)")
```

---

## Integration with Learning Loop

The YAML Hall of Fame is designed to integrate seamlessly with the learning system:

```python
from src.repository.hall_of_fame_yaml import HallOfFameRepository, StrategyGenome

# In iteration loop
repo = HallOfFameRepository()

# After strategy generation and backtest
genome = StrategyGenome(
    iteration_num=current_iteration,
    code=generated_code,
    parameters=extracted_parameters,
    metrics=backtest_results,
    success_patterns=attributed_patterns
)

# Add to repository (automatic novelty check)
success, message = repo.add_strategy(genome)

if success:
    logger.info(f"Iteration {current_iteration}: {message}")

    # Get current best for comparison
    champions = repo.get_champions(limit=1)
    if champions:
        current_best = champions[0]
        logger.info(f"Current champion: {current_best.genome_id} (Sharpe: {current_best.metrics['sharpe_ratio']:.2f})")
else:
    logger.warning(f"Iteration {current_iteration}: {message}")
```

---

## Summary

The YAML Hall of Fame provides:

✅ **Human-readable storage** with YAML format
✅ **Automatic novelty detection** to prevent duplicates
✅ **Tier-based classification** (Champions/Contenders/Archive)
✅ **Performance optimization** with vector caching
✅ **Robust error handling** with automatic backups
✅ **Simple API** for easy integration

**Next**: See Tasks 19-25 for advanced query, maintenance, and pattern search features.
