"""Tests for Type Conversion Performance (Phase 3, Task 3.1).

Tests TC-1.9: Type conversion overhead <0.1ms

This module benchmarks StrategyMetrics to_dict() / from_dict() performance
to ensure conversion overhead meets the <0.1ms requirement.

Author: Phase 3 Implementation Team
Date: 2025-01-13
"""

import pytest
import time
import statistics
from src.backtest.metrics import StrategyMetrics


class TestTypeConversionPerformance:
    """Benchmark StrategyMetrics conversion performance (TC-1.9)."""

    def test_to_dict_performance_under_01ms(self):
        """TC-1.9: to_dict() conversion completes in <0.1ms.

        WHEN: Convert StrategyMetrics to dict 1000 times
        THEN: Average conversion time <0.1ms (100 microseconds)
        """
        # Arrange
        metrics = StrategyMetrics(
            sharpe_ratio=1.85,
            total_return=0.42,
            max_drawdown=-0.15,
            win_rate=0.65,
            execution_success=True
        )

        iterations = 1000
        times = []

        # Act - Benchmark
        for _ in range(iterations):
            start = time.perf_counter()
            result = metrics.to_dict()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to milliseconds

        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        p95_time = sorted(times)[int(0.95 * len(times))]

        # Assert
        assert avg_time < 0.1, f"Average time {avg_time:.4f}ms exceeds 0.1ms threshold"
        assert median_time < 0.1, f"Median time {median_time:.4f}ms exceeds 0.1ms threshold"
        assert p95_time < 0.2, f"P95 time {p95_time:.4f}ms exceeds 0.2ms threshold"

        # Log performance metrics
        print(f"\nto_dict() Performance:")
        print(f"  Average: {avg_time:.4f}ms")
        print(f"  Median:  {median_time:.4f}ms")
        print(f"  P95:     {p95_time:.4f}ms")

    def test_from_dict_performance_under_01ms(self):
        """TC-1.9: from_dict() conversion completes in <0.1ms.

        WHEN: Convert dict to StrategyMetrics 1000 times
        THEN: Average conversion time <0.1ms
        """
        # Arrange
        data = {
            'sharpe_ratio': 2.05,
            'total_return': 0.48,
            'max_drawdown': -0.13,
            'win_rate': 0.70,
            'execution_success': True
        }

        iterations = 1000
        times = []

        # Act - Benchmark
        for _ in range(iterations):
            start = time.perf_counter()
            metrics = StrategyMetrics.from_dict(data)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        p95_time = sorted(times)[int(0.95 * len(times))]

        # Assert
        assert avg_time < 0.1, f"Average time {avg_time:.4f}ms exceeds 0.1ms threshold"
        assert median_time < 0.1, f"Median time {median_time:.4f}ms exceeds 0.1ms threshold"
        assert p95_time < 0.2, f"P95 time {p95_time:.4f}ms exceeds 0.2ms threshold"

        # Log performance metrics
        print(f"\nfrom_dict() Performance:")
        print(f"  Average: {avg_time:.4f}ms")
        print(f"  Median:  {median_time:.4f}ms")
        print(f"  P95:     {p95_time:.4f}ms")

    def test_roundtrip_conversion_performance_under_02ms(self):
        """TC-1.9: Roundtrip (to_dict + from_dict) completes in <0.2ms.

        WHEN: Full roundtrip conversion 1000 times
        THEN: Average roundtrip time <0.2ms
        """
        # Arrange
        original = StrategyMetrics(
            sharpe_ratio=1.95,
            total_return=0.38,
            max_drawdown=-0.14,
            win_rate=0.62,
            execution_success=True
        )

        iterations = 1000
        times = []

        # Act - Benchmark roundtrip
        for _ in range(iterations):
            start = time.perf_counter()
            dict_form = original.to_dict()
            restored = StrategyMetrics.from_dict(dict_form)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        p95_time = sorted(times)[int(0.95 * len(times))]

        # Assert
        assert avg_time < 0.2, f"Average roundtrip {avg_time:.4f}ms exceeds 0.2ms threshold"
        assert median_time < 0.2, f"Median roundtrip {median_time:.4f}ms exceeds 0.2ms threshold"
        assert p95_time < 0.4, f"P95 roundtrip {p95_time:.4f}ms exceeds 0.4ms threshold"

        # Log performance metrics
        print(f"\nRoundtrip Performance:")
        print(f"  Average: {avg_time:.4f}ms")
        print(f"  Median:  {median_time:.4f}ms")
        print(f"  P95:     {p95_time:.4f}ms")

    def test_conversion_no_performance_regression(self):
        """TC-1.9: Verify no performance regression in type conversion.

        WHEN: Run comprehensive benchmark suite
        THEN: All operations meet performance targets consistently
        """
        # Arrange
        test_cases = [
            # (sharpe, return, drawdown, win_rate)
            (1.0, 0.2, -0.1, 0.5),
            (2.5, 0.5, -0.2, 0.7),
            (0.5, 0.1, -0.05, 0.4),
        ]

        iterations = 100

        # Act & Assert - Test multiple scenarios
        for sharpe, ret, dd, wr in test_cases:
            metrics = StrategyMetrics(
                sharpe_ratio=sharpe,
                total_return=ret,
                max_drawdown=dd,
                win_rate=wr,
                execution_success=True
            )

            # Benchmark to_dict
            start = time.perf_counter()
            for _ in range(iterations):
                _ = metrics.to_dict()
            to_dict_time = (time.perf_counter() - start) / iterations * 1000

            # Benchmark from_dict
            data = metrics.to_dict()
            start = time.perf_counter()
            for _ in range(iterations):
                _ = StrategyMetrics.from_dict(data)
            from_dict_time = (time.perf_counter() - start) / iterations * 1000

            # Assert
            assert to_dict_time < 0.1, f"to_dict {to_dict_time:.4f}ms exceeds threshold"
            assert from_dict_time < 0.1, f"from_dict {from_dict_time:.4f}ms exceeds threshold"


class TestConversionMemoryEfficiency:
    """Test memory efficiency of type conversions."""

    def test_conversion_does_not_leak_references(self):
        """Verify conversion methods don't create circular references.

        WHEN: Convert StrategyMetrics to dict
        THEN: No circular references or memory leaks
        """
        # Arrange
        metrics = StrategyMetrics(
            sharpe_ratio=1.5,
            total_return=0.3,
            execution_success=True
        )

        # Act
        dict1 = metrics.to_dict()
        dict1['sharpe_ratio'] = 999.0

        dict2 = metrics.to_dict()

        # Assert - Verify independence
        assert dict2['sharpe_ratio'] == 1.5
        assert metrics.sharpe_ratio == 1.5
