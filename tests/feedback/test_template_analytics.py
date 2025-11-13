"""
Unit Tests for TemplateAnalytics
=================================

Unit tests for the template usage tracking and analytics system.

Test Coverage:
    - Template usage recording
    - Success rate calculation
    - Statistical aggregation
    - Trend analysis
    - JSON persistence (load/save)
    - Best template identification
    - Report generation

Components Tested:
    - TemplateAnalytics.record_template_usage()
    - TemplateAnalytics.get_template_statistics()
    - TemplateAnalytics.get_all_templates_summary()
    - TemplateAnalytics.get_usage_trend()
    - TemplateAnalytics.get_best_performing_template()
    - TemplateAnalytics.export_report()
    - TemplateAnalytics._load_from_storage()
    - TemplateAnalytics._save_to_storage()
"""

import pytest
import json
from pathlib import Path
from src.feedback.template_analytics import (
    TemplateAnalytics,
    TemplateUsageRecord
)


class TestTemplateUsageRecord:
    """Unit tests for TemplateUsageRecord dataclass."""

    def test_create_basic_record(self):
        """Test: Create basic usage record."""
        record = TemplateUsageRecord(
            iteration=1,
            timestamp='2025-01-01T12:00:00',
            template_name='TurtleTemplate'
        )

        assert record.iteration == 1
        assert record.template_name == 'TurtleTemplate'
        assert record.sharpe_ratio == 0.0  # Default
        assert record.validation_passed is False  # Default

    def test_create_full_record(self):
        """Test: Create full usage record with all fields."""
        record = TemplateUsageRecord(
            iteration=5,
            timestamp='2025-01-01T12:00:00',
            template_name='MastiffTemplate',
            sharpe_ratio=1.8,
            validation_passed=True,
            exploration_mode=True,
            champion_based=True,
            match_score=0.85
        )

        assert record.iteration == 5
        assert record.sharpe_ratio == 1.8
        assert record.validation_passed is True
        assert record.exploration_mode is True
        assert record.champion_based is True
        assert record.match_score == 0.85

    def test_record_to_dict(self):
        """Test: Convert record to dictionary."""
        record = TemplateUsageRecord(
            iteration=3,
            timestamp='2025-01-01T12:00:00',
            template_name='FactorTemplate',
            sharpe_ratio=1.5
        )

        data = record.to_dict()

        assert isinstance(data, dict)
        assert data['iteration'] == 3
        assert data['template_name'] == 'FactorTemplate'
        assert data['sharpe_ratio'] == 1.5


class TestTemplateAnalytics:
    """Unit tests for TemplateAnalytics."""

    @pytest.fixture
    def analytics(self, tmp_path):
        """Create TemplateAnalytics with temporary storage."""
        storage_file = tmp_path / "test_analytics.json"
        return TemplateAnalytics(storage_path=str(storage_file))

    @pytest.fixture
    def storage_path(self, tmp_path):
        """Return temporary storage path."""
        return tmp_path / "test_analytics.json"

    # Initialization Tests
    def test_init_creates_empty_storage(self, analytics):
        """Test: Initialization creates empty usage records."""
        assert len(analytics.usage_records) == 0

    def test_init_with_nonexistent_file(self, tmp_path):
        """Test: Initialization with non-existent storage file."""
        storage_file = tmp_path / "nonexistent.json"
        analytics = TemplateAnalytics(storage_path=str(storage_file))

        assert len(analytics.usage_records) == 0

    def test_init_loads_existing_file(self, tmp_path):
        """Test: Initialization loads existing storage file."""
        storage_file = tmp_path / "existing.json"

        # Create existing file with data
        data = [
            {
                'iteration': 1,
                'timestamp': '2025-01-01T12:00:00',
                'template_name': 'TurtleTemplate',
                'sharpe_ratio': 1.5,
                'validation_passed': True,
                'exploration_mode': False,
                'champion_based': False,
                'match_score': 0.80
            }
        ]

        with storage_file.open('w') as f:
            json.dump(data, f)

        # Load from existing file
        analytics = TemplateAnalytics(storage_path=str(storage_file))

        assert len(analytics.usage_records) == 1
        assert analytics.usage_records[0].template_name == 'TurtleTemplate'
        assert analytics.usage_records[0].sharpe_ratio == 1.5

    # Recording Tests
    def test_record_template_usage_basic(self, analytics, storage_path):
        """Test: Record basic template usage."""
        analytics.record_template_usage(
            iteration=1,
            template_name='TurtleTemplate'
        )

        assert len(analytics.usage_records) == 1
        assert analytics.usage_records[0].template_name == 'TurtleTemplate'
        assert analytics.usage_records[0].iteration == 1

        # Should save to storage
        assert storage_path.exists()

    def test_record_template_usage_full(self, analytics):
        """Test: Record full template usage with all fields."""
        analytics.record_template_usage(
            iteration=5,
            template_name='MastiffTemplate',
            sharpe_ratio=1.8,
            validation_passed=True,
            exploration_mode=True,
            champion_based=True,
            match_score=0.85
        )

        record = analytics.usage_records[0]
        assert record.template_name == 'MastiffTemplate'
        assert record.sharpe_ratio == 1.8
        assert record.validation_passed is True
        assert record.exploration_mode is True
        assert record.champion_based is True
        assert record.match_score == 0.85

    def test_record_multiple_usages(self, analytics):
        """Test: Record multiple template usages."""
        for i in range(5):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                sharpe_ratio=1.0 + (i * 0.1)
            )

        assert len(analytics.usage_records) == 5

    # Statistics Tests
    def test_get_template_statistics_no_data(self, analytics):
        """Test: Get statistics for template with no data."""
        stats = analytics.get_template_statistics('TurtleTemplate')

        assert stats['total_usage'] == 0
        assert stats['success_rate'] == 0.0
        assert stats['avg_sharpe'] == 0.0
        assert stats['has_data'] is False

    def test_get_template_statistics_single_record(self, analytics):
        """Test: Get statistics for single record."""
        analytics.record_template_usage(
            iteration=1,
            template_name='TurtleTemplate',
            sharpe_ratio=1.5,
            validation_passed=True
        )

        stats = analytics.get_template_statistics('TurtleTemplate')

        assert stats['total_usage'] == 1
        assert stats['avg_sharpe'] == 1.5
        assert stats['best_sharpe'] == 1.5
        assert stats['worst_sharpe'] == 1.5
        assert stats['has_data'] is True

    def test_get_template_statistics_success_rate_calculation(self, analytics):
        """Test: Success rate calculation (validation + Sharpe ≥1.0)."""
        # 5 successful: validation passed AND Sharpe ≥1.0
        for i in range(5):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                sharpe_ratio=1.2,
                validation_passed=True
            )

        # 3 failed: validation failed OR Sharpe <1.0
        for i in range(5, 8):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                sharpe_ratio=0.8,
                validation_passed=False
            )

        stats = analytics.get_template_statistics('TurtleTemplate')

        assert stats['total_usage'] == 8
        assert stats['success_rate'] == 0.625  # 5/8 = 0.625

    def test_get_template_statistics_sharpe_aggregation(self, analytics):
        """Test: Sharpe ratio aggregation (avg, best, worst)."""
        sharpe_values = [1.0, 1.5, 2.0, 0.5, 1.2]

        for i, sharpe in enumerate(sharpe_values):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                sharpe_ratio=sharpe
            )

        stats = analytics.get_template_statistics('TurtleTemplate')

        assert stats['avg_sharpe'] == 1.24  # (1.0 + 1.5 + 2.0 + 0.5 + 1.2) / 5
        assert stats['best_sharpe'] == 2.0
        assert stats['worst_sharpe'] == 0.5

    def test_get_template_statistics_validation_pass_rate(self, analytics):
        """Test: Validation pass rate calculation."""
        # 7 passed, 3 failed
        for i in range(7):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                validation_passed=True
            )

        for i in range(7, 10):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                validation_passed=False
            )

        stats = analytics.get_template_statistics('TurtleTemplate')

        assert stats['validation_pass_rate'] == 0.7  # 7/10

    def test_get_template_statistics_exploration_tracking(self, analytics):
        """Test: Exploration mode usage tracking."""
        # 3 exploration, 7 normal
        for i in range(3):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                exploration_mode=True
            )

        for i in range(3, 10):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                exploration_mode=False
            )

        stats = analytics.get_template_statistics('TurtleTemplate')

        assert stats['exploration_usage'] == 3
        assert stats['total_usage'] == 10

    def test_get_template_statistics_champion_tracking(self, analytics):
        """Test: Champion-based usage tracking."""
        # 5 champion-based, 5 not
        for i in range(5):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                champion_based=True
            )

        for i in range(5, 10):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                champion_based=False
            )

        stats = analytics.get_template_statistics('TurtleTemplate')

        assert stats['champion_usage'] == 5
        assert stats['total_usage'] == 10

    def test_get_template_statistics_reliable_stats_threshold(self, analytics):
        """Test: Reliable stats flag (≥3 records)."""
        # Less than 3 records
        analytics.record_template_usage(
            iteration=1,
            template_name='TurtleTemplate'
        )
        analytics.record_template_usage(
            iteration=2,
            template_name='TurtleTemplate'
        )

        stats = analytics.get_template_statistics('TurtleTemplate')
        assert stats['reliable_stats'] is False

        # Exactly 3 records
        analytics.record_template_usage(
            iteration=3,
            template_name='TurtleTemplate'
        )

        stats = analytics.get_template_statistics('TurtleTemplate')
        assert stats['reliable_stats'] is True

    # Summary Tests
    def test_get_all_templates_summary_empty(self, analytics):
        """Test: Get summary with no data."""
        summary = analytics.get_all_templates_summary()

        assert isinstance(summary, dict)
        assert len(summary) == 0

    def test_get_all_templates_summary_multiple_templates(self, analytics):
        """Test: Get summary for multiple templates."""
        # Record usage for 3 templates
        analytics.record_template_usage(iteration=1, template_name='TurtleTemplate')
        analytics.record_template_usage(iteration=2, template_name='MastiffTemplate')
        analytics.record_template_usage(iteration=3, template_name='FactorTemplate')

        summary = analytics.get_all_templates_summary()

        assert len(summary) == 3
        assert 'TurtleTemplate' in summary
        assert 'MastiffTemplate' in summary
        assert 'FactorTemplate' in summary

    # Trend Tests
    def test_get_usage_trend_all_templates(self, analytics):
        """Test: Get usage trend for all templates."""
        for i in range(10):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                sharpe_ratio=1.0 + (i * 0.1)
            )

        trend = analytics.get_usage_trend(last_n_iterations=5)

        assert len(trend) == 5
        # Should be most recent first
        assert trend[0]['iteration'] == 10
        assert trend[4]['iteration'] == 6

    def test_get_usage_trend_specific_template(self, analytics):
        """Test: Get usage trend for specific template."""
        # Record for two templates
        for i in range(5):
            analytics.record_template_usage(iteration=i + 1, template_name='TurtleTemplate')
            analytics.record_template_usage(iteration=i + 6, template_name='MastiffTemplate')

        trend = analytics.get_usage_trend(template_name='TurtleTemplate', last_n_iterations=3)

        assert len(trend) == 3
        # All should be TurtleTemplate
        assert all(t['template_name'] == 'TurtleTemplate' for t in trend)

    # Best Template Tests
    def test_get_best_performing_template_no_data(self, analytics):
        """Test: Get best template with no data."""
        best = analytics.get_best_performing_template()

        assert best is None

    def test_get_best_performing_template_insufficient_data(self, analytics):
        """Test: Get best template with <3 records (unreliable)."""
        analytics.record_template_usage(iteration=1, template_name='TurtleTemplate')
        analytics.record_template_usage(iteration=2, template_name='TurtleTemplate')

        best = analytics.get_best_performing_template()

        assert best is None  # Not enough data

    def test_get_best_performing_template_by_success_rate(self, analytics):
        """Test: Best template selected by success rate."""
        # TurtleTemplate: 100% success rate (5/5)
        for i in range(5):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                sharpe_ratio=1.5,
                validation_passed=True
            )

        # MastiffTemplate: 60% success rate (3/5)
        for i in range(5, 10):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='MastiffTemplate',
                sharpe_ratio=1.2 if i < 8 else 0.8,
                validation_passed=i < 8
            )

        best = analytics.get_best_performing_template()

        assert best == 'TurtleTemplate'

    def test_get_best_performing_template_tiebreaker_avg_sharpe(self, analytics):
        """Test: Tiebreaker uses avg Sharpe ratio."""
        # Both templates: 100% success rate, but different Sharpe
        # TurtleTemplate: avg Sharpe = 2.0
        for i in range(5):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                sharpe_ratio=2.0,
                validation_passed=True
            )

        # MastiffTemplate: avg Sharpe = 1.5
        for i in range(5, 10):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='MastiffTemplate',
                sharpe_ratio=1.5,
                validation_passed=True
            )

        best = analytics.get_best_performing_template()

        assert best == 'TurtleTemplate'

    # Persistence Tests
    def test_save_to_storage(self, analytics, storage_path):
        """Test: Data is saved to storage file."""
        analytics.record_template_usage(
            iteration=1,
            template_name='TurtleTemplate',
            sharpe_ratio=1.5
        )

        # Storage file should exist
        assert storage_path.exists()

        # Load and verify content
        with storage_path.open('r') as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]['template_name'] == 'TurtleTemplate'
        assert data[0]['sharpe_ratio'] == 1.5

    def test_load_from_storage(self, tmp_path):
        """Test: Data is loaded from storage file."""
        storage_file = tmp_path / "load_test.json"

        # Create initial data
        analytics1 = TemplateAnalytics(storage_path=str(storage_file))
        analytics1.record_template_usage(
            iteration=1,
            template_name='TurtleTemplate',
            sharpe_ratio=1.8
        )

        # Create new instance - should load existing data
        analytics2 = TemplateAnalytics(storage_path=str(storage_file))

        assert len(analytics2.usage_records) == 1
        assert analytics2.usage_records[0].template_name == 'TurtleTemplate'
        assert analytics2.usage_records[0].sharpe_ratio == 1.8

    def test_persistence_across_multiple_sessions(self, tmp_path):
        """Test: Data persists across multiple sessions."""
        storage_file = tmp_path / "multi_session.json"

        # Session 1
        analytics1 = TemplateAnalytics(storage_path=str(storage_file))
        analytics1.record_template_usage(iteration=1, template_name='TurtleTemplate')

        # Session 2
        analytics2 = TemplateAnalytics(storage_path=str(storage_file))
        analytics2.record_template_usage(iteration=2, template_name='MastiffTemplate')

        # Session 3 - should have data from both previous sessions
        analytics3 = TemplateAnalytics(storage_path=str(storage_file))

        assert len(analytics3.usage_records) == 2

    # Report Export Tests
    def test_export_report(self, analytics, tmp_path):
        """Test: Export comprehensive analytics report."""
        # Record some data
        for i in range(5):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                sharpe_ratio=1.5,
                validation_passed=True
            )

        report_file = tmp_path / "report.json"
        analytics.export_report(output_path=str(report_file))

        # Verify report file created
        assert report_file.exists()

        # Load and verify report structure
        with report_file.open('r') as f:
            report = json.load(f)

        assert 'generated_at' in report
        assert 'total_records' in report
        assert 'template_summary' in report
        assert 'best_template' in report
        assert 'recent_usage' in report

        assert report['total_records'] == 5
        assert report['best_template'] == 'TurtleTemplate'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
