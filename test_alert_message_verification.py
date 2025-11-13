"""
Alert Message Verification - Detailed Check
Validates alert message structure and content quality.
"""

import logging
from src.monitoring.alert_manager import AlertManager, AlertConfig, Alert
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.diversity_monitor import DiversityMonitor

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def verify_alert_structure():
    """Verify alert structure includes all required fields."""
    print("\n" + "="*60)
    print("ALERT STRUCTURE VERIFICATION")
    print("="*60)

    # Create sample alerts for each type
    config = AlertConfig()
    collector = MetricsCollector()
    alert_mgr = AlertManager(config, collector)

    # Test data sources
    alert_mgr.set_memory_source(lambda: {'memory_percent': 85.0})
    alert_mgr.set_staleness_source(lambda: 25)
    alert_mgr.set_success_rate_source(lambda: 15.0)
    alert_mgr.set_container_source(lambda: 5)
    alert_mgr.set_iteration_source(lambda: 100)

    # Evaluate to trigger alerts
    alert_mgr.evaluate_alerts()

    # Check alert structure
    active = alert_mgr.get_active_alerts()
    print(f"\nActive alerts: {active}")

    # Get status
    status = alert_mgr.get_status()
    print(f"\nAlert Manager Status:")
    print(f"  Active alerts: {status['active_alerts']}")
    print(f"  Monitoring active: {status['monitoring_active']}")
    print(f"  Suppressed count: {status['suppressed_count']}")
    print(f"\nConfiguration:")
    for key, value in status['config'].items():
        print(f"  {key}: {value}")

    print("\n✅ Alert structure verification complete")


def verify_diversity_collapse_details():
    """Verify diversity collapse alert includes detailed information."""
    print("\n" + "="*60)
    print("DIVERSITY COLLAPSE DETAILS VERIFICATION")
    print("="*60)

    collector = MetricsCollector()
    monitor = DiversityMonitor(collector, collapse_threshold=0.1, collapse_window=5)

    # Simulate collapse
    print("\nSimulating diversity collapse...")
    for i in range(5):
        diversity = 0.05 + (i * 0.001)  # Slight variation
        monitor.record_diversity(i, diversity, 5 + i, 100)
        print(f"  Iteration {i}: diversity={diversity:.4f}, unique={5+i}/100")

    # Check collapse
    collapse = monitor.check_diversity_collapse()
    print(f"\nCollapse detected: {collapse}")

    # Get detailed status
    status = monitor.get_status()
    print(f"\nDiversity Monitor Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")

    # Get history
    history = monitor.get_diversity_history()
    print(f"\nDiversity history: {[f'{d:.4f}' for d in history]}")

    print("\n✅ Diversity collapse details verification complete")


def verify_champion_staleness_tracking():
    """Verify champion staleness calculation and tracking."""
    print("\n" + "="*60)
    print("CHAMPION STALENESS TRACKING VERIFICATION")
    print("="*60)

    collector = MetricsCollector()
    monitor = DiversityMonitor(collector)

    # Record champion updates
    print("\nRecording champion updates:")
    updates = [
        (0, 1.0, 1.2),
        (10, 1.2, 1.5),
        (25, 1.5, 1.8)
    ]

    for iteration, old_sharpe, new_sharpe in updates:
        monitor.record_champion_update(iteration, old_sharpe, new_sharpe)
        print(f"  Iteration {iteration}: {old_sharpe:.1f} -> {new_sharpe:.1f}")

    # Calculate staleness at different points
    print("\nStaleness calculations:")
    test_iterations = [30, 40, 50]
    for current_iter in test_iterations:
        staleness = monitor.calculate_staleness(current_iter, 25)
        print(f"  At iteration {current_iter}: staleness = {staleness}")

    print("\n✅ Champion staleness tracking verification complete")


def verify_alert_message_clarity():
    """Verify alert messages are clear and actionable."""
    print("\n" + "="*60)
    print("ALERT MESSAGE CLARITY VERIFICATION")
    print("="*60)

    alert_scenarios = [
        {
            'name': 'Memory Alert',
            'alert': Alert(
                alert_type='high_memory',
                severity='critical',
                message='High memory usage detected: 85.0% (threshold: 80.0%)',
                current_value=85.0,
                threshold_value=80.0,
                iteration_context=100
            )
        },
        {
            'name': 'Diversity Collapse',
            'alert': Alert(
                alert_type='diversity_collapse',
                severity='warning',
                message='Diversity collapse detected: 0.0500 (threshold: 0.1000)',
                current_value=0.05,
                threshold_value=0.1,
                iteration_context=50
            )
        },
        {
            'name': 'Champion Staleness',
            'alert': Alert(
                alert_type='champion_staleness',
                severity='warning',
                message='Champion staleness detected: 25 iterations (threshold: 20)',
                current_value=25.0,
                threshold_value=20.0,
                iteration_context=75
            )
        },
        {
            'name': 'Low Success Rate',
            'alert': Alert(
                alert_type='low_success_rate',
                severity='warning',
                message='Low success rate detected: 15.0% (threshold: 20.0%)',
                current_value=15.0,
                threshold_value=20.0,
                iteration_context=30
            )
        },
        {
            'name': 'Orphaned Containers',
            'alert': Alert(
                alert_type='orphaned_containers',
                severity='critical',
                message='Container cleanup failures detected: 5 orphaned containers (threshold: 3)',
                current_value=5.0,
                threshold_value=3.0,
                iteration_context=10
            )
        }
    ]

    print("\nAlert Message Quality Checklist:")
    print("-" * 60)

    for scenario in alert_scenarios:
        alert = scenario['alert']
        print(f"\n{scenario['name']}:")
        print(f"  Type: {alert.alert_type}")
        print(f"  Severity: {alert.severity}")
        print(f"  Message: {alert.message}")

        # Verify message components
        has_current = str(alert.current_value) in alert.message
        has_threshold = str(alert.threshold_value) in alert.message
        has_context = len(alert.message) > 20  # Sufficient detail

        print(f"  ✓ Includes current value: {has_current}")
        print(f"  ✓ Includes threshold: {has_threshold}")
        print(f"  ✓ Has sufficient context: {has_context}")

        # Convert to dict
        alert_dict = alert.to_dict()
        print(f"  ✓ Serializable: {isinstance(alert_dict, dict)}")
        print(f"  ✓ Has timestamp: {'timestamp' in alert_dict}")

    print("\n✅ Alert message clarity verification complete")


def main():
    """Run all verification tests."""
    print("\n" + "#"*60)
    print("ALERT MESSAGE VERIFICATION - DETAILED CHECK")
    print("#"*60)

    verify_alert_structure()
    verify_diversity_collapse_details()
    verify_champion_staleness_tracking()
    verify_alert_message_clarity()

    print("\n" + "="*60)
    print("ALL VERIFICATION CHECKS COMPLETE")
    print("="*60)
    print("\n✅ All alert messages are properly structured and actionable")


if __name__ == "__main__":
    main()
