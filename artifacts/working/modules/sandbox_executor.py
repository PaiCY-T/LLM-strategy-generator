"""Multiprocessing sandbox for isolated strategy execution.

Executes AI-generated code in isolated process with timeout and resource limits
to prevent infinite loops, memory exhaustion, or system hangs.

Features:
- Process isolation via multiprocessing.Process
- Timeout protection with process termination
- Memory limit monitoring (Unix only)
- Return value capture via multiprocessing.Queue
- Error capture with stack traces
- Resource cleanup on timeout/error

Platform compatibility:
- Timeout: Cross-platform (Windows, Unix)
- Memory limits: Unix only (requires resource module)
"""

import multiprocessing
import time
import traceback
import pandas as pd
from typing import Dict, Any, Optional
import sys


def _execute_code_in_process(
    code: str,
    result_queue: multiprocessing.Queue,
    timeout: int,
    memory_limit_mb: int = 8192,
    data_wrapper = None,  # PreloadedData wrapper (picklable)
    validate_only: bool = False  # NEW: Fast validation mode (no sim() call)
) -> None:
    """Execute code in child process and return signal via queue.

    This function runs in the child process. It executes the strategy code,
    extracts the 'signal' variable from the namespace, and puts the result
    in the queue for the parent process to retrieve.

    Args:
        code: Strategy code to execute
        result_queue: Queue for returning results to parent
        timeout: Timeout value (for error messages)
        data_wrapper: PreloadedData wrapper with datasets (avoids expensive import)
        validate_only: If True, only validate code and generate signal (no backtest)
    """
    start_time = time.time()

    try:
        # Set memory limit (Unix only)
        if sys.platform != 'win32':
            try:
                import resource
                # Set memory limit based on parameter (soft and hard limits)
                memory_limit_bytes = memory_limit_mb * 1024 * 1024
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (memory_limit_bytes, memory_limit_bytes)
                )
            except ImportError:
                # resource module not available
                pass
            except Exception as e:
                # Memory limit setting failed, continue without it
                pass

        # Use preloaded data wrapper if provided (avoids 10+ minute data load)
        # Otherwise import fresh (fallback for standalone usage)
        if data_wrapper is None:
            from finlab import data
        else:
            data = data_wrapper  # PreloadedData has .get() method just like finlab.data

        # Import sim only if needed (validation mode doesn't need it)
        if validate_only:
            # Validation mode: Only need data access, no backtest execution
            namespace = {
                'data': data,
                '__builtins__': __builtins__  # Provide built-in functions
            }
        else:
            # Full execution mode: Import sim for backtest
            from finlab.backtest import sim
            namespace = {
                'data': data,
                'sim': sim,
                '__builtins__': __builtins__  # Provide built-in functions
            }

        # Execute the code
        exec(code, namespace)

        # Extract signal variable (support two patterns)
        # Pattern 1: Strategy defines 'signal' variable directly
        # Pattern 2: Strategy calls sim() and creates 'report' variable (deprecated but supported)

        if 'signal' in namespace:
            signal = namespace['signal']
        elif 'report' in namespace:
            # Legacy pattern: extract position from report object
            # The strategy called sim() directly, we need to get the original position signal
            error_msg = ('Strategy called sim() directly but should return signal variable. '
                        'Expected: signal = position. Found: report = sim(position, ...)')
            result_queue.put({
                'success': False,
                'signal': None,
                'error': error_msg,
                'execution_time': time.time() - start_time,
                'memory_used_mb': None
            })
            return
        elif 'position' in namespace:
            # Fallback: use 'position' as signal (common naming pattern)
            signal = namespace['position']
        else:
            result_queue.put({
                'success': False,
                'signal': None,
                'error': 'Generated code does not define "signal" or "position" variable',
                'execution_time': time.time() - start_time,
                'memory_used_mb': None
            })
            return

        # Validate signal is a DataFrame
        if not isinstance(signal, pd.DataFrame):
            result_queue.put({
                'success': False,
                'signal': None,
                'error': f'Signal must be pandas DataFrame, got {type(signal).__name__}',
                'execution_time': time.time() - start_time,
                'memory_used_mb': None
            })
            return

        # Get memory usage (Unix only)
        memory_used_mb = None
        if sys.platform != 'win32':
            try:
                import resource
                usage = resource.getrusage(resource.RUSAGE_SELF)
                memory_used_mb = usage.ru_maxrss / 1024  # Convert KB to MB
            except:
                pass

        # Success - return signal
        result_queue.put({
            'success': True,
            'signal': signal,
            'error': None,
            'execution_time': time.time() - start_time,
            'memory_used_mb': memory_used_mb
        })

    except MemoryError:
        result_queue.put({
            'success': False,
            'signal': None,
            'error': f'Memory limit exceeded ({memory_limit_mb}MB)',
            'execution_time': time.time() - start_time,
            'memory_used_mb': None
        })

    except Exception as e:
        # Capture full stack trace
        error_trace = traceback.format_exc()
        result_queue.put({
            'success': False,
            'signal': None,
            'error': f'{type(e).__name__}: {str(e)}\n\nStack trace:\n{error_trace}',
            'execution_time': time.time() - start_time,
            'memory_used_mb': None
        })


def execute_strategy_in_sandbox(
    code: str,
    timeout: int = 300,
    memory_limit_mb: int = 8192,
    data_wrapper = None,  # PreloadedData wrapper (picklable)
    validate_only: bool = False  # NEW: Fast validation mode (no sim() call)
) -> dict:
    """Execute strategy code in isolated process with resource limits.

    Creates a child process to execute the code with timeout protection
    and memory limits. The child process executes the code and extracts
    the 'signal' variable, which must be a pandas DataFrame.

    Platform compatibility:
    - Timeout: Works on Windows and Unix
    - Memory limits: Unix only (ignored on Windows)

    Performance optimization:
    - Pass data_wrapper (PreloadedData) to avoid expensive Finlab imports per iteration
    - Without wrapper, Finlab data import takes 10+ minutes per iteration
    - With wrapper, execution completes in < 1 minute
    - Use validate_only=True for fast validation (30s) without backtest execution

    Args:
        code: Strategy code to execute (must define 'signal' variable)
        timeout: Maximum execution time in seconds (default: 300s = 5 min)
        memory_limit_mb: Memory limit in MB (default: 8192 MB = 8 GB)
                        Only enforced on Unix platforms
        data_wrapper: PreloadedData wrapper with datasets (optional, recommended for performance)
        validate_only: If True, only validate code and generate signal (no backtest, faster)

    Returns:
        Dictionary with keys:
            - success (bool): Whether execution succeeded
            - signal (pd.DataFrame or None): Strategy signal DataFrame
            - error (str or None): Error message if failed
            - execution_time (float): Time taken in seconds
            - memory_used_mb (float or None): Memory used in MB (Unix only)

    Examples:
        >>> from data_wrapper import PreloadedData
        >>> datasets = {'price:收盤價': df_close, 'price:成交股數': df_volume}
        >>> wrapper = PreloadedData(datasets)
        >>> code = '''
        ... close = data.get('price:收盤價')
        ... signal = close.pct_change(20).is_largest(10)
        ... '''
        >>> result = execute_strategy_in_sandbox(code, timeout=60, data_wrapper=wrapper)
        >>> if result['success']:
        ...     print(f"Signal shape: {result['signal'].shape}")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    # Create queue for result passing
    result_queue = multiprocessing.Queue()

    # Create child process
    process = multiprocessing.Process(
        target=_execute_code_in_process,
        args=(code, result_queue, timeout, memory_limit_mb, data_wrapper, validate_only)
    )

    # Start process
    start_time = time.time()
    process.start()

    # Wait for result with timeout
    process.join(timeout=timeout)

    # Check if process is still alive (timeout exceeded)
    if process.is_alive():
        # Timeout exceeded - terminate process
        process.terminate()
        process.join(timeout=5)  # Give it 5 seconds to terminate gracefully

        # Force kill if still alive
        if process.is_alive():
            process.kill()
            process.join()

        # Return timeout error
        return {
            'success': False,
            'signal': None,
            'error': f'Execution timeout exceeded ({timeout}s)',
            'execution_time': timeout,
            'memory_used_mb': None
        }

    # Process finished - get result from queue
    execution_time = time.time() - start_time

    if not result_queue.empty():
        result = result_queue.get()
        # Ensure execution_time is accurate (may have been set in child process)
        result['execution_time'] = execution_time
        return result
    else:
        # No result in queue - process crashed or was killed
        return {
            'success': False,
            'signal': None,
            'error': 'Process terminated unexpectedly (possible memory limit or crash)',
            'execution_time': execution_time,
            'memory_used_mb': None
        }


def main():
    """Test sandbox executor with various scenarios."""
    print("Testing sandbox executor...\n")

    # Test 1: Valid signal
    print("Test 1: Valid signal generation")
    code1 = """
import pandas as pd
signal = pd.DataFrame({'stock': ['AAPL', 'GOOGL'], 'position': [1.0, -1.0]})
"""
    result1 = execute_strategy_in_sandbox(code1, timeout=10)
    print(f"Success: {result1['success']}")
    print(f"Signal shape: {result1['signal'].shape if result1['success'] else 'N/A'}")
    print(f"Execution time: {result1['execution_time']:.2f}s")
    print()

    # Test 2: Missing signal variable
    print("Test 2: Missing signal variable")
    code2 = """
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3]})
"""
    result2 = execute_strategy_in_sandbox(code2, timeout=10)
    print(f"Success: {result2['success']}")
    print(f"Error: {result2['error'][:100] if result2['error'] else 'N/A'}")
    print()

    # Test 3: Invalid signal type
    print("Test 3: Invalid signal type")
    code3 = """
signal = [1, 2, 3]  # Not a DataFrame
"""
    result3 = execute_strategy_in_sandbox(code3, timeout=10)
    print(f"Success: {result3['success']}")
    print(f"Error: {result3['error'][:100] if result3['error'] else 'N/A'}")
    print()

    # Test 4: Execution error
    print("Test 4: Execution error (division by zero)")
    code4 = """
import pandas as pd
x = 1 / 0  # This will raise ZeroDivisionError
signal = pd.DataFrame()
"""
    result4 = execute_strategy_in_sandbox(code4, timeout=10)
    print(f"Success: {result4['success']}")
    print(f"Error type: {result4['error'].split(':')[0] if result4['error'] else 'N/A'}")
    print()

    # Test 5: Timeout (if we want to test, use short timeout)
    print("Test 5: Timeout protection (3 second timeout)")
    code5 = """
import time
import pandas as pd
time.sleep(10)  # Sleep longer than timeout
signal = pd.DataFrame()
"""
    result5 = execute_strategy_in_sandbox(code5, timeout=3)
    print(f"Success: {result5['success']}")
    print(f"Error: {result5['error']}")
    print(f"Execution time: {result5['execution_time']:.2f}s")
    print()

    print("✅ All sandbox tests complete")


if __name__ == '__main__':
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    main()
