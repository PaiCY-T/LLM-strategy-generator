#!/usr/bin/env python3
"""Example usage of Phase 2 Task 4.1 - ResultsReporter.

Demonstrates how to use the ResultsReporter class to generate
JSON and Markdown reports from backtest execution results.
"""

from src.backtest import ExecutionResult, ResultsReporter


def main():
    """Demonstrate ResultsReporter usage."""

    # Create a reporter instance
    reporter = ResultsReporter()

    # Example 1: Create mock execution results
    print("=== Creating Mock Execution Results ===\n")

    results = [
        # Successful execution with strong metrics
        ExecutionResult(
            success=True,
            error_type=None,
            error_message=None,
            execution_time=5.2,
            sharpe_ratio=1.8,
            total_return=0.30,
            max_drawdown=-0.12,
            report=None,
            stack_trace=None,
        ),
        # Successful execution with moderate metrics
        ExecutionResult(
            success=True,
            error_type=None,
            error_message=None,
            execution_time=4.1,
            sharpe_ratio=0.9,
            total_return=0.15,
            max_drawdown=-0.18,
            report=None,
            stack_trace=None,
        ),
        # Successful execution but with negative returns
        ExecutionResult(
            success=True,
            error_type=None,
            error_message=None,
            execution_time=3.8,
            sharpe_ratio=-0.3,
            total_return=-0.08,
            max_drawdown=-0.25,
            report=None,
            stack_trace=None,
        ),
        # Failed execution - timeout
        ExecutionResult(
            success=False,
            error_type="TimeoutError",
            error_message="Execution exceeded timeout of 420 seconds",
            execution_time=420.0,
            sharpe_ratio=None,
            total_return=None,
            max_drawdown=None,
            report=None,
            stack_trace="...",
        ),
        # Failed execution - missing data
        ExecutionResult(
            success=False,
            error_type="KeyError",
            error_message="key 'price:close' not found in dataset",
            execution_time=1.5,
            sharpe_ratio=None,
            total_return=None,
            max_drawdown=None,
            report=None,
            stack_trace="...",
        ),
    ]

    print(f"Created {len(results)} mock execution results")
    print(f"  - Successful: {sum(1 for r in results if r.success)}")
    print(f"  - Failed: {sum(1 for r in results if not r.success)}\n")


    # Example 2: Generate JSON report
    print("=== Generating JSON Report ===\n")

    json_report = reporter.generate_json_report(results)

    print("JSON Report Summary:")
    print(f"  Total: {json_report['summary']['total']}")
    print(f"  Successful: {json_report['summary']['successful']}")
    print(f"  Failed: {json_report['summary']['failed']}")
    print(f"\nClassification Breakdown:")
    for level_name, count in json_report['summary']['classification_breakdown'].items():
        print(f"  {level_name}: {count}")

    print(f"\nPerformance Metrics:")
    metrics = json_report['metrics']
    print(f"  Avg Sharpe: {metrics['avg_sharpe']:.4f}")
    print(f"  Avg Return: {metrics['avg_return']:.2%}")
    print(f"  Avg Drawdown: {metrics['avg_drawdown']:.2%}")
    print(f"  Win Rate: {metrics['win_rate']:.1%}")
    print(f"  Success Rate: {metrics['execution_success_rate']:.1%}")

    print(f"\nError Statistics:")
    errors = json_report['errors']
    print(f"  By Category:")
    for category, count in errors['by_category'].items():
        if count > 0:
            print(f"    {category}: {count}")
    print(f"  Top Errors: {len(errors['top_errors'])} unique errors")

    print(f"\nExecution Statistics:")
    exec_stats = json_report['execution_stats']
    print(f"  Avg Time: {exec_stats['avg_execution_time']:.2f}s")
    print(f"  Total Time: {exec_stats['total_execution_time']:.2f}s")
    print(f"  Timeouts: {exec_stats['timeout_count']}\n")


    # Example 3: Save JSON report to file
    print("=== Saving JSON Report ===\n")

    json_path = reporter.save_report(
        json_report,
        "/tmp/backtest_report.json",
        format="json"
    )
    print(f"JSON report saved to: {json_path}\n")


    # Example 4: Generate Markdown report
    print("=== Generating Markdown Report ===\n")

    md_report = reporter.generate_markdown_report(results)

    # Print first 500 characters
    print("Markdown Report (first 500 chars):")
    print("-" * 50)
    print(md_report[:500])
    print("...")
    print("-" * 50)
    print()


    # Example 5: Save Markdown report to file
    print("=== Saving Markdown Report ===\n")

    md_path = reporter.save_report(
        md_report,
        "/tmp/backtest_report.md",
        format="markdown"
    )
    print(f"Markdown report saved to: {md_path}\n")


    # Example 6: Handle empty results
    print("=== Handling Empty Results ===\n")

    empty_json = reporter.generate_json_report([])
    print(f"Empty JSON report summary: {empty_json['summary']}\n")

    empty_md = reporter.generate_markdown_report([])
    print(f"Empty Markdown report (first 100 chars): {empty_md[:100]}...\n")


    print("=== Usage Examples Complete ===")


if __name__ == "__main__":
    main()
