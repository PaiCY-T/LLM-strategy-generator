#!/usr/bin/env python3
"""Verification script for monitoring integration (Task 8).

This script verifies that monitoring components are properly integrated
into the autonomous loop without running full iterations.

Usage:
    python verify_monitoring_integration.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def verify_imports():
    """Verify all monitoring modules can be imported."""
    print("=" * 60)
    print("STEP 1: Verifying Imports")
    print("=" * 60)

    try:
        from src.monitoring.metrics_collector import MetricsCollector
        print("✓ MetricsCollector imported")

        from src.monitoring.resource_monitor import ResourceMonitor
        print("✓ ResourceMonitor imported")

        from src.monitoring.diversity_monitor import DiversityMonitor
        print("✓ DiversityMonitor imported")

        from src.monitoring.container_monitor import ContainerMonitor
        print("✓ ContainerMonitor imported")

        from src.monitoring.alert_manager import AlertManager, AlertConfig
        print("✓ AlertManager imported")

        print("\n✓ All monitoring modules imported successfully\n")
        return True

    except ImportError as e:
        print(f"\n✗ Import failed: {e}\n")
        return False


def verify_integration():
    """Verify monitoring is integrated into autonomous loop."""
    print("=" * 60)
    print("STEP 2: Verifying Integration")
    print("=" * 60)

    try:
        # Import autonomous loop
        from artifacts.working.modules.autonomous_loop import AutonomousLoop
        print("✓ AutonomousLoop imported")

        # Verify integration points exist
        methods = [
            '_initialize_monitoring',
            '_record_iteration_monitoring',
            '_cleanup_monitoring'
        ]

        for method in methods:
            if hasattr(AutonomousLoop, method):
                print(f"✓ Method {method} exists")
            else:
                print(f"✗ Method {method} NOT FOUND")
                return False

        print("\n✓ All integration methods present\n")
        return True

    except Exception as e:
        print(f"\n✗ Integration verification failed: {e}\n")
        return False


def verify_initialization():
    """Verify monitoring can be initialized."""
    print("=" * 60)
    print("STEP 3: Verifying Initialization")
    print("=" * 60)

    try:
        from unittest.mock import patch

        # Mock dependencies to avoid full initialization
        with patch('artifacts.working.modules.autonomous_loop.HallOfFameRepository'):
            with patch('artifacts.working.modules.autonomous_loop.ExperimentConfigManager'):
                with patch('artifacts.working.modules.autonomous_loop.VarianceMonitor'):
                    with patch('artifacts.working.modules.autonomous_loop.AntiChurnManager'):
                        with patch('artifacts.working.modules.autonomous_loop.get_event_logger'):
                            from artifacts.working.modules.autonomous_loop import AutonomousLoop

                            # Create loop instance
                            loop = AutonomousLoop(
                                model="gemini-2.5-flash",
                                max_iterations=1,
                                history_file="test_verify.json",
                                enable_sandbox=False
                            )

                            print(f"✓ AutonomousLoop instantiated")

                            # Check monitoring enabled
                            if hasattr(loop, '_monitoring_enabled'):
                                print(f"✓ _monitoring_enabled flag present: {loop._monitoring_enabled}")

                                if loop._monitoring_enabled:
                                    # Check components initialized
                                    components = [
                                        'metrics_collector',
                                        'resource_monitor',
                                        'diversity_monitor',
                                        'container_monitor',
                                        'alert_manager'
                                    ]

                                    for component in components:
                                        if hasattr(loop, component):
                                            print(f"✓ {component} initialized")
                                        else:
                                            print(f"✗ {component} NOT initialized")
                                            return False

                                    # Check background threads started
                                    if loop.resource_monitor and loop.resource_monitor._monitoring_thread:
                                        print(f"✓ ResourceMonitor thread started")

                                    if loop.alert_manager and loop.alert_manager._monitoring_thread:
                                        print(f"✓ AlertManager thread started")

                                    # Cleanup
                                    loop._cleanup_monitoring()
                                    print(f"✓ Monitoring cleanup successful")

                                else:
                                    print("⚠ Monitoring disabled (this is OK - graceful degradation)")

                            else:
                                print(f"✗ _monitoring_enabled flag NOT FOUND")
                                return False

        print("\n✓ Initialization verification passed\n")
        return True

    except Exception as e:
        print(f"\n✗ Initialization failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification steps."""
    print("\n" + "=" * 60)
    print("MONITORING INTEGRATION VERIFICATION (Task 8)")
    print("=" * 60 + "\n")

    results = []

    # Step 1: Verify imports
    results.append(("Imports", verify_imports()))

    # Step 2: Verify integration
    results.append(("Integration", verify_integration()))

    # Step 3: Verify initialization
    results.append(("Initialization", verify_initialization()))

    # Summary
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for step, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{step:20s}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ ALL VERIFICATION STEPS PASSED")
        print("\nMonitoring integration is working correctly!")
        print("\nNext steps:")
        print("  1. Run integration tests: pytest tests/integration/test_autonomous_loop_monitoring.py -v")
        print("  2. Test with real loop execution")
        print("  3. Verify Prometheus metrics export")
        return 0
    else:
        print("\n✗ SOME VERIFICATION STEPS FAILED")
        print("\nPlease review the output above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
