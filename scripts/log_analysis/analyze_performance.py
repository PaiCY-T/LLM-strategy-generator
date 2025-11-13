#!/usr/bin/env python3
"""
Performance Analysis Tool for Trading System Logs.

Analyzes JSON logs to extract performance metrics and identify bottlenecks:
- Iteration duration statistics
- Champion update frequency
- Validation pass rates
- Metric extraction performance
- Template instantiation success rates

Usage:
    python analyze_performance.py --log-file logs/iterations.json.log --report summary
    python analyze_performance.py --log-file logs/iterations.json.log --report detailed --output report.html
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import statistics


class PerformanceAnalyzer:
    """Analyzer for trading system performance metrics from logs."""

    def __init__(self, log_file: Path):
        """
        Initialize analyzer.

        Args:
            log_file: Path to JSON log file
        """
        self.log_file = log_file
        self.entries: List[Dict[str, Any]] = []
        self.load_logs()

    def load_logs(self):
        """Load log entries from file."""
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    self.entries.append(entry)
                except json.JSONDecodeError:
                    continue

    def analyze_iterations(self) -> Dict[str, Any]:
        """
        Analyze iteration performance.

        Returns:
            Dictionary with iteration statistics
        """
        iteration_starts = [e for e in self.entries if e.get('event_type') == 'iteration_start']
        iteration_ends = [e for e in self.entries if e.get('event_type') == 'iteration_end']

        # Calculate duration statistics
        durations = [e.get('duration_seconds', 0) for e in iteration_ends if 'duration_seconds' in e]

        # Success rates
        total_iterations = len(iteration_ends)
        successful = len([e for e in iteration_ends if e.get('success')])
        validation_passed = len([e for e in iteration_ends if e.get('validation_passed')])
        execution_success = len([e for e in iteration_ends if e.get('execution_success')])

        return {
            'total_iterations': total_iterations,
            'successful_iterations': successful,
            'success_rate': (successful / total_iterations * 100) if total_iterations > 0 else 0,
            'validation_pass_rate': (validation_passed / total_iterations * 100) if total_iterations > 0 else 0,
            'execution_success_rate': (execution_success / total_iterations * 100) if total_iterations > 0 else 0,
            'duration_stats': {
                'min': min(durations) if durations else 0,
                'max': max(durations) if durations else 0,
                'mean': statistics.mean(durations) if durations else 0,
                'median': statistics.median(durations) if durations else 0,
                'stdev': statistics.stdev(durations) if len(durations) > 1 else 0,
            }
        }

    def analyze_champions(self) -> Dict[str, Any]:
        """
        Analyze champion updates.

        Returns:
            Dictionary with champion statistics
        """
        champion_updates = [e for e in self.entries if e.get('event_type') == 'champion_update']
        champion_rejections = [e for e in self.entries if e.get('event_type') == 'champion_rejected']
        champion_demotions = [e for e in self.entries if e.get('event_type') == 'champion_demotion']

        # Calculate update frequency
        total_updates = len(champion_updates)
        iterations = [e.get('iteration_num') for e in champion_updates]

        # Calculate improvement statistics
        improvements = [e.get('improvement_pct', 0) for e in champion_updates]

        # Threshold type distribution
        threshold_types = Counter([e.get('threshold_type') for e in champion_updates])

        return {
            'total_updates': total_updates,
            'total_rejections': len(champion_rejections),
            'total_demotions': len(champion_demotions),
            'update_rate': (total_updates / len(iterations) * 100) if iterations else 0,
            'improvement_stats': {
                'min': min(improvements) if improvements else 0,
                'max': max(improvements) if improvements else 0,
                'mean': statistics.mean(improvements) if improvements else 0,
                'median': statistics.median(improvements) if improvements else 0,
            },
            'threshold_types': dict(threshold_types),
            'multi_objective_pass_rate': (
                len([e for e in champion_updates if e.get('multi_objective_passed', True)]) /
                len(champion_updates) * 100
            ) if champion_updates else 0,
        }

    def analyze_metrics(self) -> Dict[str, Any]:
        """
        Analyze metric extraction performance.

        Returns:
            Dictionary with metric extraction statistics
        """
        extractions = [e for e in self.entries if e.get('event_type') == 'metric_extraction']

        # Success rate
        successful = [e for e in extractions if e.get('success')]
        success_rate = (len(successful) / len(extractions) * 100) if extractions else 0

        # Method distribution
        methods = Counter([e.get('method_used') for e in extractions])

        # Duration statistics
        durations = [e.get('duration_ms', 0) for e in extractions if 'duration_ms' in e]

        # Fallback statistics
        fallback_counts = [e.get('fallback_attempts', 0) for e in extractions]

        return {
            'total_extractions': len(extractions),
            'success_rate': success_rate,
            'method_distribution': dict(methods),
            'duration_stats': {
                'min': min(durations) if durations else 0,
                'max': max(durations) if durations else 0,
                'mean': statistics.mean(durations) if durations else 0,
                'median': statistics.median(durations) if durations else 0,
                'p95': sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
            },
            'fallback_stats': {
                'mean': statistics.mean(fallback_counts) if fallback_counts else 0,
                'max': max(fallback_counts) if fallback_counts else 0,
            }
        }

    def analyze_validations(self) -> Dict[str, Any]:
        """
        Analyze validation performance.

        Returns:
            Dictionary with validation statistics
        """
        validations = [e for e in self.entries if e.get('event_type') == 'validation_result']

        # Group by validator
        by_validator = defaultdict(list)
        for entry in validations:
            validator = entry.get('validator_name', 'Unknown')
            by_validator[validator].append(entry)

        validator_stats = {}
        for validator, entries in by_validator.items():
            passed = len([e for e in entries if e.get('passed')])
            total = len(entries)
            durations = [e.get('duration_ms', 0) for e in entries if 'duration_ms' in e]

            validator_stats[validator] = {
                'total_validations': total,
                'pass_rate': (passed / total * 100) if total > 0 else 0,
                'duration_stats': {
                    'mean': statistics.mean(durations) if durations else 0,
                    'median': statistics.median(durations) if durations else 0,
                    'p95': sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
                }
            }

        return validator_stats

    def analyze_templates(self) -> Dict[str, Any]:
        """
        Analyze template integration performance.

        Returns:
            Dictionary with template statistics
        """
        recommendations = [e for e in self.entries if e.get('event_type') == 'template_recommendation']
        instantiations = [e for e in self.entries if e.get('event_type') == 'template_instantiation']

        # Template distribution
        template_names = Counter([e.get('template_name') for e in recommendations])

        # Exploration mode frequency
        exploration = len([e for e in recommendations if e.get('exploration_mode')])

        # Instantiation success rate
        successful = len([e for e in instantiations if e.get('success')])
        success_rate = (successful / len(instantiations) * 100) if instantiations else 0

        # Retry statistics
        retries = [e.get('retry_count', 0) for e in instantiations]

        return {
            'total_recommendations': len(recommendations),
            'total_instantiations': len(instantiations),
            'instantiation_success_rate': success_rate,
            'template_distribution': dict(template_names),
            'exploration_mode_rate': (exploration / len(recommendations) * 100) if recommendations else 0,
            'retry_stats': {
                'mean': statistics.mean(retries) if retries else 0,
                'max': max(retries) if retries else 0,
            }
        }

    def generate_summary_report(self) -> str:
        """
        Generate summary performance report.

        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("TRADING SYSTEM PERFORMANCE SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Log file: {self.log_file}")
        lines.append(f"Total log entries: {len(self.entries)}")
        lines.append(f"Analysis timestamp: {datetime.now().isoformat()}")
        lines.append("")

        # Iteration statistics
        lines.append("-" * 80)
        lines.append("ITERATION PERFORMANCE")
        lines.append("-" * 80)
        iter_stats = self.analyze_iterations()
        lines.append(f"Total iterations: {iter_stats['total_iterations']}")
        lines.append(f"Success rate: {iter_stats['success_rate']:.1f}%")
        lines.append(f"Validation pass rate: {iter_stats['validation_pass_rate']:.1f}%")
        lines.append(f"Execution success rate: {iter_stats['execution_success_rate']:.1f}%")
        lines.append(f"\nDuration statistics:")
        lines.append(f"  Mean: {iter_stats['duration_stats']['mean']:.2f}s")
        lines.append(f"  Median: {iter_stats['duration_stats']['median']:.2f}s")
        lines.append(f"  Min/Max: {iter_stats['duration_stats']['min']:.2f}s / {iter_stats['duration_stats']['max']:.2f}s")
        lines.append("")

        # Champion statistics
        lines.append("-" * 80)
        lines.append("CHAMPION UPDATES")
        lines.append("-" * 80)
        champ_stats = self.analyze_champions()
        lines.append(f"Total updates: {champ_stats['total_updates']}")
        lines.append(f"Total rejections: {champ_stats['total_rejections']}")
        lines.append(f"Total demotions: {champ_stats['total_demotions']}")
        lines.append(f"Multi-objective pass rate: {champ_stats['multi_objective_pass_rate']:.1f}%")
        lines.append(f"\nImprovement statistics:")
        lines.append(f"  Mean: {champ_stats['improvement_stats']['mean']:.2f}%")
        lines.append(f"  Median: {champ_stats['improvement_stats']['median']:.2f}%")
        lines.append(f"  Max: {champ_stats['improvement_stats']['max']:.2f}%")
        lines.append(f"\nThreshold types:")
        for threshold_type, count in champ_stats['threshold_types'].items():
            lines.append(f"  {threshold_type}: {count}")
        lines.append("")

        # Metric extraction statistics
        lines.append("-" * 80)
        lines.append("METRIC EXTRACTION")
        lines.append("-" * 80)
        metric_stats = self.analyze_metrics()
        lines.append(f"Total extractions: {metric_stats['total_extractions']}")
        lines.append(f"Success rate: {metric_stats['success_rate']:.1f}%")
        lines.append(f"\nMethod distribution:")
        for method, count in metric_stats['method_distribution'].items():
            lines.append(f"  {method}: {count}")
        lines.append(f"\nDuration statistics:")
        lines.append(f"  Mean: {metric_stats['duration_stats']['mean']:.2f}ms")
        lines.append(f"  Median: {metric_stats['duration_stats']['median']:.2f}ms")
        lines.append(f"  P95: {metric_stats['duration_stats']['p95']:.2f}ms")
        lines.append(f"\nFallback statistics:")
        lines.append(f"  Mean attempts: {metric_stats['fallback_stats']['mean']:.2f}")
        lines.append(f"  Max attempts: {metric_stats['fallback_stats']['max']}")
        lines.append("")

        # Validation statistics
        lines.append("-" * 80)
        lines.append("VALIDATION PERFORMANCE")
        lines.append("-" * 80)
        val_stats = self.analyze_validations()
        for validator, stats in val_stats.items():
            lines.append(f"\n{validator}:")
            lines.append(f"  Total: {stats['total_validations']}")
            lines.append(f"  Pass rate: {stats['pass_rate']:.1f}%")
            lines.append(f"  Mean duration: {stats['duration_stats']['mean']:.2f}ms")
            lines.append(f"  P95 duration: {stats['duration_stats']['p95']:.2f}ms")
        lines.append("")

        # Template statistics
        lines.append("-" * 80)
        lines.append("TEMPLATE INTEGRATION")
        lines.append("-" * 80)
        template_stats = self.analyze_templates()
        lines.append(f"Total recommendations: {template_stats['total_recommendations']}")
        lines.append(f"Instantiation success rate: {template_stats['instantiation_success_rate']:.1f}%")
        lines.append(f"Exploration mode rate: {template_stats['exploration_mode_rate']:.1f}%")
        lines.append(f"\nTemplate distribution:")
        for template, count in sorted(template_stats['template_distribution'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {template}: {count}")
        lines.append(f"\nRetry statistics:")
        lines.append(f"  Mean retries: {template_stats['retry_stats']['mean']:.2f}")
        lines.append(f"  Max retries: {template_stats['retry_stats']['max']}")

        lines.append("\n" + "=" * 80)
        return '\n'.join(lines)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze performance metrics from JSON logs'
    )

    parser.add_argument('--log-file', type=Path, required=True,
                        help='Path to JSON log file')
    parser.add_argument('--report', type=str, default='summary',
                        choices=['summary', 'detailed'],
                        help='Report type')
    parser.add_argument('--output', type=Path,
                        help='Output file (default: stdout)')

    args = parser.parse_args()

    # Verify log file exists
    if not args.log_file.exists():
        print(f"Error: Log file not found: {args.log_file}")
        return 1

    # Analyze logs
    analyzer = PerformanceAnalyzer(args.log_file)
    report = analyzer.generate_summary_report()

    # Output report
    if args.output:
        args.output.write_text(report, encoding='utf-8')
        print(f"Report written to: {args.output}")
    else:
        print(report)

    return 0


if __name__ == '__main__':
    exit(main())
