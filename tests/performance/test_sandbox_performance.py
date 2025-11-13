"""Performance benchmark suite for Docker Sandbox overhead measurement.

Compares execution time between:
- AST-only execution (sandbox.enabled: false)
- Docker Sandbox execution (sandbox.enabled: true)

Task 3.1: docker-sandbox-integration-testing
Requirement 5: Performance Benchmarking
"""

import pytest
import sys
import os
import time
import json
import statistics
from pathlib import Path
from typing import List, Dict, Tuple
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'artifacts' / 'working' / 'modules'))


class TestSandboxPerformance:
    """Performance benchmark tests for Docker Sandbox."""

    @pytest.fixture
    def performance_data(self):
        """Create realistic performance test data."""
        # Create larger dataset for realistic performance testing
        dates = pd.date_range('2020-01-01', periods=252, freq='D')  # 1 year of trading days

        class PerformanceData:
            def __init__(self):
                # Realistic price data
                self.close = pd.Series(
                    np.random.randn(252).cumsum() + 100,
                    index=dates
                )
                self.open = self.close + np.random.randn(252) * 0.5
                self.high = self.close + abs(np.random.randn(252)) * 1.0
                self.low = self.close - abs(np.random.randn(252)) * 1.0
                self.volume = pd.Series(
                    np.random.randint(1000000, 10000000, 252),
                    index=dates
                )

        return PerformanceData()

    @pytest.fixture
    def benchmark_strategy(self):
        """Strategy template for benchmarking."""
        return """
# Benchmark strategy - simple momentum with volume filter
def strategy(data):
    '''Momentum strategy with volume confirmation'''
    price_momentum = data.close > data.close.shift(20)
    volume_confirm = data.volume > data.volume.shift(20).rolling(5).mean()
    return price_momentum & volume_confirm

# Execute backtest
position = strategy(data)
report = sim(position, resample='M')
"""

    def run_iterations(
        self,
        wrapper,
        strategy_code: str,
        data,
        num_iterations: int = 20
    ) -> List[Dict]:
        """Run multiple iterations and collect timing data.

        Args:
            wrapper: SandboxExecutionWrapper instance
            strategy_code: Strategy code to execute
            data: Performance test data
            num_iterations: Number of iterations to run

        Returns:
            List of timing dictionaries with success status
        """
        results = []

        for i in range(num_iterations):
            start_time = time.time()

            try:
                success, metrics, error = wrapper.execute_strategy(
                    code=strategy_code,
                    data=data,
                    timeout=120
                )

                elapsed = time.time() - start_time

                results.append({
                    'iteration': i + 1,
                    'success': success,
                    'elapsed_time': elapsed,
                    'metrics': metrics,
                    'error': error
                })

            except Exception as e:
                elapsed = time.time() - start_time
                results.append({
                    'iteration': i + 1,
                    'success': False,
                    'elapsed_time': elapsed,
                    'metrics': None,
                    'error': str(e)
                })

        return results

    def calculate_statistics(self, results: List[Dict]) -> Dict:
        """Calculate performance statistics from results.

        Args:
            results: List of timing dictionaries

        Returns:
            Statistics dictionary
        """
        elapsed_times = [r['elapsed_time'] for r in results if r['success']]
        success_count = sum(1 for r in results if r['success'])

        if not elapsed_times:
            return {
                'mean': None,
                'std': None,
                'min': None,
                'max': None,
                'success_rate': 0.0,
                'total_iterations': len(results)
            }

        return {
            'mean': statistics.mean(elapsed_times),
            'std': statistics.stdev(elapsed_times) if len(elapsed_times) > 1 else 0.0,
            'min': min(elapsed_times),
            'max': max(elapsed_times),
            'median': statistics.median(elapsed_times),
            'success_rate': success_count / len(results),
            'total_iterations': len(results),
            'successful_iterations': success_count
        }

    @pytest.mark.performance
    @pytest.mark.slow
    def test_baseline_ast_only_performance(
        self,
        performance_data,
        benchmark_strategy,
        tmp_path
    ):
        """Benchmark: 20 iterations with AST-only execution (baseline).

        Requirement 5.1: Measure baseline performance without Docker Sandbox.
        This establishes the performance baseline for comparison.
        """
        # Import SandboxExecutionWrapper
        from autonomous_loop import SandboxExecutionWrapper

        # Create mock event logger
        mock_event_logger = Mock()
        mock_event_logger.log_event = Mock()

        # Create wrapper with sandbox DISABLED (baseline)
        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=False,
            docker_executor=None,
            event_logger=mock_event_logger
        )

        print("\n" + "="*60)
        print("BASELINE: AST-Only Execution (20 iterations)")
        print("="*60)

        # Run 20 iterations
        results = self.run_iterations(
            wrapper=wrapper,
            strategy_code=benchmark_strategy,
            data=performance_data,
            num_iterations=20
        )

        # Calculate statistics
        stats = self.calculate_statistics(results)

        # Verify success rate
        assert stats['success_rate'] == 1.0, \
            f"Baseline should have 100% success rate, got {stats['success_rate']:.1%}"

        # Print results
        print(f"\n📊 Baseline Results:")
        print(f"   Mean time: {stats['mean']:.3f}s")
        print(f"   Std dev:   {stats['std']:.3f}s")
        print(f"   Min time:  {stats['min']:.3f}s")
        print(f"   Max time:  {stats['max']:.3f}s")
        print(f"   Median:    {stats['median']:.3f}s")
        print(f"   Success:   {stats['successful_iterations']}/{stats['total_iterations']}")
        print(f"   Rate:      {stats['success_rate']:.1%}")

        # Save results to file for later analysis
        results_file = tmp_path / "baseline_ast_only_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'mode': 'ast_only',
                'statistics': stats,
                'raw_results': results
            }, f, indent=2)

        print(f"\n✅ Baseline results saved to: {results_file}")

        # Store in pytest cache for comparison in next test
        pytest.baseline_stats = stats
        pytest.baseline_results_file = str(results_file)

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.docker
    def test_sandbox_enabled_performance(
        self,
        performance_data,
        benchmark_strategy,
        tmp_path
    ):
        """Benchmark: 20 iterations with Docker Sandbox enabled.

        Requirement 5.2: Measure performance with Docker Sandbox enabled.
        Compares against baseline to calculate overhead percentage.
        """
        # Import required modules
        from autonomous_loop import SandboxExecutionWrapper

        # Skip if Docker not available
        try:
            from src.sandbox.docker_executor import DockerExecutor
            from src.sandbox.docker_config import DockerConfig
        except ImportError:
            pytest.skip("Docker Sandbox not available")

        # Create mock event logger
        mock_event_logger = Mock()
        mock_event_logger.log_event = Mock()

        # Create Docker configuration
        try:
            docker_config = DockerConfig.from_yaml()
        except Exception as e:
            pytest.skip(f"Could not load Docker config: {e}")

        # Create Docker executor
        try:
            docker_executor = DockerExecutor(config=docker_config)
        except Exception as e:
            pytest.skip(f"Could not create Docker executor: {e}")

        # Create wrapper with sandbox ENABLED
        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=docker_executor,
            event_logger=mock_event_logger
        )

        print("\n" + "="*60)
        print("SANDBOX: Docker Execution (20 iterations)")
        print("="*60)

        # Run 20 iterations
        results = self.run_iterations(
            wrapper=wrapper,
            strategy_code=benchmark_strategy,
            data=performance_data,
            num_iterations=20
        )

        # Calculate statistics
        stats = self.calculate_statistics(results)

        # Print results
        print(f"\n📊 Sandbox Results:")
        print(f"   Mean time: {stats['mean']:.3f}s")
        print(f"   Std dev:   {stats['std']:.3f}s")
        print(f"   Min time:  {stats['min']:.3f}s")
        print(f"   Max time:  {stats['max']:.3f}s")
        print(f"   Median:    {stats['median']:.3f}s")
        print(f"   Success:   {stats['successful_iterations']}/{stats['total_iterations']}")
        print(f"   Rate:      {stats['success_rate']:.1%}")

        # Calculate fallback stats
        fallback_stats = wrapper.get_fallback_stats()
        print(f"\n   Fallbacks: {fallback_stats['fallback_count']}/{fallback_stats['execution_count']}")
        print(f"   Fallback rate: {fallback_stats['fallback_rate']:.1%}")

        # Save results
        results_file = tmp_path / "sandbox_enabled_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'mode': 'docker_sandbox',
                'statistics': stats,
                'fallback_stats': fallback_stats,
                'raw_results': results
            }, f, indent=2)

        print(f"\n✅ Sandbox results saved to: {results_file}")

        # Compare with baseline if available
        if hasattr(pytest, 'baseline_stats'):
            baseline = pytest.baseline_stats

            # Calculate overhead
            if baseline['mean'] and stats['mean']:
                overhead_pct = ((stats['mean'] - baseline['mean']) / baseline['mean']) * 100
                overhead_seconds = stats['mean'] - baseline['mean']

                print(f"\n" + "="*60)
                print(f"📈 PERFORMANCE COMPARISON")
                print(f"="*60)
                print(f"   Baseline (AST-only):  {baseline['mean']:.3f}s")
                print(f"   Sandbox (Docker):     {stats['mean']:.3f}s")
                print(f"   Overhead:             +{overhead_seconds:.3f}s ({overhead_pct:+.1f}%)")
                print(f"   Success rate parity:  {baseline['success_rate']:.1%} vs {stats['success_rate']:.1%}")

                # Save comparison
                comparison_file = tmp_path / "performance_comparison.json"
                with open(comparison_file, 'w') as f:
                    json.dump({
                        'baseline': baseline,
                        'sandbox': stats,
                        'overhead_seconds': overhead_seconds,
                        'overhead_percentage': overhead_pct,
                        'fallback_stats': fallback_stats
                    }, f, indent=2)

                print(f"\n✅ Comparison saved to: {comparison_file}")

                # Assert reasonable overhead (< 300%)
                assert overhead_pct < 300, \
                    f"Sandbox overhead too high: {overhead_pct:.1f}% (expected < 300%)"

        # Verify acceptable success rate (>= 95%)
        assert stats['success_rate'] >= 0.95, \
            f"Sandbox success rate too low: {stats['success_rate']:.1%} (expected >= 95%)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
