"""Usage examples for SuccessClassifier.

Demonstrates how to use the classification system for evaluating
backtest results at different levels of detail.
"""

from src.backtest import ClassificationResult, SuccessClassifier, StrategyMetrics


# Example 1: Single Strategy Classification - Profitable
print("=" * 70)
print("Example 1: Single Strategy - Profitable")
print("=" * 70)

classifier = SuccessClassifier()

# Create metrics for a successful profitable strategy
profitable_metrics = StrategyMetrics(
    sharpe_ratio=1.8,
    total_return=0.35,  # 35% return
    max_drawdown=-0.12,  # 12% max drawdown
    win_rate=0.58,
    execution_success=True
)

result = classifier.classify_single(profitable_metrics)
print(f"Classification Level: {result.level}")
print(f"Reason: {result.reason}")
print(f"Metrics Coverage: {result.metrics_coverage:.1%}")
print()


# Example 2: Single Strategy Classification - Failed Execution
print("=" * 70)
print("Example 2: Single Strategy - Failed Execution")
print("=" * 70)

failed_metrics = StrategyMetrics(
    execution_success=False  # Only this matters for Level 0
)

result = classifier.classify_single(failed_metrics)
print(f"Classification Level: {result.level}")
print(f"Reason: {result.reason}")
print(f"Metrics Coverage: {result.metrics_coverage:.1%}")
print()


# Example 3: Single Strategy - Valid Metrics but Unprofitable
print("=" * 70)
print("Example 3: Single Strategy - Valid Metrics, Not Profitable")
print("=" * 70)

unprofitable_metrics = StrategyMetrics(
    sharpe_ratio=-0.45,  # Negative Sharpe (not profitable)
    total_return=0.08,   # Small positive return
    max_drawdown=-0.25,  # Large drawdown
    execution_success=True
)

result = classifier.classify_single(unprofitable_metrics)
print(f"Classification Level: {result.level}")
print(f"Reason: {result.reason}")
print(f"Metrics Coverage: {result.metrics_coverage:.1%}")
print()


# Example 4: Single Strategy - Partial Metrics Extracted
print("=" * 70)
print("Example 4: Single Strategy - Partial Metrics (Only 1/3)")
print("=" * 70)

partial_metrics = StrategyMetrics(
    sharpe_ratio=1.2,
    total_return=None,      # Missing
    max_drawdown=None,      # Missing
    execution_success=True
)

result = classifier.classify_single(partial_metrics)
print(f"Classification Level: {result.level}")
print(f"Reason: {result.reason}")
print(f"Metrics Coverage: {result.metrics_coverage:.1%}")
print(f"Note: {1}/3 metrics extracted = {100/3:.1f}% < 60% threshold")
print()


# Example 5: Batch Classification - High Profitability
print("=" * 70)
print("Example 5: Batch Classification - High Profitability (4/5 profitable)")
print("=" * 70)

batch_metrics = [
    StrategyMetrics(sharpe_ratio=1.5, total_return=0.25, max_drawdown=-0.15, execution_success=True),
    StrategyMetrics(sharpe_ratio=0.8, total_return=0.18, max_drawdown=-0.18, execution_success=True),
    StrategyMetrics(sharpe_ratio=1.2, total_return=0.22, max_drawdown=-0.14, execution_success=True),
    StrategyMetrics(sharpe_ratio=0.3, total_return=0.12, max_drawdown=-0.20, execution_success=True),
    StrategyMetrics(sharpe_ratio=-0.5, total_return=0.05, max_drawdown=-0.30, execution_success=True),
]

result = classifier.classify_batch(batch_metrics)
print(f"Classification Level: {result.level}")
print(f"Reason: {result.reason}")
print(f"Metrics Coverage: {result.metrics_coverage:.1%} (average)")
print(f"Profitable Count: {result.profitable_count}/{result.total_count}")
print(f"Profitability Ratio: {result.profitable_count/result.total_count:.1%} >= 40% threshold")
print()


# Example 6: Batch Classification - Low Profitability
print("=" * 70)
print("Example 6: Batch Classification - Low Profitability (1/4 profitable)")
print("=" * 70)

batch_low_profit = [
    StrategyMetrics(sharpe_ratio=1.5, total_return=0.25, max_drawdown=-0.15, execution_success=True),
    StrategyMetrics(sharpe_ratio=-0.8, total_return=0.05, max_drawdown=-0.35, execution_success=True),
    StrategyMetrics(sharpe_ratio=-0.5, total_return=0.08, max_drawdown=-0.30, execution_success=True),
    StrategyMetrics(sharpe_ratio=-0.2, total_return=0.10, max_drawdown=-0.25, execution_success=True),
]

result = classifier.classify_batch(batch_low_profit)
print(f"Classification Level: {result.level}")
print(f"Reason: {result.reason}")
print(f"Metrics Coverage: {result.metrics_coverage:.1%} (average)")
print(f"Profitable Count: {result.profitable_count}/{result.total_count}")
print(f"Profitability Ratio: {result.profitable_count/result.total_count:.1%} < 40% threshold")
print()


# Example 7: Batch Classification - Mixed Success/Failure
print("=" * 70)
print("Example 7: Batch - Mixed Success/Failure (2 failed, 3 executed)")
print("=" * 70)

batch_mixed = [
    StrategyMetrics(execution_success=False),  # Failed
    StrategyMetrics(sharpe_ratio=1.5, total_return=0.25, max_drawdown=-0.15, execution_success=True),
    StrategyMetrics(execution_success=False),  # Failed
    StrategyMetrics(sharpe_ratio=0.8, total_return=0.18, max_drawdown=-0.18, execution_success=True),
    StrategyMetrics(sharpe_ratio=1.2, total_return=0.22, max_drawdown=-0.14, execution_success=True),
]

result = classifier.classify_batch(batch_mixed)
print(f"Classification Level: {result.level}")
print(f"Reason: {result.reason}")
print(f"Metrics Coverage: {result.metrics_coverage:.1%} (average, only executed)")
print(f"Profitable Count: {result.profitable_count}/{result.total_count} (only executed)")
print()


# Example 8: Batch Classification - All Failed
print("=" * 70)
print("Example 8: Batch - All Failed Execution (0/5)")
print("=" * 70)

batch_all_failed = [
    StrategyMetrics(execution_success=False),
    StrategyMetrics(execution_success=False),
    StrategyMetrics(execution_success=False),
    StrategyMetrics(execution_success=False),
    StrategyMetrics(execution_success=False),
]

result = classifier.classify_batch(batch_all_failed)
print(f"Classification Level: {result.level}")
print(f"Reason: {result.reason}")
print(f"Metrics Coverage: {result.metrics_coverage:.1%}")
print(f"Profitable Count: {result.profitable_count}/{result.total_count}")
print()


# Example 9: Practical Workflow - Filter by Classification Level
print("=" * 70)
print("Example 9: Practical Workflow - Filtering by Classification Level")
print("=" * 70)

# Simulate backtest results from multiple strategies
all_results = [
    StrategyMetrics(execution_success=False),  # Level 0
    StrategyMetrics(sharpe_ratio=0.5, total_return=None, max_drawdown=None, execution_success=True),  # Level 1
    StrategyMetrics(sharpe_ratio=-0.2, total_return=0.15, max_drawdown=-0.20, execution_success=True),  # Level 2
    StrategyMetrics(sharpe_ratio=1.5, total_return=0.25, max_drawdown=-0.15, execution_success=True),  # Level 3
]

print(f"Total strategies: {len(all_results)}\n")

for i, metrics in enumerate(all_results):
    result = classifier.classify_single(metrics)
    print(f"Strategy {i+1}: Level {result.level} - {result.reason[:50]}...")

# Filter for profitable strategies
profitable = [m for m in all_results if classifier.classify_single(m).level == 3]
print(f"\nProfitable strategies (Level 3): {len(profitable)}/{len(all_results)}")

# Filter for valid metrics (Level 2+)
valid = [m for m in all_results if classifier.classify_single(m).level >= 2]
print(f"Valid metrics (Level 2+): {len(valid)}/{len(all_results)}")

# Filter out failed (Level 0+)
executed = [m for m in all_results if classifier.classify_single(m).level > 0]
print(f"Executed successfully (Level 1+): {len(executed)}/{len(all_results)}")
print()


# Example 10: Classification Thresholds
print("=" * 70)
print("Example 10: Classification System Thresholds")
print("=" * 70)

print(f"Metrics Coverage Threshold: {SuccessClassifier.METRICS_COVERAGE_THRESHOLD:.0%}")
print(f"  - Need at least 2/3 core metrics (sharpe, return, drawdown)")
print(f"  - This ensures sufficient data for strategy evaluation")
print()
print(f"Profitability Threshold: {SuccessClassifier.PROFITABILITY_THRESHOLD:.0%}")
print(f"  - In batch, need >= 40% of strategies with Sharpe > 0")
print(f"  - Example: 4/10 strategies profitable = 40% >= 40% = Level 3")
print(f"  - Example: 3/10 strategies profitable = 30% < 40% = Level 2")
