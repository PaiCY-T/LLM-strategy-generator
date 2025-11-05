"""
Multi-objective metrics and type definitions for evolutionary optimization.

Defines the MultiObjectiveMetrics dataclass representing fitness across
multiple objectives (Sharpe, Calmar, Max Drawdown) for NSGA-II optimization.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


@dataclass
class MultiObjectiveMetrics:
    """
    Multi-objective fitness metrics for NSGA-II evolutionary optimization.

    Represents performance across multiple objectives to enable Pareto-optimal
    selection and population-based learning. Used for comparing individuals
    and determining dominance relationships.

    Objectives (all to maximize except max_drawdown):
        - sharpe_ratio: Risk-adjusted return (higher is better)
        - calmar_ratio: Return / max drawdown (higher is better)
        - max_drawdown: Peak-to-trough decline as negative value (less negative is better)
        - total_return: Cumulative return (higher is better)
        - win_rate: Percentage of winning trades (higher is better)
        - annual_return: Annualized return (higher is better)

    Attributes:
        sharpe_ratio: Risk-adjusted return metric (return / volatility)
        calmar_ratio: Return / abs(max_drawdown) ratio
        max_drawdown: Maximum peak-to-trough decline (negative value, e.g., -0.20 for -20%)
        total_return: Cumulative return over backtest period (e.g., 0.50 for 50% return)
        win_rate: Percentage of winning trades (0.0 to 1.0)
        annual_return: Annualized return (e.g., 0.15 for 15% annual return)
        success: Whether backtest completed successfully

    Example:
        >>> metrics1 = MultiObjectiveMetrics(
        ...     sharpe_ratio=1.5,
        ...     calmar_ratio=2.0,
        ...     max_drawdown=-0.15,
        ...     total_return=0.50,
        ...     win_rate=0.60,
        ...     annual_return=0.20,
        ...     success=True
        ... )
        >>> metrics2 = MultiObjectiveMetrics(
        ...     sharpe_ratio=1.2,
        ...     calmar_ratio=1.8,
        ...     max_drawdown=-0.20,
        ...     total_return=0.40,
        ...     win_rate=0.55,
        ...     annual_return=0.18,
        ...     success=True
        ... )
        >>> metrics1.dominates(metrics2)  # True: metrics1 better in all objectives
        True

    Notes:
        - max_drawdown is negative: -0.15 is better than -0.20
        - All other metrics: higher is better
        - Dominance requires strict improvement in ALL objectives
        - Used in NSGA-II Pareto ranking and crowding distance calculations
    """

    sharpe_ratio: float
    calmar_ratio: float
    max_drawdown: float
    total_return: float
    win_rate: float
    annual_return: float
    success: bool = True

    def dominates(self, other: 'MultiObjectiveMetrics') -> bool:
        """
        Check if this metrics dominates another (Pareto dominance).

        Pareto dominance: This metrics dominates other if it is at least as good
        in all objectives and strictly better in at least one objective.

        Maximization objectives: sharpe_ratio, calmar_ratio, total_return, win_rate, annual_return
        Minimization objective: max_drawdown (less negative is better)

        Args:
            other: Another MultiObjectiveMetrics to compare against

        Returns:
            bool: True if this metrics Pareto-dominates other, False otherwise

        Example:
            >>> m1 = MultiObjectiveMetrics(1.5, 2.0, -0.10, 0.50, 0.60, 0.20, True)
            >>> m2 = MultiObjectiveMetrics(1.2, 1.8, -0.15, 0.40, 0.55, 0.18, True)
            >>> m1.dominates(m2)  # True: m1 better in all objectives
            True
            >>> m2.dominates(m1)  # False: m2 worse in all objectives
            False

        Notes:
            - Failed backtests (success=False) are never dominant
            - Requires strict improvement in at least one objective
            - Used in NSGA-II non-dominated sorting and Pareto front identification
        """
        # Failed backtests cannot dominate
        if not self.success or not other.success:
            return False

        # Check if at least as good in all objectives and strictly better in at least one
        at_least_as_good = (
            self.sharpe_ratio >= other.sharpe_ratio and
            self.calmar_ratio >= other.calmar_ratio and
            self.max_drawdown >= other.max_drawdown and  # Less negative is better
            self.total_return >= other.total_return and
            self.win_rate >= other.win_rate and
            self.annual_return >= other.annual_return
        )

        strictly_better = (
            self.sharpe_ratio > other.sharpe_ratio or
            self.calmar_ratio > other.calmar_ratio or
            self.max_drawdown > other.max_drawdown or  # Less negative is better
            self.total_return > other.total_return or
            self.win_rate > other.win_rate or
            self.annual_return > other.annual_return
        )

        return at_least_as_good and strictly_better

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            str: Human-readable representation of metrics

        Example:
            >>> m = MultiObjectiveMetrics(1.5, 2.0, -0.15, 0.50, 0.60, 0.20, True)
            >>> repr(m)
            'MultiObjectiveMetrics(sharpe=1.5000, calmar=2.0000, dd=-0.1500, ret=0.5000)'
        """
        return (
            f"MultiObjectiveMetrics("
            f"sharpe={self.sharpe_ratio:.4f}, "
            f"calmar={self.calmar_ratio:.4f}, "
            f"dd={self.max_drawdown:.4f}, "
            f"ret={self.total_return:.4f})"
        )


@dataclass
class Strategy:
    """
    Individual strategy in the evolutionary population with complete lineage tracking.

    Represents a single strategy in the population-based learning system, including
    its implementation code, parameters, fitness metrics, and evolutionary metadata.
    Used for NSGA-II multi-objective optimization with Pareto ranking and crowding
    distance calculations.

    Attributes:
        id: Unique identifier (UUID), auto-generated if not provided
        generation: Generation number when this strategy was created
        parent_ids: List of parent strategy IDs for lineage tracking
        code: Strategy implementation as Python code string
        parameters: Extracted strategy parameters as dictionary
        metrics: Multi-objective fitness metrics (None if not evaluated)
        novelty_score: Diversity measure for novelty search (0.0 = not calculated)
        pareto_rank: NSGA-II Pareto rank (0 = not ranked, 1 = Pareto front)
        crowding_distance: NSGA-II diversity metric (0.0 = not calculated)
        timestamp: ISO 8601 creation timestamp, auto-generated if not provided
        template_type: Template name used to generate this strategy
        metadata: Additional strategy information (tags, notes, etc.)

    Example:
        >>> strategy = Strategy(
        ...     generation=5,
        ...     parent_ids=['uuid1', 'uuid2'],
        ...     code='def strategy(): pass',
        ...     parameters={'n_stocks': 10, 'holding_period': 20},
        ...     template_type='Momentum'
        ... )
        >>> strategy.id  # Auto-generated UUID
        'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        >>> strategy.timestamp  # Auto-generated ISO 8601 timestamp
        '2025-10-19T12:34:56.789012'

    Notes:
        - ID and timestamp are auto-generated in __post_init__ if not provided
        - Novelty score, pareto_rank, and crowding_distance are set by NSGA-II algorithm
        - Metrics are populated after backtest evaluation
        - Parent IDs enable lineage tracking and genealogy analysis
    """

    id: str = field(default="")
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    code: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    metrics: Optional[MultiObjectiveMetrics] = None
    novelty_score: float = 0.0
    pareto_rank: int = 0
    crowding_distance: float = 0.0
    timestamp: str = ""
    template_type: str = 'Momentum'
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """
        Auto-generate ID and timestamp if not provided.

        Creates a unique UUID for the strategy ID and an ISO 8601 timestamp
        if these fields are not already set. This ensures all strategies have
        unique identifiers and creation timestamps for tracking.

        Example:
            >>> s = Strategy(code='def strategy(): pass')
            >>> s.id  # Auto-generated
            'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
            >>> s.timestamp  # Auto-generated
            '2025-10-19T12:34:56.789012'
        """
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert strategy to dictionary for JSON serialization.

        Creates a complete dictionary representation including all fields.
        Metrics are serialized as a nested dictionary if present.

        Returns:
            Dict[str, Any]: Dictionary with all strategy fields

        Example:
            >>> strategy = Strategy(
            ...     generation=1,
            ...     code='def strategy(): pass',
            ...     parameters={'n_stocks': 10}
            ... )
            >>> data = strategy.to_dict()
            >>> data['generation']
            1
            >>> data['parameters']
            {'n_stocks': 10}
        """
        return {
            'id': self.id,
            'generation': self.generation,
            'parent_ids': self.parent_ids,
            'code': self.code,
            'parameters': self.parameters,
            'metrics': {
                'sharpe_ratio': self.metrics.sharpe_ratio,
                'calmar_ratio': self.metrics.calmar_ratio,
                'max_drawdown': self.metrics.max_drawdown,
                'total_return': self.metrics.total_return,
                'win_rate': self.metrics.win_rate,
                'annual_return': self.metrics.annual_return,
                'success': self.metrics.success
            } if self.metrics else None,
            'novelty_score': self.novelty_score,
            'pareto_rank': self.pareto_rank,
            'crowding_distance': self.crowding_distance,
            'timestamp': self.timestamp,
            'template_type': self.template_type,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Strategy':
        """
        Create Strategy from dictionary.

        Reconstructs a Strategy instance from a dictionary representation,
        including deserializing the nested metrics dictionary if present.

        Args:
            data: Dictionary with strategy data (from to_dict())

        Returns:
            Strategy: New strategy instance

        Example:
            >>> data = {
            ...     'id': 'uuid-1234',
            ...     'generation': 1,
            ...     'code': 'def strategy(): pass',
            ...     'parameters': {'n_stocks': 10},
            ...     'parent_ids': [],
            ...     'metrics': None,
            ...     'novelty_score': 0.0,
            ...     'pareto_rank': 0,
            ...     'crowding_distance': 0.0,
            ...     'timestamp': '2025-10-19T12:34:56',
            ...     'template_type': 'Momentum',
            ...     'metadata': {}
            ... }
            >>> strategy = Strategy.from_dict(data)
            >>> strategy.generation
            1
        """
        # Reconstruct metrics if present
        metrics = None
        if data.get('metrics'):
            metrics_data = data['metrics']
            metrics = MultiObjectiveMetrics(
                sharpe_ratio=metrics_data['sharpe_ratio'],
                calmar_ratio=metrics_data['calmar_ratio'],
                max_drawdown=metrics_data['max_drawdown'],
                total_return=metrics_data['total_return'],
                win_rate=metrics_data['win_rate'],
                annual_return=metrics_data['annual_return'],
                success=metrics_data.get('success', True)
            )

        return cls(
            id=data.get('id', ''),
            generation=data.get('generation', 0),
            parent_ids=data.get('parent_ids', []),
            code=data.get('code', ''),
            parameters=data.get('parameters', {}),
            metrics=metrics,
            novelty_score=data.get('novelty_score', 0.0),
            pareto_rank=data.get('pareto_rank', 0),
            crowding_distance=data.get('crowding_distance', 0.0),
            timestamp=data.get('timestamp', ''),
            template_type=data.get('template_type', 'Momentum'),
            metadata=data.get('metadata', {})
        )

    def dominates(self, other: 'Strategy') -> bool:
        """
        Check if this strategy dominates another (Pareto dominance).

        Delegates to the metrics.dominates() method to determine if this
        strategy's metrics Pareto-dominate the other strategy's metrics.
        Requires both strategies to have evaluated metrics.

        Args:
            other: Another Strategy to compare against

        Returns:
            bool: True if this strategy dominates other, False otherwise

        Example:
            >>> s1 = Strategy(
            ...     metrics=MultiObjectiveMetrics(
            ...         sharpe_ratio=1.5, calmar_ratio=2.0,
            ...         max_drawdown=-0.10, total_return=0.50,
            ...         win_rate=0.60, annual_return=0.20, success=True
            ...     )
            ... )
            >>> s2 = Strategy(
            ...     metrics=MultiObjectiveMetrics(
            ...         sharpe_ratio=1.2, calmar_ratio=1.8,
            ...         max_drawdown=-0.15, total_return=0.40,
            ...         win_rate=0.55, annual_return=0.18, success=True
            ...     )
            ... )
            >>> s1.dominates(s2)
            True

        Notes:
            - Returns False if either strategy lacks metrics
            - Uses MultiObjectiveMetrics.dominates() for the actual comparison
            - Part of NSGA-II non-dominated sorting algorithm
        """
        if self.metrics is None or other.metrics is None:
            return False
        return self.metrics.dominates(other.metrics)

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            str: Human-readable representation with key fields

        Example:
            >>> s = Strategy(id='abc123', generation=5, template_type='Momentum')
            >>> repr(s)
            'Strategy(id=abc123, gen=5, template=Momentum, rank=0)'
        """
        return (
            f"Strategy(id={self.id[:8]}, gen={self.generation}, "
            f"template={self.template_type}, rank={self.pareto_rank})"
        )


@dataclass
class Population:
    """
    Complete population state for evolutionary optimization.

    Represents the entire population of strategies at a specific generation,
    including Pareto front, diversity metrics, and population-level statistics.
    Used for NSGA-II multi-objective optimization and population management.

    Attributes:
        generation: Current generation number
        strategies: All strategies in the population
        pareto_front: Non-dominated strategies (Pareto optimal)
        diversity_metrics: Population diversity statistics
        timestamp: ISO 8601 creation timestamp, auto-generated

    Properties:
        size: Number of strategies in population
        best_sharpe: Strategy with highest Sharpe ratio (None if no evaluated strategies)
        avg_sharpe: Average Sharpe ratio across evaluated strategies (0.0 if none)

    Example:
        >>> from datetime import datetime
        >>> strategies = [
        ...     Strategy(generation=1, code='def s1(): pass',
        ...              metrics=MultiObjectiveMetrics(1.5, 2.0, -0.10, 0.50, 0.60, 0.20, True)),
        ...     Strategy(generation=1, code='def s2(): pass',
        ...              metrics=MultiObjectiveMetrics(1.2, 1.8, -0.15, 0.40, 0.55, 0.18, True))
        ... ]
        >>> pop = Population(
        ...     generation=1,
        ...     strategies=strategies,
        ...     pareto_front=[strategies[0]],
        ...     diversity_metrics={'avg_distance': 0.5}
        ... )
        >>> pop.size
        2
        >>> pop.best_sharpe.metrics.sharpe_ratio
        1.5
        >>> pop.avg_sharpe
        1.35

    Notes:
        - Timestamp is auto-generated in __post_init__ if not provided
        - Pareto front is typically computed by NSGA-II algorithm
        - Diversity metrics include measures like average crowding distance
        - Used for tracking population evolution and analysis
    """

    generation: int
    strategies: List[Strategy]
    pareto_front: List[Strategy] = field(default_factory=list)
    diversity_metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        """
        Auto-generate timestamp if not provided.

        Creates an ISO 8601 timestamp if the field is not already set.
        This ensures all populations have creation timestamps for tracking.

        Example:
            >>> pop = Population(generation=1, strategies=[])
            >>> pop.timestamp  # Auto-generated
            '2025-10-19T12:34:56.789012'
        """
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    @property
    def size(self) -> int:
        """
        Number of strategies in population.

        Returns:
            int: Total number of strategies

        Example:
            >>> strategies = [Strategy(), Strategy(), Strategy()]
            >>> pop = Population(generation=1, strategies=strategies)
            >>> pop.size
            3
        """
        return len(self.strategies)

    @property
    def best_sharpe(self) -> Optional[Strategy]:
        """
        Strategy with highest Sharpe ratio.

        Finds and returns the strategy with the maximum Sharpe ratio among
        all evaluated strategies. Returns None if no strategies have been
        evaluated or all evaluations failed.

        Returns:
            Optional[Strategy]: Strategy with highest Sharpe, or None if no evaluated strategies

        Example:
            >>> s1 = Strategy(metrics=MultiObjectiveMetrics(1.5, 2.0, -0.10, 0.50, 0.60, 0.20, True))
            >>> s2 = Strategy(metrics=MultiObjectiveMetrics(1.2, 1.8, -0.15, 0.40, 0.55, 0.18, True))
            >>> pop = Population(generation=1, strategies=[s1, s2])
            >>> pop.best_sharpe.metrics.sharpe_ratio
            1.5

        Notes:
            - Only considers strategies with successful evaluations (metrics.success=True)
            - Returns None if population is empty or no strategies evaluated
        """
        evaluated = [s for s in self.strategies if s.metrics and s.metrics.success]
        if not evaluated:
            return None
        return max(evaluated, key=lambda s: s.metrics.sharpe_ratio)

    @property
    def avg_sharpe(self) -> float:
        """
        Average Sharpe ratio across evaluated strategies.

        Calculates the mean Sharpe ratio of all successfully evaluated strategies.
        Returns 0.0 if no strategies have been evaluated.

        Returns:
            float: Average Sharpe ratio, or 0.0 if no evaluated strategies

        Example:
            >>> s1 = Strategy(metrics=MultiObjectiveMetrics(1.5, 2.0, -0.10, 0.50, 0.60, 0.20, True))
            >>> s2 = Strategy(metrics=MultiObjectiveMetrics(1.2, 1.8, -0.15, 0.40, 0.55, 0.18, True))
            >>> pop = Population(generation=1, strategies=[s1, s2])
            >>> pop.avg_sharpe
            1.35

        Notes:
            - Only includes strategies with successful evaluations (metrics.success=True)
            - Returns 0.0 if population is empty or no strategies evaluated
        """
        evaluated = [s for s in self.strategies if s.metrics and s.metrics.success]
        if not evaluated:
            return 0.0
        return sum(s.metrics.sharpe_ratio for s in evaluated) / len(evaluated)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert population to dictionary for JSON serialization.

        Creates a complete dictionary representation including all fields.
        Strategies are serialized as a list of dictionaries.

        Returns:
            Dict[str, Any]: Dictionary with all population fields

        Example:
            >>> pop = Population(
            ...     generation=1,
            ...     strategies=[Strategy(code='def s(): pass')],
            ...     diversity_metrics={'avg_distance': 0.5}
            ... )
            >>> data = pop.to_dict()
            >>> data['generation']
            1
            >>> data['diversity_metrics']
            {'avg_distance': 0.5}
            >>> len(data['strategies'])
            1

        Notes:
            - All strategies are serialized using Strategy.to_dict()
            - Pareto front contains strategy IDs, not full strategy objects
            - Timestamp is included as ISO 8601 string
        """
        return {
            'generation': self.generation,
            'strategies': [s.to_dict() for s in self.strategies],
            'pareto_front': [s.id for s in self.pareto_front],
            'diversity_metrics': self.diversity_metrics,
            'timestamp': self.timestamp
        }

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            str: Human-readable representation with key statistics

        Example:
            >>> pop = Population(generation=5, strategies=[Strategy(), Strategy()])
            >>> repr(pop)
            'Population(gen=5, size=2, pareto=0)'
        """
        return (
            f"Population(gen={self.generation}, size={self.size}, "
            f"pareto={len(self.pareto_front)})"
        )


@dataclass
class EvolutionResult:
    """
    Tracks the results of a single evolution generation for logging and analysis.

    Encapsulates all metrics and timing information from one generation of the
    evolutionary process, including population state, performance metrics, timing
    breakdowns, and metadata about the evolution cycle.

    Attributes:
        generation: Generation number (0 = initial population)
        population: Complete population state after this generation
        elite_strategies: List of elite strategies preserved from previous generation
        offspring_count: Number of new offspring created in this generation
        selection_time: Time spent on parent selection (seconds)
        crossover_time: Time spent on crossover operations (seconds)
        mutation_time: Time spent on mutation operations (seconds)
        evaluation_time: Time spent on fitness evaluation (seconds)
        total_time: Total time for this generation (seconds)
        champion_updated: Whether the global champion strategy improved this generation
        diversity_score: Population diversity metric (0.0-1.0)
        pareto_front_size: Number of strategies in the Pareto optimal front
        timestamp: ISO 8601 timestamp when generation completed, auto-generated if not provided

    Example:
        >>> pop = Population(
        ...     generation=5,
        ...     strategies=[Strategy() for _ in range(20)]
        ... )
        >>> result = EvolutionResult(
        ...     generation=5,
        ...     population=pop,
        ...     elite_strategies=[Strategy()],
        ...     offspring_count=15,
        ...     selection_time=1.2,
        ...     crossover_time=0.8,
        ...     mutation_time=0.5,
        ...     evaluation_time=10.3,
        ...     total_time=12.8,
        ...     champion_updated=True,
        ...     diversity_score=0.75,
        ...     pareto_front_size=5
        ... )
        >>> result.summary()
        'Generation 5: 20 strategies, 5 Pareto front, 15 offspring, champion improved, 12.8s total'
        >>> result.timestamp  # Auto-generated
        '2025-10-19T12:34:56.789012'

    Notes:
        - Timestamp is auto-generated in __post_init__ if not provided
        - All timing metrics are in seconds (float)
        - Diversity score ranges from 0.0 (low diversity) to 1.0 (high diversity)
        - Used for logging, monitoring, and performance analysis
    """

    generation: int
    population: Population
    elite_strategies: List[Strategy] = field(default_factory=list)
    offspring_count: int = 0
    selection_time: float = 0.0
    crossover_time: float = 0.0
    mutation_time: float = 0.0
    evaluation_time: float = 0.0
    total_time: float = 0.0
    champion_updated: bool = False
    diversity_score: float = 0.0
    pareto_front_size: int = 0
    timestamp: str = ""

    def __post_init__(self):
        """
        Auto-generate timestamp if not provided.

        Creates an ISO 8601 timestamp for this evolution result if the timestamp
        field is not already set. This ensures all results have completion
        timestamps for tracking evolution history.

        Example:
            >>> pop = Population(generation=5, strategies=[])
            >>> result = EvolutionResult(generation=5, population=pop)
            >>> result.timestamp  # Auto-generated
            '2025-10-19T12:34:56.789012'
        """
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def summary(self) -> str:
        """
        Generate a human-readable summary of this generation's results.

        Creates a concise one-line summary with key metrics including population
        size, Pareto front size, offspring count, champion update status, and
        total execution time.

        Returns:
            str: Human-readable summary string

        Example:
            >>> pop = Population(generation=5, strategies=[Strategy() for _ in range(20)])
            >>> result = EvolutionResult(
            ...     generation=5,
            ...     population=pop,
            ...     offspring_count=15,
            ...     total_time=12.8,
            ...     champion_updated=True,
            ...     pareto_front_size=5
            ... )
            >>> result.summary()
            'Generation 5: 20 strategies, 5 Pareto front, 15 offspring, champion improved, 12.8s total'

        Notes:
            - Format: "Generation N: X strategies, Y Pareto front, Z offspring, [champion status], Ts total"
            - Champion status is either "champion improved" or "no champion improvement"
            - Total time is rounded to 1 decimal place
        """
        champion_status = "champion improved" if self.champion_updated else "no champion improvement"
        return (
            f"Generation {self.generation}: {self.population.size} strategies, "
            f"{self.pareto_front_size} Pareto front, {self.offspring_count} offspring, "
            f"{champion_status}, {self.total_time:.1f}s total"
        )

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            str: Human-readable representation with key fields

        Example:
            >>> pop = Population(generation=5, strategies=[])
            >>> result = EvolutionResult(generation=5, population=pop, total_time=12.8)
            >>> repr(result)
            'EvolutionResult(gen=5, pop_size=0, time=12.8s)'
        """
        return (
            f"EvolutionResult(gen={self.generation}, "
            f"pop_size={self.population.size}, "
            f"time={self.total_time:.1f}s)"
        )
