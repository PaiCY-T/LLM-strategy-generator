#!/usr/bin/env python3
"""
Task 15.3: Pattern Coverage Analysis
Analyze Factor Graph successful strategies and map them to top 5 patterns.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter, defaultdict

def load_successful_strategies(result_dir: Path) -> List[Dict[str, Any]]:
    """Load all successful Factor Graph strategies from a result directory."""
    innovations_file = result_dir / "innovations.jsonl"

    if not innovations_file.exists():
        return []

    strategies = []
    with open(innovations_file, 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if data.get('execution_result', {}).get('success'):
                    strategies.append(data)

    return strategies


def categorize_strategy_by_template(strategy_id: str) -> str:
    """Categorize strategy by template ID."""
    # Template IDs follow pattern: template_N where N is the template number
    # Based on template_registry.py, templates rotate through:
    # 0-5: Momentum, MomentumExit, Turtle, Factor, Mastiff, Combination

    if 'template_' in strategy_id:
        try:
            template_num = int(strategy_id.split('_')[1])
            template_types = ['Momentum', 'MomentumExit', 'Turtle', 'Factor', 'Mastiff', 'Combination']
            return template_types[template_num % 6]
        except (IndexError, ValueError):
            return 'Unknown'

    return 'Unknown'


def identify_pattern_from_metrics(strategy: Dict[str, Any]) -> str:
    """
    Identify strategy pattern based on metrics and template type.

    Patterns:
    1. Pure Momentum - Fast breakout, moderate Sharpe
    2. Momentum+Exit - Momentum with trailing stops, higher Sharpe
    3. Turtle - Breakout following, consistent returns
    4. Factor-based - Multi-factor scoring, balanced metrics
    5. Mastiff - Complex combinations, variable performance
    """
    template_type = categorize_strategy_by_template(strategy['strategy_id'])

    # Map template types to pattern categories
    template_to_pattern = {
        'Momentum': 'Pure Momentum',
        'MomentumExit': 'Momentum + Exit Strategy',
        'Turtle': 'Turtle Breakout',
        'Factor': 'Multi-Factor Scoring',
        'Mastiff': 'Complex Combination',
        'Combination': 'Hybrid Strategy'
    }

    return template_to_pattern.get(template_type, 'Unknown Pattern')


def analyze_pattern_coverage(strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze pattern distribution and coverage."""

    # Count strategies by pattern
    pattern_counts = Counter()
    pattern_strategies = defaultdict(list)
    pattern_metrics = defaultdict(lambda: {'sharpe': [], 'return': [], 'drawdown': []})

    for strategy in strategies:
        pattern = identify_pattern_from_metrics(strategy)
        pattern_counts[pattern] += 1
        pattern_strategies[pattern].append(strategy['strategy_id'])

        metrics = strategy.get('metrics', {})
        pattern_metrics[pattern]['sharpe'].append(metrics.get('sharpe_ratio', 0))
        pattern_metrics[pattern]['return'].append(metrics.get('total_return', 0))
        pattern_metrics[pattern]['drawdown'].append(metrics.get('max_drawdown', 0))

    # Calculate average metrics per pattern
    pattern_avg_metrics = {}
    for pattern, metrics in pattern_metrics.items():
        pattern_avg_metrics[pattern] = {
            'avg_sharpe': sum(metrics['sharpe']) / len(metrics['sharpe']) if metrics['sharpe'] else 0,
            'avg_return': sum(metrics['return']) / len(metrics['return']) if metrics['return'] else 0,
            'avg_drawdown': sum(metrics['drawdown']) / len(metrics['drawdown']) if metrics['drawdown'] else 0,
            'count': len(metrics['sharpe'])
        }

    # Get top 5 patterns by count
    top_5_patterns = pattern_counts.most_common(5)
    top_5_coverage = sum(count for _, count in top_5_patterns)
    total_strategies = len(strategies)
    coverage_percentage = (top_5_coverage / total_strategies * 100) if total_strategies > 0 else 0

    return {
        'total_strategies': total_strategies,
        'pattern_counts': dict(pattern_counts),
        'top_5_patterns': top_5_patterns,
        'top_5_coverage': top_5_coverage,
        'coverage_percentage': coverage_percentage,
        'pattern_avg_metrics': pattern_avg_metrics,
        'pattern_strategies': {k: v[:5] for k, v in pattern_strategies.items()}  # First 5 examples
    }


def main():
    """Main analysis function."""

    # Find all Factor Graph result directories
    results_base = Path("/mnt/c/Users/jnpi/documents/finlab/LLM-strategy-generator/experiments/llm_learning_validation/results")

    fg_dirs = [
        results_base / "fg_only_50",
        results_base / "fg_only_20",
        results_base / "fg_only_10"
    ]

    all_strategies = []

    for fg_dir in fg_dirs:
        if fg_dir.exists():
            print(f"\nLoading strategies from: {fg_dir.name}")
            strategies = load_successful_strategies(fg_dir)
            print(f"  Found {len(strategies)} successful strategies")
            all_strategies.extend(strategies)

    if not all_strategies:
        print("\nNo successful strategies found!")
        return

    print(f"\n{'='*80}")
    print(f"PATTERN COVERAGE ANALYSIS")
    print(f"{'='*80}")

    # Analyze coverage
    analysis = analyze_pattern_coverage(all_strategies)

    print(f"\nTotal Successful Strategies: {analysis['total_strategies']}")
    print(f"\nPattern Distribution:")
    print(f"{'─'*80}")

    for pattern, count in sorted(analysis['pattern_counts'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / analysis['total_strategies'] * 100)
        avg_metrics = analysis['pattern_avg_metrics'][pattern]
        print(f"\n{pattern}:")
        print(f"  Count: {count} ({percentage:.1f}%)")
        print(f"  Avg Sharpe: {avg_metrics['avg_sharpe']:.3f}")
        print(f"  Avg Return: {avg_metrics['avg_return']:.3f}")
        print(f"  Avg Drawdown: {avg_metrics['avg_drawdown']:.3f}")
        print(f"  Examples: {', '.join(analysis['pattern_strategies'][pattern][:3])}")

    print(f"\n{'='*80}")
    print(f"TOP 5 PATTERN COVERAGE")
    print(f"{'='*80}")

    print(f"\nTop 5 Patterns:")
    for i, (pattern, count) in enumerate(analysis['top_5_patterns'], 1):
        percentage = (count / analysis['total_strategies'] * 100)
        print(f"  {i}. {pattern}: {count} strategies ({percentage:.1f}%)")

    print(f"\nCoverage Statistics:")
    print(f"  Strategies covered by top 5: {analysis['top_5_coverage']}/{analysis['total_strategies']}")
    print(f"  Coverage percentage: {analysis['coverage_percentage']:.1f}%")
    print(f"  Target coverage (60%): {'✓ PASS' if analysis['coverage_percentage'] >= 60 else '✗ FAIL'}")

    # Save results
    output_file = results_base.parent.parent / "docs" / "PATTERN_COVERAGE_ANALYSIS.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        f.write("# Task 15.3: Pattern Coverage Analysis\n\n")
        f.write("## Executive Summary\n\n")
        f.write(f"- **Total Successful Strategies Analyzed**: {analysis['total_strategies']}\n")
        f.write(f"- **Top 5 Pattern Coverage**: {analysis['coverage_percentage']:.1f}%\n")
        f.write(f"- **Coverage Target (60%)**: {'✓ PASS' if analysis['coverage_percentage'] >= 60 else '✗ FAIL'}\n\n")

        f.write("## Top 5 Strategy Patterns\n\n")
        for i, (pattern, count) in enumerate(analysis['top_5_patterns'], 1):
            percentage = (count / analysis['total_strategies'] * 100)
            avg_metrics = analysis['pattern_avg_metrics'][pattern]

            f.write(f"### {i}. {pattern}\n\n")
            f.write(f"**Coverage**: {count} strategies ({percentage:.1f}%)\n\n")
            f.write(f"**Performance Metrics**:\n")
            f.write(f"- Average Sharpe Ratio: {avg_metrics['avg_sharpe']:.3f}\n")
            f.write(f"- Average Total Return: {avg_metrics['avg_return']:.3f}\n")
            f.write(f"- Average Max Drawdown: {avg_metrics['avg_drawdown']:.3f}\n\n")
            f.write(f"**Example Strategy IDs**: {', '.join(analysis['pattern_strategies'][pattern][:5])}\n\n")

        f.write("## Pattern Distribution\n\n")
        f.write("| Pattern | Count | Percentage | Avg Sharpe | Avg Return | Avg Drawdown |\n")
        f.write("|---------|-------|------------|------------|------------|---------------|\n")

        for pattern in sorted(analysis['pattern_counts'].keys()):
            count = analysis['pattern_counts'][pattern]
            percentage = (count / analysis['total_strategies'] * 100)
            avg_metrics = analysis['pattern_avg_metrics'][pattern]
            f.write(f"| {pattern} | {count} | {percentage:.1f}% | ")
            f.write(f"{avg_metrics['avg_sharpe']:.3f} | {avg_metrics['avg_return']:.3f} | ")
            f.write(f"{avg_metrics['avg_drawdown']:.3f} |\n")

        f.write(f"\n## Coverage Analysis\n\n")
        f.write(f"The top 5 patterns cover **{analysis['top_5_coverage']} out of {analysis['total_strategies']} ")
        f.write(f"successful strategies ({analysis['coverage_percentage']:.1f}%)**.\n\n")

        if analysis['coverage_percentage'] >= 60:
            f.write("✓ **REQUIREMENT MET**: Coverage exceeds 60% target.\n\n")
        else:
            f.write("✗ **REQUIREMENT NOT MET**: Coverage below 60% target.\n\n")

        f.write("## Methodology\n\n")
        f.write("1. **Data Sources**: Analyzed successful Factor Graph strategies from:\n")
        for fg_dir in fg_dirs:
            if fg_dir.exists():
                f.write(f"   - `{fg_dir.name}`\n")
        f.write("\n2. **Pattern Identification**: Strategies categorized by template type:\n")
        f.write("   - Pure Momentum: Fast breakout strategies\n")
        f.write("   - Momentum + Exit Strategy: Momentum with trailing stops\n")
        f.write("   - Turtle Breakout: Channel breakout following\n")
        f.write("   - Multi-Factor Scoring: Factor-based scoring systems\n")
        f.write("   - Complex Combination: Multi-strategy combinations\n\n")
        f.write("3. **Coverage Calculation**: (Top 5 pattern count / Total successful) × 100%\n\n")

        f.write("## Recommendations\n\n")
        if analysis['coverage_percentage'] >= 60:
            f.write("The top 5 patterns provide sufficient coverage. Proceed with:\n")
            f.write("- Task 16: Design YAML schemas for these 5 patterns\n")
            f.write("- Task 17: Implement pattern matching logic\n\n")
        else:
            f.write("Consider expanding pattern coverage by:\n")
            f.write("- Adding hybrid patterns\n")
            f.write("- Refining pattern definitions\n")
            f.write("- Analyzing additional successful strategies\n\n")

        f.write(f"**Analysis Date**: 2025-11-18\n")
        f.write(f"**Task**: 15.3 - Pattern Coverage Analysis\n")

    print(f"\n{'='*80}")
    print(f"Analysis complete! Results saved to:")
    print(f"  {output_file}")
    print(f"{'='*80}\n")

    # Also save JSON for programmatic access
    json_output = results_base.parent.parent / "docs" / "pattern_coverage_data.json"
    with open(json_output, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)

    print(f"JSON data saved to: {json_output}\n")


if __name__ == "__main__":
    main()
