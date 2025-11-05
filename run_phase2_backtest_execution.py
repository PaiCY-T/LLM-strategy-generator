#!/usr/bin/env python3
"""
Phase 2 Task 5.1: Phase2TestRunner - End-to-end Backtest Execution Orchestrator

This module implements the main orchestration logic for executing 20 strategies end-to-end,
integrating all 5 components from earlier phases:
  1. BacktestExecutor: Execute strategy code with timeout protection
  2. MetricsExtractor: Extract performance metrics from backtest reports
  3. SuccessClassifier: Classify results into success levels (0-3)
  4. ErrorClassifier: Categorize execution errors
  5. ResultsReporter: Generate JSON and Markdown reports

The runner:
  - Scans for generated_strategy_fixed_iter*.py files
  - Verifies finlab session authentication before execution
  - Executes each strategy with progress logging
  - Handles individual strategy failures gracefully (continue to next)
  - Aggregates results from all strategies
  - Saves JSON and Markdown reports
  - Supports --limit flag for testing subset of strategies
  - Supports --timeout flag for custom timeout per strategy

Usage:
    python run_phase2_backtest_execution.py                 # Execute all 20 strategies
    python run_phase2_backtest_execution.py --limit 5       # Execute first 5 strategies
    python run_phase2_backtest_execution.py --timeout 300   # 5-minute timeout per strategy
    python run_phase2_backtest_execution.py --limit 3 --timeout 300
"""

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import components
from src.backtest.executor import BacktestExecutor, ExecutionResult
from src.backtest.metrics import MetricsExtractor, StrategyMetrics
from src.backtest.classifier import SuccessClassifier, ClassificationResult
from src.backtest.error_classifier import ErrorClassifier
from src.backtest.reporter import ResultsReporter
from src.backtest.finlab_authenticator import verify_finlab_session


class Phase2TestRunner:
    """Orchestrator for executing 20 trading strategies end-to-end.

    Manages the complete execution pipeline:
      1. Verify finlab session authentication
      2. Discover strategy files (generated_strategy_fixed_iter*.py)
      3. Execute each strategy with BacktestExecutor
      4. Extract metrics with MetricsExtractor
      5. Classify results with SuccessClassifier
      6. Categorize errors with ErrorClassifier
      7. Generate reports with ResultsReporter

    Attributes:
        executor: BacktestExecutor for isolated strategy execution
        metrics_extractor: MetricsExtractor for metrics extraction
        classifier: SuccessClassifier for result classification
        error_classifier: ErrorClassifier for error categorization
        reporter: ResultsReporter for report generation
        default_timeout: Default execution timeout in seconds
        limit: Maximum number of strategies to execute (None = all)
    """

    def __init__(self, timeout: int = 420, limit: Optional[int] = None):
        """Initialize Phase2TestRunner.

        Args:
            timeout: Default timeout per strategy in seconds (default: 420 = 7 minutes)
            limit: Maximum number of strategies to execute (None = all)
        """
        self.executor = BacktestExecutor(timeout=timeout)
        self.metrics_extractor = MetricsExtractor()
        self.classifier = SuccessClassifier()
        self.error_classifier = ErrorClassifier()
        self.reporter = ResultsReporter()
        self.default_timeout = timeout
        self.limit = limit

    def run(self, timeout: Optional[int] = None, verbose: bool = True) -> dict:
        """Execute main orchestration loop for all strategies.

        This is the primary entry point that:
          1. Verifies finlab session is authenticated
          2. Discovers all strategy files
          3. Executes each strategy with progress tracking
          4. Handles failures gracefully (continues to next strategy)
          5. Aggregates results
          6. Saves reports

        Args:
            timeout: Override default timeout (in seconds)
            verbose: Whether to print progress messages

        Returns:
            Dictionary with execution summary:
            {
                'success': bool,
                'total_strategies': int,
                'executed': int,
                'failed': int,
                'results': [ExecutionResult, ...],
                'strategy_metrics': [StrategyMetrics, ...],
                'classifications': [ClassificationResult, ...],
                'report': dict (JSON report),
                'timestamp': str,
                'execution_time': float
            }

        Raises:
            RuntimeError: If finlab session is not authenticated
        """
        execution_timeout = timeout or self.default_timeout
        start_time = time.time()

        logger.info("=" * 80)
        logger.info("PHASE 2 TASK 5.1: BACKTEST EXECUTION ORCHESTRATOR")
        logger.info("=" * 80)

        # Step 1: Verify finlab session authentication
        logger.info("\nStep 1/5: Verifying finlab session authentication...")
        if not self._verify_authentication(verbose=verbose):
            raise RuntimeError("Finlab session authentication failed. Cannot continue.")

        # Step 2: Discover strategy files
        logger.info("\nStep 2/5: Discovering strategy files...")
        strategy_files = self._discover_strategies()
        logger.info(f"Found {len(strategy_files)} strategy files")

        if not strategy_files:
            logger.error("No strategy files found. Cannot continue.")
            raise RuntimeError("No strategy files discovered")

        # Apply limit if specified
        if self.limit:
            strategy_files = strategy_files[:self.limit]
            logger.info(f"Limited to {len(strategy_files)} strategies (--limit {self.limit})")

        # Step 3: Execute strategies with progress tracking
        logger.info(f"\nStep 3/5: Executing {len(strategy_files)} strategies...")
        execution_results = self._execute_strategies(
            strategy_files,
            timeout=execution_timeout,
            verbose=verbose
        )

        # Step 4: Extract metrics and classify results
        logger.info("\nStep 4/5: Extracting metrics and classifying results...")
        strategy_metrics = []
        classifications = []

        for i, result in enumerate(execution_results, 1):
            # Extract metrics from execution result
            metrics = self._extract_metrics_from_result(result)
            strategy_metrics.append(metrics)

            # Classify the result
            classification = self.classifier.classify_single(metrics)
            classifications.append(classification)

            if i % 5 == 0:
                logger.info(f"  Processed {i}/{len(execution_results)} strategies")

        # Step 5: Generate reports
        logger.info("\nStep 5/5: Generating reports...")
        json_report = self.reporter.generate_json_report(execution_results)
        markdown_report = self.reporter.generate_markdown_report(execution_results)

        # Save reports
        self._save_reports(json_report, markdown_report)

        execution_time = time.time() - start_time

        # Prepare summary
        summary = {
            'success': True,
            'total_strategies': len(strategy_files),
            'executed': sum(1 for r in execution_results if r.success),
            'failed': sum(1 for r in execution_results if not r.success),
            'results': execution_results,
            'strategy_metrics': strategy_metrics,
            'classifications': classifications,
            'report': json_report,
            'timestamp': datetime.now().isoformat(),
            'execution_time': execution_time,
        }

        # Print summary
        self._print_summary(summary)

        logger.info("=" * 80)
        logger.info("EXECUTION COMPLETE")
        logger.info("=" * 80)

        return summary

    def _verify_authentication(self, verbose: bool = True) -> bool:
        """Verify finlab session is authenticated before execution.

        Args:
            verbose: Whether to print detailed status

        Returns:
            True if authenticated, False otherwise
        """
        try:
            status = verify_finlab_session(verbose=verbose)
            if status.is_authenticated:
                logger.info("✅ Finlab session authenticated and ready")
                return True
            else:
                logger.error(f"❌ Authentication failed: {status.error_message}")
                return False
        except Exception as e:
            logger.error(f"❌ Error during authentication check: {e}")
            return False

    def _discover_strategies(self) -> List[Path]:
        """Discover all generated_strategy_fixed_iter*.py files.

        Scans the project root directory for strategy files in the expected
        naming pattern and returns them sorted by iteration number.

        Returns:
            List of Path objects for discovered strategy files, sorted by iteration
        """
        project_root = Path(__file__).parent
        strategy_files = sorted(
            project_root.glob("generated_strategy_fixed_iter*.py"),
            key=lambda p: int(p.stem.split("_iter")[1])
        )

        logger.debug(f"Discovered {len(strategy_files)} strategy files:")
        for f in strategy_files:
            logger.debug(f"  - {f.name}")

        return strategy_files

    def _execute_strategies(
        self,
        strategy_files: List[Path],
        timeout: int,
        verbose: bool = True
    ) -> List[ExecutionResult]:
        """Execute all strategy files with progress tracking.

        Executes each strategy in isolation using BacktestExecutor,
        handling failures gracefully (continues to next strategy).

        Args:
            strategy_files: List of strategy file paths to execute
            timeout: Execution timeout per strategy in seconds
            verbose: Whether to print progress messages

        Returns:
            List of ExecutionResult objects (one per strategy)

        Note:
            Individual strategy failures do not stop execution.
            All results are returned, including failed ones.
        """
        # Load finlab context needed for execution
        try:
            from finlab import data, backtest
            logger.info("✅ Finlab context loaded successfully")
        except ImportError as e:
            logger.error(f"Failed to import finlab: {e}")
            raise RuntimeError(f"Cannot load finlab context: {e}")

        results = []
        start_time = time.time()

        for idx, strategy_file in enumerate(strategy_files, 1):
            iteration = strategy_file.stem.split("_iter")[1]
            logger.info(f"\nProcessing strategy {idx}/{len(strategy_files)} (iter{iteration})...")

            try:
                # Read strategy code
                with open(strategy_file, 'r', encoding='utf-8') as f:
                    strategy_code = f.read()

                # Measure execution time for this strategy
                strategy_start = time.time()

                # Execute strategy in isolated process
                result = self.executor.execute(
                    strategy_code=strategy_code,
                    data=data,
                    sim=backtest.sim,
                    timeout=timeout
                )

                strategy_time = time.time() - strategy_start

                if result.success:
                    logger.info(
                        f"  ✅ SUCCESS - Sharpe: {result.sharpe_ratio:.2f}, "
                        f"Return: {result.total_return:.1%}, "
                        f"Time: {strategy_time:.1f}s"
                    )
                else:
                    logger.warning(
                        f"  ❌ FAILED - {result.error_type}: {result.error_message} "
                        f"(Time: {strategy_time:.1f}s)"
                    )

                results.append(result)

            except Exception as e:
                logger.error(f"  ❌ EXCEPTION - {type(e).__name__}: {e}")
                # Create error result for this strategy
                error_result = ExecutionResult(
                    success=False,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    execution_time=time.time() - strategy_start
                )
                results.append(error_result)

            # Print progress every 5 strategies
            if idx % 5 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / idx
                remaining = len(strategy_files) - idx
                eta = avg_time * remaining
                logger.info(
                    f"  Progress: {idx}/{len(strategy_files)} strategies, "
                    f"Elapsed: {elapsed:.1f}s, ETA: {eta:.1f}s"
                )

        total_time = time.time() - start_time
        logger.info(f"\nExecution complete in {total_time:.1f}s ({total_time/len(strategy_files):.1f}s/strategy)")

        return results

    def _extract_metrics_from_result(self, result: ExecutionResult) -> StrategyMetrics:
        """Extract metrics from an ExecutionResult.

        Converts an ExecutionResult to StrategyMetrics by extracting
        the key performance indicators.

        Args:
            result: ExecutionResult from strategy execution

        Returns:
            StrategyMetrics with extracted values
        """
        if not result.success:
            return StrategyMetrics(execution_success=False)

        return StrategyMetrics(
            sharpe_ratio=result.sharpe_ratio,
            total_return=result.total_return,
            max_drawdown=result.max_drawdown,
            execution_success=True
        )

    def _save_reports(self, json_report: dict, markdown_report: str) -> None:
        """Save JSON and Markdown reports to disk.

        Args:
            json_report: Dictionary of JSON report content
            markdown_report: Markdown report as string
        """
        project_root = Path(__file__).parent

        # Save JSON report
        json_path = project_root / "phase2_backtest_results.json"
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_report, f, indent=2)
            logger.info(f"✅ JSON report saved: {json_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save JSON report: {e}")

        # Save Markdown report
        md_path = project_root / "phase2_backtest_results.md"
        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_report)
            logger.info(f"✅ Markdown report saved: {md_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save Markdown report: {e}")

    def _print_summary(self, summary: dict) -> None:
        """Print execution summary to console.

        Args:
            summary: Summary dictionary from run()
        """
        logger.info("\n" + "=" * 80)
        logger.info("EXECUTION SUMMARY")
        logger.info("=" * 80)

        total = summary['total_strategies']
        executed = summary['executed']
        failed = summary['failed']
        execution_time = summary['execution_time']

        logger.info(f"\nTotal Strategies:      {total}")
        logger.info(f"Successfully Executed: {executed} ({executed/total*100:.1f}%)")
        logger.info(f"Failed:                {failed} ({failed/total*100:.1f}%)")
        logger.info(f"Total Execution Time:  {execution_time:.1f}s ({execution_time/total:.1f}s/strategy)")

        # Classification breakdown
        classifications = summary['classifications']
        level_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        for cls in classifications:
            level_counts[cls.level] += 1

        logger.info(f"\nClassification Breakdown:")
        logger.info(f"  Level 0 (FAILED):         {level_counts[0]}")
        logger.info(f"  Level 1 (EXECUTED):       {level_counts[1]}")
        logger.info(f"  Level 2 (VALID_METRICS):  {level_counts[2]}")
        logger.info(f"  Level 3 (PROFITABLE):     {level_counts[3]}")

        # Metrics summary
        results = summary['results']
        successful_results = [r for r in results if r.success]
        if successful_results:
            sharpe_values = [r.sharpe_ratio for r in successful_results if r.sharpe_ratio is not None]
            return_values = [r.total_return for r in successful_results if r.total_return is not None]
            drawdown_values = [r.max_drawdown for r in successful_results if r.max_drawdown is not None]

            if sharpe_values:
                logger.info(f"\nPerformance Metrics (Successful Strategies):")
                logger.info(f"  Avg Sharpe Ratio:      {sum(sharpe_values)/len(sharpe_values):.2f}")
                logger.info(f"  Best Sharpe Ratio:     {max(sharpe_values):.2f}")
                logger.info(f"  Worst Sharpe Ratio:    {min(sharpe_values):.2f}")

            if return_values:
                logger.info(f"  Avg Total Return:      {sum(return_values)/len(return_values):.1%}")
                logger.info(f"  Best Total Return:     {max(return_values):.1%}")
                logger.info(f"  Worst Total Return:    {min(return_values):.1%}")

            if drawdown_values:
                logger.info(f"  Avg Max Drawdown:      {sum(drawdown_values)/len(drawdown_values):.1%}")
                logger.info(f"  Best Max Drawdown:     {max(drawdown_values):.1%}")
                logger.info(f"  Worst Max Drawdown:    {min(drawdown_values):.1%}")

        logger.info("\n" + "=" * 80)


def main():
    """Command-line entry point for Phase2TestRunner."""
    parser = argparse.ArgumentParser(
        description='Phase 2 Task 5.1: Execute 20 trading strategies end-to-end',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_phase2_backtest_execution.py
  python run_phase2_backtest_execution.py --limit 5
  python run_phase2_backtest_execution.py --timeout 300
  python run_phase2_backtest_execution.py --limit 3 --timeout 300 --quiet
        """
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of strategies to execute (default: all)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=420,
        help='Timeout per strategy in seconds (default: 420 = 7 minutes)'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress verbose output and authentication details'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.limit and args.limit < 1:
        parser.error("--limit must be >= 1")

    if args.timeout < 1:
        parser.error("--timeout must be >= 1")

    # Create and run test runner
    runner = Phase2TestRunner(timeout=args.timeout, limit=args.limit)

    try:
        summary = runner.run(timeout=args.timeout, verbose=not args.quiet)
        sys.exit(0 if summary.get('success', False) else 1)
    except Exception as e:
        logger.error(f"Execution failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
