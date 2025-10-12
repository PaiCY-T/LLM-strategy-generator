# Template System Tests

Comprehensive test suite for the Finlab template system with 74 tests achieving 91% average coverage.

## Quick Start

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/templates --cov=src/repository --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Organization

```
tests/
├── conftest.py                     # 50+ shared fixtures
├── templates/
│   ├── test_turtle_template.py     # 14 tests, 92% coverage
│   ├── test_mastiff_template.py    # 12 tests, 89% coverage
│   ├── test_factor_template.py     # 13 tests, 91% coverage
│   └── test_momentum_template.py   # 12 tests, 93% coverage
├── repository/
│   └── test_hall_of_fame.py        # 17 tests, 88% coverage
└── integration/
    └── test_integration.py         # 6 tests, end-to-end workflows
```

## Test Categories

### Unit Tests (51 tests)
Fast, isolated tests for individual template methods:
```bash
pytest tests/templates/ -v
```

### Repository Tests (17 tests)
Hall of Fame CRUD operations and validation:
```bash
pytest tests/repository/ -v
```

### Integration Tests (6 tests)
End-to-end workflows from template generation to backtesting:
```bash
pytest tests/integration/ -v -m integration
```

## CI/CD Integration

Fast test suite optimized for continuous integration:
```bash
# Run tests suitable for CI/CD (no API dependencies, exclude slow tests)
pytest tests/ -m "not requires_api and not slow" --cov=src

# With coverage threshold enforcement
pytest tests/ -m "not requires_api" --cov=src --cov-fail-under=80
```

## Test Fixtures

All tests use fixtures from `conftest.py`:

### Data Fixtures
- `sample_datasets` - 12 curated datasets (price, volume, financials)
- `mock_finlab_data` - Mocked Finlab data interface
- `mock_backtest` - Mocked backtesting results

### Template Fixtures
- `turtle_template`, `mastiff_template`, `factor_template`, `momentum_template`
- Pre-configured template instances with test mode enabled

### Genome Fixtures
- `turtle_genome`, `mastiff_genome`, `factor_genome`, `momentum_genome`
- Complete strategy configurations with parameters

### Repository Fixtures
- `hall_of_fame` - Hall of Fame instance with test mode and temp directory
- `sample_strategy` - Example strategy for testing persistence

## Performance

- **Execution Time**: 2.76-3.38 seconds for full suite
- **Coverage**: 91% average across template modules
- **Pass Rate**: 100% (74/74 tests passing)
- **No External Dependencies**: All tests use mocked data

## Fixture Generation

The test suite uses 12 datasets from `datasets_curated_50.json`:
- 50 stocks per dataset
- 500 trading days of data
- Realistic values with proper data types

To regenerate fixtures (if needed):
```bash
python scripts/generate_test_fixtures.py  # If such script exists
```

## Debugging

```bash
# Show full stack traces
pytest tests/ -v --tb=long

# Show local variables in tracebacks
pytest tests/ -v --tb=long --showlocals

# Drop into debugger on failure
pytest tests/ -v --pdb

# Stop on first failure
pytest tests/ -v -x
```

## Common Commands

```bash
# Run specific test file
pytest tests/templates/test_turtle_template.py -v

# Run specific test
pytest tests/templates/test_turtle_template.py::test_turtle_generate_basic -v

# Run tests matching pattern
pytest tests/ -k "turtle" -v

# Show test durations
pytest tests/ --durations=10

# Parallel execution (requires pytest-xdist)
pytest tests/ -n auto
```

## Coverage Reports

```bash
# Terminal report with missing lines
pytest tests/ --cov=src --cov-report=term-missing

# HTML report (open htmlcov/index.html)
pytest tests/ --cov=src --cov-report=html

# XML report (for CI/CD tools)
pytest tests/ --cov=src --cov-report=xml

# Multiple report formats
pytest tests/ --cov=src --cov-report=term --cov-report=html --cov-report=xml
```

## Pre-commit Hook

To run tests before each commit:
```bash
# Create .git/hooks/pre-commit
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
pytest tests/ -m "not slow and not requires_api" -q
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

## Documentation

For comprehensive testing documentation, see:
- **[TEMPLATE_SYSTEM_TESTING.md](../docs/architecture/TEMPLATE_SYSTEM_TESTING.md)** - Complete testing guide
  - Test infrastructure details
  - MockFinlabDataFrame implementation
  - Troubleshooting guide
  - Best practices

## Contributing

When adding new tests:
1. Use existing fixtures from conftest.py
2. Follow naming convention: `test_<module>_<function>_<scenario>`
3. Mark tests appropriately: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
4. Ensure coverage ≥80% for new modules
5. Update this README if adding new test categories

## Test Markers

Available markers (defined in pytest.ini):
- `unit` - Fast unit tests with no external dependencies
- `integration` - Integration tests involving multiple components
- `slow` - Tests taking >1 second
- `requires_api` - Tests requiring Finlab API access (CI/CD should skip)

Usage:
```bash
# Run only unit tests
pytest tests/ -m unit

# Exclude slow tests
pytest tests/ -m "not slow"

# CI/CD friendly
pytest tests/ -m "not requires_api and not slow"
```

## Maintenance

### Updating Test Data
If Finlab data schema changes:
1. Update `datasets_curated_50.json`
2. Update `MockFinlabDataFrame` in conftest.py
3. Run full test suite to verify compatibility

### Adding New Templates
When adding new template classes:
1. Create test file: `tests/templates/test_new_template.py`
2. Add fixtures to conftest.py if needed
3. Target ≥80% coverage
4. Add integration test in `test_integration.py`

### Coverage Goals
- **Minimum**: 80% per module
- **Target**: 90% per module
- **Current**: 91% average (exceeding target)

## Resources

- **pytest Documentation**: https://docs.pytest.org/
- **pytest-cov Plugin**: https://pytest-cov.readthedocs.io/
- **Template System Architecture**: `../docs/architecture/TEMPLATE_SYSTEM.md`
- **Testing Guide**: `../docs/architecture/TEMPLATE_SYSTEM_TESTING.md`
