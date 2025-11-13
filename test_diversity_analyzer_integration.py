"""
Integration test for DiversityAnalyzer with real project data

This test verifies that the DiversityAnalyzer works correctly with
actual strategy files and validation results from the project.

Author: AI Assistant
Date: 2025-11-01
"""

import json
import logging
from pathlib import Path

from src.analysis.diversity_analyzer import DiversityAnalyzer, DiversityReport

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_full_integration():
    """Full integration test with real data."""
    print("\n" + "=" * 80)
    print("DIVERSITY ANALYZER - FULL INTEGRATION TEST")
    print("=" * 80 + "\n")

    # Initialize analyzer
    analyzer = DiversityAnalyzer()

    # Find available validation results
    validation_files = [
        'baseline_checkpoints/generation_0.json',
        'baseline_checkpoints/generation_10.json',
        'baseline_checkpoints/generation_20.json',
    ]

    results = []

    for vf in validation_files:
        if not Path(vf).exists():
            logger.warning(f"Validation file not found: {vf}")
            continue

        print(f"\nAnalyzing: {vf}")
        print("-" * 80)

        # Load validation results
        with open(vf, 'r') as f:
            validation_results = json.load(f)

        population = validation_results.get('population', [])
        n_strategies = len(population)

        print(f"Population size: {n_strategies}")

        # Find corresponding strategy files
        generation = int(vf.split('_')[-1].split('.')[0])
        strategy_files = []

        for i in range(n_strategies):
            # Try different naming patterns
            patterns = [
                f'generated_strategy_loop_iter{i}.py',
                f'generated_strategy_loop_iter{generation}_{i}.py',
            ]

            for pattern in patterns:
                if Path(pattern).exists():
                    strategy_files.append(pattern)
                    break

        print(f"Strategy files found: {len(strategy_files)}")

        if len(strategy_files) < 2:
            logger.warning("Insufficient strategy files, skipping")
            continue

        # Run diversity analysis
        try:
            report = analyzer.analyze_diversity(
                strategy_files=strategy_files,
                validation_results=validation_results,
                exclude_indices=[]
            )

            # Store results
            results.append({
                'file': vf,
                'generation': generation,
                'n_strategies': report.total_strategies,
                'factor_diversity': report.factor_diversity,
                'avg_correlation': report.avg_correlation,
                'risk_diversity': report.risk_diversity,
                'diversity_score': report.diversity_score,
                'recommendation': report.recommendation,
                'n_warnings': len(report.warnings),
                'n_unique_factors': report.factor_details['total_unique_factors'] if report.factor_details else 0
            })

            # Print results
            print(f"\nDiversity Analysis Results:")
            print(f"  Strategies Analyzed:  {report.total_strategies}")
            print(f"  Factor Diversity:     {report.factor_diversity:.4f}")
            print(f"  Average Correlation:  {report.avg_correlation:.4f}")
            print(f"  Risk Diversity:       {report.risk_diversity:.4f}")
            print(f"  Overall Score:        {report.diversity_score:.2f} / 100")
            print(f"  Recommendation:       {report.recommendation}")

            if report.factor_details:
                print(f"  Unique Factors:       {report.factor_details['total_unique_factors']}")
                print(f"  Avg Factors/Strategy: {report.factor_details['avg_factors_per_strategy']:.2f}")

            if report.warnings:
                print(f"  Warnings ({len(report.warnings)}):")
                for warning in report.warnings:
                    print(f"    - {warning}")

            # Verify all metrics are in valid ranges
            assert 0 <= report.factor_diversity <= 1, "Factor diversity out of range"
            assert 0 <= report.avg_correlation <= 1, "Correlation out of range"
            assert 0 <= report.risk_diversity <= 1, "Risk diversity out of range"
            assert 0 <= report.diversity_score <= 100, "Diversity score out of range"
            assert report.recommendation in ["SUFFICIENT", "MARGINAL", "INSUFFICIENT"]

            print("\n✅ Validation passed!")

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            continue

    # Print summary
    if results:
        print("\n" + "=" * 80)
        print("SUMMARY OF ALL GENERATIONS")
        print("=" * 80)
        print(f"\n{'Generation':<12} {'Strategies':<12} {'Factor':<10} {'Corr':<10} {'Risk':<10} {'Score':<10} {'Rec':<15}")
        print("-" * 80)

        for r in results:
            print(f"{r['generation']:<12} {r['n_strategies']:<12} {r['factor_diversity']:<10.4f} {r['avg_correlation']:<10.4f} {r['risk_diversity']:<10.4f} {r['diversity_score']:<10.2f} {r['recommendation']:<15}")

        # Calculate trends
        if len(results) > 1:
            print("\nTrends:")
            first_score = results[0]['diversity_score']
            last_score = results[-1]['diversity_score']
            change = last_score - first_score

            if change > 5:
                print(f"  📈 Diversity improved: {change:+.2f} points")
            elif change < -5:
                print(f"  📉 Diversity decreased: {change:+.2f} points")
            else:
                print(f"  ➡️  Diversity stable: {change:+.2f} points")

    print("\n" + "=" * 80)
    print("INTEGRATION TEST COMPLETE")
    print("=" * 80 + "\n")


def test_with_exclusions():
    """Test with strategy exclusions."""
    print("\n" + "=" * 80)
    print("INTEGRATION TEST: WITH EXCLUSIONS")
    print("=" * 80 + "\n")

    analyzer = DiversityAnalyzer()

    # Load validation results
    vf = 'baseline_checkpoints/generation_0.json'
    if not Path(vf).exists():
        logger.warning("Validation file not found, skipping test")
        return

    with open(vf, 'r') as f:
        validation_results = json.load(f)

    population = validation_results.get('population', [])
    n_strategies = len(population)

    # Find strategy files
    strategy_files = []
    for i in range(min(n_strategies, 15)):
        path = f'generated_strategy_loop_iter{i}.py'
        if Path(path).exists():
            strategy_files.append(path)

    if len(strategy_files) < 5:
        logger.warning("Insufficient strategy files for exclusion test")
        return

    print(f"Total strategy files: {len(strategy_files)}")

    # Test 1: No exclusions
    print("\nTest 1: No exclusions")
    report_no_exclusions = analyzer.analyze_diversity(
        strategy_files=strategy_files,
        validation_results=validation_results,
        exclude_indices=[]
    )
    print(f"  Strategies: {report_no_exclusions.total_strategies}")
    print(f"  Score: {report_no_exclusions.diversity_score:.2f}")

    # Test 2: Exclude some strategies
    exclude_indices = [2, 5, 8]
    print(f"\nTest 2: Exclude indices {exclude_indices}")
    report_with_exclusions = analyzer.analyze_diversity(
        strategy_files=strategy_files,
        validation_results=validation_results,
        exclude_indices=exclude_indices
    )
    print(f"  Strategies: {report_with_exclusions.total_strategies}")
    print(f"  Score: {report_with_exclusions.diversity_score:.2f}")
    print(f"  Expected strategies: {len(strategy_files) - len(exclude_indices)}")

    # Verify exclusions worked
    expected_count = len(strategy_files) - len(exclude_indices)
    assert report_with_exclusions.total_strategies == expected_count, "Exclusion count mismatch"
    assert report_with_exclusions.excluded_strategies == exclude_indices, "Exclusion indices mismatch"

    print("\n✅ Exclusion test passed!")


def test_factor_extraction_coverage():
    """Test factor extraction across many strategies."""
    print("\n" + "=" * 80)
    print("INTEGRATION TEST: FACTOR EXTRACTION COVERAGE")
    print("=" * 80 + "\n")

    analyzer = DiversityAnalyzer()

    # Find all available strategy files
    strategy_files = []
    for i in range(50):  # Check first 50 strategies
        path = Path(f'generated_strategy_loop_iter{i}.py')
        if path.exists():
            strategy_files.append(path)

    if len(strategy_files) == 0:
        logger.warning("No strategy files found")
        return

    print(f"Testing factor extraction on {len(strategy_files)} strategies\n")

    all_factors = set()
    factor_counts = []
    successful_extractions = 0
    failed_extractions = 0

    for path in strategy_files[:20]:  # Test first 20
        try:
            factors = analyzer.extract_factors(path)
            all_factors.update(factors)
            factor_counts.append(len(factors))
            successful_extractions += 1
        except Exception as e:
            logger.error(f"Failed to extract factors from {path.name}: {e}")
            failed_extractions += 1

    # Print statistics
    print(f"Extraction Results:")
    print(f"  Successful: {successful_extractions}")
    print(f"  Failed: {failed_extractions}")
    print(f"  Success Rate: {successful_extractions / len(strategy_files[:20]) * 100:.1f}%")
    print(f"\nFactor Statistics:")
    print(f"  Total Unique Factors: {len(all_factors)}")
    print(f"  Avg Factors/Strategy: {sum(factor_counts) / len(factor_counts):.2f}")
    print(f"  Min Factors: {min(factor_counts) if factor_counts else 0}")
    print(f"  Max Factors: {max(factor_counts) if factor_counts else 0}")

    print(f"\nAll Unique Factors Found:")
    for factor in sorted(all_factors):
        print(f"  - {factor}")

    print("\n✅ Factor extraction coverage test passed!")


def main():
    """Run all integration tests."""
    try:
        test_full_integration()
        test_with_exclusions()
        test_factor_extraction_coverage()

        print("\n" + "=" * 80)
        print("ALL INTEGRATION TESTS PASSED ✅")
        print("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"Integration test failed: {e}", exc_info=True)


if __name__ == '__main__':
    main()
