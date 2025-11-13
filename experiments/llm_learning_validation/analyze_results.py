#!/usr/bin/env python3
"""
Analysis script for 300-iteration LLM characterization test.

Generates comprehensive statistics including:
- Success rate by classification level
- Sharpe ratio distribution
- Strategy diversity metrics
- Error pattern analysis
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Any
import statistics


def load_history(filepath: Path) -> List[Dict[str, Any]]:
    """Load iteration history from JSONL file."""
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def analyze_classification(records: List[Dict]) -> Dict:
    """Analyze classification level distribution."""
    levels = [r.get('classification_level', 'UNKNOWN') for r in records]
    total = len(levels)

    counts = Counter(levels)

    return {
        'total': total,
        'level_0': counts.get('LEVEL_0', 0),
        'level_1': counts.get('LEVEL_1', 0),
        'level_2': counts.get('LEVEL_2', 0),
        'level_3': counts.get('LEVEL_3', 0),
        'level_0_pct': counts.get('LEVEL_0', 0) / total * 100,
        'level_1_pct': counts.get('LEVEL_1', 0) / total * 100,
        'level_2_pct': counts.get('LEVEL_2', 0) / total * 100,
        'level_3_pct': counts.get('LEVEL_3', 0) / total * 100,
        'success_rate_1plus': (total - counts.get('LEVEL_0', 0)) / total * 100,
        'success_rate_3': counts.get('LEVEL_3', 0) / total * 100,
    }


def analyze_sharpe_ratios(records: List[Dict]) -> Dict:
    """Analyze Sharpe ratio distribution."""
    sharpe_ratios = []

    for r in records:
        metrics = r.get('metrics', {})
        if metrics and 'sharpe_ratio' in metrics:
            try:
                sharpe = float(metrics['sharpe_ratio'])
                if sharpe != 0:  # Exclude failed strategies
                    sharpe_ratios.append(sharpe)
            except (ValueError, TypeError):
                pass

    if not sharpe_ratios:
        return {'count': 0, 'error': 'No valid Sharpe ratios found'}

    return {
        'count': len(sharpe_ratios),
        'mean': statistics.mean(sharpe_ratios),
        'median': statistics.median(sharpe_ratios),
        'stdev': statistics.stdev(sharpe_ratios) if len(sharpe_ratios) > 1 else 0,
        'min': min(sharpe_ratios),
        'max': max(sharpe_ratios),
        'q1': statistics.quantiles(sharpe_ratios, n=4)[0] if len(sharpe_ratios) >= 4 else None,
        'q3': statistics.quantiles(sharpe_ratios, n=4)[2] if len(sharpe_ratios) >= 4 else None,
    }


def analyze_errors(records: List[Dict]) -> Dict:
    """Analyze error patterns."""
    error_types = defaultdict(int)
    error_messages = []

    for r in records:
        if r.get('classification_level') == 'LEVEL_0':
            # Get error message from execution_result
            exec_result = r.get('execution_result', {})
            error_msg = exec_result.get('error_message', 'Unknown error')

            # Categorize errors
            if 'did not create' in error_msg and 'report' in error_msg:
                error_types['missing_sim_call'] += 1
            elif 'SyntaxError' in error_msg or 'IndentationError' in error_msg:
                error_types['syntax'] += 1
            elif 'NameError' in error_msg or 'AttributeError' in error_msg:
                error_types['name_attribute'] += 1
            elif 'TypeError' in error_msg or 'ValueError' in error_msg:
                error_types['type_value'] += 1
            elif 'KeyError' in error_msg or 'IndexError' in error_msg:
                error_types['key_index'] += 1
            elif 'timeout' in error_msg.lower():
                error_types['timeout'] += 1
            else:
                error_types['other'] += 1

            # Keep first 100 chars of error message
            if error_msg and error_msg not in error_messages:
                error_messages.append(error_msg[:150])

    return {
        'total_errors': sum(error_types.values()),
        'error_types': dict(error_types),
        'sample_errors': list(set(error_messages))[:10],  # First 10 unique errors
    }


def analyze_generation_methods(records: List[Dict]) -> Dict:
    """Analyze generation method distribution."""
    methods = [r.get('generation_method', 'UNKNOWN') for r in records]
    counts = Counter(methods)

    return {
        'total': len(methods),
        'distribution': dict(counts),
        'llm_count': counts.get('llm', 0) + counts.get('LLM', 0),
        'llm_percentage': (counts.get('llm', 0) + counts.get('LLM', 0)) / len(methods) * 100,
    }


def analyze_champion_updates(records: List[Dict]) -> Dict:
    """Analyze champion update patterns."""
    updates = [r.get('champion_updated', False) for r in records]
    update_iterations = [i for i, r in enumerate(records) if r.get('champion_updated', False)]

    return {
        'total_updates': sum(updates),
        'update_rate': sum(updates) / len(updates) * 100,
        'update_iterations': update_iterations,
        'avg_iterations_between_updates': (
            statistics.mean([update_iterations[i+1] - update_iterations[i]
                           for i in range(len(update_iterations)-1)])
            if len(update_iterations) > 1 else None
        ),
    }


def generate_report(records: List[Dict]) -> str:
    """Generate comprehensive analysis report."""

    classification = analyze_classification(records)
    sharpe = analyze_sharpe_ratios(records)
    errors = analyze_errors(records)
    methods = analyze_generation_methods(records)
    champions = analyze_champion_updates(records)

    report = []
    report.append("=" * 80)
    report.append("LLM CHARACTERIZATION TEST - 300 ITERATIONS")
    report.append("=" * 80)
    report.append("")

    # Classification Analysis
    report.append("📊 CLASSIFICATION DISTRIBUTION")
    report.append("-" * 80)
    report.append(f"Total Iterations:     {classification['total']}")
    report.append(f"")
    report.append(f"LEVEL_0 (Failures):   {classification['level_0']:3d} ({classification['level_0_pct']:.1f}%)")
    report.append(f"LEVEL_1 (Executed):   {classification['level_1']:3d} ({classification['level_1_pct']:.1f}%)")
    report.append(f"LEVEL_2 (Weak):       {classification['level_2']:3d} ({classification['level_2_pct']:.1f}%)")
    report.append(f"LEVEL_3 (Success):    {classification['level_3']:3d} ({classification['level_3_pct']:.1f}%)")
    report.append(f"")
    report.append(f"✅ Success Rate (LEVEL_1+): {classification['success_rate_1plus']:.1f}%")
    report.append(f"🏆 Strong Success (LEVEL_3): {classification['success_rate_3']:.1f}%")
    report.append("")

    # Sharpe Ratio Analysis
    report.append("📈 SHARPE RATIO DISTRIBUTION")
    report.append("-" * 80)
    if 'error' not in sharpe:
        report.append(f"Valid Strategies:     {sharpe['count']}")
        report.append(f"Mean:                 {sharpe['mean']:.4f}")
        report.append(f"Median:               {sharpe['median']:.4f}")
        report.append(f"Std Dev:              {sharpe['stdev']:.4f}")
        report.append(f"Min:                  {sharpe['min']:.4f}")
        report.append(f"Max:                  {sharpe['max']:.4f}")
        if sharpe['q1'] is not None:
            report.append(f"Q1 (25th percentile): {sharpe['q1']:.4f}")
            report.append(f"Q3 (75th percentile): {sharpe['q3']:.4f}")
    else:
        report.append(f"⚠️  {sharpe['error']}")
    report.append("")

    # Error Analysis
    report.append("❌ ERROR PATTERN ANALYSIS")
    report.append("-" * 80)
    report.append(f"Total Errors:         {errors['total_errors']}")
    report.append(f"")
    report.append("Error Type Distribution:")
    for error_type, count in sorted(errors['error_types'].items(), key=lambda x: x[1], reverse=True):
        pct = count / errors['total_errors'] * 100 if errors['total_errors'] > 0 else 0
        report.append(f"  {error_type:20s}: {count:3d} ({pct:.1f}%)")

    if errors['sample_errors']:
        report.append(f"")
        report.append("Sample Error Messages (first 10):")
        for i, msg in enumerate(errors['sample_errors'][:10], 1):
            report.append(f"  {i}. {msg}...")
    report.append("")

    # Generation Method Analysis
    report.append("🤖 GENERATION METHOD DISTRIBUTION")
    report.append("-" * 80)
    report.append(f"Total Iterations:     {methods['total']}")
    report.append(f"LLM Generated:        {methods['llm_count']} ({methods['llm_percentage']:.1f}%)")
    report.append(f"")
    report.append("Method Distribution:")
    for method, count in sorted(methods['distribution'].items(), key=lambda x: x[1], reverse=True):
        pct = count / methods['total'] * 100
        report.append(f"  {method:20s}: {count:3d} ({pct:.1f}%)")
    report.append("")

    # Champion Updates
    report.append("🏆 CHAMPION UPDATE ANALYSIS")
    report.append("-" * 80)
    report.append(f"Total Updates:        {champions['total_updates']}")
    report.append(f"Update Rate:          {champions['update_rate']:.1f}%")
    if champions['avg_iterations_between_updates']:
        report.append(f"Avg Iterations Between Updates: {champions['avg_iterations_between_updates']:.1f}")
    if len(champions['update_iterations']) <= 20:
        report.append(f"Update Iterations:    {champions['update_iterations']}")
    else:
        report.append(f"First 10 Updates:     {champions['update_iterations'][:10]}")
        report.append(f"Last 10 Updates:      {champions['update_iterations'][-10:]}")
    report.append("")

    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)

    return "\n".join(report)


def main():
    """Main analysis function."""
    # File paths
    base_dir = Path(__file__).parent / "results"
    history_file = base_dir / "llm_only_run1_history.jsonl"
    output_file = base_dir / "analysis_report.txt"

    if not history_file.exists():
        print(f"❌ Error: History file not found: {history_file}")
        sys.exit(1)

    print(f"📊 Loading data from: {history_file}")
    records = load_history(history_file)
    print(f"✓ Loaded {len(records)} iteration records")

    print(f"📈 Generating analysis report...")
    report = generate_report(records)

    # Save report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ Report saved to: {output_file}")
    print("")
    print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
