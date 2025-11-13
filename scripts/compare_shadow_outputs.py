#!/usr/bin/env python3
"""
Shadow Mode Output Comparison Script

Compares outputs between Phase 1/2 and Phase 3 Strategy Pattern implementations
to validate behavioral equivalence. Used in CI/CD pipeline for shadow mode validation.

Usage:
    python scripts/compare_shadow_outputs.py \\
        --old logs/old_generation.json \\
        --new logs/new_generation.json \\
        --threshold 0.95

Exit Codes:
    0: Equivalence threshold met (success)
    1: Equivalence threshold not met (failure)
    2: Error during comparison (invalid input, file not found, etc.)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any


class ComparisonResult:
    """Results from comparing old and new implementations."""

    def __init__(self):
        self.total_comparisons = 0
        self.matches = 0
        self.mismatches = 0
        self.errors = 0
        self.mismatch_details: List[Dict[str, Any]] = []

    def add_match(self):
        """Record a successful match."""
        self.total_comparisons += 1
        self.matches += 1

    def add_mismatch(self, iteration: int, old_output: Any, new_output: Any, reason: str):
        """Record a mismatch with details."""
        self.total_comparisons += 1
        self.mismatches += 1
        self.mismatch_details.append({
            "iteration": iteration,
            "old_output": old_output,
            "new_output": new_output,
            "reason": reason
        })

    def add_error(self):
        """Record a comparison error."""
        self.errors += 1

    def get_equivalence_rate(self) -> float:
        """Calculate equivalence rate (0.0-1.0)."""
        if self.total_comparisons == 0:
            return 0.0
        return self.matches / self.total_comparisons

    def meets_threshold(self, threshold: float) -> bool:
        """Check if equivalence rate meets threshold."""
        return self.get_equivalence_rate() >= threshold


def load_json_logs(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load generation logs from JSON or JSONL file.

    Args:
        file_path: Path to log file

    Returns:
        List of log entries (dicts)

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Log file not found: {file_path}")

    with open(file_path, 'r') as f:
        content = f.read().strip()

        # Try parsing as JSON array first
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
        except json.JSONDecodeError:
            pass

        # Try parsing as JSONL (newline-delimited JSON)
        logs = []
        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            if not line:
                continue
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping invalid JSON at line {line_num}: {e}", file=sys.stderr)

        if logs:
            return logs

        # If we get here, file contains invalid JSON
        raise json.JSONDecodeError(
            f"File contains invalid JSON/JSONL format",
            content,
            0
        )


def compare_outputs(
    old_logs: List[Dict[str, Any]],
    new_logs: List[Dict[str, Any]]
) -> ComparisonResult:
    """
    Compare outputs between old and new implementations.

    Args:
        old_logs: Logs from Phase 1/2 implementation
        new_logs: Logs from Phase 3 Strategy Pattern implementation

    Returns:
        ComparisonResult object with detailed comparison metrics
    """
    result = ComparisonResult()

    # Check if log counts match
    if len(old_logs) != len(new_logs):
        print(
            f"Warning: Log count mismatch - Old: {len(old_logs)}, New: {len(new_logs)}",
            file=sys.stderr
        )

    # Compare each pair of logs
    for i, (old_entry, new_entry) in enumerate(zip(old_logs, new_logs)):
        iteration = i + 1

        # Extract key fields for comparison
        try:
            old_code = old_entry.get('strategy_code')
            new_code = new_entry.get('strategy_code')

            old_method = old_entry.get('generation_method')
            new_method = new_entry.get('generation_method')

            old_success = old_entry.get('success', True)
            new_success = new_entry.get('success', True)

            # Compare generation method
            if old_method != new_method:
                result.add_mismatch(
                    iteration,
                    old_method,
                    new_method,
                    f"Generation method mismatch: {old_method} vs {new_method}"
                )
                continue

            # Compare success status
            if old_success != new_success:
                result.add_mismatch(
                    iteration,
                    old_success,
                    new_success,
                    f"Success status mismatch: {old_success} vs {new_success}"
                )
                continue

            # Compare strategy code (if both succeeded)
            if old_success and new_success:
                if old_code != new_code:
                    result.add_mismatch(
                        iteration,
                        old_code[:100] + "..." if old_code and len(old_code) > 100 else old_code,
                        new_code[:100] + "..." if new_code and len(new_code) > 100 else new_code,
                        "Strategy code mismatch"
                    )
                    continue

            # If we reach here, the outputs match
            result.add_match()

        except Exception as e:
            print(f"Error comparing iteration {iteration}: {e}", file=sys.stderr)
            result.add_error()

    return result


def generate_report(result: ComparisonResult, threshold: float) -> str:
    """
    Generate human-readable comparison report.

    Args:
        result: ComparisonResult object
        threshold: Equivalence threshold

    Returns:
        Formatted report string
    """
    equivalence_rate = result.get_equivalence_rate()
    meets_threshold = result.meets_threshold(threshold)

    report = []
    report.append("=" * 80)
    report.append("SHADOW MODE COMPARISON REPORT")
    report.append("=" * 80)
    report.append("")
    report.append(f"Total Comparisons: {result.total_comparisons}")
    report.append(f"Matches:           {result.matches}")
    report.append(f"Mismatches:        {result.mismatches}")
    report.append(f"Errors:            {result.errors}")
    report.append("")
    report.append(f"Equivalence Rate:  {equivalence_rate:.2%}")
    report.append(f"Threshold:         {threshold:.2%}")
    report.append(f"Status:            {'✅ PASS' if meets_threshold else '❌ FAIL'}")
    report.append("")

    if result.mismatches > 0:
        report.append("MISMATCH DETAILS:")
        report.append("-" * 80)
        for detail in result.mismatch_details:
            report.append(f"Iteration {detail['iteration']}: {detail['reason']}")
            report.append(f"  Old: {detail['old_output']}")
            report.append(f"  New: {detail['new_output']}")
            report.append("")

    report.append("=" * 80)

    return "\n".join(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compare shadow mode outputs between Phase 1/2 and Phase 3 implementations"
    )
    parser.add_argument(
        "--old",
        required=True,
        type=Path,
        help="Path to Phase 1/2 generation logs (JSON/JSONL)"
    )
    parser.add_argument(
        "--new",
        required=True,
        type=Path,
        help="Path to Phase 3 Strategy Pattern generation logs (JSON/JSONL)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.95,
        help="Equivalence threshold (0.0-1.0, default: 0.95)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file for comparison report (default: stdout)"
    )

    args = parser.parse_args()

    # Validate threshold
    if not 0.0 <= args.threshold <= 1.0:
        print("Error: Threshold must be between 0.0 and 1.0", file=sys.stderr)
        return 2

    try:
        # Load logs
        print(f"Loading old logs from: {args.old}", file=sys.stderr)
        old_logs = load_json_logs(args.old)
        print(f"Loaded {len(old_logs)} entries from old logs", file=sys.stderr)

        print(f"Loading new logs from: {args.new}", file=sys.stderr)
        new_logs = load_json_logs(args.new)
        print(f"Loaded {len(new_logs)} entries from new logs", file=sys.stderr)

        # Compare outputs
        print("Comparing outputs...", file=sys.stderr)
        result = compare_outputs(old_logs, new_logs)

        # Generate report
        report = generate_report(result, args.threshold)

        # Output report
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"Report written to: {args.output}", file=sys.stderr)
        else:
            print(report)

        # Return appropriate exit code
        if result.meets_threshold(args.threshold):
            print("\n✅ Shadow mode validation PASSED", file=sys.stderr)
            return 0
        else:
            print(f"\n❌ Shadow mode validation FAILED: Equivalence rate {result.get_equivalence_rate():.2%} below threshold {args.threshold:.2%}", file=sys.stderr)
            return 1

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
