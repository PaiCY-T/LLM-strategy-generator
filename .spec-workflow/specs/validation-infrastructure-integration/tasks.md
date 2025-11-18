# Validation Infrastructure Integration - Task List

## Implementation Tasks

### Week 1: Foundation & Security (Day 1-5)

- [x] **1. Security Fix - Remove Hardcoded API Keys**
    - [x] 1.1. Fix hardcoded API key in tests/e2e/conftest.py:77
        - *Goal*: Eliminate security vulnerability and prevent credentials from being committed to repository
        - *Details*:
            - RED: Write test that fails if hardcoded API keys are detected in codebase
            - GREEN: Replace hardcoded key with environment variable loading (os.getenv("API_KEY"))
            - REFACTOR: Extract API key loading into a dedicated configuration module
            - Add .env.example file with placeholder values
            - Update documentation with environment variable setup instructions
        - *Requirements*: AC1.1, NFR-S1, NFR-S2
        - *Files*: tests/e2e/conftest.py
        - *Tests*: test_no_hardcoded_secrets.py (new)
        - *Estimated Time*: 2 hours

- [x] **2. Layer 1 Integration - DataFieldManifest in LLM Prompts**
    - [x] 2.1. Integrate DataFieldManifest into iteration_executor.py
        - *Goal*: Provide LLM with valid field names and common corrections before strategy generation
        - *Details*:
            - RED: Write test_field_suggestions_appear_in_prompt() - verify COMMON_CORRECTIONS in prompt
            - GREEN: Add inject_field_suggestions() method to IterationExecutor
            - GREEN: Call inject_field_suggestions() in _generate_prompt() method (line 217-316)
            - REFACTOR: Extract prompt formatting logic into separate helper functions
            - Ensure COMMON_CORRECTIONS (21 entries) are properly formatted in prompt
        - *Requirements*: AC1.2, AC1.3, NFR-P1 (Layer 1 <1μs)
        - *Files*: src/learning/iteration_executor.py
        - *Tests*: tests/learning/test_iteration_executor_layer1.py (new)
        - *Estimated Time*: 6 hours

    - [x] 2.2. Create Layer 1 feature flag system
        - *Goal*: Enable/disable Layer 1 validation independently for incremental rollout
        - *Details*:
            - RED: Write test_feature_flag_layer1_disabled() - verify Layer 1 skipped when flag=False
            - GREEN: Read ENABLE_VALIDATION_LAYER1 from environment variables
            - GREEN: Add conditional logic to skip field suggestion injection when disabled
            - REFACTOR: Create FeatureFlagManager class for centralized flag management
        - *Requirements*: AC1.4, NFR-R2 (fail-safe flags)
        - *Files*: src/learning/iteration_executor.py, src/config/feature_flags.py (new)
        - *Tests*: tests/config/test_feature_flags.py (new)
        - *Estimated Time*: 4 hours
        - **COMPLETED**: 2025-11-18 - FeatureFlagManager implemented with singleton pattern, 16/16 tests passing, 100% backward compatibility

    - [x] 2.3. Implement 10% rollout mechanism
        - *Goal*: Deploy Layer 1 to 10% of strategy generation requests with baseline metrics tracking
        - *Details*:
            - RED: Write test_rollout_percentage_respected() - verify 10% traffic gets validation
            - GREEN: Implement sampling logic based on strategy hash (deterministic 10% selection)
            - GREEN: Add metrics collection for baseline comparison (field_error_rate, llm_success_rate)
            - REFACTOR: Extract metrics collection into dedicated MetricsCollector class
        - *Requirements*: AC1.5, NFR-O1 (real-time metrics)
        - *Files*: src/learning/iteration_executor.py, src/metrics/collector.py (new)
        - *Tests*: tests/metrics/test_rollout.py (new)
        - *Estimated Time*: 5 hours

    - [x] 2.4. Validate regression testing passes
        - *Goal*: Ensure all 273 existing test files pass with Layer 1 integration
        - *Details*:
            - Run full test suite: pytest tests/
            - Identify and fix any failing tests
            - Verify backward compatibility with ENABLE_VALIDATION_LAYER1=False
            - Document any test modifications required
        - *Requirements*: AC1.6, NFR-C1 (backward compatibility)
        - *Files*: All existing test files
        - *Tests*: Entire test suite (273 files)
        - *Estimated Time*: 4 hours
        - **COMPLETED**: 2025-11-18 - Fixed 5 import issues, 276 test files collecting, backward compatibility verified

### Week 2: Code Validation & Retry (Day 6-10)

- [ ] **3. Layer 2 Integration - FieldValidator for Code Validation**
    - [x] 3.1. Create ValidationGateway orchestrator class
        - *Goal*: Central orchestrator for all validation layers with feature flag support
        - *Details*:
            - RED: Write test_validation_gateway_initialization() - verify component initialization
            - GREEN: Create ValidationGateway class in src/validation/gateway.py
            - GREEN: Initialize DataFieldManifest, FieldValidator, SchemaValidator based on flags
            - REFACTOR: Extract validator initialization into factory methods
        - *Requirements*: Design.Components.ValidationGateway
        - *Files*: src/validation/gateway.py (new)
        - *Tests*: tests/validation/test_gateway_init.py (new)
        - *Estimated Time*: 4 hours

    - [ ] 3.2. Integrate FieldValidator into strategy validation workflow
        - *Goal*: Detect invalid field usage in strategy code with AST-based validation
        - *Details*:
            - RED: Write test_invalid_field_detected() - verify AST validation catches invalid fields
            - GREEN: Add validate_strategy_code() method to ValidationGateway
            - GREEN: Call FieldValidator.validate_code() after YAML parsing but before execution
            - GREEN: Return structured FieldError objects with line/column information
            - REFACTOR: Optimize AST parsing for <5ms performance budget
        - *Requirements*: AC2.1, AC2.2, NFR-P1 (Layer 2 <5ms)
        - *Files*: src/validation/gateway.py, src/learning/iteration_executor.py
        - *Tests*: tests/validation/test_field_validator_integration.py (new)
        - *Estimated Time*: 6 hours

    - [ ] 3.3. Add Layer 2 feature flag
        - *Goal*: Enable/disable Layer 2 (FieldValidator) independently
        - *Details*:
            - RED: Write test_feature_flag_layer2_controls_validation()
            - GREEN: Add ENABLE_VALIDATION_LAYER2 environment variable support
            - GREEN: Conditional FieldValidator initialization in ValidationGateway
            - REFACTOR: Update FeatureFlagManager with Layer 2 controls
        - *Requirements*: AC2.3, AC-CC1 (independent layer control)
        - *Files*: src/validation/gateway.py, src/config/feature_flags.py
        - *Tests*: tests/config/test_feature_flags_layer2.py (new)
        - *Estimated Time*: 3 hours

- [ ] **4. ErrorFeedbackLoop Integration - Automatic Retry System**
    - [x] 4.1. Integrate ErrorFeedbackLoop into ValidationGateway
        - *Goal*: Automatically retry invalid LLM outputs with structured error feedback
        - *Details*:
            - RED: Write test_retry_on_validation_failure() - verify retry mechanism triggers
            - GREEN: Add ErrorFeedbackLoop to ValidationGateway initialization
            - GREEN: Call error_loop.validate_and_retry() in validate_strategy() method
            - GREEN: Pass llm_generate_func callback for retry operations
            - REFACTOR: Extract retry logic into separate RetryCoordinator class
        - *Requirements*: AC2.4, AC2.5, Design.Components.ValidationGateway.validate_strategy
        - *Files*: src/validation/gateway.py
        - *Tests*: tests/validation/test_error_feedback_integration.py (new)
        - *Estimated Time*: 5 hours

    - [ ] 4.2. Implement retry prompt generation
        - *Goal*: Feed validation errors back to LLM with actionable suggestions
        - *Details*:
            - RED: Write test_retry_prompt_contains_errors() - verify error details in prompt
            - GREEN: Use ErrorFeedbackLoop.generate_retry_prompt() to create structured prompts
            - GREEN: Include original YAML, validation errors, and suggestions in retry prompt
            - REFACTOR: Template-based retry prompt generation for consistency
        - *Requirements*: AC2.5, Design.ErrorHandling (retry flow)
        - *Files*: src/validation/gateway.py, src/prompts/error_feedback.py
        - *Tests*: tests/validation/test_retry_prompts.py (new)
        - *Estimated Time*: 4 hours

    - [ ] 4.3. Measure and validate field error rate reduction
        - *Goal*: Achieve field error rate <10% (from 73.26% baseline)
        - *Details*:
            - Run integration tests with Layer 1 + Layer 2 enabled
            - Collect field_error_rate metrics from 50+ test strategies
            - Analyze error patterns and adjust COMMON_CORRECTIONS if needed
            - Validate LLM success rate >50% (from 0% baseline)
        - *Requirements*: AC2.6, AC2.7, Success Metrics (Week 2 targets)
        - *Files*: tests/integration/test_error_rate_reduction.py (new)
        - *Tests*: Integration test suite with metrics validation
        - *Estimated Time*: 5 hours

    - [ ] 4.4. Deploy 50% rollout
        - *Goal*: Increase rollout to 50% of strategy generation requests
        - *Details*:
            - RED: Write test_rollout_50_percent() - verify 50% sampling
            - GREEN: Update rollout percentage from 10% to 50%
            - GREEN: Monitor metrics for performance degradation or quality issues
            - REFACTOR: Make rollout percentage configurable via environment variable
        - *Requirements*: AC2.8, Success Metrics (Week 2)
        - *Files*: src/metrics/collector.py, src/learning/iteration_executor.py
        - *Tests*: tests/metrics/test_rollout_50.py (new)
        - *Estimated Time*: 3 hours

### Week 3: Schema Validation & Performance (Day 11-15)

- [ ] **5. Layer 3 Integration - SchemaValidator for YAML Structure**
    - [x] 5.1. Integrate SchemaValidator into ValidationGateway
        - *Goal*: Validate YAML structure before parsing to catch schema errors early
        - *Details*:
            - RED: Write test_schema_validation_before_parsing() - verify YAML schema checks
            - GREEN: Add SchemaValidator initialization to ValidationGateway
            - GREEN: Call schema_validator.validate() after YAML parsing
            - GREEN: Return structured ValidationError objects for schema failures
            - REFACTOR: Optimize schema validation for <5ms performance budget
        - *Requirements*: AC3.1, NFR-P1 (Layer 3 <5ms)
        - *Files*: src/validation/gateway.py
        - *Tests*: tests/validation/test_schema_validator_integration.py (new)
        - *Estimated Time*: 5 hours

    - [ ] 5.2. Add Layer 3 feature flag
        - *Goal*: Enable/disable Layer 3 (SchemaValidator) independently
        - *Details*:
            - RED: Write test_feature_flag_layer3_controls_schema_validation()
            - GREEN: Add ENABLE_VALIDATION_LAYER3 environment variable support
            - GREEN: Conditional SchemaValidator initialization in ValidationGateway
            - REFACTOR: Update FeatureFlagManager with Layer 3 controls
        - *Requirements*: AC3.2, AC-CC1 (independent layer control)
        - *Files*: src/validation/gateway.py, src/config/feature_flags.py
        - *Tests*: tests/config/test_feature_flags_layer3.py (new)
        - *Estimated Time*: 3 hours

    - [ ] 5.3. Validate all YAML structure errors are caught
        - *Goal*: Ensure 100% of malformed YAML is caught before parsing
        - *Details*:
            - Create test suite with 20+ malformed YAML examples
            - Verify SchemaValidator catches all structure errors
            - Validate error messages are actionable and include suggestions
            - Test edge cases: missing keys, invalid types, nested structure errors
        - *Requirements*: AC3.3, NFR-Q4 (90%+ actionable error messages)
        - *Files*: tests/validation/test_schema_edge_cases.py (new)
        - *Tests*: Comprehensive YAML error test suite
        - *Estimated Time*: 4 hours

- [ ] **6. Circuit Breaker Implementation - Prevent API Waste**
    - [x] 6.1. Implement error signature tracking
        - *Goal*: Detect repeated identical errors to prevent API waste
        - *Details*:
            - RED: Write test_circuit_breaker_detects_repeated_errors()
            - GREEN: Add error_signatures Dict[str, int] to ValidationGateway
            - GREEN: Hash error messages to create error signatures
            - GREEN: Track error signature frequency across retry attempts
            - REFACTOR: Extract error signature hashing into utility function
        - *Requirements*: AC3.4, AC3.5, NFR-R3 (prevent >10 identical retries)
        - *Files*: src/validation/gateway.py, src/validation/circuit_breaker.py (new)
        - *Tests*: tests/validation/test_circuit_breaker.py (new)
        - *Estimated Time*: 5 hours

    - [ ] 6.2. Implement circuit breaker activation logic
        - *Goal*: Auto-disable retry loop when same error occurs multiple times
        - *Details*:
            - RED: Write test_circuit_breaker_triggers_on_threshold()
            - GREEN: Set circuit_breaker_threshold = 2 (same error twice triggers break)
            - GREEN: Check error_signatures before each retry attempt
            - GREEN: Set circuit_breaker_triggered flag and exit retry loop
            - REFACTOR: Make threshold configurable via environment variable
        - *Requirements*: AC3.5, NFR-R3, AC-CC3 (cost monitoring)
        - *Files*: src/validation/gateway.py, src/validation/circuit_breaker.py
        - *Tests*: tests/validation/test_circuit_breaker_activation.py (new)
        - *Estimated Time*: 4 hours

    - [ ] 6.3. Achieve 0% field error rate
        - *Goal*: Validate field error rate reduced to 0% with all 3 layers enabled
        - *Details*:
            - Run integration tests with all validation layers enabled
            - Collect field_error_rate metrics from 100+ test strategies
            - Validate 0% field errors in LLM-generated strategies
            - Document any edge cases that still produce errors
        - *Requirements*: AC3.6, Success Metrics (Week 3: 0% field error rate)
        - *Files*: tests/integration/test_zero_field_errors.py (new)
        - *Tests*: Comprehensive integration test suite
        - *Estimated Time*: 4 hours

    - [ ] 6.4. Validate total validation latency <10ms
        - *Goal*: Ensure combined validation layers meet <10ms performance budget
        - *Details*:
            - RED: Write test_validation_latency_under_budget() - fail if >10ms
            - GREEN: Measure validation_time_ms for all 3 layers combined
            - GREEN: Optimize hot paths if latency exceeds budget
            - REFACTOR: Add caching for repeated field lookups
        - *Requirements*: AC3.7, NFR-P1 (total <10ms)
        - *Files*: src/validation/gateway.py
        - *Tests*: tests/performance/test_validation_latency.py (new)
        - *Estimated Time*: 5 hours

    - [ ] 6.5. Set up performance monitoring dashboard
        - *Goal*: Real-time metrics dashboard for validation effectiveness tracking
        - *Details*:
            - Implement metrics collection for field_error_rate, llm_success_rate, validation_latency
            - Export metrics to monitoring system (Prometheus/CloudWatch compatible)
            - Create dashboard with graphs for key metrics
            - Set up alerts for metric threshold violations
        - *Requirements*: AC3.8, NFR-O1, NFR-O4 (30s update time)
        - *Files*: src/metrics/collector.py, src/metrics/exporter.py (new)
        - *Tests*: tests/metrics/test_dashboard.py (new)
        - *Estimated Time*: 6 hours

    - [ ] 6.6. Deploy 100% rollout
        - *Goal*: Enable validation for 100% of strategy generation requests
        - *Details*:
            - RED: Write test_rollout_100_percent() - verify all requests validated
            - GREEN: Update rollout percentage to 100%
            - GREEN: Monitor metrics for any issues during full rollout
            - GREEN: Validate rollback capability works (can revert to 0% in <5 min)
            - REFACTOR: Remove rollout sampling logic (no longer needed at 100%)
        - *Requirements*: AC3.9, AC-CC2 (rollback <5 min)
        - *Files*: src/learning/iteration_executor.py, src/metrics/collector.py
        - *Tests*: tests/metrics/test_rollout_100.py (new)
        - *Estimated Time*: 3 hours

### Week 4: Polish & Production Readiness (Day 16-20)

- [ ] **7. Validation Metadata Integration - Result Enhancement**
    - [x] 7.1. Add validation metadata fields to BacktestResult
        - *Goal*: Track validation outcomes in backtest results for analysis
        - *Details*:
            - RED: Write test_backtest_result_has_validation_metadata()
            - GREEN: Add validation_passed, validation_errors, error_category, retry_count to BacktestResult
            - GREEN: Make validation metadata optional (default: None) for backward compatibility
            - REFACTOR: Update BacktestResult.__post_init__() to validate new fields
        - *Requirements*: AC4.2, NFR-C3 (optional metadata)
        - *Files*: src/execution/backtest_result.py
        - *Tests*: tests/execution/test_backtest_result_metadata.py (new)
        - *Estimated Time*: 3 hours

    - [ ] 7.2. Populate validation metadata in StrategyFactory
        - *Goal*: Pass validation results from ValidationGateway to BacktestResult
        - *Details*:
            - RED: Write test_validation_metadata_populated_in_result()
            - GREEN: Extract validation metadata from ValidationResult in StrategyFactory.execute()
            - GREEN: Pass metadata to BacktestResult constructor
            - REFACTOR: Create ValidationMetadata dataclass for type safety
        - *Requirements*: AC4.2, Design.DataModels.ValidationMetadata
        - *Files*: src/execution/strategy_factory.py
        - *Tests*: tests/execution/test_strategy_factory_metadata.py (new)
        - *Estimated Time*: 4 hours

- [ ] **8. Complete Type Validation - Field Type Checking**
    - [x] 8.1. Implement type validation for all field types
        - *Goal*: Validate field data types match expected types from DataFieldManifest
        - *Details*:
            - RED: Write test_type_validation_catches_type_mismatches()
            - GREEN: Add validate_field_types() method to FieldValidator
            - GREEN: Check field types against DataFieldManifest schema
            - GREEN: Return TypeError validation errors for type mismatches
            - REFACTOR: Optimize type checking for performance
        - *Requirements*: AC4.1, Design.Components.FieldValidator (type validation)
        - *Files*: src/validation/field_validator.py
        - *Tests*: tests/validation/test_type_validation.py (new)
        - *Estimated Time*: 5 hours

- [ ] **9. LLM Success Rate Validation - Target Achievement**
    - [x] 9.1. Measure LLM success rate with all layers enabled
        - *Goal*: Validate LLM success rate reaches 70-85% target range
        - *Details*:
            - Run comprehensive test suite with 200+ strategy generation attempts
            - Collect llm_success_rate metric (successful generations / total attempts)
            - Analyze failure patterns and adjust retry prompts if needed
            - Validate success rate meets 70-85% target
        - *Requirements*: AC4.3, Success Metrics (Week 4: 70-85%)
        - *Files*: tests/integration/test_llm_success_rate.py (new)
        - *Tests*: Large-scale integration test suite
        - *Estimated Time*: 6 hours

- [ ] **10. Integration Testing - End-to-End Validation**
    - [x] 10.1. Create comprehensive integration test suite
        - *Goal*: Validate entire workflow from LLM generation to backtest execution
        - *Details*:
            - Create 50+ end-to-end test scenarios covering all validation layers
            - Test with validation enabled and disabled (A/B comparison)
            - Validate rollback scenarios (disable layers, verify fallback)
            - Test circuit breaker activation and recovery
        - *Requirements*: AC4.4, NFR-C1 (backward compatibility)
        - *Files*: tests/integration/test_validation_e2e.py (new)
        - *Tests*: Comprehensive E2E test suite
        - *Estimated Time*: 8 hours

    - [ ] 10.2. Performance validation under load
        - *Goal*: Confirm <10ms latency under realistic load conditions
        - *Details*:
            - RED: Write test_validation_latency_under_load() - concurrent requests
            - GREEN: Run performance tests with 10+ parallel strategy generations
            - GREEN: Measure validation_latency percentiles (p50, p95, p99)
            - GREEN: Validate p99 latency <10ms
            - REFACTOR: Add connection pooling or caching if performance issues found
        - *Requirements*: AC4.5, NFR-P1, NFR-SC1 (10+ parallel)
        - *Files*: tests/performance/test_load.py (new)
        - *Tests*: Performance test suite with load simulation
        - *Estimated Time*: 5 hours

- [ ] **11. Documentation & Training - Production Readiness**
    - [x] 11.1. Create comprehensive documentation
        - *Goal*: Document all validation features, configuration, and troubleshooting
        - *Details*:
            - Write API documentation for ValidationGateway, ValidationResult
            - Create runbook for operations team (rollback, monitoring, troubleshooting)
            - Document feature flags and environment variables
            - Create migration guide from non-validated to validated workflow
        - *Requirements*: AC4.6
        - *Files*: docs/validation-integration-api.md (new), docs/validation-runbook.md (new), docs/validation-migration-guide.md (new)
        - *Tests*: Documentation review and validation
        - *Estimated Time*: 6 hours

    - [ ] 11.2. Train operations team on new validation system
        - *Goal*: Ensure operations team can manage, monitor, and troubleshoot validation system
        - *Details*:
            - Conduct training session on validation architecture and features
            - Walk through runbook procedures (rollback, monitoring, alerts)
            - Practice rollback scenarios in staging environment
            - Answer questions and address concerns
        - *Requirements*: AC4.7
        - *Files*: Training materials and runbook
        - *Tests*: Training completion and competency validation
        - *Estimated Time*: 4 hours

    - [ ] 11.3. Obtain production deployment approval
        - *Goal*: Get stakeholder approval for production deployment
        - *Details*:
            - Present validation system overview and benefits
            - Share success metrics (0% field error rate, 70-85% LLM success rate)
            - Review rollback plan and risk mitigation strategies
            - Obtain sign-off from product, engineering, and operations stakeholders
        - *Requirements*: AC4.8
        - *Files*: Stakeholder approval documentation
        - *Tests*: Approval checklist completion
        - *Estimated Time*: 2 hours

## Task Dependencies

### Week 1 Dependencies
- Task 1 (Security Fix) must be completed before any other tasks (Day 1 priority)
- Task 2.1 (DataFieldManifest integration) must be completed before Task 2.2 (feature flags)
- Task 2.2 (feature flags) must be completed before Task 2.3 (rollout)
- Task 2.4 (regression testing) must pass before Week 1 completion

### Week 2 Dependencies
- Task 3.1 (ValidationGateway) must be completed before Task 3.2 (FieldValidator integration)
- Task 3.2 (FieldValidator) must be completed before Task 3.3 (Layer 2 flag)
- Task 4.1 (ErrorFeedbackLoop) must be completed before Task 4.2 (retry prompts)
- Tasks 4.3 (metrics) and 4.4 (rollout) can only start after Task 4.2 completion
- All Week 1 tasks must be completed before Week 2 tasks begin

### Week 3 Dependencies
- Task 5.1 (SchemaValidator) must be completed before Task 5.2 (Layer 3 flag)
- Task 5.3 (YAML error validation) requires Task 5.1 completion
- Task 6.1 (error signature tracking) must be completed before Task 6.2 (circuit breaker activation)
- Task 6.3 (0% field error rate) requires all validation layers (Tasks 2.1, 3.2, 5.1) completed
- Task 6.4 (latency validation) can run in parallel with Task 6.3
- Task 6.5 (monitoring dashboard) can run in parallel with Tasks 6.3-6.4
- Task 6.6 (100% rollout) requires all Week 3 tasks completed
- All Week 2 tasks must be completed before Week 3 tasks begin

### Week 4 Dependencies
- Task 7.1 (BacktestResult metadata) must be completed before Task 7.2 (StrategyFactory integration)
- Task 8.1 (type validation) can run in parallel with Task 7
- Task 9.1 (LLM success rate) requires all validation layers completed (Tasks 2, 3, 4, 5, 6)
- Task 10.1 (integration testing) requires all core features completed (Tasks 2-9)
- Task 10.2 (performance testing) can run in parallel with Task 10.1
- Task 11.1 (documentation) can run in parallel with Tasks 10.1-10.2
- Task 11.2 (training) requires Task 11.1 (documentation) completion
- Task 11.3 (approval) requires all Week 4 tasks completed

### Critical Path
Security Fix (Task 1) → DataFieldManifest (Task 2.1-2.2) → ValidationGateway (Task 3.1) → FieldValidator (Task 3.2) → ErrorFeedbackLoop (Task 4.1-4.2) → SchemaValidator (Task 5.1-5.2) → Circuit Breaker (Task 6.1-6.2) → Metadata Integration (Task 7) → Integration Testing (Task 10) → Production Approval (Task 11.3)

### Parallel Execution Opportunities
- Week 1: Tasks 2.3 and 2.4 can partially overlap
- Week 2: Tasks 3.3 and 4.1 can run in parallel after Task 3.2
- Week 3: Tasks 6.3, 6.4, and 6.5 can run in parallel
- Week 4: Tasks 7, 8, and 11.1 can run in parallel; Tasks 10.1 and 10.2 can run in parallel

## Estimated Timeline

### Week 1: Foundation & Security
- Task 1 (Security Fix): 2 hours
- Task 2.1 (DataFieldManifest integration): 6 hours
- Task 2.2 (Layer 1 feature flag): 4 hours
- Task 2.3 (10% rollout): 5 hours
- Task 2.4 (Regression testing): 4 hours
- **Week 1 Total: 21 hours (2.6 days at 8 hours/day)**

### Week 2: Code Validation & Retry
- Task 3.1 (ValidationGateway): 4 hours
- Task 3.2 (FieldValidator integration): 6 hours
- Task 3.3 (Layer 2 feature flag): 3 hours
- Task 4.1 (ErrorFeedbackLoop integration): 5 hours
- Task 4.2 (Retry prompt generation): 4 hours
- Task 4.3 (Field error rate measurement): 5 hours
- Task 4.4 (50% rollout): 3 hours
- **Week 2 Total: 30 hours (3.75 days at 8 hours/day)**

### Week 3: Schema Validation & Performance
- Task 5.1 (SchemaValidator integration): 5 hours
- Task 5.2 (Layer 3 feature flag): 3 hours
- Task 5.3 (YAML error validation): 4 hours
- Task 6.1 (Error signature tracking): 5 hours
- Task 6.2 (Circuit breaker activation): 4 hours
- Task 6.3 (0% field error rate): 4 hours
- Task 6.4 (Latency validation): 5 hours
- Task 6.5 (Performance monitoring): 6 hours
- Task 6.6 (100% rollout): 3 hours
- **Week 3 Total: 39 hours (4.9 days at 8 hours/day)**

### Week 4: Polish & Production Readiness
- Task 7.1 (BacktestResult metadata): 3 hours
- Task 7.2 (StrategyFactory metadata): 4 hours
- Task 8.1 (Type validation): 5 hours
- Task 9.1 (LLM success rate): 6 hours
- Task 10.1 (Integration testing): 8 hours
- Task 10.2 (Performance testing): 5 hours
- Task 11.1 (Documentation): 6 hours
- Task 11.2 (Training): 4 hours
- Task 11.3 (Production approval): 2 hours
- **Week 4 Total: 43 hours (5.4 days at 8 hours/day)**

### Overall Project Estimate
- **Total Development Time: 133 hours (16.6 days at 8 hours/day)**
- **Calendar Time: 4 weeks (20 working days)** with buffer for testing, reviews, and unforeseen issues
- **Team Capacity Required**: 1 senior developer (full-time) OR 2 developers (part-time collaboration)
- **Risk Buffer**: 20% additional time built into calendar schedule for:
    - Code review iterations (estimated 10 hours)
    - Bug fixes and rework (estimated 15 hours)
    - Stakeholder feedback incorporation (estimated 5 hours)
    - Integration issues resolution (estimated 10 hours)

### Milestone Checkpoints
- **M1 (End of Week 1)**: Layer 1 deployed at 10%, security fix complete, regression tests passing
- **M2 (End of Week 2)**: Layer 2 + ErrorFeedbackLoop integrated, 50% rollout, field error rate <10%
- **M3 (End of Week 3)**: All layers deployed at 100%, circuit breaker active, field error rate 0%
- **M4 (End of Week 4)**: Production-ready, LLM success rate 70-85%, documentation complete, approval obtained
