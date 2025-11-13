"""
Train/Validation/Test Data Split Validation

Implements temporal data splitting for strategy validation to detect overfitting
and ensure strategies generalize to unseen data.

Design Rationale:
- Training (2018-2020): 3 years capturing bull/bear cycles
- Validation (2021-2022): 2 years covering market volatility
- Test (2023-2024): 2 years hold-out for final evaluation
- Taiwan market: Uses TW stock market trading calendar

Taiwan Market Considerations:
1. **Market Structure (2018-2024)**:
   - Training period (2018-2020): Includes 2018 trade war volatility,
     2019 recovery, and 2020 COVID crash - captures diverse market conditions
   - Validation period (2021-2022): Post-COVID recovery with high inflation
     and Fed rate hike cycles - tests strategy resilience
   - Test period (2023-2024): Normalization phase with AI boom impact -
     provides recent market validation

2. **Trading Calendar**:
   - Taiwan Stock Exchange (TWSE) has ~250 trading days per year
   - Lunar New Year holidays cause data gaps (typically late Jan/early Feb)
   - Training period: ~750 trading days (sufficient for 252-day metrics)
   - Validation period: ~500 trading days
   - Test period: ~500 trading days

3. **Market Characteristics**:
   - Taiwan market is export-driven, sensitive to global semiconductor demand
   - High retail participation (~70% of trading volume)
   - TAIEX correlation with US markets: ~0.6-0.7
   - Currency risk: TWD/USD fluctuations affect returns

4. **Data Quality Considerations**:
   - FinLab data availability: 2018+ has high quality coverage
   - Pre-2018 data may have survivorship bias and incomplete coverage
   - Recent data (2023-2024) includes AI/semiconductor boom effects
   - Liquidity filters are critical (use ≥100M TWD daily volume threshold)

5. **Period Selection Rationale**:
   - 3-year training: Captures full business cycle (expansion + contraction)
   - 2-year validation: Sufficient for statistical significance (500 days)
   - 2-year test: Recent enough to reflect current market regime
   - No overlap: Ensures true out-of-sample validation

6. **Consistency Score Interpretation**:
   - High consistency (>0.8): Strategy robust across market regimes
   - Medium consistency (0.6-0.8): Acceptable with regime awareness
   - Low consistency (<0.6): Likely overfit to specific market conditions
   - Taiwan market volatility higher than US, expect consistency 0.65-0.85

7. **Validation Thresholds Calibration**:
   - Min Sharpe 1.0: Appropriate for Taiwan market (risk-free rate ~1%)
   - Min consistency 0.6: Accounts for Taiwan's higher volatility
   - Degradation ratio 0.7: Allows 30% performance drop (realistic)

Requirements: AC-2.1.1 to AC-2.1.6
"""

import logging
import warnings
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataSplitValidator:
    """
    Validates trading strategies using train/validation/test temporal split.

    Prevents overfitting by testing on separate time periods and measuring
    consistency across different market conditions.
    """

    # AC-2.1.1: Fixed date ranges for temporal validation
    TRAIN_START = "2018-01-01"
    TRAIN_END = "2020-12-31"

    VALIDATION_START = "2021-01-01"
    VALIDATION_END = "2022-12-31"

    TEST_START = "2023-01-01"
    TEST_END = "2024-12-31"

    # AC-2.1.3: Validation pass criteria
    MIN_VALIDATION_SHARPE = 1.0
    MIN_CONSISTENCY = 0.6
    MIN_DEGRADATION_RATIO = 0.7  # Validation Sharpe >= Training Sharpe * 0.7

    # AC-2.1.5: Error handling - minimum trading days
    MIN_TRADING_DAYS = 252

    def __init__(self, epsilon: float = 0.1, strict_filtering: bool = False):
        """
        Initialize validator with period configurations.

        Args:
            epsilon: Minimum acceptable mean Sharpe for consistency calculation.
                     Rejects consistently losing or near-zero strategies.
                     Default 0.1 prevents numerical instability.
            strict_filtering: If True, raise error when report filtering not supported.
                              If False (default), use unfiltered report with warning.
                              Backward compatible default allows migration period.
                              Will become True by default in v3.0.
        """
        self.periods = {
            'training': (self.TRAIN_START, self.TRAIN_END),
            'validation': (self.VALIDATION_START, self.VALIDATION_END),
            'test': (self.TEST_START, self.TEST_END)
        }
        self.epsilon = epsilon
        self.strict_filtering = strict_filtering

    def validate_strategy(
        self,
        strategy_code: str,
        data: Any,
        iteration_num: int = 0
    ) -> Dict[str, Any]:
        """
        Validate strategy using train/validation/test split.

        Args:
            strategy_code: Python code for trading strategy
            data: FinLab data object with historical data
            iteration_num: Iteration number for logging

        Returns:
            Dictionary with validation results:
            {
                'validation_passed': bool,
                'validation_skipped': bool,
                'skip_reason': str or None,
                'sharpes': {
                    'training': float,
                    'validation': float,
                    'test': float
                },
                'consistency': float,
                'degradation_ratio': float,
                'periods_tested': list,
                'periods_skipped': list
            }

        Requirements: AC-2.1.1, AC-2.1.2, AC-2.1.3, AC-2.1.5, AC-2.1.6
        """
        logger.info(f"[Iteration {iteration_num}] Starting data split validation")

        results = {
            'validation_passed': False,
            'validation_skipped': False,
            'skip_reason': None,
            'sharpes': {},
            'consistency': 0.0,
            'degradation_ratio': 0.0,
            'periods_tested': [],
            'periods_skipped': []
        }

        # AC-2.1.1: Execute backtest on all three periods
        for period_name, (start_date, end_date) in self.periods.items():
            logger.info(f"  Testing {period_name} period: {start_date} to {end_date}")

            sharpe, error = self._run_period_backtest(
                strategy_code=strategy_code,
                data=data,
                start_date=start_date,
                end_date=end_date,
                period_name=period_name,
                iteration_num=iteration_num
            )

            if error:
                # AC-2.1.5, AC-2.1.6: Error handling
                logger.warning(f"  {period_name} period skipped: {error}")
                results['periods_skipped'].append({
                    'period': period_name,
                    'reason': error
                })
                results['sharpes'][period_name] = None
            else:
                results['periods_tested'].append(period_name)
                results['sharpes'][period_name] = sharpe
                logger.info(f"  ✅ {period_name} Sharpe: {sharpe:.4f}")

        # Check if we have enough periods to validate
        if len(results['periods_tested']) < 2:
            results['validation_skipped'] = True
            results['skip_reason'] = f"Insufficient periods tested (need ≥2, got {len(results['periods_tested'])})"
            logger.warning(f"⚠️  Validation skipped: {results['skip_reason']}")
            return results

        # AC-2.1.2: Calculate consistency score
        sharpe_values = [s for s in results['sharpes'].values() if s is not None]
        results['consistency'] = self._calculate_consistency(sharpe_values)
        logger.info(f"  Consistency score: {results['consistency']:.4f}")

        # Calculate degradation ratio (validation vs training)
        training_sharpe = results['sharpes'].get('training')
        validation_sharpe = results['sharpes'].get('validation')

        if training_sharpe and validation_sharpe and training_sharpe > 0:
            results['degradation_ratio'] = validation_sharpe / training_sharpe
            logger.info(f"  Degradation ratio: {results['degradation_ratio']:.4f}")
        else:
            results['degradation_ratio'] = 0.0

        # AC-2.1.3: Check validation pass criteria
        validation_passed = self._check_validation_criteria(results)
        results['validation_passed'] = validation_passed

        if validation_passed:
            logger.info(f"✅ Validation PASSED")
        else:
            logger.info(f"❌ Validation FAILED")

        return results

    def _run_period_backtest(
        self,
        strategy_code: str,
        data: Any,
        start_date: str,
        end_date: str,
        period_name: str,
        iteration_num: int
    ) -> Tuple[Optional[float], Optional[str]]:
        """
        Execute backtest for a specific time period.

        Args:
            strategy_code: Python strategy code
            data: FinLab data object
            start_date: Period start date (YYYY-MM-DD)
            end_date: Period end date (YYYY-MM-DD)
            period_name: Period identifier for logging
            iteration_num: Iteration number

        Returns:
            (sharpe_ratio, error_message) tuple
            - If success: (float, None)
            - If failure: (None, error_string)

        Requirements: AC-2.1.5, AC-2.1.6
        """
        try:
            # AC-2.1.5: Check data availability
            if not self._has_sufficient_data(data, start_date, end_date):
                return (None, f"Insufficient data (<{self.MIN_TRADING_DAYS} days)")

            # Execute strategy code in isolated namespace
            namespace = {'data': data, 'finlab': __import__('finlab')}

            try:
                exec(strategy_code, namespace)
            except Exception as e:
                # AC-2.1.6: Catch execution errors
                logger.error(f"  Strategy execution failed for {period_name}: {e}")
                return (None, f"Execution error: {str(e)[:100]}")

            # Extract report from namespace
            if 'report' not in namespace:
                return (None, "No report object generated")

            report = namespace['report']

            # Filter report to period dates
            try:
                period_report = self._filter_report_to_period(
                    report, start_date, end_date
                )
            except Exception as e:
                logger.error(f"  Report filtering failed for {period_name}: {e}")
                return (None, f"Report filtering error: {str(e)[:100]}")

            # Extract Sharpe ratio
            try:
                sharpe = self._extract_sharpe_from_report(period_report)
                return (sharpe, None)
            except Exception as e:
                logger.error(f"  Sharpe extraction failed for {period_name}: {e}")
                return (None, f"Metric extraction error: {str(e)[:100]}")

        except Exception as e:
            # AC-2.1.6: Catch all unexpected errors
            logger.error(f"  Unexpected error in {period_name} backtest: {e}")
            return (None, f"Unexpected error: {str(e)[:100]}")

    def _has_sufficient_data(
        self,
        data: Any,
        start_date: str,
        end_date: str
    ) -> bool:
        """
        Check if data has sufficient trading days for period.

        Requirements: AC-2.1.5
        """
        try:
            # Try to get a sample dataset to check date range
            # This assumes data has a .get() method or similar
            # Actual implementation depends on FinLab data structure

            # For now, assume data is valid if it exists
            # TODO: Add actual date range checking when data structure is known
            return True
        except Exception as e:
            logger.warning(f"Data availability check failed: {e}")
            return False

    def _filter_report_to_period(
        self,
        report: Any,
        start_date: str,
        end_date: str
    ) -> Any:
        """
        Filter backtest report to specific time period.

        M2 FIX: Added version parameter control to handle reports without
        filtering capability while maintaining backward compatibility.

        CRITICAL: Without proper filtering, train/validation/test periods
        will all use metrics from the ENTIRE backtest period, defeating
        the purpose of temporal data splitting and causing data leakage.

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

        Args:
            report: FinLab backtest report object

        Returns:
            Sharpe ratio as float

        Raises:
            ValueError: If Sharpe cannot be extracted
        """
        try:
            # Try get_stats() method (dict return)
            if hasattr(report, 'get_stats'):
                stats = report.get_stats()
                if isinstance(stats, dict):
                    return float(stats.get('sharpe_ratio', 0.0))
                elif isinstance(stats, (int, float)):
                    return float(stats)

            # Try direct attribute access
            if hasattr(report, 'sharpe_ratio'):
                return float(report.sharpe_ratio)

            # Try stats attribute
            if hasattr(report, 'stats'):
                stats = report.stats
                if isinstance(stats, dict):
                    return float(stats.get('sharpe_ratio', 0.0))

            raise ValueError("No Sharpe ratio found in report")

        except (TypeError, ValueError, AttributeError) as e:
            raise ValueError(f"Sharpe extraction failed: {e}")

    def _calculate_consistency(self, sharpe_values: list) -> float:
        """
        Calculate consistency score across periods.

        Consistency = 1 - (std_dev / mean)
        - High consistency (>0.8): Stable strategy
        - Low consistency (<0.5): Potential overfitting

        M1 FIX: Reject negative or near-zero mean Sharpe to prevent
        consistently losing strategies from getting high consistency scores.

        Example issue:
        - Strategy with Sharpe [-0.5, -0.6, -0.7] has low variance
        - Old formula: 1 - (0.1 / abs(-0.6)) = 0.83 (incorrectly high!)
        - New formula: Returns 0.0 since mean_sharpe < epsilon

        Args:
            sharpe_values: List of Sharpe ratios from different periods

        Returns:
            Consistency score (0-1, higher is better)

        Requirements: AC-2.1.2
        """
        # Fast reject: need at least 2 periods
        if len(sharpe_values) < 2:
            return 0.0

        sharpes = np.array(sharpe_values)
        mean_sharpe = np.mean(sharpes)

        # M1 FIX: Reject negative or near-zero mean Sharpe
        # This prevents consistently losing strategies from getting high scores
        # Also avoids numerical instability when mean_sharpe ≈ 0
        if mean_sharpe < self.epsilon:
            logger.debug(
                f"Consistency rejected: mean_sharpe={mean_sharpe:.4f} < "
                f"epsilon={self.epsilon}. Sharpe values: {sharpe_values}"
            )
            return 0.0

        std_sharpe = np.std(sharpes, ddof=1)

        # Consistency = 1 - (coefficient of variation)
        # No need for abs() since mean_sharpe >= epsilon > 0
        consistency = 1.0 - (std_sharpe / mean_sharpe)

        # Clamp to [0, 1] range
        return max(0.0, min(1.0, consistency))

    def _check_validation_criteria(self, results: Dict[str, Any]) -> bool:
        """
        Check if strategy passes validation criteria.

        Requirements: AC-2.1.3, AC-2.1.4

        Criteria:
        1. Validation Sharpe > 1.0
        2. Consistency > 0.6
        3. Degradation ratio > 0.7 (validation >= training * 0.7)

        Returns:
            True if ALL criteria met, False otherwise
        """
        validation_sharpe = results['sharpes'].get('validation')
        consistency = results['consistency']
        degradation_ratio = results['degradation_ratio']

        # Criterion 1: Validation Sharpe > 1.0
        if not validation_sharpe or validation_sharpe <= self.MIN_VALIDATION_SHARPE:
            sharpe_str = f"{validation_sharpe:.4f}" if validation_sharpe is not None else "None"
            logger.info(
                f"  ❌ Criterion 1 FAIL: Validation Sharpe {sharpe_str} "
                f"≤ {self.MIN_VALIDATION_SHARPE}"
            )
            return False
        logger.info(f"  ✅ Criterion 1 PASS: Validation Sharpe {validation_sharpe:.4f}")

        # Criterion 2: Consistency > 0.6
        if consistency <= self.MIN_CONSISTENCY:
            logger.info(
                f"  ❌ Criterion 2 FAIL: Consistency {consistency:.4f} "
                f"≤ {self.MIN_CONSISTENCY}"
            )
            return False
        logger.info(f"  ✅ Criterion 2 PASS: Consistency {consistency:.4f}")

        # Criterion 3: Degradation ratio > 0.7 (if training sharpe exists)
        training_sharpe = results['sharpes'].get('training')
        if training_sharpe and training_sharpe > 0:
            if degradation_ratio <= self.MIN_DEGRADATION_RATIO:
                logger.info(
                    f"  ❌ Criterion 3 FAIL: Degradation ratio {degradation_ratio:.4f} "
                    f"≤ {self.MIN_DEGRADATION_RATIO}"
                )
                return False
            logger.info(f"  ✅ Criterion 3 PASS: Degradation ratio {degradation_ratio:.4f}")

        return True


def validate_strategy_with_data_split(
    strategy_code: str,
    data: Any,
    iteration_num: int = 0
) -> Dict[str, Any]:
    """
    Convenience function for strategy validation with data split.

    Args:
        strategy_code: Python code for trading strategy
        data: FinLab data object
        iteration_num: Iteration number for logging

    Returns:
        Validation results dictionary

    Example:
        >>> results = validate_strategy_with_data_split(strategy_code, data, 42)
        >>> if results['validation_passed']:
        >>>     print("Strategy validated!")
    """
    validator = DataSplitValidator()
    return validator.validate_strategy(strategy_code, data, iteration_num)
