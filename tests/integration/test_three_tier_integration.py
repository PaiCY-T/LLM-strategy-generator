"""
End-to-end integration tests for three-tier mutation system.

Tests the complete integration of:
- UnifiedMutationOperator
- TierPerformanceTracker
- PopulationManagerV2
- Three-tier mutation system

Architecture: Structural Mutation Phase 2 - Phase D.5
Task: D.5 - Three-Tier Mutation System Integration
"""

import pytest
from unittest.mock import Mock

from src.population.population_manager_v2 import PopulationManagerV2
from src.mutation.unified_mutation_operator import UnifiedMutationOperator
from src.mutation.tier_performance_tracker import TierPerformanceTracker
from src.factor_graph.strategy import Strategy
from src.factor_graph.factor import Factor, FactorCategory


class TestThreeTierIntegration:
    """Test end-to-end three-tier mutation system integration."""

    def test_population_manager_v2_initialization(self):
        """Test PopulationManagerV2 initializes correctly."""
        config = {
            "population_size": 20,
            "elite_size": 2,
            "enable_three_tier": True,
            "tier_selection_config": {
                "tier1_threshold": 0.3,
                "tier2_threshold": 0.7
            }
        }

        manager = PopulationManagerV2(config)

        assert manager is not None
        assert manager.population_size == 20
        assert manager.elite_size == 2
        assert manager.enable_three_tier is True

    def test_population_manager_v2_backward_compatibility(self):
        """Test PopulationManagerV2 backward compatibility with tier 2 only."""
        config = {
            "population_size": 10,
            "enable_three_tier": False  # Disable three-tier
        }

        manager = PopulationManagerV2(config)

        assert manager.enable_three_tier is False
        assert manager.unified_mutator is None
        assert manager.tier_tracker is None

    def test_population_manager_v2_evolution_report(self):
        """Test getting evolution report from PopulationManagerV2."""
        config = {
            "population_size": 10,
            "enable_three_tier": True
        }

        manager = PopulationManagerV2(config)

        report = manager.get_evolution_report()

        assert report["three_tier_enabled"] is True
        assert "tier_statistics" in report
        assert "tier_performance" in report
        assert "tier_comparison" in report

    def test_population_manager_v2_tier_statistics(self):
        """Test getting tier statistics from PopulationManagerV2."""
        config = {
            "population_size": 10,
            "enable_three_tier": True
        }

        manager = PopulationManagerV2(config)

        stats = manager.get_tier_statistics()

        assert "three_tier_enabled" in stats or "tier_attempts" in stats

    def test_unified_mutation_and_tracking(self):
        """Test UnifiedMutationOperator works with TierPerformanceTracker."""
        # This is a simplified test - full integration requires more mocking
        tracker = TierPerformanceTracker()

        # Simulate some mutations
        tracker.record_mutation(tier=2, success=True, performance_delta=0.05, mutation_type="add_factor")
        tracker.record_mutation(tier=3, success=False, performance_delta=0.0, mutation_type="ast_mutation")
        tracker.record_mutation(tier=2, success=True, performance_delta=0.03, mutation_type="mutate_parameters")

        # Get summary
        summary = tracker.get_tier_summary()

        assert summary["tier_2"]["count"] == 2
        assert summary["tier_2"]["successes"] == 2
        assert summary["tier_3"]["count"] == 1
        assert summary["tier_3"]["failures"] == 1

    def test_tier_distribution_across_mutations(self):
        """Test tier distribution across multiple mutations."""
        tracker = TierPerformanceTracker()

        # Simulate mutation distribution: Tier 1: 20%, Tier 2: 50%, Tier 3: 30%
        for i in range(20):
            tracker.record_mutation(tier=1, success=True, performance_delta=0.02, mutation_type="yaml")

        for i in range(50):
            tracker.record_mutation(tier=2, success=True, performance_delta=0.04, mutation_type="add_factor")

        for i in range(30):
            tracker.record_mutation(tier=3, success=True, performance_delta=0.10, mutation_type="ast_mutation")

        comparison = tracker.get_tier_comparison()

        assert comparison["total_mutations"] == 100
        assert comparison["tier_distribution"][2] == 50
        assert comparison["most_used_tier"] == 2

        # Check distribution percentages
        assert abs(comparison["tier_distribution_pct"][1] - 0.20) < 0.01
        assert abs(comparison["tier_distribution_pct"][2] - 0.50) < 0.01
        assert abs(comparison["tier_distribution_pct"][3] - 0.30) < 0.01

    def test_performance_improvement_by_tier(self):
        """Test tracking performance improvements by tier."""
        tracker = TierPerformanceTracker()

        # Tier 1: Safe, small improvements
        for i in range(10):
            tracker.record_mutation(tier=1, success=True, performance_delta=0.02, mutation_type="yaml")

        # Tier 2: Medium improvements
        for i in range(10):
            tracker.record_mutation(tier=2, success=True, performance_delta=0.05, mutation_type="add_factor")

        # Tier 3: High improvements (when successful)
        for i in range(5):
            tracker.record_mutation(tier=3, success=True, performance_delta=0.15, mutation_type="ast_mutation")

        comparison = tracker.get_tier_comparison()

        # Verify Tier 3 has highest average improvement
        assert comparison["avg_improvement_comparison"][3] > comparison["avg_improvement_comparison"][2]
        assert comparison["avg_improvement_comparison"][2] > comparison["avg_improvement_comparison"][1]
        assert comparison["best_tier_by_improvement"] == 3

    def test_complete_workflow_simulation(self):
        """Test complete workflow: Manager → Operator → Tracker."""
        config = {
            "population_size": 10,
            "elite_size": 2,
            "enable_three_tier": True
        }

        manager = PopulationManagerV2(config)

        # Verify initialization
        assert manager.enable_three_tier is True
        assert manager.unified_mutator is not None
        assert manager.tier_tracker is not None

        # Get initial report
        report = manager.get_evolution_report()
        assert report["tier_statistics"]["total_mutations"] == 0

        # Note: Full mutation testing requires more complex mocking
        # of strategies and backtest infrastructure

    def test_tier_recommendations(self):
        """Test getting tier recommendations from PopulationManagerV2."""
        config = {
            "population_size": 10,
            "enable_three_tier": True
        }

        manager = PopulationManagerV2(config)

        # Get recommendations (may be empty initially)
        recommendations = manager.get_tier_recommendations()

        assert recommendations is not None
        # Recommendations should have basic structure
        assert isinstance(recommendations, dict)

    def test_three_tier_system_components_exist(self):
        """Test that all three-tier system components are accessible."""
        config = {
            "population_size": 10,
            "enable_three_tier": True
        }

        manager = PopulationManagerV2(config)

        # Verify all components exist
        assert hasattr(manager, 'unified_mutator')
        assert hasattr(manager, 'tier_tracker')
        assert manager.unified_mutator is not None
        assert manager.tier_tracker is not None

        # Verify unified mutator has all tier components
        assert hasattr(manager.unified_mutator, 'yaml_interpreter')
        assert hasattr(manager.unified_mutator, 'tier2_engine')
        assert hasattr(manager.unified_mutator, 'tier3_mutator')
        assert hasattr(manager.unified_mutator, 'tier_selector')


class TestIntegrationEdgeCases:
    """Test edge cases and error handling in integration."""

    def test_empty_tier_tracker_statistics(self):
        """Test tracker with no mutations recorded."""
        tracker = TierPerformanceTracker()

        summary = tracker.get_tier_summary()
        assert all(summary[f"tier_{i}"]["count"] == 0 for i in [1, 2, 3])

        comparison = tracker.get_tier_comparison()
        assert comparison["total_mutations"] == 0

    def test_tier_recommendations_without_data(self):
        """Test tier recommendations with no mutation history."""
        config = {
            "population_size": 10,
            "enable_three_tier": True
        }

        manager = PopulationManagerV2(config)

        # Should not raise error even without data
        recommendations = manager.get_tier_recommendations()
        assert recommendations is not None

    def test_reset_tier_learning(self):
        """Test resetting tier learning in PopulationManagerV2."""
        config = {
            "population_size": 10,
            "enable_three_tier": True
        }

        manager = PopulationManagerV2(config)

        # Record some mutations (simulated via tracker)
        manager.tier_tracker.record_mutation(
            tier=2,
            success=True,
            performance_delta=0.05,
            mutation_type="add_factor"
        )

        assert len(manager.tier_tracker._records) > 0

        # Reset
        manager.reset_tier_learning()

        assert len(manager.tier_tracker._records) == 0
        assert manager.current_generation == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
