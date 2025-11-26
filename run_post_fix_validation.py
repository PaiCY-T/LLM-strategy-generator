#!/usr/bin/env python3
"""
Post-Fix Validation Test
=========================

Quick 5-iteration test to validate the field name fixes:
- price:成交量 → price:成交股數 (fixed in prompt_builder.py)
- MAX_PROMPT_TOKENS: 2000 → 100000 (fixed in prompt_builder.py)

Expected Results:
- LLM Only: 0% → 80%+ success rate
- Factor Graph: Baseline comparison (~100%)
- Hybrid: 44% → 70%+ success rate

Test Duration: ~5-10 minutes (5 iterations x 3 modes)
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
    logger.info("POST-FIX VALIDATION TEST - 5 Iterations")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Fixes Applied:")
    logger.info("  1. Field name: price:成交量 → price:成交股數 (3 locations)")
    logger.info("  2. Token limit: 2,000 → 100,000 (50x increase)")
    logger.info("")
    logger.info("Expected Improvements:")
    logger.info("  - LLM Only: 0% → 80%+ success rate")
    logger.info("  - Hybrid: 44% → 70%+ success rate")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")

    # Create result directory
    result_dir = Path("experiments/llm_learning_validation/results/post_fix_validation")
    result_dir.mkdir(parents=True, exist_ok=True)

    # Run 5-iteration test for all three modes
    iteration_count = 5

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
            experiment_name=f"post_fix_validation_{mode}",
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
    logger.info("POST-FIX VALIDATION SUMMARY")
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

    # Evaluation
    logger.info("=" * 80)
    logger.info("EVALUATION")
    logger.info("=" * 80)
    logger.info("")

    llm_success_rate = llm_result['success_rate']
    hybrid_success_rate = hybrid_result['success_rate']

    if llm_success_rate >= 0.8:
        logger.info("✅ LLM VALIDATION PASSED!")
        logger.info(f"   LLM success rate improved to {llm_success_rate:.1%} (target: 80%+)")
    elif llm_success_rate > 0:
        logger.info(f"⚠️  LLM PARTIAL SUCCESS")
        logger.info(f"   LLM success rate: {llm_success_rate:.1%} (target: 80%+)")
        logger.info(f"   Some improvement but not meeting target")
    else:
        logger.info("❌ LLM VALIDATION FAILED")
        logger.info(f"   LLM success rate still at {llm_success_rate:.1%}")
        logger.info(f"   Field name fix may not have resolved the issue")

    logger.info("")

    if hybrid_success_rate >= 0.7:
        logger.info("✅ HYBRID VALIDATION PASSED!")
        logger.info(f"   Hybrid success rate improved to {hybrid_success_rate:.1%} (target: 70%+)")
    elif hybrid_success_rate > 0.44:
        logger.info(f"⚠️  HYBRID PARTIAL SUCCESS")
        logger.info(f"   Hybrid success rate: {hybrid_success_rate:.1%} (target: 70%+)")
        logger.info(f"   Some improvement from 44% baseline")
    else:
        logger.info("⚠️  HYBRID NO IMPROVEMENT")
        logger.info(f"   Hybrid success rate: {hybrid_success_rate:.1%} (baseline: 44%)")

    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST COMPLETE")
    logger.info("=" * 80)

    return 0 if llm_success_rate >= 0.8 else 1


if __name__ == "__main__":
    sys.exit(main())
