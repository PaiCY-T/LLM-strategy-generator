"""Verify Sandbox Deployment Setup.

Quick verification script to ensure all components are ready before
running the actual sandbox deployment.
"""

import sys
import importlib
from pathlib import Path

def test_imports():
    """Test all required imports."""
    print("Testing imports...")

    required_modules = [
        ('src.monitoring.evolution_integration', 'MonitoredEvolution'),
        ('src.monitoring.alerts', 'AlertManager'),
        ('src.monitoring.evolution_metrics', 'EvolutionMetricsTracker'),
        ('src.population.population_manager', 'PopulationManager'),
        ('src.population.genetic_operators', 'GeneticOperators'),
        ('src.population.fitness_evaluator', 'FitnessEvaluator'),
        ('src.population.evolution_monitor', 'EvolutionMonitor'),
    ]

    failed = []
    for module_name, class_name in required_modules:
        try:
            module = importlib.import_module(module_name)
            assert hasattr(module, class_name), f"{class_name} not found in {module_name}"
            print(f"  ✓ {module_name}.{class_name}")
        except Exception as e:
            print(f"  ✗ {module_name}.{class_name}: {e}")
            failed.append((module_name, class_name, str(e)))

    return len(failed) == 0, failed


def test_scripts():
    """Test all deployment scripts exist."""
    print("\nTesting deployment scripts...")

    scripts = [
        'sandbox_deployment.py',
        'start_sandbox.sh',
        'stop_sandbox.sh',
        'sandbox_monitor.sh',
        'test_sandbox.sh'
    ]

    project_root = Path(__file__).parent
    failed = []

    for script in scripts:
        script_path = project_root / script
        if script_path.exists():
            print(f"  ✓ {script}")
        else:
            print(f"  ✗ {script} - NOT FOUND")
            failed.append(script)

    return len(failed) == 0, failed


def test_monitoring_integration():
    """Test MonitoredEvolution initialization."""
    print("\nTesting MonitoredEvolution integration...")

    try:
        from src.monitoring.evolution_integration import MonitoredEvolution

        # Try to initialize (don't run)
        evolution = MonitoredEvolution(
            population_size=10,
            alert_file=None,
            metrics_export_interval=10
        )

        print("  ✓ MonitoredEvolution initialized")
        print(f"    - PopulationManager: {evolution.population_manager is not None}")
        print(f"    - EvolutionMonitor: {evolution.evolution_monitor is not None}")
        print(f"    - GeneticOperators: {evolution.genetic_operators is not None}")
        print(f"    - FitnessEvaluator: {evolution.fitness_evaluator is not None}")
        print(f"    - MetricsTracker: {evolution.metrics_tracker is not None}")
        print(f"    - AlertManager: {evolution.alert_manager is not None}")

        return True, None
    except Exception as e:
        print(f"  ✗ MonitoredEvolution initialization failed: {e}")
        return False, str(e)


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Sandbox Deployment Setup Verification")
    print("=" * 60)
    print()

    results = []

    # Test 1: Imports
    success, failed = test_imports()
    results.append(("Imports", success, failed))

    # Test 2: Scripts
    success, failed = test_scripts()
    results.append(("Scripts", success, failed))

    # Test 3: Integration
    success, error = test_monitoring_integration()
    results.append(("Integration", success, error))

    # Summary
    print()
    print("=" * 60)
    print("Verification Summary")
    print("=" * 60)

    all_passed = True
    for test_name, success, details in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not success and details:
            print(f"  Details: {details}")
            all_passed = False

    print()

    if all_passed:
        print("✓ All checks passed! System is ready for deployment.")
        print()
        print("Next steps:")
        print("  1. Run quick test: ./test_sandbox.sh")
        print("  2. Start full deployment: ./start_sandbox.sh")
        return 0
    else:
        print("✗ Some checks failed. Please fix issues before deployment.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
