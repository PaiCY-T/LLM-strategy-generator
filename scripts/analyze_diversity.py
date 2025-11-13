#!/usr/bin/env python3
"""
Diversity Analysis Script (Task 3.2)
====================================

Analyzes strategy diversity using factor diversity, return correlation, and risk profile analysis.
This script is part of the validation-framework-critical-fixes specification.

Requirements:
    - REQ-3 (Acceptance Criteria 5): Diversity analysis reporting

Features:
    - Loads validation results and optionally duplicate reports
    - Filters to validated strategies only
    - Excludes duplicate strategies if specified
    - Generates diversity metrics and overall score
    - Creates visualizations (correlation heatmap, factor usage chart)
    - Outputs JSON and Markdown reports

Usage:
    # Without duplicate exclusion
    python3 scripts/analyze_diversity.py \\
        --validation-results phase2_validated_results_20251101_060315.json \\
        --output diversity_report.md

    # With duplicate exclusion
    python3 scripts/analyze_diversity.py \\
        --validation-results phase2_validated_results_20251101_060315.json \\
        --duplicate-report duplicate_report.json \\
        --output diversity_report.md

Author: AI Assistant
Date: 2025-11-01
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# Try to import visualization libraries
VISUALIZATION_AVAILABLE = True
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError:
    VISUALIZATION_AVAILABLE = False

# Import diversity analyzer
try:
    from src.analysis.diversity_analyzer import DiversityAnalyzer, DiversityReport
except ImportError:
    # Try relative import
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.analysis.diversity_analyzer import DiversityAnalyzer, DiversityReport

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Analyze strategy diversity using factor, correlation, and risk metrics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Without duplicate exclusion
  python3 scripts/analyze_diversity.py \\
      --validation-results phase2_validated_results_20251101_060315.json \\
      --output diversity_report.md

  # With duplicate exclusion
  python3 scripts/analyze_diversity.py \\
      --validation-results phase2_validated_results_20251101_060315.json \\
      --duplicate-report duplicate_report.json \\
      --output diversity_report.md
        """
    )

    parser.add_argument(
        '--validation-results',
        type=str,
        required=True,
        help='Path to validation results JSON file'
    )

    parser.add_argument(
        '--duplicate-report',
        type=str,
        required=False,
        help='Path to duplicate report JSON (to exclude duplicates)'
    )

    parser.add_argument(
        '--strategy-dir',
        type=str,
        default='.',
        help='Directory containing strategy files (default: current directory)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='diversity_report.md',
        help='Output path for Markdown report (default: diversity_report.md)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    return parser.parse_args()


def load_json_file(file_path: Path, description: str) -> Dict:
    """Load and parse a JSON file.

    Args:
        file_path: Path to JSON file
        description: Description for error messages

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not valid JSON
    """
    if not file_path.exists():
        raise FileNotFoundError(f"{description} not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded {description} from {file_path}")
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {description} ({file_path}): {e}")


def load_validation_results(file_path: Path) -> Dict:
    """Load validation results JSON file.

    Args:
        file_path: Path to validation results file

    Returns:
        Validation results dict
    """
    return load_json_file(file_path, "validation results")


def load_duplicate_report(file_path: Optional[Path]) -> Optional[Dict]:
    """Load duplicate report JSON file.

    Args:
        file_path: Path to duplicate report file (optional)

    Returns:
        Duplicate report dict or None if not provided
    """
    if file_path is None:
        return None

    return load_json_file(file_path, "duplicate report")


def find_strategy_files(strategy_dir: Path) -> List[Path]:
    """Find all strategy files in the directory.

    Args:
        strategy_dir: Directory to search

    Returns:
        Sorted list of strategy file paths
    """
    pattern = "generated_strategy_*.py"
    strategy_files = sorted(strategy_dir.glob(pattern))

    if not strategy_files:
        logger.warning(f"No strategy files found matching {pattern} in {strategy_dir}")

    logger.info(f"Found {len(strategy_files)} strategy files")
    return strategy_files


def filter_validated_strategies(
    validation_results: Dict,
    strategy_files: List[Path]
) -> Tuple[List[Path], List[int]]:
    """Filter to only validated strategies.

    Args:
        validation_results: Validation results dict
        strategy_files: All strategy files

    Returns:
        Tuple of (validated_strategy_files, validated_indices)
    """
    # Extract validation info
    strategies_validation = validation_results.get('strategies_validation', [])

    # Get indices of validated strategies
    validated_indices = [
        s['strategy_index'] for s in strategies_validation
        if s.get('validation_passed', False)
    ]

    logger.info(f"Found {len(validated_indices)} validated strategies: {validated_indices}")

    # Filter strategy files to only validated ones
    validated_files = [
        f for f in strategy_files
        if extract_strategy_index(f) in validated_indices
    ]

    return validated_files, validated_indices


def extract_strategy_index(file_path: Path) -> int:
    """Extract strategy index from filename.

    Args:
        file_path: Strategy file path

    Returns:
        Strategy index

    Raises:
        ValueError: If index cannot be extracted
    """
    filename = file_path.name
    try:
        if 'iter' in filename:
            index_str = filename.split('iter')[1].split('.')[0]
            return int(index_str)
        else:
            raise ValueError(f"Cannot extract index from {filename}")
    except (IndexError, ValueError) as e:
        raise ValueError(f"Cannot parse strategy index from {filename}: {e}")


def get_excluded_indices(duplicate_report: Optional[Dict]) -> List[int]:
    """Get list of strategy indices to exclude based on duplicate report.

    Args:
        duplicate_report: Duplicate report dict or None

    Returns:
        List of strategy indices to exclude
    """
    if duplicate_report is None:
        return []

    excluded = []
    duplicate_groups = duplicate_report.get('duplicate_groups', [])

    for group in duplicate_groups:
        # Exclude all strategies in the group except the first one
        strategies = group.get('strategies', [])
        if len(strategies) > 1:
            # Get indices from StrategyInfo objects
            indices = []
            for s in strategies:
                if isinstance(s, dict):
                    indices.append(s.get('index'))
                else:
                    # Handle case where strategies are just indices
                    indices.append(s)

            # Keep first, exclude rest
            excluded.extend(indices[1:])

    if excluded:
        logger.info(f"Excluding {len(excluded)} duplicate strategies: {excluded}")

    return excluded


def calculate_correlation_matrix(
    validation_results: Dict,
    strategy_indices: List[int]
) -> Optional[np.ndarray]:
    """Calculate correlation matrix between strategies.

    Args:
        validation_results: Validation results dict
        strategy_indices: Indices of strategies to include

    Returns:
        Correlation matrix or None if insufficient data
    """
    # Extract Sharpe ratios
    strategies_validation = validation_results.get('strategies_validation', [])
    sharpes = []

    for idx in strategy_indices:
        for s in strategies_validation:
            if s['strategy_index'] == idx:
                sharpes.append(s['sharpe_ratio'])
                break

    if len(sharpes) < 2:
        return None

    # Since we only have single values, create pseudo-correlation matrix
    # based on pairwise differences (normalized)
    n = len(sharpes)
    corr_matrix = np.ones((n, n))

    sharpe_array = np.array(sharpes)
    max_diff = np.max(sharpes) - np.min(sharpes)

    if max_diff > 0:
        for i in range(n):
            for j in range(i + 1, n):
                # Correlation proxy: 1 - normalized_difference
                diff = abs(sharpes[i] - sharpes[j])
                pseudo_corr = 1.0 - (diff / max_diff)
                corr_matrix[i, j] = pseudo_corr
                corr_matrix[j, i] = pseudo_corr

    return corr_matrix


def calculate_factor_usage(
    strategy_files: List[Path],
    analyzer: DiversityAnalyzer
) -> Dict[str, int]:
    """Calculate factor usage frequency across strategies.

    Args:
        strategy_files: List of strategy files
        analyzer: DiversityAnalyzer instance

    Returns:
        Dict mapping factor names to usage count
    """
    factor_usage = {}

    for file_path in strategy_files:
        try:
            factors = analyzer.extract_factors(file_path)
            for factor in factors:
                factor_usage[factor] = factor_usage.get(factor, 0) + 1
        except Exception as e:
            logger.warning(f"Failed to extract factors from {file_path}: {e}")

    return factor_usage


def generate_correlation_heatmap(
    corr_matrix: np.ndarray,
    strategy_indices: List[int],
    output_path: Path
) -> bool:
    """Generate correlation heatmap visualization.

    Args:
        corr_matrix: Correlation matrix
        strategy_indices: Strategy indices for labels
        output_path: Output file path

    Returns:
        True if successful, False otherwise
    """
    if not VISUALIZATION_AVAILABLE:
        logger.warning("Matplotlib/seaborn not available, skipping heatmap")
        return False

    try:
        fig, ax = plt.subplots(figsize=(10, 8))

        # Create heatmap
        sns.heatmap(
            corr_matrix,
            annot=True,
            fmt='.2f',
            cmap='RdYlBu_r',
            vmin=0,
            vmax=1,
            xticklabels=strategy_indices,
            yticklabels=strategy_indices,
            ax=ax,
            cbar_kws={'label': 'Correlation'}
        )

        ax.set_title('Strategy Correlation Matrix', fontsize=14, fontweight='bold')
        ax.set_xlabel('Strategy Index', fontsize=12)
        ax.set_ylabel('Strategy Index', fontsize=12)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        logger.info(f"Saved correlation heatmap to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to generate correlation heatmap: {e}")
        return False


def generate_factor_usage_chart(
    factor_usage: Dict[str, int],
    output_path: Path,
    top_n: int = 15
) -> bool:
    """Generate factor usage bar chart.

    Args:
        factor_usage: Dict mapping factor names to usage count
        output_path: Output file path
        top_n: Number of top factors to show (default: 15)

    Returns:
        True if successful, False otherwise
    """
    if not VISUALIZATION_AVAILABLE:
        logger.warning("Matplotlib not available, skipping factor usage chart")
        return False

    if not factor_usage:
        logger.warning("No factor usage data available")
        return False

    try:
        # Get top N factors
        sorted_factors = sorted(factor_usage.items(), key=lambda x: x[1], reverse=True)
        top_factors = sorted_factors[:top_n]

        if not top_factors:
            return False

        factors, counts = zip(*top_factors)

        # Create horizontal bar chart
        fig, ax = plt.subplots(figsize=(10, max(6, len(top_factors) * 0.4)))

        y_pos = np.arange(len(factors))
        ax.barh(y_pos, counts, color='steelblue', alpha=0.8)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(factors)
        ax.invert_yaxis()  # Labels read top-to-bottom
        ax.set_xlabel('Number of Strategies', fontsize=12)
        ax.set_ylabel('Factor Name', fontsize=12)
        ax.set_title(f'Top {len(top_factors)} Most Used Factors', fontsize=14, fontweight='bold')

        # Add value labels on bars
        for i, count in enumerate(counts):
            ax.text(count, i, f' {count}', va='center', fontsize=10)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        logger.info(f"Saved factor usage chart to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to generate factor usage chart: {e}")
        return False


def generate_json_report(
    report: DiversityReport,
    factor_usage: Dict[str, int],
    output_path: Path
) -> None:
    """Generate JSON report.

    Args:
        report: DiversityReport instance
        factor_usage: Factor usage frequency dict
        output_path: Output file path
    """
    json_data = {
        "total_strategies": report.total_strategies,
        "excluded_strategies": report.excluded_strategies,
        "metrics": {
            "factor_diversity": report.factor_diversity,
            "avg_correlation": report.avg_correlation,
            "risk_diversity": report.risk_diversity
        },
        "diversity_score": report.diversity_score,
        "recommendation": report.recommendation,
        "warnings": report.warnings,
        "factors": {
            "unique_count": report.factor_details.get('total_unique_factors', 0) if report.factor_details else 0,
            "avg_per_strategy": report.factor_details.get('avg_factors_per_strategy', 0.0) if report.factor_details else 0.0,
            "usage_distribution": factor_usage
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)

    logger.info(f"Saved JSON report to {output_path}")


def generate_markdown_report(
    report: DiversityReport,
    factor_usage: Dict[str, int],
    output_path: Path,
    heatmap_path: Optional[Path],
    chart_path: Optional[Path],
    validation_file: Path
) -> None:
    """Generate Markdown report.

    Args:
        report: DiversityReport instance
        factor_usage: Factor usage frequency dict
        output_path: Output file path
        heatmap_path: Path to correlation heatmap image (or None)
        chart_path: Path to factor usage chart image (or None)
        validation_file: Path to validation results file
    """
    lines = []

    # Header
    lines.append("# Strategy Diversity Analysis Report")
    lines.append("")
    lines.append(f"**Validation Results**: `{validation_file.name}`")
    lines.append(f"**Total Strategies Analyzed**: {report.total_strategies}")
    if report.excluded_strategies:
        lines.append(f"**Excluded Strategies**: {len(report.excluded_strategies)} (indices: {report.excluded_strategies})")
    lines.append("")

    # Summary Section
    lines.append("## Summary")
    lines.append("")
    lines.append(f"**Diversity Score**: {report.diversity_score:.1f}/100")
    lines.append(f"**Recommendation**: **{report.recommendation}**")
    lines.append("")

    # Recommendation explanation
    if report.recommendation == "SUFFICIENT":
        lines.append("The strategy portfolio demonstrates sufficient diversity across factors, returns, and risk profiles.")
    elif report.recommendation == "MARGINAL":
        lines.append("The strategy portfolio shows marginal diversity. Consider adding more diverse strategies to improve portfolio robustness.")
    else:  # INSUFFICIENT
        lines.append("The strategy portfolio lacks sufficient diversity. This may lead to correlated losses and reduced portfolio effectiveness.")
    lines.append("")

    # Key Metrics Breakdown
    lines.append("## Key Metrics")
    lines.append("")
    lines.append("| Metric | Value | Interpretation |")
    lines.append("|--------|-------|----------------|")

    # Factor diversity
    factor_status = "Good" if report.factor_diversity >= 0.5 else "Low"
    lines.append(f"| Factor Diversity | {report.factor_diversity:.3f} | {factor_status} (>0.5 recommended) |")

    # Average correlation
    corr_status = "Good" if report.avg_correlation <= 0.8 else "High"
    lines.append(f"| Average Correlation | {report.avg_correlation:.3f} | {corr_status} (<0.8 recommended) |")

    # Risk diversity
    risk_status = "Good" if report.risk_diversity >= 0.3 else "Low"
    lines.append(f"| Risk Diversity | {report.risk_diversity:.3f} | {risk_status} (>0.3 recommended) |")

    lines.append("")

    # Factor Analysis Section
    lines.append("## Factor Analysis")
    lines.append("")

    if report.factor_details:
        total_unique = report.factor_details.get('total_unique_factors', 0)
        avg_per_strategy = report.factor_details.get('avg_factors_per_strategy', 0.0)

        lines.append(f"**Total Unique Factors**: {total_unique}")
        lines.append(f"**Average Factors per Strategy**: {avg_per_strategy:.1f}")
        lines.append("")

        # Top 10 most used factors
        if factor_usage:
            sorted_factors = sorted(factor_usage.items(), key=lambda x: x[1], reverse=True)
            top_10 = sorted_factors[:10]

            lines.append("### Top 10 Most Used Factors")
            lines.append("")
            lines.append("| Rank | Factor | Usage Count |")
            lines.append("|------|--------|-------------|")
            for rank, (factor, count) in enumerate(top_10, 1):
                lines.append(f"| {rank} | `{factor}` | {count} |")
            lines.append("")

    # Correlation Analysis Section
    lines.append("## Correlation Analysis")
    lines.append("")
    lines.append(f"**Average Pairwise Correlation**: {report.avg_correlation:.3f}")
    lines.append("")

    if report.avg_correlation > 0.8:
        lines.append("High correlation detected between strategies. This suggests:")
        lines.append("- Strategies may be using similar factors or logic")
        lines.append("- Portfolio may be susceptible to correlated losses")
        lines.append("- Consider adding more diverse trading approaches")
    elif report.avg_correlation < 0.3:
        lines.append("Low correlation between strategies, which is excellent for diversification.")
    else:
        lines.append("Moderate correlation between strategies, providing reasonable diversification.")
    lines.append("")

    # Risk Analysis Section
    lines.append("## Risk Analysis")
    lines.append("")
    lines.append(f"**Risk Diversity (CV of Max Drawdowns)**: {report.risk_diversity:.3f}")
    lines.append("")

    if report.risk_diversity < 0.3:
        lines.append("Low risk diversity suggests strategies have similar risk profiles.")
        lines.append("Consider adding strategies with different risk characteristics.")
    else:
        lines.append("Good risk diversity across strategies, providing varied risk-return profiles.")
    lines.append("")

    # Warnings Section
    if report.warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in report.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    # Visualizations Section
    if heatmap_path or chart_path:
        lines.append("## Visualizations")
        lines.append("")

        if heatmap_path and heatmap_path.exists():
            lines.append("### Correlation Heatmap")
            lines.append("")
            lines.append(f"![Correlation Heatmap]({heatmap_path.name})")
            lines.append("")

        if chart_path and chart_path.exists():
            lines.append("### Factor Usage Distribution")
            lines.append("")
            lines.append(f"![Factor Usage Chart]({chart_path.name})")
            lines.append("")

    # Recommendations Section
    lines.append("## Recommendations")
    lines.append("")

    if report.recommendation == "INSUFFICIENT":
        lines.append("1. **Urgent**: Add more diverse strategies to the portfolio")
        lines.append("2. Consider strategies using different factor combinations")
        lines.append("3. Explore different trading timeframes or market regimes")
        lines.append("4. Review and remove highly correlated strategies")
    elif report.recommendation == "MARGINAL":
        lines.append("1. Consider adding 1-2 more diverse strategies")
        lines.append("2. Review strategies with high correlation for potential consolidation")
        lines.append("3. Explore underutilized factors from the factor library")
    else:  # SUFFICIENT
        lines.append("1. Monitor diversity metrics as portfolio evolves")
        lines.append("2. Continue to validate new strategies against diversity criteria")
        lines.append("3. Periodically review for emerging correlations")

    lines.append("")

    # Next Steps Section
    lines.append("## Next Steps")
    lines.append("")
    lines.append("- [ ] Review individual strategy performance metrics")
    lines.append("- [ ] Conduct portfolio-level backtesting")
    lines.append("- [ ] Monitor correlation changes over time")
    lines.append("- [ ] Update diversity analysis after adding new strategies")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*Report generated by `scripts/analyze_diversity.py` (Task 3.2)*")
    lines.append("")

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    logger.info(f"Saved Markdown report to {output_path}")


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Parse arguments
    args = parse_arguments()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("="*60)
    logger.info("Strategy Diversity Analysis (Task 3.2)")
    logger.info("="*60)

    try:
        # Convert paths
        validation_path = Path(args.validation_results)
        duplicate_path = Path(args.duplicate_report) if args.duplicate_report else None
        strategy_dir = Path(args.strategy_dir)
        output_path = Path(args.output)

        # Validate input paths
        if not strategy_dir.exists():
            logger.error(f"Strategy directory does not exist: {strategy_dir}")
            return 1

        # Load input files
        logger.info("Loading input files...")
        validation_results = load_validation_results(validation_path)
        duplicate_report = load_duplicate_report(duplicate_path)

        # Find strategy files
        logger.info("Finding strategy files...")
        all_strategy_files = find_strategy_files(strategy_dir)

        if not all_strategy_files:
            logger.error("No strategy files found")
            return 1

        # Filter to validated strategies
        logger.info("Filtering to validated strategies...")
        validated_files, validated_indices = filter_validated_strategies(
            validation_results, all_strategy_files
        )

        if not validated_files:
            logger.error("No validated strategies found")
            return 1

        # Get excluded indices from duplicate report
        excluded_indices = get_excluded_indices(duplicate_report)

        # Filter out excluded strategies
        included_files = []
        included_indices = []

        for file_path in validated_files:
            idx = extract_strategy_index(file_path)
            if idx not in excluded_indices:
                included_files.append(file_path)
                included_indices.append(idx)

        logger.info(f"Analyzing {len(included_files)} strategies after exclusions")

        if len(included_files) < 2:
            logger.error(f"Insufficient strategies for diversity analysis: {len(included_files)} < 2")
            return 1

        # Initialize analyzer
        logger.info("Initializing diversity analyzer...")
        analyzer = DiversityAnalyzer()

        # Run diversity analysis
        logger.info("Running diversity analysis...")
        report = analyzer.analyze_diversity(
            strategy_files=included_files,
            validation_results=validation_results,
            exclude_indices=excluded_indices
        )

        # Calculate additional metrics
        logger.info("Calculating additional metrics...")

        # Correlation matrix
        corr_matrix = calculate_correlation_matrix(validation_results, included_indices)

        # Factor usage
        factor_usage = calculate_factor_usage(included_files, analyzer)

        # Generate outputs
        logger.info("Generating reports and visualizations...")

        # Output paths
        json_output = output_path.with_suffix('.json')
        heatmap_output = output_path.parent / f"{output_path.stem}_correlation_heatmap.png"
        chart_output = output_path.parent / f"{output_path.stem}_factor_usage.png"

        # Generate JSON report
        generate_json_report(report, factor_usage, json_output)

        # Generate visualizations
        heatmap_generated = False
        chart_generated = False

        if VISUALIZATION_AVAILABLE:
            if corr_matrix is not None and len(included_indices) >= 2:
                heatmap_generated = generate_correlation_heatmap(
                    corr_matrix, included_indices, heatmap_output
                )

            if factor_usage:
                chart_generated = generate_factor_usage_chart(
                    factor_usage, chart_output, top_n=15
                )
        else:
            logger.warning("Visualization libraries not available (matplotlib/seaborn). Skipping charts.")

        # Generate Markdown report
        generate_markdown_report(
            report=report,
            factor_usage=factor_usage,
            output_path=output_path,
            heatmap_path=heatmap_output if heatmap_generated else None,
            chart_path=chart_output if chart_generated else None,
            validation_file=validation_path
        )

        # Print summary
        logger.info("="*60)
        logger.info("Analysis Complete!")
        logger.info("="*60)
        logger.info(f"Total Strategies Analyzed: {report.total_strategies}")
        logger.info(f"Excluded Strategies: {len(report.excluded_strategies)}")
        logger.info(f"Diversity Score: {report.diversity_score:.1f}/100")
        logger.info(f"Recommendation: {report.recommendation}")
        logger.info("")
        logger.info("Output Files:")
        logger.info(f"  - Markdown Report: {output_path}")
        logger.info(f"  - JSON Report: {json_output}")
        if heatmap_generated:
            logger.info(f"  - Correlation Heatmap: {heatmap_output}")
        if chart_generated:
            logger.info(f"  - Factor Usage Chart: {chart_output}")
        logger.info("="*60)

        # Print warnings if any
        if report.warnings:
            logger.warning("Warnings:")
            for warning in report.warnings:
                logger.warning(f"  - {warning}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
