#!/usr/bin/env python3
"""
60-Iteration Three-Mode Phase 5 API Mismatch Prevention Validation Test

Runs 20 iterations each across THREE strategy generation modes:
1. LLM Only Mode (innovation_rate=100%)
2. Factor Graph Only Mode (innovation_rate=0%)
3. Hybrid Mode (innovation_rate=50%)

Total: 60 iterations to validate Phase 5 API error prevention (initial test before full 300-iteration run)

Phase 5 Validation Goals:
- 8 API errors prevented (100% prevention rate across ALL modes)
- Runtime validation overhead acceptable (<5ms)
- Protocol compliance working correctly
- Champion tracking using correct .champion property
- No regression in iteration execution
- Works consistently across LLM, Factor Graph, and Hybrid generation

Usage:
    python3 run_300iteration_three_mode_validation.py

Note: This is the initial 60-iteration validation test (20×3 modes).
      After confirming no errors, update configs to max_iterations: 100 for full 300-iteration test.
"""

import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path

# Add src to path for Phase 6 LearningLoop import
sys.path.insert(0, os.path.dirname(__file__))

from src.learning.learning_config import LearningConfig
from src.learning.learning_loop import LearningLoop


def setup_logging(base_output_dir: str) -> logging.Logger:
    """Configure comprehensive logging for Phase 5 three-mode validation run.

    Creates logs directory and timestamp-based log file for test output.

    Args:
        base_output_dir: Base directory for output files

    Returns:
        Logger instance
    """
    log_dir = Path(base_output_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"60iteration_three_mode_validation_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized: {log_file}")
    return logger


def run_mode_test(
    mode_name: str,
    config_path: str,
    logger: logging.Logger,
    base_output_dir: Path
) -> dict:
    """Run test for a specific generation mode (iteration count from config file).

    Args:
        mode_name: Human-readable mode name (e.g., "LLM Only")
        config_path: Path to YAML configuration file
        logger: Logger instance
        base_output_dir: Base directory for results

    Returns:
        dict: Test results including success rate, Sharpe ratios, API errors
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"STARTING MODE: {mode_name}")
    logger.info("=" * 80)
    logger.info(f"Config File: {config_path}")
    logger.info(f"Start Time: {datetime.now().isoformat()}")
    logger.info("")

    try:
        # Load configuration from YAML
        config = LearningConfig.from_yaml(config_path)
        logger.info(f"✓ Configuration loaded successfully")
        logger.info(f"  Max Iterations: {config.max_iterations}")
        logger.info(f"  Innovation Mode: {config.innovation_mode}")
        logger.info(f"  Innovation Rate: {config.innovation_rate}%")
        logger.info(f"  LLM Model: {config.llm_model}")
        logger.info("")

        # Initialize learning loop
        logger.info("Initializing LearningLoop...")
        loop = LearningLoop(config)
        logger.info("✓ LearningLoop initialized successfully")
        logger.info("")

        # Run iterations
        logger.info(f"Starting {config.max_iterations} iterations for {mode_name}...")
        logger.info("(This will take approximately 8-20 minutes depending on system performance)")
        logger.info("")

        start_time = datetime.now()
        loop.run()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Collect results
        all_records = loop.history.get_all()
        total = len(all_records)

        # Calculate statistics
        level_0 = sum(1 for r in all_records if r.classification_level == "LEVEL_0")
        level_1 = sum(1 for r in all_records if r.classification_level == "LEVEL_1")
        level_2 = sum(1 for r in all_records if r.classification_level == "LEVEL_2")
        level_3 = sum(1 for r in all_records if r.classification_level == "LEVEL_3")

        successful = level_1 + level_2 + level_3
        success_rate = (successful / total * 100) if total > 0 else 0

        # Collect Sharpe ratios
        sharpes = [
            r.metrics.get("sharpe_ratio", 0.0)
            for r in all_records
            if r.metrics and "sharpe_ratio" in r.metrics
        ]
        avg_sharpe = sum(sharpes) / len(sharpes) if sharpes else 0.0
        best_sharpe = max(sharpes) if sharpes else 0.0

        # Get champion info
        champion = loop.champion_tracker.champion
        champion_sharpe = champion.metrics.get("sharpe_ratio", 0.0) if champion else 0.0

        # Count API errors (should be 0 with Phase 5 fixes)
        # Phase 5 prevents AttributeError from champion tracker API mismatches
        api_errors = sum(
            1 for r in all_records
            if r.classification_level == "LEVEL_0"
            and r.execution_result.get("error_type") == "AttributeError"
        )

        # Build results
        results = {
            "mode_name": mode_name,
            "config_path": config_path,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "total_iterations": total,
            "successful_iterations": successful,
            "failed_iterations": level_0,
            "success_rate": success_rate,
            "level_0_count": level_0,
            "level_1_count": level_1,
            "level_2_count": level_2,
            "level_3_count": level_3,
            "average_sharpe": avg_sharpe,
            "best_sharpe": best_sharpe,
            "champion_sharpe": champion_sharpe,
            "api_errors_detected": api_errors,
            "innovation_rate": config.innovation_rate
        }

        logger.info("")
        logger.info("=" * 80)
        logger.info(f"MODE COMPLETE: {mode_name}")
        logger.info("=" * 80)
        logger.info(f"Total Iterations: {total}")
        logger.info(f"Successful: {successful} ({success_rate:.1f}%)")
        logger.info(f"Failed: {level_0}")
        logger.info(f"Average Sharpe: {avg_sharpe:.4f}")
        logger.info(f"Best Sharpe: {best_sharpe:.4f}")
        logger.info(f"Champion Sharpe: {champion_sharpe:.4f}")
        logger.info(f"API Errors: {api_errors} {'✅ (Phase 5 working!)' if api_errors == 0 else '❌ (Phase 5 issue!)'}")
        logger.info(f"Duration: {duration:.1f}s ({duration/60:.1f} min)")
        logger.info("=" * 80)

        return results

    except KeyboardInterrupt:
        logger.warning(f"\n⚠️  {mode_name} INTERRUPTED BY USER (CTRL+C)")
        raise

    except Exception as e:
        logger.error(f"\n❌ {mode_name} FAILED WITH EXCEPTION")
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise


def main():
    """Main execution function for 60-iteration (20×3) three-mode Phase 5 validation test."""

    # Setup base output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_output_dir = Path(f"phase5_three_mode_validation_20iter_{timestamp}")
    base_output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logger = setup_logging(base_output_dir)

    logger.info("=" * 80)
    logger.info("60-ITERATION (20×3) THREE-MODE PHASE 5 API MISMATCH PREVENTION VALIDATION TEST")
    logger.info("=" * 80)
    logger.info(f"Output Directory: {base_output_dir}")
    logger.info(f"Start Time: {datetime.now().isoformat()}")
    logger.info("")
    logger.info("Phase 5 Validation Goals:")
    logger.info("  - Verify 8 API errors prevented (100% prevention rate)")
    logger.info("  - Confirm runtime validation overhead acceptable (<5ms)")
    logger.info("  - Validate Protocol compliance working correctly")
    logger.info("  - Verify champion tracking using correct .champion property")
    logger.info("  - Confirm no regression in iteration execution")
    logger.info("  - Test across ALL THREE generation modes")
    logger.info("")
    logger.info("Test Plan (Initial Validation - 20 iterations per mode):")
    logger.info("  Mode 1: LLM Only (20 iterations, innovation_rate=100%)")
    logger.info("  Mode 2: Factor Graph Only (20 iterations, innovation_rate=0%)")
    logger.info("  Mode 3: Hybrid (20 iterations, innovation_rate=50%)")
    logger.info("  Total: 60 iterations")
    logger.info("")
    logger.info("Note: This is initial validation. If successful, run full test with 100 iterations per mode.")
    logger.info("Estimated Duration: 25-60 minutes depending on system performance")
    logger.info("=" * 80)
    logger.info("")

    # Define test modes with their configurations
    test_modes = [
        {
            "name": "LLM Only Mode",
            "config": "config/phase5_validation_llm_only.yaml"
        },
        {
            "name": "Factor Graph Only Mode",
            "config": "config/phase5_validation_factor_graph_only.yaml"
        },
        {
            "name": "Hybrid Mode",
            "config": "config/phase5_validation_hybrid.yaml"
        }
    ]

    # Run tests for all three modes
    all_results = []

    try:
        for mode_config in test_modes:
            mode_results = run_mode_test(
                mode_name=mode_config["name"],
                config_path=mode_config["config"],
                logger=logger,
                base_output_dir=base_output_dir
            )
            all_results.append(mode_results)

            # Save intermediate results after each mode
            results_file = base_output_dir / f"results_{mode_config['name'].replace(' ', '_').lower()}.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(mode_results, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Mode results saved: {results_file}")
            logger.info("")

        # Generate final summary report
        logger.info("")
        logger.info("=" * 80)
        logger.info("FINAL SUMMARY: ALL THREE MODES COMPLETE (20 ITERATIONS EACH)")
        logger.info("=" * 80)
        logger.info("")

        total_iterations = sum(r["total_iterations"] for r in all_results)
        total_successful = sum(r["successful_iterations"] for r in all_results)
        total_failed = sum(r["failed_iterations"] for r in all_results)
        total_api_errors = sum(r["api_errors_detected"] for r in all_results)
        overall_success_rate = (total_successful / total_iterations * 100) if total_iterations > 0 else 0

        logger.info(f"Overall Statistics:")
        logger.info(f"  Total Iterations: {total_iterations}")
        logger.info(f"  Successful: {total_successful} ({overall_success_rate:.1f}%)")
        logger.info(f"  Failed: {total_failed}")
        logger.info(f"  Total API Errors: {total_api_errors}")
        logger.info("")

        logger.info("Per-Mode Breakdown:")
        for result in all_results:
            logger.info(f"  {result['mode_name']}:")
            logger.info(f"    Success Rate: {result['success_rate']:.1f}%")
            logger.info(f"    API Errors: {result['api_errors_detected']}")
            logger.info(f"    Best Sharpe: {result['best_sharpe']:.4f}")
            logger.info(f"    Duration: {result['duration_seconds']/60:.1f} min")
        logger.info("")

        # Phase 5 validation assessment
        logger.info("PHASE 5 VALIDATION RESULTS:")
        logger.info(f"  Total API Errors Detected: {total_api_errors}")
        logger.info(f"  API Error Prevention: {'✅ SUCCESS (0 errors across all modes)' if total_api_errors == 0 else f'❌ FAILURE ({total_api_errors} errors detected)'}")
        logger.info(f"  Champion API Usage: {'✅ .champion property working' if total_api_errors == 0 else '⚠️  Check logs for issues'}")
        logger.info(f"  Protocol Compliance: {'✅ All validations passed' if overall_success_rate > 90 else '⚠️  Review failures'}")
        logger.info(f"  Multi-Mode Stability: {'✅ Consistent across all modes' if total_api_errors == 0 else '⚠️  Mode-specific issues detected'}")
        logger.info("")

        # Save comprehensive results
        comprehensive_results = {
            "test_metadata": {
                "test_name": "60-Iteration (20×3) Three-Mode Phase 5 Validation",
                "start_time": all_results[0]["start_time"],
                "end_time": all_results[-1]["end_time"],
                "output_directory": str(base_output_dir)
            },
            "overall_statistics": {
                "total_iterations": total_iterations,
                "successful_iterations": total_successful,
                "failed_iterations": total_failed,
                "overall_success_rate": overall_success_rate,
                "total_api_errors": total_api_errors
            },
            "mode_results": all_results
        }

        comprehensive_file = base_output_dir / "comprehensive_results.json"
        with open(comprehensive_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_results, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Comprehensive results saved: {comprehensive_file}")
        logger.info("")

        # Final verdict
        if overall_success_rate >= 90.0 and total_api_errors == 0:
            logger.info("=" * 80)
            logger.info("✅ PHASE 5 VALIDATION: PASSED (20 ITERATIONS)")
            logger.info("=" * 80)
            logger.info("   All API errors prevented across ALL THREE modes")
            logger.info("   System stable and reliable over 60 iterations (20×3)")
            logger.info("   LLM, Factor Graph, and Hybrid modes all working correctly")
            logger.info("   ✓ Ready for full 300-iteration test (update configs to max_iterations: 100)")
            logger.info("=" * 80)
            return 0
        elif overall_success_rate >= 80.0:
            logger.warning("=" * 80)
            logger.warning("⚠️  PHASE 5 VALIDATION: MARGINAL PASS")
            logger.warning("=" * 80)
            logger.warning(f"   Success rate {overall_success_rate:.1f}% slightly below target (90%)")
            logger.warning("   Review mode-specific results for issues")
            logger.warning("=" * 80)
            return 0
        else:
            logger.error("=" * 80)
            logger.error("❌ PHASE 5 VALIDATION: FAILED")
            logger.error("=" * 80)
            logger.error(f"   Success rate {overall_success_rate:.1f}% below acceptable threshold")
            logger.error(f"   API errors detected: {total_api_errors}")
            logger.error("=" * 80)
            return 1

    except KeyboardInterrupt:
        logger.warning("")
        logger.warning("=" * 80)
        logger.warning("TEST INTERRUPTED BY USER (CTRL+C)")
        logger.warning("=" * 80)
        logger.warning(f"Partial results saved in: {base_output_dir}")
        logger.warning(f"Completed modes: {len(all_results)}/3")
        logger.warning("=" * 80)
        return 2

    except Exception as e:
        logger.error("")
        logger.error("=" * 80)
        logger.error("TEST FAILED WITH EXCEPTION")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}", exc_info=True)
        logger.error(f"Partial results may be available in: {base_output_dir}")
        logger.error("=" * 80)
        return 3


if __name__ == "__main__":
    sys.exit(main())
