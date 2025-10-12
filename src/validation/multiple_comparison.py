"""
Bonferroni Multiple Comparison Correction

Prevents false discoveries due to testing multiple strategies:
- Adjusts significance threshold: α / n
- Calculates Sharpe ratio threshold for statistical significance
- Validates strategy set false discovery rate

The Problem:
    Testing 500 strategies at α=0.05 (5% significance)
    Expected false discoveries: 500 × 0.05 = 25 strategies

The Solution:
    Bonferroni correction: adjusted_alpha = α / n_strategies
    Example: 0.05 / 500 = 0.0001 (0.01% significance)

Sharpe Ratio Significance:
    threshold_formula: Sharpe > Z(1 - α/(2n)) / sqrt(T)
    for_500_strategies: Sharpe > 3.89 / sqrt(252) ≈ 0.245
    conservative_threshold: 0.5 (recommended for real trading)
"""

from typing import Dict, List, Any, Optional
import numpy as np
from scipy.stats import norm
import logging

logger = logging.getLogger(__name__)


class BonferroniValidator:
    """
    Implements Bonferroni multiple comparison correction for strategy validation.

    This validator prevents false discoveries when testing multiple strategies by
    adjusting the significance threshold based on the number of strategies tested.

    Key Concepts:
        - Family-Wise Error Rate (FWER): Probability of at least one false discovery
        - Bonferroni Correction: Ensures FWER ≤ α by testing each hypothesis at α/n
        - Conservative Threshold: Uses max(calculated, 0.5) to prevent false positives

    Example:
        >>> validator = BonferroniValidator(n_strategies=500, alpha=0.05)
        >>> threshold = validator.calculate_significance_threshold()
        >>> print(f"Sharpe must be > {threshold:.4f} to be significant")
        Sharpe must be > 0.5000 to be significant

        >>> is_sig = validator.is_significant(sharpe_ratio=1.5)
        >>> print(f"Sharpe 1.5 is significant: {is_sig}")
        Sharpe 1.5 is significant: True
    """

    def __init__(
        self,
        n_strategies: int = 500,
        alpha: float = 0.05
    ):
        """
        Initialize Bonferroni validator.

        Args:
            n_strategies: Total number of strategies tested
            alpha: Unadjusted significance level (e.g., 0.05 = 5%)

        Raises:
            ValueError: If n_strategies <= 0 or alpha not in (0, 1)
        """
        if n_strategies <= 0:
            raise ValueError(f"n_strategies must be positive, got {n_strategies}")
        if not (0 < alpha < 1):
            raise ValueError(f"alpha must be in (0, 1), got {alpha}")

        self.n_strategies = n_strategies
        self.alpha = alpha
        self.adjusted_alpha = alpha / n_strategies

        logger.info(f"Bonferroni correction initialized:")
        logger.info(f"  Number of strategies: {n_strategies}")
        logger.info(f"  Original α: {alpha}")
        logger.info(f"  Adjusted α: {self.adjusted_alpha:.6f}")

    def calculate_significance_threshold(
        self,
        n_periods: int = 252,
        use_conservative: bool = True
    ) -> float:
        """
        Calculate Bonferroni-adjusted Sharpe ratio threshold.

        The threshold is calculated as:
            1. Z-score from adjusted alpha: Z = norm.ppf(1 - adjusted_alpha / 2)
            2. Sharpe threshold: threshold = Z / sqrt(T)
            3. Conservative adjustment: max(threshold, 0.5)

        Args:
            n_periods: Number of time periods (e.g., 252 trading days)
            use_conservative: Whether to use conservative threshold (recommended)

        Returns:
            Sharpe ratio significance threshold

        Raises:
            ValueError: If n_periods <= 0

        Example:
            >>> validator = BonferroniValidator(n_strategies=500)
            >>> threshold = validator.calculate_significance_threshold(n_periods=252)
            >>> print(f"Theoretical: {threshold:.4f}, Conservative: 0.5000")
        """
        if n_periods <= 0:
            raise ValueError(f"n_periods must be positive, got {n_periods}")

        # Calculate z-score for adjusted alpha (two-tailed test)
        z_score = norm.ppf(1 - self.adjusted_alpha / 2)

        # Sharpe ratio threshold = z / sqrt(T)
        threshold = z_score / np.sqrt(n_periods)

        logger.info(f"Significance threshold calculation:")
        logger.info(f"  Z-score (adjusted α={self.adjusted_alpha:.6f}): {z_score:.2f}")
        logger.info(f"  Theoretical threshold: {threshold:.4f}")

        if use_conservative:
            # Use conservative threshold (recommended for actual trading)
            conservative_threshold = max(0.5, threshold)
            logger.info(f"  Conservative threshold: {conservative_threshold:.4f}")
            return conservative_threshold

        return threshold

    def calculate_bootstrap_threshold(
        self,
        n_periods: int = 252,
        n_bootstrap: int = 1000,
        block_size: int = 21,
        market_volatility: float = 0.22
    ) -> Dict[str, Any]:
        """
        Calculate Sharpe significance threshold using bootstrap under null hypothesis.

        More robust than parametric method for Taiwan market's fat-tailed distributions.

        Args:
            n_periods: Number of trading periods (default 252)
            n_bootstrap: Bootstrap iterations (default 1000)
            block_size: Block size for bootstrap (default 21)
            market_volatility: Annual market volatility (default 0.22 for Taiwan ~22%)

        Returns:
            Dictionary with:
                - bootstrap_threshold: Bootstrap-based threshold
                - parametric_threshold: Traditional parametric threshold
                - difference: Absolute difference
                - percent_diff: Percentage difference
                - n_valid: Number of valid bootstrap samples
                - method: 'bootstrap'

        Example:
            >>> validator = BonferroniValidator(n_strategies=500)
            >>> result = validator.calculate_bootstrap_threshold()
            >>> print(f"Bootstrap: {result['bootstrap_threshold']:.4f}")
            >>> print(f"Parametric: {result['parametric_threshold']:.4f}")

        Algorithm:
            1. Generate null hypothesis returns: N(0, σ²) with σ from Taiwan market
            2. Bootstrap resample and calculate Sharpe ratios
            3. Find (1 - adjusted_alpha) percentile as threshold
            4. Compare with parametric threshold for validation

        References:
            - Efron & Tibshirani (1993): "An Introduction to the Bootstrap"
            - Politis & Romano (1994): "The Stationary Bootstrap"
        """
        try:
            from .bootstrap import _block_bootstrap_resample, _calculate_sharpe_ratio
        except ImportError:
            logger.error("Bootstrap module not available - falling back to parametric threshold")
            parametric = self.calculate_significance_threshold(n_periods, use_conservative=False)
            return {
                'bootstrap_threshold': parametric,
                'parametric_threshold': parametric,
                'difference': 0.0,
                'percent_diff': 0.0,
                'n_valid': 0,
                'method': 'parametric_fallback',
                'error': 'Bootstrap module import failed'
            }

        # Estimate Taiwan market daily volatility
        # Annual volatility ~22% → Daily volatility = 22% / sqrt(252)
        daily_vol = market_volatility / np.sqrt(252)

        logger.info(f"Bootstrap threshold calculation:")
        logger.info(f"  Market volatility (annual): {market_volatility:.1%}")
        logger.info(f"  Daily volatility: {daily_vol:.4f}")
        logger.info(f"  Null hypothesis: Returns ~ N(0, {daily_vol:.4f}²)")

        # Generate null hypothesis returns: zero mean, market volatility
        null_returns = np.random.normal(0, daily_vol, n_periods)

        # Bootstrap under null hypothesis
        bootstrap_sharpes = []
        for _ in range(n_bootstrap):
            resampled = _block_bootstrap_resample(null_returns, block_size)
            sharpe = _calculate_sharpe_ratio(resampled)
            if not np.isnan(sharpe):
                bootstrap_sharpes.append(abs(sharpe))  # Take absolute for two-tailed

        n_valid = len(bootstrap_sharpes)
        if n_valid < n_bootstrap * 0.9:
            logger.warning(
                f"Low bootstrap success rate: {n_valid}/{n_bootstrap} "
                f"({n_valid/n_bootstrap:.1%})"
            )

        # Calculate threshold as (1 - adjusted_alpha/2) percentile
        # Two-tailed test: we want P(|Sharpe| > threshold) = adjusted_alpha
        percentile = (1 - self.adjusted_alpha / 2) * 100
        bootstrap_threshold = np.percentile(bootstrap_sharpes, percentile)

        # Compare with parametric threshold
        z_score = norm.ppf(1 - self.adjusted_alpha / 2)
        parametric_threshold = z_score / np.sqrt(n_periods)

        difference = bootstrap_threshold - parametric_threshold
        percent_diff = (difference / parametric_threshold * 100) if parametric_threshold > 0 else 0.0

        result = {
            'bootstrap_threshold': float(bootstrap_threshold),
            'parametric_threshold': float(parametric_threshold),
            'difference': float(difference),
            'percent_diff': float(percent_diff),
            'n_valid': n_valid,
            'n_bootstrap': n_bootstrap,
            'method': 'bootstrap'
        }

        logger.info(f"  Bootstrap threshold: {bootstrap_threshold:.4f}")
        logger.info(f"  Parametric threshold: {parametric_threshold:.4f}")
        logger.info(f"  Difference: {difference:+.4f} ({percent_diff:+.1f}%)")
        logger.info(f"  Valid samples: {n_valid}/{n_bootstrap}")

        # Warning if large difference
        if abs(percent_diff) > 20:
            logger.warning(
                f"Large difference ({percent_diff:+.1f}%) between bootstrap and parametric thresholds. "
                f"This suggests normality assumption may not hold for Taiwan market. "
                f"Consider using bootstrap threshold for more robust validation."
            )

        return result

    def is_significant(
        self,
        sharpe_ratio: float,
        n_periods: int = 252,
        use_conservative: bool = True
    ) -> bool:
        """
        Test if a Sharpe ratio is statistically significant.

        Args:
            sharpe_ratio: Sharpe ratio to test
            n_periods: Number of time periods (e.g., 252 trading days)
            use_conservative: Whether to use conservative threshold

        Returns:
            True if Sharpe ratio is statistically significant

        Example:
            >>> validator = BonferroniValidator(n_strategies=500)
            >>> validator.is_significant(sharpe_ratio=0.3)
            False
            >>> validator.is_significant(sharpe_ratio=1.5)
            True
        """
        if not np.isfinite(sharpe_ratio):
            logger.warning(f"Invalid Sharpe ratio: {sharpe_ratio}")
            return False

        threshold = self.calculate_significance_threshold(n_periods, use_conservative)
        return abs(sharpe_ratio) > threshold

    def validate_strategy_set(
        self,
        strategies_with_sharpes: List[Dict[str, Any]],
        n_periods: int = 252
    ) -> Dict[str, Any]:
        """
        Validate entire strategy set with multiple comparison correction.

        Args:
            strategies_with_sharpes: List of strategies, each with 'sharpe_ratio' key
            n_periods: Number of time periods for threshold calculation

        Returns:
            Validation results dictionary with:
                - total_strategies: Total number of strategies tested
                - significant_count: Number of statistically significant strategies
                - significance_threshold: Sharpe threshold used
                - adjusted_alpha: Bonferroni-adjusted alpha
                - expected_false_discoveries: Expected number of false positives
                - estimated_fdr: Estimated false discovery rate
                - significant_strategies: List of significant strategies

        Example:
            >>> strategies = [
            ...     {'name': 'Strategy_A', 'sharpe_ratio': 1.8},
            ...     {'name': 'Strategy_B', 'sharpe_ratio': 0.3},
            ...     {'name': 'Strategy_C', 'sharpe_ratio': 2.1},
            ... ]
            >>> results = validator.validate_strategy_set(strategies)
            >>> print(f"Significant: {results['significant_count']}/{results['total_strategies']}")
        """
        if not strategies_with_sharpes:
            logger.warning("Empty strategy list provided")
            return {
                'total_strategies': 0,
                'significant_count': 0,
                'significance_threshold': 0.0,
                'adjusted_alpha': self.adjusted_alpha,
                'expected_false_discoveries': 0.0,
                'estimated_fdr': 0.0,
                'significant_strategies': []
            }

        threshold = self.calculate_significance_threshold(n_periods)

        # Identify significant strategies
        significant_strategies = []
        for strategy in strategies_with_sharpes:
            sharpe = strategy.get('sharpe_ratio', 0.0)
            if self.is_significant(sharpe, n_periods):
                significant_strategies.append(strategy)

        # Calculate false discovery rate
        expected_false_discoveries = self.adjusted_alpha * len(strategies_with_sharpes)

        # Avoid division by zero
        estimated_fdr = (
            expected_false_discoveries / max(1, len(significant_strategies))
            if significant_strategies else 0.0
        )

        results = {
            'total_strategies': len(strategies_with_sharpes),
            'significant_count': len(significant_strategies),
            'significance_threshold': threshold,
            'adjusted_alpha': self.adjusted_alpha,
            'expected_false_discoveries': expected_false_discoveries,
            'estimated_fdr': estimated_fdr,
            'significant_strategies': significant_strategies
        }

        logger.info(f"Strategy set validation:")
        logger.info(f"  Total strategies: {results['total_strategies']}")
        logger.info(f"  Significant strategies: {results['significant_count']}")
        logger.info(f"  Significance threshold: {threshold:.4f}")
        logger.info(f"  Expected false discoveries: {expected_false_discoveries:.2f}")
        logger.info(f"  Estimated FDR: {results['estimated_fdr']:.2%}")

        return results

    def calculate_family_wise_error_rate(self) -> float:
        """
        Calculate Family-Wise Error Rate (FWER).

        FWER = Probability of at least one false discovery
        Bonferroni guarantee: FWER ≤ α

        The exact FWER is: 1 - (1 - adjusted_alpha)^n
        For small alpha, this approximates to: n * adjusted_alpha = alpha

        Returns:
            Family-wise error rate

        Example:
            >>> validator = BonferroniValidator(n_strategies=500, alpha=0.05)
            >>> fwer = validator.calculate_family_wise_error_rate()
            >>> print(f"FWER: {fwer:.4f}, Guarantee: ≤ 0.05")
        """
        # Exact calculation: FWER = 1 - (1 - α/n)^n
        fwer = 1 - (1 - self.adjusted_alpha) ** self.n_strategies

        logger.info(f"Family-Wise Error Rate (FWER): {fwer:.4f}")
        logger.info(f"Bonferroni guarantee: FWER ≤ {self.alpha}")

        return fwer

    def generate_report(
        self,
        validation_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a human-readable validation report.

        Args:
            validation_results: Results from validate_strategy_set() (optional)

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 70)
        report.append("BONFERRONI MULTIPLE COMPARISON CORRECTION REPORT")
        report.append("=" * 70)
        report.append("")

        # Configuration
        report.append("Configuration:")
        report.append(f"  Total strategies tested: {self.n_strategies}")
        report.append(f"  Significance level (α): {self.alpha}")
        report.append(f"  Adjusted α (Bonferroni): {self.adjusted_alpha:.6f}")
        report.append("")

        # FWER
        fwer = self.calculate_family_wise_error_rate()
        report.append("Family-Wise Error Rate:")
        report.append(f"  Calculated FWER: {fwer:.4f}")
        report.append(f"  Bonferroni guarantee: FWER ≤ {self.alpha}")
        report.append("")

        # Validation results
        if validation_results:
            report.append("Validation Results:")
            report.append(f"  Total strategies: {validation_results['total_strategies']}")
            report.append(f"  Significant strategies: {validation_results['significant_count']}")
            report.append(f"  Significance threshold: {validation_results['significance_threshold']:.4f}")
            report.append(f"  Expected false discoveries: {validation_results['expected_false_discoveries']:.2f}")
            report.append(f"  Estimated FDR: {validation_results['estimated_fdr']:.2%}")
            report.append("")

        report.append("=" * 70)

        return "\n".join(report)
