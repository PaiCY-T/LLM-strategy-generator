#!/usr/bin/env python3
"""Analyze historical iteration performance for Task A4 validation.

This script analyzes the iteration_history.json to validate the system
has achieved the required 70% success rate threshold.
"""

import json
from pathlib import Path
from typing import Dict, Any, List


def analyze_historical_data() -> Dict[str, Any]:
    """Analyze historical iteration data.

    Returns:
        Dictionary with analysis results
    """
    # Load data
    with open('iteration_history.json', 'r') as f:
        data = json.load(f)

    records = data.get('records', [])

    if not records:
        return {'error': 'No records found'}

    # Calculate statistics
    total = len(records)
    has_code = sum(1 for r in records if r.get('code'))
    validation_passed = sum(1 for r in records if r.get('validation_passed'))
    execution_success = sum(1 for r in records if r.get('execution_success'))
    has_metrics = sum(1 for r in records if r.get('metrics'))

    # Recent performance (last 10)
    recent_records = records[-10:]
    recent_success = sum(1 for r in recent_records
                        if r.get('execution_success') and r.get('metrics'))

    # Metrics statistics
    successful_metrics = [r['metrics'] for r in records if r.get('metrics')]

    metrics_stats = None
    if successful_metrics:
        sharpe_ratios = [m['sharpe_ratio'] for m in successful_metrics]
        returns = [m['total_return'] * 100 for m in successful_metrics]
        drawdowns = [m['max_drawdown'] * 100 for m in successful_metrics]

        metrics_stats = {
            'sharpe_ratio': {
                'min': min(sharpe_ratios),
                'max': max(sharpe_ratios),
                'avg': sum(sharpe_ratios) / len(sharpe_ratios),
                'median': sorted(sharpe_ratios)[len(sharpe_ratios) // 2]
            },
            'total_return': {
                'min': min(returns),
                'max': max(returns),
                'avg': sum(returns) / len(returns),
                'median': sorted(returns)[len(returns) // 2]
            },
            'max_drawdown': {
                'min': min(drawdowns),
                'max': max(drawdowns),
                'avg': sum(drawdowns) / len(drawdowns),
                'median': sorted(drawdowns)[len(drawdowns) // 2]
            }
        }

    # Error analysis
    failed_records = [r for r in records if not r.get('execution_success')]
    error_types = {}

    for rec in failed_records:
        error = rec.get('execution_error', 'Unknown error')
        # Categorize
        if 'not exists' in error:
            error_type = 'Dataset key error'
        elif 'NameError' in error:
            error_type = 'Name/variable error'
        elif 'TypeError' in error:
            error_type = 'Type error'
        elif 'ValueError' in error:
            error_type = 'Value error'
        else:
            error_type = 'Other runtime error'

        error_types[error_type] = error_types.get(error_type, 0) + 1

    # Timeline analysis (group by batches of 25)
    timeline = []
    batch_size = 25
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        batch_success = sum(1 for r in batch if r.get('execution_success'))
        timeline.append({
            'range': f"{i}-{i+len(batch)-1}",
            'success_rate': batch_success / len(batch) if batch else 0,
            'count': len(batch)
        })

    return {
        'total_iterations': total,
        'code_generation_rate': has_code / total,
        'validation_rate': validation_passed / total,
        'execution_rate': execution_success / total,
        'metrics_rate': has_metrics / total,
        'overall_success_rate': has_metrics / total,  # Success = has metrics
        'recent_success_rate': recent_success / len(recent_records),
        'recent_count': len(recent_records),
        'metrics_stats': metrics_stats,
        'error_types': error_types,
        'timeline': timeline,
        'go_no_go': 'GO' if (recent_success / len(recent_records)) >= 0.70 else 'NO-GO'
    }


def print_report(analysis: Dict[str, Any]):
    """Print formatted report.

    Args:
        analysis: Analysis results dictionary
    """
    print("="*70)
    print("HISTORICAL ITERATION ANALYSIS - TASK A4 VALIDATION")
    print("="*70)
    print()

    print(f"Total Iterations: {analysis['total_iterations']}")
    print()

    print("STAGE-WISE SUCCESS RATES:")
    print(f"  Code Generation:  {analysis['code_generation_rate']*100:>6.1f}%")
    print(f"  AST Validation:   {analysis['validation_rate']*100:>6.1f}%")
    print(f"  Execution:        {analysis['execution_rate']*100:>6.1f}%")
    print(f"  Metrics:          {analysis['metrics_rate']*100:>6.1f}%")
    print()

    print(f"OVERALL SUCCESS RATE: {analysis['overall_success_rate']*100:.1f}%")
    print(f"RECENT SUCCESS RATE (last {analysis['recent_count']}): {analysis['recent_success_rate']*100:.1f}%")
    print()

    if analysis['metrics_stats']:
        print("METRICS QUALITY (Successful Iterations):")
        stats = analysis['metrics_stats']

        print(f"\n  Sharpe Ratio:")
        print(f"    Min: {stats['sharpe_ratio']['min']:>7.3f}")
        print(f"    Max: {stats['sharpe_ratio']['max']:>7.3f}")
        print(f"    Avg: {stats['sharpe_ratio']['avg']:>7.3f}")
        print(f"    Med: {stats['sharpe_ratio']['median']:>7.3f}")

        print(f"\n  Total Return (%):")
        print(f"    Min: {stats['total_return']['min']:>7.1f}%")
        print(f"    Max: {stats['total_return']['max']:>7.1f}%")
        print(f"    Avg: {stats['total_return']['avg']:>7.1f}%")
        print(f"    Med: {stats['total_return']['median']:>7.1f}%")

        print(f"\n  Max Drawdown (%):")
        print(f"    Min: {stats['max_drawdown']['min']:>7.1f}%")
        print(f"    Max: {stats['max_drawdown']['max']:>7.1f}%")
        print(f"    Avg: {stats['max_drawdown']['avg']:>7.1f}%")
        print(f"    Med: {stats['max_drawdown']['median']:>7.1f}%")

    if analysis['error_types']:
        print("\nERROR BREAKDOWN (Failed Iterations):")
        for error_type, count in sorted(analysis['error_types'].items(),
                                       key=lambda x: -x[1]):
            pct = count / (analysis['total_iterations'] - int(analysis['total_iterations'] * analysis['execution_rate']))
            print(f"  {error_type:<25} {count:>3} ({pct*100:>5.1f}%)")

    print("\nPERFORMANCE TIMELINE (by batch):")
    for batch in analysis['timeline']:
        bar_length = int(batch['success_rate'] * 40)
        bar = "█" * bar_length + "░" * (40 - bar_length)
        print(f"  Iter {batch['range']:>7}: {bar} {batch['success_rate']*100:>5.1f}%")

    print()
    print("="*70)
    print(f"GO/NO-GO DECISION: {analysis['go_no_go']}")
    print("="*70)

    if analysis['go_no_go'] == 'GO':
        print("\n✅ System meets ≥70% success threshold")
        print("   Recent performance: {:.0f}%".format(analysis['recent_success_rate']*100))
        print("   → PROCEED TO TASK A5 (PROMPT REFINEMENT)")
    else:
        print("\n❌ System below 70% success threshold")
        print("   Recent performance: {:.0f}%".format(analysis['recent_success_rate']*100))
        print("   → STOP AND REASSESS APPROACH")

    print()


def main():
    """Main entry point."""
    analysis = analyze_historical_data()

    if 'error' in analysis:
        print(f"Error: {analysis['error']}")
        return 1

    print_report(analysis)

    # Save detailed JSON
    output_path = Path('historical_analysis.json')
    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2)

    print(f"Detailed analysis saved to: {output_path}")
    print()

    return 0 if analysis['go_no_go'] == 'GO' else 1


if __name__ == '__main__':
    exit(main())
