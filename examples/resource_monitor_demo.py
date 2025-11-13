#!/usr/bin/env python3
"""Demo script showing ResourceMonitor usage.

This demonstrates how to use ResourceMonitor for system resource tracking
during an autonomous learning loop or other long-running process.
"""

import time
from src.monitoring.resource_monitor import ResourceMonitor
from src.monitoring.metrics_collector import MetricsCollector


def demo_basic_usage():
    """Demo 1: Basic usage without MetricsCollector."""
    print("=== Demo 1: Basic ResourceMonitor Usage ===\n")

    monitor = ResourceMonitor()
    monitor.start_monitoring(interval_seconds=2)

    print("Monitoring started. Collecting metrics for 10 seconds...")

    for i in range(5):
        time.sleep(2)
        stats = monitor.get_current_stats()

        print(f"[{i+1}/5] System Stats:")
        print(f"  Memory: {stats['memory_percent']:.1f}% "
              f"({stats['memory_used_gb']:.2f}/{stats['memory_total_gb']:.2f} GB)")
        print(f"  CPU: {stats['cpu_percent']:.1f}%")
        print(f"  Disk: {stats['disk_percent']:.1f}% "
              f"({stats['disk_used_gb']:.1f}/{stats['disk_total_gb']:.1f} GB)")
        print()

    monitor.stop_monitoring()
    print("Monitoring stopped.\n")


def demo_with_metrics_collector():
    """Demo 2: Usage with MetricsCollector for Prometheus export."""
    print("=== Demo 2: ResourceMonitor with MetricsCollector ===\n")

    collector = MetricsCollector()
    monitor = ResourceMonitor(metrics_collector=collector)

    monitor.start_monitoring(interval_seconds=2)

    print("Monitoring with Prometheus export enabled...")
    print("(Metrics would be exported to /metrics endpoint if HTTP server running)\n")

    time.sleep(6)

    stats = monitor.get_current_stats()
    print(f"Latest Stats:")
    print(f"  Memory: {stats['memory_percent']:.1f}%")
    print(f"  CPU: {stats['cpu_percent']:.1f}%")
    print(f"  Disk: {stats['disk_percent']:.1f}%")

    monitor.stop_monitoring()
    print("\nMonitoring stopped.\n")


def demo_context_manager():
    """Demo 3: Using context manager for automatic cleanup."""
    print("=== Demo 3: Context Manager Usage ===\n")

    print("Starting monitoring via context manager...")

    with ResourceMonitor() as monitor:
        time.sleep(4)  # Wait for collection
        stats = monitor.get_current_stats()

        print(f"Collected stats within context:")
        print(f"  Memory: {stats['memory_percent']:.1f}%")
        print(f"  CPU: {stats['cpu_percent']:.1f}%")

    print("Context exited - monitoring automatically stopped.\n")


def demo_during_workload():
    """Demo 4: Monitoring during a simulated workload."""
    print("=== Demo 4: Monitoring During Workload ===\n")

    monitor = ResourceMonitor()
    monitor.start_monitoring(interval_seconds=1)

    print("Running simulated workload...")

    # Simulate some work
    for iteration in range(5):
        print(f"Iteration {iteration + 1}: Processing...")

        # Simulate work (allocate some memory, do calculations)
        data = [i ** 2 for i in range(100000)]
        result = sum(data)

        # Check system stats
        stats = monitor.get_current_stats()
        print(f"  Memory: {stats['memory_percent']:.1f}%, CPU: {stats['cpu_percent']:.1f}%")

        time.sleep(1)

    monitor.stop_monitoring()
    print("\nWorkload complete, monitoring stopped.\n")


def demo_monitoring_overhead():
    """Demo 5: Demonstrate low overhead of monitoring."""
    print("=== Demo 5: Monitoring Overhead Test ===\n")

    print("Running without monitoring...")
    start = time.time()
    for _ in range(10):
        # Simulate work
        _ = sum(i ** 2 for i in range(100000))
    baseline = time.time() - start
    print(f"Baseline time: {baseline:.3f}s")

    print("\nRunning with monitoring...")
    monitor = ResourceMonitor()
    monitor.start_monitoring(interval_seconds=1)

    start = time.time()
    for _ in range(10):
        # Same work
        _ = sum(i ** 2 for i in range(100000))
    monitored = time.time() - start
    print(f"Monitored time: {monitored:.3f}s")

    monitor.stop_monitoring()

    overhead_percent = ((monitored - baseline) / baseline) * 100 if baseline > 0 else 0
    print(f"\nMonitoring overhead: {overhead_percent:.2f}%")
    print(f"✓ Overhead is {'minimal (<1%)' if overhead_percent < 1 else 'acceptable'}\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ResourceMonitor Demo Script")
    print("=" * 60 + "\n")

    demos = [
        demo_basic_usage,
        demo_with_metrics_collector,
        demo_context_manager,
        demo_during_workload,
        demo_monitoring_overhead
    ]

    for demo in demos:
        try:
            demo()
        except KeyboardInterrupt:
            print("\nDemo interrupted by user.\n")
            break
        except Exception as e:
            print(f"Error in demo: {e}\n")

    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)
