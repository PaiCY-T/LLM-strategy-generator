# Task 16.3: Central Schema Definition - COMPLETE ✓

## Summary

Successfully created comprehensive YAML schema definition file combining all 5 strategy patterns identified in Task 15.3.

## Deliverable

**File**: `/mnt/c/Users/jnpi/documents/finlab/LLM-strategy-generator/src/config/strategy_schema.yaml`

- **Size**: 23KB
- **Lines**: 665
- **Format**: YAML (valid syntax verified)

## Schema Coverage

### Patterns Defined (5 total, 84% coverage)

1. **Pure Momentum** (18% coverage)
   - Fast breakout using price momentum
   - 3 parameters, 3 constraints
   - Entry: Momentum threshold, Exit: None (rebalance)

2. **Momentum + Exit Strategy** (18% coverage)
   - Momentum with trailing stop loss
   - 4 parameters, 3 constraints
   - Entry: Momentum, Exit: Trailing stop

3. **Turtle Breakout** (16% coverage)
   - Channel breakout with ATR-based stops
   - 4 parameters, 3 constraints
   - Entry: N-day high, Exit: ATR stop loss

4. **Multi-Factor Scoring** (16% coverage)
   - Weighted combination of momentum, value, quality
   - 6 parameters, 4 constraints
   - Entry: Top N% composite score, Exit: Score decline

5. **Complex Combination** (16% coverage)
   - Hybrid strategy with regime detection
   - 9 parameters, 5 constraints
   - Entry: Weighted signals, Exit: Score/volatility

## Key Features

### Layer 1 Integration ✓

- **Canonical Field Names**: All fields use Layer 1 canonical naming
  - Example: `price:收盤價`, `fundamental_features:ROE`
- **Alias Support**: 46 aliases defined for LLM compatibility
  - Example: `close` → `price:收盤價`
- **Auto-Correction**: 21 common field corrections included
  - Example: `成交量` → `price:成交金額` (CRITICAL correction)

### Schema Structure ✓

Each pattern includes:
- **Name & Type**: Human-readable identification
- **Description**: Strategy behavior explanation
- **Coverage**: Percentage of successful strategies
- **Required Fields**: Canonical names + aliases + usage
- **Optional Fields**: Enhancement opportunities
- **Parameters**: Type, default, range, unit, validation
- **Logic**: Entry/exit formulas with dependencies
- **Constraints**: Data quality, parameter, performance checks

### Validation Rules ✓

**Global Validation**:
- Data Quality: Max 5% NaN, min 252 days history
- Performance Bounds: Min Sharpe -0.5, max DD -60%, min win rate 30%
- Parameter Consistency: Positive periods, weights in [0,1], normalized weights

**Pattern-Specific**:
- 18 constraints across all patterns
- Severity levels: critical, warning
- Specific checks for each pattern's requirements

## Integration Points

### With Layer 1 (data_fields.py)
```python
from src.config.data_fields import DataFieldManifest

# Schema uses canonical names from manifest
manifest = DataFieldManifest()
field = manifest.get_field('close')  # Returns 'price:收盤價'
```

### With Pattern Matching (Task 17)
```python
import yaml

# Load schema for validation
with open('src/config/strategy_schema.yaml') as f:
    schema = yaml.safe_load(f)

# Access pattern definitions
pattern = schema['patterns']['pure_momentum']
required_fields = pattern['required_fields']
parameters = pattern['parameters']
```

### With LLM Field Validation
```python
# Auto-correct common mistakes
corrections = schema['field_corrections']
if field_name in corrections:
    corrected_name = corrections[field_name]
```

## Verification Results

✓ All 5 patterns defined with complete sections
✓ 26 total parameters with validation ranges
✓ 18 constraints for quality assurance
✓ 6 unique canonical fields referenced
✓ 46 aliases for LLM compatibility
✓ 21 field corrections for auto-correction
✓ Valid YAML syntax (parsed successfully)
✓ Layer 1 integration (canonical names + aliases)
✓ Global validation rules defined

## Next Steps

**Task 16.4**: Implement schema loader and validator
- Create Python class to load and parse YAML schema
- Implement parameter validation logic
- Add field name resolution using Layer 1

**Task 17**: Implement pattern matching logic
- Use schema definitions for strategy classification
- Validate parameters against schema ranges
- Auto-correct field names using corrections dict

## File Statistics

```
File: src/config/strategy_schema.yaml
Size: 23KB
Lines: 665
Patterns: 5
Coverage: 84%
Parameters: 26
Constraints: 18
Corrections: 21
Aliases: 46
```

**Completion Date**: 2025-11-18
**Task Reference**: 16.3 - Central Schema Definition File
**Status**: ✓ COMPLETE
