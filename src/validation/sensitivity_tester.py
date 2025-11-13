"""
Parameter Sensitivity Testing Framework
=======================================

**OPTIONAL QUALITY CHECK** - Tests parameter sensitivity by varying parameters
and measuring strategy stability. Identifies fragile parameters that significantly
impact performance.

⚠️  TIME/RESOURCE COST: 50-75 minutes per strategy
    - Each parameter tested requires 5 backtests (default variation steps)
    - Testing 4-6 parameters = 20-30 backtests per strategy
    - Each backtest: ~2-3 minutes

WHEN TO USE:
    ✅ Recommended for:
        - Champion strategies before production deployment
        - Final validation of optimized strategies
        - Robustness verification for critical strategies

    ⏭️  Optional/Skip for:
        - Rapid development iterations
        - Exploratory strategy development
        - Time-constrained validation cycles

Features:
    - Systematic parameter variation (±20% from baseline)
    - Stability score calculation (avg_sharpe / baseline_sharpe)
    - Sensitive parameter flagging (stability < 0.6)
    - Performance degradation analysis
    - Automated parameter robustness testing

Usage:
    from src.validation import SensitivityTester

    # Full sensitivity testing (50-75 min for typical strategy)
    tester = SensitivityTester()
    results = tester.test_parameter_sensitivity(
        template=turtle_template,
        baseline_params=params,
        parameters_to_test=['n_stocks', 'ma_short']  # Test specific params
    )

    for param, sensitivity in results.items():
        if sensitivity['stability'] < 0.6:
            print(f"⚠️  Sensitive parameter: {param}")

    # Skip sensitivity testing during development
    # Simply don't call test_parameter_sensitivity() - this is OPTIONAL

Requirements:
    - Requirement 3.3: Parameter sensitivity testing (optional quality check)
"""

from typing import Dict, Any, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError


@dataclass
class SensitivityResult:
    """
    Result of parameter sensitivity testing.

    Attributes:
        parameter: Parameter name being tested
        baseline_value: Original parameter value
        variations: List of (varied_value, sharpe_ratio) tuples
        stability_score: Average Sharpe / baseline Sharpe
        is_sensitive: True if stability < 0.6
        performance_range: (min_sharpe, max_sharpe) across variations
        degradation_percent: Maximum performance degradation percentage
    """
    parameter: str
    baseline_value: Any
    variations: List[Tuple[Any, float]] = field(default_factory=list)
    stability_score: float = 0.0
    is_sensitive: bool = False
    performance_range: Tuple[float, float] = (0.0, 0.0)
    degradation_percent: float = 0.0

    def __str__(self) -> str:
        """Format sensitivity result for display."""
        status = "⚠️  SENSITIVE" if self.is_sensitive else "✅ STABLE"
        return f"""
{status} - {self.parameter}
  Baseline Value: {self.baseline_value}
  Stability Score: {self.stability_score:.3f}
  Performance Range: [{self.performance_range[0]:.3f}, {self.performance_range[1]:.3f}]
  Max Degradation: {self.degradation_percent:.1f}%
  Variations Tested: {len(self.variations)}
"""


class SensitivityTester:
    """
    Test parameter sensitivity by systematic variation.

    **IMPORTANT: This is an OPTIONAL quality check with significant time costs.**

    ⚠️  TIME COST: Each test consumes 50-75 minutes per strategy
        - Testing N parameters = (N × 5) + 1 backtests
        - Typical strategy (4-6 params): 20-30 backtests = 50-75 minutes
        - Use judiciously for champion strategies and final validation

    Provides automated parameter sensitivity testing to identify fragile
    parameters that significantly impact strategy performance. Varies each
    parameter by ±20% and measures performance stability.

    Testing Methodology:
        1. Run baseline backtest with original parameters (1 backtest)
        2. For each parameter, generate variations (±20%)
        3. Run backtest for each variation (5 backtests per param by default)
        4. Calculate stability score: avg_sharpe / baseline_sharpe
        5. Flag parameters with stability < 0.6 as sensitive

    Stability Interpretation:
        - stability ≥ 0.9: Very stable (excellent)
        - 0.7 ≤ stability < 0.9: Stable (good)
        - 0.6 ≤ stability < 0.7: Moderately stable (acceptable)
        - stability < 0.6: Sensitive (requires attention)

    Usage Guidance:
        - Champion strategies: Full testing recommended (all parameters)
        - Development: Skip or test only critical parameters
        - Time-constrained: Test 1-2 most important parameters only
        - Production deployment: Full testing strongly recommended

    Example (Full Testing):
        >>> tester = SensitivityTester()
        >>> # This will take 50-75 minutes for typical strategy
        >>> results = tester.test_parameter_sensitivity(
        ...     template=turtle_template,
        ...     baseline_params={'n_stocks': 10, 'ma_short': 20, 'ma_long': 60},
        ...     parameters_to_test=['n_stocks', 'ma_short']  # Test specific params
        ... )
        >>> for param, result in results.items():
        ...     print(result)

    Example (Skip Testing):
        >>> # During development, simply don't call test_parameter_sensitivity()
        >>> # Proceed directly to deployment without sensitivity testing
    """

    # ═══════════════════════════════════════════════════════════════════════
    # OPTIONAL QUALITY CHECK CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════
    # This testing is OPTIONAL per Requirement 3.3
    # Time Cost: 50-75 minutes per strategy with default settings
    # Recommendation: Use for champion strategies, skip during development
    # ═══════════════════════════════════════════════════════════════════════

    # Sensitivity thresholds
    STABLE_THRESHOLD = 0.9  # stability ≥ 0.9 is very stable
    ACCEPTABLE_THRESHOLD = 0.7  # stability ≥ 0.7 is stable
    MODERATE_THRESHOLD = 0.6  # stability ≥ 0.6 is moderately stable
    SENSITIVE_THRESHOLD = 0.6  # stability < 0.6 is sensitive

    # Variation settings (controls time/accuracy trade-off)
    DEFAULT_VARIATION_PERCENT = 0.20  # ±20% variation from baseline
    DEFAULT_VARIATION_STEPS = 5  # Number of variation points to test
                                  # Reduce to 3 for faster testing (~40% time savings)

    # Timeout settings (prevents runaway backtests)
    DEFAULT_TIMEOUT_PER_PARAMETER = 300  # 5 minutes per parameter (in seconds)
    DEFAULT_TIMEOUT_PER_BACKTEST = 60  # 60 seconds per individual backtest

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize sensitivity tester.

        Args:
            logger: Optional logger for detailed testing information
        """
        self.logger = logger or logging.getLogger(__name__)

    def test_parameter_sensitivity(
        self,
        template: Any,
        baseline_params: Dict[str, Any],
        parameters_to_test: Optional[List[str]] = None,
        variation_percent: float = DEFAULT_VARIATION_PERCENT,
        variation_steps: int = DEFAULT_VARIATION_STEPS,
        timeout_per_parameter: float = DEFAULT_TIMEOUT_PER_PARAMETER,
        timeout_per_backtest: float = DEFAULT_TIMEOUT_PER_BACKTEST
    ) -> Dict[str, SensitivityResult]:
        """
        Test parameter sensitivity for specified parameters.

        ⚠️  TIME IMPLICATIONS:
            - Each parameter tested = 5 backtests (~10-15 minutes)
            - Testing all parameters = (N × 5) + 1 backtests
            - Example: 4 parameters = 21 backtests = ~50 minutes

        USAGE RECOMMENDATIONS:
            - Champion strategies: Test all numeric parameters
            - Development: Test 1-2 critical parameters or skip entirely
            - Time-constrained: Use parameters_to_test to limit scope
            - Quick validation: Reduce variation_steps to 3 (saves ~40% time)

        Args:
            template: Template instance with generate_strategy() method
            baseline_params: Baseline parameter dictionary
            parameters_to_test: List of parameter names to test (None = test all)
            variation_percent: Variation percentage (default: 0.20 for ±20%)
            variation_steps: Number of variation points (default: 5)
            timeout_per_parameter: Maximum seconds per parameter test (default: 300s = 5min)
            timeout_per_backtest: Maximum seconds per individual backtest (default: 60s)

        Returns:
            Dictionary mapping parameter name to SensitivityResult

        Example (Full Testing - 50+ minutes):
            >>> results = tester.test_parameter_sensitivity(
            ...     template=turtle_template,
            ...     baseline_params={'n_stocks': 10, 'ma_short': 20, 'ma_long': 60},
            ...     parameters_to_test=None  # Test all params
            ... )

        Example (Selective Testing - 10-20 minutes):
            >>> results = tester.test_parameter_sensitivity(
            ...     template=turtle_template,
            ...     baseline_params={'n_stocks': 10, 'ma_short': 20},
            ...     parameters_to_test=['n_stocks']  # Test only critical param
            ... )

        Example (Quick Testing - 30 minutes):
            >>> results = tester.test_parameter_sensitivity(
            ...     template=turtle_template,
            ...     baseline_params={'n_stocks': 10, 'ma_short': 20},
            ...     variation_steps=3  # Reduce from 5 to 3 steps
            ... )
        """
        # Step 1: Run baseline backtest
        self.logger.info("Running baseline backtest...")
        baseline_sharpe = self._run_backtest(template, baseline_params)

        if baseline_sharpe is None or baseline_sharpe <= 0:
            self.logger.error(f"Baseline backtest failed: Sharpe = {baseline_sharpe}")
            return {}

        self.logger.info(f"Baseline Sharpe: {baseline_sharpe:.3f}")

        # Step 2: Determine parameters to test
        if parameters_to_test is None:
            parameters_to_test = self._get_testable_parameters(baseline_params)

        # Step 3: Test each parameter
        results = {}
        for param_name in parameters_to_test:
            if param_name not in baseline_params:
                self.logger.warning(f"Parameter '{param_name}' not in baseline_params, skipping")
                continue

            self.logger.info(f"Testing sensitivity for '{param_name}'...")
            result = self._test_single_parameter(
                template=template,
                baseline_params=baseline_params,
                param_name=param_name,
                baseline_sharpe=baseline_sharpe,
                variation_percent=variation_percent,
                variation_steps=variation_steps,
                timeout_per_parameter=timeout_per_parameter,
                timeout_per_backtest=timeout_per_backtest
            )
            results[param_name] = result

        return results

    def _run_backtest(
        self,
        template: Any,
        parameters: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> Optional[float]:
        """
        Run backtest and extract Sharpe ratio with optional timeout protection.

        Args:
            template: Template instance with generate_strategy() method
            parameters: Parameter dictionary for backtest
            timeout: Maximum execution time in seconds (None = no timeout)

        Returns:
            Sharpe ratio (float) or None if backtest fails or times out
        """
        if timeout is None:
            # No timeout - run directly
            return self._execute_backtest(template, parameters)

        # Use ThreadPoolExecutor for timeout protection
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._execute_backtest, template, parameters)
            try:
                return future.result(timeout=timeout)
            except FuturesTimeoutError:
                self.logger.error(f"Backtest timed out after {timeout}s")
                return None
            except Exception as e:
                self.logger.error(f"Backtest failed with exception: {e}")
                return None

    def _execute_backtest(
        self,
        template: Any,
        parameters: Dict[str, Any]
    ) -> Optional[float]:
        """
        Execute backtest and extract Sharpe ratio (internal method without timeout).

        Args:
            template: Template instance with generate_strategy() method
            parameters: Parameter dictionary for backtest

        Returns:
            Sharpe ratio (float) or None if backtest fails
        """
        try:
            # Generate strategy with parameters
            report, metrics = template.generate_strategy(parameters)

            # Extract Sharpe ratio from metrics
            sharpe_ratio = metrics.get('sharpe_ratio', None)

            if sharpe_ratio is None:
                self.logger.error("Sharpe ratio not found in metrics")
                return None

            return float(sharpe_ratio)

        except Exception as e:
            self.logger.error(f"Backtest failed: {e}")
            return None

    def _get_testable_parameters(
        self,
        baseline_params: Dict[str, Any]
    ) -> List[str]:
        """
        Identify testable parameters (numeric only).

        Args:
            baseline_params: Baseline parameter dictionary

        Returns:
            List of parameter names that are numeric (int or float)
        """
        testable = []
        for param_name, param_value in baseline_params.items():
            if isinstance(param_value, (int, float)) and param_name != 'resample':
                testable.append(param_name)

        return testable

    def _test_single_parameter(
        self,
        template: Any,
        baseline_params: Dict[str, Any],
        param_name: str,
        baseline_sharpe: float,
        variation_percent: float,
        variation_steps: int,
        timeout_per_parameter: float,
        timeout_per_backtest: float
    ) -> SensitivityResult:
        """
        Test sensitivity for a single parameter.

        ⚠️  TIME COST: ~10-15 minutes per parameter
            - variation_steps=5 (default): 5 backtests × 2-3 min each
            - variation_steps=3 (fast mode): 3 backtests × 2-3 min each

        Args:
            template: Template instance
            baseline_params: Baseline parameters
            param_name: Parameter name to test
            baseline_sharpe: Baseline Sharpe ratio
            variation_percent: Variation percentage (e.g., 0.20 for ±20%)
            variation_steps: Number of variation points
            timeout_per_parameter: Maximum seconds for all variations of this parameter
            timeout_per_backtest: Maximum seconds per individual backtest

        Returns:
            SensitivityResult with stability score and variations
        """
        baseline_value = baseline_params[param_name]

        # Generate parameter variations
        variations = self._generate_variations(
            baseline_value=baseline_value,
            variation_percent=variation_percent,
            steps=variation_steps
        )

        # Test each variation with timeout protection
        sharpe_values = []
        variation_results = []
        start_time = time.time()

        for varied_value in variations:
            # Check parameter-level timeout
            elapsed = time.time() - start_time
            if elapsed > timeout_per_parameter:
                self.logger.warning(
                    f"Parameter-level timeout reached for '{param_name}' after {elapsed:.1f}s. "
                    f"Tested {len(variation_results)}/{len(variations)} variations."
                )
                break

            # Create parameter set with varied value
            test_params = baseline_params.copy()
            test_params[param_name] = varied_value

            # Run backtest with per-backtest timeout
            sharpe = self._run_backtest(template, test_params, timeout=timeout_per_backtest)

            if sharpe is not None:
                sharpe_values.append(sharpe)
                variation_results.append((varied_value, sharpe))
                self.logger.debug(f"  {param_name}={varied_value}: Sharpe={sharpe:.3f}")
            else:
                self.logger.warning(f"  {param_name}={varied_value}: Backtest failed or timed out")

        # Calculate stability score
        if sharpe_values:
            avg_sharpe = sum(sharpe_values) / len(sharpe_values)
            stability_score = avg_sharpe / baseline_sharpe if baseline_sharpe > 0 else 0.0
            min_sharpe = min(sharpe_values)
            max_sharpe = max(sharpe_values)
            degradation_percent = ((baseline_sharpe - min_sharpe) / baseline_sharpe * 100) if baseline_sharpe > 0 else 0.0
        else:
            stability_score = 0.0
            min_sharpe = 0.0
            max_sharpe = 0.0
            degradation_percent = 100.0

        # Create result
        result = SensitivityResult(
            parameter=param_name,
            baseline_value=baseline_value,
            variations=variation_results,
            stability_score=stability_score,
            is_sensitive=(stability_score < self.SENSITIVE_THRESHOLD),
            performance_range=(min_sharpe, max_sharpe),
            degradation_percent=degradation_percent
        )

        self.logger.info(f"  Stability Score: {stability_score:.3f} {'⚠️  SENSITIVE' if result.is_sensitive else '✅ STABLE'}")

        return result

    def _generate_variations(
        self,
        baseline_value: float,
        variation_percent: float,
        steps: int
    ) -> List[float]:
        """
        Generate parameter variation values.

        Creates variations from baseline ± variation_percent with specified steps.

        Args:
            baseline_value: Original parameter value
            variation_percent: Variation percentage (e.g., 0.20 for ±20%)
            steps: Number of variation points

        Returns:
            List of varied parameter values

        Example:
            >>> variations = tester._generate_variations(10, 0.20, 5)
            >>> variations
            [8.0, 9.0, 10.0, 11.0, 12.0]  # ±20% from 10 in 5 steps
        """
        # Calculate variation range
        min_value = baseline_value * (1 - variation_percent)
        max_value = baseline_value * (1 + variation_percent)

        # Generate evenly spaced variations
        if steps == 1:
            return [baseline_value]

        step_size = (max_value - min_value) / (steps - 1)
        variations = [min_value + i * step_size for i in range(steps)]

        # Handle integer parameters
        if isinstance(baseline_value, int):
            variations = [int(round(v)) for v in variations]
            # Remove duplicates while preserving order
            seen = set()
            variations = [v for v in variations if not (v in seen or seen.add(v))]

        return variations

    def generate_sensitivity_report(
        self,
        results: Dict[str, SensitivityResult],
        baseline_sharpe: float
    ) -> str:
        """
        Generate human-readable sensitivity report.

        Provides comprehensive analysis of parameter stability and recommendations
        for parameter robustness improvements. Use this report to identify which
        parameters require careful tuning vs. which are naturally stable.

        Args:
            results: Dictionary of SensitivityResult objects
            baseline_sharpe: Baseline Sharpe ratio

        Returns:
            Formatted sensitivity report string

        Example:
            >>> report = tester.generate_sensitivity_report(results, 2.0)
            >>> print(report)
            # Displays stability scores, sensitive parameters, and recommendations
        """
        # Count parameters by stability
        very_stable = [r for r in results.values() if r.stability_score >= self.STABLE_THRESHOLD]
        stable = [r for r in results.values() if self.ACCEPTABLE_THRESHOLD <= r.stability_score < self.STABLE_THRESHOLD]
        moderate = [r for r in results.values() if self.MODERATE_THRESHOLD <= r.stability_score < self.ACCEPTABLE_THRESHOLD]
        sensitive = [r for r in results.values() if r.stability_score < self.SENSITIVE_THRESHOLD]

        report = f"""
╔══════════════════════════════════════════════════════════════════════╗
║              PARAMETER SENSITIVITY TESTING REPORT                    ║
╚══════════════════════════════════════════════════════════════════════╝

Baseline Sharpe Ratio: {baseline_sharpe:.3f}
Parameters Tested: {len(results)}

SUMMARY BY STABILITY:
  ✅ Very Stable (≥0.9):      {len(very_stable)} parameters
  ✅ Stable (0.7-0.9):        {len(stable)} parameters
  ⚠️  Moderately Stable (0.6-0.7): {len(moderate)} parameters
  🚨 Sensitive (<0.6):        {len(sensitive)} parameters

"""

        # Report sensitive parameters first
        if sensitive:
            report += "🚨 SENSITIVE PARAMETERS (Require Attention):\n"
            report += "=" * 70 + "\n"
            for result in sorted(sensitive, key=lambda r: r.stability_score):
                report += str(result)

        # Report moderate parameters
        if moderate:
            report += "\n⚠️  MODERATELY STABLE PARAMETERS:\n"
            report += "=" * 70 + "\n"
            for result in sorted(moderate, key=lambda r: r.stability_score):
                report += str(result)

        # Report stable parameters
        if stable or very_stable:
            report += "\n✅ STABLE PARAMETERS:\n"
            report += "=" * 70 + "\n"
            for result in sorted(stable + very_stable, key=lambda r: r.stability_score, reverse=True):
                report += str(result)

        # Recommendations
        report += "\nRECOMMENDATIONS:\n"
        report += "=" * 70 + "\n"

        if sensitive:
            report += f"⚠️  {len(sensitive)} sensitive parameter(s) detected:\n"
            for result in sensitive:
                report += f"   - {result.parameter}: Consider using more robust values or implementing parameter constraints\n"

        if moderate:
            report += f"ℹ️  {len(moderate)} moderately stable parameter(s):\n"
            for result in moderate:
                report += f"   - {result.parameter}: Monitor performance variations during parameter optimization\n"

        if very_stable and not sensitive:
            report += "✅ All parameters show good stability. Strategy is robust to parameter variations.\n"

        return report

    def identify_robust_ranges(
        self,
        results: Dict[str, SensitivityResult],
        min_stability: float = 0.7
    ) -> Dict[str, Tuple[Any, Any]]:
        """
        Identify robust parameter ranges based on stability testing.

        Args:
            results: Dictionary of SensitivityResult objects
            min_stability: Minimum stability threshold (default: 0.7)

        Returns:
            Dictionary mapping parameter to (min_value, max_value) robust range

        Example:
            >>> robust_ranges = tester.identify_robust_ranges(results, min_stability=0.7)
            >>> print(robust_ranges['n_stocks'])
            (8, 12)  # Robust range for n_stocks parameter
        """
        robust_ranges = {}

        for param_name, result in results.items():
            if result.stability_score >= min_stability:
                # Extract variation values
                values = [v for v, _ in result.variations]

                if values:
                    robust_ranges[param_name] = (min(values), max(values))

        return robust_ranges
