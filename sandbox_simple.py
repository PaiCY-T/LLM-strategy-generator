"""Simple sandbox for strategy execution in parent process.

Executes strategies in the same process to preserve finlab authentication.
Uses signal-based timeout for safety.
"""

import signal
from typing import Dict, Any, Optional, Tuple
import random


class TimeoutException(Exception):
    """Raised when strategy execution exceeds timeout."""
    pass


def execute_strategy_safe(
    code: str,
    data: Any,
    timeout: int = 120
) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """Safely execute strategy code with timeout and metrics extraction.

    Executes in PARENT process to preserve finlab authentication.
    Uses signal-based timeout (Unix only).

    Args:
        code: Validated strategy code to execute
        data: Finlab data object
        timeout: Execution timeout in seconds

    Returns:
        Tuple of (success, metrics, error_message)
    """
    def timeout_handler(signum, frame):
        raise TimeoutException(f"Strategy execution exceeded {timeout}s timeout")

    try:
        # Set up timeout (Unix only)
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)

        # Create execution namespace with data object
        namespace = {'data': data}

        # Use mock sim function for MVP testing
        def mock_sim(position, **kwargs):
            """Mock sim function that generates random but realistic metrics."""
            class MockReport:
                def __init__(self):
                    # Generate random but realistic backtest metrics
                    self.final_stats = {
                        'total_return': random.uniform(-0.3, 0.8),
                        'annual_return': random.uniform(-0.15, 0.35),
                        'sharpe_ratio': random.uniform(-0.5, 2.5),
                        'max_drawdown': random.uniform(-0.5, -0.05),
                        'win_rate': random.uniform(0.3, 0.7),
                    }
            return MockReport()
        namespace['sim'] = mock_sim

        # Execute strategy code
        exec(code, namespace)

        # Extract metrics from report
        metrics = None
        if 'report' in namespace:
            report = namespace['report']
            if hasattr(report, 'final_stats'):
                metrics = dict(report.final_stats)
                metrics['position_count'] = len(namespace.get('position', [])) if 'position' in namespace else 0

        # Cancel timeout alarm
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

        return True, metrics, None

    except TimeoutException as e:
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
            try:
                signal.signal(signal.SIGALRM, old_handler)
            except:
                pass
        return False, None, str(e)

    except Exception as e:
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
            try:
                signal.signal(signal.SIGALRM, old_handler)
            except:
                pass
        return False, None, f"{type(e).__name__}: {str(e)}"
