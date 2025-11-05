# Requirements Document

## Introduction

This specification addresses a critical validation issue where LLM-generated YAML strategies have only 25% validation success rate despite 4 schema fixes. The root cause is a fundamental mismatch between prescriptive schema design and exploratory LLM generation patterns. This feature implements a two-stage validation architecture (Normalizer → Pydantic) to bridge this gap and achieve 90%+ success rate.

**Current State:**
- YAML schema validation success rate: 25% (5/20 iterations)
- 40% of failures: `indicators` type mismatch (array vs object)
- 30% of failures: Field naming mismatches (`length` vs `period`, `rule` vs `field`)
- 15% of failures: Type enum violations (lowercase `sma` vs uppercase `SMA`)
- Schema fixes (oneOf patterns) showed diminishing returns (0%→20%→40%→30%→25%)

**Target State:**
- Phase 1 (Normalizer MVP): 70-75% success rate
- Phase 2 (Pydantic Integration): 80-85% success rate
- Phase 3 (Pipeline Integration): 85-90% success rate
- Phase 4 (Prompt Optimization): 90-95% success rate

## Alignment with Product Vision

This feature aligns with the Finlab Backtesting Optimization System's core principles:

**避免過度工程化 (Avoid Over-Engineering):**
- MVP normalizer using 80/20 approach: handles top 5 error patterns (covers 95% of failures)
- Regex-based transformations sufficient for current scale
- No AST complexity needed for this phase

**從數據中學習 (Learn from Data):**
- Analysis of 15 real failure cases drives normalizer patterns
- Empirical error distribution (40%/30%/15%/10%/5%) guides prioritization
- TDD approach using actual LLM outputs

**漸進式改進 (Incremental Improvement):**
- Four-phase rollout with measurable success metrics
- Build upon existing schema fixes (already at 25%)
- Systematic progression: 25% → 70% → 85% → 90%+

**自動化優先 (Automation First):**
- Automatic normalization without human intervention
- Integration into autonomous iteration loop
- Fail-fast mechanism for unfixable cases (Jinja templates)

**Product Impact:**
- **Validation Pass Rate**: From 25% → 90%+ (target metric from product.md)
- **Iteration Efficiency**: Reduce wasted iterations from validation failures
- **Time Savings**: Eliminate manual YAML debugging and fixes
- **System Quality**: Increase success rate towards >60% target

## Requirements

### Requirement 1: YAML Normalizer Core Implementation

**User Story:** As a developer running autonomous strategy optimization, I want the system to automatically transform LLM-generated YAML into schema-compliant format, so that 90%+ of iterations pass validation without manual intervention.

#### Acceptance Criteria

1. WHEN LLM generates YAML with `indicators` as array THEN normalizer SHALL convert to `{technical_indicators: [...]}` object structure
   - **Evidence**: 40% of failures (8/20 iterations) show this pattern
   - **Test Cases**: Extract from `complete_validation_output.txt` iterations 1, 3, 5, 7, 9, 11, 13, 15

2. WHEN LLM uses field aliases (`length`, `window`, `rule`, `order`) THEN normalizer SHALL map to canonical names (`period`, `field`, `method`)
   - **Evidence**: 30% of failures show alias mismatches
   - **Mapping Table**: `FIELD_ALIASES = {'length': 'period', 'window': 'period', 'rule': 'field', 'order': 'method'}`

3. WHEN LLM generates `params` nested object THEN normalizer SHALL flatten params to top-level indicator properties
   - **Example**: `{'type': 'RSI', 'params': {'length': 14}}` → `{'type': 'RSI', 'period': 14}`
   - **Evidence**: Consistent pattern across all failures with indicators

4. WHEN LLM uses lowercase indicator types (`sma`, `rsi`, `macd`) THEN normalizer SHALL uppercase and map to canonical types
   - **Type Map**: `INDICATOR_TYPE_MAP = {'sma': 'SMA', 'ema': 'EMA', 'rsi': 'RSI', 'macd': 'MACD', 'macd_histogram': 'MACD', 'macd_signal': 'MACD'}`
   - **Evidence**: 15% of failures show case mismatches

5. WHEN normalized YAML contains Jinja templates (`{{`, `{%`) THEN normalizer SHALL raise `NormalizationError` to trigger retry
   - **Rationale**: Jinja templates cannot be normalized (require re-generation)
   - **Fail Fast**: Early detection prevents downstream validation errors

6. WHEN normalized YAML is missing required fields (`metadata`, `indicators`, `entry_conditions`) THEN normalizer SHALL raise `NormalizationError`
   - **Sanity Check**: Basic structure validation before Pydantic

7. IF normalization succeeds THEN normalizer SHALL return deep-copied dict (no mutation of input)
   - **Safety**: Preserve original for debugging/retry

### Requirement 2: Pydantic Validation Models

**User Story:** As a developer integrating normalized YAML, I want strict type validation with auto-generated Pydantic models, so that downstream code can safely assume valid structure without defensive checks.

#### Acceptance Criteria

1. WHEN Pydantic models are generated from schema THEN all enum types SHALL be enforced as Literal types
   - **Example**: `type: Literal['RSI', 'MACD', 'SMA', 'EMA', 'ATR', 'ADX']`
   - **Tool**: Use `datamodel-code-generator` CLI

2. WHEN normalized YAML is validated THEN Pydantic SHALL apply field validators for automatic type conversions
   - **Example**: Uppercase type conversion as double-insurance: `@field_validator('type', mode='before') def uppercase_type(cls, v): return v.upper() if isinstance(v, str) else v`

3. WHEN validation fails THEN Pydantic SHALL return detailed error messages with field paths
   - **Format**: `indicators.technical_indicators.0.type: 'invalid' not in ['RSI', 'MACD', ...]`
   - **Usage**: Enable quick diagnosis of remaining 5-10% failures

4. WHEN Pydantic models are instantiated THEN they SHALL support both object and array formats via discriminated unions
   - **Pattern**: Handle `oneOf` scenarios from schema (entry_conditions, exit_conditions)

### Requirement 3: Integration Point Analysis and Validation

**User Story:** As a developer integrating the normalizer, I want clear understanding of insertion points in the existing pipeline, so that integration is minimal-risk and backward compatible.

#### Acceptance Criteria

1. WHEN integration points are identified THEN documentation SHALL map exact locations in `innovation_engine.py` and `llm_providers.py`
   - **Expected Locations**:
     - `InnovationEngine.generate_innovation()` - after YAML generation
     - `LLMProvider._parse_yaml_response()` - before schema validation

2. WHEN pytest is executed THEN existing test suite SHALL pass (926 tests) as baseline
   - **Command**: `pytest -v`
   - **Benchmark**: Establish pre-integration test health

3. WHEN InnovationEngine code is reviewed THEN YAML generation flow SHALL be documented from LLM API call through validation
   - **Diagram**: `LLM API → parse_yaml → [INSERT NORMALIZER HERE] → validate_schema → return strategy`

4. IF insertion point modifies existing interface THEN backward compatibility SHALL be maintained
   - **Pattern**: Wrapper function or optional parameter (e.g., `normalize=True`)

5. WHEN normalizer integration is complete THEN new unit tests SHALL cover all transformation patterns (indicators, params, types, aliases)
   - **Coverage Target**: >80% for `yaml_normalizer.py`

### Requirement 4: Test-Driven Development with Real Failure Cases

**User Story:** As a developer building the normalizer, I want comprehensive tests based on actual LLM failures, so that the solution addresses real-world issues rather than theoretical edge cases.

#### Acceptance Criteria

1. WHEN test suite is created THEN it SHALL include at least 15 real failure cases extracted from validation reports
   - **Sources**:
     - `complete_validation_output.txt` (20 iterations, 15 failures)
     - `QUICKWINS_VALIDATION_REPORT.md` (additional 10 iterations, 7 failures)

2. WHEN tests are written THEN each SHALL include:
   - **Input**: Raw LLM-generated YAML (from failure logs)
   - **Expected Output**: Schema-compliant normalized YAML
   - **Assertion**: Validates against schema after normalization

3. WHEN test categories are defined THEN they SHALL match error distribution:
   - **Category 1** (40%): Array→object structure conversion (6 tests)
   - **Category 2** (30%): Field alias mapping (5 tests)
   - **Category 3** (15%): Type uppercase/mapping (3 tests)
   - **Category 4** (10%): Nested params flattening (2 tests)
   - **Category 5** (5%): Jinja/unfixable cases (1 test)

4. WHEN TDD workflow is followed THEN each transformation SHALL:
   - **Red**: Write failing test with real failure case
   - **Green**: Implement minimal transformation to pass
   - **Refactor**: Extract configuration (e.g., `FIELD_ALIASES`, `INDICATOR_TYPE_MAP`)

### Requirement 5: Pipeline Integration and Backward Compatibility

**User Story:** As a system maintainer, I want normalizer integration to be optional and backward compatible, so that existing workflows continue to function during rollout.

#### Acceptance Criteria

1. WHEN normalizer is integrated THEN it SHALL be behind a feature flag in configuration
   - **Config**: `learning_system.yaml` → `yaml_normalization: enabled: true`
   - **Default**: Enabled for new runs, manual opt-in for existing

2. WHEN feature flag is disabled THEN existing validation flow SHALL execute unchanged
   - **No Regression**: 926 tests pass with flag=false

3. WHEN normalizer fails (raises `NormalizationError`) THEN system SHALL fall back to direct validation
   - **Graceful Degradation**: Log warning but continue iteration
   - **Metric Tracking**: Count normalization failures for monitoring

4. WHEN integration is complete THEN success rate SHALL increase from 25% to 70%+ (Phase 1 target)
   - **Measurement**: Run 10-iteration test with real LLM API
   - **Acceptance**: ≥7/10 successful validations

## Non-Functional Requirements

### Code Architecture and Modularity

**Single Responsibility Principle:**
- `src/generators/yaml_normalizer.py`: Only normalization logic (no validation, no parsing)
- `src/models/strategy_models.py`: Only Pydantic models (no transformation logic)
- `tests/test_normalizer.py`: Only normalizer tests (no integration tests here)

**Modular Design:**
- Normalizer is stateless (pure function: `normalize_yaml(dict) -> dict`)
- Configuration externalized (`FIELD_ALIASES`, `INDICATOR_TYPE_MAP` as module constants)
- Easy to extend with new transformation patterns

**Dependency Management:**
- Normalizer depends only on Python stdlib (`copy`, `logging`, `typing`)
- Pydantic models depend on schema (one-time generation)
- Integration depends on normalizer + Pydantic (layered dependency)

**Clear Interfaces:**
```python
# Public API
def normalize_yaml(raw_data: dict) -> dict:
    """
    Transform LLM-generated YAML to schema-compliant format.

    Args:
        raw_data: Raw YAML dict from LLM

    Returns:
        Normalized YAML dict

    Raises:
        NormalizationError: If unfixable (Jinja, missing required fields)
    """
```

### Performance

**Normalization Speed:**
- **Target**: <10ms per iteration (negligible vs. 30-120s backtest)
- **Measurement**: `pytest-benchmark` for all transformation patterns
- **Bottlenecks**: Avoid regex in hot path, use dict lookups

**Memory Overhead:**
- **Target**: <1MB per iteration (YAML dicts are small, ~10-50KB)
- **Deep Copy**: Acceptable trade-off for safety (no input mutation)

**Integration Impact:**
- **Target**: <1% increase in total iteration time (10ms / 60000ms = 0.017%)
- **Negligible**: Backtest dominates runtime, normalization is noise

### Security

**Code Execution Safety:**
- **No eval/exec**: Only dict manipulation (no code generation/execution)
- **Input Validation**: Check for Jinja templates (potential injection risk)
- **Fail Fast**: Reject suspicious patterns early

**Data Integrity:**
- **Deep Copy**: Input data never mutated (prevents side effects)
- **Validation Chain**: Normalizer → Pydantic → Schema (three layers of defense)

### Reliability

**Error Handling:**
- **Explicit Exceptions**: `NormalizationError` for unfixable cases (clear signal to retry)
- **Logging**: Structured logging for all transformations (debug and audit trail)
- **Graceful Degradation**: Fall back to direct validation if normalizer fails

**Backward Compatibility:**
- **Feature Flag**: Controlled rollout without breaking changes
- **Test Coverage**: 926 existing tests must pass (100% backward compatibility)
- **Migration Path**: No data migration needed (stateless transformation)

**Monitoring:**
- **Success Rate Tracking**: Log normalization success/failure counts
- **Error Categorization**: Count each transformation pattern applied
- **Alert Threshold**: Warn if normalization failure rate >20% (indicates new pattern)

### Usability

**Developer Experience:**
- **Clear Error Messages**: `NormalizationError` includes specific reason (e.g., "Contains Jinja templates at line 15")
- **Logging**: Info-level logs show transformations applied (e.g., "Converted indicators array → object")
- **Testing**: Easy to add new test cases (just extract from failure logs)

**Integration Simplicity:**
- **One-Line Integration**: `normalized = normalize_yaml(raw_data)` before validation
- **No Configuration Required**: Works out-of-box with sensible defaults
- **Optional Advanced Config**: Override `FIELD_ALIASES` if needed (future extensibility)

**Documentation:**
- **API Docs**: Comprehensive docstrings (Google-style)
- **Integration Guide**: Step-by-step insertion into `innovation_engine.py`
- **Troubleshooting**: Common failures and solutions in docs/TROUBLESHOOTING.md

### Maintainability

**Code Quality:**
- **Type Hints**: All functions fully typed (mypy strict mode)
- **PEP 8 Compliance**: flake8 passing, 100-char line length
- **Test Coverage**: >80% for normalizer module, >90% for critical paths

**Configuration Management:**
- **Centralized Constants**: All mappings in module top (`FIELD_ALIASES`, `INDICATOR_TYPE_MAP`)
- **Easy to Extend**: Add new alias: just one line in `FIELD_ALIASES` dict
- **No Magic Strings**: All hardcoded values extracted to constants

**Future-Proofing:**
- **Plugin Architecture**: Easy to add new transformation patterns (just add to `normalize_yaml()` function)
- **Schema Evolution**: Pydantic models regenerated from schema (single command)
- **Migration to AST**: Normalizer can be replaced module-by-module (clear interface)

---

**Document Version**: 1.0
**Created**: 2025-10-27
**Status**: Draft - Pending Approval
**Owner**: Personal Project (週/月交易系統)
**Estimated Effort**: 4.5 hours (Phase 1: 2h, Phase 2: 1h, Phase 3: 30min, Phase 4: 1h)
