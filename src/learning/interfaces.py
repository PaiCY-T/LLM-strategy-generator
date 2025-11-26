"""Learning Module Protocol Interfaces - TDD GREEN Phase.

This module defines @runtime_checkable Protocol interfaces for core learning
components, enabling duck typing with runtime validation and API contract
enforcement.

**TDD Phase: GREEN (Minimal Implementation)**

Design Principles:
    1. Protocols define WHAT, not HOW - structural subtyping via duck typing
    2. @runtime_checkable enables isinstance() checks at runtime
    3. Minimal interface surface - only essential methods/properties
    4. No implementation - pure contracts

Protocols Defined:
    - IChampionTracker: Champion strategy management interface
    - IIterationHistory: Iteration persistence interface
    - IErrorClassifier: Error categorization interface

Usage Example:
    >>> from src.learning.interfaces import IChampionTracker
    >>> from src.learning.champion_tracker import ChampionTracker
    >>>
    >>> tracker = ChampionTracker(...)
    >>> assert isinstance(tracker, IChampionTracker)  # Runtime check
    >>>
    >>> # Type hint usage
    >>> def process_champion(tracker: IChampionTracker) -> None:
    ...     if tracker.champion:
    ...         print(f"Champion Sharpe: {tracker.champion.metrics['sharpe_ratio']}")

Design Reference:
    See .spec-workflow/specs/api-mismatch-prevention-system/DESIGN_IMPROVEMENTS.md
    Section 1: Runtime Validation with @runtime_checkable Protocols

Next Steps (REFACTOR Phase):
    - Add comprehensive docstrings with behavioral contracts
    - Document pre-conditions and post-conditions
    - Add usage examples
    - Document idempotency guarantees
"""

from typing import Protocol, runtime_checkable, Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.learning.iteration_history import IterationRecord
    from src.learning.champion_tracker import ChampionStrategy
    from src.backtest.metrics import StrategyMetrics


@runtime_checkable
class IStrategy(Protocol):
    """Unified strategy interface for Template, LLM, and Factor Graph modes.

    **TDD Phase: GREEN - Spec A Task 4.1**

    This Protocol defines the DOMAIN contract for strategy objects. It does
    NOT include persistence methods (save/load) as those belong to the
    Repository layer (HallOfFameRepository).

    Design Decision (Architecture Analysis):
        - Adding save/load here would violate Single Responsibility Principle
        - Would create Active Record anti-pattern (domain + persistence mixed)
        - Would reduce testability (domain models require I/O)
        - Would reduce flexibility (cannot swap persistence layer)

    Implementation Requirements:
        - All three strategy modes must implement these properties/methods
        - Runtime validation via isinstance(obj, IStrategy)
        - No inheritance required (structural subtyping)

    Supported Strategy Types:
        - Template Mode: Template-based strategies (MomentumTemplate, etc.)
        - LLM Mode: LLM-generated strategies
        - Factor Graph Mode: Factor Graph DAG strategies (src.evolution.types.Strategy)

    Example Usage:
        >>> from src.learning.interfaces import IStrategy
        >>> from src.evolution.types import Strategy
        >>>
        >>> # Factor Graph Strategy implements IStrategy via duck typing
        >>> strategy = Strategy(id='test-001', generation=5, ...)
        >>> assert isinstance(strategy, IStrategy)  # Runtime check
        >>>
        >>> # Type hint usage
        >>> def compare_strategies(s1: IStrategy, s2: IStrategy) -> bool:
        ...     return s1.dominates(s2)

    Architecture Reference:
        See .spec-workflow/specs/unified-strategy-interface/design.md
        Section: IStrategy Protocol (NEW)
    """

    @property
    def id(self) -> str:
        """Strategy unique identifier.

        Behavioral Contract:
        - MUST return non-empty string
        - MUST be stable (same value across calls)
        - MUST be unique within the system

        Post-conditions:
        - len(return_value) > 0
        - return_value is immutable for lifetime of strategy

        Returns:
            str: Unique strategy identifier

        Example:
            - Template Mode: "template_iter_42"
            - LLM Mode: "llm_iter_42"
            - Factor Graph: "a1b2c3d4-e5f6-7890-..."
        """
        ...

    @property
    def generation(self) -> int:
        """Strategy generation number.

        Behavioral Contract:
        - MUST return non-negative integer
        - MUST be immutable after creation
        - Generation 0 = initial/seed strategy

        Post-conditions:
        - return_value >= 0
        - return_value is stable (doesn't change)

        Returns:
            int: Generation number (0 = first generation)

        Example:
            - Template Mode: iteration_num
            - LLM Mode: iteration_num
            - Factor Graph: strategy.generation
        """
        ...

    @property
    def metrics(self) -> Optional[Any]:
        """Strategy performance metrics.

        Behavioral Contract:
        - Returns None if strategy not yet evaluated
        - Returns metrics object if evaluated
        - If not None, MUST include sharpe_ratio attribute or key

        Post-conditions:
        - If None: strategy has not been backtested
        - If not None: metrics.sharpe_ratio or metrics['sharpe_ratio'] exists

        Returns:
            Optional[Any]: StrategyMetrics, MultiObjectiveMetrics, or None

        Note:
            The exact type varies by strategy mode:
            - Template/LLM: StrategyMetrics from src.backtest.metrics
            - Factor Graph: MultiObjectiveMetrics from src.evolution.types
        """
        ...

    def dominates(self, other: 'IStrategy') -> bool:
        """Compare this strategy against another using Pareto dominance.

        Behavioral Contract:
        - MUST compare via metrics (typically sharpe_ratio as primary)
        - MUST handle None metrics gracefully (return False)
        - MUST be consistent: if A.dominates(B) == False and B.dominates(A) == False,
          then A and B have equivalent or incomparable performance

        Pre-conditions:
        - other MUST implement IStrategy protocol

        Post-conditions:
        - Returns True only if this strategy is strictly better
        - Returns False if metrics are None for either strategy

        Args:
            other: Another strategy to compare against

        Returns:
            bool: True if this strategy dominates other, False otherwise

        Example:
            >>> if strategy_a.dominates(strategy_b):
            ...     print("Strategy A is strictly better than B")
        """
        ...

    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters.

        Behavioral Contract:
        - MUST return dictionary (may be empty)
        - MUST be JSON-serializable
        - Template mode: template parameters (n_stocks, lookback, etc.)
        - LLM mode: empty dict (parameters embedded in code)
        - Factor Graph mode: factor configuration

        Post-conditions:
        - isinstance(return_value, dict) == True
        - All values are JSON-serializable

        Returns:
            Dict[str, Any]: Strategy parameters dictionary

        Example:
            >>> params = strategy.get_parameters()
            >>> print(params)  # {'n_stocks': 20, 'lookback': 60}
        """
        ...

    def get_metrics(self) -> Dict[str, float]:
        """Get strategy performance metrics as dictionary.

        Behavioral Contract:
        - MUST return dictionary with numeric values
        - MUST include 'sharpe_ratio' key if strategy evaluated
        - MUST return empty dict if strategy not evaluated

        Post-conditions:
        - isinstance(return_value, dict) == True
        - If strategy evaluated: 'sharpe_ratio' in return_value
        - All values are float or convertible to float

        Returns:
            Dict[str, float]: Performance metrics dictionary

        Example:
            >>> metrics = strategy.get_metrics()
            >>> print(metrics)
            {'sharpe_ratio': 2.5, 'max_drawdown': -0.15, ...}
        """
        ...


@runtime_checkable
class IChampionTracker(Protocol):
    """Protocol for champion strategy tracking and management.

    **TDD Phase: REFACTOR - Enhanced with Behavioral Contracts**

    Defines the essential interface for tracking and updating the best-performing
    trading strategy (champion) across learning iterations.

    Required Interface:
        - champion property: Access current champion strategy
        - update_champion(): Update champion with new iteration results

    Implementation Requirements:
        - ChampionTracker class must provide these methods/properties
        - Runtime validation via isinstance(obj, IChampionTracker)
        - No inheritance required - structural subtyping (duck typing)

    Example Usage:
        >>> tracker = ChampionTracker(hall_of_fame, history, anti_churn)
        >>> # Check current champion
        >>> if tracker.champion:
        ...     print(f"Current champion: Iteration {tracker.champion.iteration_num}")
        ...     print(f"Sharpe: {tracker.champion.metrics['sharpe_ratio']:.4f}")
        >>> # Update with new iteration
        >>> updated = tracker.update_champion(
        ...     iteration_num=10,
        ...     code="# strategy",
        ...     metrics={'sharpe_ratio': 2.5, 'max_drawdown': -0.15}
        ... )
        >>> if updated:
        ...     print("New champion!")
    """

    @property
    def champion(self) -> Optional['ChampionStrategy']:
        """Get current champion strategy.

        Behavioral Contract:
        - MUST be referentially stable: returns same object if champion unchanged
        - MUST return None if no champion exists (never raises exception)
        - MUST return ChampionStrategy instance when champion exists

        Post-conditions:
        - If returns non-None, object.metrics['sharpe_ratio'] MUST exist
        - If returns non-None, object.iteration_num MUST be non-negative
        """
        ...

    def update_champion(
        self,
        iteration_num: int,
        code: Optional[str],
        metrics: Dict[str, float],
        **kwargs: Any
    ) -> bool:
        """Update champion if new strategy performs better.

        Behavioral Contract:
        - MUST compare via Sharpe ratio (primary metric)
        - MUST validate metrics['sharpe_ratio'] exists before comparison
        - MUST be atomic: either fully updates or leaves champion unchanged
        - MUST persist champion to storage if updated
        - MUST return True only if champion was actually updated

        Pre-conditions:
        - metrics MUST contain 'sharpe_ratio' key (float value)
        - iteration_num MUST be non-negative integer
        - If code is None, kwargs MUST contain Factor Graph parameters

        Post-conditions:
        - If returns True, subsequent .champion property MUST return new champion
        - If returns True, .champion.iteration_num MUST equal iteration_num
        - If returns False, .champion remains unchanged (referential identity)

        Args:
            iteration_num: Current iteration number (>= 0)
            code: Strategy code for LLM-generated strategies (None for Factor Graph)
            metrics: Performance metrics (must include 'sharpe_ratio')
            **kwargs: Additional parameters (strategy_id, generation for Factor Graph)

        Returns:
            True if champion was updated, False otherwise
        """
        ...


@runtime_checkable
class IIterationHistory(Protocol):
    """Protocol for iteration history persistence.

    **TDD Phase: REFACTOR - Enhanced with Behavioral Contracts**

    Defines the essential interface for saving and retrieving iteration records
    in JSONL (JSON Lines) format with atomic write protection.

    Required Interface:
        - save(): Persist iteration record
        - get_all(): Retrieve all iteration records
        - load_recent(): Retrieve recent N iterations

    Implementation Requirements:
        - IterationHistory class must provide these methods
        - Runtime validation via isinstance(obj, IIterationHistory)
        - No inheritance required - structural subtyping (duck typing)

    Thread Safety:
        - Single process safe (atomic os.replace())
        - NOT safe for concurrent multi-process writes
        - Read operations always safe (read-only)

    Example Usage:
        >>> history = IterationHistory("artifacts/data/innovations.jsonl")
        >>> # Save iteration
        >>> record = IterationRecord(iteration_num=0, ...)
        >>> history.save(record)
        >>> # Load recent iterations
        >>> recent = history.load_recent(N=5)
        >>> print(f"Last {len(recent)} iterations")
    """

    def save(self, record: 'IterationRecord') -> None:
        """Save iteration record to persistent storage.

        Behavioral Contract:
        - MUST be idempotent: saving same record twice is safe (no duplicates)
        - MUST use atomic write mechanism (temp file + os.replace())
        - MUST preserve record.iteration_num as unique key
        - After successful save, get_all() MUST include this record
        - MUST handle filesystem errors gracefully (log and raise)

        Pre-conditions:
        - record.iteration_num MUST be non-negative integer
        - record.metrics MUST be serializable to JSON

        Post-conditions:
        - Record retrievable via load_recent() or get_all()
        - File never left in corrupted state (atomic write)

        Args:
            record: IterationRecord instance to persist
        """
        ...

    def get_all(self) -> List['IterationRecord']:
        """Retrieve all iteration records from storage.

        Behavioral Contract:
        - MUST return records ordered by iteration_num ascending
        - MUST return empty list if no records exist (never None)
        - MUST return copies of records (caller cannot mutate storage)
        - MUST skip corrupted lines (log warning)

        Post-conditions:
        - Returned list order: records[i].iteration_num <= records[i+1].iteration_num
        - len(returned_list) >= 0 (never raises for empty file)

        Returns:
            List of all IterationRecord instances (may be empty)
        """
        ...

    def load_recent(self, N: int = 5) -> List['IterationRecord']:
        """Retrieve recent N iteration records.

        Behavioral Contract:
        - MUST return last N iterations ordered newest first (descending)
        - MUST return fewer than N if total records < N (never raises)
        - MUST return empty list if no records exist (never None)

        Pre-conditions:
        - N MUST be positive integer (>= 1)

        Post-conditions:
        - len(returned_list) <= N
        - If len(returned_list) > 0, records[0] is most recent iteration

        Args:
            N: Number of recent iterations to retrieve (default: 5)

        Returns:
            List of up to N most recent IterationRecord instances
        """
        ...


@runtime_checkable
class IErrorClassifier(Protocol):
    """Protocol for execution error classification.

    **TDD Phase: REFACTOR - Enhanced with Behavioral Contracts**

    Defines the essential interface for categorizing execution errors into
    standardized categories for debugging and analysis.

    Required Interface:
        - classify_error(): Classify error into predefined category

    Implementation Requirements:
        - ErrorClassifier class must provide this method
        - Runtime validation via isinstance(obj, IErrorClassifier)
        - No inheritance required - structural subtyping (duck typing)

    Supported Error Categories:
        - DATA_MISSING: Missing required data columns
        - CALCULATION: Math/computation errors
        - SYNTAX: Python syntax errors
        - TIMEOUT: Execution timeout
        - UNKNOWN: Unrecognized errors

    Example Usage:
        >>> classifier = ErrorClassifier()
        >>> result = classifier.classify_error({
        ...     'error_type': 'KeyError',
        ...     'error_msg': "key 'price' not found"
        ... })
        >>> print(result['category'])  # ErrorCategory.DATA_MISSING
    """

    def classify_error(self, strategy_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Classify execution error into standardized category.

        Behavioral Contract:
        - MUST be deterministic: same input produces same category
        - MUST return valid classification for any input (never raises)
        - MUST support both English and Chinese error messages
        - MUST handle missing keys gracefully (default to UNKNOWN)

        Pre-conditions:
        - strategy_metrics MUST be a dictionary (may be empty)
        - Keys 'error_type' and 'error_msg' are optional

        Post-conditions:
        - Returns dict with 'category' key (ErrorCategory enum value)
        - Returns dict with 'classification_level' key (str: LEVEL_X)
        - If input contains no error info, returns UNKNOWN category

        Args:
            strategy_metrics: Execution result containing error information
                Expected keys (all optional):
                - error_type: Exception class name (str)
                - error_msg: Exception message (str)
                - traceback: Full error traceback (str)

        Returns:
            Dictionary with classification result:
            - category: ErrorCategory enum value
            - classification_level: Severity level (str: LEVEL_X)
            - confidence: Classification confidence 0.0-1.0 (optional)
            - details: Additional metadata (optional)
        """
        ...
