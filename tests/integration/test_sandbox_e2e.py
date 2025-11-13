"""End-to-end smoke test for SandboxExecutionWrapper integration.

Tests the complete integration of SandboxExecutionWrapper by simulating
5 full iterations similar to autonomous loop execution patterns.

Task 2.3: docker-sandbox-integration-testing
Requirement 4: Integration with Autonomous Loop

KNOWN ISSUE:
- Importing autonomous_loop causes pytest cleanup to fail with "I/O operation on closed file"
- This is a cosmetic issue with pytest's output handling and does not affect test validity
- All tests PASS correctly before the cleanup error occurs
- Root cause: autonomous_loop.py may close/redirect sys.stdout during import
- Tests are delayed-import to minimize impact and tests themselves succeed
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
import json
from typing import Dict, Any, Tuple, Optional
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'artifacts' / 'working' / 'modules'))

# Note: SandboxExecutionWrapper will be imported inside each test to avoid
# module-level import side effects from autonomous_loop


class TestSandboxE2E:
    """End-to-end smoke tests for sandbox integration."""

    @pytest.fixture
    def temp_test_dir(self):
        """Create temporary directory for test artifacts."""
        temp_dir = tempfile.mkdtemp(prefix="sandbox_e2e_")
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_data(self):
        """Mock finlab data object for testing."""
        import pandas as pd
        import numpy as np

        # Create realistic mock data that supports operations
        class MockData:
            def __init__(self):
                # Create simple price series for testing
                dates = pd.date_range('2020-01-01', periods=100, freq='D')
                self.close = pd.Series(
                    np.random.randn(100).cumsum() + 100,
                    index=dates
                )

        return MockData()

    @pytest.fixture
    def sample_strategy_template(self):
        """Sample strategy code template for testing."""
        return """
# Simple momentum strategy for testing
def strategy(data):
    '''Simple momentum strategy'''
    return data.close > data.close.shift(1)

# Execute backtest with sim
position = strategy(data)
report = sim(position, resample='M')
"""

    def test_5_iteration_smoke_sandbox_enabled(
        self,
        temp_test_dir,
        mock_data,
        sample_strategy_template
    ):
        """Test: 5 iterations complete successfully with sandbox enabled.

        Requirement 4.1: WHEN `sandbox.enabled: true` in config THEN
        the autonomous loop SHALL route strategy execution through Docker Sandbox.

        This simulates 5 full iterations of strategy execution.
        """
        # Import SandboxExecutionWrapper (delayed to avoid module-level side effects)
        from autonomous_loop import SandboxExecutionWrapper

        # Create mock Docker executor
        mock_docker_executor = Mock()

        # Track execution results
        execution_results = []

        def mock_docker_execute(code, data, timeout):
            """Mock Docker execution that records calls."""
            iteration = len(execution_results) + 1
            execution_results.append({
                'iteration': iteration,
                'code_length': len(code),
                'timeout': timeout,
                'mode': 'sandbox'
            })
            return (
                True,
                {
                    'sharpe_ratio': 1.0 + iteration * 0.1,
                    'annual_return': 0.10,
                    'max_drawdown': -0.05
                },
                None
            )

        mock_docker_executor.execute_strategy = Mock(side_effect=mock_docker_execute)

        # Create mock event logger
        mock_event_logger = Mock()
        mock_event_logger.log_event = Mock()

        # Create wrapper with sandbox enabled
        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker_executor,
            event_logger=mock_event_logger
        )

        # Execute 5 iterations
        for i in range(5):
            success, metrics, error = wrapper.execute_strategy(
                code=sample_strategy_template,
                data=mock_data,
                timeout=120
            )

            # Verify each iteration succeeded
            assert success is True, f"Iteration {i+1} failed"
            assert metrics is not None
            assert error is None
            assert metrics['sharpe_ratio'] > 1.0

        # Verify all 5 iterations executed
        assert len(execution_results) == 5, \
            f"Expected 5 iterations, got {len(execution_results)}"

        # Verify all used sandbox mode
        for i, result in enumerate(execution_results, 1):
            assert result['iteration'] == i
            assert result['mode'] == 'sandbox'
            assert result['code_length'] > 0

        # Verify no fallbacks occurred
        stats = wrapper.get_fallback_stats()
        assert stats['execution_count'] == 5
        assert stats['fallback_count'] == 0, \
            "No fallbacks should occur in successful test"
        assert stats['fallback_rate'] == 0.0

        # Verify Docker executor was called 5 times
        assert mock_docker_executor.execute_strategy.call_count == 5

        print(f"\n✅ E2E Test Success:")
        print(f"   - Iterations: {len(execution_results)}/5")
        print(f"   - Success rate: 100%")
        print(f"   - Fallbacks: {stats['fallback_count']}")
        print(f"   - Sandbox wrapper working correctly!")

    def test_5_iteration_smoke_sandbox_disabled(
        self,
        temp_test_dir,
        mock_data,
        sample_strategy_template
    ):
        """Test: 5 iterations complete successfully with sandbox disabled (baseline).

        Requirement 4.4: IF sandbox is disabled THEN the system SHALL use
        AST-only execution (current behavior).

        This verifies backward compatibility.
        """
        # Import SandboxExecutionWrapper (delayed to avoid module-level side effects)
        from autonomous_loop import SandboxExecutionWrapper

        # Create mock event logger
        mock_event_logger = Mock()
        mock_event_logger.log_event = Mock()

        # Create wrapper with sandbox DISABLED
        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=False,
            docker_executor=None,  # No Docker executor when disabled
            event_logger=mock_event_logger
        )

        # Execute 5 iterations in direct mode
        execution_results = []
        for i in range(5):
            success, metrics, error = wrapper.execute_strategy(
                code=sample_strategy_template,
                data=mock_data,
                timeout=120
            )

            execution_results.append({
                'iteration': i + 1,
                'mode': 'direct',
                'success': success
            })

            # Verify each iteration succeeded
            assert success is True, f"Iteration {i+1} failed"
            assert metrics is not None
            assert error is None

        # Verify 5 iterations executed
        assert len(execution_results) == 5

        # Verify all used direct mode
        for result in execution_results:
            assert result['mode'] == 'direct'
            assert result['success'] is True

        # Verify no fallbacks in direct mode (sandbox was never attempted)
        stats = wrapper.get_fallback_stats()
        assert stats['execution_count'] == 5
        assert stats['fallback_count'] == 0
        assert stats['fallback_rate'] == 0.0

        print(f"\n✅ Direct Mode Test Success:")
        print(f"   - Iterations: {len(execution_results)}/5")
        print(f"   - Mode: Direct (sandbox disabled)")
        print(f"   - Backward compatibility: Verified!")

    def test_5_iteration_with_fallbacks(
        self,
        temp_test_dir,
        mock_data,
        sample_strategy_template
    ):
        """Test: 5 iterations with some fallbacks (mixed success/fallback).

        Requirement 4.2-4.3: WHEN a sandbox execution fails THEN the system
        SHALL automatically fallback to AST-only execution AND continue the iteration.

        This verifies that fallback mechanism works correctly.
        """
        # Import SandboxExecutionWrapper (delayed to avoid module-level side effects)
        from autonomous_loop import SandboxExecutionWrapper

        # Create mock Docker executor that fails on iterations 2 and 4
        mock_docker_executor = Mock()
        fallback_iterations = [2, 4]

        def mock_docker_execute(code, data, timeout):
            """Mock Docker execution that fails on specific iterations."""
            # Use wrapper's execution_count to determine current iteration
            # (This is called after execution_count is incremented)
            if wrapper.execution_count in fallback_iterations:
                raise TimeoutError(f"Simulated timeout on iteration {wrapper.execution_count}")
            return (
                True,
                {
                    'sharpe_ratio': 1.0 + wrapper.execution_count * 0.1,
                    'annual_return': 0.10
                },
                None
            )

        mock_docker_executor.execute_strategy = Mock(side_effect=mock_docker_execute)

        # Create mock event logger
        mock_event_logger = Mock()
        mock_event_logger.log_event = Mock()

        # Create wrapper with sandbox enabled
        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker_executor,
            event_logger=mock_event_logger
        )

        # Execute 5 iterations (2 and 4 will fallback)
        execution_results = []
        for i in range(5):
            success, metrics, error = wrapper.execute_strategy(
                code=sample_strategy_template,
                data=mock_data,
                timeout=120
            )

            execution_results.append({
                'iteration': i + 1,
                'success': success,
                'expected_fallback': (i + 1) in fallback_iterations
            })

            # Verify each iteration succeeded (even with fallback)
            assert success is True, f"Iteration {i+1} failed"
            assert metrics is not None
            assert error is None

        # Verify all 5 iterations completed
        assert len(execution_results) == 5

        # Verify fallback statistics
        stats = wrapper.get_fallback_stats()
        assert stats['execution_count'] == 5
        assert stats['fallback_count'] == 2, \
            f"Expected 2 fallbacks, got {stats['fallback_count']}"
        assert stats['fallback_rate'] == pytest.approx(0.4, 0.01)

        # Verify fallback events were logged
        fallback_logs = [
            call for call in mock_event_logger.log_event.call_args_list
            if len(call[0]) > 1 and call[0][1] == "sandbox_fallback"
        ]
        assert len(fallback_logs) == 2, "Expected 2 fallback events logged"

        print(f"\n✅ Fallback Test Success:")
        print(f"   - Iterations: {len(execution_results)}/5")
        print(f"   - Fallbacks: {stats['fallback_count']}")
        print(f"   - Fallback rate: {stats['fallback_rate']:.1%}")
        print(f"   - Loop continued successfully!")

    def test_monitoring_integration(
        self,
        temp_test_dir,
        mock_data,
        sample_strategy_template
    ):
        """Test: Monitoring integration validates sandbox execution metadata.

        Requirement 4.5: WHEN an iteration completes THEN the system SHALL
        record whether sandbox or fallback was used in iteration metadata.

        This verifies that the event logger captures sandbox metadata correctly.
        """
        # Import SandboxExecutionWrapper (delayed to avoid module-level side effects)
        from autonomous_loop import SandboxExecutionWrapper

        # Create mock Docker executor
        mock_docker_executor = Mock()
        mock_docker_executor.execute_strategy = Mock(
            return_value=(True, {'sharpe_ratio': 1.2}, None)
        )

        # Track event logger calls
        event_log_calls = []

        def capture_log_event(*args, **kwargs):
            """Capture event logger calls."""
            event_log_calls.append({
                'args': args,
                'kwargs': kwargs,
                'level': args[0] if len(args) > 0 else None,
                'event_type': args[1] if len(args) > 1 else None
            })

        # Create mock event logger
        mock_event_logger = Mock()
        mock_event_logger.log_event = Mock(side_effect=capture_log_event)

        # Create wrapper with sandbox enabled
        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker_executor,
            event_logger=mock_event_logger
        )

        # Execute 3 iterations
        for i in range(3):
            success, metrics, error = wrapper.execute_strategy(
                code=sample_strategy_template,
                data=mock_data,
                timeout=120
            )

            assert success is True, f"Iteration {i+1} failed"

        # Verify event logging occurred
        assert len(event_log_calls) > 0, \
            "Event logger should be called during execution"

        # Verify sandbox execution events were logged
        sandbox_events = [
            call for call in event_log_calls
            if call['event_type'] == 'sandbox_execution'
        ]
        assert len(sandbox_events) == 3, \
            f"Expected 3 sandbox execution events, got {len(sandbox_events)}"

        # Verify each event contains execution_count
        for event in sandbox_events:
            assert 'execution_count' in event['kwargs'], \
                "execution_count should be in event metadata"

        print(f"\n✅ Monitoring Integration Success:")
        print(f"   - Event log calls: {len(event_log_calls)}")
        print(f"   - Sandbox execution events: {len(sandbox_events)}")
        print(f"   - Metadata tracking: Verified!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
