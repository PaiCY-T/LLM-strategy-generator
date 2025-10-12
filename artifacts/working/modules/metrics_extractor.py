"""Metrics extraction from Finlab backtest results.

Executes backtests on trading signals and extracts performance metrics
for strategy ranking and feedback generation.
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


def extract_metrics_from_signal(signal: pd.DataFrame,
                                backtest_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run backtest and extract performance metrics.

    Executes a Finlab backtest on the provided trading signal and extracts
    comprehensive performance metrics for strategy evaluation.

    Args:
        signal: DataFrame with datetime index containing boolean/numeric (0/1)
               trading signals. True/1 = hold position, False/0 = no position.
        backtest_params: Optional dictionary of backtest parameters to use.
                        If None, uses DEFAULT_BACKTEST_PARAMS.
                        Common parameters: resample, stop_loss, upload, etc.

    Returns:
        Dictionary containing:
        - success (bool): Whether backtest executed successfully
        - metrics (dict): Performance metrics including:
            - total_return (float): Total return over backtest period
            - sharpe_ratio (float): Risk-adjusted return
            - max_drawdown (float): Maximum drawdown (negative value)
            - win_rate (float): Percentage of winning trades (0-1)
            - total_trades (int): Number of trades executed
            - annual_return (float): Annualized return
            - volatility (float): Annual volatility
            - calmar_ratio (float): Return / abs(MDD)
            - final_portfolio_value (float): Ending portfolio value
        - error (str or None): Error message if execution failed
        - backtest_report (Report or None): Full Finlab Report object

    Example:
        >>> signal = close.pct_change(20).is_largest(10)
        >>> result = extract_metrics_from_signal(signal)
        >>> if result['success']:
        ...     print(f"Sharpe: {result['metrics']['sharpe_ratio']:.2f}")
    """
    # Initialize return structure
    result = {
        'success': False,
        'metrics': {},
        'error': None,
        'backtest_report': None
    }

    # Validate signal format
    validation_error = _validate_signal(signal)
    if validation_error:
        result['error'] = validation_error
        return result

    try:
        # Import Finlab backtest
        from finlab.backtest import sim

        # Use provided parameters or fall back to defaults
        if backtest_params is None:
            params = DEFAULT_BACKTEST_PARAMS.copy()
            logger.info(f"Running backtest with default parameters: {params}")
        else:
            params = backtest_params.copy()
            logger.info(f"Running backtest with provided parameters: {params}")

        # Execute backtest with specified parameters
        report = sim(signal, **params)

        # Extract metrics from report
        metrics = _extract_metrics_from_report(report)

        result['success'] = True
        result['metrics'] = metrics
        result['backtest_report'] = report

        logger.info(f"Backtest successful: {len(metrics)} metrics extracted")
        return result

    except ImportError as e:
        error_msg = f"Failed to import finlab.backtest: {e}"
        logger.error(error_msg)
        result['error'] = error_msg
        return result

    except Exception as e:
        error_msg = f"Backtest execution failed: {type(e).__name__}: {str(e)}"
        logger.error(error_msg)
        result['error'] = error_msg

        # Try to extract partial metrics even on error
        if 'report' in locals():
            try:
                result['metrics'] = _extract_metrics_from_report(report)
            except Exception as extraction_error:
                logger.warning(f"Metric extraction also failed: {extraction_error}")

        return result


def _validate_signal(signal: pd.DataFrame) -> Optional[str]:
    """Validate signal DataFrame format.

    Args:
        signal: Trading signal DataFrame to validate

    Returns:
        Error message if validation fails, None if valid
    """
    # Check if input is DataFrame
    if not isinstance(signal, pd.DataFrame):
        return f"Signal must be pd.DataFrame, got {type(signal).__name__}"

    # Check if DataFrame is empty
    if signal.empty:
        return "Signal DataFrame is empty"

    # Check for datetime index
    if not isinstance(signal.index, pd.DatetimeIndex):
        return f"Signal must have DatetimeIndex, got {type(signal.index).__name__}"

    # Check for NaN/inf values
    if signal.isnull().any().any():
        nan_count = signal.isnull().sum().sum()
        logger.warning(f"Signal contains {nan_count} NaN values")

    if np.isinf(signal.select_dtypes(include=[np.number]).values).any():
        return "Signal contains infinite values"

    # Check if signal has any True/1 values (not empty signal)
    if signal.sum().sum() == 0:
        return ("Signal has no positions (all False/0). "
                "Check if data.get() calls are returning valid data. "
                "Debug: Verify dataset keys are correct and data exists for the time period.")

    return None


def _safe_extract_metric(value: Any, metric_name: str = 'metric') -> float:
    """Safely extract metric value from either float or dict format.

    Handles API evolution in finlab where metrics changed from returning
    floats to returning dicts with 'strategy' and 'benchmark' keys.

    Args:
        value: Either a float/int or a dict with 'strategy' key
        metric_name: Name of metric for logging purposes

    Returns:
        float: The extracted metric value, or 0.0 if extraction fails

    Example:
        >>> _safe_extract_metric(1.23, 'sharpe')
        1.23
        >>> _safe_extract_metric({'strategy': 1.23, 'benchmark': 0.5}, 'sharpe')
        1.23
        >>> _safe_extract_metric({'invalid': 1.23}, 'sharpe')
        0.0
    """
    try:
        if isinstance(value, (int, float)):
            # Old API: direct float value
            logger.debug(f"{metric_name}: float format detected, value={value}")
            return float(value)
        elif isinstance(value, dict):
            # New API: dict with 'strategy' key
            if 'strategy' in value:
                extracted_value = float(value['strategy'])
                logger.info(f"{metric_name}: dict format detected, extracted strategy value={extracted_value}")
                return extracted_value
            else:
                logger.warning(f"{metric_name}: dict format missing 'strategy' key. Keys: {list(value.keys())}, using 0.0")
                return 0.0
        elif value is None:
            logger.debug(f"{metric_name}: None value, using 0.0")
            return 0.0
        else:
            logger.warning(f"{metric_name}: unexpected type {type(value).__name__}, using 0.0")
            return 0.0
    except Exception as e:
        logger.error(f"Error extracting {metric_name}: {type(e).__name__}: {e}")
        return 0.0


def _detect_suspicious_metrics(metrics: dict) -> list:
    """
    Detect suspicious metric patterns that indicate extraction failures.

    Args:
        metrics: Dictionary containing extracted metrics

    Returns:
        List of warning messages for suspicious patterns detected
    """
    warnings = []

    # Get key metrics
    sharpe = metrics.get('sharpe_ratio', 0.0)
    annual_return = metrics.get('annual_return', 0.0)
    max_drawdown = metrics.get('max_drawdown', 0.0)
    trades = metrics.get('total_trades', 0)

    # Pattern 1: Trades > 0 but Sharpe = 0
    if trades > 0 and sharpe == 0.0:
        warnings.append(f"Suspicious: {trades} trades but Sharpe = 0.0 (extraction failure?)")

    # Pattern 2: Trades > 0 but annual_return = 0
    if trades > 0 and annual_return == 0.0:
        warnings.append(f"Suspicious: {trades} trades but annual_return = 0.0 (extraction failure?)")

    # Pattern 3: Trades > 0 but max_drawdown = 0 (unrealistic)
    if trades > 0 and max_drawdown == 0.0:
        warnings.append(f"Suspicious: {trades} trades but max_drawdown = 0.0 (unrealistic)")

    # Pattern 4: All core metrics are zero but trades > 0
    if trades > 0 and sharpe == 0.0 and annual_return == 0.0 and max_drawdown == 0.0:
        warnings.append(f"CRITICAL: All metrics = 0.0 but {trades} trades (total extraction failure)")

    return warnings


def _extract_metrics_from_report(report: Any) -> Dict[str, float]:
    """Extract performance metrics from Finlab Report object.

    Handles both old and new finlab API formats:
    - Old API: metrics are floats (e.g., report.sharpe = 1.23)
    - New API: metrics are dicts (e.g., report.sharpe = {'strategy': 1.23, 'benchmark': 0.5})

    Args:
        report: Finlab backtest Report object

    Returns:
        Dictionary of performance metrics with default values for missing metrics
    """
    metrics = {
        'total_return': 0.0,
        'sharpe_ratio': 0.0,
        'max_drawdown': 0.0,
        'win_rate': 0.0,
        'total_trades': 0,
        'annual_return': 0.0,
        'volatility': 0.0,
        'calmar_ratio': 0.0,
        'final_portfolio_value': 1.0
    }

    extraction_method_used = None

    try:
        # Method 1: Try final_stats dict (most common)
        if hasattr(report, 'final_stats'):
            logger.info("Attempting extraction: Method 1 (final_stats dict)")
            stats = report.final_stats
            if isinstance(stats, dict):
                # Map finlab metric names to our standard names using safe extraction
                metrics['total_return'] = _safe_extract_metric(
                    stats.get('total_return', 0.0), 'total_return')
                metrics['sharpe_ratio'] = _safe_extract_metric(
                    stats.get('sharpe_ratio', 0.0), 'sharpe_ratio')
                metrics['max_drawdown'] = _safe_extract_metric(
                    stats.get('max_drawdown', 0.0), 'max_drawdown')
                metrics['win_rate'] = _safe_extract_metric(
                    stats.get('win_rate', 0.0), 'win_rate')
                metrics['annual_return'] = _safe_extract_metric(
                    stats.get('annual_return', 0.0), 'annual_return')
                metrics['volatility'] = _safe_extract_metric(
                    stats.get('volatility', 0.0), 'volatility')

                # Calculate derived metrics
                if metrics['max_drawdown'] != 0:
                    metrics['calmar_ratio'] = metrics['annual_return'] / abs(metrics['max_drawdown'])

                extraction_method_used = "final_stats"
                logger.info("✅ Extraction Method: final_stats dict (primary method)")

        # Method 2: Try get_stats() method (alternative API)
        elif hasattr(report, 'get_stats'):
            logger.info("Attempting extraction: Method 2 (get_stats() method)")
            try:
                metrics['total_return'] = _safe_extract_metric(
                    report.get_stats('Return'), 'total_return')
                metrics['sharpe_ratio'] = _safe_extract_metric(
                    report.get_stats('Sharpe'), 'sharpe_ratio')
                metrics['max_drawdown'] = _safe_extract_metric(
                    report.get_stats('MDD'), 'max_drawdown')

                # Try additional metrics
                for stat_name, metric_key in [
                    ('Annual Return', 'annual_return'),
                    ('Volatility', 'volatility'),
                    ('Win Rate', 'win_rate')
                ]:
                    try:
                        value = report.get_stats(stat_name)
                        if value is not None:
                            metrics[metric_key] = _safe_extract_metric(value, metric_key)
                    except (KeyError, AttributeError):
                        pass

                # Calculate calmar ratio
                if metrics['max_drawdown'] != 0:
                    metrics['calmar_ratio'] = metrics['annual_return'] / abs(metrics['max_drawdown'])

                extraction_method_used = "get_stats"
                logger.info("⚠️ Extraction Method: get_stats() method (alternative API)")
            except Exception as e:
                logger.warning(f"get_stats() method failed: {e}")
                logger.info("Falling back to Method 3 (direct attributes)")

        # Method 3: Try direct attributes
        else:
            logger.warning("Report has neither final_stats nor get_stats()")
            logger.info("Attempting extraction: Method 3 (direct attributes)")
            for attr in dir(report):
                if not attr.startswith('_'):
                    try:
                        value = getattr(report, attr)
                        # Use safe extraction to handle both float and dict formats
                        attr_lower = attr.lower()
                        if 'return' in attr_lower and 'annual' in attr_lower:
                            metrics['annual_return'] = _safe_extract_metric(value, 'annual_return')
                        elif 'return' in attr_lower and 'total' in attr_lower:
                            metrics['total_return'] = _safe_extract_metric(value, 'total_return')
                        elif 'sharpe' in attr_lower:
                            metrics['sharpe_ratio'] = _safe_extract_metric(value, 'sharpe_ratio')
                        elif 'drawdown' in attr_lower or 'mdd' in attr_lower:
                            metrics['max_drawdown'] = _safe_extract_metric(value, 'max_drawdown')
                    except Exception:
                        pass
            extraction_method_used = "direct_attributes"
            logger.info("⚠️ Extraction Method: direct attributes (fallback method)")

        # Try to extract trade count from report
        if hasattr(report, 'trades'):
            try:
                metrics['total_trades'] = len(report.trades)
            except Exception:
                pass

        # Try to extract final portfolio value
        if hasattr(report, 'final_value'):
            try:
                metrics['final_portfolio_value'] = float(report.final_value)
            except Exception:
                pass

        # Ensure all metrics are valid numbers (no NaN/inf)
        for key, value in metrics.items():
            if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                logger.warning(f"Invalid metric value for {key}: {value}, setting to 0.0")
                metrics[key] = 0.0

        # Log successful extraction summary
        if extraction_method_used:
            logger.info(f"📊 Successfully extracted {len(metrics)} metrics using {extraction_method_used} method")

        # Task 15: Detect suspicious metric patterns
        suspicious_warnings = _detect_suspicious_metrics(metrics)
        if suspicious_warnings:
            logger.warning("Suspicious metrics detected:")
            for warning in suspicious_warnings:
                logger.warning(f"  - {warning}")
            logger.warning("Metrics extraction may have failed. Review report capture and API compatibility.")

        return metrics

    except Exception as e:
        logger.error(f"Metric extraction failed: {e}")
        if extraction_method_used:
            logger.error(f"Failed during {extraction_method_used} method")
        # Return default metrics on error
        return metrics


# Default backtest parameters
DEFAULT_BACKTEST_PARAMS = {
    'resample': 'D',      # Daily rebalancing
    'stop_loss': 0.1,     # 10% stop loss
    'upload': False       # Don't upload to cloud
}


def get_default_params() -> Dict[str, Any]:
    """Get default backtest parameters.

    Returns:
        Dictionary of default backtest parameters
    """
    return DEFAULT_BACKTEST_PARAMS.copy()
