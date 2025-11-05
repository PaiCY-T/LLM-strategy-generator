# Requirements Document

## Introduction

This specification addresses the gap between Phase 1 (71.4% validation success rate) and the 90% target by **completing the normalization layer** and integrating **Pydantic-based validation**.

**Critical Finding from Phase 1 Analysis**: All 4 integration test failures (4/14 = 28.6%) are caused by indicator `name` field violating schema pattern `^[a-z_][a-z0-9_]*$`. LLM outputs use uppercase names (e.g., "SMA_Fast", "RSI") but schema requires lowercase (e.g., "sma_fast", "rsi"). The Phase 1 normalizer lacks name normalization logic.

**Key Insight**: Pydantic validation alone **cannot** fix pattern violations - it validates but doesn't transform. The solution requires **enhancing the normalizer** to handle name transformation, then adding Pydantic for strict validation.

**Current State:**
- YAML normalization: 100% unit tests passing (59/59)
- End-to-end validation: 71.4% (10/14 integration tests)
- **Root Cause**: Missing name normalization in Phase 1
- **Evidence**: All 4 failures share identical error: "name field does not match pattern"

**Target State:**
- Phase 2 completion: 85-87% validation success rate
- Complete normalizer with all transformations
- Pydantic as single validation source (replacing JSON Schema)
- Enhanced error messages with field paths

**Detailed Analysis**: See `/mnt/c/Users/jnpi/documents/finlab/PHASE1_FAILURE_ANALYSIS.md`

## Alignment with Product Vision

This feature aligns with the Finlab Backtesting Optimization System's core principles:

**避免過度工程化 (Avoid Over-Engineering):**
- Simple name normalization (lowercase + replace spaces)
- Remove redundant JSON Schema validation layer
- Reuse existing `strategy_models.py` (no regeneration needed)

**從數據中學習 (Learn from Data):**
- **Evidence-based approach**: Analysis of 4/14 actual failures
- Root cause identified through systematic investigation
- Solution targets verified pain points, not theoretical issues

**漸進式改進 (Incremental Improvement):**
- Phase 1 (Normalizer MVP): 71.4% ✓
- Phase 2 (Complete Normalization + Validation): 85-87%
- Phase 3 (Pipeline Integration): 90%+
- Each phase builds on previous work without breaking changes

**自動化優先 (Automation First):**
- Automatic name transformation (no manual fixes)
- Pydantic field validators for type coercion
- Fail-fast with actionable error messages

**Product Impact:**
- **Validation Pass Rate**: From 71.4% → 85-87% (+13.6-15.6%)
- **Architecture Simplicity**: Single validation source (Pydantic)
- **Error Quality**: Field-path specific error messages
- **Path to 90%**: Solid foundation for Phase 3 pipeline integration

## Requirements

### Requirement 1: Enhanced Normalizer with Name Transformation

**User Story:** As a developer running autonomous strategy optimization, I want the normalizer to transform indicator names to match schema patterns, so that LLM-generated uppercase names don't cause validation failures.

#### Acceptance Criteria

1. WHEN normalizer processes indicator names THEN it SHALL convert to lowercase
   - **Pattern**: `"SMA_Fast"` → `"sma_fast"`, `"RSI"` → `"rsi"`
   - **Evidence**: All 4 failed cases have uppercase names
   - **Coverage**: technical_indicators, fundamental_factors, custom_calculations

2. WHEN indicator names contain spaces THEN normalizer SHALL replace with underscores
   - **Pattern**: `"SMA Fast"` → `"sma_fast"`
   - **Robustness**: Handle edge cases from LLM variations
   - **Consistency**: Ensure valid Python identifiers

3. WHEN normalizer transforms names THEN it SHALL log transformations
   - **Level**: DEBUG for name transformations
   - **Message**: `"Normalized indicator name: 'SMA_Fast' → 'sma_fast'"`
   - **Metric**: Count name transformations applied

4. WHEN names are already lowercase THEN normalizer SHALL leave unchanged
   - **Efficiency**: Skip transformation if pattern already matches
   - **Idempotency**: Repeated normalization produces same result
   - **Test**: Verify no unnecessary transformations

5. IF name transformation produces invalid identifier THEN normalizer SHALL raise NormalizationError
   - **Example**: Empty string, starts with digit, contains invalid chars
   - **Safety**: Fail fast on edge cases
   - **Message**: Clear indication of what's invalid

### Requirement 2: Pydantic Validator Implementation

**User Story:** As a system maintainer, I want Pydantic to be the primary validation mechanism, so that validation is strict, errors are clear, and architecture is simplified.

#### Acceptance Criteria

1. WHEN PydanticValidator is instantiated THEN it SHALL load Strategy model from `src/models/strategy_models.py`
   - **Import**: `from src.models.strategy_models import Strategy`
   - **Reuse**: Leverage models generated in Phase 1 Task 3
   - **No Changes**: Existing Pydantic models work as-is

2. WHEN normalized YAML is validated THEN PydanticValidator SHALL call `Strategy.model_validate(normalized_data)`
   - **Returns**: Pydantic Strategy instance if valid
   - **Raises**: `pydantic.ValidationError` if invalid
   - **Type Coercion**: Automatic conversion (e.g., string '14' → int 14)

3. WHEN validation succeeds THEN PydanticValidator SHALL return `(True, [])`
   - **Tuple**: Compatible with existing YAMLSchemaValidator interface
   - **Clean Data**: Use `model_dump(mode='json')` for downstream consumption
   - **Log**: INFO level success message

4. WHEN validation fails THEN PydanticValidator SHALL extract and format Pydantic errors
   - **Field Paths**: Include full path (e.g., `indicators.technical_indicators.0.type`)
   - **Expected/Actual**: Show what was expected vs. what was received
   - **Human Readable**: Format as list of strings
   - **Return**: `(False, error_messages)`

5. IF Pydantic model has field validators THEN they SHALL execute automatically
   - **Example**: Uppercase type conversion as double-insurance
   - **Benefit**: Additional automatic corrections beyond normalization
   - **Pattern**: `@field_validator('type', mode='before')`

### Requirement 3: Replace JSON Schema Validation

**User Story:** As a system architect, I want to remove the redundant JSON Schema validation layer, so that Pydantic is the single source of truth and architecture is simpler.

#### Acceptance Criteria

1. WHEN YAMLSchemaValidator.validate() is called with normalize=True THEN it SHALL:
   - **Step 1**: Call `normalize_yaml(yaml_spec)` (enhanced with name normalization)
   - **Step 2**: Call `PydanticValidator.validate(normalized_spec)` (NEW)
   - **Step 3**: Return `(is_valid, errors)` tuple
   - **Removed**: JSON Schema validation (redundant, Pydantic is stricter)

2. WHEN both normalizer and Pydantic succeed THEN validation SHALL return `(True, [])`
   - **Success Path**: No further validation needed
   - **Performance**: Faster than previous two-stage validation
   - **Simplicity**: One validation source

3. WHEN normalizer fails (NormalizationError) THEN validation SHALL:
   - **Catch**: NormalizationError exception
   - **Log**: WARNING with error details
   - **Return**: `(False, [error_message])`
   - **No Retry Here**: Retry logic belongs in Phase 3 pipeline integration

4. WHEN Pydantic fails (ValidationError) THEN validation SHALL:
   - **Extract**: Error messages from Pydantic exception
   - **Format**: Convert to list of strings
   - **Log**: WARNING with field paths
   - **Return**: `(False, error_messages)`

5. IF normalize=False THEN YAMLSchemaValidator SHALL use legacy JSON Schema validation
   - **Backward Compatibility**: Support existing code paths
   - **Feature Flag**: Gradual rollout capability
   - **Safety**: No breaking changes during transition

6. WHEN all 926 existing tests are run with normalize=False THEN they SHALL pass
   - **Requirement**: 100% pass rate (backward compatibility)
   - **Command**: `pytest -v`
   - **Validation**: Ensure no regressions

### Requirement 4: End-to-End Testing and Validation

**User Story:** As a QA engineer, I want comprehensive testing to verify Phase 2 achieves 85-87% success rate, so that we confirm the normalizer enhancement solves the identified failures.

#### Acceptance Criteria

1. WHEN integration tests are run with enhanced normalizer THEN success rate SHALL be ≥85%
   - **Baseline**: Phase 1 achieved 71.4% (10/14 fixtures)
   - **Target**: Phase 2 should reach ≥85% (12/14 fixtures)
   - **Test Set**: Same 14 fixtures from Phase 1
   - **Evidence**: Name normalization should fix all 4 failures

2. WHEN 50-100 iterations with real LLM API are executed THEN validation success rate SHALL be ≥85%
   - **Test Script**: `python scripts/test_yaml_validation_phase2.py --iterations 100`
   - **Real LLM**: Use Gemini 2.5 Flash or Grok for realistic testing
   - **Measurement**: Count successful validations / total iterations
   - **Statistical Significance**: 100 iterations provides confidence

3. WHEN tests compare before vs. after THEN improvement SHALL be measurable
   - **Baseline (Phase 1)**: 71.4% success rate
   - **Phase 2 (Enhanced Normalizer + Pydantic)**: ≥85% success rate
   - **Improvement**: ≥13.6% increase
   - **Verification**: Statistical test confirms significance

4. IF success rate is <85% THEN failure analysis SHALL identify root causes
   - **Categorize**: By error type (structural, type, semantic, pattern)
   - **Prioritize**: Identify highest-frequency failure patterns
   - **Document**: Feed into Phase 3 pipeline integration planning
   - **Decision**: Determine if additional normalizer enhancements needed

5. WHEN name normalization tests are run THEN all transformations SHALL work correctly
   - **Test Cases**:
     - Uppercase → lowercase: "SMA_Fast" → "sma_fast"
     - Spaces → underscores: "SMA Fast" → "sma_fast"
     - Already lowercase → unchanged: "sma_fast" → "sma_fast"
     - Invalid names → NormalizationError
   - **Coverage**: >90% for name normalization code

6. WHEN all 926 existing tests are run THEN they SHALL pass
   - **Command**: `pytest -v`
   - **Requirement**: 100% pass rate with normalize=False
   - **Safety**: Ensure backward compatibility

## Non-Functional Requirements

### Code Architecture and Modularity

**Single Responsibility Principle:**
- `src/generators/yaml_normalizer.py`: Data transformation (add name normalization)
- `src/generators/pydantic_validator.py`: Pydantic validation (NEW)
- `src/generators/yaml_schema_validator.py`: Orchestration (normalize → validate)
- `src/models/strategy_models.py`: Pydantic models (no changes)

**Modular Design:**
- Name normalization is separate function: `_normalize_indicator_name(name: str) -> str`
- PydanticValidator is stateless: `validate(dict) -> Tuple[bool, List[str]]`
- Each component testable independently

**Dependency Management:**
- Normalizer: Python stdlib only (no new dependencies)
- PydanticValidator: `pydantic` (existing dependency) + `strategy_models.py`
- YAMLSchemaValidator: Depends on both (orchestrates)

**Clear Interfaces:**
```python
# Enhanced Normalizer
def _normalize_indicator_name(name: str) -> str:
    """Convert indicator name to lowercase with underscores."""
    return name.lower().replace(' ', '_')

# PydanticValidator
class PydanticValidator:
    def validate(self, data: dict) -> Tuple[bool, List[str]]:
        """Validate against Pydantic Strategy model."""
        try:
            strategy = Strategy.model_validate(data)
            return (True, [])
        except ValidationError as e:
            errors = [str(err) for err in e.errors()]
            return (False, errors)
```

### Performance

**Name Normalization Speed:**
- **Target**: <1ms per indicator (simple string operations)
- **Impact**: Negligible (typically 3-5 indicators per strategy)
- **Total Overhead**: <5ms per iteration

**Pydantic Validation Speed:**
- **Target**: <20ms per iteration (Pydantic is fast)
- **Comparison**: Faster than JSON Schema validation
- **Net Impact**: Neutral or positive (removing JSON Schema offsets Pydantic cost)

**Integration Impact:**
- **Total Validation Time**: <25ms (normalization + Pydantic)
- **Percentage of Iteration**: <0.04% (25ms / 60000ms backtest)
- **Acceptable**: Validation overhead is negligible

### Security

**Code Execution Safety:**
- **Name Normalization**: Only string operations (no eval/exec)
- **Pydantic Validation**: Safe validation (no code execution)
- **Input Validation**: Pattern matching prevents injection

**Data Integrity:**
- **Immutability**: Deep copy in normalizer (input not mutated)
- **Type Safety**: Pydantic enforces strict types
- **Validation Chain**: Normalizer → Pydantic (two defense layers)

### Reliability

**Error Handling:**
- **NormalizationError**: Clear signal for retry (Phase 3)
- **ValidationError**: Detailed field-level errors
- **Graceful Degradation**: Fallback to legacy validation if normalize=False

**Backward Compatibility:**
- **Feature Flag**: `normalize` parameter controls new behavior
- **Test Coverage**: 926 tests must pass with normalize=False
- **Migration Path**: Gradual rollout without breaking changes

**Monitoring:**
- **Success Rate Tracking**: Log normalization + validation success/failure
- **Name Transformation Stats**: Count how often names need normalization
- **Error Categorization**: Track error types for Phase 3 planning

### Usability

**Developer Experience:**
- **Clear Error Messages**: "indicator name 'SMA_Fast' normalized to 'sma_fast'"
- **Field Paths in Errors**: "indicators.technical_indicators.0.name"
- **Testing**: Easy to add new test cases (use existing fixture pattern)

**Integration Simplicity:**
- **Drop-in Enhancement**: Modify existing normalizer function
- **No Configuration**: Works automatically
- **Optional**: Controlled by normalize parameter

**Documentation:**
- **API Docs**: Comprehensive docstrings (Google-style)
- **Integration Guide**: Update yaml_schema_validator.py
- **Troubleshooting**: Document name normalization logic

### Maintainability

**Code Quality:**
- **Type Hints**: All functions fully typed (mypy strict)
- **PEP 8 Compliance**: flake8 passing, 100-char line length
- **Test Coverage**: >85% for yaml_normalizer.py, >80% for pydantic_validator.py

**Configuration Management:**
- **No Configuration**: Name normalization rules are hardcoded (simple and clear)
- **Feature Flag**: normalize parameter in YAMLSchemaValidator
- **Easy to Extend**: Add new transformation patterns as needed

**Future-Proofing:**
- **Plugin Architecture**: Easy to add validators (inherit from PydanticValidator)
- **Schema Evolution**: Regenerate Pydantic models if schema changes
- **Migration to AST**: Name normalization can be replaced without interface changes

---

**Document Version**: 1.0
**Created**: 2025-10-27
**Status**: Draft - Pending Approval
**Owner**: Personal Project (週/月交易系統)
**Dependencies**: Phase 1 Failure Analysis (PHASE1_FAILURE_ANALYSIS.md)
**Estimated Effort**: 5-7 hours
- Task 1: Enhanced Normalizer (name normalization) - 1.5h
- Task 2: PydanticValidator Implementation - 2h
- Task 3: YAMLSchemaValidator Integration - 1h
- Task 4: Testing and Validation (50-100 iterations) - 1.5h
