# Template System Architecture

## Overview

The Template System provides a modular, extensible framework for strategy generation and backtesting in the Finlab platform. It supports multiple strategy types through a plugin architecture with consistent interfaces.

## Core Components

### Template Classes

#### Base Template Interface
All templates implement:
- `generate(genome)` - Generate trading signals from parameters
- `adjust_position(position)` - Apply position size adjustments
- `validate_parameters(parameters)` - Validate parameter ranges

#### Implemented Templates

1. **TurtleTemplate** - Trend-following breakout strategy
   - Entry/exit window configuration
   - ATR-based position sizing
   - Breakout signal generation

2. **MastiffTemplate** - Multi-factor strategy
   - Factor combination (momentum + value + quality)
   - Weighted scoring system
   - Dynamic rebalancing

3. **FactorTemplate** - Factor-based strategy
   - Multiple factor selection
   - Factor normalization
   - Percentile-based signals

4. **MomentumTemplate** - Momentum-based strategy
   - Multiple momentum indicators
   - Signal strength calculation
   - Trend confirmation

### Hall of Fame Repository

Persistent storage for high-performing strategies:
- JSON-based storage format
- CRUD operations (create, read, update, delete)
- Filtering and sorting capabilities
- Metadata tracking (performance, timestamps)

## Testing

The template system includes a comprehensive test suite with 74 tests achieving 91% average coverage across all modules.

### Quick Start

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/templates --cov=src/repository --cov-report=term-missing

# Fast CI/CD tests (no API dependencies)
pytest tests/ -m "not requires_api" --cov=src
```

### Test Coverage

| Module | Tests | Coverage | Status |
|--------|-------|----------|--------|
| TurtleTemplate | 14 | 92% | ✅ |
| MastiffTemplate | 12 | 89% | ✅ |
| FactorTemplate | 13 | 91% | ✅ |
| MomentumTemplate | 12 | 93% | ✅ |
| HallOfFame | 17 | 88% | ✅ |
| Integration | 6 | N/A | ✅ |

### Key Features

- **Fast Execution**: <4 seconds for full suite (99% faster than target)
- **No API Dependencies**: Fully mocked Finlab data structures
- **CI/CD Ready**: All tests pass without external services
- **Comprehensive Fixtures**: 50+ reusable test fixtures

For detailed testing documentation, see [TEMPLATE_SYSTEM_TESTING.md](./TEMPLATE_SYSTEM_TESTING.md).

## Architecture Patterns

### Strategy Composition

Templates use a compositional approach:
1. **Data Fetching**: Retrieve market data via Finlab API
2. **Signal Generation**: Calculate technical indicators and signals
3. **Position Sizing**: Determine optimal position sizes
4. **Risk Management**: Apply risk controls and adjustments

### Genome Structure

Strategies are parameterized via genome dictionaries:
```python
genome = {
    'template': 'turtle',
    'parameters': {
        'entry_window': 20,
        'exit_window': 10,
        'position_size': 0.1
    },
    'backtest_result': {
        'final_return': 0.35,
        'sharpe_ratio': 1.2,
        'max_drawdown': -0.15
    }
}
```

### Extension Points

1. **New Templates**: Implement base template interface
2. **Custom Factors**: Add to FactorTemplate factor library
3. **Position Adjusters**: Extend adjust_position methods
4. **Validators**: Add custom parameter validation

## Integration with Learning System

Templates integrate with the Autonomous Iteration Engine:
1. **Generation**: Templates generate strategies from genomes
2. **Backtesting**: Finlab backtesting engine evaluates performance
3. **Feedback**: Results fed back for strategy evolution
4. **Persistence**: Top performers saved to Hall of Fame

## Performance Considerations

- **Lazy Loading**: Data fetched only when needed
- **Caching**: Repeated data access uses cached results
- **Vectorization**: Operations use pandas vectorized methods
- **Memory**: Large DataFrames managed carefully

## Future Enhancements

- Additional template types (pairs trading, mean reversion)
- Advanced position sizing algorithms
- Multi-asset portfolio construction
- Real-time strategy deployment

## References

- [Template System Testing Guide](./TEMPLATE_SYSTEM_TESTING.md) - Comprehensive testing documentation
- [Migration Guide](../MIGRATION_GUIDE.md) - Guide for updating existing code
- [Dataset Reference](../dataset_reference.md) - Available data sources
