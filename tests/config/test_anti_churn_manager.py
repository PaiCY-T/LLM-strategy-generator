"""Unit tests for AntiChurnManager (Story 4: Anti-Churn Configuration).

Tests anti-churn configuration, dynamic thresholds, and update frequency analysis.
"""

import pytest
import tempfile
import os
from unittest.mock import patch

from src.config.anti_churn_manager import AntiChurnManager, ChampionUpdateRecord


# Test Fixtures
@pytest.fixture
def test_config_file():
    """Create temporary test configuration file."""
    config_content = """
anti_churn:
  probation_period: 2
  probation_threshold: 0.10
  post_probation_threshold: 0.05
  min_sharpe_for_champion: 0.5
  target_update_frequency: 0.15
  tuning_range:
    probation_period: [1, 3]
    probation_threshold: [0.05, 0.15]
    post_probation_threshold: [0.03, 0.10]

features:
  enable_anti_churn: true
  enable_adaptive_tuning: false

monitoring:
  log_champion_updates: true
  alert_on_excessive_churn: true
  alert_on_stagnation: true
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


# Test Suite 1: Configuration Loading
class TestConfigLoading:
    """Test YAML configuration loading."""

    def test_load_valid_config(self, test_config_file):
        """Test loading valid configuration file."""
        manager = AntiChurnManager(config_path=test_config_file)

        assert manager.probation_period == 2
        assert manager.probation_threshold == 0.10
        assert manager.post_probation_threshold == 0.05
        assert manager.min_sharpe_for_champion == 0.5
        assert manager.target_update_frequency == 0.15

    def test_config_file_not_found(self):
        """Test handling of missing config file."""
        with pytest.raises(FileNotFoundError):
            AntiChurnManager(config_path="nonexistent_config.yaml")

    def test_default_values(self, test_config_file):
        """Test default fallback values."""
        # Malformed config with missing values
        malformed_content = """
anti_churn:
  probation_period: 3
  # Other values missing - should use defaults
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(malformed_content)
            malformed_path = f.name

        try:
            manager = AntiChurnManager(config_path=malformed_path)
            assert manager.probation_period == 3
            # Should use defaults for missing values
            assert manager.probation_threshold == 0.10  # default
            assert manager.post_probation_threshold == 0.05  # default
        finally:
            os.unlink(malformed_path)


# Test Suite 2: Dynamic Threshold Calculation
class TestDynamicThresholds:
    """Test get_required_improvement() method."""

    def test_probation_period_threshold(self, test_config_file):
        """Test higher threshold during probation period."""
        manager = AntiChurnManager(config_path=test_config_file)

        # Champion at iteration 5, now at iteration 6 (within probation)
        threshold = manager.get_required_improvement(
            current_iteration=6,
            champion_iteration=5
        )

        assert threshold == 0.10, "Should use probation threshold"

    def test_post_probation_threshold(self, test_config_file):
        """Test lower threshold after probation period."""
        manager = AntiChurnManager(config_path=test_config_file)

        # Champion at iteration 5, now at iteration 10 (after probation)
        threshold = manager.get_required_improvement(
            current_iteration=10,
            champion_iteration=5
        )

        assert threshold == 0.05, "Should use post-probation threshold"

    def test_boundary_condition(self, test_config_file):
        """Test threshold at exact probation boundary."""
        manager = AntiChurnManager(config_path=test_config_file)

        # Champion at iteration 5, now at iteration 7 (exactly 2 iterations)
        threshold = manager.get_required_improvement(
            current_iteration=7,
            champion_iteration=5
        )

        assert threshold == 0.10, "Should still use probation threshold at boundary"

        # Champion at iteration 5, now at iteration 8 (3 iterations = post-probation)
        threshold = manager.get_required_improvement(
            current_iteration=8,
            champion_iteration=5
        )

        assert threshold == 0.05, "Should use post-probation threshold after boundary"


# Test Suite 3: Champion Update Tracking
class TestUpdateTracking:
    """Test track_champion_update() method."""

    def test_track_successful_update(self, test_config_file):
        """Test tracking successful champion update."""
        manager = AntiChurnManager(config_path=test_config_file)

        manager.track_champion_update(
            iteration_num=5,
            was_updated=True,
            old_sharpe=1.2,
            new_sharpe=1.35,
            threshold_used=0.10
        )

        assert len(manager.champion_updates) == 1
        record = manager.champion_updates[0]

        assert record.iteration_num == 5
        assert record.was_updated is True
        assert record.old_sharpe == 1.2
        assert record.new_sharpe == 1.35
        assert record.threshold_used == 0.10
        assert record.improvement_pct is not None
        assert abs(record.improvement_pct - 12.5) < 0.1  # (1.35/1.2 - 1) * 100 ≈ 12.5%

    def test_track_failed_update(self, test_config_file):
        """Test tracking failed champion update attempt."""
        manager = AntiChurnManager(config_path=test_config_file)

        manager.track_champion_update(
            iteration_num=6,
            was_updated=False
        )

        assert len(manager.champion_updates) == 1
        record = manager.champion_updates[0]

        assert record.iteration_num == 6
        assert record.was_updated is False
        assert record.old_sharpe is None
        assert record.new_sharpe is None
        assert record.improvement_pct is None

    def test_track_multiple_updates(self, test_config_file):
        """Test tracking multiple champion updates."""
        manager = AntiChurnManager(config_path=test_config_file)

        manager.track_champion_update(0, True, None, 1.2, 0.10)
        manager.track_champion_update(1, False)
        manager.track_champion_update(2, False)
        manager.track_champion_update(3, True, 1.2, 1.35, 0.10)

        assert len(manager.champion_updates) == 4
        assert sum(1 for r in manager.champion_updates if r.was_updated) == 2


# Test Suite 4: Update Frequency Analysis
class TestFrequencyAnalysis:
    """Test analyze_update_frequency() method."""

    def test_frequency_within_target(self, test_config_file):
        """Test frequency analysis when within target range (10-20%)."""
        manager = AntiChurnManager(config_path=test_config_file)

        # Simulate 15% update rate (within target)
        for i in range(20):
            manager.track_champion_update(i, was_updated=(i % 7 == 0))  # ~14.3% update rate

        frequency, recommendations = manager.analyze_update_frequency(window=20)

        assert 0.10 <= frequency <= 0.20, "Frequency should be in target range"
        assert any('healthy' in rec.lower() for rec in recommendations)

    def test_excessive_churn_detection(self, test_config_file):
        """Test detection of excessive champion churn (>20%)."""
        manager = AntiChurnManager(config_path=test_config_file)

        # Simulate 30% update rate (excessive churn)
        for i in range(20):
            manager.track_champion_update(i, was_updated=(i % 3 == 0))  # ~33% update rate

        frequency, recommendations = manager.analyze_update_frequency(window=20)

        assert frequency > 0.20, "Should detect excessive churn"
        assert any('excessive' in rec.lower() for rec in recommendations)
        assert any('increasing' in rec.lower() for rec in recommendations)

    def test_stagnation_detection(self, test_config_file):
        """Test detection of champion stagnation (<10%)."""
        manager = AntiChurnManager(config_path=test_config_file)

        # Simulate 5% update rate (stagnation)
        for i in range(20):
            manager.track_champion_update(i, was_updated=(i == 0))  # Only 1 update = 5%

        frequency, recommendations = manager.analyze_update_frequency(window=20)

        assert frequency < 0.10, "Should detect stagnation"
        assert any('stagnation' in rec.lower() for rec in recommendations)
        assert any('decreasing' in rec.lower() for rec in recommendations)

    def test_no_updates_recorded(self, test_config_file):
        """Test frequency analysis with no updates recorded."""
        manager = AntiChurnManager(config_path=test_config_file)

        frequency, recommendations = manager.analyze_update_frequency()

        assert frequency == 0.0
        assert any('no champion updates' in rec.lower() for rec in recommendations)

    def test_windowed_analysis(self, test_config_file):
        """Test frequency analysis with custom window size."""
        manager = AntiChurnManager(config_path=test_config_file)

        # Simulate varying update rates over time
        # First 30 iterations: high churn (30%)
        for i in range(30):
            manager.track_champion_update(i, was_updated=(i % 3 == 0))

        # Next 20 iterations: low churn (5%)
        for i in range(30, 50):
            manager.track_champion_update(i, was_updated=(i == 30))

        # Analyze recent window (20 iterations) should show low churn
        frequency, _ = manager.analyze_update_frequency(window=20)
        assert frequency < 0.10, "Recent window should show stagnation"

        # Analyze full history (50 iterations) should show higher rate
        frequency_full, _ = manager.analyze_update_frequency(window=50)
        assert frequency_full > frequency, "Full history should have higher rate"


# Test Suite 5: Summary Generation
class TestSummaryGeneration:
    """Test get_recent_updates_summary() method."""

    def test_summary_format(self, test_config_file):
        """Test summary string format."""
        manager = AntiChurnManager(config_path=test_config_file)

        manager.track_champion_update(0, True, None, 1.2, 0.10)
        manager.track_champion_update(1, False)
        manager.track_champion_update(2, True, 1.2, 1.35, 0.10)

        summary = manager.get_recent_updates_summary(count=3)

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert 'Recent Champion Updates' in summary
        assert 'Iter 0' in summary
        assert 'Iter 1' in summary
        assert 'Iter 2' in summary
        assert 'Update frequency' in summary

    def test_summary_empty(self, test_config_file):
        """Test summary with no updates."""
        manager = AntiChurnManager(config_path=test_config_file)

        summary = manager.get_recent_updates_summary()

        assert 'No champion updates recorded' in summary

    def test_summary_limited_count(self, test_config_file):
        """Test summary with limited count."""
        manager = AntiChurnManager(config_path=test_config_file)

        # Track 10 updates
        for i in range(10):
            manager.track_champion_update(i, was_updated=(i % 2 == 0))

        summary = manager.get_recent_updates_summary(count=5)

        # Should only show last 5
        assert 'Iter 5' in summary
        assert 'Iter 9' in summary
        assert 'Iter 0' not in summary


# Test Suite 6: Edge Cases
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_zero_old_sharpe(self, test_config_file):
        """Test handling of zero old_sharpe in improvement calculation."""
        manager = AntiChurnManager(config_path=test_config_file)

        manager.track_champion_update(
            iteration_num=5,
            was_updated=True,
            old_sharpe=0.0,  # Zero sharpe
            new_sharpe=1.2,
            threshold_used=0.10
        )

        record = manager.champion_updates[0]
        # Should handle gracefully (no division by zero)
        assert record.improvement_pct is None

    def test_negative_iteration_delta(self, test_config_file):
        """Test handling of negative iteration delta (edge case)."""
        manager = AntiChurnManager(config_path=test_config_file)

        # Shouldn't happen in practice, but test defensive programming
        threshold = manager.get_required_improvement(
            current_iteration=3,
            champion_iteration=5  # Champion in the future?
        )

        # Should still return a valid threshold (using probation threshold)
        assert threshold == 0.10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
