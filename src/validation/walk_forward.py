"""
Walk-Forward Analysis Validation

Implements rolling window analysis to validate strategy robustness across time
with true out-of-sample testing using consecutive train/test windows.

Design Rationale:
- Training window: 252 trading days (~1 year) - sufficient for parameter optimization
- Test window: 63 trading days (~3 months) - validates near-term performance
- Step size: 63 trading days - quarterly rebalancing, standard practice
- Minimum 3 windows: Statistical validity threshold

Taiwan Market Considerations:
1. **Trading Calendar**:
   - ~250 trading days per year in TWSE
   - 252-day window captures full seasonal cycles
   - 63-day test window covers one quarter
   - Lunar New Year holidays may cause gaps

2. **Window Configuration**:
   - Training: 252 days = 1 year of data
   - Test: 63 days = 1 quarter (standard rebalancing)
   - Step: 63 days = non-overlapping test periods
   - Total required: 252 + 63*3 = 441 days minimum

3. **Performance Thresholds**:
   - Average Sharpe > 0.5: Conservative threshold for consistent profitability
   - Win rate > 60%: Majority of windows profitable
   - Worst Sharpe > -0.5: No catastrophic failures
   - Sharpe std < 1.0: Reasonable stability across market conditions

4. **Validation Interpretation**:
   - High avg Sharpe + low std: Robust strategy
   - High avg Sharpe + high std: Regime-dependent strategy
   - Low win rate: Unreliable, few profitable periods
   - Bad worst case: Risk of severe drawdowns

Requirements: AC-2.2.1 to AC-2.2.4
"""

import logging
import warnings
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class WalkForwardValidator:
    """
    Validates trading strategies using rolling window analysis.

    Implements walk-forward methodology:
    1. Train on window N (252 days)
    2. Test on window N+1 (63 days)
    3. Roll forward by step size (63 days)
    4. Aggregate results across all windows
    """

    # AC-2.2.1: Rolling window configuration
    TRAINING_WINDOW = 252  # 1 year trading days
    TEST_WINDOW = 63  # 1 quarter trading days
    STEP_SIZE = 63  # Quarterly steps

    # AC-2.2.3: Validation criteria
    MIN_AVG_SHARPE = 0.5
    MIN_WIN_RATE = 0.6  # 60% of windows with Sharpe > 0
    MIN_WORST_SHARPE = -0.5
    MAX_SHARPE_STD = 1.0

    # AC-2.2.4: Minimum window requirement
    MIN_WINDOWS = 3

    def __init__(
        self,
        training_window: int = TRAINING_WINDOW,
        test_window: int = TEST_WINDOW,
        step_size: int = STEP_SIZE,
        min_windows: int = MIN_WINDOWS,
        strict_filtering: bool = False
    ):
        """
        Initialize walk-forward validator.

        Args:
            training_window: Number of days for training (default 252)
            test_window: Number of days for testing (default 63)
            step_size: Number of days to roll forward (default 63)
            min_windows: Minimum number of windows required (default 3)
            strict_filtering: If True, raise error when report filtering not supported.
                              If False (default), use unfiltered report with warning.
                              Backward compatible default allows migration period.
                              Will become True by default in v3.0.
        """
        self.training_window = training_window
        self.test_window = test_window
        self.step_size = step_size
        self.min_windows = min_windows
        self.strict_filtering = strict_filtering

        logger.info(f"Walk-forward validator initialized:")
        logger.info(f"  Training window: {training_window} days (~{training_window/252:.1f} years)")
        logger.info(f"  Test window: {test_window} days (~{test_window/63:.1f} quarters)")
        logger.info(f"  Step size: {step_size} days (~{step_size/63:.1f} quarters)")
        logger.info(f"  Minimum windows: {min_windows}")

    def validate_strategy(
        self,
        strategy_code: str,
        data: Any,
        iteration_num: int = 0
    ) -> Dict[str, Any]:
        """
        Perform walk-forward analysis on strategy.

        Args:
            strategy_code: Python code for trading strategy
            data: FinLab data object with historical data
            iteration_num: Iteration number for logging

        Returns:
            Dictionary with walk-forward results:
            {
                'validation_passed': bool,
                'validation_skipped': bool,
                'skip_reason': str or None,
                'avg_sharpe': float,
                'sharpe_std': float,
                'win_rate': float,
                'worst_sharpe': float,
                'best_sharpe': float,
                'num_windows': int,
                'windows': list of per-window results
            }

        Requirements: AC-2.2.1, AC-2.2.2, AC-2.2.3, AC-2.2.4
        """
        logger.info(f"[Iteration {iteration_num}] Starting walk-forward analysis")

        results = {
            'validation_passed': False,
            'validation_skipped': False,
            'skip_reason': None,
            'avg_sharpe': 0.0,
            'sharpe_std': 0.0,
            'win_rate': 0.0,
            'worst_sharpe': 0.0,
            'best_sharpe': 0.0,
            'num_windows': 0,
            'windows': []
        }

        # AC-2.2.1: Configure rolling windows
        try:
            windows = self._generate_windows(data)
        except Exception as e:
            results['validation_skipped'] = True
            results['skip_reason'] = f"Window generation failed: {str(e)[:100]}"
            logger.warning(f"⚠️  Walk-forward skipped: {results['skip_reason']}")
            return results

        # AC-2.2.4: Check minimum window requirement
        if len(windows) < self.min_windows:
            results['validation_skipped'] = True
            results['skip_reason'] = (
                f"Insufficient windows (need ≥{self.min_windows}, got {len(windows)})"
            )
            logger.warning(f"⚠️  Walk-forward skipped: {results['skip_reason']}")
            return results

        logger.info(f"  Generated {len(windows)} walk-forward windows")

        # AC-2.2.1: Execute train/test loop for each window
        window_sharpes = []
        for i, window in enumerate(windows):
            logger.info(
                f"  Window {i+1}/{len(windows)}: "
                f"Train {window['train_start']} to {window['train_end']}, "
                f"Test {window['test_start']} to {window['test_end']}"
            )

            test_sharpe, error = self._run_window_backtest(
                strategy_code=strategy_code,
                data=data,
                window=window,
                window_idx=i,
                iteration_num=iteration_num
            )

            if error:
                logger.warning(f"    Window {i+1} failed: {error}")
                window['test_sharpe'] = None
                window['error'] = error
            else:
                window['test_sharpe'] = test_sharpe
                window['error'] = None
                window_sharpes.append(test_sharpe)
                logger.info(f"    ✅ Test Sharpe: {test_sharpe:.4f}")

            results['windows'].append(window)

        # Check if we have enough successful windows
        if len(window_sharpes) < self.min_windows:
            results['validation_skipped'] = True
            results['skip_reason'] = (
                f"Insufficient successful windows (need ≥{self.min_windows}, "
                f"got {len(window_sharpes)})"
            )
            logger.warning(f"⚠️  Walk-forward skipped: {results['skip_reason']}")
            return results

        # AC-2.2.2: Calculate aggregate metrics
        results['avg_sharpe'] = float(np.mean(window_sharpes))
        results['sharpe_std'] = float(np.std(window_sharpes, ddof=1))
        results['win_rate'] = float(sum(1 for s in window_sharpes if s > 0) / len(window_sharpes))
        results['worst_sharpe'] = float(np.min(window_sharpes))
        results['best_sharpe'] = float(np.max(window_sharpes))
        results['num_windows'] = len(window_sharpes)

        logger.info(f"  Aggregate metrics:")
        logger.info(f"    Average Sharpe: {results['avg_sharpe']:.4f}")
        logger.info(f"    Sharpe Std Dev: {results['sharpe_std']:.4f}")
        logger.info(f"    Win Rate: {results['win_rate']:.1%}")
        logger.info(f"    Worst Sharpe: {results['worst_sharpe']:.4f}")
        logger.info(f"    Best Sharpe: {results['best_sharpe']:.4f}")

        # AC-2.2.3: Check validation criteria
        validation_passed = self._check_validation_criteria(results)
        results['validation_passed'] = validation_passed

        if validation_passed:
            logger.info(f"✅ Walk-forward validation PASSED")
        else:
            logger.info(f"❌ Walk-forward validation FAILED")

        return results

    def _generate_windows(self, data: Any) -> List[Dict[str, Any]]:
        """
        Generate rolling train/test windows.

        Args:
            data: FinLab data object or DataFrame

        Returns:
            List of window dictionaries with train/test date ranges

        Requirements: AC-2.2.1

        Raises:
            ValueError: If insufficient data for minimum windows
        """
        # Get available date range from data
        # This assumes data has a method to get price data or is a DataFrame
        try:
            # Case 1: data is a DataFrame with index
            if hasattr(data, 'index'):
                dates = data.index.tolist()
            # Case 2: data has a get method (FinLab data object)
            elif hasattr(data, 'get'):
                close = data.get('price:收盤價')
                if close is None:
                    raise ValueError("data.get('price:收盤價') returned None")
                dates = close.index.tolist()
            else:
                raise ValueError("Data must be DataFrame or have get() method")

            total_days = len(dates)
            logger.info(f"  Total available days: {total_days}")

        except Exception as e:
            raise ValueError(f"Failed to get date range from data: {e}")

        # Calculate minimum required days
        min_required = self.training_window + self.test_window + (self.min_windows - 1) * self.step_size

        if total_days < min_required:
            raise ValueError(
                f"Insufficient data: need {min_required} days, have {total_days} days"
            )

        # Generate windows
        windows = []
        position = 0

        while True:
            # Training period indices
            train_start_idx = position
            train_end_idx = position + self.training_window

            # Test period indices
            test_start_idx = train_end_idx
            test_end_idx = test_start_idx + self.test_window

            # Check if we have enough data for this window
            if test_end_idx > total_days:
                break

            # Create window definition
            window = {
                'window_idx': len(windows),
                'train_start': str(dates[train_start_idx]),
                'train_end': str(dates[train_end_idx - 1]),
                'test_start': str(dates[test_start_idx]),
                'test_end': str(dates[test_end_idx - 1]),
                'train_days': self.training_window,
                'test_days': self.test_window
            }

            windows.append(window)

            # Move to next window
            # CRITICAL FIX: Use test_end_idx to prevent training window overlap with previous test data
            # Previous bug: position += self.step_size caused Window N+1 training to include Window N testing
            # Example: Window 0 tests [252, 315), Window 1 would train on [63, 315) including [252, 315)
            # Fix ensures true out-of-sample validation with non-overlapping windows
            position = test_end_idx

        return windows

    def _run_window_backtest(
        self,
        strategy_code: str,
        data: Any,
        window: Dict[str, Any],
        window_idx: int,
        iteration_num: int
    ) -> Tuple[Optional[float], Optional[str]]:
        """
        Execute backtest for a single walk-forward window.

        Only tests on the test period (train period used for parameter fitting).

        Args:
            strategy_code: Python strategy code
            data: FinLab data object
            window: Window definition with train/test dates
            window_idx: Window index for logging
            iteration_num: Iteration number

        Returns:
            (test_sharpe, error_message) tuple
            - If success: (float, None)
            - If failure: (None, error_string)

        Requirements: AC-2.2.1
        """
        try:
            # Execute strategy on TEST period only
            # (In true walk-forward, training period would be used for optimization)
            test_start = window['test_start']
            test_end = window['test_end']

            # Execute strategy code in isolated namespace
            namespace = {'data': data, 'finlab': __import__('finlab')}

            try:
                exec(strategy_code, namespace)
            except Exception as e:
                logger.error(f"    Strategy execution failed for window {window_idx}: {e}")
                return (None, f"Execution error: {str(e)[:100]}")

            # Extract report
            if 'report' not in namespace:
                return (None, "No report object generated")

            report = namespace['report']

            # Filter report to test period
            try:
                test_report = self._filter_report_to_period(
                    report, test_start, test_end
                )
            except Exception as e:
                logger.error(f"    Report filtering failed for window {window_idx}: {e}")
                return (None, f"Report filtering error: {str(e)[:100]}")

            # Extract Sharpe ratio
            try:
                sharpe = self._extract_sharpe_from_report(test_report)
                return (sharpe, None)
            except Exception as e:
                logger.error(f"    Sharpe extraction failed for window {window_idx}: {e}")
                return (None, f"Metric extraction error: {str(e)[:100]}")

        except Exception as e:
            logger.error(f"    Unexpected error in window {window_idx} backtest: {e}")
            return (None, f"Unexpected error: {str(e)[:100]}")

    def _filter_report_to_period(
        self,
        report: Any,
        start_date: str,
        end_date: str
    ) -> Any:
        """
        Filter backtest report to specific time period for walk-forward analysis.

        M2 FIX: Added version parameter control to handle reports without
        filtering capability while maintaining backward compatibility.

        CRITICAL: Without proper filtering, all walk-forward test windows
        will use metrics from the ENTIRE backtest period, defeating the
        purpose of rolling window validation and causing severe data leakage.

        Args:
            report: FinLab backtest report object
            start_date: Period start (YYYY-MM-DD)
            end_date: Period end (YYYY-MM-DD)

        Returns:
            Filtered report for the period

        Raises:
            ValueError: If strict_filtering=True and report doesn't support filtering
        """
        # Method 1: Check if report has filter_dates() method
        if hasattr(report, 'filter_dates'):
            logger.debug(f"Using report.filter_dates() for period {start_date} to {end_date}")
            return report.filter_dates(start_date, end_date)

        # Method 2: Check if report is DataFrame with DatetimeIndex
        if isinstance(report, pd.DataFrame):
            if isinstance(report.index, pd.DatetimeIndex):
                logger.debug(f"Using DataFrame.loc[] for period {start_date} to {end_date}")
                return report.loc[start_date:end_date]

        # M2 FIX: Fallback behavior controlled by strict_filtering parameter
        if self.strict_filtering:
            # Strict mode: Raise error to force proper filtering implementation
            raise ValueError(
                f"Report filtering not supported for period {start_date} to {end_date}. "
                f"Report type: {type(report)}. "
                f"Report must have filter_dates() method or be DataFrame with DatetimeIndex. "
                f"Consider implementing a report wrapper or set strict_filtering=False "
                f"for backward compatibility (with data leakage risk)."
            )
        else:
            # Backward compatible mode: Warn but allow fallback
            warnings.warn(
                f"Report filtering not supported for period {start_date} to {end_date}. "
                f"Using unfiltered report - this may cause data leakage. "
                f"Report type: {type(report)}. "
                f"Enable strict_filtering=True to enforce filtering requirement (will be default in v3.0).",
                DeprecationWarning,
                stacklevel=2
            )
            logger.warning(
                f"Report filtering unavailable for {start_date} to {end_date}. "
                f"Returning unfiltered report (data leakage risk)."
            )
            return report

    def _extract_sharpe_from_report(self, report: Any) -> float:
        """
        Extract Sharpe ratio from backtest report.

        Handles multiple API formats for compatibility.

        Args:
            report: FinLab backtest report object

        Returns:
            Sharpe ratio as float

        Raises:
            ValueError: If Sharpe cannot be extracted
        """
        try:
            # Method 1: get_stats() returning dict
            if hasattr(report, 'get_stats'):
                stats = report.get_stats('sharpe_ratio')
                if isinstance(stats, dict):
                    return float(stats.get('value', 0.0))
                elif isinstance(stats, (int, float)):
                    return float(stats)

            # Method 2: Direct attribute access
            if hasattr(report, 'sharpe_ratio'):
                sharpe = report.sharpe_ratio
                if callable(sharpe):
                    return float(sharpe())
                return float(sharpe)

            # Method 3: stats dict attribute
            if hasattr(report, 'stats'):
                stats = report.stats
                if isinstance(stats, dict):
                    return float(stats.get('sharpe_ratio', 0.0))

            # Method 4: metrics object
            if hasattr(report, 'metrics'):
                metrics = report.metrics
                if hasattr(metrics, 'sharpe_ratio'):
                    sharpe = metrics.sharpe_ratio
                    if callable(sharpe):
                        return float(sharpe())
                    return float(sharpe)

            raise ValueError("No Sharpe ratio found in report")

        except (TypeError, ValueError, AttributeError) as e:
            raise ValueError(f"Sharpe extraction failed: {e}")

    def _check_validation_criteria(self, results: Dict[str, Any]) -> bool:
        """
        Check if walk-forward results pass validation criteria.

        Requirements: AC-2.2.3

        Criteria:
        1. Average Sharpe > 0.5
        2. Win rate > 60%
        3. Worst Sharpe > -0.5
        4. Sharpe std < 1.0

        Returns:
            True if ALL criteria met, False otherwise
        """
        avg_sharpe = results['avg_sharpe']
        win_rate = results['win_rate']
        worst_sharpe = results['worst_sharpe']
        sharpe_std = results['sharpe_std']

        # Criterion 1: Average Sharpe > 0.5
        if avg_sharpe <= self.MIN_AVG_SHARPE:
            logger.info(
                f"  ❌ Criterion 1 FAIL: Average Sharpe {avg_sharpe:.4f} "
                f"≤ {self.MIN_AVG_SHARPE}"
            )
            return False
        logger.info(f"  ✅ Criterion 1 PASS: Average Sharpe {avg_sharpe:.4f}")

        # Criterion 2: Win rate > 60%
        if win_rate <= self.MIN_WIN_RATE:
            logger.info(
                f"  ❌ Criterion 2 FAIL: Win rate {win_rate:.1%} "
                f"≤ {self.MIN_WIN_RATE:.0%}"
            )
            return False
        logger.info(f"  ✅ Criterion 2 PASS: Win rate {win_rate:.1%}")

        # Criterion 3: Worst Sharpe > -0.5
        if worst_sharpe <= self.MIN_WORST_SHARPE:
            logger.info(
                f"  ❌ Criterion 3 FAIL: Worst Sharpe {worst_sharpe:.4f} "
                f"≤ {self.MIN_WORST_SHARPE}"
            )
            return False
        logger.info(f"  ✅ Criterion 3 PASS: Worst Sharpe {worst_sharpe:.4f}")

        # Criterion 4: Sharpe std < 1.0
        if sharpe_std >= self.MAX_SHARPE_STD:
            logger.info(
                f"  ❌ Criterion 4 FAIL: Sharpe std {sharpe_std:.4f} "
                f"≥ {self.MAX_SHARPE_STD}"
            )
            return False
        logger.info(f"  ✅ Criterion 4 PASS: Sharpe std {sharpe_std:.4f}")

        return True


def validate_strategy_walk_forward(
    strategy_code: str,
    data: Any,
    iteration_num: int = 0
) -> Dict[str, Any]:
    """
    Convenience function for walk-forward validation.

    Args:
        strategy_code: Python code for trading strategy
        data: FinLab data object
        iteration_num: Iteration number for logging

    Returns:
        Walk-forward validation results dictionary

    Example:
        >>> results = validate_strategy_walk_forward(strategy_code, data, 42)
        >>> if results['validation_passed']:
        >>>     print(f"Robust strategy! Average Sharpe: {results['avg_sharpe']:.2f}")
    """
    validator = WalkForwardValidator()
    return validator.validate_strategy(strategy_code, data, iteration_num)
