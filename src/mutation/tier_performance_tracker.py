"""
Tier Performance Tracker - Track mutation performance metrics per tier.

Collects and analyzes performance metrics for each mutation tier to:
- Monitor success rates per tier
- Track performance improvements (fitness deltas)
- Identify most effective tiers
- Generate tier comparison reports

Architecture: Structural Mutation Phase 2 - Phase D.5
Task: D.5 - Three-Tier Mutation System Integration
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import numpy as np


@dataclass
class MutationRecord:
    """
    Record of a single mutation attempt.

    Attributes:
        tier: Tier used (1, 2, or 3)
        mutation_type: Type of mutation (e.g., "add_factor", "operator_mutation")
        success: Whether mutation succeeded
        performance_delta: Change in fitness/performance (can be negative)
        strategy_id: ID of strategy that was mutated
        timestamp: When mutation occurred
        metadata: Additional metadata about mutation
    """
    tier: int
    mutation_type: str
    success: bool
    performance_delta: float
    strategy_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TierStats:
    """
    Statistics for a single tier.

    Attributes:
        tier: Tier number (1, 2, or 3)
        count: Total mutations attempted
        successes: Number of successful mutations
        failures: Number of failed mutations
        success_rate: Success rate (0-1)
        avg_improvement: Average performance improvement
        best_improvement: Best performance improvement
        worst_improvement: Worst performance improvement
        mutation_type_distribution: Count of mutations by type
    """
    tier: int
    count: int = 0
    successes: int = 0
    failures: int = 0
    success_rate: float = 0.0
    avg_improvement: float = 0.0
    best_improvement: float = 0.0
    worst_improvement: float = 0.0
    mutation_type_distribution: Dict[str, int] = field(default_factory=dict)


class TierPerformanceTracker:
    """
    Track performance metrics per mutation tier.

    Maintains detailed statistics for each tier including:
    - Success/failure counts
    - Performance improvements (fitness deltas)
    - Mutation type distributions
    - Time series data for trend analysis

    Example:
        >>> tracker = TierPerformanceTracker()
        >>>
        >>> # Record successful Tier 2 mutation with improvement
        >>> tracker.record_mutation(
        ...     tier=2,
        ...     success=True,
        ...     performance_delta=0.05,
        ...     mutation_type="add_factor",
        ...     strategy_id="strategy_001"
        ... )
        >>>
        >>> # Get summary statistics
        >>> summary = tracker.get_tier_summary()
        >>> print(f"Tier 2 success rate: {summary['tier_2']['success_rate']:.2%}")
        >>> print(f"Tier 2 avg improvement: {summary['tier_2']['avg_improvement']:.4f}")
        >>>
        >>> # Export analysis to file
        >>> tracker.export_analysis("tier_performance.json")
    """

    def __init__(self):
        """Initialize tier performance tracker."""
        # Track all mutation records
        self._records: List[MutationRecord] = []

        # Track records per tier
        self._tier_records: Dict[int, List[MutationRecord]] = {
            1: [],
            2: [],
            3: []
        }

        # Track aggregated stats per tier
        self._tier_stats: Dict[int, TierStats] = {
            1: TierStats(tier=1),
            2: TierStats(tier=2),
            3: TierStats(tier=3)
        }

    def record_mutation(
        self,
        tier: int,
        success: bool,
        performance_delta: float,
        mutation_type: str,
        strategy_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record mutation result.

        Args:
            tier: Tier used (1, 2, or 3)
            success: Whether mutation succeeded
            performance_delta: Change in performance/fitness
                Positive = improvement, Negative = degradation
            mutation_type: Type of mutation applied
            strategy_id: ID of strategy that was mutated
            metadata: Additional metadata about mutation

        Raises:
            ValueError: If tier is not 1, 2, or 3

        Example:
            >>> tracker = TierPerformanceTracker()
            >>> tracker.record_mutation(
            ...     tier=2,
            ...     success=True,
            ...     performance_delta=0.05,
            ...     mutation_type="add_factor",
            ...     strategy_id="strat_001"
            ... )
        """
        if tier not in [1, 2, 3]:
            raise ValueError(f"Invalid tier: {tier}. Must be 1, 2, or 3")

        # Create record
        record = MutationRecord(
            tier=tier,
            mutation_type=mutation_type,
            success=success,
            performance_delta=performance_delta,
            strategy_id=strategy_id,
            metadata=metadata or {}
        )

        # Add to records
        self._records.append(record)
        self._tier_records[tier].append(record)

        # Update aggregated stats
        self._update_tier_stats(tier)

    def _update_tier_stats(self, tier: int) -> None:
        """
        Update aggregated statistics for a tier.

        Args:
            tier: Tier to update (1, 2, or 3)
        """
        records = self._tier_records[tier]
        if not records:
            return

        stats = self._tier_stats[tier]

        # Count totals
        stats.count = len(records)
        stats.successes = sum(1 for r in records if r.success)
        stats.failures = stats.count - stats.successes

        # Calculate success rate
        stats.success_rate = stats.successes / stats.count if stats.count > 0 else 0.0

        # Calculate performance improvements (only for successful mutations)
        successful_records = [r for r in records if r.success]
        if successful_records:
            deltas = [r.performance_delta for r in successful_records]
            stats.avg_improvement = np.mean(deltas)
            stats.best_improvement = np.max(deltas)
            stats.worst_improvement = np.min(deltas)
        else:
            stats.avg_improvement = 0.0
            stats.best_improvement = 0.0
            stats.worst_improvement = 0.0

        # Calculate mutation type distribution
        type_counts = defaultdict(int)
        for r in records:
            type_counts[r.mutation_type] += 1
        stats.mutation_type_distribution = dict(type_counts)

    def get_tier_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics per tier.

        Returns:
            Dictionary with tier statistics:
            {
                "tier_1": {
                    "count": 30,
                    "successes": 25,
                    "failures": 5,
                    "success_rate": 0.833,
                    "avg_improvement": 0.02,
                    "best_improvement": 0.08,
                    "worst_improvement": -0.01,
                    "mutation_types": {"yaml_config": 30}
                },
                "tier_2": {...},
                "tier_3": {...}
            }

        Example:
            >>> tracker = TierPerformanceTracker()
            >>> # ... record some mutations ...
            >>> summary = tracker.get_tier_summary()
            >>> print(f"Tier 2 success rate: {summary['tier_2']['success_rate']:.2%}")
        """
        summary = {}

        for tier in [1, 2, 3]:
            stats = self._tier_stats[tier]
            summary[f"tier_{tier}"] = {
                "count": stats.count,
                "successes": stats.successes,
                "failures": stats.failures,
                "success_rate": stats.success_rate,
                "avg_improvement": stats.avg_improvement,
                "best_improvement": stats.best_improvement,
                "worst_improvement": stats.worst_improvement,
                "mutation_types": stats.mutation_type_distribution
            }

        return summary

    def get_tier_comparison(self) -> Dict[str, Any]:
        """
        Get comparative analysis across tiers.

        Returns:
            Dictionary with tier comparison metrics:
            {
                "total_mutations": 100,
                "tier_distribution": {"1": 30, "2": 50, "3": 20},
                "tier_distribution_pct": {"1": 0.3, "2": 0.5, "3": 0.2},
                "success_rate_comparison": {"1": 0.85, "2": 0.70, "3": 0.40},
                "avg_improvement_comparison": {"1": 0.02, "2": 0.05, "3": 0.15},
                "best_tier_by_success_rate": 1,
                "best_tier_by_improvement": 3,
                "most_used_tier": 2
            }

        Example:
            >>> comparison = tracker.get_tier_comparison()
            >>> print(f"Most used tier: {comparison['most_used_tier']}")
            >>> print(f"Best tier by improvement: {comparison['best_tier_by_improvement']}")
        """
        total_mutations = len(self._records)

        # Tier distribution
        tier_distribution = {
            tier: len(records)
            for tier, records in self._tier_records.items()
        }

        tier_distribution_pct = {
            tier: count / total_mutations if total_mutations > 0 else 0.0
            for tier, count in tier_distribution.items()
        }

        # Success rate comparison
        success_rate_comparison = {
            tier: self._tier_stats[tier].success_rate
            for tier in [1, 2, 3]
        }

        # Average improvement comparison
        avg_improvement_comparison = {
            tier: self._tier_stats[tier].avg_improvement
            for tier in [1, 2, 3]
        }

        # Best tier by success rate
        best_tier_by_success_rate = max(
            [1, 2, 3],
            key=lambda t: self._tier_stats[t].success_rate
        )

        # Best tier by improvement
        best_tier_by_improvement = max(
            [1, 2, 3],
            key=lambda t: self._tier_stats[t].avg_improvement
        )

        # Most used tier
        most_used_tier = max(
            [1, 2, 3],
            key=lambda t: len(self._tier_records[t])
        )

        return {
            "total_mutations": total_mutations,
            "tier_distribution": tier_distribution,
            "tier_distribution_pct": tier_distribution_pct,
            "success_rate_comparison": success_rate_comparison,
            "avg_improvement_comparison": avg_improvement_comparison,
            "best_tier_by_success_rate": best_tier_by_success_rate,
            "best_tier_by_improvement": best_tier_by_improvement,
            "most_used_tier": most_used_tier
        }

    def get_mutation_type_analysis(self) -> Dict[str, Any]:
        """
        Get analysis of mutation types across tiers.

        Returns:
            Dictionary mapping mutation types to tier usage and success rates

        Example:
            >>> analysis = tracker.get_mutation_type_analysis()
            >>> print(analysis["add_factor"])
            # {"tier_1": 0, "tier_2": 20, "tier_3": 5, "success_rate": 0.8}
        """
        mutation_types = set()
        for records in self._tier_records.values():
            for record in records:
                mutation_types.add(record.mutation_type)

        analysis = {}
        for mutation_type in mutation_types:
            # Count per tier
            tier_counts = {}
            tier_successes = {}
            total_count = 0
            total_successes = 0

            for tier in [1, 2, 3]:
                records = [
                    r for r in self._tier_records[tier]
                    if r.mutation_type == mutation_type
                ]
                count = len(records)
                successes = sum(1 for r in records if r.success)

                tier_counts[f"tier_{tier}"] = count
                tier_successes[f"tier_{tier}_successes"] = successes

                total_count += count
                total_successes += successes

            # Overall success rate for this mutation type
            success_rate = total_successes / total_count if total_count > 0 else 0.0

            analysis[mutation_type] = {
                **tier_counts,
                **tier_successes,
                "total_count": total_count,
                "total_successes": total_successes,
                "success_rate": success_rate
            }

        return analysis

    def export_analysis(self, path: str) -> None:
        """
        Export detailed tier performance analysis to JSON file.

        Args:
            path: Path to export file

        Example:
            >>> tracker.export_analysis("tier_performance.json")
        """
        analysis = {
            "summary": self.get_tier_summary(),
            "comparison": self.get_tier_comparison(),
            "mutation_type_analysis": self.get_mutation_type_analysis(),
            "export_timestamp": datetime.now().isoformat(),
            "total_records": len(self._records)
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)

    def get_records(
        self,
        tier: Optional[int] = None,
        success: Optional[bool] = None,
        limit: Optional[int] = None
    ) -> List[MutationRecord]:
        """
        Get mutation records with optional filtering.

        Args:
            tier: Filter by tier (1, 2, or 3)
            success: Filter by success status
            limit: Maximum number of records to return

        Returns:
            List of matching mutation records

        Example:
            >>> # Get all successful Tier 2 mutations
            >>> records = tracker.get_records(tier=2, success=True)
            >>> print(f"Found {len(records)} successful Tier 2 mutations")
        """
        # Start with all records
        if tier is not None:
            records = self._tier_records.get(tier, [])
        else:
            records = self._records

        # Filter by success if specified
        if success is not None:
            records = [r for r in records if r.success == success]

        # Apply limit if specified
        if limit is not None:
            records = records[-limit:]  # Get most recent

        return records

    def reset_stats(self) -> None:
        """Reset all statistics and records."""
        self._records = []
        self._tier_records = {1: [], 2: [], 3: []}
        self._tier_stats = {
            1: TierStats(tier=1),
            2: TierStats(tier=2),
            3: TierStats(tier=3)
        }

    def get_recent_trends(self, window: int = 20) -> Dict[str, Any]:
        """
        Get recent trends in tier performance.

        Args:
            window: Number of recent mutations to analyze

        Returns:
            Dictionary with trend analysis

        Example:
            >>> trends = tracker.get_recent_trends(window=20)
            >>> print(f"Recent Tier 2 success rate: {trends['tier_2_success_rate']:.2%}")
        """
        recent_records = self._records[-window:] if len(self._records) > window else self._records

        if not recent_records:
            return {
                "window_size": 0,
                "tier_1_count": 0,
                "tier_2_count": 0,
                "tier_3_count": 0
            }

        # Count by tier
        tier_counts = {1: 0, 2: 0, 3: 0}
        tier_successes = {1: 0, 2: 0, 3: 0}

        for record in recent_records:
            tier_counts[record.tier] += 1
            if record.success:
                tier_successes[record.tier] += 1

        # Calculate success rates
        tier_success_rates = {}
        for tier in [1, 2, 3]:
            count = tier_counts[tier]
            if count > 0:
                tier_success_rates[f"tier_{tier}_success_rate"] = tier_successes[tier] / count
            else:
                tier_success_rates[f"tier_{tier}_success_rate"] = 0.0

        return {
            "window_size": len(recent_records),
            "tier_1_count": tier_counts[1],
            "tier_2_count": tier_counts[2],
            "tier_3_count": tier_counts[3],
            **tier_success_rates
        }
