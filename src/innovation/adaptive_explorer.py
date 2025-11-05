"""
Adaptive Exploration - Task 3.4

Dynamically adjusts innovation rate based on performance and
diversity metrics to optimize exploration vs exploitation.

Responsibilities:
- Monitor performance trends
- Detect stagnation and breakthroughs
- Adjust innovation rate adaptively (20% → 50% when needed)
- Track rate changes and their impact
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import deque
import numpy as np


class AdaptiveExplorer:
    """
    Adaptive innovation rate controller.

    Adjusts innovation frequency based on:
    - Performance improvements (breakthroughs)
    - Performance stagnation
    - Population diversity
    - Recent innovation success rate
    """

    def __init__(
        self,
        default_rate: float = 0.20,
        min_rate: float = 0.10,
        max_rate: float = 0.50,
        window_size: int = 10
    ):
        """
        Initialize adaptive explorer.

        Args:
            default_rate: Default innovation rate (20%)
            min_rate: Minimum innovation rate (10%)
            max_rate: Maximum innovation rate (50%)
            window_size: Window size for moving statistics
        """
        self.default_rate = default_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.window_size = window_size

        # Current state
        self.current_rate = default_rate
        self.performance_history: deque = deque(maxlen=window_size)
        self.diversity_history: deque = deque(maxlen=window_size)
        self.rate_history: List[Tuple[int, float, str]] = []  # (iteration, rate, reason)

    def update_metrics(
        self,
        iteration: int,
        performance: float,
        diversity: float
    ):
        """
        Update performance and diversity history.

        Args:
            iteration: Current iteration number
            performance: Current best performance (e.g., Sharpe ratio)
            diversity: Current population diversity (0-1)
        """
        self.performance_history.append(performance)
        self.diversity_history.append(diversity)

    def adjust_rate(
        self,
        iteration: int,
        current_performance: float,
        current_diversity: float,
        innovation_success_rate: float
    ) -> Tuple[float, str]:
        """
        Adjust innovation rate based on current metrics.

        Args:
            iteration: Current iteration number
            current_performance: Current best performance
            current_diversity: Current population diversity
            innovation_success_rate: Recent innovation success rate

        Returns:
            (new_rate, reason) tuple
        """
        # Update history
        self.update_metrics(iteration, current_performance, current_diversity)

        # Not enough history yet
        if len(self.performance_history) < 3:
            return self.current_rate, "Insufficient history"

        # Detect conditions
        is_breakthrough = self._detect_breakthrough()
        is_stagnant = self._detect_stagnation()
        is_low_diversity = current_diversity < 0.30

        # Decision logic
        new_rate = self.current_rate
        reason = "No change"

        # Priority 1: Breakthrough → Increase exploration
        if is_breakthrough:
            new_rate = min(self.current_rate * 1.5, self.max_rate)
            reason = "Breakthrough detected - increase exploration"

        # Priority 2: Stagnation → Increase exploration
        elif is_stagnant:
            new_rate = min(self.current_rate * 1.25, self.max_rate)
            reason = "Stagnation detected - increase exploration"

        # Priority 3: Low diversity → Increase exploration
        elif is_low_diversity:
            new_rate = min(self.current_rate * 1.2, self.max_rate)
            reason = "Low diversity - increase exploration"

        # Priority 4: High success + high diversity → Reduce exploration
        elif innovation_success_rate > 0.50 and current_diversity > 0.50:
            new_rate = max(self.current_rate * 0.9, self.min_rate)
            reason = "High success + diversity - reduce exploration"

        # Priority 5: Low success → Reduce exploration
        elif innovation_success_rate < 0.20 and iteration > 20:
            new_rate = max(self.current_rate * 0.8, self.min_rate)
            reason = "Low success rate - reduce exploration"

        # Update current rate and log change
        if abs(new_rate - self.current_rate) > 0.01:
            self.current_rate = new_rate
            self.rate_history.append((iteration, new_rate, reason))

        return new_rate, reason

    def _detect_breakthrough(self) -> bool:
        """
        Detect breakthrough: significant performance improvement.

        Returns:
            True if breakthrough detected
        """
        if len(self.performance_history) < self.window_size:
            return False

        recent_perfs = list(self.performance_history)
        recent_avg = np.mean(recent_perfs[-3:])
        previous_avg = np.mean(recent_perfs[:-3])

        # Breakthrough: >10% improvement
        improvement = (recent_avg - previous_avg) / (previous_avg + 1e-6)
        return improvement > 0.10

    def _detect_stagnation(self) -> bool:
        """
        Detect stagnation: no improvement for extended period.

        Returns:
            True if stagnation detected
        """
        if len(self.performance_history) < self.window_size:
            return False

        recent_perfs = list(self.performance_history)

        # Check if performance is flat (std < 5% of mean)
        mean_perf = np.mean(recent_perfs)
        std_perf = np.std(recent_perfs)

        if mean_perf == 0:
            return False

        relative_std = std_perf / mean_perf
        return relative_std < 0.05  # Less than 5% variation

    def get_rate_report(self) -> Dict[str, Any]:
        """
        Get adaptive exploration report.

        Returns:
            Report dictionary
        """
        return {
            'current_rate': self.current_rate,
            'default_rate': self.default_rate,
            'rate_changes': len(self.rate_history),
            'recent_changes': self.rate_history[-5:] if self.rate_history else [],
            'performance_window': list(self.performance_history),
            'diversity_window': list(self.diversity_history)
        }

    def reset(self):
        """Reset to default settings."""
        self.current_rate = self.default_rate
        self.performance_history.clear()
        self.diversity_history.clear()
        self.rate_history.clear()


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("TESTING ADAPTIVE EXPLORER")
    print("=" * 70)

    explorer = AdaptiveExplorer(default_rate=0.20)

    # Simulate evolution with different scenarios
    print("\nScenario 1: Breakthrough Detection")
    print("-" * 70)

    for i in range(15):
        # Simulate breakthrough at iteration 10
        if i < 10:
            perf = 0.68 + np.random.normal(0, 0.02)
        else:
            perf = 0.82 + np.random.normal(0, 0.02)  # Breakthrough!

        div = 0.45
        success_rate = 0.35

        new_rate, reason = explorer.adjust_rate(i, perf, div, success_rate)

        if "Breakthrough" in reason:
            print(f"✅ Iteration {i}: {reason}")
            print(f"   Rate: {explorer.current_rate:.0%} (was {0.20:.0%})")

    # Scenario 2: Stagnation detection
    print("\nScenario 2: Stagnation Detection")
    print("-" * 70)

    explorer.reset()

    for i in range(15):
        # Simulate stagnation
        perf = 0.68 + np.random.normal(0, 0.01)  # Very little variation
        div = 0.45
        success_rate = 0.35

        new_rate, reason = explorer.adjust_rate(i, perf, div, success_rate)

        if "Stagnation" in reason:
            print(f"✅ Iteration {i}: {reason}")
            print(f"   Rate: {explorer.current_rate:.0%}")

    # Scenario 3: Low diversity
    print("\nScenario 3: Low Diversity")
    print("-" * 70)

    explorer.reset()

    perf = 0.75
    div = 0.25  # Low diversity
    success_rate = 0.35

    for i in range(5):
        new_rate, reason = explorer.adjust_rate(i, perf, div, success_rate)

        if "diversity" in reason.lower():
            print(f"✅ Iteration {i}: {reason}")
            print(f"   Rate: {explorer.current_rate:.0%}")

    # Get report
    print("\nAdaptive Explorer Report")
    print("-" * 70)

    report = explorer.get_rate_report()
    print(f"✅ Current rate: {report['current_rate']:.0%}")
    print(f"✅ Rate changes: {report['rate_changes']}")
    if report['recent_changes']:
        print(f"✅ Recent changes:")
        for iter, rate, reason in report['recent_changes'][-3:]:
            print(f"   Iteration {iter}: {rate:.0%} ({reason})")

    print("\n" + "=" * 70)
    print("ADAPTIVE EXPLORER TEST COMPLETE")
    print("=" * 70)
