# Template System Testing Guide

## Overview

The template system uses a comprehensive fixture-based testing approach with mocked Finlab data structures. This design enables fast, reliable, and CI/CD-friendly tests without requiring API access or external dependencies.

**Key Achievements**:
- 74 tests implemented (45% over target of 51)
- 91% average coverage across template modules
- 2.76-3.38 second execution time (99% faster than 5-minute target)
- 100% pass rate
- Zero API dependencies

## Test Infrastructure

### Test Datasets

The testing system uses 12 curated datasets stored in `datasets_curated_50.json`:

1. **price** - Historical price data (OHLCV)
2. **volume** - Trading volume data
3. **revenue** - Company revenue data
4. **revenue_growth** - Quarter-over-quarter revenue growth
5. **operating_margin** - Operating profit margins
6. **roa** - Return on Assets
7. **roe** - Return on Equity
8. **current_ratio** - Liquidity ratio
9. **debt_ratio** - Debt to equity ratio
10. **dividend_yield** - Dividend yield percentage
11. **market_cap** - Market capitalization
12. **pe_ratio** - Price-to-earnings ratio

Each dataset includes:
- 50 stocks (2330.TW, 2317.TW, 2454.TW, etc.)
- 500 trading days of historical data
- Realistic values with proper data types
- Complete coverage for all template operations

### MockFinlabDataFrame

Custom mock implementation that simulates `finlab.data.FinlabDataFrame` behavior:

**Core Features**:
- Arithmetic operations: `+, -, *, /, //, %, **`
- Comparison operations: `<, <=, >, >=, ==, !=`
- Rolling window operations via `MockRolling`
- Boolean indexing and filtering
- Method chaining support
- Statistical functions: `mean()`, `std()`, `sum()`, `abs()`

**MockRolling Capabilities**:
- `mean()`, `std()`, `max()`, `min()`, `sum()`
- Proper chaining: `data.rolling(20).mean().rolling(5).std()`
- Window size validation
- NaN handling for insufficient data

**Key Implementation Details**:
```python
# Rolling operations work correctly
ma_20 = close.rolling(20).mean()  # MockFinlabDataFrame
volatility = returns.rolling(20).std()  # MockFinlabDataFrame

# Arithmetic operations
upper_band = ma_20 + (volatility * 2)  # Works
lower_band = ma_20 - (volatility * 2)  # Works

# Comparisons return MockFinlabDataFrame (not boolean)
signal = close > upper_band  # MockFinlabDataFrame with 0/1 values
```

### Mock Strategy

**What's Mocked**:
- `finlab.data.FinlabDataFrame` - Custom implementation
- `finlab.data.get()` - Returns MockFinlabDataFrame from fixtures
- `finlab.backtest.sim()` - Returns mock backtest results
- `finlab.data.Data` - Simulates data fetching interface

**What's Real**:
- Template classes (TurtleTemplate, MastiffTemplate, etc.)
- Template methods (generate, adjust_position)
- Parameter validation logic
- Genome processing
- Hall of Fame repository operations
- File I/O operations

**Why This Approach**:
- Fast execution: No API calls or network delays
- Deterministic: Same inputs always produce same outputs
- CI/CD friendly: No credentials or external dependencies
- Complete control: Can test edge cases and error conditions

## Test Organization

```
tests/
├── conftest.py                 # Shared fixtures (50+ fixtures)
├── templates/
│   ├── test_turtle_template.py        # 14 tests, 92% coverage
│   ├── test_mastiff_template.py       # 12 tests, 89% coverage
│   ├── test_factor_template.py        # 13 tests, 91% coverage
│   └── test_momentum_template.py      # 12 tests, 93% coverage
├── repository/
│   └── test_hall_of_fame.py           # 17 tests, 88% coverage
└── integration/
    └── test_integration.py            # 6 tests, end-to-end workflows
```

**Test Categories**:
- **Template Tests (51)**: Unit tests for individual template methods
- **Repository Tests (17)**: Hall of Fame CRUD operations
- **Integration Tests (6)**: End-to-end template→backtest→save workflows

## Running Tests

### Basic Commands

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=src/templates --cov=src/repository --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser

# Run specific test file
pytest tests/templates/test_turtle_template.py -v

# Run specific test function
pytest tests/templates/test_turtle_template.py::test_turtle_generate_basic -v
```

### Test Selection

```bash
# Run only unit tests (fast, no integration)
pytest tests/ -m "unit" -v

# Run only integration tests
pytest tests/ -m "integration" -v

# Exclude slow tests (for quick validation)
pytest tests/ -m "not slow" -v

# Exclude API-dependent tests (for CI/CD)
pytest tests/ -m "not requires_api" -v

# Fast CI/CD test suite
pytest tests/ -m "not slow and not requires_api" --cov=src
```

### Coverage Analysis

```bash
# Module-specific coverage
pytest tests/templates/ --cov=src/templates --cov-report=term
pytest tests/repository/ --cov=src/repository --cov-report=term

# Detailed missing lines report
pytest tests/ --cov=src --cov-report=term-missing

# Coverage threshold enforcement (fail if below 80%)
pytest tests/ --cov=src --cov-fail-under=80
```

### Debugging

```bash
# Show full stack traces
pytest tests/ -v --tb=long

# Show local variables in tracebacks
pytest tests/ -v --tb=long --showlocals

# Drop into debugger on failure
pytest tests/ -v --pdb

# Stop on first failure
pytest tests/ -v -x

# Show captured stdout/stderr
pytest tests/ -v -s
```

## Coverage Metrics

### Template Modules

| Module | Tests | Coverage | Key Areas |
|--------|-------|----------|-----------|
| TurtleTemplate | 14 | 92% | generate, adjust_position, signals |
| MastiffTemplate | 12 | 89% | generate, factor interactions |
| FactorTemplate | 13 | 91% | generate, multi-factor logic |
| MomentumTemplate | 12 | 93% | generate, momentum indicators |

### Repository Modules

| Module | Tests | Coverage | Key Areas |
|--------|-------|----------|-----------|
| HallOfFame | 17 | 88% | CRUD operations, validation, filtering |

### Overall Metrics

- **Total Tests**: 74
- **Average Coverage**: 91%
- **Pass Rate**: 100% (74/74)
- **Execution Time**: 2.76-3.38 seconds
- **Lines Covered**: 850+ out of 950 total

## Key Implementation Details

### 1. MockRolling for Chained Operations

**Problem**: Rolling operations need to support chaining:
```python
ma = close.rolling(20).mean()
volatility = returns.rolling(20).std().rolling(5).mean()
```

**Solution**: MockRolling returns MockFinlabDataFrame, which has `.rolling()` method:
```python
class MockRolling:
    def mean(self) -> MockFinlabDataFrame:
        result = self.df.copy()
        # Apply rolling mean calculation
        return MockFinlabDataFrame(result)  # Enables chaining
```

### 2. test_mode for Hall of Fame Path Validation

**Problem**: Hall of Fame tests need to verify file paths without actual file I/O:
```python
def test_save_creates_proper_paths(hall_of_fame, tmp_path):
    # Need to check tmp_path was used, but save() would fail
    hall_of_fame.save(genome, backtest_result)
    # How to verify tmp_path was used?
```

**Solution**: test_mode flag that bypasses file operations but allows path inspection:
```python
@pytest.fixture
def hall_of_fame(tmp_path):
    return HallOfFame(
        data_dir=tmp_path,
        test_mode=True  # Bypasses file I/O, enables validation
    )
```

In HallOfFame:
```python
def save(self, genome, backtest_result):
    if not self.test_mode:
        self.storage.save(filename, genome)
    else:
        # Store for test verification
        self._last_saved_path = self.data_dir / filename
```

### 3. Deep Copy Requirement for Genome Fixtures

**Problem**: Tests were failing due to shared mutable state:
```python
@pytest.fixture
def turtle_genome():
    return {
        'parameters': {'entry_window': 20, 'exit_window': 10},
        'backtest_result': {...}
    }

def test_modify_genome(turtle_genome):
    turtle_genome['parameters']['entry_window'] = 30  # Modifies fixture!
    # Next test sees modified value
```

**Solution**: Deep copy in conftest.py:
```python
import copy

@pytest.fixture
def turtle_genome():
    base = {
        'parameters': {'entry_window': 20, 'exit_window': 10},
        'backtest_result': {...}
    }
    return copy.deepcopy(base)  # Fresh copy for each test
```

### 4. Comparison Operations Return MockFinlabDataFrame

**Problem**: Templates use comparisons for signals:
```python
buy_signal = close > upper_band  # Should be FinlabDataFrame, not bool
position = position.where(buy_signal, 0)  # Requires DataFrame
```

**Solution**: Override comparison operators to return MockFinlabDataFrame:
```python
class MockFinlabDataFrame:
    def __gt__(self, other):
        result = (self.df > self._extract_value(other)).astype(int)
        return MockFinlabDataFrame(result)  # Not bool
```

### 5. Statistical Methods Delegate to Pandas

**Problem**: Templates use `.mean()`, `.std()`, `.sum()` on DataFrames:
```python
average_volume = volume.rolling(20).mean()
volatility = returns.std()
```

**Solution**: Delegate to underlying pandas DataFrame:
```python
class MockFinlabDataFrame:
    def mean(self, *args, **kwargs):
        return MockFinlabDataFrame(self.df.mean(*args, **kwargs))

    def std(self, *args, **kwargs):
        return MockFinlabDataFrame(self.df.std(*args, **kwargs))
```

## Troubleshooting

### Common Issues

#### 1. "AttributeError: 'MockFinlabDataFrame' has no attribute 'X'"

**Cause**: Template uses method not implemented in mock.

**Solution**: Add method to MockFinlabDataFrame:
```python
class MockFinlabDataFrame:
    def shift(self, periods=1):
        return MockFinlabDataFrame(self.df.shift(periods))
```

#### 2. "TypeError: unsupported operand type(s)"

**Cause**: Arithmetic operation not implemented.

**Solution**: Check __add__, __sub__, __mul__, __truediv__ implementations.

#### 3. "ValueError: The truth value of a DataFrame is ambiguous"

**Cause**: Comparison returning bool instead of MockFinlabDataFrame.

**Solution**: Ensure comparison operators return MockFinlabDataFrame:
```python
def __gt__(self, other):
    return MockFinlabDataFrame((self.df > value).astype(int))
```

#### 4. "KeyError: 'dataset_name'"

**Cause**: Dataset not loaded in mock_finlab_data fixture.

**Solution**: Add dataset to datasets_curated_50.json and conftest.py:
```python
@pytest.fixture
def mock_finlab_data(mocker, sample_datasets):
    def mock_get(name):
        if name not in sample_datasets:
            raise KeyError(f"Dataset {name} not found")
        return MockFinlabDataFrame(sample_datasets[name])
```

#### 5. Tests Pass Individually but Fail Together

**Cause**: Shared mutable state between tests.

**Solution**: Use `copy.deepcopy()` in fixtures:
```python
@pytest.fixture
def my_fixture():
    return copy.deepcopy(BASE_DATA)
```

#### 6. "FileNotFoundError" in Hall of Fame Tests

**Cause**: test_mode not enabled.

**Solution**: Set test_mode=True in fixture:
```python
@pytest.fixture
def hall_of_fame(tmp_path):
    return HallOfFame(data_dir=tmp_path, test_mode=True)
```

### Performance Issues

#### Slow Test Execution

**Symptoms**: Tests take >10 seconds to run.

**Solutions**:
1. Mark slow tests with `@pytest.mark.slow`
2. Use smaller datasets in fixtures
3. Mock expensive operations (API calls, file I/O)
4. Run parallel: `pytest -n auto` (requires pytest-xdist)

#### High Memory Usage

**Symptoms**: Tests consume >1GB RAM.

**Solutions**:
1. Use generator fixtures instead of loading all data upfront
2. Clear large objects after tests: `df = None`
3. Reduce dataset size in fixtures
4. Use `pytest --forked` to isolate tests

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest tests/ \
          -m "not requires_api" \
          --cov=src \
          --cov-report=xml \
          --cov-report=term

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running tests..."
pytest tests/ -m "not slow and not requires_api" -q

if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi

echo "All tests passed!"
exit 0
```

## Best Practices

### Writing New Tests

1. **Use Existing Fixtures**: Leverage conftest.py fixtures for consistency
2. **Test One Thing**: Each test should verify a single behavior
3. **Descriptive Names**: `test_turtle_generate_with_custom_windows` > `test_1`
4. **Arrange-Act-Assert**: Structure tests clearly
5. **Use Markers**: Tag tests appropriately (unit, integration, slow)
6. **Deep Copy Mutable Data**: Prevent test pollution

### Example Test Structure

```python
def test_turtle_generate_with_custom_windows(turtle_template, sample_genome):
    # Arrange
    sample_genome['parameters']['entry_window'] = 30
    sample_genome['parameters']['exit_window'] = 15

    # Act
    result = turtle_template.generate(sample_genome)

    # Assert
    assert result is not None
    assert 'position' in result
    assert result['position'].shape[0] > 0
    assert all(result['position'].abs() <= 1)
```

### Adding New Datasets

1. Add to `datasets_curated_50.json`:
```json
{
  "new_dataset": {
    "2330.TW": [1.0, 2.0, 3.0, ...],
    "2317.TW": [1.5, 2.5, 3.5, ...]
  }
}
```

2. Update `sample_datasets` fixture in conftest.py:
```python
@pytest.fixture
def sample_datasets():
    with open('datasets_curated_50.json', 'r') as f:
        data = json.load(f)
    return {
        'price': pd.DataFrame(data['price']),
        'new_dataset': pd.DataFrame(data['new_dataset'])  # Add here
    }
```

3. Use in tests:
```python
def test_with_new_dataset(mock_finlab_data):
    data = finlab.data.get('new_dataset')  # Works automatically
```

## Maintenance

### Updating Mocks

When Finlab library adds new features:

1. Check if templates use new features
2. Add to MockFinlabDataFrame if needed
3. Update tests to cover new features
4. Run full test suite to verify compatibility

### Coverage Goals

- **Minimum**: 80% per module
- **Target**: 90% per module
- **Ideal**: 95% with meaningful edge cases

### Test Review Checklist

- [ ] All tests passing
- [ ] Coverage ≥80% per module
- [ ] No skipped tests without reason
- [ ] Fixtures properly isolated (deep copy)
- [ ] Integration tests cover key workflows
- [ ] Documentation updated
- [ ] CI/CD pipeline working

## Resources

- **pytest Documentation**: https://docs.pytest.org/
- **pytest-cov Plugin**: https://pytest-cov.readthedocs.io/
- **Finlab Documentation**: (internal reference)
- **Template System Architecture**: `docs/architecture/TEMPLATE_SYSTEM.md`

## Revision History

- 2025-10-12: Initial comprehensive testing guide
  - 74 tests, 91% average coverage
  - MockFinlabDataFrame with rolling operations
  - Fixture-based approach with deep copy
  - test_mode for Hall of Fame validation
