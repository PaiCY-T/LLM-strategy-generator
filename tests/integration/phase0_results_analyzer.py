"""Phase 0 Results Analyzer for Template Mode Decision Making.

Analyzes 50-iteration test results to make GO/NO-GO/PARTIAL decision based on:
- Champion update rate (≥5% = GO, 2-5% = PARTIAL, <2% = NO-GO)
- Average Sharpe ratio (>1.0 = GO, 0.8-1.0 = PARTIAL, <0.8 = NO-GO)
- Parameter diversity (≥30 unique = target)
- Validation pass rate (≥90% = target)

Decision Matrix:
- SUCCESS (≥5% update rate AND >1.0 Sharpe): Skip population-based, use template mode
- PARTIAL (2-5% update rate OR 0.8-1.0 Sharpe): Consider hybrid approach
- FAILURE (<2% update rate OR <0.8 Sharpe): Proceed to population-based learning

Baseline Comparison (from 200-iteration free-form test):
- Champion update rate: 0.5%
- Average Sharpe: 1.3728
- Variance: 1.001
"""

import logging
from typing import Dict, Any, Tuple, Optional
from datetime import datetime


class ResultsAnalyzer:
    """Analyzer for Phase 0 template mode test results.

    Takes results from Phase0TestHarness and performs comprehensive analysis to
    determine if template mode achieves sufficient champion update rate to skip
    population-based learning (Phase 1).

    Attributes:
        results: Complete results dictionary from Phase0TestHarness
        baseline: Baseline metrics from 200-iteration free-form test
        logger: Logger instance for analyzer output
    """

    # Baseline metrics from 200-iteration free-form test
    BASELINE = {
        'champion_update_rate': 0.5,  # 0.5% update rate
        'avg_sharpe': 1.3728,
        'sharpe_variance': 1.001
    }

    # Decision thresholds
    THRESHOLDS = {
        'success': {
            'champion_update_rate': 5.0,  # ≥5% for SUCCESS
            'avg_sharpe': 1.0               # >1.0 for SUCCESS
        },
        'partial': {
            'champion_update_rate': 2.0,  # 2-5% for PARTIAL
            'avg_sharpe': 0.8               # 0.8-1.0 for PARTIAL
        },
        'target': {
            'param_diversity': 30,          # ≥30 unique combinations
            'validation_pass_rate': 90.0    # ≥90% validation pass rate
        }
    }

    def __init__(self, results: Dict[str, Any]):
        """Initialize ResultsAnalyzer with test results.

        Args:
            results: Complete results dictionary from Phase0TestHarness.run()
                Must contain all primary metrics (champion_update_rate, avg_sharpe, etc.)
        """
        self.results = results
        self.baseline = self.BASELINE
        self.logger = logging.getLogger(__name__)

        # Cache for expensive calculations
        self._metrics_cache: Optional[Dict[str, float]] = None

        # Log initialization
        self.logger.info("=" * 70)
        self.logger.info("RESULTS ANALYZER INITIALIZED")
        self.logger.info("=" * 70)
        self.logger.info(f"Total iterations: {results.get('total_iterations', 0)}")
        self.logger.info(f"Champion updates: {results.get('champion_update_count', 0)}")
        self.logger.info(f"Update rate: {results.get('champion_update_rate', 0.0):.1f}%")
        self.logger.info(f"Best Sharpe: {results.get('best_sharpe', 0.0):.4f}")
        self.logger.info(f"Avg Sharpe: {results.get('avg_sharpe', 0.0):.4f}")
        self.logger.info("=" * 70)

    def calculate_primary_metrics(self) -> Dict[str, float]:
        """Calculate all primary decision metrics from test results.

        Extracts and validates the 5 key metrics used for GO/NO-GO decision:
        1. Champion update rate (updates / total iterations × 100)
        2. Average Sharpe ratio (mean across successful iterations)
        3. Best Sharpe ratio (maximum achieved)
        4. Sharpe variance (variability of Sharpe ratios)
        5. Parameter diversity rate (unique combinations / total × 100)

        Handles edge cases:
        - No champion updates: update_rate = 0.0
        - All iterations failed: avg_sharpe = 0.0, best_sharpe = 0.0
        - Single successful iteration: variance = 0.0

        Uses caching to prevent recalculation when called multiple times.

        Returns:
            Dict[str, float]: Primary metrics dictionary containing:
                - champion_update_rate: Percentage (0-100)
                - avg_sharpe: Average Sharpe ratio
                - best_sharpe: Maximum Sharpe ratio
                - sharpe_variance: Variance of Sharpe ratios
                - param_diversity_rate: Percentage (0-100)

        Raises:
            KeyError: If required metrics are missing from results
        """
        # Return cached metrics if available
        if self._metrics_cache is not None:
            return self._metrics_cache

        # Validate required fields exist
        required_fields = [
            'champion_update_rate',
            'avg_sharpe',
            'best_sharpe',
            'sharpe_variance',
            'param_diversity_rate'
        ]

        missing_fields = [field for field in required_fields
                         if field not in self.results]
        if missing_fields:
            raise KeyError(f"Results missing required fields: {missing_fields}")

        # Extract primary metrics
        metrics = {
            'champion_update_rate': float(self.results['champion_update_rate']),
            'avg_sharpe': float(self.results['avg_sharpe']),
            'best_sharpe': float(self.results['best_sharpe']),
            'sharpe_variance': float(self.results['sharpe_variance']),
            'param_diversity_rate': float(self.results['param_diversity_rate'])
        }

        # Log metrics
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("PRIMARY METRICS")
        self.logger.info("=" * 70)
        self.logger.info(f"Champion update rate: {metrics['champion_update_rate']:.2f}%")
        self.logger.info(f"Average Sharpe: {metrics['avg_sharpe']:.4f}")
        self.logger.info(f"Best Sharpe: {metrics['best_sharpe']:.4f}")
        self.logger.info(f"Sharpe variance: {metrics['sharpe_variance']:.4f}")
        self.logger.info(f"Parameter diversity rate: {metrics['param_diversity_rate']:.1f}%")
        self.logger.info("=" * 70)

        # Cache metrics for future calls
        self._metrics_cache = metrics

        return metrics

    def compare_to_baseline(self) -> Dict[str, Any]:
        """Compare Phase 0 template mode results to free-form baseline.

        Calculates improvement factors against 200-iteration free-form baseline:
        - Baseline update rate: 0.5%
        - Baseline avg Sharpe: 1.3728
        - Baseline variance: 1.001

        Improvement calculations:
        - Update rate improvement: (template_rate / 0.5) × 100 - 100 (percentage improvement)
        - Sharpe comparison: template_avg - baseline_avg (absolute difference)
        - Variance improvement: (1.001 - template_variance) / 1.001 × 100 (percentage reduction)

        Returns:
            Dict[str, Any]: Comparison results containing:
                - template_update_rate: Template mode update rate
                - baseline_update_rate: Baseline update rate
                - update_rate_improvement_pct: Percentage improvement
                - update_rate_multiple: How many times better (template / baseline)
                - template_avg_sharpe: Template mode average Sharpe
                - baseline_avg_sharpe: Baseline average Sharpe
                - sharpe_difference: Absolute difference
                - sharpe_improvement_pct: Percentage improvement
                - template_variance: Template mode variance
                - baseline_variance: Baseline variance
                - variance_reduction_pct: Percentage variance reduction
                - comparison_summary: Summary assessment
        """
        # Get template mode metrics
        metrics = self.calculate_primary_metrics()

        # Calculate update rate improvement
        template_update_rate = metrics['champion_update_rate']
        baseline_update_rate = self.baseline['champion_update_rate']

        if baseline_update_rate > 0:
            update_rate_multiple = template_update_rate / baseline_update_rate
            update_rate_improvement_pct = (update_rate_multiple - 1.0) * 100
        else:
            update_rate_multiple = 0.0
            update_rate_improvement_pct = 0.0

        # Calculate Sharpe comparison
        template_sharpe = metrics['avg_sharpe']
        baseline_sharpe = self.baseline['avg_sharpe']
        sharpe_difference = template_sharpe - baseline_sharpe

        if baseline_sharpe > 0:
            sharpe_improvement_pct = (sharpe_difference / baseline_sharpe) * 100
        else:
            sharpe_improvement_pct = 0.0

        # Calculate variance reduction
        template_variance = metrics['sharpe_variance']
        baseline_variance = self.baseline['sharpe_variance']

        if baseline_variance > 0:
            variance_reduction_pct = ((baseline_variance - template_variance) / baseline_variance) * 100
        else:
            variance_reduction_pct = 0.0

        # Determine comparison summary
        if update_rate_multiple >= 10.0:
            summary = "EXCEPTIONAL: 10x+ improvement over baseline"
        elif update_rate_multiple >= 5.0:
            summary = "EXCELLENT: 5-10x improvement over baseline"
        elif update_rate_multiple >= 2.0:
            summary = "GOOD: 2-5x improvement over baseline"
        elif update_rate_multiple >= 1.0:
            summary = "MARGINAL: Slight improvement over baseline"
        else:
            summary = "WORSE: Below baseline performance"

        # Build comparison results
        comparison = {
            # Update rate comparison
            'template_update_rate': template_update_rate,
            'baseline_update_rate': baseline_update_rate,
            'update_rate_improvement_pct': float(update_rate_improvement_pct),
            'update_rate_multiple': float(update_rate_multiple),

            # Sharpe comparison
            'template_avg_sharpe': template_sharpe,
            'baseline_avg_sharpe': baseline_sharpe,
            'sharpe_difference': float(sharpe_difference),
            'sharpe_improvement_pct': float(sharpe_improvement_pct),

            # Variance comparison
            'template_variance': template_variance,
            'baseline_variance': baseline_variance,
            'variance_reduction_pct': float(variance_reduction_pct),

            # Summary
            'comparison_summary': summary
        }

        # Log comparison
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("BASELINE COMPARISON")
        self.logger.info("=" * 70)
        self.logger.info(f"Update Rate:")
        self.logger.info(f"  Template mode: {template_update_rate:.2f}%")
        self.logger.info(f"  Baseline (free-form): {baseline_update_rate:.2f}%")
        self.logger.info(f"  Improvement: {update_rate_improvement_pct:+.1f}% ({update_rate_multiple:.1f}x)")
        self.logger.info("")
        self.logger.info(f"Average Sharpe:")
        self.logger.info(f"  Template mode: {template_sharpe:.4f}")
        self.logger.info(f"  Baseline (free-form): {baseline_sharpe:.4f}")
        self.logger.info(f"  Difference: {sharpe_difference:+.4f} ({sharpe_improvement_pct:+.1f}%)")
        self.logger.info("")
        self.logger.info(f"Variance:")
        self.logger.info(f"  Template mode: {template_variance:.4f}")
        self.logger.info(f"  Baseline (free-form): {baseline_variance:.4f}")
        self.logger.info(f"  Reduction: {variance_reduction_pct:+.1f}%")
        self.logger.info("")
        self.logger.info(f"SUMMARY: {summary}")
        self.logger.info("=" * 70)

        return comparison

    def make_decision(self) -> Dict[str, Any]:
        """Make GO/NO-GO/PARTIAL decision based on Phase 0 test results.

        Applies decision matrix to determine next steps:
        - SUCCESS: Template mode achieves target metrics, skip population-based
        - PARTIAL: Improvement shown but below targets, consider hybrid approach
        - FAILURE: No significant improvement, proceed to population-based learning

        Decision Logic:
            SUCCESS criteria (both must be met):
                - Champion update rate ≥5.0% AND
                - Average Sharpe ratio >1.0

            PARTIAL criteria (either can trigger):
                - Champion update rate 2.0-5.0% OR
                - Average Sharpe ratio 0.8-1.0

            FAILURE criteria:
                - Champion update rate <2.0% OR
                - Average Sharpe ratio <0.8

        Secondary Criteria (informational):
            - Parameter diversity ≥30 unique combinations (target)
            - Validation pass rate ≥90% (target)

        Returns:
            Dict[str, Any]: Decision result containing:
                - decision: 'SUCCESS', 'PARTIAL', or 'FAILURE'
                - confidence: 'HIGH', 'MEDIUM', or 'LOW'
                - recommendation: Detailed next steps
                - reasoning: Detailed explanation of decision
                - primary_criteria_met: Dict of primary criteria pass/fail
                - secondary_criteria_met: Dict of secondary criteria pass/fail
                - key_metrics: Summary of key metrics used in decision
        """
        # Get primary metrics
        metrics = self.calculate_primary_metrics()

        # Extract key values
        update_rate = metrics['champion_update_rate']
        avg_sharpe = metrics['avg_sharpe']
        best_sharpe = metrics['best_sharpe']
        param_diversity_rate = metrics['param_diversity_rate']

        # Get parameter diversity count
        param_diversity_count = self.results.get('param_diversity', 0)

        # Calculate validation pass rate
        validation_stats = self.results.get('validation_stats', {})
        total_validations = validation_stats.get('total_validations', 0)
        validation_passes = validation_stats.get('validation_passes', 0)

        if total_validations > 0:
            validation_pass_rate = (validation_passes / total_validations) * 100
        else:
            # No validations = no failures = 100% pass rate (conservative assumption)
            validation_pass_rate = 100.0

        # Evaluate primary criteria
        primary_criteria = {
            'update_rate_success': update_rate >= self.THRESHOLDS['success']['champion_update_rate'],
            'sharpe_success': avg_sharpe > self.THRESHOLDS['success']['avg_sharpe'],
            'update_rate_partial': (self.THRESHOLDS['partial']['champion_update_rate'] <=
                                   update_rate < self.THRESHOLDS['success']['champion_update_rate']),
            'sharpe_partial': (self.THRESHOLDS['partial']['avg_sharpe'] <=
                              avg_sharpe <= self.THRESHOLDS['success']['avg_sharpe'])
        }

        # Evaluate secondary criteria
        secondary_criteria = {
            'param_diversity_met': param_diversity_count >= self.THRESHOLDS['target']['param_diversity'],
            'validation_pass_rate_met': validation_pass_rate >= self.THRESHOLDS['target']['validation_pass_rate']
        }

        # Apply decision logic
        decision = None
        confidence = None
        recommendation = None
        reasoning = []

        # SUCCESS: Both primary criteria met
        if primary_criteria['update_rate_success'] and primary_criteria['sharpe_success']:
            decision = 'SUCCESS'
            confidence = 'HIGH'
            recommendation = (
                "Template mode has proven effective. SKIP population-based learning (Phase 1) "
                "and proceed directly to template mode optimization and out-of-sample validation."
            )
            reasoning.append(
                f"✅ Champion update rate ({update_rate:.2f}%) exceeds SUCCESS threshold "
                f"(≥{self.THRESHOLDS['success']['champion_update_rate']}%)"
            )
            reasoning.append(
                f"✅ Average Sharpe ratio ({avg_sharpe:.4f}) exceeds SUCCESS threshold "
                f"(>{self.THRESHOLDS['success']['avg_sharpe']})"
            )

            # Check if secondary criteria also met
            if secondary_criteria['param_diversity_met']:
                reasoning.append(
                    f"✅ Parameter diversity ({param_diversity_count} unique) meets target "
                    f"(≥{self.THRESHOLDS['target']['param_diversity']})"
                )
            else:
                reasoning.append(
                    f"⚠️ Parameter diversity ({param_diversity_count} unique) below target "
                    f"(≥{self.THRESHOLDS['target']['param_diversity']}), but not critical for SUCCESS"
                )

            if secondary_criteria['validation_pass_rate_met']:
                reasoning.append(
                    f"✅ Validation pass rate ({validation_pass_rate:.1f}%) meets target "
                    f"(≥{self.THRESHOLDS['target']['validation_pass_rate']}%)"
                )
            else:
                reasoning.append(
                    f"⚠️ Validation pass rate ({validation_pass_rate:.1f}%) below target "
                    f"(≥{self.THRESHOLDS['target']['validation_pass_rate']}%), but not critical for SUCCESS"
                )

        # PARTIAL: Either primary criteria in partial range
        elif (primary_criteria['update_rate_partial'] or primary_criteria['sharpe_partial'] or
              (primary_criteria['update_rate_success'] and not primary_criteria['sharpe_success']) or
              (primary_criteria['sharpe_success'] and not primary_criteria['update_rate_success'])):
            decision = 'PARTIAL'
            recommendation = (
                "Template mode shows improvement but below full SUCCESS criteria. "
                "CONSIDER hybrid approach: use template mode as baseline for population-based learning "
                "with reduced population size (N=5-10 instead of 20)."
            )

            # Determine confidence based on how close to SUCCESS
            if primary_criteria['update_rate_success'] or primary_criteria['sharpe_success']:
                confidence = 'MEDIUM'
                reasoning.append(
                    "One primary criterion meets SUCCESS threshold, but not both"
                )
            else:
                confidence = 'MEDIUM'
                reasoning.append(
                    "Primary criteria in PARTIAL range (between FAILURE and SUCCESS thresholds)"
                )

            # Detailed reasoning for each criterion
            if primary_criteria['update_rate_success']:
                reasoning.append(
                    f"✅ Champion update rate ({update_rate:.2f}%) exceeds SUCCESS threshold "
                    f"(≥{self.THRESHOLDS['success']['champion_update_rate']}%)"
                )
            elif primary_criteria['update_rate_partial']:
                reasoning.append(
                    f"⚠️ Champion update rate ({update_rate:.2f}%) in PARTIAL range "
                    f"({self.THRESHOLDS['partial']['champion_update_rate']}-{self.THRESHOLDS['success']['champion_update_rate']}%)"
                )
            else:
                reasoning.append(
                    f"❌ Champion update rate ({update_rate:.2f}%) below PARTIAL threshold "
                    f"(<{self.THRESHOLDS['partial']['champion_update_rate']}%)"
                )

            if primary_criteria['sharpe_success']:
                reasoning.append(
                    f"✅ Average Sharpe ratio ({avg_sharpe:.4f}) exceeds SUCCESS threshold "
                    f"(>{self.THRESHOLDS['success']['avg_sharpe']})"
                )
            elif primary_criteria['sharpe_partial']:
                reasoning.append(
                    f"⚠️ Average Sharpe ratio ({avg_sharpe:.4f}) in PARTIAL range "
                    f"({self.THRESHOLDS['partial']['avg_sharpe']}-{self.THRESHOLDS['success']['avg_sharpe']})"
                )
            else:
                reasoning.append(
                    f"❌ Average Sharpe ratio ({avg_sharpe:.4f}) below PARTIAL threshold "
                    f"(<{self.THRESHOLDS['partial']['avg_sharpe']})"
                )

            # Secondary criteria
            if secondary_criteria['param_diversity_met']:
                reasoning.append(
                    f"✅ Parameter diversity ({param_diversity_count} unique) meets target"
                )
            if secondary_criteria['validation_pass_rate_met']:
                reasoning.append(
                    f"✅ Validation pass rate ({validation_pass_rate:.1f}%) meets target"
                )

        # FAILURE: Primary criteria below partial thresholds
        else:
            decision = 'FAILURE'
            confidence = 'HIGH'
            recommendation = (
                "Template mode does not achieve sufficient improvement over baseline. "
                "PROCEED to Phase 1 (population-based learning) as originally planned. "
                "Reuse components: Template PARAM_GRID → parameter schema, "
                "StrategyValidator → offspring validation, Enhanced prompt → evolutionary prompt base."
            )

            reasoning.append(
                f"❌ Champion update rate ({update_rate:.2f}%) below PARTIAL threshold "
                f"(<{self.THRESHOLDS['partial']['champion_update_rate']}%)"
            )
            reasoning.append(
                f"❌ Average Sharpe ratio ({avg_sharpe:.4f}) below PARTIAL threshold "
                f"(<{self.THRESHOLDS['partial']['avg_sharpe']})"
            )
            reasoning.append(
                "Template mode hypothesis not validated. Population-based learning needed."
            )

        # Build decision result
        decision_result = {
            'decision': decision,
            'confidence': confidence,
            'recommendation': recommendation,
            'reasoning': reasoning,
            'primary_criteria_met': primary_criteria,
            'secondary_criteria_met': secondary_criteria,
            'key_metrics': {
                'champion_update_rate': update_rate,
                'avg_sharpe': avg_sharpe,
                'best_sharpe': best_sharpe,
                'param_diversity_count': param_diversity_count,
                'param_diversity_rate': param_diversity_rate,
                'validation_pass_rate': validation_pass_rate
            }
        }

        # Log decision
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("PHASE 0 DECISION")
        self.logger.info("=" * 70)
        self.logger.info(f"Decision: {decision}")
        self.logger.info(f"Confidence: {confidence}")
        self.logger.info("")
        self.logger.info("Reasoning:")
        for reason in reasoning:
            self.logger.info(f"  {reason}")
        self.logger.info("")
        self.logger.info("Recommendation:")
        self.logger.info(f"  {recommendation}")
        self.logger.info("=" * 70)

        return decision_result

    def analyze_parameter_diversity(self) -> Dict[str, Any]:
        """Analyze parameter diversity and exploration patterns.

        Examines the parameter combinations explored during the test to assess:
        - Total unique combinations discovered
        - Diversity rate (unique combinations / total iterations)
        - Parameter space coverage
        - Most frequently explored combinations
        - Parameter value distributions

        This analysis helps determine if template mode is effectively exploring
        the parameter space or getting stuck in local optima.

        Returns:
            Dict[str, Any]: Parameter diversity analysis containing:
                - total_combinations: Total unique parameter combinations
                - diversity_rate: Percentage (unique / total iterations)
                - meets_target: Whether diversity meets ≥30 target
                - param_combinations_list: List of unique combinations
                - combination_frequencies: Dict of combination occurrence counts
                - parameter_value_stats: Statistics for each parameter dimension
                - diversity_assessment: Overall assessment of parameter exploration
        """
        # Extract parameter data
        param_combinations = self.results.get('param_combinations', [])
        total_iterations = self.results.get('total_iterations', 0)

        # Calculate basic diversity metrics
        total_combinations = len(param_combinations)
        diversity_rate = (total_combinations / total_iterations * 100) if total_iterations > 0 else 0.0
        meets_target = total_combinations >= self.THRESHOLDS['target']['param_diversity']

        # Count combination frequencies (if we have iteration records)
        combination_frequencies = {}
        iteration_records = self.results.get('iteration_records', [])

        for record in iteration_records:
            if 'parameters' in record and record['parameters']:
                params = record['parameters']
                # Create tuple representation
                param_tuple = (
                    params.get('momentum_period'),
                    params.get('ma_periods'),
                    params.get('catalyst_type'),
                    params.get('catalyst_lookback'),
                    params.get('n_stocks'),
                    params.get('stop_loss'),
                    params.get('resample'),
                    params.get('resample_offset')
                )
                # Convert to string key for counting
                param_key = str(param_tuple)
                combination_frequencies[param_key] = combination_frequencies.get(param_key, 0) + 1

        # Analyze parameter value distributions
        parameter_value_stats = {}

        if param_combinations:
            # Initialize stats for each parameter dimension
            param_names = [
                'momentum_period', 'ma_periods', 'catalyst_type', 'catalyst_lookback',
                'n_stocks', 'stop_loss', 'resample', 'resample_offset'
            ]

            for i, param_name in enumerate(param_names):
                values = [combo[i] for combo in param_combinations if len(combo) > i and combo[i] is not None]

                if values:
                    # Calculate stats based on parameter type
                    if param_name in ['catalyst_type', 'resample']:
                        # Categorical parameters - count unique values
                        unique_values = set(values)
                        parameter_value_stats[param_name] = {
                            'type': 'categorical',
                            'unique_count': len(unique_values),
                            'values': list(unique_values),
                            'total_samples': len(values)
                        }
                    else:
                        # Numeric parameters - calculate range and distribution
                        numeric_values = [v for v in values if isinstance(v, (int, float))]
                        if numeric_values:
                            import numpy as np
                            parameter_value_stats[param_name] = {
                                'type': 'numeric',
                                'min': float(min(numeric_values)),
                                'max': float(max(numeric_values)),
                                'mean': float(np.mean(numeric_values)),
                                'std': float(np.std(numeric_values)),
                                'unique_count': len(set(numeric_values)),
                                'total_samples': len(numeric_values)
                            }

        # Assess diversity quality
        if diversity_rate >= 90:
            diversity_assessment = "EXCELLENT - High parameter space exploration"
        elif diversity_rate >= 60:
            diversity_assessment = "GOOD - Adequate parameter diversity"
        elif diversity_rate >= 30:
            diversity_assessment = "MODERATE - Some parameter reuse, acceptable diversity"
        else:
            diversity_assessment = "LOW - Limited parameter exploration, possible convergence to local optima"

        # Build analysis result
        analysis = {
            'total_combinations': total_combinations,
            'diversity_rate': float(diversity_rate),
            'meets_target': meets_target,
            'param_combinations_list': param_combinations,
            'combination_frequencies': combination_frequencies,
            'parameter_value_stats': parameter_value_stats,
            'diversity_assessment': diversity_assessment
        }

        # Log analysis
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("PARAMETER DIVERSITY ANALYSIS")
        self.logger.info("=" * 70)
        self.logger.info(f"Total unique combinations: {total_combinations}")
        self.logger.info(f"Diversity rate: {diversity_rate:.1f}%")
        self.logger.info(f"Meets target (≥{self.THRESHOLDS['target']['param_diversity']}): {'✅ YES' if meets_target else '❌ NO'}")
        self.logger.info(f"Assessment: {diversity_assessment}")
        self.logger.info("")

        if parameter_value_stats:
            self.logger.info("Parameter value distributions:")
            for param_name, stats in parameter_value_stats.items():
                if stats['type'] == 'categorical':
                    self.logger.info(f"  {param_name}: {stats['unique_count']} unique values from {stats['values']}")
                else:
                    self.logger.info(f"  {param_name}: range [{stats['min']:.2f}, {stats['max']:.2f}], "
                                   f"mean {stats['mean']:.2f}, {stats['unique_count']} unique values")

        self.logger.info("=" * 70)

        return analysis

    def generate_report(self, output_file: str = "PHASE0_RESULTS.md") -> str:
        """Generate comprehensive markdown report of Phase 0 test results and decision.

        Creates a detailed markdown report containing:
        - Executive summary with decision
        - Test configuration
        - Primary metrics results
        - Baseline comparison
        - Decision matrix evaluation
        - Detailed analysis
        - Next steps and recommendations

        Args:
            output_file: Path to save markdown report (default: PHASE0_RESULTS.md)

        Returns:
            str: Path to generated report file

        Raises:
            IOError: If report file cannot be written
        """
        # Get all analysis components
        metrics = self.calculate_primary_metrics()
        comparison = self.compare_to_baseline()
        decision_result = self.make_decision()

        # Extract key values for report
        total_iterations = self.results.get('total_iterations', 0)
        success_count = self.results.get('success_count', 0)
        champion_update_count = self.results.get('champion_update_count', 0)
        param_diversity = self.results.get('param_diversity', 0)
        test_duration = self.results.get('test_duration_seconds', 0.0)

        # Format test duration
        hours = int(test_duration // 3600)
        minutes = int((test_duration % 3600) // 60)
        seconds = int(test_duration % 60)
        duration_str = f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s"

        # Get validation stats
        validation_stats = self.results.get('validation_stats', {})
        total_validations = validation_stats.get('total_validations', 0)
        validation_passes = validation_stats.get('validation_passes', 0)
        validation_failures = validation_stats.get('validation_failures', 0)

        # Build markdown report
        report_lines = []

        # Header
        report_lines.append("# Phase 0: Template-Guided Generation - Results Report")
        report_lines.append("")
        report_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**Test Duration**: {duration_str}")
        report_lines.append(f"**Total Iterations**: {total_iterations}")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Executive Summary
        report_lines.append("## Executive Summary")
        report_lines.append("")
        report_lines.append(f"**Decision**: {decision_result['decision']}")
        report_lines.append(f"**Confidence**: {decision_result['confidence']}")
        report_lines.append("")
        report_lines.append(f"**Recommendation**: {decision_result['recommendation']}")
        report_lines.append("")

        # Decision symbol
        if decision_result['decision'] == 'SUCCESS':
            report_lines.append("✅ **Template mode SUCCEEDS** - Skip population-based learning")
        elif decision_result['decision'] == 'PARTIAL':
            report_lines.append("⚠️ **Template mode PARTIAL** - Consider hybrid approach")
        else:
            report_lines.append("❌ **Template mode FAILS** - Proceed to population-based learning")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Primary Metrics
        report_lines.append("## Primary Metrics")
        report_lines.append("")
        report_lines.append("| Metric | Value | Threshold | Status |")
        report_lines.append("|--------|-------|-----------|--------|")
        report_lines.append(
            f"| Champion Update Rate | {metrics['champion_update_rate']:.2f}% | "
            f"≥{self.THRESHOLDS['success']['champion_update_rate']}% (SUCCESS) | "
            f"{'✅' if decision_result['primary_criteria_met']['update_rate_success'] else '❌'} |"
        )
        report_lines.append(
            f"| Average Sharpe Ratio | {metrics['avg_sharpe']:.4f} | "
            f">{self.THRESHOLDS['success']['avg_sharpe']} (SUCCESS) | "
            f"{'✅' if decision_result['primary_criteria_met']['sharpe_success'] else '❌'} |"
        )
        report_lines.append(
            f"| Best Sharpe Ratio | {metrics['best_sharpe']:.4f} | - | - |"
        )
        report_lines.append(
            f"| Sharpe Variance | {metrics['sharpe_variance']:.4f} | - | - |"
        )
        report_lines.append(
            f"| Parameter Diversity | {param_diversity} unique | "
            f"≥{self.THRESHOLDS['target']['param_diversity']} (TARGET) | "
            f"{'✅' if decision_result['secondary_criteria_met']['param_diversity_met'] else '⚠️'} |"
        )
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Baseline Comparison
        report_lines.append("## Baseline Comparison")
        report_lines.append("")
        report_lines.append(f"**Baseline**: 200-iteration free-form test")
        report_lines.append("")
        report_lines.append("### Champion Update Rate")
        report_lines.append(
            f"- Template Mode: **{comparison['template_update_rate']:.2f}%**"
        )
        report_lines.append(
            f"- Baseline: {comparison['baseline_update_rate']:.2f}%"
        )
        report_lines.append(
            f"- Improvement: **{comparison['update_rate_improvement_pct']:+.1f}%** "
            f"({comparison['update_rate_multiple']:.1f}x)"
        )
        report_lines.append("")

        report_lines.append("### Average Sharpe Ratio")
        report_lines.append(
            f"- Template Mode: **{comparison['template_avg_sharpe']:.4f}**"
        )
        report_lines.append(
            f"- Baseline: {comparison['baseline_avg_sharpe']:.4f}"
        )
        report_lines.append(
            f"- Difference: **{comparison['sharpe_difference']:+.4f}** "
            f"({comparison['sharpe_improvement_pct']:+.1f}%)"
        )
        report_lines.append("")

        report_lines.append("### Sharpe Variance")
        report_lines.append(
            f"- Template Mode: **{comparison['template_variance']:.4f}**"
        )
        report_lines.append(
            f"- Baseline: {comparison['baseline_variance']:.4f}"
        )
        report_lines.append(
            f"- Reduction: **{comparison['variance_reduction_pct']:+.1f}%**"
        )
        report_lines.append("")

        report_lines.append(f"**Summary**: {comparison['comparison_summary']}")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Decision Analysis
        report_lines.append("## Decision Analysis")
        report_lines.append("")
        report_lines.append("### Reasoning")
        report_lines.append("")
        for reason in decision_result['reasoning']:
            report_lines.append(f"- {reason}")
        report_lines.append("")

        report_lines.append("### Primary Criteria Evaluation")
        report_lines.append("")
        report_lines.append(f"- Update Rate (SUCCESS): "
                          f"{'✅ PASS' if decision_result['primary_criteria_met']['update_rate_success'] else '❌ FAIL'}")
        report_lines.append(f"- Sharpe Ratio (SUCCESS): "
                          f"{'✅ PASS' if decision_result['primary_criteria_met']['sharpe_success'] else '❌ FAIL'}")
        report_lines.append(f"- Update Rate (PARTIAL): "
                          f"{'⚠️ YES' if decision_result['primary_criteria_met']['update_rate_partial'] else 'NO'}")
        report_lines.append(f"- Sharpe Ratio (PARTIAL): "
                          f"{'⚠️ YES' if decision_result['primary_criteria_met']['sharpe_partial'] else 'NO'}")
        report_lines.append("")

        report_lines.append("### Secondary Criteria Evaluation")
        report_lines.append("")
        report_lines.append(f"- Parameter Diversity (≥{self.THRESHOLDS['target']['param_diversity']}): "
                          f"{'✅ PASS' if decision_result['secondary_criteria_met']['param_diversity_met'] else '⚠️ FAIL'}")
        report_lines.append(f"- Validation Pass Rate (≥{self.THRESHOLDS['target']['validation_pass_rate']}%): "
                          f"{'✅ PASS' if decision_result['secondary_criteria_met']['validation_pass_rate_met'] else '⚠️ FAIL'}")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Detailed Statistics
        report_lines.append("## Detailed Statistics")
        report_lines.append("")
        report_lines.append("### Test Execution")
        report_lines.append(f"- Total Iterations: {total_iterations}")
        report_lines.append(f"- Successful Iterations: {success_count}")
        report_lines.append(f"- Success Rate: {(success_count/total_iterations*100):.1f}%")
        report_lines.append(f"- Champion Updates: {champion_update_count}")
        report_lines.append(f"- Test Duration: {duration_str}")
        report_lines.append(
            f"- Average Iteration Time: {(test_duration/total_iterations):.1f}s"
            if total_iterations > 0 else "- Average Iteration Time: N/A"
        )
        report_lines.append("")

        report_lines.append("### Validation Statistics")
        report_lines.append(f"- Total Validations: {total_validations}")
        report_lines.append(f"- Validation Passes: {validation_passes}")
        report_lines.append(f"- Validation Failures: {validation_failures}")
        if total_validations > 0:
            validation_pass_rate = (validation_passes / total_validations) * 100
            report_lines.append(f"- Validation Pass Rate: {validation_pass_rate:.1f}%")
        else:
            report_lines.append("- Validation Pass Rate: N/A")
        report_lines.append("")

        report_lines.append("### Parameter Diversity")
        report_lines.append(f"- Unique Parameter Combinations: {param_diversity}")
        report_lines.append(f"- Diversity Rate: {metrics['param_diversity_rate']:.1f}%")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Next Steps
        report_lines.append("## Next Steps")
        report_lines.append("")

        if decision_result['decision'] == 'SUCCESS':
            report_lines.append("### ✅ SUCCESS Path")
            report_lines.append("")
            report_lines.append("1. **Archive population-based spec** for future reference")
            report_lines.append("2. **Document template mode** as standard approach")
            report_lines.append("3. **Optimize prompt** for 10%+ update rate (stretch goal)")
            report_lines.append("4. **Out-of-sample validation** with different time periods")
            report_lines.append("5. **Robustness testing** with market regime changes")
            report_lines.append("6. **Production deployment** preparation")

        elif decision_result['decision'] == 'PARTIAL':
            report_lines.append("### ⚠️ PARTIAL Path")
            report_lines.append("")
            report_lines.append("1. **Analyze what worked** in template mode")
            report_lines.append("2. **Design hybrid approach**:")
            report_lines.append("   - Use template mode as baseline")
            report_lines.append("   - Add population-based variation (N=5-10)")
            report_lines.append("   - Combine template structure with evolutionary search")
            report_lines.append("3. **Reduce population size** from original plan (20 → 5-10)")
            report_lines.append("4. **Leverage template components**:")
            report_lines.append("   - Template PARAM_GRID as parameter schema")
            report_lines.append("   - StrategyValidator for offspring validation")
            report_lines.append("   - Enhanced prompt as evolutionary prompt base")
            report_lines.append("5. **Test hybrid approach** with 20-iteration pilot")

        else:  # FAILURE
            report_lines.append("### ❌ FAILURE Path")
            report_lines.append("")
            report_lines.append("1. **Document Phase 0 findings** in lessons learned")
            report_lines.append("2. **Extract reusable components**:")
            report_lines.append("   - Template PARAM_GRID → parameter schema")
            report_lines.append("   - StrategyValidator → offspring validation")
            report_lines.append("   - Enhanced prompt → evolutionary prompt base")
            report_lines.append("3. **Proceed to Phase 1** (population-based learning):")
            report_lines.append("   - Implement genetic algorithm")
            report_lines.append("   - Population size: N=20")
            report_lines.append("   - Target: 10%+ champion update rate")
            report_lines.append("4. **Leverage learning** from Phase 0 template analysis")

        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Appendix
        report_lines.append("## Appendix: Decision Matrix")
        report_lines.append("")
        report_lines.append("### SUCCESS Criteria")
        report_lines.append(f"- Champion update rate ≥{self.THRESHOLDS['success']['champion_update_rate']}% **AND**")
        report_lines.append(f"- Average Sharpe ratio >{self.THRESHOLDS['success']['avg_sharpe']}")
        report_lines.append("")

        report_lines.append("### PARTIAL Criteria")
        report_lines.append(f"- Champion update rate {self.THRESHOLDS['partial']['champion_update_rate']}"
                          f"-{self.THRESHOLDS['success']['champion_update_rate']}% **OR**")
        report_lines.append(f"- Average Sharpe ratio {self.THRESHOLDS['partial']['avg_sharpe']}"
                          f"-{self.THRESHOLDS['success']['avg_sharpe']}")
        report_lines.append("")

        report_lines.append("### FAILURE Criteria")
        report_lines.append(f"- Champion update rate <{self.THRESHOLDS['partial']['champion_update_rate']}% **OR**")
        report_lines.append(f"- Average Sharpe ratio <{self.THRESHOLDS['partial']['avg_sharpe']}")
        report_lines.append("")

        report_lines.append("### Secondary Criteria (Informational)")
        report_lines.append(f"- Parameter diversity: ≥{self.THRESHOLDS['target']['param_diversity']} unique combinations")
        report_lines.append(f"- Validation pass rate: ≥{self.THRESHOLDS['target']['validation_pass_rate']}%")
        report_lines.append("")

        # Write report to file
        report_content = "\n".join(report_lines)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)

            self.logger.info("")
            self.logger.info("=" * 70)
            self.logger.info(f"REPORT GENERATED: {output_file}")
            self.logger.info("=" * 70)

            return output_file

        except IOError as e:
            self.logger.error(f"Failed to write report to {output_file}: {e}")
            raise
