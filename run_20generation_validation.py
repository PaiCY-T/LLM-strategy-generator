#!/usr/bin/env python3
"""
20-Generation Validation Script for Population-Based Learning System.

Runs comprehensive validation test with production configuration (N=20, 20 generations)
and evaluates success criteria:
1. Champion update rate ≥10%
2. Rolling variance <0.5
3. P-value <0.05 (vs random baseline)
4. Pareto front size ≥5

Generates detailed validation report with statistical analysis.

Usage:
    python run_20generation_validation.py
    python run_20generation_validation.py --generations 30 --output CUSTOM_REPORT.md

Tasks: 58 (Validation script), 59 (Statistical analysis)
Requirements: All success criteria
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import numpy as np

from src.evolution.population_manager import PopulationManager
from src.evolution.types import EvolutionResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('validation.log')
    ]
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Run 20-generation validation test with success criteria evaluation',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--population-size',
        type=int,
        default=20,
        help='Population size (production: 20)'
    )

    parser.add_argument(
        '--generations',
        type=int,
        default=20,
        help='Number of generations (production: 20)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='VALIDATION_REPORT.md',
        help='Output report filename'
    )

    parser.add_argument(
        '--checkpoint-dir',
        type=str,
        default='validation_checkpoints',
        help='Directory for saving checkpoints'
    )

    return parser.parse_args()


def calculate_champion_update_rate(results: List[EvolutionResult]) -> float:
    """
    Calculate champion update rate (% of generations with champion improvement).

    Success Criterion: ≥10%

    Args:
        results: List of EvolutionResult objects from each generation

    Returns:
        Champion update rate as percentage (0.0-1.0)
    """
    if not results:
        return 0.0

    updates = sum(1 for r in results if r.champion_updated)
    rate = updates / len(results)

    logger.info(f"Champion updates: {updates}/{len(results)} = {rate*100:.1f}%")
    return rate


def calculate_rolling_variance(results: List[EvolutionResult]) -> float:
    """
    Calculate rolling variance of Sharpe ratios in final generation.

    Success Criterion: <0.5

    Args:
        results: List of EvolutionResult objects

    Returns:
        Rolling variance of final generation Sharpe ratios
    """
    if not results:
        return float('inf')

    # Get final generation population
    final_population = results[-1].population.strategies

    # Extract Sharpe ratios from strategies with valid metrics
    sharpe_ratios = [
        s.metrics.sharpe_ratio
        for s in final_population
        if s.metrics and s.metrics.success and s.metrics.sharpe_ratio is not None
    ]

    if len(sharpe_ratios) < 2:
        logger.warning("Insufficient valid Sharpe ratios for variance calculation")
        return float('inf')

    variance = float(np.var(sharpe_ratios))
    logger.info(f"Rolling variance: {variance:.4f} (from {len(sharpe_ratios)} strategies)")

    return variance


def perform_statistical_test(results: List[EvolutionResult]) -> Tuple[float, float]:
    """
    Perform t-test comparing final population against random baseline.

    Success Criterion: p-value <0.05

    Args:
        results: List of EvolutionResult objects

    Returns:
        Tuple of (p_value, cohens_d)
    """
    try:
        from scipy import stats
    except ImportError:
        logger.warning("SciPy not available, skipping statistical test")
        return 1.0, 0.0

    if not results:
        return 1.0, 0.0

    # Get final generation Sharpe ratios
    final_population = results[-1].population.strategies
    evolved_sharpe = [
        s.metrics.sharpe_ratio
        for s in final_population
        if s.metrics and s.metrics.success and s.metrics.sharpe_ratio is not None
    ]

    # Get initial generation Sharpe ratios (random baseline)
    initial_population = results[0].population.strategies if results[0].population else []
    random_sharpe = [
        s.metrics.sharpe_ratio
        for s in initial_population
        if s.metrics and s.metrics.success and s.metrics.sharpe_ratio is not None
    ]

    if len(evolved_sharpe) < 2 or len(random_sharpe) < 2:
        logger.warning("Insufficient data for statistical test")
        return 1.0, 0.0

    # Perform independent samples t-test
    t_stat, p_value = stats.ttest_ind(evolved_sharpe, random_sharpe)

    # Calculate Cohen's d effect size
    pooled_std = np.sqrt(
        ((len(evolved_sharpe) - 1) * np.var(evolved_sharpe) +
         (len(random_sharpe) - 1) * np.var(random_sharpe)) /
        (len(evolved_sharpe) + len(random_sharpe) - 2)
    )

    cohens_d = (np.mean(evolved_sharpe) - np.mean(random_sharpe)) / pooled_std if pooled_std > 0 else 0.0

    logger.info(f"t-test: t={t_stat:.3f}, p={p_value:.4f}, Cohen's d={cohens_d:.3f}")
    logger.info(f"  Evolved: mean={np.mean(evolved_sharpe):.3f}, std={np.std(evolved_sharpe):.3f}")
    logger.info(f"  Random:  mean={np.mean(random_sharpe):.3f}, std={np.std(random_sharpe):.3f}")

    return float(p_value), float(cohens_d)


def calculate_pareto_front_size(results: List[EvolutionResult]) -> int:
    """
    Calculate Pareto front size in final generation.

    Success Criterion: ≥5

    Args:
        results: List of EvolutionResult objects

    Returns:
        Number of strategies in Pareto front (rank 1)
    """
    if not results:
        return 0

    final_population = results[-1].population.strategies
    pareto_front = [s for s in final_population if hasattr(s, 'pareto_rank') and s.pareto_rank == 1]

    size = len(pareto_front)
    logger.info(f"Pareto front size: {size}")

    return size


def generate_validation_report(
    results: List[EvolutionResult],
    champion_rate: float,
    variance: float,
    p_value: float,
    cohens_d: float,
    pareto_size: int,
    output_file: str,
    args: argparse.Namespace
) -> None:
    """
    Generate validation report in Markdown format.

    Args:
        results: List of EvolutionResult objects
        champion_rate: Champion update rate
        variance: Rolling variance
        p_value: Statistical test p-value
        cohens_d: Cohen's d effect size
        pareto_size: Pareto front size
        output_file: Output filename
        args: Command-line arguments
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Evaluate success criteria
    criteria = {
        "Champion Update Rate ≥10%": (champion_rate >= 0.10, f"{champion_rate*100:.1f}%", "≥10%"),
        "Rolling Variance <0.5": (variance < 0.5, f"{variance:.4f}", "<0.5"),
        "P-value <0.05": (p_value < 0.05, f"{p_value:.4f}", "<0.05"),
        "Pareto Front Size ≥5": (pareto_size >= 5, str(pareto_size), "≥5")
    }

    all_passed = all(passed for passed, _, _ in criteria.values())

    # Generate report
    report = f"""# Population-Based Learning Validation Report

**Generated**: {timestamp}
**Configuration**: N={args.population_size}, Generations={args.generations}
**Status**: {'✅ **PASSED**' if all_passed else '❌ **FAILED**'}

---

## Executive Summary

This validation report evaluates the population-based learning system against production success criteria using a {args.generations}-generation test with population size N={args.population_size}.

{'✅ **All success criteria met. System ready for production.**' if all_passed else '⚠️ **Some success criteria not met. Further tuning recommended.**'}

---

## Success Criteria Results

"""

    for criterion, (passed, actual, threshold) in criteria.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        report += f"### {criterion}\n\n"
        report += f"- **Status**: {status}\n"
        report += f"- **Actual**: {actual}\n"
        report += f"- **Threshold**: {threshold}\n\n"

    report += """---

## Detailed Analysis

### Champion Update Rate

Champion update rate measures the percentage of generations where the global best strategy improved. This indicates continuous learning and adaptation.

"""
    report += f"- **Result**: {champion_rate*100:.1f}%\n"
    report += f"- **Updates**: {sum(1 for r in results if r.champion_updated)}/{len(results)} generations\n"
    report += f"- **Interpretation**: {'System demonstrates consistent improvement' if champion_rate >= 0.10 else 'Low update rate suggests premature convergence or insufficient diversity'}\n\n"

    report += """### Rolling Variance

Rolling variance of final generation Sharpe ratios measures population diversity. Lower values indicate convergence to similar strategies.

"""
    report += f"- **Result**: {variance:.4f}\n"
    report += f"- **Interpretation**: {'Healthy convergence with maintained diversity' if variance < 0.5 else 'High variance suggests insufficient convergence'}\n\n"

    report += """### Statistical Significance

T-test comparing final population against random baseline (initial generation) validates that evolution produces superior strategies.

"""
    report += f"- **P-value**: {p_value:.4f}\n"
    report += f"- **Cohen's d**: {cohens_d:.3f}\n"
    report += f"- **Effect Size**: {get_effect_size_interpretation(cohens_d)}\n"
    report += f"- **Interpretation**: {'Evolution significantly outperforms random baseline' if p_value < 0.05 else 'No significant improvement over random baseline'}\n\n"

    report += """### Pareto Front Size

Number of non-dominated strategies in the final generation. Larger fronts indicate successful multi-objective optimization.

"""
    report += f"- **Result**: {pareto_size} strategies\n"
    report += f"- **Interpretation**: {'Diverse set of Pareto-optimal solutions found' if pareto_size >= 5 else 'Limited diversity in Pareto front'}\n\n"

    report += """---

## Generation History

"""

    # Add generation summary table
    report += "| Gen | Diversity | Pareto Size | Champion Updated | Best Sharpe | Time (s) |\n"
    report += "|-----|-----------|-------------|------------------|-------------|----------|\n"

    for i, result in enumerate(results):
        best_sharpe = max(
            (s.metrics.sharpe_ratio for s in result.population.strategies if s.metrics and s.metrics.success),
            default=0.0
        )
        pareto = len([s for s in result.population.strategies if hasattr(s, 'pareto_rank') and s.pareto_rank == 1])
        updated = "✓" if result.champion_updated else ""

        report += f"| {i+1:2d}  | {result.diversity_score:.3f}     | {pareto:11d} | {updated:16s} | {best_sharpe:11.3f} | {result.total_time:8.2f} |\n"

    report += "\n---\n\n"

    # Add diversity trend analysis
    diversity_values = [r.diversity_score for r in results]
    avg_diversity = np.mean(diversity_values)
    min_diversity = np.min(diversity_values)
    max_diversity = np.max(diversity_values)

    report += f"""## Diversity Trend Analysis

- **Average Diversity**: {avg_diversity:.3f}
- **Range**: [{min_diversity:.3f}, {max_diversity:.3f}]
- **Trend**: {'Stable' if max_diversity - min_diversity < 0.3 else 'Variable'}

"""

    # Add timing analysis
    total_time = sum(r.total_time for r in results)
    avg_time = total_time / len(results)

    report += f"""---

## Performance Metrics

- **Total Runtime**: {total_time:.2f} seconds ({total_time/60:.2f} minutes)
- **Average Generation Time**: {avg_time:.2f} seconds
- **Total Generations**: {len(results)}

---

## Recommendations

"""

    if all_passed:
        report += """✅ **System Validated for Production**

All success criteria met. The population-based learning system demonstrates:
- Consistent champion improvement
- Healthy convergence with diversity preservation
- Statistically significant superiority over random baseline
- Diverse Pareto-optimal solution set

**Next Steps**:
1. Deploy to production environment
2. Monitor real-world performance
3. Consider scaling to larger populations if needed

"""
    else:
        report += "⚠️ **Tuning Recommended**\n\n"

        if champion_rate < 0.10:
            report += "- **Champion Update Rate**: Increase mutation rate or diversity mechanisms\n"

        if variance >= 0.5:
            report += "- **Rolling Variance**: Increase selection pressure or elite count\n"

        if p_value >= 0.05:
            report += "- **Statistical Significance**: Run longer (more generations) or increase population size\n"

        if pareto_size < 5:
            report += "- **Pareto Front Size**: Enhance diversity preservation or multi-objective selection\n"

        report += "\n**Next Steps**:\n"
        report += "1. Apply recommended tuning\n"
        report += "2. Re-run validation test\n"
        report += "3. Iterate until all criteria met\n\n"

    report += """---

## Appendix

### Configuration Details

"""
    report += f"- **Population Size**: {args.population_size}\n"
    report += f"- **Generations**: {args.generations}\n"
    report += f"- **Elite Count**: 2 (default)\n"
    report += f"- **Tournament Size**: 3 (default)\n"
    report += f"- **Checkpoint Directory**: {args.checkpoint_dir}\n\n"

    report += """### Success Criteria Source

All success criteria are derived from the system requirements document:
- Champion update rate: Measures continuous learning (R9.1)
- Rolling variance: Validates convergence quality (R6.2)
- P-value: Statistical validation of improvement (R9.2)
- Pareto front size: Multi-objective diversity (R6.1)

---

**End of Report**
"""

    # Write report to file
    with open(output_file, 'w') as f:
        f.write(report)

    logger.info(f"Validation report saved to: {output_file}")


def get_effect_size_interpretation(cohens_d: float) -> str:
    """
    Interpret Cohen's d effect size.

    Args:
        cohens_d: Cohen's d value

    Returns:
        Human-readable interpretation
    """
    abs_d = abs(cohens_d)

    if abs_d < 0.2:
        return "Negligible"
    elif abs_d < 0.5:
        return "Small"
    elif abs_d < 0.8:
        return "Medium"
    else:
        return "Large"


def main():
    """Main execution function."""
    args = parse_arguments()

    print("="*70)
    print("20-GENERATION VALIDATION TEST")
    print("Population-Based Learning System")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  Population Size: {args.population_size}")
    print(f"  Generations:     {args.generations}")
    print(f"  Output Report:   {args.output}")
    print()

    # Create checkpoint directory
    checkpoint_dir = Path(args.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # Initialize PopulationManager
    logger.info("Initializing PopulationManager...")
    manager = PopulationManager(
        population_size=args.population_size,
        elite_count=2,
        tournament_size=3
    )

    # Initialize population
    print("Initializing population...")
    manager.initialize_population()

    # Save initial checkpoint
    manager.save_checkpoint(str(checkpoint_dir / "generation_0.json"))

    # Run evolution
    results = []

    try:
        for gen in range(1, args.generations + 1):
            print(f"\n{'='*70}")
            print(f"GENERATION {gen}/{args.generations}")
            print(f"{'='*70}")

            result = manager.evolve_generation(gen)
            results.append(result)

            # Display progress
            best_sharpe = max(
                (s.metrics.sharpe_ratio for s in result.population.strategies if s.metrics and s.metrics.success),
                default=0.0
            )

            print(f"Diversity:        {result.diversity_score:.3f}")
            print(f"Best Sharpe:      {best_sharpe:.3f}")
            print(f"Champion Updated: {'Yes' if result.champion_updated else 'No'}")
            print(f"Time:             {result.total_time:.2f}s")

            # Save checkpoint
            manager.save_checkpoint(str(checkpoint_dir / f"generation_{gen}.json"))

    except KeyboardInterrupt:
        logger.warning("\nValidation interrupted by user")
        print("\n\n⚠️  Validation interrupted. Partial results will be analyzed.")

    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        print(f"\n\n❌ Validation failed: {e}")
        sys.exit(1)

    # Perform statistical analysis
    print(f"\n{'='*70}")
    print("STATISTICAL ANALYSIS")
    print(f"{'='*70}\n")

    champion_rate = calculate_champion_update_rate(results)
    variance = calculate_rolling_variance(results)
    p_value, cohens_d = perform_statistical_test(results)
    pareto_size = calculate_pareto_front_size(results)

    # Generate validation report
    print(f"\nGenerating validation report...")
    generate_validation_report(
        results=results,
        champion_rate=champion_rate,
        variance=variance,
        p_value=p_value,
        cohens_d=cohens_d,
        pareto_size=pareto_size,
        output_file=args.output,
        args=args
    )

    # Display summary
    print(f"\n{'='*70}")
    print("VALIDATION SUMMARY")
    print(f"{'='*70}\n")

    print(f"Champion Update Rate: {champion_rate*100:.1f}% {'✅' if champion_rate >= 0.10 else '❌'}")
    print(f"Rolling Variance:     {variance:.4f} {'✅' if variance < 0.5 else '❌'}")
    print(f"P-value:              {p_value:.4f} {'✅' if p_value < 0.05 else '❌'}")
    print(f"Pareto Front Size:    {pareto_size} {'✅' if pareto_size >= 5 else '❌'}")

    all_passed = (champion_rate >= 0.10 and variance < 0.5 and p_value < 0.05 and pareto_size >= 5)

    print(f"\n{'='*70}")
    if all_passed:
        print("✅ VALIDATION PASSED - System ready for production")
    else:
        print("❌ VALIDATION FAILED - Tuning recommended")
    print(f"{'='*70}\n")

    print(f"Report saved to: {args.output}")
    print(f"Checkpoints saved to: {checkpoint_dir}\n")

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
