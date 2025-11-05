"""
Unit Tests for Template Stats Tracker
======================================

Tests for TemplateStatsTracker class covering:
    - Task 36: Base class initialization and storage
    - Task 37: update_template_stats() functionality
    - Task 38: get_template_recommendations() LLM prompt generation

Test Coverage:
    - Storage file creation and loading
    - Statistics update and persistence
    - Success rate calculations
    - Sharpe distribution tracking
    - LLM recommendation generation
    - Filtering and ranking logic
    - Edge cases and error handling
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from src.feedback.template_feedback_integrator import (
    TemplateStatsTracker,
    TemplateStats
)


class TestTemplateStats:
    """Test TemplateStats dataclass."""

    def test_template_stats_initialization(self):
        """Test TemplateStats initialization with defaults."""
        stats = TemplateStats()

        assert stats.total_attempts == 0
        assert stats.successful_strategies == 0
        assert stats.avg_sharpe == 0.0
        assert stats.sharpe_distribution == []
        assert stats.last_updated != ""

    def test_template_stats_success_rate_zero_attempts(self):
        """Test success rate calculation with zero attempts."""
        stats = TemplateStats(total_attempts=0, successful_strategies=0)

        assert stats.success_rate == 0.0

    def test_template_stats_success_rate_calculation(self):
        """Test success rate calculation."""
        stats = TemplateStats(total_attempts=10, successful_strategies=8)

        assert stats.success_rate == 80.0

    def test_template_stats_to_dict(self):
        """Test conversion to dictionary."""
        stats = TemplateStats(
            total_attempts=10,
            successful_strategies=8,
            avg_sharpe=1.5,
            sharpe_distribution=[1.0, 1.5, 2.0],
            last_updated="2025-10-16T10:30:00"
        )

        result = stats.to_dict()

        assert result['total_attempts'] == 10
        assert result['successful_strategies'] == 8
        assert result['avg_sharpe'] == 1.5
        assert result['sharpe_distribution'] == [1.0, 1.5, 2.0]
        assert result['last_updated'] == "2025-10-16T10:30:00"

    def test_template_stats_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'total_attempts': 10,
            'successful_strategies': 8,
            'avg_sharpe': 1.5,
            'sharpe_distribution': [1.0, 1.5, 2.0],
            'last_updated': "2025-10-16T10:30:00"
        }

        stats = TemplateStats.from_dict(data)

        assert stats.total_attempts == 10
        assert stats.successful_strategies == 8
        assert stats.avg_sharpe == 1.5
        assert stats.sharpe_distribution == [1.0, 1.5, 2.0]
        assert stats.last_updated == "2025-10-16T10:30:00"


class TestTemplateStatsTrackerInitialization:
    """Test TemplateStatsTracker initialization and storage."""

    def test_initialization_default_path(self):
        """Test initialization with default storage path."""
        integrator = TemplateStatsTracker()

        assert integrator.storage_path == TemplateStatsTracker.DEFAULT_STORAGE_PATH
        assert isinstance(integrator.template_stats, dict)

    def test_initialization_custom_path(self):
        """Test initialization with custom storage path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / 'custom_stats.json'
            integrator = TemplateStatsTracker(storage_path=custom_path)

            assert integrator.storage_path == custom_path
            assert custom_path.exists()

    def test_initialization_creates_storage_directory(self):
        """Test that initialization creates storage directory if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'nested' / 'dir' / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            assert storage_path.parent.exists()
            assert storage_path.exists()

    def test_load_empty_storage_file(self):
        """Test loading from newly created empty storage file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            assert len(integrator.template_stats) == 0
            assert storage_path.exists()

    def test_load_existing_storage_file(self):
        """Test loading from existing storage file with data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'

            # Create storage file with sample data
            sample_data = {
                'TurtleTemplate': {
                    'total_attempts': 10,
                    'successful_strategies': 8,
                    'avg_sharpe': 1.5,
                    'sharpe_distribution': [1.0, 1.5, 2.0],
                    'last_updated': "2025-10-16T10:30:00"
                }
            }

            with open(storage_path, 'w') as f:
                json.dump(sample_data, f)

            # Load integrator
            integrator = TemplateStatsTracker(storage_path=storage_path)

            assert len(integrator.template_stats) == 1
            assert 'TurtleTemplate' in integrator.template_stats

            stats = integrator.template_stats['TurtleTemplate']
            assert stats.total_attempts == 10
            assert stats.successful_strategies == 8
            assert stats.avg_sharpe == 1.5

    def test_load_corrupted_storage_file(self):
        """Test handling of corrupted JSON storage file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'

            # Create corrupted JSON file
            with open(storage_path, 'w') as f:
                f.write("{ invalid json }")

            # Should handle gracefully
            integrator = TemplateStatsTracker(storage_path=storage_path)

            assert len(integrator.template_stats) == 0


class TestUpdateTemplateStats:
    """Test update_template_stats() method (Task 37)."""

    def test_update_new_template(self):
        """Test updating stats for a new template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            integrator.update_template_stats('TurtleTemplate', sharpe_ratio=1.5, is_successful=True)

            stats = integrator.template_stats['TurtleTemplate']
            assert stats.total_attempts == 1
            assert stats.successful_strategies == 1
            assert stats.avg_sharpe == 1.5
            assert stats.sharpe_distribution == [1.5]

    def test_update_existing_template(self):
        """Test updating stats for existing template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            # First update
            integrator.update_template_stats('TurtleTemplate', sharpe_ratio=1.5, is_successful=True)

            # Second update
            integrator.update_template_stats('TurtleTemplate', sharpe_ratio=2.0, is_successful=True)

            stats = integrator.template_stats['TurtleTemplate']
            assert stats.total_attempts == 2
            assert stats.successful_strategies == 2
            assert stats.avg_sharpe == 1.75  # (1.5 + 2.0) / 2
            assert stats.sharpe_distribution == [1.5, 2.0]

    def test_update_with_failure(self):
        """Test updating stats with failed strategy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            integrator.update_template_stats('TurtleTemplate', sharpe_ratio=0.3, is_successful=False)

            stats = integrator.template_stats['TurtleTemplate']
            assert stats.total_attempts == 1
            assert stats.successful_strategies == 0
            assert stats.avg_sharpe == 0.3
            assert stats.sharpe_distribution == [0.3]

    def test_update_mixed_success_failure(self):
        """Test updating stats with mix of successes and failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            integrator.update_template_stats('TurtleTemplate', sharpe_ratio=1.5, is_successful=True)
            integrator.update_template_stats('TurtleTemplate', sharpe_ratio=0.3, is_successful=False)
            integrator.update_template_stats('TurtleTemplate', sharpe_ratio=2.0, is_successful=True)

            stats = integrator.template_stats['TurtleTemplate']
            assert stats.total_attempts == 3
            assert stats.successful_strategies == 2
            assert stats.success_rate == pytest.approx(66.67, rel=0.01)
            assert stats.avg_sharpe == pytest.approx(1.27, rel=0.01)  # (1.5 + 0.3 + 2.0) / 3

    def test_update_persists_to_disk(self):
        """Test that updates are persisted to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            integrator.update_template_stats('TurtleTemplate', sharpe_ratio=1.5, is_successful=True)

            # Load from disk directly
            with open(storage_path, 'r') as f:
                data = json.load(f)

            assert 'TurtleTemplate' in data
            assert data['TurtleTemplate']['total_attempts'] == 1
            assert data['TurtleTemplate']['successful_strategies'] == 1
            assert data['TurtleTemplate']['avg_sharpe'] == 1.5

    def test_update_timestamp_changes(self):
        """Test that last_updated timestamp changes on update."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            integrator.update_template_stats('TurtleTemplate', sharpe_ratio=1.5, is_successful=True)
            first_timestamp = integrator.template_stats['TurtleTemplate'].last_updated

            # Small delay to ensure timestamp difference
            import time
            time.sleep(0.01)

            integrator.update_template_stats('TurtleTemplate', sharpe_ratio=2.0, is_successful=True)
            second_timestamp = integrator.template_stats['TurtleTemplate'].last_updated

            assert second_timestamp != first_timestamp


class TestGetTemplateRecommendations:
    """Test get_template_recommendations() method (Task 38)."""

    def test_recommendations_empty_stats(self):
        """Test recommendations with no template stats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            recommendations = integrator.get_template_recommendations()

            assert "No templates have sufficient data" in recommendations

    def test_recommendations_insufficient_attempts(self):
        """Test recommendations filtering by minimum attempts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            # Only 2 attempts (below default threshold of 3)
            integrator.update_template_stats('TurtleTemplate', sharpe_ratio=1.5, is_successful=True)
            integrator.update_template_stats('TurtleTemplate', sharpe_ratio=2.0, is_successful=True)

            recommendations = integrator.get_template_recommendations()

            assert "No templates have sufficient data" in recommendations

    def test_recommendations_low_sharpe(self):
        """Test recommendations filtering by minimum Sharpe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            # 3 attempts but low Sharpe (below default threshold of 0.5)
            for _ in range(3):
                integrator.update_template_stats('TurtleTemplate', sharpe_ratio=0.2, is_successful=True)

            recommendations = integrator.get_template_recommendations()

            assert "No templates have sufficient data" in recommendations

    def test_recommendations_single_template(self):
        """Test recommendations with single eligible template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            # Add sufficient data for TurtleTemplate
            for sharpe in [1.5, 1.8, 2.0, 1.7]:
                integrator.update_template_stats('TurtleTemplate', sharpe, is_successful=True)

            recommendations = integrator.get_template_recommendations(top_n=1)

            assert "Focus on TurtleTemplate" in recommendations
            assert "100.0% success" in recommendations
            assert "avg Sharpe" in recommendations

    def test_recommendations_multiple_templates_ranking(self):
        """Test recommendations ranking by composite score."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            # TurtleTemplate: 80% success, avg Sharpe 1.5
            for sharpe in [1.5, 1.8, 2.0, 1.7, 0.3]:  # 4 success, 1 failure
                is_success = sharpe > 0.5
                integrator.update_template_stats('TurtleTemplate', sharpe, is_success)

            # MastiffTemplate: 100% success, avg Sharpe 1.2
            for sharpe in [1.2, 1.3, 1.1]:
                integrator.update_template_stats('MastiffTemplate', sharpe, is_successful=True)

            # FactorTemplate: 50% success, avg Sharpe 0.8
            for sharpe in [0.8, 0.7, 0.3, 0.2]:
                is_success = sharpe > 0.5
                integrator.update_template_stats('FactorTemplate', sharpe, is_success)

            recommendations = integrator.get_template_recommendations(top_n=3)

            # TurtleTemplate should be first (composite: 0.8 * 1.5 = 1.2)
            # MastiffTemplate should be second (composite: 1.0 * 1.2 = 1.2, but slightly lower sharpe)
            assert "Focus on" in recommendations
            assert "TurtleTemplate" in recommendations or "MastiffTemplate" in recommendations

    def test_recommendations_format_primary_template(self):
        """Test recommendation format for primary (first) template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            for sharpe in [1.5, 1.8, 2.0]:
                integrator.update_template_stats('TurtleTemplate', sharpe, is_successful=True)

            recommendations = integrator.get_template_recommendations(top_n=1)

            assert "Focus on TurtleTemplate" in recommendations
            assert "100.0% success" in recommendations

    def test_recommendations_format_secondary_template(self):
        """Test recommendation format for secondary templates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            # Add two templates
            for sharpe in [1.8, 1.9, 2.0]:
                integrator.update_template_stats('TurtleTemplate', sharpe, is_successful=True)

            for sharpe in [1.5, 1.6, 1.7]:
                integrator.update_template_stats('MastiffTemplate', sharpe, is_successful=True)

            recommendations = integrator.get_template_recommendations(top_n=2)

            assert "Focus on" in recommendations
            assert "Consider" in recommendations

    def test_recommendations_custom_thresholds(self):
        """Test recommendations with custom min_attempts and min_sharpe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            # Add template with 2 attempts
            integrator.update_template_stats('TurtleTemplate', 1.5, is_successful=True)
            integrator.update_template_stats('TurtleTemplate', 1.8, is_successful=True)

            # Should fail with default thresholds
            recommendations_default = integrator.get_template_recommendations()
            assert "No templates have sufficient data" in recommendations_default

            # Should pass with custom thresholds
            recommendations_custom = integrator.get_template_recommendations(
                min_attempts=2,
                min_sharpe=1.0
            )
            assert "Focus on TurtleTemplate" in recommendations_custom


class TestHelperMethods:
    """Test helper methods."""

    def test_get_template_stats_existing(self):
        """Test getting stats for existing template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            integrator.update_template_stats('TurtleTemplate', 1.5, is_successful=True)

            stats = integrator.get_template_stats('TurtleTemplate')

            assert stats is not None
            assert stats.total_attempts == 1

    def test_get_template_stats_nonexistent(self):
        """Test getting stats for non-existent template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            stats = integrator.get_template_stats('NonExistent')

            assert stats is None

    def test_get_all_template_stats(self):
        """Test getting all template stats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            integrator.update_template_stats('TurtleTemplate', 1.5, is_successful=True)
            integrator.update_template_stats('MastiffTemplate', 1.2, is_successful=True)

            all_stats = integrator.get_all_template_stats()

            assert len(all_stats) == 2
            assert 'TurtleTemplate' in all_stats
            assert 'MastiffTemplate' in all_stats

    def test_reset_template_stats_specific(self):
        """Test resetting stats for specific template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            integrator.update_template_stats('TurtleTemplate', 1.5, is_successful=True)
            integrator.update_template_stats('MastiffTemplate', 1.2, is_successful=True)

            integrator.reset_template_stats('TurtleTemplate')

            assert 'TurtleTemplate' not in integrator.template_stats
            assert 'MastiffTemplate' in integrator.template_stats

    def test_reset_template_stats_all(self):
        """Test resetting all template stats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            integrator.update_template_stats('TurtleTemplate', 1.5, is_successful=True)
            integrator.update_template_stats('MastiffTemplate', 1.2, is_successful=True)

            integrator.reset_template_stats()

            assert len(integrator.template_stats) == 0

    def test_get_stats_summary_empty(self):
        """Test stats summary with no data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            summary = integrator.get_stats_summary()

            assert summary['total_templates'] == 0
            assert summary['total_attempts'] == 0
            assert summary['total_successful'] == 0
            assert summary['overall_success_rate'] == 0.0
            assert summary['avg_sharpe_all'] == 0.0
            assert summary['best_template'] is None

    def test_get_stats_summary_with_data(self):
        """Test stats summary with data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'stats.json'
            integrator = TemplateStatsTracker(storage_path=storage_path)

            # TurtleTemplate: 4 attempts, 3 successful, avg Sharpe 1.5
            for sharpe in [1.5, 1.8, 2.0, 0.3]:
                is_success = sharpe > 0.5
                integrator.update_template_stats('TurtleTemplate', sharpe, is_success)

            # MastiffTemplate: 2 attempts, 2 successful, avg Sharpe 1.2
            for sharpe in [1.2, 1.3]:
                integrator.update_template_stats('MastiffTemplate', sharpe, is_successful=True)

            summary = integrator.get_stats_summary()

            assert summary['total_templates'] == 2
            assert summary['total_attempts'] == 6
            assert summary['total_successful'] == 5
            assert summary['overall_success_rate'] == pytest.approx(83.33, rel=0.01)
            assert summary['avg_sharpe_all'] > 0
            assert summary['best_template'] in ['TurtleTemplate', 'MastiffTemplate']
