# Population-Based Evolution System - User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Concept Overview](#concept-overview)
3. [Quick Start](#quick-start)
4. [Command-Line Interface](#command-line-interface)
5. [Configuration Parameters](#configuration-parameters)
6. [Running Validation](#running-validation)
7. [Understanding Results](#understanding-results)
8. [Integration Testing](#integration-testing)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

The Population-Based Evolution System replaces the previous single-champion learning approach with a **multi-objective evolutionary algorithm (NSGA-II)**. Instead of iteratively improving one strategy, the system maintains a diverse population of strategies and evolves them over multiple generations using genetic operations.

**Key Benefits:**
- **Diversity**: Maintains multiple high-performing strategies instead of one
- **Multi-Objective Optimization**: Balances Sharpe ratio, Calmar ratio, and max drawdown
- **Robustness**: Explores different regions of the strategy space simultaneously
- **Pareto Front**: Identifies trade-offs between competing objectives

**Target Users:**
- Quantitative researchers developing trading strategies
- Financial analysts exploring strategy optimization
- System integrators testing population evolution workflows

---

## Concept Overview

### What is Population-Based Learning?

**Traditional Approach (Single-Champion):**
```
Initialize champion → Evaluate → Mutate → Compare → Update champion → Repeat
```
- Only one strategy at a time
- Greedy optimization (local optima risk)
- Single objective (Sharpe ratio only)

**Population-Based Approach (NSGA-II):**
```
Initialize population (N=20) → Evaluate all →
  Pareto ranking → Selection → Crossover → Mutation →
    Replace old population → Repeat
```
- Multiple strategies evolved simultaneously (N=20)
- Genetic diversity through crossover and mutation
- Multi-objective optimization (Sharpe, Calmar, max drawdown)
- Pareto front identifies non-dominated solutions

### NSGA-II Algorithm Overview

**NSGA-II** (Non-dominated Sorting Genetic Algorithm II) is a fast multi-objective evolutionary algorithm:

1. **Non-dominated Sorting**: Assign Pareto ranks (rank 1 = Pareto front)
2. **Crowding Distance**: Measure diversity within each rank
3. **Tournament Selection**: Select parents based on rank and crowding distance
4. **Crossover**: Combine parameters from two parents
5. **Mutation**: Randomly modify parameters for exploration
6. **Elitism**: Preserve best strategies across generations

**Pareto Optimality:**
- A strategy is **Pareto-optimal** if no other strategy is better in all objectives
- The **Pareto front** is the set of all Pareto-optimal strategies
- Represents trade-offs (e.g., high Sharpe but lower Calmar vs. balanced)

### Evolution Workflow

```
Generation 0: Random initialization (N=20)
│
├─ Backtest all strategies
├─ Assign Pareto ranks
├─ Calculate crowding distances
│
Generation 1-20:
│
├─ Tournament selection (select parents)
├─ Crossover (combine parent parameters)
├─ Mutation (explore variations)
├─ Evaluate offspring
├─ Combine parents + offspring
├─ Non-dominated sorting
├─ Select top N=20 for next generation
│
Final: Pareto front with diverse high-performing strategies
```

---

## Quick Start

### Prerequisites

```bash
# Required dependencies
pip install numpy scipy matplotlib finlab

# Optional for visualization
pip install plotly seaborn

# Set FinLab API token
export FINLAB_API_TOKEN="your_token_here"
```

### Basic Usage (10 Generations)

```bash
# Run evolution for 10 generations with default settings
python run_population_evolution.py --generations 10

# Expected output:
# ╔════════════════════════════════════════════════════════════╗
# ║       Population-Based Strategy Evolution System           ║
# ║                  NSGA-II Multi-Objective                   ║
# ╚════════════════════════════════════════════════════════════╝
#
# GENERATION 1/10 (10.0% complete)
# ======================================================================
# Population Size:     20
# Offspring Created:   10
# Diversity Score:     0.752
# Pareto Front Size:   5
# Best Sharpe Ratio:   1.823
# Best Calmar Ratio:   2.145
# ...
```

### Validation Run (20 Generations)

```bash
# Run production validation with statistical analysis
python run_20generation_validation.py --generations 20 --population-size 20

# Generates VALIDATION_REPORT.md with:
# - Champion update rate
# - Rolling variance
# - Statistical significance (t-test)
# - Pareto front size
```

### Integration Testing

```bash
# Run full integration test suite
pytest tests/integration/test_full_evolution.py -v

# Expected output:
# tests/integration/test_full_evolution.py::test_scenario1_full_evolution_run PASSED
# tests/integration/test_full_evolution.py::test_scenario2_diversity_recovery_mechanism PASSED
# tests/integration/test_full_evolution.py::test_scenario3_elitism_preserves_best_strategies PASSED
# tests/integration/test_full_evolution.py::test_scenario4_crossover_all_parameter_types PASSED
# tests/integration/test_full_evolution.py::test_scenario5_pareto_front_correctness PASSED
# tests/integration/test_full_evolution.py::test_scenario5_pareto_dominance PASSED
# ============================== 6 passed in 1.55s ==============================
```

---

## Command-Line Interface

### `run_population_evolution.py` - Main Evolution CLI

**Purpose:** Run population-based evolution with configurable parameters and real-time progress display.

**Syntax:**
```bash
python run_population_evolution.py [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--population-size` | int | 20 | Number of strategies in population |
| `--generations` | int | 10 | Number of generations to evolve |
| `--elite-count` | int | 2 | Number of elite strategies to preserve |
| `--tournament-size` | int | 3 | Tournament size for parent selection |
| `--mutation-rate` | float | 0.1 | Initial mutation rate (0.0-1.0) |
| `--checkpoint-dir` | str | `checkpoints` | Directory for saving checkpoints |
| `--output-dir` | str | `evolution_output` | Directory for results and plots |
| `--verbose` | flag | False | Enable verbose logging (DEBUG level) |

**Examples:**

```bash
# Small test run (5 strategies, 5 generations)
python run_population_evolution.py --population-size 5 --generations 5

# Production run with high elitism
python run_population_evolution.py \
  --population-size 30 \
  --generations 20 \
  --elite-count 5 \
  --tournament-size 5 \
  --verbose

# Custom checkpoint location
python run_population_evolution.py \
  --generations 15 \
  --checkpoint-dir ./my_checkpoints \
  --output-dir ./my_results
```

**Output Files:**

- `checkpoints/generation_N.json` - Checkpoint files for each generation
- `checkpoints/final_population.json` - Final population state
- `evolution_output/generation_N_pareto.png` - Pareto front visualizations
- `evolution_output/diversity.png` - Diversity trend over generations
- `population_evolution.log` - Detailed execution log

**Progress Display:**

```
======================================================================
GENERATION 5/10 (50.0% complete)
======================================================================
Population Size:     20
Offspring Created:   12
Diversity Score:     0.681
Pareto Front Size:   6
Best Sharpe Ratio:   2.145
Best Calmar Ratio:   2.876

Timing Breakdown:
  Selection:  12.34s
  Crossover:  8.56s
  Mutation:   5.23s
  Evaluation: 45.67s
  Total:      71.80s
```

### `run_20generation_validation.py` - Validation CLI

**Purpose:** Run comprehensive 20-generation validation with statistical analysis and success criteria evaluation.

**Syntax:**
```bash
python run_20generation_validation.py [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--population-size` | int | 20 | Population size (production: N=20) |
| `--generations` | int | 20 | Number of generations (production: 20) |
| `--elite-count` | int | 2 | Elite strategies to preserve |
| `--tournament-size` | int | 3 | Tournament selection size |
| `--mutation-rate` | float | 0.1 | Initial mutation rate |
| `--checkpoint-dir` | str | `validation_checkpoints` | Checkpoint directory |
| `--output-file` | str | `VALIDATION_REPORT.md` | Report output file |
| `--verbose` | flag | False | Enable verbose logging |

**Examples:**

```bash
# Standard validation run
python run_20generation_validation.py

# Custom configuration
python run_20generation_validation.py \
  --population-size 30 \
  --generations 25 \
  --output-file MY_VALIDATION.md

# Verbose output for debugging
python run_20generation_validation.py --verbose
```

**Success Criteria:**

1. **Champion Update Rate ≥10%**: At least 10% of generations show champion improvement
2. **Rolling Variance <0.5**: Final generation Sharpe ratio variance below 0.5
3. **P-value <0.05**: Statistically significant improvement over random baseline (t-test)
4. **Pareto Front Size ≥5**: Final Pareto front contains at least 5 strategies

**Output Files:**

- `VALIDATION_REPORT.md` - Comprehensive validation report
- `validation_checkpoints/generation_N.json` - Generation checkpoints
- `validation_evolution.log` - Detailed log

**Report Structure:**

```markdown
# Validation Report: Population-Based Evolution

## Executive Summary
- **Overall Status**: ✅ PASS (4/4 criteria met)
- **Population Size**: 20
- **Generations**: 20
- **Timestamp**: 2025-10-19 14:30:00

## Success Criteria Results
| Criterion | Status | Actual | Threshold | Details |
|-----------|--------|--------|-----------|---------|
| Champion Update Rate | ✅ PASS | 15.0% | ≥10% | 3 updates in 20 generations |
| Rolling Variance | ✅ PASS | 0.3421 | <0.5 | Low variance = good convergence |
| Statistical Significance | ✅ PASS | p=0.0012 | <0.05 | Cohen's d = 1.34 (large effect) |
| Pareto Front Size | ✅ PASS | 7 | ≥5 | Good diversity maintained |

## Detailed Analysis
...
```

---

## Configuration Parameters

### Population Size (`--population-size`)

**Default:** 20

**Recommendations:**
- **Small (5-10)**: Quick testing, debugging
- **Medium (20-30)**: Production runs, balanced diversity
- **Large (50+)**: Extensive exploration, high compute budget

**Trade-offs:**
- Larger populations = better diversity, slower execution
- Smaller populations = faster execution, risk of premature convergence

### Generations (`--generations`)

**Default:** 10

**Recommendations:**
- **Short (5-10)**: Smoke tests, quick validation
- **Medium (20-30)**: Production validation, stability testing
- **Long (50+)**: Extensive optimization, research

**Convergence Indicators:**
- Diversity score plateau (e.g., stable around 0.3-0.5)
- Champion update rate drops below 5%
- Pareto front size stabilizes

### Elite Count (`--elite-count`)

**Default:** 2

**Recommendations:**
- **Low (1-2)**: Aggressive exploration, risk of losing good strategies
- **Medium (3-5)**: Balanced preservation, recommended for production
- **High (10%)**: Conservative, high elitism pressure

**Formula:** Elite count = 10-20% of population size

**Trade-offs:**
- Higher elitism = faster convergence, risk of premature convergence
- Lower elitism = more exploration, risk of losing best strategies

### Tournament Size (`--tournament-size`)

**Default:** 3

**Recommendations:**
- **Small (2-3)**: Weak selection pressure, high diversity
- **Medium (4-5)**: Balanced selection pressure
- **Large (7+)**: Strong selection pressure, aggressive convergence

**Trade-offs:**
- Larger tournament = stronger selection pressure = faster convergence
- Smaller tournament = weaker selection pressure = more exploration

### Mutation Rate (`--mutation-rate`)

**Default:** 0.1 (10%)

**Recommendations:**
- **Low (0.05-0.1)**: Fine-tuning, late-stage optimization
- **Medium (0.1-0.2)**: Balanced exploration
- **High (0.3+)**: Aggressive exploration, early-stage search

**Adaptive Mutation:**
- System automatically increases mutation rate when diversity drops below 0.3
- Maximum adaptive rate: 0.3 (30%)

---

## Running Validation

### Step-by-Step Validation Workflow

**1. Prepare Environment:**

```bash
# Ensure dependencies installed
pip install -r requirements.txt

# Set API token
export FINLAB_API_TOKEN="your_token"

# Verify environment
python -c "import src.evolution.population_manager; print('✅ Import successful')"
```

**2. Run Integration Tests:**

```bash
# Full test suite (6 tests)
pytest tests/integration/test_full_evolution.py -v

# Individual scenario tests
pytest tests/integration/test_full_evolution.py::test_scenario1_full_evolution_run -v
pytest tests/integration/test_full_evolution.py::test_scenario2_diversity_recovery_mechanism -v
```

**3. Run Validation:**

```bash
# Standard 20-generation validation
python run_20generation_validation.py

# Monitor progress (real-time)
tail -f validation_evolution.log
```

**4. Review Report:**

```bash
# View validation report
cat VALIDATION_REPORT.md

# Check for failures
grep "❌ FAIL" VALIDATION_REPORT.md

# Extract executive summary
head -20 VALIDATION_REPORT.md
```

### Interpreting Validation Results

**✅ PASS (All Criteria Met):**
```
Overall Status: ✅ PASS (4/4 criteria met)
```
- System is production-ready
- Evolution algorithm functioning correctly
- Population maintains diversity and improves over time

**⚠️ PARTIAL PASS (Some Criteria Failed):**

**Scenario 1: Low Champion Update Rate**
```
Champion Update Rate: ❌ FAIL | 5.0% | ≥10%
```
- **Diagnosis**: Population converged too quickly or mutation rate too low
- **Action**: Increase mutation rate, decrease elite count, or increase tournament size

**Scenario 2: High Rolling Variance**
```
Rolling Variance: ❌ FAIL | 0.812 | <0.5
```
- **Diagnosis**: Population diversity too high or insufficient convergence
- **Action**: Increase generations, increase elite count, or increase tournament size

**Scenario 3: Not Statistically Significant**
```
Statistical Significance: ❌ FAIL | p=0.067 | <0.05
```
- **Diagnosis**: Evolution not significantly better than random baseline
- **Action**: Increase generations, check backtest configuration, verify data quality

**Scenario 4: Small Pareto Front**
```
Pareto Front Size: ❌ FAIL | 3 | ≥5
```
- **Diagnosis**: Excessive convergence or insufficient diversity
- **Action**: Increase population size, increase mutation rate, decrease elite count

---

## Understanding Results

### Checkpoint Files

**Structure:** `checkpoints/generation_N.json`

```json
{
  "generation": 5,
  "population_size": 20,
  "strategies": [
    {
      "id": "strategy_gen5_001",
      "code": "...",
      "parameters": {
        "factor_weights": {"momentum": 0.4, "value": 0.3, "quality": 0.3},
        "entry_threshold": 0.15,
        "exit_threshold": 0.05,
        "rebalance_frequency": "monthly"
      },
      "metrics": {
        "sharpe_ratio": 1.82,
        "calmar_ratio": 2.14,
        "max_drawdown": -0.18,
        "success": true
      },
      "pareto_rank": 1,
      "crowding_distance": 0.45
    },
    ...
  ],
  "diversity_score": 0.681,
  "generation_time": 71.8
}
```

**Key Fields:**
- `pareto_rank`: 1 = Pareto front (best), 2+ = dominated solutions
- `crowding_distance`: Higher = more unique (preferred for diversity)
- `diversity_score`: Population-wide diversity metric (0.3-0.7 ideal)

### Pareto Front Interpretation

**Example Pareto Front (5 strategies):**

| Strategy ID | Sharpe | Calmar | Max DD | Trade-off |
|-------------|--------|--------|--------|-----------|
| strategy_001 | **2.15** | 1.98 | -0.15 | High Sharpe, moderate risk |
| strategy_002 | 1.92 | **2.45** | -0.12 | Balanced |
| strategy_003 | 1.78 | 2.12 | **-0.08** | Low drawdown, lower returns |
| strategy_004 | 2.05 | 2.23 | -0.14 | Well-rounded |
| strategy_005 | 1.85 | 2.38 | -0.10 | Calmar-focused |

**Selecting a Strategy:**
1. **Aggressive investor**: Choose high Sharpe (strategy_001)
2. **Conservative investor**: Choose low max drawdown (strategy_003)
3. **Balanced investor**: Choose middle ground (strategy_004)

**Ensemble Strategy:**
- Combine multiple Pareto-optimal strategies
- Allocate capital across top 3-5 strategies
- Reduces single-strategy risk

### Diversity Score

**Interpretation:**

| Range | Interpretation | Action |
|-------|----------------|--------|
| 0.7-1.0 | Very high diversity | Exploration phase, early generations |
| 0.5-0.7 | Good diversity | Healthy balance |
| 0.3-0.5 | Moderate diversity | Convergence phase |
| 0.1-0.3 | Low diversity | Risk of premature convergence |
| <0.1 | Very low diversity | **Warning:** Population collapsed |

**Diversity Calculation:**
- Average pairwise Hamming distance between strategy parameters
- Considers factor weights, thresholds, and rebalance frequency
- Normalized to [0, 1] range

### Generation Timing

**Typical Breakdown (N=20, 1 generation):**

```
Selection:   12.3s (17%)  ← Tournament selection
Crossover:   8.5s (12%)   ← Parameter combination
Mutation:    5.2s (7%)    ← Random exploration
Evaluation:  45.6s (64%)  ← Backtest execution (dominant)
Total:       71.8s
```

**Optimization Opportunities:**
- **Evaluation**: Parallelize backtests, cache data, optimize backtest code
- **Selection**: Vectorize tournament selection
- **Crossover/Mutation**: Batch parameter operations

---

## Integration Testing

### Test Suite Overview

**File:** `tests/integration/test_full_evolution.py`

**Test Scenarios:**

1. **Scenario 1: Full Evolution Run (N=20, 5 generations)**
   - Validates complete evolution workflow
   - Checks population size preservation
   - Verifies offspring creation
   - Validates diversity maintenance

2. **Scenario 2: Diversity Recovery Mechanism**
   - Creates homogeneous population (diversity < 0.3)
   - Verifies adaptive mutation rate increase
   - Validates diversity recovery after mutation

3. **Scenario 3: Elitism Preservation**
   - Verifies elite strategies never lost across generations
   - Checks elite_count parameter enforcement
   - Validates fitness preservation

4. **Scenario 4: Crossover Compatibility**
   - Tests crossover with all parameter types
   - Verifies factor weight normalization
   - Validates parameter inheritance

5. **Scenario 5: Pareto Front Correctness**
   - Validates non-domination relationships
   - Checks Pareto rank assignment
   - Verifies front size and composition

### Running Tests

**Full Suite:**
```bash
pytest tests/integration/test_full_evolution.py -v
```

**Individual Tests:**
```bash
# Test 1: Full evolution
pytest tests/integration/test_full_evolution.py::test_scenario1_full_evolution_run -v

# Test 2: Diversity recovery
pytest tests/integration/test_full_evolution.py::test_scenario2_diversity_recovery_mechanism -v

# Test 3: Elitism
pytest tests/integration/test_full_evolution.py::test_scenario3_elitism_preserves_best_strategies -v

# Test 4: Crossover
pytest tests/integration/test_full_evolution.py::test_scenario4_crossover_all_parameter_types -v

# Test 5: Pareto front
pytest tests/integration/test_full_evolution.py::test_scenario5_pareto_front_correctness -v
pytest tests/integration/test_full_evolution.py::test_scenario5_pareto_dominance -v
```

**Expected Output:**
```
tests/integration/test_full_evolution.py::test_scenario1_full_evolution_run PASSED     [16%]
tests/integration/test_full_evolution.py::test_scenario2_diversity_recovery_mechanism PASSED [33%]
tests/integration/test_full_evolution.py::test_scenario3_elitism_preserves_best_strategies PASSED [50%]
tests/integration/test_full_evolution.py::test_scenario4_crossover_all_parameter_types PASSED [66%]
tests/integration/test_full_evolution.py::test_scenario5_pareto_front_correctness PASSED [83%]
tests/integration/test_full_evolution.py::test_scenario5_pareto_dominance PASSED      [100%]

============================== 6 passed in 1.55s ==============================
```

### Test Fixtures

**Population Sizes:**
- `manager_n20`: N=20 (production configuration)
- `manager_n10`: N=10 (testing configuration)
- `manager_n5`: N=5 (small testing configuration)

**Usage in Custom Tests:**
```python
import pytest
from src.evolution.population_manager import PopulationManager

def test_custom_evolution(manager_n20):
    """Custom test using N=20 fixture."""
    initial_pop = manager_n20.initialize_population()
    assert len(initial_pop) == 20

    result = manager_n20.evolve_generation(1)
    assert result.population.size == 20
```

---

## Best Practices

### Production Recommendations

**Standard Configuration:**
```bash
python run_population_evolution.py \
  --population-size 20 \
  --generations 20 \
  --elite-count 2 \
  --tournament-size 3 \
  --mutation-rate 0.1
```

**Conservative (High Quality):**
```bash
python run_population_evolution.py \
  --population-size 30 \
  --generations 30 \
  --elite-count 5 \
  --tournament-size 5 \
  --mutation-rate 0.08
```

**Exploratory (High Diversity):**
```bash
python run_population_evolution.py \
  --population-size 40 \
  --generations 25 \
  --elite-count 2 \
  --tournament-size 2 \
  --mutation-rate 0.15
```

### Checkpoint Management

**Automatic Checkpoints:**
- Saved every generation in `checkpoint_dir`
- Include full population state
- Can be used for recovery after interruption

**Recovery from Checkpoint:**
```python
from src.evolution.population_manager import PopulationManager

# Load checkpoint
manager = PopulationManager(population_size=20)
manager.load_checkpoint('checkpoints/generation_10.json')

# Continue from generation 11
for gen in range(11, 21):
    result = manager.evolve_generation(gen)
    manager.save_checkpoint(f'checkpoints/generation_{gen}.json')
```

### Performance Optimization

**1. Parallelize Backtests:**
```python
# In backtest code, use multiprocessing
from multiprocessing import Pool

def evaluate_population(strategies):
    with Pool(processes=4) as pool:
        metrics = pool.map(backtest_strategy, strategies)
    return metrics
```

**2. Cache Data:**
```python
# Cache finlab data to avoid repeated downloads
from src.data.finlab_data import FinlabDataCache

cache = FinlabDataCache(cache_dir='data_cache')
price_data = cache.get_price_data()  # Cached after first call
```

**3. Monitor Diversity:**
```python
# Stop early if diversity collapses
if result.diversity_score < 0.1:
    print("⚠️ Warning: Diversity collapsed, stopping early")
    break
```

### Strategy Selection

**Multi-Strategy Portfolio:**
```python
# Load final population
import json
with open('checkpoints/final_population.json') as f:
    final_pop = json.load(f)

# Get Pareto front
pareto_front = [s for s in final_pop['strategies'] if s['pareto_rank'] == 1]

# Allocate capital across top 5
top_5 = sorted(pareto_front, key=lambda s: s['metrics']['sharpe_ratio'], reverse=True)[:5]
allocation = {s['id']: 0.2 for s in top_5}  # Equal weight

print(f"Portfolio allocation: {allocation}")
```

**Risk-Adjusted Selection:**
```python
# Select strategy with best Sharpe/Calmar balance
def risk_adjusted_score(strategy):
    sharpe = strategy['metrics']['sharpe_ratio']
    calmar = strategy['metrics']['calmar_ratio']
    return 0.6 * sharpe + 0.4 * calmar

best_strategy = max(pareto_front, key=risk_adjusted_score)
print(f"Best risk-adjusted strategy: {best_strategy['id']}")
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Diversity Collapses Quickly

**Symptoms:**
```
GENERATION 5/10 (50.0% complete)
Diversity Score:     0.082  ← Very low!
```

**Diagnosis:**
- Elite count too high
- Mutation rate too low
- Tournament size too large

**Solution:**
```bash
# Increase exploration
python run_population_evolution.py \
  --elite-count 1 \           # Lower elitism
  --mutation-rate 0.2 \       # Higher mutation
  --tournament-size 2         # Weaker selection
```

#### Issue 2: No Champion Updates

**Symptoms:**
```
Champion Update Rate: 0.0% (0 updates in 20 generations)
```

**Diagnosis:**
- Population converged immediately
- Initial population quality too high
- Mutation not creating improvements

**Solution:**
1. Increase mutation rate: `--mutation-rate 0.15`
2. Increase population size: `--population-size 30`
3. Check backtest configuration (may be too noisy)

#### Issue 3: All Strategies Fail Backtest

**Symptoms:**
```
GENERATION 1/10 (10.0% complete)
Best Sharpe Ratio:   0.000  ← No valid metrics!
```

**Diagnosis:**
- Backtest configuration error
- Data unavailable
- API token invalid

**Solution:**
```bash
# Verify environment
export FINLAB_API_TOKEN="your_token"
python -c "from src.data.finlab_data import get_price_data; print(get_price_data().head())"

# Check backtest configuration
pytest tests/backtest/test_metrics.py -v
```

#### Issue 4: Tests Fail with AttributeError

**Symptoms:**
```
AttributeError: 'NoneType' object has no attribute 'sharpe_ratio'
```

**Diagnosis:**
- Strategy metrics are None (backtest failed)
- Need to filter strategies before accessing metrics

**Solution:**
```python
# Filter strategies with valid metrics first
valid_strategies = [s for s in population if s.metrics is not None]

if not valid_strategies:
    pytest.skip("No strategies with valid metrics")

# Now safe to access metrics
best_sharpe = max(s.metrics.sharpe_ratio for s in valid_strategies)
```

#### Issue 5: Slow Evolution Performance

**Symptoms:**
```
Evaluation: 450.6s (95%)  ← Dominant time spent in backtest
Total:      471.2s
```

**Diagnosis:**
- Backtest code not optimized
- Data downloaded repeatedly
- No parallelization

**Solution:**
1. **Cache data:**
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=1)
   def get_cached_price_data():
       return get_price_data()
   ```

2. **Parallelize backtests:**
   ```python
   from concurrent.futures import ProcessPoolExecutor

   with ProcessPoolExecutor(max_workers=4) as executor:
       metrics = list(executor.map(backtest_strategy, strategies))
   ```

3. **Optimize backtest:**
   ```python
   # Use vectorized pandas operations instead of loops
   returns = (price_data.pct_change() * signals).sum(axis=1)
   ```

### Debug Mode

**Enable verbose logging:**
```bash
python run_population_evolution.py --verbose
```

**Check logs:**
```bash
# View full log
cat population_evolution.log

# Filter for errors
grep "ERROR" population_evolution.log

# Monitor in real-time
tail -f population_evolution.log
```

**Test individual components:**
```bash
# Test population manager
pytest tests/evolution/test_population_manager.py -v

# Test multi-objective functions
pytest tests/evolution/test_multi_objective.py -v

# Test selection manager
pytest tests/evolution/test_selection_manager.py -v
```

---

## Appendix

### Algorithm Parameters Reference

| Parameter | Symbol | Default | Range | Effect |
|-----------|--------|---------|-------|--------|
| Population Size | N | 20 | 5-100 | Diversity vs. speed |
| Generations | G | 10 | 5-100 | Convergence quality |
| Elite Count | E | 2 | 1-N/5 | Preservation vs. exploration |
| Tournament Size | T | 3 | 2-7 | Selection pressure |
| Mutation Rate | μ | 0.1 | 0.05-0.3 | Exploration vs. exploitation |
| Crossover Rate | χ | 0.7 | 0.5-0.9 | Information exchange |

### Metrics Glossary

**Sharpe Ratio:**
- Measures risk-adjusted returns
- Formula: (Mean Return - Risk-Free Rate) / Std Dev of Returns
- Higher is better (>1.0 good, >2.0 excellent)

**Calmar Ratio:**
- Measures return relative to maximum drawdown
- Formula: Annualized Return / Max Drawdown
- Higher is better (>1.0 good, >2.0 excellent)

**Maximum Drawdown:**
- Largest peak-to-trough decline
- Expressed as negative percentage (e.g., -0.15 = -15%)
- Closer to 0 is better (lower risk)

**Pareto Rank:**
- 1 = Pareto front (non-dominated)
- 2 = Dominated by rank 1
- 3+ = Further dominated

**Crowding Distance:**
- Diversity measure within Pareto rank
- Higher = more unique
- Used for tie-breaking in selection

**Diversity Score:**
- Population-wide parameter diversity
- Range: [0, 1]
- Formula: Average pairwise Hamming distance

### File Structure

```
finlab/
├── run_population_evolution.py          # Main CLI
├── run_20generation_validation.py       # Validation CLI
├── checkpoints/                         # Auto-generated checkpoints
│   ├── generation_0.json
│   ├── generation_1.json
│   └── final_population.json
├── evolution_output/                    # Auto-generated results
│   ├── generation_1_pareto.png
│   └── diversity.png
├── tests/integration/
│   └── test_full_evolution.py          # Integration tests
├── src/evolution/
│   ├── population_manager.py           # Main evolution logic
│   ├── multi_objective.py              # NSGA-II implementation
│   ├── selection_manager.py            # Tournament selection
│   ├── crossover.py                    # Genetic crossover
│   ├── mutation.py                     # Genetic mutation
│   └── visualization.py                # Plotting functions
└── docs/
    └── POPULATION_EVOLUTION_GUIDE.md   # This guide
```

### Further Reading

**NSGA-II Algorithm:**
- Deb, K., et al. (2002). "A fast and elitist multiobjective genetic algorithm: NSGA-II"
- IEEE Transactions on Evolutionary Computation, 6(2), 182-197

**Multi-Objective Optimization:**
- Coello, C. A. C., et al. (2007). "Evolutionary Algorithms for Solving Multi-Objective Problems"
- Springer Science & Business Media

**Trading Strategy Optimization:**
- Pardo, R. (2008). "The Evaluation and Optimization of Trading Strategies"
- John Wiley & Sons

**Population-Based Training:**
- Jaderberg, M., et al. (2017). "Population Based Training of Neural Networks"
- arXiv preprint arXiv:1711.09846

---

## Support

For issues, questions, or contributions:
- **Bug Reports**: Open an issue on GitHub
- **Feature Requests**: Submit a feature request
- **Documentation**: Refer to this guide and inline code comments
- **Community**: Join discussions on project forums

**Version:** 1.0.0
**Last Updated:** 2025-10-19
**Maintainer:** FinLab Evolution Team
