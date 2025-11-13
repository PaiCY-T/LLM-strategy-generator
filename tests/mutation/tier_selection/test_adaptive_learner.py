"""
Test Adaptive Learner - Unit tests for adaptive learning logic.

Tests:
- Stats tracking and updates
- Threshold adjustment
- Recommendation generation
- Persistence
- Edge cases

Architecture: Phase 2.0+ Factor Graph System
Task: D.4 - Adaptive Mutation Tier Selection
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.mutation.tier_selection.adaptive_learner import (
    AdaptiveLearner,
    TierPerformance,
    MutationHistory
)


class TestAdaptiveLearnerInitialization:
    """Test adaptive learner initialization."""

    def test_default_initialization(self):
        """Test default initialization."""
        learner = AdaptiveLearner()
        assert learner.history_window == 100
        assert learner.learning_rate == 0.1
        assert learner.min_samples == 20
        assert len(learner.tier_performance) == 3
        assert learner.mutation_history == []

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        learner = AdaptiveLearner(
            history_window=50,
            learning_rate=0.2,
            min_samples=10
        )
        assert learner.history_window == 50
        assert learner.learning_rate == 0.2
        assert learner.min_samples == 10


class TestTierPerformance:
    """Test TierPerformance dataclass."""

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        perf = TierPerformance(tier=1)
        assert perf.success_rate == 0.5  # Default

        perf.attempts = 10
        perf.successes = 7
        assert perf.success_rate == 0.7

    def test_success_rate_zero_attempts(self):
        """Test success rate with zero attempts."""
        perf = TierPerformance(tier=1, attempts=0, successes=0)
        assert perf.success_rate == 0.5

    def test_to_dict(self):
        """Test conversion to dictionary."""
        perf = TierPerformance(tier=2, attempts=10, successes=7)
        data = perf.to_dict()

        assert data['tier'] == 2
        assert data['attempts'] == 10
        assert data['successes'] == 7

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {'tier': 2, 'attempts': 10, 'successes': 7, 'failures': 3}
        perf = TierPerformance.from_dict(data)

        assert perf.tier == 2
        assert perf.attempts == 10
        assert perf.successes == 7


class TestStatsUpdating:
    """Test tier statistics updating."""

    def test_update_tier_stats_success(self):
        """Test updating stats for successful mutation."""
        learner = AdaptiveLearner()

        learner.update_tier_stats(tier=2, success=True)

        perf = learner.tier_performance[2]
        assert perf.attempts == 1
        assert perf.successes == 1
        assert perf.failures == 0

    def test_update_tier_stats_failure(self):
        """Test updating stats for failed mutation."""
        learner = AdaptiveLearner()

        learner.update_tier_stats(tier=2, success=False)

        perf = learner.tier_performance[2]
        assert perf.attempts == 1
        assert perf.successes == 0
        assert perf.failures == 1

    def test_update_tier_stats_with_metrics(self):
        """Test updating stats with fitness delta."""
        learner = AdaptiveLearner()

        learner.update_tier_stats(
            tier=2,
            success=True,
            metrics={'fitness_delta': 0.05}
        )

        perf = learner.tier_performance[2]
        assert perf.avg_fitness_delta != 0.0

    def test_invalid_tier_raises_error(self):
        """Test invalid tier number raises error."""
        learner = AdaptiveLearner()

        with pytest.raises(ValueError, match="Invalid tier"):
            learner.update_tier_stats(tier=4, success=True)

    def test_mutation_history_tracking(self):
        """Test mutation history is tracked."""
        learner = AdaptiveLearner()

        learner.update_tier_stats(
            tier=2,
            success=True,
            metrics={'mutation_type': 'add_factor'}
        )

        assert len(learner.mutation_history) == 1
        mutation = learner.mutation_history[0]
        assert mutation.tier == 2
        assert mutation.success is True
        assert mutation.mutation_type == 'add_factor'

    def test_history_window_trimming(self):
        """Test history is trimmed to window size."""
        learner = AdaptiveLearner(history_window=10)

        # Add 20 mutations
        for i in range(20):
            learner.update_tier_stats(tier=1, success=True)

        # Should only keep last 10
        assert len(learner.mutation_history) == 10

    def test_recent_success_rate_update(self):
        """Test recent success rate is updated."""
        learner = AdaptiveLearner()

        # Add several mutations to Tier 2
        for i in range(10):
            learner.update_tier_stats(tier=2, success=(i % 2 == 0))

        perf = learner.tier_performance[2]
        # Should have calculated recent rate
        assert 0.0 <= perf.recent_success_rate <= 1.0


class TestThresholdAdjustment:
    """Test threshold adjustment logic."""

    def test_adjust_thresholds_insufficient_samples(self):
        """Test threshold adjustment with insufficient samples."""
        learner = AdaptiveLearner(min_samples=20)

        # Add only 5 samples
        for i in range(5):
            learner.update_tier_stats(tier=1, success=True)

        result = learner.adjust_thresholds(0.3, 0.7)

        assert result['adjusted'] is False
        assert 'Insufficient samples' in result['reason']
        assert result['tier1_threshold'] == 0.3
        assert result['tier2_threshold'] == 0.7

    def test_adjust_thresholds_with_sufficient_samples(self):
        """Test threshold adjustment with sufficient samples."""
        learner = AdaptiveLearner(min_samples=20, learning_rate=0.1)

        # Add 30 samples with varying success rates
        for i in range(10):
            learner.update_tier_stats(tier=1, success=True)  # 100% success
        for i in range(10):
            learner.update_tier_stats(tier=2, success=(i < 5))  # 50% success
        for i in range(10):
            learner.update_tier_stats(tier=3, success=False)  # 0% success

        result = learner.adjust_thresholds(0.3, 0.7)

        assert result['adjusted'] is True
        assert 'tier1_threshold' in result
        assert 'tier2_threshold' in result

    def test_high_tier1_success_increases_threshold(self):
        """Test high Tier 1 success increases threshold."""
        learner = AdaptiveLearner(min_samples=10, learning_rate=0.1)

        # Tier 1 with high success
        for i in range(15):
            learner.update_tier_stats(tier=1, success=True)
        for i in range(5):
            learner.update_tier_stats(tier=2, success=True)

        result = learner.adjust_thresholds(0.3, 0.7)

        # Tier 1 threshold should increase
        assert result['tier1_threshold'] > 0.3

    def test_thresholds_clamped_to_valid_range(self):
        """Test thresholds are clamped to valid ranges."""
        learner = AdaptiveLearner(min_samples=10, learning_rate=0.5)

        # Extreme success rates
        for i in range(20):
            learner.update_tier_stats(tier=1, success=True)
            learner.update_tier_stats(tier=2, success=True)
            learner.update_tier_stats(tier=3, success=True)

        result = learner.adjust_thresholds(0.3, 0.7)

        # Should be clamped
        assert 0.1 <= result['tier1_threshold'] <= 0.5
        assert result['tier1_threshold'] < result['tier2_threshold'] <= 0.9

    def test_threshold_deltas_recorded(self):
        """Test threshold deltas are recorded in result."""
        learner = AdaptiveLearner(min_samples=10)

        for i in range(20):
            learner.update_tier_stats(tier=1, success=True)

        result = learner.adjust_thresholds(0.3, 0.7)

        if result['adjusted']:
            assert 'tier1_delta' in result
            assert 'tier2_delta' in result


class TestRecommendations:
    """Test recommendation generation."""

    def test_get_recommendations_structure(self):
        """Test recommendations have correct structure."""
        learner = AdaptiveLearner()

        recommendations = learner.get_tier_recommendations()

        assert 'recommended_tier' in recommendations
        assert 'confidence' in recommendations
        assert 'performance_summary' in recommendations
        assert 'threshold_recommendations' in recommendations
        assert 'insights' in recommendations
        assert 'total_mutations' in recommendations

    def test_recommendations_with_no_data(self):
        """Test recommendations with no mutation history."""
        learner = AdaptiveLearner()

        recommendations = learner.get_tier_recommendations()

        assert recommendations['total_mutations'] == 0
        assert recommendations['confidence'] == 0.0
        assert len(recommendations['insights']) > 0

    def test_recommendations_with_data(self):
        """Test recommendations with mutation history."""
        learner = AdaptiveLearner()

        # Add mutations with varying success
        for i in range(10):
            learner.update_tier_stats(tier=1, success=True)
        for i in range(10):
            learner.update_tier_stats(tier=2, success=(i < 7))
        for i in range(10):
            learner.update_tier_stats(tier=3, success=(i < 5))

        recommendations = learner.get_tier_recommendations()

        assert recommendations['total_mutations'] == 30
        assert 0.0 <= recommendations['confidence'] <= 1.0
        assert recommendations['recommended_tier'] in [1, 2, 3]

    def test_best_tier_identification(self):
        """Test best performing tier is identified."""
        learner = AdaptiveLearner()

        # Tier 2 performs best
        for i in range(10):
            learner.update_tier_stats(tier=1, success=(i < 5))  # 50%
        for i in range(10):
            learner.update_tier_stats(tier=2, success=(i < 9))  # 90%
        for i in range(10):
            learner.update_tier_stats(tier=3, success=(i < 3))  # 30%

        recommendations = learner.get_tier_recommendations()

        # Tier 2 should be recommended
        assert recommendations['recommended_tier'] == 2

    def test_confidence_calculation(self):
        """Test confidence increases with more samples."""
        learner = AdaptiveLearner()

        # Few samples
        for i in range(5):
            learner.update_tier_stats(tier=1, success=True)

        recs_low = learner.get_tier_recommendations()
        confidence_low = recs_low['confidence']

        # Many samples
        for i in range(50):
            learner.update_tier_stats(tier=1, success=True)

        recs_high = learner.get_tier_recommendations()
        confidence_high = recs_high['confidence']

        assert confidence_high > confidence_low

    def test_performance_summary_structure(self):
        """Test performance summary has correct structure."""
        learner = AdaptiveLearner()

        for i in range(10):
            learner.update_tier_stats(tier=1, success=True)

        recommendations = learner.get_tier_recommendations()
        summary = recommendations['performance_summary']

        assert 'tier1' in summary
        assert 'tier2' in summary
        assert 'tier3' in summary

        for tier_stats in summary.values():
            assert 'success_rate' in tier_stats
            assert 'recent_success_rate' in tier_stats
            assert 'attempts' in tier_stats
            assert 'trend' in tier_stats


class TestTierStats:
    """Test tier statistics retrieval."""

    def test_get_tier_stats(self):
        """Test getting tier statistics."""
        learner = AdaptiveLearner()

        for i in range(10):
            learner.update_tier_stats(tier=2, success=True)

        stats = learner.get_tier_stats()

        assert 'tier1' in stats
        assert 'tier2' in stats
        assert 'tier3' in stats
        assert stats['tier2']['attempts'] == 10
        assert stats['tier2']['successes'] == 10

    def test_reset_stats(self):
        """Test resetting all statistics."""
        learner = AdaptiveLearner()

        # Add some data
        for i in range(10):
            learner.update_tier_stats(tier=1, success=True)

        # Reset
        learner.reset_stats()

        # Should be clean
        stats = learner.get_tier_stats()
        for tier_stats in stats.values():
            assert tier_stats['attempts'] == 0
            assert tier_stats['successes'] == 0


class TestPersistence:
    """Test history persistence."""

    def test_save_and_load_history(self):
        """Test saving and loading mutation history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence_path = str(Path(tmpdir) / "history.json")

            # Create learner and add data
            learner1 = AdaptiveLearner(persistence_path=persistence_path)
            for i in range(10):
                learner1.update_tier_stats(tier=2, success=True)

            # Create new learner and load
            learner2 = AdaptiveLearner(persistence_path=persistence_path)

            # Should have loaded data
            stats = learner2.get_tier_stats()
            assert stats['tier2']['attempts'] == 10

    def test_persistence_with_no_file(self):
        """Test loading when persistence file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence_path = str(Path(tmpdir) / "nonexistent.json")

            # Should not fail
            learner = AdaptiveLearner(persistence_path=persistence_path)
            assert len(learner.mutation_history) == 0

    def test_persistence_without_path(self):
        """Test learner works without persistence path."""
        learner = AdaptiveLearner()

        # Should not fail when updating
        learner.update_tier_stats(tier=1, success=True)


class TestPrivateHelpers:
    """Test private helper methods."""

    def test_calculate_trend_improving(self):
        """Test trend calculation for improving performance."""
        learner = AdaptiveLearner()

        # Add worsening then improving mutations
        for i in range(10):
            learner.update_tier_stats(tier=2, success=(i < 3))  # Early: 30% success
        for i in range(10):
            learner.update_tier_stats(tier=2, success=(i < 8))  # Late: 80% success

        trend = learner._calculate_trend(2)
        assert trend == "improving"

    def test_calculate_trend_declining(self):
        """Test trend calculation for declining performance."""
        learner = AdaptiveLearner()

        # Add improving then worsening mutations
        for i in range(10):
            learner.update_tier_stats(tier=2, success=(i < 8))  # Early: 80% success
        for i in range(10):
            learner.update_tier_stats(tier=2, success=(i < 3))  # Late: 30% success

        trend = learner._calculate_trend(2)
        assert trend == "declining"

    def test_calculate_trend_stable(self):
        """Test trend calculation for stable performance."""
        learner = AdaptiveLearner()

        # Consistent performance
        for i in range(20):
            learner.update_tier_stats(tier=2, success=(i % 2 == 0))

        trend = learner._calculate_trend(2)
        assert trend == "stable"

    def test_calculate_trend_insufficient_data(self):
        """Test trend calculation with insufficient data."""
        learner = AdaptiveLearner()

        for i in range(5):
            learner.update_tier_stats(tier=2, success=True)

        trend = learner._calculate_trend(2)
        assert trend == "insufficient_data"

    def test_generate_insights(self):
        """Test insights generation."""
        learner = AdaptiveLearner()

        for i in range(20):
            learner.update_tier_stats(tier=1, success=True)

        insights = learner._generate_insights()

        assert isinstance(insights, list)
        assert len(insights) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_fitness_delta_none(self):
        """Test handling of None fitness delta."""
        learner = AdaptiveLearner()

        learner.update_tier_stats(
            tier=1,
            success=True,
            metrics={'fitness_delta': None}
        )

        # Should not crash
        perf = learner.tier_performance[1]
        assert perf.attempts == 1

    def test_empty_metrics(self):
        """Test handling of empty metrics."""
        learner = AdaptiveLearner()

        learner.update_tier_stats(tier=1, success=True, metrics={})

        # Should not crash
        assert learner.tier_performance[1].attempts == 1

    def test_none_metrics(self):
        """Test handling of None metrics."""
        learner = AdaptiveLearner()

        learner.update_tier_stats(tier=1, success=True, metrics=None)

        # Should not crash
        assert learner.tier_performance[1].attempts == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
