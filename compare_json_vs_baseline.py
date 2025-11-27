"""Compare JSON mode test results vs Full Code baseline results.

This script analyzes and compares the performance of:
1. JSON Mode (template_mode=True, use_json_mode=True)
2. Full Code Baseline (template_mode=False, use_json_mode=False)

Metrics compared:
- Success rate (LEVEL_3 classification)
- Average Sharpe ratio
- Average total return
- Average max drawdown
- Execution time per iteration
- Champion quality
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

def load_history(filepath: str) -> List[Dict[str, Any]]:
    """Load iteration history from JSONL file."""
    if not os.path.exists(filepath):
        print(f"[ERROR] History file not found: {filepath}")
        return []

    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            records.append(json.loads(line))
    return records

def analyze_results(records: List[Dict[str, Any]], mode_name: str) -> Dict[str, Any]:
    """Analyze test results and compute statistics."""
    if not records:
        return {
            'mode': mode_name,
            'total_iterations': 0,
            'error': 'No records found'
        }

    # Count classifications
    level_counts = {
        'LEVEL_0': 0,
        'LEVEL_1': 0,
        'LEVEL_2': 0,
        'LEVEL_3': 0
    }

    sharpe_ratios = []
    total_returns = []
    max_drawdowns = []

    for record in records:
        level = record.get('classification_level', 'LEVEL_0')
        level_counts[level] = level_counts.get(level, 0) + 1

        metrics = record.get('metrics', {})
        if metrics.get('sharpe_ratio') is not None:
            sharpe_ratios.append(metrics['sharpe_ratio'])
        if metrics.get('total_return') is not None:
            total_returns.append(metrics['total_return'])
        if metrics.get('max_drawdown') is not None:
            max_drawdowns.append(metrics['max_drawdown'])

    # Compute statistics
    total = len(records)
    success_count = level_counts['LEVEL_3']
    success_rate = (success_count / total * 100) if total > 0 else 0

    avg_sharpe = sum(sharpe_ratios) / len(sharpe_ratios) if sharpe_ratios else 0
    avg_return = sum(total_returns) / len(total_returns) if total_returns else 0
    avg_drawdown = sum(max_drawdowns) / len(max_drawdowns) if max_drawdowns else 0

    # Find champion (best Sharpe ratio)
    champion = None
    best_sharpe = -float('inf')
    for record in records:
        metrics = record.get('metrics', {})
        sharpe = metrics.get('sharpe_ratio', -float('inf'))
        if sharpe > best_sharpe:
            best_sharpe = sharpe
            champion = {
                'iteration': record.get('iteration_num'),
                'sharpe_ratio': sharpe,
                'total_return': metrics.get('total_return'),
                'max_drawdown': metrics.get('max_drawdown')
            }

    return {
        'mode': mode_name,
        'total_iterations': total,
        'level_counts': level_counts,
        'success_rate': success_rate,
        'avg_sharpe': avg_sharpe,
        'avg_return': avg_return,
        'avg_drawdown': avg_drawdown,
        'champion': champion
    }

def print_comparison(json_results: Dict[str, Any], baseline_results: Dict[str, Any]):
    """Print comparison report."""
    print("=" * 80)
    print("Phase 2.3: JSON Mode vs Full Code Baseline Comparison")
    print("=" * 80)
    print()

    # Overall comparison
    print("Overall Results:")
    print("-" * 80)
    print(f"{'Metric':<30} {'JSON Mode':<20} {'Full Code':<20} {'Difference'}")
    print("-" * 80)

    # Success rate
    json_success = json_results.get('success_rate', 0)
    baseline_success = baseline_results.get('success_rate', 0)
    success_diff = json_success - baseline_success
    print(f"{'Success Rate (LEVEL_3)':<30} {json_success:>6.1f}% {baseline_success:>14.1f}% {success_diff:>13.1f}%")

    # Average Sharpe ratio
    json_sharpe = json_results.get('avg_sharpe', 0)
    baseline_sharpe = baseline_results.get('avg_sharpe', 0)
    sharpe_diff = json_sharpe - baseline_sharpe
    print(f"{'Avg Sharpe Ratio':<30} {json_sharpe:>8.4f} {baseline_sharpe:>16.4f} {sharpe_diff:>15.4f}")

    # Average total return
    json_return = json_results.get('avg_return', 0)
    baseline_return = baseline_results.get('avg_return', 0)
    return_diff = json_return - baseline_return
    print(f"{'Avg Total Return':<30} {json_return:>7.2%} {baseline_return:>15.2%} {return_diff:>14.2%}")

    # Average max drawdown
    json_dd = json_results.get('avg_drawdown', 0)
    baseline_dd = baseline_results.get('avg_drawdown', 0)
    dd_diff = json_dd - baseline_dd
    print(f"{'Avg Max Drawdown':<30} {json_dd:>7.2%} {baseline_dd:>15.2%} {dd_diff:>14.2%}")

    print()

    # Classification breakdown
    print("Classification Breakdown:")
    print("-" * 80)
    print(f"{'Level':<20} {'JSON Mode':<20} {'Full Code':<20}")
    print("-" * 80)

    json_counts = json_results.get('level_counts', {})
    baseline_counts = baseline_results.get('level_counts', {})
    json_total = json_results.get('total_iterations', 0)
    baseline_total = baseline_results.get('total_iterations', 0)

    for level in ['LEVEL_0', 'LEVEL_1', 'LEVEL_2', 'LEVEL_3']:
        json_count = json_counts.get(level, 0)
        baseline_count = baseline_counts.get(level, 0)
        json_pct = (json_count / json_total * 100) if json_total > 0 else 0
        baseline_pct = (baseline_count / baseline_total * 100) if baseline_total > 0 else 0
        print(f"{level:<20} {json_count:>3} ({json_pct:>5.1f}%) {baseline_count:>11} ({baseline_pct:>5.1f}%)")

    print()

    # Champion comparison
    print("Champion Strategies:")
    print("-" * 80)

    json_champ = json_results.get('champion', {})
    baseline_champ = baseline_results.get('champion', {})

    print(f"JSON Mode Champion:")
    if json_champ:
        print(f"  Iteration: #{json_champ.get('iteration')}")
        print(f"  Sharpe Ratio: {json_champ.get('sharpe_ratio', 0):.4f}")
        print(f"  Total Return: {json_champ.get('total_return', 0):.2%}")
        print(f"  Max Drawdown: {json_champ.get('max_drawdown', 0):.2%}")
    else:
        print("  No champion found")

    print()

    print(f"Full Code Baseline Champion:")
    if baseline_champ:
        print(f"  Iteration: #{baseline_champ.get('iteration')}")
        print(f"  Sharpe Ratio: {baseline_champ.get('sharpe_ratio', 0):.4f}")
        print(f"  Total Return: {baseline_champ.get('total_return', 0):.2%}")
        print(f"  Max Drawdown: {baseline_champ.get('max_drawdown', 0):.2%}")
    else:
        print("  No champion found")

    print()
    print("=" * 80)

    # Conclusion
    print("\nConclusion:")
    print("-" * 80)

    if json_success > baseline_success:
        improvement = json_success - baseline_success
        print(f"[OK] JSON Mode shows {improvement:.1f}% higher success rate")
    elif json_success < baseline_success:
        degradation = baseline_success - json_success
        print(f"[WARN] JSON Mode shows {degradation:.1f}% lower success rate")
    else:
        print(f"[INFO] Both modes have equal success rates ({json_success:.1f}%)")

    if json_sharpe > baseline_sharpe:
        improvement = (json_sharpe - baseline_sharpe) / baseline_sharpe * 100 if baseline_sharpe != 0 else 0
        print(f"[OK] JSON Mode shows {improvement:.1f}% better average Sharpe ratio")
    elif json_sharpe < baseline_sharpe:
        degradation = (baseline_sharpe - json_sharpe) / baseline_sharpe * 100 if baseline_sharpe != 0 else 0
        print(f"[WARN] JSON Mode shows {degradation:.1f}% worse average Sharpe ratio")
    else:
        print(f"[INFO] Both modes have equal average Sharpe ratios")

    print()

def main():
    """Main comparison function."""
    # File paths
    json_history = "experiments/llm_learning_validation/results/json_mode_test/history.jsonl"
    baseline_history = "experiments/llm_learning_validation/results/full_code_baseline/history.jsonl"

    print("\n" + "=" * 80)
    print("Loading Test Results")
    print("=" * 80)

    # Load results
    print(f"\nLoading JSON mode results: {json_history}")
    json_records = load_history(json_history)
    print(f"  Loaded: {len(json_records)} iterations")

    print(f"\nLoading Full Code baseline results: {baseline_history}")
    baseline_records = load_history(baseline_history)
    print(f"  Loaded: {len(baseline_records)} iterations")

    if not json_records:
        print("\n[ERROR] JSON mode results not found. Run: python3 run_json_mode_test_20.py")
        sys.exit(1)

    if not baseline_records:
        print("\n[ERROR] Full Code baseline results not found. Run: python3 run_full_code_baseline_20.py")
        sys.exit(1)

    print()

    # Analyze results
    print("Analyzing results...")
    json_results = analyze_results(json_records, "JSON Mode")
    baseline_results = analyze_results(baseline_records, "Full Code Baseline")

    # Print comparison
    print()
    print_comparison(json_results, baseline_results)

    # Save comparison report
    report_file = f"docs/PHASE2_COMPARISON_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    print(f"\nSaving detailed report to: {report_file}")

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Phase 2.3 Comparison Report: JSON Mode vs Full Code Baseline\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- JSON Mode Success Rate: {json_results['success_rate']:.1f}%\n")
        f.write(f"- Full Code Success Rate: {baseline_results['success_rate']:.1f}%\n")
        f.write(f"- Difference: {json_results['success_rate'] - baseline_results['success_rate']:.1f}%\n\n")
        f.write("## Detailed Results\n\n")
        f.write("See console output for full comparison.\n")

    print(f"[OK] Report saved: {report_file}")
    print()

if __name__ == "__main__":
    main()
