# LLM Field Validation Fix - Three-Layered Defense - Task List

## Phase 1: Foundation Week (Days 1-7)

### Days 1-2: finlab Field Discovery

- [x] 1. **Create finlab Field Discovery Script**
    - [x] 1.1. Implement `scripts/discover_finlab_fields.py`
        - *Goal*: Query finlab API to discover all available fields
        - *Details*: Use finlab.data API to enumerate price, fundamental, and technical fields. Implement retry logic with exponential backoff (3 attempts). Include fallback to Factor Graph field list if API unavailable.
        - *Requirements*: Day 1-2 field discovery requirements
    - [x] 1.2. Create field metadata data structure
        - *Goal*: Design FieldMetadata class with all required attributes
        - *Details*: Define dataclass with canonical_name, category, frequency, dtype, description (zh/en), aliases, example_values, valid_range
        - *Requirements*: Layer 1 enhanced manifest requirements
    - [x] 1.3. Implement JSON cache saving/loading
        - *Goal*: Cache discovered fields to tests/fixtures/finlab_fields.json
        - *Details*: Use json.dump() for serialization, include metadata (discovery_date, total_fields, api_version)
        - *Requirements*: Field cache creation requirements

- [x] 2. **Write Field Discovery Tests (TDD)**
    - [x] 2.1. RED: Write `test_finlab_api_field_availability()`
        - *Goal*: Failing test for finlab API field discovery
        - *Details*: Test should verify ≥17 fields discovered, all critical fields exist (price:收盤價, price:成交金額, fundamental_features:ROE), metadata completeness
        - *Requirements*: Day 1-2 testing requirements
    - [x] 2.2. GREEN: Implement discovery to pass test
        - *Goal*: Make test pass with minimal implementation
        - *Details*: Query finlab API, populate FieldMetadata, save to cache
        - *Requirements*: TDD methodology requirements
    - [x] 2.3. REFACTOR: Improve code quality
        - *Goal*: Clean up implementation, add logging, improve error handling
        - *Details*: Add type hints, docstrings, logging statements, error handling with fallback strategies
        - *Requirements*: Quality requirements (PEP 8, type hints)

- [ ] 3. **Field Discovery Validation**
    - [x] 3.1. Run field discovery script
        - *Goal*: Execute discovery and create finlab_fields.json cache
        - *Details*: Run `python scripts/discover_finlab_fields.py`, verify cache created with ≥17 fields
        - *Requirements*: Day 2 acceptance criteria
    - [x] 3.2. Verify 0% field error rate
        - *Goal*: Confirm all discovered fields are valid
        - *Details*: Cross-validate discovered fields against finlab API, ensure no invalid fields in cache
        - *Requirements*: 0% field error rate (non-negotiable)

### Days 3-4: Layer 1 - Enhanced Data Field Manifest

- [x] 4. **Create DataFieldManifest Class**
    - [x] 4.1. RED: Write `test_alias_resolution()` test
        - *Goal*: Failing test for alias → canonical name resolution
        - *Details*: Test cases: 'close' → 'price:收盤價', 'volume' → 'price:成交金額', 'roe' → 'fundamental_features:ROE'
        - *Requirements*: Day 3-4 Layer 1 requirements
    - [x] 4.2. GREEN: Implement `DataFieldManifest` class
        - *Goal*: Create manifest with get_field(), validate_field(), get_aliases() methods
        - *Details*: Load fields from finlab_fields.json, build alias_map, implement resolution logic
        - *Requirements*: Layer 1 manifest specification
    - [x] 4.3. REFACTOR: Optimize lookup performance
        - *Goal*: Ensure <1ms query performance for alias resolution
        - *Details*: Use dict for O(1) lookups, pre-compute alias_map, add caching if needed
        - *Requirements*: Performance requirements (<1ms)

- [x] 5. **Implement Field Metadata Access**
    - [x] 5.1. RED: Write `test_field_metadata_access()` test
        - *Goal*: Test metadata retrieval (category, frequency, dtype, aliases)
        - *Details*: Verify manifest.get_field('close') returns FieldMetadata with category='price', frequency='daily', dtype='float'
        - *Requirements*: Field metadata management requirements
    - [x] 5.2. GREEN: Add metadata access methods
        - *Goal*: Implement get_fields_by_category(), get_aliases()
        - *Details*: Filter fields by category, return lists of field names/aliases
        - *Requirements*: Layer 1 interface specification
    - [x] 5.3. Write `test_category_filtering()` test
        - *Goal*: Test get_fields_by_category() functionality
        - *Details*: Verify price_fields = manifest.get_fields_by_category('price') contains expected fields
        - *Requirements*: Category-based field discovery

- [x] 6. **Implement Field Validation**
    - [x] 6.1. RED: Write `test_field_validation()` test
        - *Goal*: Test validate_field() returns (bool, suggestion)
        - *Details*: Valid field returns (True, None), invalid field returns (False, suggestion like "Did you mean 'price:成交金額'?")
        - *Requirements*: Validation mechanism requirements
    - [x] 6.2. GREEN: Implement validate_field() method
        - *Goal*: Check if field exists in manifest, provide suggestions for common mistakes
        - *Details*: Use Levenshtein distance or fuzzy matching for suggestions, prioritize common corrections
        - *Requirements*: Field validation specification
    - [x] 6.3. Add common mistake mapping
        - *Goal*: Hardcode top 20 common field mistakes
        - *Details*: Create COMMON_CORRECTIONS dict with 'price:成交量' → 'price:成交金額', 'close' → 'price:收盤價', etc.
        - *Requirements*: Common mistake handling

- [x] 7. **Layer 1 Integration Tests**
    - [x] 7.1. Write `test_finlab_integration()` test
        - *Goal*: Verify all manifest fields exist in finlab API
        - *Details*: For each field in manifest, call finlab.data.get(field_name) and assert not None
        - *Requirements*: Integration testing requirements
    - [x] 7.2. Run full Layer 1 test suite
        - *Goal*: Achieve ≥90% code coverage for Layer 1
        - *Details*: Run `pytest tests/test_data_field_manifest.py --cov=src/config --cov-report=term-missing`
        - *Requirements*: 90% code coverage requirement
    - [x] 7.3. Verify 0% field error rate
        - *Goal*: Confirm all fields in manifest are valid
        - *Details*: Run validation against finlab API, ensure no errors
        - *Requirements*: 0% field error rate checkpoint

### Days 5-6: Layer 2 - Pattern-Based Validator

- [x] 8. **Create FieldValidator Class**
    - [x] 8.1. RED: Write `test_invalid_field_detection()` test
        - *Goal*: Failing test for AST-based field error detection
        - *Details*: Test code with `data.get('price:成交量')` should return ValidationResult with error and suggestion 'price:成交金額'
        - *Requirements*: Layer 2 pattern validator requirements
    - [x] 8.2. GREEN: Implement AST-based validation
        - *Goal*: Parse code with ast.parse(), extract data.get() calls
        - *Details*: Walk AST tree, find ast.Call nodes with data.get pattern, extract field names, validate against manifest
        - *Requirements*: AST-based pattern detection specification
    - [x] 8.3. Define ValidationResult data structures
        - *Goal*: Create ValidationResult, FieldError, FieldWarning dataclasses
        - *Details*: Include line/column numbers, error_type, message, suggestion fields
        - *Requirements*: Structured error reporting

- [x] 9. **Implement Auto-Correction**
    - [x] 9.1. RED: Write `test_common_mistake_autocorrection()` test
        - *Goal*: Test auto-correction of top 20 common mistakes
        - *Details*: Test cases: 'price:成交量' → 'price:成交金額', 'close' → 'price:收盤價', 'volume' → 'price:成交金額'
        - *Requirements*: Auto-correction requirements (90%+ success)
    - [x] 9.2. GREEN: Implement auto_correct() method
        - *Goal*: Replace invalid fields with correct ones in code
        - *Details*: Use COMMON_CORRECTIONS dict, apply regex/AST replacement, track corrections with Correction dataclass
        - *Requirements*: Top 20 common mistakes specification
    - [x] 9.3. Add confidence scoring
        - *Goal*: Assign confidence levels to corrections
        - *Details*: High confidence (>0.9) for exact COMMON_CORRECTIONS matches, lower for fuzzy matches
        - *Requirements*: Auto-correction confidence requirements

- [x] 10. **Integrate Validator with Manifest**
    - [x] 10.1. RED: Write `test_integration_with_manifest()` test
        - *Goal*: Test validator uses Layer 1 manifest for validation
        - *Details*: Validator should accept valid canonical names, reject invalid fields, suggest canonical names for aliases
        - *Requirements*: Layer 1+2 integration requirements
    - [x] 10.2. GREEN: Pass manifest to validator constructor
        - *Goal*: Initialize FieldValidator(manifest)
        - *Details*: Store manifest reference, use manifest.validate_field() in validation logic
        - *Requirements*: Validator-manifest integration
    - [x] 10.3. Write structured error feedback tests
        - *Goal*: Test clear error messages with suggestions
        - *Details*: Error messages should include line numbers, field names, suggestions like "Did you mean 'price:成交金額'?"
        - *Requirements*: Structured error feedback specification

- [x] 11. **Layer 2 Testing**
    - [x] 11.1. Run full Layer 2 test suite
        - *Goal*: Achieve ≥90% code coverage for Layer 2
        - *Details*: Run `pytest tests/test_field_validator.py --cov=src/validation --cov-report=term-missing`
        - *Requirements*: 90% code coverage requirement
    - [x] 11.2. Test auto-correction rate
        - *Goal*: Verify 90%+ common mistakes are auto-corrected
        - *Details*: Test all 20 common mistakes, ensure high confidence corrections succeed
        - *Requirements*: 90%+ auto-correction rate

### Day 7: Integration Checkpoint (DECISION GATE 1)

- [x] 12. **Prepare 20-Iteration Validation Test**
    - [x] 12.1. Create test script for LLM improvement
        - *Goal*: Implement 20-iteration test with Layer 1+2 enabled
        - *Details*: Modify existing LLM test to use DataFieldManifest and FieldValidator, track field errors and success rate
        - *Requirements*: Day 7 checkpoint requirements
    - [x] 12.2. Configure test parameters
        - *Goal*: Set mode='llm_only', enable_manifest=True, enable_validator=True
        - *Details*: Update config to activate Layer 1+2, disable Factor Graph features
        - *Requirements*: 20-iteration test specification

- [x] 13. **Run Day 7 Checkpoint Test**
    - [x] 13.1. Execute 20-iteration test
        - *Goal*: Run test and collect results
        - *Details*: Execute test script, monitor progress, capture success_rate and field_error_rate
        - *Requirements*: Day 7 decision gate requirements
    - [x] 13.2. Analyze results
        - *Goal*: Evaluate success rate and field error rate
        - *Details*: Extract metrics from test results, verify field_error_rate = 0%, check if success_rate ≥ 25%
        - *Requirements*: Decision Gate 1 criteria
    - [x] 13.3. Make PASS/FAIL decision
        - *Goal*: Determine if Layer 3 implementation should proceed
        - *Details*: If field_error_rate > 0% → ROLLBACK (investigate manifest). If success_rate < 25% → DEBUG (analyze failures). If success_rate ≥ 25% → PROCEED to Layer 3
        - *Requirements*: Day 7 decision logic

- [x] 14. **Day 7 Checkpoint Documentation**
    - [x] 14.1. Document test results
        - *Goal*: Create checkpoint report with metrics
        - *Details*: Record success_rate, field_error_rate, avg_execution_time, auto_corrected count in docs/DAY7_CHECKPOINT_REPORT.md
        - *Requirements*: Evidence generation requirements
    - [x] 14.2. Update steering documentation
        - *Goal*: Update IMPLEMENTATION_STATUS.md with Day 7 results
        - *Details*: Record checkpoint outcome (PASS/FAIL), update overall progress, note next steps
        - *Requirements*: Documentation requirements

## Phase 2: Configuration Migration (Days 8-21)

### Days 8-10: Top 5 Pattern Selection

- [x] 15. **Analyze Factor Graph Success Patterns**
    - [x] 15.1. Review Factor Graph successful strategies
        - *Goal*: Identify top 5 most successful strategy patterns
        - *Details*: Analyze Factor Graph results, categorize patterns (momentum, value, quality, mixed), select 5 patterns covering ≥60% of successes
        - *Requirements*: Day 8-10 pattern selection requirements
    - [x] 15.2. Document pattern characteristics
        - *Goal*: Extract key features of each pattern
        - *Details*: Document required fields, parameters, entry/exit logic, constraints for each of 5 patterns
        - *Requirements*: Pattern identification requirements
    - [x] 15.3. Create pattern coverage analysis
        - *Goal*: Verify 5 patterns cover ≥60% of Factor Graph successes
        - *Details*: Map successful Factor Graph strategies to 5 patterns, calculate coverage percentage
        - *Requirements*: 60% coverage requirement

- [x] 16. **Design YAML Schema for Patterns**
    - [x] 16.1. Create base schema structure
        - *Goal*: Define YAML schema with required fields, parameters, logic, constraints
        - *Details*: Design schema with name, type, description, required_fields (with field/alias/usage), parameters (type/default/range), logic (entry/exit), constraints
        - *Requirements*: YAML schema specification
    - [x] 16.2. Define schemas for top 5 patterns
        - *Goal*: Create YAML schemas for SMA Crossover, Momentum+Value, Quality Score, Reversal, Breakout
        - *Details*: Write complete YAML schema for each pattern with all required fields and parameters
        - *Requirements*: Top 5 pattern schema requirements
    - [x] 16.3. Document schema in src/config/strategy_schema.yaml
        - *Goal*: Create central schema definition file
        - *Details*: Combine all 5 schemas into single YAML file with clear structure
        - *Requirements*: Schema definition file creation

- [ ] 17. **Pattern Coverage Testing**
    - [x] 17.1. RED: Write `test_top5_pattern_coverage()` test
        - *Goal*: Test 5 patterns cover ≥60% of Factor Graph successes
        - *Details*: Load Factor Graph results, map to patterns, calculate coverage, assert ≥ 60%
        - *Requirements*: Pattern coverage testing requirements
    - [x] 17.2. GREEN: Implement pattern matching logic
        - *Goal*: Classify Factor Graph strategies into 5 patterns
        - *Details*: Create pattern matcher that identifies which of 5 patterns a strategy follows
        - *Requirements*: Pattern identification specification

### Days 11-14: YAML Schema + Factory

- [x] 18. **Implement StrategyFactory**
    - [x] 18.1. RED: Write `test_yaml_config_parsing()` test
        - *Goal*: Failing test for YAML → StrategyConfig parsing
        - *Details*: Test factory.parse_config(yaml_str) returns StrategyConfig with name, type, fields, parameters, logic
        - *Requirements*: Day 11-14 factory requirements
    - [x] 18.2. GREEN: Implement parse_config() method
        - *Goal*: Parse YAML string into StrategyConfig dataclass
        - *Details*: Use yaml.safe_load(), validate schema, extract fields/parameters/logic, validate fields with Layer 1 manifest
        - *Requirements*: YAML config parsing specification
    - [x] 18.3. Define StrategyConfig data structure
        - *Goal*: Create StrategyConfig and FieldMapping dataclasses
        - *Details*: StrategyConfig with name/type/fields/parameters/logic/constraints, FieldMapping with canonical_name/alias/usage
        - *Requirements*: Config data model specification

- [x] 19. **Implement Config Execution**
    - [x] 19.1. RED: Write `test_factory_execution()` test
        - *Goal*: Test factory.create_strategy(config) creates executable strategy
        - *Details*: Verify strategy object has backtest() method, can be executed
        - *Requirements*: Factory execution requirements
    - [x] 19.2. GREEN: Implement create_strategy() method
        - *Goal*: Convert StrategyConfig to executable Strategy object
        - *Details*: Build strategy from config, set up field mappings, parameters, entry/exit logic
        - *Requirements*: Strategy creation specification
    - [x] 19.3. Implement execute() method
        - *Goal*: Run strategy backtest
        - *Details*: Execute strategy.backtest() with finlab data, return BacktestResult with metrics
        - *Requirements*: Strategy execution specification

- [x] 20. **Field Validation in Configs**
    - [x] 20.1. RED: Write `test_invalid_field_rejection()` test
        - *Goal*: Test configs with invalid fields are rejected
        - *Details*: Config with 'price:成交量' should raise FieldValidationError with suggestion 'price:成交金額'
        - *Requirements*: Layer 3 field validation requirements
    - [x] 20.2. GREEN: Integrate Layer 1+2 validation
        - *Goal*: Validate all fields in YAML config against manifest
        - *Details*: For each field in required_fields, call manifest.validate_field(), raise error if invalid
        - *Requirements*: Config field validation integration
    - [x] 20.3. Add schema validation
        - *Goal*: Validate YAML structure matches expected schema
        - *Details*: Check required keys exist (name, type, required_fields, parameters, logic), validate data types
        - *Requirements*: Schema validation specification

- [x] 21. **Create Example Configs**
    - [x] 21.1. Write 5 example YAML configs
        - *Goal*: Create executable configs for top 5 patterns
        - *Details*: Write examples/configs/sma_crossover.yaml, momentum_value.yaml, quality_score.yaml, reversal.yaml, breakout.yaml
        - *Requirements*: Example config creation
    - [x] 21.2. Test all 5 examples execute successfully
        - *Goal*: Verify all examples parse and run without errors
        - *Details*: For each config, test parsing, strategy creation, execution, verify generates trading signals
        - *Requirements*: All 5 configs executable requirement
    - [x] 21.3. Document config format
        - *Goal*: Create config documentation
        - *Details*: Write docs/CONFIG_FORMAT.md explaining YAML schema, field usage, examples
        - *Requirements*: Documentation requirements

- [ ] 22. **Layer 3 Testing**
    - [x] 22.1. Run full Layer 3 test suite
        - *Goal*: Achieve ≥90% code coverage for Layer 3
        - *Details*: Run `pytest tests/test_config_executor.py --cov=src/execution --cov-report=term-missing`
        - *Requirements*: 90% code coverage requirement
    - [x] 22.2. Verify 0% field errors in configs
        - *Goal*: Ensure all example configs use valid fields
        - *Details*: Parse all configs, validate fields, ensure no field validation errors
        - *Requirements*: 0% field error rate maintenance

### Days 15-18: LLM → Config Generation (DECISION GATE 2)

- [x] 23. **Implement Two-Stage Prompting**
    - [x] 23.1. Create field selection prompt (Stage 1)
        - *Goal*: Design prompt for LLM to select fields from manifest
        - *Details*: Create STAGE1_PROMPT_TEMPLATE with available_fields list, guidelines, JSON output format
        - *Requirements*: Two-stage prompting specification
    - [x] 23.2. Create config generation prompt (Stage 2)
        - *Goal*: Design prompt for LLM to generate YAML config
        - *Details*: Create STAGE2_PROMPT_TEMPLATE with selected_fields, YAML schema, examples
        - *Requirements*: Config generation prompting
    - [x] 23.3. Implement prompt formatting functions
        - *Goal*: Create generate_field_selection_prompt() and generate_config_creation_prompt()
        - *Details*: Format prompts with available_fields and strategy_type parameters
        - *Requirements*: Prompt template implementation

- [x] 24. **Integrate Two-Stage Prompts with LLM**
    - [x] 24.1. Modify LLM strategy generation to use two-stage prompts
        - *Goal*: Replace direct code generation with two-stage config generation
        - *Details*: Stage 1: LLM selects fields → Stage 2: LLM generates YAML config using selected fields
        - *Requirements*: Two-stage LLM integration
    - [x] 24.2. Add YAML validation after generation
        - *Goal*: Validate LLM-generated YAML before execution
        - *Details*: Parse YAML with yaml.safe_load(), validate schema, validate fields with manifest, raise errors for invalid configs
        - *Requirements*: YAML validation after generation
    - [x] 24.3. Implement error feedback loop
        - *Goal*: If YAML invalid, provide error feedback to LLM
        - *Details*: Capture validation errors, format as feedback, allow LLM to retry config generation
        - *Requirements*: Error feedback mechanism

- [x] 25. **Run Day 18 Checkpoint Test**
    - [x] 25.1. RED: Write `test_20iteration_config_mode()` test
        - *Goal*: Test 20-iteration validation in config mode
        - *Details*: Run 20 iterations with LLM generating YAML configs, track success_rate and yaml_parse_success_rate
        - *Requirements*: Day 18 checkpoint requirements
    - [x] 25.2. Execute 20-iteration config test
        - *Goal*: Run test and collect results
        - *Details*: LLM generates 20 YAML configs, parse and execute each, record successes/failures
        - *Requirements*: Decision Gate 2 testing
    - [x] 25.3. Analyze Day 18 results
        - *Goal*: Evaluate success rate improvement
        - *Details*: Extract success_rate, yaml_parse_success_rate, verify success_rate ≥ 40%, yaml_parse_success_rate = 100%
        - *Requirements*: Day 18 decision criteria

- [x] 26. **Make Day 18 PASS/FAIL Decision**
    - [x] 26.1. Diagnose issues if success_rate < 40%
        - *Goal*: Identify root causes of low success rate
        - *Details*: Analyze failure types: YAML parse errors, field validation errors, execution errors, logic errors
        - *Requirements*: Day 18 diagnostic requirements
    - [x] 26.2. Determine expansion path
        - *Goal*: Decide next steps based on results
        - *Details*: If 40-60%: add patterns 6-10. If <40%: debug prompts. If >60%: accelerate to patterns 11-15
        - *Requirements*: Iterative expansion decision logic
    - [x] 26.3. Document Day 18 checkpoint
        - *Goal*: Create checkpoint report
        - *Details*: Record metrics, decisions, next steps in docs/DAY18_CHECKPOINT_REPORT.md
        - *Requirements*: Evidence documentation requirements

### Days 19-21: Iterative Expansion

- [ ] 27. **Expand Strategy Pattern Library**
    - [x] 27.1. Add patterns 6-10 (if success_rate 40-60%)
        - *Goal*: Expand pattern library with 5 additional patterns
        - *Details*: Identify patterns 6-10 from Factor Graph successes, create YAML schemas, add to strategy_schema.yaml
        - *Requirements*: Iterative expansion requirements
    - [x] 27.2. Debug prompts (if success_rate <40%)
        - *Goal*: Improve two-stage prompts to increase success rate
        - *Details*: Analyze failure patterns, refine Stage 1/2 prompts, add more examples, improve guidelines
        - *Requirements*: Prompt debugging requirements
    - [x] 27.3. Accelerate to patterns 11-15 (if success_rate >60%)
        - *Goal*: Fast-track pattern expansion
        - *Details*: Add 10 more patterns rapidly, test in parallel, prioritize coverage expansion
        - *Requirements*: Accelerated expansion path

- [x] 28. **Final Validation (Day 21)**
    - [x] 28.1. Run final 20-iteration test
        - *Goal*: Measure final success rate with all layers
        - *Details*: Execute 20-iteration test with full Layer 1+2+3, record final metrics
        - *Requirements*: Day 21 final validation
    - [x] 28.2. Verify target success rate
        - *Goal*: Check if 70-85% success rate achieved
        - *Details*: Extract final success_rate, compare against target (70-85% stretch, 40-60% realistic)
        - *Requirements*: Final success rate target
    - [x] 28.3. Confirm 0% field error rate
        - *Goal*: Ensure field errors remain at 0%
        - *Details*: Verify field_error_rate = 0% in final test results
        - *Requirements*: 0% field error rate maintenance

- [x] 29. **Final Documentation**
    - [x] 29.1. Create Layer 3 configuration spec
        - *Goal*: Document configuration architecture
        - *Details*: Write docs/LAYER3_CONFIG_SPEC.md with YAML schema, usage guide, examples
        - *Requirements*: Layer 3 documentation requirement
    - [x] 29.2. Update steering documentation
        - *Goal*: Mark project complete in IMPLEMENTATION_STATUS.md
        - *Details*: Update status, record final metrics, document achievements
        - *Requirements*: Final steering update
    - [x] 29.3. Create final completion report
        - *Goal*: Comprehensive project summary
        - *Details*: Write docs/THREE_LAYERED_DEFENSE_COMPLETION_REPORT.md with all metrics, lessons learned, recommendations
        - *Requirements*: Completion documentation

## Task Dependencies

### Detailed Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 1: Days 1-7                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Day 1-2: Field Discovery                                       │
│  ┌─────┐                                                        │
│  │ T1  │ ──┬──> T2.1 (RED test)                                │
│  └─────┘   │                                                     │
│            ├──> T2.2 (GREEN impl) ──> T2.3 (REFACTOR)          │
│            │                                                     │
│            └──> T3 (Validation) ───────────────┐                │
│                                                 │                │
│  Day 3-4: Layer 1 Manifest                     ├─> Day 7 Gate   │
│  ┌─────┐   ┌─────┐   ┌─────┐                 │                │
│  │ T4  │   │ T5  │   │ T6  │  (Parallel)     │                │
│  └─────┘   └─────┘   └─────┘                 │                │
│     │         │         │                      │                │
│     └────┬────┴────┬────┘                     │                │
│          │         │                           │                │
│          v         v                           │                │
│        T7.1     T7.2                          │                │
│          └────┬────┘                           │                │
│               v                                │                │
│             T7.3 ─────────────────────────────┤                │
│                                                │                │
│  Day 5-6: Layer 2 Validator                   │                │
│  ┌─────┐   ┌─────┐   ┌─────┐                 │                │
│  │ T8  │   │ T9  │   │ T10 │  (Parallel)     │                │
│  └─────┘   └─────┘   └─────┘                 │                │
│     │         │         │                      │                │
│     └────┬────┴────┬────┘                     │                │
│          │         │                           │                │
│          v         v                           │                │
│        T11.1    T11.2 ────────────────────────┤                │
│                                                │                │
│  Day 7: Checkpoint                             │                │
│  ┌─────────────────┐                           │                │
│  │ T12 ──> T13     │ <─────────────────────────┘                │
│  └─────────────────┘                                            │
│         │                                                        │
│         v                                                        │
│    [DECISION GATE 1]                                            │
│    ├─> PASS: Continue to Phase 2                                │
│    ├─> FAIL (field_error > 0%): ROLLBACK                       │
│    └─> FAIL (success < 25%): DEBUG                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2: Days 8-21                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Day 8-10: Pattern Selection                                    │
│  ┌─────────────────┐                                            │
│  │ T15.1 ┬ T15.2   │ (Parallel)                                │
│  │       └ T15.3   │                                            │
│  └─────────────────┘                                            │
│         │                                                        │
│         v                                                        │
│       T16 ──> T17                                               │
│                │                                                 │
│  Day 11-14: YAML Schema + Factory                              │
│  ┌─────┐   ┌─────┐   ┌─────┐                                  │
│  │ T18 │   │ T19 │   │ T20 │  (Tests parallel, impl sequential)│
│  └─────┘   └─────┘   └─────┘                                  │
│     │         │         │                                       │
│     └────┬────┴────┬────┘                                       │
│          v         v                                            │
│        T21 ──> T22 ────────────┐                               │
│                                 │                                │
│  Day 15-18: LLM Integration     │                               │
│  ┌─────────────────┐            ├─> Day 18 Gate                │
│  │ T23 ──> T24     │ ───────────┤                               │
│  └─────────────────┘            │                                │
│         │                        │                                │
│         v                        │                                │
│  ┌─────────────────┐            │                                │
│  │ T25 ──> T26     │ ───────────┘                               │
│  └─────────────────┘                                            │
│         │                                                        │
│         v                                                        │
│    [DECISION GATE 2]                                            │
│    ├─> 40-60%: T27.1 (Add patterns 6-10)                       │
│    ├─> <40%:   T27.2 (Debug prompts)                           │
│    └─> >60%:   T27.3 (Accelerate to 11-15)                     │
│                                                                  │
│  Day 19-21: Expansion                                           │
│  ┌─────────────────┐                                            │
│  │ T27 ──> T28     │                                            │
│  └─────────────────┘                                            │
│         │                                                        │
│         v                                                        │
│       T29 (Final documentation)                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Sequential Dependencies (Must Complete Before)

| Task | Blocks | Reason |
|------|--------|--------|
| T1 (Field Discovery) | T4 (Manifest) | Manifest requires field metadata from discovery |
| T2 (Discovery Tests) | T3 (Validation) | Must test before validating field cache |
| T7 (Layer 1 Tests) | T8 (Layer 2) | Layer 2 depends on Layer 1 manifest |
| T11 (Layer 2 Tests) | T12 (Checkpoint Prep) | Checkpoint requires completed validation |
| T13 (Day 7 Test) | T14 (Documentation) | Documentation records checkpoint results |
| T14 (Day 7 PASS) | T15 (Pattern Selection) | Gate 1 decision blocks Phase 2 |
| T17 (Pattern Coverage) | T18 (Factory) | Factory needs pattern definitions |
| T22 (Layer 3 Tests) | T23 (Two-Stage Prompts) | Prompts need working factory |
| T24 (LLM Integration) | T25 (Day 18 Test) | Test requires integrated LLM |
| T26 (Day 18 Decision) | T27 (Expansion) | Decision determines expansion strategy |
| T28 (Final Test) | T29 (Documentation) | Final docs require test results |

### Parallel Execution Opportunities (Time Savings)

#### Days 1-2: Field Discovery
- **Parallel Group 1**:
  - Task 1.2 (Data structure design) + Task 1.3 (Cache implementation)
  - **Time Savings**: 2 hours (from 8h sequential to 6h parallel)
  - **Resource Requirement**: 1 developer focusing on design, 1 on implementation

#### Days 3-4: Layer 1 Tests (TDD RED Phase)
- **Parallel Group 2**:
  - Task 4.1 (test_alias_resolution) + Task 5.1 (test_field_metadata) + Task 6.1 (test_field_validation)
  - **Time Savings**: 4 hours (from 6h sequential to 2h parallel)
  - **Resource Requirement**: 3 developers or 1 developer writing all tests simultaneously

#### Days 5-6: Layer 2 Tests (TDD RED Phase)
- **Parallel Group 3**:
  - Task 8.1 (test_invalid_field_detection) + Task 9.1 (test_autocorrection) + Task 10.1 (test_integration_with_manifest)
  - **Time Savings**: 4 hours (from 6h sequential to 2h parallel)
  - **Resource Requirement**: 3 developers or batch test writing

#### Days 8-10: Pattern Analysis
- **Parallel Group 4**:
  - Task 15.1 (Review Factor Graph) + Task 15.2 (Document patterns) + Task 15.3 (Coverage analysis)
  - **Time Savings**: 8 hours (from 12h sequential to 4h parallel)
  - **Resource Requirement**: 3 analysts working on different pattern categories

#### Days 11-14: Layer 3 Tests (TDD RED Phase)
- **Parallel Group 5**:
  - Task 18.1 (test_yaml_config_parsing) + Task 19.1 (test_factory_execution) + Task 20.1 (test_invalid_field_rejection)
  - **Time Savings**: 4 hours (from 6h sequential to 2h parallel)
  - **Resource Requirement**: 3 developers or batch test writing

#### Days 11-14: Example Configs
- **Parallel Group 6**:
  - Task 21.1 (5 YAML configs): sma_crossover.yaml, momentum_value.yaml, quality_score.yaml, reversal.yaml, breakout.yaml
  - **Time Savings**: 6 hours (from 10h sequential to 4h parallel)
  - **Resource Requirement**: 5 developers each creating 1 config

**Total Potential Time Savings**: 28 hours (≈3.5 days)
**Realistic Savings (with 1-2 developers)**: 12-18 hours (≈1.5-2 days)

### Critical Path Analysis

**Longest Dependency Chain** (Cannot be Parallelized):
```
T1 (8h) → T2 (6h) → T3 (2h) → T4 (6h) → T7 (4h) → T8 (6h) →
T11 (4h) → T12 (4h) → T13 (6h) → T14 (2h) → [Gate 1] →
T15 (8h) → T16 (8h) → T17 (8h) → T18 (8h) → T19 (8h) →
T20 (8h) → T21 (8h) → T22 (4h) → T23 (8h) → T24 (8h) →
T25 (8h) → T26 (8h) → [Gate 2] → T27 (8h) → T28 (8h) → T29 (8h)
```

**Critical Path Total**: 160 hours (20 days × 8 hours)
**With Parallelization**: 142-148 hours (17.75-18.5 days)
**Risk Buffer**: 21 days planned (allows 2-3 days slack)

### Bottleneck Identification

**Bottleneck 1: Decision Gate 1 (Day 7)**
- **Impact**: Blocks all Phase 2 tasks (15-29)
- **Risk**: If success_rate < 25%, could delay project 2-3 days for debugging
- **Mitigation**: Parallel implementation of Layer 1+2 (Days 3-6), early testing

**Bottleneck 2: Pattern Selection (Days 8-10)**
- **Impact**: Blocks factory implementation and all downstream tasks
- **Risk**: If pattern coverage < 60%, delays Layer 3 by 1-2 days
- **Mitigation**: Parallel pattern analysis (Task 15.1, 15.2, 15.3)

**Bottleneck 3: Decision Gate 2 (Day 18)**
- **Impact**: Determines expansion strategy for Days 19-21
- **Risk**: If success_rate < 40%, requires prompt debugging (2-4 days)
- **Mitigation**: Two-stage prompting design, early YAML validation testing

### Resource Allocation Matrix

| Day(s) | Phase | Tasks | Parallel Tasks | Developers Needed | Bottleneck Risk |
|--------|-------|-------|----------------|-------------------|-----------------|
| 1-2    | Field Discovery | 1-3 | 1.2 + 1.3 | 1-2 | Low |
| 3-4    | Layer 1 | 4-7 | 4.1 + 5.1 + 6.1 | 1-2 | Low |
| 5-6    | Layer 2 | 8-11 | 8.1 + 9.1 + 10.1 | 1-2 | Low |
| 7      | Checkpoint 1 | 12-14 | None | 1 | **HIGH** (Gate 1) |
| 8-10   | Patterns | 15-17 | 15.1 + 15.2 + 15.3 | 1-3 | Medium |
| 11-14  | Factory | 18-22 | 18.1 + 19.1 + 20.1, 21.1 (5 configs) | 1-2 | Low |
| 15-18  | LLM Integration | 23-26 | None | 1 | **HIGH** (Gate 2) |
| 19-21  | Expansion | 27-29 | Depends on Gate 2 decision | 1-2 | Medium |

### Parallel Execution Schedule (Optimized)

**Week 1 (Days 1-7)**:
- **Day 1**: T1.1 (serial) → T1.2 ∥ T1.3 (parallel)
- **Day 2**: T2.1 → T2.2 → T2.3 → T3 (serial)
- **Day 3**: T4.1 ∥ T5.1 ∥ T6.1 (parallel RED tests) → T4.2, T5.2, T6.2 (serial GREEN)
- **Day 4**: T4.3, T5.3, T6.3 (serial REFACTOR) → T7.1 → T7.2 → T7.3
- **Day 5**: T8.1 ∥ T9.1 ∥ T10.1 (parallel RED tests) → T8.2, T9.2, T10.2 (serial GREEN)
- **Day 6**: T8.3, T9.3, T10.3 (serial REFACTOR) → T11.1 → T11.2
- **Day 7**: T12 → T13 → T14 → **[DECISION GATE 1]**

**Week 2 (Days 8-14)**:
- **Days 8-9**: T15.1 ∥ T15.2 ∥ T15.3 (parallel pattern analysis)
- **Day 10**: T16 → T17 (serial)
- **Days 11-12**: T18.1 ∥ T19.1 ∥ T20.1 (parallel RED tests) → T18.2, T19.2, T20.2 (serial GREEN)
- **Days 13-14**: T18.3, T19.3, T20.3 → T21.1 (5 configs in parallel) → T21.2 → T21.3 → T22

**Week 3 (Days 15-21)**:
- **Days 15-16**: T23 (two-stage prompts) → T24 (LLM integration)
- **Days 17-18**: T25 (Day 18 test) → T26 → **[DECISION GATE 2]**
- **Days 19-20**: T27 (expansion based on Gate 2 decision)
- **Day 21**: T28 (final validation) → T29 (final documentation)

### Decision Gates Impact

**Gate 1 (Day 7) - Three Possible Outcomes**:

| Outcome | Condition | Action | Impact on Timeline |
|---------|-----------|--------|-------------------|
| **PASS** | success_rate ≥ 25% AND field_error_rate = 0% | Proceed to Phase 2 (T15-29) | **+0 days** (on schedule) |
| **FAIL (Field Errors)** | field_error_rate > 0% | ROLLBACK to T1-7, debug manifest | **+2-3 days** (critical) |
| **FAIL (Low Success)** | success_rate < 25% AND field_error_rate = 0% | DEBUG Layer 2 validator, improve prompts | **+1-2 days** (moderate) |

**Gate 2 (Day 18) - Three Possible Outcomes**:

| Outcome | Condition | Action | Impact on Timeline |
|---------|-----------|--------|-------------------|
| **Path A: Moderate** | 40% ≤ success_rate < 60% | T27.1: Add patterns 6-10 | **+0 days** (planned) |
| **Path B: Debug** | success_rate < 40% | T27.2: Debug two-stage prompts | **+1-2 days** (moderate) |
| **Path C: Accelerate** | success_rate ≥ 60% | T27.3: Fast-track patterns 11-15 | **-1 day** (ahead of schedule) |

### Critical Path Optimization Recommendations

1. **Maximize Parallel Execution**:
   - Write all TDD RED tests in parallel (saves 12 hours across phases)
   - Create 5 example YAML configs in parallel (saves 6 hours)
   - Analyze Factor Graph patterns in parallel (saves 8 hours)

2. **Risk Mitigation for Bottlenecks**:
   - **Gate 1**: Implement comprehensive field discovery fallback (use Factor Graph list if API fails)
   - **Gate 2**: Design robust two-stage prompting with extensive examples to maximize success rate

3. **Resource Optimization**:
   - **Single Developer**: Follow serial path, leverage weekend work for buffer (25-30 days realistic)
   - **Two Developers**: Parallel execution saves 1.5-2 days (19-20 days realistic)
   - **Three+ Developers**: Maximum parallelization saves 3-3.5 days (17-18 days achievable)

## Estimated Timeline

### Phase 1: Foundation Week (Days 1-7)
- **Days 1-2**: Field Discovery (Tasks 1-3) - 16 hours
- **Days 3-4**: Layer 1 Manifest (Tasks 4-7) - 16 hours
- **Days 5-6**: Layer 2 Validator (Tasks 8-11) - 16 hours
- **Day 7**: Integration Checkpoint (Tasks 12-14) - 8 hours
- **Phase 1 Total**: 56 hours (7 days × 8 hours)

### Phase 2: Configuration Migration (Days 8-21)
- **Days 8-10**: Pattern Selection (Tasks 15-17) - 24 hours
- **Days 11-14**: YAML Schema + Factory (Tasks 18-22) - 32 hours
- **Days 15-18**: LLM Integration (Tasks 23-26) - 32 hours
- **Days 19-21**: Expansion (Tasks 27-29) - 24 hours
- **Phase 2 Total**: 112 hours (14 days × 8 hours)

### Overall Timeline
- **Total Hours**: 168 hours (21 days × 8 hours)
- **Total Days**: 21 calendar days
- **Phases**: 2 (Foundation Week + Configuration Migration)
- **Decision Gates**: 2 (Day 7, Day 18)
- **Checkpoints**: 8 (Day 2, Day 4, Day 6, Day 7, Day 10, Day 14, Day 18, Day 21)

### Risk Buffer
- **Built-in buffer**: Decision gates allow pause for debugging if needed
- **Parallel execution**: Some tasks can overlap to save time
- **Contingency**: If Day 7 fails, 2-3 days debugging before reconsidering Layer 3
- **Realistic timeline**: 21 days assumes no major blockers; could extend to 25-30 days if issues arise

---

**Task Document Status**: ✅ Complete

**Next Steps**:
1. Obtain user approval for task plan
2. Begin Day 1 implementation (finlab field discovery)
3. Follow TDD red-green-refactor cycle for all tasks
