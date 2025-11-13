"""Diversity Monitor for Population-Based Learning System.

This module tracks population diversity metrics and detects diversity collapse
conditions to prevent learning system degradation.

Responsibilities:
    - Track population diversity score (0.0-1.0)
    - Calculate champion staleness (iterations since last update)
    - Detect diversity collapse (<0.1 for 5 consecutive iterations)
    - Export metrics to Prometheus via MetricsCollector

Requirements: Task 2 - DiversityMonitor module
Fulfills: Requirements 1.3 (Diversity tracking), 1.4 (Collapse detection)
"""

import logging
from typing import Optional, Deque
from collections import deque

logger = logging.getLogger(__name__)


class DiversityMonitor:
    """Monitor population diversity and champion staleness.

    Features:
        - Real-time diversity score tracking (0.0-1.0)
        - Champion staleness calculation (iterations since update)
        - Diversity collapse detection (5-iteration sliding window)
        - Prometheus metrics integration via MetricsCollector
        - Minimal performance overhead (<1% of iteration time)

    Example:
        >>> from src.monitoring.metrics_collector import MetricsCollector
        >>> collector = MetricsCollector()
        >>> monitor = DiversityMonitor(collector)
        >>> monitor.record_diversity(iteration=1, diversity=0.85, unique_count=42, total_count=50)
        >>> monitor.record_champion_update(iteration=5, old_sharpe=1.8, new_sharpe=2.0)
        >>> staleness = monitor.calculate_staleness(current_iteration=10, last_update_iteration=5)
        >>> if monitor.check_diversity_collapse():
        ...     print("WARNING: Diversity collapse detected!")
    """

    def __init__(
        self,
        metrics_collector,
        collapse_threshold: float = 0.1,
        collapse_window: int = 5
    ):
        """Initialize DiversityMonitor.

        Args:
            metrics_collector: MetricsCollector instance for Prometheus export
            collapse_threshold: Diversity threshold for collapse detection (default: 0.1)
            collapse_window: Number of consecutive iterations to check (default: 5)
        """
        self.metrics_collector = metrics_collector
        self.collapse_threshold = collapse_threshold
        self.collapse_window = collapse_window

        # Diversity tracking
        self._diversity_history: Deque[float] = deque(maxlen=collapse_window)
        self._current_diversity: Optional[float] = None
        self._unique_count: Optional[int] = None
        self._total_count: Optional[int] = None

        # Champion tracking
        self._last_champion_update_iteration: Optional[int] = None
        self._current_staleness: int = 0

        # Collapse tracking
        self._collapse_detected: bool = False
        self._collapse_iteration: Optional[int] = None

        # Register new metrics if not already present
        self._register_metrics()

        logger.info(
            f"DiversityMonitor initialized: collapse_threshold={collapse_threshold}, "
            f"collapse_window={collapse_window}"
        )

    def _register_metrics(self) -> None:
        """Register diversity metrics with MetricsCollector."""
        # Check if metrics already registered (avoid duplicates)
        if not hasattr(self.metrics_collector, '_diversity_metrics_registered'):
            # Note: Extend MetricsCollector with diversity metrics as designed in Task 5
            # For now, we'll use the existing metrics structure
            self.metrics_collector._diversity_metrics_registered = True
            logger.debug("Diversity metrics registered with MetricsCollector")

    def record_diversity(
        self,
        iteration: int,
        diversity: float,
        unique_count: int,
        total_count: int
    ) -> None:
        """Record population diversity metrics after each generation.

        Args:
            iteration: Current iteration number
            diversity: Diversity score (0.0-1.0, where 1.0 = all unique)
            unique_count: Number of unique individuals in population
            total_count: Total population size

        Raises:
            ValueError: If diversity not in [0.0, 1.0] or counts invalid
        """
        # Validate inputs
        if not 0.0 <= diversity <= 1.0:
            raise ValueError(f"Diversity must be in [0.0, 1.0], got {diversity}")

        if unique_count < 0 or total_count < 0:
            raise ValueError(f"Counts must be non-negative: unique={unique_count}, total={total_count}")

        if unique_count > total_count:
            raise ValueError(f"Unique count ({unique_count}) cannot exceed total ({total_count})")

        # Update internal state
        self._current_diversity = diversity
        self._unique_count = unique_count
        self._total_count = total_count

        # Add to sliding window
        self._diversity_history.append(diversity)

        # Export to Prometheus (via MetricsCollector extension from Task 5)
        # For now, use existing metric recording pattern
        self.metrics_collector.record_strategy_diversity(unique_count)

        logger.debug(
            f"Iteration {iteration}: diversity={diversity:.4f}, "
            f"unique={unique_count}/{total_count}"
        )

    def record_champion_update(
        self,
        iteration: int,
        old_sharpe: float,
        new_sharpe: float
    ) -> None:
        """Record champion update event.

        Args:
            iteration: Iteration number when champion was updated
            old_sharpe: Previous champion's Sharpe ratio
            new_sharpe: New champion's Sharpe ratio
        """
        self._last_champion_update_iteration = iteration
        self._current_staleness = 0

        # Export to MetricsCollector
        self.metrics_collector.record_champion_update(
            old_sharpe=old_sharpe,
            new_sharpe=new_sharpe,
            iteration_num=iteration
        )

        improvement = ((new_sharpe / old_sharpe) - 1) * 100 if old_sharpe > 0 else 0
        logger.info(
            f"Champion updated at iteration {iteration}: "
            f"{old_sharpe:.4f} -> {new_sharpe:.4f} (+{improvement:.1f}%)"
        )

    def calculate_staleness(
        self,
        current_iteration: int,
        last_update_iteration: Optional[int] = None
    ) -> int:
        """Calculate champion staleness (iterations since last update).

        Args:
            current_iteration: Current iteration number
            last_update_iteration: Iteration of last champion update (optional)
                                  If None, uses internally tracked value

        Returns:
            int: Number of iterations since last champion update

        Raises:
            ValueError: If no champion update has been recorded
        """
        # Use provided value or fall back to internal tracking
        update_iteration = (
            last_update_iteration
            if last_update_iteration is not None
            else self._last_champion_update_iteration
        )

        if update_iteration is None:
            raise ValueError(
                "Cannot calculate staleness: no champion update recorded. "
                "Call record_champion_update() first."
            )

        staleness = current_iteration - update_iteration
        self._current_staleness = staleness

        return staleness

    def check_diversity_collapse(self, window: Optional[int] = None) -> bool:
        """Check if diversity collapse has occurred.

        Diversity collapse is detected when diversity falls below the collapse
        threshold for a consecutive window of iterations.

        Args:
            window: Number of iterations to check (default: use collapse_window from init)

        Returns:
            bool: True if diversity collapse detected, False otherwise

        Note:
            Requires at least 'window' diversity measurements to evaluate.
            Returns False if insufficient history.
        """
        check_window = window if window is not None else self.collapse_window

        # Need enough history to check
        if len(self._diversity_history) < check_window:
            return False

        # Check if all values in window are below threshold
        recent_diversity = list(self._diversity_history)[-check_window:]
        collapse = all(d < self.collapse_threshold for d in recent_diversity)

        # Update collapse state
        if collapse and not self._collapse_detected:
            self._collapse_detected = True
            self._collapse_iteration = len(self._diversity_history)
            logger.warning(
                f"DIVERSITY COLLAPSE DETECTED! "
                f"Diversity < {self.collapse_threshold} for {check_window} consecutive iterations. "
                f"Recent diversity: {[f'{d:.4f}' for d in recent_diversity]}"
            )
        elif not collapse and self._collapse_detected:
            # Collapse recovered
            self._collapse_detected = False
            logger.info(
                f"Diversity collapse recovered. Current diversity: {self._current_diversity:.4f}"
            )

        return collapse

    def get_current_diversity(self) -> Optional[float]:
        """Get the most recently recorded diversity score.

        Returns:
            Optional[float]: Current diversity (0.0-1.0), or None if no data recorded
        """
        return self._current_diversity

    def get_current_staleness(self) -> int:
        """Get the current champion staleness.

        Returns:
            int: Number of iterations since last champion update (0 if just updated)
        """
        return self._current_staleness

    def get_diversity_history(self) -> list[float]:
        """Get recent diversity history (up to collapse_window values).

        Returns:
            list[float]: Recent diversity values (oldest to newest)
        """
        return list(self._diversity_history)

    def is_collapse_detected(self) -> bool:
        """Check if diversity collapse is currently detected.

        Returns:
            bool: True if collapse currently detected, False otherwise
        """
        return self._collapse_detected

    def get_status(self) -> dict:
        """Get comprehensive status of diversity monitoring.

        Returns:
            dict: Status information including:
                - current_diversity: Latest diversity score
                - unique_count: Number of unique individuals
                - total_count: Total population size
                - staleness: Iterations since last champion update
                - diversity_history_length: Number of recorded measurements
                - collapse_detected: Whether collapse is currently detected
                - collapse_iteration: When collapse was first detected (if applicable)
        """
        return {
            'current_diversity': self._current_diversity,
            'unique_count': self._unique_count,
            'total_count': self._total_count,
            'staleness': self._current_staleness,
            'diversity_history_length': len(self._diversity_history),
            'collapse_detected': self._collapse_detected,
            'collapse_iteration': self._collapse_iteration,
            'collapse_threshold': self.collapse_threshold,
            'collapse_window': self.collapse_window
        }

    def reset(self) -> None:
        """Reset all tracking state (useful for testing or new runs).

        Clears:
            - Diversity history
            - Champion update tracking
            - Collapse detection state
        """
        self._diversity_history.clear()
        self._current_diversity = None
        self._unique_count = None
        self._total_count = None
        self._last_champion_update_iteration = None
        self._current_staleness = 0
        self._collapse_detected = False
        self._collapse_iteration = None

        logger.info("DiversityMonitor state reset")
