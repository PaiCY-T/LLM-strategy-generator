"""
Test suite for TierPerformanceTracker.

Tests performance tracking, statistics calculation, and reporting
for the three-tier mutation system.

Architecture: Structural Mutation Phase 2 - Phase D.5
Task: D.5 - Three-Tier Mutation System Integration
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.mutation.tier_performance_tracker import (
    TierPerformanceTracker,
    MutationRecord,
    TierStats
)


class TestTierPerformanceTracker:
    """Test TierPerformanceTracker functionality."""

    def test_initialization(self):
        """Test tracker initializes correctly."""
        tracker = TierPerformanceTracker()

        assert tracker is not None
        assert len(tracker._records) == 0
        assert all(len(tracker._tier_records[tier]) == 0 for tier in [1, 2, 3])

    def test_record_mutation_tier_2_success(self):
        """Test recording successful Tier 2 mutation."""
        tracker = TierPerformanceTracker()

        tracker.record_mutation(
            tier=2,
            success=True,
            performance_delta=0.05,
            mutation_type="add_factor",
            strategy_id="strat_001"
        )

        assert len(tracker._records) == 1
        assert len(tracker._tier_records[2]) == 1
        assert tracker._tier_stats[2].count == 1
        assert tracker._tier_stats[2].successes == 1
        assert tracker._tier_stats[2].success_rate == 1.0

    def test_record_mutation_tier_3_failure(self):
        """Test recording failed Tier 3 mutation."""
        tracker = TierPerformanceTracker()

        tracker.record_mutation(
            tier=3,
            success=False,
            performance_delta=0.0,
            mutation_type="ast_mutation",
            strategy_id="strat_002"
        )

        assert len(tracker._records) == 1
        assert tracker._tier_stats[3].failures == 1
        assert tracker._tier_stats[3].success_rate == 0.0

    def test_record_multiple_mutations(self):
        """Test recording multiple mutations across tiers."""
        tracker = TierPerformanceTracker()

        # Record 5 Tier 2 mutations (4 success, 1 failure)
        for i in range(4):
            tracker.record_mutation(
                tier=2,
                success=True,
                performance_delta=0.03 + i * 0.01,
                mutation_type="add_factor"
            )

        tracker.record_mutation(
            tier=2,
            success=False,
            performance_delta=0.0,
            mutation_type="add_factor"
        )

        # Record 3 Tier 3 mutations (2 success, 1 failure)
        tracker.record_mutation(tier=3, success=True, performance_delta=0.10, mutation_type="ast_mutation")
        tracker.record_mutation(tier=3, success=True, performance_delta=0.15, mutation_type="ast_mutation")
        tracker.record_mutation(tier=3, success=False, performance_delta=0.0, mutation_type="ast_mutation")

        assert len(tracker._records) == 8
        assert tracker._tier_stats[2].count == 5
        assert tracker._tier_stats[2].successes == 4
        assert tracker._tier_stats[2].success_rate == 0.8
        assert tracker._tier_stats[3].count == 3
        assert tracker._tier_stats[3].successes == 2

    def test_invalid_tier_raises_error(self):
        """Test that invalid tier raises ValueError."""
        tracker = TierPerformanceTracker()

        with pytest.raises(ValueError, match="Invalid tier"):
            tracker.record_mutation(
                tier=4,  # Invalid
                success=True,
                performance_delta=0.05,
                mutation_type="unknown"
            )

    def test_get_tier_summary(self):
        """Test getting tier summary statistics."""
        tracker = TierPerformanceTracker()

        # Add some data
        tracker.record_mutation(tier=1, success=True, performance_delta=0.02, mutation_type="yaml_config")
        tracker.record_mutation(tier=1, success=True, performance_delta=0.03, mutation_type="yaml_config")
        tracker.record_mutation(tier=2, success=True, performance_delta=0.05, mutation_type="add_factor")
        tracker.record_mutation(tier=2, success=False, performance_delta=0.0, mutation_type="add_factor")

        summary = tracker.get_tier_summary()

        assert "tier_1" in summary
        assert "tier_2" in summary
        assert "tier_3" in summary

        assert summary["tier_1"]["count"] == 2
        assert summary["tier_1"]["successes"] == 2
        assert summary["tier_1"]["success_rate"] == 1.0
        assert summary["tier_1"]["avg_improvement"] == pytest.approx(0.025, rel=1e-3)

        assert summary["tier_2"]["count"] == 2
        assert summary["tier_2"]["success_rate"] == 0.5

    def test_get_tier_comparison(self):
        """Test tier comparison analysis."""
        tracker = TierPerformanceTracker()

        # Add varied data across tiers
        tracker.record_mutation(tier=1, success=True, performance_delta=0.02, mutation_type="yaml")
        tracker.record_mutation(tier=1, success=True, performance_delta=0.02, mutation_type="yaml")

        tracker.record_mutation(tier=2, success=True, performance_delta=0.05, mutation_type="add_factor")
        tracker.record_mutation(tier=2, success=True, performance_delta=0.04, mutation_type="remove_factor")
        tracker.record_mutation(tier=2, success=False, performance_delta=0.0, mutation_type="replace_factor")

        tracker.record_mutation(tier=3, success=True, performance_delta=0.15, mutation_type="ast_mutation")

        comparison = tracker.get_tier_comparison()

        assert comparison["total_mutations"] == 6
        assert comparison["tier_distribution"][2] == 3  # Most used
        assert comparison["tier_distribution_pct"][2] == pytest.approx(0.5, rel=1e-3)
        assert comparison["most_used_tier"] == 2
        assert comparison["best_tier_by_success_rate"] == 1  # 100% success
        assert comparison["best_tier_by_improvement"] == 3  # Highest delta

    def test_get_mutation_type_analysis(self):
        """Test mutation type analysis across tiers."""
        tracker = TierPerformanceTracker()

        # Add data with different mutation types
        tracker.record_mutation(tier=2, success=True, performance_delta=0.05, mutation_type="add_factor")
        tracker.record_mutation(tier=2, success=True, performance_delta=0.04, mutation_type="add_factor")
        tracker.record_mutation(tier=2, success=False, performance_delta=0.0, mutation_type="add_factor")

        tracker.record_mutation(tier=3, success=True, performance_delta=0.10, mutation_type="add_factor")

        analysis = tracker.get_mutation_type_analysis()

        assert "add_factor" in analysis
        add_factor_stats = analysis["add_factor"]

        assert add_factor_stats["tier_2"] == 3
        assert add_factor_stats["tier_3"] == 1
        assert add_factor_stats["total_count"] == 4
        assert add_factor_stats["total_successes"] == 3
        assert add_factor_stats["success_rate"] == 0.75

    def test_export_analysis(self):
        """Test exporting analysis to JSON file."""
        tracker = TierPerformanceTracker()

        # Add some data
        tracker.record_mutation(tier=2, success=True, performance_delta=0.05, mutation_type="add_factor")
        tracker.record_mutation(tier=3, success=False, performance_delta=0.0, mutation_type="ast_mutation")

        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "tier_analysis.json"
            tracker.export_analysis(str(export_path))

            assert export_path.exists()

            # Verify JSON structure
            with open(export_path, 'r') as f:
                data = json.load(f)

            assert "summary" in data
            assert "comparison" in data
            assert "mutation_type_analysis" in data
            assert "export_timestamp" in data
            assert data["total_records"] == 2

    def test_get_records_filtering(self):
        """Test getting records with filtering."""
        tracker = TierPerformanceTracker()

        # Add mixed data
        tracker.record_mutation(tier=2, success=True, performance_delta=0.05, mutation_type="add_factor")
        tracker.record_mutation(tier=2, success=False, performance_delta=0.0, mutation_type="add_factor")
        tracker.record_mutation(tier=3, success=True, performance_delta=0.10, mutation_type="ast_mutation")

        # Test tier filtering
        tier2_records = tracker.get_records(tier=2)
        assert len(tier2_records) == 2

        # Test success filtering
        successful_records = tracker.get_records(success=True)
        assert len(successful_records) == 2

        # Test combined filtering
        tier2_successful = tracker.get_records(tier=2, success=True)
        assert len(tier2_successful) == 1

        # Test limit
        limited_records = tracker.get_records(limit=2)
        assert len(limited_records) == 2

    def test_reset_stats(self):
        """Test resetting statistics."""
        tracker = TierPerformanceTracker()

        # Add data
        tracker.record_mutation(tier=2, success=True, performance_delta=0.05, mutation_type="add_factor")
        tracker.record_mutation(tier=3, success=False, performance_delta=0.0, mutation_type="ast_mutation")

        assert len(tracker._records) == 2

        # Reset
        tracker.reset_stats()

        assert len(tracker._records) == 0
        assert all(len(tracker._tier_records[tier]) == 0 for tier in [1, 2, 3])
        assert all(tracker._tier_stats[tier].count == 0 for tier in [1, 2, 3])

    def test_get_recent_trends(self):
        """Test getting recent trends in tier performance."""
        tracker = TierPerformanceTracker()

        # Add 30 mutations
        for i in range(30):
            tier = (i % 3) + 1  # Cycle through tiers
            success = i % 3 != 0  # 2/3 success rate
            tracker.record_mutation(
                tier=tier,
                success=success,
                performance_delta=0.05 if success else 0.0,
                mutation_type=f"type_{tier}"
            )

        # Get trends for last 20 mutations
        trends = tracker.get_recent_trends(window=20)

        assert trends["window_size"] == 20
        assert trends["tier_1_count"] + trends["tier_2_count"] + trends["tier_3_count"] == 20

    def test_performance_improvement_calculations(self):
        """Test performance improvement calculations."""
        tracker = TierPerformanceTracker()

        # Add mutations with known deltas
        tracker.record_mutation(tier=2, success=True, performance_delta=0.05, mutation_type="add_factor")
        tracker.record_mutation(tier=2, success=True, performance_delta=0.10, mutation_type="add_factor")
        tracker.record_mutation(tier=2, success=True, performance_delta=0.15, mutation_type="add_factor")

        summary = tracker.get_tier_summary()
        tier2_stats = summary["tier_2"]

        assert tier2_stats["avg_improvement"] == pytest.approx(0.10, rel=1e-3)
        assert tier2_stats["best_improvement"] == pytest.approx(0.15, rel=1e-3)
        assert tier2_stats["worst_improvement"] == pytest.approx(0.05, rel=1e-3)

    def test_empty_tracker_statistics(self):
        """Test statistics with no data."""
        tracker = TierPerformanceTracker()

        summary = tracker.get_tier_summary()
        assert all(summary[f"tier_{i}"]["count"] == 0 for i in [1, 2, 3])
        assert all(summary[f"tier_{i}"]["success_rate"] == 0.0 for i in [1, 2, 3])

        comparison = tracker.get_tier_comparison()
        assert comparison["total_mutations"] == 0

    def test_mutation_type_distribution(self):
        """Test mutation type distribution tracking."""
        tracker = TierPerformanceTracker()

        # Add mutations with different types
        tracker.record_mutation(tier=2, success=True, performance_delta=0.05, mutation_type="add_factor")
        tracker.record_mutation(tier=2, success=True, performance_delta=0.04, mutation_type="add_factor")
        tracker.record_mutation(tier=2, success=True, performance_delta=0.03, mutation_type="remove_factor")

        summary = tracker.get_tier_summary()
        mutation_types = summary["tier_2"]["mutation_types"]

        assert mutation_types["add_factor"] == 2
        assert mutation_types["remove_factor"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
