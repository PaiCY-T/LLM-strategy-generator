"""
Tests for 50-generation three-tier validation infrastructure.

Tests the metrics tracker, report generator, and validation harness
components to ensure they work correctly for validation runs.

Architecture: Structural Mutation Phase 2 - Phase D.6
Task: D.6 - 50-Generation Three-Tier Validation
"""

import pytest
import tempfile
import os
import json
from datetime import datetime
from typing import Dict, Any, List

from src.validation.three_tier_metrics_tracker import (
    ThreeTierMetricsTracker,
    GenerationMetrics,
    TierEffectiveness,
    BreakthroughStrategy
)
from src.validation.validation_report_generator import ValidationReportGenerator


class MockStrategy:
    """Mock strategy for testing."""

    def __init__(self, strategy_id: str):
        self.strategy_id = strategy_id

    def __str__(self):
        return self.strategy_id


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample validation configuration."""
    return {
        "name": "Test Validation",
        "population": {
            "size": 20,
            "generations": 50
        },
        "validation": {
            "checkpoint_interval": 10,
            "target_tier_distribution": {
                "tier1": 0.30,
                "tier2": 0.50,
                "tier3": 0.20
            },
            "performance_targets": {
                "min_best_sharpe": 1.8
            }
        }
    }


@pytest.fixture
def tracker() -> ThreeTierMetricsTracker:
    """Create fresh metrics tracker."""
    return ThreeTierMetricsTracker()


@pytest.fixture
def populated_tracker() -> ThreeTierMetricsTracker:
    """Create tracker with sample data."""
    tracker = ThreeTierMetricsTracker()
    tracker.start_time = datetime.now().isoformat()

    # Add 10 generations of data
    for gen in range(1, 11):
        population = [MockStrategy(f"strategy_{i}") for i in range(20)]
        fitness_scores = {f"strategy_{i}": 1.0 + (gen * 0.05) + (i * 0.01) for i in range(20)}

        tier_stats = {
            "tier1": 3,
            "tier2": 10,
            "tier3": 2
        }

        tier_success_rates = {
            "tier1": 0.8,
            "tier2": 0.6,
            "tier3": 0.5
        }

        tracker.record_generation(
            generation=gen,
            population=population,
            tier_stats=tier_stats,
            fitness_scores=fitness_scores,
            tier_success_rates=tier_success_rates,
            diversity_score=0.5
        )

    tracker.end_time = datetime.now().isoformat()
    return tracker


class TestThreeTierMetricsTracker:
    """Tests for ThreeTierMetricsTracker."""

    def test_initialization(self, tracker):
        """Test tracker initialization."""
        assert len(tracker.generation_metrics) == 0
        assert tracker.best_sharpe_overall == float('-inf')
        assert tracker.best_strategy_id == ""

    def test_record_generation(self, tracker):
        """Test recording generation metrics."""
        population = [MockStrategy(f"strategy_{i}") for i in range(5)]
        fitness_scores = {"strategy_0": 1.5, "strategy_1": 1.8, "strategy_2": 1.2, "strategy_3": 1.6, "strategy_4": 1.4}
        tier_stats = {"tier1": 2, "tier2": 5, "tier3": 1}

        tracker.record_generation(
            generation=1,
            population=population,
            tier_stats=tier_stats,
            fitness_scores=fitness_scores
        )

        assert len(tracker.generation_metrics) == 1
        metrics = tracker.generation_metrics[0]
        assert metrics.generation == 1
        assert metrics.best_sharpe == 1.8
        assert metrics.tier1_count == 2
        assert metrics.tier2_count == 5
        assert metrics.tier3_count == 1

    def test_get_tier_distribution(self, populated_tracker):
        """Test tier distribution calculation."""
        distribution = populated_tracker.get_tier_distribution()

        assert "tier1" in distribution
        assert "tier2" in distribution
        assert "tier3" in distribution
        assert "total_mutations" in distribution

        # Check percentages sum to ~1.0
        total = distribution["tier1"] + distribution["tier2"] + distribution["tier3"]
        assert 0.99 <= total <= 1.01

        # Check tier 2 is dominant (should be ~10/15 = 0.67)
        assert distribution["tier2"] > 0.5

    def test_get_tier_distribution_empty(self, tracker):
        """Test tier distribution with no data."""
        distribution = tracker.get_tier_distribution()

        assert distribution["tier1"] == 0.0
        assert distribution["tier2"] == 0.0
        assert distribution["tier3"] == 0.0
        assert distribution["total_mutations"] == 0

    def test_get_performance_progression(self, populated_tracker):
        """Test performance progression DataFrame."""
        progression = populated_tracker.get_performance_progression()

        assert len(progression) == 10
        assert "generation" in progression.columns
        assert "best_sharpe" in progression.columns
        assert "improvement" in progression.columns

        # Check monotonic improvement
        assert progression["best_sharpe"].iloc[-1] > progression["best_sharpe"].iloc[0]

    def test_get_tier_effectiveness(self, populated_tracker):
        """Test tier effectiveness calculation."""
        effectiveness = populated_tracker.get_tier_effectiveness()

        assert "tier_1" in effectiveness
        assert "tier_2" in effectiveness
        assert "tier_3" in effectiveness

        # Check tier 2 has highest usage
        tier2 = effectiveness["tier_2"]
        assert tier2.usage_count > 0
        assert 0 <= tier2.success_rate <= 1.0

    def test_detect_breakthroughs(self, populated_tracker):
        """Test breakthrough detection."""
        # No breakthroughs in sample data (max ~2.0)
        breakthroughs = populated_tracker.detect_breakthroughs(threshold=2.5)
        assert len(breakthroughs) == 0

        # Lower threshold should find some
        breakthroughs = populated_tracker.detect_breakthroughs(threshold=1.5)
        assert len(breakthroughs) > 0

    def test_export_report(self, populated_tracker):
        """Test report export to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, "metrics.json")
            populated_tracker.export_report(report_path)

            assert os.path.exists(report_path)

            # Load and validate JSON
            with open(report_path, 'r') as f:
                report = json.load(f)

            assert "metadata" in report
            assert "tier_distribution" in report
            assert "generation_metrics" in report

    def test_get_summary_statistics(self, populated_tracker):
        """Test summary statistics generation."""
        summary = populated_tracker.get_summary_statistics()

        assert "performance_summary" in summary
        assert "tier_summary" in summary
        assert "stability_summary" in summary

        perf = summary["performance_summary"]
        assert "initial_best_sharpe" in perf
        assert "final_best_sharpe" in perf
        assert "improvement" in perf


class TestValidationReportGenerator:
    """Tests for ValidationReportGenerator."""

    def test_initialization(self):
        """Test report generator initialization."""
        generator = ValidationReportGenerator()
        assert len(generator.tier_names) == 3

    def test_generate_markdown_report(self, populated_tracker, sample_config):
        """Test markdown report generation."""
        generator = ValidationReportGenerator()
        report = generator.generate_markdown_report(
            metrics=populated_tracker,
            config=sample_config
        )

        assert isinstance(report, str)
        assert len(report) > 0
        assert "# 50-Generation Three-Tier Validation Report" in report
        assert "Executive Summary" in report
        assert "Tier Distribution" in report
        assert "Performance Progression" in report

    def test_generate_markdown_report_with_output(self, populated_tracker, sample_config):
        """Test markdown report generation with file output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, "report.md")

            generator = ValidationReportGenerator()
            report = generator.generate_markdown_report(
                metrics=populated_tracker,
                config=sample_config,
                output_path=report_path
            )

            assert os.path.exists(report_path)

            # Verify file content
            with open(report_path, 'r') as f:
                file_content = f.read()

            assert file_content == report

    def test_generate_visualizations(self, populated_tracker):
        """Test visualization generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ValidationReportGenerator()
            generator.generate_visualizations(
                metrics=populated_tracker,
                output_dir=tmpdir
            )

            # Check files created
            assert os.path.exists(os.path.join(tmpdir, "tier_distribution.txt"))
            assert os.path.exists(os.path.join(tmpdir, "performance_progression.txt"))

    def test_report_sections(self, populated_tracker, sample_config):
        """Test that all report sections are included."""
        generator = ValidationReportGenerator()
        report = generator.generate_markdown_report(
            metrics=populated_tracker,
            config=sample_config
        )

        # Check all expected sections present
        expected_sections = [
            "Executive Summary",
            "Tier Distribution Analysis",
            "Performance Progression",
            "Tier Effectiveness",
            "System Stability",
            "Breakthrough Strategies",
            "Recommendations",
            "Appendix"
        ]

        for section in expected_sections:
            assert section in report, f"Missing section: {section}"


class TestValidationConfiguration:
    """Tests for validation configuration loading."""

    def test_config_structure(self, sample_config):
        """Test configuration structure."""
        assert "name" in sample_config
        assert "population" in sample_config
        assert "validation" in sample_config

        pop = sample_config["population"]
        assert "size" in pop
        assert "generations" in pop

        val = sample_config["validation"]
        assert "target_tier_distribution" in val
        assert "performance_targets" in val

    def test_tier_distribution_targets(self, sample_config):
        """Test tier distribution target configuration."""
        targets = sample_config["validation"]["target_tier_distribution"]

        assert "tier1" in targets
        assert "tier2" in targets
        assert "tier3" in targets

        # Check targets sum to 1.0
        total = targets["tier1"] + targets["tier2"] + targets["tier3"]
        assert 0.99 <= total <= 1.01


class TestValidationWorkflow:
    """Integration tests for validation workflow."""

    def test_full_validation_workflow(self, sample_config):
        """Test complete validation workflow."""
        # Create tracker
        tracker = ThreeTierMetricsTracker()
        tracker.start_time = datetime.now().isoformat()

        # Simulate 5 generations
        for gen in range(1, 6):
            population = [MockStrategy(f"strategy_{i}") for i in range(10)]
            fitness_scores = {f"strategy_{i}": 1.0 + (gen * 0.1) + (i * 0.01) for i in range(10)}
            tier_stats = {"tier1": 2, "tier2": 5, "tier3": 1}

            tracker.record_generation(
                generation=gen,
                population=population,
                tier_stats=tier_stats,
                fitness_scores=fitness_scores
            )

        tracker.end_time = datetime.now().isoformat()

        # Generate report
        generator = ValidationReportGenerator()
        report = generator.generate_markdown_report(
            metrics=tracker,
            config=sample_config
        )

        # Validate report
        assert len(report) > 1000
        assert "Generation 5" in report or "5 generations" in report.lower()

        # Export metrics
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = os.path.join(tmpdir, "metrics.json")
            tracker.export_report(metrics_path)
            assert os.path.exists(metrics_path)

    def test_checkpoint_save_load(self, populated_tracker):
        """Test checkpoint save and load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save checkpoint data
            checkpoint_path = os.path.join(tmpdir, "checkpoint.json")

            checkpoint = {
                "generation": 10,
                "best_sharpe": populated_tracker.best_sharpe_overall,
                "tier_distribution": populated_tracker.get_tier_distribution()
            }

            with open(checkpoint_path, 'w') as f:
                json.dump(checkpoint, f)

            # Load and verify
            with open(checkpoint_path, 'r') as f:
                loaded = json.load(f)

            assert loaded["generation"] == 10
            assert "best_sharpe" in loaded
            assert "tier_distribution" in loaded


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
