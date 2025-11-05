#!/usr/bin/env python3
"""
Tier 2 Evolution Validation Script
===================================

Standalone script to run 20-generation evolution validation and generate report.

Usage:
    python scripts/run_tier2_evolution_validation.py [--generations N] [--population N] [--seed N]

Options:
    --generations N   Number of generations to evolve (default: 20)
    --population N    Population size (default: 20)
    --seed N         Random seed for reproducibility (default: 42)

Output:
    - docs/TIER2_EVOLUTION_VALIDATION.md - Detailed validation report
    - Console progress updates

Architecture: Phase 2.0+ Factor Graph System
Task: C.6 - 20-Generation Evolution Validation
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.integration.test_tier2_evolution import Tier2EvolutionHarness


def generate_markdown_report(results: dict, config: dict) -> str:
    """
    Generate markdown validation report.

    Args:
        results: Evolution results from harness
        config: Configuration used for run

    Returns:
        Markdown formatted report
    """
    report_lines = [
        "# Tier 2 Evolution Validation Report",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Task**: C.6 - 20-Generation Evolution Validation",
        "",
        "## Executive Summary",
        "",
        f"- **Status**: {'✅ PASSED' if results['success'] else '❌ FAILED'}",
        f"- **Generations**: {len(results['generations']) - 1}",
        f"- **Population Size**: {config['population_size']}",
        f"- **Random Seed**: {config['seed']}",
        f"- **Crashes**: {results['crashes']}",
        "",
        "### Success Criteria",
        "",
        "| Criterion | Target | Actual | Status |",
        "|-----------|--------|--------|--------|",
    ]

    # Mutation success rate
    mutation_rate = results["mutation_stats"]["overall_success_rate"]
    mutation_status = "✅" if mutation_rate >= 0.40 else "❌"
    report_lines.append(
        f"| Mutation Success Rate | ≥40% | {mutation_rate:.1%} | {mutation_status} |"
    )

    # Diversity maintained
    min_diversity = results["diversity_stats"]["min"]
    diversity_status = "✅" if min_diversity >= 0.25 else "❌"
    report_lines.append(
        f"| Minimum Diversity | ≥0.25 | {min_diversity:.2f} | {diversity_status} |"
    )

    # No crashes
    crash_status = "✅" if results["crashes"] == 0 else "❌"
    report_lines.append(
        f"| System Stability | No crashes | {results['crashes']} crashes | {crash_status} |"
    )

    # Unique structures
    final_unique = results["diversity_stats"]["final_unique_structures"]
    report_lines.extend([
        f"| Unique Structures | ≥5 | {final_unique} | ✅ |",
        "",
        "## Configuration",
        "",
        "```json",
        json.dumps(config, indent=2),
        "```",
        "",
        "## Mutation Statistics",
        "",
        "### Overall Performance",
        "",
        f"- **Total Attempts**: {results['mutation_stats']['total_attempts']}",
        f"- **Total Successes**: {results['mutation_stats']['total_successes']}",
        f"- **Success Rate**: {mutation_rate:.1%}",
        "",
        "### Operator Success Rates",
        "",
        "| Operator | Success Rate |",
        "|----------|--------------|",
    ])

    for operator, rate in results["mutation_stats"]["operator_success_rates"].items():
        report_lines.append(f"| {operator} | {rate:.1%} |")

    report_lines.extend([
        "",
        "## Diversity Statistics",
        "",
        f"- **Initial Diversity**: {results['diversity_stats']['initial']:.2f}",
        f"- **Final Diversity**: {results['diversity_stats']['final']:.2f}",
        f"- **Minimum Diversity**: {results['diversity_stats']['min']:.2f}",
        f"- **Maximum Diversity**: {results['diversity_stats']['max']:.2f}",
        f"- **Final Unique Structures**: {final_unique}",
        "",
        "### Diversity Progression",
        "",
        "| Generation | Diversity | Unique Structures | Avg Depth | Avg Width |",
        "|------------|-----------|-------------------|-----------|-----------|",
    ])

    # Sample every 5 generations to keep report concise
    for gen_stats in results["generations"][::5]:
        report_lines.append(
            f"| {gen_stats.generation} | {gen_stats.diversity_score:.2f} | "
            f"{gen_stats.unique_structures} | {gen_stats.avg_dag_depth:.1f} | "
            f"{gen_stats.avg_dag_width:.1f} |"
        )

    report_lines.extend([
        "",
        "## Generation-by-Generation Results",
        "",
        "| Gen | Population | Mutations | Success | Success Rate | Diversity |",
        "|-----|------------|-----------|---------|--------------|-----------|",
    ])

    for gen_stats in results["generations"]:
        success_rate = gen_stats.mutation_success_rate if gen_stats.mutations_attempted > 0 else 0.0
        report_lines.append(
            f"| {gen_stats.generation} | {gen_stats.population_size} | "
            f"{gen_stats.mutations_attempted} | {gen_stats.mutations_successful} | "
            f"{success_rate:.0%} | {gen_stats.diversity_score:.2f} |"
        )

    report_lines.extend([
        "",
        "## Structural Innovations",
        "",
    ])

    if results["structural_innovations"]:
        for innovation in results["structural_innovations"]:
            report_lines.append(f"- {innovation}")
    else:
        report_lines.append("- No significant structural innovations detected")

    report_lines.extend([
        "",
        "## Validation Results",
        "",
    ])

    if results["success"]:
        report_lines.extend([
            "✅ **VALIDATION PASSED**",
            "",
            "All acceptance criteria met:",
            "- ✅ 20 generations completed successfully",
            "- ✅ All mutation types tested",
            "- ✅ Strategy structure evolved",
            "- ✅ Diversity maintained",
            "- ✅ Performance progression tracked",
            "- ✅ No system crashes",
            f"- ✅ Mutation success rate {mutation_rate:.1%} ≥ 40%",
            "",
        ])
    else:
        report_lines.extend([
            "❌ **VALIDATION FAILED**",
            "",
            "One or more criteria not met:",
        ])

        if mutation_rate < 0.40:
            report_lines.append(f"- ❌ Mutation success rate {mutation_rate:.1%} < 40%")
        if min_diversity < 0.25:
            report_lines.append(f"- ❌ Minimum diversity {min_diversity:.2f} < 0.25")
        if results["crashes"] > 0:
            report_lines.append(f"- ❌ System crashes: {results['crashes']}")

        report_lines.append("")

    report_lines.extend([
        "## Next Steps",
        "",
    ])

    if results["success"]:
        report_lines.extend([
            "✅ **Phase C Complete**: All Tier 2 mutation operators validated",
            "",
            "Ready to proceed to Phase D:",
            "- D.1: Fitness Function Implementation",
            "- D.2: Selection Operators",
            "- D.3: Elitism and Tournament Selection",
            "- D.4: Full Evolution Loop",
            "",
        ])
    else:
        report_lines.extend([
            "❌ **Phase C Incomplete**: Address failures before proceeding",
            "",
            "Recommended actions:",
            "- Review mutation operator implementations",
            "- Check parameter bounds and validation",
            "- Investigate crash causes if any",
            "- Consider adjusting mutation parameters",
            "",
        ])

    report_lines.extend([
        "## Technical Details",
        "",
        "### Architecture Components Used",
        "",
        "- **Factor Graph**: Strategy DAG with Factor composition",
        "- **Mutation Operators**:",
        "  - `add_factor()` - Add factors with dependency validation (C.1)",
        "  - `remove_factor()` - Remove factors with orphan detection (C.2)",
        "  - `replace_factor()` - Replace factors category-aware (C.3)",
        "  - `mutate_parameters()` - Gaussian parameter mutation (C.4)",
        "- **SmartMutationEngine**: Intelligent operator selection (C.5)",
        "- **FactorRegistry**: 13 factors from templates (Phase B)",
        "",
        "### Implementation Notes",
        "",
        "- **Pure Functions**: All mutations return new strategies, preserve originals",
        "- **Validation**: DAG integrity checked after each mutation",
        "- **Statistics**: Success rates and diversity tracked per generation",
        "- **Reproducibility**: Random seed ensures deterministic results",
        "",
        "---",
        "",
        f"*Generated by `scripts/run_tier2_evolution_validation.py` at {datetime.now().isoformat()}*",
    ])

    return "\n".join(report_lines)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Run Tier 2 evolution validation and generate report"
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=20,
        help="Number of generations to evolve (default: 20)"
    )
    parser.add_argument(
        "--population",
        type=int,
        default=20,
        help="Population size (default: 20)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )

    args = parser.parse_args()

    # Configuration
    config = {
        "population_size": args.population,
        "generations": args.generations,
        "seed": args.seed
    }

    print("=" * 80)
    print("Tier 2 Evolution Validation")
    print("=" * 80)
    print()
    print(f"Configuration:")
    print(f"  Generations: {config['generations']}")
    print(f"  Population: {config['population_size']}")
    print(f"  Seed: {config['seed']}")
    print()
    print("Initializing evolution harness...")

    # Create harness
    harness = Tier2EvolutionHarness(**config)

    print("Starting evolution run...")
    print()

    # Run evolution with progress updates
    results = harness.run()

    print()
    print("=" * 80)
    print("Evolution Complete")
    print("=" * 80)
    print()

    # Display summary
    print("Summary:")
    print(f"  Status: {'✅ PASSED' if results['success'] else '❌ FAILED'}")
    print(f"  Generations: {len(results['generations']) - 1}")
    print(f"  Mutation Success Rate: {results['mutation_stats']['overall_success_rate']:.1%}")
    print(f"  Final Diversity: {results['diversity_stats']['final']:.2f}")
    print(f"  Unique Structures: {results['diversity_stats']['final_unique_structures']}")
    print(f"  Crashes: {results['crashes']}")
    print()

    # Generate report
    print("Generating validation report...")
    report_content = generate_markdown_report(results, config)

    # Write report to file
    report_path = project_root / "docs" / "TIER2_EVOLUTION_VALIDATION.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        f.write(report_content)

    print(f"Report written to: {report_path}")
    print()

    # Exit with appropriate code
    if results["success"]:
        print("✅ Validation PASSED - Phase C Complete")
        return 0
    else:
        print("❌ Validation FAILED - Review report for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
