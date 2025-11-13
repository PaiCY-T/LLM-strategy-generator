#!/usr/bin/env python3
"""
5-Iteration Template Mode Smoke Test

Quick validation that template mode works end-to-end with the Momentum template.
This is a simplified smoke test focused on template mode functionality.

Expected runtime: ~30 minutes with real API calls
Expected outcome: 5 successful iterations with champion updates

Usage:
    python3 run_5iteration_template_smoke_test.py

Dependencies:
    - Task 2.7 (AutonomousLoop template mode integration) completed
    - FINLAB_API_TOKEN environment variable set
    - Google Gemini API key configured
"""

import os
import sys
import logging
from datetime import datetime

# Add modules to path
sys.path.insert(0, os.path.dirname(__file__))

from artifacts.working.modules.autonomous_loop import AutonomousLoop


def setup_logging():
    """Configure logging for smoke test."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f"template_smoke_test_{timestamp}.log")

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


def run_template_smoke_test():
    """Run 5-iteration template mode smoke test.

    Uses AutonomousLoop with:
    - template_mode=True
    - template_name="Momentum"
    - model="gemini-2.5-flash"
    - max_iterations=5

    Returns:
        Dictionary with test results and metrics
    """
    logger, log_file = setup_logging()

    logger.info("=" * 70)
    logger.info("TEMPLATE MODE SMOKE TEST - START")
    logger.info("=" * 70)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Template: Momentum")
    logger.info(f"Model: google/gemini-2.5-flash")
    logger.info(f"Target iterations: 5")
    logger.info(f"Mode: Template-guided")
    logger.info(f"Log file: {log_file}")
    logger.info("")

    # Load Finlab data
    try:
        data = load_finlab_data()
    except Exception as e:
        logger.error(f"❌ Data loading failed: {e}")
        logger.error("Cannot proceed without data")
        return {
            'success': False,
            'error': str(e),
            'log_file': log_file
        }

    # Initialize AutonomousLoop in template mode
    logger.info("Initializing AutonomousLoop in template mode...")
    try:
        loop = AutonomousLoop(
            template_mode=True,
            template_name="Momentum",
            model="gemini-2.5-flash",
            max_iterations=5,
            data=data
        )
    except Exception as e:
        logger.error(f"❌ Failed to initialize AutonomousLoop: {e}")
        return {
            'success': False,
            'error': f"Initialization failed: {str(e)}",
            'log_file': log_file
        }

    # Run test
    try:
        logger.info("Starting 5-iteration template mode test...")
        logger.info("")

        results = loop.run()

        # Extract key metrics
        champion_updates = results.get('champion_update_count', 0)
        successful_iterations = results.get('successful_iterations', 0)
        failed_iterations = results.get('failed_iterations', 0)
        best_sharpe = results.get('best_sharpe', 0.0)
        final_sharpe = results.get('final_sharpe', 0.0)

        # Calculate success rate
        total_attempts = successful_iterations + failed_iterations
        success_rate = (successful_iterations / total_attempts * 100) if total_attempts > 0 else 0.0

        # Print summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("TEMPLATE MODE SMOKE TEST - COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Successful iterations: {successful_iterations}/5")
        logger.info(f"Failed iterations: {failed_iterations}")
        logger.info(f"Success rate: {success_rate:.1f}%")
        logger.info(f"Champion updates: {champion_updates}/5")
        logger.info(f"Best Sharpe: {best_sharpe:.4f}")
        logger.info(f"Final Sharpe: {final_sharpe:.4f}")
        logger.info("")
        logger.info(f"Log file: {log_file}")
        logger.info("=" * 70)

        return {
            'success': True,
            'successful_iterations': successful_iterations,
            'failed_iterations': failed_iterations,
            'success_rate': success_rate,
            'champion_update_count': champion_updates,
            'best_sharpe': best_sharpe,
            'final_sharpe': final_sharpe,
            'log_file': log_file,
            'full_results': results
        }

    except KeyboardInterrupt:
        logger.warning("")
        logger.warning("=" * 70)
        logger.warning("TEST INTERRUPTED BY USER")
        logger.warning("=" * 70)
        return {
            'success': False,
            'error': 'User interrupted',
            'log_file': log_file
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
            'log_file': log_file
        }


def main():
    """Main entry point."""
    try:
        print("\n🚀 Starting 5-iteration template mode smoke test...\n")
        results = run_template_smoke_test()

        if results.get('success'):
            print(f"\n✅ Template mode smoke test completed successfully")
            print(f"   Successful iterations: {results.get('successful_iterations', 0)}/5")
            print(f"   Success rate: {results.get('success_rate', 0.0):.1f}%")
            print(f"   Champion updates: {results.get('champion_update_count', 0)}/5")
            print(f"   Best Sharpe: {results.get('best_sharpe', 0.0):.4f}")
            print(f"   Final Sharpe: {results.get('final_sharpe', 0.0):.4f}")
            print(f"   Log file: {results['log_file']}")

            # Recommendation
            print("\n📊 Test Results:")
            champion_updates = results.get('champion_update_count', 0)
            success_rate = results.get('success_rate', 0.0)

            if success_rate >= 80.0 and champion_updates >= 3:
                print("   ✅ Template mode working well - Phase 2 integration complete!")
            elif success_rate >= 60.0:
                print("   ⚠️  Template mode functional but some issues - review logs")
            else:
                print("   ❌ Template mode issues detected - investigate before proceeding")

            sys.exit(0)
        else:
            print(f"\n❌ Template mode smoke test failed: {results.get('error', 'Unknown error')}")
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
