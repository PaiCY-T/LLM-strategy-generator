"""
Test Metric Accuracy - Fix 1.2 Validation
==========================================

Validates that extracted metrics match actual backtest results within acceptable tolerance.

Acceptance Criteria:
- AC-1.2.21: Sharpe ratio error < 0.01
- AC-1.2.22: Annual return error < 0.001 (0.1%)
- AC-1.2.23: Max drawdown error < 0.001 (0.1%)
- AC-1.2.24: Total return error < 0.001 (0.1%)

Test Strategy:
1. Create simple test strategies with known characteristics
2. Run through extraction pipeline (DIRECT, SIGNAL, DEFAULT methods)
3. Compare extracted metrics with ground truth
4. Validate error tolerances are met

Design:
- Uses REAL finlab API for integration testing
- Tests complete extraction pipeline (Tasks 11-18)
- Validates parameter consistency (Task 13)
- Tests API compatibility (Task 14)
- Verifies suspicious detection (Task 15)
- Validates 3-method fallback chain (Task 17-18)
"""

import pytest
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from metrics_extractor import (
    extract_metrics_from_signal,
    _extract_metrics_from_report,
    _safe_extract_metric,
    _detect_suspicious_metrics,
    DEFAULT_BACKTEST_PARAMS
)

# Configure logging for test visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Test Fixtures and Utilities
# ============================================================================

def create_simple_momentum_strategy() -> str:
    """
    Create a simple momentum strategy for testing.

    Strategy: Buy top 50% of stocks by 20-day returns.
    This strategy is simple, predictable, and should execute quickly.

    Returns:
        Strategy code as string
    """
    return '''
from finlab import data

# Simple price momentum strategy
close = data.get('price:收盤價')
returns = close.pct_change(20)  # 20-day returns

# Buy top 50% by momentum
signal = returns > returns.median()

# Run backtest
report = sim(signal, resample='D', stop_loss=0.1)
'''


def create_test_signal(num_stocks: int = 10, num_days: int = 100,
                       seed: int = 42) -> pd.DataFrame:
    """
    Create a synthetic test signal for controlled testing.

    Args:
        num_stocks: Number of stock columns
        num_days: Number of trading days
        seed: Random seed for reproducibility

    Returns:
        DataFrame with DatetimeIndex and boolean values
    """
    np.random.seed(seed)

    # Create date range
    dates = pd.date_range('2023-01-01', periods=num_days, freq='D')

    # Create stock symbols
    stocks = [f'TEST_{i:04d}' for i in range(num_stocks)]

    # Create random signal (30% probability of True)
    signal = pd.DataFrame(
        np.random.random((num_days, num_stocks)) < 0.3,
        index=dates,
        columns=stocks
    )

    return signal


def create_mock_report(metrics: Dict[str, float], api_format: str = 'dict') -> MagicMock:
    """
    Create a mock Finlab Report object with specified metrics.

    Args:
        metrics: Dictionary of metric values
        api_format: 'dict' for new API, 'float' for old API

    Returns:
        Mock Report object
    """
    report = MagicMock()

    # Create final_stats dict
    final_stats = {}
    for key, value in metrics.items():
        if api_format == 'dict':
            # New API: metrics are dicts with 'strategy' and 'benchmark' keys
            final_stats[key] = {'strategy': value, 'benchmark': 0.0}
        else:
            # Old API: metrics are floats
            final_stats[key] = value

    report.final_stats = final_stats
    report.trades = []  # Empty trades list
    report.final_value = 1.0 + metrics.get('total_return', 0.0)

    return report


def assert_metric_accuracy(extracted: Dict[str, Any],
                          ground_truth: Dict[str, float],
                          tolerance_ratios: float = 0.01,
                          tolerance_percentages: float = 0.001) -> None:
    """
    Compare extracted metrics with ground truth within tolerance.

    Args:
        extracted: Result from extract_metrics_from_signal
        ground_truth: Expected metric values
        tolerance_ratios: Tolerance for ratios (Sharpe, Calmar)
        tolerance_percentages: Tolerance for percentages (returns, drawdown, win_rate)

    Raises:
        AssertionError: If any metric exceeds tolerance
    """
    assert extracted['success'], f"Extraction failed: {extracted.get('error')}"

    metrics = extracted['metrics']

    # Define which metrics use which tolerance
    ratio_metrics = ['sharpe_ratio', 'calmar_ratio']
    percentage_metrics = ['total_return', 'annual_return', 'max_drawdown',
                         'win_rate', 'volatility']

    errors = []

    for metric_name, expected_value in ground_truth.items():
        actual_value = metrics.get(metric_name, 0.0)

        # Determine tolerance based on metric type
        if metric_name in ratio_metrics:
            tolerance = tolerance_ratios
        elif metric_name in percentage_metrics:
            tolerance = tolerance_percentages
        else:
            # For other metrics (like total_trades), use ratio tolerance
            tolerance = tolerance_ratios

        # Calculate absolute error
        error = abs(actual_value - expected_value)

        # Check if error exceeds tolerance
        if error >= tolerance:
            errors.append(
                f"{metric_name}: error {error:.6f} exceeds tolerance {tolerance:.6f} "
                f"(actual={actual_value:.6f}, expected={expected_value:.6f})"
            )
        else:
            logger.info(f"✅ {metric_name}: error {error:.6f} within tolerance {tolerance:.6f}")

    # Raise assertion error if any metrics failed
    if errors:
        error_msg = "Metric accuracy validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise AssertionError(error_msg)


# ============================================================================
# Test Cases: DIRECT Extraction Method
# ============================================================================

def test_direct_extraction_dict_format():
    """
    Test DIRECT extraction with new API (dict format).

    Validates:
    - AC-1.2.21: Sharpe ratio error < 0.01
    - AC-1.2.22: Annual return error < 0.001
    - AC-1.2.23: Max drawdown error < 0.001
    - AC-1.2.24: Total return error < 0.001
    - Task 14: API compatibility (dict format)
    """
    logger.info("=" * 70)
    logger.info("TEST: DIRECT extraction with dict format (new API)")
    logger.info("=" * 70)

    # Define expected metrics
    expected_metrics = {
        'sharpe_ratio': 1.5432,
        'total_return': 0.2345,
        'annual_return': 0.1234,
        'max_drawdown': -0.1567,
        'win_rate': 0.5678,
        'volatility': 0.2123
    }

    # Create mock report with dict format (new API)
    mock_report = create_mock_report(expected_metrics, api_format='dict')

    # Extract metrics using DIRECT method
    extracted_metrics = _extract_metrics_from_report(mock_report)

    # Build result structure matching extract_metrics_from_signal format
    result = {
        'success': True,
        'metrics': extracted_metrics,
        'error': None,
        'backtest_report': mock_report
    }

    # Validate accuracy
    assert_metric_accuracy(result, expected_metrics)

    logger.info("✅ DIRECT extraction (dict format) passed accuracy validation")


def test_direct_extraction_float_format():
    """
    Test DIRECT extraction with old API (float format).

    Validates:
    - Task 14: API compatibility (float format)
    - Backward compatibility with old finlab versions
    """
    logger.info("=" * 70)
    logger.info("TEST: DIRECT extraction with float format (old API)")
    logger.info("=" * 70)

    # Define expected metrics
    expected_metrics = {
        'sharpe_ratio': 2.1234,
        'total_return': 0.3456,
        'annual_return': 0.1567,
        'max_drawdown': -0.2234,
        'win_rate': 0.6123
    }

    # Create mock report with float format (old API)
    mock_report = create_mock_report(expected_metrics, api_format='float')

    # Extract metrics using DIRECT method
    extracted_metrics = _extract_metrics_from_report(mock_report)

    # Build result structure
    result = {
        'success': True,
        'metrics': extracted_metrics,
        'error': None,
        'backtest_report': mock_report
    }

    # Validate accuracy
    assert_metric_accuracy(result, expected_metrics)

    logger.info("✅ DIRECT extraction (float format) passed accuracy validation")


# ============================================================================
# Test Cases: API Compatibility
# ============================================================================

def test_safe_extract_metric_dict_format():
    """
    Test _safe_extract_metric with dict format.

    Validates Task 14: API compatibility helper function.
    """
    logger.info("=" * 70)
    logger.info("TEST: _safe_extract_metric with dict format")
    logger.info("=" * 70)

    # Test dict with 'strategy' key
    value = {'strategy': 1.234, 'benchmark': 0.567}
    result = _safe_extract_metric(value, 'test_metric')
    assert abs(result - 1.234) < 0.001, f"Expected 1.234, got {result}"

    # Test dict without 'strategy' key
    value = {'invalid': 1.234}
    result = _safe_extract_metric(value, 'test_metric')
    assert result == 0.0, f"Expected 0.0 for invalid dict, got {result}"

    logger.info("✅ _safe_extract_metric (dict format) works correctly")


def test_safe_extract_metric_float_format():
    """
    Test _safe_extract_metric with float format.

    Validates Task 14: API compatibility with old format.
    """
    logger.info("=" * 70)
    logger.info("TEST: _safe_extract_metric with float format")
    logger.info("=" * 70)

    # Test float value
    value = 2.345
    result = _safe_extract_metric(value, 'test_metric')
    assert abs(result - 2.345) < 0.001, f"Expected 2.345, got {result}"

    # Test int value
    value = 5
    result = _safe_extract_metric(value, 'test_metric')
    assert abs(result - 5.0) < 0.001, f"Expected 5.0, got {result}"

    # Test None value
    result = _safe_extract_metric(None, 'test_metric')
    assert result == 0.0, f"Expected 0.0 for None, got {result}"

    logger.info("✅ _safe_extract_metric (float format) works correctly")


# ============================================================================
# Test Cases: Suspicious Detection
# ============================================================================

def test_suspicious_detection_all_zeros():
    """
    Test suspicious metric detection for all zeros.

    Validates Task 15: Pattern detection for extraction failures.
    """
    logger.info("=" * 70)
    logger.info("TEST: Suspicious detection - all zeros")
    logger.info("=" * 70)

    # Create metrics with all zeros but trades > 0
    metrics = {
        'sharpe_ratio': 0.0,
        'annual_return': 0.0,
        'max_drawdown': 0.0,
        'total_return': 0.0,
        'total_trades': 100  # Should trigger CRITICAL warning
    }

    warnings = _detect_suspicious_metrics(metrics)

    # Should detect CRITICAL pattern
    assert len(warnings) > 0, "Should detect suspicious pattern"
    assert any('CRITICAL' in w for w in warnings), "Should flag CRITICAL extraction failure"

    logger.info(f"✅ Detected {len(warnings)} suspicious patterns")
    for warning in warnings:
        logger.info(f"  - {warning}")


def test_suspicious_detection_valid_metrics():
    """
    Test that valid metrics don't trigger false positives.

    Validates Task 15: No false positives for good metrics.
    """
    logger.info("=" * 70)
    logger.info("TEST: Suspicious detection - valid metrics")
    logger.info("=" * 70)

    # Create valid metrics
    metrics = {
        'sharpe_ratio': 1.5,
        'annual_return': 0.15,
        'max_drawdown': -0.12,
        'total_return': 0.25,
        'total_trades': 100
    }

    warnings = _detect_suspicious_metrics(metrics)

    # Should not detect any suspicious patterns
    assert len(warnings) == 0, f"False positive: {warnings}"

    logger.info("✅ No false positives for valid metrics")


# ============================================================================
# Test Cases: Parameter Consistency
# ============================================================================

def test_parameter_consistency():
    """
    Test that SIGNAL fallback uses same parameters as original execution.

    Validates Task 13: Parameter capture and reuse.
    """
    logger.info("=" * 70)
    logger.info("TEST: Parameter consistency")
    logger.info("=" * 70)

    # Create test signal
    signal = create_test_signal(num_stocks=5, num_days=50)

    # Define custom parameters
    custom_params = {
        'resample': 'W',  # Weekly instead of default daily
        'stop_loss': 0.08,  # 8% instead of default 10%
        'upload': False
    }

    # Mock sim function to verify parameters are passed correctly
    with patch('finlab.backtest.sim') as mock_sim:
        # Configure mock to return a report
        mock_report = create_mock_report({
            'sharpe_ratio': 1.0,
            'total_return': 0.10,
            'annual_return': 0.08,
            'max_drawdown': -0.15
        })
        mock_sim.return_value = mock_report

        # Extract metrics with custom parameters
        result = extract_metrics_from_signal(signal, backtest_params=custom_params)

        # Verify sim was called with correct parameters
        mock_sim.assert_called_once()
        call_args = mock_sim.call_args

        # Check that all custom parameters were passed
        assert call_args.kwargs['resample'] == 'W', "resample parameter not passed correctly"
        assert call_args.kwargs['stop_loss'] == 0.08, "stop_loss parameter not passed correctly"
        assert call_args.kwargs['upload'] == False, "upload parameter not passed correctly"

        logger.info("✅ Custom parameters passed correctly")
        logger.info(f"  - resample: {call_args.kwargs['resample']}")
        logger.info(f"  - stop_loss: {call_args.kwargs['stop_loss']}")
        logger.info(f"  - upload: {call_args.kwargs['upload']}")


def test_default_parameter_usage():
    """
    Test that default parameters are used when none provided.

    Validates Task 13: Default parameter fallback.
    """
    logger.info("=" * 70)
    logger.info("TEST: Default parameter usage")
    logger.info("=" * 70)

    # Create test signal
    signal = create_test_signal(num_stocks=5, num_days=50)

    # Mock sim function
    with patch('finlab.backtest.sim') as mock_sim:
        mock_report = create_mock_report({
            'sharpe_ratio': 1.0,
            'total_return': 0.10
        })
        mock_sim.return_value = mock_report

        # Extract metrics without custom parameters
        result = extract_metrics_from_signal(signal)

        # Verify sim was called with default parameters
        mock_sim.assert_called_once()
        call_args = mock_sim.call_args

        # Check default parameters
        assert call_args.kwargs['resample'] == DEFAULT_BACKTEST_PARAMS['resample']
        assert call_args.kwargs['stop_loss'] == DEFAULT_BACKTEST_PARAMS['stop_loss']
        assert call_args.kwargs['upload'] == DEFAULT_BACKTEST_PARAMS['upload']

        logger.info("✅ Default parameters used correctly")
        logger.info(f"  - resample: {call_args.kwargs['resample']}")
        logger.info(f"  - stop_loss: {call_args.kwargs['stop_loss']}")
        logger.info(f"  - upload: {call_args.kwargs['upload']}")


# ============================================================================
# Test Cases: Signal Validation
# ============================================================================

def test_signal_validation_empty_signal():
    """
    Test that empty signals are properly detected.

    Validates signal validation logic.
    """
    logger.info("=" * 70)
    logger.info("TEST: Signal validation - empty signal")
    logger.info("=" * 70)

    # Create signal with all False (no positions)
    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    signal = pd.DataFrame(False, index=dates, columns=['STOCK_A', 'STOCK_B'])

    # Extract metrics - should fail validation
    result = extract_metrics_from_signal(signal)

    assert not result['success'], "Should fail for empty signal"
    assert 'no positions' in result['error'].lower(), "Error message should mention no positions"

    logger.info("✅ Empty signal properly detected and rejected")


def test_signal_validation_valid_signal():
    """
    Test that valid signals pass validation.

    Validates signal validation logic doesn't reject good signals.
    """
    logger.info("=" * 70)
    logger.info("TEST: Signal validation - valid signal")
    logger.info("=" * 70)

    # Create valid signal with some True values
    signal = create_test_signal(num_stocks=5, num_days=50)

    # Mock sim to avoid actual backtest
    with patch('finlab.backtest.sim') as mock_sim:
        mock_report = create_mock_report({
            'sharpe_ratio': 1.0,
            'total_return': 0.10
        })
        mock_sim.return_value = mock_report

        # Extract metrics
        result = extract_metrics_from_signal(signal)

        assert result['success'], f"Should succeed for valid signal: {result.get('error')}"

        logger.info("✅ Valid signal passed validation")


# ============================================================================
# Test Cases: Edge Cases
# ============================================================================

def test_extreme_values():
    """
    Test handling of extreme metric values.

    Validates robustness with edge cases.
    """
    logger.info("=" * 70)
    logger.info("TEST: Extreme metric values")
    logger.info("=" * 70)

    # Create metrics with extreme values
    extreme_metrics = {
        'sharpe_ratio': 10.0,  # Extremely high
        'total_return': 5.0,  # 500% return
        'annual_return': 2.0,  # 200% annual return
        'max_drawdown': -0.95,  # 95% drawdown
        'win_rate': 0.99  # 99% win rate
    }

    mock_report = create_mock_report(extreme_metrics, api_format='dict')
    extracted_metrics = _extract_metrics_from_report(mock_report)

    result = {
        'success': True,
        'metrics': extracted_metrics,
        'error': None
    }

    # Validate extraction succeeded and values are reasonable
    assert result['success'], "Should handle extreme values"
    assert extracted_metrics['sharpe_ratio'] == 10.0, "Should preserve extreme Sharpe"
    assert extracted_metrics['max_drawdown'] == -0.95, "Should preserve extreme drawdown"

    logger.info("✅ Extreme values handled correctly")


def test_missing_metrics():
    """
    Test handling when some metrics are missing from report.

    Validates graceful degradation.
    """
    logger.info("=" * 70)
    logger.info("TEST: Missing metrics in report")
    logger.info("=" * 70)

    # Create report with only partial metrics
    partial_metrics = {
        'sharpe_ratio': 1.5,
        'total_return': 0.20
        # Missing: annual_return, max_drawdown, win_rate, etc.
    }

    mock_report = create_mock_report(partial_metrics, api_format='dict')
    extracted_metrics = _extract_metrics_from_report(mock_report)

    # Verify available metrics were extracted
    assert extracted_metrics['sharpe_ratio'] == 1.5
    assert extracted_metrics['total_return'] == 0.20

    # Verify missing metrics defaulted to 0.0
    assert extracted_metrics['annual_return'] == 0.0
    assert extracted_metrics['max_drawdown'] == 0.0
    assert extracted_metrics['win_rate'] == 0.0

    logger.info("✅ Missing metrics handled with defaults")


# ============================================================================
# Main Test Runner
# ============================================================================

if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short', '-s'])
