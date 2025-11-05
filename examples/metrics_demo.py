"""Demonstration of MetricsCollector with Resource Monitoring Metrics.

This script demonstrates the new metrics added in Task 5 of the
resource-monitoring-system spec. It shows how to record and export metrics
from all monitoring modules:
- ResourceMonitor
- DiversityMonitor
- ContainerMonitor
- AlertManager

Run this to see the complete Prometheus export with all metrics.
"""

from src.monitoring.metrics_collector import MetricsCollector


def main():
    """Demonstrate MetricsCollector with all new metrics."""

    print("=" * 80)
    print("MetricsCollector - Resource Monitoring Metrics Demo")
    print("=" * 80)
    print()

    # Create metrics collector
    collector = MetricsCollector()

    # Simulate resource monitoring data
    print("1. Recording resource metrics...")
    collector.record_resource_memory(
        used_bytes=8 * 1024**3,   # 8 GB
        total_bytes=16 * 1024**3,  # 16 GB
        percent=50.0
    )
    collector.record_resource_cpu(percent=45.5)
    collector.record_resource_disk(
        used_bytes=100 * 1024**3,  # 100 GB
        total_bytes=200 * 1024**3,  # 200 GB
        percent=50.0
    )
    print("   - Memory: 50.0% (8 GB / 16 GB)")
    print("   - CPU: 45.5%")
    print("   - Disk: 50.0% (100 GB / 200 GB)")
    print()

    # Simulate diversity monitoring data
    print("2. Recording diversity metrics...")
    collector.record_diversity_metrics(
        diversity=0.85,
        unique_count=42,
        total_count=50,
        staleness=5,
        collapse_detected=False
    )
    print("   - Population diversity: 0.85")
    print("   - Unique individuals: 42 / 50")
    print("   - Champion staleness: 5 iterations")
    print("   - Collapse detected: No")
    print()

    # Simulate container monitoring data
    print("3. Recording container metrics...")
    collector.record_container_counts(active=3, orphaned=1)
    collector.record_container_created()
    collector.record_container_created()
    collector.record_container_memory(
        container_id="abc123def456",
        memory_bytes=512 * 1024**2,
        limit_bytes=1024 * 1024**2,
        percent=50.0
    )
    collector.record_container_cpu(
        container_id="abc123def456",
        cpu_percent=25.5
    )
    collector.record_container_cleanup(success=True)
    print("   - Active containers: 3")
    print("   - Orphaned containers: 1")
    print("   - Containers created: 2")
    print("   - Container abc123def45: 50.0% memory, 25.5% CPU")
    print("   - Successful cleanups: 1")
    print()

    # Simulate alert data
    print("4. Recording alert metrics...")
    collector.record_alert_triggered("high_memory")
    collector.record_alert_triggered("diversity_collapse")
    collector.record_active_alerts(count=2)
    print("   - Alerts triggered: 2 (high_memory, diversity_collapse)")
    print("   - Active alerts: 2")
    print()

    # Display summary
    print("=" * 80)
    print("Metrics Summary")
    print("=" * 80)
    summary = collector.get_summary()

    print("\nResources:")
    print(f"  Memory: {summary['resources']['memory_percent']}%")
    print(f"  CPU: {summary['resources']['cpu_percent']}%")
    print(f"  Disk: {summary['resources']['disk_percent']}%")

    print("\nDiversity:")
    print(f"  Population diversity: {summary['diversity']['population_diversity']}")
    print(f"  Unique count: {summary['diversity']['unique_count']}")
    print(f"  Champion staleness: {summary['diversity']['champion_staleness']}")
    print(f"  Collapse detected: {summary['diversity']['collapse_detected']}")

    print("\nContainers:")
    print(f"  Active: {summary['containers']['active_count']}")
    print(f"  Orphaned: {summary['containers']['orphaned_count']}")
    print(f"  Created total: {summary['containers']['created_total']}")
    print(f"  Cleanup success: {summary['containers']['cleanup_success']}")

    print("\nAlerts:")
    print(f"  Triggered total: {summary['alerts']['triggered_total']}")
    print(f"  Active count: {summary['alerts']['active_count']}")

    # Export to Prometheus format
    print("\n" + "=" * 80)
    print("Prometheus Export (Sample)")
    print("=" * 80)
    prometheus_output = collector.export_prometheus()

    # Show first 30 lines
    lines = prometheus_output.split('\n')
    for i, line in enumerate(lines[:30]):
        print(line)

    if len(lines) > 30:
        print(f"\n... ({len(lines) - 30} more lines)")

    print("\n" + "=" * 80)
    print("Metric Categories Exported")
    print("=" * 80)

    # Count metrics by category
    categories = {
        'resource': 0,
        'diversity': 0,
        'container': 0,
        'alert': 0,
        'learning': 0,
        'performance': 0,
        'quality': 0,
        'system': 0
    }

    for line in lines:
        if line.startswith('# HELP'):
            for category in categories:
                if category in line:
                    categories[category] += 1

    for category, count in categories.items():
        if count > 0:
            print(f"  {category.capitalize()}: {count} metrics")

    print("\n" + "=" * 80)
    print("Demo complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
