#!/usr/bin/env python3
"""
Exit Mutation Metrics Demonstration

This script demonstrates the exit mutation metrics tracking system
implemented in Task 3.2 of the exit-mutation-redesign spec.

Features demonstrated:
1. Recording exit mutation attempts (success/failure)
2. Tracking mutation duration
3. Computing success rates
4. Getting comprehensive statistics
5. Exporting metrics to Prometheus format

Usage:
    python3 examples/exit_mutation_metrics_demo.py
"""

import time
import random
from src.monitoring.metrics_collector import MetricsCollector


def simulate_exit_mutation(collector: MetricsCollector, success_probability: float = 0.8):
    """
    Simulate a single exit mutation with random duration and success.

    Args:
        collector: MetricsCollector instance
        success_probability: Probability of success (0.0-1.0)
    """
    # Simulate mutation duration (100-500ms)
    duration = random.uniform(0.1, 0.5)
    time.sleep(duration / 10)  # Short sleep for demo

    # Determine success
    success = random.random() < success_probability

    # Record mutation
    collector.record_exit_mutation(success=success, duration=duration)

    return success, duration


def main():
    """Main demonstration function."""
    print("=" * 80)
    print("Exit Mutation Metrics Demonstration (Task 3.2)")
    print("=" * 80)
    print()

    # Initialize metrics collector
    collector = MetricsCollector()
    print("✓ MetricsCollector initialized")
    print()

    # Simulate 50 exit mutations
    print("Simulating 50 exit mutations...")
    print("-" * 80)

    successes = 0
    failures = 0

    for i in range(50):
        success, duration = simulate_exit_mutation(collector)

        if success:
            successes += 1
            status = "✓ SUCCESS"
        else:
            failures += 1
            status = "✗ FAILURE"

        # Print every 10th mutation
        if (i + 1) % 10 == 0:
            print(f"Mutation {i+1:3d}: {status} (duration: {duration*1000:.2f}ms)")

    print()
    print(f"Total: {successes} successes, {failures} failures")
    print()

    # Get comprehensive statistics
    print("=" * 80)
    print("Exit Mutation Statistics")
    print("=" * 80)

    stats = collector.get_exit_mutation_statistics()

    print(f"Total mutations:     {stats['total']}")
    print(f"Successful:          {stats['successes']}")
    print(f"Failed:              {stats['failures']}")
    print(f"Success rate:        {stats['success_percentage']:.1f}%")
    print()

    print("Duration Statistics:")
    print(f"  Average:           {stats['avg_duration_seconds']*1000:.2f}ms")
    print(f"  Recent (last 10):  {stats['recent_avg_duration_seconds']*1000:.2f}ms")

    if stats['duration_statistics']:
        duration_stats = stats['duration_statistics']
        print(f"  Min:               {duration_stats['min']*1000:.2f}ms")
        print(f"  Median (p50):      {duration_stats['p50']*1000:.2f}ms")
        print(f"  p95:               {duration_stats['p95']*1000:.2f}ms")
        print(f"  p99:               {duration_stats['p99']*1000:.2f}ms")
        print(f"  Max:               {duration_stats['max']*1000:.2f}ms")

    print()

    # Display summary
    print("=" * 80)
    print("Overall Summary (Exit Mutations Section)")
    print("=" * 80)

    summary = collector.get_summary()
    exit_summary = summary.get('exit_mutations', {})

    print(f"Total:               {exit_summary.get('total', 0)}")
    print(f"Successes:           {exit_summary.get('successes', 0)}")
    print(f"Success Rate:        {exit_summary.get('success_rate', 0.0):.1%}")
    print(f"Avg Duration:        {exit_summary.get('avg_duration', 0.0)*1000:.2f}ms")
    print()

    # Export Prometheus metrics
    print("=" * 80)
    print("Prometheus Export (Exit Mutation Metrics)")
    print("=" * 80)

    prometheus_output = collector.export_prometheus()

    # Extract exit mutation metrics from output
    exit_metrics = [
        line for line in prometheus_output.split('\n')
        if 'exit_mutation' in line.lower()
    ]

    for line in exit_metrics:
        if line.strip():
            print(line)

    print()
    print("=" * 80)
    print("Demonstration Complete!")
    print("=" * 80)
    print()
    print("All 4 required metrics have been demonstrated:")
    print("  1. ✓ exit_mutations_total (Counter)")
    print("  2. ✓ exit_mutations_success (Counter)")
    print("  3. ✓ exit_mutation_success_rate (Gauge)")
    print("  4. ✓ exit_mutation_duration_seconds (Histogram)")
    print()


if __name__ == '__main__':
    main()
