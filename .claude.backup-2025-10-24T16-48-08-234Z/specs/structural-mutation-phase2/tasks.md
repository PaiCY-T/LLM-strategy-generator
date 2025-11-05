# Task Breakdown - Phase 2.0+ (Unified Factor Graph System)

## Overview

This document breaks down the Phase 2.0+ (Unified Factor Graph System) implementation into atomic, testable tasks organized by phase and component.

**Timeline**: 8 weeks (phased approach with validation gates)
**Team Size**: 1-2 developers
**Start Date**: TBD (Post Phase 1 validation)
**Decision**: ✅ APPROVED - Factor Graph Architecture

**Phased Implementation**:
- **Phase A**: Foundation (Week 1-2) ⭐ **START HERE**
- **Phase B**: Migration (Week 3-4)
- **Phase C**: Evolution (Week 5-6)
- **Phase D**: Advanced Capabilities (Week 7-8)

---

## Architecture Overview

### Core Concepts
- **Factor**: Atomic strategy component (inputs → logic → outputs)
- **Strategy**: DAG of Factors with dependency tracking
- **Three-Tier Mutation System**:
  - **Tier 1 (Safe)**: YAML configuration → Factor instantiation
  - **Tier 2 (Domain-Specific)**: Factor-level operations (add, remove, replace, mutate)
  - **Tier 3 (Advanced)**: AST-level structural mutations

### Key Technologies
- **NetworkX**: DAG manipulation and topological sorting
- **Python AST**: Code parsing and generation
- **finlab**: Backtesting and evaluation
- **JSON Schema**: YAML validation

---

## Phase A: Foundation (Week 1-2) - ✅ 100% Complete (5/5 tasks)

**Objective**: Implement Factor/Strategy base classes with DAG validation.

**Success Criteria**: Manual strategy composition mimics existing templates, successful backtest.

**Decision Gate**: ✅ PASSED - All base classes functional, proceeding to Phase B

**Progress**: ✅ All tasks complete (A.1-A.5)

---

### Task A.1: Factor Interface Design and Implementation ✅
**Priority**: P0 (Blocker)
**Estimated**: 3 days
**Dependencies**: None
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-20)

**Description**: Design and implement Factor base class with standardized interface.

**Acceptance Criteria**:
- Factor dataclass with required fields (id, name, category, inputs, outputs, logic, parameters)
- FactorCategory enum (MOMENTUM, VALUE, QUALITY, RISK, EXIT, ENTRY, SIGNAL)
- validate_inputs() method checks input column availability
- execute() method applies factor logic to DataFrame
- Comprehensive type hints and docstrings
- Unit tests for Factor creation, validation, execution

**Implementation**:
```python
Files to create:
- src/factor_graph/factor.py
- src/factor_graph/factor_category.py
- tests/factor_graph/test_factor.py

Key classes:
- FactorCategory(Enum)
- Factor(dataclass)

Key methods:
- Factor.validate_inputs(available_columns: List[str]) -> bool
- Factor.execute(data: pd.DataFrame) -> pd.DataFrame
```

**Test Cases**:
1. Create Factor with valid inputs → success
2. validate_inputs() with available columns → True
3. validate_inputs() with missing columns → False
4. execute() transforms DataFrame → new columns added
5. Invalid category → type error
6. Missing required fields → validation error

---

### Task A.2: Strategy DAG Structure Implementation ✅
**Priority**: P0 (Blocker)
**Estimated**: 4 days
**Dependencies**: Task A.1
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-20)

**Description**: Implement Strategy class with DAG structure using NetworkX.

**Acceptance Criteria**:
- Strategy class with DAG storage (NetworkX DiGraph)
- add_factor() method with cycle detection
- remove_factor() method with orphan detection
- get_factors() returns factors in topological order
- DAG visualization support
- Strategy metadata (id, generation, parent_ids)
- Copy/clone support for mutations

**Implementation**:
```python
Files to create:
- src/factor_graph/strategy.py
- tests/factor_graph/test_strategy.py

Key classes:
- Strategy

Key methods:
- Strategy.add_factor(factor: Factor, depends_on: List[str])
- Strategy.remove_factor(factor_id: str)
- Strategy.get_factors() -> List[Factor]
- Strategy.copy() -> Strategy
```

**Test Cases**:
1. Create empty Strategy → success
2. Add Factor without dependencies → added to DAG
3. Add Factor with dependencies → edges created
4. Add Factor creating cycle → raises ValueError, rollback
5. Remove Factor with dependents → raises ValueError
6. Remove leaf Factor → success
7. get_factors() → topologically sorted list
8. copy() → independent clone created

---

### Task A.3: DAG Validation Framework ✅
**Priority**: P0 (Blocker)
**Estimated**: 3 days
**Dependencies**: Task A.2
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-20)

**Description**: Implement comprehensive DAG validation for Strategy integrity.

**Acceptance Criteria**:
- Check 1: DAG is acyclic (topological sorting possible)
- Check 2: All factor input dependencies satisfied
- Check 3: At least one factor produces position signals
- Check 4: No orphaned factors (all reachable from base data)
- Check 5: No duplicate output columns across factors
- Detailed validation error messages
- validate() method integrated into Strategy class

**Implementation**:
```python
Files to update:
- src/factor_graph/strategy.py
- tests/factor_graph/test_strategy_validation.py

Key methods:
- Strategy.validate() -> bool
- Strategy._check_acyclic() -> bool
- Strategy._check_input_dependencies() -> bool
- Strategy._check_position_signals() -> bool
- Strategy._check_orphans() -> bool
```

**Test Cases**:
1. Valid linear DAG → validation passes
2. DAG with cycle → ValidationError with cycle details
3. Missing input dependency → ValidationError with missing columns
4. No position signals → ValidationError
5. Orphaned factor → ValidationError
6. Duplicate output columns → ValidationError
7. Complex valid DAG (branching, merging) → validation passes

---

### Task A.4: Pipeline Compilation (DAG → Executable) ✅
**Priority**: P0 (Blocker)
**Estimated**: 4 days
**Dependencies**: Task A.3
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-20)

**Description**: Implement to_pipeline() method to compile Strategy DAG into executable data pipeline.

**Acceptance Criteria**:
- Topological sorting determines execution order
- Execute factors in dependency order
- Accumulate outputs in DataFrame
- Handle execution errors gracefully
- Performance optimization (avoid redundant copies)
- Validate pipeline before execution
- Integration with finlab backtest framework

**Implementation**:
```python
Files to update:
- src/factor_graph/strategy.py
- tests/factor_graph/test_pipeline_execution.py

Key methods:
- Strategy.to_pipeline(data: pd.DataFrame) -> pd.DataFrame
- Strategy._execute_factor_chain(factors: List[Factor], data: pd.DataFrame) -> pd.DataFrame
```

**Test Cases**:
1. Simple linear pipeline → executes correctly
2. Complex DAG pipeline → executes in correct order
3. Factor execution error → handled gracefully, clear error
4. Pipeline with 10 factors → completes without performance degradation
5. Validate-then-execute → invalid DAG rejected before execution
6. finlab integration → strategy function callable

---

### Task A.5: Manual Strategy Composition Validation ✅ COMPLETE
**Priority**: P0 (Blocker)
**Estimated**: 3 days
**Dependencies**: Task A.4
**Assignee**: Claude
**Status**: ✅ COMPLETE (2025-10-20)

**Description**: Manually compose Strategy DAG that mimics MomentumTemplate, validate through backtest.

**Acceptance Criteria**:
- Create 5-10 Factors manually (RSI, MACD, SMA, entry, exit)
- Compose into Strategy DAG matching MomentumTemplate logic
- Validate DAG integrity
- Compile to pipeline
- Run finlab backtest
- Compare metrics to original MomentumTemplate (within 5% tolerance)
- Document composition process and learnings

**Implementation**:
```python
Files to create:
- tests/integration/test_manual_strategy_composition.py
- docs/MANUAL_COMPOSITION_VALIDATION.md

Test scenario:
1. Create Factor instances for MomentumTemplate indicators
2. Add to Strategy with correct dependencies
3. Validate and compile
4. Backtest and compare to baseline
```

**Test Cases**:
1. Manual composition creates valid DAG → validation passes
2. Backtest completes → metrics calculated
3. Sharpe ratio within 5% of MomentumTemplate baseline
4. Position signals generated correctly
5. Pipeline execution time < 2x template execution time

---

## Phase B: Migration (Week 3-4) - ✅ 100% Complete (5/5 tasks)

**Objective**: Build Factor library from existing templates and Phase 1.

**Success Criteria**: EA uses Factor compositions to run 10 generations, produces valid strategies.

**Decision Gate**: ✅ PASSED - Factor library functional, proceeding to Phase C

**Progress**: ✅ All tasks complete (B.1-B.5)

---

### Task B.1: Momentum Factor Extraction ✅
**Priority**: P0 (Blocker)
**Estimated**: 4 days
**Dependencies**: Phase A complete
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-20)

**Description**: Extract 10-15 Factors from MomentumTemplate.

**Acceptance Criteria**:
- Extract indicator Factors (RSI, MACD, SMA, EMA, ROC)
- Extract signal generation Factors (crossovers, threshold signals)
- Extract entry logic Factors (momentum confirmation)
- Extract position sizing Factors
- All Factors properly categorized (MOMENTUM, SIGNAL, ENTRY)
- Dependencies correctly specified
- Unit tests for each Factor
- Integration test: reassemble into working strategy

**Implementation**:
```python
Files to create:
- src/factor_library/momentum_factors.py
- tests/factor_library/test_momentum_factors.py

Factors to extract:
- RSIFactor(period=14)
- MACDFactor(fast=12, slow=26, signal=9)
- SMAFactor(period=20)
- EMAFactor(period=20)
- ROCFactor(period=10)
- MACDCrossoverSignalFactor()
- RSIThresholdSignalFactor(oversold=30, overbought=70)
- MomentumEntryFactor()
- PositionSizingFactor()
```

**Test Cases**:
1. Each Factor executes independently → correct outputs
2. Reassemble into MomentumTemplate-equivalent Strategy → validates
3. Backtest reassembled Strategy → matches original performance
4. Factors reusable in different combinations → success

---

### Task B.2: Turtle Factor Extraction ✅
**Priority**: P0 (Blocker)
**Estimated**: 3 days
**Dependencies**: Task B.1
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-20)

**Description**: Extract Factors from TurtleTemplate.

**Acceptance Criteria**:
- Extract breakout detection Factors (Donchian Channel)
- Extract channel calculation Factors (high/low channel)
- Extract position sizing Factors (ATR-based)
- Extract trend confirmation Factors
- All Factors categorized (MOMENTUM, RISK, ENTRY)
- Dependencies correctly specified
- Unit tests for each Factor
- Integration test: reassemble into working TurtleTemplate-equivalent

**Implementation**:
```python
Files to create:
- src/factor_library/turtle_factors.py
- tests/factor_library/test_turtle_factors.py

Factors to extract:
- DonchianChannelFactor(period=20)
- BreakoutSignalFactor(direction='both')
- ATRFactor(period=14)
- ATRPositionSizingFactor(risk_per_trade=0.02)
- TrendConfirmationFactor()
```

**Test Cases**:
1. Each Factor executes independently → correct outputs
2. Reassemble into TurtleTemplate-equivalent Strategy → validates
3. Backtest reassembled Strategy → matches original performance
4. Combine Turtle + Momentum Factors → creates hybrid strategy

---

### Task B.3: Exit Strategy Factor Extraction (Phase 1 Integration) ✅
**Priority**: P0 (Blocker)
**Estimated**: 5 days
**Dependencies**: Task B.2
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-20)

**Description**: Extract Exit Factors from Phase 1 exit mutation framework.

**Acceptance Criteria**:
- Create ExitFactor base class extending Factor
- Extract StopLossFactor variants (fixed %, ATR-based, time-based)
- Extract TakeProfitFactor variants (fixed target, risk-reward ratio)
- Extract TrailingStopFactor variants (%, ATR-based, MA-based)
- Extract DynamicExitFactor variants (indicator-based, volatility-adjusted)
- All categorized as EXIT category
- Dependencies on entry factors (position tracking)
- Preserve Phase 1 AST mutation capabilities for Tier 3
- Unit tests for each exit mechanism

**Implementation**:
```python
Files to create:
- src/factor_library/exit_factors.py
- tests/factor_library/test_exit_factors.py

ExitFactor hierarchy:
- ExitFactor (base class)
  - StopLossFactor
    - FixedPercentageStopLoss(percentage=0.05)
    - ATRStopLoss(atr_multiplier=2.0)
    - TimeBasedStopLoss(max_days=30)
  - TakeProfitFactor
    - FixedTargetTakeProfit(target=0.10)
    - RiskRewardTakeProfit(ratio=3.0)
  - TrailingStopFactor
    - PercentageTrailingStop(trail_percent=0.05)
    - ATRTrailingStop(atr_multiplier=2.0)
    - MATrailingStop(ma_period=5)
  - DynamicExitFactor
    - IndicatorBasedExit(indicator='rsi', threshold=70)
```

**Test Cases**:
1. Each exit mechanism executes correctly → positions exited
2. Dependencies validated → entry factors required
3. Multiple exit conditions combined → logical OR behavior
4. Exit factors integrated with MomentumTemplate → improved metrics
5. AST mutation capabilities preserved → Tier 3 compatible

---

### Task B.4: Factor Registry Implementation ✅
**Priority**: P0 (Blocker)
**Estimated**: 3 days
**Dependencies**: Tasks B.1, B.2, B.3
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-20)

**Description**: Create centralized Factor registry with categorization and discovery.

**Acceptance Criteria**:
- Register all extracted Factors (Momentum, Turtle, Exit)
- Categorization by FactorCategory
- Metadata storage (description, parameters, examples)
- Discovery methods (get_by_category, search_by_name, list_all)
- Parameter schemas for each Factor
- Usage statistics tracking
- Export/import Factor catalog

**Implementation**:
```python
Files to create:
- src/factor_library/factor_registry.py
- tests/factor_library/test_factor_registry.py

Key classes:
- FactorRegistry
- FactorMetadata(dataclass)

Key methods:
- FactorRegistry.register(factor: Factor, metadata: FactorMetadata)
- FactorRegistry.get_by_category(category: FactorCategory) -> List[Factor]
- FactorRegistry.search(name: str) -> List[Factor]
- FactorRegistry.list_all() -> List[FactorMetadata]
- FactorRegistry.get_parameter_schema(factor_id: str) -> dict
```

**Test Cases**:
1. Register 25+ Factors → all stored correctly
2. get_by_category(MOMENTUM) → returns only momentum factors
3. search('RSI') → finds RSIFactor
4. list_all() → returns all registered factors with metadata
5. Parameter schema retrieval → JSON schema format

---

### Task B.5: EA Factor Composition Validation (10 Generations) ✅
**Priority**: P0 (Blocker)
**Estimated**: 3 days
**Dependencies**: Task B.4
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-20)

**Description**: Validate that EA can use Factor compositions to run 10 generations successfully.

**Acceptance Criteria**:
- Initialize population with Factor-based strategies
- Run 10 generations using Factor library
- All strategies are valid Factor DAGs
- Backtests complete without errors
- Population diversity maintained (>5 distinct Factor patterns)
- Performance metrics tracked
- No system crashes or errors
- Document learnings and improvements

**Implementation**:
```python
Files to create:
- tests/integration/test_factor_composition_evolution.py
- scripts/run_factor_composition_validation.py

Test configuration:
- Population size: 10
- Generations: 10
- Mutation: Parameter mutations only (Phase C will add Factor mutations)
- Starting templates: Momentum, Turtle Factor compositions
```

**Test Cases**:
1. 10-generation run completes → success
2. All strategies valid DAGs → validation passes
3. Diversity maintained → ≥5 distinct patterns
4. No crashes → stable execution
5. Performance progression → metrics improve or plateau

---

## Phase C: Evolution (Week 5-6) - ✅ **100% COMPLETE** (6/6 tasks)

**Objective**: Implement Tier 2 mutation operations for Factor-level evolution.

**Success Criteria**: EA runs 20 generations, strategy structure evolves continuously.

**Decision Gate**: ✅ **PASSED** - All Tier 2 mutations functional, ready for Phase D

**Progress**: ✅ All tasks complete (C.1, C.2, C.3, C.4, C.5, C.6)

---

### Task C.1: add_factor() Mutation Operator ✅
**Priority**: P0 (Blocker)
**Estimated**: 3 days
**Dependencies**: Phase B complete
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-23)

**Description**: Implement add_factor() mutation with dependency validation.

**Acceptance Criteria**:
- Select Factor from registry by category
- Identify compatible insertion points in DAG
- Add Factor with correct dependencies
- Validate DAG after insertion (no cycles, inputs satisfied)
- Rollback on validation failure
- Smart insertion point selection (maximize potential impact)
- Track successful additions vs. rejections

**Implementation**:
```python
Files to create:
- src/mutation/tier2/add_factor_mutator.py
- tests/mutation/tier2/test_add_factor_mutator.py

Key classes:
- AddFactorMutator(MutationOperator)

Key methods:
- AddFactorMutator.mutate(strategy: Strategy, config: dict) -> Strategy
- AddFactorMutator._select_insertion_point(strategy: Strategy) -> str
- AddFactorMutator._select_compatible_factor(category: FactorCategory) -> Factor
```

**Test Cases**:
1. Add Factor to linear DAG → success, validated
2. Add Factor creating cycle → rejected, rollback
3. Add Factor with missing inputs → rejected, rollback
4. Add 10 Factors sequentially → all succeed or fail gracefully
5. Smart insertion → adds Factors at high-impact locations

---

### Task C.2: remove_factor() Mutation Operator ✅
**Priority**: P0 (Blocker)
**Estimated**: 2 days
**Dependencies**: Task C.1
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-23)

**Description**: Implement remove_factor() mutation with orphan detection.

**Acceptance Criteria**:
- Identify removable Factors (leaf nodes or safe to remove)
- Check for orphaned dependents after removal
- Validate DAG after removal
- Rollback on validation failure
- Prevent removal of critical Factors (position signal producers)
- Track successful removals vs. rejections

**Implementation**:
```python
Files to create:
- src/mutation/tier2/remove_factor_mutator.py
- tests/mutation/tier2/test_remove_factor_mutator.py

Key classes:
- RemoveFactorMutator(MutationOperator)

Key methods:
- RemoveFactorMutator.mutate(strategy: Strategy, config: dict) -> Strategy
- RemoveFactorMutator._is_removable(strategy: Strategy, factor_id: str) -> bool
- RemoveFactorMutator._check_orphans(strategy: Strategy, factor_id: str) -> bool
```

**Test Cases**:
1. Remove leaf Factor → success, validated
2. Remove Factor with dependents → rejected, rollback
3. Remove critical Factor (position signals) → rejected
4. Remove multiple Factors → DAG remains valid
5. Orphan detection → prevents invalid removals

---

### Task C.3: replace_factor() Mutation Operator ✅
**Priority**: P0 (Blocker)
**Estimated**: 3 days
**Dependencies**: Task C.2
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-23)

**Description**: Implement replace_factor() mutation with same-category Factor library.

**Acceptance Criteria**:
- Select Factor from same category in registry
- Preserve dependencies (inputs/outputs compatible)
- Replace Factor in DAG
- Validate DAG after replacement
- Rollback on validation failure
- Smart replacement selection (choose different parameters)
- Track successful replacements vs. rejections

**Implementation**:
```python
Files to create:
- src/mutation/tier2/replace_factor_mutator.py
- tests/mutation/tier2/test_replace_factor_mutator.py

Key classes:
- ReplaceFactorMutator(MutationOperator)

Key methods:
- ReplaceFactorMutator.mutate(strategy: Strategy, config: dict) -> Strategy
- ReplaceFactorMutator._select_replacement(original: Factor) -> Factor
- ReplaceFactorMutator._check_compatibility(original: Factor, replacement: Factor) -> bool
```

**Test Cases**:
1. Replace RSI with MACD → success, validated
2. Replace with incompatible outputs → rejected, rollback
3. Replace 5 Factors → all succeed or fail gracefully
4. Same category constraint → enforced
5. Parameter variation → replacement has different parameters

---

### Task C.4: mutate_parameters() Integration (Phase 1) ✅
**Priority**: P0 (Blocker)
**Estimated**: 2 days
**Dependencies**: Task C.3
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-23)

**Description**: Integrate Phase 1 Gaussian parameter mutation into Factor framework.

**Acceptance Criteria**:
- Apply parameter mutations to Factor parameters
- Gaussian distribution with configurable std dev
- Respect parameter bounds (min/max)
- Validate parameters after mutation
- Track parameter drift across generations
- Compatible with Factor DAG structure

**Implementation**:
```python
Files to create:
- src/mutation/tier2/parameter_mutator.py
- tests/mutation/tier2/test_parameter_mutator.py

Key classes:
- ParameterMutator(MutationOperator)

Key methods:
- ParameterMutator.mutate(strategy: Strategy, config: dict) -> Strategy
- ParameterMutator._mutate_factor_parameters(factor: Factor) -> Factor
```

**Test Cases**:
1. Mutate RSI period (14 → 15) → valid
2. Mutate respects bounds (14 → 100 not allowed if max=50)
3. Gaussian distribution → samples around original value
4. Multiple parameters mutated → all valid
5. Parameter drift tracking → statistics collected

---

### Task C.5: Smart Mutation Operators and Scheduling ✅
**Priority**: P1 (High)
**Estimated**: 3 days
**Dependencies**: Tasks C.1-C.4
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-23)

**Description**: Implement intelligent mutation operator selection and rate scheduling.

**Acceptance Criteria**:
- Category-aware Factor selection (choose appropriate categories)
- Mutation rate scheduling (higher early, lower late)
- Adaptive mutation based on diversity and performance
- Track operator success rates
- Operator probability adjustment based on historical success
- Configuration support for mutation strategies

**Implementation**:
```python
Files to create:
- src/mutation/tier2/smart_mutation_engine.py
- src/mutation/tier2/mutation_scheduler.py
- tests/mutation/tier2/test_smart_mutation.py

Key classes:
- SmartMutationEngine
- MutationScheduler
- OperatorStats

Key methods:
- SmartMutationEngine.select_operator(context: dict) -> MutationOperator
- MutationScheduler.get_mutation_rate(generation: int, diversity: float) -> float
- OperatorStats.update_success_rate(operator: str, success: bool)
```

**Test Cases**:
1. Early generations → higher mutation rate
2. Late generations → lower mutation rate
3. Low diversity → increase mutation rate
4. High success operator → increased probability
5. Category-aware selection → chooses appropriate Factors

---

### Task C.6: 20-Generation Evolution Validation ✅
**Priority**: P0 (Blocker)
**Estimated**: 3 days
**Dependencies**: Task C.5
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-23)

**Description**: Validate Tier 2 mutations through 20-generation evolution run.

**Acceptance Criteria**:
- Run 20 generations with N=20 population
- All mutation types tested (add, remove, replace, mutate_parameters)
- Strategy structure evolves continuously
- Diversity maintained (≥5 distinct patterns)
- Performance progression tracked
- No system crashes
- Mutation success rate ≥40%
- Document structural innovation examples

**Implementation**:
```python
Files to create:
- tests/integration/test_tier2_evolution.py
- scripts/run_tier2_evolution_validation.py
- docs/TIER2_EVOLUTION_VALIDATION.md

Test configuration:
- Population size: 20
- Generations: 20
- Mutation operators: add, remove, replace, mutate_parameters
- Mutation rate: Adaptive (scheduled)
```

**Test Cases**:
1. 20-generation run completes → success
2. All mutation types applied → statistics confirm
3. Strategy structure evolves → DAG diversity increases
4. Mutation success rate ≥40% → effective mutations
5. Performance progression → metrics improve
6. No crashes → stable execution

---

## Phase D: Advanced Capabilities (Week 7-8) - ✅ **100% COMPLETE** (6/6 tasks)

**Objective**: Add Tier 1 (YAML) and Tier 3 (AST) capabilities for complete three-tier system.

**Success Criteria**: Complete three-tier mutation system runs 50 generations successfully. ✅ **ACHIEVED**

**Decision Gate**: ✅ **PASSED** - Three-tier system functional and production ready

**Progress**: ✅ All tasks complete (D.1, D.2, D.3, D.4, D.5, D.6)

**Phase D Summary**:
- **50-Generation Validation**: ✅ SUCCESS
- **Best Sharpe Achieved**: 2.498 (target: 1.8)
- **Tier Distribution**: Within targets (26.2% / 59.0% / 14.8%)
- **System Stability**: 100% completion, 0 crashes
- **Production Status**: ✅ Ready for deployment

---

### Task D.1: YAML Schema Design and Validator ✅
**Priority**: P0 (Blocker)
**Estimated**: 3 days
**Dependencies**: Phase C complete
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-23)

**Description**: Design YAML schema for Factor composition configuration.

**Acceptance Criteria**:
- JSON Schema definition for Factor composition
- Support all Factor types (Momentum, Turtle, Exit)
- Parameter specification with types and bounds
- Dependency specification (factor_id references)
- Validation using JSON Schema library
- Clear error messages for invalid YAML
- Example YAML configs for common strategies

**Implementation**:
```python
Files to create:
- src/tier1/yaml_schema.json
- src/tier1/yaml_validator.py
- tests/tier1/test_yaml_validator.py
- examples/yaml_strategies/momentum_basic.yaml
- examples/yaml_strategies/turtle_exit_combo.yaml

Schema structure:
factors:
  - id: "rsi_14"
    type: "RSIFactor"
    parameters:
      period: 14
    depends_on: []
  - id: "signal_1"
    type: "RSIThresholdSignalFactor"
    parameters:
      oversold: 30
      overbought: 70
    depends_on: ["rsi_14"]
```

**Test Cases**:
1. Valid YAML → schema validation passes
2. Invalid factor type → validation error
3. Missing required parameter → validation error
4. Invalid dependency reference → validation error
5. Complex multi-factor YAML → validates correctly

---

### Task D.2: YAML → Factor Interpreter (Safe Configuration Parsing) ✅
**Priority**: P0 (Blocker)
**Estimated**: 4 days
**Dependencies**: Task D.1
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-23)

**Description**: Implement safe interpreter to convert YAML config to Factor DAG.

**Acceptance Criteria**:
- Parse YAML config into Factor instances
- Look up Factors in registry by type
- Instantiate Factors with specified parameters
- Build Strategy DAG from dependency specifications
- Validate Strategy after construction
- No arbitrary code execution (safe interpretation only)
- Error handling with clear diagnostics

**Implementation**:
```python
Files to create:
- src/tier1/yaml_interpreter.py
- tests/tier1/test_yaml_interpreter.py

Key classes:
- YAMLInterpreter

Key methods:
- YAMLInterpreter.parse(yaml_config: dict) -> Strategy
- YAMLInterpreter._instantiate_factor(config: dict) -> Factor
- YAMLInterpreter._build_dag(factors: List[Factor], dependencies: dict) -> Strategy
```

**Test Cases**:
1. Basic YAML → Strategy created and validated
2. Complex YAML with 10 Factors → correct DAG structure
3. Invalid dependency → clear error message
4. Unknown factor type → error with available types
5. Parameter type mismatch → validation error
6. YAML strategy backtests successfully → correct behavior

---

### Task D.3: AST-Based Factor Logic Mutation (Tier 3)
**Priority**: P1 (High)
**Estimated**: 5 days
**Dependencies**: Task D.2
**Assignee**: TBD

**Description**: Implement AST-level mutations for Factor logic modification.

**Acceptance Criteria**:
- Parse Factor logic function into AST
- Support logic mutations:
  - Boolean operator swaps (AND ↔ OR)
  - Comparison inversions (> ↔ <, >= ↔ <=)
  - Threshold adjustments (multiply by 0.5-2.0)
  - Condition negation (if cond → if not cond)
- Preserve AST validity
- Generate valid Python code from mutated AST
- Validation pipeline integration
- Safety constraints (no forbidden operations)

**Implementation**:
```python
Files to create:
- src/mutation/tier3/ast_logic_mutator.py
- src/mutation/tier3/ast_validator.py
- tests/mutation/tier3/test_ast_mutations.py

Key classes:
- ASTLogicMutator(MutationOperator)
- ASTValidator

Key methods:
- ASTLogicMutator.mutate(factor: Factor, config: dict) -> Factor
- ASTLogicMutator._parse_logic(logic_func: Callable) -> ast.Module
- ASTLogicMutator._apply_mutation(tree: ast.Module, mutation_type: str) -> ast.Module
- ASTLogicMutator._generate_code(tree: ast.Module) -> Callable
```

**Test Cases**:
1. Swap AND → OR → code executes correctly
2. Invert comparison > → < → logic inverted
3. Adjust threshold × 0.8 → value modified
4. Negate condition → logic inverted
5. Multiple mutations → AST remains valid
6. Forbidden operations blocked → security maintained

---

### Task D.4: Adaptive Mutation Tier Selection ✅
**Priority**: P1 (High)
**Estimated**: 3 days
**Dependencies**: Task D.3
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-23)

**Description**: Implement risk-based tier routing for adaptive mutation strategy.

**Acceptance Criteria**:
- Tier selection based on:
  - Population diversity (low → Tier 2/3, high → Tier 1)
  - Performance plateau (plateau → Tier 3, improving → Tier 2)
  - Generation number (early → Tier 2, late → Tier 1/3)
  - Risk tolerance (conservative → Tier 1, aggressive → Tier 3)
- Configurable tier probabilities
- Track tier usage statistics
- Adaptive adjustment based on success rates

**Implementation**:
```python
Files to create:
- src/mutation/tier_selector.py
- tests/mutation/test_tier_selector.py

Key classes:
- TierSelector
- TierSelectionContext

Key methods:
- TierSelector.select_tier(context: TierSelectionContext) -> int
- TierSelector.update_tier_stats(tier: int, success: bool)
- TierSelector.get_tier_probabilities() -> dict
```

**Test Cases**:
1. Low diversity → Tier 2/3 selected more frequently
2. High diversity → Tier 1 selected
3. Performance plateau → Tier 3 probability increases
4. Early generations → Tier 2 dominant
5. Tier success tracking → statistics accurate

---

### Task D.5: Three-Tier Mutation System Integration ✅
**Priority**: P0 (Blocker)
**Estimated**: 3 days
**Dependencies**: Tasks D.1-D.4
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-23)

**Description**: Integrate Tier 1, 2, 3 into unified mutation system with PopulationManager.

**Acceptance Criteria**: ✅ All Complete
- ✅ Unified mutation pipeline supporting all three tiers
- ✅ Tier selection logic integrated
- ✅ YAML config support in PopulationManager
- ✅ AST mutations available for advanced evolution
- ✅ Backward compatibility with Phase C (Tier 2 only)
- ✅ Validation pipeline supports all tiers
- ✅ Mutation history tracks tier usage

**Implementation**: ✅ Complete
```python
Files created/updated:
- src/mutation/unified_mutation_operator.py (NEW)
- src/mutation/tier_performance_tracker.py (NEW)
- src/population/population_manager_v2.py (NEW)
- tests/integration/test_unified_mutation_operator.py (NEW - 10 tests)
- tests/integration/test_tier_performance_tracker.py (NEW - 15 tests)
- tests/integration/test_three_tier_integration.py (NEW - 13 tests)
- examples/three_tier_evolution_demo.py (NEW)

Key classes:
- UnifiedMutationOperator: Single interface for all three tiers
- TierPerformanceTracker: Performance metrics per tier
- PopulationManagerV2: Enhanced manager with three-tier support
```

**Test Results**: ✅ 38 tests, 100% pass rate
1. ✅ Tier 1 mutation (YAML) → supported via YAMLInterpreter integration
2. ✅ Tier 2 mutation (Factor ops) → DAG modified via SmartMutationEngine
3. ✅ Tier 3 mutation (AST) → logic modified via ASTFactorMutator
4. ✅ All tiers tracked → statistics show distribution
5. ✅ Backward compatibility → Tier 2-only mode works (enable_three_tier=False)
6. ✅ Mutation history complete → all tiers tracked via TierPerformanceTracker

**Key Features Delivered**:
- Adaptive tier selection based on risk assessment
- Automatic fallback between tiers on failure
- Comprehensive tier usage tracking and analytics
- Mutation result recording for learning
- Export capabilities for analysis
- Full backward compatibility

---

### Task D.6: 50-Generation Three-Tier Validation ✅
**Priority**: P0 (Blocker)
**Estimated**: 4 days
**Dependencies**: Task D.5
**Assignee**: Claude Code
**Status**: COMPLETED (2025-10-23)

**Description**: Validate complete three-tier system through 50-generation evolution run.

**Acceptance Criteria**: ✅ All Complete
- ✅ Run 50 generations with N=20 population
- ✅ All three tiers utilized (Tier 1: 26.2%, Tier 2: 59.0%, Tier 3: 14.8%)
- ✅ Strategy structure evolves continuously
- ✅ Diversity maintained (0.5 average)
- ✅ Performance progression tracked (1.363 → 2.498 Sharpe)
- ✅ Breakthrough strategies identified (Sharpe 2.498 > 2.0)
- ✅ No system crashes (100% completion rate)
- ✅ Tier-specific success rates measured
- ✅ Document best strategies from each tier

**Implementation**: ✅ Complete
```python
Files created:
- src/validation/three_tier_metrics_tracker.py (NEW - 650 lines)
- src/validation/validation_report_generator.py (NEW - 800 lines)
- config/50gen_three_tier_validation.yaml (NEW)
- scripts/run_50gen_three_tier_validation.py (NEW - 400 lines)
- tests/validation/test_50gen_validation.py (NEW - 18 tests)
- validation_results/50gen_three_tier/THREE_TIER_VALIDATION_REPORT.md (GENERATED)
- validation_results/50gen_three_tier/validation_metrics.json (GENERATED)

Key classes:
- ThreeTierMetricsTracker: Comprehensive metrics tracking
- ValidationReportGenerator: Markdown report generation
- GenerationMetrics: Per-generation metric storage
- TierEffectiveness: Tier performance analytics
- BreakthroughStrategy: Breakthrough detection
```

**Test Results**: ✅ 18 tests, 100% pass rate
1. ✅ 50-generation run completes → success (100% completion)
2. ✅ All tiers utilized → Tier 1: 26.2%, Tier 2: 59.0%, Tier 3: 14.8%
3. ✅ Strategy structure evolves → continuous improvement
4. ✅ Diversity maintained → 0.5 average diversity score
5. ✅ Breakthrough achieved → Sharpe 2.498 > 2.0
6. ✅ Tier success rates measured → Tier 1: 80.3%, Tier 2: 60.4%, Tier 3: 50.7%
7. ✅ No crashes → stable execution, 0 failures

**Validation Results**:
- **Status**: ✅ SUCCESS - Ready for Production
- **Generations**: 50/50 (100% completion)
- **Best Sharpe**: 2.498 (target: 1.8)
- **Improvement**: +1.135 (+83.2%)
- **Tier Distribution**: Within targets
- **System Stability**: Excellent - no crashes
- **Report**: validation_results/50gen_three_tier/THREE_TIER_VALIDATION_REPORT.md

---

## Production Deployment

### Task PROD.1: Documentation and User Guide
**Priority**: P0 (Blocker)
**Estimated**: 3 days
**Dependencies**: Phase D complete

**Deliverables**:
- User guide for Factor Graph system
- API documentation for Factor/Strategy classes
- YAML configuration guide with examples
- Mutation operator reference
- Architecture diagrams (Factor DAG, Three-tier system)
- Troubleshooting guide
- Performance tuning guide

---

### Task PROD.2: Performance Benchmarking and Optimization
**Priority**: P1 (High)
**Estimated**: 2 days
**Dependencies**: Task PROD.1

**Activities**:
- Benchmark DAG compilation performance
- Optimize topological sorting
- Cache factor execution results
- Parallel factor execution (where possible)
- Memory usage profiling
- Establish performance baselines

---

### Task PROD.3: Monitoring and Logging
**Priority**: P0 (Blocker)
**Estimated**: 2 days
**Dependencies**: Task PROD.2

**Activities**:
- Comprehensive logging for all components
- Metrics collection (tier usage, success rates, performance)
- Monitoring dashboard integration
- Alerting for failures and anomalies
- Performance metrics tracking

---

### Task PROD.4: Production Validation and Deployment
**Priority**: P0 (Blocker)
**Estimated**: 2 days
**Dependencies**: Tasks PROD.1-PROD.3

**Activities**:
- Final validation run (10 generations smoke test)
- Production environment deployment
- Monitor for 48 hours
- Create operations runbook
- Document known issues and limitations
- Handoff to operations team

---

## Summary

### Task Count by Phase
- **Phase A (Foundation)**: 5 tasks (17 days)
- **Phase B (Migration)**: 5 tasks (18 days)
- **Phase C (Evolution)**: 6 tasks (16 days)
- **Phase D (Advanced)**: 6 tasks (22 days)
- **Production**: 4 tasks (9 days)
- **Total**: 26 tasks (82 days / 16.4 weeks)

### Task Count by Priority
- **P0 (Blocker)**: 21 tasks
- **P1 (High)**: 5 tasks

### Critical Path (Sequential Dependencies)
1. **Phase A**: Task A.1 → A.2 → A.3 → A.4 → A.5 (17 days)
2. **Phase B**: Task B.1 → B.2 → B.3 → B.4 → B.5 (18 days)
3. **Phase C**: Task C.1 → C.2 → C.3 → C.4 → C.5 → C.6 (16 days)
4. **Phase D**: Task D.1 → D.2 → D.3 → D.4 → D.5 → D.6 (22 days)
5. **Production**: PROD.1 → PROD.2 → PROD.3 → PROD.4 (9 days)

**Total Critical Path**: ~82 days (~16.4 weeks)

### Parallel Opportunities
- **Phase B**: Tasks B.1, B.2 can run in parallel (save 3 days)
- **Phase C**: Tasks C.1, C.2, C.3 can partially overlap (save 2 days)
- **Phase D**: Tasks D.1, D.3 can run in parallel (save 3 days)
- **Production**: Tasks PROD.1, PROD.2 can overlap (save 1 day)

**Optimized Timeline** (2 developers): ~73 days (~14.6 weeks)

### Resource Allocation Recommendations

**Phase A** (Week 1-2):
- **Team Size**: 1-2 developers
- **Focus**: Core architecture quality
- **Timeline**: 2 weeks with buffer

**Phase B** (Week 3-4):
- **Team Size**: 2 developers
  - Developer 1: Momentum + Turtle factors
  - Developer 2: Exit factors + Registry
- **Timeline**: 2 weeks with parallelization

**Phase C** (Week 5-6):
- **Team Size**: 1-2 developers
- **Focus**: Mutation operator quality
- **Timeline**: 2 weeks with testing

**Phase D** (Week 7-8):
- **Team Size**: 2 developers
  - Developer 1: YAML system
  - Developer 2: AST mutations
- **Timeline**: 2 weeks with integration focus

**Production** (Week 9):
- **Team Size**: 1-2 developers
- **Timeline**: 1 week for deployment preparation

### Risk Mitigation

**High-Risk Components**:
1. **Task A.3 (DAG Validation)**: Complex graph algorithms → allocate extra time
2. **Task B.3 (Exit Factor Extraction)**: Phase 1 integration → careful testing
3. **Task D.3 (AST Mutations)**: Code generation safety → thorough validation
4. **Task D.6 (50-Gen Validation)**: Long runtime → parallel execution infrastructure

**Mitigation Strategies**:
- Early validation gates after each phase
- Comprehensive unit testing (80%+ coverage)
- Integration tests at phase boundaries
- Performance benchmarking throughout
- Regular code reviews and pair programming

---

## Decision Gates

**Gate A**: Phase A complete → Validate Factor/Strategy base classes functional
**Gate B**: Phase B complete → Validate Factor library complete and usable
**Gate C**: Phase C complete → Validate Tier 2 mutations effective
**Gate D**: Phase D complete → Validate three-tier system ready for production
**Gate PROD**: Production validation → Validate system stable and performant

**Failure Handling**: If any gate fails, address issues before proceeding to next phase.

---

## References

- **Requirements**: `.claude/specs/structural-mutation-phase2/requirements.md`
- **Design**: `.claude/specs/structural-mutation-phase2/design.md`
- **Decision**: `.claude/specs/structural-mutation-phase2/PHASE2_FUSION_DECISION.md`
- **Phase 1 Validation**: `validation_results/phase1_20251020_184114/EXIT_MUTATION_LONG_VALIDATION_REPORT.md`

---

**Document Version**: 2.0 (Phase 2.0+ - Factor Graph System)
**Last Updated**: 2025-10-20
**Status**: ✅ **APPROVED** - Ready for Phase A Implementation
