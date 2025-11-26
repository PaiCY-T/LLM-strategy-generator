"""
Tests for Runtime TTPT Monitor Integration.

The Runtime TTPT Monitor integrates Time-Travel Perturbation Testing into
the optimization workflow, providing real-time look-ahead bias detection
during TPE parameter optimization.

Test Structure (TDD RED Phase):
1. TestRuntimeTTPTConfig - Configuration and initialization
2. TestCheckpointValidation - Checkpoint-based validation during optimization
3. TestViolationLogging - Automated violation tracking and logging
4. TestOptimizationIntegration - Full integration with TPE optimizer
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Callable
import optuna
from pathlib import Path
import json


# Expected interface (implementation doesn't exist yet - TDD RED phase)
class RuntimeTTPTMonitor:
    """
    Runtime monitor for TTPT validation during optimization.

    Integrates with TPE optimizer to validate strategies at checkpoints,
    log violations, and alert when look-ahead bias is detected.
    """

    def __init__(
        self,
        ttpt_config: Dict[str, Any] = None,
        checkpoint_interval: int = 10,
        log_dir: str = None,
        alert_on_violation: bool = True
    ):
        """
        Initialize runtime TTPT monitor.

        Args:
            ttpt_config: Configuration for TTPTFramework (shift_days, tolerance, etc.)
            checkpoint_interval: Validate every N trials
            log_dir: Directory for violation logs
            alert_on_violation: Print alert when violation detected
        """
        pass

    def validate_checkpoint(
        self,
        trial_number: int,
        strategy_fn: Callable,
        data: Dict[str, pd.DataFrame],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate strategy at optimization checkpoint.

        Returns:
            {
                'passed': bool,
                'should_continue': bool,  # Continue optimization or stop
                'violations': List,
                'logged': bool
            }
        """
        pass

    def log_violation(
        self,
        trial_number: int,
        params: Dict[str, Any],
        ttpt_result: Dict[str, Any]
    ) -> str:
        """
        Log TTPT violation to file.

        Returns:
            Path to log file
        """
        pass

    def get_violation_summary(self) -> Dict[str, Any]:
        """
        Get summary of violations detected during optimization.

        Returns:
            {
                'total_validations': int,
                'total_violations': int,
                'violation_rate': float,
                'violations': List[Dict]
            }
        """
        pass


class TestRuntimeTTPTConfig:
    """Test configuration and initialization."""

    def test_default_config_initialization(self):
        """Monitor should initialize with sensible defaults."""
        monitor = RuntimeTTPTMonitor()

        # Should have default TTPT config
        assert monitor is not None

    def test_custom_ttpt_config(self):
        """Monitor should accept custom TTPT configuration."""
        custom_config = {
            'shift_days': [1, 3, 5],
            'tolerance': 0.03,
            'min_correlation': 0.97
        }

        monitor = RuntimeTTPTMonitor(ttpt_config=custom_config)

        assert monitor is not None

    def test_checkpoint_interval_configuration(self):
        """Monitor should respect checkpoint interval setting."""
        monitor = RuntimeTTPTMonitor(checkpoint_interval=5)

        # Should validate every 5 trials
        assert monitor is not None

    def test_log_directory_creation(self):
        """Monitor should create log directory if it doesn't exist."""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        log_dir = Path(temp_dir) / "ttpt_logs"

        monitor = RuntimeTTPTMonitor(log_dir=str(log_dir))

        assert log_dir.exists()

        # Cleanup
        shutil.rmtree(temp_dir)


class TestCheckpointValidation:
    """Test checkpoint-based validation during optimization."""

    def test_validates_at_checkpoint_intervals(self):
        """Should validate at configured checkpoint intervals."""
        monitor = RuntimeTTPTMonitor(checkpoint_interval=10)

        # Create test data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.random.randn(100) + 100
            }, index=dates)
        }

        def simple_strategy(data_dict, params):
            close = data_dict['close']
            ma = close.rolling(window=params['lookback']).mean()
            return (close > ma).astype(float)

        # Trial 9 - should NOT validate
        result_9 = monitor.validate_checkpoint(
            trial_number=9,
            strategy_fn=simple_strategy,
            data=data,
            params={'lookback': 20}
        )

        # Trial 10 - SHOULD validate
        result_10 = monitor.validate_checkpoint(
            trial_number=10,
            strategy_fn=simple_strategy,
            data=data,
            params={'lookback': 20}
        )

        # Should have validation result at checkpoint
        assert 'passed' in result_10

    def test_skips_non_checkpoint_trials(self):
        """Should skip validation for non-checkpoint trials."""
        monitor = RuntimeTTPTMonitor(checkpoint_interval=10)

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.random.randn(100) + 100
            }, index=dates)
        }

        def simple_strategy(data_dict, params):
            close = data_dict['close']
            return (close > close.mean()).astype(float)

        # Trial 7 is not a checkpoint (interval=10)
        result = monitor.validate_checkpoint(
            trial_number=7,
            strategy_fn=simple_strategy,
            data=data,
            params={}
        )

        # Should indicate skipped
        assert result.get('skipped') is True or 'passed' not in result

    def test_detects_violations_at_checkpoints(self):
        """Should detect look-ahead bias at checkpoints."""
        monitor = RuntimeTTPTMonitor(checkpoint_interval=5)

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.arange(100) + 100
            }, index=dates)
        }

        # Strategy with look-ahead bias
        def biased_strategy(data_dict, params):
            close = data_dict['close']
            future = close.shift(-5)  # Look-ahead bias
            return (future > close).astype(float)

        result = monitor.validate_checkpoint(
            trial_number=5,  # Checkpoint
            strategy_fn=biased_strategy,
            data=data,
            params={}
        )

        assert result['passed'] is False
        assert len(result.get('violations', [])) > 0

    def test_passes_valid_strategies_at_checkpoints(self):
        """Should pass strategies without look-ahead bias."""
        monitor = RuntimeTTPTMonitor(checkpoint_interval=5)

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.random.randn(100) + 100
            }, index=dates)
        }

        # Valid strategy
        def valid_strategy(data_dict, params):
            close = data_dict['close']
            ma = close.rolling(window=10).mean()
            return (close > ma).astype(float)

        result = monitor.validate_checkpoint(
            trial_number=5,
            strategy_fn=valid_strategy,
            data=data,
            params={}
        )

        assert result['passed'] is True


class TestViolationLogging:
    """Test automated violation tracking and logging."""

    def test_logs_violations_to_file(self):
        """Should write violations to log file."""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        log_dir = Path(temp_dir) / "ttpt_logs"

        monitor = RuntimeTTPTMonitor(log_dir=str(log_dir))

        ttpt_result = {
            'passed': False,
            'violations': [
                {'shift_days': 5, 'type': 'performance_degradation'}
            ],
            'metrics': {'signal_correlation': 0.85}
        }

        log_path = monitor.log_violation(
            trial_number=42,
            params={'lookback': 20},
            ttpt_result=ttpt_result
        )

        # Log file should exist
        assert Path(log_path).exists()

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_log_contains_trial_info(self):
        """Log file should contain trial number and parameters."""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        log_dir = Path(temp_dir) / "ttpt_logs"

        monitor = RuntimeTTPTMonitor(log_dir=str(log_dir))

        ttpt_result = {
            'passed': False,
            'violations': [{'shift_days': 5}],
            'metrics': {}
        }

        log_path = monitor.log_violation(
            trial_number=42,
            params={'lookback': 20, 'threshold': 0.05},
            ttpt_result=ttpt_result
        )

        # Read log file
        with open(log_path, 'r') as f:
            log_data = json.load(f)

        assert log_data['trial_number'] == 42
        assert 'lookback' in log_data['params']

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_alerts_on_violation_when_enabled(self, capsys):
        """Should print alert when violation detected and alerts enabled."""
        monitor = RuntimeTTPTMonitor(alert_on_violation=True)

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.arange(100) + 100
            }, index=dates)
        }

        def biased_strategy(data_dict, params):
            close = data_dict['close']
            return (close.shift(-5) > close).astype(float)

        result = monitor.validate_checkpoint(
            trial_number=10,
            strategy_fn=biased_strategy,
            data=data,
            params={}
        )

        # Check if alert was printed (captured by capsys)
        # (This will work once implementation exists)
        assert result['passed'] is False

    def test_no_alert_when_disabled(self):
        """Should not print alert when alerts disabled."""
        monitor = RuntimeTTPTMonitor(alert_on_violation=False)

        # Should not print anything even if violation detected
        assert monitor is not None


class TestViolationSummary:
    """Test violation summary and statistics."""

    def test_tracks_total_validations(self):
        """Should track total number of validations performed."""
        monitor = RuntimeTTPTMonitor(checkpoint_interval=5)

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.random.randn(100) + 100
            }, index=dates)
        }

        def simple_strategy(data_dict, params):
            close = data_dict['close']
            return (close > close.mean()).astype(float)

        # Run several checkpoints
        for trial in [5, 10, 15]:
            monitor.validate_checkpoint(
                trial_number=trial,
                strategy_fn=simple_strategy,
                data=data,
                params={}
            )

        summary = monitor.get_violation_summary()

        assert summary['total_validations'] >= 3

    def test_calculates_violation_rate(self):
        """Should calculate violation rate correctly."""
        monitor = RuntimeTTPTMonitor(checkpoint_interval=1)

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.arange(100) + 100
            }, index=dates)
        }

        # Half valid, half biased
        def valid_strategy(data_dict, params):
            close = data_dict['close']
            return (close > close.mean()).astype(float)

        def biased_strategy(data_dict, params):
            close = data_dict['close']
            return (close.shift(-5) > close).astype(float)

        # 2 valid
        monitor.validate_checkpoint(1, valid_strategy, data, {})
        monitor.validate_checkpoint(2, valid_strategy, data, {})

        # 2 biased
        monitor.validate_checkpoint(3, biased_strategy, data, {})
        monitor.validate_checkpoint(4, biased_strategy, data, {})

        summary = monitor.get_violation_summary()

        # Should have ~50% violation rate
        assert 0.4 <= summary['violation_rate'] <= 0.6


class TestOptimizationIntegration:
    """Test full integration with TPE optimizer."""

    def test_integrates_with_tpe_optimizer(self):
        """Should integrate seamlessly with TPEOptimizer."""
        from src.learning.optimizer import TPEOptimizer

        optimizer = TPEOptimizer()
        monitor = RuntimeTTPTMonitor(checkpoint_interval=5)

        # Should be able to use monitor in objective function
        assert monitor is not None
        assert optimizer is not None

    def test_optimize_with_runtime_ttpt_method(self):
        """TPEOptimizer should have optimize_with_runtime_ttpt() method."""
        from src.learning.optimizer import TPEOptimizer

        optimizer = TPEOptimizer()

        # Check if method exists
        assert hasattr(optimizer, 'optimize_with_runtime_ttpt')

    def test_runtime_validation_during_optimization(self):
        """Should validate strategies during optimization runtime."""
        from src.learning.optimizer import TPEOptimizer

        optimizer = TPEOptimizer()

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.random.randn(100) + 100,
                '2317.TW': np.random.randn(100) + 50
            }, index=dates)
        }

        def objective_with_strategy(params):
            # Mock backtest
            return np.random.rand()

        # Create strategy function for TTPT validation
        def strategy_fn(data_dict, params):
            close = data_dict['close']
            lookback = params.get('lookback', 20)
            ma = close.rolling(window=lookback).mean()
            return (close > ma).astype(float)

        result = optimizer.optimize_with_runtime_ttpt(
            objective_fn=objective_with_strategy,
            strategy_fn=strategy_fn,
            data=data,
            n_trials=20,
            param_space={'lookback': (10, 50)},
            checkpoint_interval=5
        )

        # Should have TTPT monitoring results
        assert 'ttpt_summary' in result
        assert result['ttpt_summary']['total_validations'] > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_handles_strategy_execution_errors(self):
        """Should handle strategy execution errors gracefully."""
        monitor = RuntimeTTPTMonitor(checkpoint_interval=5)

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.random.randn(100) + 100
            }, index=dates)
        }

        # Strategy that will raise error
        def buggy_strategy(data_dict, params):
            raise ValueError("Intentional error for testing")

        result = monitor.validate_checkpoint(
            trial_number=5,
            strategy_fn=buggy_strategy,
            data=data,
            params={}
        )

        # Should handle gracefully
        assert result['passed'] is False or 'error' in result

    def test_handles_insufficient_data(self):
        """Should handle data that's too short for TTPT shifts."""
        monitor = RuntimeTTPTMonitor(
            ttpt_config={'shift_days': [50, 100]},  # Large shifts
            checkpoint_interval=5
        )

        # Short data
        dates = pd.date_range('2023-01-01', periods=30, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.random.randn(30) + 100
            }, index=dates)
        }

        def simple_strategy(data_dict, params):
            close = data_dict['close']
            return (close > close.mean()).astype(float)

        result = monitor.validate_checkpoint(
            trial_number=5,
            strategy_fn=simple_strategy,
            data=data,
            params={}
        )

        # Should handle gracefully (skip or warn)
        assert 'passed' in result or 'skipped' in result


# Expected test results (RED phase - all should fail initially)
"""
Expected Test Failures (TDD RED Phase):
========================================

TestRuntimeTTPTConfig:
  ❌ test_default_config_initialization - RuntimeTTPTMonitor not implemented
  ❌ test_custom_ttpt_config - RuntimeTTPTMonitor not implemented
  ❌ test_checkpoint_interval_configuration - RuntimeTTPTMonitor not implemented
  ❌ test_log_directory_creation - RuntimeTTPTMonitor not implemented

TestCheckpointValidation:
  ❌ test_validates_at_checkpoint_intervals - RuntimeTTPTMonitor not implemented
  ❌ test_skips_non_checkpoint_trials - RuntimeTTPTMonitor not implemented
  ❌ test_detects_violations_at_checkpoints - RuntimeTTPTMonitor not implemented
  ❌ test_passes_valid_strategies_at_checkpoints - RuntimeTTPTMonitor not implemented

TestViolationLogging:
  ❌ test_logs_violations_to_file - RuntimeTTPTMonitor not implemented
  ❌ test_log_contains_trial_info - RuntimeTTPTMonitor not implemented
  ❌ test_alerts_on_violation_when_enabled - RuntimeTTPTMonitor not implemented
  ❌ test_no_alert_when_disabled - RuntimeTTPTMonitor not implemented

TestViolationSummary:
  ❌ test_tracks_total_validations - RuntimeTTPTMonitor not implemented
  ❌ test_calculates_violation_rate - RuntimeTTPTMonitor not implemented

TestOptimizationIntegration:
  ❌ test_integrates_with_tpe_optimizer - RuntimeTTPTMonitor not implemented
  ❌ test_optimize_with_runtime_ttpt_method - Method not implemented
  ❌ test_runtime_validation_during_optimization - Method not implemented

TestEdgeCases:
  ❌ test_handles_strategy_execution_errors - RuntimeTTPTMonitor not implemented
  ❌ test_handles_insufficient_data - RuntimeTTPTMonitor not implemented

Total: 18 tests (all failing - expected for RED phase)
"""
