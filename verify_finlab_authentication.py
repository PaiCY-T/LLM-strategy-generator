#!/usr/bin/env python3
"""
Phase 2 Task 6.2: Verify Finlab Session Authentication

This script verifies that the finlab session is authenticated and can access data
before running backtest execution. It's a critical setup validation step.

Purpose:
    - Test finlab module accessibility
    - Verify data.get() works
    - Confirm sim() function is available
    - Provide clear diagnostics if authentication fails

Usage:
    python verify_finlab_authentication.py [--data-key KEY] [--quiet] [--json]

Examples:
    python verify_finlab_authentication.py
    python verify_finlab_authentication.py --data-key 'price:收盤價'
    python verify_finlab_authentication.py --quiet --json
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from backtest.finlab_authenticator import verify_finlab_session
import json


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Verify finlab session authentication (Phase 2 Task 6.2)',
        epilog="""
Examples:
  python verify_finlab_authentication.py
  python verify_finlab_authentication.py --data-key 'price:收盤價'
  python verify_finlab_authentication.py --json --quiet
        """
    )
    parser.add_argument(
        '--data-key',
        default='etl:adj_close',
        help='Data key to test for access (default: etl:adj_close)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON for programmatic use'
    )

    args = parser.parse_args()

    # Run authentication verification
    status = verify_finlab_session(test_data_key=args.data_key, verbose=not args.quiet)

    # Output as JSON if requested
    if args.json:
        output = status.to_dict()
        print(json.dumps(output, indent=2))

    # Exit with appropriate code
    exit_code = 0 if status.is_authenticated else 1
    if not args.quiet:
        if exit_code == 0:
            print("\n✅ SUCCESS: finlab session is ready for backtest execution!")
        else:
            print("\n❌ FAILURE: finlab session authentication failed.")
            print("   Please review the diagnostics above and troubleshooting steps.")

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
