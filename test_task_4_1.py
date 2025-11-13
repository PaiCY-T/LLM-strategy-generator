#!/usr/bin/env python3
"""Test script for Phase 2 Task 4.1 - ResultsReporter implementation.

Tests the ResultsReporter class with various scenarios:
- JSON report generation
- Markdown report generation
- File saving functionality
- Empty results handling
- Error aggregation
"""

import json
import tempfile
from pathlib import Path

from src.backtest import ExecutionResult, ResultsReporter


def create_mock_results():
    """Create mock ExecutionResult objects for testing."""
    results = [
        # Successful execution with good metrics
        ExecutionResult(
            success=True,
            error_type=None,
            error_message=None,
            execution_time=5.2,
            sharpe_ratio=1.5,
            total_return=0.25,
            max_drawdown=-0.10,
            report=None,
            stack_trace=None,
        ),
        # Successful execution with lower metrics
        ExecutionResult(
            success=True,
            error_type=None,
            error_message=None,
            execution_time=3.8,
            sharpe_ratio=0.8,
            total_return=0.12,
            max_drawdown=-0.15,
            report=None,
            stack_trace=None,
        ),
        # Successful execution but unprofitable
        ExecutionResult(
            success=True,
            error_type=None,
            error_message=None,
            execution_time=4.1,
            sharpe_ratio=-0.5,
            total_return=-0.05,
            max_drawdown=-0.20,
            report=None,
            stack_trace=None,
        ),
        # Failed execution - timeout
        ExecutionResult(
            success=False,
            error_type="TimeoutError",
            error_message="Execution exceeded timeout",
            execution_time=420.0,
            sharpe_ratio=None,
            total_return=None,
            max_drawdown=None,
            report=None,
            stack_trace="Full traceback here...",
        ),
        # Failed execution - data missing
        ExecutionResult(
            success=False,
            error_type="KeyError",
            error_message="key 'price' not found",
            execution_time=1.2,
            sharpe_ratio=None,
            total_return=None,
            max_drawdown=None,
            report=None,
            stack_trace="Traceback...",
        ),
        # Failed execution - calculation error
        ExecutionResult(
            success=False,
            error_type="ZeroDivisionError",
            error_message="division by zero",
            execution_time=2.5,
            sharpe_ratio=None,
            total_return=None,
            max_drawdown=None,
            report=None,
            stack_trace="Traceback...",
        ),
    ]
    return results


def test_json_report_generation():
    """Test JSON report generation."""
    print("Testing JSON report generation...")

    reporter = ResultsReporter()
    results = create_mock_results()

    json_report = reporter.generate_json_report(results)

    # Validate structure
    assert "summary" in json_report
    assert "metrics" in json_report
    assert "errors" in json_report
    assert "execution_stats" in json_report

    # Validate summary
    summary = json_report["summary"]
    assert summary["total"] == 6
    assert summary["successful"] == 3
    assert summary["failed"] == 3
    assert "classification_breakdown" in summary

    # Validate metrics
    metrics = json_report["metrics"]
    assert metrics["execution_success_rate"] == 0.5  # 3/6
    assert metrics["avg_sharpe"] is not None
    assert metrics["avg_return"] is not None
    assert metrics["avg_drawdown"] is not None
    assert metrics["win_rate"] is not None

    # Validate errors
    errors = json_report["errors"]
    assert "by_category" in errors
    assert "top_errors" in errors
    assert errors["by_category"]["timeout"] == 1
    assert errors["by_category"]["data_missing"] == 1
    assert errors["by_category"]["calculation"] == 1

    # Validate execution stats
    exec_stats = json_report["execution_stats"]
    assert exec_stats["timeout_count"] == 1
    assert exec_stats["avg_execution_time"] > 0

    print("JSON report validation: PASSED")
    return json_report


def test_markdown_report_generation():
    """Test Markdown report generation."""
    print("Testing Markdown report generation...")

    reporter = ResultsReporter()
    results = create_mock_results()

    md_report = reporter.generate_markdown_report(results)

    # Validate content
    assert "# Backtest Execution Results Report" in md_report
    assert "## Executive Summary" in md_report
    assert "## Success/Failure Breakdown" in md_report
    assert "## Classification Level Distribution" in md_report
    assert "## Top Errors" in md_report
    assert "## Performance Metrics Summary" in md_report
    assert "## Execution Statistics" in md_report

    # Validate tables exist
    assert "|" in md_report  # Tables use pipes
    assert "Successful" in md_report
    assert "Failed" in md_report

    print("Markdown report validation: PASSED")
    return md_report


def test_save_json_report():
    """Test saving JSON report to file."""
    print("Testing JSON report file saving...")

    reporter = ResultsReporter()
    results = create_mock_results()
    json_report = reporter.generate_json_report(results)

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "report.json"
        saved_path = reporter.save_report(json_report, str(filepath), format="json")

        assert saved_path.exists()
        assert saved_path.suffix == ".json"

        # Verify content
        with open(saved_path, "r") as f:
            loaded = json.load(f)
            assert loaded["summary"]["total"] == 6
            assert loaded["summary"]["successful"] == 3

    print("JSON report saving: PASSED")


def test_save_markdown_report():
    """Test saving Markdown report to file."""
    print("Testing Markdown report file saving...")

    reporter = ResultsReporter()
    results = create_mock_results()
    md_report = reporter.generate_markdown_report(results)

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "report.md"
        saved_path = reporter.save_report(md_report, str(filepath), format="markdown")

        assert saved_path.exists()
        assert saved_path.suffix == ".md"

        # Verify content
        with open(saved_path, "r") as f:
            content = f.read()
            assert "# Backtest Execution Results Report" in content

    print("Markdown report saving: PASSED")


def test_empty_results():
    """Test handling of empty results."""
    print("Testing empty results handling...")

    reporter = ResultsReporter()
    empty_results = []

    # Test JSON
    json_report = reporter.generate_json_report(empty_results)
    assert json_report["summary"]["total"] == 0
    assert json_report["summary"]["successful"] == 0

    # Test Markdown
    md_report = reporter.generate_markdown_report(empty_results)
    assert "No execution results provided" in md_report

    print("Empty results handling: PASSED")


def test_metrics_aggregation():
    """Test metrics aggregation."""
    print("Testing metrics aggregation...")

    reporter = ResultsReporter()
    results = create_mock_results()

    json_report = reporter.generate_json_report(results)
    metrics = json_report["metrics"]

    # Should have aggregated metrics from successful results only
    assert metrics["execution_success_rate"] == 3 / 6
    assert metrics["avg_sharpe"] is not None
    assert metrics["win_rate"] is not None  # 1/3 profitable (only first result has Sharpe > 0)

    print("Metrics aggregation: PASSED")


def test_error_aggregation():
    """Test error categorization and aggregation."""
    print("Testing error aggregation...")

    reporter = ResultsReporter()
    results = create_mock_results()

    json_report = reporter.generate_json_report(results)
    errors = json_report["errors"]

    # Verify error counts by category
    assert errors["by_category"]["timeout"] == 1
    assert errors["by_category"]["data_missing"] == 1
    assert errors["by_category"]["calculation"] == 1

    # Verify top errors
    assert len(errors["top_errors"]) > 0

    print("Error aggregation: PASSED")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Phase 2 Task 4.1 - ResultsReporter Tests")
    print("=" * 60 + "\n")

    try:
        test_json_report_generation()
        test_markdown_report_generation()
        test_save_json_report()
        test_save_markdown_report()
        test_empty_results()
        test_metrics_aggregation()
        test_error_aggregation()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60 + "\n")

    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
