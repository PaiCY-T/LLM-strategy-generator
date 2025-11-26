# Design Document - Structural Mutation Phase 2.0+ (Factor Graph System)

## Executive Summary

Phase 2.0+ adopts a **Factor Graph architecture** that fundamentally transforms how strategies are represented and evolved. Instead of treating strategies as parameter dictionaries, strategies are now **Directed Acyclic Graphs (DAGs) of atomic Factors**.

**Key Design Decisions**:
- Factor-based composability for structural innovation
- Three-tier mutation system (Safe → Domain-Specific → Advanced)
- Natural integration of Phase 1 exit mutations as Factor library
- YAML configuration as safe entry point (Phase 2a integration)
- DAG validation through topological sorting

**Architecture Benefits**:
- ✅ Breakthrough innovation through Factor composition
- ✅ Unified Phase 1/2a/2.0 architecture (no redundancy)
- ✅ Validation-first approach (prevent invalid strategies before backtest)
- ✅ Long-term maintainability and extensibility
- ✅ Expert-validated design direction

## System Architecture

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                     Phase 2.0+ Factor Graph System                  │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐           │
│  │    Factor    │   │   Strategy   │   │   Mutation   │           │
│  │   Library    │──▶│  Composition │──▶│   Engine     │           │
│  └──────────────┘   └──────────────┘   └──────────────┘           │
│         │                    │                   │                  │
│         │                    ▼                   ▼                  │
│         │           ┌──────────────┐   ┌──────────────┐           │
│         │           │  DAG         │   │  Three-Tier  │           │
│         │           │  Validator   │   │  Mutations   │           │
│         │           └──────────────┘   └──────────────┘           │
│         │                                        │                  │
│         │                                        ▼                  │
│         │                                ┌──────────────┐           │
│         │                                │  Tier 1:     │           │
│         │                                │  YAML Config │           │
│         │                                ├──────────────┤           │
│         └───────────────────────────────▶│  Tier 2:     │           │
│                                          │  Factor Ops  │           │
│                                          ├──────────────┤           │
│                                          │  Tier 3:     │           │
│                                          │  AST Mutations│          │
│                                          └──────────────┘           │
│                                                   │                  │
│                                                   ▼                  │
│                                          ┌──────────────┐           │
│                                          │  Evaluation  │           │
│                                          │   Engine     │           │
│                                          └──────────────┘           │
│                                                                      │
├────────────────────────────────────────────────────────────────────┤
│                     Supporting Infrastructure                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐           │
│  │  Population  │   │   Template   │   │   Finlab     │           │
│  │   Manager    │   │   Registry   │   │   Library    │           │
│  └──────────────┘   └──────────────┘   └──────────────┘           │
│                                                                      │
└────────────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Factor Base Class

**Purpose**: Atomic strategy component with defined inputs, outputs, and execution logic

**Interface**:
```python
from dataclasses import dataclass
from typing import List, Callable, Dict, Any
from enum import Enum

class FactorCategory(Enum):
    """Categories for factor classification and mutation."""
    MOMENTUM = "momentum"
    VALUE = "value"
    QUALITY = "quality"
    RISK = "risk"
    EXIT = "exit"
    ENTRY = "entry"
    SIGNAL = "signal"

@dataclass
class Factor:
    """
    Atomic strategy component in Factor Graph architecture.

    A Factor represents a single computational step in a trading strategy,
    with explicit dependencies (inputs) and outputs. Factors can be composed
    into DAGs to create complete trading strategies.

    Attributes:
        id: Unique identifier for this factor instance
        name: Human-readable name (e.g., "RSI_Momentum", "ATR_StopLoss")
        category: Factor category for mutation and discovery
        inputs: List of required data columns (dependencies)
        outputs: List of produced data columns
        logic: Callable that implements factor computation
        parameters: Tunable parameters for optimization
        description: Human-readable description for documentation

    Example:
        >>> rsi_factor = Factor(
        ...     id="rsi_14",
        ...     name="RSI Momentum Signal",
        ...     category=FactorCategory.MOMENTUM,
        ...     inputs=["close"],
        ...     outputs=["rsi_14", "rsi_signal"],
        ...     logic=calculate_rsi,
        ...     parameters={"period": 14, "overbought": 70, "oversold": 30}
        ... )
    """
    id: str
    name: str
    category: FactorCategory
    inputs: List[str]
    outputs: List[str]
    logic: Callable[[pd.DataFrame, Dict[str, Any]], pd.DataFrame]
    parameters: Dict[str, Any]
    description: str = ""

    def validate_inputs(self, available_columns: List[str]) -> bool:
        """Check if all required inputs are available."""
        return all(inp in available_columns for inp in self.inputs)

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        """Execute factor logic and return data with new columns."""
        return self.logic(data, self.parameters)
```

#### 2. Strategy DAG

**Purpose**: Compose Factors into executable trading strategies with dependency tracking

**Interface**:
```python
from typing import Dict, List, Optional
import networkx as nx

class Strategy:
    """
    Trading strategy represented as DAG of Factors.

    A Strategy is a composition of Factors arranged in a Directed Acyclic Graph
    where edges represent data dependencies. The Strategy validates DAG integrity,
    compiles to executable pipeline, and supports Factor-level mutations.

    Attributes:
        id: Unique strategy identifier
        generation: Generation number in evolution
        parent_ids: Parent strategy IDs for lineage tracking
        factors: Dictionary mapping factor IDs to Factor instances
        dag: NetworkX DiGraph representing factor dependencies
        parameters: Strategy-level parameters
        metrics: Performance metrics from backtest

    Example:
        >>> strategy = Strategy(id="strat_001", generation=0)
        >>> strategy.add_factor(rsi_factor)
        >>> strategy.add_factor(atr_stop_loss, depends_on=["rsi_14"])
        >>> strategy.validate()  # Check DAG integrity
        >>> pipeline = strategy.to_pipeline()  # Compile to executable code
    """

    def __init__(
        self,
        id: str,
        generation: int = 0,
        parent_ids: List[str] = None
    ):
        self.id = id
        self.generation = generation
        self.parent_ids = parent_ids or []
        self.factors: Dict[str, Factor] = {}
        self.dag: nx.DiGraph = nx.DiGraph()
        self.parameters: Dict[str, Any] = {}
        self.metrics: Optional[MultiObjectiveMetrics] = None

    def add_factor(
        self,
        factor: Factor,
        depends_on: List[str] = None
    ) -> None:
        """
        Add factor to strategy DAG.

        Args:
            factor: Factor instance to add
            depends_on: List of factor IDs this factor depends on

        Raises:
            ValueError: If adding factor would create cycle
        """
        self.factors[factor.id] = factor
        self.dag.add_node(factor.id, factor=factor)

        for dependency in (depends_on or []):
            if dependency not in self.factors:
                raise ValueError(f"Dependency {dependency} not found in strategy")
            self.dag.add_edge(dependency, factor.id)

        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.dag):
            # Rollback
            self.factors.pop(factor.id)
            self.dag.remove_node(factor.id)
            raise ValueError(f"Adding factor {factor.id} would create cycle")

    def remove_factor(self, factor_id: str) -> None:
        """
        Remove factor from strategy.

        Args:
            factor_id: ID of factor to remove

        Raises:
            ValueError: If removing factor would orphan dependent factors
        """
        if factor_id not in self.factors:
            raise ValueError(f"Factor {factor_id} not found")

        # Check for dependent factors
        dependents = list(self.dag.successors(factor_id))
        if dependents:
            raise ValueError(
                f"Cannot remove {factor_id}: factors {dependents} depend on it"
            )

        self.factors.pop(factor_id)
        self.dag.remove_node(factor_id)

    def validate(self) -> bool:
        """
        Validate strategy DAG integrity.

        Checks:
        1. DAG is acyclic (topological sorting possible)
        2. All factor input dependencies satisfied
        3. At least one factor produces position signals
        4. No orphaned factors (all factors reachable from base data)

        Returns:
            True if strategy is valid, raises ValueError otherwise
        """
        # Check 1: DAG is acyclic
        if not nx.is_directed_acyclic_graph(self.dag):
            raise ValueError("Strategy contains cycles")

        # Check 2: Input dependencies
        available_columns = ["open", "high", "low", "close", "volume"]  # Base data

        for factor_id in nx.topological_sort(self.dag):
            factor = self.factors[factor_id]
            if not factor.validate_inputs(available_columns):
                missing = set(factor.inputs) - set(available_columns)
                raise ValueError(
                    f"Factor {factor_id} missing inputs: {missing}"
                )
            available_columns.extend(factor.outputs)

        # Check 3: Position signals produced
        has_position_signal = any(
            "positions" in factor.outputs or "signal" in factor.outputs
            for factor in self.factors.values()
        )
        if not has_position_signal:
            raise ValueError("Strategy does not produce position signals")

        # Check 4: No orphaned factors
        if not nx.is_weakly_connected(self.dag):
            raise ValueError("Strategy contains orphaned factors")

        return True

    def to_pipeline(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Compile strategy DAG to executable data pipeline.

        Args:
            data: Input DataFrame with OHLCV data

        Returns:
            DataFrame with all factor outputs computed in dependency order

        Example:
            >>> data = finlab.data.get("price:收盤價", start="2020-01-01")
            >>> result = strategy.to_pipeline(data)
            >>> positions = result['positions']  # Final position signals
        """
        # Ensure strategy is valid
        self.validate()

        # Execute factors in topological order
        result = data.copy()

        for factor_id in nx.topological_sort(self.dag):
            factor = self.factors[factor_id]
            result = factor.execute(result)

        return result

    def get_lineage(self) -> List[str]:
        """Get full lineage from initial template to current strategy."""
        # TODO: Implement lineage tracking through parent_ids
        return [self.id] + self.parent_ids
```

#### 3. Three-Tier Mutation System

**Purpose**: Progressive risk mutation system from safe configuration to advanced AST modifications

**Architecture**:

```python
from abc import ABC, abstractmethod
from enum import Enum

class MutationTier(Enum):
    """Risk levels for mutation operations."""
    TIER_1_SAFE = 1      # YAML configuration, schema-validated
    TIER_2_DOMAIN = 2    # Factor-level mutations, domain-safe
    TIER_3_ADVANCED = 3  # AST-level mutations, powerful but risky

class MutationOperator(ABC):
    """Base class for all mutation operators."""

    @abstractmethod
    def get_tier(self) -> MutationTier:
        """Return mutation tier (risk level)."""
        pass

    @abstractmethod
    def mutate(self, strategy: Strategy, config: dict) -> Strategy:
        """Apply mutation to strategy, return new strategy."""
        pass

    @abstractmethod
    def validate(self, strategy: Strategy) -> bool:
        """Validate mutation result."""
        pass
```

**Tier 1: Safe Configuration** (YAML → Factors)
```python
class Tier1ConfigurationMutator(MutationOperator):
    """
    Safe mutation through YAML configuration.

    LLM generates YAML describing factor composition,
    system validates against schema and instantiates factors.

    Example YAML:
        strategy:
          name: "Momentum with ATR Exit"
          factors:
            - id: rsi_signal
              type: RSIFactor
              parameters:
                period: 14
                overbought: 70
            - id: atr_stop
              type: ATRStopLossFactor
              parameters:
                multiplier: 2.0
              depends_on: [rsi_signal]
    """

    def get_tier(self) -> MutationTier:
        return MutationTier.TIER_1_SAFE

    def mutate(self, strategy: Strategy, config: dict) -> Strategy:
        """
        Generate new strategy from YAML configuration.

        Steps:
        1. LLM generates YAML config
        2. Validate against JSON schema
        3. Instantiate factors from factor library
        4. Build strategy DAG
        5. Validate DAG integrity
        """
        yaml_config = config.get("yaml_config")

        # Validate schema
        self._validate_yaml_schema(yaml_config)

        # Create new strategy
        new_strategy = Strategy(
            id=f"{strategy.id}_tier1_{self._generate_id()}",
            generation=strategy.generation + 1,
            parent_ids=[strategy.id]
        )

        # Instantiate factors from config
        for factor_spec in yaml_config['factors']:
            factor = self._instantiate_factor(factor_spec)
            new_strategy.add_factor(
                factor,
                depends_on=factor_spec.get('depends_on', [])
            )

        # Validate complete strategy
        new_strategy.validate()

        return new_strategy
```

**Tier 2: Factor Mutations** (Domain-Specific Operations)
```python
class Tier2FactorMutator(MutationOperator):
    """
    Factor-level mutations: add, remove, replace, mutate parameters.

    Operations:
    - add_factor(): Add new factor with dependency validation
    - remove_factor(): Remove factor with orphan checking
    - replace_factor(): Swap factor with same-category alternative
    - mutate_parameters(): Gaussian parameter mutation (Phase 1 integration)
    """

    def get_tier(self) -> MutationTier:
        return MutationTier.TIER_2_DOMAIN

    def mutate(self, strategy: Strategy, config: dict) -> Strategy:
        """Apply factor-level mutation."""
        operation = config.get("operation")

        new_strategy = strategy.copy()

        if operation == "add_factor":
            factor = self._select_factor_from_library(config)
            new_strategy.add_factor(factor, depends_on=config.get("depends_on"))

        elif operation == "remove_factor":
            new_strategy.remove_factor(config["factor_id"])

        elif operation == "replace_factor":
            self._replace_factor(new_strategy, config)

        elif operation == "mutate_parameters":
            self._mutate_parameters(new_strategy, config)

        else:
            raise ValueError(f"Unknown Tier 2 operation: {operation}")

        new_strategy.validate()
        return new_strategy

    def _select_factor_from_library(self, config: dict) -> Factor:
        """Select factor from library based on category and constraints."""
        category = config.get("category", random.choice(list(FactorCategory)))
        candidates = FACTOR_LIBRARY.get_by_category(category)
        return random.choice(candidates)

    def _replace_factor(self, strategy: Strategy, config: dict) -> None:
        """Replace factor with same-category alternative."""
        factor_id = config["factor_id"]
        old_factor = strategy.factors[factor_id]

        # Find replacement from same category
        candidates = FACTOR_LIBRARY.get_by_category(old_factor.category)
        candidates = [f for f in candidates if f.id != old_factor.id]

        if not candidates:
            raise ValueError(f"No alternatives found for {old_factor.category}")

        new_factor = random.choice(candidates)

        # Preserve dependencies
        predecessors = list(strategy.dag.predecessors(factor_id))
        successors = list(strategy.dag.successors(factor_id))

        # Remove old, add new
        strategy.remove_factor(factor_id)
        strategy.add_factor(new_factor, depends_on=predecessors)

        # Reconnect successors
        for successor_id in successors:
            strategy.dag.add_edge(new_factor.id, successor_id)
```

**Tier 3: Structural Mutations** (AST-Level Advanced)
```python
class Tier3StructuralMutator(MutationOperator):
    """
    AST-level structural mutations for advanced evolution.

    Operations:
    - modify_factor_logic(): Modify factor computation logic
    - combine_signals(): Create composite signal factors
    - adaptive_parameters(): Add dynamic parameter adjustment

    Leverages Phase 1 AST mutation capabilities.
    """

    def get_tier(self) -> MutationTier:
        return MutationTier.TIER_3_ADVANCED

    def mutate(self, strategy: Strategy, config: dict) -> Strategy:
        """Apply AST-level mutation to factor logic."""
        operation = config.get("operation")
        factor_id = config.get("factor_id")

        new_strategy = strategy.copy()
        factor = new_strategy.factors[factor_id]

        if operation == "modify_logic":
            # Use Phase 1 AST mutation capabilities
            new_logic = self._modify_factor_ast(factor, config)
            factor.logic = new_logic

        elif operation == "combine_signals":
            # Create composite factor from multiple signals
            composite_factor = self._create_composite_factor(
                new_strategy, config
            )
            new_strategy.add_factor(composite_factor)

        elif operation == "adaptive_parameters":
            # Add dynamic parameter adjustment
            adaptive_factor = self._create_adaptive_factor(factor, config)
            new_strategy.add_factor(adaptive_factor)

        new_strategy.validate()
        return new_strategy
```

#### 4. Factor Library

**Purpose**: Registry of pre-built factors extracted from templates and Phase 1

**Structure**:
```python
class FactorLibrary:
    """
    Central registry of reusable factors.

    Populated from:
    - MomentumTemplate: RSI, MACD, Moving Average factors
    - TurtleTemplate: Breakout, Channel, Position Sizing factors
    - Phase 1 Exit Mutations: Stop-Loss, Take-Profit, Trailing Stop factors
    - Custom Factors: User-defined factor implementations
    """

    def __init__(self):
        self._factors: Dict[str, Factor] = {}
        self._by_category: Dict[FactorCategory, List[Factor]] = {}

    def register(self, factor: Factor) -> None:
        """Register factor in library."""
        self._factors[factor.id] = factor

        if factor.category not in self._by_category:
            self._by_category[factor.category] = []
        self._by_category[factor.category].append(factor)

    def get_by_category(self, category: FactorCategory) -> List[Factor]:
        """Get all factors in category."""
        return self._by_category.get(category, [])

    def get_by_id(self, factor_id: str) -> Optional[Factor]:
        """Get factor by ID."""
        return self._factors.get(factor_id)

    def search(self, query: str) -> List[Factor]:
        """Search factors by name or description."""
        results = []
        for factor in self._factors.values():
            if query.lower() in factor.name.lower() or \
               query.lower() in factor.description.lower():
                results.append(factor)
        return results

# Global factor library instance
FACTOR_LIBRARY = FactorLibrary()
```

## Phase Implementation Roadmap

### Phase A: Foundation (Week 1-2)

**Goal**: Implement Factor/Strategy base classes

**Deliverables**:
1. `src/factor_graph/factor.py`: Factor dataclass and validation
2. `src/factor_graph/strategy.py`: Strategy DAG with validation
3. `tests/factor_graph/test_factor.py`: Factor unit tests
4. `tests/factor_graph/test_strategy.py`: Strategy DAG tests

**Success Criteria**:
- Manual strategy composition mimics MomentumTemplate
- DAG validation catches cycles and missing dependencies
- to_pipeline() compiles to executable backtest

### Phase B: Migration (Week 3-4)

**Goal**: Extract Factor library from templates

**Deliverables**:
1. `src/factor_graph/library.py`: FactorLibrary with registration
2. `src/factors/momentum.py`: 10-15 Momentum factors
3. `src/factors/turtle.py`: Turtle breakout/channel factors
4. `src/factors/exit.py`: Phase 1 exit strategy factors
5. `docs/FACTOR_CATALOG.md`: Factor documentation

**Success Criteria**:
- Factor library contains 30+ factors across categories
- EA can compose strategies from Factor library
- 10-generation validation produces valid strategies

### Phase C: Evolution (Week 5-6)

**Goal**: Implement Tier 2 mutation operators

**Deliverables**:
1. `src/mutation/tier2_mutator.py`: Factor mutation operators
2. `src/mutation/operators.py`: add/remove/replace/mutate implementations
3. `tests/mutation/test_tier2.py`: Tier 2 mutation tests

**Success Criteria**:
- add_factor() validates dependencies successfully
- remove_factor() detects orphaned factors
- replace_factor() finds same-category alternatives
- 20-generation validation shows structural evolution

### Phase D: Advanced Capabilities (Week 7-8)

**Goal**: Add Tier 1 (YAML) and Tier 3 (AST)

**Deliverables**:
1. `src/mutation/tier1_config.py`: YAML configuration mutator
2. `src/mutation/tier3_structural.py`: AST-level mutations
3. `config/factor_schema.json`: YAML validation schema
4. `tests/mutation/test_tier1.py`: Configuration tests
5. `tests/mutation/test_tier3.py`: AST mutation tests

**Success Criteria**:
- YAML configuration validates against schema
- Tier 3 integrates Phase 1 AST capabilities
- 50-generation validation runs full three-tier system
- Adaptive tier selection routes based on risk tolerance

## Integration with Existing Systems

### Population Manager Integration

```python
class PopulationManager:
    """Updated to work with Factor Graph strategies."""

    def evaluate_population(self, strategies: List[Strategy]) -> None:
        """Backtest Factor Graph strategies."""
        for strategy in strategies:
            # Compile strategy DAG to executable pipeline
            try:
                strategy.validate()
                # Execute backtest using compiled pipeline
                metrics = self._backtest_strategy(strategy)
                strategy.metrics = metrics
            except Exception as e:
                logger.error(f"Strategy {strategy.id} evaluation failed: {e}")
                strategy.metrics = None

    def _backtest_strategy(self, strategy: Strategy) -> MultiObjectiveMetrics:
        """Execute Factor Graph strategy backtest."""
        # Get data
        data = finlab.data.get("price:收盤價", start="2020-01-01")

        # Compile strategy to executable pipeline
        result = strategy.to_pipeline(data)

        # Extract positions and run finlab backtest
        positions = result['positions']
        report = finlab.backtest.sim(positions, resample="M")

        # Calculate metrics
        return MultiObjectiveMetrics(
            sharpe_ratio=report.sharpe,
            annual_return=report.annual_return,
            max_drawdown=report.max_drawdown,
            calmar_ratio=report.calmar_ratio,
            total_return=report.total_return,
            win_rate=report.win_rate,
            success=True
        )
```

### Phase 1 Exit Mutations Integration

Phase 1 exit mutation framework becomes specialized Factor category:

```python
# Extract from Phase 1
from src.mutation.exit_mutator import ExitStrategyMutator
from src.mutation.exit_detector import ExitMechanismDetector

# Wrap as Tier 3 capability
class ExitFactorMutator(Tier3StructuralMutator):
    """Leverage Phase 1 AST mutations for exit factors."""

    def __init__(self):
        self.exit_mutator = ExitStrategyMutator()
        self.exit_detector = ExitMechanismDetector()

    def modify_factor_ast(self, factor: Factor, config: dict) -> Callable:
        """Use Phase 1 AST mutation on exit factor logic."""
        # Convert factor logic to code
        code = inspect.getsource(factor.logic)

        # Apply Phase 1 exit mutation
        mutated_code = self.exit_mutator.mutate(code, config)

        # Compile back to callable
        return self._code_to_callable(mutated_code)
```

## Validation and Safety

### DAG Validation Pipeline

1. **Topological Sort**: Ensure no cycles in factor dependencies
2. **Input Validation**: All factor inputs satisfied by predecessors or base data
3. **Output Validation**: At least one factor produces position signals
4. **Connectivity**: No orphaned factors isolated from base data
5. **Type Safety**: Factor inputs/outputs match expected data types

### Mutation Safety

**Tier 1 Safety**:
- JSON schema validation for YAML configuration
- Factor library lookup (only registered factors allowed)
- DAG integrity check before instantiation

**Tier 2 Safety**:
- Dependency validation for add_factor()
- Orphan detection for remove_factor()
- Category matching for replace_factor()
- Parameter bounds checking for mutate_parameters()

**Tier 3 Safety**:
- AST validation (Phase 1 capabilities)
- Security checking (no file I/O, network access)
- Execution sandboxing
- Rollback on validation failure

## Performance Optimizations

### DAG Compilation Caching

```python
class Strategy:
    def __init__(self, ...):
        self._compiled_pipeline: Optional[Callable] = None

    def to_pipeline(self, data: pd.DataFrame) -> pd.DataFrame:
        """Cache compiled pipeline for reuse."""
        if self._compiled_pipeline is None:
            self._compiled_pipeline = self._compile_dag()
        return self._compiled_pipeline(data)
```

### Parallel Factor Execution

For factors with no dependencies, execute in parallel:

```python
def _execute_parallel(self, data: pd.DataFrame) -> pd.DataFrame:
    """Execute independent factors in parallel."""
    layers = self._get_dependency_layers()

    for layer in layers:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(self.factors[fid].execute, data)
                for fid in layer
            ]
            results = [f.result() for f in futures]
            data = self._merge_results(data, results)

    return data
```

## Success Metrics

### Technical Metrics
- **Factor Library Size**: >30 factors by end of Phase B
- **DAG Complexity**: Average 3-5 layers deep, 5-10 factors wide
- **Validation Speed**: <100ms for typical strategy DAG
- **Mutation Success Rate**: >60% Tier 2, >40% Tier 3

### Performance Metrics
- **Sharpe Ratio**: Achieve >2.5 breakthrough (primary goal)
- **Factor Diversity**: >10 distinct factor patterns in population
- **Structural Innovation**: Novel factor compositions not in initial templates
- **Efficiency**: Breakthrough within 100 generations

## References

- **Phase 2.0+ Fusion Decision**: `PHASE2_FUSION_DECISION.md`
- **Phase 1 Exit Mutations**: `src/mutation/exit_*.py`
- **Population-based Learning**: `.claude/specs/population-based-learning/design.md`
- **NetworkX Documentation**: https://networkx.org/documentation/stable/

---

**Document Version**: 2.0 (Phase 2.0+ - Factor Graph System)
**Last Updated**: 2025-10-20
**Status**: ✅ **APPROVED** - Ready for Phase A Implementation
