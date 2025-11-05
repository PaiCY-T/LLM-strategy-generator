# Factor Library

Reusable factor library for the Factor Graph architecture. Provides pre-built factors extracted from templates, organized by category.

## Architecture

**Phase**: 2.0+ Factor Graph System
**Design Pattern**: Composable atomic factors with explicit dependencies
**Integration**: DataCache singleton for efficient data loading

## Factor Registry

**New in Task B.4**: Centralized Factor Registry for factor discovery, lookup, and management.

The Factor Registry provides a singleton registry for all available factors, enabling:
- **Factor Discovery**: Find factors by category or name
- **Parameter Validation**: Validate parameters before creation
- **Factory Management**: Create factors with validated parameters
- **Mutation Support**: Replace factors with same-category alternatives

### Basic Registry Usage

```python
from src.factor_library import FactorRegistry
from src.factor_graph.factor_category import FactorCategory

# Get registry instance (singleton)
registry = FactorRegistry.get_instance()

# List all available factors
all_factors = registry.list_factors()
print(f"Total factors: {len(all_factors)}")  # 13 factors

# Discover factors by category
momentum_factors = registry.get_momentum_factors()
exit_factors = registry.get_exit_factors()
entry_factors = registry.get_entry_factors()

# Get factor metadata
metadata = registry.get_metadata("momentum_factor")
print(f"Default parameters: {metadata['parameters']}")
print(f"Parameter ranges: {metadata['parameter_ranges']}")

# Create factor with custom parameters
factor = registry.create_factor(
    "momentum_factor",
    parameters={"momentum_period": 30}
)

# Validate parameters before creation
is_valid, msg = registry.validate_parameters(
    "momentum_factor",
    {"momentum_period": 50}
)
if is_valid:
    factor = registry.create_factor("momentum_factor", {"momentum_period": 50})
```

### Category-Based Discovery

```python
# Discover by category enum
momentum_factors = registry.list_by_category(FactorCategory.MOMENTUM)
exit_factors = registry.list_by_category(FactorCategory.EXIT)

# Or use convenience methods
momentum_factors = registry.get_momentum_factors()
value_factors = registry.get_value_factors()
quality_factors = registry.get_quality_factors()
risk_factors = registry.get_risk_factors()
exit_factors = registry.get_exit_factors()
entry_factors = registry.get_entry_factors()
```

### Parameter Validation

```python
# Validate before creating
params = {"momentum_period": 20}
is_valid, msg = registry.validate_parameters("momentum_factor", params)

if is_valid:
    factor = registry.create_factor("momentum_factor", params)
else:
    print(f"Invalid parameters: {msg}")

# Validation checks:
# - Parameter exists
# - Value within valid range
# - Type compatibility
```

### Mutation Scenarios

```python
# Original factor
original = registry.create_factor("momentum_factor")

# Discover same-category alternatives
alternatives = registry.get_momentum_factors()
# ['momentum_factor', 'ma_filter_factor', 'dual_ma_filter_factor']

# Replace with alternative (same category)
replacement = registry.create_factor("ma_filter_factor")

# Both are momentum factors, enabling category-aware mutation
assert original.category == replacement.category
```

### Available Factors in Registry

The registry automatically registers all 13 factors on first access:

**Momentum (3 factors)**:
- `momentum_factor`: Price momentum using rolling mean of returns
- `ma_filter_factor`: Moving average filter for trend confirmation
- `dual_ma_filter_factor`: Dual moving average filter

**Value (1 factor)**:
- `revenue_catalyst_factor`: Revenue acceleration catalyst detection

**Quality (1 factor)**:
- `earnings_catalyst_factor`: Earnings momentum catalyst (ROE improvement)

**Risk (1 factor)**:
- `atr_factor`: Average True Range for volatility measurement

**Entry (1 factor)**:
- `breakout_factor`: N-day breakout detection for entry signals

**Exit (6 factors)**:
- `atr_stop_loss_factor`: ATR-based stop loss
- `trailing_stop_factor`: Trailing stop loss that follows price
- `time_based_exit_factor`: Exit after N periods
- `volatility_stop_factor`: Volatility-based stop using std dev
- `profit_target_factor`: Fixed profit target exit
- `composite_exit_factor`: Combines multiple exit signals with OR logic

### Parameter Ranges

Each factor has predefined parameter ranges for validation:

```python
metadata = registry.get_metadata("momentum_factor")
print(metadata['parameter_ranges'])
# {'momentum_period': (5, 100)}

metadata = registry.get_metadata("dual_ma_filter_factor")
print(metadata['parameter_ranges'])
# {'short_ma': (5, 100), 'long_ma': (10, 200)}
```

See `examples/factor_registry_usage.py` for comprehensive usage examples.

## Available Factors

### Momentum Factors (from MomentumTemplate)

Momentum-related factors for trend-following strategies.

#### 1. MomentumFactor
**Purpose**: Calculate price momentum using rolling mean of returns

- **Category**: MOMENTUM
- **Inputs**: `["close"]`
- **Outputs**: `["momentum"]`
- **Parameters**:
  - `momentum_period` (int): Lookback period for momentum calculation
    - Common values: 5 (1 week), 10 (2 weeks), 20 (1 month), 30 (1.5 months)

**Example**:
```python
from src.factor_library import create_momentum_factor

momentum = create_momentum_factor(momentum_period=20)
data = pd.DataFrame({"close": [100, 102, 101, 103, 105]})
result = momentum.execute(data)
# result now has "momentum" column
```

#### 2. MAFilterFactor
**Purpose**: Moving average filter for trend confirmation

- **Category**: MOMENTUM
- **Inputs**: `["close"]`
- **Outputs**: `["ma_filter"]` (boolean)
- **Parameters**:
  - `ma_periods` (int): Moving average period for trend filter
    - Common values: 20 (1 month), 60 (3 months), 90 (4.5 months), 120 (6 months)

**Example**:
```python
from src.factor_library import create_ma_filter_factor

ma_filter = create_ma_filter_factor(ma_periods=60)
data = pd.DataFrame({"close": [100, 102, 101, 103, 105]})
result = ma_filter.execute(data)
# result now has "ma_filter" column (True when price > MA)
```

#### 3. RevenueCatalystFactor
**Purpose**: Revenue acceleration catalyst detection

- **Category**: VALUE
- **Inputs**: `["_dummy"]` (placeholder, uses DataCache internally)
- **Outputs**: `["revenue_catalyst"]` (boolean)
- **Parameters**:
  - `catalyst_lookback` (int): Lookback window for short-term MA in months
    - Common values: 2 (very recent), 3 (recent), 4 (short-term), 6 (medium-term)

**Example**:
```python
from src.factor_library import create_revenue_catalyst_factor

catalyst = create_revenue_catalyst_factor(catalyst_lookback=3)
data = pd.DataFrame({"_dummy": [True]})  # Placeholder
result = catalyst.execute(data)
# result now has "revenue_catalyst" column (True when revenue accelerating)
```

#### 4. EarningsCatalystFactor
**Purpose**: Earnings momentum catalyst detection using ROE

- **Category**: QUALITY
- **Inputs**: `["_dummy"]` (placeholder, uses DataCache internally)
- **Outputs**: `["earnings_catalyst"]` (boolean)
- **Parameters**:
  - `catalyst_lookback` (int): Lookback window for short-term ROE MA in quarters
    - Common values: 2 (very recent), 3 (recent), 4 (short-term), 6 (medium-term)

**Example**:
```python
from src.factor_library import create_earnings_catalyst_factor

catalyst = create_earnings_catalyst_factor(catalyst_lookback=3)
data = pd.DataFrame({"_dummy": [True]})  # Placeholder
result = catalyst.execute(data)
# result now has "earnings_catalyst" column (True when ROE improving)
```

### Turtle Factors (from TurtleTemplate)

Turtle strategy factors for breakout-based trading with volatility-adjusted risk management.

#### 5. ATRFactor
**Purpose**: Average True Range calculation for volatility measurement

- **Category**: RISK
- **Inputs**: `["high", "low", "close"]`
- **Outputs**: `["atr"]`
- **Parameters**:
  - `atr_period` (int): Lookback period for ATR calculation
    - Common values: 14 (original Turtle), 20 (1 month), 30 (1.5 months)

**Example**:
```python
from src.factor_library import create_atr_factor

atr = create_atr_factor(atr_period=20)
data = pd.DataFrame({
    "high": [102, 104, 103, 105, 107],
    "low": [98, 100, 99, 101, 103],
    "close": [100, 102, 101, 103, 105]
})
result = atr.execute(data)
# result now has "atr" column (average volatility)
```

#### 6. BreakoutFactor
**Purpose**: N-day high/low breakout detection for entry signals

- **Category**: ENTRY
- **Inputs**: `["high", "low", "close"]`
- **Outputs**: `["breakout_signal"]` (1=long, -1=short, 0=none)
- **Parameters**:
  - `entry_window` (int): N-day lookback for breakout detection
    - Common values: 20 (1 month), 55 (original Turtle entry)

**Example**:
```python
from src.factor_library import create_breakout_factor

breakout = create_breakout_factor(entry_window=20)
data = pd.DataFrame({
    "high": [102, 104, 103, 110, 112],
    "low": [98, 100, 99, 106, 108],
    "close": [100, 102, 101, 108, 110]
})
result = breakout.execute(data)
# result now has "breakout_signal" column (1 when breaking to new highs)
```

#### 7. DualMAFilterFactor
**Purpose**: Dual moving average filter for trend confirmation

- **Category**: MOMENTUM
- **Inputs**: `["close"]`
- **Outputs**: `["dual_ma_filter"]` (boolean)
- **Parameters**:
  - `short_ma` (int): Short-term moving average period (10-30 days)
  - `long_ma` (int): Long-term moving average period (40-80 days)

**Example**:
```python
from src.factor_library import create_dual_ma_filter_factor

ma_filter = create_dual_ma_filter_factor(short_ma=20, long_ma=60)
data = pd.DataFrame({"close": [100, 102, 101, 103, 105]})
result = ma_filter.execute(data)
# result now has "dual_ma_filter" column (True when price above both MAs)
```

#### 8. ATRStopLossFactor
**Purpose**: ATR-based stop loss calculation for risk management

- **Category**: EXIT
- **Inputs**: `["close", "atr", "positions"]`
- **Outputs**: `["stop_loss_level"]`
- **Parameters**:
  - `atr_multiplier` (float): Multiplier for ATR to set stop distance
    - Common values: 2.0 (original Turtle), 1.5 (tighter), 3.0 (wider)

**Example**:
```python
from src.factor_library import create_atr_stop_loss_factor

stop_loss = create_atr_stop_loss_factor(atr_multiplier=2.0)
data = pd.DataFrame({
    "close": [100, 102, 104],
    "atr": [2.0, 2.1, 2.0],
    "positions": [1, 1, 1]  # 1=long, -1=short, 0=none
})
result = stop_loss.execute(data)
# result now has "stop_loss_level" column (adaptive to volatility)
```

### Exit Factors (from Phase 1 Exit Mutation Framework)

Exit strategy factors extracted from Phase 1 Exit Mutation MVP. Provides multi-layered exit logic for risk management and profit taking.

#### 9. TrailingStopFactor
**Purpose**: Trailing stop loss that follows price upward to lock in profits

- **Category**: EXIT
- **Inputs**: `["close", "positions", "entry_price"]`
- **Outputs**: `["trailing_stop_signal"]` (boolean)
- **Parameters**:
  - `trail_percent` (float): Trailing stop percentage (e.g., 0.10 = 10% from peak)
  - `activation_profit` (float): Minimum profit to activate trailing (e.g., 0.05 = 5%)

**Example**:
```python
from src.factor_library import create_trailing_stop_factor

trailing_stop = create_trailing_stop_factor(trail_percent=0.10, activation_profit=0.05)
data = pd.DataFrame({
    "close": [100, 105, 110, 108, 95],
    "positions": [True, True, True, True, True],
    "entry_price": [100, 100, 100, 100, 100]
})
result = trailing_stop.execute(data)
# result has "trailing_stop_signal" column (True when stop triggered)
```

#### 10. TimeBasedExitFactor
**Purpose**: Exit positions after maximum holding period

- **Category**: EXIT
- **Inputs**: `["positions", "entry_date"]`
- **Outputs**: `["time_exit_signal"]` (boolean)
- **Parameters**:
  - `max_holding_periods` (int): Maximum holding periods before forced exit
    - Common values: 20 (days), 30 (1 month), 60 (2 months)

**Example**:
```python
from src.factor_library import create_time_based_exit_factor
import pandas as pd

time_exit = create_time_based_exit_factor(max_holding_periods=20)
dates = pd.date_range("2023-01-01", periods=25, freq="D")
data = pd.DataFrame({
    "positions": [True] * 25,
    "entry_date": [dates[0]] * 25
}, index=dates)
result = time_exit.execute(data)
# result has "time_exit_signal" column (True after 20 days)
```

#### 11. VolatilityStopFactor
**Purpose**: Volatility-based stop loss using standard deviation

- **Category**: EXIT
- **Inputs**: `["close", "positions"]`
- **Outputs**: `["volatility_stop_signal"]` (boolean)
- **Parameters**:
  - `std_period` (int): Lookback period for standard deviation
  - `std_multiplier` (float): Multiplier for stop distance (e.g., 2.0 = 2 std devs)

**Example**:
```python
from src.factor_library import create_volatility_stop_factor

vol_stop = create_volatility_stop_factor(std_period=20, std_multiplier=2.0)
data = pd.DataFrame({
    "close": [100, 102, 98, 95, 90],
    "positions": [True, True, True, True, True]
})
result = vol_stop.execute(data)
# result has "volatility_stop_signal" column (True when volatility stop hit)
```

#### 12. ProfitTargetFactor
**Purpose**: Fixed profit target exit

- **Category**: EXIT
- **Inputs**: `["close", "positions", "entry_price"]`
- **Outputs**: `["profit_target_signal"]` (boolean)
- **Parameters**:
  - `target_percent` (float): Profit target percentage (e.g., 0.30 = 30% profit)

**Example**:
```python
from src.factor_library import create_profit_target_factor

profit_target = create_profit_target_factor(target_percent=0.30)
data = pd.DataFrame({
    "close": [100, 110, 120, 130, 135],
    "positions": [True, True, True, True, True],
    "entry_price": [100, 100, 100, 100, 100]
})
result = profit_target.execute(data)
# result has "profit_target_signal" column (True when 30% profit reached)
```

#### 13. CompositeExitFactor
**Purpose**: Combine multiple exit signals with OR logic

- **Category**: EXIT
- **Inputs**: List of exit signal columns (dynamic)
- **Outputs**: `["final_exit_signal"]` (boolean)
- **Parameters**:
  - `exit_signals` (List[str]): List of exit signal column names to combine

**Example**:
```python
from src.factor_library import (
    create_trailing_stop_factor,
    create_profit_target_factor,
    create_composite_exit_factor
)

# Create individual exit factors
trailing_stop = create_trailing_stop_factor(trail_percent=0.10, activation_profit=0.05)
profit_target = create_profit_target_factor(target_percent=0.30)

# Execute individual exits
data = pd.DataFrame({
    "close": [100, 105, 110, 135, 120],
    "positions": [True, True, True, True, True],
    "entry_price": [100, 100, 100, 100, 100]
})
result = trailing_stop.execute(data)
result = profit_target.execute(result)

# Combine exits with OR logic
composite = create_composite_exit_factor(
    exit_signals=["trailing_stop_signal", "profit_target_signal"]
)
result = composite.execute(result)
# result has "final_exit_signal" column (True when ANY exit condition met)
```

## Usage Patterns

### Basic Factor Execution
```python
from src.factor_library import (
    create_momentum_factor,
    create_ma_filter_factor
)
import pandas as pd

# Create factors
momentum = create_momentum_factor(momentum_period=20)
ma_filter = create_ma_filter_factor(ma_periods=60)

# Prepare data
data = pd.DataFrame({
    "close": [100, 102, 101, 103, 105, 107, 106, 108, 110, 112]
})

# Execute factors in sequence
result = momentum.execute(data)
result = ma_filter.execute(result)

# Access outputs
print(result["momentum"])
print(result["ma_filter"])
```

### Multi-Factor Composition
```python
from src.factor_library import (
    create_momentum_factor,
    create_ma_filter_factor,
    create_revenue_catalyst_factor
)

# Create factor pipeline
momentum = create_momentum_factor(momentum_period=10)
ma_filter = create_ma_filter_factor(ma_periods=60)
catalyst = create_revenue_catalyst_factor(catalyst_lookback=3)

# Prepare data with dummy column for catalyst
data = pd.DataFrame({
    "close": [100, 102, 101, 103, 105, 107, 106, 108, 110, 112],
    "_dummy": [True] * 10
})

# Execute all factors
result = momentum.execute(data)
result = ma_filter.execute(result)
result = catalyst.execute(result)

# Combine conditions
combined_signal = (
    (result["momentum"] > 0) &
    result["ma_filter"] &
    result["revenue_catalyst"]
)
```

### Turtle Strategy Composition
```python
from src.factor_library import (
    create_atr_factor,
    create_breakout_factor,
    create_dual_ma_filter_factor,
    create_atr_stop_loss_factor
)
import pandas as pd
import numpy as np

# Create turtle strategy factors
atr = create_atr_factor(atr_period=20)
breakout = create_breakout_factor(entry_window=20)
ma_filter = create_dual_ma_filter_factor(short_ma=20, long_ma=60)
stop_loss = create_atr_stop_loss_factor(atr_multiplier=2.0)

# Prepare market data
data = pd.DataFrame({
    "high": [102, 104, 106, 110, 112, 114, 116, 118],
    "low": [98, 100, 102, 106, 108, 110, 112, 114],
    "close": [100, 102, 104, 108, 110, 112, 114, 116],
    "positions": [0, 0, 0, 1, 1, 1, 1, 1]  # Enter at breakout
})

# Execute factor chain (order matters for dependencies)
result = atr.execute(data)          # Calculate volatility
result = breakout.execute(result)   # Detect breakouts
result = ma_filter.execute(result)  # Confirm trend
result = stop_loss.execute(result)  # Calculate stops

# Create entry signal: breakout + trend confirmation
entry_signal = (
    (result["breakout_signal"] == 1) &  # Long breakout
    result["dual_ma_filter"]             # Price above both MAs
)

# Access risk management
print(f"ATR: {result['atr'].iloc[-1]:.2f}")
print(f"Stop Loss: {result['stop_loss_level'].iloc[-1]:.2f}")
```

### Integration with FactorGraph
```python
from src.factor_graph import FactorGraph
from src.factor_library import (
    create_momentum_factor,
    create_ma_filter_factor,
    create_revenue_catalyst_factor
)

# Create factor graph
graph = FactorGraph()

# Add factors
graph.add_factor(create_momentum_factor(momentum_period=20))
graph.add_factor(create_ma_filter_factor(ma_periods=60))
graph.add_factor(create_revenue_catalyst_factor(catalyst_lookback=3))

# Execute graph
result = graph.execute(data)
```

## DataCache Integration

Catalyst factors use DataCache to avoid redundant data loading:

```python
from src.templates.data_cache import DataCache

# Factors automatically use the singleton cache
catalyst = create_revenue_catalyst_factor(catalyst_lookback=3)

# First execution loads from finlab data API
result1 = catalyst.execute(data)

# Subsequent executions use cached data (no API call)
result2 = catalyst.execute(data)
```

### Cache Management
```python
from src.templates.data_cache import DataCache

cache = DataCache.get_instance()

# Check cache stats
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Cache size: {stats['cache_size']} datasets")

# Preload common datasets
cache.preload_all()

# Clear cache if needed
cache.clear()
```

## Design Considerations

### Input Requirements
- **Momentum/MA Filters**: Require `["close"]` column in data
- **Catalyst Factors**: Require `["_dummy"]` placeholder column
  - Actual data loaded from DataCache internally
  - Dummy input satisfies Factor base class validation

### Parameter Ranges

**Momentum Factors** (from MomentumTemplate PARAM_GRID):
- `momentum_period`: [5, 10, 20, 30]
- `ma_periods`: [20, 60, 90, 120]
- `catalyst_lookback`: [2, 3, 4, 6]

**Turtle Factors** (from TurtleTemplate PARAM_GRID):
- `atr_period`: [14, 20, 30]
- `entry_window`: [20, 55]
- `short_ma`: [10, 20, 30]
- `long_ma`: [40, 60, 80]
- `atr_multiplier`: [1.5, 2.0, 2.5, 3.0]

### Performance
- **First execution**: Loads data from finlab API (cached automatically)
- **Subsequent executions**: Uses cached data (instant)
- **Target**: <100ms per factor execution (cached)

## Testing

Comprehensive test suite covers:
- Factor creation and instantiation
- Factory functions with various parameters
- Execution with valid/invalid data
- Parameter validation and edge cases
- Integration with DataCache
- Multi-factor composition

Run tests:
```bash
# Test momentum factors
pytest tests/factor_library/test_momentum_factors.py -v

# Test turtle factors
pytest tests/factor_library/test_turtle_factors.py -v
pytest tests/factor_library/test_turtle_integration.py -v

# Test exit factors
pytest tests/factor_library/test_exit_factors.py -v
pytest tests/factor_library/test_exit_integration.py -v

# Test all factors
pytest tests/factor_library/ -v
```

## Future Extensions

### Planned Factor Categories
1. **Value Factors**: P/E ratio, P/B ratio, dividend yield
2. **Quality Factors**: Profit margins, asset turnover, debt ratios
3. **Risk Factors**: Volatility, beta, drawdown metrics
4. **Entry/Exit Factors**: Stop-loss, take-profit, position sizing

### Roadmap
- **Phase B.1**: ✅ Extract momentum factors (momentum, MA filter, catalysts)
- **Phase B.2**: ✅ Extract turtle factors (ATR, breakout, dual MA, stop loss)
- **Phase B.3**: ✅ Extract exit factors (trailing stop, time exit, volatility stop, profit target, composite)
- **Phase B.4**: Extract mastiff factors (multi-factor scoring)
- **Phase B.5**: Extract factor template factors (value, quality, momentum)
- **Phase C**: Factor composition and mutation strategies

## Architecture Benefits

1. **Modularity**: Each factor is independent and reusable
2. **Composability**: Factors can be combined into DAGs
3. **Testability**: Individual factors can be tested in isolation
4. **Performance**: DataCache ensures efficient data loading
5. **Extensibility**: New factors can be added without modifying existing code
6. **Maintainability**: Clear separation of concerns and responsibilities

## See Also

- `src/factor_graph/factor.py`: Factor base class
- `src/factor_graph/factor_category.py`: Factor categories
- `src/templates/data_cache.py`: DataCache singleton
- `src/templates/momentum_template.py`: Original MomentumTemplate
- `tests/factor_library/test_momentum_factors.py`: Test suite
