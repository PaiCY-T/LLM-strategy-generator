"""
Code execution sandbox with resource limits.

Provides safe execution environment for user-provided strategy code
with memory limits, CPU time limits, and timeout protection.
"""

import logging
import resource
import signal
import sys
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# Safe builtins for code execution
SAFE_BUILTINS = {
    'abs': abs,
    'all': all,
    'any': any,
    'bool': bool,
    'dict': dict,
    'enumerate': enumerate,
    'filter': filter,
    'float': float,
    'int': int,
    'len': len,
    'list': list,
    'map': map,
    'max': max,
    'min': min,
    'range': range,
    'round': round,
    'set': set,
    'sorted': sorted,
    'str': str,
    'sum': sum,
    'tuple': tuple,
    'type': type,
    'zip': zip,
    # Allow print for debugging
    'print': print,
    # Required for Python internals
    'None': None,
    'True': True,
    'False': False,
}


class TimeoutError(Exception):
    """Raised when code execution exceeds timeout limit."""
    pass


class MemoryLimitError(Exception):
    """Raised when code execution exceeds memory limit."""
    pass


def _timeout_handler(signum: int, frame: Any) -> None:
    """Signal handler for timeout alarm.

    Args:
        signum: Signal number
        frame: Current stack frame

    Raises:
        TimeoutError: Always raised to interrupt execution
    """
    raise TimeoutError("Code execution exceeded timeout limit")


def execute_with_limits(
    code: str,
    timeout: int = 120,
    memory_limit_mb: int = 500,
    globals_dict: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute code with resource limits.

    Executes user-provided code in a restricted environment with:
    - Memory limit (default 500MB)
    - CPU time limit (matches timeout)
    - Wall clock timeout (default 120s)
    - Restricted builtins (no file I/O, no dangerous operations)

    Args:
        code: Python code string to execute
        timeout: Maximum execution time in seconds (default: 120)
        memory_limit_mb: Maximum memory usage in MB (default: 500)
        globals_dict: Optional custom globals dictionary

    Returns:
        Dictionary of globals after execution

    Raises:
        TimeoutError: If execution exceeds timeout
        MemoryLimitError: If execution exceeds memory limit
        Exception: Any exception raised by the executed code

    Example:
        >>> code = "result = 2 + 2"
        >>> result = execute_with_limits(code, timeout=10)
        >>> result['result']
        4
    """
    # Skip resource limits on Windows (not supported)
    is_windows = sys.platform.startswith('win')

    # Warn about Windows platform limitations
    if is_windows:
        logger.warning(
            "Running on Windows platform. Resource limits (memory, CPU time, "
            "timeout) are not enforced. Strategy code will run without "
            "resource protection."
        )

    # Set up execution environment
    if globals_dict is None:
        globals_dict = {}

    # Add safe builtins
    globals_dict['__builtins__'] = SAFE_BUILTINS

    # Store original signal handler
    original_handler = signal.signal(signal.SIGALRM, _timeout_handler)

    try:
        # Set resource limits (Unix/Linux only)
        if not is_windows:
            # Set memory limit
            memory_bytes = memory_limit_mb * 1024 * 1024
            try:
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (memory_bytes, memory_bytes)
                )
            except (ValueError, OSError):
                # Some systems don't support RLIMIT_AS
                # Fall back to RLIMIT_DATA if available
                try:
                    resource.setrlimit(
                        resource.RLIMIT_DATA,
                        (memory_bytes, memory_bytes)
                    )
                except (ValueError, OSError):
                    # Resource limits not available on this system
                    pass

            # Set CPU time limit
            try:
                resource.setrlimit(
                    resource.RLIMIT_CPU,
                    (timeout, timeout)
                )
            except (ValueError, OSError):
                # CPU time limits not available
                pass

        # Set timeout alarm (Unix/Linux only)
        if not is_windows:
            signal.alarm(timeout)

        # Execute code
        try:
            exec(code, globals_dict)
        except MemoryError:
            raise MemoryLimitError(
                f"Code execution exceeded memory limit of {memory_limit_mb}MB"
            )

    finally:
        # Cancel alarm
        if not is_windows:
            signal.alarm(0)

        # Restore original signal handler
        signal.signal(signal.SIGALRM, original_handler)

        # Reset resource limits (Unix/Linux only)
        if not is_windows:
            try:
                # Reset to unlimited
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (resource.RLIM_INFINITY, resource.RLIM_INFINITY)
                )
            except (ValueError, OSError):
                pass

            try:
                resource.setrlimit(
                    resource.RLIMIT_CPU,
                    (resource.RLIM_INFINITY, resource.RLIM_INFINITY)
                )
            except (ValueError, OSError):
                pass

    return globals_dict


def create_safe_globals() -> Dict[str, Any]:
    """Create a safe globals dictionary for code execution.

    Returns:
        Dictionary with safe builtins and common imports
    """
    safe_globals: Dict[str, Any] = {
        '__builtins__': SAFE_BUILTINS,
    }

    # Try to import allowed modules
    try:
        import pandas as pd  # noqa: F401
        safe_globals['pd'] = pd
        safe_globals['pandas'] = pd
    except ImportError:
        pass

    try:
        import numpy as np  # noqa: F401
        safe_globals['np'] = np
        safe_globals['numpy'] = np
    except ImportError:
        pass

    try:
        import datetime  # noqa: F401
        safe_globals['datetime'] = datetime
    except ImportError:
        pass

    return safe_globals
