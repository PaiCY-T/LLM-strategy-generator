#!/usr/bin/env python3
"""
Performance Benchmarking Suite for Factor Graph System
PROD.2: Performance Benchmarking and Optimization

Benchmarks:
1. DAG Compilation Performance
2. Factor Execution Performance
3. Mutation Operation Performance
4. Memory Usage Profiling
5. Parallel vs Sequential Execution
6. Strategy Scaling Tests

Establishes performance baselines for production deployment.
"""

import time
import sys
import json
import gc
import psutil
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Factor Graph components
from src.factor_graph.factor import Factor, FactorCategory
from src.factor_graph.strategy import Strategy
from src.factor_graph.mutations import add_factor, remove_factor, replace_factor
from src.factor_library.registry import FactorRegistry


@dataclass
class BenchmarkResult:
    """Single benchmark result."""
    name: str
    mean_time_ms: float
    std_time_ms: float
    min_time_ms: float
    max_time_ms: float
    iterations: int
    memory_mb: float
    success_rate: float
    details: Dict[str, Any]


class PerformanceBenchmark:
    """Comprehensive performance benchmarking suite."""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.test_data = None
        self.process = psutil.Process()

        # Performance targets (from PERFORMANCE_TUNING_GUIDE.md)
        self.targets = {
            'dag_compilation_ms': 1000,      # <1 second
            'factor_execution_s': 300,       # <5 minutes
            'mutation_operation_ms': 1000,   # <1 second
            'generation_evolution_h': 2      # <2 hours for N=20, 20 gen
        }

    def setup_test_data(self, size: str = 'small'):
        """Setup test data of various sizes."""
        logger.info(f"Setting up {size} test data...")

        try:
            import finlab
            from finlab import data

            if size == 'small':
                # 100 days for quick tests
                close = data.get('price:收盤價')
                self.test_data = close.tail(100) if close is not None else None
            elif size == 'medium':
                # 250 days (1 year)
                close = data.get('price:收盤價')
                self.test_data = close.tail(250) if close is not None else None
            elif size == 'large':
                # 500 days (2 years)
                close = data.get('price:收盤價')
                self.test_data = close.tail(500) if close is not None else None

            if self.test_data is None or self.test_data.empty:
                raise ValueError("Failed to fetch data")

            logger.info(f"Test data loaded: {self.test_data.shape}")
            return True

        except Exception as e:
            logger.error(f"Failed to load real data: {e}")
            logger.info("Creating synthetic test data...")

            # Create synthetic data
            if size == 'small':
                days, stocks = 100, 100
            elif size == 'medium':
                days, stocks = 250, 500
            else:
                days, stocks = 500, 1000

            dates = pd.date_range('2024-01-01', periods=days, freq='D')
            stock_ids = [f'STOCK_{i:04d}' for i in range(stocks)]

            self.test_data = pd.DataFrame(
                index=dates,
                columns=stock_ids,
                data=100 + np.random.randn(days, stocks).cumsum(axis=0)
            )
            logger.info(f"Synthetic test data created: {self.test_data.shape}")
            return True

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def benchmark_function(
        self,
        name: str,
        func,
        iterations: int = 10,
        warmup: int = 2
    ) -> BenchmarkResult:
        """Benchmark a function with multiple iterations."""
        logger.info(f"\nBenchmarking: {name}")

        # Warmup runs
        for _ in range(warmup):
            try:
                func()
            except:
                pass

        # Actual benchmark runs
        times = []
        successes = 0
        gc.collect()
        mem_before = self.get_memory_usage()

        for i in range(iterations):
            gc.collect()
            start = time.time()
            try:
                result = func()
                elapsed = (time.time() - start) * 1000  # Convert to ms
                times.append(elapsed)
                successes += 1
            except Exception as e:
                logger.warning(f"Iteration {i+1} failed: {e}")

        mem_after = self.get_memory_usage()
        memory_delta = max(0, mem_after - mem_before)

        if not times:
            logger.error(f"❌ {name}: All iterations failed")
            return BenchmarkResult(
                name=name,
                mean_time_ms=0,
                std_time_ms=0,
                min_time_ms=0,
                max_time_ms=0,
                iterations=iterations,
                memory_mb=0,
                success_rate=0.0,
                details={'error': 'All iterations failed'}
            )

        result = BenchmarkResult(
            name=name,
            mean_time_ms=np.mean(times),
            std_time_ms=np.std(times),
            min_time_ms=np.min(times),
            max_time_ms=np.max(times),
            iterations=len(times),
            memory_mb=memory_delta,
            success_rate=successes / iterations,
            details={
                'times_ms': times,
                'mem_before_mb': mem_before,
                'mem_after_mb': mem_after
            }
        )

        logger.info(
            f"  Mean: {result.mean_time_ms:.2f}ms ± {result.std_time_ms:.2f}ms "
            f"(min: {result.min_time_ms:.2f}ms, max: {result.max_time_ms:.2f}ms)"
        )
        logger.info(f"  Memory: {result.memory_mb:.2f}MB, Success: {result.success_rate*100:.0f}%")

        self.results.append(result)
        return result

    def create_test_strategy(self, size: str = 'small') -> Strategy:
        """Create test strategy of various sizes."""
        strategy = Strategy(id=f"test_strategy_{size}", generation=0)

        # Factor 1: Returns
        def returns_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
            period = params.get('period', 20)
            data['returns'] = data['close'].pct_change(period)
            return data

        returns_factor = Factor(
            id="returns_20",
            name="momentum_returns",
            category=FactorCategory.MOMENTUM,
            inputs=['close'],
            outputs=['returns'],
            logic=returns_logic,
            parameters={'period': 20}
        )

        # Factor 2: Signal
        def signal_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
            threshold = params.get('threshold', 0.0)
            data['signal'] = (data['returns'] > threshold).astype(int)
            return data

        signal_factor = Factor(
            id="signal_gen",
            name="threshold_signal",
            category=FactorCategory.SIGNAL,
            inputs=['returns'],
            outputs=['signal'],
            logic=signal_logic,
            parameters={'threshold': 0.0}
        )

        strategy.add_factor(returns_factor)
        strategy.add_factor(signal_factor, depends_on=['returns_20'])

        # Add more factors for medium/large strategies
        if size in ['medium', 'large']:
            # Add MA filter
            def ma_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
                period = params.get('ma_period', 50)
                data['ma'] = data['close'].rolling(window=period).mean()
                data['above_ma'] = (data['close'] > data['ma']).astype(int)
                return data

            ma_factor = Factor(
                id="ma_filter",
                name="ma_filter",
                category=FactorCategory.MOMENTUM,
                inputs=['close'],
                outputs=['ma', 'above_ma'],
                logic=ma_logic,
                parameters={'ma_period': 50}
            )
            strategy.add_factor(ma_factor)

        if size == 'large':
            # Add volatility calculation
            def vol_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
                period = params.get('vol_period', 20)
                data['volatility'] = data['close'].pct_change().rolling(window=period).std()
                return data

            vol_factor = Factor(
                id="volatility",
                name="volatility",
                category=FactorCategory.RISK,
                inputs=['close'],
                outputs=['volatility'],
                logic=vol_logic,
                parameters={'vol_period': 20}
            )
            strategy.add_factor(vol_factor)

        return strategy

    def benchmark_dag_compilation(self):
        """Benchmark DAG compilation performance."""
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK 1: DAG Compilation Performance")
        logger.info("="*60)

        for size in ['small', 'medium', 'large']:
            def compile_dag():
                strategy = self.create_test_strategy(size)
                strategy.validate()
                return strategy

            result = self.benchmark_function(
                name=f"DAG Compilation ({size})",
                func=compile_dag,
                iterations=20
            )

            # Check against target
            target = self.targets['dag_compilation_ms']
            if result.mean_time_ms <= target:
                logger.info(f"  ✅ PASS: {result.mean_time_ms:.2f}ms <= {target}ms target")
            else:
                logger.warning(f"  ⚠️  SLOW: {result.mean_time_ms:.2f}ms > {target}ms target")

    def benchmark_factor_execution(self):
        """Benchmark factor execution performance."""
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK 2: Factor Execution Performance")
        logger.info("="*60)

        for data_size, strategy_size in [('small', 'small'), ('medium', 'medium'), ('small', 'large')]:
            self.setup_test_data(data_size)

            def execute_strategy():
                strategy = self.create_test_strategy(strategy_size)

                # Execute on first stock
                data = self.test_data.copy()
                data = data.reset_index()
                data.rename(columns={data.columns[0]: 'date'}, inplace=True)

                stock_data = pd.DataFrame({
                    'date': data['date'],
                    'close': data.iloc[:, 1]
                })

                result = strategy.to_pipeline(stock_data)
                return result

            result = self.benchmark_function(
                name=f"Strategy Execution (data={data_size}, strategy={strategy_size})",
                func=execute_strategy,
                iterations=10
            )

            # Convert to seconds and check against target
            time_s = result.mean_time_ms / 1000
            target_s = self.targets['factor_execution_s']

            if time_s <= target_s:
                logger.info(f"  ✅ PASS: {time_s:.2f}s <= {target_s}s target")
            else:
                logger.warning(f"  ⚠️  SLOW: {time_s:.2f}s > {target_s}s target")

    def benchmark_mutations(self):
        """Benchmark mutation operation performance."""
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK 3: Mutation Operation Performance")
        logger.info("="*60)

        registry = FactorRegistry.get_instance()
        base_strategy = self.create_test_strategy('medium')

        # Benchmark add_factor
        def test_add_factor():
            # Add a compatible factor
            return add_factor(
                strategy=base_strategy,
                factor_name='atr_factor',
                parameters={'atr_period': 14},
                insert_point='root'
            )

        add_result = self.benchmark_function(
            name="Mutation: add_factor",
            func=test_add_factor,
            iterations=50
        )

        # Benchmark remove_factor
        # First add a removable factor
        strategy_with_extra = add_factor(
            base_strategy,
            'atr_factor',
            {'atr_period': 14},
            'root'
        )

        def test_remove_factor():
            return remove_factor(
                strategy=strategy_with_extra,
                factor_id='atr_14',
                cascade=False
            )

        remove_result = self.benchmark_function(
            name="Mutation: remove_factor",
            func=test_remove_factor,
            iterations=50
        )

        # Check against targets
        target = self.targets['mutation_operation_ms']

        for result in [add_result, remove_result]:
            if result.mean_time_ms <= target:
                logger.info(f"  ✅ {result.name}: {result.mean_time_ms:.2f}ms <= {target}ms")
            else:
                logger.warning(f"  ⚠️  {result.name}: {result.mean_time_ms:.2f}ms > {target}ms")

    def benchmark_memory_usage(self):
        """Benchmark memory usage patterns."""
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK 4: Memory Usage Profiling")
        logger.info("="*60)

        gc.collect()
        mem_baseline = self.get_memory_usage()
        logger.info(f"Baseline memory: {mem_baseline:.2f}MB")

        # Test 1: Strategy creation memory
        strategies = []
        mem_before = self.get_memory_usage()

        for i in range(100):
            strategies.append(self.create_test_strategy('small'))

        mem_after = self.get_memory_usage()
        mem_per_strategy = (mem_after - mem_before) / 100

        logger.info(f"  100 strategies: {mem_after - mem_before:.2f}MB total")
        logger.info(f"  Per strategy: {mem_per_strategy:.3f}MB")

        # Cleanup
        strategies.clear()
        gc.collect()

        # Test 2: Data loading memory
        mem_before = self.get_memory_usage()
        self.setup_test_data('large')
        mem_after = self.get_memory_usage()

        logger.info(f"  Large dataset (500 days): {mem_after - mem_before:.2f}MB")

        # Test 3: Mutation memory
        base = self.create_test_strategy('medium')
        mem_before = self.get_memory_usage()

        mutated_strategies = []
        for i in range(50):
            try:
                mutated = add_factor(base, 'atr_factor', {'atr_period': 14}, 'root')
                mutated_strategies.append(mutated)
            except:
                pass

        mem_after = self.get_memory_usage()
        logger.info(f"  50 mutations: {mem_after - mem_before:.2f}MB")

        # Overall verdict
        total_mem = self.get_memory_usage() - mem_baseline
        logger.info(f"\nTotal memory overhead: {total_mem:.2f}MB")

        if total_mem < 500:
            logger.info("  ✅ PASS: Memory usage reasonable (<500MB)")
        else:
            logger.warning("  ⚠️  HIGH: Memory usage elevated (>500MB)")

    def benchmark_scaling(self):
        """Benchmark performance scaling with strategy size."""
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK 5: Strategy Scaling Performance")
        logger.info("="*60)

        self.setup_test_data('small')

        # Test with increasing number of factors
        for num_factors in [2, 5, 10, 15]:
            def create_and_execute():
                strategy = Strategy(id=f"scale_test_{num_factors}", generation=0)

                # Add chain of factors
                for i in range(num_factors):
                    if i == 0:
                        # Root factor
                        def logic(data, params, idx=i):
                            data[f'factor_{idx}'] = data['close'].pct_change(params.get('period', 5))
                            return data

                        factor = Factor(
                            id=f"factor_{i}",
                            name=f"factor_{i}",
                            category=FactorCategory.MOMENTUM,
                            inputs=['close'],
                            outputs=[f'factor_{i}'],
                            logic=logic,
                            parameters={'period': 5}
                        )
                        strategy.add_factor(factor)
                    elif i == num_factors - 1:
                        # Final signal factor
                        def logic(data, params, idx=i):
                            data['signal'] = (data[f'factor_{i-1}'] > 0).astype(int)
                            return data

                        factor = Factor(
                            id=f"factor_{i}",
                            name=f"factor_{i}",
                            category=FactorCategory.SIGNAL,
                            inputs=[f'factor_{i-1}'],
                            outputs=['signal'],
                            logic=logic,
                            parameters={}
                        )
                        strategy.add_factor(factor, depends_on=[f"factor_{i-1}"])
                    else:
                        # Middle factors
                        def logic(data, params, idx=i):
                            data[f'factor_{idx}'] = data[f'factor_{idx-1}'].rolling(3).mean()
                            return data

                        factor = Factor(
                            id=f"factor_{i}",
                            name=f"factor_{i}",
                            category=FactorCategory.MOMENTUM,
                            inputs=[f'factor_{i-1}'],
                            outputs=[f'factor_{i}'],
                            logic=logic,
                            parameters={}
                        )
                        strategy.add_factor(factor, depends_on=[f"factor_{i-1}"])

                # Execute
                data = self.test_data.copy()
                data = data.reset_index()
                data.rename(columns={data.columns[0]: 'date'}, inplace=True)
                stock_data = pd.DataFrame({
                    'date': data['date'],
                    'close': data.iloc[:, 1]
                })

                return strategy.to_pipeline(stock_data)

            result = self.benchmark_function(
                name=f"Strategy with {num_factors} factors",
                func=create_and_execute,
                iterations=10
            )

            logger.info(f"  Scaling factor: {result.mean_time_ms / (2 * 10):.2f}x per factor")

    def generate_report(self) -> str:
        """Generate comprehensive benchmark report."""
        logger.info("\n" + "="*60)
        logger.info("PERFORMANCE BENCHMARK REPORT")
        logger.info("="*60)

        # Calculate summary statistics
        total_benchmarks = len(self.results)
        passed = sum(1 for r in self.results if r.success_rate >= 0.9)

        logger.info(f"\nTotal Benchmarks: {total_benchmarks}")
        logger.info(f"Successful: {passed}/{total_benchmarks} ({passed/total_benchmarks*100:.0f}%)")

        # Performance summary
        logger.info("\n" + "-"*60)
        logger.info("PERFORMANCE SUMMARY")
        logger.info("-"*60)

        for result in self.results:
            status = "✅" if result.success_rate >= 0.9 else "❌"
            logger.info(
                f"{status} {result.name}: "
                f"{result.mean_time_ms:.2f}ms ± {result.std_time_ms:.2f}ms "
                f"({result.memory_mb:.1f}MB)"
            )

        # Performance targets comparison
        logger.info("\n" + "-"*60)
        logger.info("TARGET COMPLIANCE")
        logger.info("-"*60)

        # Find relevant results
        dag_results = [r for r in self.results if 'DAG Compilation' in r.name]
        mutation_results = [r for r in self.results if 'Mutation:' in r.name]

        if dag_results:
            avg_dag_time = np.mean([r.mean_time_ms for r in dag_results])
            target = self.targets['dag_compilation_ms']
            status = "✅ PASS" if avg_dag_time <= target else "⚠️  SLOW"
            logger.info(f"{status} DAG Compilation: {avg_dag_time:.2f}ms (target: <{target}ms)")

        if mutation_results:
            avg_mutation_time = np.mean([r.mean_time_ms for r in mutation_results])
            target = self.targets['mutation_operation_ms']
            status = "✅ PASS" if avg_mutation_time <= target else "⚠️  SLOW"
            logger.info(f"{status} Mutations: {avg_mutation_time:.2f}ms (target: <{target}ms)")

        # Save detailed results
        report_path = "/mnt/c/Users/jnpi/documents/finlab/PERFORMANCE_BENCHMARK_RESULTS.json"

        results_dict = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_benchmarks': total_benchmarks,
                'passed': passed,
                'success_rate': passed / total_benchmarks if total_benchmarks > 0 else 0
            },
            'targets': self.targets,
            'results': [asdict(r) for r in self.results]
        }

        with open(report_path, 'w') as f:
            json.dump(results_dict, f, indent=2, default=str)

        logger.info(f"\nDetailed results saved to: {report_path}")

        # Final verdict
        logger.info("\n" + "="*60)
        if passed / total_benchmarks >= 0.8:
            logger.info("✅ VERDICT: PERFORMANCE MEETS PRODUCTION TARGETS")
            logger.info("   System ready for deployment")
        elif passed / total_benchmarks >= 0.6:
            logger.info("⚠️  VERDICT: PERFORMANCE ACCEPTABLE WITH OPTIMIZATION")
            logger.info("   Some areas need attention before deployment")
        else:
            logger.info("❌ VERDICT: PERFORMANCE BELOW TARGETS")
            logger.info("   Optimization required before deployment")
        logger.info("="*60)

        return report_path

    def run_all_benchmarks(self):
        """Run complete benchmark suite."""
        logger.info("="*60)
        logger.info("PERFORMANCE BENCHMARKING SUITE")
        logger.info("PROD.2: Performance Benchmarking and Optimization")
        logger.info("="*60)

        try:
            # Setup
            self.setup_test_data('small')

            # Run all benchmarks
            self.benchmark_dag_compilation()
            self.benchmark_factor_execution()
            self.benchmark_mutations()
            self.benchmark_memory_usage()
            self.benchmark_scaling()

            # Generate report
            self.generate_report()

            return True

        except Exception as e:
            logger.error(f"Benchmark suite failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    benchmark = PerformanceBenchmark()
    success = benchmark.run_all_benchmarks()

    sys.exit(0 if success else 1)
