# Requirements Document: Exit Conditions Mandate

## Introduction

Trading strategies require clear exit logic to determine when to close positions. Without exit conditions, strategies cannot function properly - they lack the critical mechanism to realize profits or limit losses. This specification mandates that all trading strategies MUST include explicit exit conditions and establishes a Three-Layer Defense architecture to ensure completeness.

**Context**: During Phase 0 smoke testing, a fundamental question was raised: "如果不定義出場邏輯，交易策略要怎麼成立？" (If exit logic is not defined, how can a trading strategy work?). This led to the discovery that exit_conditions were incorrectly marked as optional in the schema, allowing incomplete strategies to pass validation.

**Value**:
- Prevents generation of incomplete trading strategies
- Ensures all strategies have well-defined risk management
- Improves system reliability by catching missing exit logic at multiple validation layers
- Aligns with financial best practices (every entry must have a corresponding exit plan)

## Alignment with Product Vision

This feature directly supports multiple product principles from `product.md`:

1. **避免過度工程化** (Avoid Over-Engineering): Simple, pragmatic solution using existing validation infrastructure. No complex new systems - just making exit_conditions required.

2. **從數據中學習** (Learn from Data): Discovery driven by actual Phase 0 testing results showing incomplete strategies passing validation.

3. **自動化優先** (Automation First): Three-Layer Defense ensures exit conditions are enforced automatically at schema, prompt, and normalization levels without manual intervention.

4. **可觀察性** (Observability): Phase 0 smoke testing provides clear visibility into validation success rate (80% pass rate with <$0.0001 cost per test).

5. **向後兼容** (Backward Compatibility): Implementation preserves existing normalizer transformation behavior while adding stricter schema validation.

## Requirements

### Requirement 1: Schema-Level Exit Conditions Enforcement

**User Story:** As a trading system, I want exit_conditions to be required in the strategy schema, so that incomplete strategies are rejected at validation time.

#### Acceptance Criteria

1. WHEN strategy YAML is validated THEN the system SHALL require the exit_conditions field in the schema
2. IF exit_conditions field is missing THEN the system SHALL fail validation with a clear error message
3. WHEN a strategy includes exit_conditions THEN the system SHALL accept it if other validation passes
4. IF a strategy has empty exit_conditions THEN the system SHALL fail validation

**Priority**: CRITICAL
**Effort**: 1 line change (schema update)
**Risk**: LOW (validation-only change, no execution logic)

### Requirement 2: Prompt-Level Exit Conditions Guidance

**User Story:** As an LLM integration system, I want prompts to explicitly request exit conditions, so that LLM-generated strategies include complete exit logic.

#### Acceptance Criteria

1. WHEN calling LLM for strategy generation THEN the prompt SHALL explicitly request exit conditions
2. IF the prompt template is used THEN it SHALL include example exit conditions
3. WHEN LLM generates YAML THEN it SHOULD include exit conditions matching the schema format
4. IF exit conditions are missing from LLM output THEN schema validation SHALL catch the error

**Priority**: HIGH
**Effort**: Prompt template updates
**Risk**: MEDIUM (LLMs may still ignore instructions)

### Requirement 3: Normalizer-Level Format Transformation

**User Story:** As a YAML normalizer, I want to transform array-format exit_conditions to object format, so that code generation templates work correctly.

#### Acceptance Criteria

1. WHEN normalizer receives array-format exit_conditions THEN it SHALL convert to object format with threshold_rules
2. IF exit_conditions are already in object format THEN normalizer SHALL preserve the structure
3. WHEN transformation completes THEN the system SHALL maintain all original condition semantics
4. IF exit_conditions contain strings THEN normalizer SHALL wrap them in condition objects

**Priority**: HIGH
**Effort**: Normalizer logic update (already implemented)
**Risk**: LOW (transformation only, no semantic changes)

### Requirement 4: Validator Dual-Format Support

**User Story:** As a YAML validator, I want to handle both array and object formats for conditions, so that schema's oneOf constraint is properly enforced.

#### Acceptance Criteria

1. WHEN validator encounters array-format conditions THEN it SHALL validate array items
2. IF validator encounters object-format conditions THEN it SHALL validate threshold_rules and ranking_rules
3. WHEN field references are checked THEN the system SHALL verify against defined indicators regardless of format
4. IF format is invalid THEN validator SHALL report specific format errors

**Priority**: HIGH
**Effort**: Validator conditional logic (already implemented)
**Risk**: LOW (backward compatible)

### Requirement 5: Phase 0 Dry-Run Testing

**User Story:** As a development team, I want to validate the entire LLM→YAML→Code pipeline without execution risk, so that I can test changes safely and cheaply.

#### Acceptance Criteria

1. WHEN Phase 0 test runs THEN Docker SHALL be disabled
2. IF test reaches code generation THEN it SHALL only validate AST syntax without execution
3. WHEN test completes THEN it SHALL generate artifacts (YAML, code, results JSON)
4. IF test passes ≥80% THEN it SHALL be considered acceptable (<$0.0001 per test cost)
5. WHEN LLM generates invalid YAML THEN test SHALL fail at appropriate validation layer

**Priority**: HIGH
**Effort**: Test script creation (already implemented)
**Risk**: ZERO (dry-run mode only)

### Requirement 6: Documentation and Rationale

**User Story:** As a future developer, I want clear documentation explaining why exit_conditions are mandatory, so that I understand the architectural decision.

#### Acceptance Criteria

1. WHEN reading yaml_normalizer.py docstring THEN it SHALL explain the Three-Layer Defense architecture
2. IF schema is examined THEN exit_conditions SHALL be in the required array with inline comment
3. WHEN reviewing design documents THEN rationale SHALL reference the fundamental question about strategy completeness
4. IF documentation is incomplete THEN it SHALL be updated before spec approval

**Priority**: MEDIUM
**Effort**: Documentation updates
**Risk**: NONE (documentation only)

## Non-Functional Requirements

### Code Architecture and Modularity

- **Single Responsibility Principle**:
  - Schema enforces data contract
  - Normalizer transforms format
  - Validator checks semantic correctness
  - Each component has one clear responsibility

- **Modular Design**:
  - Three-Layer Defense distributes responsibility across independent modules
  - Changes to one layer don't require changes to others
  - Each layer can be tested independently

- **Dependency Management**:
  - Schema is the source of truth (no dependencies)
  - Normalizer depends only on schema
  - Validator depends on schema + normalizer
  - Linear dependency chain prevents circular dependencies

- **Clear Interfaces**:
  - Schema uses JSON Schema v7 standard
  - Normalizer exposes functional API (normalize_yaml function)
  - Validator returns structured error lists
  - All interfaces documented with type hints

### Performance

- **Schema Validation**: <5ms per strategy (jsonschema library)
- **Normalization**: <10ms per strategy (dict operations only)
- **AST Validation**: <50ms per strategy (Python compile)
- **Phase 0 Test**: 1-2 seconds end-to-end including LLM API call
- **Cost**: <$0.0001 per Phase 0 test (google/gemini-2.5-flash-lite)

### Security

- **Zero Execution Risk**: Phase 0 testing uses dry-run mode with Docker disabled
- **No Code Execution**: AST validation only, no eval/exec
- **Import Safety**: Dangerous imports (os.system, subprocess, eval, exec) are checked
- **API Key Protection**: Stored in environment variables, never logged or persisted

### Reliability

- **80% Pass Rate**: Acceptable for Phase 0 smoke testing (user-verified)
- **Validation Success**: 8/10 test cases passing consistently
- **Known Failures**: Code generation dependent on LLM output quality (expected variability)
- **Artifact Persistence**: All test outputs saved for debugging (phase0_*.yaml, phase0_*.py, phase0_*.json)
- **Graceful Degradation**: If normalizer fails, validator catches it; if validator fails, code generator fails safely

### Usability

- **Clear Error Messages**: Schema validation errors specify missing fields
- **Comprehensive Logging**: Phase 0 test outputs detailed pass/fail status for each test case
- **Artifact Generation**: Intermediate outputs (raw YAML, normalized YAML, generated code) saved for inspection
- **Status Dashboard**: Test summary shows pass rate, timing, and cost metrics
- **Developer Experience**: Docstrings explain design principles and architectural decisions inline

## Success Metrics

### Phase 0 Testing Metrics (Already Achieved)
- ✅ Pass Rate: 80% (8/10 tests)
- ✅ Cost: <$0.0001 per test
- ✅ Time: 1-2 seconds per test
- ✅ Zero Execution Risk: Maintained throughout

### Validation Metrics (Target)
- Schema Validation: 100% catch rate for missing exit_conditions
- Prompt Compliance: ≥90% LLM-generated strategies include exit conditions
- Normalizer Success: 100% array→object conversion for valid inputs
- Validator Accuracy: 100% correct handling of both array/object formats

### Integration Metrics (Target)
- Backward Compatibility: 100% (existing tests pass)
- Documentation Coverage: All three layers documented
- Test Coverage: >80% for modified files
- Regression Prevention: Zero regressions in 926+ existing tests

## Out of Scope

- **AST-based mutation for exit conditions**: Still using regex-based mutations (per avoid over-engineering principle)
- **Exit condition optimization**: This spec only ensures exit conditions exist, not that they're optimal
- **Multi-condition logic (AND/OR/NOT)**: Schema supports it but prompts keep it simple
- **Dynamic exit conditions**: Time-based or market-condition-based exits not yet supported
- **Exit condition backtesting**: Validation happens but performance analysis is separate

## References

- **Conversation Context**: User question "如果不定義出場邏輯，交易策略要怎麼成立？" (Phase 0 testing discussion)
- **Implementation Files**:
  - `schemas/strategy_schema_v1.json:8` (exit_conditions required)
  - `src/generators/yaml_normalizer.py:10-23` (Three-Layer Defense docstring)
  - `src/generators/yaml_schema_validator.py:401-419` (dual format handling)
  - `run_phase0_smoke_test.py` (smoke test implementation)
  - `config/test_phase0_smoke.yaml` (dry-run configuration)
- **Test Results**: `artifacts/phase0_test_results.json` (80% pass rate)
- **Status Report**: `.spec-workflow/PROJECT_STATUS_REPORT.md:349-401` (Phase 0 summary)

---

**Document Version**: 1.0
**Created**: 2025-10-27
**Status**: Pending Approval
**Spec Name**: exit-conditions-mandate
