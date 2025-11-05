#!/usr/bin/env python3
"""
Rollback Champion CLI Tool
===========================

Command-line interface for rolling back to previous champion strategies.

Features:
    - List available champion history
    - Rollback to a specific iteration
    - Validate rollback candidates
    - Audit trail of rollback operations

Usage:
    # List available champions
    python rollback_champion.py --list-history

    # Rollback to specific iteration
    python rollback_champion.py --target-iteration 5 --reason "Production issue" --operator "john@example.com"

    # Rollback without validation (fast but risky)
    python rollback_champion.py --target-iteration 5 --reason "Emergency" --operator "ops" --no-validate
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Optional

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'artifacts', 'working', 'modules'))
sys.path.insert(0, os.path.dirname(__file__))

from src.repository.hall_of_fame import HallOfFameRepository
from src.recovery.rollback_manager import RollbackManager


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for rollback operations.

    Args:
        verbose: Enable verbose logging

    Returns:
        Configured logger
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f"rollback_{timestamp}.log")

    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Log file: {log_file}")

    return logger


def load_finlab_data():
    """Load real Finlab data for validation.

    Returns:
        Finlab data object with Taiwan stock market data

    Raises:
        ValueError: If FINLAB_API_TOKEN environment variable not set
        Exception: If data loading fails
    """
    try:
        import finlab
        from finlab import data

        # Login with API token
        api_token = os.getenv("FINLAB_API_TOKEN")
        if not api_token:
            raise ValueError(
                "FINLAB_API_TOKEN environment variable not set. "
                "Cannot validate rollback without data."
            )

        finlab.login(api_token)

        logger = logging.getLogger(__name__)
        logger.info("✅ Finlab data loaded successfully")

        return data

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to load Finlab data: {e}")
        raise


def list_champion_history(rollback_mgr: RollbackManager, limit: int = 20) -> None:
    """Display champion history in readable format.

    Args:
        rollback_mgr: RollbackManager instance
        limit: Maximum number of champions to display
    """
    print("\n" + "=" * 80)
    print("CHAMPION HISTORY")
    print("=" * 80)

    champions = rollback_mgr.get_champion_history(limit=limit)

    if not champions:
        print("\n⚠️  No champions found in Hall of Fame")
        print("   Run some iterations first to generate champion strategies\n")
        return

    print(f"\nFound {len(champions)} champion strategies:\n")
    print(f"{'Iter':<6} {'Sharpe':<8} {'Return':<10} {'Timestamp':<20} {'Patterns':<8}")
    print("-" * 80)

    for champ in champions:
        sharpe = champ.metrics.get('sharpe_ratio', 0)
        total_return = champ.metrics.get('total_return', 0)
        annual_return = champ.metrics.get('annual_return', 0)

        # Use annual_return if available, else total_return
        return_val = annual_return if annual_return != 0 else total_return

        # Format timestamp (show date and time)
        try:
            dt = datetime.fromisoformat(champ.timestamp)
            ts_str = dt.strftime('%Y-%m-%d %H:%M')
        except (ValueError, AttributeError):
            ts_str = champ.timestamp[:19] if len(champ.timestamp) >= 19 else champ.timestamp

        pattern_count = len(champ.success_patterns)

        print(f"{champ.iteration_num:<6} {sharpe:<8.4f} {return_val:<10.2%} {ts_str:<20} {pattern_count:<8}")

    print("\n" + "=" * 80)
    print("\nTo rollback to a specific iteration, use:")
    print("  python rollback_champion.py --target-iteration <N> --reason \"<reason>\" --operator \"<email>\"")
    print()


def confirm_rollback(target_iteration: int, reason: str, operator: str, validate: bool) -> bool:
    """Prompt user for rollback confirmation.

    Args:
        target_iteration: Target iteration to rollback to
        reason: Rollback reason
        operator: Operator name/email
        validate: Whether validation will be performed

    Returns:
        True if user confirms, False otherwise
    """
    print("\n" + "=" * 80)
    print("ROLLBACK CONFIRMATION")
    print("=" * 80)
    print(f"\nTarget iteration: {target_iteration}")
    print(f"Reason:           {reason}")
    print(f"Operator:         {operator}")
    print(f"Validation:       {'Yes' if validate else 'No (RISKY!)'}")

    if not validate:
        print("\n⚠️  WARNING: Validation disabled - rollback will NOT be tested before activation!")
        print("   This is faster but risks deploying a broken strategy.")

    print()
    response = input("Proceed with rollback? (yes/no): ").strip().lower()

    return response in ['yes', 'y']


def perform_rollback(
    rollback_mgr: RollbackManager,
    target_iteration: int,
    reason: str,
    operator: str,
    data: Optional[any],
    validate: bool = True,
    skip_confirmation: bool = False
) -> bool:
    """Perform rollback operation.

    Args:
        rollback_mgr: RollbackManager instance
        target_iteration: Target iteration to rollback to
        reason: Rollback reason
        operator: Operator name/email
        data: Finlab data for validation (None if --no-validate)
        validate: Whether to validate rollback candidate
        skip_confirmation: Skip user confirmation (for scripting)

    Returns:
        True if rollback succeeded, False otherwise
    """
    logger = logging.getLogger(__name__)

    # User confirmation (unless skipped)
    if not skip_confirmation:
        if not confirm_rollback(target_iteration, reason, operator, validate):
            print("\n❌ Rollback cancelled by user")
            return False

    print("\n" + "=" * 80)
    print("PERFORMING ROLLBACK")
    print("=" * 80)

    # Perform rollback
    print(f"\nRolling back to iteration {target_iteration}...")

    start_time = datetime.now()

    success, message = rollback_mgr.rollback_to_iteration(
        target_iteration=target_iteration,
        reason=reason,
        operator=operator,
        data=data,
        validate=validate
    )

    elapsed = (datetime.now() - start_time).total_seconds()

    if success:
        print(f"\n✅ {message}")
        print(f"   Time taken: {elapsed:.1f}s")

        # Show rollback record
        history = rollback_mgr.get_rollback_history(limit=1)
        if history:
            record = history[0]
            print(f"\n📋 Rollback record:")
            print(f"   ID: {record.rollback_id}")
            print(f"   From iteration: {record.from_iteration}")
            print(f"   To iteration: {record.to_iteration}")
            print(f"   Timestamp: {record.timestamp}")

            if validate and record.validation_report:
                report = record.validation_report
                if 'current_sharpe' in report:
                    print(f"   Validation: Sharpe {report['current_sharpe']:.4f}")
                    if 'original_sharpe' in report:
                        print(f"               (original: {report['original_sharpe']:.4f})")

        print()
        logger.info(f"Rollback successful: {message}")
        return True

    else:
        print(f"\n❌ Rollback failed: {message}")
        print()
        logger.error(f"Rollback failed: {message}")
        return False


def main():
    """Main entry point for rollback CLI."""
    parser = argparse.ArgumentParser(
        description="Rollback to previous champion strategies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List champion history
  python rollback_champion.py --list-history

  # Rollback with validation
  python rollback_champion.py --target-iteration 5 --reason "Production bug" --operator "john@example.com"

  # Emergency rollback without validation (fast but risky)
  python rollback_champion.py --target-iteration 5 --reason "Emergency" --operator "ops" --no-validate

  # Automated rollback (skip confirmation)
  python rollback_champion.py --target-iteration 5 --reason "Automated" --operator "system" --yes
        """
    )

    # Operation mode
    parser.add_argument(
        '--list-history',
        action='store_true',
        help="List available champion strategies"
    )

    # Rollback parameters
    parser.add_argument(
        '--target-iteration',
        type=int,
        help="Iteration number to rollback to"
    )

    parser.add_argument(
        '--reason',
        type=str,
        help="Reason for rollback (required for rollback operation)"
    )

    parser.add_argument(
        '--operator',
        type=str,
        default=os.getenv('USER', 'system'),
        help="Name or email of operator performing rollback (default: current user)"
    )

    # Validation control
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help="Skip validation (faster but risky - not recommended)"
    )

    # Automation support
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help="Skip confirmation prompt (for automation)"
    )

    # Display options
    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help="Maximum number of champions to display (default: 20)"
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(verbose=args.verbose)

    try:
        # Initialize Hall of Fame and Rollback Manager
        print("\n🔧 Initializing rollback system...")
        hall_of_fame = HallOfFameRepository()
        rollback_mgr = RollbackManager(hall_of_fame)
        print("✅ System initialized\n")

        # List history mode
        if args.list_history:
            list_champion_history(rollback_mgr, limit=args.limit)
            sys.exit(0)

        # Rollback mode - validate arguments
        if args.target_iteration is None:
            print("❌ Error: --target-iteration is required for rollback operation")
            print("   Use --list-history to see available iterations")
            parser.print_help()
            sys.exit(1)

        if args.reason is None:
            print("❌ Error: --reason is required for rollback operation")
            print("   Example: --reason \"Production bug fix\"")
            parser.print_help()
            sys.exit(1)

        # Load data if validation enabled
        data = None
        validate = not args.no_validate

        if validate:
            print("📊 Loading Finlab data for validation...")
            try:
                data = load_finlab_data()
            except Exception as e:
                print(f"\n❌ Failed to load data: {e}")
                print("\nOptions:")
                print("  1. Set FINLAB_API_TOKEN environment variable")
                print("  2. Use --no-validate flag (risky, not recommended)")
                sys.exit(1)
        else:
            print("⚠️  Validation disabled - rollback will NOT be tested!")

        # Perform rollback
        success = perform_rollback(
            rollback_mgr=rollback_mgr,
            target_iteration=args.target_iteration,
            reason=args.reason,
            operator=args.operator,
            data=data,
            validate=validate,
            skip_confirmation=args.yes
        )

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(2)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ Unexpected error: {e}")
        print("   Check logs for details")
        sys.exit(3)


if __name__ == '__main__':
    main()
