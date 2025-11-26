"""
BaselineMetrics: Immutable Baseline Metrics Framework

This module implements the baseline metrics framework required by Condition 1
of the Executive Approval. It computes 20+ performance metrics from the
20-generation baseline test and establishes adaptive thresholds.

Key Features:
- Compute baseline metrics from Week 1 test
- Lock baseline as immutable reference
- Compute adaptive thresholds (e.g., Sharpe ≥ baseline × 1.2)
- Statistical validation (paired t-test, Wilcoxon signed-rank)

Executive Mandate: "Create immutable baseline metrics" - Opus 4.1

Usage:
    # Week 1: Compute and lock baseline
    from src.innovation.baseline_metrics import BaselineMetrics

    baseline = BaselineMetrics()
    baseline.compute_baseline(iteration_history_path='iteration_history.json')
    baseline.lock_baseline()

    # Week 2+: Compare innovations against baseline
    is_improvement = baseline.validate_innovation(
        sharpe_ratio=0.85,
        max_drawdown=0.18,
        calmar_ratio=2.8
    )
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from scipy import stats


class BaselineMetrics:
    """
    Immutable baseline metrics framework.

    This class computes and locks baseline performance metrics from the
    Week 1 20-generation test. These metrics serve as the reference point
    for all future innovations, preventing metric inflation.

    Attributes:
        config_path: Path to baseline configuration file
        baseline_hash: SHA-256 hash of baseline metrics
        lock_timestamp: When baseline was locked
        is_locked: Whether baseline is locked (immutable)
        metrics: Dictionary of baseline metrics
    """

    def __init__(self, config_path: str = '.spec-workflow/specs/llm-innovation-capability/baseline_metrics.json'):
        """
        Initialize BaselineMetrics.

        Args:
            config_path: Path to store baseline configuration
        """
        self.config_path = Path(config_path)
        self.baseline_hash: Optional[str] = None
        self.lock_timestamp: Optional[str] = None
        self.is_locked: bool = False
        self.metrics: Dict[str, Any] = {}

        # Load existing baseline if present
        if self.config_path.exists():
            self._load_baseline()

    def compute_baseline(self, iteration_history_path: str) -> Dict[str, Any]:
        """
        Compute baseline metrics from Week 1 20-generation test.

        This method analyzes the iteration history from the baseline test
        and computes 20+ performance metrics across all strategies.

        Args:
            iteration_history_path: Path to iteration_history.json from Week 1 test

        Returns:
            dict with computed baseline metrics

        Example:
            >>> baseline = BaselineMetrics()
            >>> metrics = baseline.compute_baseline('iteration_history.json')
            >>> print(f"Baseline Sharpe: {metrics['mean_sharpe']:.3f}")
            Baseline Sharpe: 0.654
        """
        if self.is_locked:
            raise RuntimeError("Baseline is already locked. Cannot recompute.")

        # Load iteration history
        with open(iteration_history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)

        # Extract metrics from all iterations
        sharpe_ratios = []
        calmar_ratios = []
        max_drawdowns = []
        total_returns = []
        win_rates = []

        for iteration in history:
            metrics = iteration.get('metrics', {})
            if metrics:
                sharpe_ratios.append(metrics.get('sharpe_ratio', 0))
                calmar_ratios.append(metrics.get('calmar_ratio', 0))
                max_drawdowns.append(metrics.get('max_drawdown', 0))
                total_returns.append(metrics.get('total_return', 0))
                win_rates.append(metrics.get('win_rate', 0))

        # Compute baseline statistics
        self.metrics = {
            # Sharpe Ratio
            'mean_sharpe': float(np.mean(sharpe_ratios)),
            'median_sharpe': float(np.median(sharpe_ratios)),
            'std_sharpe': float(np.std(sharpe_ratios)),
            'min_sharpe': float(np.min(sharpe_ratios)),
            'max_sharpe': float(np.max(sharpe_ratios)),
            'p25_sharpe': float(np.percentile(sharpe_ratios, 25)),
            'p75_sharpe': float(np.percentile(sharpe_ratios, 75)),

            # Calmar Ratio
            'mean_calmar': float(np.mean(calmar_ratios)),
            'median_calmar': float(np.median(calmar_ratios)),
            'std_calmar': float(np.std(calmar_ratios)),

            # Max Drawdown
            'mean_mdd': float(np.mean(max_drawdowns)),
            'median_mdd': float(np.median(max_drawdowns)),
            'std_mdd': float(np.std(max_drawdowns)),

            # Total Return
            'mean_return': float(np.mean(total_returns)),
            'median_return': float(np.median(total_returns)),
            'std_return': float(np.std(total_returns)),

            # Win Rate
            'mean_win_rate': float(np.mean(win_rates)),
            'median_win_rate': float(np.median(win_rates)),

            # Adaptive Thresholds (Opus 4.1 modification)
            'adaptive_sharpe_threshold': float(np.mean(sharpe_ratios) * 1.2),
            'adaptive_calmar_threshold': float(np.mean(calmar_ratios) * 1.2),
            'max_drawdown_limit': 0.25,  # Fixed at 25%

            # Meta
            'total_iterations': len(history),
            'computation_timestamp': datetime.now().isoformat(),
            'source_file': iteration_history_path
        }

        print(f"✅ Baseline metrics computed from {len(history)} iterations")
        print(f"   Mean Sharpe: {self.metrics['mean_sharpe']:.3f}")
        print(f"   Adaptive Sharpe Threshold: {self.metrics['adaptive_sharpe_threshold']:.3f}")
        print(f"   Mean Calmar: {self.metrics['mean_calmar']:.3f}")
        print(f"   Adaptive Calmar Threshold: {self.metrics['adaptive_calmar_threshold']:.3f}")
        print(f"   Mean MDD: {self.metrics['mean_mdd']:.1%}")

        return self.metrics

    def lock_baseline(self) -> Dict[str, Any]:
        """
        Lock baseline metrics as immutable reference.

        This method computes a SHA-256 hash of the baseline metrics and
        marks them as locked. Once locked, the baseline cannot be modified.

        Returns:
            dict with lock record

        Example:
            >>> baseline.lock_baseline()
            ✅ Baseline metrics LOCKED
               Hash: a1b2c3...
               Timestamp: 2025-10-23T14:30:00
        """
        if not self.metrics:
            raise ValueError("No metrics to lock. Call compute_baseline() first.")

        if self.is_locked:
            raise RuntimeError("Baseline is already locked.")

        # Compute SHA-256 hash
        metrics_json = json.dumps(self.metrics, sort_keys=True)
        self.baseline_hash = hashlib.sha256(metrics_json.encode('utf-8')).hexdigest()
        self.lock_timestamp = datetime.now().isoformat()
        self.is_locked = True

        # Create lock record
        lock_record = {
            'baseline_hash': self.baseline_hash,
            'lock_timestamp': self.lock_timestamp,
            'is_locked': True,
            'metrics': self.metrics
        }

        # Save lock configuration
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(lock_record, f, indent=2)

        print(f"✅ Baseline metrics LOCKED")
        print(f"   Hash: {self.baseline_hash}")
        print(f"   Timestamp: {self.lock_timestamp}")

        return lock_record

    def validate_innovation(
        self,
        sharpe_ratio: float,
        max_drawdown: float,
        calmar_ratio: float,
        verbose: bool = True
    ) -> bool:
        """
        Validate innovation against baseline adaptive thresholds.

        This method checks whether an innovation meets the adaptive
        thresholds derived from baseline metrics.

        Args:
            sharpe_ratio: Innovation's Sharpe ratio
            max_drawdown: Innovation's max drawdown (absolute value)
            calmar_ratio: Innovation's Calmar ratio
            verbose: Print validation details

        Returns:
            True if innovation passes all thresholds

        Example:
            >>> baseline.validate_innovation(
            ...     sharpe_ratio=0.85,
            ...     max_drawdown=0.18,
            ...     calmar_ratio=2.8
            ... )
            ✅ Innovation PASSES adaptive thresholds
               Sharpe: 0.850 ≥ 0.785 (baseline × 1.2) ✓
               MDD: 0.180 ≤ 0.250 (limit) ✓
               Calmar: 2.800 ≥ 2.400 (baseline × 1.2) ✓
        """
        if not self.is_locked:
            raise RuntimeError("Baseline not locked. Call lock_baseline() first.")

        # Check adaptive thresholds
        sharpe_pass = sharpe_ratio >= self.metrics['adaptive_sharpe_threshold']
        mdd_pass = max_drawdown <= self.metrics['max_drawdown_limit']
        calmar_pass = calmar_ratio >= self.metrics['adaptive_calmar_threshold']

        all_pass = sharpe_pass and mdd_pass and calmar_pass

        if verbose:
            status = "✅ PASSES" if all_pass else "❌ FAILS"
            print(f"{status} adaptive thresholds")

            sharpe_symbol = "✓" if sharpe_pass else "✗"
            print(f"   Sharpe: {sharpe_ratio:.3f} ≥ {self.metrics['adaptive_sharpe_threshold']:.3f} (baseline × 1.2) {sharpe_symbol}")

            mdd_symbol = "✓" if mdd_pass else "✗"
            print(f"   MDD: {max_drawdown:.3f} ≤ {self.metrics['max_drawdown_limit']:.3f} (limit) {mdd_symbol}")

            calmar_symbol = "✓" if calmar_pass else "✗"
            print(f"   Calmar: {calmar_ratio:.3f} ≥ {self.metrics['adaptive_calmar_threshold']:.3f} (baseline × 1.2) {calmar_symbol}")

        return all_pass

    def get_baseline_summary(self) -> Dict[str, Any]:
        """
        Get baseline summary for reporting.

        Returns:
            dict with baseline status and key metrics
        """
        if not self.is_locked:
            return {
                'is_locked': False,
                'status': 'NOT_LOCKED',
                'message': 'Baseline not yet locked. Call lock_baseline() first.'
            }

        return {
            'is_locked': True,
            'lock_timestamp': self.lock_timestamp,
            'baseline_hash': self.baseline_hash,
            'total_iterations': self.metrics.get('total_iterations', 0),
            'key_metrics': {
                'mean_sharpe': self.metrics['mean_sharpe'],
                'adaptive_sharpe_threshold': self.metrics['adaptive_sharpe_threshold'],
                'mean_calmar': self.metrics['mean_calmar'],
                'adaptive_calmar_threshold': self.metrics['adaptive_calmar_threshold'],
                'mean_mdd': self.metrics['mean_mdd'],
                'max_drawdown_limit': self.metrics['max_drawdown_limit']
            }
        }

    def _load_baseline(self) -> dict:
        """Load baseline configuration from disk."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.baseline_hash = config['baseline_hash']
        self.lock_timestamp = config['lock_timestamp']
        self.is_locked = config['is_locked']
        self.metrics = config['metrics']

        return config


class StatisticalValidator:
    """
    Statistical significance testing for innovations.

    This class implements the statistical tests required by the
    Pre-Implementation Audit to validate that innovations are
    statistically significant improvements over baseline.
    """

    @staticmethod
    def paired_t_test(
        baseline_sharpe_values: List[float],
        innovation_sharpe_values: List[float],
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Paired t-test for Sharpe ratio improvement.

        Args:
            baseline_sharpe_values: List of Sharpe ratios from baseline
            innovation_sharpe_values: List of Sharpe ratios from innovation
            alpha: Significance level (default: 0.05)

        Returns:
            dict with t-statistic, p-value, and significance result
        """
        t_stat, p_value = stats.ttest_rel(innovation_sharpe_values, baseline_sharpe_values)

        is_significant = p_value < alpha
        mean_improvement = np.mean(innovation_sharpe_values) - np.mean(baseline_sharpe_values)

        return {
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'alpha': alpha,
            'is_significant': is_significant,
            'mean_improvement': float(mean_improvement),
            'conclusion': 'SIGNIFICANT' if is_significant else 'NOT_SIGNIFICANT'
        }

    @staticmethod
    def wilcoxon_test(
        baseline_sharpe_values: List[float],
        innovation_sharpe_values: List[float],
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Wilcoxon signed-rank test (non-parametric alternative).

        Args:
            baseline_sharpe_values: List of Sharpe ratios from baseline
            innovation_sharpe_values: List of Sharpe ratios from innovation
            alpha: Significance level (default: 0.05)

        Returns:
            dict with test statistic, p-value, and significance result
        """
        statistic, p_value = stats.wilcoxon(
            innovation_sharpe_values,
            baseline_sharpe_values,
            alternative='greater'
        )

        is_significant = p_value < alpha
        median_improvement = np.median(innovation_sharpe_values) - np.median(baseline_sharpe_values)

        return {
            'statistic': float(statistic),
            'p_value': float(p_value),
            'alpha': alpha,
            'is_significant': is_significant,
            'median_improvement': float(median_improvement),
            'conclusion': 'SIGNIFICANT' if is_significant else 'NOT_SIGNIFICANT'
        }

    @staticmethod
    def holdout_validation(
        innovation_sharpe: float,
        baseline_mean_sharpe: float,
        baseline_std_sharpe: float,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Hold-out validation with confidence intervals.

        Args:
            innovation_sharpe: Sharpe ratio on hold-out set
            baseline_mean_sharpe: Mean Sharpe from baseline
            baseline_std_sharpe: Std dev of Sharpe from baseline
            confidence_level: Confidence level (default: 0.95)

        Returns:
            dict with validation result and confidence interval
        """
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        margin = z_score * baseline_std_sharpe

        lower_bound = baseline_mean_sharpe - margin
        upper_bound = baseline_mean_sharpe + margin

        is_exceptional = innovation_sharpe > upper_bound
        is_within_baseline = lower_bound <= innovation_sharpe <= upper_bound
        is_below_baseline = innovation_sharpe < lower_bound

        return {
            'innovation_sharpe': innovation_sharpe,
            'baseline_ci_lower': float(lower_bound),
            'baseline_ci_upper': float(upper_bound),
            'confidence_level': confidence_level,
            'is_exceptional': is_exceptional,
            'is_within_baseline': is_within_baseline,
            'is_below_baseline': is_below_baseline,
            'conclusion': 'EXCEPTIONAL' if is_exceptional else ('BASELINE' if is_within_baseline else 'BELOW_BASELINE')
        }
