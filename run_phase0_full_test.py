#!/usr/bin/env python3
"""
Phase 0: 50-Iteration Template Mode Full Test

Full validation of O3's template mode hypothesis:
Can template-guided parameter generation achieve ≥5% champion update rate?

Tests the template-guided parameter generation with:
- MomentumTemplate with LLM parameter generation
- TemplateParameterGenerator
- StrategyValidator
- Parameter diversity tracking
- Validation statistics tracking
- Champion update tracking

Target Metrics:
- Champion update rate: ≥5% (target), 2-5% (partial), <2% (failure)
- Average Sharpe: >1.0 (target), 0.8-1.0 (partial), <0.8 (failure)
- Parameter diversity: ≥30 unique combinations (target)
- Validation pass rate: ≥90% (target)

Decision Matrix:
- SUCCESS (≥5% update rate AND >1.0 Sharpe): Skip population-based, use template mode
- PARTIAL (2-5% OR 0.8-1.0 Sharpe): Consider hybrid approach
- FAILURE (<2% OR <0.8 Sharpe): Proceed to population-based learning

Usage:
    python3 run_phase0_full_test.py
"""

import os
import sys
import logging
from datetime import datetime

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests', 'integration'))
sys.path.insert(0, os.path.dirname(__file__))

from phase0_test_harness import Phase0TestHarness
from phase0_results_analyzer import ResultsAnalyzer


def setup_logging():
    """Configure comprehensive logging for full test."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f"phase0_full_test_{timestamp}.log")

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


def validate_phase0_components(logger: logging.Logger) -> dict:
    """Validate that all Phase 0 components are available.

    Checks:
    - MomentumTemplate available
    - TemplateParameterGenerator available
    - StrategyValidator available

    Returns:
        dict: {
            'all_available': bool,
            'template_available': bool,
            'generator_available': bool,
            'validator_available': bool,
            'missing_components': list
        }
    """
    logger.info("=" * 70)
    logger.info("VALIDATING PHASE 0 COMPONENTS")
    logger.info("=" * 70)

    status = {
        'all_available': True,
        'template_available': False,
        'generator_available': False,
        'validator_available': False,
        'missing_components': []
    }

    # Check MomentumTemplate
    try:
        from src.templates.momentum_template import MomentumTemplate
        status['template_available'] = True
        logger.info("  ✅ MomentumTemplate available")
    except ImportError as e:
        status['all_available'] = False
        status['missing_components'].append('MomentumTemplate')
        logger.error(f"  ❌ MomentumTemplate not available - {e}")

    # Check TemplateParameterGenerator
    try:
        from src.generators.template_parameter_generator import TemplateParameterGenerator
        status['generator_available'] = True
        logger.info("  ✅ TemplateParameterGenerator available")
    except ImportError as e:
        status['all_available'] = False
        status['missing_components'].append('TemplateParameterGenerator')
        logger.error(f"  ❌ TemplateParameterGenerator not available - {e}")

    # Check StrategyValidator
    try:
        from src.validation.strategy_validator import StrategyValidator
        status['validator_available'] = True
        logger.info("  ✅ StrategyValidator available")
    except ImportError as e:
        status['all_available'] = False
        status['missing_components'].append('StrategyValidator')
        logger.error(f"  ❌ StrategyValidator not available - {e}")

    # Summary
    logger.info("")
    if status['all_available']:
        logger.info("✅ All Phase 0 components available")
    else:
        logger.error(f"❌ Missing {len(status['missing_components'])} components: {', '.join(status['missing_components'])}")
        logger.error("Cannot proceed without all components")

    logger.info("=" * 70)
    logger.info("")

    return status


def run_phase0_full_test():
    """Run 50-iteration full test for Phase 0 template mode.

    Uses Phase0TestHarness which includes:
    - Template mode (Momentum strategy)
    - LLM parameter generation (gemini-2.5-flash)
    - TemplateParameterGenerator
    - StrategyValidator
    - Parameter diversity tracking
    - Validation statistics tracking
    - Champion update tracking

    Returns:
        Dictionary with test results and metrics
    """
    logger, log_file = setup_logging()

    logger.info("=" * 70)
    logger.info("PHASE 0: 50-ITERATION TEMPLATE MODE FULL TEST")
    logger.info("=" * 70)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Model: gemini-2.5-flash")
    logger.info(f"Target iterations: 50")
    logger.info(f"Mode: Template mode (Momentum)")
    logger.info(f"Log file: {log_file}")
    logger.info("")

    # Validate Phase 0 components availability
    phase0_status = validate_phase0_components(logger)

    if not phase0_status['all_available']:
        logger.error("❌ Cannot proceed without all Phase 0 components")
        return {
            'success': False,
            'error': f"Missing components: {', '.join(phase0_status['missing_components'])}",
            'log_file': log_file,
            'phase0_status': phase0_status
        }

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
            'phase0_status': phase0_status
        }

    # Initialize Phase0TestHarness with 50 iterations
    logger.info("Initializing Phase0TestHarness for full test...")
    harness = Phase0TestHarness(
        test_name='full_test',
        max_iterations=50,
        model='gemini-2.5-flash',
        checkpoint_interval=10  # Save checkpoint every 10 iterations
    )

    # Run test
    try:
        logger.info("Starting 50-iteration template mode test...")
        logger.info("")

        results = harness.run(data=data, resume_from_checkpoint=None)

        # Enhance results with Phase 0 status
        results['phase0_status'] = phase0_status
        results['log_file'] = log_file
        results['success'] = results.get('test_completed', False)

        # Print summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("PHASE 0 FULL TEST - COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Test completed: {results['success']}")
        logger.info(f"Total iterations: {results.get('total_iterations', 0)}")
        logger.info(f"Success rate: {results.get('success_rate', 0.0):.1f}%")
        logger.info(f"Champion updates: {results.get('champion_update_count', 0)} ({results.get('champion_update_rate', 0.0):.1f}%)")
        logger.info(f"Best Sharpe: {results.get('best_sharpe', 0.0):.4f}")
        logger.info(f"Avg Sharpe: {results.get('avg_sharpe', 0.0):.4f}")
        logger.info(f"Parameter diversity: {results.get('param_diversity', 0)} unique ({results.get('param_diversity_rate', 0.0):.1f}%)")
        logger.info(f"Validation pass rate: {results.get('validation_pass_rate', 0.0):.1f}%")
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
            'phase0_status': phase0_status
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
            'phase0_status': phase0_status
        }


def main():
    """Main entry point."""
    try:
        print("\n🚀 Starting Phase 0 template mode full test (50 iterations)...\n")
        print("⏱️  Estimated duration: 10-12 minutes\n")

        results = run_phase0_full_test()

        if results.get('success'):
            print(f"\n✅ Full test completed successfully")
            print(f"   Total iterations: {results.get('total_iterations', 0)}")
            print(f"   Success rate: {results.get('success_rate', 0.0):.1f}%")
            print(f"   Champion updates: {results.get('champion_update_count', 0)} ({results.get('champion_update_rate', 0.0):.1f}%)")
            print(f"   Best Sharpe: {results.get('best_sharpe', 0.0):.4f}")
            print(f"   Avg Sharpe: {results.get('avg_sharpe', 0.0):.4f}")
            print(f"   Parameter diversity: {results.get('param_diversity', 0)} unique ({results.get('param_diversity_rate', 0.0):.1f}%)")
            print(f"   Validation pass rate: {results.get('validation_pass_rate', 0.0):.1f}%")

            # Phase 0 status
            phase0_status = results.get('phase0_status', {})
            if phase0_status.get('all_available'):
                print(f"   Phase 0 components: ✅ All available")

            print(f"   Log file: {results['log_file']}")

            # Decision analysis
            print("\n📊 Phase 0 Decision Analysis:")
            champion_update_rate = results.get('champion_update_rate', 0.0)
            avg_sharpe = results.get('avg_sharpe', 0.0)
            param_diversity = results.get('param_diversity', 0)

            if champion_update_rate >= 5.0 and avg_sharpe > 1.0:
                print("   ✅ SUCCESS: Template mode meets both targets")
                print("   📝 Recommendation: Skip population-based learning, use template mode")
            elif (champion_update_rate >= 2.0 and champion_update_rate < 5.0) or (avg_sharpe >= 0.8 and avg_sharpe <= 1.0):
                print("   ⚠️  PARTIAL: Template mode shows promise but below targets")
                print("   📝 Recommendation: Consider hybrid approach (template + population-based)")
            else:
                print("   ❌ FAILURE: Template mode below thresholds")
                print("   📝 Recommendation: Proceed to population-based learning")

            print(f"\n   Metrics achieved:")
            print(f"   - Champion update rate: {champion_update_rate:.1f}% (target: ≥5%)")
            print(f"   - Average Sharpe: {avg_sharpe:.4f} (target: >1.0)")
            print(f"   - Parameter diversity: {param_diversity} (target: ≥30)")

            sys.exit(0)
        else:
            print(f"\n❌ Full test failed: {results.get('error', 'Unknown error')}")
            print(f"   Log file: {results.get('log_file', 'N/A')}")
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
