# Factor Graph System - API Reference

**Version**: 2.0+
**Last Updated**: 2025-10-23

---

## Table of Contents

1. [Factor API](#factor-api)
2. [Strategy API](#strategy-api)
3. [Mutation Operators API](#mutation-operators-api)
4. [Factory Registry API](#factory-registry-api)
5. [YAML Interpreter API](#yaml-interpreter-api)
6. [Evaluation API](#evaluation-api)

---

## Factor API

### Factor Class

**Location**: `src/factor_graph/factor.py`

```python
@dataclass
class Factor:
    """
    Atomic strategy component in Factor Graph architecture.
    """
    id: str
    name: str
    category: FactorCategory
    inputs: List[str]
    outputs: List[str]
    logic: Callable[[pd.DataFrame, Dict[str, Any]], pd.DataFrame]
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
```

#### Constructor

```python
Factor(
    id: str,                    # Unique identifier (e.g., "rsi_14")
    name: str,                  # Human-readable name (e.g., "RSI Momentum Signal")
    category: FactorCategory,   # Factor category enum
    inputs: List[str],          # Required data columns (e.g., ["close"])
    outputs: List[str],         # Produced data columns (e.g., ["rsi", "signal"])
    logic: Callable,            # Computation function
    parameters: Dict[str, Any] = {},  # Tunable parameters
    description: str = ""       # Optional description
)
```

**Raises**:
- `ValueError`: If id is empty, invalid format, or inputs/outputs contain duplicates
- `TypeError`: If category is not FactorCategory enum or inputs/outputs not list of strings

#### Methods

##### validate_inputs()

```python
def validate_inputs(self, available_columns: List[str]) -> bool:
    """
    Check if all required inputs are available.

    Args:
        available_columns: List of column names available in the data

    Returns:
        True if all required inputs are in available_columns

    Example:
        >>> factor.validate_inputs(["open", "high", "low", "close", "volume"])
        True
    """
```

##### execute()

```python
def execute(self, data: pd.DataFrame) -> pd.DataFrame:
    """
    Execute factor logic and return data with new columns.

    Args:
        data: Input DataFrame with required input columns

    Returns:
        DataFrame with new columns added (specified in self.outputs)

    Raises:
        KeyError: If required input columns are missing
        RuntimeError: If logic function fails or doesn't produce expected outputs

    Example:
        >>> result = factor.execute(data)
        >>> "rsi" in result.columns
        True
    """
```

---

## Strategy API

### Strategy Class

**Location**: `src/factor_graph/strategy.py`

```python
class Strategy:
    """
    Trading strategy represented as DAG of Factors.
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
```

#### Methods

##### add_factor()

```python
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
        ValueError: If adding factor would create cycle or dependency not found

    Example:
        >>> strategy.add_factor(rsi_factor)
        >>> strategy.add_factor(entry_factor, depends_on=["rsi_14"])
    """
```

##### remove_factor()

```python
def remove_factor(self, factor_id: str) -> None:
    """
    Remove factor from strategy.

    Args:
        factor_id: ID of factor to remove

    Raises:
        ValueError: If factor not found or removing would orphan dependent factors

    Example:
        >>> strategy.remove_factor("old_indicator")
    """
```

##### validate()

```python
def validate(self) -> bool:
    """
    Validate strategy DAG integrity.

    Checks:
    1. DAG is acyclic (topological sorting possible)
    2. All factor input dependencies satisfied
    3. At least one factor produces position signals
    4. No orphaned factors

    Returns:
        True if strategy is valid

    Raises:
        ValueError: If validation fails with detailed error message

    Example:
        >>> strategy.validate()
        True
    """
```

##### to_pipeline()

```python
def to_pipeline(self, data: pd.DataFrame) -> pd.DataFrame:
    """
    Compile strategy DAG to executable data pipeline.

    Args:
        data: Input DataFrame with OHLCV data

    Returns:
        DataFrame with all factor outputs computed in dependency order

    Raises:
        ValueError: If strategy validation fails

    Example:
        >>> result = strategy.to_pipeline(data)
        >>> positions = result['positions']
    """
```

##### get_lineage()

```python
def get_lineage(self) -> List[str]:
    """
    Get full lineage from initial template to current strategy.

    Returns:
        List of strategy IDs from root to current

    Example:
        >>> lineage = strategy.get_lineage()
        >>> print(f"Generations: {len(lineage)}")
    """
```

##### copy()

```python
def copy(self) -> "Strategy":
    """
    Create deep copy of strategy.

    Returns:
        New Strategy instance with same factors and structure

    Example:
        >>> mutated = strategy.copy()
        >>> mutated.id = "mutated_v1"
    """
```

---

## Mutation Operators API

### add_factor()

**Location**: `src/factor_graph/mutations.py`

```python
def add_factor(
    strategy: Strategy,
    new_factor: Factor,
    depends_on: List[str],
    insert_before: Optional[str] = None
) -> Strategy:
    """
    Add new factor to strategy with dependency validation.

    Args:
        strategy: Original strategy (not modified)
        new_factor: Factor to add
        depends_on: List of factor IDs new factor depends on
        insert_before: Optional factor ID to insert before

    Returns:
        New Strategy instance with factor added

    Raises:
        ValueError: If addition would create cycle or dependencies not found

    Example:
        >>> mutated = add_factor(
        ...     strategy=original,
        ...     new_factor=volatility_filter,
        ...     depends_on=["momentum_20"],
        ...     insert_before="entry_signal"
        ... )
    """
```

### remove_factor()

```python
def remove_factor(
    strategy: Strategy,
    factor_id: str,
    remove_dependents: bool = False
) -> Strategy:
    """
    Remove factor from strategy.

    Args:
        strategy: Original strategy (not modified)
        factor_id: ID of factor to remove
        remove_dependents: If True, also remove all dependent factors

    Returns:
        New Strategy instance with factor removed

    Raises:
        ValueError: If factor not found or has dependents (unless remove_dependents=True)

    Example:
        >>> mutated = remove_factor(
        ...     strategy=original,
        ...     factor_id="old_indicator",
        ...     remove_dependents=False
        ... )
    """
```

### replace_factor()

```python
def replace_factor(
    strategy: Strategy,
    old_factor_id: str,
    new_factor_name: str,
    parameters: Optional[Dict[str, Any]] = None,
    match_category: bool = True
) -> Strategy:
    """
    Replace existing factor with new factor from registry.

    Args:
        strategy: Original strategy (not modified)
        old_factor_id: ID of factor to replace
        new_factor_name: Name of new factor in registry
        parameters: Parameters for new factor (uses defaults if None)
        match_category: If True, require same category

    Returns:
        New Strategy instance with factor replaced

    Raises:
        ValueError: If old factor not found, new factor not in registry,
                   or category mismatch (when match_category=True)

    Example:
        >>> mutated = replace_factor(
        ...     strategy=original,
        ...     old_factor_id="momentum_20",
        ...     new_factor_name="ma_filter_factor",
        ...     parameters={"ma_periods": 60},
        ...     match_category=True
        ... )
    """
```

### mutate_parameters()

```python
def mutate_parameters(
    strategy: Strategy,
    factor_id: str,
    mutation_rate: float = 0.1,
    mutation_scale: float = 0.2
) -> Strategy:
    """
    Mutate factor parameters using Gaussian noise.

    Args:
        strategy: Original strategy (not modified)
        factor_id: ID of factor to mutate
        mutation_rate: Probability of mutating each parameter (0.0-1.0)
        mutation_scale: Scale of mutation relative to parameter value (0.0-1.0)

    Returns:
        New Strategy instance with mutated parameters

    Raises:
        ValueError: If factor not found or parameters invalid

    Example:
        >>> mutated = mutate_parameters(
        ...     strategy=original,
        ...     factor_id="rsi_14",
        ...     mutation_rate=0.1,
        ...     mutation_scale=0.2
        ... )
    """
```

---

## Factory Registry API

### FactorRegistry Class

**Location**: `src/factor_library/registry.py`

```python
class FactorRegistry:
    """
    Central registry for factor creation and discovery.
    """
    @staticmethod
    def get_instance() -> "FactorRegistry":
        """Get singleton instance."""
        pass

    def register(
        self,
        name: str,
        factory: Callable,
        category: FactorCategory,
        parameters: Dict[str, Any],
        description: str = ""
    ) -> None:
        """
        Register factor factory function.

        Args:
            name: Factor name (e.g., "ma_filter_factor")
            factory: Factory function that creates Factor instances
            category: Factor category
            parameters: Default parameters with validation ranges
            description: Human-readable description
        """
        pass

    def create_factor(
        self,
        name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Factor:
        """
        Create factor instance from registry.

        Args:
            name: Factor name
            parameters: Override default parameters

        Returns:
            Factor instance

        Raises:
            ValueError: If name not found or parameters invalid
        """
        pass

    def list_factors(self) -> List[str]:
        """List all registered factor names."""
        pass

    def get_factors_by_category(
        self,
        category: FactorCategory
    ) -> List[str]:
        """
        Get factor names by category.

        Args:
            category: Factor category to filter by

        Returns:
            List of factor names in that category
        """
        pass

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """
        Get factor metadata.

        Args:
            name: Factor name

        Returns:
            Dictionary with category, parameters, description

        Raises:
            ValueError: If name not found
        """
        pass
```

---

## YAML Interpreter API

### YAMLInterpreter Class

**Location**: `src/mutation/yaml/interpreter.py`

```python
class YAMLInterpreter:
    """
    Safe YAML configuration to Strategy interpreter.
    """
    def __init__(self, registry: Optional[FactorRegistry] = None):
        """
        Initialize interpreter.

        Args:
            registry: FactorRegistry instance (uses singleton if None)
        """
        pass

    def parse_yaml_file(self, filepath: str) -> Strategy:
        """
        Parse YAML file to Strategy.

        Args:
            filepath: Path to YAML configuration file

        Returns:
            Strategy instance

        Raises:
            ValueError: If YAML is invalid or factors not found
            FileNotFoundError: If filepath doesn't exist
        """
        pass

    def parse_yaml_string(self, yaml_string: str) -> Strategy:
        """
        Parse YAML string to Strategy.

        Args:
            yaml_string: YAML configuration as string

        Returns:
            Strategy instance

        Raises:
            ValueError: If YAML is invalid or factors not found
        """
        pass

    def validate_yaml(self, yaml_string: str) -> Tuple[bool, Optional[str]]:
        """
        Validate YAML configuration without creating Strategy.

        Args:
            yaml_string: YAML configuration as string

        Returns:
            (is_valid, error_message) tuple

        Example:
            >>> is_valid, error = interpreter.validate_yaml(yaml_str)
            >>> if not is_valid:
            ...     print(f"Invalid YAML: {error}")
        """
        pass
```

---

## Evaluation API

### MultiObjectiveEvaluator Class

**Location**: `src/evaluation/multi_objective_evaluator.py`

```python
class MultiObjectiveEvaluator:
    """
    Multi-objective fitness evaluation for strategies.
    """
    def evaluate(
        self,
        strategy: Strategy,
        data: pd.DataFrame
    ) -> MultiObjectiveMetrics:
        """
        Evaluate strategy with multi-objective metrics.

        Args:
            strategy: Strategy to evaluate
            data: Backtest data

        Returns:
            MultiObjectiveMetrics with all calculated metrics

        Raises:
            RuntimeError: If backtest fails
        """
        pass
```

### MultiObjectiveMetrics Class

```python
@dataclass
class MultiObjectiveMetrics:
    """
    Container for all multi-objective fitness metrics.
    """
    # Primary metrics
    sharpe_ratio: float
    calmar_ratio: float

    # Risk metrics
    max_drawdown: float
    volatility: float

    # Robustness metrics
    win_rate: float
    profit_factor: float
    avg_holding_period: float

    # Stability metrics
    drawdown_duration: float
    recovery_time: float

    # Pareto ranking
    pareto_rank: int = 0
    crowding_distance: float = 0.0

    def dominates(self, other: "MultiObjectiveMetrics") -> bool:
        """Check if this metrics Pareto-dominates other."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        pass

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MultiObjectiveMetrics":
        """Create metrics from dictionary."""
        pass
```

---

## Type Definitions

### FactorCategory Enum

```python
class FactorCategory(Enum):
    """Factor categories for classification and mutation."""
    MOMENTUM = "momentum"
    VALUE = "value"
    QUALITY = "quality"
    RISK = "risk"
    EXIT = "exit"
    ENTRY = "entry"
    SIGNAL = "signal"
```

### MutationRecord Class

```python
@dataclass
class MutationRecord:
    """
    Record of a single mutation operation.
    """
    mutation_id: str
    parent_strategy_id: str
    child_strategy_id: str
    mutation_type: str
    tier: int
    timestamp: datetime
    factor_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    parent_fitness: Optional[float] = None
    child_fitness: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
```

---

## Error Handling

### Common Exceptions

```python
# Factor validation errors
ValueError("Factor id cannot be empty")
ValueError("Factor must have at least one input column")
TypeError("Factor category must be FactorCategory enum")

# Strategy validation errors
ValueError("Adding factor would create cycle")
ValueError("Factor X missing inputs: ['col']")
ValueError("Strategy does not produce position signals")
ValueError("Strategy contains orphaned factors")

# Mutation errors
ValueError("Cannot remove factor 'X': factors ['Y'] depend on it")
ValueError("Factor 'X' not found in strategy")
ValueError("New factor 'X' not found in registry")
ValueError("Category mismatch: expected EXIT, got MOMENTUM")
ValueError("Invalid parameters for factor 'X': param 'Y' out of range [min, max]")

# Registry errors
ValueError("Factor 'X' not registered")
ValueError("Invalid parameters: unknown parameters: {'param'}")
```

---

## Examples

### Complete API Usage Example

```python
from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.strategy import Strategy
from src.factor_graph.mutations import add_factor, replace_factor
from src.factor_library.registry import FactorRegistry
from src.evaluation.multi_objective_evaluator import MultiObjectiveEvaluator

# 1. Create custom factor
def my_logic(data, params):
    data["signal"] = (data["close"] > data["close"].rolling(params["period"]).mean()).astype(int)
    return data

my_factor = Factor(
    id="my_signal",
    name="My Custom Signal",
    category=FactorCategory.SIGNAL,
    inputs=["close"],
    outputs=["signal"],
    logic=my_logic,
    parameters={"period": 20}
)

# 2. Build strategy
strategy = Strategy(id="my_strategy", generation=0)
strategy.add_factor(my_factor)

# 3. Use registry
registry = FactorRegistry.get_instance()
entry_factor = registry.create_factor("entry_signal_factor")
strategy.add_factor(entry_factor, depends_on=["my_signal"])

# 4. Validate
strategy.validate()

# 5. Mutate
mutated = replace_factor(
    strategy=strategy,
    old_factor_id="my_signal",
    new_factor_name="ma_filter_factor",
    parameters={"ma_periods": 60},
    match_category=False
)

# 6. Evaluate
evaluator = MultiObjectiveEvaluator()
metrics = evaluator.evaluate(mutated, data)
print(f"Sharpe: {metrics.sharpe_ratio:.2f}")
```

---

**Version**: 2.0+ (Production Ready)
**Last Updated**: 2025-10-23
**Spec**: structural-mutation-phase2
