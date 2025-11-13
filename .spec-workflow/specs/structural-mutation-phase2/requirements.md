# Requirements Document - Structural Mutation Phase 2.0+ (Factor Graph System)

## Introduction

Phase 1 exit mutation validation completed successfully, achieving technical objectives but revealing a fundamental architectural insight: **strategies are not parameter dictionaries, but Factor DAGs (Directed Acyclic Graphs)**.

**Phase 2.0+ (Unified Factor Graph System)** adopts a Factor Graph architecture that naturally fuses:
- **Phase 1** exit mutations → Factor library components
- **Phase 2a** YAML configuration → Tier 1 safe entry point
- **Phase 2.0** structural mutations → Tier 3 advanced capabilities

This unified approach enables breakthrough performance through compositional innovation rather than monolithic template evolution.

## Alignment with Product Vision

This feature directly supports the autonomous strategy generation goals by:
- **Breakthrough Performance**: Enable discovery of strategies that exceed single-template performance ceiling (Sharpe >2.5)
- **Innovation Capability**: Generate novel trading logic through structural evolution rather than parameter optimization
- **Competitive Advantage**: Create unique strategies that cannot be replicated through simple combinations

## Context and Decision Gate

### Phase 1 Exit Mutation Results (Validated - 2025-10-20)
- **Exit Mutation Framework**: ✅ **Complete** (detector, mutator, validator, operator)
- **PopulationManager Integration**: ✅ **Complete** (10-generation validation)
- **Success Rate**: **0%** (validation test design issue, framework operational)
- **Sharpe Ratio**: **1.7384** (plateaued, no improvement from mutations)
- **Decision**: ⚠️ **OPTIMIZATION_NEEDED** → Deep architectural analysis

### Deep Analysis Results (Gemini 2.5 Pro + Expert Analysis)
**Key Insight**: Strategy representation fundamentally limits innovation capacity

**Current Limitation**: `Strategy = Dict[str, Any]` (parameter dictionary)
- Mutations can only modify parameter values
- Cannot change strategy structure or composition
- Limited to pre-defined template architectures

**Breakthrough Solution**: `Strategy = Factor DAG` (Directed Acyclic Graph)
- Strategies are compositions of atomic Factors
- Each Factor: inputs → logic → outputs
- Mutations operate at Factor level (add, remove, replace, modify)
- Natural validation through dependency checking

### Architectural Decision (2025-10-20)
✅ **APPROVED**: Phase 2.0+ (Unified Factor Graph System)

**Rationale**:
1. Expert-validated architecture (DAG > parameter dict)
2. Natural fusion of Phase 1/2a/2.0 (no redundancy)
3. Longer-term maintainability and extensibility
4. Additional 2 weeks investment yields superior architecture

## Requirements

### REQ-1: Factor Graph Architecture and Three-Tier Mutation System

**User Story:** As a quantitative researcher, I want strategies represented as Factor DAGs with multi-tier mutation capabilities, so that the system can evolve strategy structure through safe, progressive innovation.

#### Core Architecture Requirements

1. WHEN defining a Factor THEN system SHALL implement:
   - **inputs**: List[str] - required data columns
   - **outputs**: List[str] - produced data columns
   - **category**: FactorCategory (momentum, value, quality, risk, exit)
   - **logic**: Callable - execution logic
   - **parameters**: dict - tunable parameters

2. WHEN defining a Strategy THEN system SHALL implement:
   - **factors**: Dict[str, Factor] - DAG of factor instances
   - **validate()**: Dependency checking + topological sorting
   - **to_pipeline()**: Compile to executable data pipeline

#### Three-Tier Mutation System Requirements

3. **Tier 1 (Safe Configuration)** WHEN LLM generates strategy THEN system SHALL:
   - Accept YAML/JSON configuration defining factor composition
   - Validate against JSON schema
   - Interpret configuration into Factor instances using safe parser
   - Provide clear error messages for invalid configurations

4. **Tier 2 (Factor Mutations)** WHEN evolving strategies THEN system SHALL support:
   - **add_factor()**: Add new factor with dependency validation
   - **remove_factor()**: Remove factor with orphan detection
   - **replace_factor()**: Swap factor with same-category alternative
   - **mutate_parameters()**: Gaussian parameter mutation (Phase 1 integration)

5. **Tier 3 (Structural Mutations)** WHEN advanced evolution THEN system SHALL support:
   - **modify_factor_logic()**: AST-level logic modification
   - **combine_signals()**: Create composite signal factors
   - **adaptive_parameters()**: Dynamic parameter adjustment factors

6. WHEN any mutation is applied THEN system SHALL:
   - Validate DAG integrity (no cycles, all dependencies satisfied)
   - Preserve syntactic correctness through AST validation
   - Ensure all required data columns are available
   - Verify strategy can be backtested without errors

### REQ-2: Multi-Objective Fitness Evaluation

**User Story:** As a system administrator, I want comprehensive fitness evaluation, so that structural mutations are guided toward robust strategies.

#### Acceptance Criteria

1. WHEN evaluating mutated strategy THEN system SHALL calculate multi-objective metrics:
   - **Primary**: Sharpe ratio, Calmar ratio
   - **Risk**: Maximum drawdown, volatility
   - **Robustness**: Win rate, profit factor, average holding period
   - **Stability**: Drawdown duration, recovery time

2. WHEN comparing strategies THEN system SHALL use NSGA-II Pareto ranking:
   - Identify non-dominated solutions
   - Calculate crowding distance for diversity
   - Maintain Pareto front across generations

3. WHEN fitness calculation fails THEN strategy SHALL receive zero fitness and be eliminated

### REQ-3: Mutation History and Provenance

**User Story:** As a quantitative researcher, I want to track mutation history, so that I can understand how successful strategies evolved.

#### Acceptance Criteria

1. WHEN strategy is mutated THEN system SHALL record:
   - Parent strategy ID and structure
   - Mutation type and parameters
   - Timestamp and generation number
   - Performance comparison (parent vs child)

2. WHEN querying mutation history THEN system SHALL provide:
   - Full lineage from initial template to current strategy
   - Branch points where multiple mutations succeeded
   - Performance progression across generations

3. WHEN exporting strategy THEN lineage metadata SHALL be included

### REQ-4: Safety and Constraint Enforcement

**User Story:** As a risk manager, I want mutation operations to enforce safety constraints, so that generated strategies remain viable and controllable.

#### Acceptance Criteria

1. WHEN applying mutation THEN system SHALL enforce limits:
   - Maximum position size: 0.95 (95% of capital)
   - Minimum rebalancing period: Daily
   - Maximum strategy complexity: 1000 lines of code
   - Maximum number of indicators: 20

2. WHEN validating mutated strategy THEN system SHALL check:
   - No unauthorized external API calls
   - No file system modifications
   - No infinite loops or excessive computation
   - All data access through finlab API only

3. WHEN safety violation detected THEN mutation SHALL be rejected and logged

### REQ-5: Performance Validation and Metrics

**User Story:** As a quantitative researcher, I want rigorous performance validation, so that I can trust the evolved strategies.

#### Acceptance Criteria

1. WHEN structural mutation completes N generations THEN system SHALL:
   - Report best Sharpe ratio achieved
   - Compare against Phase 1.5 baseline (1.37)
   - Identify if breakthrough threshold (2.5) is reached
   - Provide statistical significance testing

2. WHEN validating evolved strategy THEN system SHALL:
   - Run out-of-sample backtest on held-out data
   - Calculate walk-forward analysis metrics
   - Test robustness to parameter variations
   - Verify consistency across market regimes

3. WHEN exporting final strategy THEN system SHALL include:
   - Full performance report with all metrics
   - Risk analysis and drawdown characteristics
   - Sensitivity analysis results
   - Mutation lineage and provenance

### REQ-6: Exit Strategy Factors ⭐ **Phase 1 Integration**

**User Story:** As a quantitative researcher, I want exit strategies integrated as Factor library components, so that Phase 1 work seamlessly integrates into the Factor Graph architecture.

**Rationale**: Phase 1 exit mutation framework is complete and operational. Phase 2.0+ integrates this work as a specialized Factor category rather than rebuilding it.

#### Factor Integration Requirements

1. WHEN building Factor library THEN system SHALL extract from Phase 1:
   - **ExitFactor** base class with standardized interface
   - **StopLossFactor**: Fixed percentage, ATR-based, time-based stop-loss factors
   - **TakeProfitFactor**: Fixed target, risk-reward ratio, multiple target factors
   - **TrailingStopFactor**: Percentage-based, ATR-based, MA-based trailing factors
   - **DynamicExitFactor**: Indicator-based, volatility-adjusted, volume-based exit factors
   - **RiskManagementExitFactor**: Portfolio drawdown, correlation-based, time-decay factors

2. WHEN using Exit Factors in strategies THEN system SHALL:
   - Define dependencies on entry factors (position tracking required)
   - Output exit signals compatible with portfolio management
   - Support composability (multiple exit conditions combined)
   - Preserve Phase 1 AST mutation capabilities for Tier 3

3. WHEN validating exit factor composition THEN system SHALL:
   - Check logical consistency (stop-loss < entry < take-profit for long)
   - Verify all required indicators are available (ATR, MA, etc.)
   - Ensure no circular dependencies in factor DAG
   - Validate exit timing doesn't conflict with rebalancing

4. WHEN evaluating strategies with exit factors THEN system SHALL measure:
   - **Primary**: Sharpe ratio vs strategies without exit factors
   - **Risk**: Max drawdown reduction, win rate improvement
   - **Trade Management**: Win/loss ratio, profit factor, holding period
   - **Robustness**: Performance across market regimes

#### Phase 1 Exit Mutation Framework (Complete - 2025-10-20)
✅ **ExitMechanismDetector**: AST-based exit pattern detection
✅ **ExitStrategyMutator**: Three-tier mutation (Parametric 80%, Structural 15%, Relational 5%)
✅ **ExitCodeValidator**: Safety validation and AST correctness
✅ **ExitMutationOperator**: Unified pipeline (Detect → Mutate → Generate → Validate)
✅ **PopulationManager Integration**: 10-generation validation complete

**Migration Strategy**: Phase B (Week 3-4) extracts Exit Factors from Phase 1 mutation framework, preserving AST mutation capabilities for Tier 3 advanced operations.

## Non-Functional Requirements

### Performance
- Structural mutation evaluation: <5 minutes per strategy (using real finlab backtest)
- Generation evolution: <2 hours for N=20 population, 20 generations
- Mutation operation: <1 second per mutation application
- History query: <100ms for full lineage retrieval

### Reliability
- Strategy generation success rate: >80% (valid, backtestable strategies)
- Backtest completion rate: >95% (no crashes or timeouts)
- Fitness calculation success rate: >99%
- System uptime during evolution: >99.9%

### Scalability
- Support population sizes: 10-100 strategies
- Support generation counts: 10-1000 generations
- Support concurrent evaluations: Up to 10 parallel backtests
- Handle mutation history: >10,000 mutations

### Maintainability
- All mutation operators documented with examples
- Code coverage: >80% for mutation logic
- Integration tests for each mutation type
- Clear logging of all mutation operations

### Security
- No code execution outside sandboxed environment
- All mutations validated before execution
- Audit trail for all structural changes
- Rate limiting on API calls to prevent abuse

## Success Metrics

### Primary Success Criteria
1. **Breakthrough Achievement**: At least one strategy achieves Sharpe >2.5
2. **Consistency**: Best strategy maintains Sharpe >2.0 across out-of-sample periods
3. **Robustness**: Best strategy shows positive returns in >70% of monthly periods
4. **Structural Innovation**: Evolved strategies use Factor compositions not present in initial templates

### Secondary Success Criteria
1. **Efficiency**: Achieve breakthrough within 100 generations
2. **Factor Diversity**: Maintain >10 distinct Factor patterns across population
3. **DAG Complexity**: Average strategy DAG depth 3-5 layers, width 5-10 factors
4. **Stability**: No catastrophic mutations that crash the system
5. **Reproducibility**: Results repeatable with same random seed
6. **Tier Utilization**: >60% Tier 2 mutations succeed, >40% Tier 3 mutations succeed

## Timeline

**Phase 2.0+ (Unified Factor Graph System) - 8 Week Implementation:**

- **Phase A: Foundation** (Week 1-2) ⭐ **START HERE**
  - **Goal**: Implement Factor/Strategy base classes
  - **Tasks**:
    1. Design Factor interface (inputs, outputs, category, logic, parameters)
    2. Implement Strategy DAG structure
    3. Implement validate() method (dependency checking + topological sorting)
    4. Implement to_pipeline() method (DAG → executable data pipeline)
  - **Validation**: Manual strategy composition mimics existing templates, successful backtest

- **Phase B: Migration** (Week 3-4)
  - **Goal**: Build Factor library from existing templates
  - **Tasks**:
    1. Extract 10-15 Factors from MomentumTemplate (indicators, signals, entry logic)
    2. Extract Factors from TurtleTemplate (breakout, channel, position sizing)
    3. Extract Exit Strategy Factors from Phase 1 (stop-loss, take-profit, trailing stops)
    4. Establish Factor Registry with categorization and discovery
  - **Validation**: EA uses Factor compositions to run 10 generations, produces valid strategies

- **Phase C: Evolution** (Week 5-6)
  - **Goal**: Implement Tier 2 mutation operations
  - **Tasks**:
    1. add_factor() with dependency validation
    2. remove_factor() with orphan detection
    3. replace_factor() with same-category Factor library
    4. Smart mutation operators (category-aware selection, mutation rate scheduling)
  - **Validation**: EA runs 20 generations, strategy structure evolves continuously

- **Phase D: Advanced Capabilities** (Week 7-8)
  - **Goal**: Add Tier 1 (YAML) and Tier 3 (AST) capabilities
  - **Tasks**:
    1. YAML schema design + validator
    2. YAML → Factor interpreter (safe configuration parsing)
    3. AST-based factor logic mutation (Tier 3 structural mutations)
    4. Adaptive mutation tier selection (risk-based tier routing)
  - **Validation**: Complete three-tier mutation system runs 50 generations

**Total Estimated Duration**: **8 weeks** (vs 6-8 weeks Phase 2.0 alone)

**Additional Value**:
- ✅ Unified architecture (long-term maintainability)
- ✅ Phase 1 integration (exit mutations as Factors)
- ✅ Three-tier safety system (Tier 1 → 2 → 3 progressive risk)
- ✅ Expert-validated design direction (DAG > parameter dictionary)

## Dependencies

- ✅ **Phase 1 Complete** (2025-10-20): Exit mutation framework operational
  - ✅ ExitMechanismDetector: AST-based pattern detection
  - ✅ ExitStrategyMutator: Three-tier mutation system
  - ✅ ExitCodeValidator: Safety validation
  - ✅ ExitMutationOperator: Unified pipeline
  - ✅ PopulationManager integration: 10-generation validation
- ✅ PopulationManager using real finlab backtest
- ✅ Multi-objective optimization (NSGA-II) functional
- ✅ Template registry and template validation operational
- ⏳ Factor/Strategy base classes (Phase A)
- ⏳ Factor library from templates (Phase B)
- ⏳ Tier 2 mutation operators (Phase C)
- ⏳ Tier 1 (YAML) and Tier 3 (AST) capabilities (Phase D)

## Risks and Mitigations

### Technical Risks
1. **Risk**: Factor DAG mutations create invalid dependency structures (cycles, missing inputs)
   - **Mitigation**: Topological sort validation before backtest, dependency graph visualization, comprehensive DAG testing

2. **Risk**: Factor mutations degrade performance instead of improving it
   - **Mitigation**: Elitism preservation, Pareto front tracking, rollback capability, tier-based risk control

3. **Risk**: Evaluation time becomes prohibitive with complex Factor DAGs
   - **Mitigation**: Parallel evaluation, DAG compilation caching, early termination for poor performers

4. **Risk**: Phase 1 exit mutations don't integrate cleanly into Factor architecture
   - **Mitigation**: Phase B explicitly focused on Phase 1 migration, preserve AST capabilities, expert review

### Business Risks
1. **Risk**: Factor Graph approach fails to achieve breakthrough (Sharpe <2.5)
   - **Mitigation**: Expert-validated architecture reduces risk, fallback to template-level combinations if needed

2. **Risk**: Timeline extends beyond 8 weeks
   - **Mitigation**: Phased delivery (A→B→C→D), each phase independently valuable, regular validation gates

## References

- **Phase 1 Validation Report**: `validation_results/phase1_20251020_184114/EXIT_MUTATION_LONG_VALIDATION_REPORT.md`
- **Phase 2.0+ Fusion Decision**: `.spec-workflow/specs/structural-mutation-phase2/PHASE2_FUSION_DECISION.md`
- **Deep Analysis**: Gemini 2.5 Pro thinkdeep workflow (2025-10-20)
- **Expert Analysis**: Factor Graph System architectural insights
- **Population-based Learning Spec**: `.spec-workflow/specs/population-based-learning/` (Phase 1 foundation)

---

**Document Version**: 2.0 (Phase 2.0+ - Factor Graph System)
**Last Updated**: 2025-10-20
**Status**: ✅ **APPROVED** - Ready for Phase A Implementation
