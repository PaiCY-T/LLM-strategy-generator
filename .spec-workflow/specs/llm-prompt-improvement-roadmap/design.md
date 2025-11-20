# LLM Prompt Engineering Improvement Roadmap - Design Document

## Overview

**Design Approach**: Test-Driven Development (TDD) with systematic prompt engineering improvements across 4 phases.

**Core Strategy**: Incrementally enhance LLM prompt quality through RED-GREEN-REFACTOR-VALIDATE cycles, targeting specific error categories identified in post-fix validation testing. Each phase adds validation layers and documentation to reduce LLM hallucination and improve code generation accuracy.

**Success Path**: 20% → 55-60% (Phase 1) → 65% (Phase 2) → 75% (Phase 3) → 87-90% (Phase 4)

**Key Innovation**: Complete field catalog exposure (not truncated), system prompt with Chain of Thought guidance, and framework-based edge case handling to simplify LLM task complexity.

## Architecture

### Component Layer Structure

```
┌─────────────────────────────────────────────────────────────┐
│ LLM Interface Layer (Gemini 2.5 Flash - 1M token context)  │
│  - System Prompt (NEW)                                      │
│  - Chain of Thought Guidance (NEW)                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Prompt Builder (src/innovation/prompt_builder.py)          │
│  - _build_system_prompt() (NEW)                             │
│  - _build_api_documentation_section() (ENHANCED)            │
│  - _build_code_requirements() (ENHANCED)                    │
│  - _build_validation_helpers() (NEW)                        │
│  - Token monitoring integration (NEW)                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Validation Layer (src/innovation/validators/)              │
│  - field_validator.py (NEW)                                 │
│  - structure_validator.py (ENHANCED)                        │
│  - metric_validator.py (ENHANCED)                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Execution Framework (src/backtest/strategy_executor.py)    │
│  - execute_strategy_with_safeguards() (NEW)                 │
│  - Automatic edge-case handling (NEW)                       │
│  - Liquidity filtering (NEW)                                │
│  - Position normalization (NEW)                             │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

```
User Feedback → Prompt Builder → LLM (Gemini 2.5 Flash)
                                        ↓
                              Generated Strategy Code
                                        ↓
                    Field Validator → Structure Validator
                                        ↓
                          Strategy Executor (with safeguards)
                                        ↓
                              Backtest & Metrics
                                        ↓
                          Metric Validator → Results
```

## Components and Interfaces

### 1. Prompt Builder Enhancement (`src/innovation/prompt_builder.py`)

**New Methods**:
- `_build_system_prompt() -> str`
  - Returns: System prompt with LLM persona definition and Chain of Thought guidance
  - Purpose: Forces LLM to outline approach before coding

- `_build_api_documentation_section() -> str` (ENHANCED)
  - Returns: **Complete** field catalog (all fields, not first 20)
  - Format: Python list format for easy copy-paste
  - Includes: fundamental_features, financial_statement, price_earning_ratio

- `_build_validation_helpers() -> str` (NEW)
  - Returns: Helper functions for field name validation
  - Includes: `validate_field_exists()` example code

**Modified Methods**:
- `build_creation_prompt(feedback: str) -> str`
  - Now includes system prompt as first section
  - Returns: Complete prompt with all sections

**Token Monitoring Integration**:
- All prompt building methods tracked with tiktoken
- Token count validation before LLM call
- Warning if approaching 100K token limit (safe threshold for 1M context)

### 2. Field Validator (`src/innovation/validators/field_validator.py`) - NEW

```python
class FieldValidator:
    """Validates field names against FinLab API catalog."""

    def __init__(self, valid_fields: dict):
        self.valid_fields = valid_fields

    def validate_code(self, code: str) -> tuple[bool, list[str]]:
        """
        Returns: (is_valid, errors)
        Checks: data.get() calls against valid field catalog
        """
```

**Interface**:
- Input: Generated strategy code as string
- Output: (bool, list[str]) - (is valid, list of invalid fields found)
- Side effects: None (pure validation)

### 3. Strategy Executor with Safeguards (`src/backtest/strategy_executor.py`) - NEW

```python
def execute_strategy_with_safeguards(
    strategy_code: str,
    data: DataCache,
    min_position_size: float = 0.01
) -> pd.DataFrame:
    """
    Execute strategy with automatic edge-case handling.

    Framework handles:
    - Empty position fallback
    - Liquidity filtering
    - Position normalization

    LLM only needs to:
    - Define core strategy logic
    - Return boolean DataFrame
    """
```

**Interface**:
- Input: Strategy code string, DataCache, optional min_position_size
- Output: Normalized position DataFrame
- Side effects: Logging (warnings for edge cases triggered)

### 4. Token Monitoring (`src/innovation/token_monitor.py`) - NEW

```python
def validate_phase_completion(
    prompt: str,
    success_rate: float
) -> dict:
    """
    Validate phase with token monitoring.

    Returns: {
        'success_rate': float,
        'token_count': int,
        'token_limit': int,
        'token_usage_pct': float,
        'within_budget': bool
    }
    """
```

## Data Models

### Field Catalog Structure

```python
VALID_FINLAB_FIELDS = {
    "fundamental_features": [
        "fundamental_features:股價淨值比",
        "fundamental_features:本益比",
        # ... (50+ fields, ALL listed)
    ],
    "financial_statement": [
        "financial_statement:營業收入",
        "financial_statement:營業利益",
        # ... (100+ fields, ALL listed)
    ],
    "price_earning_ratio": [
        "price_earning_ratio:股價淨值比",
        "price_earning_ratio:本益比",
        "price_earning_ratio:殖利率"
    ]
}
```

### Validation Result Model

```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    validator_type: str  # 'field', 'structure', 'metric'
```

### Phase Validation Model

```python
@dataclass
class PhaseValidationResult:
    phase_number: int
    success_rate: float
    token_count: int
    token_usage_pct: float
    within_budget: bool
    errors_by_type: dict[str, int]
    timestamp: str
```

## Error Handling

### Error Classification System

**Phase 1 Targets (Field Name Errors)**:
- Error Type: KeyError, AttributeError on data.get()
- Detection: Field validator checks against VALID_FINLAB_FIELDS
- Recovery: Validation failure → retry with field name suggestions
- Logging: Record invalid field attempts for pattern analysis

**Phase 2 Targets (Code Structure Errors)**:
- Error Type: SyntaxError, NameError, missing return statement
- Detection: AST parsing + structure validator
- Recovery: Validation failure → retry with structure requirements
- Logging: Record structure violations for improvement

**Phase 3 Targets (API Misuse)**:
- Error Type: TypeError, invalid method calls
- Detection: API pattern matching + execution simulation
- Recovery: Validation failure → retry with correct API examples
- Logging: Record API misuse patterns

**Phase 4 Targets (Edge Cases)**:
- Error Type: Empty positions, NaN/Inf metrics
- Detection: Framework safeguards in execute_strategy_with_safeguards()
- Recovery: Automatic fallback strategies (no LLM retry needed)
- Logging: Warning level (not error, handled automatically)

### Error Propagation Strategy

```
LLM Generation → Validation Layers → Execution Framework
                       ↓                     ↓
                   FAIL: Retry         FAIL: Safeguard
                   with feedback       (automatic recovery)
```

**Critical Path**: Field validation must pass before code execution attempt

## Testing Strategy

### TDD Cycle per Phase

**RED (Test First)**:
```python
def test_field_validator_rejects_invalid_fields():
    """Write failing test before implementation"""
    validator = FieldValidator(VALID_FINLAB_FIELDS)
    code = "data.get('fundamental_features:不存在的欄位')"
    is_valid, errors = validator.validate_code(code)
    assert not is_valid
    assert "不存在的欄位" in errors[0]
```

**GREEN (Minimum Implementation)**:
```python
class FieldValidator:
    def validate_code(self, code: str) -> tuple[bool, list[str]]:
        # Minimum code to pass test
        pattern = r"data\.get\('([^']+)'\)"
        matches = re.findall(pattern, code)
        errors = [f for f in matches if f not in self.all_valid_fields]
        return len(errors) == 0, errors
```

**REFACTOR (Improve)**:
- Add fuzzy matching for field name suggestions
- Cache validation results
- Optimize regex patterns

**VALIDATE (20-iteration test)**:
```bash
python3 run_20iteration_three_mode_test.py
# Expected: Phase 1 → 55-60% success rate
```

### Test Coverage Requirements

**Unit Tests** (≥90% coverage):
- Field validator: All validation logic paths
- Structure validator: All code structure requirements
- Token monitor: All threshold conditions

**Integration Tests** (≥80% coverage):
- Prompt builder: All section combinations
- Validation pipeline: All error recovery paths
- Executor safeguards: All edge case handlers

**Statistical Tests** (20+ iterations per phase):
- Success rate measurement with confidence intervals
- Error distribution analysis
- Token usage monitoring

### Validation Metrics per Phase

**Phase 1 Validation**:
- Success rate: ≥55% (target: 55-60%)
- Field errors: <15% of failures (down from 50%)
- Token count: <25K (safe margin from 100K limit)

**Phase 2 Validation**:
- Success rate: ≥65%
- Structure errors: <5% of failures (down from 18.8%)
- Token count: <30K

**Phase 3 Validation**:
- Success rate: ≥75%
- API errors: <2% of failures (down from 6.2%)
- Token count: <35K

**Phase 4 Validation**:
- Success rate: ≥87%
- Metric errors: <5% of failures (down from 18.8%)
- Token count: <40K (well within 100K safe limit)

### Continuous Validation

**After Each Code Change**:
1. Run unit tests (pytest)
2. Check token count (tiktoken)
3. Validate prompt structure
4. Run 5-iteration smoke test

**After Each Phase**:
1. Run 20-iteration validation test
2. Analyze error distribution
3. Verify success rate targets met
4. Document lessons learned
5. Update token usage trends

**Final Validation** (before production):
- 50-iteration comprehensive test
- All modes: LLM Only, Hybrid, Factor Graph
- Performance regression check
- Documentation completeness review
