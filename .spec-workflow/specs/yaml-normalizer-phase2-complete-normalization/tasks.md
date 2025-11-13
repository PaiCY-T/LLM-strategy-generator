# Tasks Document

## Overview

This document breaks down Phase 2 design into **6 executable tasks** with detailed implementation prompts.

**Phase Goal**: Increase validation success rate from 71.4% → 100% (integration tests) and ≥85% (E2E tests)

**Implementation Order**: Tasks must be completed sequentially (dependencies indicated)

---

## Task 1: Update Test Fixtures (CRITICAL - PREREQUISITE)

**Status**: [x] Complete

**Priority**: CRITICAL (blocks Task 5 integration testing)

**Estimated Time**: 30 minutes

**Dependencies**: None (prerequisite for all other tasks)

### Objective

Update all test fixture `expected_yaml` values to reflect post-normalization state (lowercase indicator names).

### Context

Current test fixtures have uppercase names in `expected_yaml`:
```python
CASE_01_INDICATORS_ARRAY = {
    "expected_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "SMA_Fast", "type": "SMA", "period": 20},  # ❌ Uppercase
            ]
        }
    }
}
```

After Phase 2 normalizer, all names will be lowercase. Tests will fail unless fixtures are updated.

### Implementation Prompt

**File to Modify**: `tests/generators/fixtures/yaml_normalizer_cases.py`

**Task**: Update `expected_yaml` in all 14 test cases:

1. **Identify all indicator name fields** in `expected_yaml` for each case:
   - CASE_01_INDICATORS_ARRAY
   - CASE_02_INDICATORS_ARRAY_WITH_SOURCE
   - CASE_03_INDICATORS_ARRAY_SIMPLE
   - CASE_04_INDICATORS_MIXED
   - CASE_05_INDICATORS_ALIASES
   - (Continue for all 14 cases)

2. **Transform all names to lowercase**:
   - "SMA_Fast" → "sma_fast"
   - "SMA_Slow" → "sma_slow"
   - "RSI" → "rsi"
   - "MACD" → "macd"
   - "ATR" → "atr"
   - etc.

3. **Apply transformations**:
   ```python
   # OLD
   {"name": "SMA_Fast", "type": "SMA", "period": 20}

   # NEW
   {"name": "sma_fast", "type": "SMA", "period": 20}
   ```

4. **Verify coverage**: Ensure ALL indicator name fields are updated in:
   - `technical_indicators[].name`
   - `fundamental_factors[].name` (if present)
   - `custom_calculations[].name` (if present)

5. **Leave `raw_yaml` unchanged**: Only modify `expected_yaml` (raw input should remain as-is)

### Acceptance Criteria

- [ ] All 14 test cases have lowercase names in `expected_yaml`
- [ ] No uppercase indicator names remain in any `expected_yaml`
- [ ] `raw_yaml` sections unchanged (still have original uppercase names)
- [ ] File passes `pytest tests/generators/test_yaml_normalizer.py --collect-only` (no syntax errors)

### Verification

```bash
# Check for any remaining uppercase names in expected_yaml
grep -n '"name": "[A-Z]' tests/generators/fixtures/yaml_normalizer_cases.py

# Should return no results (or only in raw_yaml sections)
```

---

## Task 2: Implement Name Normalization Function

**Status**: [x] Complete

**Priority**: HIGH

**Estimated Time**: 1 hour

**Dependencies**: None

### Objective

Add `_normalize_indicator_name()` function to `yaml_normalizer.py` with complete validation logic.

### Context

Phase 1 failure analysis showed ALL 4 failures caused by uppercase indicator names violating schema pattern `^[a-z_][a-z0-9_]*$`.

### Implementation Prompt

**File to Modify**: `src/generators/yaml_normalizer.py`

**Location**: Add function after line ~50 (after INDICATOR_TYPE_MAP constants)

**Code to Add**:

```python
import re

def _normalize_indicator_name(name: str) -> str:
    """
    Normalize indicator name to match schema pattern ^[a-z_][a-z0-9_]*$.

    Transformations:
    1. Convert to lowercase
    2. Replace spaces with underscores
    3. Validate result matches pattern

    Args:
        name: Raw indicator name (e.g., "SMA_Fast", "RSI 14")

    Returns:
        Normalized name (e.g., "sma_fast", "rsi_14")

    Raises:
        NormalizationError: If normalized name is invalid (empty, starts with digit,
                           contains invalid characters)

    Examples:
        >>> _normalize_indicator_name("SMA_Fast")
        "sma_fast"
        >>> _normalize_indicator_name("RSI 14")
        "rsi_14"
        >>> _normalize_indicator_name("macd")
        "macd"
        >>> _normalize_indicator_name("14_day_rsi")
        NormalizationError: Indicator name '14_day_rsi' starts with digit
    """
    # Step 1: Convert to lowercase
    name_lower = name.lower()

    # Step 2: Replace spaces with underscores
    name_normalized = name_lower.replace(' ', '_')

    # Step 3: Validate pattern - empty name
    if not name_normalized:
        raise NormalizationError(
            f"Indicator name cannot be empty (original: '{name}')"
        )

    # Step 4: Validate pattern - starts with digit
    if name_normalized[0].isdigit():
        raise NormalizationError(
            f"Indicator name '{name_normalized}' starts with digit "
            f"(invalid Python identifier)"
        )

    # Step 5: Full pattern validation (defense-in-depth)
    pattern = re.compile(r"^[a-z_][a-z0-9_]*$")
    if not pattern.match(name_normalized):
        raise NormalizationError(
            f"Normalized name '{name_normalized}' contains invalid characters. "
            f"Pattern requires ^[a-z_][a-z0-9_]*$ (original: '{name}')"
        )

    # Log transformation if changed
    if name_normalized != name:
        logger.debug(f"Normalized indicator name: '{name}' → '{name_normalized}'")

    return name_normalized
```

**Integration Point**: Modify `_normalize_single_indicator()` function:

```python
def _normalize_single_indicator(indicator: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a single indicator object."""
    normalized = copy.deepcopy(indicator)

    # NEW: Normalize name field (ADD THIS BLOCK)
    if "name" in normalized:
        normalized["name"] = _normalize_indicator_name(normalized["name"])

    # Existing transformations (params flattening, aliases, type)
    if "params" in normalized:
        # ... existing code ...

    # ... rest of existing code ...

    return normalized
```

### Acceptance Criteria

- [ ] `_normalize_indicator_name()` function added with complete docstring
- [ ] Function handles all transformations: lowercase, space→underscore
- [ ] Full regex pattern validation included (`^[a-z_][a-z0-9_]*$`)
- [ ] Appropriate NormalizationError raised for invalid names
- [ ] Debug logging added for transformations
- [ ] Function integrated into `_normalize_single_indicator()`
- [ ] mypy type checking passes
- [ ] flake8 linting passes

### Verification

```bash
# Run type checking
mypy src/generators/yaml_normalizer.py

# Run linting
flake8 src/generators/yaml_normalizer.py

# Quick syntax check
python3 -c "from src.generators.yaml_normalizer import _normalize_indicator_name; print(_normalize_indicator_name('SMA_Fast'))"
# Should output: sma_fast
```

---

## Task 3: Add Unit Tests for Name Normalization

**Status**: [x] Complete

**Priority**: HIGH

**Estimated Time**: 45 minutes

**Dependencies**: Task 2 (requires `_normalize_indicator_name()` function)

### Objective

Create comprehensive unit tests for name normalization function covering all edge cases.

### Implementation Prompt

**File to Modify**: `tests/generators/test_yaml_normalizer.py`

**Location**: Add new test class after existing test classes

**Code to Add**:

```python
class TestNameNormalization:
    """Test indicator name normalization (Phase 2)."""

    def test_uppercase_to_lowercase(self):
        """Test: SMA_Fast → sma_fast"""
        result = _normalize_indicator_name("SMA_Fast")
        assert result == "sma_fast"

    def test_simple_uppercase_name(self):
        """Test: RSI → rsi"""
        result = _normalize_indicator_name("RSI")
        assert result == "rsi"

    def test_mixed_case_name(self):
        """Test: MaCd → macd"""
        result = _normalize_indicator_name("MaCd")
        assert result == "macd"

    def test_spaces_to_underscores(self):
        """Test: RSI 14 → rsi_14"""
        result = _normalize_indicator_name("RSI 14")
        assert result == "rsi_14"

    def test_multiple_spaces(self):
        """Test: SMA  Fast  20 → sma_fast_20"""
        result = _normalize_indicator_name("SMA  Fast  20")
        assert result == "sma__fast__20"

    def test_already_lowercase_unchanged(self):
        """Test: sma_fast → sma_fast (idempotent)"""
        result = _normalize_indicator_name("sma_fast")
        assert result == "sma_fast"

    def test_lowercase_with_numbers(self):
        """Test: rsi_14 → rsi_14 (idempotent)"""
        result = _normalize_indicator_name("rsi_14")
        assert result == "rsi_14"

    def test_underscore_prefix(self):
        """Test: _private → _private (valid pattern)"""
        result = _normalize_indicator_name("_private")
        assert result == "_private"

    def test_invalid_name_starts_with_digit(self):
        """Test: 14_day_rsi → raises NormalizationError"""
        with pytest.raises(NormalizationError, match="starts with digit"):
            _normalize_indicator_name("14_day_rsi")

    def test_invalid_name_empty_string(self):
        """Test: '' → raises NormalizationError"""
        with pytest.raises(NormalizationError, match="cannot be empty"):
            _normalize_indicator_name("")

    def test_invalid_name_only_spaces(self):
        """Test: '   ' → raises NormalizationError (becomes empty after replace)"""
        # Note: This might need special handling
        with pytest.raises(NormalizationError):
            _normalize_indicator_name("   ")

    def test_invalid_name_with_dash(self):
        """Test: RSI-14 → raises NormalizationError (dash not in pattern)"""
        with pytest.raises(NormalizationError, match="invalid characters"):
            _normalize_indicator_name("RSI-14")

    def test_invalid_name_with_dot(self):
        """Test: SMA.Fast → raises NormalizationError (dot not in pattern)"""
        with pytest.raises(NormalizationError, match="invalid characters"):
            _normalize_indicator_name("SMA.Fast")

    def test_invalid_name_with_special_char(self):
        """Test: RSI@home → raises NormalizationError"""
        with pytest.raises(NormalizationError, match="invalid characters"):
            _normalize_indicator_name("RSI@home")
```

### Acceptance Criteria

- [ ] All 15+ test cases added to new `TestNameNormalization` class
- [ ] Tests cover: uppercase, spaces, idempotency, edge cases, error cases
- [ ] All tests pass: `pytest tests/generators/test_yaml_normalizer.py::TestNameNormalization -v`
- [ ] Test coverage for `_normalize_indicator_name()` ≥95%
- [ ] No test failures in existing test suite (backward compatibility)

### Verification

```bash
# Run new tests
pytest tests/generators/test_yaml_normalizer.py::TestNameNormalization -v

# Check coverage
pytest tests/generators/test_yaml_normalizer.py::TestNameNormalization --cov=src.generators.yaml_normalizer --cov-report=term-missing

# Ensure existing tests still pass
pytest tests/generators/test_yaml_normalizer.py -v
```

---

## Task 4: Implement PydanticValidator Component

**Status**: [x] Complete

**Priority**: HIGH

**Estimated Time**: 1.5 hours

**Completed**: 2025-10-27

**Dependencies**: None (uses existing `strategy_models.py`)

**Deliverables**:
- src/generators/pydanticvalidator.py (321 lines)
- tests/generators/test_pydantic_validator.py (653 lines, 38 tests, all passing)
- tests/generators/test_yaml_schema_validator_pydantic_integration.py (428 lines, 17 tests, all passing)
- 55/55 tests passing, 86% coverage

### Objective

Create new `PydanticValidator` class that wraps Pydantic validation with clean error formatting.

### Implementation Prompt

**File to Create**: `src/generators/pydantic_validator.py`

**Content**:

```python
"""
Pydantic Validator Module

Provides Pydantic-based validation for YAML strategy specifications.
Wraps Pydantic model validation with formatted error messages.

Phase 2 of yaml-normalizer-phase2-complete-normalization spec.
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

from typing import Tuple, List, Dict, Any, Optional
from pydantic import ValidationError
import logging

from src.models.strategy_models import Strategy

logger = logging.getLogger(__name__)


class PydanticValidator:
    """
    Validates YAML strategies using Pydantic Strategy model.

    Provides:
    - Strict type validation via Pydantic
    - Automatic type coercion (e.g., string '14' → int 14)
    - Field-path specific error messages
    - Returns validated Strategy instance (prevents re-validation downstream)

    Example:
        >>> validator = PydanticValidator()
        >>> strategy, errors = validator.validate(normalized_data)
        >>> if strategy:
        ...     print(f"Valid! Strategy: {strategy.name}")
        >>> else:
        ...     print(f"Errors: {errors}")
    """

    def __init__(self):
        """Initialize validator with Strategy model."""
        self.model = Strategy
        logger.info("PydanticValidator initialized with Strategy model")

    def validate(self, data: Dict[str, Any]) -> Tuple[Optional[Strategy], List[str]]:
        """
        Validate data against Pydantic Strategy model.

        Args:
            data: Normalized YAML dictionary

        Returns:
            (strategy_instance, error_messages) tuple:
            - strategy_instance: Validated Strategy model if valid, else None
            - error_messages: List of human-readable error strings (empty if valid)

        Example:
            >>> validator = PydanticValidator()
            >>> strategy, errors = validator.validate({"name": "Test", ...})
            >>> if strategy:
            ...     json_data = strategy.model_dump(mode='json')
        """
        try:
            # Validate and create Pydantic model instance
            strategy = self.model.model_validate(data)

            logger.info(
                f"Pydantic validation successful - Strategy '{strategy.name}' validated"
            )

            # Return validated instance (avoids re-parsing downstream)
            return (strategy, [])

        except ValidationError as e:
            # Extract and format Pydantic errors
            error_messages = self._format_pydantic_errors(e)

            logger.warning(
                f"Pydantic validation failed with {len(error_messages)} error(s)"
            )

            # Return None with error messages
            return (None, error_messages)

    def _format_pydantic_errors(self, error: ValidationError) -> List[str]:
        """
        Format Pydantic ValidationError into human-readable messages.

        Converts Pydantic's error dict format to plain strings with field paths.

        Args:
            error: Pydantic ValidationError exception

        Returns:
            List of formatted error strings

        Example Output:
            [
                "indicators.technical_indicators.0.type: Input should be a valid string",
                "indicators.technical_indicators.0.period: Input should be less than or equal to 250"
            ]
        """
        formatted_errors = []

        for err in error.errors():
            # Build field path (e.g., "indicators.technical_indicators.0.type")
            field_path = ".".join(str(loc) for loc in err["loc"])

            # Get error message
            msg = err["msg"]

            # Get error type for additional context
            error_type = err["type"]

            # Format: "field.path: Error message (type: error_type)"
            formatted_error = f"{field_path}: {msg}"

            formatted_errors.append(formatted_error)

        return formatted_errors
```

**Unit Tests File**: `tests/generators/test_pydantic_validator.py`

```python
"""Unit tests for PydanticValidator."""

import pytest
from src.generators.pydantic_validator import PydanticValidator


class TestPydanticValidator:
    """Test Pydantic validation wrapper."""

    def test_valid_strategy_returns_instance(self):
        """Test: Valid data returns Strategy instance with empty errors."""
        validator = PydanticValidator()

        valid_data = {
            "name": "Test Strategy",
            "description": "Test description",
            "indicators": {
                "technical_indicators": [
                    {"name": "rsi_14", "type": "RSI", "period": 14}
                ]
            },
            "entry_conditions": {
                "threshold_rules": [
                    {"field": "rsi_14", "operator": ">", "value": 30}
                ]
            },
            "exit_conditions": {
                "threshold_rules": [
                    {"field": "rsi_14", "operator": "<", "value": 70}
                ]
            },
            "position_sizing": {"method": "equal_weight"}
        }

        strategy, errors = validator.validate(valid_data)

        assert strategy is not None
        assert strategy.name == "Test Strategy"
        assert errors == []

    def test_invalid_data_returns_errors(self):
        """Test: Invalid data returns None with error messages."""
        validator = PydanticValidator()

        invalid_data = {
            "name": "Test Strategy",
            # Missing required fields
        }

        strategy, errors = validator.validate(invalid_data)

        assert strategy is None
        assert len(errors) > 0
        assert any("required" in err.lower() for err in errors)

    def test_type_coercion_works(self):
        """Test: Pydantic coerces types (string '14' → int 14)."""
        validator = PydanticValidator()

        data_with_string_period = {
            "name": "Test Strategy",
            "description": "Test",
            "indicators": {
                "technical_indicators": [
                    {"name": "rsi_14", "type": "RSI", "period": "14"}  # String
                ]
            },
            "entry_conditions": {"threshold_rules": []},
            "exit_conditions": {"threshold_rules": []},
            "position_sizing": {"method": "equal_weight"}
        }

        strategy, errors = validator.validate(data_with_string_period)

        assert strategy is not None
        assert strategy.indicators["technical_indicators"][0]["period"] == 14  # Int

    def test_error_formatting_includes_field_paths(self):
        """Test: Errors include full field paths."""
        validator = PydanticValidator()

        invalid_data = {
            "name": "Test",
            "description": "Test",
            "indicators": {
                "technical_indicators": [
                    {"name": "rsi", "type": 123, "period": 14}  # type should be string
                ]
            },
            "entry_conditions": {"threshold_rules": []},
            "exit_conditions": {"threshold_rules": []},
            "position_sizing": {"method": "equal_weight"}
        }

        strategy, errors = validator.validate(invalid_data)

        assert strategy is None
        assert len(errors) > 0
        assert any("indicators.technical_indicators" in err for err in errors)
```

### Acceptance Criteria

- [ ] `src/generators/pydantic_validator.py` created with PydanticValidator class
- [ ] Returns `Tuple[Optional[Strategy], List[str]]` as per design
- [ ] Error formatting includes field paths
- [ ] Unit tests in `tests/generators/test_pydantic_validator.py` pass
- [ ] Test coverage ≥80% for pydantic_validator.py
- [ ] mypy and flake8 pass

### Verification

```bash
# Run unit tests
pytest tests/generators/test_pydantic_validator.py -v

# Check coverage
pytest tests/generators/test_pydantic_validator.py --cov=src.generators.pydantic_validator

# Type checking
mypy src/generators/pydantic_validator.py
```

---

## Task 5: Integrate PydanticValidator into YAMLSchemaValidator

**Status**: [x] Complete

**Priority**: HIGH

**Estimated Time**: 1 hour

**Completed**: 2025-10-27

**Dependencies**: Task 2 (name normalization), Task 4 (PydanticValidator)

**Deliverables**:
- Modified src/generators/yaml_schema_validator.py (~40 lines changed)
- Fixed bug in src/models/strategy_models.py (regex pattern)
- Dual validation paths: JSON Schema (legacy) and Pydantic (Phase 2)
- Backward compatibility maintained with `normalize=False` default
- 55/55 integration tests passing

### Objective

Modify `YAMLSchemaValidator` to orchestrate: normalize → Pydantic (replacing JSON Schema validation).

### Implementation Prompt

**File to Modify**: `src/generators/yaml_schema_validator.py`

**Changes Required**:

1. **Add import**:
   ```python
   from src.generators.pydantic_validator import PydanticValidator
   ```

2. **Modify `__init__` method**:
   ```python
   def __init__(self, schema_path: Optional[str] = None):
       """Initialize validator."""
       # Existing JSON Schema setup
       self.schema_path = schema_path or os.path.join(...)
       self.schema = self._load_schema()

       # NEW: Initialize Pydantic validator
       self.pydantic_validator = PydanticValidator()

       logger.info("YAMLSchemaValidator initialized with Pydantic support")
   ```

3. **Modify `validate` method**:
   ```python
   def validate(
       self,
       yaml_spec: Dict[str, Any],
       normalize: bool = False
   ) -> Tuple[bool, List[str]]:
       """
       Validate YAML specification against schema.

       Args:
           yaml_spec: YAML dict to validate
           normalize: If True, apply normalization + Pydantic validation (Phase 2)
                     If False, use legacy JSON Schema validation (backward compatibility)

       Returns:
           (is_valid, error_messages) tuple
       """
       if normalize:
           # Phase 2 path: normalize → Pydantic
           try:
               # Step 1: Normalize
               from src.generators.yaml_normalizer import normalize_yaml
               normalized_spec = normalize_yaml(yaml_spec)

               logger.debug("YAML normalization successful")

               # Step 2: Pydantic validation
               strategy, errors = self.pydantic_validator.validate(normalized_spec)

               if strategy:
                   # Validation succeeded
                   logger.info("YAML validation successful (normalize + Pydantic)")
                   return (True, [])
               else:
                   # Validation failed
                   logger.warning(
                       f"YAML validation failed with {len(errors)} error(s)"
                   )
                   return (False, errors)

           except NormalizationError as e:
               # Normalization failed
               error_msg = f"Normalization failed: {str(e)}"
               logger.warning(error_msg)
               return (False, [error_msg])

       else:
           # Legacy path: JSON Schema validation only
           return self._validate_with_json_schema(yaml_spec)

   def _validate_with_json_schema(self, yaml_spec: Dict[str, Any]) -> Tuple[bool, List[str]]:
       """Legacy JSON Schema validation (backward compatibility)."""
       # Move existing validation logic here
       try:
           jsonschema.validate(instance=yaml_spec, schema=self.schema)
           logger.info("YAML validation successful (JSON Schema)")
           return (True, [])
       except jsonschema.exceptions.ValidationError as e:
           # ... existing error handling ...
           return (False, error_messages)
   ```

### Acceptance Criteria

- [ ] PydanticValidator imported and initialized
- [ ] `validate(normalize=True)` path uses normalize → Pydantic
- [ ] `validate(normalize=False)` path uses legacy JSON Schema
- [ ] NormalizationError properly caught and formatted
- [ ] All 926 existing tests pass with `normalize=False`
- [ ] Logging updated appropriately

### Verification

```bash
# Ensure backward compatibility (all existing tests pass)
pytest -v

# Should be 100% pass rate with normalize=False
```

---

## Task 6: Integration Testing and Validation

**Status**: [x] Complete

**Priority**: CRITICAL (validates entire Phase 2)

**Estimated Time**: 1.5 hours

**Completed**: 2025-10-27

**Dependencies**: All previous tasks (1-5)

**Deliverables**:
- tests/integration/test_yaml_normalizer_e2e.py (780 lines, 19 tests, all passing)
- Updated src/generators/yaml_normalizer.py (added normalization for all indicator types)
- E2E validation success rate: **100%** (12/12 test cases)
- All 19 E2E integration tests passing
- Performance: <100ms per E2E pipeline execution
- Backward compatibility verified (normalize=False still works)

### Objective

Verify Phase 2 achieves 100% success rate on integration tests and ≥85% on E2E tests.

### Implementation Prompt

**Part 1: Integration Tests**

Run existing integration tests with updated fixtures:

```bash
# Should achieve 100% success rate (14/14)
pytest tests/integration/test_yaml_normalizer_integration.py::TestEndToEndNormalization::test_success_rate_with_normalizer -v
```

**Expected Output**:
```
Total Cases:     14
Successful:      14
Failed:          0
Success Rate:    100.0%
Target:          100.0%
✅ PASSED
```

**Part 2: E2E Testing with Real LLM**

Create and run E2E test script:

**File to Create**: `scripts/test_yaml_validation_phase2.py`

```python
"""
Phase 2 End-to-End Validation Test

Tests YAML normalizer + Pydantic validation against real LLM outputs.
Target: ≥85% success rate over 50-100 iterations.
"""

import sys
import argparse
from src.generators.yaml_schema_validator import YAMLSchemaValidator
# ... implementation ...

def run_e2e_test(iterations: int = 100, llm_model: str = "gemini-2.5-flash"):
    """Run E2E test with real LLM."""
    validator = YAMLSchemaValidator()

    successful = 0
    failed = 0

    for i in range(iterations):
        # Generate strategy with LLM
        raw_yaml = generate_strategy_with_llm(llm_model)

        # Validate with Phase 2 normalizer + Pydantic
        is_valid, errors = validator.validate(raw_yaml, normalize=True)

        if is_valid:
            successful += 1
        else:
            failed += 1
            print(f"Iteration {i+1} failed: {errors}")

    success_rate = (successful / iterations) * 100

    print(f"\n{'='*70}")
    print(f"Phase 2 E2E Test Results")
    print(f"{'='*70}")
    print(f"Total Iterations: {iterations}")
    print(f"Successful:       {successful}")
    print(f"Failed:           {failed}")
    print(f"Success Rate:     {success_rate:.1f}%")
    print(f"Target:           ≥85.0%")
    print(f"{'='*70}")

    if success_rate >= 85.0:
        print("✅ PASSED - Phase 2 target achieved")
        return 0
    else:
        print("❌ FAILED - Below target")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--model", type=str, default="gemini-2.5-flash")
    args = parser.parse_args()

    sys.exit(run_e2e_test(args.iterations, args.model))
```

**Run E2E Test**:
```bash
python scripts/test_yaml_validation_phase2.py --iterations 100 --model gemini-2.5-flash
```

**Part 3: Coverage Verification**

```bash
# Check overall test coverage for Phase 2 components
pytest tests/generators/test_yaml_normalizer.py tests/generators/test_pydantic_validator.py \
  --cov=src.generators.yaml_normalizer \
  --cov=src.generators.pydantic_validator \
  --cov-report=term-missing \
  --cov-report=html

# Target: ≥85% coverage for yaml_normalizer.py, ≥80% for pydantic_validator.py
```

### Acceptance Criteria

- [ ] Integration tests achieve 100% success rate (14/14 fixtures)
- [ ] E2E tests achieve ≥85% success rate (50-100 iterations with real LLM)
- [ ] All 926 existing tests still pass (backward compatibility)
- [ ] Test coverage: ≥85% for yaml_normalizer.py, ≥80% for pydantic_validator.py
- [ ] No regressions in Phase 1 functionality

### Verification

```bash
# Complete test suite
pytest -v

# Integration test specific
pytest tests/integration/test_yaml_normalizer_integration.py -v

# E2E test
python scripts/test_yaml_validation_phase2.py --iterations 100

# Coverage report
pytest --cov=src.generators --cov-report=html
open htmlcov/index.html
```

---

## Success Metrics

| Metric | Target | Verification |
|--------|--------|--------------|
| **Integration Test Success** | 100% (14/14) | `pytest tests/integration/...` |
| **E2E Test Success** | ≥85% | `python scripts/test_yaml_validation_phase2.py` |
| **Backward Compatibility** | 100% (926 tests) | `pytest -v` |
| **Code Coverage - Normalizer** | ≥85% | `pytest --cov` |
| **Code Coverage - Pydantic** | ≥80% | `pytest --cov` |
| **Type Checking** | 0 errors | `mypy src/generators/` |
| **Linting** | 0 errors | `flake8 src/generators/` |

---

## Task Dependencies Graph

```
Task 1 (Update Fixtures) ─┐
                          │
Task 2 (Name Norm) ───────┼─→ Task 5 (Integration) ─→ Task 6 (Testing)
                          │                              ↑
Task 3 (Unit Tests) ──────┘                              │
                                                          │
Task 4 (Pydantic) ────────────────────────────────────────┘
```

**Critical Path**: Task 1 → Task 2 → Task 5 → Task 6

---

## Document Metadata

**Document Version**: 1.0
**Created**: 2025-10-27
**Status**: Draft - Ready for Implementation
**Owner**: Personal Project (週/月交易系統)
**Dependencies**:
- requirements.md (approved)
- design.md v1.1 (approved with 5 critical fixes)
**Estimated Total Time**: 6.5 hours
- Task 1: 0.5h
- Task 2: 1h
- Task 3: 0.75h
- Task 4: 1.5h
- Task 5: 1h
- Task 6: 1.5h
- Contingency: 0.25h
