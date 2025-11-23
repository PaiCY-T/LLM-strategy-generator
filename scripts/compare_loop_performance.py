#!/usr/bin/env python3
"""
Loop Performance Comparison Script

Compares performance metrics between AutonomousLoop and UnifiedLoop from
100-iteration test runs. Generates comprehensive comparison report with
statistical analysis.

Usage:
    python3 scripts/compare_loop_performance.py --autonomous AUTONOMOUS_RESULTS --unified UNIFIED_RESULTS [--output REPORT_FILE]

Arguments:
    --autonomous    Path to AutonomousLoop results JSON file
    --unified       Path to UnifiedLoop results JSON file
    --output        Optional output file for comparison report (default: stdout)

Example:
    python3 scripts/compare_loop_performance.py \\
        --autonomous results/baseline_autonomous_100iter.json \\
        --unified results/unified_100iter_momentum_20251122_150000.json \\
        --output comparison_report.md
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple


def load_results(filepath: str) -> Dict[str, Any]:
    """Load test results from JSON file.

    Args:
        filepath: Path to results JSON file

    Returns:
        dict: Test results dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Results file not found: {filepath}")

    with open(filepath, 'r') as f:
        return json.load(f)


def extract_key_metrics(results: Dict[str, Any]) -> Dict[str, float]:
    """Extract key performance metrics from results.

    Args:
        results: Test results dictionary

    Returns:
        dict: Extracted metrics
    """
    statistical_report = results.get('statistical_report', {})

    return {
        'total_iterations': results.get('total_iterations', 0),
        'success_rate': results.get('success_rate', 0.0),
        'total_duration_seconds': results.get('total_duration_seconds', 0.0),
        'best_sharpe': results.get('best_sharpe', 0.0),
        'avg_sharpe': results.get('avg_sharpe', 0.0),
        'mean_sharpe': statistical_report.get('mean_sharpe', 0.0),
        'std_sharpe': statistical_report.get('std_sharpe', 0.0),
        'cohens_d': statistical_report.get('cohens_d', 0.0),
        'p_value': statistical_report.get('p_value', 1.0),
        'is_significant': statistical_report.get('is_significant', False),
        'champion_update_frequency': statistical_report.get('champion_update_frequency', 0.0),
        'production_ready': statistical_report.get('production_ready', False)
    }


def compare_execution_time(
    autonomous_duration: float,
    unified_duration: float
) -> Tuple[bool, float, str]:
    """Compare execution time between loops.

    Criterion: UnifiedLoop execution time ≤ AutonomousLoop * 1.1 (10% overhead acceptable)

    Args:
        autonomous_duration: AutonomousLoop duration in seconds
        unified_duration: UnifiedLoop duration in seconds

    Returns:
        tuple: (passed, ratio, interpretation)
    """
    if autonomous_duration == 0:
        return (False, 0.0, "Cannot compare: AutonomousLoop duration is 0")

    ratio = unified_duration / autonomous_duration
    threshold = 1.1

    passed = ratio <= threshold

    if passed:
        interpretation = f"✅ UnifiedLoop is {ratio:.2f}x AutonomousLoop speed (within 10% overhead)"
    else:
        interpretation = f"❌ UnifiedLoop is {ratio:.2f}x AutonomousLoop speed (exceeds 10% overhead)"

    return (passed, ratio, interpretation)


def compare_success_rate(
    autonomous_rate: float,
    unified_rate: float
) -> Tuple[bool, float, str]:
    """Compare success rate between loops.

    Criterion: UnifiedLoop success rate ≥ AutonomousLoop * 0.95 (no more than 5% degradation)

    Args:
        autonomous_rate: AutonomousLoop success rate (percentage)
        unified_rate: UnifiedLoop success rate (percentage)

    Returns:
        tuple: (passed, difference, interpretation)
    """
    if autonomous_rate == 0:
        return (False, 0.0, "Cannot compare: AutonomousLoop success rate is 0")

    threshold_rate = autonomous_rate * 0.95
    passed = unified_rate >= threshold_rate

    difference = unified_rate - autonomous_rate

    if passed:
        if difference >= 0:
            interpretation = f"✅ UnifiedLoop success rate is {difference:.1f}% higher than AutonomousLoop"
        else:
            interpretation = f"✅ UnifiedLoop success rate is {abs(difference):.1f}% lower (within 5% tolerance)"
    else:
        interpretation = f"❌ UnifiedLoop success rate is {abs(difference):.1f}% lower (exceeds 5% tolerance)"

    return (passed, difference, interpretation)


def compare_champion_update_rate(
    autonomous_rate: float,
    unified_rate: float
) -> Tuple[bool, float, str]:
    """Compare champion update rate between loops.

    Criterion: UnifiedLoop champion update rate > AutonomousLoop
    (FeedbackGenerator should increase learning effectiveness)

    Args:
        autonomous_rate: AutonomousLoop champion update rate (percentage)
        unified_rate: UnifiedLoop champion update rate (percentage)

    Returns:
        tuple: (passed, difference, interpretation)
    """
    passed = unified_rate > autonomous_rate
    difference = unified_rate - autonomous_rate

    if passed:
        improvement_ratio = (unified_rate / autonomous_rate) if autonomous_rate > 0 else float('inf')
        interpretation = f"✅ UnifiedLoop update rate is {difference:.1f}% higher ({improvement_ratio:.2f}x)"
    else:
        interpretation = f"❌ UnifiedLoop update rate is {abs(difference):.1f}% lower (expected improvement)"

    return (passed, difference, interpretation)


def compare_cohens_d(unified_cohens_d: float) -> Tuple[bool, str]:
    """Check if UnifiedLoop achieves meaningful effect size.

    Criterion: Cohen's d > 0.4 (medium effect size)

    Args:
        unified_cohens_d: UnifiedLoop Cohen's d value

    Returns:
        tuple: (passed, interpretation)
    """
    threshold = 0.4
    passed = unified_cohens_d > threshold

    if passed:
        if unified_cohens_d >= 0.8:
            size = "large"
        elif unified_cohens_d >= 0.5:
            size = "medium-large"
        else:
            size = "medium"
        interpretation = f"✅ Cohen's d = {unified_cohens_d:.3f} ({size} effect size)"
    else:
        interpretation = f"❌ Cohen's d = {unified_cohens_d:.3f} (below medium effect size threshold 0.4)"

    return (passed, interpretation)


def generate_comparison_report(
    autonomous_results: Dict[str, Any],
    unified_results: Dict[str, Any],
    output_file: str = None
) -> str:
    """Generate comprehensive comparison report.

    Args:
        autonomous_results: AutonomousLoop test results
        unified_results: UnifiedLoop test results
        output_file: Optional output file path

    Returns:
        str: Comparison report text
    """
    # Extract metrics
    auto_metrics = extract_key_metrics(autonomous_results)
    unified_metrics = extract_key_metrics(unified_results)

    # Perform comparisons
    time_passed, time_ratio, time_interp = compare_execution_time(
        auto_metrics['total_duration_seconds'],
        unified_metrics['total_duration_seconds']
    )

    success_passed, success_diff, success_interp = compare_success_rate(
        auto_metrics['success_rate'],
        unified_metrics['success_rate']
    )

    update_passed, update_diff, update_interp = compare_champion_update_rate(
        auto_metrics['champion_update_frequency'],
        unified_metrics['champion_update_frequency']
    )

    cohens_passed, cohens_interp = compare_cohens_d(
        unified_metrics['cohens_d']
    )

    # Overall pass/fail
    all_passed = time_passed and success_passed and update_passed and cohens_passed

    # Build report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("LOOP PERFORMANCE COMPARISON REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"Generated: {datetime.now().isoformat()}")
    report_lines.append("")

    # Overall result
    report_lines.append("## OVERALL RESULT")
    report_lines.append("")
    if all_passed:
        report_lines.append("✅ **ALL CRITERIA PASSED** - UnifiedLoop meets all performance requirements")
    else:
        report_lines.append("❌ **SOME CRITERIA FAILED** - UnifiedLoop does not meet all requirements")
    report_lines.append("")

    # Summary table
    report_lines.append("## PERFORMANCE SUMMARY")
    report_lines.append("")
    report_lines.append("| Metric | AutonomousLoop | UnifiedLoop | Status |")
    report_lines.append("|--------|----------------|-------------|---------|")
    report_lines.append(f"| Total Iterations | {auto_metrics['total_iterations']} | {unified_metrics['total_iterations']} | - |")
    report_lines.append(f"| Success Rate | {auto_metrics['success_rate']:.1f}% | {unified_metrics['success_rate']:.1f}% | {'✅' if success_passed else '❌'} |")
    report_lines.append(f"| Duration (hours) | {auto_metrics['total_duration_seconds']/3600:.2f} | {unified_metrics['total_duration_seconds']/3600:.2f} | {'✅' if time_passed else '❌'} |")
    report_lines.append(f"| Best Sharpe | {auto_metrics['best_sharpe']:.4f} | {unified_metrics['best_sharpe']:.4f} | - |")
    report_lines.append(f"| Avg Sharpe | {auto_metrics['avg_sharpe']:.4f} | {unified_metrics['avg_sharpe']:.4f} | - |")
    report_lines.append(f"| Champion Updates | {auto_metrics['champion_update_frequency']:.1f}% | {unified_metrics['champion_update_frequency']:.1f}% | {'✅' if update_passed else '❌'} |")
    report_lines.append(f"| Cohen's d | {auto_metrics['cohens_d']:.3f} | {unified_metrics['cohens_d']:.3f} | {'✅' if cohens_passed else '❌'} |")
    report_lines.append("")

    # Detailed comparisons
    report_lines.append("## DETAILED COMPARISON")
    report_lines.append("")

    report_lines.append("### 1. Execution Time")
    report_lines.append(f"- **Criterion**: UnifiedLoop ≤ AutonomousLoop × 1.1")
    report_lines.append(f"- **AutonomousLoop**: {auto_metrics['total_duration_seconds']/3600:.2f} hours")
    report_lines.append(f"- **UnifiedLoop**: {unified_metrics['total_duration_seconds']/3600:.2f} hours")
    report_lines.append(f"- **Ratio**: {time_ratio:.2f}x")
    report_lines.append(f"- **Result**: {time_interp}")
    report_lines.append("")

    report_lines.append("### 2. Success Rate")
    report_lines.append(f"- **Criterion**: UnifiedLoop ≥ AutonomousLoop × 0.95")
    report_lines.append(f"- **AutonomousLoop**: {auto_metrics['success_rate']:.1f}%")
    report_lines.append(f"- **UnifiedLoop**: {unified_metrics['success_rate']:.1f}%")
    report_lines.append(f"- **Difference**: {success_diff:+.1f}%")
    report_lines.append(f"- **Result**: {success_interp}")
    report_lines.append("")

    report_lines.append("### 3. Champion Update Rate")
    report_lines.append(f"- **Criterion**: UnifiedLoop > AutonomousLoop")
    report_lines.append(f"- **AutonomousLoop**: {auto_metrics['champion_update_frequency']:.1f}%")
    report_lines.append(f"- **UnifiedLoop**: {unified_metrics['champion_update_frequency']:.1f}%")
    report_lines.append(f"- **Difference**: {update_diff:+.1f}%")
    report_lines.append(f"- **Result**: {update_interp}")
    report_lines.append("")

    report_lines.append("### 4. Learning Effect Size (Cohen's d)")
    report_lines.append(f"- **Criterion**: Cohen's d > 0.4")
    report_lines.append(f"- **AutonomousLoop**: {auto_metrics['cohens_d']:.3f}")
    report_lines.append(f"- **UnifiedLoop**: {unified_metrics['cohens_d']:.3f}")
    report_lines.append(f"- **Result**: {cohens_interp}")
    report_lines.append("")

    # Statistical significance
    report_lines.append("## STATISTICAL ANALYSIS")
    report_lines.append("")
    report_lines.append(f"**AutonomousLoop**:")
    report_lines.append(f"- Mean Sharpe: {auto_metrics['mean_sharpe']:.4f}")
    report_lines.append(f"- Std Sharpe: {auto_metrics['std_sharpe']:.4f}")
    report_lines.append(f"- P-value: {auto_metrics['p_value']:.4f} ({'significant' if auto_metrics['is_significant'] else 'not significant'})")
    report_lines.append(f"- Production ready: {auto_metrics['production_ready']}")
    report_lines.append("")
    report_lines.append(f"**UnifiedLoop**:")
    report_lines.append(f"- Mean Sharpe: {unified_metrics['mean_sharpe']:.4f}")
    report_lines.append(f"- Std Sharpe: {unified_metrics['std_sharpe']:.4f}")
    report_lines.append(f"- P-value: {unified_metrics['p_value']:.4f} ({'significant' if unified_metrics['is_significant'] else 'not significant'})")
    report_lines.append(f"- Production ready: {unified_metrics['production_ready']}")
    report_lines.append("")

    # Conclusion
    report_lines.append("## CONCLUSION")
    report_lines.append("")
    if all_passed:
        report_lines.append("✅ **UnifiedLoop successfully meets all performance criteria:**")
        report_lines.append("- Execution time is within acceptable overhead (≤10%)")
        report_lines.append("- Success rate is maintained (≥95% of baseline)")
        report_lines.append("- Champion update rate improved (learning effectiveness)")
        report_lines.append("- Meaningful learning effect achieved (Cohen's d > 0.4)")
        report_lines.append("")
        report_lines.append("**UnifiedLoop is ready for production use.**")
    else:
        report_lines.append("❌ **UnifiedLoop does not meet all performance criteria.**")
        report_lines.append("")
        report_lines.append("**Failed criteria:**")
        if not time_passed:
            report_lines.append(f"- Execution time: {time_interp}")
        if not success_passed:
            report_lines.append(f"- Success rate: {success_interp}")
        if not update_passed:
            report_lines.append(f"- Champion update rate: {update_interp}")
        if not cohens_passed:
            report_lines.append(f"- Cohen's d: {cohens_interp}")
        report_lines.append("")
        report_lines.append("**Further investigation and optimization required.**")

    report_lines.append("")
    report_lines.append("=" * 80)

    report_text = "\n".join(report_lines)

    # Write to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(report_text)
        print(f"Comparison report saved to: {output_file}")

    return report_text


def main():
    """Main entry point for comparison script."""
    parser = argparse.ArgumentParser(
        description="Compare performance between AutonomousLoop and UnifiedLoop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python3 scripts/compare_loop_performance.py \\
      --autonomous results/baseline_autonomous_100iter.json \\
      --unified results/unified_100iter_momentum_20251122_150000.json \\
      --output comparison_report.md
        """
    )

    parser.add_argument(
        '--autonomous',
        type=str,
        required=True,
        help='Path to AutonomousLoop results JSON file'
    )

    parser.add_argument(
        '--unified',
        type=str,
        required=True,
        help='Path to UnifiedLoop results JSON file'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file for comparison report (default: stdout)'
    )

    args = parser.parse_args()

    try:
        # Load results
        print(f"Loading AutonomousLoop results from: {args.autonomous}")
        autonomous_results = load_results(args.autonomous)

        print(f"Loading UnifiedLoop results from: {args.unified}")
        unified_results = load_results(args.unified)

        # Generate comparison report
        print("\nGenerating comparison report...")
        report = generate_comparison_report(
            autonomous_results,
            unified_results,
            args.output
        )

        # Print to stdout if no output file specified
        if not args.output:
            print("\n")
            print(report)

        print("\n✅ Comparison complete")
        sys.exit(0)

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"\n❌ Error: Invalid JSON file - {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
