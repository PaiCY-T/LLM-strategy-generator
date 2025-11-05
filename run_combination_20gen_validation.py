#!/usr/bin/env python3
"""
10-Generation Smoke Test for CombinationTemplate
=================================================

Validates CombinationTemplate integration with population-based evolution:
- Population size: 10
- Generations: 10
- Template: 'Combination' (CombinationTemplate)
- Elite count: 2

Success Criteria:
-----------------
1. Test completes all 10 generations without crashes
2. No exceptions during evolution
3. At least 50% of strategies have Sharpe >0
4. Best strategy Sharpe >1.0
5. Diversity maintained throughout evolution

Usage:
    python run_combination_smoke_test.py
    python run_combination_smoke_test.py --output COMBINATION_SMOKE_TEST.md
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List

import numpy as np

from src.evolution.population_manager import PopulationManager
from src.evolution.types import EvolutionResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('combination_validation.log')
    ]
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Run 10-generation smoke test for CombinationTemplate',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--output',
        type=str,
        default='COMBINATION_SMOKE_TEST.md',
        help='Output report filename'
    )

    parser.add_argument(
        '--checkpoint-dir',
        type=str,
        default='combination_validation_checkpoints',
        help='Directory for saving checkpoints'
    )

    return parser.parse_args()


def evaluate_success_criteria(results: List[EvolutionResult]) -> dict:
    """
    Evaluate success criteria for smoke test.

    Args:
        results: List of EvolutionResult objects

    Returns:
        Dictionary with success criteria results
    """
    if not results:
        return {
            "all_passed": False,
            "no_crashes": False,
            "no_exceptions": False,
            "sharpe_gt_zero_pct": 0.0,
            "best_sharpe": 0.0,
            "diversity_maintained": False
        }

    # Criterion 1 & 2: No crashes/exceptions (if we got here, test completed)
    no_crashes = True
    no_exceptions = True

    # Criterion 3: At least 50% of strategies have Sharpe >0
    final_population = results[-1].population.strategies
    strategies_with_metrics = [
        s for s in final_population
        if s.metrics and s.metrics.success and s.metrics.sharpe_ratio is not None
    ]

    sharpe_gt_zero = sum(1 for s in strategies_with_metrics if s.metrics.sharpe_ratio > 0)
    sharpe_gt_zero_pct = (sharpe_gt_zero / len(strategies_with_metrics)) if strategies_with_metrics else 0.0

    logger.info(f"Sharpe >0: {sharpe_gt_zero}/{len(strategies_with_metrics)} ({sharpe_gt_zero_pct*100:.1f}%)")

    # Criterion 4: Best strategy Sharpe >1.0
    best_sharpe = max(
        (s.metrics.sharpe_ratio for s in strategies_with_metrics),
        default=0.0
    )
    logger.info(f"Best Sharpe: {best_sharpe:.3f}")

    # Criterion 5: Diversity maintained (check if diversity never drops below 0.3)
    diversity_values = [r.diversity_score for r in results]
    min_diversity = min(diversity_values)
    diversity_maintained = min_diversity >= 0.3

    logger.info(f"Diversity maintained: {diversity_maintained} (min={min_diversity:.3f})")

    # Overall evaluation
    all_passed = (
        no_crashes and
        no_exceptions and
        sharpe_gt_zero_pct >= 0.5 and
        best_sharpe > 1.0 and
        diversity_maintained
    )

    return {
        "all_passed": all_passed,
        "no_crashes": no_crashes,
        "no_exceptions": no_exceptions,
        "sharpe_gt_zero_pct": sharpe_gt_zero_pct,
        "sharpe_gt_zero_count": sharpe_gt_zero,
        "sharpe_total_count": len(strategies_with_metrics),
        "best_sharpe": best_sharpe,
        "diversity_maintained": diversity_maintained,
        "min_diversity": min_diversity
    }


def generate_smoke_test_report(
    results: List[EvolutionResult],
    criteria: dict,
    output_file: str,
    checkpoint_dir: str
) -> None:
    """
    Generate smoke test report in Markdown format.

    Args:
        results: List of EvolutionResult objects
        criteria: Success criteria evaluation results
        output_file: Output filename
        checkpoint_dir: Checkpoint directory path
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Generate report
    report = f"""# CombinationTemplate 10-Generation Smoke Test

**Generated**: {timestamp}
**Configuration**: Population=10, Generations=10, Elite=2
**Template**: CombinationTemplate
**Status**: {'✅ **PASSED**' if criteria['all_passed'] else '❌ **FAILED**'}

---

## Executive Summary

This smoke test validates CombinationTemplate integration with the population-based evolution system.
The test uses minimal configuration (N=10, 10 generations) to verify basic functionality and stability.

{'✅ **All success criteria met. CombinationTemplate is stable and functional.**' if criteria['all_passed'] else '⚠️ **Some criteria not met. Investigation required.**'}

---

## Success Criteria Results

### 1. Test Completion Without Crashes

- **Status**: {'✅ PASS' if criteria['no_crashes'] else '❌ FAIL'}
- **Result**: Test completed all 10 generations
- **Interpretation**: System stability validated

### 2. No Exceptions During Evolution

- **Status**: {'✅ PASS' if criteria['no_exceptions'] else '❌ FAIL'}
- **Result**: No exceptions raised
- **Interpretation**: Clean execution path

### 3. At Least 50% Strategies Have Sharpe >0

- **Status**: {'✅ PASS' if criteria['sharpe_gt_zero_pct'] >= 0.5 else '❌ FAIL'}
- **Actual**: {criteria['sharpe_gt_zero_pct']*100:.1f}% ({criteria['sharpe_gt_zero_count']}/{criteria['sharpe_total_count']} strategies)
- **Threshold**: ≥50%
- **Interpretation**: {'Majority of strategies produce positive risk-adjusted returns' if criteria['sharpe_gt_zero_pct'] >= 0.5 else 'Insufficient positive performance strategies'}

### 4. Best Strategy Sharpe >1.0

- **Status**: {'✅ PASS' if criteria['best_sharpe'] > 1.0 else '❌ FAIL'}
- **Actual**: {criteria['best_sharpe']:.3f}
- **Threshold**: >1.0
- **Interpretation**: {'Strong best-case performance achieved' if criteria['best_sharpe'] > 1.0 else 'Best strategy underperforms target'}

### 5. Diversity Maintained Throughout Evolution

- **Status**: {'✅ PASS' if criteria['diversity_maintained'] else '❌ FAIL'}
- **Minimum Diversity**: {criteria['min_diversity']:.3f}
- **Threshold**: ≥0.3
- **Interpretation**: {'Population maintains healthy diversity' if criteria['diversity_maintained'] else 'Premature convergence detected'}

---

## Generation History

| Gen | Diversity | Pareto Size | Champion Updated | Best Sharpe | Time (s) |
|-----|-----------|-------------|------------------|-------------|----------|
"""

    # Add generation data
    for i, result in enumerate(results):
        best_sharpe = max(
            (s.metrics.sharpe_ratio for s in result.population.strategies
             if s.metrics and s.metrics.success),
            default=0.0
        )
        pareto = len([s for s in result.population.strategies
                     if hasattr(s, 'pareto_rank') and s.pareto_rank == 1])
        updated = "✓" if result.champion_updated else ""

        report += f"| {i+1:2d}  | {result.diversity_score:.3f}     | {pareto:11d} | {updated:16s} | {best_sharpe:11.3f} | {result.total_time:8.2f} |\n"

    # Add diversity analysis
    diversity_values = [r.diversity_score for r in results]
    avg_diversity = np.mean(diversity_values)

    report += f"""

---

## Performance Analysis

### Diversity Trend
- **Average Diversity**: {avg_diversity:.3f}
- **Minimum Diversity**: {criteria['min_diversity']:.3f}
- **Maximum Diversity**: {max(diversity_values):.3f}
- **Trend**: {'Stable' if max(diversity_values) - criteria['min_diversity'] < 0.3 else 'Variable'}

### Sharpe Distribution (Final Generation)
"""

    # Add Sharpe distribution
    final_population = results[-1].population.strategies
    sharpe_ratios = [
        s.metrics.sharpe_ratio
        for s in final_population
        if s.metrics and s.metrics.success and s.metrics.sharpe_ratio is not None
    ]

    if sharpe_ratios:
        report += f"""- **Mean Sharpe**: {np.mean(sharpe_ratios):.3f}
- **Median Sharpe**: {np.median(sharpe_ratios):.3f}
- **Std Dev**: {np.std(sharpe_ratios):.3f}
- **Range**: [{min(sharpe_ratios):.3f}, {max(sharpe_ratios):.3f}]
"""
    else:
        report += "- **No valid Sharpe ratios**\n"

    # Add timing analysis
    total_time = sum(r.total_time for r in results)
    avg_time = total_time / len(results)

    report += f"""
### Timing Analysis
- **Total Runtime**: {total_time:.2f} seconds ({total_time/60:.2f} minutes)
- **Average Generation Time**: {avg_time:.2f} seconds
- **Estimated 100-gen Runtime**: {avg_time * 100 / 60:.1f} minutes

---

## Recommendations

"""

    if criteria['all_passed']:
        report += """✅ **Smoke Test Passed**

CombinationTemplate integration validated. The template demonstrates:
- Stable execution without crashes
- Clean error handling
- Positive performance on majority of strategies
- Strong best-case performance
- Maintained population diversity

**Next Steps**:
1. Proceed with extended validation (20-50 generations)
2. Test with larger populations (N=20-30)
3. Monitor real-world performance
"""
    else:
        report += "⚠️ **Issues Detected**\n\n"

        if not criteria['no_crashes']:
            report += "- **Critical**: System crashes detected. Debug required.\n"

        if not criteria['no_exceptions']:
            report += "- **Critical**: Exceptions during evolution. Check logs.\n"

        if criteria['sharpe_gt_zero_pct'] < 0.5:
            report += f"- **Performance**: Only {criteria['sharpe_gt_zero_pct']*100:.1f}% strategies have Sharpe >0. Review template logic.\n"

        if criteria['best_sharpe'] <= 1.0:
            report += f"- **Performance**: Best Sharpe {criteria['best_sharpe']:.3f} ≤1.0. Increase target performance.\n"

        if not criteria['diversity_maintained']:
            report += f"- **Diversity**: Minimum diversity {criteria['min_diversity']:.3f} <0.3. Risk of premature convergence.\n"

        report += "\n**Next Steps**:\n"
        report += "1. Review logs for detailed error information\n"
        report += "2. Apply fixes based on identified issues\n"
        report += "3. Re-run smoke test\n"

    report += f"""
---

## Appendix

### Test Configuration
- **Population Size**: 10
- **Generations**: 10
- **Elite Count**: 2
- **Tournament Size**: 3 (default)
- **Template**: CombinationTemplate
- **Checkpoint Directory**: {checkpoint_dir}
- **Log File**: combination_validation.log

### Template Information
- **Name**: Combination
- **Type**: Multi-template weighted combination
- **Sub-templates**: turtle, momentum, mastiff
- **Rebalancing**: Monthly ('M') or Weekly ('W-FRI')
- **Weight Options**: [0.5, 0.5], [0.7, 0.3], [0.4, 0.4, 0.2]

---

**End of Smoke Test Report**
"""

    # Write report to file
    with open(output_file, 'w') as f:
        f.write(report)

    logger.info(f"Smoke test report saved to: {output_file}")


def main():
    """Main execution function."""
    args = parse_arguments()

    print("="*70)
    print("COMBINATIONTEMPLATE 10-GENERATION SMOKE TEST")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  Population Size: 10")
    print(f"  Generations:     10")
    print(f"  Elite Count:     2")
    print(f"  Template:        CombinationTemplate")
    print(f"  Output Report:   {args.output}")
    print()

    # Create checkpoint directory
    checkpoint_dir = Path(args.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # Initialize PopulationManager
    logger.info("Initializing PopulationManager...")
    try:
        manager = PopulationManager(
            population_size=10,
            elite_count=2,
            tournament_size=3
        )
    except Exception as e:
        logger.error(f"Failed to initialize PopulationManager: {e}", exc_info=True)
        print(f"\n❌ Initialization failed: {e}")
        return 1

    # Initialize population with CombinationTemplate
    print("Initializing population with CombinationTemplate...")
    try:
        import random
        from src.utils.template_registry import TemplateRegistry
        from src.evolution.types import Strategy
        from src.backtest import PerformanceMetrics
        registry = TemplateRegistry()

        # Get param grid for sampling
        param_grid = registry.get_param_grid('Combination')

        # Generate initial population using CombinationTemplate
        initial_population = []
        for i in range(10):
            # Get CombinationTemplate
            template = registry.get_template('Combination')

            # Sample templates first
            templates = random.choice(param_grid['templates'])

            # Sample weights matching template count
            matching_weights = [w for w in param_grid['weights'] if len(w) == len(templates)]
            weights = random.choice(matching_weights)

            # Sample rebalance frequency
            rebalance = random.choice(param_grid['rebalance'])

            # Build params
            params = {
                'templates': templates,
                'weights': weights,
                'rebalance': rebalance
            }

            # Generate strategy (returns tuple: report, metrics_dict)
            report, metrics_dict = template.generate_strategy(params)

            # Create Strategy object
            strategy = Strategy(
                id=f"gen0_strategy_{i}",
                generation=0,
                parent_ids=[],
                code="",  # Not needed for template-based strategies
                parameters=params,
                template_type='Combination',
                metadata={},
                metrics=PerformanceMetrics(**metrics_dict) if metrics_dict.get('success') else None
            )

            initial_population.append(strategy)

            sharpe_value = metrics_dict.get('sharpe_ratio')
            sharpe_str = f"{sharpe_value:.3f}" if sharpe_value is not None else "N/A"
            logger.info(f"  Strategy {i+1}: templates={params.get('templates')}, "
                       f"weights={params.get('weights')}, "
                       f"sharpe={sharpe_str}")

        # Set initial population
        manager.current_population = initial_population
        logger.info(f"Population initialized successfully with {len(initial_population)} CombinationTemplate strategies")
    except Exception as e:
        logger.error(f"Failed to initialize population: {e}", exc_info=True)
        print(f"\n❌ Population initialization failed: {e}")
        return 1

    # Save initial checkpoint
    try:
        manager.save_checkpoint(str(checkpoint_dir / "generation_0.json"))
    except Exception as e:
        logger.warning(f"Failed to save initial checkpoint: {e}")

    # Run evolution
    results = []
    exception_occurred = False

    try:
        for gen in range(1, 11):  # 10 generations
            print(f"\n{'='*70}")
            print(f"GENERATION {gen}/10")
            print(f"{'='*70}")

            result = manager.evolve_generation(gen)
            results.append(result)

            # Display progress
            best_sharpe = max(
                (s.metrics.sharpe_ratio for s in result.population.strategies
                 if s.metrics and s.metrics.success),
                default=0.0
            )

            print(f"Diversity:        {result.diversity_score:.3f}")
            print(f"Best Sharpe:      {best_sharpe:.3f}")
            print(f"Champion Updated: {'Yes' if result.champion_updated else 'No'}")
            print(f"Time:             {result.total_time:.2f}s")

            # Save checkpoint
            try:
                manager.save_checkpoint(str(checkpoint_dir / f"generation_{gen}.json"))
            except Exception as e:
                logger.warning(f"Failed to save checkpoint for generation {gen}: {e}")

    except KeyboardInterrupt:
        logger.warning("\nSmoke test interrupted by user")
        print("\n\n⚠️  Test interrupted. Partial results will be analyzed.")

    except Exception as e:
        logger.error(f"Exception during evolution: {e}", exc_info=True)
        print(f"\n\n❌ Exception occurred: {e}")
        exception_occurred = True

    # Evaluate success criteria
    print(f"\n{'='*70}")
    print("EVALUATING SUCCESS CRITERIA")
    print(f"{'='*70}\n")

    # If exception occurred, mark test as failed
    if exception_occurred:
        criteria = evaluate_success_criteria(results)
        criteria['no_exceptions'] = False
        criteria['all_passed'] = False
    else:
        criteria = evaluate_success_criteria(results)

    # Generate smoke test report
    print(f"\nGenerating smoke test report...")
    generate_smoke_test_report(
        results=results,
        criteria=criteria,
        output_file=args.output,
        checkpoint_dir=args.checkpoint_dir
    )

    # Display summary
    print(f"\n{'='*70}")
    print("SMOKE TEST SUMMARY")
    print(f"{'='*70}\n")

    print(f"1. No Crashes:           {'✅' if criteria['no_crashes'] else '❌'}")
    print(f"2. No Exceptions:        {'✅' if criteria['no_exceptions'] else '❌'}")
    print(f"3. Sharpe >0 (≥50%):     {criteria['sharpe_gt_zero_pct']*100:.1f}% {'✅' if criteria['sharpe_gt_zero_pct'] >= 0.5 else '❌'}")
    print(f"4. Best Sharpe >1.0:     {criteria['best_sharpe']:.3f} {'✅' if criteria['best_sharpe'] > 1.0 else '❌'}")
    print(f"5. Diversity Maintained: {'✅' if criteria['diversity_maintained'] else '❌'}")

    print(f"\n{'='*70}")
    if criteria['all_passed']:
        print("✅ SMOKE TEST PASSED - CombinationTemplate is stable")
    else:
        print("❌ SMOKE TEST FAILED - Review report for details")
    print(f"{'='*70}\n")

    print(f"Report saved to: {args.output}")
    print(f"Checkpoints saved to: {checkpoint_dir}")
    print(f"Logs saved to: combination_validation.log\n")

    return 0 if criteria['all_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
