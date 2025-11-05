# Design Document: CombinationTemplate Phase 1.5

**Spec ID**: combination-template-phase15
**Status**: Draft
**Version**: 1.0
**Last Updated**: 2025-10-20

---

## 1. Architecture Overview

### 1.1 System Context

```
┌─────────────────────────────────────────────────────────────┐
│                  Population Manager                         │
│  (No changes - template agnostic)                          │
└────────────┬──────────────────────────────┬────────────────┘
             │                              │
             ▼                              ▼
┌────────────────────────┐    ┌────────────────────────────┐
│  Existing Templates    │    │  NEW: CombinationTemplate  │
│  - TurtleTemplate      │    │                            │
│  - MomentumTemplate    │    │  - Weighted allocation     │
│  - MastiffTemplate     │    │  - Multi-template rebal.   │
│  - FactorTemplate      │    │  - Independent mutation    │
└────────────────────────┘    └────────────────────────────┘
             │                              │
             └──────────────┬───────────────┘
                            ▼
               ┌─────────────────────────┐
               │  Template Registry      │
               │  (Auto-discovery)       │
               └─────────────────────────┘
```

### 1.2 Design Philosophy

**Principle 1: Maximum Code Reuse**
- Leverage 100% of existing template infrastructure
- Zero modifications to population_manager.py, mutation.py, diversity.py

**Principle 2: Fail-Safe Design**
- Invalid combinations raise clear errors early
- Degenerate strategies detected and logged
- Easy rollback (remove from registry)

**Principle 3: Data-Driven Validation**
- Every decision backed by backtest results
- Comparative analysis vs. single-template baselines
- Statistical significance testing (p<0.05)

---

## 2. Component Design

### 2.1 CombinationTemplate Class

**Location**: `src/templates/combination_template.py`

**Responsibilities**:
1. Instantiate multiple sub-templates with independent parameters
2. Allocate positions based on weighted strategy
3. Rebalance portfolio according to frequency
4. Handle parameter mutation (delegate to sub-templates)
5. Validate combinations (no duplicate templates, valid weights)

**Class Structure**:
```python
class CombinationTemplate(StrategyTemplate):
    """
    Weighted combination of existing strategy templates.

    Purpose: Validate if template combination can exceed single-template ceiling.
    Expected Sharpe: >2.5 (vs. Turtle baseline 1.5-2.5)

    Architecture:
    - Delegates signal generation to sub-templates
    - Combines positions using weighted allocation
    - Rebalances at specified frequency (M/W-FRI)

    Example Configuration:
        templates: ['turtle', 'momentum']
        weights: [0.7, 0.3]
        rebalance: 'M'
    """

    PARAM_GRID = {
        'templates': [...],      # Template combinations
        'weights': [...],        # Allocation weights
        'rebalance': ['M', 'W-FRI']
    }

    def __init__(self, params: Dict[str, Any]):
        """Initialize with validation."""

    def generate_positions(self, data: FinlabDataFrame) -> pd.Series:
        """
        Weighted combination of sub-template positions.

        Algorithm:
        1. Generate positions from each sub-template
        2. Normalize positions to sum to 1.0
        3. Apply weights: final_position = sum(weight_i * position_i)
        4. Rebalance at specified frequency
        """

    def mutate_parameters(self, mutation_rate: float) -> Dict[str, Any]:
        """Delegate mutation to sub-template parameters."""
```

### 2.2 Parameter Grid Design

**Design Rationale**: Balance exploration vs. exploitation

```python
PARAM_GRID = {
    'templates': [
        # 2-template combinations (proven templates first)
        ['turtle', 'momentum'],           # Trend + reversal
        ['turtle', 'mastiff'],            # Conservative blend
        ['momentum', 'mastiff'],          # Balanced

        # 3-template combinations (more exploration)
        ['turtle', 'momentum', 'mastiff'] # Full diversification
    ],

    'weights': [
        # 2-template weights
        [0.5, 0.5],           # Equal weight
        [0.7, 0.3],           # Dominant + satellite
        [0.8, 0.2],           # Primary + hedge

        # 3-template weights
        [0.4, 0.4, 0.2],      # Balanced with small hedge
        [0.5, 0.3, 0.2]       # Tiered allocation
    ],

    'rebalance': ['M', 'W-FRI']  # Monthly vs. weekly
}

# Total configurations: 4 + 2 = 6 template combos × (3 + 2) weights × 2 rebalance
# = ~30-40 unique configurations (sufficient for 20-generation test)
```

**Search Space Justification**:
- **Templates**: Start with proven templates (Turtle Sharpe 1.5-2.5)
- **Weights**: Test equal, dominant, and satellite strategies
- **Rebalance**: Monthly (lower turnover) vs. Weekly (more responsive)

### 2.3 Position Generation Algorithm

**Challenge**: Combine multiple template signals into single position vector

**Solution**: Weighted sum with normalization

```python
def generate_positions(self, data: FinlabDataFrame) -> pd.Series:
    """
    Step 1: Generate individual template positions
    """
    sub_positions = []
    for template_name, weight in zip(self.templates, self.weights):
        template = self._instantiate_template(template_name)
        positions = template.generate_positions(data)

        # Normalize to sum to 1.0 (position sizing)
        positions_norm = positions / positions.sum()

        sub_positions.append(positions_norm * weight)

    """
    Step 2: Combine with weights
    """
    combined_positions = sum(sub_positions)

    """
    Step 3: Rebalance at frequency
    """
    if self.rebalance == 'M':
        combined_positions = combined_positions.resample('M').last().ffill()
    elif self.rebalance == 'W-FRI':
        combined_positions = combined_positions.resample('W-FRI').last().ffill()

    return combined_positions
```

**Edge Cases**:
- **Empty positions**: If all sub-templates return empty, return empty Series
- **NaN handling**: Forward-fill missing values, drop if still NaN
- **Weight validation**: Must sum to 1.0 (±0.01 tolerance)

### 2.4 Mutation Strategy

**Key Insight**: Templates and weights should mutate independently

```python
def mutate_parameters(self, mutation_rate: float) -> Dict[str, Any]:
    """
    Mutation operates at two levels:
    1. Template-level: Which templates to combine (structural)
    2. Weight-level: How to allocate (quantitative)

    Strategy:
    - Templates: 10% chance to swap one template
    - Weights: Gaussian mutation (σ = 0.1), renormalize
    - Rebalance: 5% chance to toggle M ↔ W-FRI
    """
    mutated = self.params.copy()

    # Mutate template selection (10% chance)
    if random.random() < 0.1:
        available = ['turtle', 'momentum', 'mastiff', 'factor']
        idx = random.randint(0, len(mutated['templates'])-1)
        mutated['templates'][idx] = random.choice(available)

    # Mutate weights (Gaussian, renormalize)
    if random.random() < mutation_rate:
        weights = np.array(mutated['weights'])
        weights += np.random.normal(0, 0.1, size=len(weights))
        weights = np.clip(weights, 0.1, 0.9)  # Avoid extreme allocations
        mutated['weights'] = (weights / weights.sum()).tolist()

    # Mutate rebalance frequency (5% chance)
    if random.random() < 0.05:
        mutated['rebalance'] = 'W-FRI' if mutated['rebalance'] == 'M' else 'M'

    return mutated
```

### 2.5 Validation & Error Handling

**Pre-execution Validation**:
```python
def _validate_params(self, params: Dict[str, Any]):
    """Run at __init__ time."""
    # Check templates exist
    for template in params['templates']:
        if template not in AVAILABLE_TEMPLATES:
            raise ValueError(f"Unknown template: {template}")

    # Check weights
    weights = params['weights']
    if len(weights) != len(params['templates']):
        raise ValueError("Weights must match templates count")

    if not (0.99 <= sum(weights) <= 1.01):
        raise ValueError(f"Weights must sum to 1.0, got {sum(weights)}")

    # Check rebalance frequency
    if params['rebalance'] not in ['M', 'W-FRI']:
        raise ValueError(f"Invalid rebalance: {params['rebalance']}")
```

**Runtime Error Handling**:
- **Data issues**: Log warning, return empty positions
- **Template failures**: Catch exceptions, log failure, exclude from combination
- **Performance degradation**: Track Sharpe <0, flag as degenerate

---

## 3. Integration Points

### 3.1 Template Registry

**Modification**: Add CombinationTemplate to registry

**Location**: `src/utils/template_registry.py`

```python
# Existing templates
TEMPLATE_REGISTRY = {
    'turtle': TurtleTemplate,
    'momentum': MomentumTemplate,
    'mastiff': MastiffTemplate,
    'factor': FactorTemplate,

    # NEW: Combination template
    'combination': CombinationTemplate  # Auto-discovery enabled
}
```

**Impact**: Zero changes to population_manager.py (automatic discovery)

### 3.2 Testing Infrastructure

**Unit Tests**: `tests/templates/test_combination_template.py`

```python
class TestCombinationTemplate:
    def test_valid_initialization(self):
        """Valid params should initialize successfully."""

    def test_invalid_weights(self):
        """Weights not summing to 1.0 should raise error."""

    def test_position_generation(self):
        """Positions should be weighted sum of sub-templates."""

    def test_mutation(self):
        """Mutation should preserve weight sum = 1.0."""

    def test_rebalancing(self):
        """Monthly vs. weekly rebalancing should differ."""
```

**Integration Test**: 10-generation smoke test

```python
# Run via: python -m pytest tests/integration/test_combination_template_integration.py
def test_10generation_smoke_test():
    """
    Success criteria:
    - Population evolves for 10 generations
    - At least 50% strategies have Sharpe >0
    - Best strategy Sharpe >1.0
    - No crashes or exceptions
    """
```

### 3.3 Validation Test

**20-Generation Validation**: Reuse `run_20generation_validation.py`

**Configuration**:
```python
# Modify to use CombinationTemplate
config = {
    'population_size': 20,
    'generations': 20,
    'template': 'combination',  # NEW: Use CombinationTemplate
    'elite_count': 2
}
```

**Success Metrics**:
- ✅ Best Sharpe >2.5 (exceeds Turtle ceiling)
- ✅ Rolling variance <0.5 (stability)
- ✅ P-value <0.05 (statistical significance)
- ✅ Pareto front size ≥5 (diversity)

---

## 4. Data Flow

### 4.1 Strategy Generation Flow

```
PopulationManager.initialize_population()
         │
         ▼
Template Registry: Select 'combination'
         │
         ▼
CombinationTemplate.__init__(params)
  - templates: ['turtle', 'momentum']
  - weights: [0.7, 0.3]
  - rebalance: 'M'
         │
         ▼
generate_positions(data)
  ├─► TurtleTemplate.generate_positions() → positions_turtle
  └─► MomentumTemplate.generate_positions() → positions_momentum
         │
         ▼
  Weighted sum: 0.7 * positions_turtle + 0.3 * positions_momentum
         │
         ▼
  Rebalance at monthly frequency
         │
         ▼
  Return combined_positions → BacktestEngine
```

### 4.2 Mutation Flow

```
PopulationManager.evolve_generation()
         │
         ▼
Mutation.mutate_strategy(combination_strategy)
         │
         ▼
CombinationTemplate.mutate_parameters(mutation_rate=0.1)
  ├─► 10% chance: Swap one template
  ├─► mutation_rate chance: Mutate weights (Gaussian)
  └─► 5% chance: Toggle rebalance frequency
         │
         ▼
Validate mutated params (_validate_params)
         │
         ▼
Return new mutated strategy
```

---

## 5. Performance Considerations

### 5.1 Computational Complexity

**Position Generation**: O(N × T)
- N = number of stocks
- T = number of sub-templates (2-3)
- Expected: 2-3× single template time (acceptable)

**Memory**: O(N × G × P)
- G = generations (20)
- P = population size (20)
- Expected: ~500MB (within limits)

### 5.2 Optimization Opportunities

**Caching**: Cache sub-template positions per generation
```python
@functools.lru_cache(maxsize=128)
def _get_template_positions(template_name, params_hash, data_hash):
    """Cache positions to avoid redundant computation."""
```

**Lazy Evaluation**: Only compute positions when needed (defer to backtest)

**Parallel Execution**: Future optimization if validation shows promise

---

## 6. Testing Strategy

### 6.1 Unit Test Coverage (Target: ≥80%)

| Component | Tests | Coverage |
|-----------|-------|----------|
| Parameter validation | 5 tests | 100% |
| Position generation | 8 tests | 90% |
| Mutation | 6 tests | 85% |
| Rebalancing | 4 tests | 80% |
| Error handling | 5 tests | 100% |

### 6.2 Integration Test Scenarios

**Scenario 1: Happy Path**
- Valid 2-template combination (Turtle + Momentum)
- 10 generations, population size 10
- Expected: Convergence to stable Sharpe >1.5

**Scenario 2: Edge Case**
- 3-template combination with unequal weights
- Monthly rebalancing
- Expected: Lower turnover, stable performance

**Scenario 3: Mutation Stress Test**
- High mutation rate (0.5)
- Expected: Diverse population, no crashes

### 6.3 Validation Test Protocol

**20-Generation Validation**:
1. Run with 20 population size, 20 generations
2. Record best Sharpe per generation
3. Compare against Turtle baseline (1.5-2.5)
4. Statistical significance test (t-test, p<0.05)
5. Analyze failure modes if Sharpe ≤2.5

---

## 7. Failure Modes & Mitigations

| Failure Mode | Detection | Mitigation |
|--------------|-----------|------------|
| Degenerate positions (all zeros) | Check positions.sum() == 0 | Return empty, log warning |
| Weight drift (mutation) | Validate sum(weights) ≈ 1.0 | Renormalize after mutation |
| Template incompatibility | Exception during position gen | Catch, log, return empty |
| Performance < single template | Compare Sharpe in validation | Expected outcome, proceed to structural mutation |
| Memory exhaustion | Monitor memory usage | Reduce population size |

---

## 8. Decision Gate Criteria

**After 20-Generation Validation**:

### Scenario A: Success (Sharpe >2.5)
**Action**:
- Optimize combination logic
- Expand to more templates (e.g., factor-based)
- End Phase 1.5, no structural mutation needed
- Document findings in Phase 2 spec

### Scenario B: Failure (Sharpe ≤2.5)
**Action**:
- Analyze failure modes (weights, rebalancing, diversity)
- Document learnings
- Proceed to structural mutation design (Hybrid approach)
- Reference this experiment in design justification

### Scenario C: Inconclusive (High variance)
**Action**:
- Extend to 50-generation test
- Increase population size to 30
- Statistical analysis of variance sources
- Re-evaluate after extended test

---

## 9. Rollback Plan

**If Integration Fails**:
1. Remove CombinationTemplate from template_registry.py
2. Delete src/templates/combination_template.py
3. Delete tests/templates/test_combination_template.py
4. Verify existing tests still pass (regression check)

**Estimated Rollback Time**: <10 minutes

---

## 10. Future Enhancements (Out of Scope for Phase 1.5)

**Phase 2 Possibilities** (if validation successful):
- Dynamic weight adjustment based on recent performance
- Correlation-aware template selection (avoid redundancy)
- Risk parity allocation (volatility-weighted)
- Multi-objective optimization (Sharpe + Calmar + Sortino)
- Template-specific logic fusion (merge factor conditions)

**Phase 3 Possibilities** (if structural mutation needed):
- Hybrid approach (structured core + LLM assistance)
- Factor Graph Evolution (DAG-based strategy representation)
- Domain-Specific Language (AST-based mutation)

---

## 11. Appendix: Design Decisions

### D1: Why Weighted Sum vs. Voting?
**Decision**: Weighted sum of positions
**Rationale**: Smoother transitions, easier to reason about, natural interpolation
**Alternative**: Majority voting (rejected: too discrete, information loss)

### D2: Why Independent Sub-Template Parameters?
**Decision**: Each sub-template has independent parameter mutation
**Rationale**: Preserves proven template logic, easier debugging
**Alternative**: Shared parameters (rejected: too complex, violates SRP)

### D3: Why Monthly/Weekly Rebalancing?
**Decision**: Fixed frequency rebalancing
**Rationale**: Simple, predictable, transaction cost control
**Alternative**: Dynamic rebalancing based on signals (rejected: out of scope for Phase 1.5)

### D4: Why 2-3 Templates Max?
**Decision**: Limit combinations to 2-3 templates
**Rationale**: Avoid over-diversification (diminishing returns), computational efficiency
**Alternative**: Unlimited templates (rejected: explosion of search space)
