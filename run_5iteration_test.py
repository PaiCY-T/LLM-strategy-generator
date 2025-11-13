#!/usr/bin/env python3
"""
5-Iteration Smoke Test with Full Phase 2 Monitoring

Enhanced smoke test using ExtendedTestHarness for comprehensive validation:
- Phase 2 monitoring: VarianceMonitor, PreservationValidator, AntiChurnManager, RollbackManager
- Statistical analysis: Cohen's d, p-value (if ≥4 iterations successful)
- All metrics tracked and reported

This provides a quick validation (30-60 mins) before running the full 200-iteration test.

Usage:
    python3 run_5iteration_test.py
"""

import os
import sys
import logging
from datetime import datetime

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests', 'integration'))
sys.path.insert(0, os.path.dirname(__file__))

from extended_test_harness import ExtendedTestHarness


def setup_logging():
    """Configure comprehensive logging for smoke test."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f"5iteration_smoke_test_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized: {log_file}")
    return logger, log_file


def load_finlab_data():
    """Load real Finlab data for testing.

    Returns:
        Finlab data object with Taiwan stock market data
    """
    try:
        import finlab
        from finlab import data

        # Login with API token
        api_token = os.getenv("FINLAB_API_TOKEN")
        if not api_token:
            raise ValueError("FINLAB_API_TOKEN environment variable not set")

        finlab.login(api_token)

        logger = logging.getLogger(__name__)
        logger.info("✅ Finlab data loaded successfully")

        return data

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Failed to load Finlab data: {e}")
        raise


def validate_phase2_features(logger: logging.Logger) -> dict:
    """Validate that all Phase 2 features are available.

    Checks:
    - Story 1: VarianceMonitor available
    - Story 2: PreservationValidator available
    - Story 4: AntiChurnManager available
    - Story 9: RollbackManager available

    Returns:
        dict: {
            'all_available': bool,
            'story1_available': bool,
            'story2_available': bool,
            'story4_available': bool,
            'story9_available': bool,
            'missing_features': list
        }
    """
    logger.info("=" * 70)
    logger.info("VALIDATING PHASE 2 FEATURES")
    logger.info("=" * 70)

    status = {
        'all_available': True,
        'story1_available': False,
        'story2_available': False,
        'story4_available': False,
        'story9_available': False,
        'missing_features': []
    }

    # Check Story 1: VarianceMonitor
    try:
        from src.monitoring.variance_monitor import VarianceMonitor
        status['story1_available'] = True
        logger.info("  ✅ Story 1: VarianceMonitor available")
    except ImportError as e:
        status['all_available'] = False
        status['missing_features'].append('VarianceMonitor')
        logger.warning(f"  ❌ Story 1: VarianceMonitor not available - {e}")

    # Check Story 2: PreservationValidator
    try:
        from src.validation.preservation_validator import PreservationValidator
        status['story2_available'] = True
        logger.info("  ✅ Story 2: PreservationValidator available")
    except ImportError as e:
        status['all_available'] = False
        status['missing_features'].append('PreservationValidator')
        logger.warning(f"  ❌ Story 2: PreservationValidator not available - {e}")

    # Check Story 4: AntiChurnManager
    try:
        from src.config.anti_churn_manager import AntiChurnManager
        status['story4_available'] = True
        logger.info("  ✅ Story 4: AntiChurnManager available")
    except ImportError as e:
        status['all_available'] = False
        status['missing_features'].append('AntiChurnManager')
        logger.warning(f"  ❌ Story 4: AntiChurnManager not available - {e}")

    # Check Story 9: RollbackManager
    try:
        from src.recovery.rollback_manager import RollbackManager
        status['story9_available'] = True
        logger.info("  ✅ Story 9: RollbackManager available")
    except ImportError as e:
        status['all_available'] = False
        status['missing_features'].append('RollbackManager')
        logger.warning(f"  ❌ Story 9: RollbackManager not available - {e}")

    # Summary
    logger.info("")
    if status['all_available']:
        logger.info("✅ All Phase 2 features available")
    else:
        logger.warning(f"⚠️  Missing {len(status['missing_features'])} Phase 2 features: {', '.join(status['missing_features'])}")
        logger.warning("Test will continue, but some monitoring may be unavailable")

    logger.info("=" * 70)
    logger.info("")

    return status


def run_5iteration_smoke_test():
    """Run 5-iteration smoke test with full Phase 2 monitoring.

    Uses ExtendedTestHarness which includes:
    - VarianceMonitor (Story 1) - integrated in AutonomousLoop
    - PreservationValidator (Story 2) - integrated in AutonomousLoop
    - AntiChurnManager (Story 4) - integrated in AutonomousLoop
    - RollbackManager (Story 9) - available for manual rollback
    - Statistical analysis: Cohen's d, p-value (if ≥4 successful iterations)

    Returns:
        Dictionary with test results and metrics
    """
    logger, log_file = setup_logging()

    logger.info("=" * 70)
    logger.info("5-ITERATION SMOKE TEST - START")
    logger.info("=" * 70)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Model: google/gemini-2.5-flash")
    logger.info(f"Target iterations: 5")
    logger.info(f"Mode: Enhanced with Phase 2 monitoring")
    logger.info(f"Log file: {log_file}")
    logger.info("")

    # Validate Phase 2 features availability
    phase2_status = validate_phase2_features(logger)

    # Load Finlab data
    try:
        data = load_finlab_data()
    except Exception as e:
        logger.error(f"❌ Data loading failed: {e}")
        logger.error("Cannot proceed without data")
        return {
            'success': False,
            'error': str(e),
            'log_file': log_file,
            'phase2_status': phase2_status
        }

    # Initialize ExtendedTestHarness with 5 iterations
    # This automatically includes all Phase 2 monitoring via AutonomousLoop
    logger.info("Initializing ExtendedTestHarness with Phase 2 monitoring...")
    harness = ExtendedTestHarness(
        model='gemini-2.5-flash',  # Primary: Google AI, Fallback: OpenRouter
        target_iterations=5,
        checkpoint_interval=5  # Save checkpoint at end
    )

    # Run test
    try:
        logger.info("Starting 5-iteration test with full monitoring...")
        logger.info("")

        results = harness.run_test(data=data, resume_from_checkpoint=None)

        # Enhance results with Phase 2 status
        results['phase2_status'] = phase2_status
        results['log_file'] = log_file
        results['success'] = results.get('test_completed', False)

        # Print summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("5-ITERATION SMOKE TEST - COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Test completed: {results['success']}")
        logger.info(f"Success rate: {results.get('success_rate', 0.0):.1f}%")
        logger.info(f"Best Sharpe: {results.get('best_sharpe', 0.0):.4f}")
        logger.info(f"Avg Sharpe: {results.get('avg_sharpe', 0.0):.4f}")

        # Statistical analysis (if available)
        stat_report = results.get('statistical_report')
        if stat_report and not stat_report.get('error'):
            logger.info("")
            logger.info("Statistical Analysis:")
            logger.info(f"  Cohen's d: {stat_report.get('cohens_d', 'N/A')}")
            logger.info(f"  Effect size: {stat_report.get('effect_size_interpretation', 'N/A')}")
            logger.info(f"  p-value: {stat_report.get('p_value', 'N/A')}")
            logger.info(f"  Significant: {stat_report.get('is_significant', False)}")
            logger.info(f"  Rolling variance: {stat_report.get('rolling_variance', 'N/A')}")
            logger.info(f"  Converged: {stat_report.get('convergence_achieved', False)}")
        elif stat_report and stat_report.get('error'):
            logger.info(f"Statistical analysis: {stat_report['error']}")

        logger.info("")
        logger.info(f"Log file: {log_file}")
        logger.info("=" * 70)

        return results

    except KeyboardInterrupt:
        logger.warning("")
        logger.warning("=" * 70)
        logger.warning("TEST INTERRUPTED BY USER")
        logger.warning("=" * 70)
        logger.warning("Partial results may be available in checkpoint")
        return {
            'success': False,
            'error': 'User interrupted',
            'log_file': log_file,
            'phase2_status': phase2_status
        }

    except Exception as e:
        logger.error("")
        logger.error("=" * 70)
        logger.error("TEST FAILED WITH EXCEPTION")
        logger.error("=" * 70)
        logger.error(f"Error: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'log_file': log_file,
            'phase2_status': phase2_status
        }


def main():
    """Main entry point."""
    try:
        print("\n🚀 Starting 5-iteration smoke test with Phase 2 monitoring...\n")
        results = run_5iteration_smoke_test()

        if results.get('success'):
            print(f"\n✅ Smoke test completed successfully")
            print(f"   Success rate: {results.get('success_rate', 0.0):.1f}%")
            print(f"   Best Sharpe: {results.get('best_sharpe', 0.0):.4f}")
            print(f"   Avg Sharpe: {results.get('avg_sharpe', 0.0):.4f}")

            # Phase 2 status
            phase2_status = results.get('phase2_status', {})
            if phase2_status.get('all_available'):
                print(f"   Phase 2 features: ✅ All available")
            else:
                print(f"   Phase 2 features: ⚠️  {len(phase2_status.get('missing_features', []))} missing")

            print(f"   Log file: {results['log_file']}")

            # Recommendation
            print("\n📊 Next Steps:")
            if results.get('success_rate', 0.0) >= 80.0:
                print("   ✅ High success rate - proceed with 200-iteration test")
            elif results.get('success_rate', 0.0) >= 60.0:
                print("   ⚠️  Moderate success rate - review logs before 200-iteration test")
            else:
                print("   ❌ Low success rate - investigate issues before proceeding")

            sys.exit(0)
        else:
            print(f"\n❌ Smoke test failed: {results.get('error', 'Unknown error')}")
            print(f"   Log file: {results['log_file']}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(2)

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == '__main__':
    main()
