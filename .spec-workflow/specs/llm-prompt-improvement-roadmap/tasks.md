# LLM Prompt Engineering Improvement Roadmap - Task List

## Implementation Tasks

- [ ] **Phase 1: Field Name Validation System (Target: 20% → 55-60%)**
    - [ ] 1.1. TDD Cycle 1.1 - Field Catalog Creation
        - *Goal*: Create comprehensive field catalog with ALL valid FinLab fields
        - *Details*:
            - Extract all fields from VALID_FINLAB_FIELDS (fundamental_features, financial_statement, price_earning_ratio)
            - Format as Python list for easy verification
            - **CRITICAL**: Show ALL fields, not just first 20
        - *Requirements*: REQ-1 (Field name validation), Critical Fix #1 from audit
        - *Files*: `src/factor_library/registry.py`, test file
        - *Test*: `test_field_catalog_completeness()`
        - *Dependencies*: None (can start immediately)
        - *Parallel*: Can develop in parallel with 1.2, 1.2.5, 1.3

    - [ ] 1.2. TDD Cycle 1.2 - API Documentation Section Enhancement
        - *Goal*: Update prompt builder to include complete field catalog
        - *Details*:
            - Modify `_build_api_documentation_section()` to show ALL fields
            - Use Python list format (not markdown list)
            - Add usage examples with data.get()
            - Add warnings about field name hallucination
        - *Requirements*: REQ-1, Critical Fix #1 from audit
        - *Files*: `src/innovation/prompt_builder.py`
        - *Test*: `test_prompt_contains_all_fields()`
        - *Dependencies*: Soft dependency on 1.1 (field catalog), but can use existing catalog
        - *Parallel*: Can develop in parallel with 1.1, 1.2.5, 1.3

    - [ ] 1.2.5. TDD Cycle 1.2.5 - System Prompt Addition (NEW from audit)
        - *Goal*: Add system prompt with Chain of Thought guidance
        - *Details*:
            - Create `_build_system_prompt()` method
            - Define LLM persona and primary goals
            - Add Chain of Thought workflow instructions
            - Integrate system prompt as first section in build_creation_prompt()
        - *Requirements*: Missing element from audit, REQ-1
        - *Files*: `src/innovation/prompt_builder.py`
        - *Test*: `test_system_prompt_exists()`, `test_system_prompt_includes_cot()`
        - *Dependencies*: None (independent prompt builder enhancement)
        - *Parallel*: Can develop in parallel with 1.1, 1.2, 1.3

    - [ ] 1.3. TDD Cycle 1.3 - Field Validation Helper
        - *Goal*: Provide LLM with field validation helper function example
        - *Details*:
            - Create `_build_validation_helpers()` method
            - Include `validate_field_exists()` example code
            - Show how to check field validity before use
        - *Requirements*: REQ-1
        - *Files*: `src/innovation/prompt_builder.py`
        - *Test*: `test_validation_helper_in_prompt()`
        - *Dependencies*: Soft dependency on 1.1 (field catalog reference)
        - *Parallel*: Can develop in parallel with 1.1, 1.2, 1.2.5

    - [ ] 1.4. Phase 1 Validation
        - *Goal*: Validate Phase 1 achieves 55-60% success rate
        - *Details*:
            - Run 20-iteration three-mode test
            - Monitor token count (<25K expected)
            - Analyze error distribution (field errors should drop to <15%)
            - Document results
        - *Requirements*: REQ-1, validation criteria
        - *Command*: `python3 run_20iteration_three_mode_test.py`
        - *Success Criteria*: LLM success ≥55%, token count <25K
        - *Dependencies*: **MUST complete 1.1, 1.2, 1.2.5, 1.3** (all Phase 1 tasks)
        - *Parallel*: None (sequential after Phase 1 development)

- [ ] **Phase 2: Code Structure Enforcement (Target: 55-60% → 65%)**
    - [ ] 2.1. TDD Cycle 2.1 - Code Structure Requirements
        - *Goal*: Enhance prompt with explicit code structure requirements
        - *Details*:
            - Update `_build_code_requirements()` method
            - Add required structure checklist
            - Include mandatory `return position` statement
            - Add proper function signature requirements
        - *Requirements*: REQ-2 (Code structure validation)
        - *Files*: `src/innovation/prompt_builder.py`
        - *Test*: `test_structure_requirements_in_prompt()`
        - *Dependencies*: **MUST complete Phase 1 (1.4 validation passed)**
        - *Parallel*: Can develop in parallel with 2.2, 2.3

    - [ ] 2.2. TDD Cycle 2.2 - Structure Validation Examples
        - *Goal*: Provide correct structure examples in prompt
        - *Details*:
            - Add 2-3 well-structured strategy examples
            - Show proper imports, function definition, return statement
            - Demonstrate data.get() usage pattern
        - *Requirements*: REQ-2
        - *Files*: `src/innovation/prompt_builder.py`
        - *Test*: `test_structure_examples_present()`
        - *Dependencies*: **MUST complete Phase 1 (1.4 validation passed)**
        - *Parallel*: Can develop in parallel with 2.1, 2.3

    - [ ] 2.3. TDD Cycle 2.3 - Structure Compliance Checks
        - *Goal*: Add automated structure validation
        - *Details*:
            - Create or enhance `structure_validator.py`
            - Check for required function signature
            - Validate return statement presence
            - Ensure no syntax errors via AST parsing
        - *Requirements*: REQ-2
        - *Files*: `src/innovation/validators/structure_validator.py` (NEW or ENHANCED)
        - *Test*: `test_structure_validator_rejects_malformed_code()`
        - *Dependencies*: **MUST complete Phase 1 (1.4 validation passed)**
        - *Parallel*: Can develop in parallel with 2.1, 2.2

    - [ ] 2.4. Phase 2 Validation
        - *Goal*: Validate Phase 2 achieves 65% success rate
        - *Details*:
            - Run 20-iteration test
            - Monitor token count (<30K expected)
            - Verify structure errors <5% of failures
        - *Requirements*: REQ-2, validation criteria
        - *Success Criteria*: LLM success ≥65%, token count <30K
        - *Dependencies*: **MUST complete 2.1, 2.2, 2.3** (all Phase 2 tasks)
        - *Parallel*: None (sequential after Phase 2 development)

- [ ] **Phase 3: API Documentation Enhancement (Target: 65% → 75%)**
    - [ ] 3.1. TDD Cycle 3.1 - Data Object Documentation
        - *Goal*: Document DataCache API and data.get() method
        - *Details*:
            - Add API reference section to prompt
            - Document data.get() signature and return type
            - Explain DataFrame operations available
            - Add shift(1) usage for avoiding look-ahead bias
        - *Requirements*: REQ-3 (API documentation)
        - *Files*: `src/innovation/prompt_builder.py`
        - *Test*: `test_api_documentation_section_exists()`
        - *Dependencies*: **MUST complete Phase 2 (2.4 validation passed)**
        - *Parallel*: Can develop in parallel with 3.2, 3.3

    - [ ] 3.2. TDD Cycle 3.2 - API Usage Examples
        - *Goal*: Provide correct API usage examples
        - *Details*:
            - Add 3-5 examples of data.get() patterns
            - Show proper DataFrame manipulation
            - Demonstrate common calculations (RSI, MA, etc.)
            - Include fillna() and shift() usage
        - *Requirements*: REQ-3
        - *Files*: `src/innovation/prompt_builder.py`
        - *Test*: `test_api_examples_cover_common_patterns()`
        - *Dependencies*: **MUST complete Phase 2 (2.4 validation passed)**
        - *Parallel*: Can develop in parallel with 3.1, 3.3

    - [ ] 3.3. TDD Cycle 3.3 - Anti-pattern Documentation
        - *Goal*: Document common API misuse patterns to avoid
        - *Details*:
            - List common mistakes (e.g., using non-existent methods)
            - Explain why certain patterns fail
            - Provide correct alternatives
        - *Requirements*: REQ-3
        - *Files*: `src/innovation/prompt_builder.py`
        - *Test*: `test_anti_patterns_documented()`
        - *Dependencies*: **MUST complete Phase 2 (2.4 validation passed)**
        - *Parallel*: Can develop in parallel with 3.1, 3.2

    - [ ] 3.4. Phase 3 Validation
        - *Goal*: Validate Phase 3 achieves 75% success rate
        - *Details*:
            - Run 20-iteration test
            - Monitor token count (<35K expected)
            - Verify API errors <2% of failures
        - *Requirements*: REQ-3, validation criteria
        - *Success Criteria*: LLM success ≥75%, token count <35K
        - *Dependencies*: **MUST complete 3.1, 3.2, 3.3** (all Phase 3 tasks)
        - *Parallel*: None (sequential after Phase 3 development)

- [ ] **Phase 4: Metric Validation & Edge Cases (Target: 75% → 87-90%)**
    - [ ] 4.1. TDD Cycle 4.1 - Metric Validation Guidelines
        - *Goal*: Add metric validation requirements to prompt
        - *Details*:
            - Document required metrics (sharpe_ratio, total_return)
            - Explain valid metric ranges (sharpe: -3 to 5, etc.)
            - Add NaN/Inf detection requirements
        - *Requirements*: REQ-4 (Metric validation)
        - *Files*: `src/innovation/prompt_builder.py`
        - *Test*: `test_metric_guidelines_in_prompt()`
        - *Dependencies*: **MUST complete Phase 3 (3.4 validation passed)**
        - *Parallel*: Can start in parallel with 4.2 development

    - [ ] 4.2. TDD Cycle 4.2 - Framework Safeguards (NEW - simplified approach from audit)
        - *Goal*: Create framework boilerplate for edge case handling
        - *Details*:
            - Create `src/backtest/strategy_executor.py` (NEW FILE)
            - Implement `execute_strategy_with_safeguards()` function
            - Add automatic empty position fallback
            - Add liquidity filtering
            - Add position normalization
            - Update prompt to explain framework handles edge cases
        - *Requirements*: REQ-4, Critical Fix #2 from audit
        - *Files*: `src/backtest/strategy_executor.py` (NEW), `src/innovation/prompt_builder.py`
        - *Test*: `test_safeguards_handle_empty_position()`, `test_safeguards_apply_liquidity_filter()`
        - *Dependencies*: **MUST complete Phase 3 (3.4 validation passed)**
        - *Parallel*: Can develop in parallel with 4.1, but before 4.3

    - [ ] 4.3. TDD Cycle 4.3 - Simplified Prompt for Edge Cases
        - *Goal*: Update prompt to focus LLM on core logic only
        - *Details*:
            - Update edge case guidance section
            - Explain framework automatically handles edge cases
            - Remove complex edge-case generation from LLM task
            - Show simplified LLM task: just return boolean DataFrame
        - *Requirements*: REQ-4, Critical Fix #2 from audit
        - *Files*: `src/innovation/prompt_builder.py`
        - *Test*: `test_prompt_simplifies_llm_task()`
        - *Dependencies*: **MUST complete 4.2** (needs safeguards framework to reference)
        - *Parallel*: None (depends on 4.2 completion)

    - [ ] 4.4. Phase 4 Validation
        - *Goal*: Validate Phase 4 achieves 87-90% success rate
        - *Details*:
            - Run 20-iteration test
            - Monitor token count (<40K expected, well within 100K limit)
            - Verify metric errors <5% of failures
        - *Requirements*: REQ-4, validation criteria
        - *Success Criteria*: LLM success ≥87%, token count <40K
        - *Dependencies*: **MUST complete 4.1, 4.2, 4.3** (all Phase 4 tasks)
        - *Parallel*: None (sequential after Phase 4 development)

- [ ] **Token Monitoring Integration (Cross-Phase)**
    - [ ] 5.1. Create Token Monitoring Module
        - *Goal*: Add explicit token count monitoring
        - *Details*:
            - Create `src/innovation/token_monitor.py` (NEW FILE)
            - Implement `validate_phase_completion()` function
            - Use tiktoken for accurate counting
            - Return dict with token metrics
        - *Requirements*: Missing element from audit
        - *Files*: `src/innovation/token_monitor.py` (NEW)
        - *Test*: `test_token_monitor_measures_correctly()`
        - *Dependencies*: None (independent utility module)
        - *Parallel*: Can develop anytime, even in parallel with Phase 1-4

    - [ ] 5.2. Integrate Token Monitoring in All Phases
        - *Goal*: Add token monitoring to each phase validation
        - *Details*:
            - Import token_monitor in test files
            - Call validate_phase_completion() after each phase
            - Log token usage trends
            - Assert token count < 100K (safe limit)
        - *Requirements*: Missing element from audit
        - *Files*: Test files for all phases
        - *Test*: Integration validated in each phase test
        - *Dependencies*: **MUST complete 5.1** (token monitor module)
        - *Parallel*: Can integrate into each phase validation as it's developed

- [ ] **Final Validation and Documentation**
    - [ ] 6.1. 50-Iteration Comprehensive Test
        - *Goal*: Validate final success rate with high confidence
        - *Details*:
            - Run 50-iteration three-mode test
            - Collect comprehensive metrics
            - Generate statistical confidence intervals
            - Compare against baseline
        - *Requirements*: All requirements, final validation
        - *Command*: `python3 run_50iteration_three_mode_test.py`
        - *Success Criteria*: LLM success ≥87%, Hybrid ≥70%, Factor Graph ≥85%
        - *Dependencies*: **MUST complete all Phases 1-4 and 5.2** (full implementation)
        - *Parallel*: None (final sequential validation)

    - [ ] 6.2. Performance Regression Check
        - *Goal*: Ensure Hybrid and Factor Graph modes not degraded
        - *Details*:
            - Compare 50-iteration results vs. baseline
            - Verify Hybrid maintained ≥70%
            - Verify Factor Graph maintained ≥85%
            - Check Sharpe ratio quality maintained
        - *Requirements*: Non-functional requirement (maintain existing performance)
        - *Success Criteria*: No regression in Hybrid or Factor Graph modes
        - *Dependencies*: **MUST complete 6.1** (needs test results)
        - *Parallel*: Can run concurrently with 6.1 analysis

    - [ ] 6.3. Documentation Updates
        - *Goal*: Document all changes and lessons learned
        - *Details*:
            - Update `docs/LLM_PROMPT_ENGINEERING.md` with improvements
            - Document token usage trends
            - Record error pattern changes
            - Add troubleshooting guide for common issues
        - *Requirements*: Documentation requirement
        - *Files*: `docs/LLM_PROMPT_ENGINEERING.md` (NEW or UPDATE)
        - *Dependencies*: Soft dependency on 6.1, 6.2 (can start during Phase 4)
        - *Parallel*: Can develop in parallel with Phase 4 and final validation

    - [ ] 6.4. Code Review and Cleanup
        - *Goal*: Ensure code quality before production
        - *Details*:
            - Run lint checks (flake8, mypy)
            - Remove debug code and comments
            - Ensure test coverage ≥90% for new code
            - Update type hints
        - *Requirements*: Quality standards
        - *Success Criteria*: All lint checks pass, coverage ≥90%
        - *Dependencies*: **MUST complete all Phases 1-4** (needs full code)
        - *Parallel*: Can run in parallel with 6.1, 6.2, 6.3

## Task Dependencies

**Sequential Dependencies**:
- Phase 1 must be completed before Phase 2 (field validation is foundation)
- Phase 2 must be completed before Phase 3 (structure precedes API understanding)
- Phase 3 must be completed before Phase 4 (API knowledge precedes metrics)
- Token monitoring (5.1) can start anytime but must complete before phase integrations (5.2)
- Final validation (6.x) requires all phases 1-4 completed

**Parallel Opportunities**:
- Within Phase 1: Tasks 1.1, 1.2, 1.2.5, 1.3 can be developed in parallel (all independent)
- Within Phase 2: Tasks 2.1, 2.2, 2.3 can be developed in parallel
- Within Phase 3: Tasks 3.1, 3.2, 3.3 can be developed in parallel
- Within Phase 4: Task 4.1 can start while 4.2 is in development
- Token monitoring module (5.1) can be developed in parallel with any phase
- Documentation (6.3) can start during Phase 4 and continue through final validation

**Critical Path**:
1. Phase 1 (Field Catalog) - CRITICAL FIX
2. Phase 1 Validation (1.4) - Verify improvement
3. Phase 2 (Structure) → Phase 3 (API) → Phase 4 (Edge Cases)
4. Final 50-iteration validation (6.1)
5. Documentation and cleanup (6.3, 6.4)

## Estimated Timeline

**Phase 1: Field Name Validation System**
- Task 1.1 (Field Catalog): 1 hour
- Task 1.2 (API Doc Enhancement): 2 hours
- Task 1.2.5 (System Prompt): 1.5 hours (NEW from audit)
- Task 1.3 (Validation Helper): 1 hour
- Task 1.4 (Phase 1 Validation): 0.5 hour
- **Phase 1 Total: 6 hours**

**Phase 2: Code Structure Enforcement**
- Task 2.1 (Structure Requirements): 1.5 hours
- Task 2.2 (Structure Examples): 1 hour
- Task 2.3 (Structure Validator): 2 hours
- Task 2.4 (Phase 2 Validation): 0.5 hour
- **Phase 2 Total: 5 hours**

**Phase 3: API Documentation Enhancement**
- Task 3.1 (Data Object Docs): 1.5 hours
- Task 3.2 (API Examples): 1.5 hours
- Task 3.3 (Anti-patterns): 1 hour
- Task 3.4 (Phase 3 Validation): 0.5 hour
- **Phase 3 Total: 4.5 hours**

**Phase 4: Metric Validation & Edge Cases**
- Task 4.1 (Metric Guidelines): 1 hour
- Task 4.2 (Framework Safeguards): 2.5 hours (NEW from audit)
- Task 4.3 (Simplified Prompt): 1 hour (NEW from audit)
- Task 4.4 (Phase 4 Validation): 0.5 hour
- **Phase 4 Total: 5 hours**

**Token Monitoring Integration**
- Task 5.1 (Token Monitor Module): 1 hour (NEW from audit)
- Task 5.2 (Integration): 1 hour (NEW from audit)
- **Token Monitoring Total: 2 hours**

**Final Validation and Documentation**
- Task 6.1 (50-iteration test): 1 hour
- Task 6.2 (Regression check): 0.5 hour
- Task 6.3 (Documentation): 2 hours
- Task 6.4 (Code review/cleanup): 1.5 hour
- **Final Total: 5 hours**

**Overall Timeline**:
- **Development: 27.5 hours** (≈3.5 days at 8 hours/day)
- **Buffer for issues: 4.5 hours** (0.5 days)
- **Total Estimate: 32 hours (4 days)**

**Audit-Enhanced Changes**:
- Added 1.5 hours for System Prompt (1.2.5)
- Added 3.5 hours for Framework Safeguards approach (4.2, 4.3)
- Added 2 hours for Token Monitoring (5.1, 5.2)
- **Total audit additions: 7 hours**
- **Original estimate: 2-3 days → New estimate: 3-4 days**

## Implementation Order (Recommended)

**Day 1 (8 hours)**: Phase 1 Complete
1. Morning (4h): Tasks 1.1, 1.2, 1.2.5 (parallel development)
2. Afternoon (4h): Task 1.3, Phase 1 validation, Phase 1 analysis

**Day 2 (8 hours)**: Phase 2 & 3 Complete
1. Morning (4h): Tasks 2.1, 2.2, 2.3 (parallel), Phase 2 validation
2. Afternoon (4h): Tasks 3.1, 3.2, 3.3 (parallel), Phase 3 validation

**Day 3 (8 hours)**: Phase 4 & Token Monitoring Complete
1. Morning (4h): Tasks 4.1, 4.2 (Framework Safeguards)
2. Afternoon (4h): Task 4.3, 5.1, 5.2, Phase 4 validation

**Day 4 (8 hours)**: Final Validation & Documentation
1. Morning (4h): Task 6.1 (50-iteration test), Task 6.2 (regression check)
2. Afternoon (4h): Tasks 6.3, 6.4 (documentation and cleanup)

**Flexibility**: Token monitoring (5.1) can be developed during Day 1-2 in parallel with phases to save time.
