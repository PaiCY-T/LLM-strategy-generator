# Requirements Document: Population-based Learning System

**Project**: Autonomous Trading Strategy Evolution
**Version**: 1.0
**Date**: 2025-10-17
**Status**: Draft

---

## Introduction

本規格旨在將現有的 single-champion learning system 轉型為 population-based evolutionary learning system，以解決當前系統無法達到 production readiness 的核心問題。

### Current System Problems

**實證數據** (200-iteration test):
- Champion 更新率：**0.5%** (210 次迭代只更新 1 次)
- Rolling variance：**1.001** (目標 <0.5)
- P-value：**0.1857** (目標 <0.05，無統計顯著性)
- Cohen's d：**0.241** (目標 ≥0.4，效果量太小)

**根本原因** (Consensus Analysis - O3 + Gemini 2.5 Pro):
> "Single-champion with text-based preservation is fundamentally flawed. The system found a good strategy early (iteration 6, Sharpe 2.4751) and got stuck because:
> 1. No diversity mechanism - all iterations compare to same champion
> 2. No exploration pressure - LLM tends to make safe, minor changes
> 3. No population dynamics - single strategy cannot represent solution space"

### Solution: Population-based Evolutionary Learning

**核心概念**：
- 每代維持 N≈20 個策略族群（population）
- 使用演化算法：Selection → Crossover → Mutation
- Multi-objective optimization：Sharpe + Calmar + MaxDD
- Diversity enforcement：Novelty metrics + crowding distance

**預期改善** (Based on consensus analysis):
| Metric | Current | Target | Expected Improvement |
|--------|---------|--------|---------------------|
| Champion update rate | 0.5% | 10-20% | 20-40x |
| Rolling variance | 1.001 | <0.5 | 50%+ reduction |
| P-value | 0.1857 | <0.05 | Statistical significance |
| Cohen's d | 0.241 | ≥0.4 | Medium effect size |

---

## Alignment with Product Vision

**Product Goal**: 自動化產生高品質交易策略，達到 production readiness 標準

本 spec 對應的問題：
- **可靠性**：目前系統無法穩定收斂，本 spec 透過族群演化提供穩定學習機制
- **效率**：目前學習效率低（0.5% 更新率），本 spec 透過多策略並行探索加速學習
- **品質**：目前單一目標優化（Sharpe），本 spec 引入多目標優化提升策略穩健性

---

## Requirements

### R1: Population Management

**User Story**: As a quantitative researcher, I want the system to maintain multiple strategies per generation, so that I can explore the solution space more effectively than single-champion learning.

#### Acceptance Criteria

1. **WHEN** system initializes **THEN** system **SHALL** create initial population of N strategies
   - N configurable (default: 20)
   - Random seed controlled for reproducibility
   - Initial strategies use diverse templates/approaches

2. **WHEN** generation completes **THEN** system **SHALL** maintain population size N
   - Add new offspring = Remove worst performers
   - Population size constant across generations
   - Diversity metrics tracked and logged

3. **WHEN** evaluating population **THEN** system **SHALL** track individual fitness scores
   - Multi-objective: Sharpe ratio, Calmar ratio, Max Drawdown
   - Pareto-optimal front identified
   - Crowding distance calculated for diversity

#### Technical Specifications

```python
@dataclass
class Strategy:
    id: str                          # Unique identifier
    generation: int                  # Generation number
    parent_ids: List[str]            # For lineage tracking
    code: str                        # Strategy implementation
    parameters: Dict[str, Any]       # Extracted parameters
    metrics: MultiObjectiveMetrics   # Fitness scores
    novelty_score: float            # Diversity measure
    timestamp: str                   # ISO 8601

@dataclass
class MultiObjectiveMetrics:
    sharpe_ratio: float             # Risk-adjusted return
    calmar_ratio: float             # Return / Max Drawdown
    max_drawdown: float             # Peak-to-trough decline
    total_return: float             # Cumulative return
    win_rate: float                 # Percentage winning trades

    def dominates(self, other: 'MultiObjectiveMetrics') -> bool:
        """Pareto dominance check"""
        ...
```

---

### R2: Selection Mechanism

**User Story**: As a system, I want to select parent strategies based on multi-objective fitness, so that high-quality strategies have higher reproduction probability while maintaining diversity.

#### Acceptance Criteria

1. **WHEN** selecting parents **THEN** system **SHALL** use tournament selection
   - Tournament size = 3 (configurable)
   - Probability of selecting best from tournament = 0.8
   - Ensures diversity through stochastic selection

2. **WHEN** comparing strategies **THEN** system **SHALL** consider Pareto dominance
   - Strategy A dominates B if better in all objectives
   - Non-dominated strategies get selection advantage
   - Crowding distance breaks ties (prefer less crowded)

3. **WHEN** selection pool is small **THEN** system **SHALL** apply diversity pressure
   - Penalize strategies similar to recent parents
   - Novelty bonus for unique approaches
   - Prevent premature convergence

#### Technical Specifications

```python
def tournament_selection(
    population: List[Strategy],
    tournament_size: int = 3,
    selection_pressure: float = 0.8
) -> Strategy:
    """Select parent using tournament selection"""
    ...

def calculate_crowding_distance(
    population: List[Strategy],
    objective_name: str
) -> Dict[str, float]:
    """NSGA-II crowding distance for diversity"""
    ...
```

---

### R3: Crossover (Strategy Breeding)

**User Story**: As a genetic algorithm, I want to combine two parent strategies to create offspring, so that successful patterns from different strategies can be recombined.

#### Acceptance Criteria

1. **WHEN** breeding two parents **THEN** system **SHALL** perform parameter-level crossover
   - Extract parameters from both parents
   - Apply uniform crossover (50/50 probability per parameter)
   - Generate valid offspring code with combined parameters

2. **WHEN** crossover fails **THEN** system **SHALL** fallback gracefully
   - Retry with single-parent inheritance
   - Log crossover failure for analysis
   - Ensure population size maintained

3. **WHEN** parameters incompatible **THEN** system **SHALL** apply compatibility rules
   - Factor types must match (momentum-momentum, value-value)
   - Liquidity filters averaged between parents
   - Smoothing windows interpolated

#### Technical Specifications

```python
def crossover(
    parent1: Strategy,
    parent2: Strategy,
    crossover_rate: float = 0.7
) -> Strategy:
    """Create offspring from two parents"""
    ...

def parameter_crossover(
    params1: Dict[str, Any],
    params2: Dict[str, Any]
) -> Dict[str, Any]:
    """Uniform crossover at parameter level"""
    ...
```

---

### R4: Mutation (Random Variation)

**User Story**: As an evolutionary algorithm, I want to introduce random variations to offspring, so that the system can explore new areas of the solution space.

#### Acceptance Criteria

1. **WHEN** mutating strategy **THEN** system **SHALL** apply Gaussian mutation to numeric parameters
   - Mutation rate = 0.1 (10% of parameters mutated)
   - Mutation strength (sigma) = 0.1 (±10% variation)
   - Preserve parameter bounds and constraints

2. **WHEN** mutating factor weights **THEN** system **SHALL** renormalize to sum=1.0
   - Weights represent factor importance
   - Must sum to 1.0 after mutation
   - All weights ≥0

3. **WHEN** mutation generates invalid code **THEN** system **SHALL** retry or reject
   - Validate code before accepting mutation
   - Max 3 retries per mutation
   - Reject offspring if all retries fail

#### Technical Specifications

```python
def mutate(
    strategy: Strategy,
    mutation_rate: float = 0.1,
    mutation_strength: float = 0.1
) -> Strategy:
    """Apply random mutations to strategy"""
    ...

def gaussian_mutation(
    value: float,
    sigma: float,
    bounds: Tuple[float, float]
) -> float:
    """Gaussian mutation with boundary constraints"""
    ...
```

---

### R5: Elitism and Replacement

**User Story**: As a system operator, I want to preserve the best strategies across generations, so that improvements are never lost.

#### Acceptance Criteria

1. **WHEN** creating new generation **THEN** system **SHALL** preserve top K elite strategies
   - K = 2 (configurable)
   - Elites copied unchanged to next generation
   - Prevents regression of best solutions

2. **WHEN** replacing population **THEN** system **SHALL** remove worst performers
   - Sort by multi-objective fitness
   - Remove bottom (offspring_count) strategies
   - Maintain population size N

3. **WHEN** all strategies degrade **THEN** system **SHALL** maintain historical best
   - Global champion tracked across all generations
   - Historical best never deleted
   - Can serve as recovery point

#### Technical Specifications

```python
def elitism_replacement(
    current_population: List[Strategy],
    offspring: List[Strategy],
    elite_count: int = 2
) -> List[Strategy]:
    """Replace worst with offspring, preserve elites"""
    ...
```

---

### R6: Multi-objective Optimization

**User Story**: As a quantitative researcher, I want strategies optimized for multiple objectives (Sharpe, Calmar, MaxDD), so that strategies are robust across different performance dimensions.

#### Acceptance Criteria

1. **WHEN** evaluating fitness **THEN** system **SHALL** calculate all objectives
   - Sharpe ratio (risk-adjusted return)
   - Calmar ratio (return / max drawdown)
   - Max drawdown (peak-to-trough decline)
   - Win rate (percentage profitable trades)

2. **WHEN** comparing strategies **THEN** system **SHALL** identify Pareto front
   - Non-dominated solutions = Pareto optimal
   - Dominated solutions marked for potential removal
   - Diversity along Pareto front maintained

3. **WHEN** reporting results **THEN** system **SHALL** visualize multi-objective trade-offs
   - 2D scatter plots (Sharpe vs Calmar)
   - Pareto front highlighted
   - Generation-over-generation progress tracked

#### Technical Specifications

```python
def calculate_pareto_front(
    population: List[Strategy]
) -> List[Strategy]:
    """Identify non-dominated strategies"""
    ...

def pareto_dominates(
    strategy_a: MultiObjectiveMetrics,
    strategy_b: MultiObjectiveMetrics
) -> bool:
    """Check if A dominates B (better in all objectives)"""
    ...
```

---

### R7: Novelty and Diversity Metrics

**User Story**: As an evolutionary system, I want to measure and maintain strategy diversity, so that the population doesn't converge prematurely to suboptimal solutions.

#### Acceptance Criteria

1. **WHEN** evaluating novelty **THEN** system **SHALL** calculate diversity metrics
   - Jaccard distance on feature sets
   - Hamming distance on parameter discretization
   - Behavioral diversity (different holdings over time)

2. **WHEN** diversity drops below threshold **THEN** system **SHALL** increase mutation rate
   - Threshold = 0.3 average pairwise distance
   - Mutation rate boost = 2x (0.1 → 0.2)
   - Automatic reversion when diversity recovers

3. **WHEN** reporting diversity **THEN** system **SHALL** track population entropy
   - Shannon entropy of parameter distributions
   - Generation-over-generation diversity trends
   - Alert if diversity collapse detected

#### Technical Specifications

```python
def calculate_jaccard_distance(
    strategy_a: Strategy,
    strategy_b: Strategy
) -> float:
    """Jaccard distance on feature sets (0=identical, 1=completely different)"""
    features_a = extract_feature_set(strategy_a.code)
    features_b = extract_feature_set(strategy_b.code)

    intersection = len(features_a & features_b)
    union = len(features_a | features_b)

    return 1.0 - (intersection / union) if union > 0 else 0.0

def extract_feature_set(code: str) -> Set[str]:
    """Extract features used in strategy code"""
    # Example: {'roe', 'momentum', 'liquidity', 'revenue_yoy', ...}
    ...
```

---

### R8: Integration with Existing System

**User Story**: As a system maintainer, I want the population-based learning to integrate smoothly with existing autonomous loop, so that minimal changes are needed to existing code.

#### Acceptance Criteria

1. **WHEN** initializing system **THEN** system **SHALL** use existing autonomous_loop.py
   - Wrap autonomous loop with population manager
   - Existing iteration logic reused
   - Minimal modifications to core loop

2. **WHEN** generating strategies **THEN** system **SHALL** use existing LLM API
   - Existing prompt_builder.py leveraged
   - Crossover/mutation implemented as prompt variations
   - Existing code validation reused

3. **WHEN** backtesting **THEN** system **SHALL** use existing Finlab integration
   - Existing backtest execution unchanged
   - Metric extraction reused
   - Sandbox security maintained

#### Technical Specifications

```python
class PopulationManager:
    def __init__(self, autonomous_loop: AutonomousLoop):
        self.loop = autonomous_loop  # Wrap existing loop
        self.population: List[Strategy] = []
        ...

    def evolve_generation(self):
        """Run one generation of evolution"""
        # 1. Evaluate current population (reuse loop.run_iteration)
        # 2. Select parents (new)
        # 3. Crossover (new)
        # 4. Mutate (new)
        # 5. Replace (new)
        ...
```

---

## Non-Functional Requirements

### Performance

**R9.1**: System **SHALL** complete one generation (N=20 strategies) in <60 minutes
- Parallel strategy evaluation when possible
- Efficient parameter extraction and crossover
- Optimized diversity calculations

**R9.2**: System **SHALL** support population sizes up to N=50
- Memory usage <2GB for N=50
- Scalable data structures
- Efficient Pareto front calculation

### Reliability

**R10.1**: System **SHALL** handle strategy generation failures gracefully
- Max 3 retries per strategy
- Fallback to simpler crossover if complex fails
- Population size maintained even with failures

**R10.2**: System **SHALL** persist population state for recovery
- Save population after each generation
- Load from checkpoint on restart
- Lineage and history preserved

### Usability

**R11.1**: System **SHALL** provide progress visualization
- Real-time generation progress
- Pareto front evolution over time
- Diversity metrics dashboard

**R11.2**: System **SHALL** log detailed evolution history
- Parent-offspring relationships (lineage tree)
- Selection/crossover/mutation events
- Fitness progression over generations

### Security

**R12.1**: System **SHALL** maintain existing code validation
- All generated code validated before execution
- AST security checks applied
- Sandbox execution for backtests

---

## Success Criteria

### Primary Success Metrics (3/4 Required to Pass)

1. **Champion Update Rate**: ≥10% (baseline: 0.5%)
   - Measure: Updates per generation across 20 generations
   - Target: At least 2 updates across 20 generations (10%)

2. **Rolling Variance**: <0.5 (baseline: 1.001)
   - Measure: Variance of Sharpe ratios in final 20 strategies
   - Target: Standard deviation <0.5

3. **Statistical Significance**: P-value <0.05 (baseline: 0.1857)
   - Measure: T-test comparing population mean vs random baseline
   - Target: P-value <0.05 with Cohen's d ≥0.4

4. **Pareto Front Quality**: ≥5 non-dominated strategies in final generation
   - Measure: Count of Pareto-optimal strategies
   - Target: At least 5 diverse high-quality solutions

### Secondary Success Metrics

- **Diversity Maintenance**: Average Jaccard distance ≥0.3 throughout evolution
- **Convergence**: Best Sharpe ratio improvement ≥20% from generation 1 to 20
- **Robustness**: ≥3 strategies with Sharpe >1.5 in final population

---

## Validation Plan

### Unit Testing (20 tests)

- Selection mechanism (5 tests)
- Crossover logic (5 tests)
- Mutation operators (5 tests)
- Diversity metrics (5 tests)

### Integration Testing (5 scenarios)

1. **Full evolution run**: 5 generations with N=10
2. **Diversity recovery**: Test mutation rate adaptation
3. **Elitism preservation**: Verify best strategies never lost
4. **Crossover compatibility**: Test all parameter type combinations
5. **Multi-objective ranking**: Verify Pareto front correctness

### Validation Testing (20-generation run)

- Population size: N=20
- Generations: 20 (400 total strategies evaluated)
- Success: 3/4 primary metrics pass
- Duration: ~20 hours (60 min/generation)

---

## Dependencies

### Existing Components (Reuse)

- `autonomous_loop.py`: Core iteration logic
- `prompt_builder.py`: Strategy generation prompts
- `performance_attributor.py`: Parameter extraction
- `validate_code.py`: Code security validation
- `sandbox_simple.py`: Backtest execution

### New Dependencies (To Implement)

- `population_manager.py`: Population-based evolution controller
- `selection.py`: Parent selection algorithms
- `crossover.py`: Strategy breeding logic
- `mutation.py`: Random variation operators
- `diversity.py`: Novelty and diversity metrics
- `multi_objective.py`: Pareto optimization utilities

### External Libraries

- **NumPy**: Numerical operations, mutation sampling
- **SciPy**: Statistical tests, distance metrics
- **Matplotlib**: Visualization (Pareto front, diversity plots)

---

## Risks and Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Crossover generates invalid code | Medium | High | Validate all offspring, fallback to mutation-only |
| Premature convergence | Medium | High | Diversity enforcement, adaptive mutation |
| LLM API rate limits | High | Medium | Batch strategy generation, implement backoff |
| Computation time >60 min/generation | Medium | Medium | Parallel evaluation, optimize parameter extraction |

### Performance Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| No improvement over single-champion | Low | Critical | Validate with 5-generation pilot test first |
| Pareto front quality poor | Medium | High | Tune selection pressure and mutation rates |
| Diversity collapse | Medium | High | Monitor entropy, automatic mutation boost |

---

## Timeline and Rollout

### Development Phase (Week 1-2)

- **Week 1**: Core evolution components (selection, crossover, mutation)
- **Week 2**: Integration with autonomous loop, diversity metrics

### Testing Phase (Week 3)

- **Day 1-2**: Unit tests (20 tests)
- **Day 3**: Integration tests (5 scenarios)
- **Day 4-5**: 5-generation pilot validation

### Production Validation (Week 4)

- **Day 1-3**: 20-generation full validation run
- **Day 4**: Metrics analysis and success criteria evaluation
- **Day 5**: Documentation and deployment

---

## Appendix

### A. Mathematical Formulations

**Pareto Dominance**:
```
Strategy A dominates Strategy B if:
  ∀ i: f_i(A) ≥ f_i(B)  AND  ∃ j: f_j(A) > f_j(B)

where f_i are objective functions (sharpe, calmar, etc.)
```

**Crowding Distance** (NSGA-II):
```
distance[i] = Σ_j (f_j[i+1] - f_j[i-1]) / (f_j^max - f_j^min)

Promotes diversity along Pareto front
```

**Novelty Score**:
```
novelty(s) = (1/k) * Σ_{i=1}^k distance(s, neighbor_i)

where neighbors are k-nearest strategies in feature space
```

### B. References

- Consensus Analysis (2025-10-17): O3 + Gemini 2.5 Pro recommendations
- 200-Iteration Test Results: `logs/200iteration_test_group1_20251017_004311.log`
- Learning System Enhancement Spec: `.claude/specs/learning-system-enhancement/`
- NSGA-II Paper: Deb et al. (2002) - Multi-objective optimization

---

**Document Status**: Draft - Ready for Design Phase
**Version**: 1.0
**Date**: 2025-10-17
**Author**: Claude Code (based on consensus analysis and user requirements)
