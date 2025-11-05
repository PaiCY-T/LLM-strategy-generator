#!/usr/bin/env python3
"""
Quick Strategy File Verification Script

Standalone script for Phase 2 Task 6.1 verification.
Can be used before running backtest execution to ensure strategy files exist.

Usage:
    python3 scripts/verify_strategy_files.py                 # Default behavior
    python3 scripts/verify_strategy_files.py --json          # JSON output
    python3 scripts/verify_strategy_files.py --summary-only  # Brief summary
"""

import os
import json
import sys
from pathlib import Path


def get_file_count(directory, pattern):
    """Count files matching pattern in directory."""
    path = Path(directory)
    if not path.exists():
        return 0
    return len(list(path.glob(pattern)))


def check_file_readable(filepath):
    """Check if file is readable."""
    try:
        with open(filepath, 'r') as f:
            f.read(100)
        return True
    except Exception:
        return False


def verify_strategies(project_root=None):
    """
    Quick verification of strategy files.

    Returns:
        dict with verification results
    """
    if project_root is None:
        project_root = os.getcwd()

    project_path = Path(project_root)

    results = {
        'project_root': str(project_path),
        'loop_iterations': 0,
        'fixed_iterations': 0,
        'loop_accessible': 0,
        'fixed_accessible': 0,
        'innovations_exists': False,
        'innovations_readable': False,
        'innovations_size': 0,
        'total_strategies': 0,
        'total_accessible': 0,
    }

    # Count loop iteration files
    loop_files = sorted(project_path.glob('generated_strategy_loop_iter*.py'))
    results['loop_iterations'] = len(loop_files)
    results['loop_accessible'] = sum(1 for f in loop_files if check_file_readable(f))

    # Count fixed iteration files
    fixed_files = sorted(project_path.glob('generated_strategy_fixed_iter*.py'))
    results['fixed_iterations'] = len(fixed_files)
    results['fixed_accessible'] = sum(1 for f in fixed_files if check_file_readable(f))

    # Check innovations file
    innovations_path = project_path / 'artifacts' / 'data' / 'innovations.jsonl'
    if innovations_path.exists():
        results['innovations_exists'] = True
        results['innovations_size'] = innovations_path.stat().st_size
        results['innovations_readable'] = check_file_readable(innovations_path)

    # Totals
    results['total_strategies'] = results['loop_iterations'] + results['fixed_iterations']
    results['total_accessible'] = results['loop_accessible'] + results['fixed_accessible']

    # Status determination
    if results['total_strategies'] == 0:
        results['status'] = 'FAILED'
        results['message'] = 'No strategy files found'
    elif results['total_accessible'] < results['total_strategies']:
        results['status'] = 'PARTIAL'
        results['message'] = f'Found {results["total_strategies"]} strategies but {results["total_strategies"] - results["total_accessible"]} are inaccessible'
    else:
        results['status'] = 'SUCCESS'
        results['message'] = f'Successfully verified {results["total_strategies"]} accessible strategy files'

    return results


def print_report(results):
    """Print human-readable report."""
    print("=" * 70)
    print("STRATEGY FILE VERIFICATION REPORT")
    print("=" * 70)
    print()
    print(f"Status: {results['status']}")
    print(f"Message: {results['message']}")
    print()
    print("STRATEGY FILES:")
    print(f"  Loop iterations: {results['loop_accessible']}/{results['loop_iterations']} accessible")
    print(f"  Fixed iterations: {results['fixed_accessible']}/{results['fixed_iterations']} accessible")
    print(f"  Total: {results['total_accessible']}/{results['total_strategies']} accessible")
    print()
    print("INNOVATIONS FILE:")
    print(f"  Exists: {results['innovations_exists']}")
    print(f"  Readable: {results['innovations_readable']}")
    print(f"  Size: {results['innovations_size']} bytes")
    print()
    print("RESULT: Ready for backtest execution" if results['status'] == 'SUCCESS' else "RESULT: Files missing or inaccessible")
    print("=" * 70)


def print_summary(results):
    """Print brief summary."""
    print(f"{results['status']}: {results['total_accessible']}/{results['total_strategies']} strategies available")


def main():
    """Main entry point."""
    project_root = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else None

    # Parse options
    json_output = '--json' in sys.argv
    summary_only = '--summary-only' in sys.argv

    # Run verification
    results = verify_strategies(project_root)

    # Output results
    if json_output:
        print(json.dumps(results, indent=2))
    elif summary_only:
        print_summary(results)
    else:
        print_report(results)

    # Exit with appropriate code
    if results['status'] == 'FAILED':
        return 1
    elif results['status'] == 'PARTIAL':
        return 2
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main())
