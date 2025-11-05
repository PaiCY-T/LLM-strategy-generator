"""
Test Tier Router - Unit tests for tier routing logic.

Tests:
- Correct tier selection for different risk levels
- Tier override functionality
- Mutation plan creation
- Threshold adjustment
- Edge cases

Architecture: Phase 2.0+ Factor Graph System
Task: D.4 - Adaptive Mutation Tier Selection
"""

import pytest
from unittest.mock import Mock

from src.mutation.tier_selection.tier_router import (
    TierRouter,
    MutationPlan,
    MutationTier
)


class TestTierRouterInitialization:
    """Test tier router initialization."""

    def test_default_initialization(self):
        """Test default initialization with standard thresholds."""
        router = TierRouter()
        assert router.tier1_threshold == 0.3
        assert router.tier2_threshold == 0.7
        assert router.allow_override is True

    def test_custom_thresholds(self):
        """Test initialization with custom thresholds."""
        router = TierRouter(tier1_threshold=0.2, tier2_threshold=0.6)
        assert router.tier1_threshold == 0.2
        assert router.tier2_threshold == 0.6

    def test_invalid_threshold_order(self):
        """Test that tier1 must be < tier2."""
        with pytest.raises(ValueError, match="Invalid thresholds"):
            TierRouter(tier1_threshold=0.7, tier2_threshold=0.3)

    def test_invalid_threshold_range(self):
        """Test that thresholds must be in [0, 1]."""
        with pytest.raises(ValueError, match="Invalid thresholds"):
            TierRouter(tier1_threshold=-0.1, tier2_threshold=0.7)

        with pytest.raises(ValueError, match="Invalid thresholds"):
            TierRouter(tier1_threshold=0.3, tier2_threshold=1.5)


class TestTierSelection:
    """Test tier selection logic."""

    def test_low_risk_selects_tier1(self):
        """Test low risk score selects Tier 1."""
        router = TierRouter(tier1_threshold=0.3, tier2_threshold=0.7)

        tier = router.select_tier(risk_score=0.1)
        assert tier == MutationTier.TIER1_YAML

        tier = router.select_tier(risk_score=0.29)
        assert tier == MutationTier.TIER1_YAML

    def test_medium_risk_selects_tier2(self):
        """Test medium risk score selects Tier 2."""
        router = TierRouter(tier1_threshold=0.3, tier2_threshold=0.7)

        tier = router.select_tier(risk_score=0.3)
        assert tier == MutationTier.TIER2_FACTOR

        tier = router.select_tier(risk_score=0.5)
        assert tier == MutationTier.TIER2_FACTOR

        tier = router.select_tier(risk_score=0.69)
        assert tier == MutationTier.TIER2_FACTOR

    def test_high_risk_selects_tier3(self):
        """Test high risk score selects Tier 3."""
        router = TierRouter(tier1_threshold=0.3, tier2_threshold=0.7)

        tier = router.select_tier(risk_score=0.7)
        assert tier == MutationTier.TIER3_AST

        tier = router.select_tier(risk_score=0.9)
        assert tier == MutationTier.TIER3_AST

    def test_risk_score_clamping(self):
        """Test risk scores are clamped to [0, 1]."""
        router = TierRouter()

        # Below 0
        tier = router.select_tier(risk_score=-0.5)
        assert tier == MutationTier.TIER1_YAML

        # Above 1
        tier = router.select_tier(risk_score=1.5)
        assert tier == MutationTier.TIER3_AST

    def test_boundary_values(self):
        """Test exact boundary values."""
        router = TierRouter(tier1_threshold=0.3, tier2_threshold=0.7)

        # Exactly at tier1 threshold
        tier = router.select_tier(risk_score=0.3)
        assert tier == MutationTier.TIER2_FACTOR

        # Exactly at tier2 threshold
        tier = router.select_tier(risk_score=0.7)
        assert tier == MutationTier.TIER3_AST

    def test_tier_override_enabled(self):
        """Test manual tier override when enabled."""
        router = TierRouter(allow_override=True)

        # Override to Tier 1
        tier = router.select_tier(risk_score=0.9, override_tier=1)
        assert tier == MutationTier.TIER1_YAML

        # Override to Tier 3
        tier = router.select_tier(risk_score=0.1, override_tier=3)
        assert tier == MutationTier.TIER3_AST

    def test_tier_override_disabled(self):
        """Test tier override raises error when disabled."""
        router = TierRouter(allow_override=False)

        with pytest.raises(ValueError, match="override is disabled"):
            router.select_tier(risk_score=0.5, override_tier=1)

    def test_invalid_override_tier(self):
        """Test invalid override tier raises error."""
        router = TierRouter(allow_override=True)

        with pytest.raises(ValueError, match="Invalid tier override"):
            router.select_tier(risk_score=0.5, override_tier=4)

        with pytest.raises(ValueError, match="Invalid tier override"):
            router.select_tier(risk_score=0.5, override_tier=0)


class TestMutationRouting:
    """Test mutation routing and plan creation."""

    def test_route_mutation_creates_plan(self):
        """Test route_mutation creates complete mutation plan."""
        router = TierRouter()
        strategy = Mock()
        strategy.id = "test_strategy"

        plan = router.route_mutation(
            strategy=strategy,
            mutation_intent="add_factor",
            risk_score=0.5
        )

        assert isinstance(plan, MutationPlan)
        assert plan.tier == MutationTier.TIER2_FACTOR
        assert plan.mutation_type is not None
        assert plan.config is not None
        assert 0.0 <= plan.risk_score <= 1.0
        assert plan.rationale is not None

    def test_plan_includes_strategy_id(self):
        """Test mutation plan includes strategy ID in config."""
        router = TierRouter()
        strategy = Mock()
        strategy.id = "momentum_v2"

        plan = router.route_mutation(
            strategy=strategy,
            mutation_intent="add_factor",
            risk_score=0.2
        )

        assert plan.config['strategy_id'] == "momentum_v2"
        assert plan.config['tier'] == 1

    def test_mutation_type_mapping_tier1(self):
        """Test mutation intent maps to Tier 1 operations."""
        router = TierRouter()
        strategy = Mock()
        strategy.id = "test"

        # Test different intents
        plan = router.route_mutation(strategy, "add_factor", 0.1)
        assert "yaml" in plan.mutation_type

        plan = router.route_mutation(strategy, "adjust_parameters", 0.1)
        assert "yaml" in plan.mutation_type

    def test_mutation_type_mapping_tier2(self):
        """Test mutation intent maps to Tier 2 operations."""
        router = TierRouter()
        strategy = Mock()
        strategy.id = "test"

        plan = router.route_mutation(strategy, "add_factor", 0.5)
        assert "factor" in plan.mutation_type

    def test_mutation_type_mapping_tier3(self):
        """Test mutation intent maps to Tier 3 operations."""
        router = TierRouter()
        strategy = Mock()
        strategy.id = "test"

        plan = router.route_mutation(strategy, "modify_logic", 0.8)
        assert "ast" in plan.mutation_type

    def test_custom_config_preserved(self):
        """Test custom config is preserved in plan."""
        router = TierRouter()
        strategy = Mock()
        strategy.id = "test"

        custom_config = {'custom_param': 'value', 'another': 123}
        plan = router.route_mutation(
            strategy, "add_factor", 0.5, config=custom_config
        )

        assert plan.config['custom_param'] == 'value'
        assert plan.config['another'] == 123

    def test_rationale_generation(self):
        """Test rationale is generated correctly."""
        router = TierRouter()
        strategy = Mock()
        strategy.id = "test"

        # Low risk
        plan = router.route_mutation(strategy, "add_factor", 0.1)
        assert "low risk" in plan.rationale.lower()
        assert "Tier 1" in plan.rationale or "tier 1" in plan.rationale.lower()

        # High risk
        plan = router.route_mutation(strategy, "add_factor", 0.9)
        assert "high risk" in plan.rationale.lower()
        assert "Tier 3" in plan.rationale or "tier 3" in plan.rationale.lower()

    def test_override_rationale(self):
        """Test rationale mentions override when used."""
        router = TierRouter()
        strategy = Mock()
        strategy.id = "test"

        plan = router.route_mutation(
            strategy, "add_factor", 0.5, override_tier=3
        )

        assert "override" in plan.rationale.lower()


class TestThresholdAdjustment:
    """Test threshold adjustment based on performance."""

    def test_high_tier1_success_increases_threshold(self):
        """Test high Tier 1 success rate increases threshold."""
        router = TierRouter(tier1_threshold=0.3, tier2_threshold=0.7)

        tier_stats = {
            'tier1': {'success_rate': 0.8},  # High success
            'tier2': {'success_rate': 0.5},
            'tier3': {'success_rate': 0.5}
        }

        new_t1, new_t2 = router.adjust_thresholds(tier_stats)

        # Tier 1 threshold should increase
        assert new_t1 > 0.3

    def test_low_tier1_success_decreases_threshold(self):
        """Test low Tier 1 success rate decreases threshold."""
        router = TierRouter(tier1_threshold=0.3, tier2_threshold=0.7)

        tier_stats = {
            'tier1': {'success_rate': 0.2},  # Low success
            'tier2': {'success_rate': 0.5},
            'tier3': {'success_rate': 0.5}
        }

        new_t1, new_t2 = router.adjust_thresholds(tier_stats)

        # Tier 1 threshold should decrease
        assert new_t1 < 0.3

    def test_threshold_clamping(self):
        """Test thresholds are clamped to valid ranges."""
        router = TierRouter(tier1_threshold=0.3, tier2_threshold=0.7)

        # Extreme success rates
        tier_stats = {
            'tier1': {'success_rate': 1.0},  # Perfect success
            'tier2': {'success_rate': 1.0},
            'tier3': {'success_rate': 1.0}
        }

        new_t1, new_t2 = router.adjust_thresholds(tier_stats)

        # Should be clamped
        assert 0.1 <= new_t1 <= 0.5
        assert new_t1 < new_t2 <= 0.9

    def test_empty_tier_stats(self):
        """Test adjustment with empty stats returns original thresholds."""
        router = TierRouter(tier1_threshold=0.3, tier2_threshold=0.7)

        new_t1, new_t2 = router.adjust_thresholds({})

        assert new_t1 == 0.3
        assert new_t2 == 0.7


class TestTierDistribution:
    """Test tier distribution calculation."""

    def test_tier_distribution_with_default_thresholds(self):
        """Test expected tier distribution with default thresholds."""
        router = TierRouter(tier1_threshold=0.3, tier2_threshold=0.7)

        dist = router.get_tier_distribution(num_samples=1000)

        # Check all tiers present
        assert 'tier1' in dist
        assert 'tier2' in dist
        assert 'tier3' in dist

        # Check probabilities sum to ~1.0
        total = sum(dist.values())
        assert abs(total - 1.0) < 0.05

        # Check approximate distribution (30%, 40%, 30%)
        assert abs(dist['tier1'] - 0.30) < 0.1
        assert abs(dist['tier2'] - 0.40) < 0.1
        assert abs(dist['tier3'] - 0.30) < 0.1

    def test_tier_distribution_with_custom_thresholds(self):
        """Test tier distribution adapts to custom thresholds."""
        # Conservative setup (more Tier 1)
        router = TierRouter(tier1_threshold=0.5, tier2_threshold=0.8)

        dist = router.get_tier_distribution(num_samples=1000)

        # Tier 1 should be more common
        assert dist['tier1'] > 0.4

    def test_tier_distribution_sample_size(self):
        """Test tier distribution with different sample sizes."""
        router = TierRouter()

        dist_small = router.get_tier_distribution(num_samples=100)
        dist_large = router.get_tier_distribution(num_samples=10000)

        # Both should give similar results
        for tier in ['tier1', 'tier2', 'tier3']:
            assert abs(dist_small[tier] - dist_large[tier]) < 0.1


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_strategy_without_id(self):
        """Test handling of strategy without id attribute."""
        router = TierRouter()
        strategy = Mock(spec=[])  # No attributes

        plan = router.route_mutation(strategy, "add_factor", 0.5)

        assert plan.config['strategy_id'] == 'unknown'

    def test_equal_thresholds_boundary(self):
        """Test that equal thresholds are technically allowed but leave no Tier 2 range."""
        # Equal thresholds are allowed but impractical (no Tier 2 range)
        router = TierRouter(tier1_threshold=0.5, tier2_threshold=0.5)
        assert router.tier1_threshold == 0.5
        assert router.tier2_threshold == 0.5

    def test_zero_risk_score(self):
        """Test zero risk score."""
        router = TierRouter()
        tier = router.select_tier(risk_score=0.0)
        assert tier == MutationTier.TIER1_YAML

    def test_one_risk_score(self):
        """Test maximum risk score."""
        router = TierRouter()
        tier = router.select_tier(risk_score=1.0)
        assert tier == MutationTier.TIER3_AST


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
