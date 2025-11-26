"""Anti-Churn Manager for Learning System Configuration (Story 4: F4).

Manages champion update thresholds with probation period to prevent excessive
champion churn and ensure stable learning dynamics.

Requirements: F4.1 (config loading), F4.2 (dynamic thresholds), F4.3 (update tracking)
"""

import os
import yaml
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChampionUpdateRecord:
    """Record of a champion update event."""
    iteration_num: int
    was_updated: bool
    old_sharpe: Optional[float]
    new_sharpe: Optional[float]
    improvement_pct: Optional[float]
    threshold_used: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class AntiChurnManager:
    """Manage anti-churn configuration and champion update dynamics.

    Provides dynamic thresholds based on probation period and tracks
    champion update frequency to detect churn or stagnation issues.

    Phase 3 Enhancement: Hybrid Threshold System
    ---------------------------------------------
    The manager now supports BOTH relative and absolute improvement thresholds.
    A strategy can replace the champion by satisfying EITHER condition:

    1. Relative threshold: new_sharpe >= old_sharpe * (1 + relative_threshold)
       Example: At Sharpe 2.0 with 1% threshold, requires 2.02 (0.02 improvement)

    2. Absolute threshold: new_sharpe >= old_sharpe + additive_threshold
       Example: At any Sharpe with 0.02 threshold, requires +0.02 improvement

    This hybrid approach prevents the system from becoming stagnant at high
    Sharpe ratios where percentage improvements become extremely difficult.

    Attributes:
        config: Anti-churn configuration dictionary from YAML
        champion_updates: History of champion update events
        probation_period: Iterations before relaxing threshold
        probation_threshold: Required improvement during probation
        post_probation_threshold: Required improvement after probation (relative)
        additive_threshold: Required absolute improvement (Phase 3 hybrid threshold)
        min_sharpe_for_champion: Minimum Sharpe to become champion
        target_update_frequency: Target champion update rate (0.10-0.20)
    """

    def __init__(self, config_path: str = "config/learning_system.yaml"):
        """Initialize AntiChurnManager from YAML configuration.

        Args:
            config_path: Path to learning_system.yaml configuration file

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is malformed
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.champion_updates: List[ChampionUpdateRecord] = []

        # Extract configuration values
        anti_churn = self.config.get('anti_churn', {})
        self.probation_period = anti_churn.get('probation_period', 2)
        self.probation_threshold = anti_churn.get('probation_threshold', 0.10)
        self.post_probation_threshold = anti_churn.get('post_probation_threshold', 0.05)
        self.additive_threshold = anti_churn.get('additive_threshold', 0.02)
        self.min_sharpe_for_champion = anti_churn.get('min_sharpe_for_champion', 0.5)
        self.target_update_frequency = anti_churn.get('target_update_frequency', 0.15)

    def _load_config(self) -> Dict:
        """Load configuration from YAML file.

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML is malformed
        """
        # Handle both absolute and relative paths
        config_path = self.config_path
        if not os.path.isabs(config_path):
            # Try relative to project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            config_path = os.path.join(project_root, config_path)

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if not isinstance(config, dict):
            raise yaml.YAMLError(f"Invalid config format: expected dict, got {type(config)}")

        return config

    def get_required_improvement(
        self,
        current_iteration: int,
        champion_iteration: int
    ) -> float:
        """Get dynamic improvement threshold based on probation period.

        Higher threshold during probation period (recent champions) to prevent
        excessive churn, lower threshold after probation for steady improvement.

        Args:
            current_iteration: Current iteration number
            champion_iteration: Iteration when current champion was crowned

        Returns:
            Required improvement multiplier (e.g., 0.10 for 10% improvement)

        Example:
            >>> manager = AntiChurnManager()
            >>> # Champion crowned at iteration 5, now at iteration 6 (probation)
            >>> manager.get_required_improvement(6, 5)
            0.10  # probation_threshold
            >>> # Champion crowned at iteration 5, now at iteration 10 (post-probation)
            >>> manager.get_required_improvement(10, 5)
            0.05  # post_probation_threshold
        """
        iterations_since_champion = current_iteration - champion_iteration

        if iterations_since_champion <= self.probation_period:
            return self.probation_threshold
        else:
            return self.post_probation_threshold

    def get_additive_threshold(self) -> float:
        """Get the absolute improvement threshold (Phase 3 hybrid threshold).

        Returns the additive threshold value which represents the minimum absolute
        Sharpe improvement required to replace the champion. This is part of the
        hybrid threshold system where EITHER the relative OR absolute threshold
        can be satisfied.

        Returns:
            Absolute improvement threshold (e.g., 0.02 for +0.02 Sharpe improvement)

        Example:
            >>> manager = AntiChurnManager()
            >>> manager.get_additive_threshold()
            0.02
        """
        return self.additive_threshold

    def track_champion_update(
        self,
        iteration_num: int,
        was_updated: bool,
        old_sharpe: Optional[float] = None,
        new_sharpe: Optional[float] = None,
        threshold_used: Optional[float] = None
    ) -> None:
        """Record a champion update event for frequency analysis.

        Args:
            iteration_num: Current iteration number
            was_updated: Whether champion was updated this iteration
            old_sharpe: Previous champion Sharpe (if updated)
            new_sharpe: New champion Sharpe (if updated)
            threshold_used: Improvement threshold that was applied
        """
        improvement_pct = None
        if was_updated and old_sharpe and new_sharpe and old_sharpe > 0:
            improvement_pct = ((new_sharpe / old_sharpe) - 1) * 100

        record = ChampionUpdateRecord(
            iteration_num=iteration_num,
            was_updated=was_updated,
            old_sharpe=old_sharpe,
            new_sharpe=new_sharpe,
            improvement_pct=improvement_pct,
            threshold_used=threshold_used or self.post_probation_threshold
        )

        self.champion_updates.append(record)

    def analyze_update_frequency(
        self,
        window: int = 50
    ) -> Tuple[float, List[str]]:
        """Analyze champion update frequency and generate recommendations.

        Calculates update rate over recent window and checks against target
        frequency (10-20%). Generates recommendations if outside bounds.

        Args:
            window: Number of recent iterations to analyze (default: 50)

        Returns:
            Tuple of (update_frequency, recommendations)
            - update_frequency: Fraction of iterations with champion updates (0.0-1.0)
            - recommendations: List of actionable recommendations

        Recommendations:
            - Excessive churn (>20%): Suggest increasing thresholds
            - Stagnation (<10%): Suggest decreasing thresholds
            - Target range (10-20%): No action needed
        """
        if len(self.champion_updates) == 0:
            return 0.0, ["No champion updates recorded yet"]

        # Get recent window
        recent_updates = self.champion_updates[-window:]

        # Calculate update frequency
        updates_count = sum(1 for record in recent_updates if record.was_updated)
        update_frequency = updates_count / len(recent_updates) if recent_updates else 0.0

        # Generate recommendations
        recommendations = []

        # Target range: 10-20% (0.10-0.20)
        TARGET_MIN = 0.10
        TARGET_MAX = 0.20

        if update_frequency > TARGET_MAX:
            # Excessive churn
            churn_rate = update_frequency * 100
            recommendations.append(
                f"⚠️ Excessive champion churn detected ({churn_rate:.1f}% update rate)"
            )
            recommendations.append(
                f"Consider increasing probation_threshold from {self.probation_threshold:.2f} "
                f"to {min(self.probation_threshold + 0.02, 0.15):.2f}"
            )
            recommendations.append(
                f"Consider increasing post_probation_threshold from {self.post_probation_threshold:.2f} "
                f"to {min(self.post_probation_threshold + 0.01, 0.08):.2f}"
            )

        elif update_frequency < TARGET_MIN:
            # Stagnation
            stagnation_rate = update_frequency * 100
            recommendations.append(
                f"⚠️ Champion stagnation detected ({stagnation_rate:.1f}% update rate)"
            )
            recommendations.append(
                f"Consider decreasing probation_threshold from {self.probation_threshold:.2f} "
                f"to {max(self.probation_threshold - 0.02, 0.05):.2f}"
            )
            recommendations.append(
                f"Consider decreasing post_probation_threshold from {self.post_probation_threshold:.2f} "
                f"to {max(self.post_probation_threshold - 0.01, 0.03):.2f}"
            )

        else:
            # Within target range
            recommendations.append(
                f"✅ Champion update frequency healthy ({update_frequency*100:.1f}% in target range 10-20%)"
            )

        return update_frequency, recommendations

    def get_recent_updates_summary(self, count: int = 10) -> str:
        """Get human-readable summary of recent champion updates.

        Args:
            count: Number of recent updates to summarize

        Returns:
            Formatted string with update history
        """
        if not self.champion_updates:
            return "No champion updates recorded"

        recent = self.champion_updates[-count:]

        lines = [f"Recent Champion Updates (last {len(recent)} iterations):"]
        lines.append("=" * 60)

        for record in recent:
            if record.was_updated:
                improvement = f"+{record.improvement_pct:.1f}%" if record.improvement_pct else "N/A"
                lines.append(
                    f"Iter {record.iteration_num}: ✅ UPDATED "
                    f"({record.old_sharpe:.4f} → {record.new_sharpe:.4f}, {improvement})"
                )
            else:
                lines.append(f"Iter {record.iteration_num}: ➖ No update")

        lines.append("=" * 60)

        # Add frequency analysis
        update_freq, _ = self.analyze_update_frequency(window=len(recent))
        lines.append(f"Update frequency: {update_freq*100:.1f}%")

        return "\n".join(lines)


if __name__ == '__main__':
    # Example usage
    print("Anti-Churn Manager - Example Usage\n")

    # Initialize manager
    manager = AntiChurnManager()

    print("Configuration loaded:")
    print(f"  Probation period: {manager.probation_period} iterations")
    print(f"  Probation threshold: {manager.probation_threshold*100:.0f}%")
    print(f"  Post-probation threshold: {manager.post_probation_threshold*100:.0f}%")
    print(f"  Additive threshold: {manager.get_additive_threshold()}")
    print(f"  Target update frequency: {manager.target_update_frequency*100:.0f}%\n")

    # Simulate champion updates
    print("Simulating champion updates:")
    manager.track_champion_update(0, True, None, 1.2, 0.10)
    manager.track_champion_update(1, False)
    manager.track_champion_update(2, False)
    manager.track_champion_update(3, True, 1.2, 1.35, 0.10)
    manager.track_champion_update(4, False)
    manager.track_champion_update(5, False)
    manager.track_champion_update(6, True, 1.35, 1.45, 0.05)

    print(manager.get_recent_updates_summary(7))
    print()

    # Analyze frequency
    freq, recommendations = manager.analyze_update_frequency(window=7)
    print(f"Update frequency: {freq*100:.1f}%")
    print("Recommendations:")
    for rec in recommendations:
        print(f"  {rec}")
