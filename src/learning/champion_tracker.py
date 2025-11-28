"""Champion Tracker - Manages best-performing trading strategies.

This module implements the ChampionTracker class which tracks, updates, and manages
the current champion strategy (best-performing trading strategy) across iterations.

**Protocol Compliance**: Implements IChampionTracker Protocol (Phase 5B.2)
    - Runtime checkable via isinstance(tracker, IChampionTracker)
    - Type hints match Protocol signatures exactly
    - Behavioral contracts enforced (see IChampionTracker docstrings)

Key Responsibilities:
    - Load/save champion from/to persistent storage
    - Compare new strategies with current champion
    - Update champion when better strategy found (Sharpe-based with tie-breaking)
    - Archive champions to hall of fame
    - Track champion staleness (iterations without update)
    - Promote cohort strategies when champion becomes stale

Champion Selection Criteria:
    1. Primary: Higher Sharpe Ratio wins
    2. Tie-breaking: Equal Sharpe + Lower Max Drawdown wins
    3. Multi-objective validation: Calmar ratio and drawdown tolerance checks

Persistence:
    - champion.json: Current champion (legacy support)
    - Hall of Fame: Unified repository for all champions (primary)
    - Atomic writes for data integrity

Staleness Detection:
    - Tracks iterations since last champion update
    - Compares champion against recent cohort (top X% performers)
    - Recommends demotion if champion falls below cohort median

Integration Points:
    - ConfigManager: Dynamic threshold configuration
    - HallOfFameRepository: Persistent storage
    - IterationHistory: Strategy cohort extraction
    - AntiChurnManager: Dynamic improvement thresholds
    - DiversityMonitor: Champion update tracking (optional)

Example:
    >>> from src.learning.champion_tracker import ChampionTracker
    >>> from src.learning.iteration_history import IterationHistory
    >>> from src.repository.hall_of_fame import HallOfFameRepository
    >>> from src.config.anti_churn_manager import AntiChurnManager
    >>> from src.learning.interfaces import IChampionTracker
    >>>
    >>> # Initialize dependencies
    >>> history = IterationHistory()
    >>> hall_of_fame = HallOfFameRepository()
    >>> anti_churn = AntiChurnManager()
    >>>
    >>> # Create tracker
    >>> tracker = ChampionTracker(
    ...     hall_of_fame=hall_of_fame,
    ...     history=history,
    ...     anti_churn=anti_churn
    ... )
    >>>
    >>> # Runtime Protocol validation
    >>> assert isinstance(tracker, IChampionTracker)
    >>>
    >>> # Check if champion exists
    >>> if tracker.champion:
    ...     print(f"Champion: Iteration {tracker.champion.iteration_num}")
    ...     print(f"Sharpe: {tracker.champion.metrics['sharpe_ratio']:.4f}")
    >>>
    >>> # Update champion after iteration
    >>> updated = tracker.update_champion(
    ...     iteration_num=10,
    ...     code="# strategy code",
    ...     metrics={'sharpe_ratio': 2.5, 'max_drawdown': -0.15}
    ... )
    >>>
    >>> # Check staleness periodically
    >>> if iteration_num % 50 == 0:
    ...     staleness = tracker.check_champion_staleness()
    ...     if staleness['should_demote']:
    ...         best_cohort = tracker.get_best_cohort_strategy()
    ...         if best_cohort:
    ...             tracker.demote_champion_to_hall_of_fame()
    ...             tracker.promote_to_champion(best_cohort)
"""

from typing import TYPE_CHECKING, Optional, Dict, Any, List, Union
from pathlib import Path
from dataclasses import dataclass, asdict, field
from datetime import datetime
import json
import os
import logging

from src.backtest.metrics import StrategyMetrics

if TYPE_CHECKING:
    from src.repository.hall_of_fame import HallOfFameRepository
    from src.learning.iteration_history import IterationHistory
    from src.config.anti_churn_manager import AntiChurnManager

logger = logging.getLogger(__name__)


@dataclass
class ChampionStrategy:
    """Best-performing strategy across all iterations (Hybrid Architecture).

    Supports both LLM-generated code strings and Factor Graph Strategy DAG objects.
    The generation_method field determines which type of champion this represents.

    Tracks the highest-performing strategy to enable:
    - Performance attribution (comparing current vs. champion)
    - Success pattern extraction (identifying what works)
    - Evolutionary constraints (preserving proven patterns)
    - Hybrid generation (LLM ↔ Factor Graph transitions)

    Attributes:
        iteration_num: Which iteration produced this champion
        generation_method: "llm" or "factor_graph"
        metrics: Performance metrics (sharpe_ratio, max_drawdown, etc.)
        timestamp: When this champion was established (ISO format)

        LLM-specific fields (None for factor_graph):
            code: Complete Python strategy code

        Factor Graph-specific fields (None for llm):
            strategy_id: Unique identifier for the Strategy DAG
            strategy_generation: Generation number (for evolution tracking)

        Optional fields (may be empty for either method):
            parameters: Extracted parameter values (from code or DAG)
            success_patterns: List of patterns that contributed to success

    Examples:
        LLM Champion:
            >>> champion = ChampionStrategy(
            ...     iteration_num=10,
            ...     generation_method="llm",
            ...     code="# strategy code",
            ...     metrics={"sharpe_ratio": 1.5},
            ...     timestamp="2025-11-08T10:00:00",
            ...     parameters={"dataset": "price:收盤價"},
            ...     success_patterns=["momentum", "volume_filter"]
            ... )

        Factor Graph Champion:
            >>> champion = ChampionStrategy(
            ...     iteration_num=15,
            ...     generation_method="factor_graph",
            ...     strategy_id="momentum_v2",
            ...     strategy_generation=2,
            ...     metrics={"sharpe_ratio": 2.0},
            ...     timestamp="2025-11-08T11:00:00",
            ...     parameters={"rsi_14": {"period": 14}},
            ...     success_patterns=["RSI", "Signal"]
            ... )
    """
    # Required fields (common to both methods)
    iteration_num: int
    metrics: StrategyMetrics
    timestamp: str

    # Generation method (default to "llm" for backward compatibility)
    generation_method: str = "llm"  # "llm" or "factor_graph"

    # LLM-specific (None for factor_graph)
    code: Optional[str] = None

    # Factor Graph-specific (None for llm)
    strategy_id: Optional[str] = None
    strategy_generation: Optional[int] = None

    # Optional fields (may be empty for either method)
    parameters: Dict[str, Any] = field(default_factory=dict)
    success_patterns: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate field consistency based on generation_method.

        Ensures that:
        - generation_method is valid ("llm" or "factor_graph")
        - LLM champions have code (and no DAG fields)
        - Factor Graph champions have strategy_id + strategy_generation (and no code)

        Raises:
            ValueError: If validation fails with descriptive error message
        """
        # Validate generation_method
        valid_methods = ["llm", "factor_graph", "template"]
        if self.generation_method not in valid_methods:
            raise ValueError(
                f"generation_method must be one of {valid_methods}, "
                f"got '{self.generation_method}'"
            )

        # Validate LLM and Template-specific fields (both generate code)
        if self.generation_method in ["llm", "template"]:
            if not self.code:
                raise ValueError(
                    f"{self.generation_method.upper()} champion must have code. "
                    f"Provide code parameter when generation_method='{self.generation_method}'"
                )
            if self.strategy_id or self.strategy_generation is not None:
                raise ValueError(
                    f"{self.generation_method.upper()} champion should not have strategy_id or strategy_generation. "
                    "These fields are for factor_graph champions only"
                )

        # Validate Factor Graph-specific fields
        elif self.generation_method == "factor_graph":
            if not self.strategy_id or self.strategy_generation is None:
                raise ValueError(
                    "Factor Graph champion must have both strategy_id and strategy_generation. "
                    f"Got strategy_id={self.strategy_id}, strategy_generation={self.strategy_generation}"
                )
            if self.code:
                raise ValueError(
                    "Factor Graph champion should not have code. "
                    "code field is for llm champions only"
                )

        # Convert metrics dict to StrategyMetrics if needed (Phase 3.3 type safety)
        if isinstance(self.metrics, dict):
            object.__setattr__(self, 'metrics', StrategyMetrics.from_dict(self.metrics))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary containing all champion data with None values preserved
        """
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ChampionStrategy':
        """Create ChampionStrategy from dictionary (with backward compatibility).

        Handles old format LLM champions that don't have generation_method field.
        Automatically infers generation_method="llm" and adds missing fields.

        Args:
            data: Dictionary with champion data

        Returns:
            ChampionStrategy instance

        Examples:
            Old LLM format (backward compatible):
                >>> data = {
                ...     "iteration_num": 5,
                ...     "code": "# old format",
                ...     "metrics": {"sharpe_ratio": 1.5},
                ...     "timestamp": "2025-11-08T10:00:00",
                ...     "parameters": {},
                ...     "success_patterns": []
                ... }
                >>> champion = ChampionStrategy.from_dict(data)
                >>> champion.generation_method  # Automatically inferred
                'llm'

            New format (explicit generation_method):
                >>> data = {
                ...     "iteration_num": 10,
                ...     "generation_method": "factor_graph",
                ...     "strategy_id": "momentum_v1",
                ...     "strategy_generation": 1,
                ...     "metrics": {"sharpe_ratio": 2.0},
                ...     "timestamp": "2025-11-08T11:00:00"
                ... }
                >>> champion = ChampionStrategy.from_dict(data)
        """
        # Backward compatibility: old format doesn't have generation_method
        if 'generation_method' not in data:
            logger.info("Loading old format champion, inferring generation_method='llm'")
            data['generation_method'] = 'llm'
            data.setdefault('strategy_id', None)
            data.setdefault('strategy_generation', None)

        # Backward compatibility: ensure default values for optional fields
        data.setdefault('parameters', {})
        data.setdefault('success_patterns', [])

        # Backward compatibility: success_patterns might be None in old format
        if data['success_patterns'] is None:
            data['success_patterns'] = []

        # Convert metrics dict to StrategyMetrics object (Phase 3.3 type safety)
        if isinstance(data.get('metrics'), dict):
            data['metrics'] = StrategyMetrics.from_dict(data['metrics'])

        return ChampionStrategy(**data)


class ChampionTracker:
    """Tracks and manages the best-performing trading strategy (champion).

    This class implements the core champion management logic for the autonomous
    learning loop. It handles champion persistence, comparison, updates, and
    staleness detection.

    The champion represents the best strategy found so far and serves as:
    - Baseline for performance comparison
    - Source of successful patterns to preserve
    - Reference for feedback generation

    Champion Update Logic:
        1. First valid strategy (Sharpe > min_threshold) becomes champion
        2. New champion requires:
           - Higher Sharpe ratio (with dynamic improvement threshold)
           - OR Equal Sharpe + Lower Max Drawdown (tie-breaking)
           - AND Passes multi-objective validation (Calmar, drawdown tolerance)
        3. Updates tracked via AntiChurnManager for dynamic thresholds

    Staleness Detection:
        - Triggered every N iterations (default: 50)
        - Compares champion against top X% of recent strategies (default: top 10%)
        - Recommends demotion if champion < cohort median Sharpe
        - Prevents eternal reign of outlier champions

    Attributes:
        champion: Current ChampionStrategy instance (None if no champion yet)
        iterations_since_update: Iterations since last champion update
        hall_of_fame: HallOfFameRepository for persistent storage
        history: IterationHistory for cohort extraction
        anti_churn: AntiChurnManager for dynamic thresholds
        multi_objective_enabled: Whether multi-objective validation is enabled
        calmar_retention_ratio: Minimum Calmar retention (default: 0.80)
        max_drawdown_tolerance: Maximum drawdown increase allowed (default: 1.10)
    """

    def __init__(
        self,
        hall_of_fame: 'HallOfFameRepository',
        history: 'IterationHistory',
        anti_churn: 'AntiChurnManager',
        champion_file: str = "artifacts/data/champion_strategy.json",
        multi_objective_enabled: bool = True,
        calmar_retention_ratio: float = 0.80,
        max_drawdown_tolerance: float = 1.10
    ):
        """Initialize ChampionTracker.

        Args:
            hall_of_fame: HallOfFameRepository instance for persistent storage
            history: IterationHistory instance for cohort extraction
            anti_churn: AntiChurnManager instance for dynamic thresholds
            champion_file: Path to legacy champion JSON file (backward compatibility)
            multi_objective_enabled: Enable Calmar/drawdown validation (default: True)
            calmar_retention_ratio: Min Calmar retention ratio (default: 0.80 = 80%)
            max_drawdown_tolerance: Max drawdown tolerance (default: 1.10 = 10% worse)
        """
        self.champion_file = Path(champion_file)
        self.hall_of_fame = hall_of_fame
        self.history = history
        self.anti_churn = anti_churn
        self.champion: Optional[ChampionStrategy] = None
        self.iterations_since_update: int = 0

        # Multi-objective validation settings
        self.multi_objective_enabled = multi_objective_enabled
        self.calmar_retention_ratio = calmar_retention_ratio
        self.max_drawdown_tolerance = max_drawdown_tolerance

        # Load champion from storage
        self._load_champion()

    def _load_champion(self) -> None:
        """Load champion strategy from Hall of Fame.

        Attempts to load champion from Hall of Fame first (unified persistence),
        then falls back to legacy champion_strategy.json if Hall of Fame is empty.
        This ensures backward compatibility during migration.

        If a legacy champion is found, it is automatically migrated to Hall of Fame.

        Sets:
            self.champion: ChampionStrategy instance if champion exists, None otherwise
        """
        from src.constants import CHAMPION_FILE

        # Try Hall of Fame first (unified persistence)
        genome = self.hall_of_fame.get_current_champion()
        if genome:
            # Convert StrategyGenome → ChampionStrategy (supports hybrid architecture)
            # Extract metadata from parameters (stored during save)
            iteration_num = genome.parameters.get('__iteration_num__', 0)
            generation_method = genome.parameters.get('__generation_method__', 'llm')  # Default to 'llm' for backward compatibility

            # Remove metadata from parameters
            clean_params = {k: v for k, v in genome.parameters.items() if not k.startswith('__')}

            # Build ChampionStrategy based on generation_method
            if generation_method == "llm":
                # Phase 3: Convert dict metrics to StrategyMetrics for backward compatibility
                metrics = genome.metrics if isinstance(genome.metrics, StrategyMetrics) else StrategyMetrics.from_dict(genome.metrics)

                self.champion = ChampionStrategy(
                    iteration_num=iteration_num,
                    generation_method="llm",
                    code=genome.strategy_code,
                    parameters=clean_params,
                    metrics=metrics,
                    success_patterns=genome.success_patterns,
                    timestamp=genome.created_at
                )
                logger.info(
                    f"Loaded LLM champion from Hall of Fame: Iteration {iteration_num}, "
                    f"Sharpe {genome.metrics.get('sharpe_ratio', 0):.4f}"
                )

            elif generation_method == "factor_graph":
                # Extract Factor Graph-specific metadata
                strategy_id = genome.parameters.get('__strategy_id__')
                strategy_generation = genome.parameters.get('__strategy_generation__')

                if not strategy_id or strategy_generation is None:
                    logger.error(
                        f"Factor Graph champion missing strategy_id or strategy_generation. "
                        f"Cannot load champion from Hall of Fame."
                    )
                    self.champion = None
                    return

                # Phase 3: Convert dict metrics to StrategyMetrics for backward compatibility
                metrics = genome.metrics if isinstance(genome.metrics, StrategyMetrics) else StrategyMetrics.from_dict(genome.metrics)

                self.champion = ChampionStrategy(
                    iteration_num=iteration_num,
                    generation_method="factor_graph",
                    strategy_id=strategy_id,
                    strategy_generation=strategy_generation,
                    parameters=clean_params,
                    metrics=metrics,
                    success_patterns=genome.success_patterns,
                    timestamp=genome.created_at
                )
                logger.info(
                    f"Loaded Factor Graph champion from Hall of Fame: Iteration {iteration_num}, "
                    f"Sharpe {genome.metrics.get('sharpe_ratio', 0):.4f}, "
                    f"Strategy '{strategy_id}' generation {strategy_generation}"
                )

            else:
                logger.error(f"Unknown generation_method '{generation_method}' in Hall of Fame champion")
                self.champion = None
                return

            return

        # Fallback: Legacy champion_strategy.json (migration support)
        if os.path.exists(CHAMPION_FILE):
            try:
                with open(CHAMPION_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                champion = ChampionStrategy.from_dict(data)

                # Migrate to Hall of Fame automatically
                logger.info(f"Migrating legacy champion from {CHAMPION_FILE} to Hall of Fame...")
                self._save_champion_to_hall_of_fame(champion)
                logger.info("Migration complete")

                self.champion = champion
                return
            except (json.JSONDecodeError, TypeError, KeyError, ValueError) as e:
                logger.warning(f"Could not load legacy champion: {e}")
                logger.info("Starting without champion")
                self.champion = None
                return

        logger.info("No champion found - starting fresh")
        self.champion = None

    def update_champion(
        self,
        iteration_num: int,
        code: Optional[str],
        metrics: Union[StrategyMetrics, Dict[str, float]],
        **kwargs: Any
    ) -> bool:
        """Update champion if new strategy performs better.

        **Protocol Compliance**: Implements IChampionTracker.update_champion()
        Matches Protocol signature exactly: (iteration_num, code, metrics, **kwargs) -> bool

        Behavioral Contract (from IChampionTracker):
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

        Supports both LLM-generated code strings and Factor Graph Strategy DAG objects.
        Uses AntiChurnManager for dynamic improvement thresholds based on probation period.
        Applies multi-objective validation to prevent brittle strategy selection.
        Tracks champion updates for frequency analysis.

        Champion Update Algorithm:
            1. First valid strategy (Sharpe > min_threshold) becomes champion
            2. For subsequent updates:
               a. Calculate dynamic improvement threshold (probation period)
               b. Check hybrid threshold (relative OR absolute improvement)
               c. Validate multi-objective criteria (Calmar, drawdown)
               d. Create new champion if all criteria pass
               e. Track update attempt (success/failure)

        Args:
            iteration_num: Current iteration number (>= 0)
            code: Strategy code for LLM-generated strategies (None for Factor Graph)
            metrics: Performance metrics (must include 'sharpe_ratio')
            **kwargs: Additional parameters for Factor Graph mode:
                - generation_method: "llm" or "factor_graph" (default: "llm")
                - strategy: Strategy DAG object (required for Factor Graph)
                - strategy_id: Strategy ID (required for Factor Graph)
                - strategy_generation: Generation number (required for Factor Graph)

        Returns:
            True if champion was updated, False otherwise

        Raises:
            ValueError: If required parameters are missing for the specified generation_method

        Examples:
            LLM Update:
                >>> tracker = ChampionTracker(hall_of_fame, history, anti_churn)
                >>> metrics = {
                ...     'sharpe_ratio': 2.5,
                ...     'max_drawdown': -0.15,
                ...     'calmar_ratio': 1.2
                ... }
                >>> updated = tracker.update_champion(
                ...     iteration_num=10,
                ...     code="# strategy code",
                ...     metrics=metrics
                ... )

            Factor Graph Update:
                >>> updated = tracker.update_champion(
                ...     iteration_num=15,
                ...     code=None,
                ...     metrics=metrics,
                ...     generation_method="factor_graph",
                ...     strategy=strategy_dag_object,
                ...     strategy_id="momentum_v2",
                ...     strategy_generation=2
                ... )
        """
        # Phase 3: Convert dict to StrategyMetrics for backward compatibility
        if isinstance(metrics, dict):
            metrics = StrategyMetrics.from_dict(metrics)

        # Extract kwargs for backward compatibility
        generation_method = kwargs.get('generation_method', 'llm')
        strategy = kwargs.get('strategy', None)
        strategy_id = kwargs.get('strategy_id', None)
        strategy_generation = kwargs.get('strategy_generation', None)
        from src.constants import METRIC_SHARPE

        # Validate generation_method (Phase 3: Added 'template' support)
        if generation_method not in ["llm", "factor_graph", "template"]:
            raise ValueError(
                f"generation_method must be 'llm', 'factor_graph', or 'template', "
                f"got '{generation_method}'"
            )

        # Validate generation_method-specific parameters
        if generation_method == "llm":
            if not code:
                raise ValueError(
                    "LLM champion update requires 'code' parameter. "
                    "Provide strategy code when generation_method='llm'"
                )
        elif generation_method == "factor_graph":
            if not strategy:
                raise ValueError(
                    "Factor Graph champion update requires 'strategy' parameter. "
                    "Provide Strategy DAG object when generation_method='factor_graph'"
                )
            if not strategy_id or strategy_generation is None:
                raise ValueError(
                    "Factor Graph champion update requires 'strategy_id' and 'strategy_generation'. "
                    f"Got strategy_id={strategy_id}, strategy_generation={strategy_generation}"
                )

        # Validate required metrics are present
        # Phase 3: Use attribute access for StrategyMetrics
        current_sharpe = metrics.sharpe_ratio if metrics.sharpe_ratio is not None else 0

        if self.multi_objective_enabled:
            # Multi-objective mode requires additional metrics
            calmar_ratio = getattr(metrics, 'calmar_ratio', None)
            max_drawdown = getattr(metrics, 'max_drawdown', None)

            if calmar_ratio is None or max_drawdown is None:
                logger.error(
                    f"Cannot update champion: Missing required multi-objective metrics. "
                    f"calmar_ratio={calmar_ratio}, max_drawdown={max_drawdown}"
                )
                # Track failed update attempt
                self.anti_churn.track_champion_update(
                    iteration_num=iteration_num,
                    was_updated=False
                )
                return False

        # First valid strategy becomes champion
        if self.champion is None:
            if current_sharpe > self.anti_churn.min_sharpe_for_champion:
                self._create_champion(
                    iteration_num=iteration_num,
                    generation_method=generation_method,
                    metrics=metrics,
                    code=code,
                    strategy=strategy,
                    strategy_id=strategy_id,
                    strategy_generation=strategy_generation
                )
                # Track initial champion creation
                self.anti_churn.track_champion_update(
                    iteration_num=iteration_num,
                    was_updated=True,
                    old_sharpe=None,
                    new_sharpe=current_sharpe,
                    threshold_used=None
                )
                return True
            else:
                # Track failed champion creation
                self.anti_churn.track_champion_update(
                    iteration_num=iteration_num,
                    was_updated=False
                )
                return False

        # Get dynamic improvement threshold
        champion_sharpe = self.champion.metrics.get(METRIC_SHARPE, 0)
        required_improvement_pct = self.anti_churn.get_required_improvement(
            current_iteration=iteration_num,
            champion_iteration=self.champion.iteration_num
        )
        required_improvement_multiplier = 1.0 + required_improvement_pct

        # Get additive threshold from anti-churn manager (Hybrid Threshold)
        additive_threshold = self.anti_churn.get_additive_threshold()

        # Hybrid threshold: Accept if EITHER condition met
        relative_threshold_met = current_sharpe >= champion_sharpe * required_improvement_multiplier
        absolute_threshold_met = current_sharpe >= champion_sharpe + additive_threshold

        if relative_threshold_met or absolute_threshold_met:
            improvement_pct = (current_sharpe / champion_sharpe - 1) * 100

            # Log which threshold was used for tracking
            threshold_type = "relative" if relative_threshold_met else "absolute"

            # Multi-objective validation
            # Prevent brittle strategy selection where Sharpe improves but risk metrics degrade
            logger.info(
                f"Champion update passed {threshold_type} threshold "
                f"(+{improvement_pct:.1f}%). Validating multi-objective criteria..."
            )

            validation_result = self._validate_multi_objective(
                new_metrics=metrics,
                old_metrics=self.champion.metrics
            )

            if not validation_result['passed']:
                # Multi-objective validation failed - reject champion update
                failed_criteria = ', '.join(validation_result['failed_criteria'])
                logger.info(
                    f"Champion update REJECTED by multi-objective validation. "
                    f"Failed criteria: {failed_criteria}. "
                    f"Sharpe improvement alone insufficient (new: {current_sharpe:.4f} vs "
                    f"champion: {champion_sharpe:.4f}, +{improvement_pct:.1f}%)"
                )

                # Track failed champion update due to multi-objective validation
                self.anti_churn.track_champion_update(
                    iteration_num=iteration_num,
                    was_updated=False
                )
                return False

            # Multi-objective validation passed
            logger.info("Multi-objective validation PASSED. Proceeding with champion update.")

            # Track successful champion update
            self.anti_churn.track_champion_update(
                iteration_num=iteration_num,
                was_updated=True,
                old_sharpe=champion_sharpe,
                new_sharpe=current_sharpe,
                threshold_used=required_improvement_pct
            )

            self._create_champion(
                iteration_num=iteration_num,
                generation_method=generation_method,
                metrics=metrics,
                code=code,
                strategy=strategy,
                strategy_id=strategy_id,
                strategy_generation=strategy_generation
            )
            logger.info(
                f"Champion updated via {threshold_type} threshold: "
                f"{champion_sharpe:.4f} → {current_sharpe:.4f} "
                f"(+{improvement_pct:.1f}%, relative_met: {relative_threshold_met}, "
                f"absolute_met: {absolute_threshold_met})"
            )

            return True
        elif current_sharpe == champion_sharpe:
            # Tie-breaking: When Sharpe ratios are equal, compare max_drawdown
            # Lower (less negative) drawdown is better
            current_drawdown = metrics.get('max_drawdown', float('inf'))
            champion_drawdown = self.champion.metrics.get('max_drawdown', float('inf'))

            if current_drawdown < champion_drawdown:
                # New strategy has equal Sharpe but better (lower) drawdown
                improvement_dd = (champion_drawdown - current_drawdown) * 100  # Improvement percentage points

                logger.info(
                    f"Tie-breaker: Equal Sharpe ({current_sharpe:.3f}), "
                    f"but better max drawdown ({current_drawdown:.2%} vs {champion_drawdown:.2%}, "
                    f"improved by {improvement_dd:.1f} pct points)"
                )

                # Track tie-breaking champion update
                self.anti_churn.track_champion_update(
                    iteration_num=iteration_num,
                    was_updated=True,
                    old_sharpe=champion_sharpe,
                    new_sharpe=current_sharpe,
                    threshold_used=0.0  # No threshold needed for tie-breaking
                )

                self._create_champion(
                    iteration_num=iteration_num,
                    generation_method=generation_method,
                    metrics=metrics,
                    code=code,
                    strategy=strategy,
                    strategy_id=strategy_id,
                    strategy_generation=strategy_generation
                )

                logger.info(
                    f"Champion updated via TIE-BREAKING: "
                    f"Sharpe {champion_sharpe:.4f} (unchanged), "
                    f"Drawdown {champion_drawdown:.2%} → {current_drawdown:.2%} "
                    f"(improved by {improvement_dd:.1f} pct points)"
                )

                return True
            else:
                # Equal Sharpe but worse/equal drawdown - reject
                logger.debug(
                    f"Tie-breaker rejected: Equal Sharpe ({current_sharpe:.3f}), "
                    f"but worse/equal drawdown ({current_drawdown:.2%} vs {champion_drawdown:.2%})"
                )
                self.anti_churn.track_champion_update(
                    iteration_num=iteration_num,
                    was_updated=False
                )
                return False
        else:
            # Track failed champion update attempt
            self.anti_churn.track_champion_update(
                iteration_num=iteration_num,
                was_updated=False
            )
            return False

    def _create_champion(
        self,
        iteration_num: int,
        metrics: StrategyMetrics,
        code: Optional[str] = None,
        generation_method: str = "llm",  # Default to "llm" for backward compatibility
        strategy: Optional[Any] = None,
        strategy_id: Optional[str] = None,
        strategy_generation: Optional[int] = None
    ) -> None:
        """Create new champion strategy (supports both LLM and Factor Graph).

        Extracts parameters and success patterns based on generation_method,
        creates a ChampionStrategy instance, and persists it to disk via Hall of Fame.

        This method supports both LLM-generated code strings and Factor Graph
        Strategy DAG objects, enabling seamless transitions between generation methods.

        Args:
            iteration_num: Iteration number that produced this champion
            metrics: Performance metrics dict
            code: Strategy code (required for LLM, None for Factor Graph)
            generation_method: "llm" or "factor_graph" (default: "llm")
            strategy: Strategy DAG object (required for Factor Graph, None for LLM)
            strategy_id: Strategy ID (required for Factor Graph, None for LLM)
            strategy_generation: Generation number (required for Factor Graph, None for LLM)

        Raises:
            ValueError: If required parameters are missing for the specified generation_method

        Examples:
            LLM Champion:
                >>> tracker._create_champion(
                ...     iteration_num=10,
                ...     generation_method="llm",
                ...     code="# strategy code",
                ...     metrics={"sharpe_ratio": 1.5}
                ... )

            Factor Graph Champion:
                >>> tracker._create_champion(
                ...     iteration_num=15,
                ...     generation_method="factor_graph",
                ...     strategy=strategy_dag_object,
                ...     strategy_id="momentum_v2",
                ...     strategy_generation=2,
                ...     metrics={"sharpe_ratio": 2.0}
                ... )
        """
        from src.constants import METRIC_SHARPE

        # Validate generation_method (Phase 3: Added 'template' support)
        if generation_method not in ["llm", "factor_graph", "template"]:
            raise ValueError(
                f"generation_method must be 'llm', 'factor_graph', or 'template', "
                f"got '{generation_method}'"
            )

        # Extract parameters and patterns based on generation method
        if generation_method == "llm":
            # Validate LLM-specific parameters
            if not code:
                raise ValueError(
                    "LLM champion requires 'code' parameter. "
                    "Provide strategy code when generation_method='llm'"
                )

            # Extract from code
            from performance_attributor import extract_strategy_params, extract_success_patterns
            parameters = extract_strategy_params(code)
            success_patterns = extract_success_patterns(code, parameters)

            # Create LLM champion
            self.champion = ChampionStrategy(
                iteration_num=iteration_num,
                generation_method="llm",
                code=code,
                parameters=parameters,
                metrics=metrics,
                success_patterns=success_patterns,
                timestamp=datetime.now().isoformat()
            )

        elif generation_method == "factor_graph":
            # Validate Factor Graph-specific parameters
            if not strategy:
                raise ValueError(
                    "Factor Graph champion requires 'strategy' parameter. "
                    "Provide Strategy DAG object when generation_method='factor_graph'"
                )
            if not strategy_id or strategy_generation is None:
                raise ValueError(
                    "Factor Graph champion requires 'strategy_id' and 'strategy_generation'. "
                    f"Got strategy_id={strategy_id}, strategy_generation={strategy_generation}"
                )

            # Extract from Strategy DAG
            from src.learning.strategy_metadata import extract_dag_parameters, extract_dag_patterns
            parameters = extract_dag_parameters(strategy)
            success_patterns = extract_dag_patterns(strategy)

            # Create Factor Graph champion
            self.champion = ChampionStrategy(
                iteration_num=iteration_num,
                generation_method="factor_graph",
                strategy_id=strategy_id,
                strategy_generation=strategy_generation,
                parameters=parameters,
                metrics=metrics,
                success_patterns=success_patterns,
                timestamp=datetime.now().isoformat()
            )

        self._save_champion()
        logger.info(
            f"New {generation_method} champion: Iteration {iteration_num}, "
            f"Sharpe {metrics.get(METRIC_SHARPE, 0):.4f}"
        )

    def _save_champion(self) -> None:
        """Save champion strategy to Hall of Fame.

        Uses unified Hall of Fame API instead of direct JSON file access.
        Automatically classifies strategy into appropriate tier based on Sharpe ratio.
        """
        if not self.champion:
            return

        self._save_champion_to_hall_of_fame(self.champion)

    def _save_champion_to_hall_of_fame(self, champion: ChampionStrategy) -> None:
        """Save champion to Hall of Fame repository (supports hybrid architecture).

        Helper method to convert ChampionStrategy format and persist to Hall of Fame.
        Used both for new champions and legacy migrations.

        Stores metadata for both LLM and Factor Graph champions:
        - LLM: code as strategy_code, generation_method in parameters
        - Factor Graph: strategy_id and strategy_generation in parameters

        Args:
            champion: ChampionStrategy to save
        """
        # Add metadata to parameters for later retrieval
        # Use __prefix__ to distinguish from strategy parameters
        params_with_metadata = champion.parameters.copy()
        params_with_metadata['__iteration_num__'] = champion.iteration_num
        params_with_metadata['__generation_method__'] = champion.generation_method

        # Add Factor Graph-specific metadata if applicable
        if champion.generation_method == "factor_graph":
            params_with_metadata['__strategy_id__'] = champion.strategy_id
            params_with_metadata['__strategy_generation__'] = champion.strategy_generation

        # Phase 3: Convert StrategyMetrics to dict for Hall of Fame serialization
        metrics_dict = champion.metrics.to_dict() if isinstance(champion.metrics, StrategyMetrics) else champion.metrics

        # Save to Hall of Fame (automatic tier classification)
        # Note: strategy_code will be None for Factor Graph champions
        self.hall_of_fame.add_strategy(
            template_name='autonomous_generated',  # Autonomous loop strategies
            parameters=params_with_metadata,
            metrics=metrics_dict,
            strategy_code=champion.code,  # None for Factor Graph
            success_patterns=champion.success_patterns
        )

    def compare_with_champion(
        self,
        current_code: str,
        current_metrics: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """Compare current strategy with champion for performance attribution.

        Extracts parameters from current code and compares with champion
        to identify what changed and how it affected performance.

        Args:
            current_code: Strategy code to compare
            current_metrics: Performance metrics for current strategy

        Returns:
            Attribution dictionary with changes and performance delta,
            or None if no champion exists or comparison fails

        Example:
            >>> attribution = tracker.compare_with_champion(code, metrics)
            >>> if attribution:
            ...     print(f"Assessment: {attribution['assessment']}")
            ...     print(f"Delta: {attribution['performance_delta']:.2f}")
            ...     for change in attribution['critical_changes']:
            ...         print(f"- {change['parameter']}: {change['from']} → {change['to']}")
        """
        if not self.champion:
            return None

        try:
            from performance_attributor import extract_strategy_params, compare_strategies

            curr_params = extract_strategy_params(current_code)
            return compare_strategies(
                prev_params=self.champion.parameters,
                curr_params=curr_params,
                prev_metrics=self.champion.metrics,
                curr_metrics=current_metrics
            )
        except Exception as e:
            logger.error(f"Attribution comparison failed: {e}")
            logger.info("Falling back to simple feedback")
            return None

    def _validate_multi_objective(
        self,
        new_metrics: Dict[str, float],
        old_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Validate multi-objective criteria for champion update.

        Validates that new strategy maintains balanced risk/return profile by checking:
        1. Sharpe ratio improvement (handled by hybrid threshold in update_champion)
        2. Calmar ratio retention: new_calmar >= old_calmar * calmar_retention_ratio
        3. Max drawdown tolerance: new_mdd <= old_mdd * max_drawdown_tolerance

        This prevents brittle strategy selection where Sharpe improves but risk
        characteristics degrade (low Calmar, high drawdown).

        Args:
            new_metrics: Performance metrics for new strategy
            old_metrics: Performance metrics for champion strategy

        Returns:
            Dictionary with validation results:
            - passed (bool): True if all criteria pass
            - failed_criteria (list): List of failed criteria names
            - details (dict): Detailed validation results for each criterion
                - calmar_check (dict): Calmar validation details
                - drawdown_check (dict): Drawdown validation details

        Example:
            >>> result = tracker._validate_multi_objective(
            ...     new_metrics={'sharpe_ratio': 2.1, 'calmar_ratio': 0.75, 'max_drawdown': -0.16},
            ...     old_metrics={'sharpe_ratio': 2.0, 'calmar_ratio': 0.80, 'max_drawdown': -0.15}
            ... )
            >>> result['passed']
            True  # All criteria pass
            >>> result['failed_criteria']
            []
        """
        from src.backtest.metrics import calculate_calmar_ratio
        import math

        # Return structure
        validation_result = {
            'passed': True,
            'failed_criteria': [],
            'details': {}
        }

        # Check if multi-objective validation is enabled
        if not self.multi_objective_enabled:
            logger.debug("Multi-objective validation disabled, skipping")
            validation_result['details']['disabled'] = True
            return validation_result

        # Extract metrics with edge case handling
        def get_metric_safe(metrics: Dict[str, float], key: str, default: float = 0.0) -> Optional[float]:
            """Safely extract metric with NaN/None handling."""
            value = metrics.get(key, default)
            if value is None or (isinstance(value, float) and math.isnan(value)):
                return None
            return value

        # Get Sharpe ratios (for logging context)
        new_sharpe = get_metric_safe(new_metrics, 'sharpe_ratio')
        old_sharpe = get_metric_safe(old_metrics, 'sharpe_ratio')

        # Get Calmar ratios
        new_calmar = get_metric_safe(new_metrics, 'calmar_ratio')
        old_calmar = get_metric_safe(old_metrics, 'calmar_ratio')

        # Get max drawdowns (negative values)
        new_mdd = get_metric_safe(new_metrics, 'max_drawdown')
        old_mdd = get_metric_safe(old_metrics, 'max_drawdown')

        # Alternative: Calculate Calmar from annual_return and max_drawdown if not provided
        if new_calmar is None:
            annual_return = get_metric_safe(new_metrics, 'annual_return')
            if annual_return is not None and new_mdd is not None:
                new_calmar = calculate_calmar_ratio(annual_return, new_mdd)

        if old_calmar is None:
            annual_return = get_metric_safe(old_metrics, 'annual_return')
            if annual_return is not None and old_mdd is not None:
                old_calmar = calculate_calmar_ratio(annual_return, old_mdd)

        # ====================
        # Criterion 1: Calmar Ratio Retention
        # ====================
        calmar_check = {'passed': False, 'reason': '', 'values': {}}

        if old_calmar is None or new_calmar is None:
            # Missing Calmar data - treat as pass with warning
            calmar_check['passed'] = True
            calmar_check['reason'] = 'Calmar ratio unavailable (missing data)'
            calmar_check['values'] = {
                'old_calmar': old_calmar,
                'new_calmar': new_calmar,
                'required_calmar': None
            }
            logger.warning("Calmar ratio validation skipped: missing data")
        else:
            # Validate: new_calmar >= old_calmar * calmar_retention_ratio
            required_calmar = old_calmar * self.calmar_retention_ratio

            if new_calmar >= required_calmar:
                calmar_check['passed'] = True
                retention_pct = (new_calmar / old_calmar) * 100 if old_calmar != 0 else 100
                calmar_check['reason'] = (
                    f'Calmar retained: {new_calmar:.4f} >= {required_calmar:.4f} '
                    f'({retention_pct:.1f}% of old Calmar)'
                )
            else:
                calmar_check['passed'] = False
                retention_pct = (new_calmar / old_calmar) * 100 if old_calmar != 0 else 0
                calmar_check['reason'] = (
                    f'Calmar degraded: {new_calmar:.4f} < {required_calmar:.4f} '
                    f'({retention_pct:.1f}% < {self.calmar_retention_ratio*100:.0f}% retention)'
                )
                validation_result['failed_criteria'].append('calmar_ratio')
                validation_result['passed'] = False

            calmar_check['values'] = {
                'old_calmar': old_calmar,
                'new_calmar': new_calmar,
                'required_calmar': required_calmar,
                'retention_ratio': self.calmar_retention_ratio
            }

        validation_result['details']['calmar_check'] = calmar_check

        # ====================
        # Criterion 2: Max Drawdown Tolerance
        # ====================
        drawdown_check = {'passed': False, 'reason': '', 'values': {}}

        if old_mdd is None or new_mdd is None:
            # Missing drawdown data - treat as pass with warning
            drawdown_check['passed'] = True
            drawdown_check['reason'] = 'Max drawdown unavailable (missing data)'
            drawdown_check['values'] = {
                'old_mdd': old_mdd,
                'new_mdd': new_mdd,
                'max_allowed_mdd': None
            }
            logger.warning("Max drawdown validation skipped: missing data")
        else:
            # Validate: new_mdd <= old_mdd * max_drawdown_tolerance
            # Note: Drawdowns are negative, so "worse" means more negative (larger magnitude)
            # Example: old_mdd = -0.15, tolerance = 1.10 → max_allowed = -0.165 (10% worse)
            max_allowed_mdd = old_mdd * self.max_drawdown_tolerance

            if new_mdd >= max_allowed_mdd:  # More negative = worse, so >= is better
                drawdown_check['passed'] = True
                # Calculate how much worse the drawdown is (as percentage)
                if old_mdd != 0:
                    worse_pct = (new_mdd / old_mdd) * 100
                else:
                    worse_pct = 100
                drawdown_check['reason'] = (
                    f'Drawdown acceptable: {new_mdd:.4f} >= {max_allowed_mdd:.4f} '
                    f'({worse_pct:.1f}% of old drawdown)'
                )
            else:
                drawdown_check['passed'] = False
                # Calculate how much worse the drawdown is (as percentage)
                if old_mdd != 0:
                    worse_pct = (new_mdd / old_mdd) * 100
                else:
                    worse_pct = 0
                drawdown_check['reason'] = (
                    f'Drawdown too large: {new_mdd:.4f} < {max_allowed_mdd:.4f} '
                    f'({worse_pct:.1f}% > {self.max_drawdown_tolerance*100:.0f}% tolerance)'
                )
                validation_result['failed_criteria'].append('max_drawdown')
                validation_result['passed'] = False

            drawdown_check['values'] = {
                'old_mdd': old_mdd,
                'new_mdd': new_mdd,
                'max_allowed_mdd': max_allowed_mdd,
                'tolerance': self.max_drawdown_tolerance
            }

        validation_result['details']['drawdown_check'] = drawdown_check

        # Log validation results
        def format_metric(value: Optional[float]) -> str:
            """Format metric value for logging."""
            if value is None:
                return 'N/A'
            return f"{value:.4f}"

        if validation_result['passed']:
            logger.info(
                f"Multi-objective validation PASSED "
                f"(Sharpe: {format_metric(old_sharpe)}→{format_metric(new_sharpe)}, "
                f"Calmar: {format_metric(old_calmar)}→{format_metric(new_calmar)}, "
                f"MDD: {format_metric(old_mdd)}→{format_metric(new_mdd)})"
            )
        else:
            logger.warning(
                f"Multi-objective validation FAILED: {', '.join(validation_result['failed_criteria'])} "
                f"(Sharpe: {format_metric(old_sharpe)}→{format_metric(new_sharpe)}, "
                f"Calmar: {format_metric(old_calmar)}→{format_metric(new_calmar)}, "
                f"MDD: {format_metric(old_mdd)}→{format_metric(new_mdd)})"
            )
            for criterion in validation_result['failed_criteria']:
                detail = validation_result['details'].get(f"{criterion.split('_')[0]}_check", {})
                if detail:
                    logger.warning(f"  - {criterion}: {detail.get('reason', 'Unknown')}")

        return validation_result

    def get_best_cohort_strategy(self) -> Optional[ChampionStrategy]:
        """Get best strategy from recent cohort for champion promotion.

        Extracts recent successful strategies, builds cohort from top performers,
        and returns the best strategy by Sharpe ratio.

        This method is used by staleness detection to find a replacement champion
        when the current champion becomes stale.

        Cohort Selection Algorithm:
            1. Get last N successful iterations (N = staleness_check_interval)
            2. Calculate Sharpe ratio percentile threshold (e.g., 90th percentile)
            3. Filter strategies above threshold (top X%)
            4. Return strategy with highest Sharpe ratio

        Returns:
            ChampionStrategy instance for best cohort strategy, or None if no suitable strategy found

        Example:
            >>> best = tracker.get_best_cohort_strategy()
            >>> if best:
            ...     print(f"Best cohort: Iteration {best.iteration_num}, Sharpe {best.metrics['sharpe_ratio']:.4f}")
        """
        from src.learning.config_manager import ConfigManager
        from src.constants import METRIC_SHARPE
        import numpy as np

        # Load staleness configuration
        try:
            config_manager = ConfigManager.get_instance()
            config_manager.load_config()
            staleness_cfg = config_manager.get('anti_churn.staleness', {})
            check_interval = staleness_cfg.get('staleness_check_interval', 50)
            cohort_percentile = staleness_cfg.get('staleness_cohort_percentile', 0.10)
        except Exception as e:
            logger.error(f"Failed to load staleness configuration: {e}")
            return None

        # Get recent successful strategies
        successful = self.history.get_successful_iterations()
        if not successful:
            logger.warning("No successful iterations available for cohort selection")
            return None

        # Extract last N strategies (window for staleness check)
        recent_strategies = successful[-check_interval:] if len(successful) > check_interval else successful

        # Build cohort: top X% by Sharpe ratio
        strategies_with_sharpe = [
            (record, record.metrics.get(METRIC_SHARPE, 0))
            for record in recent_strategies
            if record.metrics and METRIC_SHARPE in record.metrics
        ]

        if not strategies_with_sharpe:
            logger.warning("No strategies with Sharpe ratios found in recent history")
            return None

        # Calculate percentile threshold
        sharpe_ratios = [sharpe for _, sharpe in strategies_with_sharpe]
        percentile_value = (1.0 - cohort_percentile) * 100
        threshold = np.percentile(sharpe_ratios, percentile_value)

        # Filter cohort: strategies above threshold
        cohort = [(record, sharpe) for record, sharpe in strategies_with_sharpe if sharpe >= threshold]

        if not cohort:
            logger.warning("No strategies in cohort after filtering")
            return None

        # Find best strategy in cohort (highest Sharpe)
        best_record, best_sharpe = max(cohort, key=lambda x: x[1])

        logger.info(
            f"Selected best cohort strategy: Iteration {best_record.iteration_num}, "
            f"Sharpe {best_sharpe:.4f}"
        )

        # Convert IterationRecord to ChampionStrategy (supports both LLM and Factor Graph)
        generation_method = getattr(best_record, 'generation_method', 'llm')  # Default to 'llm' for backward compatibility

        if generation_method == "llm":
            # Extract from LLM code
            from performance_attributor import extract_strategy_params, extract_success_patterns

            parameters = extract_strategy_params(best_record.code)
            success_patterns = extract_success_patterns(best_record.code, parameters)

            return ChampionStrategy(
                iteration_num=best_record.iteration_num,
                generation_method="llm",
                code=best_record.code,
                parameters=parameters,
                metrics=best_record.metrics,
                success_patterns=success_patterns,
                timestamp=datetime.now().isoformat()
            )

        elif generation_method == "factor_graph":
            # Extract from Factor Graph (note: actual Strategy object not stored in IterationRecord)
            # For Factor Graph records, we use strategy_id and strategy_generation
            # Parameters and patterns would need to be stored in IterationRecord or reconstructed

            # For Phase 3, we use basic metadata from IterationRecord
            # In future phases, consider storing full metadata in IterationRecord
            strategy_id = getattr(best_record, 'strategy_id', None)
            strategy_generation = getattr(best_record, 'strategy_generation', None)

            if not strategy_id or strategy_generation is None:
                logger.warning(
                    f"Factor Graph record (iteration {best_record.iteration_num}) missing "
                    f"strategy_id or strategy_generation. Cannot create ChampionStrategy."
                )
                return None

            # Note: Parameters and success_patterns not available from IterationRecord alone
            # This is acceptable for cohort selection - the Strategy DAG would need to be
            # reconstructed from storage if detailed metadata is needed
            return ChampionStrategy(
                iteration_num=best_record.iteration_num,
                generation_method="factor_graph",
                strategy_id=strategy_id,
                strategy_generation=strategy_generation,
                parameters={},  # Empty for now - would need Strategy DAG to extract
                metrics=best_record.metrics,
                success_patterns=[],  # Empty for now - would need Strategy DAG to extract
                timestamp=datetime.now().isoformat()
            )

        else:
            logger.error(f"Unknown generation_method '{generation_method}' in IterationRecord")
            return None

    def demote_champion_to_hall_of_fame(self) -> None:
        """Demote current champion by saving to Hall of Fame (if not already there).

        The champion is already saved in Hall of Fame from _save_champion(), so this
        method is primarily for logging and tracking the demotion event.
        The actual demotion happens when we replace self.champion with a new strategy.

        Example:
            >>> tracker.demote_champion_to_hall_of_fame()
            >>> # Champion demoted: Iteration 50, Sharpe 2.4751
        """
        from src.constants import METRIC_SHARPE

        if not self.champion:
            logger.warning("No champion to demote")
            return

        # Champion is already persisted in Hall of Fame from previous _save_champion() call
        # This method is a placeholder for future demotion tracking logic
        # (e.g., marking strategy as "demoted_champion" in Hall of Fame metadata)

        logger.info(
            f"Champion demoted: Iteration {self.champion.iteration_num}, "
            f"Sharpe {self.champion.metrics.get(METRIC_SHARPE, 0):.4f}"
        )

    def promote_to_champion(
        self,
        strategy: Union[ChampionStrategy, Any],
        iteration_num: Optional[int] = None,
        metrics: Optional[Dict[str, float]] = None
    ) -> None:
        """Promote a cohort strategy to new champion (supports ChampionStrategy or Strategy DAG).

        This method accepts either:
        1. ChampionStrategy object (from get_best_cohort_strategy or manual creation)
        2. Strategy DAG object (Factor Graph strategy requiring metadata extraction)

        For Strategy DAG objects, iteration_num and metrics must be provided.

        Args:
            strategy: ChampionStrategy instance or Strategy DAG object
            iteration_num: Required for Strategy DAG, ignored for ChampionStrategy
            metrics: Required for Strategy DAG, ignored for ChampionStrategy

        Raises:
            ValueError: If Strategy DAG is provided without iteration_num/metrics
            TypeError: If strategy is not ChampionStrategy or Strategy DAG

        Examples:
            Promote ChampionStrategy (from cohort):
                >>> best_cohort = tracker.get_best_cohort_strategy()
                >>> if best_cohort:
                ...     tracker.promote_to_champion(best_cohort)
                >>> # Champion promoted: Iteration 75, Sharpe 2.6123

            Promote Strategy DAG:
                >>> tracker.promote_to_champion(
                ...     strategy=strategy_dag_object,
                ...     iteration_num=80,
                ...     metrics={"sharpe_ratio": 2.8, "max_drawdown": -0.10}
                ... )
                >>> # Champion promoted: Iteration 80, Sharpe 2.8000
        """
        from src.constants import METRIC_SHARPE

        if not strategy:
            logger.error("Cannot promote None strategy to champion")
            return

        # Check if strategy is ChampionStrategy
        if isinstance(strategy, ChampionStrategy):
            # Direct promotion path (current behavior)
            self.champion = strategy
            self._save_champion()

            logger.info(
                f"Champion promoted (ChampionStrategy): Iteration {strategy.iteration_num}, "
                f"Sharpe {strategy.metrics.get(METRIC_SHARPE, 0):.4f}"
            )

        else:
            # Strategy DAG object path (new behavior)
            # Validate required parameters
            if iteration_num is None:
                raise ValueError(
                    "iteration_num is required when promoting Strategy DAG object. "
                    "Provide iteration_num parameter"
                )
            if metrics is None:
                raise ValueError(
                    "metrics is required when promoting Strategy DAG object. "
                    "Provide metrics parameter"
                )

            # Extract strategy_id and strategy_generation from Strategy object
            if not hasattr(strategy, 'id') or not hasattr(strategy, 'generation'):
                raise TypeError(
                    "Strategy object must have 'id' and 'generation' attributes. "
                    f"Got object of type {type(strategy).__name__}"
                )

            strategy_id = strategy.id
            strategy_generation = strategy.generation

            # Extract metadata from Strategy DAG
            from src.learning.strategy_metadata import extract_dag_parameters, extract_dag_patterns

            parameters = extract_dag_parameters(strategy)
            success_patterns = extract_dag_patterns(strategy)

            # Create ChampionStrategy from Strategy DAG
            self.champion = ChampionStrategy(
                iteration_num=iteration_num,
                generation_method="factor_graph",
                strategy_id=strategy_id,
                strategy_generation=strategy_generation,
                parameters=parameters,
                metrics=metrics,
                success_patterns=success_patterns,
                timestamp=datetime.now().isoformat()
            )

            # Persist to Hall of Fame
            self._save_champion()

            logger.info(
                f"Champion promoted (Strategy DAG): Iteration {iteration_num}, "
                f"Sharpe {metrics.get(METRIC_SHARPE, 0):.4f}, "
                f"Strategy ID '{strategy_id}' generation {strategy_generation}"
            )

    def check_champion_staleness(self) -> Dict[str, Any]:
        """Check if champion is stale by comparing against recent strategy cohort.

        Staleness mechanism prevents eternal reign of outlier champions by:
        1. Extracting last N strategies from iteration history (N = staleness_check_interval)
        2. Calculating top X% threshold (e.g., 90th percentile of Sharpe ratios)
        3. Building cohort from strategies above threshold (top 10%)
        4. Calculating cohort median Sharpe ratio
        5. Comparing champion Sharpe vs cohort median
        6. Recommending demotion if champion < cohort median

        Example scenario:
        - Iteration 6: Champion achieves Sharpe 2.4751 (outlier)
        - Iterations 7-56: Champion remains dominant
        - Iteration 50: Staleness check triggered
        - Recent cohort (top 10% from iterations 0-50): median Sharpe 1.8
        - Champion Sharpe 2.4751 > cohort median 1.8 → KEEP champion (still competitive)

        Returns:
            Dictionary with staleness check results:
            - should_demote (bool): True if champion should be demoted
            - reason (str): Human-readable explanation of decision
            - metrics (dict): Supporting metrics for the decision
                - champion_sharpe (float): Champion's Sharpe ratio
                - cohort_median (float or None): Cohort median Sharpe ratio
                - cohort_size (int): Number of strategies in cohort
                - window_size (int): Number of recent strategies analyzed
                - percentile_threshold (float): Sharpe threshold for cohort membership

        Example:
            >>> staleness = tracker.check_champion_staleness()
            >>> if staleness['should_demote']:
            ...     print(f"Champion stale: {staleness['reason']}")
            ...     best_cohort = tracker.get_best_cohort_strategy()
            ...     if best_cohort:
            ...         tracker.demote_champion_to_hall_of_fame()
            ...         tracker.promote_to_champion(best_cohort)
        """
        from src.learning.config_manager import ConfigManager
        from src.constants import METRIC_SHARPE
        import numpy as np

        # Load configuration
        try:
            config_manager = ConfigManager.get_instance()
            config_manager.load_config()
            staleness_cfg = config_manager.get('anti_churn.staleness', {})
        except Exception as e:
            logger.error(f"Failed to load staleness configuration: {e}")
            return {
                'should_demote': False,
                'reason': f"Configuration error: {e}",
                'metrics': {}
            }

        # Extract configuration parameters
        check_interval = staleness_cfg.get('staleness_check_interval', 50)
        cohort_percentile = staleness_cfg.get('staleness_cohort_percentile', 0.10)
        min_cohort_size = staleness_cfg.get('staleness_min_cohort_size', 5)

        # Edge case: No champion exists
        if not self.champion:
            return {
                'should_demote': False,
                'reason': "No champion exists",
                'metrics': {}
            }

        champion_sharpe = self.champion.metrics.get(METRIC_SHARPE, 0)

        # Get recent N successful strategies from history
        successful = self.history.get_successful_iterations()
        if not successful:
            return {
                'should_demote': False,
                'reason': "No successful iterations in history",
                'metrics': {
                    'champion_sharpe': champion_sharpe,
                    'cohort_median': None,
                    'cohort_size': 0,
                    'window_size': 0
                }
            }

        # Extract last N strategies (window for staleness check)
        recent_strategies = successful[-check_interval:] if len(successful) > check_interval else successful
        window_size = len(recent_strategies)

        # Edge case: Insufficient data for meaningful analysis
        if window_size < min_cohort_size:
            return {
                'should_demote': False,
                'reason': f"Insufficient data: {window_size} strategies < minimum {min_cohort_size}",
                'metrics': {
                    'champion_sharpe': champion_sharpe,
                    'cohort_median': None,
                    'cohort_size': 0,
                    'window_size': window_size
                }
            }

        # Extract Sharpe ratios from recent strategies
        sharpe_ratios = []
        for record in recent_strategies:
            if record.metrics and METRIC_SHARPE in record.metrics:
                sharpe_ratios.append(record.metrics[METRIC_SHARPE])

        # Edge case: No valid Sharpe ratios found
        if not sharpe_ratios:
            return {
                'should_demote': False,
                'reason': "No valid Sharpe ratios in recent strategies",
                'metrics': {
                    'champion_sharpe': champion_sharpe,
                    'cohort_median': None,
                    'cohort_size': 0,
                    'window_size': window_size
                }
            }

        # Calculate percentile threshold (e.g., 90th percentile for top 10%)
        percentile_value = (1.0 - cohort_percentile) * 100  # Convert 0.10 → 90th percentile
        threshold = np.percentile(sharpe_ratios, percentile_value)

        # Build cohort: strategies above threshold (top X%)
        cohort_sharpes = [s for s in sharpe_ratios if s >= threshold]
        cohort_size = len(cohort_sharpes)

        # Edge case: Cohort too small for reliable comparison
        if cohort_size < min_cohort_size:
            return {
                'should_demote': False,
                'reason': f"Cohort too small: {cohort_size} strategies < minimum {min_cohort_size}",
                'metrics': {
                    'champion_sharpe': champion_sharpe,
                    'cohort_median': None,
                    'cohort_size': cohort_size,
                    'window_size': window_size,
                    'percentile_threshold': threshold
                }
            }

        # Calculate cohort median Sharpe ratio
        cohort_median = float(np.median(cohort_sharpes))

        # Compare champion vs cohort median
        if champion_sharpe < cohort_median:
            # Champion is stale - recent top strategies outperform
            return {
                'should_demote': True,
                'reason': (
                    f"Champion stale: Sharpe {champion_sharpe:.4f} < "
                    f"cohort median {cohort_median:.4f} "
                    f"(top {cohort_percentile*100:.0f}% of {window_size} recent strategies)"
                ),
                'metrics': {
                    'champion_sharpe': champion_sharpe,
                    'cohort_median': cohort_median,
                    'cohort_size': cohort_size,
                    'window_size': window_size,
                    'percentile_threshold': threshold
                }
            }
        else:
            # Champion still competitive
            logger.info(
                f"Champion competitive: Sharpe {champion_sharpe:.4f} >= "
                f"cohort median {cohort_median:.4f} "
                f"(cohort size: {cohort_size}, window: {window_size})"
            )
            return {
                'should_demote': False,
                'reason': (
                    f"Champion competitive: Sharpe {champion_sharpe:.4f} >= "
                    f"cohort median {cohort_median:.4f}"
                ),
                'metrics': {
                    'champion_sharpe': champion_sharpe,
                    'cohort_median': cohort_median,
                    'cohort_size': cohort_size,
                    'window_size': window_size,
                    'percentile_threshold': threshold
                }
            }
