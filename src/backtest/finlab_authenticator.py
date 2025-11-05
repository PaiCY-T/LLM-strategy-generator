"""
Finlab Session Authentication Verifier

This module provides verification functions to ensure finlab session is properly
authenticated and can access data before executing backtest operations.

Key Functions:
    - verify_finlab_session(): Main verification function
    - check_data_access(): Verify data.get() works
    - check_sim_availability(): Verify sim function exists
    - get_authentication_status(): Get current authentication status

Purpose:
    Setup validation before running backtest execution to ensure:
    - finlab module is accessible
    - Session is authenticated
    - Data access works (data.get() returns data)
    - sim() function is available for backtesting
"""

import sys
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AuthenticationStatus:
    """Status result from authentication verification.

    Attributes:
        is_authenticated: Whether session is fully authenticated
        timestamp: When verification was performed
        finlab_available: Whether finlab module can be imported
        data_accessible: Whether data.get() works
        sim_available: Whether sim function is callable
        error_message: Error details if authentication failed
        diagnostics: List of diagnostic messages for troubleshooting
    """
    is_authenticated: bool
    timestamp: datetime
    finlab_available: bool
    data_accessible: bool
    sim_available: bool
    error_message: Optional[str] = None
    diagnostics: List[str] = None

    def __post_init__(self):
        if self.diagnostics is None:
            self.diagnostics = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'is_authenticated': self.is_authenticated,
            'timestamp': self.timestamp.isoformat(),
            'finlab_available': self.finlab_available,
            'data_accessible': self.data_accessible,
            'sim_available': self.sim_available,
            'error_message': self.error_message,
            'diagnostics': self.diagnostics
        }


def check_finlab_importable() -> Tuple[bool, Optional[str]]:
    """Check if finlab module can be imported.

    Returns:
        Tuple of (can_import, error_message)
        error_message is None if successful
    """
    try:
        import finlab
        logger.debug(f"✅ finlab module imported successfully")
        return True, None
    except ImportError as e:
        error_msg = f"Failed to import finlab: {e}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error importing finlab: {type(e).__name__}: {e}"
        logger.error(error_msg)
        return False, error_msg


def check_data_access(test_data_key: str = 'etl:adj_close') -> Tuple[bool, Optional[str], Optional[Any]]:
    """Verify finlab.data is accessible and can retrieve data.

    Args:
        test_data_key: Data key to test with (default: 'etl:adj_close')

    Returns:
        Tuple of (success, error_message, sample_data_shape)
        error_message is None if successful
        sample_data_shape is (rows, cols) if successful, None otherwise
    """
    try:
        # Import finlab and data module
        from finlab import data
        logger.debug(f"✅ finlab.data imported successfully")

        # Attempt to get sample data
        logger.debug(f"Testing data.get('{test_data_key}')...")
        sample_data = data.get(test_data_key)

        if sample_data is None:
            error_msg = f"data.get('{test_data_key}') returned None"
            logger.error(error_msg)
            return False, error_msg, None

        # Verify data has shape (is a DataFrame or Series)
        if not hasattr(sample_data, 'shape'):
            error_msg = f"data.get('{test_data_key}') did not return a DataFrame/Series"
            logger.error(error_msg)
            return False, error_msg, None

        data_shape = sample_data.shape
        logger.info(f"✅ Data access verified! Retrieved {data_shape} data")
        return True, None, data_shape

    except ImportError as e:
        error_msg = f"Failed to import finlab.data: {e}"
        logger.error(error_msg)
        return False, error_msg, None

    except KeyError as e:
        error_msg = f"Data key '{test_data_key}' not found: {e}"
        logger.error(error_msg)
        return False, error_msg, None

    except Exception as e:
        error_msg = f"Error accessing finlab data: {type(e).__name__}: {e}"
        logger.error(error_msg)
        return False, error_msg, None


def check_sim_availability() -> Tuple[bool, Optional[str]]:
    """Verify finlab.backtest.sim function is available and callable.

    Returns:
        Tuple of (sim_available, error_message)
        error_message is None if successful
    """
    try:
        # Import finlab and backtest module
        from finlab import backtest
        logger.debug(f"✅ finlab.backtest imported successfully")

        # Check if sim function exists
        if not hasattr(backtest, 'sim'):
            error_msg = "finlab.backtest module has no 'sim' attribute"
            logger.error(error_msg)
            return False, error_msg

        # Check if sim is callable
        if not callable(backtest.sim):
            error_msg = "finlab.backtest.sim is not callable"
            logger.error(error_msg)
            return False, error_msg

        logger.info(f"✅ sim() function verified and callable")
        return True, None

    except ImportError as e:
        error_msg = f"Failed to import finlab.backtest: {e}"
        logger.error(error_msg)
        return False, error_msg

    except Exception as e:
        error_msg = f"Error checking sim availability: {type(e).__name__}: {e}"
        logger.error(error_msg)
        return False, error_msg


def get_authentication_status(test_data_key: str = 'etl:adj_close') -> AuthenticationStatus:
    """Get comprehensive authentication and data access status.

    Args:
        test_data_key: Data key to test with

    Returns:
        AuthenticationStatus object with detailed status information
    """
    diagnostics: List[str] = []
    timestamp = datetime.now()

    # Check 1: finlab module importable
    logger.info("=" * 60)
    logger.info("FINLAB SESSION AUTHENTICATION CHECK")
    logger.info("=" * 60)

    finlab_available, finlab_error = check_finlab_importable()
    if finlab_available:
        diagnostics.append("✅ finlab module is importable")
    else:
        diagnostics.append(f"❌ {finlab_error}")

    # Check 2: data access
    data_accessible = False
    data_shape = None
    if finlab_available:
        data_accessible, data_error, data_shape = check_data_access(test_data_key)
        if data_accessible:
            diagnostics.append(f"✅ finlab.data accessible (shape: {data_shape})")
        else:
            diagnostics.append(f"❌ {data_error}")
    else:
        diagnostics.append("⚠️  Skipping data access check (finlab not available)")

    # Check 3: sim availability
    sim_available = False
    if finlab_available:
        sim_available, sim_error = check_sim_availability()
        if sim_available:
            diagnostics.append("✅ finlab.backtest.sim() is available and callable")
        else:
            diagnostics.append(f"❌ {sim_error}")
    else:
        diagnostics.append("⚠️  Skipping sim check (finlab not available)")

    # Determine overall authentication status
    is_authenticated = finlab_available and data_accessible and sim_available

    # Build error message if authentication failed
    error_message = None
    if not is_authenticated:
        failed_checks = []
        if not finlab_available:
            failed_checks.append("finlab module not available")
        if not data_accessible:
            failed_checks.append("data access not working")
        if not sim_available:
            failed_checks.append("sim function not available")
        error_message = "Authentication failed: " + ", ".join(failed_checks)

    return AuthenticationStatus(
        is_authenticated=is_authenticated,
        timestamp=timestamp,
        finlab_available=finlab_available,
        data_accessible=data_accessible,
        sim_available=sim_available,
        error_message=error_message,
        diagnostics=diagnostics
    )


def verify_finlab_session(test_data_key: str = 'etl:adj_close', verbose: bool = True) -> AuthenticationStatus:
    """Main verification function for finlab session authentication.

    This is the primary entry point for verifying finlab is properly setup
    before attempting to run backtest execution.

    Args:
        test_data_key: Data key to test data access with
        verbose: Whether to print detailed status output

    Returns:
        AuthenticationStatus with authentication result and diagnostics
    """
    status = get_authentication_status(test_data_key)

    if verbose:
        # Print results
        print("\n" + "=" * 60)
        print("FINLAB SESSION AUTHENTICATION VERIFICATION")
        print("=" * 60)
        print(f"\nTimestamp: {status.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Overall Status: {'✅ AUTHENTICATED' if status.is_authenticated else '❌ NOT AUTHENTICATED'}\n")

        print("Component Checks:")
        print(f"  - finlab module:     {'✅ Available' if status.finlab_available else '❌ Not Available'}")
        print(f"  - data access:       {'✅ Working' if status.data_accessible else '❌ Not Working'}")
        print(f"  - sim function:      {'✅ Available' if status.sim_available else '❌ Not Available'}")

        if status.diagnostics:
            print("\nDiagnostics:")
            for diag in status.diagnostics:
                print(f"  {diag}")

        if status.error_message:
            print(f"\nError: {status.error_message}")

        print("\nTroubleshooting:")
        if not status.finlab_available:
            print("  - Ensure finlab is installed: pip install finlab")
            print("  - Verify PYTHONPATH includes finlab installation")
            print("  - Check for finlab import errors in logs")

        if not status.data_accessible:
            print("  - Verify finlab authentication/login is complete")
            print("  - Check that credentials are properly set")
            print("  - Verify network connectivity to finlab servers")
            print("  - Check that the data key exists and is accessible")

        if not status.sim_available:
            print("  - Verify finlab.backtest module is properly installed")
            print("  - Check for any API version mismatches")

        print("\n" + "=" * 60)

    return status


def main():
    """Command-line entry point for finlab authentication verification."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Verify finlab session authentication and data access'
    )
    parser.add_argument(
        '--data-key',
        default='etl:adj_close',
        help='Data key to test (default: etl:adj_close)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    args = parser.parse_args()

    # Run verification
    status = verify_finlab_session(test_data_key=args.data_key, verbose=not args.quiet)

    # Output JSON if requested
    if args.json:
        import json
        print(json.dumps(status.to_dict(), indent=2))

    # Exit with appropriate code
    sys.exit(0 if status.is_authenticated else 1)


if __name__ == '__main__':
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    main()
