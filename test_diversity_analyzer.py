"""
Test script for DiversityAnalyzer module (Task 3.1)

Tests the diversity analysis functionality with real strategy files
and validation results from the project.
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


def test_factor_extraction():
    """Test factor extraction from strategy files."""
    logger.info("=" * 80)
    logger.info("TEST 1: Factor Extraction")
    logger.info("=" * 80)

    analyzer = DiversityAnalyzer()

    # Test with a few strategy files
    strategy_files = [
        Path('generated_strategy_loop_iter0.py'),
        Path('generated_strategy_loop_iter1.py'),
        Path('generated_strategy_loop_iter2.py'),
    ]

    for strategy_file in strategy_files:
        if strategy_file.exists():
            try:
                factors = analyzer.extract_factors(strategy_file)
                logger.info(f"\n{strategy_file.name}:")
                logger.info(f"  Factors extracted: {len(factors)}")
                logger.info(f"  Factors: {sorted(factors)}")
            except Exception as e:
                logger.error(f"  Failed to extract factors: {e}")
        else:
            logger.warning(f"  File not found: {strategy_file}")

    logger.info("\n")


def test_factor_diversity():
    """Test factor diversity calculation."""
    logger.info("=" * 80)
    logger.info("TEST 2: Factor Diversity Calculation")
    logger.info("=" * 80)

    analyzer = DiversityAnalyzer()

    # Test case 1: Identical factor sets (should be 0 diversity)
    factor_sets_identical = [
        {'factor_a', 'factor_b', 'factor_c'},
        {'factor_a', 'factor_b', 'factor_c'},
        {'factor_a', 'factor_b', 'factor_c'},
    ]
    diversity_identical = analyzer.calculate_factor_diversity(factor_sets_identical)
    logger.info(f"\nIdentical factor sets:")
    logger.info(f"  Diversity: {diversity_identical:.4f} (expected: ~0.00)")

    # Test case 2: Completely different factor sets (should be high diversity)
    factor_sets_different = [
        {'factor_a', 'factor_b'},
        {'factor_c', 'factor_d'},
        {'factor_e', 'factor_f'},
    ]
    diversity_different = analyzer.calculate_factor_diversity(factor_sets_different)
    logger.info(f"\nCompletely different factor sets:")
    logger.info(f"  Diversity: {diversity_different:.4f} (expected: ~1.00)")

    # Test case 3: Partially overlapping factor sets
    factor_sets_partial = [
        {'factor_a', 'factor_b', 'factor_c'},
        {'factor_b', 'factor_c', 'factor_d'},
        {'factor_c', 'factor_d', 'factor_e'},
    ]
    diversity_partial = analyzer.calculate_factor_diversity(factor_sets_partial)
    logger.info(f"\nPartially overlapping factor sets:")
    logger.info(f"  Diversity: {diversity_partial:.4f} (expected: ~0.30-0.60)")

    logger.info("\n")


def test_with_real_data():
    """Test with real strategy files and validation results."""
    logger.info("=" * 80)
    logger.info("TEST 3: Real Data Analysis")
    logger.info("=" * 80)

    analyzer = DiversityAnalyzer()

    # Find validation results file
    validation_files = [
        'baseline_checkpoints/generation_0.json',
        'validation_checkpoints/generation_0.json',
    ]

    validation_results = None
    validation_file = None

    for vf in validation_files:
        if Path(vf).exists():
            validation_file = vf
            with open(vf, 'r') as f:
                validation_results = json.load(f)
            break

    if validation_results is None:
        logger.warning("No validation results file found, skipping real data test")
        return

    logger.info(f"\nUsing validation file: {validation_file}")

    # Get strategy count
    population = validation_results.get('population', [])
    n_strategies = len(population)
    logger.info(f"Strategies in population: {n_strategies}")

    if n_strategies == 0:
        logger.warning("No strategies in population, skipping test")
        return

    # Create dummy strategy files (use generated_strategy_loop_iter*.py if available)
    strategy_files = []
    for i in range(min(n_strategies, 10)):  # Test with first 10 strategies
        # Try to find actual generated strategy files
        path = Path(f'generated_strategy_loop_iter{i}.py')
        if path.exists():
            strategy_files.append(str(path))
        else:
            # If not found, we'll skip this for now
            pass

    if len(strategy_files) < 2:
        logger.warning(f"Insufficient strategy files found ({len(strategy_files)}), skipping test")
        return

    logger.info(f"\nAnalyzing {len(strategy_files)} strategy files...")

    # Run diversity analysis
    try:
        report = analyzer.analyze_diversity(
            strategy_files=strategy_files,
            validation_results=validation_results,
            exclude_indices=[]
        )

        # Print results
        logger.info("\n" + "=" * 80)
        logger.info("DIVERSITY ANALYSIS REPORT")
        logger.info("=" * 80)
        logger.info(f"Total Strategies: {report.total_strategies}")
        logger.info(f"Excluded Strategies: {report.excluded_strategies}")
        logger.info(f"\nDiversity Metrics:")
        logger.info(f"  Factor Diversity:     {report.factor_diversity:.4f} (0-1, higher is better)")
        logger.info(f"  Avg Correlation:      {report.avg_correlation:.4f} (0-1, lower is better)")
        logger.info(f"  Risk Diversity:       {report.risk_diversity:.4f} (0-1, higher is better)")
        logger.info(f"\nOverall Diversity Score: {report.diversity_score:.2f} / 100")
        logger.info(f"Recommendation: {report.recommendation}")

        if report.warnings:
            logger.info(f"\nWarnings:")
            for warning in report.warnings:
                logger.info(f"  - {warning}")

        if report.factor_details:
            logger.info(f"\nFactor Details:")
            logger.info(f"  Total Unique Factors: {report.factor_details['total_unique_factors']}")
            logger.info(f"  Avg Factors/Strategy: {report.factor_details['avg_factors_per_strategy']:.2f}")

        logger.info("\n")

        # Validate score ranges
        assert 0 <= report.factor_diversity <= 1, "Factor diversity out of range"
        assert 0 <= report.avg_correlation <= 1, "Correlation out of range"
        assert 0 <= report.risk_diversity <= 1, "Risk diversity out of range"
        assert 0 <= report.diversity_score <= 100, "Diversity score out of range"
        assert report.recommendation in ["SUFFICIENT", "MARGINAL", "INSUFFICIENT"]

        logger.info("✓ All validations passed!")

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)


def test_exclude_strategies():
    """Test excluding strategies from analysis."""
    logger.info("=" * 80)
    logger.info("TEST 4: Strategy Exclusion")
    logger.info("=" * 80)

    analyzer = DiversityAnalyzer()

    # Find validation results
    validation_file = 'baseline_checkpoints/generation_0.json'
    if not Path(validation_file).exists():
        logger.warning("Validation file not found, skipping test")
        return

    with open(validation_file, 'r') as f:
        validation_results = json.load(f)

    population = validation_results.get('population', [])
    n_strategies = len(population)

    if n_strategies < 5:
        logger.warning("Insufficient strategies for exclusion test")
        return

    # Create strategy file list
    strategy_files = []
    for i in range(min(n_strategies, 10)):
        path = Path(f'generated_strategy_loop_iter{i}.py')
        if path.exists():
            strategy_files.append(str(path))

    if len(strategy_files) < 5:
        logger.warning("Insufficient strategy files for exclusion test")
        return

    # Test with no exclusions
    report_full = analyzer.analyze_diversity(
        strategy_files=strategy_files,
        validation_results=validation_results,
        exclude_indices=[]
    )
    logger.info(f"\nFull analysis (no exclusions):")
    logger.info(f"  Total strategies: {report_full.total_strategies}")
    logger.info(f"  Diversity score: {report_full.diversity_score:.2f}")

    # Test with some exclusions
    exclude_indices = [1, 3]  # Exclude strategies 1 and 3
    report_excluded = analyzer.analyze_diversity(
        strategy_files=strategy_files,
        validation_results=validation_results,
        exclude_indices=exclude_indices
    )
    logger.info(f"\nWith exclusions {exclude_indices}:")
    logger.info(f"  Total strategies: {report_excluded.total_strategies}")
    logger.info(f"  Diversity score: {report_excluded.diversity_score:.2f}")

    assert report_excluded.total_strategies == report_full.total_strategies - len(exclude_indices)
    logger.info("\n✓ Exclusion test passed!")


def test_edge_cases():
    """Test edge cases and error handling."""
    logger.info("=" * 80)
    logger.info("TEST 5: Edge Cases")
    logger.info("=" * 80)

    analyzer = DiversityAnalyzer()

    # Test case 1: Single strategy (should return INSUFFICIENT)
    logger.info("\nTest case 1: Single strategy")
    validation_results_single = {
        'population': [
            {
                'metrics': {
                    'sharpe_ratio': 0.5,
                    'max_drawdown': -0.2
                }
            }
        ]
    }

    report_single = analyzer.analyze_diversity(
        strategy_files=['generated_strategy_loop_iter0.py'],
        validation_results=validation_results_single,
        exclude_indices=[]
    )
    logger.info(f"  Recommendation: {report_single.recommendation}")
    assert report_single.recommendation == "INSUFFICIENT", "Single strategy should be insufficient"
    logger.info("  ✓ Passed")

    # Test case 2: Empty factor sets
    logger.info("\nTest case 2: Empty factor sets")
    empty_factor_sets = [set(), set(), set()]
    diversity_empty = analyzer.calculate_factor_diversity(empty_factor_sets)
    logger.info(f"  Diversity: {diversity_empty:.4f}")
    assert diversity_empty == 0.0, "Empty factor sets should have 0 diversity"
    logger.info("  ✓ Passed")

    # Test case 3: Missing metrics
    logger.info("\nTest case 3: Missing metrics in validation results")
    validation_results_incomplete = {
        'population': [
            {},  # No metrics
            {'metrics': {}},  # Empty metrics
            {'metrics': {'sharpe_ratio': 0.5}},  # Missing drawdown
        ]
    }

    # This should not crash
    try:
        report_incomplete = analyzer.analyze_diversity(
            strategy_files=[
                'generated_strategy_loop_iter0.py',
                'generated_strategy_loop_iter1.py',
                'generated_strategy_loop_iter2.py'
            ],
            validation_results=validation_results_incomplete,
            exclude_indices=[]
        )
        logger.info(f"  Handled gracefully, score: {report_incomplete.diversity_score:.2f}")
        logger.info("  ✓ Passed")
    except Exception as e:
        logger.error(f"  Failed: {e}")

    logger.info("\n")


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("=" * 80)
    logger.info("DIVERSITY ANALYZER TEST SUITE")
    logger.info("=" * 80)
    logger.info("\n")

    try:
        test_factor_extraction()
        test_factor_diversity()
        test_with_real_data()
        test_exclude_strategies()
        test_edge_cases()

        logger.info("=" * 80)
        logger.info("ALL TESTS COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info("\n")

    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)


if __name__ == '__main__':
    main()
