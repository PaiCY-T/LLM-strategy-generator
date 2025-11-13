"""
Tier Selection Manager - Main orchestrator for adaptive tier selection.

Coordinates risk assessment, tier routing, and adaptive learning
to intelligently select mutation tiers based on context and history.

Architecture: Phase 2.0+ Factor Graph System
Task: D.4 - Adaptive Mutation Tier Selection
"""

from typing import Dict, Any, Optional
import pandas as pd

from .risk_assessor import RiskAssessor, RiskMetrics
from .tier_router import TierRouter, MutationPlan, MutationTier
from .adaptive_learner import AdaptiveLearner


class TierSelectionManager:
    """
    Main orchestrator for adaptive tier selection.

    Integrates three components for intelligent mutation tier selection:
    1. RiskAssessor: Evaluate strategy/market/mutation risk
    2. TierRouter: Route mutations to appropriate tiers
    3. AdaptiveLearner: Learn from history and adapt thresholds

    The manager provides the primary interface for tier selection and
    handles the coordination between components.

    Attributes:
        risk_assessor: RiskAssessor for risk calculation
        tier_router: TierRouter for tier selection
        adaptive_learner: AdaptiveLearner for threshold adaptation

    Example:
        >>> manager = TierSelectionManager()
        >>>
        >>> # Select tier for mutation
        >>> plan = manager.select_mutation_tier(
        ...     strategy=my_strategy,
        ...     market_data=recent_data,
        ...     mutation_intent="add_factor"
        ... )
        >>> print(f"Selected {plan.tier} with risk {plan.risk_score:.3f}")
        >>> print(plan.rationale)
        >>>
        >>> # After mutation completes
        >>> manager.record_mutation_result(
        ...     plan=plan,
        ...     success=True,
        ...     metrics={'fitness_delta': 0.05}
        ... )
        >>>
        >>> # Get recommendations
        >>> recommendations = manager.get_recommendations()
        >>> print(recommendations['recommended_tier'])
    """

    def __init__(
        self,
        strategy_complexity_weight: float = 0.4,
        market_risk_weight: float = 0.3,
        mutation_risk_weight: float = 0.3,
        tier1_threshold: float = 0.3,
        tier2_threshold: float = 0.7,
        learning_rate: float = 0.1,
        history_window: int = 100,
        min_samples: int = 20,
        enable_adaptation: bool = True,
        persistence_path: Optional[str] = None
    ):
        """
        Initialize tier selection manager.

        Args:
            strategy_complexity_weight: Weight for strategy risk (0-1)
            market_risk_weight: Weight for market risk (0-1)
            mutation_risk_weight: Weight for mutation history risk (0-1)
            tier1_threshold: Upper bound for Tier 1 selection [0.0-1.0]
            tier2_threshold: Upper bound for Tier 2 selection [0.0-1.0]
            learning_rate: Rate of threshold adjustment (0.0-1.0)
            history_window: Number of recent mutations to track
            min_samples: Minimum samples before adapting
            enable_adaptation: Enable automatic threshold adaptation
            persistence_path: Optional path to persist learning history

        Example:
            >>> # Conservative setup (prefer safe mutations)
            >>> manager = TierSelectionManager(
            ...     tier1_threshold=0.5,  # More Tier 1
            ...     tier2_threshold=0.8,  # Less Tier 3
            ...     enable_adaptation=True
            ... )
            >>>
            >>> # Aggressive setup (prefer advanced mutations)
            >>> manager = TierSelectionManager(
            ...     tier1_threshold=0.2,  # Less Tier 1
            ...     tier2_threshold=0.5,  # More Tier 3
            ...     enable_adaptation=True
            ... )
        """
        # Initialize components
        self.risk_assessor = RiskAssessor(
            strategy_complexity_weight=strategy_complexity_weight,
            market_risk_weight=market_risk_weight,
            mutation_risk_weight=mutation_risk_weight
        )

        self.tier_router = TierRouter(
            tier1_threshold=tier1_threshold,
            tier2_threshold=tier2_threshold,
            allow_override=True
        )

        self.adaptive_learner = AdaptiveLearner(
            history_window=history_window,
            learning_rate=learning_rate,
            min_samples=min_samples,
            persistence_path=persistence_path
        )

        self.enable_adaptation = enable_adaptation

        # Track current thresholds for adaptation
        self._current_tier1_threshold = tier1_threshold
        self._current_tier2_threshold = tier2_threshold

    def select_mutation_tier(
        self,
        strategy: Any,
        market_data: Optional[pd.DataFrame] = None,
        mutation_intent: str = "generic",
        override_tier: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> MutationPlan:
        """
        Select mutation tier and create mutation plan.

        Main entry point for tier selection. Coordinates:
        1. Risk assessment (strategy + market + history)
        2. Tier routing (select appropriate tier)
        3. Plan creation (complete mutation specification)

        Args:
            strategy: Strategy object to mutate
            market_data: Optional recent market data for risk assessment
            mutation_intent: High-level mutation intent
                (e.g., "add_factor", "adjust_parameters", "modify_logic")
            override_tier: Optional manual tier override (1, 2, or 3)
            config: Optional additional configuration

        Returns:
            Complete mutation plan with tier, type, config, and rationale

        Example:
            >>> plan = manager.select_mutation_tier(
            ...     strategy=my_strategy,
            ...     market_data=recent_data,
            ...     mutation_intent="add_factor"
            ... )
            >>> print(f"Tier: {plan.tier.value}")
            >>> print(f"Risk: {plan.risk_score:.3f}")
            >>> print(f"Type: {plan.mutation_type}")
            >>> print(f"Rationale: {plan.rationale}")
        """
        # Get historical stats for risk assessment
        historical_stats = self._get_historical_stats()

        # Assess overall risk
        risk_metrics = self.risk_assessor.assess_overall_risk(
            strategy=strategy,
            market_data=market_data,
            mutation_type=mutation_intent,
            historical_stats=historical_stats
        )

        # Get tier statistics for routing
        tier_stats = self.adaptive_learner.get_tier_stats()

        # Route mutation to appropriate tier
        plan = self.tier_router.route_mutation(
            strategy=strategy,
            mutation_intent=mutation_intent,
            risk_score=risk_metrics.overall_risk,
            tier_stats=tier_stats,
            override_tier=override_tier,
            config=config
        )

        # Add risk metrics to plan config
        plan.config['risk_metrics'] = {
            'strategy_risk': risk_metrics.strategy_risk,
            'market_risk': risk_metrics.market_risk,
            'mutation_risk': risk_metrics.mutation_risk,
            'overall_risk': risk_metrics.overall_risk,
            'details': risk_metrics.details
        }

        return plan

    def record_mutation_result(
        self,
        plan: MutationPlan,
        success: bool,
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record mutation result and update adaptive learning.

        Args:
            plan: The mutation plan that was executed
            success: Whether mutation succeeded
            metrics: Optional metrics (fitness_delta, etc.)

        Example:
            >>> plan = manager.select_mutation_tier(...)
            >>> # ... execute mutation ...
            >>> manager.record_mutation_result(
            ...     plan=plan,
            ...     success=True,
            ...     metrics={'fitness_delta': 0.05, 'strategy_id': 'strat_123'}
            ... )
        """
        if metrics is None:
            metrics = {}

        # Add plan info to metrics
        metrics['mutation_type'] = plan.mutation_type
        metrics['strategy_id'] = plan.config.get('strategy_id', 'unknown')

        # Update learner
        self.adaptive_learner.update_tier_stats(
            tier=plan.tier.value,
            success=success,
            metrics=metrics
        )

        # Adapt thresholds if enabled
        if self.enable_adaptation:
            self._maybe_adapt_thresholds()

    def get_recommendations(self) -> Dict[str, Any]:
        """
        Get comprehensive tier selection recommendations.

        Returns:
            Dictionary with recommendations, stats, and insights

        Example:
            >>> recommendations = manager.get_recommendations()
            >>> print(recommendations['recommended_tier'])
            >>> print(recommendations['confidence'])
            >>> print(recommendations['insights'])
        """
        recommendations = self.adaptive_learner.get_tier_recommendations()

        # Add current thresholds
        recommendations['current_thresholds'] = {
            'tier1_threshold': self._current_tier1_threshold,
            'tier2_threshold': self._current_tier2_threshold
        }

        # Add tier distribution
        recommendations['tier_distribution'] = self.tier_router.get_tier_distribution(
            tier_stats=self.adaptive_learner.get_tier_stats()
        )

        return recommendations

    def get_tier_stats(self) -> Dict[str, Any]:
        """
        Get current tier statistics.

        Returns:
            Dictionary with detailed tier statistics
        """
        return self.adaptive_learner.get_tier_stats()

    def adjust_thresholds_manually(
        self,
        tier1_threshold: Optional[float] = None,
        tier2_threshold: Optional[float] = None
    ) -> None:
        """
        Manually adjust tier thresholds.

        Args:
            tier1_threshold: New Tier 1 threshold [0.0-1.0]
            tier2_threshold: New Tier 2 threshold [0.0-1.0]

        Raises:
            ValueError: If thresholds are invalid
        """
        if tier1_threshold is not None:
            if not 0.0 <= tier1_threshold <= 1.0:
                raise ValueError(f"Invalid tier1_threshold: {tier1_threshold}")
            self._current_tier1_threshold = tier1_threshold

        if tier2_threshold is not None:
            if not 0.0 <= tier2_threshold <= 1.0:
                raise ValueError(f"Invalid tier2_threshold: {tier2_threshold}")
            self._current_tier2_threshold = tier2_threshold

        # Validate relationship
        if self._current_tier1_threshold >= self._current_tier2_threshold:
            raise ValueError(
                f"tier1_threshold ({self._current_tier1_threshold}) must be < "
                f"tier2_threshold ({self._current_tier2_threshold})"
            )

        # Update router
        self.tier_router.tier1_threshold = self._current_tier1_threshold
        self.tier_router.tier2_threshold = self._current_tier2_threshold

    def reset_learning(self) -> None:
        """Reset all learning history (useful for testing or fresh start)."""
        self.adaptive_learner.reset_stats()

    def export_state(self) -> Dict[str, Any]:
        """
        Export complete manager state.

        Returns:
            Dictionary with all state for persistence/analysis
        """
        return {
            'thresholds': {
                'tier1_threshold': self._current_tier1_threshold,
                'tier2_threshold': self._current_tier2_threshold
            },
            'tier_stats': self.get_tier_stats(),
            'recommendations': self.get_recommendations(),
            'configuration': {
                'enable_adaptation': self.enable_adaptation,
                'learning_rate': self.adaptive_learner.learning_rate,
                'history_window': self.adaptive_learner.history_window,
                'min_samples': self.adaptive_learner.min_samples
            }
        }

    def _get_historical_stats(self) -> Dict[str, Any]:
        """Get historical stats in format needed by risk assessor."""
        tier_stats = self.adaptive_learner.get_tier_stats()

        historical_stats = {}
        for tier_name, stats in tier_stats.items():
            historical_stats[tier_name] = {
                'attempts': stats['attempts'],
                'successes': stats['successes']
            }

        return historical_stats

    def _maybe_adapt_thresholds(self) -> None:
        """
        Adapt thresholds based on learning if conditions are met.

        Called automatically after recording mutation results
        if adaptation is enabled.
        """
        # Get adjustment recommendations
        adjustment = self.adaptive_learner.adjust_thresholds(
            current_tier1_threshold=self._current_tier1_threshold,
            current_tier2_threshold=self._current_tier2_threshold
        )

        if adjustment.get('adjusted', False):
            # Update thresholds
            self._current_tier1_threshold = adjustment['tier1_threshold']
            self._current_tier2_threshold = adjustment['tier2_threshold']

            # Update router
            self.tier_router.tier1_threshold = self._current_tier1_threshold
            self.tier_router.tier2_threshold = self._current_tier2_threshold
