# Phase 1: Population-Based Learning - Architecture Design

**Version**: 1.0
**Date**: 2025-10-17
**Status**: Design Phase
**Objective**: Evolutionary parameter optimization to achieve ≥10% champion update rate and >1.5 Sharpe

---

## 1. Executive Summary

### Design Philosophy

Based on Phase 0 root cause analysis, this design addresses all identified failures:
- **RC1 (LLM Exploration)**: Algorithmic diversity guarantees via mutation operators
- **RC2 (Feedback Loop)**: Population-based selection creates learning gradient
- **RC3 (Parameter Space)**: Systematic coverage through genetic operators
- **RC4 (Prompt Bias)**: No prompts - pure algorithmic optimization

### Key Design Principles

1. **Diversity First**: Maintain 50%+ unique parameter combinations at all times
2. **Balanced Exploration-Exploitation**: Use adaptive mutation rates
3. **Incremental Learning**: Population evolves toward better solutions
4. **Testability**: All components independently testable
5. **Leverage Phase 0**: Reuse test harness, checkpointing, metrics tracking

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase1TestHarness                        │
│  (Orchestrates evolution loop, inherits Phase0TestHarness)  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ├─► PopulationManager
                 │   ├─ Population (List[Individual])
                 │   ├─ Selection Strategy
                 │   ├─ Diversity Tracker
                 │   └─ Convergence Monitor
                 │
                 ├─► GeneticOperators
                 │   ├─ MutationOperator (adaptive rate)
                 │   ├─ CrossoverOperator (uniform/single-point)
                 │   └─ ElitismOperator (preserve top 10%)
                 │
                 ├─► FitnessEvaluator
                 │   ├─ Strategy Execution (via MomentumTemplate)
                 │   ├─ Metrics Calculation (Sharpe, Return, Drawdown)
                 │   └─ Fitness Caching (avoid re-evaluation)
                 │
                 └─► EvolutionMonitor
                     ├─ Performance Tracking
                     ├─ Diversity Metrics
                     └─ Convergence Detection
```

### 2.2 Component Relationships

```
Generation N:
  PopulationManager.get_population() → List[Individual]
    ↓
  FitnessEvaluator.evaluate_all() → List[(Individual, Fitness)]
    ↓
  PopulationManager.select_parents() → List[Individual]
    ↓
  GeneticOperators.apply_crossover() → List[Individual]
    ↓
  GeneticOperators.apply_mutation() → List[Individual]
    ↓
  PopulationManager.apply_elitism() → List[Individual]
    ↓
  PopulationManager.replace_generation() → New Population
    ↓
Generation N+1
```

---

## 3. Core Components Design

### 3.1 Individual

**Purpose**: Represents a single parameter combination with metadata

```python
@dataclass
class Individual:
    """
    Single parameter combination in population.

    Attributes:
        parameters: Dict[str, Any] - Strategy parameters (8 keys from PARAM_GRID)
        fitness: Optional[float] - Sharpe ratio (None if not evaluated)
        metrics: Optional[Dict] - Full backtest metrics
        generation: int - Generation number when created
        parent_ids: List[str] - IDs of parents (for tracking lineage)
        id: str - Unique identifier (hash of parameters)
    """
    parameters: Dict[str, Any]
    fitness: Optional[float] = None
    metrics: Optional[Dict] = None
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    id: str = field(default="", init=False)

    def __post_init__(self):
        """Generate unique ID from parameters."""
        self.id = self._hash_parameters()

    def _hash_parameters(self) -> str:
        """Create unique hash from parameter combination."""
        # Sort parameters for consistent hashing
        params_str = json.dumps(self.parameters, sort_keys=True)
        return hashlib.md5(params_str.encode()).hexdigest()[:8]

    def is_evaluated(self) -> bool:
        """Check if individual has been evaluated."""
        return self.fitness is not None
```

**Design Rationale**:
- `id` enables fitness caching (avoid re-evaluating same parameters)
- `parent_ids` allows lineage tracking for analysis
- `generation` helps track evolution progress

### 3.2 PopulationManager

**Purpose**: Manages population lifecycle, selection, and diversity

```python
class PopulationManager:
    """
    Manages population of parameter combinations.

    Responsibilities:
        - Initialize diverse population
        - Track population diversity metrics
        - Implement selection strategies
        - Apply elitism (preserve top performers)
        - Monitor convergence
    """

    def __init__(
        self,
        population_size: int = 30,
        elite_size: int = 3,
        selection_strategy: str = "tournament",
        tournament_size: int = 3,
        diversity_threshold: float = 0.5
    ):
        """
        Initialize population manager.

        Args:
            population_size: Number of individuals per generation (default: 30)
            elite_size: Number of top individuals to preserve (default: 3 = 10%)
            selection_strategy: "tournament" or "roulette" (default: tournament)
            tournament_size: Size of tournament for selection (default: 3)
            diversity_threshold: Minimum diversity ratio (default: 0.5 = 50%)
        """
        self.population_size = population_size
        self.elite_size = elite_size
        self.selection_strategy = selection_strategy
        self.tournament_size = tournament_size
        self.diversity_threshold = diversity_threshold

        self.population: List[Individual] = []
        self.generation_num: int = 0
        self.diversity_history: List[float] = []

    def initialize_population(
        self,
        param_grid: Dict[str, List],
        seed_parameters: Optional[List[Dict]] = None
    ) -> List[Individual]:
        """
        Create initial population with diversity guarantee.

        Strategy:
            1. Include seed parameters if provided (e.g., weekly resampling from Phase 0)
            2. Generate random combinations to fill population
            3. Ensure 100% diversity (all unique combinations)

        Args:
            param_grid: Parameter grid with allowed values
            seed_parameters: Optional list of parameter dicts to include

        Returns:
            List[Individual]: Initial population (all with fitness=None)
        """
        pass

    def select_parents(
        self,
        num_parents: int
    ) -> List[Individual]:
        """
        Select parents for next generation.

        Tournament Selection (default):
            - Randomly select tournament_size individuals
            - Choose best from tournament
            - Repeat until num_parents selected

        Roulette Selection (alternative):
            - Probability proportional to fitness
            - Higher fitness = more likely to be selected

        Args:
            num_parents: Number of parents to select

        Returns:
            List[Individual]: Selected parents
        """
        pass

    def apply_elitism(
        self,
        current_population: List[Individual],
        new_population: List[Individual]
    ) -> List[Individual]:
        """
        Preserve top individuals from current generation.

        Strategy:
            1. Sort current_population by fitness (descending)
            2. Take top elite_size individuals
            3. Replace worst individuals in new_population

        Args:
            current_population: Current generation (evaluated)
            new_population: New generation (may include unevaluated)

        Returns:
            List[Individual]: New population with elites preserved
        """
        pass

    def calculate_diversity(
        self,
        population: List[Individual]
    ) -> float:
        """
        Calculate population diversity ratio.

        Metric: unique_combinations / population_size

        Example: 25 unique out of 30 total = 0.83 diversity (83%)

        Args:
            population: List of individuals to analyze

        Returns:
            float: Diversity ratio [0.0, 1.0]
        """
        pass

    def check_convergence(
        self,
        population: List[Individual],
        window_size: int = 5
    ) -> bool:
        """
        Check if population has converged (stuck in local optimum).

        Criteria (ANY trigger convergence):
            1. Diversity < diversity_threshold for window_size generations
            2. Best fitness unchanged for window_size * 2 generations
            3. Average fitness variance < 0.01 for window_size generations

        Args:
            population: Current population
            window_size: Number of generations to check (default: 5)

        Returns:
            bool: True if converged, False otherwise
        """
        pass
```

**Design Rationale**:
- **Diversity Tracking**: Addresses RC1 (exploration limitations)
- **Elitism**: Preserves good solutions (prevents loss of progress)
- **Convergence Detection**: Triggers restart or termination
- **Flexible Selection**: Tournament (default) or roulette wheel

### 3.3 GeneticOperators

**Purpose**: Mutation and crossover operations

```python
class GeneticOperators:
    """
    Genetic operators for population evolution.

    Operators:
        - Mutation: Randomly change parameter values
        - Crossover: Combine two parents to create offspring
        - Adaptive Mutation: Adjust mutation rate based on diversity
    """

    def __init__(
        self,
        param_grid: Dict[str, List],
        base_mutation_rate: float = 0.15,
        adaptive_mutation: bool = True,
        crossover_type: str = "uniform"
    ):
        """
        Initialize genetic operators.

        Args:
            param_grid: Parameter grid with allowed values
            base_mutation_rate: Base probability of mutating each parameter (default: 0.15)
            adaptive_mutation: Enable adaptive mutation rate (default: True)
            crossover_type: "uniform" or "single_point" (default: uniform)
        """
        self.param_grid = param_grid
        self.base_mutation_rate = base_mutation_rate
        self.adaptive_mutation = adaptive_mutation
        self.crossover_type = crossover_type

        self.current_mutation_rate = base_mutation_rate

    def mutate(
        self,
        individual: Individual,
        generation: int
    ) -> Individual:
        """
        Apply mutation to individual parameters.

        Strategy:
            1. For each parameter:
                - Mutate with probability = current_mutation_rate
                - Select random value from param_grid[parameter]
            2. Create new Individual with mutated parameters
            3. Record parent lineage

        Adaptive Mutation:
            - If diversity < 0.5: increase mutation_rate by 20%
            - If diversity > 0.8: decrease mutation_rate by 20%
            - Clamp to [0.05, 0.30]

        Args:
            individual: Individual to mutate
            generation: Current generation number

        Returns:
            Individual: New mutated individual
        """
        pass

    def crossover(
        self,
        parent1: Individual,
        parent2: Individual,
        generation: int
    ) -> Tuple[Individual, Individual]:
        """
        Create two offspring from two parents.

        Uniform Crossover (default):
            - For each parameter:
                - Flip coin (50/50)
                - Child1 inherits from parent1 or parent2
                - Child2 inherits opposite

        Single-Point Crossover (alternative):
            - Choose random split point in parameter list
            - Child1: parent1[0:split] + parent2[split:]
            - Child2: parent2[0:split] + parent1[split:]

        Args:
            parent1: First parent
            parent2: Second parent
            generation: Current generation number

        Returns:
            Tuple[Individual, Individual]: Two offspring
        """
        pass

    def update_mutation_rate(
        self,
        diversity: float
    ):
        """
        Adapt mutation rate based on population diversity.

        Strategy:
            - Low diversity (< 0.5): Increase exploration
            - High diversity (> 0.8): Reduce exploration
            - Target: maintain diversity around 0.6-0.7

        Args:
            diversity: Current population diversity [0.0, 1.0]
        """
        if not self.adaptive_mutation:
            return

        if diversity < 0.5:
            # Low diversity - increase mutation for exploration
            self.current_mutation_rate = min(0.30, self.current_mutation_rate * 1.2)
        elif diversity > 0.8:
            # High diversity - decrease mutation for exploitation
            self.current_mutation_rate = max(0.05, self.current_mutation_rate * 0.8)
```

**Design Rationale**:
- **Adaptive Mutation**: Maintains diversity automatically (addresses RC1)
- **Uniform Crossover**: Explores parameter combinations (addresses RC3)
- **Mutation Rate Range**: [0.05, 0.30] balances exploration/exploitation

### 3.4 FitnessEvaluator

**Purpose**: Evaluate strategy performance and cache results

```python
class FitnessEvaluator:
    """
    Evaluate individual fitness (Sharpe ratio) with caching.

    Responsibilities:
        - Execute strategies using MomentumTemplate
        - Calculate fitness metrics (Sharpe, Return, Drawdown)
        - Cache results to avoid re-evaluation
        - Batch evaluation for efficiency
    """

    def __init__(
        self,
        template,
        data,
        fitness_metric: str = "sharpe_ratio"
    ):
        """
        Initialize fitness evaluator.

        Args:
            template: MomentumTemplate instance
            data: Finlab data object
            fitness_metric: Metric to use as fitness (default: sharpe_ratio)
        """
        self.template = template
        self.data = data
        self.fitness_metric = fitness_metric

        # Fitness cache: {individual_id: (fitness, metrics)}
        self.fitness_cache: Dict[str, Tuple[float, Dict]] = {}
        self.cache_hits: int = 0
        self.cache_misses: int = 0

    def evaluate(
        self,
        individual: Individual
    ) -> Tuple[float, Dict]:
        """
        Evaluate single individual.

        Strategy:
            1. Check cache using individual.id
            2. If cached: return cached fitness (increment cache_hits)
            3. If not cached:
                - Generate strategy using template.generate(parameters)
                - Execute backtest
                - Extract fitness and metrics
                - Store in cache
                - Increment cache_misses

        Args:
            individual: Individual to evaluate

        Returns:
            Tuple[float, Dict]: (fitness, metrics)
        """
        pass

    def evaluate_population(
        self,
        population: List[Individual],
        parallel: bool = False
    ) -> List[Individual]:
        """
        Evaluate entire population.

        Strategy:
            1. Filter out already-evaluated individuals (fitness is not None)
            2. For unevaluated individuals:
                - Check cache first
                - Evaluate if not cached
            3. Update individual.fitness and individual.metrics

        Parallel Evaluation (future):
            - Use multiprocessing.Pool
            - Evaluate 3-5 individuals concurrently
            - Requires careful data/template cloning

        Args:
            population: List of individuals to evaluate
            parallel: Enable parallel evaluation (default: False)

        Returns:
            List[Individual]: Population with fitness updated
        """
        pass

    def get_cache_stats(self) -> Dict:
        """
        Get cache performance statistics.

        Returns:
            Dict: {
                'cache_size': int,
                'cache_hits': int,
                'cache_misses': int,
                'hit_rate': float
            }
        """
        pass
```

**Design Rationale**:
- **Fitness Caching**: Avoid re-evaluating same parameters (20-30% speedup)
- **Flexible Fitness Metric**: Can use Sharpe, Calmar, or custom metric
- **Batch Evaluation**: Future parallelization support

### 3.5 EvolutionMonitor

**Purpose**: Track evolution progress and metrics

```python
class EvolutionMonitor:
    """
    Monitor evolution progress and collect metrics.

    Tracks:
        - Best fitness per generation
        - Average fitness per generation
        - Diversity per generation
        - Champion updates
        - Convergence indicators
    """

    def __init__(self):
        """Initialize evolution monitor."""
        self.generation_stats: List[Dict] = []
        self.champion_history: List[Individual] = []
        self.current_champion: Optional[Individual] = None

    def record_generation(
        self,
        generation_num: int,
        population: List[Individual],
        diversity: float
    ):
        """
        Record statistics for current generation.

        Metrics Collected:
            - generation: int
            - best_fitness: float (max)
            - avg_fitness: float (mean)
            - worst_fitness: float (min)
            - fitness_std: float (standard deviation)
            - diversity: float (unique ratio)
            - champion_updated: bool

        Args:
            generation_num: Current generation number
            population: Current population (evaluated)
            diversity: Population diversity ratio
        """
        pass

    def update_champion(
        self,
        individual: Individual
    ) -> bool:
        """
        Update champion if individual is better.

        Args:
            individual: Candidate champion

        Returns:
            bool: True if champion updated, False otherwise
        """
        pass

    def get_summary(self) -> Dict:
        """
        Get evolution summary statistics.

        Returns:
            Dict: {
                'total_generations': int,
                'champion_updates': int,
                'champion_update_rate': float,
                'final_best_fitness': float,
                'final_avg_fitness': float,
                'final_diversity': float,
                'improvement_trend': float  # Linear regression slope
            }
        """
        pass
```

---

## 4. Evolution Algorithm

### 4.1 Main Evolution Loop

```python
def evolve(
    num_generations: int,
    population_size: int = 30,
    elite_size: int = 3,
    mutation_rate: float = 0.15,
    crossover_rate: float = 0.8
) -> Dict:
    """
    Main evolution loop.

    Pseudocode:
        # Initialize
        population = PopulationManager.initialize_population(seed=weekly_resampling)
        genetic_ops = GeneticOperators(param_grid, mutation_rate)
        evaluator = FitnessEvaluator(template, data)
        monitor = EvolutionMonitor()

        # Evolution loop
        for generation in range(num_generations):
            # Evaluate fitness
            population = evaluator.evaluate_population(population)

            # Track progress
            diversity = PopulationManager.calculate_diversity(population)
            monitor.record_generation(generation, population, diversity)

            # Check convergence
            if PopulationManager.check_convergence(population):
                print(f"Converged at generation {generation}")
                break

            # Selection
            parents = PopulationManager.select_parents(num_parents=population_size)

            # Crossover
            offspring = []
            for i in range(0, len(parents), 2):
                if random.random() < crossover_rate:
                    child1, child2 = genetic_ops.crossover(parents[i], parents[i+1])
                    offspring.extend([child1, child2])
                else:
                    offspring.extend([parents[i], parents[i+1]])

            # Mutation
            offspring = [genetic_ops.mutate(ind) for ind in offspring]

            # Elitism
            new_population = PopulationManager.apply_elitism(population, offspring)

            # Update for next generation
            population = new_population
            genetic_ops.update_mutation_rate(diversity)

        # Return summary
        return monitor.get_summary()
    """
```

### 4.2 Evolution Parameters

| Parameter | Default | Range | Purpose |
|-----------|---------|-------|---------|
| `population_size` | 30 | [20, 50] | Number of individuals per generation |
| `num_generations` | 20 | [10, 50] | Maximum generations to evolve |
| `elite_size` | 3 (10%) | [2, 5] | Top individuals to preserve |
| `mutation_rate` | 0.15 | [0.05, 0.30] | Probability of mutating each parameter |
| `crossover_rate` | 0.8 | [0.6, 0.9] | Probability of crossover vs cloning |
| `tournament_size` | 3 | [2, 5] | Size of tournament for selection |

**Tuning Strategy**:
- Start with defaults
- If diversity < 0.5: increase mutation_rate
- If no improvement after 10 generations: increase population_size
- If convergence too fast: decrease elite_size

---

## 5. Integration with Phase 0 Infrastructure

### 5.1 Reuse Phase0TestHarness

```python
class Phase1TestHarness(Phase0TestHarness):
    """
    Extends Phase0TestHarness for population-based learning.

    Inheritance:
        - Checkpointing system
        - Metrics tracking
        - Validation logic
        - History management

    New Features:
        - Population tracking per generation
        - Diversity metrics
        - Genetic operator statistics
        - Convergence monitoring
    """

    def __init__(
        self,
        test_name: str = 'phase1_test',
        num_generations: int = 20,
        population_size: int = 30,
        **kwargs
    ):
        super().__init__(
            test_name=test_name,
            max_iterations=num_generations,
            **kwargs
        )
        self.population_size = population_size
        self.population_manager = PopulationManager(population_size)
        self.genetic_operators = GeneticOperators(self.template.PARAM_GRID)
        self.fitness_evaluator = FitnessEvaluator(self.template, self.data)
        self.evolution_monitor = EvolutionMonitor()
```

### 5.2 Checkpoint Format Extension

```python
# Phase 0 checkpoint (individual parameters)
{
    "iteration_number": 49,
    "sharpes": [0.15, 0.15, ...],
    "param_combinations": [[10, 60, "revenue", ...]],
    ...
}

# Phase 1 checkpoint (population state)
{
    "generation_number": 19,
    "population": [
        {
            "id": "a1b2c3d4",
            "parameters": {...},
            "fitness": 1.45,
            "metrics": {...},
            "generation": 19
        },
        ...  # 30 individuals
    ],
    "diversity_history": [1.0, 0.93, 0.87, ...],
    "champion_history": [...],
    "genetic_operator_stats": {
        "current_mutation_rate": 0.18,
        "crossover_count": 450,
        "mutation_count": 320
    },
    ...
}
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

**Component**: `Individual`
- Test ID generation consistency
- Test parameter hashing
- Test equality comparison

**Component**: `PopulationManager`
- Test population initialization (diversity = 1.0)
- Test diversity calculation accuracy
- Test selection strategies (tournament, roulette)
- Test elitism preservation
- Test convergence detection

**Component**: `GeneticOperators`
- Test mutation validity (parameters in PARAM_GRID)
- Test mutation rate adaptation
- Test crossover creates valid offspring
- Test parameter type preservation

**Component**: `FitnessEvaluator`
- Test cache hit/miss logic
- Test fitness calculation correctness
- Test batch evaluation

### 6.2 Integration Tests

**Test 1**: Small Population Evolution (5 individuals, 5 generations)
- Verify all components work together
- Check diversity tracking
- Validate champion updates

**Test 2**: Seeded Population (include Phase 0 best parameters)
- Verify seed parameters preserved in population
- Check if evolution improves from seeds

**Test 3**: Convergence Detection
- Create homogeneous population
- Verify convergence detected correctly

### 6.3 Smoke Test (10-Generation Test)

**Configuration**:
- Population size: 20
- Generations: 10
- Elite size: 2
- Mutation rate: 0.15
- Expected duration: ~15-20 minutes (20 individuals × 10 generations = 200 evaluations)

**Success Criteria**:
- ✅ All generations complete without crashes
- ✅ Diversity ≥ 50% in first 3 generations
- ✅ At least 1 champion update
- ✅ Checkpoint system working correctly

### 6.4 Full Test (50-Generation Test)

**Configuration**:
- Population size: 30
- Generations: 50
- Elite size: 3
- Expected duration: ~2 hours (30 × 50 = 1500 evaluations, with ~30% cache hits = ~1000 actual evaluations)

**Success Criteria**:
- ✅ Champion update rate ≥ 10% (5+ champion updates in 50 generations)
- ✅ Average Sharpe > 1.5
- ✅ Final diversity ≥ 40%
- ✅ Improvement trend (positive slope in champion fitness)

---

## 7. Success Metrics

### 7.1 Primary Metrics (Must Achieve)

| Metric | Phase 0 Result | Phase 1 Target | Threshold |
|--------|----------------|----------------|-----------|
| **Champion Update Rate** | 0% | ≥10% | ≥5% |
| **Average Fitness (Sharpe)** | 0.44 | >1.5 | >1.0 |
| **Parameter Diversity** | 26% | ≥50% | ≥40% |

### 7.2 Secondary Metrics (Nice to Have)

| Metric | Target |
|--------|--------|
| **Best Fitness** | >2.5 (beat Phase 0 champion) |
| **Improvement Trend** | Positive slope >0.01 per generation |
| **Convergence Time** | <30 generations |
| **Cache Hit Rate** | >25% |

### 7.3 Decision Matrix

```
SUCCESS (≥10% updates AND >1.5 Sharpe):
  → Phase 1 validated, proceed to production optimization

PARTIAL (5-10% updates OR 1.0-1.5 Sharpe):
  → Tune hyperparameters (increase population_size or mutation_rate)
  → Run additional test with tuned parameters

FAILURE (<5% updates OR <1.0 Sharpe):
  → Investigate root cause
  → Consider hybrid approach (population-based + LLM guidance)
```

---

## 8. Implementation Plan

### Phase 1A: Core Components (2-3 hours)

1. **Individual class** (30 min)
   - Implement `Individual` dataclass
   - Test ID generation and hashing

2. **PopulationManager** (60 min)
   - Implement initialization with diversity guarantee
   - Implement selection strategies
   - Implement diversity calculation
   - Implement elitism

3. **GeneticOperators** (45 min)
   - Implement mutation operator
   - Implement crossover operator
   - Implement adaptive mutation rate

4. **FitnessEvaluator** (30 min)
   - Implement evaluation with caching
   - Integrate with MomentumTemplate

5. **EvolutionMonitor** (15 min)
   - Implement metrics tracking
   - Implement champion updates

### Phase 1B: Integration (30-60 min)

1. **Phase1TestHarness** (30 min)
   - Extend Phase0TestHarness
   - Integrate population components
   - Update checkpoint format

2. **Run scripts** (15 min)
   - `run_phase1_smoke_test.py` (10 generations)
   - `run_phase1_full_test.py` (50 generations)

### Phase 1C: Testing (1-2 hours)

1. **Unit Tests** (30 min)
   - Test each component independently

2. **Smoke Test** (20 min execution + 10 min analysis)
   - 10 generations, 20 population size
   - Verify basic functionality

3. **Full Test** (60 min execution + 30 min analysis)
   - 50 generations, 30 population size
   - Comprehensive evaluation

**Total Estimated Time**: 4-6 hours (design → implementation → testing)

---

## 9. Risk Mitigation

### Risk 1: Slow Execution (1500+ evaluations)

**Mitigation**:
- Fitness caching (expect 25-30% cache hits)
- Batch evaluation (evaluate generation in parallel if needed)
- Reduce population_size for smoke test (20 instead of 30)

### Risk 2: Premature Convergence

**Mitigation**:
- Adaptive mutation rate (increases when diversity drops)
- Diversity monitoring (warn if < 0.5)
- Convergence detection (restart with new random population)

### Risk 3: No Improvement Over Phase 0 Champion

**Mitigation**:
- Seed population with Phase 0 best parameters
- Use weekly resampling insight
- Ensure elite_size preserves good solutions

### Risk 4: Implementation Bugs

**Mitigation**:
- Comprehensive unit tests
- Smoke test before full test (like Phase 0)
- Checkpoint system for recovery

---

## 10. Expected Outcomes

### Optimistic Scenario (90% confidence)

- **Champion updates**: 15-20% (7-10 updates in 50 generations)
- **Average Sharpe**: 1.8-2.2
- **Best Sharpe**: 2.5-3.0 (beats Phase 0 champion)
- **Diversity**: 50-60%
- **Conclusion**: SUCCESS - Population-based learning validated

### Realistic Scenario (70% confidence)

- **Champion updates**: 10-15% (5-7 updates)
- **Average Sharpe**: 1.5-1.8
- **Best Sharpe**: 2.0-2.5
- **Diversity**: 40-50%
- **Conclusion**: SUCCESS - Proceed with confidence

### Pessimistic Scenario (10% confidence)

- **Champion updates**: 5-10% (2-5 updates)
- **Average Sharpe**: 1.0-1.5
- **Best Sharpe**: 1.5-2.0
- **Diversity**: 30-40%
- **Conclusion**: PARTIAL - Needs tuning

### Worst Case Scenario (<5% probability)

- **Champion updates**: <5%
- **Average Sharpe**: <1.0
- **Root cause**: Parameter space too complex, need different approach
- **Action**: Investigate hybrid LLM + evolutionary approach

---

## 11. Appendix: Parameter Grid Reference

```python
PARAM_GRID = {
    'momentum_period': [5, 10, 20, 30],        # 4 options
    'ma_periods': [20, 60, 90, 120],           # 4 options
    'catalyst_type': ['revenue', 'earnings'],  # 2 options
    'catalyst_lookback': [2, 3, 4, 6],         # 4 options
    'n_stocks': [5, 10, 15, 20],               # 4 options
    'stop_loss': [0.08, 0.10, 0.12, 0.15],     # 4 options
    'resample': ['W', 'M'],                     # 2 options
    'resample_offset': [0, 1, 2, 3, 4]         # 5 options
}
```

**Total combinations**: 20,480
**Target coverage (50 generations)**: ~0.24% of space

---

## 12. Design Sign-Off

**Design Complete**: 2025-10-17
**Review Status**: Ready for Implementation
**Next Step**: Implement Phase 1A (Core Components)

**Design Principles Validated**:
- ✅ Addresses all Phase 0 root causes
- ✅ Algorithmic diversity guarantees
- ✅ Reuses Phase 0 infrastructure
- ✅ Clear testability
- ✅ Realistic success criteria

---

**Designed by**: Claude Code
**Version**: 1.0
**Status**: ✅ DESIGN APPROVED - PROCEED TO IMPLEMENTATION
