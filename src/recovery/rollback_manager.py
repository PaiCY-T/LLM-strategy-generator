"""Rollback Manager
=================

Provides rollback functionality for reverting to previous champion strategies.

This module enables operators to:
- View historical champion strategies
- Rollback to a specific iteration
- Validate that rollback candidates still work
- Maintain audit trail of rollback operations

Usage:
    >>> from src.repository.hall_of_fame import HallOfFameRepository
    >>> from src.recovery.rollback_manager import RollbackManager
    >>>
    >>> hall_of_fame = HallOfFameRepository()
    >>> rollback_mgr = RollbackManager(hall_of_fame)
    >>>
    >>> # View champion history
    >>> champions = rollback_mgr.get_champion_history(limit=10)
    >>> for champ in champions:
    ...     print(f"Iteration {champ.iteration_num}: Sharpe {champ.metrics['sharpe_ratio']:.2f}")
    >>>
    >>> # Rollback to specific iteration
    >>> success, msg = rollback_mgr.rollback_to_iteration(
    ...     target_iteration=5,
    ...     reason="Production issue - reverting to stable version",
    ...     operator="john@example.com",
    ...     data=finlab_data
    ... )
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import json
import uuid
from pathlib import Path

from src.repository.hall_of_fame import HallOfFameRepository, StrategyGenome


@dataclass
class ChampionStrategy:
    """Champion strategy representation for rollback system.

    This is a simplified representation used by the rollback system,
    compatible with the ChampionStrategy used in autonomous_loop.py.

    Attributes:
        iteration_num: Which iteration produced this champion
        code: Complete strategy code
        parameters: Extracted parameter values
        metrics: Performance metrics
        success_patterns: Patterns that contributed to success
        timestamp: When this champion was established
    """
    iteration_num: int
    code: str
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    success_patterns: List[str]
    timestamp: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> 'ChampionStrategy':
        """Create ChampionStrategy from dictionary."""
        return ChampionStrategy(**data)


@dataclass
class RollbackRecord:
    """Audit record for rollback operations.

    Attributes:
        rollback_id: Unique identifier for this rollback (UUID)
        from_iteration: Iteration we're rolling back from
        to_iteration: Target iteration we're rolling back to
        reason: Human-readable explanation for rollback
        operator: Name/email of person performing rollback
        timestamp: When rollback was performed (ISO format)
        validation_passed: Whether rollback candidate passed validation
        validation_report: Detailed validation results
    """
    rollback_id: str
    from_iteration: int
    to_iteration: int
    reason: str
    operator: str
    timestamp: str
    validation_passed: bool
    validation_report: Dict

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> 'RollbackRecord':
        """Create RollbackRecord from dictionary."""
        return RollbackRecord(**data)


class RollbackManager:
    """Manages rollback operations for champion strategies.

    Features:
        - Query historical champions
        - Validate rollback candidates
        - Update current champion
        - Maintain audit trail

    Usage:
        >>> rollback_mgr = RollbackManager(hall_of_fame)
        >>> success, msg = rollback_mgr.rollback_to_iteration(
        ...     target_iteration=5,
        ...     reason="Production issue",
        ...     operator="operator@example.com",
        ...     data=finlab_data
        ... )
    """

    def __init__(
        self,
        hall_of_fame: HallOfFameRepository,
        rollback_log_file: str = "rollback_history.json"
    ):
        """Initialize RollbackManager.

        Args:
            hall_of_fame: HallOfFameRepository instance for strategy access
            rollback_log_file: Path to rollback audit trail file
        """
        self.hall_of_fame = hall_of_fame
        self.rollback_log_file = Path(rollback_log_file)
        self.rollback_log: List[RollbackRecord] = []

        # Load existing rollback history if available
        self._load_rollback_history()

    def _load_rollback_history(self) -> None:
        """Load existing rollback history from file."""
        if self.rollback_log_file.exists():
            try:
                with open(self.rollback_log_file, 'r', encoding='utf-8') as f:
                    # Read all lines (one JSON object per line)
                    for line in f:
                        line = line.strip()
                        if line:
                            record_dict = json.loads(line)
                            record = RollbackRecord.from_dict(record_dict)
                            self.rollback_log.append(record)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # Log warning but continue - corrupt history file shouldn't block operations
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to load rollback history: {e}")

    def get_champion_history(self, limit: int = 20) -> List[ChampionStrategy]:
        """Retrieve historical champion strategies sorted by date.

        Queries Hall of Fame for all Champions tier strategies and converts
        them to ChampionStrategy format for rollback operations.

        Args:
            limit: Maximum number of champions to return (default: 20)

        Returns:
            List of ChampionStrategy objects sorted by created_at (newest first)

        Example:
            >>> champions = rollback_mgr.get_champion_history(limit=10)
            >>> for champ in champions:
            ...     print(f"Iteration {champ.iteration_num}: Sharpe {champ.metrics['sharpe_ratio']:.2f}")
        """
        # Query champions from Hall of Fame (Sharpe >= 2.0)
        genomes = self.hall_of_fame.get_champions(limit=limit, sort_by='sharpe_ratio')

        # Convert StrategyGenome -> ChampionStrategy
        champions = []
        for genome in genomes:
            # Extract iteration_num from parameters (stored with __ prefix)
            iteration_num = genome.parameters.get('__iteration_num__', 0)

            # Remove metadata from parameters
            clean_params = {k: v for k, v in genome.parameters.items() if not k.startswith('__')}

            champion = ChampionStrategy(
                iteration_num=iteration_num,
                code=genome.strategy_code or "",
                parameters=clean_params,
                metrics=genome.metrics,
                success_patterns=genome.success_patterns or [],
                timestamp=genome.created_at
            )
            champions.append(champion)

        # Sort by timestamp descending (newest first)
        champions.sort(key=lambda c: c.timestamp, reverse=True)

        return champions

    def rollback_to_iteration(
        self,
        target_iteration: int,
        reason: str,
        operator: str,
        data: Any,
        validate: bool = True
    ) -> Tuple[bool, str]:
        """Rollback to a specific champion iteration.

        Workflow:
            1. Find champion matching target_iteration
            2. Validate that champion still works (if validate=True)
            3. Update current champion in Hall of Fame
            4. Record rollback in audit trail

        Args:
            target_iteration: Iteration number to rollback to
            reason: Human-readable explanation for rollback
            operator: Name/email of person performing rollback
            data: Finlab data object for validation
            validate: Whether to validate rollback candidate (default: True)

        Returns:
            Tuple of (success: bool, message: str)

        Example:
            >>> success, msg = rollback_mgr.rollback_to_iteration(
            ...     target_iteration=5,
            ...     reason="Production issue - reverting to stable version",
            ...     operator="john@example.com",
            ...     data=finlab_data
            ... )
            >>> print(msg)
        """
        import logging
        logger = logging.getLogger(__name__)

        # Get current champion for "from_iteration"
        current_champion = self.hall_of_fame.get_current_champion()
        from_iteration = 0
        if current_champion:
            from_iteration = current_champion.parameters.get('__iteration_num__', 0)

        # Step 1: Find champion matching target_iteration
        champions = self.get_champion_history(limit=100)  # Get more for search
        target_champion = None

        for champ in champions:
            if champ.iteration_num == target_iteration:
                target_champion = champ
                break

        if target_champion is None:
            error_msg = f"No champion found for iteration {target_iteration}"
            logger.error(error_msg)

            # Record failed rollback attempt
            self.record_rollback(
                from_iteration=from_iteration,
                to_iteration=target_iteration,
                reason=reason,
                operator=operator,
                validation_passed=False,
                validation_report={'error': error_msg}
            )

            return False, error_msg

        # Step 2: Validate rollback candidate (if requested)
        validation_report = {}
        if validate:
            is_valid, validation_report = self.validate_rollback_champion(
                champion=target_champion,
                data=data
            )

            if not is_valid:
                error_msg = f"Validation failed: {validation_report.get('error', 'Unknown error')}"
                logger.error(error_msg)

                # Record failed rollback attempt
                self.record_rollback(
                    from_iteration=from_iteration,
                    to_iteration=target_iteration,
                    reason=reason,
                    operator=operator,
                    validation_passed=False,
                    validation_report=validation_report
                )

                return False, error_msg

        # Step 3: Update current champion in Hall of Fame
        # Add champion strategy to Hall of Fame (will be classified to appropriate tier)
        params_with_metadata = target_champion.parameters.copy()
        params_with_metadata['__iteration_num__'] = target_champion.iteration_num
        params_with_metadata['__rollback_timestamp__'] = datetime.now().isoformat()
        params_with_metadata['__rollback_from_iteration__'] = from_iteration

        success, save_msg = self.hall_of_fame.add_strategy(
            template_name='autonomous_generated',
            parameters=params_with_metadata,
            metrics=target_champion.metrics,
            strategy_code=target_champion.code,
            success_patterns=target_champion.success_patterns
        )

        if not success:
            error_msg = f"Failed to save rollback champion: {save_msg}"
            logger.error(error_msg)

            # Record failed rollback attempt
            self.record_rollback(
                from_iteration=from_iteration,
                to_iteration=target_iteration,
                reason=reason,
                operator=operator,
                validation_passed=validate,
                validation_report=validation_report if validate else {'skipped': True}
            )

            return False, error_msg

        # Step 4: Record successful rollback
        self.record_rollback(
            from_iteration=from_iteration,
            to_iteration=target_iteration,
            reason=reason,
            operator=operator,
            validation_passed=True,
            validation_report=validation_report if validate else {'skipped': True}
        )

        success_msg = f"Successfully rolled back from iteration {from_iteration} to {target_iteration}"
        logger.info(success_msg)

        return True, success_msg

    def validate_rollback_champion(
        self,
        champion: ChampionStrategy,
        data: Any,
        min_sharpe_threshold: float = 0.5
    ) -> Tuple[bool, Dict]:
        """Validate that a rollback champion still works.

        Executes the champion's code with current data and validates:
        1. Execution succeeds without errors
        2. Metrics are reasonable (Sharpe > threshold)

        Args:
            champion: ChampionStrategy to validate
            data: Finlab data object for execution
            min_sharpe_threshold: Minimum Sharpe ratio to consider valid (default: 0.5)

        Returns:
            Tuple of (is_valid: bool, validation_report: Dict)

        Example:
            >>> is_valid, report = rollback_mgr.validate_rollback_champion(
            ...     champion=target_champion,
            ...     data=finlab_data
            ... )
            >>> if not is_valid:
            ...     print(f"Validation failed: {report['error']}")
        """
        from artifacts.working.modules.sandbox_simple import execute_strategy_safe

        report = {
            'iteration_num': champion.iteration_num,
            'original_sharpe': champion.metrics.get('sharpe_ratio', 0),
            'validation_timestamp': datetime.now().isoformat()
        }

        try:
            # Execute champion code
            success, metrics, error = execute_strategy_safe(
                code=champion.code,
                data=data,
                timeout=120
            )

            report['execution_success'] = success
            report['execution_error'] = error
            report['execution_metrics'] = metrics

            # Check execution success
            if not success:
                report['error'] = f"Execution failed: {error}"
                return False, report

            # Check metrics availability
            if not metrics or 'sharpe_ratio' not in metrics:
                report['error'] = "No metrics returned from execution"
                return False, report

            # Validate metrics are reasonable
            current_sharpe = metrics.get('sharpe_ratio', 0)
            report['current_sharpe'] = current_sharpe

            if current_sharpe < min_sharpe_threshold:
                report['error'] = (
                    f"Sharpe ratio {current_sharpe:.2f} below threshold {min_sharpe_threshold:.2f}"
                )
                return False, report

            # Validation passed
            report['status'] = 'valid'
            report['sharpe_degradation'] = champion.metrics.get('sharpe_ratio', 0) - current_sharpe

            return True, report

        except Exception as e:
            report['error'] = f"Validation exception: {str(e)}"
            report['exception_type'] = type(e).__name__
            return False, report

    def record_rollback(
        self,
        from_iteration: int,
        to_iteration: int,
        reason: str,
        operator: str,
        validation_passed: bool,
        validation_report: Dict
    ) -> None:
        """Record rollback operation in audit trail.

        Creates a RollbackRecord and appends it to both in-memory log
        and persistent JSON file (append mode).

        Args:
            from_iteration: Iteration we're rolling back from
            to_iteration: Target iteration we're rolling back to
            reason: Human-readable explanation
            operator: Name/email of person performing rollback
            validation_passed: Whether validation succeeded
            validation_report: Detailed validation results

        Example:
            >>> rollback_mgr.record_rollback(
            ...     from_iteration=10,
            ...     to_iteration=5,
            ...     reason="Production issue",
            ...     operator="john@example.com",
            ...     validation_passed=True,
            ...     validation_report={'sharpe': 2.3}
            ... )
        """
        # Generate unique rollback ID
        rollback_id = str(uuid.uuid4())

        # Create rollback record
        record = RollbackRecord(
            rollback_id=rollback_id,
            from_iteration=from_iteration,
            to_iteration=to_iteration,
            reason=reason,
            operator=operator,
            timestamp=datetime.now().isoformat(),
            validation_passed=validation_passed,
            validation_report=validation_report
        )

        # Add to in-memory log
        self.rollback_log.append(record)

        # Append to persistent log file (one JSON object per line)
        try:
            # Ensure directory exists
            self.rollback_log_file.parent.mkdir(parents=True, exist_ok=True)

            # Append record as JSON line
            with open(self.rollback_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record.to_dict(), ensure_ascii=False) + '\n')

        except (IOError, OSError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to save rollback record: {e}")

    def get_rollback_history(self, limit: Optional[int] = None) -> List[RollbackRecord]:
        """Get rollback audit trail.

        Args:
            limit: Maximum number of records to return (default: None = all)

        Returns:
            List of RollbackRecord objects (newest first)

        Example:
            >>> history = rollback_mgr.get_rollback_history(limit=10)
            >>> for record in history:
            ...     print(f"{record.timestamp}: {record.from_iteration} -> {record.to_iteration}")
        """
        # Return most recent first
        sorted_log = sorted(self.rollback_log, key=lambda r: r.timestamp, reverse=True)

        if limit is not None:
            return sorted_log[:limit]
        return sorted_log
