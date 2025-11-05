# Task 2.2: ExperimentConfig Unit Tests - Quick Reference

## Test File Location
```
tests/unit/config/test_experiment_config.py
```

## Run Tests
```bash
# Run all ExperimentConfig tests
python3 -m pytest tests/unit/config/test_experiment_config.py -v

# Run specific test
python3 -m pytest tests/unit/config/test_experiment_config.py::TestExperimentConfig::test_experiment_config_creation -v

# Run with coverage
python3 -m pytest tests/unit/config/test_experiment_config.py --cov=src.config.experiment_config --cov-report=term-missing
```

## Expected Current State
- **Status**: All 7 tests FAIL with `ModuleNotFoundError`
- **Reason**: src/config/experiment_config.py does not exist yet (Bug #3)
- **Expected**: This is correct for test-first development

## Test Suite Structure

```python
class TestExperimentConfig:
    """7 test functions covering ExperimentConfig dataclass"""
    
    test_experiment_config_creation()           # Basic instantiation
    test_experiment_config_with_timestamp()     # Optional field
    test_experiment_config_from_dict()          # Deserialization
    test_experiment_config_to_dict()            # Serialization
    test_experiment_config_roundtrip()          # Round-trip conversion
    test_experiment_config_optional_timestamp() # Default value behavior
    test_experiment_config_complex_snapshot()   # Nested data handling
```

## Expected Module API (from tests)

```python
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

@dataclass
class ExperimentConfig:
    """Captures configuration state for a single experiment iteration."""
    iteration: int
    config_snapshot: Dict[str, Any]
    timestamp: Optional[str] = None

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ExperimentConfig':
        """Create ExperimentConfig from dictionary."""
        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ExperimentConfig to dictionary."""
        return asdict(self)
```

## Test Coverage Matrix

| Test Function | Covers | Expected Result (Now) | Expected Result (After Task 3.2) |
|--------------|--------|---------------------|----------------------------------|
| test_experiment_config_creation | Basic creation | FAIL (ImportError) | PASS |
| test_experiment_config_with_timestamp | Optional field | FAIL (ImportError) | PASS |
| test_experiment_config_from_dict | from_dict() method | FAIL (ImportError) | PASS |
| test_experiment_config_to_dict | to_dict() method | FAIL (ImportError) | PASS |
| test_experiment_config_roundtrip | Round-trip serialization | FAIL (ImportError) | PASS |
| test_experiment_config_optional_timestamp | Default value None | FAIL (ImportError) | PASS |
| test_experiment_config_complex_snapshot | Nested data structures | FAIL (ImportError) | PASS |

## Task 3.2 Implementation Checklist

When implementing src/config/experiment_config.py, verify:
- [ ] Module can be imported: `from src.config.experiment_config import ExperimentConfig`
- [ ] Dataclass has 3 fields: iteration (int), config_snapshot (dict), timestamp (str|None)
- [ ] timestamp defaults to None
- [ ] from_dict() creates instance from dictionary
- [ ] to_dict() returns dictionary with all fields
- [ ] Round-trip preserves data: `from_dict(config.to_dict()) == config`
- [ ] All 7 tests pass

## Verification Command

After Task 3.2 implementation:
```bash
python3 -m pytest tests/unit/config/test_experiment_config.py -v
# Expected: 7 passed
```

## Integration with Bug Fix

This addresses **Bug #3** identified in characterization test:
- Autonomous loop imports ExperimentConfig
- Import currently fails every iteration
- After Task 3.2: Import succeeds, config snapshots work
- Loop can track configuration changes across iterations
