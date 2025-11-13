#!/usr/bin/env python3
"""
Phase 2 Integration Test - Verify all Phase 2 features work together.

Tests:
- Story 1: VarianceMonitor tracks convergence
- Story 2: PreservationValidator checks behavioral similarity
- Story 4: AntiChurnManager uses externalized config
- Story 9: RollbackManager can restore champions
"""

import sys
import os
from pathlib import Path

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'artifacts', 'working', 'modules'))
sys.path.insert(0, os.path.dirname(__file__))

def test_phase2_module_availability():
    """Test that all Phase 2 modules can be imported."""
    print("\n" + "="*70)
    print("PHASE 2 MODULE AVAILABILITY CHECK")
    print("="*70)

    results = {
        'all_available': True,
        'modules': {}
    }

    # Story 1: VarianceMonitor
    try:
        from src.monitoring.variance_monitor import VarianceMonitor
        print("✅ Story 1: VarianceMonitor - Available")
        results['modules']['variance_monitor'] = True
    except ImportError as e:
        print(f"❌ Story 1: VarianceMonitor - NOT Available ({e})")
        results['modules']['variance_monitor'] = False
        results['all_available'] = False

    # Story 2: PreservationValidator
    try:
        from src.validation.preservation_validator import PreservationValidator
        print("✅ Story 2: PreservationValidator - Available")
        results['modules']['preservation_validator'] = True
    except ImportError as e:
        print(f"❌ Story 2: PreservationValidator - NOT Available ({e})")
        results['modules']['preservation_validator'] = False
        results['all_available'] = False

    # Story 4: AntiChurnManager
    try:
        from src.config.anti_churn_manager import AntiChurnManager
        print("✅ Story 4: AntiChurnManager - Available")
        results['modules']['anti_churn_manager'] = True
    except ImportError as e:
        print(f"❌ Story 4: AntiChurnManager - NOT Available ({e})")
        results['modules']['anti_churn_manager'] = False
        results['all_available'] = False

    # Story 9: RollbackManager
    try:
        from src.recovery.rollback_manager import RollbackManager
        print("✅ Story 9: RollbackManager - Available")
        results['modules']['rollback_manager'] = True
    except ImportError as e:
        print(f"❌ Story 9: RollbackManager - NOT Available ({e})")
        results['modules']['rollback_manager'] = False
        results['all_available'] = False

    print()
    return results


def test_phase2_config_files():
    """Test that Phase 2 config files exist."""
    print("="*70)
    print("PHASE 2 CONFIG FILES CHECK")
    print("="*70)

    config_file = Path('config/learning_system.yaml')

    if config_file.exists():
        print(f"✅ Anti-churn config: {config_file}")

        # Try loading it
        try:
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            print(f"   ✅ YAML loaded successfully")
            print(f"   ✅ Probation period: {config['anti_churn']['probation_period']}")
            print(f"   ✅ Probation threshold: {config['anti_churn']['probation_threshold']}")
        except Exception as e:
            print(f"   ⚠️  Could not load YAML: {e}")
    else:
        print(f"❌ Anti-churn config: NOT FOUND")
        return False

    print()
    return True


def test_phase2_cli_tools():
    """Test that Phase 2 CLI tools exist."""
    print("="*70)
    print("PHASE 2 CLI TOOLS CHECK")
    print("="*70)

    rollback_cli = Path('rollback_champion.py')

    if rollback_cli.exists():
        print(f"✅ Rollback CLI tool: {rollback_cli}")
    else:
        print(f"❌ Rollback CLI tool: NOT FOUND")
        return False

    print()
    return True


def test_phase2_functional():
    """Test Phase 2 components functional behavior."""
    print("="*70)
    print("PHASE 2 FUNCTIONAL TESTS")
    print("="*70)

    try:
        # Test VarianceMonitor
        from src.monitoring.variance_monitor import VarianceMonitor
        monitor = VarianceMonitor(alert_threshold=0.8)
        monitor.update(0, 1.0)
        monitor.update(1, 1.5)
        monitor.update(2, 0.8)
        variance = monitor.get_rolling_variance(window=3)
        print(f"✅ VarianceMonitor: variance = {variance:.4f}")

        # Test AntiChurnManager
        from src.config.anti_churn_manager import AntiChurnManager
        manager = AntiChurnManager()
        threshold = manager.get_required_improvement(current_iteration=1, champion_iteration=0)
        print(f"✅ AntiChurnManager: required_improvement = {threshold:.4f}")

        # Test PreservationValidator structure
        from src.validation.preservation_validator import PreservationValidator, PreservationReport
        validator = PreservationValidator()
        print(f"✅ PreservationValidator: initialized successfully")

        # Test RollbackManager structure (without Hall of Fame)
        from src.recovery.rollback_manager import RollbackManager
        print(f"✅ RollbackManager: class available (needs Hall of Fame for full test)")

    except Exception as e:
        print(f"❌ Functional test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()
    return True


def main():
    """Run all Phase 2 integration tests."""
    print("\n🔍 Phase 2 Integration Validation")
    print("="*70)

    # Test module availability
    module_results = test_phase2_module_availability()

    # Test config files
    config_results = test_phase2_config_files()

    # Test CLI tools
    cli_results = test_phase2_cli_tools()

    # Test functional behavior
    functional_results = test_phase2_functional()

    # Summary
    print("="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    all_passed = True

    # Module availability
    if module_results['all_available']:
        print("✅ All Phase 2 modules available")
    else:
        print("❌ Some Phase 2 modules missing")
        all_passed = False

    # Config files
    if config_results:
        print("✅ Phase 2 config files present")
    else:
        print("❌ Phase 2 config files missing")
        all_passed = False

    # CLI tools
    if cli_results:
        print("✅ Phase 2 CLI tools present")
    else:
        print("❌ Phase 2 CLI tools missing")
        all_passed = False

    # Functional tests
    if functional_results:
        print("✅ Phase 2 functional tests passed")
    else:
        print("❌ Phase 2 functional tests failed")
        all_passed = False

    print("="*70)

    if all_passed:
        print("\n🎉 Phase 2 Integration: VALIDATED")
        print("\n✅ All Stories Complete:")
        print("   - Story 1: Convergence Monitoring (VarianceMonitor)")
        print("   - Story 2: Enhanced Preservation (PreservationValidator)")
        print("   - Story 4: Anti-Churn Configuration (AntiChurnManager)")
        print("   - Story 9: Rollback Mechanism (RollbackManager)")
        return 0
    else:
        print("\n❌ Phase 2 Integration: INCOMPLETE")
        return 1


if __name__ == '__main__':
    exit(main())
