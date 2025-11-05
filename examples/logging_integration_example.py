#!/usr/bin/env python3
"""
Example: Structured Logging Integration.

This script demonstrates how to integrate JSON structured logging
into trading system components.

Run this script to see example log output:
    python examples/logging_integration_example.py

View logs:
    cat logs/example.json.log | python -m json.tool
    python scripts/log_analysis/query_logs.py --log-file logs/example.json.log
"""

import time
from src.utils.json_logger import get_event_logger


def simulate_iteration(iteration_num: int, event_logger):
    """
    Simulate a single iteration with structured logging.

    Args:
        iteration_num: Iteration number
        event_logger: EventLogger instance
    """
    start_time = time.time()

    # Log iteration start
    event_logger.log_iteration_start(
        iteration_num=iteration_num,
        model="google/gemini-2.5-flash",
        max_iterations=5,
        has_champion=iteration_num > 0
    )

    # Simulate template recommendation
    event_logger.log_template_recommendation(
        iteration_num=iteration_num,
        template_name="momentum_value_hybrid",
        exploration_mode=(iteration_num % 5 == 0),
        confidence_score=0.85
    )

    # Simulate template instantiation
    time.sleep(0.1)  # Simulate work
    event_logger.log_template_instantiation(
        iteration_num=iteration_num,
        template_name="momentum_value_hybrid",
        success=True,
        retry_count=0
    )

    # Simulate metric extraction
    extraction_start = time.time()
    time.sleep(0.05)  # Simulate extraction
    extraction_duration = (time.time() - extraction_start) * 1000

    event_logger.log_metric_extraction(
        iteration_num=iteration_num,
        method_used="DIRECT",
        success=True,
        duration_ms=extraction_duration,
        metrics={
            "sharpe_ratio": 2.5 + (iteration_num * 0.1),
            "annual_return": 0.35 + (iteration_num * 0.02),
            "max_drawdown": -0.15
        },
        fallback_attempts=0
    )

    # Simulate validation
    validation_start = time.time()
    time.sleep(0.01)  # Simulate validation
    validation_duration = (time.time() - validation_start) * 1000

    event_logger.log_validation_result(
        iteration_num=iteration_num,
        validator_name="MetricValidator",
        passed=True,
        checks_performed=["sharpe_cross_validation", "impossible_combinations"],
        failures=[],
        warnings=[],
        duration_ms=validation_duration
    )

    # Simulate champion update (every 3 iterations)
    if iteration_num > 0 and iteration_num % 3 == 0:
        old_sharpe = 2.5 + ((iteration_num - 3) * 0.1)
        new_sharpe = 2.5 + (iteration_num * 0.1)
        improvement = ((new_sharpe - old_sharpe) / old_sharpe) * 100

        event_logger.log_champion_update(
            iteration_num=iteration_num,
            old_sharpe=old_sharpe,
            new_sharpe=new_sharpe,
            improvement_pct=improvement,
            threshold_type="relative",
            multi_objective_passed=True
        )

    # Log iteration end
    duration = time.time() - start_time
    event_logger.log_iteration_end(
        iteration_num=iteration_num,
        success=True,
        validation_passed=True,
        execution_success=True,
        duration_seconds=duration,
        metrics={
            "sharpe_ratio": 2.5 + (iteration_num * 0.1),
            "annual_return": 0.35 + (iteration_num * 0.02)
        }
    )


def main():
    """Main entry point."""
    print("=" * 80)
    print("STRUCTURED LOGGING INTEGRATION EXAMPLE")
    print("=" * 80)
    print()
    print("This script demonstrates JSON structured logging for the trading system.")
    print()
    print("Running 5 simulated iterations...")
    print("-" * 80)

    # Initialize event logger
    event_logger = get_event_logger(
        logger_name="example_component",
        log_file="example.json.log"
    )

    # Simulate 5 iterations
    for i in range(5):
        print(f"\n[Iteration {i}] Running...")
        simulate_iteration(i, event_logger)
        print(f"[Iteration {i}] Complete")
        time.sleep(0.1)

    print()
    print("-" * 80)
    print("✓ All iterations complete!")
    print()
    print("Log file created: logs/example.json.log")
    print()
    print("View logs with:")
    print("  cat logs/example.json.log | python -m json.tool")
    print()
    print("Query logs with:")
    print("  python scripts/log_analysis/query_logs.py --log-file logs/example.json.log --format compact")
    print()
    print("Analyze performance with:")
    print("  python scripts/log_analysis/analyze_performance.py --log-file logs/example.json.log")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
