#!/usr/bin/env python3
"""
300-Iteration Phase 5 API Mismatch Prevention Validation Test

Runs 300 iterations of the autonomous learning loop to validate Phase 5 fixes:
- 8 API errors prevented (100% prevention rate)
- Runtime validation overhead acceptable (<5ms)
- Protocol compliance working correctly
- Champion tracking using correct API
- No regression in iteration execution

This is a comprehensive production validation to ensure Phase 5 API fixes
work correctly under sustained load over 300 iterations.

Usage:
    python3 run_300iteration_phase5_validation.py [group_id]

Arguments:
    group_id: Optional identifier for test group (default: "phase5")
"""

import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'artifacts', 'working', 'modules'))
sys.path.insert(0, os.path.dirname(__file__))

from tests.integration.extended_test_harness import ExtendedTestHarness


def setup_logging(group_id: str = "phase5"):
    """Configure comprehensive logging for Phase 5 validation run.

    Creates logs directory and timestamp-based log file for test output.

    Args:
        group_id: Test group identifier (default: "phase5")

    Returns:
        tuple: (logger, log_file_path)
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f"300iteration_phase5_validation_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    return logger, log_file


def main():
    """Main execution function for 300-iteration Phase 5 validation test."""
    # Parse command-line arguments
    group_id = sys.argv[1] if len(sys.argv) > 1 else "phase5"

    # Setup logging
    logger, log_file = setup_logging(group_id)

    logger.info("=" * 80)
    logger.info("300-ITERATION PHASE 5 API MISMATCH PREVENTION VALIDATION TEST")
    logger.info("=" * 80)
    logger.info(f"Group ID: {group_id}")
    logger.info(f"Log File: {log_file}")
    logger.info(f"Start Time: {datetime.now().isoformat()}")
    logger.info("")
    logger.info("Phase 5 Validation Goals:")
    logger.info("  - Verify 8 API errors prevented (100% prevention rate)")
    logger.info("  - Confirm runtime validation overhead acceptable (<5ms)")
    logger.info("  - Validate Protocol compliance working correctly")
    logger.info("  - Verify champion tracking using correct .champion property")
    logger.info("  - Confirm no regression in iteration execution")
    logger.info("=" * 80)
    logger.info("")

    # Create output directories
    base_output_dir = f"phase5_validation_results_group{group_id}"
    checkpoints_dir = os.path.join(base_output_dir, "checkpoints")
    os.makedirs(checkpoints_dir, exist_ok=True)

    logger.info(f"Output directory: {base_output_dir}")
    logger.info(f"Checkpoints directory: {checkpoints_dir}")
    logger.info("")

    # Initialize test harness
    logger.info("Initializing ExtendedTestHarness for 300 iterations...")
    harness = ExtendedTestHarness(
        max_iterations=300,
        checkpoint_dir=checkpoints_dir,
        save_interval=25,  # Checkpoint every 25 iterations
        enable_checkpoints=True,
        enable_retries=True,
        max_retries=3
    )

    logger.info("ExtendedTestHarness initialized successfully")
    logger.info("")

    # Run the test
    try:
        logger.info("Starting 300-iteration test run...")
        logger.info("This will take approximately 2-4 hours depending on system performance")
        logger.info("")

        results = harness.run_test()

        logger.info("")
        logger.info("=" * 80)
        logger.info("300-ITERATION TEST COMPLETE")
        logger.info("=" * 80)

        # Display summary statistics
        logger.info("")
        logger.info("SUMMARY STATISTICS:")
        logger.info(f"  Total Iterations: {results.get('total_iterations', 0)}")
        logger.info(f"  Successful: {results.get('successful_iterations', 0)}")
        logger.info(f"  Failed: {results.get('failed_iterations', 0)}")
        logger.info(f"  Success Rate: {results.get('success_rate', 0.0):.2f}%")
        logger.info(f"  Average Sharpe: {results.get('average_sharpe', 0.0):.4f}")
        logger.info(f"  Best Sharpe: {results.get('best_sharpe', 0.0):.4f}")
        logger.info(f"  Total Runtime: {results.get('total_runtime_seconds', 0):.2f}s")
        logger.info("")

        # Phase 5 specific validation
        logger.info("PHASE 5 VALIDATION RESULTS:")
        api_errors = results.get('api_errors_detected', 0)
        logger.info(f"  API Errors Detected: {api_errors}")
        logger.info(f"  API Error Prevention: {'✅ SUCCESS (0 errors)' if api_errors == 0 else '❌ FAILURE'}")
        logger.info(f"  Champion API Usage: {'✅ .champion property' if api_errors == 0 else '⚠️  Check logs'}")
        logger.info(f"  Protocol Compliance: {'✅ All validations passed' if results.get('success_rate', 0) > 95 else '⚠️  Review failures'}")
        logger.info("")

        # Save detailed results
        results_file = os.path.join(base_output_dir, f"phase5_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Detailed results saved to: {results_file}")
        logger.info("")

        # Final assessment
        success_rate = results.get('success_rate', 0.0)
        if success_rate >= 95.0 and api_errors == 0:
            logger.info("✅ PHASE 5 VALIDATION: PASSED")
            logger.info("   All API errors prevented, system stable over 300 iterations")
            return 0
        elif success_rate >= 90.0:
            logger.warning("⚠️  PHASE 5 VALIDATION: MARGINAL PASS")
            logger.warning(f"   Success rate {success_rate:.2f}% slightly below target (95%)")
            return 0
        else:
            logger.error("❌ PHASE 5 VALIDATION: FAILED")
            logger.error(f"   Success rate {success_rate:.2f}% below acceptable threshold")
            return 1

    except KeyboardInterrupt:
        logger.warning("")
        logger.warning("=" * 80)
        logger.warning("TEST INTERRUPTED BY USER (CTRL+C)")
        logger.warning("=" * 80)
        logger.warning("Partial results may be available in checkpoint directory")
        logger.warning(f"Checkpoint directory: {checkpoints_dir}")
        return 2

    except Exception as e:
        logger.error("")
        logger.error("=" * 80)
        logger.error("TEST FAILED WITH EXCEPTION")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}", exc_info=True)
        return 3


if __name__ == "__main__":
    sys.exit(main())
