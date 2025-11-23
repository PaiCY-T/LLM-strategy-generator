#!/usr/bin/env python3
"""
Phase 1 Validation Test - 20 Iterations
========================================

Validate Phase 1 improvements (Tasks 1.1, 1.2, 1.2.5, 1.3):
- Task 1.1: Complete field catalog (160 fields)
- Task 1.2: API documentation with all fields
- Task 1.2.5: System prompt with Chain of Thought
- Task 1.3: Field validation helper

Expected Results (Phase 1 Target):
- LLM Only: 20% → 55%+ success rate
- Field errors: Should drop to <15% of failures
- Token count: <25K expected

Test Duration: ~15-25 minutes (20 iterations x 3 modes)
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from learning.iteration_executor import IterationExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 80)
    logger.info("PHASE 1 VALIDATION TEST - 20 Iterations")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Phase 1 Improvements Applied:")
    logger.info("  ✅ Task 1.1: Complete field catalog (160 fields)")
    logger.info("  ✅ Task 1.2: API documentation enhancement")
    logger.info("  ✅ Task 1.2.5: System prompt with Chain of Thought")
    logger.info("  ✅ Task 1.3: Field validation helper")
    logger.info("")
    logger.info("Expected Improvements (vs Baseline 20%):")
    logger.info("  - LLM Only: 20% → 55%+ success rate")
    logger.info("  - Field errors: <15% of failures")
    logger.info("  - Token count: <25K per prompt")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")

    # Create result directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_dir = Path(f"experiments/llm_learning_validation/results/phase1_validation_{timestamp}")
    result_dir.mkdir(parents=True, exist_ok=True)

    # Run 20-iteration test for all three modes
    iteration_count = 20

    modes = ["llm_only", "fg_only", "hybrid"]
    results = {}

    for mode in modes:
        logger.info(f"Testing {mode.upper()} mode...")
        logger.info("-" * 80)

        # Create mode-specific result directory
        mode_dir = result_dir / mode
        mode_dir.mkdir(exist_ok=True)

        # Initialize executor for this mode
        executor = IterationExecutor(
            experiment_name=f"phase1_validation_{mode}",
            result_dir=str(mode_dir),
            mode=mode,
            max_iterations=iteration_count,
            champion_tracker_path=str(mode_dir / "champion_tracker.json"),
            failure_patterns_path="artifacts/data/failure_patterns.json"
        )

        # Run iterations
        start_time = datetime.now()
        result = executor.run_iterations(max_iterations=iteration_count)
        duration = (datetime.now() - start_time).total_seconds()

        # Store results
        results[mode] = {
            **result,
            'duration': duration
        }

        logger.info(f"  Success Rate: {result['success_rate']:.1%}")
        logger.info(f"  Successful Strategies: {result['successful_count']}/{iteration_count}")
        logger.info(f"  Duration: {duration:.1f}s")
        logger.info("")

    # Print summary comparison
    logger.info("=" * 80)
    logger.info("PHASE 1 VALIDATION SUMMARY")
    logger.info("=" * 80)
    logger.info("")

    # LLM Only Results
    llm_result = results['llm_only']
    logger.info(f"LLM Only:")
    logger.info(f"  Success Rate: {llm_result['success_rate']:.1%}")
    logger.info(f"  Classification Breakdown:")
    for level, count in llm_result['level_breakdown'].items():
        logger.info(f"    {level}: {count}")
    logger.info(f"  Avg Sharpe: {llm_result['avg_sharpe']:.4f}")
    logger.info(f"  Best Sharpe: {llm_result['best_sharpe']:.4f}")
    logger.info(f"  Duration: {llm_result['duration']:.2f}s")
    logger.info("")

    # Factor Graph Results
    fg_result = results['fg_only']
    logger.info(f"Factor Graph (Baseline):")
    logger.info(f"  Success Rate: {fg_result['success_rate']:.1%}")
    logger.info(f"  Classification Breakdown:")
    for level, count in fg_result['level_breakdown'].items():
        logger.info(f"    {level}: {count}")
    logger.info(f"  Avg Sharpe: {fg_result['avg_sharpe']:.4f}")
    logger.info(f"  Best Sharpe: {fg_result['best_sharpe']:.4f}")
    logger.info(f"  Duration: {fg_result['duration']:.2f}s")
    logger.info("")

    # Hybrid Results
    hybrid_result = results['hybrid']
    logger.info(f"Hybrid:")
    logger.info(f"  Success Rate: {hybrid_result['success_rate']:.1%}")
    logger.info(f"  Classification Breakdown:")
    for level, count in hybrid_result['level_breakdown'].items():
        logger.info(f"    {level}: {count}")
    logger.info(f"  Avg Sharpe: {hybrid_result['avg_sharpe']:.4f}")
    logger.info(f"  Best Sharpe: {hybrid_result['best_sharpe']:.4f}")
    logger.info(f"  Duration: {hybrid_result['duration']:.2f}s")
    logger.info("")

    # Evaluation against Phase 1 targets
    logger.info("=" * 80)
    logger.info("PHASE 1 TARGET EVALUATION")
    logger.info("=" * 80)
    logger.info("")

    llm_success_rate = llm_result['success_rate']
    baseline_rate = 0.20  # 20% baseline from pre-Phase-1 test

    logger.info(f"📊 Baseline (Pre-Phase-1): {baseline_rate:.1%}")
    logger.info(f"📊 Phase 1 Result: {llm_success_rate:.1%}")
    logger.info(f"📊 Improvement: {(llm_success_rate - baseline_rate):.1%}")
    logger.info("")

    if llm_success_rate >= 0.55:
        logger.info("✅ PHASE 1 VALIDATION PASSED!")
        logger.info(f"   LLM success rate: {llm_success_rate:.1%} (target: 55%+)")
        logger.info(f"   Improvement from baseline: +{(llm_success_rate - baseline_rate)*100:.1f}%")
    elif llm_success_rate > baseline_rate:
        logger.info(f"⚠️  PHASE 1 PARTIAL SUCCESS")
        logger.info(f"   LLM success rate: {llm_success_rate:.1%} (target: 55%+)")
        logger.info(f"   Improved from {baseline_rate:.1%} but not meeting Phase 1 target")
        logger.info(f"   Additional improvements needed in Phase 2-4")
    else:
        logger.info("❌ PHASE 1 VALIDATION FAILED")
        logger.info(f"   LLM success rate: {llm_success_rate:.1%} (no improvement)")
        logger.info(f"   Baseline: {baseline_rate:.1%}")
        logger.info(f"   Phase 1 improvements may not be working as expected")

    logger.info("")

    # Check if we maintain other modes
    if fg_result['success_rate'] >= 0.85:
        logger.info("✅ Factor Graph baseline maintained (≥85%)")
    else:
        logger.info(f"⚠️  Factor Graph performance degraded: {fg_result['success_rate']:.1%}")

    if hybrid_result['success_rate'] >= 0.70:
        logger.info("✅ Hybrid performance maintained (≥70%)")
    else:
        logger.info(f"⚠️  Hybrid performance: {hybrid_result['success_rate']:.1%} (baseline: 70%)")

    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST COMPLETE")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Results saved to: {result_dir}")

    # Return success if Phase 1 target met
    return 0 if llm_success_rate >= 0.55 else 1


if __name__ == "__main__":
    sys.exit(main())
