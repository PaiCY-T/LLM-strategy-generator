"""Variance Monitor for Learning System Convergence Tracking.

This module provides VarianceMonitor to track Sharpe ratio variance over time
and detect learning convergence or instability patterns.

Requirements: F1.1 (rolling variance), F1.2 (alert conditions), F1.3 (convergence reports)
"""

from collections import deque
from typing import Dict, List, Tuple, Optional
import numpy as np


class VarianceMonitor:
    """Monitor Sharpe ratio variance to detect convergence and instability.

    Tracks rolling variance with configurable window (default 10 iterations).
    Success criterion: σ < 0.5 after iteration 10 indicates convergence.
    Alert threshold: σ > 0.8 for 5+ consecutive iterations indicates instability.

    Attributes:
        alert_threshold: Variance threshold triggering stability alerts (default 0.8)
        sharpes: Rolling window deque for recent Sharpe ratios (maxlen=10)
        all_sharpes: Complete history of all Sharpe ratios
        consecutive_high_variance_count: Counter for alert condition tracking
    """

    def __init__(self, alert_threshold: float = 0.8):
        """Initialize VarianceMonitor with configurable alert threshold.

        Args:
            alert_threshold: Variance threshold for instability alerts (default 0.8)
        """
        self.alert_threshold = alert_threshold
        self.sharpes: deque = deque(maxlen=10)  # Rolling window for variance calculation
        self.all_sharpes: List[float] = []  # Full history
        self.consecutive_high_variance_count: int = 0  # Track consecutive alerts

    def update(self, iteration_num: int, sharpe: float) -> None:
        """Update monitor with new iteration Sharpe ratio.

        Args:
            iteration_num: Current iteration number (for logging context)
            sharpe: Sharpe ratio from current iteration
        """
        self.sharpes.append(sharpe)
        self.all_sharpes.append(sharpe)

    def get_rolling_variance(self, window: int = 10) -> float:
        """Calculate rolling variance (standard deviation) of recent Sharpe ratios.

        Args:
            window: Number of recent iterations to include (default 10)

        Returns:
            Standard deviation (σ) of Sharpe ratios, or 0.0 if insufficient data
        """
        if len(self.sharpes) < 2:
            return 0.0

        # Use actual window size or available data, whichever is smaller
        effective_window = min(window, len(self.sharpes))
        recent_sharpes = list(self.sharpes)[-effective_window:]

        return float(np.std(recent_sharpes, ddof=1))  # Sample standard deviation

    def check_alert_condition(self) -> Tuple[bool, str]:
        """Check if alert condition is met (high variance for 5+ consecutive iterations).

        Alert triggers when σ > alert_threshold for 5+ consecutive iterations,
        indicating unstable learning.

        Returns:
            Tuple of (alert_triggered, context_message)
        """
        current_variance = self.get_rolling_variance()

        # Check if current variance exceeds threshold
        if current_variance > self.alert_threshold:
            self.consecutive_high_variance_count += 1
        else:
            self.consecutive_high_variance_count = 0  # Reset counter

        # Trigger alert if 5+ consecutive high variance iterations
        if self.consecutive_high_variance_count >= 5:
            return (
                True,
                f"High variance (σ={current_variance:.4f}) for {self.consecutive_high_variance_count} consecutive iterations. "
                f"Learning may be unstable."
            )

        return (False, "")

    def generate_convergence_report(self) -> Dict[str, any]:
        """Generate comprehensive convergence analysis report.

        Analyzes variance trend, detects convergence point, and provides
        recommendations for system tuning.

        Returns:
            Dict containing:
                - variance_trend: List of (iteration, variance) tuples
                - convergence_status: "converged", "converging", or "unstable"
                - convergence_iteration: First iteration where σ < 0.5 (after iter 10), or None
                - current_variance: Latest rolling variance
                - recommendations: List of actionable recommendations
        """
        # Calculate variance trend (rolling window over time)
        variance_trend = []
        window = 10

        for i in range(len(self.all_sharpes)):
            if i >= window - 1:  # Need at least 'window' points
                window_sharpes = self.all_sharpes[max(0, i - window + 1):i + 1]
                if len(window_sharpes) >= 2:
                    variance = float(np.std(window_sharpes, ddof=1))
                    variance_trend.append((i, variance))

        # Detect convergence point (first time σ < 0.5 after iteration 10)
        convergence_iteration = None
        for iteration, variance in variance_trend:
            if iteration >= 10 and variance < 0.5:
                convergence_iteration = iteration
                break

        # Determine convergence status
        current_variance = self.get_rolling_variance()
        total_iterations = len(self.all_sharpes)

        if total_iterations < 10:
            status = "converging"  # Too early to determine
        elif convergence_iteration is not None:
            status = "converged"
        elif current_variance > 0.8:
            status = "unstable"
        else:
            status = "converging"

        # Generate recommendations
        recommendations = []

        if status == "unstable":
            recommendations.append(
                "High variance detected. Consider: (1) Tightening preservation constraints, "
                "(2) Reducing exploration frequency, or (3) Increasing anti-churn thresholds."
            )
        elif status == "converging" and total_iterations > 20:
            recommendations.append(
                "Learning still converging after 20+ iterations. Consider: (1) Adjusting champion update thresholds, "
                "(2) Reviewing failure pattern accumulation, or (3) Validating data consistency."
            )
        elif status == "converging" and total_iterations < 10:
            recommendations.append(
                "Early learning phase. Continue running iterations to establish convergence baseline."
            )
        elif status == "converged":
            recommendations.append(
                f"System converged at iteration {convergence_iteration}. Monitor for regression and consider "
                "reducing test frequency or transitioning to production validation."
            )

        return {
            "variance_trend": variance_trend,
            "convergence_status": status,
            "convergence_iteration": convergence_iteration,
            "current_variance": current_variance,
            "total_iterations": total_iterations,
            "recommendations": recommendations
        }
