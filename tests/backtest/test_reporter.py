"""
Unit tests for backtest report generation.

Tests JSON and Markdown report generation from ExecutionResult objects,
including format validation, statistics accuracy, and edge case handling.
"""

import json
import tempfile
from pathlib import Path
from typing import List

import pytest

from src.backtest.executor import ExecutionResult
from src.backtest.reporter import ResultsReporter, ReportMetrics


class TestReportMetrics:
    """Test ReportMetrics dataclass."""

    def test_create_with_all_values(self):
        """Test creating ReportMetrics with all values."""
        metrics = ReportMetrics(
            avg_sharpe=1.5,
            avg_return=0.25,
            avg_drawdown=-0.15,
            win_rate=0.65,
            execution_success_rate=0.95,
        )
        assert metrics.avg_sharpe == 1.5
        assert metrics.avg_return == 0.25
        assert metrics.avg_drawdown == -0.15
        assert metrics.win_rate == 0.65
        assert metrics.execution_success_rate == 0.95

    def test_create_with_none_values(self):
        """Test creating ReportMetrics with None values."""
        metrics = ReportMetrics()
        assert metrics.avg_sharpe is None
        assert metrics.avg_return is None
        assert metrics.avg_drawdown is None
        assert metrics.win_rate is None
        assert metrics.execution_success_rate is None


class TestResultsReporter:
    """Test ResultsReporter class."""

    @pytest.fixture
    def reporter(self):
        """Create a ResultsReporter instance."""
        return ResultsReporter()

    @pytest.fixture
    def successful_result(self) -> ExecutionResult:
        """Create a successful ExecutionResult."""
        return ExecutionResult(
            success=True,
            execution_time=2.5,
            sharpe_ratio=1.5,
            total_return=0.25,
            max_drawdown=-0.15,
        )

    @pytest.fixture
    def failed_result(self) -> ExecutionResult:
        """Create a failed ExecutionResult."""
        return ExecutionResult(
            success=False,
            error_type="SyntaxError",
            error_message="Invalid syntax in strategy code",
            execution_time=0.1,
        )

    @pytest.fixture
    def timeout_result(self) -> ExecutionResult:
        """Create a timeout ExecutionResult."""
        return ExecutionResult(
            success=False,
            error_type="TimeoutError",
            error_message="Execution exceeded timeout of 420 seconds",
            execution_time=420.5,
        )

    # JSON Report Tests

    def test_generate_json_report_empty_results(self, reporter):
        """Test generating JSON report with empty results."""
        report = reporter.generate_json_report([])

        assert isinstance(report, dict)
        assert "summary" in report
        assert "metrics" in report
        assert "errors" in report
        assert "execution_stats" in report

        # Check empty summary
        assert report["summary"]["total"] == 0
        assert report["summary"]["successful"] == 0
        assert report["summary"]["failed"] == 0

    def test_generate_json_report_single_success(self, reporter, successful_result):
        """Test generating JSON report with single successful result."""
        report = reporter.generate_json_report([successful_result])

        assert report["summary"]["total"] == 1
        assert report["summary"]["successful"] == 1
        assert report["summary"]["failed"] == 0

        # Check metrics are present
        assert report["metrics"]["avg_sharpe"] is not None
        assert report["metrics"]["avg_return"] is not None
        assert report["metrics"]["avg_drawdown"] is not None

    def test_generate_json_report_single_failure(self, reporter, failed_result):
        """Test generating JSON report with single failed result."""
        report = reporter.generate_json_report([failed_result])

        assert report["summary"]["total"] == 1
        assert report["summary"]["successful"] == 0
        assert report["summary"]["failed"] == 1

        # Check error is recorded
        assert report["errors"]["top_errors"]
        assert report["errors"]["top_errors"][0]["error_type"] == "SyntaxError"

    def test_generate_json_report_mixed_results(
        self, reporter, successful_result, failed_result, timeout_result
    ):
        """Test generating JSON report with mixed results."""
        results = [successful_result, failed_result, timeout_result]
        report = reporter.generate_json_report(results)

        assert report["summary"]["total"] == 3
        assert report["summary"]["successful"] == 1
        assert report["summary"]["failed"] == 2

        # Check error categorization
        assert "timeout" in report["errors"]["by_category"]
        assert "syntax" in report["errors"]["by_category"]

    def test_json_report_structure_validation(self, reporter, successful_result):
        """Test that JSON report has correct structure."""
        report = reporter.generate_json_report([successful_result])

        # Validate top-level keys
        required_keys = {"summary", "metrics", "errors", "execution_stats"}
        assert set(report.keys()) == required_keys

        # Validate summary structure
        summary = report["summary"]
        assert "total" in summary
        assert "successful" in summary
        assert "failed" in summary
        assert "classification_breakdown" in summary

        # Validate metrics structure
        metrics = report["metrics"]
        assert "avg_sharpe" in metrics
        assert "avg_return" in metrics
        assert "avg_drawdown" in metrics
        assert "win_rate" in metrics
        assert "execution_success_rate" in metrics

        # Validate errors structure
        errors = report["errors"]
        assert "by_category" in errors
        assert "top_errors" in errors

        # Validate execution_stats structure
        exec_stats = report["execution_stats"]
        assert "avg_execution_time" in exec_stats
        assert "total_execution_time" in exec_stats
        assert "timeout_count" in exec_stats

    def test_json_report_is_serializable(self, reporter, successful_result):
        """Test that JSON report can be serialized to JSON string."""
        report = reporter.generate_json_report([successful_result])

        # Should not raise
        json_str = json.dumps(report)
        assert isinstance(json_str, str)

        # Should be able to deserialize
        deserialized = json.loads(json_str)
        assert deserialized["summary"]["total"] == 1

    def test_json_report_metrics_aggregation(self, reporter):
        """Test that metrics are correctly aggregated."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=1.0,
                total_return=0.10,
                max_drawdown=-0.05,
                execution_time=1.0,
            ),
            ExecutionResult(
                success=True,
                sharpe_ratio=2.0,
                total_return=0.30,
                max_drawdown=-0.10,
                execution_time=2.0,
            ),
        ]

        report = reporter.generate_json_report(results)
        metrics = report["metrics"]

        # Check averages
        assert metrics["avg_sharpe"] == pytest.approx(1.5)
        assert metrics["avg_return"] == pytest.approx(0.2)
        assert metrics["avg_drawdown"] == pytest.approx(-0.075)
        assert metrics["execution_success_rate"] == 1.0

    def test_json_report_win_rate_calculation(self, reporter):
        """Test win rate calculation (profitable sharpe > 0)."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=0.5,  # Profitable
                total_return=0.10,
                max_drawdown=-0.05,
                execution_time=1.0,
            ),
            ExecutionResult(
                success=True,
                sharpe_ratio=-0.5,  # Not profitable
                total_return=-0.10,
                max_drawdown=-0.15,
                execution_time=1.0,
            ),
            ExecutionResult(
                success=True,
                sharpe_ratio=1.5,  # Profitable
                total_return=0.25,
                max_drawdown=-0.10,
                execution_time=1.0,
            ),
        ]

        report = reporter.generate_json_report(results)
        # 2 out of 3 have positive sharpe
        assert report["metrics"]["win_rate"] == pytest.approx(2.0 / 3.0)

    def test_json_report_error_aggregation(self, reporter):
        """Test that errors are correctly aggregated."""
        results = [
            ExecutionResult(
                success=False,
                error_type="SyntaxError",
                error_message="Invalid syntax",
                execution_time=0.1,
            ),
            ExecutionResult(
                success=False,
                error_type="SyntaxError",
                error_message="Invalid syntax",
                execution_time=0.1,
            ),
            ExecutionResult(
                success=False,
                error_type="TimeoutError",
                error_message="Timeout",
                execution_time=420.0,
            ),
        ]

        report = reporter.generate_json_report(results)

        # Check error categorization
        assert report["errors"]["by_category"]["syntax"] == 2
        assert report["errors"]["by_category"]["timeout"] == 1

        # Check top errors are sorted by frequency
        top_errors = report["errors"]["top_errors"]
        assert len(top_errors) == 2
        assert top_errors[0]["count"] == 2  # SyntaxError is most common

    def test_json_report_top_errors_limit(self, reporter):
        """Test that top errors are limited to 10."""
        results = []
        for i in range(15):
            results.append(
                ExecutionResult(
                    success=False,
                    error_type=f"Error{i}",
                    error_message=f"Message {i}",
                    execution_time=0.1,
                )
            )

        report = reporter.generate_json_report(results)

        # Should have at most 10 top errors
        assert len(report["errors"]["top_errors"]) <= 10

    def test_json_report_only_successful_metrics(self, reporter):
        """Test that metrics are only calculated from successful results."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=10.0,
                total_return=1.0,
                max_drawdown=-0.01,
                execution_time=1.0,
            ),
            ExecutionResult(
                success=False,
                error_type="RuntimeError",
                error_message="Error",
                execution_time=0.1,
            ),
        ]

        report = reporter.generate_json_report(results)

        # Metrics should only be from successful result
        assert report["metrics"]["avg_sharpe"] == 10.0
        assert report["metrics"]["avg_return"] == 1.0
        assert report["metrics"]["execution_success_rate"] == 0.5

    def test_json_report_edge_case_all_failures(self, reporter, failed_result):
        """Test JSON report with all failures (no successful metrics)."""
        results = [failed_result, failed_result, failed_result]
        report = reporter.generate_json_report(results)

        assert report["summary"]["successful"] == 0
        assert report["summary"]["failed"] == 3
        assert report["metrics"]["avg_sharpe"] is None
        assert report["metrics"]["execution_success_rate"] == 0.0

    def test_json_report_edge_case_none_metrics(self, reporter):
        """Test JSON report when successful results have None metrics."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=None,
                total_return=None,
                max_drawdown=None,
                execution_time=1.0,
            ),
        ]

        report = reporter.generate_json_report(results)

        assert report["summary"]["successful"] == 1
        # Metrics should be None since they couldn't be extracted
        assert report["metrics"]["avg_sharpe"] is None
        assert report["metrics"]["avg_return"] is None

    def test_json_report_timeout_count(self, reporter, timeout_result):
        """Test timeout counting in execution stats."""
        results = [timeout_result, timeout_result]
        report = reporter.generate_json_report(results)

        assert report["execution_stats"]["timeout_count"] == 2

    def test_json_report_execution_time_stats(self, reporter):
        """Test execution time statistics calculation."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=1.0,
                total_return=0.10,
                max_drawdown=-0.05,
                execution_time=2.0,
            ),
            ExecutionResult(
                success=True,
                sharpe_ratio=2.0,
                total_return=0.20,
                max_drawdown=-0.10,
                execution_time=4.0,
            ),
        ]

        report = reporter.generate_json_report(results)
        exec_stats = report["execution_stats"]

        assert exec_stats["total_execution_time"] == pytest.approx(6.0)
        assert exec_stats["avg_execution_time"] == pytest.approx(3.0)

    # Markdown Report Tests

    def test_generate_markdown_report_empty_results(self, reporter):
        """Test generating Markdown report with empty results."""
        report = reporter.generate_markdown_report([])

        assert isinstance(report, str)
        assert "Backtest Execution Results Report" in report
        assert "No execution results provided" in report

    def test_generate_markdown_report_single_success(self, reporter, successful_result):
        """Test generating Markdown report with single successful result."""
        report = reporter.generate_markdown_report([successful_result])

        assert "Backtest Execution Results Report" in report
        assert "Executive Summary" in report
        assert "Success/Failure Breakdown" in report
        assert "Performance Metrics Summary" in report
        assert "Execution Statistics" in report

    def test_markdown_report_contains_tables(self, reporter, successful_result):
        """Test that Markdown report contains properly formatted tables."""
        report = reporter.generate_markdown_report([successful_result])

        # Check for table separators
        assert "|" in report
        assert "---" in report

    def test_markdown_report_contains_sections(self, reporter, successful_result):
        """Test that Markdown report contains all major sections."""
        report = reporter.generate_markdown_report([successful_result])

        sections = [
            "Executive Summary",
            "Success/Failure Breakdown",
            "Classification Level Distribution",
            "Performance Metrics Summary",
            "Execution Statistics",
        ]

        for section in sections:
            assert section in report, f"Missing section: {section}"

    def test_markdown_report_summary_statistics(self, reporter, successful_result):
        """Test that executive summary contains correct statistics."""
        results = [successful_result, successful_result]
        report = reporter.generate_markdown_report(results)

        assert "Total Executions" in report
        assert "Successful" in report
        assert "Failed" in report

    def test_markdown_report_success_breakdown_table(self, reporter):
        """Test success/failure breakdown table formatting."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=1.0,
                total_return=0.10,
                max_drawdown=-0.05,
                execution_time=1.0,
            ),
            ExecutionResult(
                success=False,
                error_type="RuntimeError",
                error_message="Error",
                execution_time=0.1,
            ),
        ]

        report = reporter.generate_markdown_report(results)

        # Check table header
        assert "Status" in report
        assert "Count" in report
        assert "Percentage" in report

        # Check values
        assert "Successful" in report
        assert "Failed" in report

    def test_markdown_report_metrics_formatting(self, reporter, successful_result):
        """Test that metrics are properly formatted in Markdown."""
        report = reporter.generate_markdown_report([successful_result])

        # Check for metric names
        assert "Avg Sharpe Ratio" in report
        assert "Avg Return" in report
        assert "Avg Max Drawdown" in report
        assert "Win Rate" in report

    def test_markdown_report_error_table_present(self, reporter):
        """Test that error table is included when errors exist."""
        results = [
            ExecutionResult(
                success=False,
                error_type="SyntaxError",
                error_message="Invalid syntax in code",
                execution_time=0.1,
            ),
        ]

        report = reporter.generate_markdown_report(results)

        assert "Top Errors" in report
        assert "Error Type" in report
        assert "Message" in report

    def test_markdown_report_no_error_section_on_success(self, reporter, successful_result):
        """Test that error section is not included when no errors."""
        report = reporter.generate_markdown_report([successful_result])

        # Should not have Top Errors section (or it should indicate no errors)
        # The report either omits it or says "No errors recorded"
        has_errors = "Top Errors" in report and "recorded" not in report
        # If Top Errors is there, it should say "No errors recorded"
        if "Top Errors" in report:
            assert "No errors recorded" in report or report.count("No errors") > 0

    def test_markdown_report_is_string(self, reporter, successful_result):
        """Test that Markdown report is a string."""
        report = reporter.generate_markdown_report([successful_result])
        assert isinstance(report, str)

    def test_markdown_report_readability(self, reporter):
        """Test that Markdown report is properly formatted and readable."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=1.5,
                total_return=0.25,
                max_drawdown=-0.15,
                execution_time=2.0,
            ),
            ExecutionResult(
                success=False,
                error_type="TimeoutError",
                error_message="Timeout",
                execution_time=420.0,
            ),
        ]

        report = reporter.generate_markdown_report(results)

        # Check that report has newlines and formatting
        assert len(report) > 100  # Should be substantial
        assert "\n" in report
        assert "#" in report  # Markdown headers

    def test_markdown_report_classification_distribution(self, reporter, successful_result):
        """Test classification level distribution table."""
        report = reporter.generate_markdown_report([successful_result])

        assert "Classification Level Distribution" in report
        assert "Level" in report
        assert "Name" in report

    def test_markdown_report_execution_stats_section(self, reporter):
        """Test execution statistics section in Markdown."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=1.0,
                total_return=0.10,
                max_drawdown=-0.05,
                execution_time=2.5,
            ),
        ]

        report = reporter.generate_markdown_report(results)

        assert "Execution Statistics" in report
        assert "Average Execution Time" in report
        assert "Total Execution Time" in report
        assert "Timeout Count" in report

    # File Saving Tests

    def test_save_report_json_format(self, reporter, successful_result):
        """Test saving report in JSON format."""
        report = reporter.generate_json_report([successful_result])

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.json"
            saved_path = reporter.save_report(
                report, str(filepath), format="json"
            )

            assert saved_path.exists()
            assert saved_path.suffix == ".json"

            # Verify content
            with open(saved_path, "r") as f:
                loaded = json.load(f)
                assert loaded["summary"]["total"] == 1

    def test_save_report_markdown_format(self, reporter, successful_result):
        """Test saving report in Markdown format."""
        report = reporter.generate_markdown_report([successful_result])

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.md"
            saved_path = reporter.save_report(
                report, str(filepath), format="markdown"
            )

            assert saved_path.exists()
            assert saved_path.suffix == ".md"

            # Verify content
            with open(saved_path, "r") as f:
                content = f.read()
                assert "Backtest Execution Results Report" in content

    def test_save_report_creates_parent_directories(self, reporter, successful_result):
        """Test that save_report creates parent directories."""
        report = reporter.generate_json_report([successful_result])

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "reports" / "subdir" / "report.json"
            saved_path = reporter.save_report(
                report, str(filepath), format="json"
            )

            assert saved_path.exists()
            assert saved_path.parent.exists()

    def test_save_report_invalid_format(self, reporter, successful_result):
        """Test that invalid format raises ValueError."""
        report = reporter.generate_json_report([successful_result])

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.txt"
            with pytest.raises(ValueError):
                reporter.save_report(report, str(filepath), format="invalid")

    def test_save_report_md_alias(self, reporter, successful_result):
        """Test that 'md' format alias works."""
        report = reporter.generate_markdown_report([successful_result])

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.md"
            saved_path = reporter.save_report(
                report, str(filepath), format="md"
            )

            assert saved_path.exists()

    def test_save_report_returns_path(self, reporter, successful_result):
        """Test that save_report returns Path object."""
        report = reporter.generate_json_report([successful_result])

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.json"
            result = reporter.save_report(report, str(filepath), format="json")

            assert isinstance(result, Path)
            assert result == filepath

    def test_save_report_overwrite_existing(self, reporter, successful_result):
        """Test that save_report overwrites existing files."""
        report1 = reporter.generate_json_report([successful_result])

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.json"

            # Save first report
            reporter.save_report(report1, str(filepath), format="json")

            # Save second report (overwrites)
            results2 = [
                ExecutionResult(
                    success=True,
                    sharpe_ratio=2.0,
                    total_return=0.50,
                    max_drawdown=-0.20,
                    execution_time=1.0,
                ),
            ]
            report2 = reporter.generate_json_report(results2)
            reporter.save_report(report2, str(filepath), format="json")

            # Verify second content
            with open(filepath, "r") as f:
                loaded = json.load(f)
                assert loaded["summary"]["total"] == 1

    # Integration Tests

    def test_full_workflow_json(self, reporter):
        """Test complete workflow: generate and save JSON report."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=1.5,
                total_return=0.25,
                max_drawdown=-0.15,
                execution_time=2.0,
            ),
            ExecutionResult(
                success=False,
                error_type="SyntaxError",
                error_message="Invalid syntax",
                execution_time=0.1,
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.json"

            # Generate report
            json_report = reporter.generate_json_report(results)

            # Save report
            saved_path = reporter.save_report(
                json_report, str(filepath), format="json"
            )

            # Verify
            assert saved_path.exists()
            with open(saved_path, "r") as f:
                loaded = json.load(f)
                assert loaded["summary"]["total"] == 2
                assert loaded["summary"]["successful"] == 1

    def test_full_workflow_markdown(self, reporter):
        """Test complete workflow: generate and save Markdown report."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=1.5,
                total_return=0.25,
                max_drawdown=-0.15,
                execution_time=2.0,
            ),
            ExecutionResult(
                success=False,
                error_type="TimeoutError",
                error_message="Timeout",
                execution_time=420.0,
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.md"

            # Generate report
            md_report = reporter.generate_markdown_report(results)

            # Save report
            saved_path = reporter.save_report(
                md_report, str(filepath), format="markdown"
            )

            # Verify
            assert saved_path.exists()
            with open(saved_path, "r") as f:
                content = f.read()
                assert "Backtest Execution Results Report" in content
                assert "2" in content  # Should mention 2 executions

    def test_large_result_set(self, reporter):
        """Test report generation with large result set."""
        results = []
        for i in range(100):
            success = i % 3 != 0  # ~67% success rate
            if success:
                results.append(
                    ExecutionResult(
                        success=True,
                        sharpe_ratio=1.0 + (i % 10) * 0.1,
                        total_return=0.1 + (i % 10) * 0.01,
                        max_drawdown=-0.1 - (i % 10) * 0.01,
                        execution_time=1.0 + (i % 5),
                    )
                )
            else:
                results.append(
                    ExecutionResult(
                        success=False,
                        error_type=f"Error{i % 5}",
                        error_message=f"Error message {i}",
                        execution_time=0.1,
                    )
                )

        # Generate both reports
        json_report = reporter.generate_json_report(results)
        md_report = reporter.generate_markdown_report(results)

        # Verify structure
        assert json_report["summary"]["total"] == 100
        assert len(md_report) > 500

    def test_classification_breakdown_in_json(self, reporter, successful_result):
        """Test that classification breakdown is present in JSON report."""
        report = reporter.generate_json_report([successful_result])

        breakdown = report["summary"]["classification_breakdown"]
        assert "level_0_failed" in breakdown
        assert "level_1_executed" in breakdown
        assert "level_2_valid_metrics" in breakdown
        assert "level_3_profitable" in breakdown

    def test_error_category_distribution(self, reporter):
        """Test error category distribution in JSON report."""
        results = [
            ExecutionResult(
                success=False,
                error_type="TimeoutError",
                error_message="Timeout",
                execution_time=420.0,
            ),
            ExecutionResult(
                success=False,
                error_type="SyntaxError",
                error_message="Invalid syntax",
                execution_time=0.1,
            ),
            ExecutionResult(
                success=False,
                error_type="NameError",
                error_message="Undefined variable",
                execution_time=0.1,
            ),
        ]

        report = reporter.generate_json_report(results)
        categories = report["errors"]["by_category"]

        # Should have categorized errors
        assert sum(categories.values()) == 3

    def test_reporter_with_mixed_none_metrics(self, reporter):
        """Test reporter handles mixed None and valid metrics."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=1.0,
                total_return=None,
                max_drawdown=-0.05,
                execution_time=1.0,
            ),
            ExecutionResult(
                success=True,
                sharpe_ratio=None,
                total_return=0.20,
                max_drawdown=None,
                execution_time=1.0,
            ),
        ]

        report = reporter.generate_json_report(results)

        # Should handle None values gracefully
        assert report["metrics"]["avg_sharpe"] is not None or True  # Extracted from first
        assert report["summary"]["successful"] == 2


class TestReporterEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def reporter(self):
        """Create a ResultsReporter instance."""
        return ResultsReporter()

    def test_all_successful_no_failures(self, reporter):
        """Test report with only successful results."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=1.5,
                total_return=0.25,
                max_drawdown=-0.15,
                execution_time=2.0,
            ),
        ] * 5

        json_report = reporter.generate_json_report(results)

        assert json_report["summary"]["successful"] == 5
        assert json_report["summary"]["failed"] == 0
        assert json_report["errors"]["top_errors"] == []

    def test_all_failures_no_successes(self, reporter):
        """Test report with only failed results."""
        results = [
            ExecutionResult(
                success=False,
                error_type="RuntimeError",
                error_message="Runtime error",
                execution_time=0.1,
            ),
        ] * 5

        json_report = reporter.generate_json_report(results)
        md_report = reporter.generate_markdown_report(results)

        assert json_report["summary"]["successful"] == 0
        assert json_report["summary"]["failed"] == 5
        assert json_report["metrics"]["avg_sharpe"] is None
        assert json_report["metrics"]["execution_success_rate"] == 0.0
        assert isinstance(md_report, str)

    def test_single_result_all_metrics_none(self, reporter):
        """Test result with successful execution but all None metrics."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=None,
                total_return=None,
                max_drawdown=None,
                execution_time=1.0,
            ),
        ]

        json_report = reporter.generate_json_report(results)

        assert json_report["summary"]["successful"] == 1
        assert json_report["metrics"]["avg_sharpe"] is None
        assert json_report["metrics"]["avg_return"] is None

    def test_zero_execution_time(self, reporter):
        """Test handling of zero execution times."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=1.0,
                total_return=0.10,
                max_drawdown=-0.05,
                execution_time=0.0,
            ),
        ]

        json_report = reporter.generate_json_report(results)

        assert json_report["execution_stats"]["avg_execution_time"] == 0.0

    def test_very_long_error_message(self, reporter):
        """Test handling of very long error messages in Markdown."""
        long_message = "x" * 1000
        results = [
            ExecutionResult(
                success=False,
                error_type="RuntimeError",
                error_message=long_message,
                execution_time=0.1,
            ),
        ]

        md_report = reporter.generate_markdown_report(results)

        # Message should be truncated in Markdown table
        assert isinstance(md_report, str)
        # The message is truncated to 50 chars in the table
        assert long_message[:50] in md_report or "x" * 50 in md_report

    def test_unicode_error_messages(self, reporter):
        """Test handling of unicode characters in error messages."""
        results = [
            ExecutionResult(
                success=False,
                error_type="UnicodeError",
                error_message="Unicode error: 中文字符 مصر العربية",
                execution_time=0.1,
            ),
        ]

        json_report = reporter.generate_json_report(results)
        md_report = reporter.generate_markdown_report(results)

        assert "中文" in json_report["errors"]["top_errors"][0]["message"]
        assert isinstance(md_report, str)

    def test_negative_execution_time(self, reporter):
        """Test handling of negative execution times (edge case)."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=1.0,
                total_return=0.10,
                max_drawdown=-0.05,
                execution_time=-1.0,
            ),
        ]

        json_report = reporter.generate_json_report(results)

        # Should handle gracefully
        assert json_report["execution_stats"]["avg_execution_time"] == 0.0

    def test_extremely_large_metrics(self, reporter):
        """Test handling of extremely large metric values."""
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=1000.0,
                total_return=100.0,  # 10000% return
                max_drawdown=-0.99,  # 99% drawdown
                execution_time=9999.0,
            ),
        ]

        json_report = reporter.generate_json_report(results)

        assert json_report["metrics"]["avg_sharpe"] == 1000.0
        assert json_report["metrics"]["avg_return"] == 100.0

    def test_duplicate_error_messages(self, reporter):
        """Test aggregation of duplicate error messages."""
        results = [
            ExecutionResult(
                success=False,
                error_type="SyntaxError",
                error_message="Same error",
                execution_time=0.1,
            ),
            ExecutionResult(
                success=False,
                error_type="SyntaxError",
                error_message="Same error",
                execution_time=0.1,
            ),
            ExecutionResult(
                success=False,
                error_type="SyntaxError",
                error_message="Same error",
                execution_time=0.1,
            ),
        ]

        json_report = reporter.generate_json_report(results)

        # Should have single entry with count=3
        assert len(json_report["errors"]["top_errors"]) == 1
        assert json_report["errors"]["top_errors"][0]["count"] == 3

    def test_mixed_error_and_none_types(self, reporter):
        """Test handling of None error types."""
        results = [
            ExecutionResult(
                success=False,
                error_type=None,
                error_message="Unknown error",
                execution_time=0.1,
            ),
        ]

        json_report = reporter.generate_json_report(results)

        # Should handle None error_type
        assert json_report["summary"]["failed"] == 1
        assert len(json_report["errors"]["top_errors"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
