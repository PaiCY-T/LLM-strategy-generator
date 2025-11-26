# population-based-learning - Task 29

Execute task 29 for the population-based-learning specification.

## Task Description
Implement parameter_crossover function

## Code Reuse
**Leverage existing code**: random module

## Requirements Reference
**Requirements**: R3.1

## Usage
```
/Task:29-population-based-learning
```

## Instructions

Execute with @spec-task-executor agent the following task: "Implement parameter_crossover function"

```
Use the @spec-task-executor agent to implement task 29: "Implement parameter_crossover function" for the population-based-learning specification and include all the below context.

# Steering Context
## Steering Documents Context

No steering documents found or all are empty.

# Specification Context
## Specification Context (Pre-loaded): population-based-learning

### Requirements
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
- Learning System Enhancement Spec: `.spec-workflow/specs/learning-system-enhancement/`
- NSGA-II Paper: Deb et al. (2002) - Multi-objective optimization

---

**Document Status**: Draft - Ready for Design Phase
**Version**: 1.0
**Date**: 2025-10-17
**Author**: Claude Code (based on consensus analysis and user requirements)

---

### Design
# Design Document: Population-based Learning System

**Project**: Autonomous Trading Strategy Evolution
**Version**: 1.0
**Date**: 2025-10-17
**Status**: Design Phase

---

## Overview

本設計文件詳述 population-based evolutionary learning system 的架構、組件、算法和整合方案。系統使用遺傳演算法（Genetic Algorithm）框架，透過 selection、crossover、mutation 機制，在策略族群中演化出高品質交易策略。

**核心設計原則**：
1. **最小侵入性**：重用現有 `autonomous_loop.py`，最小化程式碼變更
2. **模組化**：各演化組件（selection、crossover、mutation）獨立實作
3. **可測試性**：每個組件都有明確介面，便於單元測試
4. **可擴展性**：支援未來擴展（如協同演化、多目標權重調整）

---

## Steering Document Alignment

### Technical Standards (tech.md)

**遵循的技術標準**：
- **Type Safety**: 使用 Python 3.10+ type hints, `@dataclass` 定義數據結構
- **Error Handling**: 所有 LLM API 調用、backtest 執行都有 try-except 和重試機制
- **Logging**: 使用 `logging` 模組記錄所有關鍵事件（selection、crossover、mutation、fitness）
- **Code Validation**: 重用現有 `validate_code.py` 的 AST 安全檢查

### Project Structure (structure.md)

**遵循的專案結構**：
```
src/
  evolution/              # 新增目錄
    __init__.py
    population_manager.py  # 族群管理器
    selection.py           # 父代選擇
    crossover.py           # 策略交叉
    mutation.py            # 策略突變
    diversity.py           # 多樣性度量
    multi_objective.py     # 多目標優化
  backtest/               # 現有目錄（重用）
    metrics.py            # 重用現有 metrics
  ...

tests/
  evolution/              # 新增測試目錄
    test_selection.py
    test_crossover.py
    test_mutation.py
    test_diversity.py
    test_population_manager.py
```

---

## Code Reuse Analysis

### Existing Components to Leverage

**重用比例**: ~70% 現有程式碼，30% 新程式碼

1. **`autonomous_loop.py`**:
   - **重用**: `run_iteration()`, `_execute_backtest()`, `_extract_metrics()`
   - **整合**: `PopulationManager` 包裝 `AutonomousLoop` 實例

2. **`prompt_builder.py`**:
   - **重用**: 基礎 prompt 架構
   - **擴展**: 添加 crossover-specific prompts, mutation-specific prompts

3. **`performance_attributor.py`**:
   - **重用**: `extract_strategy_params()` 用於參數提取
   - **擴展**: 支援參數相似度計算（Jaccard distance）

4. **`validate_code.py`**:
   - **重用**: 所有 offspring 程式碼驗證
   - **不變**: AST 檢查邏輯保持不變

5. **`backtest/metrics.py`**:
   - **重用**: Sharpe ratio 計算
   - **擴展**: 添加 Calmar ratio、Max Drawdown 計算

### Integration Points

**與現有系統的整合點**：

```python
# Integration Point 1: AutonomousLoop Wrapper
class PopulationManager:
    def __init__(self, autonomous_loop: AutonomousLoop):
        self.loop = autonomous_loop  # 重用現有 loop
        ...

    def evaluate_strategy(self, strategy: Strategy) -> MultiObjectiveMetrics:
        """使用現有 loop 評估單一策略"""
        success, result = self.loop.run_iteration(
            iteration_num=strategy.generation,
            code=strategy.code
        )
        return self._extract_multi_objective_metrics(result)

# Integration Point 2: Prompt Builder Extension
class EvolutionaryPromptBuilder(PromptBuilder):
    def build_crossover_prompt(
        self,
        parent1: Strategy,
        parent2: Strategy
    ) -> str:
        """建構 crossover prompt，重用基礎 prompt 架構"""
        base_prompt = self.build_prompt(...)
        crossover_directive = self._format_crossover_directive(parent1, parent2)
        return base_prompt + "\n\n" + crossover_directive
```

---

## Architecture

### High-Level System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   Population Manager                           │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │  Population  │───>│  Evaluation  │───>│  Selection   │    │
│  │  (N=20)      │    │  (Fitness)   │    │  (Parents)   │    │
│  └──────────────┘    └──────────────┘    └──────┬───────┘    │
│         ▲                    │                    │             │
│         │                    │                    ▼             │
│  ┌──────┴───────┐    ┌──────┴──────┐    ┌──────────────┐    │
│  │  Replacement │<───│  Mutation   │<───│  Crossover   │    │
│  │  (Elitism)   │    │  (Variation)│    │  (Breeding)  │    │
│  └──────────────┘    └─────────────┘    └──────────────┘    │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
         │                                            │
         ▼                                            ▼
┌──────────────────┐                        ┌──────────────────┐
│ Autonomous Loop  │                        │  Diversity       │
│  (Evaluation)    │                        │  Maintenance     │
│                  │                        │                  │
│ • run_iteration()│                        │ • Jaccard dist   │
│ • backtest exec  │                        │ • Entropy        │
│ • metric extract │                        │ • Crowding dist  │
└──────────────────┘                        └──────────────────┘
```

### Evolution Workflow (Single Generation)

```
GENERATION N
    │
    ├──> 1. EVALUATE POPULATION
    │       ├─> For each strategy in population:
    │       │     ├─> Run backtest (reuse autonomous_loop)
    │       │     ├─> Calculate multi-objective metrics
    │       │     └─> Compute novelty score
    │       └─> Identify Pareto front
    │
    ├──> 2. SELECT PARENTS (create offspring_count pairs)
    │       ├─> Tournament selection (size=3)
    │       ├─> Favor non-dominated strategies
    │       └─> Apply diversity pressure
    │
    ├──> 3. CROSSOVER (breed offspring)
    │       ├─> For each parent pair:
    │       │     ├─> Extract parameters from both
    │       │     ├─> Uniform crossover (50/50 per param)
    │       │     └─> Generate offspring code via LLM
    │       └─> Validate all offspring
    │
    ├──> 4. MUTATION (introduce variation)
    │       ├─> For each offspring:
    │       │     ├─> Mutate parameters (rate=0.1)
    │       │     ├─> Gaussian noise (sigma=0.1)
    │       │     └─> Validate mutated code
    │       └─> Reject invalid mutations
    │
    ├──> 5. REPLACEMENT (form next generation)
    │       ├─> Preserve elite_count best strategies
    │       ├─> Add valid offspring
    │       └─> Remove worst performers to maintain size N
    │
    └──> 6. LOGGING & CHECKPOINTING
            ├─> Save population state
            ├─> Log diversity metrics
            ├─> Update Pareto front visualization
            └─> Persist lineage tree
```

---

## Components and Interfaces

### Component 1: Population Manager

**Purpose**: 協調整個演化流程，管理族群狀態

**Interfaces**:
```python
class PopulationManager:
    def __init__(
        self,
        autonomous_loop: AutonomousLoop,
        population_size: int = 20,
        elite_count: int = 2,
        tournament_size: int = 3
    ):
        """Initialize population manager"""
        ...

    def initialize_population(self) -> List[Strategy]:
        """Create initial diverse population"""
        ...

    def evolve_generation(self, generation_num: int) -> EvolutionResult:
        """Execute one complete generation of evolution"""
        ...

    def save_checkpoint(self, filepath: str):
        """Persist population state for recovery"""
        ...

    def load_checkpoint(self, filepath: str):
        """Resume from saved checkpoint"""
        ...
```

**Dependencies**:
- `AutonomousLoop`: 重用現有迭代邏輯
- `SelectionManager`: 父代選擇
- `CrossoverManager`: 策略交叉
- `MutationManager`: 策略突變
- `DiversityAnalyzer`: 多樣性度量

**Reuses**:
- `autonomous_loop.run_iteration()`: 策略評估
- `performance_attributor.extract_strategy_params()`: 參數提取

---

### Component 2: Selection Manager

**Purpose**: 根據多目標適應度選擇父代策略

**Interfaces**:
```python
class SelectionManager:
    def tournament_selection(
        self,
        population: List[Strategy],
        tournament_size: int = 3,
        selection_pressure: float = 0.8
    ) -> Strategy:
        """Select single parent using tournament selection"""
        ...

    def select_parents(
        self,
        population: List[Strategy],
        count: int
    ) -> List[Tuple[Strategy, Strategy]]:
        """Select count pairs of parents for breeding"""
        ...

    def calculate_selection_probability(
        self,
        strategy: Strategy,
        population: List[Strategy]
    ) -> float:
        """Calculate selection probability based on fitness and diversity"""
        ...
```

**Algorithm Details**:

**Tournament Selection**:
```python
def tournament_selection(population, tournament_size=3):
    # 1. Randomly sample tournament_size strategies
    tournament = random.sample(population, tournament_size)

    # 2. Sort by Pareto rank (non-dominated first)
    tournament.sort(key=lambda s: s.pareto_rank)

    # 3. Among same rank, prefer higher crowding distance
    best = tournament[0]
    if tournament[0].pareto_rank == tournament[1].pareto_rank:
        # Tie-breaking by diversity
        best = max(tournament[:2], key=lambda s: s.crowding_distance)

    # 4. Stochastic selection (80% best, 20% random from tournament)
    if random.random() < selection_pressure:
        return best
    else:
        return random.choice(tournament)
```

---

### Component 3: Crossover Manager

**Purpose**: 組合兩個父代策略產生 offspring

**Interfaces**:
```python
class CrossoverManager:
    def __init__(
        self,
        prompt_builder: EvolutionaryPromptBuilder,
        code_validator: CodeValidator
    ):
        """Initialize crossover manager"""
        ...

    def crossover(
        self,
        parent1: Strategy,
        parent2: Strategy,
        crossover_rate: float = 0.7
    ) -> Optional[Strategy]:
        """Create offspring from two parents"""
        ...

    def parameter_crossover(
        self,
        params1: Dict[str, Any],
        params2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Uniform crossover at parameter level"""
        ...

    def generate_offspring_code(
        self,
        parent1: Strategy,
        parent2: Strategy,
        crossover_params: Dict[str, Any]
    ) -> str:
        """Generate valid Python code for offspring using LLM"""
        ...
```

**Algorithm Details**:

**Parameter Crossover** (Uniform):
```python
def parameter_crossover(params1, params2):
    offspring_params = {}

    for key in set(params1.keys()) | set(params2.keys()):
        # 50/50 chance to inherit from parent1 or parent2
        if random.random() < 0.5:
            offspring_params[key] = params1.get(key)
        else:
            offspring_params[key] = params2.get(key)

    # Special handling for factor weights (must sum to 1.0)
    if 'factor_weights' in offspring_params:
        weights = offspring_params['factor_weights']
        total = sum(weights.values())
        offspring_params['factor_weights'] = {
            k: v/total for k, v in weights.items()
        }

    return offspring_params
```

**Code Generation via LLM**:
```python
def generate_offspring_code(parent1, parent2, crossover_params):
    prompt = self.prompt_builder.build_crossover_prompt(
        parent1=parent1,
        parent2=parent2,
        target_params=crossover_params
    )

    code = self.llm_api.generate(prompt)

    # Validate generated code
    if self.code_validator.validate(code):
        return code
    else:
        # Fallback: Retry or use single-parent inheritance
        logger.warning("Crossover generated invalid code, retrying...")
        return self._fallback_crossover(parent1, parent2)
```

---

### Component 4: Mutation Manager

**Purpose**: 對 offspring 引入隨機變異

**Interfaces**:
```python
class MutationManager:
    def mutate(
        self,
        strategy: Strategy,
        mutation_rate: float = 0.1,
        mutation_strength: float = 0.1
    ) -> Strategy:
        """Apply random mutations to strategy"""
        ...

    def gaussian_mutation(
        self,
        value: float,
        sigma: float,
        bounds: Tuple[float, float]
    ) -> float:
        """Gaussian mutation with boundary constraints"""
        ...

    def mutate_parameters(
        self,
        params: Dict[str, Any],
        mutation_rate: float
    ) -> Dict[str, Any]:
        """Mutate parameters with given probability"""
        ...
```

**Algorithm Details**:

**Gaussian Mutation**:
```python
def gaussian_mutation(value, sigma=0.1, bounds=(0.0, 1.0)):
    # Add Gaussian noise
    noise = np.random.normal(0, sigma)
    mutated = value + noise * value  # Relative mutation

    # Clip to bounds
    mutated = np.clip(mutated, bounds[0], bounds[1])

    return mutated
```

**Parameter Mutation** (with adaptive rate):
```python
def mutate_parameters(params, mutation_rate=0.1):
    mutated_params = params.copy()

    for key, value in params.items():
        if random.random() < mutation_rate:
            if isinstance(value, float):
                # Gaussian mutation for numeric values
                bounds = get_parameter_bounds(key)
                mutated_params[key] = gaussian_mutation(value, sigma=0.1, bounds=bounds)

            elif isinstance(value, int):
                # Integer mutation (±1 or ±10%)
                delta = max(1, int(value * 0.1))
                mutated_params[key] = value + random.choice([-delta, delta])

    # Renormalize weights if mutated
    if 'factor_weights' in mutated_params:
        weights = mutated_params['factor_weights']
        total = sum(weights.values())
        mutated_params['factor_weights'] = {
            k: v/total for k, v in weights.items()
        }

    return mutated_params
```

---

### Component 5: Diversity Analyzer

**Purpose**: 計算族群多樣性度量，防止premature convergence

**Interfaces**:
```python
class DiversityAnalyzer:
    def calculate_jaccard_distance(
        self,
        strategy1: Strategy,
        strategy2: Strategy
    ) -> float:
        """Jaccard distance on feature sets (0=identical, 1=different)"""
        ...

    def calculate_population_diversity(
        self,
        population: List[Strategy]
    ) -> float:
        """Average pairwise Jaccard distance"""
        ...

    def calculate_crowding_distance(
        self,
        population: List[Strategy],
        pareto_front: List[Strategy]
    ) -> Dict[str, float]:
        """NSGA-II crowding distance for Pareto front"""
        ...

    def extract_feature_set(self, code: str) -> Set[str]:
        """Extract features used in strategy (e.g., {'roe', 'momentum', ...})"""
        ...
```

**Algorithm Details**:

**Jaccard Distance**:
```python
def calculate_jaccard_distance(strategy1, strategy2):
    features1 = extract_feature_set(strategy1.code)
    features2 = extract_feature_set(strategy2.code)

    intersection = len(features1 & features2)
    union = len(features1 | features2)

    return 1.0 - (intersection / union) if union > 0 else 0.0
```

**Crowding Distance** (NSGA-II):
```python
def calculate_crowding_distance(population, pareto_front):
    distances = {s.id: 0.0 for s in pareto_front}

    # For each objective
    for objective in ['sharpe_ratio', 'calmar_ratio', 'max_drawdown']:
        # Sort by objective value
        sorted_front = sorted(pareto_front, key=lambda s: getattr(s.metrics, objective))

        # Boundary solutions get infinite distance
        distances[sorted_front[0].id] = float('inf')
        distances[sorted_front[-1].id] = float('inf')

        # Interior solutions
        obj_min = getattr(sorted_front[0].metrics, objective)
        obj_max = getattr(sorted_front[-1].metrics, objective)
        obj_range = obj_max - obj_min

        if obj_range > 0:
            for i in range(1, len(sorted_front) - 1):
                prev_val = getattr(sorted_front[i-1].metrics, objective)
                next_val = getattr(sorted_front[i+1].metrics, objective)
                distances[sorted_front[i].id] += (next_val - prev_val) / obj_range

    return distances
```

---

### Component 6: Multi-objective Optimizer

**Purpose**: 管理多目標優化，識別 Pareto front

**Interfaces**:
```python
class MultiObjectiveOptimizer:
    def calculate_pareto_front(
        self,
        population: List[Strategy]
    ) -> List[Strategy]:
        """Identify non-dominated strategies"""
        ...

    def pareto_dominates(
        self,
        metrics_a: MultiObjectiveMetrics,
        metrics_b: MultiObjectiveMetrics
    ) -> bool:
        """Check if A dominates B (better in all objectives)"""
        ...

    def assign_pareto_ranks(
        self,
        population: List[Strategy]
    ) -> Dict[str, int]:
        """Assign Pareto rank to each strategy (1=best, 2=second front, ...)"""
        ...
```

**Algorithm Details**:

**Pareto Dominance**:
```python
def pareto_dominates(metrics_a, metrics_b):
    """
    A dominates B if:
    - A is better or equal in ALL objectives
    - A is strictly better in AT LEAST ONE objective
    """
    objectives = ['sharpe_ratio', 'calmar_ratio']  # Maximize
    worse_objectives = ['max_drawdown']           # Minimize

    better_in_all = True
    strictly_better_in_one = False

    for obj in objectives:
        a_val = getattr(metrics_a, obj)
        b_val = getattr(metrics_b, obj)
        if a_val < b_val:
            better_in_all = False
            break
        if a_val > b_val:
            strictly_better_in_one = True

    for obj in worse_objectives:
        a_val = getattr(metrics_a, obj)
        b_val = getattr(metrics_b, obj)
        if a_val > b_val:  # A is worse (higher drawdown)
            better_in_all = False
            break
        if a_val < b_val:  # A is better (lower drawdown)
            strictly_better_in_one = True

    return better_in_all and strictly_better_in_one
```

**Fast Non-dominated Sorting** (NSGA-II):
```python
def assign_pareto_ranks(population):
    """Assign Pareto ranks using fast non-dominated sorting"""
    ranks = {}
    fronts = [[]]  # fronts[0] = first Pareto front

    # Count dominations and dominated-by sets
    domination_count = {s.id: 0 for s in population}
    dominated_by = {s.id: [] for s in population}

    for p in population:
        for q in population:
            if p.id != q.id:
                if pareto_dominates(p.metrics, q.metrics):
                    dominated_by[p.id].append(q.id)
                elif pareto_dominates(q.metrics, p.metrics):
                    domination_count[p.id] += 1

        if domination_count[p.id] == 0:
            fronts[0].append(p)
            ranks[p.id] = 1

    # Build subsequent fronts
    front_idx = 0
    while fronts[front_idx]:
        next_front = []
        for p_id in [s.id for s in fronts[front_idx]]:
            for q_id in dominated_by[p_id]:
                domination_count[q_id] -= 1
                if domination_count[q_id] == 0:
                    q = next((s for s in population if s.id == q_id), None)
                    next_front.append(q)
                    ranks[q_id] = front_idx + 2

        front_idx += 1
        fronts.append(next_front)

    return ranks
```

---

## Data Models

### Strategy

```python
@dataclass
class Strategy:
    """Individual strategy in population"""

    # Identity
    id: str                           # UUID
    generation: int                   # Generation number (0, 1, 2, ...)
    parent_ids: List[str]             # Parent strategy IDs (for lineage)

    # Code & Parameters
    code: str                         # Python strategy code
    parameters: Dict[str, Any]        # Extracted parameters

    # Fitness & Objectives
    metrics: MultiObjectiveMetrics    # Performance metrics
    pareto_rank: int                  # Pareto front rank (1=best)
    crowding_distance: float          # Diversity measure

    # Diversity
    novelty_score: float              # Novelty relative to population
    feature_set: Set[str]             # Features used (for Jaccard)

    # Metadata
    timestamp: str                    # ISO 8601 creation time
    evaluation_time_sec: float        # Backtest duration

    def dominates(self, other: 'Strategy') -> bool:
        """Check if this strategy Pareto-dominates other"""
        return pareto_dominates(self.metrics, other.metrics)

    def to_dict(self) -> Dict:
        """Serialize to JSON"""
        return {
            'id': self.id,
            'generation': self.generation,
            'parent_ids': self.parent_ids,
            'code': self.code,
            'parameters': self.parameters,
            'metrics': asdict(self.metrics),
            'pareto_rank': self.pareto_rank,
            'crowding_distance': self.crowding_distance,
            'novelty_score': self.novelty_score,
            'feature_set': list(self.feature_set),
            'timestamp': self.timestamp,
            'evaluation_time_sec': self.evaluation_time_sec
        }

    @staticmethod
    def from_dict(data: Dict) -> 'Strategy':
        """Deserialize from JSON"""
        data['metrics'] = MultiObjectiveMetrics(**data['metrics'])
        data['feature_set'] = set(data['feature_set'])
        return Strategy(**data)
```

### MultiObjectiveMetrics

```python
@dataclass
class MultiObjectiveMetrics:
    """Multi-objective performance metrics"""

    # Primary Objectives (Maximize)
    sharpe_ratio: float               # Risk-adjusted return
    calmar_ratio: float               # Return / Max Drawdown

    # Risk Metrics (Minimize)
    max_drawdown: float               # Peak-to-trough decline (negative)

    # Secondary Metrics (Informational)
    total_return: float               # Cumulative return
    annual_return: float              # Annualized return
    win_rate: float                   # Percentage profitable trades
    avg_trade_duration_days: float    # Average holding period

    def dominates(self, other: 'MultiObjectiveMetrics') -> bool:
        """Pareto dominance check"""
        # Better in all, strictly better in at least one
        better_sharpe = self.sharpe_ratio >= other.sharpe_ratio
        better_calmar = self.calmar_ratio >= other.calmar_ratio
        better_dd = self.max_drawdown >= other.max_drawdown  # Less negative

        strictly_better = (
            self.sharpe_ratio > other.sharpe_ratio or
            self.calmar_ratio > other.calmar_ratio or
            self.max_drawdown > other.max_drawdown
        )

        return better_sharpe and better_calmar and better_dd and strictly_better
```

### Population

```python
@dataclass
class Population:
    """Collection of strategies in one generation"""

    generation: int                   # Generation number
    strategies: List[Strategy]        # All strategies in population
    pareto_front: List[Strategy]      # Non-dominated strategies
    diversity_score: float            # Average pairwise Jaccard distance
    timestamp: str                    # ISO 8601 generation completion time

    @property
    def size(self) -> int:
        return len(self.strategies)

    @property
    def best_sharpe(self) -> float:
        return max(s.metrics.sharpe_ratio for s in self.strategies)

    @property
    def avg_sharpe(self) -> float:
        return sum(s.metrics.sharpe_ratio for s in self.strategies) / self.size

    def to_dict(self) -> Dict:
        """Serialize to JSON"""
        return {
            'generation': self.generation,
            'strategies': [s.to_dict() for s in self.strategies],
            'pareto_front': [s.id for s in self.pareto_front],
            'diversity_score': self.diversity_score,
            'timestamp': self.timestamp
        }
```

### EvolutionResult

```python
@dataclass
class EvolutionResult:
    """Results from one generation of evolution"""

    generation: int                   # Generation number
    population: Population            # Final population state
    offspring_created: int            # Number of offspring generated
    offspring_valid: int              # Number passing validation
    elites_preserved: int             # Number of elite strategies carried over
    selection_time_sec: float         # Time spent in selection
    crossover_time_sec: float         # Time spent in crossover
    mutation_time_sec: float          # Time spent in mutation
    evaluation_time_sec: float        # Time spent evaluating strategies
    total_time_sec: float             # Total generation time

    # Metrics
    best_sharpe_improved: bool        # Did best Sharpe improve this generation?
    diversity_maintained: bool        # Is diversity above threshold (0.3)?
    pareto_front_size: int            # Number of non-dominated strategies

    def summary(self) -> str:
        """Human-readable summary"""
        return f"""
Generation {self.generation} Summary:
  Population Size: {self.population.size}
  Pareto Front: {self.pareto_front_size} strategies
  Best Sharpe: {self.population.best_sharpe:.4f}
  Avg Sharpe: {self.population.avg_sharpe:.4f}
  Diversity: {self.population.diversity_score:.3f}
  Offspring: {self.offspring_valid}/{self.offspring_created} valid
  Time: {self.total_time_sec:.1f}s
        """
```

---

## Error Handling

### Error Scenarios

#### Scenario 1: Crossover Generates Invalid Code

**Description**: LLM 產生的 offspring 程式碼無法通過 AST 驗證

**Handling**:
```python
def crossover(parent1, parent2, max_retries=3):
    for attempt in range(max_retries):
        try:
            code = generate_offspring_code(parent1, parent2)
            if validate_code(code):
                return Strategy(code=code, ...)
            else:
                logger.warning(f"Crossover attempt {attempt+1} failed validation")
        except Exception as e:
            logger.error(f"Crossover error: {e}")

    # Fallback: Single-parent inheritance
    logger.info("Crossover failed, falling back to mutation-only")
    return mutate(random.choice([parent1, parent2]))
```

**User Impact**: 無影響，系統自動 fallback

---

#### Scenario 2: Population Diversity Collapse

**Description**: 族群多樣性降至 threshold 以下 (0.3)

**Handling**:
```python
def check_diversity_and_adapt(population):
    diversity = calculate_population_diversity(population)

    if diversity < 0.3:
        logger.warning(f"Diversity collapse detected: {diversity:.3f}")

        # Increase mutation rate
        global MUTATION_RATE
        MUTATION_RATE *= 2.0  # 0.1 → 0.2

        # Force diversity injection
        inject_random_strategies(population, count=2)

        logger.info(f"Diversity recovery: mutation_rate={MUTATION_RATE}")
```

**User Impact**: 系統自動恢復多樣性，記錄於 log

---

#### Scenario 3: All Offspring Fail Validation

**Description**: 一代中所有 offspring 都無效

**Handling**:
```python
def evolve_generation(generation_num):
    offspring = []
    for _ in range(offspring_count):
        child = crossover_and_mutate(parents)
        if child:
            offspring.append(child)

    if len(offspring) == 0:
        logger.error(f"Generation {generation_num}: No valid offspring created")

        # Fallback: Clone elites with increased mutation
        elites = get_elite_strategies(population)
        offspring = [mutate(elite, mutation_rate=0.3) for elite in elites]

    return offspring
```

**User Impact**: 族群暫時停滯，但不會 crash

---

#### Scenario 4: LLM API Rate Limit

**Description**: OpenRouter/Gemini API 達到 rate limit

**Handling**:
```python
def generate_with_backoff(prompt, max_retries=5):
    for attempt in range(max_retries):
        try:
            return llm_api.generate(prompt)
        except RateLimitError as e:
            wait_time = 2 ** attempt  # Exponential backoff
            logger.warning(f"Rate limit hit, waiting {wait_time}s...")
            time.sleep(wait_time)

    raise RuntimeError("LLM API unavailable after all retries")
```

**User Impact**: Generation 時間延長，但不會失敗

---

## Testing Strategy

### Unit Testing (20 tests)

#### Selection Tests (5 tests)
- `test_tournament_selection_returns_valid_strategy`
- `test_selection_pressure_affects_outcome`
- `test_pareto_rank_influences_selection`
- `test_crowding_distance_breaks_ties`
- `test_select_parents_returns_unique_pairs`

#### Crossover Tests (5 tests)
- `test_parameter_crossover_uniform_distribution`
- `test_factor_weights_renormalized_after_crossover`
- `test_crossover_generates_valid_code`
- `test_crossover_fallback_on_invalid_code`
- `test_crossover_preserves_parent_features`

#### Mutation Tests (5 tests)
- `test_gaussian_mutation_within_bounds`
- `test_mutation_rate_controls_frequency`
- `test_mutation_strength_controls_magnitude`
- `test_mutated_weights_sum_to_one`
- `test_mutation_retries_on_invalid_code`

#### Diversity Tests (5 tests)
- `test_jaccard_distance_identical_strategies`
- `test_jaccard_distance_completely_different`
- `test_crowding_distance_calculation`
- `test_population_diversity_average`
- `test_diversity_collapse_triggers_adaptation`

---

### Integration Testing (5 scenarios)

#### Scenario 1: Full Evolution (5 Generations)
```python
def test_full_evolution_run():
    """Test complete evolution workflow with N=10, 5 generations"""
    pop_manager = PopulationManager(
        autonomous_loop=mock_loop,
        population_size=10,
        elite_count=2
    )

    pop_manager.initialize_population()

    for gen in range(5):
        result = pop_manager.evolve_generation(gen)

        # Assertions
        assert result.population.size == 10
        assert result.offspring_valid > 0
        assert result.pareto_front_size >= 1
        assert result.population.diversity_score > 0.2

    # Final assertions
    assert pop_manager.population[0].generation == 4
    assert pop_manager.best_sharpe >= initial_best_sharpe
```

---

#### Scenario 2: Diversity Recovery
```python
def test_diversity_recovery_mechanism():
    """Test that mutation rate adapts when diversity collapses"""
    # Create homogeneous population (low diversity)
    population = [clone_strategy(base_strategy) for _ in range(10)]

    diversity_before = calculate_population_diversity(population)
    assert diversity_before < 0.3

    # Trigger evolution
    result = pop_manager.evolve_generation(generation_num=1)

    # Verify recovery actions
    assert pop_manager.mutation_rate > 0.1  # Increased from default
    assert result.population.diversity_score > diversity_before
```

---

#### Scenario 3: Elitism Preservation
```python
def test_elitism_preserves_best_strategies():
    """Test that elite strategies are never lost"""
    initial_population = pop_manager.population.copy()
    initial_best = max(initial_population, key=lambda s: s.metrics.sharpe_ratio)

    # Evolve one generation
    result = pop_manager.evolve_generation(generation_num=1)

    # Verify elite preserved
    elite_ids = [s.id for s in pop_manager.get_elites()]
    assert initial_best.id in elite_ids
```

---

#### Scenario 4: Crossover Compatibility
```python
def test_crossover_all_parameter_types():
    """Test crossover handles all parameter types correctly"""
    parent1 = create_strategy_with_params({
        'roe_type': 'smoothed',
        'roe_window': 4,
        'liquidity_threshold': 100_000_000,
        'factor_weights': {'momentum': 0.4, 'value': 0.6}
    })

    parent2 = create_strategy_with_params({
        'roe_type': 'raw',
        'roe_window': 1,
        'liquidity_threshold': 50_000_000,
        'factor_weights': {'momentum': 0.3, 'quality': 0.7}
    })

    offspring = crossover_manager.crossover(parent1, parent2)

    # Verify valid offspring
    assert offspring is not None
    assert sum(offspring.parameters['factor_weights'].values()) == 1.0
    assert offspring.parameters['roe_window'] in [1, 4]
```

---

#### Scenario 5: Multi-objective Pareto Front
```python
def test_pareto_front_correctness():
    """Test that Pareto front identification is correct"""
    # Create population with known dominance relationships
    population = [
        create_strategy_with_metrics(sharpe=2.0, calmar=1.5, dd=-0.3),  # Pareto optimal
        create_strategy_with_metrics(sharpe=1.8, calmar=1.8, dd=-0.25), # Pareto optimal
        create_strategy_with_metrics(sharpe=1.5, calmar=1.2, dd=-0.4),  # Dominated
        create_strategy_with_metrics(sharpe=1.0, calmar=1.0, dd=-0.5),  # Dominated
    ]

    pareto_front = multi_obj_optimizer.calculate_pareto_front(population)

    assert len(pareto_front) == 2
    assert pareto_front[0].metrics.sharpe_ratio == 2.0
    assert pareto_front[1].metrics.calmar_ratio == 1.8
```

---

### End-to-End Testing

#### 20-Generation Validation Run

**Configuration**:
- Population size: N=20
- Generations: 20 (total 400 strategies)
- Duration: ~20 hours (60 min/generation)

**Success Criteria** (from requirements):
- Champion update rate ≥10%
- Rolling variance <0.5
- P-value <0.05
- Pareto front size ≥5

**Test Script**:
```python
def run_20_generation_validation():
    """Full validation test with production configuration"""

    pop_manager = PopulationManager(
        autonomous_loop=AutonomousLoop(...),
        population_size=20,
        elite_count=2,
        tournament_size=3
    )

    pop_manager.initialize_population()

    results = []
    for gen in range(20):
        print(f"\n{'='*60}")
        print(f"GENERATION {gen}")
        print(f"{'='*60}")

        result = pop_manager.evolve_generation(gen)
        results.append(result)

        print(result.summary())

        # Save checkpoint
        pop_manager.save_checkpoint(f"checkpoint_gen{gen}.json")

    # Analyze results
    analyze_evolution_results(results)

    # Check success criteria
    validate_success_criteria(results)
```

---

## Performance Optimization

### Parallelization Opportunities

**Strategy Evaluation** (Most time-consuming):
```python
def evaluate_population_parallel(population: List[Strategy]):
    """Evaluate strategies in parallel using multiprocessing"""
    with multiprocessing.Pool(processes=4) as pool:
        results = pool.map(evaluate_single_strategy, population)

    for strategy, metrics in zip(population, results):
        strategy.metrics = metrics

    return population
```

**Expected Speedup**: 4x (with 4 CPU cores)

---

### Caching Strategies

**Parameter Extraction Caching**:
```python
@lru_cache(maxsize=100)
def extract_strategy_params_cached(code: str) -> Dict[str, Any]:
    """Cache parameter extraction results"""
    return extract_strategy_params(code)
```

**Expected Savings**: ~5 seconds per generation

---

## Deployment Plan

### Phase 1: Core Implementation (Week 1-2)
- Implement all evolution components
- Unit tests (20 tests)
- Integration with autonomous loop

### Phase 2: Testing (Week 3)
- Integration tests (5 scenarios)
- 5-generation pilot validation

### Phase 3: Production Validation (Week 4)
- 20-generation full validation
- Success criteria evaluation
- Documentation and deployment

---

**Document Status**: Design Complete - Ready for Implementation
**Version**: 1.0
**Date**: 2025-10-17

**Note**: Specification documents have been pre-loaded. Do not use get-content to fetch them again.

## Task Details
- Task ID: 29
- Description: Implement parameter_crossover function
- Leverage: random module
- Requirements: R3.1

## Instructions
- Implement ONLY task 29: "Implement parameter_crossover function"
- Follow all project conventions and leverage existing code
- Mark the task as complete using: claude-code-spec-workflow get-tasks population-based-learning 29 --mode complete
- Provide a completion summary
```

## Task Completion
When the task is complete, mark it as done:
```bash
claude-code-spec-workflow get-tasks population-based-learning 29 --mode complete
```

## Next Steps
After task completion, you can:
- Execute the next task using /population-based-learning-task-[next-id]
- Check overall progress with /spec-status population-based-learning
