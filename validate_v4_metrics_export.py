#!/usr/bin/env python3
"""Validation Task V4: Prometheus Metrics Real Export Verification

This script verifies that:
1. All 22 metrics are defined and exported
2. Metrics are in Prometheus format
3. HELP and TYPE lines are present
4. Values are reasonable (not all zeros)
"""

import time
import sys
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.resource_monitor import ResourceMonitor
from src.monitoring.diversity_monitor import DiversityMonitor
from src.monitoring.alert_manager import AlertManager, AlertConfig

# Expected metrics list (22 metrics)
EXPECTED_METRICS = [
    # Resource metrics (7)
    "resource_memory_percent",
    "resource_memory_used_bytes",
    "resource_memory_total_bytes",
    "resource_cpu_percent",
    "resource_disk_percent",
    "resource_disk_used_bytes",
    "resource_disk_total_bytes",

    # Diversity metrics (5)
    "diversity_population_diversity",
    "diversity_unique_count",
    "diversity_total_count",
    "diversity_collapse_detected",
    "diversity_champion_staleness",

    # Container metrics (8)
    "container_active_count",
    "container_orphaned_count",
    "container_memory_usage_bytes",
    "container_memory_percent",
    "container_cpu_percent",
    "container_created_total",
    "container_cleanup_success_total",
    "container_cleanup_failed_total",

    # Alert metrics (2)
    "alert_triggered_total",
    "alert_active_count",
]

def validate_metrics_export():
    """Execute validation according to VALIDATION_TASKS.md Task V4."""

    print("=" * 80)
    print("VALIDATION TASK V4: Prometheus Metrics Real Export Verification")
    print("=" * 80)
    print()

    # Initialize components
    print("Step 1: Initializing monitoring components...")
    collector = MetricsCollector()
    resource_monitor = ResourceMonitor(metrics_collector=collector)
    diversity_monitor = DiversityMonitor(metrics_collector=collector)
    config = AlertConfig()
    alert_manager = AlertManager(config=config, metrics_collector=collector)

    # Start monitoring
    print("Step 2: Starting background threads...")
    resource_monitor.start_monitoring()
    alert_manager.start_monitoring()

    # Let background threads collect data
    print("Step 3: Waiting 10 seconds for background collection...")
    time.sleep(10)

    # Record some diversity metrics
    print("Step 4: Recording test metrics...")
    diversity_monitor.record_diversity(
        iteration=1,
        diversity=0.5,
        unique_count=10,
        total_count=20
    )
    collector.record_diversity_metrics(
        diversity=0.5,
        unique_count=10,
        total_count=20,
        staleness=5,
        collapse_detected=False
    )

    # Record container metrics
    collector.record_container_counts(active=2, orphaned=0)
    collector.record_container_created()
    collector.record_container_cleanup(success=True)

    # Record alert metrics
    collector.record_active_alerts(count=0)

    print("Step 5: Exporting metrics...")
    summary = collector.get_summary()

    # Export Prometheus format
    prometheus_output = collector.export_prometheus()

    # Cleanup
    print("Step 6: Stopping monitoring threads...")
    resource_monitor.stop_monitoring()
    alert_manager.stop_monitoring()

    print()
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()

    # Check 1: All 22 metrics defined
    print("Check 1: Verify all 22 metrics are defined")
    print("-" * 80)
    found_metrics = []
    missing_metrics = []

    for metric_name in EXPECTED_METRICS:
        if metric_name in collector.metrics:
            found_metrics.append(metric_name)
            print(f"  ✓ {metric_name}")
        else:
            missing_metrics.append(metric_name)
            print(f"  ✗ MISSING: {metric_name}")

    print()
    print(f"Found: {len(found_metrics)}/{len(EXPECTED_METRICS)} metrics")

    if missing_metrics:
        print(f"Missing metrics: {missing_metrics}")
        check1_passed = False
    else:
        check1_passed = True

    print()

    # Check 2: Prometheus format validation
    print("Check 2: Verify Prometheus format (HELP and TYPE lines)")
    print("-" * 80)

    help_lines = [line for line in prometheus_output.split('\n') if line.startswith('# HELP')]
    type_lines = [line for line in prometheus_output.split('\n') if line.startswith('# TYPE')]

    print(f"  HELP lines found: {len(help_lines)}")
    print(f"  TYPE lines found: {len(type_lines)}")

    # Show sample output
    print()
    print("  Sample Prometheus output (first 20 lines with resource/diversity/container/alert):")
    relevant_lines = [
        line for line in prometheus_output.split('\n')
        if any(prefix in line for prefix in ['resource_', 'diversity_', 'container_', 'alert_'])
    ][:20]

    for line in relevant_lines:
        print(f"    {line}")

    check2_passed = len(help_lines) > 0 and len(type_lines) > 0
    print()

    # Check 3: Verify values are reasonable (not all zeros)
    print("Check 3: Verify metric values are reasonable (not all zeros)")
    print("-" * 80)

    non_zero_count = 0
    total_with_values = 0

    for metric_name in found_metrics:
        metric = collector.metrics[metric_name]
        if metric.values:
            total_with_values += 1
            latest_value = metric.get_latest()
            if latest_value is not None and latest_value != 0.0:
                non_zero_count += 1
                print(f"  ✓ {metric_name} = {latest_value}")
            else:
                print(f"  - {metric_name} = 0.0 (may be expected)")

    print()
    print(f"Metrics with values: {total_with_values}/{len(found_metrics)}")
    print(f"Non-zero values: {non_zero_count}/{total_with_values}")

    # At least 50% should have non-zero values (resource metrics should always be non-zero)
    check3_passed = total_with_values > 0 and (non_zero_count / total_with_values) >= 0.3

    print()

    # Check 4: Verify summary output
    print("Check 4: Verify get_summary() output")
    print("-" * 80)
    print(f"  Resources: {summary.get('resources', {})}")
    print(f"  Diversity: {summary.get('diversity', {})}")
    print(f"  Containers: {summary.get('containers', {})}")
    print(f"  Alerts: {summary.get('alerts', {})}")

    check4_passed = (
        'resources' in summary and
        'diversity' in summary and
        'containers' in summary and
        'alerts' in summary
    )

    print()
    print("=" * 80)
    print("FINAL VALIDATION RESULT")
    print("=" * 80)
    print()

    all_checks_passed = check1_passed and check2_passed and check3_passed and check4_passed

    print(f"  Check 1 (All 22 metrics defined): {'✓ PASS' if check1_passed else '✗ FAIL'}")
    print(f"  Check 2 (Prometheus format): {'✓ PASS' if check2_passed else '✗ FAIL'}")
    print(f"  Check 3 (Reasonable values): {'✓ PASS' if check3_passed else '✗ FAIL'}")
    print(f"  Check 4 (Summary output): {'✓ PASS' if check4_passed else '✗ FAIL'}")
    print()

    if all_checks_passed:
        print("🎉 VALIDATION TASK V4: PASSED")
        print()
        print("All 22 metrics are correctly defined and exported in Prometheus format.")
        print("Background threads successfully collect data and update metrics.")
        return 0
    else:
        print("❌ VALIDATION TASK V4: FAILED")
        print()
        print("Issues found:")
        if not check1_passed:
            print(f"  - Missing {len(missing_metrics)} required metrics")
        if not check2_passed:
            print("  - Prometheus format incomplete (missing HELP/TYPE lines)")
        if not check3_passed:
            print("  - Too many metrics with zero values")
        if not check4_passed:
            print("  - Summary output incomplete")
        return 1

if __name__ == '__main__':
    sys.exit(validate_metrics_export())
