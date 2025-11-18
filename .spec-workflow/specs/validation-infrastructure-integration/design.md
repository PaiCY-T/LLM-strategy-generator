# Validation Infrastructure Integration - Design Document

## Overview

### Design Philosophy

This design follows **Test-Driven Development (TDD)** methodology with **incremental integration** to transform complete but unused validation infrastructure into a production-ready system. The approach prioritizes:

1. **Safety First**: Feature flags enable instant rollback at any integration stage
2. **Evidence-Based**: All design decisions validated through metrics and A/B testing
3. **Zero Breaking Changes**: Backward compatibility maintained through defensive design
4. **Performance Budget**: <10ms total validation latency strictly enforced

### Integration Strategy

**Layered Defense Architecture**: Three independent validation layers integrated sequentially over 4 weeks, each with isolated feature flags and rollback capability:

- **Week 1**: Layer 1 (DataFieldManifest) - Field suggestions in LLM prompts
- **Week 2**: Layer 2 (FieldValidator) + ErrorFeedbackLoop - Code validation and retry
- **Week 3**: Layer 3 (SchemaValidator) + Circuit Breaker - YAML validation and cost control
- **Week 4**: Production polish - Metadata, monitoring, documentation

### Key Design Decisions

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| Feature flags per layer | Independent control, granular rollback | Slight complexity increase |
| ErrorFeedbackLoop max_retries=3 | Balance success rate vs API cost | May miss edge cases needing 4+ retries |
| Circuit breaker after 2 identical errors | Prevent API waste quickly | May stop valid retry scenarios too early |
| <10ms validation budget | Maintain workflow performance | Limits validation complexity |
| Incremental 10%→50%→100% rollout | Risk mitigation through gradual deployment | Slower full deployment |

## Architecture

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     LLM Strategy Generation Workflow             │
│                                                                  │
│  ┌────────────┐       ┌─────────────────┐      ┌─────────────┐ │
│  │  Strategy  │──────>│  Iteration      │─────>│  Backtest   │ │
│  │  Learner   │       │  Executor       │      │  Executor   │ │
│  └────────────┘       └────────┬────────┘      └─────────────┘ │
│                                 │                                │
│                    ┌────────────▼───────────┐                   │
│                    │  Validation Gateway    │                   │
│                    │  (NEW INTEGRATION)     │                   │
│                    └────────────┬───────────┘                   │
│                                 │                                │
│        ┌────────────────────────┼────────────────────────┐      │
│        │                        │                        │      │
│  ┌─────▼──────┐        ┌───────▼────────┐      ┌───────▼─────┐│
│  │  Layer 1   │        │    Layer 2     │      │   Layer 3   ││
│  │DataField   │        │FieldValidator  │      │  Schema     ││
│  │ Manifest   │        │+ ErrorFeedback │      │ Validator   ││
│  └────────────┘        └────────────────┘      └─────────────┘│
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Circuit Breaker & Monitoring                 │  │
│  │   (Error Tracking, API Cost Control, Metrics Dashboard)  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Validation Gateway Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ValidationGateway Class                      │
│                    (NEW - src/validation/gateway.py)            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  validate_strategy(strategy_yaml: str, llm_generate_func)       │
│      │                                                           │
│      ├─> [1] Load Feature Flags (ENV)                          │
│      │     - ENABLE_VALIDATION_LAYER1                          │
│      │     - ENABLE_VALIDATION_LAYER2                          │
│      │     - ENABLE_VALIDATION_LAYER3                          │
│      │                                                           │
│      ├─> [2] Layer 1: DataFieldManifest                        │
│      │     if LAYER1: inject field suggestions into prompt     │
│      │     Performance: <1μs (already validated)               │
│      │                                                           │
│      ├─> [3] Parse YAML → dict                                 │
│      │     try: yaml.safe_load(strategy_yaml)                  │
│      │     except YAMLError: create synthetic error            │
│      │                                                           │
│      ├─> [4] Layer 3: SchemaValidator                          │
│      │     if LAYER3: validate(yaml_dict)                      │
│      │     Performance budget: <5ms                             │
│      │                                                           │
│      ├─> [5] ErrorFeedbackLoop                                 │
│      │     if errors: retry with feedback (max 3 times)        │
│      │     Circuit breaker: detect identical errors            │
│      │                                                           │
│      ├─> [6] Generate Strategy Code from validated YAML        │
│      │                                                           │
│      ├─> [7] Layer 2: FieldValidator                           │
│      │     if LAYER2: validate(strategy_code)                  │
│      │     AST parsing for invalid field detection             │
│      │     Performance budget: <5ms                             │
│      │                                                           │
│      └─> [8] Return ValidationResult + validated config        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Points

**Primary Integration Point**: `src/learning/iteration_executor.py` (Line 217-316)

**Before Integration** (Current - 0% success rate):
```python
def execute_iteration(self, iteration_num: int) -> IterationRecord:
    # Generate strategy
    strategy_code, strategy_id, generation = strategy.generate(context)

    # ❌ NO VALIDATION - Execute directly
    execution_result = self._execute_strategy(strategy_code, ...)
```

**After Integration** (Target - 70-85% success rate):
```python
def execute_iteration(self, iteration_num: int) -> IterationRecord:
    # Generate strategy with validation
    validation_gateway = ValidationGateway(
        manifest=self.manifest,
        enable_layer1=os.getenv('ENABLE_VALIDATION_LAYER1', 'false') == 'true',
        enable_layer2=os.getenv('ENABLE_VALIDATION_LAYER2', 'false') == 'true',
        enable_layer3=os.getenv('ENABLE_VALIDATION_LAYER3', 'false') == 'true',
    )

    # Validate before execution
    validation_result = validation_gateway.validate_strategy(
        strategy_yaml=strategy_yaml,
        llm_generate_func=lambda prompt: strategy.generate(prompt)
    )

    if not validation_result.success:
        # Record validation failure
        return IterationRecord(
            success=False,
            error=validation_result.error_summary,
            validation_errors=validation_result.errors
        )

    # ✅ VALIDATED - Execute with confidence
    execution_result = self._execute_strategy(
        validated_config=validation_result.config,
        ...
    )
```

## Components and Interfaces

### 1. ValidationGateway (NEW Component)

**Location**: `src/validation/gateway.py`

**Responsibility**: Orchestrate all validation layers and retry logic

**Interface**:
```python
class ValidationGateway:
    """
    Central orchestrator for all validation layers.

    Manages feature flags, validation execution, error feedback loop,
    and circuit breaker logic. Provides single entry point for
    strategy validation in iteration_executor.
    """

    def __init__(
        self,
        manifest: DataFieldManifest,
        enable_layer1: bool = True,
        enable_layer2: bool = True,
        enable_layer3: bool = True,
        max_retries: int = 3
    ):
        """Initialize validation gateway with feature flags."""
        self.manifest = manifest
        self.enable_layer1 = enable_layer1
        self.enable_layer2 = enable_layer2
        self.enable_layer3 = enable_layer3

        # Initialize validators
        self.field_validator = FieldValidator(manifest) if enable_layer2 else None
        self.schema_validator = SchemaValidator() if enable_layer3 else None
        self.error_loop = ErrorFeedbackLoop(max_retries=max_retries)

        # Circuit breaker state
        self.error_signatures: Dict[str, int] = {}
        self.circuit_breaker_threshold = 2

    def validate_strategy(
        self,
        strategy_yaml: str,
        llm_generate_func: Callable[[str], str]
    ) -> ValidationResult:
        """
        Validate strategy through all enabled layers with retry logic.

        Args:
            strategy_yaml: YAML string from LLM
            llm_generate_func: Function to regenerate strategy on errors

        Returns:
            ValidationResult with success status, validated config, errors
        """
        pass  # Implementation in Week 2-3

    def inject_field_suggestions(self, base_prompt: str) -> str:
        """
        Layer 1: Add field suggestions to LLM prompt.

        Args:
            base_prompt: Original LLM prompt

        Returns:
            Enhanced prompt with field suggestions and COMMON_CORRECTIONS
        """
        pass  # Implementation in Week 1
```

**Dependencies**:
- DataFieldManifest (existing)
- FieldValidator (existing)
- SchemaValidator (existing)
- ErrorFeedbackLoop (existing)

### 2. ValidationResult (NEW Data Structure)

**Location**: `src/validation/result.py`

**Responsibility**: Encapsulate validation outcome with structured errors

**Interface**:
```python
@dataclass
class ValidationResult:
    """
    Result from ValidationGateway.validate_strategy().

    Provides comprehensive validation outcome including success status,
    validated configuration, error details, and retry metadata.
    """

    success: bool
    """Whether validation passed (True) or failed (False)"""

    config: Optional[Dict] = None
    """Validated configuration dict (only if success=True)"""

    errors: List[ValidationError] = field(default_factory=list)
    """List of validation errors (from Layer 2 or Layer 3)"""

    error_summary: str = ""
    """Human-readable error summary for logging"""

    retry_count: int = 0
    """Number of retry attempts made"""

    error_history: List[str] = field(default_factory=list)
    """Error messages from each retry attempt"""

    circuit_breaker_triggered: bool = False
    """Whether circuit breaker stopped retry loop"""

    validation_time_ms: float = 0.0
    """Total validation time in milliseconds"""

    layer1_applied: bool = False
    """Whether Layer 1 (field suggestions) was enabled"""

    layer2_applied: bool = False
    """Whether Layer 2 (code validation) was enabled"""

    layer3_applied: bool = False
    """Whether Layer 3 (schema validation) was enabled"""
```

### 3. Enhanced BacktestResult (MODIFIED)

**Location**: `src/execution/backtest_result.py`

**Modification**: Add validation metadata fields

**New Fields**:
```python
@dataclass
class BacktestResult:
    # ... existing fields ...

    # NEW: Validation metadata
    validation_passed: bool = True
    """Whether strategy passed validation (default: True for backward compat)"""

    validation_errors: List[str] = field(default_factory=list)
    """List of validation error messages (empty if validation_passed)"""

    error_category: Optional[str] = None
    """Error category: 'field' | 'schema' | 'type' | None"""

    retry_count: int = 0
    """Number of validation retry attempts"""
```

### 4. IterationExecutor (MODIFIED)

**Location**: `src/learning/iteration_executor.py`

**Integration Points**:

**Point A: Initialization** (Line ~100-150)
```python
class IterationExecutor:
    def __init__(self, ...):
        # ... existing initialization ...

        # NEW: Initialize validation gateway
        self.validation_gateway = ValidationGateway(
            manifest=DataFieldManifest(),
            enable_layer1=os.getenv('ENABLE_VALIDATION_LAYER1', 'false').lower() == 'true',
            enable_layer2=os.getenv('ENABLE_VALIDATION_LAYER2', 'false').lower() == 'true',
            enable_layer3=os.getenv('ENABLE_VALIDATION_LAYER3', 'false').lower() == 'true',
            max_retries=int(os.getenv('VALIDATION_MAX_RETRIES', '3'))
        )
```

**Point B: Strategy Generation** (Line 217-316)
```python
def execute_iteration(self, iteration_num: int) -> IterationRecord:
    # ... existing code ...

    # Generate strategy YAML
    strategy_yaml = strategy.generate(context)

    # NEW: Validate before execution
    validation_result = self.validation_gateway.validate_strategy(
        strategy_yaml=strategy_yaml,
        llm_generate_func=lambda prompt: strategy.generate(prompt)
    )

    # Record validation metadata
    self._record_validation_metrics(validation_result)

    if not validation_result.success:
        # Validation failed - return error record
        return IterationRecord(
            iteration_num=iteration_num,
            success=False,
            error=validation_result.error_summary,
            validation_errors=validation_result.errors,
            retry_count=validation_result.retry_count
        )

    # Validation passed - proceed with execution
    execution_result = self._execute_strategy(
        validated_config=validation_result.config,
        ...
    )
```

### 5. Circuit Breaker Pattern

**Location**: `src/validation/circuit_breaker.py` (NEW)

**Responsibility**: Detect and prevent repeated identical errors

**Interface**:
```python
class CircuitBreaker:
    """
    Detect repeated identical errors to prevent API waste.

    Tracks error signatures (hash of error messages) and triggers
    circuit breaker after N consecutive identical errors.
    """

    def __init__(self, threshold: int = 2):
        """
        Initialize circuit breaker.

        Args:
            threshold: Number of identical errors before triggering
        """
        self.threshold = threshold
        self.error_signatures: Dict[str, int] = {}

    def record_error(self, errors: List[ValidationError]) -> bool:
        """
        Record error and check if circuit breaker should trigger.

        Args:
            errors: List of validation errors

        Returns:
            True if circuit breaker triggered, False otherwise
        """
        # Generate error signature (hash of error messages)
        signature = self._generate_signature(errors)

        # Increment counter for this signature
        self.error_signatures[signature] = self.error_signatures.get(signature, 0) + 1

        # Check threshold
        return self.error_signatures[signature] >= self.threshold

    def _generate_signature(self, errors: List[ValidationError]) -> str:
        """Generate unique signature for error set."""
        error_messages = [e.message for e in errors]
        return hashlib.md5("|".join(sorted(error_messages)).encode()).hexdigest()

    def reset(self):
        """Reset circuit breaker state."""
        self.error_signatures.clear()
```

## Data Models

### ValidationError (Enhanced)

**Location**: `src/execution/schema_validator.py` (existing, no changes needed)

**Structure** (already defined):
```python
@dataclass
class ValidationError:
    severity: ValidationSeverity  # ERROR, WARNING, INFO
    message: str
    field_path: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
```

### FieldError (Enhanced)

**Location**: `src/validation/validation_result.py` (existing, no changes needed)

**Structure** (already defined):
```python
@dataclass
class FieldError:
    line: int
    column: int
    field_name: str
    error_type: str
    message: str
    suggestion: Optional[str] = None
```

### IterationRecord (Enhanced)

**Location**: `src/learning/iteration_executor.py` (existing, needs modification)

**New Fields**:
```python
@dataclass
class IterationRecord:
    # ... existing fields ...

    # NEW: Validation metadata
    validation_passed: bool = True
    validation_errors: List[str] = field(default_factory=list)
    retry_count: int = 0
    circuit_breaker_triggered: bool = False
```

### Metrics Data Models

**Location**: `src/monitoring/validation_metrics.py` (NEW)

```python
@dataclass
class ValidationMetrics:
    """
    Real-time validation metrics for monitoring dashboard.
    """

    # Primary metrics
    field_error_rate: float  # 0.0-1.0
    llm_success_rate: float  # 0.0-1.0
    validation_latency_ms: float  # milliseconds

    # Secondary metrics
    total_validations: int
    successful_validations: int
    failed_validations: int
    retry_count_avg: float
    circuit_breaker_triggers: int

    # Layer metrics
    layer1_enabled_pct: float
    layer2_enabled_pct: float
    layer3_enabled_pct: float

    # Cost metrics
    api_cost_ratio: float  # 1.0 = baseline, >1.0 = increase
    retry_api_calls: int

    # Timestamps
    timestamp: datetime
    window_start: datetime
    window_end: datetime
```

## Error Handling

### Error Handling Strategy

**Three-Layer Defense**:
1. **Prevention** (Layer 1): Field suggestions reduce errors before generation
2. **Detection** (Layers 2-3): Validation catches errors before execution
3. **Recovery** (ErrorFeedbackLoop): Retry with feedback to fix errors

### Error Flow Diagram

```
LLM Generates Strategy YAML
         │
         ▼
    Parse YAML
         │
         ├──[YAML Parse Error]──────────────────┐
         │                                       │
         ▼                                       │
  Layer 3: Schema Validation                    │
         │                                       │
         ├──[Schema Error]──────────────────────┤
         │                                       │
         ▼                                       ▼
  Generate Python Code                   ErrorFeedbackLoop
         │                                  (max 3 retries)
         ▼                                       │
  Layer 2: Field Validation                     │
         │                                       │
         ├──[Field Error]───────────────────────┤
         │                                       │
         ▼                                       │
  Execute Strategy                              │
         │                                       │
         ▼                                       │
    SUCCESS                              Circuit Breaker
                                              Check
                                                │
                                                ├─[Same Error 2x]─> STOP
                                                │
                                                └─[Different Error]─> Retry
```

### Error Types and Handling

| Error Type | Layer | Handling Strategy | Recovery |
|------------|-------|-------------------|----------|
| YAML Parse Error | Pre-Layer 3 | Create synthetic ValidationError | Retry with syntax guidance |
| Schema Validation Error | Layer 3 | Return structured errors | Retry with schema requirements |
| Field Name Error | Layer 2 | AST-based detection + suggestion | Retry with COMMON_CORRECTIONS |
| Type Mismatch | Layer 3 | Type validation error | Retry with type requirements |
| Identical Error (2x) | Circuit Breaker | Stop retry loop | Return failure, log for analysis |
| Unexpected Exception | All layers | Catch-all handler | Return failure, full error logged |

### Error Message Format

**Schema Validation Error Example**:
```
=== ERRORS (2) ===

1. Missing required key: 'type'
   Field: <root>
   Suggestion: Add 'type' field with value 'factor_graph', 'llm_generated', or 'hybrid'

2. Invalid field name: 'price:成交量'
   Field: fields[0].canonical_name
   Line: 5
   Suggestion: Did you mean 'price:成交金額'? (成交量 → 成交金額)
```

**Field Validation Error Example**:
```
Line 15:10 - invalid_field: Invalid field name: 'price:成交量'
(Did you mean 'price:成交金額'?)
```

### Fallback Behavior

**Feature Flag Failure** (e.g., env service down):
- Default: ALL validation disabled (fail-safe)
- System continues with 0% validation (backward compatible)
- Alert triggered for ops team

**Validation Service Timeout**:
- Timeout budget: 10ms per layer
- On timeout: Skip that layer, log warning, continue
- Alert if timeout rate >5%

**Critical Failure** (e.g., validation gateway crash):
- Catch all exceptions in iteration_executor
- Return IterationRecord with success=False
- Log full stack trace for debugging
- Do NOT crash entire iteration loop

## Testing Strategy

### TDD Methodology

**RED-GREEN-REFACTOR Cycle**:

1. **RED**: Write failing test
2. **GREEN**: Write minimal code to pass test
3. **REFACTOR**: Improve code while keeping tests green

### Test Pyramid

```
          ┌─────────────────┐
          │  E2E Tests (5%) │  Full workflow integration
          │  - 5 scenarios  │
          └─────────────────┘
        ┌───────────────────────┐
        │ Integration Tests (20%)│  Multi-component interaction
        │ - 15 test cases        │
        └───────────────────────┘
    ┌─────────────────────────────────┐
    │     Unit Tests (75%)              │  Individual component behavior
    │     - Layer 1: 10 tests           │
    │     - Layer 2: 15 tests           │
    │     - Layer 3: 10 tests           │
    │     - Gateway: 20 tests           │
    │     - Circuit Breaker: 8 tests    │
    └─────────────────────────────────┘
```

### Week-by-Week Test Plan

**Week 1: Layer 1 Tests**
```python
# test_layer1_integration.py

class TestDataFieldManifestIntegration:
    def test_field_suggestions_injected_into_prompt(self):
        """RED: Field suggestions not in prompt"""
        # GREEN: Implement inject_field_suggestions()
        # REFACTOR: Extract suggestion formatting

    def test_common_corrections_appear_in_prompt(self):
        """RED: COMMON_CORRECTIONS not visible"""
        # GREEN: Add COMMON_CORRECTIONS to prompt

    def test_layer1_can_be_disabled_via_flag(self):
        """RED: Feature flag not working"""
        # GREEN: Check ENABLE_VALIDATION_LAYER1

    def test_layer1_performance_under_1_microsecond(self):
        """RED: Performance not measured"""
        # GREEN: Add timing instrumentation
```

**Week 2: Layer 2 + ErrorFeedbackLoop Tests**
```python
# test_layer2_integration.py

class TestFieldValidatorIntegration:
    def test_invalid_field_detected_before_execution(self):
        """RED: Invalid field not caught"""
        # GREEN: Integrate FieldValidator

    def test_ast_validation_provides_line_numbers(self):
        """RED: Line numbers not in errors"""
        # GREEN: Pass through FieldError.line

    def test_suggestions_included_in_validation_errors(self):
        """RED: Suggestions missing"""
        # GREEN: Include FieldError.suggestion

# test_error_feedback_loop.py

class TestErrorFeedbackLoopIntegration:
    def test_retry_on_validation_error(self):
        """RED: No retry happens"""
        # GREEN: Call error_loop.validate_and_retry()

    def test_max_retries_limit_enforced(self):
        """RED: Retry loop doesn't stop"""
        # GREEN: Check attempt_number <= max_retries

    def test_error_history_tracked_across_retries(self):
        """RED: Error history not recorded"""
        # GREEN: Append to error_history list
```

**Week 3: Layer 3 + Circuit Breaker Tests**
```python
# test_layer3_integration.py

class TestSchemaValidatorIntegration:
    def test_yaml_structure_validated_before_parsing(self):
        """RED: Schema errors not caught"""
        # GREEN: Call schema_validator.validate()

    def test_circuit_breaker_triggers_on_identical_errors(self):
        """RED: Same error retried indefinitely"""
        # GREEN: Implement CircuitBreaker.record_error()

    def test_circuit_breaker_allows_different_errors(self):
        """RED: Different errors trigger circuit breaker"""
        # GREEN: Use error signature hashing
```

**Week 4: Production Tests**
```python
# test_validation_metadata.py

class TestBacktestResultMetadata:
    def test_validation_passed_field_added(self):
        """RED: validation_passed field missing"""
        # GREEN: Add field to BacktestResult

    def test_validation_errors_populated_on_failure(self):
        """RED: Errors not in result"""
        # GREEN: Set validation_errors from ValidationResult
```

### Integration Test Scenarios

**Scenario 1: End-to-End Success Flow**
```python
def test_e2e_valid_strategy_all_layers_enabled():
    """
    Test complete workflow with valid strategy and all validation layers.

    Given: Valid strategy YAML
    When: All 3 layers enabled
    Then: Validation passes on first attempt, execution succeeds
    """
    # Setup
    config = create_valid_strategy_config()
    executor = IterationExecutor(
        enable_layer1=True,
        enable_layer2=True,
        enable_layer3=True
    )

    # Execute
    result = executor.execute_iteration(iteration_num=1)

    # Assert
    assert result.success == True
    assert result.validation_passed == True
    assert result.retry_count == 0
    assert result.sharpe_ratio is not None
```

**Scenario 2: Retry Success Flow**
```python
def test_e2e_invalid_yaml_retries_and_succeeds():
    """
    Test ErrorFeedbackLoop with invalid YAML that succeeds on retry.

    Given: Invalid YAML (missing 'type' field)
    When: ErrorFeedbackLoop retries with feedback
    Then: Second attempt succeeds, retry_count=1
    """
    # Setup with mock LLM that fixes error on retry
    mock_llm = MockLLMWithRetryFix(
        first_attempt='invalid_yaml',
        second_attempt='valid_yaml'
    )

    # Execute
    result = executor.execute_iteration(...)

    # Assert
    assert result.success == True
    assert result.retry_count == 1
    assert 'Missing required key' in result.error_history[0]
```

**Scenario 3: Circuit Breaker Activation**
```python
def test_e2e_circuit_breaker_stops_repeated_errors():
    """
    Test circuit breaker prevents infinite retry on same error.

    Given: LLM generates same error repeatedly
    When: Circuit breaker threshold reached (2 identical errors)
    Then: Retry stops, circuit_breaker_triggered=True
    """
    # Setup with mock LLM that never fixes error
    mock_llm = MockLLMStuckOnError(error_type='invalid_field')

    # Execute
    result = executor.execute_iteration(...)

    # Assert
    assert result.success == False
    assert result.circuit_breaker_triggered == True
    assert result.retry_count <= 2  # Stopped early
```

**Scenario 4: Performance Budget**
```python
def test_e2e_validation_completes_within_10ms():
    """
    Test all validation layers meet <10ms performance budget.

    Given: Valid strategy
    When: All 3 layers enabled
    Then: Total validation time <10ms
    """
    # Execute with timing
    start = time.perf_counter()
    result = executor.execute_iteration(...)
    validation_time_ms = (time.perf_counter() - start) * 1000

    # Assert
    assert validation_time_ms < 10.0
    assert result.success == True
```

**Scenario 5: Rollback Safety**
```python
def test_e2e_all_flags_disabled_maintains_baseline():
    """
    Test backward compatibility with all validation disabled.

    Given: All feature flags disabled
    When: Execute iteration
    Then: Works exactly as before integration (0% validation)
    """
    # Setup with all validation disabled
    executor = IterationExecutor(
        enable_layer1=False,
        enable_layer2=False,
        enable_layer3=False
    )

    # Execute
    result = executor.execute_iteration(...)

    # Assert - should behave like pre-integration
    assert result.validation_passed == True  # Default True
    assert len(result.validation_errors) == 0
    assert result.retry_count == 0
```

### Performance Testing

**Latency Benchmarks**:
```python
def test_layer1_latency_under_1_microsecond():
    """Layer 1 must be <1μs (already validated)."""
    times = [measure_layer1() for _ in range(1000)]
    assert np.percentile(times, 99) < 0.001  # 99th percentile <1μs

def test_layer2_latency_under_5ms():
    """Layer 2 budget: <5ms for AST parsing."""
    times = [measure_layer2(strategy_code) for _ in range(100)]
    assert np.percentile(times, 99) < 5.0

def test_layer3_latency_under_5ms():
    """Layer 3 budget: <5ms for YAML validation."""
    times = [measure_layer3(yaml_dict) for _ in range(100)]
    assert np.percentile(times, 99) < 5.0

def test_total_validation_latency_under_10ms():
    """Total budget: <10ms for all layers combined."""
    times = [measure_full_validation() for _ in range(100)]
    assert np.percentile(times, 95) < 10.0
```

### Regression Testing

**Test Suite**: All existing 273 test files MUST pass with validation disabled

```bash
# Regression test command
ENABLE_VALIDATION_LAYER1=false \
ENABLE_VALIDATION_LAYER2=false \
ENABLE_VALIDATION_LAYER3=false \
pytest tests/ -v

# Expected: 273/273 PASS (100%)
```

### A/B Testing Strategy

**Rollout Stages**:
- **10% Rollout**: Random 10% of iterations use validation
- **50% Rollout**: Random 50% of iterations use validation
- **100% Rollout**: All iterations use validation

**Metrics Comparison**:
```python
# A/B test metrics collection
class ABTestMetrics:
    control_group: List[IterationRecord]  # No validation
    treatment_group: List[IterationRecord]  # With validation

    def calculate_improvement(self) -> Dict[str, float]:
        return {
            'field_error_rate_reduction': ...,
            'llm_success_rate_increase': ...,
            'api_cost_ratio': ...,
        }
```

---

## Implementation Phases

### Week 1: Foundation (Layer 1)

**Files to Create**:
- `src/validation/gateway.py` (ValidationGateway skeleton)
- `src/validation/result.py` (ValidationResult dataclass)
- `tests/validation/test_layer1_integration.py`

**Files to Modify**:
- `src/learning/iteration_executor.py` (add Layer 1 integration)
- `tests/e2e/conftest.py` (fix hardcoded API keys)

**TDD Cycle**:
1. RED: Write test_field_suggestions_injected_into_prompt (FAIL)
2. GREEN: Implement inject_field_suggestions() (PASS)
3. REFACTOR: Extract suggestion formatting logic

### Week 2: Code Validation (Layer 2 + Retry)

**Files to Create**:
- `src/validation/circuit_breaker.py` (CircuitBreaker class)
- `tests/validation/test_error_feedback_loop.py`
- `tests/validation/test_layer2_integration.py`

**Files to Modify**:
- `src/validation/gateway.py` (add Layer 2 + ErrorFeedbackLoop)
- `src/learning/iteration_executor.py` (integrate FieldValidator)

**TDD Cycle**:
1. RED: Write test_invalid_field_detected_before_execution (FAIL)
2. GREEN: Call FieldValidator in gateway (PASS)
3. REFACTOR: Extract error formatting

### Week 3: Schema Validation (Layer 3 + Circuit Breaker)

**Files to Create**:
- `src/monitoring/validation_metrics.py` (ValidationMetrics)
- `tests/validation/test_circuit_breaker.py`
- `tests/validation/test_layer3_integration.py`

**Files to Modify**:
- `src/validation/gateway.py` (add Layer 3 + CircuitBreaker)
- `src/learning/iteration_executor.py` (complete integration)

**TDD Cycle**:
1. RED: Write test_circuit_breaker_triggers_on_identical_errors (FAIL)
2. GREEN: Implement CircuitBreaker.record_error() (PASS)
3. REFACTOR: Optimize error signature hashing

### Week 4: Production Polish

**Files to Create**:
- `docs/VALIDATION_RUNBOOK.md` (operations guide)
- `tests/e2e/test_validation_complete_workflow.py`

**Files to Modify**:
- `src/execution/backtest_result.py` (add validation metadata)
- `src/learning/iteration_executor.py` (add metrics recording)

**TDD Cycle**:
1. RED: Write test_validation_metadata_in_backtest_result (FAIL)
2. GREEN: Add validation_passed field (PASS)
3. REFACTOR: Clean up metadata population logic

---

## Security Considerations

**Immediate Fix (Day 1)**:
- Remove hardcoded API key in `tests/e2e/conftest.py:77`
- Replace with `get_test_api_key()` environment-based function

**Error Message Sanitization**:
- Strip file paths from error messages before logging
- Never expose internal implementation details
- Sanitize YAML content in error logs (remove sensitive data)

**Feature Flag Security**:
- Fail-safe: Default to validation disabled if flags unavailable
- No sensitive data in feature flag values
- Environment-based configuration only (no hardcoded flags)

---

This design document provides the complete technical blueprint for TDD-based integration of the validation infrastructure. All components, interfaces, data models, error handling strategies, and testing approaches are defined to enable systematic Week-by-Week implementation.
