"""
Adaptive Learner - Learn from mutation history to optimize tier selection.

Tracks mutation success rates by tier and adapts selection thresholds
based on historical performance to maximize evolution effectiveness.

Architecture: Phase 2.0+ Factor Graph System
Task: D.4 - Adaptive Mutation Tier Selection
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import json
import numpy as np
from pathlib import Path


@dataclass
class TierPerformance:
    """
    Track performance metrics for a mutation tier.

    Attributes:
        tier: Tier number (1, 2, or 3)
        attempts: Total mutation attempts
        successes: Successful mutations
        failures: Failed mutations
        avg_fitness_delta: Average fitness improvement from mutations
        recent_success_rate: Recent success rate (last N mutations)
    """
    tier: int
    attempts: int = 0
    successes: int = 0
    failures: int = 0
    avg_fitness_delta: float = 0.0
    recent_success_rate: float = 0.5

    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.attempts == 0:
            return 0.5  # Default neutral rate
        return self.successes / self.attempts

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TierPerformance':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class MutationHistory:
    """
    Record of a single mutation attempt.

    Attributes:
        tier: Tier used (1, 2, or 3)
        mutation_type: Type of mutation
        success: Whether mutation succeeded
        fitness_delta: Change in fitness (if available)
        timestamp: When mutation occurred
        strategy_id: ID of strategy that was mutated
    """
    tier: int
    mutation_type: str
    success: bool
    fitness_delta: Optional[float] = None
    timestamp: Optional[str] = None
    strategy_id: Optional[str] = None


class AdaptiveLearner:
    """
    Learn from mutation history to optimize tier selection.

    Tracks mutation success rates and performance by tier, then adapts
    tier selection thresholds to maximize evolution effectiveness.

    The learner maintains:
    - Historical performance per tier
    - Recent mutation history for trend analysis
    - Adaptive threshold recommendations
    - Performance metrics and analytics

    Attributes:
        history_window: Number of recent mutations to track (default: 100)
        learning_rate: Rate of threshold adjustment (default: 0.1)
        min_samples: Minimum samples before adapting (default: 20)

    Example:
        >>> learner = AdaptiveLearner()
        >>> learner.update_tier_stats(tier=2, success=True, metrics={'fitness_delta': 0.05})
        >>> learner.update_tier_stats(tier=2, success=True, metrics={'fitness_delta': 0.03})
        >>> learner.update_tier_stats(tier=3, success=False, metrics={'fitness_delta': -0.02})
        >>>
        >>> # Get recommendations
        >>> recommendations = learner.get_tier_recommendations()
        >>> print(recommendations['recommended_tier'])  # Tier with best performance
        >>> print(recommendations['threshold_adjustments'])  # Suggested threshold changes
    """

    def __init__(
        self,
        history_window: int = 100,
        learning_rate: float = 0.1,
        min_samples: int = 20,
        persistence_path: Optional[str] = None
    ):
        """
        Initialize adaptive learner.

        Args:
            history_window: Number of recent mutations to track
            learning_rate: Rate of threshold adjustment (0.0-1.0)
            min_samples: Minimum samples before making recommendations
            persistence_path: Optional path to save/load history
        """
        self.history_window = history_window
        self.learning_rate = learning_rate
        self.min_samples = min_samples
        self.persistence_path = persistence_path

        # Track performance by tier
        self.tier_performance: Dict[int, TierPerformance] = {
            1: TierPerformance(tier=1),
            2: TierPerformance(tier=2),
            3: TierPerformance(tier=3)
        }

        # Track recent mutation history
        self.mutation_history: List[MutationHistory] = []

        # Track threshold evolution
        self.threshold_history: List[Dict[str, float]] = []

        # Load persisted data if available
        if persistence_path:
            self._load_history()

    def update_tier_stats(
        self,
        tier: int,
        success: bool,
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update tier performance statistics.

        Args:
            tier: Tier number (1, 2, or 3)
            success: Whether mutation succeeded
            metrics: Optional metrics (fitness_delta, strategy_id, etc.)

        Example:
            >>> learner.update_tier_stats(
            ...     tier=2,
            ...     success=True,
            ...     metrics={'fitness_delta': 0.05, 'strategy_id': 'strat_123'}
            ... )
        """
        if tier not in [1, 2, 3]:
            raise ValueError(f"Invalid tier: {tier}. Must be 1, 2, or 3")

        if metrics is None:
            metrics = {}

        # Update tier performance
        perf = self.tier_performance[tier]
        perf.attempts += 1
        if success:
            perf.successes += 1
        else:
            perf.failures += 1

        # Update average fitness delta
        fitness_delta = metrics.get('fitness_delta', 0.0)
        if fitness_delta is not None:
            # Exponential moving average
            alpha = 0.1
            perf.avg_fitness_delta = (
                alpha * fitness_delta +
                (1 - alpha) * perf.avg_fitness_delta
            )

        # Add to mutation history
        mutation = MutationHistory(
            tier=tier,
            mutation_type=metrics.get('mutation_type', 'unknown'),
            success=success,
            fitness_delta=fitness_delta,
            strategy_id=metrics.get('strategy_id')
        )
        self.mutation_history.append(mutation)

        # Trim history to window size
        if len(self.mutation_history) > self.history_window:
            self.mutation_history = self.mutation_history[-self.history_window:]

        # Update recent success rate
        self._update_recent_success_rates()

        # Persist if configured
        if self.persistence_path:
            self._save_history()

    def adjust_thresholds(
        self,
        current_tier1_threshold: float,
        current_tier2_threshold: float
    ) -> Dict[str, float]:
        """
        Adjust tier selection thresholds based on historical performance.

        Strategy:
        - If a tier has high success rate, expand its usage range
        - If a tier has low success rate, shrink its usage range
        - Balance exploration (trying different tiers) with exploitation

        Args:
            current_tier1_threshold: Current Tier 1 threshold
            current_tier2_threshold: Current Tier 2 threshold

        Returns:
            Dictionary with recommended thresholds

        Example:
            >>> learner = AdaptiveLearner()
            >>> # ... update stats ...
            >>> new_thresholds = learner.adjust_thresholds(0.3, 0.7)
            >>> print(new_thresholds)
            {'tier1_threshold': 0.32, 'tier2_threshold': 0.68}
        """
        # Check if we have enough samples
        total_attempts = sum(p.attempts for p in self.tier_performance.values())
        if total_attempts < self.min_samples:
            return {
                'tier1_threshold': current_tier1_threshold,
                'tier2_threshold': current_tier2_threshold,
                'adjusted': False,
                'reason': f'Insufficient samples ({total_attempts}/{self.min_samples})'
            }

        # Get success rates
        tier1_rate = self.tier_performance[1].recent_success_rate
        tier2_rate = self.tier_performance[2].recent_success_rate
        tier3_rate = self.tier_performance[3].recent_success_rate

        # Calculate adjustments
        # Tier 1: High success → expand range (increase threshold)
        tier1_adjustment = (tier1_rate - 0.5) * self.learning_rate
        new_tier1 = current_tier1_threshold + tier1_adjustment
        new_tier1 = max(0.1, min(0.5, new_tier1))  # Clamp to [0.1, 0.5]

        # Tier 2: Adjust based on relative performance
        # High Tier 2 success → maintain/expand range
        # High Tier 3 success → shrink Tier 2 range (expand Tier 3)
        tier2_adjustment = (tier2_rate - tier3_rate) * self.learning_rate * 0.5
        new_tier2 = current_tier2_threshold + tier2_adjustment
        new_tier2 = max(new_tier1 + 0.1, min(0.9, new_tier2))  # Clamp

        # Record threshold adjustment
        self.threshold_history.append({
            'tier1_threshold': new_tier1,
            'tier2_threshold': new_tier2,
            'tier1_rate': tier1_rate,
            'tier2_rate': tier2_rate,
            'tier3_rate': tier3_rate,
        })

        return {
            'tier1_threshold': new_tier1,
            'tier2_threshold': new_tier2,
            'adjusted': True,
            'tier1_delta': new_tier1 - current_tier1_threshold,
            'tier2_delta': new_tier2 - current_tier2_threshold,
        }

    def get_tier_recommendations(self) -> Dict[str, Any]:
        """
        Provide tier selection recommendations based on history.

        Returns comprehensive analysis including:
        - Best performing tier
        - Recommended tier for next mutation
        - Threshold adjustment suggestions
        - Performance trends
        - Risk assessment

        Returns:
            Dictionary with recommendations and analytics

        Example:
            >>> recommendations = learner.get_tier_recommendations()
            >>> print(recommendations['recommended_tier'])  # Best tier to use
            >>> print(recommendations['confidence'])  # Confidence in recommendation
            >>> print(recommendations['performance_summary'])  # Performance by tier
        """
        # Calculate performance metrics per tier
        performance_summary = {}
        for tier, perf in self.tier_performance.items():
            performance_summary[f'tier{tier}'] = {
                'success_rate': perf.success_rate,
                'recent_success_rate': perf.recent_success_rate,
                'avg_fitness_delta': perf.avg_fitness_delta,
                'attempts': perf.attempts,
                'trend': self._calculate_trend(tier)
            }

        # Identify best performing tier
        best_tier = self._identify_best_tier()

        # Calculate confidence in recommendation
        confidence = self._calculate_confidence()

        # Generate recommendations
        recommendations = {
            'recommended_tier': best_tier,
            'confidence': confidence,
            'performance_summary': performance_summary,
            'threshold_recommendations': self._get_threshold_recommendations(),
            'insights': self._generate_insights(),
            'total_mutations': sum(p.attempts for p in self.tier_performance.values())
        }

        return recommendations

    def get_tier_stats(self) -> Dict[str, Any]:
        """
        Get current tier statistics.

        Returns:
            Dictionary with detailed statistics per tier
        """
        stats = {}
        for tier, perf in self.tier_performance.items():
            stats[f'tier{tier}'] = {
                'attempts': perf.attempts,
                'successes': perf.successes,
                'failures': perf.failures,
                'success_rate': perf.success_rate,
                'recent_success_rate': perf.recent_success_rate,
                'avg_fitness_delta': perf.avg_fitness_delta
            }
        return stats

    def reset_stats(self) -> None:
        """Reset all statistics (useful for testing or fresh start)."""
        self.tier_performance = {
            1: TierPerformance(tier=1),
            2: TierPerformance(tier=2),
            3: TierPerformance(tier=3)
        }
        self.mutation_history.clear()
        self.threshold_history.clear()

    def _update_recent_success_rates(self) -> None:
        """Update recent success rates for each tier."""
        if not self.mutation_history:
            return

        # Calculate recent success rate per tier (last N mutations per tier)
        recent_window = min(20, self.history_window // 3)
        for tier in [1, 2, 3]:
            tier_mutations = [m for m in self.mutation_history if m.tier == tier]
            if len(tier_mutations) >= 3:
                recent = tier_mutations[-recent_window:]
                successes = sum(1 for m in recent if m.success)
                self.tier_performance[tier].recent_success_rate = successes / len(recent)

    def _identify_best_tier(self) -> int:
        """
        Identify best performing tier based on multiple criteria.

        Considers:
        - Recent success rate
        - Average fitness delta
        - Consistency (variance in success)

        Returns:
            Best tier number (1, 2, or 3)
        """
        # Score each tier
        scores = {}
        for tier, perf in self.tier_performance.items():
            if perf.attempts < 3:
                # Not enough data
                scores[tier] = 0.0
            else:
                # Weighted score: recent success (60%) + fitness delta (40%)
                success_score = perf.recent_success_rate
                fitness_score = (perf.avg_fitness_delta + 0.1) / 0.2  # Normalize
                fitness_score = max(0.0, min(1.0, fitness_score))
                scores[tier] = 0.6 * success_score + 0.4 * fitness_score

        # Return tier with highest score
        if not scores or max(scores.values()) == 0.0:
            return 2  # Default to Tier 2
        return max(scores, key=scores.get)

    def _calculate_confidence(self) -> float:
        """
        Calculate confidence in recommendations.

        Based on:
        - Number of samples
        - Variance in performance
        - Consistency of trends

        Returns:
            Confidence score [0.0-1.0]
        """
        total_attempts = sum(p.attempts for p in self.tier_performance.values())

        if total_attempts == 0:
            return 0.0

        # Sample confidence (more samples = higher confidence)
        sample_confidence = min(total_attempts / (self.min_samples * 3), 1.0)

        # Performance variance (consistent performance = higher confidence)
        success_rates = [p.recent_success_rate for p in self.tier_performance.values()]
        variance = np.var(success_rates)
        variance_confidence = 1.0 - min(variance * 2, 1.0)

        # Combined confidence
        confidence = 0.6 * sample_confidence + 0.4 * variance_confidence

        return confidence

    def _calculate_trend(self, tier: int) -> str:
        """
        Calculate trend for a tier (improving, stable, declining).

        Args:
            tier: Tier number

        Returns:
            Trend string
        """
        # Get recent mutations for this tier
        tier_mutations = [m for m in self.mutation_history if m.tier == tier]

        if len(tier_mutations) < 10:
            return "insufficient_data"

        # Split into early and late halves
        mid = len(tier_mutations) // 2
        early = tier_mutations[:mid]
        late = tier_mutations[mid:]

        early_rate = sum(1 for m in early if m.success) / len(early)
        late_rate = sum(1 for m in late if m.success) / len(late)

        diff = late_rate - early_rate
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"

    def _get_threshold_recommendations(self) -> Dict[str, str]:
        """Generate threshold adjustment recommendations."""
        recommendations = {}

        for tier in [1, 2, 3]:
            perf = self.tier_performance[tier]
            if perf.attempts < self.min_samples // 3:
                recommendations[f'tier{tier}'] = "Need more samples"
            elif perf.recent_success_rate > 0.7:
                recommendations[f'tier{tier}'] = "High success - expand usage"
            elif perf.recent_success_rate < 0.3:
                recommendations[f'tier{tier}'] = "Low success - reduce usage"
            else:
                recommendations[f'tier{tier}'] = "Moderate performance - maintain"

        return recommendations

    def _generate_insights(self) -> List[str]:
        """Generate actionable insights from performance data."""
        insights = []

        # Overall performance insight
        total = sum(p.attempts for p in self.tier_performance.values())
        if total == 0:
            insights.append("No mutation history yet. Start evolving to gather data.")
            return insights

        # Per-tier insights
        for tier in [1, 2, 3]:
            perf = self.tier_performance[tier]
            if perf.attempts == 0:
                insights.append(f"Tier {tier} unused - consider testing")
            elif perf.recent_success_rate > 0.7:
                insights.append(f"Tier {tier} performing well (success rate: {perf.recent_success_rate:.1%})")
            elif perf.recent_success_rate < 0.3:
                insights.append(f"Tier {tier} struggling (success rate: {perf.recent_success_rate:.1%})")

        # Fitness delta insights
        best_fitness_tier = max(
            self.tier_performance.items(),
            key=lambda x: x[1].avg_fitness_delta
        )[0]
        insights.append(f"Tier {best_fitness_tier} provides best fitness improvements")

        return insights

    def _save_history(self) -> None:
        """Save history to persistence file."""
        if not self.persistence_path:
            return

        try:
            data = {
                'tier_performance': {
                    tier: perf.to_dict()
                    for tier, perf in self.tier_performance.items()
                },
                'mutation_history': [
                    asdict(m) for m in self.mutation_history[-self.history_window:]
                ],
                'threshold_history': self.threshold_history[-100:]
            }

            path = Path(self.persistence_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            # Don't fail if persistence fails
            print(f"Warning: Could not save history: {e}")

    def _load_history(self) -> None:
        """Load history from persistence file."""
        if not self.persistence_path:
            return

        try:
            path = Path(self.persistence_path)
            if not path.exists():
                return

            with open(path, 'r') as f:
                data = json.load(f)

            # Load tier performance
            for tier_str, perf_data in data.get('tier_performance', {}).items():
                tier = int(tier_str) if isinstance(tier_str, str) else tier_str
                self.tier_performance[tier] = TierPerformance.from_dict(perf_data)

            # Load mutation history
            for m_data in data.get('mutation_history', []):
                self.mutation_history.append(MutationHistory(**m_data))

            # Load threshold history
            self.threshold_history = data.get('threshold_history', [])

        except Exception as e:
            # Don't fail if loading fails
            print(f"Warning: Could not load history: {e}")
