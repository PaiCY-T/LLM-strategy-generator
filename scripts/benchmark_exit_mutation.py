#!/usr/bin/env python3
"""
Exit Mutation Performance Benchmark Script

Purpose:
    Comprehensive performance benchmarking for the exit mutation framework,
    measuring throughput, latency, memory usage, and validation overhead.

Benchmark Tests:
    1. Single mutation performance (1000 iterations)
    2. Batch mutation throughput (100 mutations)
    3. Memory usage under sustained load
    4. Validation pipeline performance
    5. Configuration loading overhead

Usage:
    python3 scripts/benchmark_exit_mutation.py [--iterations N] [--output FILE] [--verbose]

Requirements:
    - src.mutation.exit_mutation_operator
    - src.mutation.exit_mutator
    - config/learning_system.yaml

Part of: structural-mutation-phase2 spec (Task 1.8)
Author: Claude Code SuperClaude
Date: 2025-10-20
"""

import argparse
import json
import logging
import sys
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional
import statistics

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mutation.exit_mutation_operator import ExitMutationOperator
from src.mutation.exit_mutator import ExitStrategyMutator


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    test_name: str
    iterations: int
    total_time: float
    avg_time: float
    median_time: float
    min_time: float
    max_time: float
    std_dev: float
    throughput: float
    memory_peak_mb: float
    memory_delta_mb: float
    success_rate: float
    notes: str


class ExitMutationBenchmark:
    """Benchmarking suite for exit mutation framework."""

    def __init__(self, max_retries: int = 3, verbose: bool = False):
        """
        Initialize benchmark suite.

        Args:
            max_retries: Maximum retry attempts for mutations
            verbose: Enable verbose logging
        """
        self.max_retries = max_retries
        self.verbose = verbose
        self.logger = self._setup_logging()
        self.operator: Optional[ExitMutationOperator] = None
        self.mutator: Optional[ExitStrategyMutator] = None
        self.results: List[BenchmarkResult] = []

        # Sample strategy code for benchmarking
        self.sample_strategy = '''
import finlab
from finlab import data
from finlab.backtest import sim

def strategy(data):
    """Sample momentum strategy with exit mechanisms."""
    # Entry signal
    close = data.get('close')
    sma_20 = close.average(20)
    sma_50 = close.average(50)

    position = (sma_20 > sma_50)

    # Exit mechanisms (will be mutated)
    stop_loss_pct = -0.05  # 5% stop loss
    take_profit_pct = 0.10  # 10% take profit
    trailing_stop_pct = 0.03  # 3% trailing stop

    # Apply exits
    position = apply_stop_loss(position, close, stop_loss_pct)
    position = apply_take_profit(position, close, take_profit_pct)
    position = apply_trailing_stop(position, close, trailing_stop_pct)

    return position

def apply_stop_loss(position, close, stop_pct):
    """Apply stop loss exit."""
    return position

def apply_take_profit(position, close, profit_pct):
    """Apply take profit exit."""
    return position

def apply_trailing_stop(position, close, trail_pct):
    """Apply trailing stop exit."""
    return position
'''

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return logging.getLogger(__name__)

    def setup(self):
        """Initialize mutation operators."""
        self.logger.info("Initializing exit mutation operators...")
        self.operator = ExitMutationOperator(max_retries=self.max_retries)
        self.mutator = ExitStrategyMutator()
        self.logger.info("Setup complete")

    def benchmark_single_mutation(self, iterations: int = 1000) -> BenchmarkResult:
        """
        Benchmark single mutation performance.

        Args:
            iterations: Number of mutations to perform

        Returns:
            BenchmarkResult with performance metrics
        """
        self.logger.info(f"Running single mutation benchmark ({iterations} iterations)...")

        times = []
        successes = 0

        # Start memory tracking
        tracemalloc.start()
        mem_start = tracemalloc.get_traced_memory()[0] / 1024 / 1024  # MB

        start_time = time.time()

        for i in range(iterations):
            iter_start = time.time()

            try:
                result = self.operator.mutate_exit_strategy(
                    code=self.sample_strategy
                )
                if result.success:
                    successes += 1

            except Exception as e:
                self.logger.debug(f"Iteration {i} failed: {e}")

            iter_time = time.time() - iter_start
            times.append(iter_time)

            if self.verbose and (i + 1) % 100 == 0:
                self.logger.debug(f"  Completed {i + 1}/{iterations} iterations...")

        total_time = time.time() - start_time

        # Memory stats
        mem_current, mem_peak = tracemalloc.get_traced_memory()
        mem_current_mb = mem_current / 1024 / 1024
        mem_peak_mb = mem_peak / 1024 / 1024
        mem_delta_mb = mem_current_mb - mem_start
        tracemalloc.stop()

        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        throughput = iterations / total_time
        success_rate = successes / iterations

        result = BenchmarkResult(
            test_name="Single Mutation Performance",
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            median_time=median_time,
            min_time=min_time,
            max_time=max_time,
            std_dev=std_dev,
            throughput=throughput,
            memory_peak_mb=mem_peak_mb,
            memory_delta_mb=mem_delta_mb,
            success_rate=success_rate,
            notes=f"Target: <1s per mutation. Actual: {avg_time*1000:.2f}ms (avg)"
        )

        self.results.append(result)
        self.logger.info(f"  Avg time: {avg_time*1000:.2f}ms, Throughput: {throughput:.1f} mut/s")
        return result

    def benchmark_batch_mutation(self, batch_size: int = 100) -> BenchmarkResult:
        """
        Benchmark batch mutation throughput.

        Args:
            batch_size: Number of mutations in batch

        Returns:
            BenchmarkResult with throughput metrics
        """
        self.logger.info(f"Running batch mutation benchmark ({batch_size} mutations)...")

        successes = 0
        times = []

        # Start memory tracking
        tracemalloc.start()
        mem_start = tracemalloc.get_traced_memory()[0] / 1024 / 1024

        start_time = time.time()

        for i in range(batch_size):
            iter_start = time.time()

            try:
                result = self.operator.mutate_exit_strategy(
                    code=self.sample_strategy
                )
                if result.success:
                    successes += 1

            except Exception as e:
                self.logger.debug(f"Batch mutation {i} failed: {e}")

            iter_time = time.time() - iter_start
            times.append(iter_time)

        total_time = time.time() - start_time

        # Memory stats
        mem_current, mem_peak = tracemalloc.get_traced_memory()
        mem_peak_mb = mem_peak / 1024 / 1024
        mem_delta_mb = (mem_current / 1024 / 1024) - mem_start
        tracemalloc.stop()

        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        throughput = batch_size / total_time
        success_rate = successes / batch_size

        result = BenchmarkResult(
            test_name="Batch Mutation Throughput",
            iterations=batch_size,
            total_time=total_time,
            avg_time=avg_time,
            median_time=median_time,
            min_time=min(times),
            max_time=max(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0.0,
            throughput=throughput,
            memory_peak_mb=mem_peak_mb,
            memory_delta_mb=mem_delta_mb,
            success_rate=success_rate,
            notes=f"Target: >60 mut/min. Actual: {throughput*60:.1f} mut/min"
        )

        self.results.append(result)
        self.logger.info(f"  Throughput: {throughput:.1f} mut/s ({throughput*60:.1f} mut/min)")
        return result

    def benchmark_memory_usage(self, duration_sec: int = 10) -> BenchmarkResult:
        """
        Benchmark memory usage under sustained load.

        Args:
            duration_sec: Duration to run benchmark (seconds)

        Returns:
            BenchmarkResult with memory metrics
        """
        self.logger.info(f"Running memory usage benchmark ({duration_sec}s sustained load)...")

        iterations = 0
        successes = 0

        # Start memory tracking
        tracemalloc.start()
        mem_start = tracemalloc.get_traced_memory()[0] / 1024 / 1024

        start_time = time.time()
        end_time = start_time + duration_sec

        while time.time() < end_time:
            try:
                result = self.operator.mutate_exit_strategy(
                    code=self.sample_strategy
                )
                if result.success:
                    successes += 1
                iterations += 1

            except Exception as e:
                self.logger.debug(f"Memory test iteration {iterations} failed: {e}")

        total_time = time.time() - start_time

        # Memory stats
        mem_current, mem_peak = tracemalloc.get_traced_memory()
        mem_current_mb = mem_current / 1024 / 1024
        mem_peak_mb = mem_peak / 1024 / 1024
        mem_delta_mb = mem_current_mb - mem_start
        tracemalloc.stop()

        throughput = iterations / total_time
        success_rate = successes / iterations if iterations > 0 else 0.0

        result = BenchmarkResult(
            test_name="Memory Usage Under Load",
            iterations=iterations,
            total_time=total_time,
            avg_time=total_time / iterations if iterations > 0 else 0.0,
            median_time=0.0,  # Not applicable
            min_time=0.0,  # Not applicable
            max_time=0.0,  # Not applicable
            std_dev=0.0,  # Not applicable
            throughput=throughput,
            memory_peak_mb=mem_peak_mb,
            memory_delta_mb=mem_delta_mb,
            success_rate=success_rate,
            notes=f"Target: <100MB. Actual: Peak={mem_peak_mb:.1f}MB, Delta={mem_delta_mb:.1f}MB"
        )

        self.results.append(result)
        self.logger.info(f"  Peak memory: {mem_peak_mb:.1f}MB, Delta: {mem_delta_mb:.1f}MB")
        return result

    def benchmark_validation_pipeline(self, iterations: int = 100) -> BenchmarkResult:
        """
        Benchmark validation pipeline performance.

        Args:
            iterations: Number of validation runs

        Returns:
            BenchmarkResult with validation metrics
        """
        self.logger.info(f"Running validation pipeline benchmark ({iterations} iterations)...")

        times = []
        successes = 0

        # Start memory tracking
        tracemalloc.start()
        mem_start = tracemalloc.get_traced_memory()[0] / 1024 / 1024

        start_time = time.time()

        for i in range(iterations):
            iter_start = time.time()

            try:
                # Perform mutation (includes validation)
                result = self.operator.mutate_exit_strategy(
                    code=self.sample_strategy
                )
                if result.success:
                    successes += 1

            except Exception as e:
                self.logger.debug(f"Validation iteration {i} failed: {e}")

            iter_time = time.time() - iter_start
            times.append(iter_time)

        total_time = time.time() - start_time

        # Memory stats
        mem_current, mem_peak = tracemalloc.get_traced_memory()
        mem_peak_mb = mem_peak / 1024 / 1024
        mem_delta_mb = (mem_current / 1024 / 1024) - mem_start
        tracemalloc.stop()

        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        throughput = iterations / total_time
        success_rate = successes / iterations

        result = BenchmarkResult(
            test_name="Validation Pipeline Performance",
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            median_time=median_time,
            min_time=min(times),
            max_time=max(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0.0,
            throughput=throughput,
            memory_peak_mb=mem_peak_mb,
            memory_delta_mb=mem_delta_mb,
            success_rate=success_rate,
            notes=f"3-layer validation (Syntax, Semantics, Types). Success rate: {success_rate*100:.1f}%"
        )

        self.results.append(result)
        self.logger.info(f"  Avg validation time: {avg_time*1000:.2f}ms, Success: {success_rate*100:.1f}%")
        return result

    def benchmark_config_loading(self, iterations: int = 100) -> BenchmarkResult:
        """
        Benchmark configuration loading overhead.

        Args:
            iterations: Number of config load operations

        Returns:
            BenchmarkResult with loading metrics
        """
        self.logger.info(f"Running config loading benchmark ({iterations} iterations)...")

        times = []
        successes = 0

        # Start memory tracking
        tracemalloc.start()
        mem_start = tracemalloc.get_traced_memory()[0] / 1024 / 1024

        start_time = time.time()

        for i in range(iterations):
            iter_start = time.time()

            try:
                # Create new operator instance
                operator = ExitMutationOperator(max_retries=self.max_retries)
                successes += 1

            except Exception as e:
                self.logger.debug(f"Config load {i} failed: {e}")

            iter_time = time.time() - iter_start
            times.append(iter_time)

        total_time = time.time() - start_time

        # Memory stats
        mem_current, mem_peak = tracemalloc.get_traced_memory()
        mem_peak_mb = mem_peak / 1024 / 1024
        mem_delta_mb = (mem_current / 1024 / 1024) - mem_start
        tracemalloc.stop()

        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        throughput = iterations / total_time
        success_rate = successes / iterations

        result = BenchmarkResult(
            test_name="Configuration Loading Overhead",
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            median_time=median_time,
            min_time=min(times),
            max_time=max(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0.0,
            throughput=throughput,
            memory_peak_mb=mem_peak_mb,
            memory_delta_mb=mem_delta_mb,
            success_rate=success_rate,
            notes=f"YAML parsing overhead. Avg: {avg_time*1000:.2f}ms per load"
        )

        self.results.append(result)
        self.logger.info(f"  Avg config load time: {avg_time*1000:.2f}ms")
        return result

    def run_all_benchmarks(self, single_iterations: int = 1000, batch_size: int = 100):
        """
        Run complete benchmark suite.

        Args:
            single_iterations: Iterations for single mutation benchmark
            batch_size: Size for batch mutation benchmark
        """
        self.logger.info("="*70)
        self.logger.info("EXIT MUTATION PERFORMANCE BENCHMARK SUITE")
        self.logger.info("="*70)

        self.setup()

        # Run benchmarks
        self.benchmark_single_mutation(iterations=single_iterations)
        self.benchmark_batch_mutation(batch_size=batch_size)
        self.benchmark_memory_usage(duration_sec=10)
        self.benchmark_validation_pipeline(iterations=100)
        self.benchmark_config_loading(iterations=100)

        self.logger.info("="*70)
        self.logger.info("BENCHMARK SUITE COMPLETE")
        self.logger.info("="*70)

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive benchmark report.

        Returns:
            Report dictionary with all results
        """
        report = {
            "benchmark_suite": "Exit Mutation Performance",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "max_retries": self.max_retries,
            "summary": {
                "total_tests": len(self.results),
                "overall_success": all(r.success_rate >= 0.8 for r in self.results if r.iterations > 0)
            },
            "performance_targets": {
                "single_mutation_time": {"target": "<1s", "unit": "seconds"},
                "batch_throughput": {"target": ">60 mut/min", "unit": "mutations/minute"},
                "memory_usage": {"target": "<100MB", "unit": "megabytes"},
                "validation_success": {"target": ">80%", "unit": "percentage"}
            },
            "results": []
        }

        for result in self.results:
            report["results"].append({
                "test_name": result.test_name,
                "iterations": result.iterations,
                "total_time_sec": round(result.total_time, 3),
                "avg_time_ms": round(result.avg_time * 1000, 2),
                "median_time_ms": round(result.median_time * 1000, 2),
                "min_time_ms": round(result.min_time * 1000, 2),
                "max_time_ms": round(result.max_time * 1000, 2),
                "std_dev_ms": round(result.std_dev * 1000, 2),
                "throughput_per_sec": round(result.throughput, 2),
                "memory_peak_mb": round(result.memory_peak_mb, 2),
                "memory_delta_mb": round(result.memory_delta_mb, 2),
                "success_rate_pct": round(result.success_rate * 100, 1),
                "notes": result.notes,
                "status": "PASS" if self._check_target(result) else "WARN"
            })

        return report

    def _check_target(self, result: BenchmarkResult) -> bool:
        """Check if benchmark result meets performance targets."""
        if result.test_name == "Single Mutation Performance":
            return result.avg_time < 1.0
        elif result.test_name == "Batch Mutation Throughput":
            return result.throughput * 60 > 60
        elif result.test_name == "Memory Usage Under Load":
            return result.memory_peak_mb < 100
        elif result.test_name == "Validation Pipeline Performance":
            return result.success_rate >= 0.8
        return True

    def save_report(self, output_path: str):
        """
        Save benchmark report to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        report = self.generate_report()

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Benchmark report saved to: {output_path}")

    def print_summary(self):
        """Print human-readable summary to console."""
        report = self.generate_report()

        print("\n" + "="*70)
        print("PERFORMANCE BENCHMARK SUMMARY")
        print("="*70)

        for result_data in report["results"]:
            status = "✅" if result_data["status"] == "PASS" else "⚠️ "
            print(f"\n{status} {result_data['test_name']}")
            print(f"  Iterations: {result_data['iterations']}")
            print(f"  Avg Time: {result_data['avg_time_ms']:.2f}ms")
            print(f"  Throughput: {result_data['throughput_per_sec']:.2f} mut/s")
            print(f"  Memory Peak: {result_data['memory_peak_mb']:.2f}MB")
            print(f"  Success Rate: {result_data['success_rate_pct']:.1f}%")
            print(f"  {result_data['notes']}")

        print("\n" + "="*70)
        overall = "✅ ALL TARGETS MET" if report["summary"]["overall_success"] else "⚠️  SOME TARGETS MISSED"
        print(f"Overall Status: {overall}")
        print("="*70 + "\n")


def main():
    """Main entry point for benchmark script."""
    parser = argparse.ArgumentParser(
        description="Exit Mutation Performance Benchmark Suite"
    )
    parser.add_argument(
        '--iterations', '-n',
        type=int,
        default=1000,
        help='Number of iterations for single mutation test (default: 1000)'
    )
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=100,
        help='Batch size for throughput test (default: 100)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='benchmark_results.json',
        help='Output JSON file path (default: benchmark_results.json)'
    )
    parser.add_argument(
        '--max-retries', '-r',
        type=int,
        default=3,
        help='Maximum retry attempts for mutations (default: 3)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Run benchmarks
    benchmark = ExitMutationBenchmark(
        max_retries=args.max_retries,
        verbose=args.verbose
    )

    try:
        benchmark.run_all_benchmarks(
            single_iterations=args.iterations,
            batch_size=args.batch_size
        )

        # Save and display results
        benchmark.save_report(args.output)
        benchmark.print_summary()

        # Exit with appropriate code
        report = benchmark.generate_report()
        if report["summary"]["overall_success"]:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        logging.error(f"Benchmark failed with error: {e}")
        logging.debug(f"Traceback: {sys.exc_info()}")
        sys.exit(2)


if __name__ == "__main__":
    main()
