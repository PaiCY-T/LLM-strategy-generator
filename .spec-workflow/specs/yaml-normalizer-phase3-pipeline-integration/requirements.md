# Requirements Document

**STATUS: ON-HOLD** - Phase 2 must complete successfully before Phase 3 work begins. This spec will be activated after Phase 2 achieves 85-87% validation success rate target.

## Introduction

This specification bridges the final gap from Phase 2 (85-87% E2E success rate) to the **90%+ target** by integrating **intelligent retry logic** and **error-aware prompting** into the autonomous strategy generation pipeline.

**Current State (Post-Phase 2)**:
- ✅ Integration tests: 100% (14/14 known fixtures)
- ✅ E2E tests: 85-87% (real LLM outputs)
- ✅ Normalizer: Complete with name transformation
- ✅ Validation: Pydantic-based with clear error messages

**Remaining Gap**:
- **10-15% of E2E iterations still fail** validation
- These failures require LLM intervention, not just normalization

**Phase 3 Strategy: "Error-Guided Retry with Feedback Loop"**
- **Intelligent Retry**: When validation fails, provide errors to LLM for correction
- **Limited Attempts**: Max 2-3 retries per generation (avoid infinite loops)
- **Pipeline Integration**: Seamless integration into `autonomous_loop.py`
- **Monitoring**: Track retry patterns, success rates, failure modes

**Evidence-Based Approach**:
- Phase 1 analysis: Normalization gaps (fixed in Phase 2)
- Phase 2 projections: 85-87% with normalizer + Pydantic
- Phase 3 target: Additional 3-5% gain through retry logic → 90%+

## Alignment with Product Vision

**避免過度工程化 (Avoid Over-Engineering)**:
- Simple retry loop (2-3 attempts max)
- Reuse existing LLM prompt infrastructure
- No complex state machines or orchestration

**從數據中學習 (Learn from Data)**:
- Track which error types benefit from retry
- Monitor retry success rates
- Identify patterns requiring prompt engineering

**漸進式改進 (Incremental Improvement)**:
- Phase 1: 71.4% → Normalizer MVP
- Phase 2: 85-87% → Complete normalization + Pydantic
- Phase 3: 90%+ → Retry logic (THIS SPEC)
- Future: 95%+ → Advanced prompt engineering (if needed)

**自動化優先 (Automation First)**:
- Automatic retry on validation failure
- No manual intervention required
- Self-healing strategy generation

**Product Impact**:
- **E2E Success Rate**: 85-87% → 90%+ (+3-5%)
- **Reduced Manual Fixes**: Fewer invalid strategies reaching backtest
- **Faster Iteration**: Automatic correction vs. debugging
- **Path to 95%+**: Foundation for future enhancements

## Requirements

### Requirement 1: Validation Retry Orchestrator

**User Story:** As the autonomous loop, I want to retry failed validations with LLM feedback, so that temporary generation issues don't cause strategy rejection.

#### Acceptance Criteria

1. WHEN strategy generation fails validation THEN orchestrator SHALL retry with error feedback
   - **Max Attempts**: 3 total (1 initial + 2 retries)
   - **Error Feedback**: Include full validation error messages in retry prompt
   - **Delay**: Optional configurable delay between retries (default: 0s)

2. WHEN retry succeeds THEN orchestrator SHALL return validated strategy
   - **Log Success**: INFO level with retry count
   - **Metric**: Track `retry_success_count` and `retry_attempt_number`
   - **Return**: Validated Pydantic Strategy instance

3. WHEN all retries exhausted THEN orchestrator SHALL raise ValidationExhaustedError
   - **Log Failure**: WARNING level with all error messages
   - **Metric**: Track `retry_exhausted_count`
   - **Error Details**: Include all validation errors from all attempts

4. WHEN retry loop detects identical errors THEN orchestrator SHALL abort early
   - **Pattern**: If errors identical for 2 consecutive attempts, stop
   - **Reason**: LLM not learning from feedback (avoid wasted API calls)
   - **Log**: INFO level "Identical errors detected, aborting retry"

5. IF configuration disables retries THEN orchestrator SHALL fail immediately
   - **Config**: `retry_enabled: false` in `config/learning_system.yaml`
   - **Behavior**: Single attempt only (Phase 2 behavior)
   - **Use Case**: Testing, debugging, or cost control

### Requirement 2: Error-Aware Prompt Enhancement

**User Story:** As the LLM, I want clear, actionable error feedback in retry prompts, so that I can correct specific validation issues rather than guessing.

#### Acceptance Criteria

1. WHEN generating retry prompt THEN it SHALL include validation errors
   - **Format**: Structured error list with field paths
   - **Example**:
     ```
     Previous attempt failed validation with errors:
     1. indicators.technical_indicators.0.name: Contains invalid characters (pattern: ^[a-z_][a-z0-9_]*$)
     2. indicators.technical_indicators.1.period: Input should be less than or equal to 250 (got: 500)
     ```
   - **Placement**: After strategy description, before YAML generation instruction

2. WHEN errors are field-specific THEN prompt SHALL highlight exact locations
   - **Field Path**: Full path from Pydantic errors (e.g., `entry_conditions.threshold_rules.0.operator`)
   - **Expected vs Actual**: Show what was received vs what's required
   - **Pattern**: Include regex patterns for name/format errors

3. WHEN errors are structural THEN prompt SHALL explain schema requirements
   - **Example**: "indicators must be an object with technical_indicators array, not a flat array"
   - **Schema Hints**: Reference schema structure for complex types
   - **Corrective Guidance**: "Please restructure as: indicators: { technical_indicators: [...] }"

4. WHEN multiple errors exist THEN prompt SHALL prioritize critical errors first
   - **Order**: Required fields > type errors > pattern errors > range errors
   - **Limit**: Show top 5 errors max (avoid overwhelming LLM)
   - **Summary**: "Showing 5 of 12 errors (most critical)"

5. IF retry attempt number > 1 THEN prompt SHALL emphasize previous failure
   - **Message**: "This is retry attempt 2/3. Previous attempt also failed. Please carefully review errors."
   - **Tone**: Firm but constructive
   - **Reminder**: Include original strategy requirements

### Requirement 3: Pipeline Integration

**User Story:** As a developer, I want retry logic seamlessly integrated into the autonomous loop, so that existing workflows continue working with enhanced reliability.

#### Acceptance Criteria

1. WHEN autonomous loop generates strategy THEN it SHALL use ValidationRetryOrchestrator
   - **Integration Point**: Replace direct `yaml_schema_validator.validate()` calls
   - **Backward Compatible**: Existing code paths unchanged (feature flag)
   - **Interface**:
     ```python
     strategy = orchestrator.generate_and_validate(
         prompt_template=template,
         llm_client=llm,
         max_retries=3
     )
     ```

2. WHEN validation succeeds on first try THEN no retry overhead occurs
   - **Fast Path**: Skip retry logic if validation passes
   - **Performance**: Same latency as Phase 2 for successful cases
   - **Metric**: Track `first_attempt_success_rate`

3. WHEN retry logic is invoked THEN metrics SHALL be recorded
   - **Metrics**:
     - `validation_retry_attempts` (histogram: 0, 1, 2, 3)
     - `validation_final_success` (bool)
     - `validation_error_types` (counter by error category)
   - **Export**: Prometheus format + JSON logs
   - **Granularity**: Per-iteration tracking

4. WHEN configuration is loaded THEN retry settings SHALL be configurable
   - **Config File**: `config/learning_system.yaml`
   - **Settings**:
     ```yaml
     yaml_validation:
       retry_enabled: true
       max_retries: 3
       retry_delay_seconds: 0
       abort_on_identical_errors: true
     ```
   - **Validation**: Schema validation for config values

5. IF integration breaks existing functionality THEN it SHALL be caught by tests
   - **Test Coverage**: Existing autonomous loop tests must pass
   - **Regression Tests**: Verify Phase 1 & Phase 2 behavior unchanged
   - **Integration Tests**: New test for retry flow

### Requirement 4: Error Pattern Analysis and Monitoring

**User Story:** As a system maintainer, I want visibility into retry patterns and failure modes, so that I can identify opportunities for prompt engineering or schema refinement.

#### Acceptance Criteria

1. WHEN validation fails THEN error SHALL be categorized by type
   - **Categories**:
     - `pattern_violation`: Name/format doesn't match regex
     - `type_mismatch`: Wrong data type
     - `range_violation`: Value outside allowed range
     - `required_missing`: Missing required field
     - `structural_error`: Schema structure mismatch
     - `semantic_error`: Invalid combination (e.g., conflicting rules)
   - **Tracking**: Counter metrics per category
   - **Export**: Prometheus + JSON logs

2. WHEN retry succeeds THEN recovery pattern SHALL be logged
   - **Log Level**: INFO
   - **Message**: "Retry #{attempt} succeeded after errors: [{error_types}]"
   - **Metric**: `retry_recovery_by_error_type` (counter)
   - **Analysis**: Which error types respond well to retry?

3. WHEN retry fails exhaustively THEN failure SHALL be documented
   - **Log Level**: WARNING
   - **Message**: Include original prompt, all errors, retry count
   - **Storage**: Optional JSON file export for analysis
   - **Format**:
     ```json
     {
       "iteration": 123,
       "original_prompt": "...",
       "attempts": [
         {"attempt": 1, "errors": [...]},
         {"attempt": 2, "errors": [...]},
         {"attempt": 3, "errors": [...]}
       ],
       "final_status": "exhausted"
     }
     ```

4. WHEN error patterns are analyzed THEN insights SHALL guide improvements
   - **Dashboard**: Grafana panels for retry metrics
   - **Reports**: Weekly summary of top error types
   - **Action Items**: Feed into prompt engineering backlog
   - **Example**: "90% of pattern violations in indicator names → improve prompt examples"

5. IF retry success rate < 50% THEN alert SHALL be raised
   - **Threshold**: Configurable (default: 50%)
   - **Alert**: WARNING log + optional webhook/email
   - **Message**: "Retry success rate below threshold: {rate}% < 50%"
   - **Action**: Review recent failures, adjust prompts/schema

### Requirement 5: End-to-End Testing and Validation

**User Story:** As a QA engineer, I want comprehensive testing to verify Phase 3 achieves 90%+ success rate, confirming retry logic provides the expected improvement.

#### Acceptance Criteria

1. WHEN E2E tests run with retry enabled THEN success rate SHALL be ≥90%
   - **Test Script**: `python scripts/test_yaml_validation_phase3.py --iterations 100`
   - **Real LLM**: Gemini 2.5 Flash or Grok
   - **Measurement**: Count successful validations (including retries) / total iterations
   - **Statistical Significance**: 100 iterations provides confidence

2. WHEN comparing Phase 2 vs Phase 3 THEN improvement SHALL be measurable
   - **Baseline (Phase 2)**: 85-87% success rate (no retries)
   - **Phase 3 (with retries)**: ≥90% success rate
   - **Improvement**: ≥3% gain
   - **Verification**: Statistical test confirms significance (chi-square or binomial)

3. WHEN retry metrics are analyzed THEN patterns SHALL be identified
   - **Retry Utilization**: % of iterations requiring retry
   - **Retry Effectiveness**: % of retries that succeed
   - **Error Distribution**: Which error types most common
   - **Iteration Cost**: Average LLM calls per successful strategy

4. IF success rate is < 90% THEN analysis SHALL identify root causes
   - **Categorize**: Exhaustive failures by error type
   - **Prioritize**: Top 3 failure patterns
   - **Document**: Feed into future enhancement planning
   - **Decision**: Determine if prompt engineering or schema changes needed

5. WHEN all tests pass THEN Phase 3 SHALL be production-ready
   - **Integration Tests**: Retry logic works correctly
   - **Unit Tests**: Individual components tested
   - **E2E Tests**: ≥90% success rate achieved
   - **Backward Compatibility**: Phase 1 & Phase 2 functionality preserved
   - **Performance**: No significant latency increase for successful first attempts

## Non-Functional Requirements

### Code Architecture and Modularity

**Single Responsibility Principle**:
- `src/validation/retry_orchestrator.py`: Retry logic orchestration (NEW)
- `src/validation/error_aware_prompt.py`: Error feedback formatting (NEW)
- `src/generators/yaml_schema_validator.py`: Validation (unchanged from Phase 2)
- `artifacts/working/modules/autonomous_loop.py`: Integration point (MODIFY)

**Modular Design**:
- Retry orchestrator is stateless: `generate_and_validate(prompt, llm, max_retries)`
- Error formatter is pure function: `format_errors_for_prompt(errors: List[str]) -> str`
- Each component independently testable

**Dependency Management**:
- **No new external dependencies**
- Reuse existing LLM client infrastructure
- Leverage Phase 2 normalizer + validator

**Clear Interfaces**:
```python
# Retry Orchestrator
class ValidationRetryOrchestrator:
    def generate_and_validate(
        self,
        prompt_template: str,
        llm_client: LLMClient,
        max_retries: int = 3
    ) -> Strategy:
        """Generate strategy with retry on validation failure."""

# Error Formatter
def format_errors_for_prompt(
    errors: List[str],
    attempt_number: int
) -> str:
    """Format validation errors for LLM retry prompt."""
```

### Performance

**Retry Overhead**:
- **First Attempt Success** (85-87% of cases): 0ms overhead (fast path)
- **Single Retry** (~10-12% of cases): +1 LLM call (~2-3s)
- **Double Retry** (~1-2% of cases): +2 LLM calls (~4-6s)
- **Exhausted** (~1-3% of cases): +3 LLM calls (~6-9s)

**Average Impact**:
- Weighted average: 0.85 * 0s + 0.12 * 3s + 0.02 * 6s + 0.01 * 9s ≈ **0.57s per iteration**
- Acceptable for autonomous loop (iterations are minutes apart)

**Cost Impact**:
- Phase 2: 1 LLM call per iteration
- Phase 3: ~1.15 LLM calls per iteration (15% retry rate)
- **Marginal increase**: 15% more LLM API costs
- **ROI**: 3-5% success rate improvement worth 15% cost increase

### Security

**LLM Prompt Injection Prevention**:
- **Input Sanitization**: Escape special characters in error messages
- **Template Safety**: Use parameterized prompts (no string concatenation)
- **Validation**: Ensure error feedback doesn't contain executable code

**Data Integrity**:
- **Immutability**: Each retry attempt is independent (no state mutation)
- **Idempotency**: Same inputs produce same outputs
- **Audit Trail**: All attempts logged for debugging

### Reliability

**Error Handling**:
- **LLM Timeout**: Configurable timeout (default: 30s per call)
- **API Failures**: Exponential backoff for transient errors
- **Validation Errors**: Clear separation from LLM errors

**Fallback Strategies**:
- **Retry Exhausted**: Raise `ValidationExhaustedError` (caller decides: skip or abort)
- **Configuration Error**: Fail fast on invalid config (don't start iteration)
- **LLM Unavailable**: Propagate error to autonomous loop (pauses iteration)

**Monitoring**:
- **Success Rate Tracking**: Real-time metrics via Prometheus
- **Error Rate Alerts**: Trigger if retry exhaustion rate > threshold
- **Cost Tracking**: Monitor LLM API call count per iteration

### Usability

**Developer Experience**:
- **Drop-in Integration**: Minimal changes to autonomous_loop.py
- **Clear Error Messages**: Actionable feedback for debugging
- **Testing**: Easy to simulate retry scenarios

**Configuration**:
- **Sensible Defaults**: Works out-of-box with `max_retries=3`
- **Tunable**: All thresholds configurable via YAML
- **Documented**: Config reference with examples

**Documentation**:
- **Integration Guide**: How to enable retry logic in autonomous loop
- **Troubleshooting**: Common retry failure patterns and solutions
- **Metrics Dashboard**: Grafana panels for monitoring

### Maintainability

**Code Quality**:
- **Type Hints**: All functions fully typed (mypy strict)
- **PEP 8 Compliance**: flake8 passing
- **Test Coverage**: >85% for retry_orchestrator.py, >80% for error_aware_prompt.py

**Configuration Management**:
- **YAML Config**: `config/learning_system.yaml` with schema validation
- **Environment Overrides**: Support env vars for CI/CD
- **Versioning**: Config changes tracked in git

**Future-Proofing**:
- **Extensible**: Easy to add new error categories
- **Pluggable**: Different retry strategies (linear, exponential backoff)
- **Migration Path**: Can evolve to more sophisticated retry logic if needed

---

## Success Metrics

| Metric | Phase 2 Baseline | Phase 3 Target | Measurement |
|--------|------------------|----------------|-------------|
| **E2E Success Rate** | 85-87% | **≥90%** | 100 LLM iterations |
| **First Attempt Success** | 85-87% | 85-87% (unchanged) | No regression |
| **Retry Utilization** | N/A | 10-15% | % iterations needing retry |
| **Retry Success Rate** | N/A | ≥50% | % retries that succeed |
| **Average LLM Calls/Iteration** | 1.0 | ~1.15 | Cost monitoring |
| **Retry Exhaustion Rate** | N/A | <3% | % iterations failing all retries |

---

**Document Version**: 1.0
**Created**: 2025-10-27
**Status**: Draft - Pending Approval
**Owner**: Personal Project (週/月交易系統)
**Dependencies**:
- Phase 1: YAML Normalizer MVP (completed)
- Phase 2: Complete Normalization + Pydantic (approved)
**Estimated Effort**: 5-6 hours
- Task 1: ValidationRetryOrchestrator - 2h
- Task 2: Error-Aware Prompt Formatting - 1h
- Task 3: Pipeline Integration - 1.5h
- Task 4: Testing and Validation (100 iterations) - 1.5h
