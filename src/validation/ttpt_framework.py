"""
Time-Travel Perturbation Testing (TTPT) Framework.

Detects look-ahead bias in trading strategies by shifting market data temporally
and validating that strategy decisions remain consistent without access to future information.

Core Methodology:
1. Generate shifted versions of market data (shift future → past)
2. Execute strategy on both original and shifted data
3. Compare signals and performance metrics
4. Detect violations via correlation and performance degradation

Example:
    >>> framework = TTPTFramework(shift_days=[5, 10], tolerance=0.05)
    >>> result = framework.validate_strategy(
    ...     strategy_fn=my_strategy,
    ...     original_data=market_data,
    ...     params={'lookback': 20}
    ... )
    >>> print(result['passed'])  # True if no look-ahead bias detected
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TTPTViolation:
    """Represents a single TTPT violation."""
    shift_days: int
    violation_type: str  # 'performance_degradation' | 'correlation_drop' | 'signal_instability'
    metric_name: str
    original_value: float
    shifted_value: float
    change: float
    severity: str  # 'minor' | 'moderate' | 'severe'


class TTPTFramework:
    """
    Time-Travel Perturbation Testing framework for look-ahead bias detection.

    Attributes:
        shift_days: List of temporal shift amounts (e.g., [1, 5, 10])
        tolerance: Maximum acceptable performance change (default: 5%)
        min_correlation: Minimum signal correlation threshold (default: 0.95)
    """

    def __init__(
        self,
        shift_days: Optional[List[int]] = None,
        tolerance: float = 0.05,
        min_correlation: float = 0.95
    ):
        """
        Initialize TTPT framework.

        Args:
            shift_days: List of shift amounts in days (default: [1, 5, 10])
            tolerance: Max acceptable performance degradation (0.05 = 5%)
            min_correlation: Min required signal correlation (0.95 = 95%)
        """
        self.shift_days = shift_days if shift_days is not None else [1, 5, 10]
        self.tolerance = tolerance
        self.min_correlation = min_correlation

        logger.info(
            f"Initialized TTPT Framework: shifts={self.shift_days}, "
            f"tolerance={tolerance:.2%}, min_correlation={min_correlation:.2f}"
        )

    def generate_shifted_data(
        self,
        data: Dict[str, pd.DataFrame],
        shift_days: int
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate time-shifted version of market data.

        Shifts data forward in time, making future data appear in the past.
        This simulates what a look-ahead biased strategy would see.

        Args:
            data: Dictionary of DataFrames (e.g., {'close': df, 'volume': df})
            shift_days: Number of days to shift forward

        Returns:
            Shifted data dictionary with same structure

        Example:
            >>> data = {'close': pd.DataFrame({'AAPL': [100, 101, 102, 103, 104]})}
            >>> shifted = framework.generate_shifted_data(data, shift_days=2)
            >>> # shifted['close']['AAPL'] = [102, 103, 104, NaN, NaN]
        """
        if shift_days == 0:
            # Special case: no shift returns copy of original
            return {key: df.copy() for key, df in data.items()}

        shifted = {}
        for key, df in data.items():
            # Shift data forward (negative shift in pandas)
            # This makes future data appear in past positions
            shifted_df = df.shift(-shift_days)

            # Preserve index and columns
            shifted_df.index = df.index
            shifted_df.columns = df.columns

            shifted[key] = shifted_df

        return shifted

    def validate_strategy(
        self,
        strategy_fn: Callable,
        original_data: Dict[str, pd.DataFrame],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate strategy for look-ahead bias across all configured shifts.

        Args:
            strategy_fn: Strategy function taking (data_dict, params) and returning signals
            original_data: Market data dictionary
            params: Strategy parameters

        Returns:
            {
                'passed': bool,  # Overall pass/fail
                'violations': List[TTPTViolation],  # Detected violations
                'metrics': {
                    'signal_correlation': float,  # Average across shifts
                    'performance_change': float,  # Average degradation
                    'shift_results': List[Dict]  # Per-shift details
                },
                'report': str  # Human-readable summary
            }
        """
        violations = []
        shift_results = []

        # Generate signals on original data
        try:
            original_signals = strategy_fn(original_data, params)
        except Exception as e:
            logger.error(f"Strategy execution failed on original data: {e}")
            return {
                'passed': False,
                'violations': [TTPTViolation(
                    shift_days=0,
                    violation_type='execution_error',
                    metric_name='strategy_execution',
                    original_value=0.0,
                    shifted_value=0.0,
                    change=0.0,
                    severity='severe'
                )],
                'metrics': {},
                'report': f"Strategy execution failed: {str(e)}"
            }

        # Validate across each shift
        for shift in self.shift_days:
            shift_result = self._validate_single_shift(
                strategy_fn=strategy_fn,
                original_data=original_data,
                original_signals=original_signals,
                shift_days=shift,
                params=params
            )

            shift_results.append(shift_result)
            violations.extend(shift_result.get('violations', []))

        # Aggregate metrics
        avg_correlation = np.mean([r['correlation'] for r in shift_results])
        avg_performance_change = np.mean([r['performance_change'] for r in shift_results])

        metrics = {
            'signal_correlation': avg_correlation,
            'performance_change': avg_performance_change,
            'shift_results': shift_results
        }

        # Determine pass/fail
        passed = len(violations) == 0

        # Generate report
        report = self.generate_report({
            'passed': passed,
            'violations': violations,
            'metrics': metrics,
            'report': ''  # Will be filled by generate_report
        })

        return {
            'passed': passed,
            'violations': violations,
            'metrics': metrics,
            'report': report
        }

    def _validate_single_shift(
        self,
        strategy_fn: Callable,
        original_data: Dict[str, pd.DataFrame],
        original_signals: pd.DataFrame,
        shift_days: int,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate strategy for a single shift amount."""
        violations = []

        # Check if data is sufficient for this shift
        min_length = min(df.shape[0] for df in original_data.values())
        if min_length <= shift_days:
            logger.warning(
                f"Insufficient data for shift={shift_days} (length={min_length}). "
                "Skipping this shift."
            )
            return {
                'shift': shift_days,
                'correlation': 1.0,
                'performance_change': 0.0,
                'violations': [],
                'skipped': True
            }

        # Generate shifted data
        shifted_data = self.generate_shifted_data(original_data, shift_days)

        # Execute strategy on shifted data
        try:
            shifted_signals = strategy_fn(shifted_data, params)
        except Exception as e:
            logger.error(f"Strategy failed on shift={shift_days}: {e}")
            violation = TTPTViolation(
                shift_days=shift_days,
                violation_type='execution_error',
                metric_name='strategy_execution',
                original_value=0.0,
                shifted_value=0.0,
                change=0.0,
                severity='severe'
            )
            return {
                'shift': shift_days,
                'correlation': 0.0,
                'performance_change': 0.0,
                'violations': [violation],
                'error': str(e)
            }

        # Compare signals (align by dropping NaN from shift)
        valid_length = min_length - shift_days
        original_aligned = original_signals.iloc[:valid_length]
        shifted_aligned = shifted_signals.iloc[:valid_length]

        # Calculate signal correlation
        correlation = self._calculate_signal_correlation(
            original_aligned,
            shifted_aligned
        )

        # Check correlation threshold
        if correlation < self.min_correlation:
            violations.append(TTPTViolation(
                shift_days=shift_days,
                violation_type='correlation_drop',
                metric_name='signal_correlation',
                original_value=1.0,
                shifted_value=correlation,
                change=1.0 - correlation,
                severity=self._classify_severity(1.0 - correlation, 0.1, 0.2)
            ))

        # Calculate performance change (mock - using mean signal as proxy)
        original_perf = float(original_aligned.mean().mean())
        shifted_perf = float(shifted_aligned.mean().mean())
        perf_change = abs(original_perf - shifted_perf) / (abs(original_perf) + 1e-9)

        # Check performance degradation
        if perf_change > self.tolerance:
            violations.append(TTPTViolation(
                shift_days=shift_days,
                violation_type='performance_degradation',
                metric_name='mean_signal',
                original_value=original_perf,
                shifted_value=shifted_perf,
                change=perf_change,
                severity=self._classify_severity(perf_change, self.tolerance, 2 * self.tolerance)
            ))

        return {
            'shift': shift_days,
            'correlation': correlation,
            'performance_change': perf_change,
            'violations': violations
        }

    def _calculate_signal_correlation(
        self,
        signals1: pd.DataFrame,
        signals2: pd.DataFrame
    ) -> float:
        """Calculate correlation between two signal DataFrames."""
        # Flatten and remove NaN
        flat1 = signals1.values.flatten()
        flat2 = signals2.values.flatten()

        # Find valid indices (non-NaN in both)
        valid = ~(np.isnan(flat1) | np.isnan(flat2))

        if valid.sum() < 10:
            # Insufficient valid data points
            return 0.0

        # Calculate Pearson correlation
        try:
            correlation = np.corrcoef(flat1[valid], flat2[valid])[0, 1]
            return correlation if not np.isnan(correlation) else 0.0
        except Exception:
            return 0.0

    def _classify_severity(
        self,
        change: float,
        moderate_threshold: float,
        severe_threshold: float
    ) -> str:
        """Classify violation severity based on magnitude."""
        if change >= severe_threshold:
            return 'severe'
        elif change >= moderate_threshold:
            return 'moderate'
        else:
            return 'minor'

    def generate_report(
        self,
        validation_result: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable TTPT validation report.

        Args:
            validation_result: Result from validate_strategy()

        Returns:
            Formatted report string
        """
        passed = validation_result['passed']
        violations = validation_result['violations']
        metrics = validation_result.get('metrics', {})

        # Header
        status_icon = "✅ PASS" if passed else "❌ FAIL"
        report = [
            "=" * 70,
            "Time-Travel Perturbation Testing (TTPT) Report",
            "=" * 70,
            f"Status: {status_icon}",
            ""
        ]

        # Overall metrics
        if metrics:
            report.extend([
                "Overall Metrics:",
                f"  Signal Correlation: {metrics.get('signal_correlation', 0.0):.4f}",
                f"  Performance Change: {metrics.get('performance_change', 0.0):.2%}",
                f"  Correlation Threshold: {self.min_correlation:.4f}",
                f"  Tolerance Threshold: {self.tolerance:.2%}",
                ""
            ])

        # Per-shift results
        shift_results = metrics.get('shift_results', [])
        if shift_results:
            report.append("Per-Shift Results:")
            report.append("  Shift | Correlation | Perf Change | Status")
            report.append("  ------|-------------|-------------|--------")

            for result in shift_results:
                if result.get('skipped'):
                    status = "SKIPPED"
                elif result.get('error'):
                    status = "ERROR"
                elif result.get('violations'):
                    status = "FAIL"
                else:
                    status = "PASS"

                shift = result['shift']
                corr = result.get('correlation', 0.0)
                perf = result.get('performance_change', 0.0)

                report.append(f"  {shift:5d} | {corr:11.4f} | {perf:11.2%} | {status}")

            report.append("")

        # Violations detail
        if violations:
            report.append(f"Violations Detected: {len(violations)}")
            report.append("")

            for i, v in enumerate(violations, 1):
                report.extend([
                    f"Violation #{i}:",
                    f"  Shift Days: {v.shift_days}",
                    f"  Type: {v.violation_type}",
                    f"  Metric: {v.metric_name}",
                    f"  Original: {v.original_value:.4f}",
                    f"  Shifted: {v.shifted_value:.4f}",
                    f"  Change: {v.change:.4f} ({v.change:.2%})",
                    f"  Severity: {v.severity}",
                    ""
                ])
        else:
            report.extend([
                "No violations detected.",
                "Strategy appears free of look-ahead bias within tested parameters.",
                ""
            ])

        # Summary
        if passed:
            report.extend([
                "=" * 70,
                "✅ VALIDATION PASSED - Strategy shows no evidence of look-ahead bias",
                "=" * 70
            ])
        else:
            report.extend([
                "=" * 70,
                "❌ VALIDATION FAILED - Look-ahead bias detected",
                "=" * 70
            ])

        return "\n".join(report)


# Convenience function for quick validation
def validate_strategy_ttpt(
    strategy_fn: Callable,
    data: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
    shift_days: Optional[List[int]] = None,
    tolerance: float = 0.05,
    min_correlation: float = 0.95,
    verbose: bool = True
) -> bool:
    """
    Convenience function for quick TTPT validation.

    Args:
        strategy_fn: Strategy function to validate
        data: Market data dictionary
        params: Strategy parameters
        shift_days: Shift amounts to test (default: [1, 5, 10])
        tolerance: Performance change tolerance
        min_correlation: Minimum signal correlation
        verbose: Print report if True

    Returns:
        True if validation passed, False otherwise

    Example:
        >>> passed = validate_strategy_ttpt(
        ...     strategy_fn=momentum_strategy,
        ...     data={'close': close_df, 'volume': volume_df},
        ...     params={'lookback': 20}
        ... )
        >>> if passed:
        ...     print("Strategy is safe to use")
    """
    framework = TTPTFramework(
        shift_days=shift_days,
        tolerance=tolerance,
        min_correlation=min_correlation
    )

    result = framework.validate_strategy(
        strategy_fn=strategy_fn,
        original_data=data,
        params=params
    )

    if verbose:
        print(result['report'])

    return result['passed']
