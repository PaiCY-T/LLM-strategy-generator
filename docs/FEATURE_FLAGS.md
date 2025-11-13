# Feature Flags for Strategy Generation Refactoring

## Overview

This document describes the feature flags system for safely deploying the strategy generation refactoring in phases.

## Master Kill Switch

**Environment Variable**: `ENABLE_GENERATION_REFACTORING`

**Default**: `false`

**Purpose**: Master control for the entire refactoring rollout. When disabled, all code paths use legacy implementations.

**Usage**:
```bash
# Enable refactoring
export ENABLE_GENERATION_REFACTORING=true

# Disable refactoring (default)
export ENABLE_GENERATION_REFACTORING=false
```

## Phase-Specific Flags

### Phase 1: Configuration Validation & Enforcement

**Environment Variable**: `PHASE1_CONFIG_ENFORCEMENT`

**Default**: `false`

**Purpose**: Enable strict configuration validation and enforcement of required parameters.

**Features**:
- Validate innovation_rate range (0-100)
- Enforce required configuration keys
- Log configuration warnings

**Usage**:
```bash
export PHASE1_CONFIG_ENFORCEMENT=true
```

### Phase 2: Pydantic Validation Models

**Environment Variable**: `PHASE2_PYDANTIC_VALIDATION`

**Default**: `false`

**Purpose**: Enable Pydantic models for type-safe configuration and data validation.

**Features**:
- Type-safe configuration objects
- Automatic validation on assignment
- Better error messages

**Usage**:
```bash
export PHASE2_PYDANTIC_VALIDATION=true
```

### Phase 3: Strategy Pattern Implementation

**Environment Variable**: `PHASE3_STRATEGY_PATTERN`

**Default**: `false`

**Purpose**: Enable strategy pattern for generator selection (LLM vs Factor Graph).

**Features**:
- Pluggable generation strategies
- Easier testing and mocking
- Better separation of concerns

**Usage**:
```bash
export PHASE3_STRATEGY_PATTERN=true
```

### Phase 4: Audit Trail & Observability

**Environment Variable**: `PHASE4_AUDIT_TRAIL`

**Default**: `false`

**Purpose**: Enable comprehensive audit trail and observability features.

**Features**:
- Detailed logging of generation decisions
- Performance metrics tracking
- Decision reasoning capture

**Usage**:
```bash
export PHASE4_AUDIT_TRAIL=true
```

## Deployment Scenarios

### Local Development (All Phases Enabled)
```bash
export ENABLE_GENERATION_REFACTORING=true
export PHASE1_CONFIG_ENFORCEMENT=true
export PHASE2_PYDANTIC_VALIDATION=true
export PHASE3_STRATEGY_PATTERN=true
export PHASE4_AUDIT_TRAIL=true
```

### Production Rollout (Gradual)

**Week 1: Phase 0 (Kill Switch Test)**
```bash
export ENABLE_GENERATION_REFACTORING=false
# All phases disabled, legacy behavior
```

**Week 2: Phase 1 Only**
```bash
export ENABLE_GENERATION_REFACTORING=true
export PHASE1_CONFIG_ENFORCEMENT=true
# Other phases disabled
```

**Week 3: Phase 1 + 2**
```bash
export ENABLE_GENERATION_REFACTORING=true
export PHASE1_CONFIG_ENFORCEMENT=true
export PHASE2_PYDANTIC_VALIDATION=true
```

**Week 4: Phase 1 + 2 + 3**
```bash
export ENABLE_GENERATION_REFACTORING=true
export PHASE1_CONFIG_ENFORCEMENT=true
export PHASE2_PYDANTIC_VALIDATION=true
export PHASE3_STRATEGY_PATTERN=true
```

**Week 5: All Phases**
```bash
export ENABLE_GENERATION_REFACTORING=true
export PHASE1_CONFIG_ENFORCEMENT=true
export PHASE2_PYDANTIC_VALIDATION=true
export PHASE3_STRATEGY_PATTERN=true
export PHASE4_AUDIT_TRAIL=true
```

## Quick Rollback

If any issues are detected, immediately disable all flags:

```bash
export ENABLE_GENERATION_REFACTORING=false
```

This will revert to the proven legacy implementation while the issue is investigated.

## Checking Current Configuration

In Python code:
```python
from src.learning.config import get_feature_flags, log_feature_flags

# Get flags as dictionary
flags = get_feature_flags()
print(flags)

# Log flags (useful in application startup)
import logging
logger = logging.getLogger(__name__)
log_feature_flags(logger)
```

## Testing Flag Behavior

```python
import os
import importlib

# Test with flags disabled
os.environ['ENABLE_GENERATION_REFACTORING'] = 'false'
import src.learning.config
importlib.reload(src.learning.config)

from src.learning.config import ENABLE_GENERATION_REFACTORING
assert ENABLE_GENERATION_REFACTORING == False

# Test with flags enabled
os.environ['ENABLE_GENERATION_REFACTORING'] = 'true'
importlib.reload(src.learning.config)
from src.learning.config import ENABLE_GENERATION_REFACTORING
assert ENABLE_GENERATION_REFACTORING == True
```

## Implementation Details

### Legacy Method Preservation

The `_decide_generation_method()` has been updated to check the master switch:

```python
def _decide_generation_method(self) -> bool:
    # Use legacy implementation when refactoring is disabled
    if not ENABLE_GENERATION_REFACTORING:
        return self._decide_generation_method_legacy()

    # New implementation...
```

The legacy method `_decide_generation_method_legacy()` preserves the exact original behavior and serves as the fallback.

### Adding Feature-Gated Code

When adding new refactored code, follow this pattern:

```python
from src.learning.config import PHASE1_CONFIG_ENFORCEMENT

def some_method(self):
    if PHASE1_CONFIG_ENFORCEMENT:
        # New refactored implementation
        return self._new_implementation()
    else:
        # Legacy implementation
        return self._legacy_implementation()
```

## Monitoring Recommendations

1. **Log feature flags on application startup**
   ```python
   log_feature_flags(logger)
   ```

2. **Monitor key metrics** when enabling phases:
   - Strategy generation success rate
   - Execution time per iteration
   - Error rates by phase
   - Backtest success/failure ratios

3. **Set up alerts** for:
   - Sudden increase in error rates
   - Performance degradation >20%
   - Failed validations (Phase 1)
   - Type errors (Phase 2)

## Best Practices

1. **Never skip phases** - Always deploy in order (Phase 0 → 1 → 2 → 3 → 4)
2. **Wait for stability** - Let each phase run for at least 1 week before advancing
3. **Monitor actively** - Watch dashboards during the first 24 hours of each phase
4. **Prepare rollback** - Have rollback procedures documented and tested
5. **Test locally first** - Enable all phases in development before production rollout
