"""
Tier Router - Route mutations to appropriate tiers based on risk.

Routes mutations across three tiers based on risk assessment:
- Tier 1 (Safe): YAML configuration mutations
- Tier 2 (Domain): Factor-level mutations
- Tier 3 (Advanced): AST code mutations

Architecture: Phase 2.0+ Factor Graph System
Task: D.4 - Adaptive Mutation Tier Selection
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random


class MutationTier(Enum):
    """Mutation tier levels."""
    TIER1_YAML = 1      # Safe: YAML configuration mutations
    TIER2_FACTOR = 2    # Domain: Factor-level mutations (add/remove/replace/mutate)
    TIER3_AST = 3       # Advanced: AST code mutations


@dataclass
class MutationPlan:
    """
    Plan for executing a mutation.

    Attributes:
        tier: Selected mutation tier (1, 2, or 3)
        mutation_type: Type of mutation to apply
        config: Configuration for the mutation
        risk_score: Risk score that led to tier selection
        rationale: Human-readable explanation of tier selection
    """
    tier: MutationTier
    mutation_type: str
    config: Dict[str, Any]
    risk_score: float
    rationale: str


class TierRouter:
    """
    Route mutations to appropriate tiers based on risk assessment.

    Implements adaptive tier selection logic:
    - Low risk (0.0-0.3) → Tier 1 (YAML safe config)
    - Medium risk (0.3-0.7) → Tier 2 (Domain mutations)
    - High risk (0.7-1.0) → Tier 3 (AST mutations)

    The router supports:
    - Configurable tier thresholds
    - Manual tier override for experimentation
    - Mutation type mapping to tiers
    - Rationale generation for explainability

    Attributes:
        tier1_threshold: Upper bound for Tier 1 selection (default: 0.3)
        tier2_threshold: Upper bound for Tier 2 selection (default: 0.7)
        allow_override: Enable manual tier override (default: True)

    Example:
        >>> router = TierRouter()
        >>> plan = router.route_mutation(
        ...     strategy=my_strategy,
        ...     mutation_intent="add_factor",
        ...     risk_score=0.5
        ... )
        >>> assert plan.tier == MutationTier.TIER2_FACTOR
        >>> assert "medium risk" in plan.rationale.lower()
    """

    def __init__(
        self,
        tier1_threshold: float = 0.3,
        tier2_threshold: float = 0.7,
        allow_override: bool = True
    ):
        """
        Initialize tier router with configurable thresholds.

        Args:
            tier1_threshold: Maximum risk score for Tier 1 selection [0.0-1.0]
            tier2_threshold: Maximum risk score for Tier 2 selection [0.0-1.0]
            allow_override: Allow manual tier override

        Raises:
            ValueError: If thresholds are invalid
        """
        if not 0.0 <= tier1_threshold <= tier2_threshold <= 1.0:
            raise ValueError(
                f"Invalid thresholds: tier1={tier1_threshold}, tier2={tier2_threshold}. "
                "Must satisfy: 0.0 <= tier1 <= tier2 <= 1.0"
            )

        self.tier1_threshold = tier1_threshold
        self.tier2_threshold = tier2_threshold
        self.allow_override = allow_override

    def select_tier(
        self,
        risk_score: float,
        tier_stats: Optional[Dict[str, Any]] = None,
        override_tier: Optional[int] = None
    ) -> MutationTier:
        """
        Select mutation tier based on risk score.

        Tier selection logic:
        - risk_score < tier1_threshold → Tier 1 (YAML)
        - tier1_threshold <= risk_score < tier2_threshold → Tier 2 (Factor)
        - risk_score >= tier2_threshold → Tier 3 (AST)

        Args:
            risk_score: Overall risk score [0.0-1.0]
            tier_stats: Optional statistics for tier performance adjustment
            override_tier: Optional manual tier selection (1, 2, or 3)

        Returns:
            Selected mutation tier

        Raises:
            ValueError: If override_tier is invalid

        Example:
            >>> router = TierRouter(tier1_threshold=0.3, tier2_threshold=0.7)
            >>> tier = router.select_tier(0.2)
            >>> assert tier == MutationTier.TIER1_YAML
            >>>
            >>> tier = router.select_tier(0.5)
            >>> assert tier == MutationTier.TIER2_FACTOR
            >>>
            >>> tier = router.select_tier(0.8)
            >>> assert tier == MutationTier.TIER3_AST
        """
        # Handle manual override
        if override_tier is not None:
            if not self.allow_override:
                raise ValueError("Tier override is disabled")
            if override_tier not in [1, 2, 3]:
                raise ValueError(f"Invalid tier override: {override_tier}. Must be 1, 2, or 3")
            return MutationTier(override_tier)

        # Clamp risk score
        risk_score = max(0.0, min(1.0, risk_score))

        # Select tier based on thresholds
        if risk_score < self.tier1_threshold:
            return MutationTier.TIER1_YAML
        elif risk_score < self.tier2_threshold:
            return MutationTier.TIER2_FACTOR
        else:
            return MutationTier.TIER3_AST

    def route_mutation(
        self,
        strategy: Any,
        mutation_intent: str,
        risk_score: float,
        tier_stats: Optional[Dict[str, Any]] = None,
        override_tier: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> MutationPlan:
        """
        Route mutation to appropriate tier and create mutation plan.

        Combines tier selection with mutation type mapping and
        configuration to create a complete mutation plan.

        Args:
            strategy: Strategy object to mutate
            mutation_intent: High-level mutation intent
                (e.g., "add_factor", "adjust_parameters", "modify_logic")
            risk_score: Overall risk score [0.0-1.0]
            tier_stats: Optional statistics for tier performance
            override_tier: Optional manual tier selection
            config: Optional mutation configuration

        Returns:
            Complete mutation plan with tier, type, config, and rationale

        Example:
            >>> plan = router.route_mutation(
            ...     strategy=my_strategy,
            ...     mutation_intent="add_factor",
            ...     risk_score=0.2
            ... )
            >>> assert plan.tier == MutationTier.TIER1_YAML
            >>> assert plan.mutation_type in ["yaml_add_factor", "yaml_compose"]
        """
        # Select tier
        tier = self.select_tier(risk_score, tier_stats, override_tier)

        # Map mutation intent to tier-specific mutation type
        mutation_type = self._map_mutation_to_tier(mutation_intent, tier)

        # Build configuration
        if config is None:
            config = {}

        # Add strategy info to config
        config['strategy_id'] = strategy.id if hasattr(strategy, 'id') else 'unknown'
        config['tier'] = tier.value

        # Generate rationale
        rationale = self._generate_rationale(
            tier=tier,
            risk_score=risk_score,
            mutation_intent=mutation_intent,
            override=override_tier is not None
        )

        return MutationPlan(
            tier=tier,
            mutation_type=mutation_type,
            config=config,
            risk_score=risk_score,
            rationale=rationale
        )

    def adjust_thresholds(
        self,
        tier_stats: Dict[str, Any],
        adjustment_rate: float = 0.05
    ) -> Tuple[float, float]:
        """
        Adjust tier thresholds based on historical performance.

        If a tier has very high success rate, expand its range.
        If a tier has low success rate, shrink its range.

        Args:
            tier_stats: Statistics per tier with success rates
                Format: {
                    'tier1': {'success_rate': float},
                    'tier2': {'success_rate': float},
                    'tier3': {'success_rate': float}
                }
            adjustment_rate: Rate of threshold adjustment (default: 0.05)

        Returns:
            Tuple of (new_tier1_threshold, new_tier2_threshold)

        Example:
            >>> stats = {
            ...     'tier1': {'success_rate': 0.8},  # High success
            ...     'tier2': {'success_rate': 0.6},  # Medium success
            ...     'tier3': {'success_rate': 0.3}   # Low success
            ... }
            >>> new_t1, new_t2 = router.adjust_thresholds(stats)
            >>> # Tier 1 threshold increases (more risk tolerated)
            >>> assert new_t1 > router.tier1_threshold
        """
        if not tier_stats:
            return self.tier1_threshold, self.tier2_threshold

        # Extract success rates
        tier1_success = tier_stats.get('tier1', {}).get('success_rate', 0.5)
        tier2_success = tier_stats.get('tier2', {}).get('success_rate', 0.5)
        tier3_success = tier_stats.get('tier3', {}).get('success_rate', 0.5)

        # Adjust tier1 threshold based on Tier 1 performance
        # High success → increase threshold (use Tier 1 more)
        # Low success → decrease threshold (use Tier 1 less)
        tier1_adjustment = (tier1_success - 0.5) * adjustment_rate
        new_tier1 = max(0.1, min(0.5, self.tier1_threshold + tier1_adjustment))

        # Adjust tier2 threshold based on Tier 2 performance
        tier2_adjustment = (tier2_success - 0.5) * adjustment_rate
        new_tier2 = max(new_tier1 + 0.1, min(0.9, self.tier2_threshold + tier2_adjustment))

        return new_tier1, new_tier2

    def _map_mutation_to_tier(self, mutation_intent: str, tier: MutationTier) -> str:
        """
        Map high-level mutation intent to tier-specific mutation type.

        Args:
            mutation_intent: High-level intent (e.g., "add_factor")
            tier: Selected tier

        Returns:
            Tier-specific mutation type
        """
        # Mapping of intents to tier-specific operations
        tier_mappings = {
            MutationTier.TIER1_YAML: {
                'add_factor': 'yaml_add_factor',
                'remove_factor': 'yaml_remove_factor',
                'replace_factor': 'yaml_replace_factor',
                'adjust_parameters': 'yaml_adjust_parameters',
                'modify_logic': 'yaml_recompose',
            },
            MutationTier.TIER2_FACTOR: {
                'add_factor': 'factor_add',
                'remove_factor': 'factor_remove',
                'replace_factor': 'factor_replace',
                'adjust_parameters': 'factor_mutate_parameters',
                'modify_logic': 'factor_replace',
            },
            MutationTier.TIER3_AST: {
                'add_factor': 'ast_inject_factor',
                'remove_factor': 'ast_prune_factor',
                'replace_factor': 'ast_replace_logic',
                'adjust_parameters': 'ast_mutate_thresholds',
                'modify_logic': 'ast_mutate_logic',
            }
        }

        mapping = tier_mappings.get(tier, {})
        mutation_type = mapping.get(mutation_intent, f"tier{tier.value}_{mutation_intent}")

        return mutation_type

    def _generate_rationale(
        self,
        tier: MutationTier,
        risk_score: float,
        mutation_intent: str,
        override: bool
    ) -> str:
        """
        Generate human-readable rationale for tier selection.

        Args:
            tier: Selected tier
            risk_score: Risk score used for selection
            mutation_intent: Mutation intent
            override: Whether selection was manual override

        Returns:
            Rationale string
        """
        if override:
            return f"Tier {tier.value} selected via manual override for {mutation_intent}"

        risk_level = "low" if risk_score < 0.3 else "medium" if risk_score < 0.7 else "high"

        rationale_templates = {
            MutationTier.TIER1_YAML: (
                f"Selected Tier 1 (YAML) for {mutation_intent}: "
                f"{risk_level} risk (score={risk_score:.3f}). "
                "Using safe configuration mutations to minimize disruption."
            ),
            MutationTier.TIER2_FACTOR: (
                f"Selected Tier 2 (Factor) for {mutation_intent}: "
                f"{risk_level} risk (score={risk_score:.3f}). "
                "Using domain-specific factor operations for controlled evolution."
            ),
            MutationTier.TIER3_AST: (
                f"Selected Tier 3 (AST) for {mutation_intent}: "
                f"{risk_level} risk (score={risk_score:.3f}). "
                "Using advanced AST mutations for structural innovation."
            )
        }

        return rationale_templates.get(tier, f"Selected Tier {tier.value} for {mutation_intent}")

    def get_tier_distribution(
        self,
        num_samples: int = 1000,
        tier_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Calculate expected tier distribution for given thresholds.

        Useful for understanding tier usage patterns and validating
        threshold settings.

        Args:
            num_samples: Number of random risk scores to sample
            tier_stats: Optional tier statistics for adjustment

        Returns:
            Dictionary with tier probabilities

        Example:
            >>> router = TierRouter(tier1_threshold=0.3, tier2_threshold=0.7)
            >>> dist = router.get_tier_distribution()
            >>> assert abs(dist['tier1'] - 0.30) < 0.05  # ~30% Tier 1
            >>> assert abs(dist['tier2'] - 0.40) < 0.05  # ~40% Tier 2
            >>> assert abs(dist['tier3'] - 0.30) < 0.05  # ~30% Tier 3
        """
        tier_counts = {tier: 0 for tier in MutationTier}

        for _ in range(num_samples):
            risk_score = random.random()
            tier = self.select_tier(risk_score, tier_stats)
            tier_counts[tier] += 1

        # Calculate probabilities
        tier_probs = {
            f"tier{tier.value}": count / num_samples
            for tier, count in tier_counts.items()
        }

        return tier_probs
