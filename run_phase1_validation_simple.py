#!/usr/bin/env python3
"""Simple Phase 1 Validation using existing LearningLoop."""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.learning.learning_config import LearningConfig
from src.learning.learning_loop import LearningLoop

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_mode(config_path: str, mode_name: str) -> dict:
    """Run single mode test."""
    logger.info(f"\n{'='*80}")
    logger.info(f"Running {mode_name} mode...")
    logger.info(f"Config: {config_path}")
    logger.info('='*80)

    # Load and run
    config = LearningConfig.from_yaml(config_path)
    loop = LearningLoop(config)
    loop.run()

    # Load results
    history_file = Path(config.history.file)
    iterations = []
    if history_file.exists():
        with open(history_file) as f:
            for line in f:
                iterations.append(json.loads(line))

    # Calculate stats
    successful = sum(1 for it in iterations if it.get('status') == 'success')
    total = len(iterations)
    success_rate = successful / total if total > 0 else 0

    sharpes = [it['metrics']['sharpe_ratio'] for it in iterations
               if it.get('status') == 'success' and 'metrics' in it]
    avg_sharpe = sum(sharpes) / len(sharpes) if sharpes else 0
    best_sharpe = max(sharpes) if sharpes else 0

    return {
        'mode': mode_name,
        'total': total,
        'successful': successful,
        'success_rate': success_rate,
        'avg_sharpe': avg_sharpe,
        'best_sharpe': best_sharpe
    }


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

    # Run three modes
    results = []
    for config_file, mode in [
        ('experiments/llm_learning_validation/config_llm_only_20.yaml', 'LLM Only'),
        ('experiments/llm_learning_validation/config_fg_only_20.yaml', 'Factor Graph'),
        ('experiments/llm_learning_validation/config_hybrid_20.yaml', 'Hybrid')
    ]:
        result = run_mode(config_file, mode)
        results.append(result)

    # Print summary
    logger.info("\n" + "="*80)
    logger.info("PHASE 1 VALIDATION RESULTS")
    logger.info("="*80)

    for r in results:
        logger.info(f"\n{r['mode']}:")
        logger.info(f"  Success Rate: {r['success_rate']:.1%} ({r['successful']}/{r['total']})")
        logger.info(f"  Avg Sharpe: {r['avg_sharpe']:.4f}")
        logger.info(f"  Best Sharpe: {r['best_sharpe']:.4f}")

    # Evaluation
    llm_result = next(r for r in results if r['mode'] == 'LLM Only')
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
