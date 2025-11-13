#!/usr/bin/env python3
"""
Example: Using Phase2TestRunner programmatically

This script demonstrates how to use the Phase2TestRunner in your own code
for custom analysis, integration testing, or automated workflows.
"""

import logging
from run_phase2_backtest_execution import Phase2TestRunner

# Setup logging to see detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Example 1: Basic usage - execute all strategies
def example_basic_usage():
    """Execute all 20 strategies with default settings."""
    print("\n=== Example 1: Basic Usage ===\n")

    runner = Phase2TestRunner()
    summary = runner.run()

    print(f"\nExecution Summary:")
    print(f"  Total: {summary['total_strategies']}")
    print(f"  Success: {summary['executed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Time: {summary['execution_time']:.1f}s")


# Example 2: Testing with limited strategies and custom timeout
def example_testing_mode():
    """Execute first 3 strategies with 2-minute timeout for quick testing."""
    print("\n=== Example 2: Testing Mode (3 strategies, 2-min timeout) ===\n")

    runner = Phase2TestRunner(timeout=120, limit=3)
    summary = runner.run(timeout=120, verbose=True)

    # Access detailed results
    for idx, result in enumerate(summary['results']):
        print(f"\nStrategy {idx}:")
        print(f"  Success: {result.success}")
        if result.success:
            print(f"  Sharpe: {result.sharpe_ratio:.2f}")
            print(f"  Return: {result.total_return:.1%}")
            print(f"  Drawdown: {result.max_drawdown:.1%}")
        else:
            print(f"  Error: {result.error_type} - {result.error_message}")


# Example 3: Extract specific metrics from results
def example_metrics_analysis():
    """Execute strategies and analyze metrics in detail."""
    print("\n=== Example 3: Metrics Analysis ===\n")

    runner = Phase2TestRunner(limit=5)
    summary = runner.run(verbose=False)

    # Analyze strategy metrics
    metrics = summary['strategy_metrics']

    print("Strategy Performance Analysis:")
    profitable_strategies = [m for m in metrics if m.execution_success and m.sharpe_ratio and m.sharpe_ratio > 0]
    print(f"  Profitable strategies: {len(profitable_strategies)}/{len(metrics)}")

    if profitable_strategies:
        avg_sharpe = sum(m.sharpe_ratio for m in profitable_strategies) / len(profitable_strategies)
        print(f"  Average Sharpe (profitable): {avg_sharpe:.2f}")

        best_strategy = max(profitable_strategies, key=lambda m: m.sharpe_ratio)
        print(f"  Best Sharpe: {best_strategy.sharpe_ratio:.2f}")


# Example 4: Classification analysis
def example_classification_analysis():
    """Execute strategies and analyze classification levels."""
    print("\n=== Example 4: Classification Analysis ===\n")

    runner = Phase2TestRunner(limit=10)
    summary = runner.run(verbose=False)

    # Count strategies by classification level
    classifications = summary['classifications']
    level_counts = {0: 0, 1: 0, 2: 0, 3: 0}

    for cls in classifications:
        level_counts[cls.level] += 1

    print("Classification Distribution:")
    print(f"  Level 0 (FAILED):        {level_counts[0]}")
    print(f"  Level 1 (EXECUTED):      {level_counts[1]}")
    print(f"  Level 2 (VALID_METRICS): {level_counts[2]}")
    print(f"  Level 3 (PROFITABLE):    {level_counts[3]}")

    # Calculate success rate
    success_rate = (level_counts[2] + level_counts[3]) / len(classifications)
    print(f"\nSuccess Rate (Level 2+3): {success_rate:.1%}")


# Example 5: Error analysis
def example_error_analysis():
    """Execute strategies and analyze error patterns."""
    print("\n=== Example 5: Error Analysis ===\n")

    runner = Phase2TestRunner(limit=10)
    summary = runner.run(verbose=False)

    # Analyze errors
    results = summary['results']
    failed_results = [r for r in results if not r.success]

    print(f"Failed Strategies: {len(failed_results)}/{len(results)}")

    if failed_results:
        # Group by error type
        error_types = {}
        for result in failed_results:
            error_type = result.error_type or "Unknown"
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(result.error_message)

        print("\nError Type Distribution:")
        for error_type, messages in error_types.items():
            print(f"  {error_type}: {len(messages)} occurrences")
            print(f"    Sample: {messages[0][:100]}...")


# Example 6: Custom analysis with JSON report
def example_json_report_analysis():
    """Execute strategies and perform custom analysis on JSON report."""
    print("\n=== Example 6: JSON Report Analysis ===\n")

    runner = Phase2TestRunner(limit=5)
    summary = runner.run(verbose=False)

    # Access JSON report
    report = summary['report']

    print("Report Summary:")
    print(f"  Total strategies: {report['summary']['total_count']}")
    print(f"  Execution success rate: {report['metrics']['execution_success_rate']:.1%}")
    print(f"  Average Sharpe: {report['metrics']['avg_sharpe']:.2f}")
    print(f"  Win rate: {report['metrics']['win_rate']:.1%}")
    print(f"  Total execution time: {report['execution_stats']['total_time_seconds']:.1f}s")

    # Error breakdown
    error_summary = report['errors']['error_summary']
    print("\nError Category Breakdown:")
    for category, count in error_summary.items():
        if count > 0:
            print(f"  {category}: {count}")


# Example 7: Quiet mode execution
def example_quiet_mode():
    """Execute strategies with minimal output."""
    print("\n=== Example 7: Quiet Mode ===\n")

    runner = Phase2TestRunner(limit=3)

    # Run with verbose=False for minimal console output
    summary = runner.run(verbose=False)

    # Only print final summary
    print(f"Execution complete: {summary['executed']}/{summary['total_strategies']} successful")
    print(f"Reports saved to: phase2_backtest_results.json/md")


if __name__ == '__main__':
    import sys

    # Select which example to run
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        examples = {
            '1': example_basic_usage,
            '2': example_testing_mode,
            '3': example_metrics_analysis,
            '4': example_classification_analysis,
            '5': example_error_analysis,
            '6': example_json_report_analysis,
            '7': example_quiet_mode,
        }

        if example_num in examples:
            examples[example_num]()
        else:
            print(f"Unknown example: {example_num}")
            print("Available examples: 1-7")
    else:
        # Run all examples
        print("=" * 80)
        print("PHASE 2 TASK 5.1: PROGRAMMATIC USAGE EXAMPLES")
        print("=" * 80)
        print("\nRun specific example with: python example_phase2_runner_usage.py <num>")
        print("Available examples:")
        print("  1: Basic usage - execute all strategies")
        print("  2: Testing mode - limited strategies with custom timeout")
        print("  3: Metrics analysis - detailed performance analysis")
        print("  4: Classification analysis - level distribution")
        print("  5: Error analysis - error pattern detection")
        print("  6: JSON report analysis - structured data analysis")
        print("  7: Quiet mode - minimal output")
        print("\nNote: Examples use --limit to keep runtime reasonable.")
        print("      Remove limit for full 20-strategy execution.")
