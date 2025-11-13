# Golden Master Test Fixtures - Quick Reference

**File**: `tests/learning/test_golden_master_deterministic.py`
**Purpose**: Fixture infrastructure for Golden Master Test
**Status**: ✅ Ready for use in Task H1.1.3

---

## Available Fixtures

### 1. `fixed_dataset`
**Type**: `pd.DataFrame`
**Purpose**: Fixed market data (2020-2024)

```python
def test_my_test(fixed_dataset):
    data = fixed_dataset
    assert 'close' in data
    assert data['start_date'] == '2020-01-01'
    assert data['end_date'] == '2024-12-31'
```

**Features**:
- Real FinLab data if available
- Synthetic fallback (seed=42)
- Deterministic date range

---

### 2. `fixed_config`
**Type**: `Dict`
**Purpose**: Fixed system configuration

```python
def test_my_test(fixed_config):
    config = fixed_config
    assert config['iteration']['max'] == 5
    assert config['llm']['enabled'] is False
    assert config['sandbox']['enabled'] is True
```

**Configuration**:
```python
{
    'iteration': {'max': 5, 'timeout': 60, 'seed': 42},
    'llm': {'enabled': False, 'provider': 'openrouter'},
    'sandbox': {'enabled': True, ...},
    'backtest': {'resample': 'M', 'fee_ratio': 0.001425/3, ...}
}
```

---

### 3. `canned_strategy`
**Type**: `str`
**Purpose**: Fixed strategy code (no LLM)

```python
def test_my_test(canned_strategy):
    code = canned_strategy
    assert 'def strategy' in code
    assert 'data.get' in code
    # Use code for backtesting
    exec(code)  # Executes MA20 strategy
```

**Strategy**: Simple MA20 crossover
```python
close = data.get('price:收盤價')
ma20 = close.rolling(window=20).mean()
signal = close > ma20
```

---

### 4. `mock_llm_client`
**Type**: `Mock`
**Purpose**: Mock LLMClient (returns canned strategy)

```python
def test_my_test(mock_llm_client):
    client = mock_llm_client

    # Check LLM is "enabled"
    assert client.is_enabled() is True

    # Get mock engine
    engine = client.get_engine()

    # Generate strategy (returns canned_strategy)
    strategy = engine.generate_strategy()
    assert 'def strategy' in strategy

    # Generate mutation (deterministic)
    mutation = engine.generate_mutation(strategy, iteration=1)
    assert 'window=25' in mutation  # MA window changed
```

**Mutation Logic**:
- Iteration 0: MA window = 20
- Iteration 1: MA window = 25
- Iteration 2: MA window = 30
- Iteration 3: MA window = 20 (repeat)

---

### 5. `golden_master_baseline`
**Type**: `Dict`
**Purpose**: Load golden master baseline data

```python
def test_my_test(golden_master_baseline):
    baseline = golden_master_baseline

    # Check if baseline exists
    if baseline.get('baseline_exists') is False:
        pytest.skip("Golden master baseline not generated yet")

    # Use baseline for validation
    expected_sharpe = baseline['final_champion']['sharpe_ratio']
    assert abs(actual_sharpe - expected_sharpe) < 0.01
```

**Baseline Format**:
```python
{
    "config": {"seed": 42, "iterations": 5},
    "final_champion": {
        "sharpe_ratio": 1.2345,
        "max_drawdown": -0.15,
        "total_return": 0.45
    },
    "iteration_outcomes": [
        {"id": 0, "success": true, "sharpe": 0.8},
        {"id": 1, "success": true, "sharpe": 1.1},
        ...
    ],
    "history_entries": 5,
    "trade_count": 42
}
```

**Baseline Location**: `tests/fixtures/golden_master_baseline.json`

---

### 6. `reset_test_state` (autouse)
**Type**: `None`
**Purpose**: Reset global state (automatic)

```python
# No need to explicitly use this fixture
# It runs automatically before each test

def test_my_test():
    # ConfigManager is already reset
    # numpy seed is already set to 42
    pass
```

**Actions**:
- Resets ConfigManager singleton
- Sets numpy seed to 42
- Cleans up after test

---

## Usage Examples

### Example 1: Test with Mock LLM
```python
def test_autonomous_loop_with_mock(
    mock_llm_client,
    fixed_dataset,
    fixed_config
):
    """Test autonomous loop with mocked LLM."""
    loop = AutonomousLoop(
        config=fixed_config,
        llm_client=mock_llm_client
    )

    results = loop.run(data=fixed_dataset, iterations=5)

    assert results.success_count > 0
    assert results.champion is not None
```

### Example 2: Test with Golden Master
```python
def test_golden_master_validation(
    mock_llm_client,
    fixed_dataset,
    fixed_config,
    golden_master_baseline
):
    """Validate refactored code against golden master."""
    # Skip if baseline doesn't exist
    if golden_master_baseline.get('baseline_exists') is False:
        pytest.skip("Baseline not generated")

    # Run refactored code
    loop = AutonomousLoop(
        config=fixed_config,
        llm_client=mock_llm_client
    )
    results = loop.run(data=fixed_dataset, iterations=5)

    # Compare against baseline
    expected = golden_master_baseline['final_champion']['sharpe_ratio']
    actual = results.champion.sharpe_ratio

    assert abs(actual - expected) < 0.01, "Sharpe ratio mismatch"
```

### Example 3: Test Determinism
```python
def test_deterministic_behavior(
    mock_llm_client,
    fixed_dataset,
    fixed_config
):
    """Verify same inputs produce same outputs."""
    loop1 = AutonomousLoop(config=fixed_config, llm_client=mock_llm_client)
    loop2 = AutonomousLoop(config=fixed_config, llm_client=mock_llm_client)

    results1 = loop1.run(data=fixed_dataset, iterations=5)
    results2 = loop2.run(data=fixed_dataset, iterations=5)

    # Should produce identical results (deterministic)
    assert results1.champion.sharpe_ratio == results2.champion.sharpe_ratio
```

---

## Common Patterns

### Pattern 1: Skip if Baseline Missing
```python
def test_requires_baseline(golden_master_baseline):
    if not golden_master_baseline.get('baseline_exists', True):
        pytest.skip("Generate baseline first: python scripts/generate_golden_master.py")

    # Test code here
```

### Pattern 2: Validate Within Tolerance
```python
def test_with_tolerance(actual_value, expected_value):
    TOLERANCE = 0.01
    assert abs(actual_value - expected_value) < TOLERANCE, \
        f"Value mismatch: {actual_value} vs {expected_value}"
```

### Pattern 3: Multiple Iterations
```python
def test_multiple_runs(mock_llm_client, fixed_dataset, fixed_config):
    results = []
    for i in range(3):
        loop = AutonomousLoop(config=fixed_config, llm_client=mock_llm_client)
        result = loop.run(data=fixed_dataset, iterations=5)
        results.append(result.champion.sharpe_ratio)

    # All runs should produce same result (deterministic)
    assert len(set(results)) == 1, "Results are not deterministic"
```

---

## Troubleshooting

### Issue: "FinLab data not available"
**Solution**: Fixture will use synthetic data automatically
```python
def test_my_test(fixed_dataset):
    if fixed_dataset.get('is_synthetic'):
        pytest.skip("Test requires real FinLab data")
```

### Issue: "Baseline file not found"
**Solution**: Generate baseline first
```bash
# Checkout pre-refactor commit
git checkout <pre-refactor-commit>

# Generate baseline
python scripts/generate_golden_master.py --iterations 5 --seed 42

# Return to current branch
git checkout feature/learning-system-enhancement
```

### Issue: "Test is not deterministic"
**Check**:
1. Are you using `fixed_config` (has seed=42)?
2. Is `reset_test_state` running (autouse)?
3. Are you using `mock_llm_client` (eliminates LLM randomness)?

---

## Next Steps (Task H1.1.3)

1. **Import fixtures**:
   ```python
   from test_golden_master_deterministic import (
       fixed_dataset,
       fixed_config,
       canned_strategy,
       mock_llm_client,
       golden_master_baseline
   )
   ```

2. **Implement golden master test**:
   - Load baseline
   - Run refactored autonomous loop
   - Compare outputs
   - Validate within tolerance

3. **Run test**:
   ```bash
   pytest tests/learning/test_golden_master_deterministic.py::test_golden_master -v
   ```

---

**Reference**: WEEK1_HARDENING_PLAN.md (Task H1.1.1)
**Status**: ✅ Infrastructure Complete
**Next**: Task H1.1.2 (Generate Baseline)
