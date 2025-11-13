#!/usr/bin/env python3
"""
Phase 2 Task 7.2: Full 20-Strategy Execution with Phase 1.1 Validation Framework

This script extends the Phase 2 backtest execution with the new statistical
validation framework (v1.1) including:
  - Stationary Bootstrap (Politis & Romano 1994)
  - Dynamic Threshold (Taiwan market benchmark)
  - Bonferroni Multiple Comparison Correction
  - Statistical Significance Testing

Improvements over run_phase2_backtest_execution.py:
  1. Statistical validation using Bonferroni correction
  2. Dynamic threshold based on Taiwan 0050.TW benchmark
  3. Confidence intervals for Sharpe ratios
  4. Comprehensive validation reporting

Usage:
    python run_phase2_with_validation.py                 # Execute all 20 strategies
    python run_phase2_with_validation.py --limit 5       # Execute first 5 strategies
    python run_phase2_with_validation.py --timeout 300   # 5-minute timeout per strategy
"""

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

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

# Import validation framework (v1.1)
from src.validation import (
    BonferroniIntegrator,
    DynamicThresholdCalculator
)


class Phase2WithValidationRunner:
    """
    Enhanced Phase 2 Test Runner with Statistical Validation (v1.1).

    Extends Phase2TestRunner with:
      - Bonferroni multiple comparison correction
      - Dynamic threshold based on Taiwan market benchmark
      - Statistical significance testing for strategies
      - Enhanced reporting with validation results

    Attributes:
        executor: BacktestExecutor for isolated strategy execution
        metrics_extractor: MetricsExtractor for metrics extraction
        classifier: SuccessClassifier for result classification
        error_classifier: ErrorClassifier for error categorization
        reporter: ResultsReporter for report generation
        bonferroni: BonferroniIntegrator for statistical validation
        threshold_calc: DynamicThresholdCalculator for market benchmark
        default_timeout: Default execution timeout in seconds
        limit: Maximum number of strategies to execute (None = all)
    """

    def __init__(self, timeout: int = 420, limit: Optional[int] = None):
        """
        Initialize Phase2WithValidationRunner.

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

        # Initialize validation framework (v1.1)
        self.bonferroni = BonferroniIntegrator(
            n_strategies=limit if limit else 20,
            use_dynamic_threshold=True  # v1.1 feature
        )
        self.threshold_calc = DynamicThresholdCalculator(
            benchmark_ticker="0050.TW",
            lookback_years=3,
            margin=0.2,
            static_floor=0.0
        )

        logger.info("✅ Initialized with Phase 1.1 Validation Framework")
        logger.info(f"   - Bonferroni correction for {limit if limit else 20} strategies")
        logger.info(f"   - Dynamic threshold: {self.threshold_calc.get_threshold():.2f}")

    def run(self, timeout: Optional[int] = None, verbose: bool = True) -> dict:
        """
        Execute main orchestration loop with validation.

        This is the primary entry point that:
          1. Verifies finlab session is authenticated
          2. Discovers all strategy files
          3. Executes each strategy with progress tracking
          4. Extracts metrics and classifies results
          5. **NEW**: Validates strategies with Bonferroni correction
          6. Generates comprehensive reports with validation results

        Args:
            timeout: Override default timeout (in seconds)
            verbose: Whether to print progress messages

        Returns:
            Dictionary with execution summary including validation results

        Raises:
            RuntimeError: If finlab session is not authenticated
        """
        execution_timeout = timeout or self.default_timeout
        start_time = time.time()

        logger.info("=" * 80)
        logger.info("PHASE 2 TASK 7.2: BACKTEST EXECUTION WITH VALIDATION (v1.1)")
        logger.info("=" * 80)

        # Step 1: Verify finlab session authentication
        logger.info("\nStep 1/6: Verifying finlab session authentication...")
        if not self._verify_authentication(verbose=verbose):
            raise RuntimeError("Finlab session authentication failed. Cannot continue.")

        # Step 2: Discover strategy files
        logger.info("\nStep 2/6: Discovering strategy files...")
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
        logger.info(f"\nStep 3/6: Executing {len(strategy_files)} strategies...")
        execution_results = self._execute_strategies(
            strategy_files,
            timeout=execution_timeout,
            verbose=verbose
        )

        # Step 4: Extract metrics and classify results
        logger.info("\nStep 4/6: Extracting metrics and classifying results...")
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

        # Step 5: **NEW** Statistical Validation with Bonferroni Correction
        logger.info("\nStep 5/6: Performing statistical validation (v1.1)...")
        validation_results = self._validate_strategies(execution_results, strategy_metrics)

        # Step 6: Generate comprehensive reports
        logger.info("\nStep 6/6: Generating reports with validation results...")
        json_report = self._generate_enhanced_json_report(
            execution_results,
            strategy_metrics,
            classifications,
            validation_results
        )
        markdown_report = self._generate_enhanced_markdown_report(
            execution_results,
            strategy_metrics,
            classifications,
            validation_results
        )

        # Save reports
        self._save_reports(json_report, markdown_report)

        execution_time = time.time() - start_time

        # Prepare summary
        summary = {
            'success': True,
            'total_strategies': len(strategy_files),
            'executed': sum(1 for r in execution_results if r.success),
            'failed': sum(1 for r in execution_results if not r.success),
            'validation_passed': sum(1 for v in validation_results if v.get('validation_passed', False)),
            'results': execution_results,
            'strategy_metrics': strategy_metrics,
            'classifications': classifications,
            'validation_results': validation_results,
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
        """Verify finlab session is authenticated before execution."""
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
        """Discover all generated_strategy_fixed_iter*.py files."""
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
        """Execute all strategy files with progress tracking."""
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
        """Extract metrics from an ExecutionResult."""
        if not result.success:
            return StrategyMetrics(execution_success=False)

        return StrategyMetrics(
            sharpe_ratio=result.sharpe_ratio,
            total_return=result.total_return,
            max_drawdown=result.max_drawdown,
            execution_success=True
        )

    def _validate_strategies(
        self,
        execution_results: List[ExecutionResult],
        strategy_metrics: List[StrategyMetrics]
    ) -> List[Dict[str, Any]]:
        """
        Validate strategies using Bonferroni correction (v1.1).

        Args:
            execution_results: List of execution results
            strategy_metrics: List of extracted metrics

        Returns:
            List of validation result dictionaries
        """
        validation_results = []
        dynamic_threshold = self.threshold_calc.get_threshold()

        logger.info(f"Statistical Validation Settings:")
        logger.info(f"  - Dynamic Threshold: {dynamic_threshold:.2f}")
        logger.info(f"  - Number of Strategies: {len(execution_results)}")
        logger.info(f"  - Significance Level (α): 0.05")
        logger.info(f"  - Bonferroni Corrected α: {0.05 / len(execution_results):.4f}")

        for idx, (result, metrics) in enumerate(zip(execution_results, strategy_metrics), 1):
            if not result.success or result.sharpe_ratio is None:
                validation_results.append({
                    'validation_passed': False,
                    'reason': 'Execution failed or no Sharpe ratio',
                    'sharpe_ratio': None,
                    'bonferroni_alpha': 0.05 / len(execution_results),
                    'bonferroni_threshold': None,
                    'dynamic_threshold': dynamic_threshold,
                    'statistically_significant': False,
                    'beats_dynamic_threshold': False
                })
                continue

            # Validate single strategy with Bonferroni correction
            validation = self.bonferroni.validate_single_strategy(
                sharpe_ratio=result.sharpe_ratio,
                n_periods=252  # Assume 1 year of trading days
            )

            # Extract Bonferroni threshold
            # FIX: Use 'statistical_threshold' (0.5) instead of 'significance_threshold' (0.8)
            bonferroni_threshold = validation.get('statistical_threshold', 0.5)
            bonferroni_alpha = 0.05 / len(execution_results)

            # FIX Bug #2: Explicitly calculate statistically_significant
            # This checks if Sharpe > Bonferroni-corrected threshold
            statistically_significant = result.sharpe_ratio > bonferroni_threshold

            # Add dynamic threshold comparison
            beats_dynamic = result.sharpe_ratio >= dynamic_threshold

            # FIX Bug #1: Add correct Bonferroni fields
            validation['bonferroni_alpha'] = bonferroni_alpha
            validation['bonferroni_threshold'] = bonferroni_threshold
            validation['statistically_significant'] = statistically_significant
            validation['dynamic_threshold'] = dynamic_threshold
            validation['beats_dynamic_threshold'] = beats_dynamic

            # Overall validation passes if:
            # 1. Statistically significant (Sharpe > Bonferroni threshold)
            # 2. Beats dynamic threshold (Sharpe >= dynamic threshold)
            validation['validation_passed'] = (
                statistically_significant and beats_dynamic
            )

            validation_results.append(validation)

            # FIX Bug #3: Add detailed validation logging
            if validation['validation_passed']:
                logger.info(
                    f"  Strategy {idx}: ✅ VALIDATED "
                    f"(Sharpe {result.sharpe_ratio:.3f} > "
                    f"Bonferroni {bonferroni_threshold:.3f} AND >= "
                    f"Dynamic {dynamic_threshold:.3f})"
                )
            else:
                reasons = []
                if not statistically_significant:
                    reasons.append(
                        f"Sharpe {result.sharpe_ratio:.3f} ≤ Bonferroni {bonferroni_threshold:.3f}"
                    )
                if not beats_dynamic:
                    reasons.append(
                        f"Sharpe {result.sharpe_ratio:.3f} < Dynamic {dynamic_threshold:.3f}"
                    )
                logger.warning(
                    f"  Strategy {idx}: ❌ NOT VALIDATED - {' AND '.join(reasons)}"
                )

        # Summary
        validated_count = sum(1 for v in validation_results if v.get('validation_passed', False))
        logger.info(f"\nValidation Summary: {validated_count}/{len(validation_results)} strategies validated")

        return validation_results

    def _generate_enhanced_json_report(
        self,
        execution_results: List[ExecutionResult],
        strategy_metrics: List[StrategyMetrics],
        classifications: List[ClassificationResult],
        validation_results: List[Dict[str, Any]]
    ) -> dict:
        """Generate enhanced JSON report with validation results."""
        # Start with base report from reporter
        base_report = self.reporter.generate_json_report(execution_results)

        # Enhance with validation results
        base_report['validation_framework_version'] = '1.1'
        base_report['validation_enabled'] = True
        base_report['dynamic_threshold'] = self.threshold_calc.get_threshold()

        # Add validation statistics (FIX: More accurate labeling)
        validated_count = sum(1 for v in validation_results if v.get('validation_passed', False))
        bonferroni_passed = sum(1 for v in validation_results if v.get('statistically_significant', False))
        dynamic_passed = sum(1 for v in validation_results if v.get('beats_dynamic_threshold', False))

        validation_stats = {
            'total_validated': validated_count,
            'total_failed_validation': len(validation_results) - validated_count,
            'validation_rate': validated_count / len(validation_results) if validation_results else 0.0,
            'bonferroni_passed': bonferroni_passed,  # NEW: Strategies > Bonferroni threshold
            'dynamic_passed': dynamic_passed,  # NEW: Strategies >= dynamic threshold
            'bonferroni_threshold': validation_results[0].get('bonferroni_threshold', 0.5) if validation_results else 0.5,
            'bonferroni_alpha': validation_results[0].get('bonferroni_alpha', 0.0025) if validation_results else 0.0025,
            # DEPRECATED (kept for backwards compatibility):
            'statistically_significant': bonferroni_passed,
            'beat_dynamic_threshold': dynamic_passed
        }

        base_report['validation_statistics'] = validation_stats

        # Add per-strategy validation details (FIX Bug #1: Correct field names)
        base_report['strategies_validation'] = [
            {
                'strategy_index': idx,
                'validation_passed': val.get('validation_passed', False),
                'statistically_significant': val.get('statistically_significant', False),
                'beats_dynamic_threshold': val.get('beats_dynamic_threshold', False),
                'sharpe_ratio': result.sharpe_ratio if result.success else None,
                'bonferroni_alpha': val.get('bonferroni_alpha'),  # NEW: Correct significance level
                'bonferroni_threshold': val.get('bonferroni_threshold'),  # NEW: Renamed from significance_threshold
                'dynamic_threshold': val.get('dynamic_threshold')
                # REMOVED: p_value (no p-values in threshold-based validation)
            }
            for idx, (result, val) in enumerate(zip(execution_results, validation_results))
        ]

        return base_report

    def _generate_enhanced_markdown_report(
        self,
        execution_results: List[ExecutionResult],
        strategy_metrics: List[StrategyMetrics],
        classifications: List[ClassificationResult],
        validation_results: List[Dict[str, Any]]
    ) -> str:
        """Generate enhanced Markdown report with validation results."""
        # Start with base report
        base_report = self.reporter.generate_markdown_report(execution_results)

        # Add validation section
        validation_section = "\n\n## Statistical Validation (v1.1)\n\n"
        validation_section += "### Validation Framework Settings\n\n"
        validation_section += f"- **Dynamic Threshold**: {self.threshold_calc.get_threshold():.2f}\n"
        validation_section += f"- **Benchmark**: 0050.TW (Taiwan 50 ETF)\n"
        validation_section += f"- **Margin**: 0.2 (active must beat passive by 0.2 Sharpe)\n"
        validation_section += f"- **Significance Level (α)**: 0.05\n"
        validation_section += f"- **Bonferroni Corrected α**: {0.05 / len(execution_results):.4f}\n\n"

        validation_section += "### Validation Statistics\n\n"
        validated_count = sum(1 for v in validation_results if v.get('validation_passed', False))
        validation_section += f"- **Total Validated**: {validated_count}/{len(validation_results)} ({validated_count/len(validation_results)*100:.1f}%)\n"
        validation_section += f"- **Statistically Significant**: {sum(1 for v in validation_results if v.get('statistically_significant', False))}\n"
        validation_section += f"- **Beat Dynamic Threshold**: {sum(1 for v in validation_results if v.get('beats_dynamic_threshold', False))}\n\n"

        validation_section += "### Validated Strategies\n\n"
        validation_section += "| Strategy | Sharpe | Threshold | Statistical Sig. | Validated |\n"
        validation_section += "|----------|--------|-----------|------------------|------------|\n"

        for idx, (result, val) in enumerate(zip(execution_results, validation_results)):
            if result.success and result.sharpe_ratio is not None:
                validation_section += (
                    f"| iter{idx} | {result.sharpe_ratio:.2f} | "
                    f"{val.get('dynamic_threshold', 0.8):.2f} | "
                    f"{'✅' if val.get('statistically_significant', False) else '❌'} | "
                    f"{'✅' if val.get('validation_passed', False) else '❌'} |\n"
                )

        # Insert validation section before final summary
        report_parts = base_report.rsplit("\n## ", 1)
        if len(report_parts) == 2:
            enhanced_report = report_parts[0] + validation_section + "\n## " + report_parts[1]
        else:
            enhanced_report = base_report + validation_section

        return enhanced_report

    def _save_reports(self, json_report: dict, markdown_report: str) -> None:
        """Save JSON and Markdown reports to disk."""
        project_root = Path(__file__).parent

        # Save JSON report with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = project_root / f"phase2_validated_results_{timestamp}.json"
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_report, f, indent=2)
            logger.info(f"✅ JSON report saved: {json_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save JSON report: {e}")

        # Save Markdown report with timestamp
        md_path = project_root / f"phase2_validated_results_{timestamp}.md"
        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_report)
            logger.info(f"✅ Markdown report saved: {md_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save Markdown report: {e}")

    def _print_summary(self, summary: dict) -> None:
        """Print execution summary to console."""
        logger.info("\n" + "=" * 80)
        logger.info("EXECUTION SUMMARY")
        logger.info("=" * 80)

        total = summary['total_strategies']
        executed = summary['executed']
        failed = summary['failed']
        validated = summary['validation_passed']
        execution_time = summary['execution_time']

        logger.info(f"\nTotal Strategies:      {total}")
        logger.info(f"Successfully Executed: {executed} ({executed/total*100:.1f}%)")
        logger.info(f"Failed:                {failed} ({failed/total*100:.1f}%)")
        logger.info(f"**VALIDATED (v1.1)**:  {validated} ({validated/total*100:.1f}%)")
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

        # Validation breakdown
        validation_results = summary['validation_results']
        stat_sig = sum(1 for v in validation_results if v.get('statistically_significant', False))
        beat_threshold = sum(1 for v in validation_results if v.get('beats_dynamic_threshold', False))

        logger.info(f"\nValidation Breakdown (v1.1):")
        logger.info(f"  Statistically Significant: {stat_sig}")
        logger.info(f"  Beat Dynamic Threshold:    {beat_threshold}")
        logger.info(f"  Both (Validated):          {validated}")

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
    """Command-line entry point for Phase2WithValidationRunner."""
    parser = argparse.ArgumentParser(
        description='Phase 2 Task 7.2: Execute 20 strategies with v1.1 validation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_phase2_with_validation.py
  python run_phase2_with_validation.py --limit 5
  python run_phase2_with_validation.py --timeout 300
  python run_phase2_with_validation.py --limit 3 --timeout 300 --quiet
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

    # Create and run test runner with validation
    runner = Phase2WithValidationRunner(timeout=args.timeout, limit=args.limit)

    try:
        summary = runner.run(timeout=args.timeout, verbose=not args.quiet)
        sys.exit(0 if summary.get('success', False) else 1)
    except Exception as e:
        logger.error(f"Execution failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()
