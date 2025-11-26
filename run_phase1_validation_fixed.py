#!/usr/bin/env python3
"""
Phase 1 Validation Test - Corrected Version
===========================================

Validates Phase 1 improvements (Tasks 1.1, 1.2, 1.2.5, 1.3):
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
import json
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.learning.learning_config import LearningConfig
from src.learning.learning_loop import LearningLoop

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_results(innovations_file: Path) -> dict:
    """Analyze results from innovations.jsonl file.

    Args:
        innovations_file: Path to innovations.jsonl

    Returns:
        Dictionary with analysis results
    """
    if not innovations_file.exists():
        return {
            'total': 0,
            'successful': 0,
            'success_rate': 0.0,
            'avg_sharpe': 0.0,
            'best_sharpe': 0.0,
            'levels': {}
        }

    iterations = []
    with open(innovations_file) as f:
        for line in f:
            iterations.append(json.loads(line))

    # Count successes (execution_result.success = true)
    successful = [
        it for it in iterations
        if it.get('execution_result', {}).get('success', False)
    ]

    # Get sharpe ratios
    sharpes = []
    for it in successful:
        sr = it.get('metrics', {}).get('sharpe_ratio')
        if sr is not None:
            sharpes.append(sr)

    # Classification levels
    levels = {}
    for it in iterations:
        level = it.get('classification_level', 'unknown')
        levels[level] = levels.get(level, 0) + 1

    total = len(iterations)
    success_rate = len(successful) / total if total > 0 else 0
    avg_sharpe = sum(sharpes) / len(sharpes) if sharpes else 0
    best_sharpe = max(sharpes) if sharpes else 0

    return {
        'total': total,
        'successful': len(successful),
        'success_rate': success_rate,
        'avg_sharpe': avg_sharpe,
        'best_sharpe': best_sharpe,
        'levels': levels
    }


def run_mode(config_path: str, mode_name: str) -> dict:
    """Run single mode test.

    Args:
        config_path: Path to config YAML file
        mode_name: Name of mode (for display)

    Returns:
        Dictionary with results
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Running {mode_name} mode...")
    logger.info(f"Config: {config_path}")
    logger.info('='*80)

    # Load and run
    config = LearningConfig.from_yaml(config_path)
    loop = LearningLoop(config)

    start_time = datetime.now()
    loop.run()
    duration = (datetime.now() - start_time).total_seconds()

    # Analyze results
    history_file = Path(config.history_file)
    results = analyze_results(history_file)
    results['mode'] = mode_name
    results['duration'] = duration

    return results


def main():
    logger.info("="*80)
    logger.info("PHASE 1 VALIDATION TEST - 20 Iterations x 3 Modes")
    logger.info("="*80)
    logger.info("\nPhase 1 Improvements:")
    logger.info("  ✅ Task 1.1: Field catalog (160 fields)")
    logger.info("  ✅ Task 1.2: API documentation")
    logger.info("  ✅ Task 1.2.5: System prompt with CoT")
    logger.info("  ✅ Task 1.3: Field validation helper")
    logger.info("\nTarget: LLM Only 20% → 55%+\n")

    # Run three modes with Phase 1 configs
    results = []
    for config_file, mode in [
        ('experiments/llm_learning_validation/config_phase1_llm_only_20.yaml', 'LLM Only'),
        ('experiments/llm_learning_validation/config_phase1_fg_only_20.yaml', 'Factor Graph'),
        ('experiments/llm_learning_validation/config_phase1_hybrid_20.yaml', 'Hybrid')
    ]:
        try:
            result = run_mode(config_file, mode)
            results.append(result)

            # Show immediate results
            logger.info(f"\n{mode} Results:")
            logger.info(f"  Success Rate: {result['success_rate']:.1%} ({result['successful']}/{result['total']})")
            logger.info(f"  Avg Sharpe: {result['avg_sharpe']:.4f}")
            logger.info(f"  Best Sharpe: {result['best_sharpe']:.4f}")
            logger.info(f"  Duration: {result['duration']:.1f}s")
            logger.info(f"  Levels: {result['levels']}")

        except Exception as e:
            logger.error(f"❌ Failed to run {mode}: {e}", exc_info=True)
            continue

    # Print summary
    logger.info("\n" + "="*80)
    logger.info("PHASE 1 VALIDATION RESULTS")
    logger.info("="*80)

    if not results:
        logger.error("❌ No results to analyze")
        return 1

    # Find LLM result
    llm_result = next((r for r in results if r['mode'] == 'LLM Only'), None)

    if not llm_result:
        logger.error("❌ LLM Only result not found")
        return 1

    # Print detailed results
    for r in results:
        logger.info(f"\n{r['mode']}:")
        logger.info(f"  Success Rate: {r['success_rate']:.1%} ({r['successful']}/{r['total']})")
        logger.info(f"  Classification Breakdown: {r['levels']}")
        logger.info(f"  Avg Sharpe: {r['avg_sharpe']:.4f}")
        logger.info(f"  Best Sharpe: {r['best_sharpe']:.4f}")
        logger.info(f"  Duration: {r['duration']:.2f}s")

    # Evaluation
    baseline = 0.20

    logger.info("\n" + "="*80)
    logger.info("EVALUATION")
    logger.info("="*80)
    logger.info(f"\n📊 Baseline: {baseline:.1%}")
    logger.info(f"📊 Phase 1: {llm_result['success_rate']:.1%}")
    logger.info(f"📊 Change: {(llm_result['success_rate'] - baseline):.1%}\n")

    if llm_result['success_rate'] >= 0.55:
        logger.info("✅ PHASE 1 PASSED! LLM ≥55%")
        return 0
    elif llm_result['success_rate'] > baseline:
        logger.info(f"⚠️  PARTIAL SUCCESS: {llm_result['success_rate']:.1%} (target: 55%)")
        return 1
    else:
        logger.info("❌ FAILED: No improvement")
        return 1


if __name__ == '__main__':
    sys.exit(main())
