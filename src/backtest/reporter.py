"""Results reporting system for backtest execution.

Generates comprehensive reports from backtest execution results in both
JSON and Markdown formats. Integrates with MetricsExtractor, SuccessClassifier,
and ErrorClassifier to provide detailed analysis of strategy performance.

Key Features:
    - JSON report generation with summary, metrics, errors, and execution stats
    - Markdown report generation with formatted tables and sections
    - File export functionality for both formats
    - Handles empty results gracefully
    - Comprehensive error aggregation and categorization
    - Support for batch result analysis
"""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .classifier import SuccessClassifier
from .error_classifier import ErrorClassifier, ErrorCategory
from .executor import ExecutionResult
from .metrics import MetricsExtractor, StrategyMetrics

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ReportMetrics:
    """Aggregated metrics statistics for report generation.

    Attributes:
        avg_sharpe: Average Sharpe ratio across results
        avg_return: Average total return across results
        avg_drawdown: Average maximum drawdown across results
        win_rate: Percentage of strategies with positive Sharpe ratio
        execution_success_rate: Percentage of successful executions
    """

    avg_sharpe: Optional[float] = None
    avg_return: Optional[float] = None
    avg_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    execution_success_rate: Optional[float] = None


class ResultsReporter:
    """Generate summary reports from backtest execution results.

    Provides methods to generate comprehensive reports in JSON and Markdown
    formats from a list of ExecutionResult objects. Leverages MetricsExtractor,
    SuccessClassifier, and ErrorClassifier for detailed analysis.

    The reporter handles:
        - Summary statistics (total, successful, failed)
        - Performance metrics aggregation (Sharpe, return, drawdown)
        - Classification level distribution
        - Error categorization and top error identification
        - Execution time statistics and timeout tracking

    Example:
        reporter = ResultsReporter()
        results = [execution_result1, execution_result2, ...]

        # Generate JSON report
        json_report = reporter.generate_json_report(results)
        reporter.save_report(json_report, 'report.json', format='json')

        # Generate Markdown report
        md_report = reporter.generate_markdown_report(results)
        reporter.save_report(md_report, 'report.md', format='markdown')
    """

    def __init__(self):
        """Initialize ResultsReporter with helper components."""
        self.metrics_extractor = MetricsExtractor()
        self.success_classifier = SuccessClassifier()
        self.error_classifier = ErrorClassifier()

    def generate_json_report(
        self, results: List[ExecutionResult]
    ) -> Dict[str, Any]:
        """Generate a JSON-serializable report from execution results.

        Creates a structured JSON report containing:
            - Summary: total count, successful/failed, classification breakdown
            - Metrics: aggregated performance statistics
            - Errors: categorized errors and top error summary
            - Execution Stats: timing information and timeout counts

        Args:
            results: List of ExecutionResult objects from backtest execution

        Returns:
            Dictionary with structure:
            {
                "summary": {
                    "total": int,
                    "successful": int,
                    "failed": int,
                    "classification_breakdown": {
                        "level_0_failed": int,
                        "level_1_executed": int,
                        "level_2_valid_metrics": int,
                        "level_3_profitable": int
                    }
                },
                "metrics": {
                    "avg_sharpe": float | None,
                    "avg_return": float | None,
                    "avg_drawdown": float | None,
                    "win_rate": float | None,
                    "execution_success_rate": float | None
                },
                "errors": {
                    "by_category": {
                        "timeout": int,
                        "data_missing": int,
                        "calculation": int,
                        "syntax": int,
                        "other": int
                    },
                    "top_errors": [
                        {"error_type": str, "message": str, "count": int}
                    ]
                },
                "execution_stats": {
                    "avg_execution_time": float,
                    "total_execution_time": float,
                    "timeout_count": int
                }
            }

        Notes:
            - Empty results list returns summary with all zeros and no metrics
            - Metrics are averaged only from successful executions with extracted values
            - Errors are aggregated from all failed executions
            - Top errors are sorted by frequency
        """
        if not results:
            logger.warning("No results provided for JSON report generation")
            return self._generate_empty_json_report()

        # Extract and classify all results
        classified_results = self._classify_results(results)

        # Generate summary
        summary = self._generate_summary(results, classified_results)

        # Generate metrics aggregation
        metrics = self._aggregate_metrics(results)

        # Generate error analysis
        errors = self._aggregate_errors(results)

        # Generate execution statistics
        execution_stats = self._calculate_execution_stats(results)

        json_report = {
            "summary": summary,
            "metrics": asdict(metrics),
            "errors": errors,
            "execution_stats": execution_stats,
        }

        logger.info(
            f"Generated JSON report for {len(results)} results: "
            f"{summary['successful']} successful, {summary['failed']} failed"
        )

        return json_report

    def generate_markdown_report(
        self, results: List[ExecutionResult]
    ) -> str:
        """Generate a human-readable Markdown report from execution results.

        Creates a formatted Markdown report with sections for:
            - Executive summary with key statistics
            - Success/failure breakdown table
            - Classification level distribution
            - Top errors table
            - Performance metrics summary

        Args:
            results: List of ExecutionResult objects from backtest execution

        Returns:
            Markdown-formatted string containing the full report

        Example:
            report = reporter.generate_markdown_report(results)
            print(report)
        """
        if not results:
            logger.warning("No results provided for Markdown report generation")
            return self._generate_empty_markdown_report()

        # Extract and classify all results
        classified_results = self._classify_results(results)

        # Create markdown sections
        md_lines = []

        # Title
        md_lines.append("# Backtest Execution Results Report\n")

        # Executive Summary
        md_lines.extend(
            self._generate_markdown_executive_summary(results, classified_results)
        )

        # Success/Failure Breakdown
        md_lines.extend(self._generate_markdown_success_breakdown(results))

        # Classification Distribution
        md_lines.extend(
            self._generate_markdown_classification_table(classified_results)
        )

        # Top Errors
        error_details = self._aggregate_errors(results)
        if error_details["top_errors"]:
            md_lines.extend(self._generate_markdown_errors_table(error_details))

        # Metrics Summary
        metrics = self._aggregate_metrics(results)
        md_lines.extend(self._generate_markdown_metrics_table(metrics))

        # Execution Statistics
        exec_stats = self._calculate_execution_stats(results)
        md_lines.extend(self._generate_markdown_execution_stats(exec_stats))

        markdown_report = "\n".join(md_lines)

        logger.info(f"Generated Markdown report for {len(results)} results")

        return markdown_report

    def save_report(
        self,
        report: Any,
        filename: str,
        format: str = "json",
    ) -> Path:
        """Save report to file in specified format.

        Args:
            report: Report object (dict for JSON, str for Markdown)
            filename: Target file path
            format: Report format ('json' or 'markdown')

        Returns:
            Path object pointing to created file

        Raises:
            ValueError: If format is not 'json' or 'markdown'
            IOError: If file cannot be written

        Example:
            json_report = reporter.generate_json_report(results)
            path = reporter.save_report(json_report, 'report.json', format='json')
            print(f"Report saved to {path}")
        """
        file_path = Path(filename)

        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if format.lower() == "json":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                logger.info(f"JSON report saved to {file_path}")

            elif format.lower() in ("markdown", "md"):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(report)
                logger.info(f"Markdown report saved to {file_path}")

            else:
                raise ValueError(
                    f"Unsupported format '{format}'. Use 'json' or 'markdown'"
                )

            return file_path

        except IOError as e:
            logger.error(f"Failed to save report to {file_path}: {e}")
            raise

    # Private helper methods

    def _classify_results(
        self, results: List[ExecutionResult]
    ) -> List[Optional[Any]]:
        """Classify each result using SuccessClassifier.

        Args:
            results: List of ExecutionResult objects

        Returns:
            List of ClassificationResult objects (None for unconvertible results)
        """
        classified = []

        for result in results:
            try:
                # Convert ExecutionResult to StrategyMetrics for classification
                metrics = StrategyMetrics(
                    sharpe_ratio=result.sharpe_ratio,
                    total_return=result.total_return,
                    max_drawdown=result.max_drawdown,
                    win_rate=None,  # Not available in ExecutionResult
                    execution_success=result.success,
                )

                classification = self.success_classifier.classify_single(metrics)
                classified.append(classification)

            except Exception as e:
                logger.warning(f"Failed to classify result: {e}")
                classified.append(None)

        return classified

    def _generate_summary(
        self,
        results: List[ExecutionResult],
        classified_results: List[Optional[Any]],
    ) -> Dict[str, Any]:
        """Generate summary statistics for report.

        Args:
            results: Original execution results
            classified_results: Classified results

        Returns:
            Dictionary with summary statistics
        """
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful

        # Count classification levels
        classification_breakdown = {
            "level_0_failed": 0,
            "level_1_executed": 0,
            "level_2_valid_metrics": 0,
            "level_3_profitable": 0,
        }

        for classified in classified_results:
            if classified is not None:
                level_key = f"level_{classified.level}_{self._get_level_name(classified.level)}"
                if level_key in classification_breakdown:
                    classification_breakdown[level_key] += 1
                else:
                    # Handle unexpected levels
                    classification_breakdown[
                        f"level_{classified.level}_unknown"
                    ] = (
                        classification_breakdown.get(
                            f"level_{classified.level}_unknown", 0
                        )
                        + 1
                    )

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "classification_breakdown": classification_breakdown,
        }

    def _aggregate_metrics(self, results: List[ExecutionResult]) -> ReportMetrics:
        """Aggregate performance metrics from successful results.

        Args:
            results: List of ExecutionResult objects

        Returns:
            ReportMetrics with averaged statistics
        """
        if not results:
            return ReportMetrics()

        # Filter successful results
        successful_results = [r for r in results if r.success]

        if not successful_results:
            return ReportMetrics(
                execution_success_rate=0.0,
                avg_sharpe=None,
                avg_return=None,
                avg_drawdown=None,
                win_rate=None,
            )

        # Aggregate Sharpe ratios
        sharpe_ratios = [
            r.sharpe_ratio
            for r in successful_results
            if r.sharpe_ratio is not None
        ]
        avg_sharpe = (
            sum(sharpe_ratios) / len(sharpe_ratios) if sharpe_ratios else None
        )

        # Aggregate returns
        returns = [r.total_return for r in successful_results if r.total_return is not None]
        avg_return = sum(returns) / len(returns) if returns else None

        # Aggregate drawdowns
        drawdowns = [
            r.max_drawdown for r in successful_results if r.max_drawdown is not None
        ]
        avg_drawdown = sum(drawdowns) / len(drawdowns) if drawdowns else None

        # Calculate win rate (percentage of positive Sharpe ratios)
        profitable_count = sum(1 for r in sharpe_ratios if r > 0)
        win_rate = (
            profitable_count / len(sharpe_ratios) if sharpe_ratios else None
        )

        # Calculate execution success rate
        execution_success_rate = len(successful_results) / len(results)

        return ReportMetrics(
            avg_sharpe=avg_sharpe,
            avg_return=avg_return,
            avg_drawdown=avg_drawdown,
            win_rate=win_rate,
            execution_success_rate=execution_success_rate,
        )

    def _aggregate_errors(self, results: List[ExecutionResult]) -> Dict[str, Any]:
        """Aggregate error information from failed results.

        Args:
            results: List of ExecutionResult objects

        Returns:
            Dictionary with error categorization and top errors
        """
        # Filter failed results
        failed_results = [r for r in results if not r.success]

        if not failed_results:
            return {
                "by_category": {
                    "timeout": 0,
                    "data_missing": 0,
                    "calculation": 0,
                    "syntax": 0,
                    "other": 0,
                },
                "top_errors": [],
            }

        # Categorize errors
        error_counts = {category.value: 0 for category in ErrorCategory}
        error_frequency: Dict[tuple, int] = {}

        for result in failed_results:
            error_type = result.error_type or "Unknown"
            error_msg = result.error_message or "No message"

            # Classify error
            category = self.error_classifier.classify_error(error_type, error_msg)
            error_counts[category.value] += 1

            # Track error frequency
            error_key = (error_type, error_msg)
            error_frequency[error_key] = error_frequency.get(error_key, 0) + 1

        # Get top errors (sorted by frequency)
        top_errors = [
            {
                "error_type": error_type,
                "message": error_msg,
                "count": count,
            }
            for (error_type, error_msg), count in sorted(
                error_frequency.items(), key=lambda x: x[1], reverse=True
            )[:10]  # Top 10 errors
        ]

        return {
            "by_category": error_counts,
            "top_errors": top_errors,
        }

    def _calculate_execution_stats(
        self, results: List[ExecutionResult]
    ) -> Dict[str, Any]:
        """Calculate execution timing and timeout statistics.

        Args:
            results: List of ExecutionResult objects

        Returns:
            Dictionary with execution statistics
        """
        if not results:
            return {
                "avg_execution_time": 0.0,
                "total_execution_time": 0.0,
                "timeout_count": 0,
            }

        execution_times = [r.execution_time for r in results if r.execution_time > 0]
        total_execution_time = sum(execution_times) if execution_times else 0.0
        avg_execution_time = (
            total_execution_time / len(execution_times) if execution_times else 0.0
        )

        # Count timeouts (errors with "TimeoutError")
        timeout_count = sum(
            1
            for r in results
            if r.error_type == "TimeoutError"
            or (r.error_message and "timeout" in r.error_message.lower())
        )

        return {
            "avg_execution_time": round(avg_execution_time, 2),
            "total_execution_time": round(total_execution_time, 2),
            "timeout_count": timeout_count,
        }

    def _generate_empty_json_report(self) -> Dict[str, Any]:
        """Generate empty JSON report for empty results."""
        return {
            "summary": {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "classification_breakdown": {
                    "level_0_failed": 0,
                    "level_1_executed": 0,
                    "level_2_valid_metrics": 0,
                    "level_3_profitable": 0,
                },
            },
            "metrics": asdict(ReportMetrics()),
            "errors": {
                "by_category": {
                    "timeout": 0,
                    "data_missing": 0,
                    "calculation": 0,
                    "syntax": 0,
                    "other": 0,
                },
                "top_errors": [],
            },
            "execution_stats": {
                "avg_execution_time": 0.0,
                "total_execution_time": 0.0,
                "timeout_count": 0,
            },
        }

    def _generate_empty_markdown_report(self) -> str:
        """Generate empty Markdown report for empty results."""
        return """# Backtest Execution Results Report

## Executive Summary

No execution results provided.
"""

    def _generate_markdown_executive_summary(
        self,
        results: List[ExecutionResult],
        classified_results: List[Optional[Any]],
    ) -> List[str]:
        """Generate executive summary section for Markdown."""
        lines = ["## Executive Summary\n"]

        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful

        lines.append(f"- **Total Executions**: {total}")
        lines.append(f"- **Successful**: {successful} ({successful/total*100:.1f}%)")
        lines.append(f"- **Failed**: {failed} ({failed/total*100:.1f}%)")

        # Count profitable strategies
        profitable = sum(
            1
            for c in classified_results
            if c is not None and c.level == 3
        )
        lines.append(f"- **Profitable Strategies (Level 3)**: {profitable}")

        lines.append("")

        return lines

    def _generate_markdown_success_breakdown(
        self, results: List[ExecutionResult]
    ) -> List[str]:
        """Generate success/failure breakdown table."""
        lines = ["## Success/Failure Breakdown\n"]

        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)

        lines.append("| Status | Count | Percentage |")
        lines.append("|--------|-------|------------|")
        lines.append(f"| Successful | {successful} | {successful/len(results)*100:.1f}% |")
        lines.append(f"| Failed | {failed} | {failed/len(results)*100:.1f}% |")
        lines.append("")

        return lines

    def _generate_markdown_classification_table(
        self, classified_results: List[Optional[Any]]
    ) -> List[str]:
        """Generate classification level distribution table."""
        lines = ["## Classification Level Distribution\n"]

        # Count levels
        level_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        level_names = {
            0: "Failed",
            1: "Executed",
            2: "Valid Metrics",
            3: "Profitable",
        }

        for classified in classified_results:
            if classified is not None:
                level_counts[classified.level] = level_counts.get(classified.level, 0) + 1

        total = sum(level_counts.values())

        lines.append("| Level | Name | Count | Percentage |")
        lines.append("|-------|------|-------|------------|")

        for level in range(4):
            count = level_counts.get(level, 0)
            pct = count / total * 100 if total > 0 else 0
            lines.append(
                f"| {level} | {level_names[level]} | {count} | {pct:.1f}% |"
            )

        lines.append("")

        return lines

    def _generate_markdown_errors_table(
        self, error_details: Dict[str, Any]
    ) -> List[str]:
        """Generate errors table."""
        lines = ["## Top Errors\n"]

        if not error_details["top_errors"]:
            lines.append("No errors recorded.\n")
            return lines

        lines.append("| Error Type | Message | Count |")
        lines.append("|------------|---------|-------|")

        for error in error_details["top_errors"]:
            error_type = error["error_type"]
            message = error["message"][:50]  # Truncate long messages
            count = error["count"]
            lines.append(f"| {error_type} | {message} | {count} |")

        lines.append("")

        return lines

    def _generate_markdown_metrics_table(self, metrics: ReportMetrics) -> List[str]:
        """Generate metrics summary table."""
        lines = ["## Performance Metrics Summary\n"]

        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")

        if metrics.avg_sharpe is not None:
            lines.append(f"| Avg Sharpe Ratio | {metrics.avg_sharpe:.4f} |")
        else:
            lines.append("| Avg Sharpe Ratio | N/A |")

        if metrics.avg_return is not None:
            lines.append(f"| Avg Return | {metrics.avg_return:.2%} |")
        else:
            lines.append("| Avg Return | N/A |")

        if metrics.avg_drawdown is not None:
            lines.append(f"| Avg Max Drawdown | {metrics.avg_drawdown:.2%} |")
        else:
            lines.append("| Avg Max Drawdown | N/A |")

        if metrics.win_rate is not None:
            lines.append(f"| Win Rate | {metrics.win_rate:.1%} |")
        else:
            lines.append("| Win Rate | N/A |")

        if metrics.execution_success_rate is not None:
            lines.append(
                f"| Execution Success Rate | {metrics.execution_success_rate:.1%} |"
            )

        lines.append("")

        return lines

    def _generate_markdown_execution_stats(
        self, exec_stats: Dict[str, Any]
    ) -> List[str]:
        """Generate execution statistics section."""
        lines = ["## Execution Statistics\n"]

        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Average Execution Time | {exec_stats['avg_execution_time']:.2f}s |")
        lines.append(f"| Total Execution Time | {exec_stats['total_execution_time']:.2f}s |")
        lines.append(f"| Timeout Count | {exec_stats['timeout_count']} |")
        lines.append("")

        return lines

    @staticmethod
    def _get_level_name(level: int) -> str:
        """Get human-readable name for classification level."""
        level_names = {
            0: "failed",
            1: "executed",
            2: "valid_metrics",
            3: "profitable",
        }
        return level_names.get(level, "unknown")
