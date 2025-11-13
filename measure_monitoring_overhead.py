"""
Validation Task M3: Monitoring Overhead Real Measurement

Measures actual monitoring overhead by comparing:
1. Baseline: autonomous loop without monitoring
2. With monitoring: autonomous loop with all monitoring enabled
3. Calculate overhead percentage
4. Verify <1% overhead requirement
"""

import sys
import time
import json
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from innovation.innovation_engine import InnovationEngine


def measure_system_resources_before():
    """Capture baseline system resource usage."""
    process = psutil.Process()
    return {
        'cpu_percent': process.cpu_percent(interval=1.0),
        'memory_mb': process.memory_info().rss / 1024 / 1024,
        'system_cpu': psutil.cpu_percent(interval=1.0),
        'system_memory': psutil.virtual_memory().percent
    }


def measure_system_resources_after(before_resources):
    """Calculate resource delta."""
    process = psutil.Process()
    after = {
        'cpu_percent': process.cpu_percent(interval=1.0),
        'memory_mb': process.memory_info().rss / 1024 / 1024,
        'system_cpu': psutil.cpu_percent(interval=1.0),
        'system_memory': psutil.virtual_memory().percent
    }

    return {
        'cpu_delta': after['cpu_percent'] - before_resources['cpu_percent'],
        'memory_delta_mb': after['memory_mb'] - before_resources['memory_mb'],
        'system_cpu_delta': after['system_cpu'] - before_resources['system_cpu'],
        'system_memory_delta': after['system_memory'] - before_resources['system_memory'],
        'final': after
    }


def run_baseline_test(iterations: int = 20) -> Dict[str, Any]:
    """
    Run baseline test WITHOUT monitoring.

    Args:
        iterations: Number of iterations to run

    Returns:
        Test results with timing and resource metrics
    """
    print("=" * 70)
    print("BASELINE TEST (Monitoring Disabled)")
    print("=" * 70)
    print()

    # Measure resources before
    before_resources = measure_system_resources_before()

    # Initialize engine with monitoring DISABLED
    print(f"Initializing InnovationEngine (monitoring DISABLED)...")

    # Create a minimal config that disables monitoring
    import os
    os.environ['MONITORING_ENABLED'] = 'false'

    start_time = time.time()

    engine = InnovationEngine(
        baseline_sharpe=0.680,
        baseline_calmar=2.406,
        innovation_frequency=0.20,
        use_mock_llm=True,  # Use mock for consistent timing
        repository_path="artifacts/data/baseline_test_innovations.jsonl"
    )

    print(f"✅ Engine initialized (monitoring: DISABLED)")
    print()

    # Run iterations
    categories = ['quality', 'value', 'growth', 'momentum', 'mixed']
    iteration_times = []

    print(f"Running {iterations} iterations...")
    print()

    for i in range(iterations):
        iter_start = time.time()

        if engine.should_innovate():
            category = categories[i % len(categories)]
            success, code, failure_reason = engine.attempt_innovation(
                iteration=i,
                category=category
            )

        iter_end = time.time()
        iteration_times.append(iter_end - iter_start)

        if (i + 1) % 5 == 0:
            print(f"  Completed {i + 1}/{iterations} iterations...")

    end_time = time.time()
    total_time = end_time - start_time

    # Measure resources after
    after_resources = measure_system_resources_after(before_resources)

    # Clean up
    os.environ.pop('MONITORING_ENABLED', None)

    print()
    print(f"✅ Baseline test completed in {total_time:.2f}s")
    print()

    # Calculate statistics
    avg_iteration_time = sum(iteration_times) / len(iteration_times)

    results = {
        'test_type': 'baseline',
        'iterations': iterations,
        'total_time_seconds': total_time,
        'avg_iteration_time_seconds': avg_iteration_time,
        'iteration_times': iteration_times,
        'resources': {
            'before': before_resources,
            'after': after_resources['final'],
            'delta': {
                'cpu_percent': after_resources['cpu_delta'],
                'memory_mb': after_resources['memory_delta_mb'],
                'system_cpu': after_resources['system_cpu_delta'],
                'system_memory': after_resources['system_memory_delta']
            }
        },
        'timestamp': datetime.now().isoformat()
    }

    return results


def run_monitoring_test(iterations: int = 20) -> Dict[str, Any]:
    """
    Run test WITH monitoring enabled.

    Args:
        iterations: Number of iterations to run

    Returns:
        Test results with timing and resource metrics
    """
    print("=" * 70)
    print("MONITORING TEST (Monitoring Enabled)")
    print("=" * 70)
    print()

    # Measure resources before
    before_resources = measure_system_resources_before()

    # Initialize engine with monitoring ENABLED
    print(f"Initializing InnovationEngine (monitoring ENABLED)...")

    # Ensure monitoring is enabled
    import os
    os.environ['MONITORING_ENABLED'] = 'true'

    start_time = time.time()

    engine = InnovationEngine(
        baseline_sharpe=0.680,
        baseline_calmar=2.406,
        innovation_frequency=0.20,
        use_mock_llm=True,  # Use mock for consistent timing
        repository_path="artifacts/data/monitoring_test_innovations.jsonl"
    )

    print(f"✅ Engine initialized (monitoring: ENABLED)")
    print()

    # Run iterations
    categories = ['quality', 'value', 'growth', 'momentum', 'mixed']
    iteration_times = []

    print(f"Running {iterations} iterations...")
    print()

    for i in range(iterations):
        iter_start = time.time()

        if engine.should_innovate():
            category = categories[i % len(categories)]
            success, code, failure_reason = engine.attempt_innovation(
                iteration=i,
                category=category
            )

        iter_end = time.time()
        iteration_times.append(iter_end - iter_start)

        if (i + 1) % 5 == 0:
            print(f"  Completed {i + 1}/{iterations} iterations...")

    end_time = time.time()
    total_time = end_time - start_time

    # Measure resources after
    after_resources = measure_system_resources_after(before_resources)

    # Clean up
    os.environ.pop('MONITORING_ENABLED', None)

    print()
    print(f"✅ Monitoring test completed in {total_time:.2f}s")
    print()

    # Calculate statistics
    avg_iteration_time = sum(iteration_times) / len(iteration_times)

    results = {
        'test_type': 'monitoring',
        'iterations': iterations,
        'total_time_seconds': total_time,
        'avg_iteration_time_seconds': avg_iteration_time,
        'iteration_times': iteration_times,
        'resources': {
            'before': before_resources,
            'after': after_resources['final'],
            'delta': {
                'cpu_percent': after_resources['cpu_delta'],
                'memory_mb': after_resources['memory_delta_mb'],
                'system_cpu': after_resources['system_cpu_delta'],
                'system_memory': after_resources['system_memory_delta']
            }
        },
        'timestamp': datetime.now().isoformat()
    }

    return results


def calculate_overhead(baseline_results: Dict, monitoring_results: Dict) -> Dict[str, Any]:
    """
    Calculate overhead percentage.

    Args:
        baseline_results: Results from baseline test
        monitoring_results: Results from monitoring test

    Returns:
        Overhead analysis
    """
    baseline_time = baseline_results['total_time_seconds']
    monitoring_time = monitoring_results['total_time_seconds']

    time_overhead_percent = ((monitoring_time - baseline_time) / baseline_time) * 100 if baseline_time > 0 else 0

    baseline_iter_time = baseline_results['avg_iteration_time_seconds']
    monitoring_iter_time = monitoring_results['avg_iteration_time_seconds']

    iter_overhead_percent = ((monitoring_iter_time - baseline_iter_time) / baseline_iter_time) * 100 if baseline_iter_time > 0 else 0

    memory_overhead_mb = monitoring_results['resources']['delta']['memory_mb'] - baseline_results['resources']['delta']['memory_mb']

    analysis = {
        'baseline_total_time_seconds': baseline_time,
        'monitoring_total_time_seconds': monitoring_time,
        'time_difference_seconds': monitoring_time - baseline_time,
        'time_overhead_percent': time_overhead_percent,

        'baseline_avg_iteration_time_seconds': baseline_iter_time,
        'monitoring_avg_iteration_time_seconds': monitoring_iter_time,
        'iteration_time_difference_seconds': monitoring_iter_time - baseline_iter_time,
        'iteration_overhead_percent': iter_overhead_percent,

        'memory_overhead_mb': memory_overhead_mb,

        'target_overhead_ideal_percent': 1.0,
        'target_overhead_acceptable_percent': 5.0,

        'status': 'PASS (IDEAL)' if time_overhead_percent < 1.0 else (
            'PASS (ACCEPTABLE)' if time_overhead_percent < 5.0 else 'FAIL'
        )
    }

    return analysis


def main():
    """Run overhead measurement test."""
    import argparse

    parser = argparse.ArgumentParser(description="Measure monitoring overhead")
    parser.add_argument('--iterations', type=int, default=20,
                       help='Number of iterations to run (default: 20, validation uses 100)')
    args = parser.parse_args()

    print("=" * 70)
    print("VALIDATION TASK M3: MONITORING OVERHEAD MEASUREMENT")
    print("=" * 70)
    print()
    print(f"Test Configuration:")
    print(f"  Iterations: {args.iterations}")
    print(f"  LLM: MockLLMClient (consistent timing)")
    print(f"  Target overhead: <1% (ideal), <5% (acceptable)")
    print()

    # Run baseline test
    baseline_results = run_baseline_test(args.iterations)

    # Wait a bit between tests
    print("Waiting 5 seconds between tests...")
    time.sleep(5)
    print()

    # Run monitoring test
    monitoring_results = run_monitoring_test(args.iterations)

    # Calculate overhead
    overhead_analysis = calculate_overhead(baseline_results, monitoring_results)

    # Print results
    print("=" * 70)
    print("OVERHEAD ANALYSIS")
    print("=" * 70)
    print()

    print(f"Timing Results:")
    print(f"  Baseline total time:     {overhead_analysis['baseline_total_time_seconds']:.2f}s")
    print(f"  Monitoring total time:   {overhead_analysis['monitoring_total_time_seconds']:.2f}s")
    print(f"  Time difference:         {overhead_analysis['time_difference_seconds']:.2f}s")
    print(f"  Time overhead:           {overhead_analysis['time_overhead_percent']:.3f}%")
    print()

    print(f"Per-Iteration Results:")
    print(f"  Baseline avg:            {overhead_analysis['baseline_avg_iteration_time_seconds']:.4f}s")
    print(f"  Monitoring avg:          {overhead_analysis['monitoring_avg_iteration_time_seconds']:.4f}s")
    print(f"  Difference:              {overhead_analysis['iteration_time_difference_seconds']:.4f}s")
    print(f"  Iteration overhead:      {overhead_analysis['iteration_overhead_percent']:.3f}%")
    print()

    print(f"Memory Results:")
    print(f"  Baseline delta:          {baseline_results['resources']['delta']['memory_mb']:.2f} MB")
    print(f"  Monitoring delta:        {monitoring_results['resources']['delta']['memory_mb']:.2f} MB")
    print(f"  Memory overhead:         {overhead_analysis['memory_overhead_mb']:.2f} MB")
    print()

    print(f"Success Criteria:")
    print(f"  Target overhead (ideal):      <{overhead_analysis['target_overhead_ideal_percent']}%")
    print(f"  Target overhead (acceptable): <{overhead_analysis['target_overhead_acceptable_percent']}%")
    print(f"  Actual overhead:              {overhead_analysis['time_overhead_percent']:.3f}%")
    print(f"  Status:                       {overhead_analysis['status']}")
    print()

    # Save results
    output = {
        'test_metadata': {
            'test_name': 'Monitoring Overhead Measurement',
            'task': 'M3',
            'iterations': args.iterations,
            'timestamp': datetime.now().isoformat()
        },
        'baseline': baseline_results,
        'monitoring': monitoring_results,
        'overhead_analysis': overhead_analysis
    }

    output_file = "monitoring_overhead_measurement_results.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"📊 Results saved to: {output_file}")
    print("=" * 70)

    # Return success/failure
    if overhead_analysis['status'].startswith('PASS'):
        print("\n✅ VALIDATION TASK M3: PASSED")
        return 0
    else:
        print("\n❌ VALIDATION TASK M3: FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
