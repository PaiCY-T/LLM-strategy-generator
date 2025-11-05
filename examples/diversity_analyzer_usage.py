"""
Example usage of DiversityAnalyzer module

This script demonstrates how to use the DiversityAnalyzer to assess
the diversity of a population of trading strategies.

Author: AI Assistant
Date: 2025-11-01
"""

import json
import logging
from pathlib import Path

from src.analysis.diversity_analyzer import DiversityAnalyzer, DiversityReport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_basic_usage():
    """Basic usage example."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 80 + "\n")

    # Initialize analyzer
    analyzer = DiversityAnalyzer()

    # Prepare strategy files
    strategy_files = [
        'generated_strategy_loop_iter0.py',
        'generated_strategy_loop_iter1.py',
        'generated_strategy_loop_iter2.py',
        'generated_strategy_loop_iter3.py',
        'generated_strategy_loop_iter4.py',
    ]

    # Load validation results
    with open('baseline_checkpoints/generation_0.json', 'r') as f:
        validation_results = json.load(f)

    # Run analysis
    report = analyzer.analyze_diversity(
        strategy_files=strategy_files,
        validation_results=validation_results,
        exclude_indices=[]
    )

    # Print results
    print(f"Total Strategies Analyzed: {report.total_strategies}")
    print(f"\nDiversity Metrics:")
    print(f"  Factor Diversity:     {report.factor_diversity:.4f}")
    print(f"  Average Correlation:  {report.avg_correlation:.4f}")
    print(f"  Risk Diversity:       {report.risk_diversity:.4f}")
    print(f"\nOverall Score: {report.diversity_score:.2f} / 100")
    print(f"Recommendation: {report.recommendation}")

    if report.warnings:
        print(f"\nWarnings:")
        for warning in report.warnings:
            print(f"  - {warning}")


def example_with_duplicate_exclusion():
    """Example with duplicate strategy exclusion."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Excluding Duplicate Strategies")
    print("=" * 80 + "\n")

    analyzer = DiversityAnalyzer()

    # Strategy files
    strategy_files = [
        'generated_strategy_loop_iter0.py',
        'generated_strategy_loop_iter1.py',
        'generated_strategy_loop_iter2.py',
        'generated_strategy_loop_iter3.py',
        'generated_strategy_loop_iter4.py',
        'generated_strategy_loop_iter5.py',
        'generated_strategy_loop_iter6.py',
        'generated_strategy_loop_iter7.py',
        'generated_strategy_loop_iter8.py',
        'generated_strategy_loop_iter9.py',
    ]

    # Load validation results
    with open('baseline_checkpoints/generation_0.json', 'r') as f:
        validation_results = json.load(f)

    # Assume we detected duplicates at indices 3 and 7
    duplicate_indices = [3, 7]

    print(f"Excluding duplicate strategies at indices: {duplicate_indices}\n")

    # Run analysis with exclusions
    report = analyzer.analyze_diversity(
        strategy_files=strategy_files,
        validation_results=validation_results,
        exclude_indices=duplicate_indices
    )

    print(f"Total Strategies (after exclusion): {report.total_strategies}")
    print(f"Excluded: {report.excluded_strategies}")
    print(f"\nDiversity Score: {report.diversity_score:.2f} / 100")
    print(f"Recommendation: {report.recommendation}")


def example_factor_analysis():
    """Example focusing on factor analysis."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Detailed Factor Analysis")
    print("=" * 80 + "\n")

    analyzer = DiversityAnalyzer()

    # Analyze individual strategies
    strategy_files = [
        Path('generated_strategy_loop_iter0.py'),
        Path('generated_strategy_loop_iter1.py'),
        Path('generated_strategy_loop_iter2.py'),
    ]

    print("Factor Analysis by Strategy:\n")

    for i, path in enumerate(strategy_files):
        if path.exists():
            factors = analyzer.extract_factors(path)
            print(f"Strategy {i}: {path.name}")
            print(f"  Number of factors: {len(factors)}")
            print(f"  Factors: {sorted(factors)}")
            print()


def example_interpretation_guide():
    """Guide for interpreting diversity metrics."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Interpreting Diversity Metrics")
    print("=" * 80 + "\n")

    print("How to interpret the diversity metrics:\n")

    print("1. FACTOR DIVERSITY (0-1, higher is better)")
    print("   - Measures how different the data factors used by strategies are")
    print("   - Based on Jaccard distance between factor sets")
    print("   - < 0.5: Low diversity (warning)")
    print("   - 0.5-0.7: Moderate diversity")
    print("   - > 0.7: High diversity\n")

    print("2. AVERAGE CORRELATION (0-1, lower is better)")
    print("   - Measures similarity of strategy returns")
    print("   - Uses Sharpe ratio as a proxy for return patterns")
    print("   - > 0.8: High correlation (warning)")
    print("   - 0.5-0.8: Moderate correlation")
    print("   - < 0.5: Low correlation (good diversity)\n")

    print("3. RISK DIVERSITY (0-1, higher is better)")
    print("   - Measures diversity of risk profiles")
    print("   - Based on coefficient of variation of max drawdowns")
    print("   - < 0.3: Low diversity (warning)")
    print("   - 0.3-0.5: Moderate diversity")
    print("   - > 0.5: High diversity\n")

    print("4. OVERALL DIVERSITY SCORE (0-100)")
    print("   - Weighted combination of the three metrics")
    print("   - Factor diversity: 50% weight (most important)")
    print("   - Low correlation: 30% weight")
    print("   - Risk diversity: 20% weight\n")

    print("5. RECOMMENDATION")
    print("   - SUFFICIENT (score >= 60): Population has good diversity")
    print("   - MARGINAL (40 <= score < 60): Diversity could be improved")
    print("   - INSUFFICIENT (score < 40): Poor diversity, action needed\n")


def example_integration_with_duplicate_detector():
    """Example integrating with DuplicateDetector."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Integration with DuplicateDetector")
    print("=" * 80 + "\n")

    try:
        from src.analysis.duplicate_detector import DuplicateDetector
    except ImportError:
        print("DuplicateDetector not available, skipping example")
        return

    # Initialize both analyzers
    duplicate_detector = DuplicateDetector()
    diversity_analyzer = DiversityAnalyzer()

    # Strategy files
    strategy_files = [
        'generated_strategy_loop_iter0.py',
        'generated_strategy_loop_iter1.py',
        'generated_strategy_loop_iter2.py',
        'generated_strategy_loop_iter3.py',
        'generated_strategy_loop_iter4.py',
    ]

    # Load validation results
    with open('baseline_checkpoints/generation_0.json', 'r') as f:
        validation_results = json.load(f)

    print("Step 1: Detect duplicates\n")

    # Detect duplicates
    duplicate_groups = duplicate_detector.find_duplicates(
        strategy_files=strategy_files,
        validation_results=validation_results
    )

    # Find indices to exclude (keep first of each duplicate group)
    exclude_indices = []
    for group in duplicate_groups:
        if len(group.member_indices) > 1:
            # Keep first, exclude rest
            exclude_indices.extend(group.member_indices[1:])

    print(f"Found {len(duplicate_groups)} duplicate groups")
    print(f"Excluding indices: {exclude_indices}\n")

    print("Step 2: Analyze diversity (excluding duplicates)\n")

    # Analyze diversity with exclusions
    report = diversity_analyzer.analyze_diversity(
        strategy_files=strategy_files,
        validation_results=validation_results,
        exclude_indices=exclude_indices
    )

    print(f"Diversity Score: {report.diversity_score:.2f} / 100")
    print(f"Recommendation: {report.recommendation}")


def main():
    """Run all examples."""
    print("\n")
    print("=" * 80)
    print("DIVERSITY ANALYZER - USAGE EXAMPLES")
    print("=" * 80)

    try:
        example_basic_usage()
        example_with_duplicate_exclusion()
        example_factor_analysis()
        example_interpretation_guide()
        example_integration_with_duplicate_detector()

        print("\n" + "=" * 80)
        print("ALL EXAMPLES COMPLETED")
        print("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)


if __name__ == '__main__':
    main()
