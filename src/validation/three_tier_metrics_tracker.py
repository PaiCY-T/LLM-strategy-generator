"""
Three-Tier Metrics Tracker - Comprehensive metrics tracking for three-tier validation.

Tracks tier usage, performance progression, effectiveness, and breakthrough detection
during multi-generation evolution runs. Provides comprehensive analytics and export
capabilities for validation reporting.

Architecture: Structural Mutation Phase 2 - Phase D.6
Task: D.6 - 50-Generation Three-Tier Validation
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import pandas as pd
import numpy as np


@dataclass
class GenerationMetrics:
    """Metrics for a single generation."""

    generation: int
    timestamp: str

    # Performance metrics
    best_sharpe: float
    avg_sharpe: float
    median_sharpe: float
    worst_sharpe: float

    # Additional metrics
    best_calmar: float = 0.0
    avg_max_drawdown: float = 0.0
    avg_win_rate: float = 0.0

    # Tier usage
    tier1_count: int = 0
    tier2_count: int = 0
    tier3_count: int = 0
    total_mutations: int = 0

    # Tier success rates
    tier1_success_rate: float = 0.0
    tier2_success_rate: float = 0.0
    tier3_success_rate: float = 0.0

    # Population diversity
    diversity_score: float = 0.0
    unique_strategies: int = 0

    # Best strategy info
    best_strategy_id: str = ""
    best_strategy_tier: str = ""


@dataclass
class TierEffectiveness:
    """Effectiveness metrics for a mutation tier."""

    tier_id: int
    tier_name: str

    # Usage statistics
    usage_count: int = 0
    usage_percentage: float = 0.0

    # Success metrics
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0

    # Performance impact
    avg_improvement: float = 0.0
    median_improvement: float = 0.0
    best_improvement: float = 0.0
    worst_improvement: float = 0.0

    # Contribution to best strategies
    contribution_to_best: float = 0.0
    best_strategies_count: int = 0

    # Timing
    avg_execution_time: float = 0.0


@dataclass
class BreakthroughStrategy:
    """Information about a breakthrough strategy."""

    generation: int
    strategy_id: str
    sharpe_ratio: float
    calmar_ratio: float
    max_drawdown: float
    win_rate: float
    tier_used: str
    parent_sharpe: float
    improvement: float


class ThreeTierMetricsTracker:
    """
    Track comprehensive metrics for three-tier validation.

    Captures generation-by-generation metrics, tier usage statistics,
    performance progression, and breakthrough detection. Provides
    analytics and export capabilities for validation reporting.

    Example:
        >>> tracker = ThreeTierMetricsTracker()
        >>>
        >>> # Record generation metrics
        >>> tracker.record_generation(
        ...     generation=1,
        ...     population=[strategy1, strategy2, ...],
        ...     tier_stats={"tier1": 3, "tier2": 5, "tier3": 2},
        ...     fitness_scores={"strategy1": 1.8, ...}
        ... )
        >>>
        >>> # Get analytics
        >>> distribution = tracker.get_tier_distribution()
        >>> effectiveness = tracker.get_tier_effectiveness()
        >>> breakthroughs = tracker.detect_breakthroughs(threshold=2.5)
        >>>
        >>> # Export report
        >>> tracker.export_report("validation_results/metrics.json")
    """

    def __init__(self):
        """Initialize metrics tracker."""
        self.generation_metrics: List[GenerationMetrics] = []
        self.tier_stats: Dict[int, Dict[str, Any]] = {1: {}, 2: {}, 3: {}}
        self.mutation_history: List[Dict[str, Any]] = []
        self.breakthrough_strategies: List[BreakthroughStrategy] = []

        # Performance tracking
        self.best_sharpe_overall: float = -np.inf
        self.best_strategy_id: str = ""

        # Timing
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None

    def record_generation(
        self,
        generation: int,
        population: List[Any],
        tier_stats: Dict[str, int],
        fitness_scores: Dict[str, float],
        tier_success_rates: Optional[Dict[str, float]] = None,
        diversity_score: Optional[float] = None,
        mutation_results: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Record metrics for a generation.

        Args:
            generation: Generation number (1-indexed)
            population: List of strategy objects
            tier_stats: Tier usage counts {"tier1": N, "tier2": N, "tier3": N}
            fitness_scores: Strategy ID to fitness score mapping
            tier_success_rates: Success rates per tier (optional)
            diversity_score: Population diversity score (optional)
            mutation_results: List of mutation result dicts (optional)
        """
        # Extract fitness values
        fitness_values = list(fitness_scores.values())
        if not fitness_values:
            fitness_values = [0.0]

        # Calculate performance metrics
        best_sharpe = max(fitness_values)
        avg_sharpe = np.mean(fitness_values)
        median_sharpe = np.median(fitness_values)
        worst_sharpe = min(fitness_values)

        # Find best strategy
        best_strategy_id = max(fitness_scores.items(), key=lambda x: x[1])[0]

        # Tier usage
        tier1_count = tier_stats.get("tier1", 0)
        tier2_count = tier_stats.get("tier2", 0)
        tier3_count = tier_stats.get("tier3", 0)
        total_mutations = tier1_count + tier2_count + tier3_count

        # Tier success rates
        if tier_success_rates is None:
            tier_success_rates = {}
        tier1_success = tier_success_rates.get("tier1", 0.0)
        tier2_success = tier_success_rates.get("tier2", 0.0)
        tier3_success = tier_success_rates.get("tier3", 0.0)

        # Diversity
        if diversity_score is None:
            diversity_score = 0.0
        unique_strategies = len(set(str(s) for s in population))

        # Create generation metrics
        metrics = GenerationMetrics(
            generation=generation,
            timestamp=datetime.now().isoformat(),
            best_sharpe=best_sharpe,
            avg_sharpe=avg_sharpe,
            median_sharpe=median_sharpe,
            worst_sharpe=worst_sharpe,
            tier1_count=tier1_count,
            tier2_count=tier2_count,
            tier3_count=tier3_count,
            total_mutations=total_mutations,
            tier1_success_rate=tier1_success,
            tier2_success_rate=tier2_success,
            tier3_success_rate=tier3_success,
            diversity_score=diversity_score,
            unique_strategies=unique_strategies,
            best_strategy_id=best_strategy_id,
            best_strategy_tier=""
        )

        self.generation_metrics.append(metrics)

        # Track overall best
        if best_sharpe > self.best_sharpe_overall:
            self.best_sharpe_overall = best_sharpe
            self.best_strategy_id = best_strategy_id

        # Store mutation results
        if mutation_results:
            for result in mutation_results:
                result["generation"] = generation
                self.mutation_history.append(result)

    def get_tier_distribution(self) -> Dict[str, float]:
        """
        Get tier usage distribution across all generations.

        Returns:
            Dictionary with tier usage percentages:
            {
                "tier1": 0.30,
                "tier2": 0.50,
                "tier3": 0.20,
                "total_mutations": 1000
            }
        """
        if not self.generation_metrics:
            return {
                "tier1": 0.0,
                "tier2": 0.0,
                "tier3": 0.0,
                "total_mutations": 0
            }

        total_tier1 = sum(m.tier1_count for m in self.generation_metrics)
        total_tier2 = sum(m.tier2_count for m in self.generation_metrics)
        total_tier3 = sum(m.tier3_count for m in self.generation_metrics)
        total_mutations = total_tier1 + total_tier2 + total_tier3

        if total_mutations == 0:
            return {
                "tier1": 0.0,
                "tier2": 0.0,
                "tier3": 0.0,
                "total_mutations": 0
            }

        return {
            "tier1": total_tier1 / total_mutations,
            "tier2": total_tier2 / total_mutations,
            "tier3": total_tier3 / total_mutations,
            "total_mutations": total_mutations
        }

    def get_performance_progression(self) -> pd.DataFrame:
        """
        Get performance progression over generations.

        Returns:
            DataFrame with columns:
            - generation
            - best_sharpe
            - avg_sharpe
            - median_sharpe
            - improvement (from previous generation)
        """
        if not self.generation_metrics:
            return pd.DataFrame()

        data = []
        prev_best = None

        for metrics in self.generation_metrics:
            improvement = 0.0
            if prev_best is not None:
                improvement = metrics.best_sharpe - prev_best

            data.append({
                "generation": metrics.generation,
                "best_sharpe": metrics.best_sharpe,
                "avg_sharpe": metrics.avg_sharpe,
                "median_sharpe": metrics.median_sharpe,
                "improvement": improvement,
                "diversity": metrics.diversity_score,
                "unique_strategies": metrics.unique_strategies
            })

            prev_best = metrics.best_sharpe

        return pd.DataFrame(data)

    def get_tier_effectiveness(self) -> Dict[str, TierEffectiveness]:
        """
        Calculate effectiveness metrics per tier.

        Returns:
            Dictionary mapping tier ID to TierEffectiveness:
            {
                "tier_1": TierEffectiveness(...),
                "tier_2": TierEffectiveness(...),
                "tier_3": TierEffectiveness(...)
            }
        """
        if not self.generation_metrics:
            return {}

        # Calculate usage and success rates
        total_tier1 = sum(m.tier1_count for m in self.generation_metrics)
        total_tier2 = sum(m.tier2_count for m in self.generation_metrics)
        total_tier3 = sum(m.tier3_count for m in self.generation_metrics)
        total_mutations = total_tier1 + total_tier2 + total_tier3

        # Calculate average success rates
        tier1_success_rates = [m.tier1_success_rate for m in self.generation_metrics if m.tier1_count > 0]
        tier2_success_rates = [m.tier2_success_rate for m in self.generation_metrics if m.tier2_count > 0]
        tier3_success_rates = [m.tier3_success_rate for m in self.generation_metrics if m.tier3_count > 0]

        avg_tier1_success = np.mean(tier1_success_rates) if tier1_success_rates else 0.0
        avg_tier2_success = np.mean(tier2_success_rates) if tier2_success_rates else 0.0
        avg_tier3_success = np.mean(tier3_success_rates) if tier3_success_rates else 0.0

        # Calculate improvements from mutation history
        tier_improvements = {1: [], 2: [], 3: []}
        for mutation in self.mutation_history:
            tier = mutation.get("tier", 0)
            improvement = mutation.get("improvement", 0.0)
            if tier in tier_improvements:
                tier_improvements[tier].append(improvement)

        # Build effectiveness objects
        effectiveness = {}

        for tier_id, tier_name, count, success_rate, improvements in [
            (1, "YAML Configuration", total_tier1, avg_tier1_success, tier_improvements[1]),
            (2, "Factor Operations", total_tier2, avg_tier2_success, tier_improvements[2]),
            (3, "AST Mutations", total_tier3, avg_tier3_success, tier_improvements[3])
        ]:
            usage_pct = count / total_mutations if total_mutations > 0 else 0.0
            success_count = int(count * success_rate)
            failure_count = count - success_count

            if improvements:
                avg_improvement = np.mean(improvements)
                median_improvement = np.median(improvements)
                best_improvement = max(improvements)
                worst_improvement = min(improvements)
            else:
                avg_improvement = 0.0
                median_improvement = 0.0
                best_improvement = 0.0
                worst_improvement = 0.0

            effectiveness[f"tier_{tier_id}"] = TierEffectiveness(
                tier_id=tier_id,
                tier_name=tier_name,
                usage_count=count,
                usage_percentage=usage_pct,
                success_count=success_count,
                failure_count=failure_count,
                success_rate=success_rate,
                avg_improvement=avg_improvement,
                median_improvement=median_improvement,
                best_improvement=best_improvement,
                worst_improvement=worst_improvement,
                contribution_to_best=0.0,  # Calculated separately
                best_strategies_count=0,
                avg_execution_time=0.0
            )

        return effectiveness

    def detect_breakthroughs(self, threshold: float = 2.5) -> List[BreakthroughStrategy]:
        """
        Detect breakthrough strategies (Sharpe > threshold).

        Args:
            threshold: Minimum Sharpe ratio to consider breakthrough

        Returns:
            List of BreakthroughStrategy objects
        """
        breakthroughs = []

        for metrics in self.generation_metrics:
            if metrics.best_sharpe >= threshold:
                # Check if this is a new breakthrough
                is_new = True
                for existing in breakthroughs:
                    if existing.strategy_id == metrics.best_strategy_id:
                        is_new = False
                        break

                if is_new:
                    # Calculate improvement from parent
                    parent_sharpe = 0.0
                    if metrics.generation > 1:
                        parent_sharpe = self.generation_metrics[metrics.generation - 2].best_sharpe

                    breakthrough = BreakthroughStrategy(
                        generation=metrics.generation,
                        strategy_id=metrics.best_strategy_id,
                        sharpe_ratio=metrics.best_sharpe,
                        calmar_ratio=metrics.best_calmar,
                        max_drawdown=0.0,  # Would need to track separately
                        win_rate=0.0,
                        tier_used=metrics.best_strategy_tier,
                        parent_sharpe=parent_sharpe,
                        improvement=metrics.best_sharpe - parent_sharpe
                    )
                    breakthroughs.append(breakthrough)

        return breakthroughs

    def export_report(self, path: str):
        """
        Export comprehensive validation report to JSON.

        Args:
            path: Output file path
        """
        report = {
            "metadata": {
                "start_time": self.start_time,
                "end_time": self.end_time,
                "total_generations": len(self.generation_metrics),
                "best_sharpe_overall": self.best_sharpe_overall,
                "best_strategy_id": self.best_strategy_id
            },
            "tier_distribution": self.get_tier_distribution(),
            "tier_effectiveness": {
                tier_key: asdict(eff)
                for tier_key, eff in self.get_tier_effectiveness().items()
            },
            "generation_metrics": [
                asdict(metrics) for metrics in self.generation_metrics
            ],
            "breakthroughs": [
                asdict(b) for b in self.detect_breakthroughs()
            ],
            "mutation_history": self.mutation_history
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics for validation.

        Returns:
            Dictionary with key metrics:
            - performance_summary
            - tier_summary
            - stability_summary
        """
        if not self.generation_metrics:
            return {}

        # Performance summary
        initial_best = self.generation_metrics[0].best_sharpe
        final_best = self.generation_metrics[-1].best_sharpe
        improvement = final_best - initial_best
        improvement_pct = (improvement / abs(initial_best)) * 100 if initial_best != 0 else 0.0

        avg_sharpe = np.mean([m.best_sharpe for m in self.generation_metrics])

        # Tier summary
        tier_dist = self.get_tier_distribution()

        # Stability summary
        completion_rate = len(self.generation_metrics) / max(
            m.generation for m in self.generation_metrics
        ) if self.generation_metrics else 0.0

        avg_diversity = np.mean([m.diversity_score for m in self.generation_metrics])

        return {
            "performance_summary": {
                "initial_best_sharpe": initial_best,
                "final_best_sharpe": final_best,
                "improvement": improvement,
                "improvement_percentage": improvement_pct,
                "avg_best_sharpe": avg_sharpe,
                "overall_best_sharpe": self.best_sharpe_overall
            },
            "tier_summary": {
                "tier1_usage": tier_dist["tier1"],
                "tier2_usage": tier_dist["tier2"],
                "tier3_usage": tier_dist["tier3"],
                "total_mutations": tier_dist["total_mutations"]
            },
            "stability_summary": {
                "completion_rate": completion_rate,
                "avg_diversity": avg_diversity,
                "total_generations": len(self.generation_metrics)
            }
        }
