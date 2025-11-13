"""Complete example of monitoring integration with autonomous loop.

This example demonstrates how to:
1. Initialize the MetricsCollector
2. Integrate with AutonomousLoop
3. Record metrics during iteration execution
4. Export metrics in multiple formats
5. Generate summary reports

Usage:
    python examples/monitoring_integration_example.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.monitoring.metrics_collector import MetricsCollector
import time
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def simulate_iteration(collector: MetricsCollector, iteration_num: int) -> dict:
    """Simulate a single iteration with metrics collection.

    Args:
        collector: MetricsCollector instance
        iteration_num: Current iteration number

    Returns:
        Dictionary with iteration results
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Iteration {iteration_num}")
    logger.info(f"{'='*60}")

    # Record iteration start
    collector.record_iteration_start(iteration_num)

    # Simulate generation
    gen_start = time.time()
    logger.info("Generating strategy...")
    time.sleep(0.5)  # Simulate LLM call
    gen_duration = time.time() - gen_start
    collector.record_generation_time(gen_duration)
    logger.info(f"  ✓ Generation complete ({gen_duration:.2f}s)")

    # Simulate validation
    val_start = time.time()
    logger.info("Validating code...")
    time.sleep(0.1)  # Simulate AST validation
    val_duration = time.time() - val_start
    collector.record_validation_time(val_duration)

    # 90% pass rate
    validation_passed = (iteration_num % 10) != 0
    collector.record_validation_result(passed=validation_passed)

    if not validation_passed:
        logger.warning("  ✗ Validation failed")
        collector.record_error("validation")
        return {"success": False, "error": "validation"}

    logger.info(f"  ✓ Validation passed ({val_duration:.2f}s)")

    # Simulate execution
    exec_start = time.time()
    logger.info("Executing strategy...")
    time.sleep(1.0)  # Simulate backtest
    exec_duration = time.time() - exec_start
    collector.record_execution_time(exec_duration)

    # 80% success rate
    execution_success = (iteration_num % 5) != 0
    collector.record_execution_result(success=execution_success)

    if not execution_success:
        logger.warning("  ✗ Execution failed")
        collector.record_error("execution")
        return {"success": False, "error": "execution"}

    logger.info(f"  ✓ Execution complete ({exec_duration:.2f}s)")

    # Simulate metric extraction
    extract_start = time.time()
    logger.info("Extracting metrics...")

    # Determine extraction method (80% DIRECT, 15% SIGNAL, 5% DEFAULT)
    if iteration_num % 20 == 0:
        method = "DEFAULT"
        time.sleep(0.05)
        collector.record_suspicious_metrics()
    elif iteration_num % 10 == 0:
        method = "SIGNAL"
        time.sleep(0.5)  # SIGNAL method is slower
    else:
        method = "DIRECT"
        time.sleep(0.1)  # DIRECT is fast

    extract_duration = time.time() - extract_start
    collector.record_metric_extraction_time(extract_duration, method)
    logger.info(f"  ✓ Metrics extracted ({extract_duration:.2f}s, method={method})")

    # Generate mock Sharpe ratio (varies between 1.0 and 3.0)
    base_sharpe = 1.5
    variation = 0.5 * ((iteration_num % 10) / 10)
    sharpe_ratio = base_sharpe + variation + (0.1 if iteration_num > 5 else 0)

    # Record successful iteration
    total_duration = time.time() - gen_start
    collector.record_iteration_success(
        sharpe_ratio=sharpe_ratio,
        duration=total_duration
    )

    logger.info(f"  ✓ Iteration complete")
    logger.info(f"    Sharpe Ratio: {sharpe_ratio:.4f}")
    logger.info(f"    Total Duration: {total_duration:.2f}s")

    return {
        "success": True,
        "sharpe_ratio": sharpe_ratio,
        "duration": total_duration,
        "extraction_method": method
    }


def simulate_champion_updates(collector: MetricsCollector, results: list):
    """Simulate champion strategy updates.

    Args:
        collector: MetricsCollector instance
        results: List of iteration results
    """
    best_sharpe = 0.0
    champion_iteration = -1

    for i, result in enumerate(results):
        if not result["success"]:
            collector.record_champion_age_increment()
            continue

        current_sharpe = result["sharpe_ratio"]

        # Champion update logic (5% improvement threshold)
        if current_sharpe > best_sharpe * 1.05:
            logger.info(f"  🏆 Champion update: {best_sharpe:.4f} → {current_sharpe:.4f}")
            collector.record_champion_update(
                old_sharpe=best_sharpe if best_sharpe > 0 else 1.0,
                new_sharpe=current_sharpe,
                iteration_num=i
            )
            best_sharpe = current_sharpe
            champion_iteration = i
        else:
            collector.record_champion_age_increment()


def export_metrics(collector: MetricsCollector, iteration: int):
    """Export metrics to multiple formats.

    Args:
        collector: MetricsCollector instance
        iteration: Current iteration number
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Exporting Metrics (Iteration {iteration})")
    logger.info(f"{'='*60}")

    # Export Prometheus format
    prometheus_file = f'metrics_prometheus_iter{iteration}.txt'
    with open(prometheus_file, 'w') as f:
        f.write(collector.export_prometheus())
    logger.info(f"  ✓ Prometheus: {prometheus_file}")

    # Export JSON format
    json_file = f'metrics_json_iter{iteration}.json'
    with open(json_file, 'w') as f:
        f.write(collector.export_json(include_history=True))
    logger.info(f"  ✓ JSON: {json_file}")

    # Print summary
    summary = collector.get_summary()
    logger.info(f"\n📊 Summary:")
    logger.info(f"  Learning:")
    logger.info(f"    - Total Iterations: {summary['learning']['total_iterations']}")
    logger.info(f"    - Success Rate: {summary['learning']['success_rate']:.1f}%")
    logger.info(f"    - Best Sharpe: {summary['learning']['best_sharpe']:.4f}")
    logger.info(f"    - Champion Updates: {summary['learning']['champion_updates']}")
    logger.info(f"  Performance:")
    logger.info(f"    - Avg Iteration Duration: {summary['performance']['avg_iteration_duration']:.2f}s")
    logger.info(f"  Quality:")
    logger.info(f"    - Validation Pass Rate: {summary['quality']['validation_pass_rate']:.1f}%")
    logger.info(f"  System:")
    logger.info(f"    - Uptime: {summary['system']['uptime_seconds']:.1f}s")


def main():
    """Main execution function."""
    logger.info("="*60)
    logger.info("Monitoring Integration Example")
    logger.info("="*60)

    # Initialize metrics collector
    collector = MetricsCollector(history_window=100)
    logger.info("✓ MetricsCollector initialized (history_window=100)")

    # Simulate 20 iterations
    num_iterations = 20
    results = []

    for i in range(num_iterations):
        result = simulate_iteration(collector, i)
        results.append(result)

        # Export metrics every 5 iterations
        if (i + 1) % 5 == 0:
            export_metrics(collector, i + 1)

    # Simulate champion updates
    logger.info(f"\n{'='*60}")
    logger.info("Processing Champion Updates")
    logger.info(f"{'='*60}")
    simulate_champion_updates(collector, results)

    # Simulate some API calls
    logger.info(f"\n{'='*60}")
    logger.info("Simulating API Interactions")
    logger.info(f"{'='*60}")

    for i in range(num_iterations):
        success = (i % 10) != 0  # 90% success rate
        retries = 1 if not success else 0
        collector.record_api_call(success=success, retries=retries)

    logger.info(f"  ✓ Recorded {num_iterations} API calls")

    # Simulate fallback usage
    fallback_count = num_iterations // 10  # 10% fallback rate
    for _ in range(fallback_count):
        collector.record_fallback_usage()

    logger.info(f"  ✓ Recorded {fallback_count} fallback usages")

    # Simulate variance alerts
    variance_alerts = 2
    for _ in range(variance_alerts):
        collector.record_variance_alert()

    logger.info(f"  ✓ Recorded {variance_alerts} variance alerts")

    # Final export
    logger.info(f"\n{'='*60}")
    logger.info("Final Metrics Export")
    logger.info(f"{'='*60}")

    # Prometheus format
    with open('metrics_final.txt', 'w') as f:
        f.write(collector.export_prometheus())
    logger.info("  ✓ Prometheus: metrics_final.txt")

    # JSON format
    with open('metrics_final.json', 'w') as f:
        f.write(collector.export_json(include_history=True))
    logger.info("  ✓ JSON: metrics_final.json")

    # Final summary
    summary = collector.get_summary()
    logger.info(f"\n{'='*60}")
    logger.info("📈 Final Summary")
    logger.info(f"{'='*60}")

    logger.info(f"\n🎯 Learning Metrics:")
    logger.info(f"  - Total Iterations: {summary['learning']['total_iterations']}")
    logger.info(f"  - Successful: {summary['learning']['successful_iterations']}")
    logger.info(f"  - Success Rate: {summary['learning']['success_rate']:.1f}%")
    logger.info(f"  - Current Sharpe: {summary['learning']['current_sharpe']:.4f}")
    logger.info(f"  - Average Sharpe: {summary['learning']['average_sharpe']:.4f}")
    logger.info(f"  - Best Sharpe: {summary['learning']['best_sharpe']:.4f}")
    logger.info(f"  - Champion Updates: {summary['learning']['champion_updates']}")
    logger.info(f"  - Champion Age: {summary['learning']['champion_age']} iterations")

    logger.info(f"\n⚡ Performance Metrics:")
    logger.info(f"  - Avg Iteration Duration: {summary['performance']['avg_iteration_duration']:.2f}s")
    logger.info(f"  - Avg Generation Time: {summary['performance']['avg_generation_time']:.2f}s")
    logger.info(f"  - Avg Execution Time: {summary['performance']['avg_execution_time']:.2f}s")
    logger.info(f"  - Avg Extraction Time: {summary['performance']['avg_extraction_time']:.2f}s")

    logger.info(f"\n✅ Quality Metrics:")
    logger.info(f"  - Validation Pass Rate: {summary['quality']['validation_pass_rate']:.1f}%")
    logger.info(f"  - Validation Passed: {summary['quality']['validation_passed']}")
    logger.info(f"  - Validation Failed: {summary['quality']['validation_failed']}")
    logger.info(f"  - Execution Success: {summary['quality']['execution_success']}")
    logger.info(f"  - Execution Failed: {summary['quality']['execution_failed']}")
    logger.info(f"  - Preservation Validated: {summary['quality']['preservation_validated']}")
    logger.info(f"  - Preservation Failed: {summary['quality']['preservation_failed']}")

    logger.info(f"\n🔧 System Metrics:")
    logger.info(f"  - API Calls: {summary['system']['api_calls']}")
    logger.info(f"  - API Errors: {summary['system']['api_errors']}")
    logger.info(f"  - API Retries: {summary['system']['api_retries']}")
    logger.info(f"  - Fallback Used: {summary['system']['fallback_used']}")
    logger.info(f"  - Variance Alerts: {summary['system']['variance_alerts']}")
    logger.info(f"  - Uptime: {summary['system']['uptime_seconds']:.1f}s")

    logger.info(f"\n{'='*60}")
    logger.info("✅ Example Complete")
    logger.info(f"{'='*60}")
    logger.info("\nGenerated Files:")
    logger.info("  - metrics_final.txt (Prometheus format)")
    logger.info("  - metrics_final.json (JSON format with history)")
    logger.info("  - metrics_prometheus_iter*.txt (checkpoints)")
    logger.info("  - metrics_json_iter*.json (checkpoints)")


if __name__ == '__main__':
    main()
