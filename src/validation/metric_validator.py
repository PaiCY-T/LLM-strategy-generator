"""
Metric Validator - Validates metric calculations for mathematical consistency.

This module implements Story 6 (Metric Integrity) from the Learning System Stability Fixes spec.
It detects impossible metric combinations (e.g., negative return + positive Sharpe) identified
in the Zen Challenge analysis.

Design Reference: design.md v1.1 lines 280-327 (Component 1)
Interface Contract: design.md v1.1 lines 149-198 (ValidationHook Protocol)
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np


# ==============================================================================
# Data Models (design.md v1.1 lines 892-919)
# ==============================================================================

@dataclass
class ValidationReport:
    """Standard validation report returned by all validators."""
    passed: bool
    component: str  # Component name (e.g., "MetricValidator")
    checks_performed: List[str]  # List of check names executed
    failures: List[Tuple[str, str]]  # [(check_name, reason)]
    warnings: List[Tuple[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for storage."""
        return {
            'passed': self.passed,
            'component': self.component,
            'checks_performed': self.checks_performed,
            'failures': self.failures,
            'warnings': self.warnings,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }


class ValidationSystemError(Exception):
    """Raised when validation infrastructure fails (not validation logic)."""
    pass


# ==============================================================================
# MetricValidator - Story 6: Metric Integrity
# ==============================================================================

class MetricValidator:
    """
    Validates metric calculations for mathematical consistency and detects
    impossible combinations.

    Implements ValidationHook protocol from design.md v1.1 lines 170-193.

    Key Responsibilities:
    1. Cross-validate Sharpe ratio calculation against industry standard formula
    2. Detect impossible metric combinations (negative return + positive Sharpe, etc.)
    3. Generate audit trail with intermediate calculation values

    Error Handling (Failure Mode Matrix, design.md v1.1 lines 966-968):
    - Logical Failure: Returns ValidationReport with passed=False
    - System Error: Raises ValidationSystemError
    - Non-critical Failure: Logs warning, continues with validation
    """

    def __init__(self):
        """Initialize MetricValidator with no parameters."""
        self.risk_free_rate = 0.01  # 1% default risk-free rate
        self.sharpe_tolerance = 0.1  # 10% tolerance for Sharpe validation

    def validate(
        self,
        code: str,
        execution_result: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationReport:
        """
        Execute validation check (ValidationHook protocol implementation).

        Args:
            code: Generated strategy code (not used for metric validation)
            execution_result: FinlabReport object with metrics
            context: Optional context with extracted metrics dict

        Returns:
            ValidationReport with detailed results

        Raises:
            ValidationSystemError: On infrastructure failure (not validation failure)
        """
        try:
            # Extract metrics from context or execution_result
            if context and 'metrics' in context:
                metrics = context['metrics']
                report = context.get('report')
            elif execution_result:
                # This case will be implemented when integrating with AutonomousLoop
                # For now, raise infrastructure error if metrics not in context
                raise ValidationSystemError("Metrics not provided in context")
            else:
                raise ValidationSystemError("No execution_result or metrics context provided")

            # Delegate to validate_metrics
            is_valid, errors = self.validate_metrics(metrics, report)

            # Build ValidationReport
            checks_performed = [
                "sharpe_cross_validation",
                "impossible_combinations"
            ]

            failures = [(check, error) for check, error in zip(['validation'], errors)] if not is_valid else []

            return ValidationReport(
                passed=is_valid,
                component="MetricValidator",
                checks_performed=checks_performed,
                failures=failures,
                warnings=[],
                metadata={'metrics': metrics}
            )

        except ValidationSystemError:
            # Re-raise infrastructure errors
            raise
        except Exception as e:
            # Convert unexpected errors to ValidationSystemError
            raise ValidationSystemError(f"Metric validation infrastructure error: {e}")

    def validate_metrics(
        self,
        metrics: Dict[str, float],
        report: Optional[Any] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate metrics for mathematical consistency.

        Args:
            metrics: Extracted metrics dict (sharpe, return, volatility, etc.)
            report: Raw Finlab backtest report for audit trail (optional)

        Returns:
            (is_valid, error_messages)

        Example:
            metrics = {'sharpe': 0.89, 'total_return': -0.158, 'volatility': 0.15}
            is_valid, errors = validator.validate_metrics(metrics)
            # Returns: (False, ["Impossible combination: negative return (-15.8%) with positive Sharpe (0.89)"])
        """
        errors = []

        # Check for impossible combinations
        impossible = self.check_impossible_combinations(metrics)
        errors.extend(impossible)

        # Cross-validate Sharpe ratio if all required metrics present
        if all(k in metrics for k in ['total_return', 'volatility', 'sharpe']):
            is_valid_sharpe, sharpe_error = self.cross_validate_sharpe(
                metrics['total_return'],
                metrics['volatility'],
                metrics['sharpe']
            )
            if not is_valid_sharpe:
                errors.append(sharpe_error)

        is_valid = len(errors) == 0
        return is_valid, errors


    def cross_validate_sharpe(
        self,
        total_return: float,
        volatility: float,
        sharpe: float,
        periods_per_year: int = 252
    ) -> Tuple[bool, str]:
        """
        Cross-validate Sharpe ratio calculation.

        Industry standard: Sharpe = (annualized_return - risk_free_rate) / annualized_volatility

        Args:
            total_return: Total return over backtest period (e.g., 0.52 for 52%)
            volatility: Return volatility (standard deviation)
            sharpe: Reported Sharpe ratio
            periods_per_year: Number of trading periods per year (default 252 for daily)

        Returns:
            (is_valid, error_message_if_invalid)

        Example:
            # Correct calculation
            is_valid, msg = validator.cross_validate_sharpe(0.52, 0.15, 0.89)
            # Returns: (True, "")

            # Incorrect calculation (miscalculated Sharpe)
            is_valid, msg = validator.cross_validate_sharpe(0.52, 0.15, 2.5)
            # Returns: (False, "Sharpe ratio mismatch: calculated=0.89, reported=2.5")
        """
        # Handle edge cases
        if volatility == 0:
            # Zero volatility case - Sharpe should be undefined/infinite
            # If Sharpe is reported, it's invalid
            if sharpe != 0:
                return False, f"Sharpe ratio invalid with zero volatility: reported={sharpe:.2f}"
            return True, ""

        # Calculate annualized return
        # Assuming total_return is already annualized (e.g., 0.52 = 52% annual return)
        annualized_return = total_return

        # Calculate annualized volatility
        # Volatility from Finlab is already annualized, so use it directly
        annualized_volatility = volatility

        # Calculate expected Sharpe using industry standard formula
        expected_sharpe = (annualized_return - self.risk_free_rate) / annualized_volatility

        # Validate against reported Sharpe with tolerance
        tolerance = 0.1 * abs(sharpe)
        difference = abs(expected_sharpe - sharpe)

        is_valid = difference <= tolerance

        if is_valid:
            return True, ""
        else:
            error_message = (
                f"Sharpe ratio mismatch: calculated={expected_sharpe:.2f}, "
                f"reported={sharpe:.2f}, difference={difference:.2f}, "
                f"tolerance={tolerance:.2f}"
            )
            return False, error_message


    def check_impossible_combinations(
        self,
        metrics: Dict[str, float]
    ) -> List[str]:
        """
        Detect mathematically impossible metric combinations.

        Checks:
        - Negative total return + high positive Sharpe (identified in Zen Challenge)
        - Zero volatility + non-zero Sharpe
        - Max drawdown > 100%
        - Sharpe ratio magnitude exceeds reasonable bounds (|Sharpe| > 10)

        Args:
            metrics: Dict with metric values

        Returns:
            List of detected anomalies with specific descriptions

        Example:
            metrics = {'sharpe': 0.89, 'total_return': -0.158, 'max_drawdown': 0.25}
            anomalies = validator.check_impossible_combinations(metrics)
            # Returns: ["Impossible combination: negative return (-15.8%) with positive Sharpe (0.89)"]
        """
        errors = []

        # Check 1: Negative return + high positive Sharpe
        # This was the key Zen Challenge finding: iteration 0 had -15.8% return with +0.89 Sharpe
        if 'total_return' in metrics and 'sharpe' in metrics:
            total_return = metrics['total_return']
            sharpe = metrics['sharpe']

            if total_return < 0 and sharpe > 0.3:
                errors.append(
                    f"Impossible combination: negative return ({total_return*100:.1f}%) "
                    f"with positive Sharpe ({sharpe:.2f})"
                )

        # Check 2: Zero volatility + non-zero Sharpe
        # Already handled in cross_validate_sharpe, but double-check here for completeness
        if 'volatility' in metrics and 'sharpe' in metrics:
            volatility = metrics['volatility']
            sharpe = metrics['sharpe']

            if volatility == 0 and sharpe != 0:
                errors.append(
                    f"Impossible combination: zero volatility with non-zero Sharpe ({sharpe:.2f})"
                )

        # Check 3: Max drawdown > 100%
        # Can't lose more than 100% of portfolio value
        if 'max_drawdown' in metrics:
            max_drawdown = metrics['max_drawdown']

            if max_drawdown > 1.0:
                errors.append(
                    f"Impossible metric: max drawdown > 100% ({max_drawdown*100:.1f}%)"
                )

        # Check 4: Sharpe ratio magnitude exceeds reasonable bounds
        # |Sharpe| > 10 is unrealistic in practice
        if 'sharpe' in metrics:
            sharpe = metrics['sharpe']

            if abs(sharpe) > 10:
                errors.append(
                    f"Unrealistic Sharpe ratio: |{sharpe:.2f}| > 10"
                )

        return errors


    def generate_audit_trail(
        self,
        report: Any
    ) -> Dict[str, Any]:
        """
        Generate detailed calculation audit trail.

        Extracts intermediate values from FinlabReport for debugging metric
        calculation issues.

        Args:
            report: Raw Finlab backtest report

        Returns:
            Dict with intermediate values:
            - daily_returns: Daily return series
            - cumulative_returns: Cumulative return series
            - rolling_volatility: Rolling volatility (30-day window)
            - annualized_return: Annualized return calculation
            - annualized_volatility: Annualized volatility calculation
            - sharpe_calculation_steps: Step-by-step Sharpe calculation

        Example:
            trail = validator.generate_audit_trail(finlab_report)
            # Returns: {'daily_returns': [...], 'annualized_return': 0.52, ...}
        """
        audit_trail = {
            'daily_returns': None,
            'cumulative_returns': None,
            'rolling_volatility': None,
            'annualized_return': None,
            'annualized_volatility': None,
            'sharpe_calculation_steps': {},
            'extraction_warnings': []
        }

        try:
            # Import pandas for data processing
            import pandas as pd

            # Step 1: Extract daily returns from report
            daily_returns = None

            # Try multiple methods to extract daily returns
            if hasattr(report, 'returns') and report.returns is not None:
                daily_returns = report.returns
                audit_trail['extraction_warnings'].append("Daily returns extracted from report.returns")
            elif hasattr(report, 'daily_returns') and report.daily_returns is not None:
                daily_returns = report.daily_returns
                audit_trail['extraction_warnings'].append("Daily returns extracted from report.daily_returns")
            elif hasattr(report, 'position') and report.position is not None:
                # Calculate returns from position changes
                try:
                    position = report.position
                    if isinstance(position, pd.DataFrame):
                        # Calculate daily returns from position values
                        daily_returns = position.sum(axis=1).pct_change().dropna()
                        audit_trail['extraction_warnings'].append("Daily returns calculated from report.position")
                except Exception as e:
                    audit_trail['extraction_warnings'].append(f"Failed to calculate returns from position: {e}")
            elif hasattr(report, 'equity') and report.equity is not None:
                # Calculate returns from equity curve
                try:
                    equity = report.equity
                    if isinstance(equity, (pd.Series, pd.DataFrame)):
                        if isinstance(equity, pd.DataFrame):
                            equity = equity.iloc[:, 0]  # Take first column if DataFrame
                        daily_returns = equity.pct_change().dropna()
                        audit_trail['extraction_warnings'].append("Daily returns calculated from report.equity")
                except Exception as e:
                    audit_trail['extraction_warnings'].append(f"Failed to calculate returns from equity: {e}")

            # Convert to list for JSON serialization if Series
            if daily_returns is not None:
                if isinstance(daily_returns, pd.Series):
                    audit_trail['daily_returns'] = daily_returns.tolist()
                elif isinstance(daily_returns, pd.DataFrame):
                    # Sum across columns if DataFrame
                    audit_trail['daily_returns'] = daily_returns.sum(axis=1).tolist()
                else:
                    audit_trail['daily_returns'] = list(daily_returns)
            else:
                audit_trail['extraction_warnings'].append("Could not extract daily returns from report")
                # Return early if we can't get daily returns
                return audit_trail

            # Step 2: Calculate cumulative returns
            try:
                returns_series = pd.Series(audit_trail['daily_returns'])
                cumulative_returns = (1 + returns_series).cumprod() - 1
                audit_trail['cumulative_returns'] = cumulative_returns.tolist()
            except Exception as e:
                audit_trail['extraction_warnings'].append(f"Failed to calculate cumulative returns: {e}")
                audit_trail['cumulative_returns'] = None

            # Step 3: Calculate rolling volatility (30-day window)
            try:
                returns_series = pd.Series(audit_trail['daily_returns'])
                rolling_vol = returns_series.rolling(window=30).std()
                # Annualize rolling volatility
                rolling_vol_annualized = rolling_vol * np.sqrt(252)
                audit_trail['rolling_volatility'] = rolling_vol_annualized.tolist()
            except Exception as e:
                audit_trail['extraction_warnings'].append(f"Failed to calculate rolling volatility: {e}")
                audit_trail['rolling_volatility'] = None

            # Step 4: Calculate annualized return
            try:
                returns_series = pd.Series(audit_trail['daily_returns'])
                total_return = (1 + returns_series).prod() - 1
                num_days = len(returns_series)

                if num_days > 0:
                    # Annualize using trading days (252 per year)
                    annualized_return = (1 + total_return) ** (252 / num_days) - 1
                    audit_trail['annualized_return'] = float(annualized_return)

                    # Store calculation steps
                    audit_trail['sharpe_calculation_steps']['total_return'] = float(total_return)
                    audit_trail['sharpe_calculation_steps']['num_days'] = num_days
                else:
                    audit_trail['extraction_warnings'].append("No trading days to calculate annualized return")
                    audit_trail['annualized_return'] = 0.0
            except Exception as e:
                audit_trail['extraction_warnings'].append(f"Failed to calculate annualized return: {e}")
                audit_trail['annualized_return'] = None

            # Step 5: Calculate annualized volatility
            try:
                returns_series = pd.Series(audit_trail['daily_returns'])
                daily_volatility = returns_series.std()
                annualized_volatility = daily_volatility * np.sqrt(252)
                audit_trail['annualized_volatility'] = float(annualized_volatility)

                # Store calculation steps
                audit_trail['sharpe_calculation_steps']['daily_volatility'] = float(daily_volatility)
            except Exception as e:
                audit_trail['extraction_warnings'].append(f"Failed to calculate annualized volatility: {e}")
                audit_trail['annualized_volatility'] = None

            # Step 6: Document Sharpe ratio calculation steps
            try:
                if audit_trail['annualized_return'] is not None and audit_trail['annualized_volatility'] is not None:
                    annualized_return = audit_trail['annualized_return']
                    annualized_volatility = audit_trail['annualized_volatility']

                    # Calculate Sharpe ratio using industry standard formula
                    excess_return = annualized_return - self.risk_free_rate

                    if annualized_volatility != 0:
                        sharpe_ratio = excess_return / annualized_volatility

                        # Document step-by-step calculation
                        audit_trail['sharpe_calculation_steps'].update({
                            'risk_free_rate': self.risk_free_rate,
                            'annualized_return': float(annualized_return),
                            'annualized_volatility': float(annualized_volatility),
                            'excess_return': float(excess_return),
                            'calculated_sharpe': float(sharpe_ratio),
                            'formula': '(annualized_return - risk_free_rate) / annualized_volatility'
                        })
                    else:
                        audit_trail['extraction_warnings'].append("Zero volatility - Sharpe ratio undefined")
                        audit_trail['sharpe_calculation_steps']['calculated_sharpe'] = None
                        audit_trail['sharpe_calculation_steps']['warning'] = "Zero volatility"
            except Exception as e:
                audit_trail['extraction_warnings'].append(f"Failed to calculate Sharpe steps: {e}")

        except ImportError as e:
            audit_trail['extraction_warnings'].append(f"Failed to import pandas: {e}")
        except Exception as e:
            audit_trail['extraction_warnings'].append(f"Unexpected error in audit trail generation: {e}")

        return audit_trail
