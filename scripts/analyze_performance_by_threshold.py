#!/usr/bin/env python3
"""
Performance Threshold Comparison Analyzer

Analyzes how trading strategy performance varies across different liquidity thresholds.
Groups historical strategies by their liquidity threshold and performs statistical
comparisons to identify optimal threshold settings.

Task 2 of Liquidity Monitoring Enhancement System
"""

import json
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict
import statistics
from scipy import stats
import math


def group_strategies_by_threshold(
    history_file: str = 'iteration_history.json',
    compliance_file: str = 'liquidity_compliance.json'
) -> Dict[int, List[Dict]]:
    """
    Group strategies by liquidity threshold buckets.

    Args:
        history_file: Path to iteration history JSON file
        compliance_file: Path to liquidity compliance JSON file

    Returns:
        Dictionary mapping threshold values to lists of strategy records
    """
    print(f"Loading data from {history_file} and {compliance_file}...")

    # Load iteration history
    with open(history_file, 'r', encoding='utf-8') as f:
        history_data = json.load(f)

    # Extract iterations with metrics - handle both list and dict formats
    if isinstance(history_data, list):
        iterations = history_data
    elif isinstance(history_data, dict) and 'records' in history_data:
        iterations = history_data['records']
    else:
        raise ValueError(f"Unexpected history file format: expected list or dict with 'records', got {type(history_data)}")

    # Load liquidity compliance data
    with open(compliance_file, 'r', encoding='utf-8') as f:
        compliance_data = json.load(f)

    # Create mapping of iteration number to threshold
    iteration_to_threshold = {}
    for check in compliance_data['checks']:
        iteration_num = check['iteration']
        threshold = check.get('threshold_found')
        # Only include if threshold was found
        if threshold is not None:
            iteration_to_threshold[iteration_num] = threshold

    print(f"Found {len(iteration_to_threshold)} iterations with valid thresholds")

    # Group strategies by threshold buckets
    threshold_groups = defaultdict(list)

    for record in iterations:
        iteration_num = record['iteration_num']

        # Skip if no threshold found for this iteration
        if iteration_num not in iteration_to_threshold:
            continue

        threshold = iteration_to_threshold[iteration_num]

        # Add to appropriate bucket
        threshold_groups[threshold].append(record)

    # Convert to regular dict and sort
    result = dict(sorted(threshold_groups.items()))

    print(f"\nGrouping summary:")
    for threshold, strategies in result.items():
        threshold_mb = threshold / 1_000_000
        print(f"  {threshold_mb:.0f}M TWD: {len(strategies)} strategies")

    return result


def calculate_threshold_statistics(strategies: List[Dict]) -> Dict[str, float]:
    """
    Calculate aggregate statistics for a threshold group.

    Args:
        strategies: List of strategy records

    Returns:
        Dictionary containing statistical metrics
    """
    if not strategies:
        return {
            'count': 0,
            'avg_sharpe': None,
            'std_sharpe': None,
            'median_sharpe': None,
            'avg_cagr': None,
            'avg_max_dd': None,
            'success_rate': None
        }

    # Extract metrics, filtering out None values
    sharpe_ratios = [s['metrics'].get('sharpe_ratio') for s in strategies
                     if s.get('metrics') is not None and s['metrics'].get('sharpe_ratio') is not None]

    annual_returns = [s['metrics'].get('annual_return') for s in strategies
                      if s.get('metrics') is not None and s['metrics'].get('annual_return') is not None]

    max_drawdowns = [s['metrics'].get('max_drawdown') for s in strategies
                     if s.get('metrics') is not None and s['metrics'].get('max_drawdown') is not None]

    # Calculate statistics
    count = len(strategies)

    # Sharpe ratio statistics
    avg_sharpe = statistics.mean(sharpe_ratios) if sharpe_ratios else None
    std_sharpe = statistics.stdev(sharpe_ratios) if len(sharpe_ratios) > 1 else None
    median_sharpe = statistics.median(sharpe_ratios) if sharpe_ratios else None

    # Other metrics
    avg_cagr = statistics.mean(annual_returns) if annual_returns else None
    avg_max_dd = statistics.mean(max_drawdowns) if max_drawdowns else None

    # Success rate (Sharpe > 0.5)
    successful = sum(1 for sr in sharpe_ratios if sr > 0.5)
    success_rate = successful / len(sharpe_ratios) if sharpe_ratios else None

    return {
        'count': count,
        'avg_sharpe': avg_sharpe,
        'std_sharpe': std_sharpe,
        'median_sharpe': median_sharpe,
        'avg_cagr': avg_cagr,
        'avg_max_dd': avg_max_dd,
        'success_rate': success_rate
    }


def calculate_cohens_d(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size.

    Args:
        group1: First group of values
        group2: Second group of values

    Returns:
        Cohen's d effect size
    """
    if not group1 or not group2:
        return 0.0

    mean1 = statistics.mean(group1)
    mean2 = statistics.mean(group2)

    # Pooled standard deviation
    n1, n2 = len(group1), len(group2)

    if n1 <= 1 and n2 <= 1:
        return 0.0

    var1 = statistics.variance(group1) if n1 > 1 else 0.0
    var2 = statistics.variance(group2) if n2 > 1 else 0.0

    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

    if pooled_std == 0:
        return 0.0

    return (mean1 - mean2) / pooled_std


def compare_thresholds_significance(
    group1: List[Dict],
    group2: List[Dict],
    metric: str = 'sharpe_ratio'
) -> Dict[str, Any]:
    """
    Perform statistical significance test between two threshold groups.

    Args:
        group1: First group of strategies
        group2: Second group of strategies
        metric: Metric to compare (default: sharpe_ratio)

    Returns:
        Dictionary with t-statistic, p-value, significance flag, and effect size
    """
    # Extract metric values
    values1 = [s['metrics'].get(metric) for s in group1
               if s.get('metrics') is not None and s['metrics'].get(metric) is not None]

    values2 = [s['metrics'].get(metric) for s in group2
               if s.get('metrics') is not None and s['metrics'].get(metric) is not None]

    # Check if we have enough data
    if len(values1) < 2 or len(values2) < 2:
        return {
            't_statistic': None,
            'p_value': None,
            'significant': False,
            'effect_size': None,
            'note': 'Insufficient data for statistical test (need at least 2 samples per group)'
        }

    # Perform independent t-test
    t_stat, p_value = stats.ttest_ind(values1, values2)

    # Calculate Cohen's d
    effect_size = calculate_cohens_d(values1, values2)

    # Determine significance (p < 0.05)
    significant = p_value < 0.05

    return {
        't_statistic': t_stat,
        'p_value': p_value,
        'significant': significant,
        'effect_size': effect_size,
        'sample_sizes': f"n1={len(values1)}, n2={len(values2)}"
    }


def generate_performance_report(
    threshold_groups: Dict[int, List[Dict]],
    output_file: str = 'LIQUIDITY_PERFORMANCE_REPORT.md'
) -> None:
    """
    Generate comprehensive markdown report.

    Args:
        threshold_groups: Dictionary mapping thresholds to strategy lists
        output_file: Output markdown file path
    """
    print(f"\nGenerating report to {output_file}...")

    with open(output_file, 'w') as f:
        # Header
        f.write("# Liquidity Threshold Performance Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("**Analysis:** Comparison of trading strategy performance across different liquidity thresholds\n\n")

        # Summary statistics table
        f.write("## Summary Statistics by Threshold\n\n")
        f.write("| Threshold | Count | Avg Sharpe | Std Sharpe | Median Sharpe | Avg CAGR | Avg Max DD | Success Rate |\n")
        f.write("|-----------|-------|------------|------------|---------------|----------|------------|-------------|\n")

        stats_by_threshold = {}
        for threshold, strategies in threshold_groups.items():
            stats = calculate_threshold_statistics(strategies)
            stats_by_threshold[threshold] = stats

            threshold_mb = threshold / 1_000_000

            # Format values
            avg_sharpe = f"{stats['avg_sharpe']:.4f}" if stats['avg_sharpe'] is not None else "N/A"
            std_sharpe = f"{stats['std_sharpe']:.4f}" if stats['std_sharpe'] is not None else "N/A"
            median_sharpe = f"{stats['median_sharpe']:.4f}" if stats['median_sharpe'] is not None else "N/A"
            avg_cagr = f"{stats['avg_cagr']*100:.2f}%" if stats['avg_cagr'] is not None else "N/A"
            avg_max_dd = f"{stats['avg_max_dd']*100:.2f}%" if stats['avg_max_dd'] is not None else "N/A"
            success_rate = f"{stats['success_rate']*100:.2f}%" if stats['success_rate'] is not None else "N/A"

            f.write(f"| {threshold_mb:.0f}M TWD | {stats['count']} | {avg_sharpe} | {std_sharpe} | {median_sharpe} | {avg_cagr} | {avg_max_dd} | {success_rate} |\n")

        f.write("\n")

        # Statistical Significance Tests
        f.write("## Statistical Significance Tests\n\n")
        f.write("Pairwise comparisons of Sharpe ratios between threshold groups using independent t-tests.\n\n")

        threshold_list = sorted(threshold_groups.keys())

        # Perform pairwise comparisons
        comparisons_made = False
        for i in range(len(threshold_list)):
            for j in range(i + 1, len(threshold_list)):
                threshold1 = threshold_list[i]
                threshold2 = threshold_list[j]

                group1 = threshold_groups[threshold1]
                group2 = threshold_groups[threshold2]

                # Skip if either group has < 10 strategies
                if len(group1) < 10 or len(group2) < 10:
                    continue

                comparisons_made = True
                comparison = compare_thresholds_significance(group1, group2)

                threshold1_mb = threshold1 / 1_000_000
                threshold2_mb = threshold2 / 1_000_000

                f.write(f"### {threshold1_mb:.0f}M TWD vs {threshold2_mb:.0f}M TWD\n\n")

                if comparison.get('note'):
                    f.write(f"**Note:** {comparison['note']}\n\n")
                else:
                    f.write(f"- **Sample sizes:** {comparison['sample_sizes']}\n")
                    f.write(f"- **t-statistic:** {comparison['t_statistic']:.4f}\n")
                    f.write(f"- **p-value:** {comparison['p_value']:.4f}\n")
                    f.write(f"- **Significant (p < 0.05):** {'Yes' if comparison['significant'] else 'No'}\n")
                    f.write(f"- **Cohen's d (effect size):** {comparison['effect_size']:.4f}\n")

                    # Interpret effect size
                    abs_d = abs(comparison['effect_size'])
                    if abs_d < 0.2:
                        effect_interp = "negligible"
                    elif abs_d < 0.5:
                        effect_interp = "small"
                    elif abs_d < 0.8:
                        effect_interp = "medium"
                    else:
                        effect_interp = "large"

                    f.write(f"- **Effect size interpretation:** {effect_interp}\n")

                    # Winner
                    if comparison['significant']:
                        stats1 = stats_by_threshold[threshold1]
                        stats2 = stats_by_threshold[threshold2]
                        winner = threshold1_mb if stats1['avg_sharpe'] > stats2['avg_sharpe'] else threshold2_mb
                        f.write(f"- **Winner:** {winner:.0f}M TWD (statistically significant)\n")

                    f.write("\n")

        if not comparisons_made:
            f.write("*No pairwise comparisons performed. Requires at least 10 strategies per threshold group.*\n\n")

        # Recommendations
        f.write("## Recommendations\n\n")

        # Find best threshold by average Sharpe
        valid_thresholds = [(t, s) for t, s in stats_by_threshold.items()
                           if s['avg_sharpe'] is not None and s['count'] >= 5]

        if valid_thresholds:
            best_threshold, best_stats = max(valid_thresholds, key=lambda x: x[1]['avg_sharpe'])
            best_threshold_mb = best_threshold / 1_000_000

            f.write(f"### Optimal Threshold\n\n")
            f.write(f"Based on average Sharpe ratio, the **{best_threshold_mb:.0f}M TWD** threshold shows the best performance:\n\n")
            f.write(f"- **Average Sharpe Ratio:** {best_stats['avg_sharpe']:.4f}\n")
            f.write(f"- **Median Sharpe Ratio:** {best_stats['median_sharpe']:.4f}\n")
            f.write(f"- **Success Rate:** {best_stats['success_rate']*100:.2f}%\n")
            f.write(f"- **Sample Size:** {best_stats['count']} strategies\n\n")

        # Highlight if current threshold (150M) is not optimal
        current_threshold = 150_000_000
        if current_threshold not in threshold_groups or len(threshold_groups[current_threshold]) == 0:
            f.write("### Current Threshold Analysis\n\n")
            f.write(f"**Note:** The current minimum threshold of 150M TWD has **no historical data**. ")
            f.write(f"All {sum(len(g) for g in threshold_groups.values())} historical strategies used lower thresholds.\n\n")
            f.write("**Recommendation:** Consider reducing the minimum threshold to align with historical practice, ")
            f.write("or collect more data using the 150M threshold before making comparisons.\n\n")

        # Detailed statistics per threshold
        f.write("## Detailed Statistics\n\n")

        for threshold, strategies in threshold_groups.items():
            threshold_mb = threshold / 1_000_000
            stats = stats_by_threshold[threshold]

            f.write(f"### {threshold_mb:.0f}M TWD Threshold\n\n")
            f.write(f"**Sample Size:** {stats['count']} strategies\n\n")

            if stats['avg_sharpe'] is not None:
                f.write("**Performance Metrics:**\n")
                f.write(f"- Average Sharpe Ratio: {stats['avg_sharpe']:.4f}\n")
                std_sharpe_str = f"{stats['std_sharpe']:.4f}" if stats['std_sharpe'] is not None else "N/A"
                f.write(f"- Std Dev Sharpe Ratio: {std_sharpe_str}\n")
                f.write(f"- Median Sharpe Ratio: {stats['median_sharpe']:.4f}\n")
                f.write(f"- Average CAGR: {stats['avg_cagr']*100:.2f}%\n")
                f.write(f"- Average Max Drawdown: {stats['avg_max_dd']*100:.2f}%\n")
                f.write(f"- Success Rate (Sharpe > 0.5): {stats['success_rate']*100:.2f}%\n")
            else:
                f.write("*Insufficient data for statistics*\n")

            f.write("\n")

        # Methodology
        f.write("## Methodology\n\n")
        f.write("### Data Sources\n")
        f.write("- **Strategy Performance:** `iteration_history.json` (125 total iterations)\n")
        f.write("- **Liquidity Thresholds:** `liquidity_compliance.json` (extracted from strategy code)\n\n")
        f.write("### Statistical Tests\n")
        f.write("- **Test:** Independent two-sample t-test\n")
        f.write("- **Null Hypothesis:** No difference in mean Sharpe ratios between threshold groups\n")
        f.write("- **Significance Level:** α = 0.05\n")
        f.write("- **Effect Size:** Cohen's d (|d| < 0.2: negligible, 0.2-0.5: small, 0.5-0.8: medium, > 0.8: large)\n")
        f.write("- **Minimum Sample Size:** 10 strategies per group for pairwise comparisons\n\n")
        f.write("### Metrics\n")
        f.write("- **Sharpe Ratio:** Risk-adjusted return measure\n")
        f.write("- **CAGR:** Compound Annual Growth Rate\n")
        f.write("- **Max Drawdown:** Maximum peak-to-trough decline\n")
        f.write("- **Success Rate:** Percentage of strategies with Sharpe > 0.5\n\n")

    print(f"Report generated successfully: {output_file}")


def main():
    """Main execution function."""
    print("=" * 70)
    print("Liquidity Threshold Performance Analysis")
    print("=" * 70)
    print()

    # Step 1: Group strategies by threshold
    threshold_groups = group_strategies_by_threshold()

    # Step 2: Generate comprehensive report
    generate_performance_report(threshold_groups)

    # Step 3: Print summary to console
    print("\n" + "=" * 70)
    print("Analysis Complete")
    print("=" * 70)
    print("\nKey Findings:")

    # Calculate and display overall statistics
    all_stats = {}
    for threshold, strategies in threshold_groups.items():
        stats = calculate_threshold_statistics(strategies)
        all_stats[threshold] = stats

    # Find best performing threshold
    valid_thresholds = [(t, s) for t, s in all_stats.items()
                       if s['avg_sharpe'] is not None and s['count'] >= 5]

    if valid_thresholds:
        best_threshold, best_stats = max(valid_thresholds, key=lambda x: x[1]['avg_sharpe'])
        best_threshold_mb = best_threshold / 1_000_000

        print(f"\nBest Performing Threshold: {best_threshold_mb:.0f}M TWD")
        print(f"  - Average Sharpe: {best_stats['avg_sharpe']:.4f}")
        print(f"  - Success Rate: {best_stats['success_rate']*100:.2f}%")
        print(f"  - Sample Size: {best_stats['count']} strategies")

    print("\nFull report saved to: LIQUIDITY_PERFORMANCE_REPORT.md")
    print()


if __name__ == "__main__":
    main()
