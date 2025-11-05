"""
Comprehensive Validation Report Generator

Aggregates all validation results and generates detailed reports:
- Out-of-sample validation results
- Walk-forward analysis results
- Baseline comparison results
- Bootstrap confidence intervals
- Bonferroni multiple comparison correction

Supports both HTML and JSON output formats.

Task 8 implementation for phase2-validation-framework-integration spec.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ValidationReportGenerator:
    """
    Generates comprehensive validation reports from all validation components.

    Aggregates results from:
    - ValidationIntegrator (out-of-sample, walk-forward)
    - BaselineIntegrator (baseline comparison)
    - BootstrapIntegrator (confidence intervals)
    - BonferroniIntegrator (multiple comparison correction)
    """

    def __init__(self, project_name: str = "Trading Strategy Validation"):
        """
        Initialize report generator.

        Args:
            project_name: Name of the project/strategy for reporting
        """
        self.project_name = project_name
        self.reports = []

    def add_strategy_validation(
        self,
        strategy_name: str,
        iteration_num: int,
        out_of_sample_results: Optional[Dict[str, Any]] = None,
        walk_forward_results: Optional[Dict[str, Any]] = None,
        baseline_results: Optional[Dict[str, Any]] = None,
        bootstrap_results: Optional[Dict[str, Any]] = None,
        bonferroni_results: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add validation results for a single strategy.

        Args:
            strategy_name: Name/identifier of the strategy
            iteration_num: Iteration number
            out_of_sample_results: Results from ValidationIntegrator.validate_out_of_sample()
            walk_forward_results: Results from ValidationIntegrator.validate_walk_forward()
            baseline_results: Results from BaselineIntegrator.compare_with_baselines()
            bootstrap_results: Results from BootstrapIntegrator.validate_with_bootstrap()
            bonferroni_results: Results from BonferroniIntegrator.validate_single_strategy()
            metadata: Additional metadata (parameters, configuration, etc.)
        """
        report = {
            'strategy_name': strategy_name,
            'iteration_num': iteration_num,
            'timestamp': datetime.now().isoformat(),
            'validations': {
                'out_of_sample': out_of_sample_results or {},
                'walk_forward': walk_forward_results or {},
                'baseline_comparison': baseline_results or {},
                'bootstrap_ci': bootstrap_results or {},
                'bonferroni_correction': bonferroni_results or {}
            },
            'metadata': metadata or {},
            'overall_status': self._calculate_overall_status(
                out_of_sample_results,
                walk_forward_results,
                baseline_results,
                bootstrap_results,
                bonferroni_results
            )
        }

        self.reports.append(report)
        logger.info(f"Added validation report for {strategy_name} (iteration {iteration_num})")

    def _calculate_overall_status(
        self,
        out_of_sample: Optional[Dict],
        walk_forward: Optional[Dict],
        baseline: Optional[Dict],
        bootstrap: Optional[Dict],
        bonferroni: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Calculate overall validation status from all components.

        Validation passes if:
        - Out-of-sample validation passes (if provided)
        - Walk-forward stability acceptable (if provided)
        - Beats at least one baseline (if provided)
        - Bootstrap CI excludes zero (if provided)
        - Bonferroni significance met (if provided)

        Args:
            out_of_sample: Out-of-sample validation results
            walk_forward: Walk-forward validation results
            baseline: Baseline comparison results
            bootstrap: Bootstrap CI results
            bonferroni: Bonferroni correction results

        Returns:
            Dictionary with overall status and reasons
        """
        passed_count = 0
        failed_count = 0
        total_validations = 0
        failures = []

        # Check out-of-sample validation
        if out_of_sample:
            total_validations += 1
            if out_of_sample.get('validation_passed', False):
                passed_count += 1
            else:
                failed_count += 1
                failures.append('Out-of-sample validation failed')

        # Check walk-forward validation
        if walk_forward:
            total_validations += 1
            if walk_forward.get('validation_passed', False):
                passed_count += 1
            else:
                failed_count += 1
                failures.append('Walk-forward validation failed')

        # Check baseline comparison
        if baseline:
            total_validations += 1
            if baseline.get('validation_passed', False):
                passed_count += 1
            else:
                failed_count += 1
                failures.append('Baseline comparison failed')

        # Check bootstrap CI
        if bootstrap:
            total_validations += 1
            if bootstrap.get('validation_passed', False):
                passed_count += 1
            else:
                failed_count += 1
                failures.append('Bootstrap CI validation failed')

        # Check Bonferroni significance
        if bonferroni:
            total_validations += 1
            if bonferroni.get('validation_passed', False):
                passed_count += 1
            else:
                failed_count += 1
                failures.append('Bonferroni significance not met')

        # Overall pass requires all validations to pass
        overall_passed = (failed_count == 0 and total_validations > 0)

        return {
            'overall_passed': overall_passed,
            'total_validations': total_validations,
            'passed_count': passed_count,
            'failed_count': failed_count,
            'pass_rate': passed_count / total_validations if total_validations > 0 else 0.0,
            'failures': failures
        }

    def generate_summary_statistics(self) -> Dict[str, Any]:
        """
        Generate summary statistics across all strategies.

        Returns:
            Dictionary with summary statistics:
            - total_strategies: Total number of strategies validated
            - strategies_passed: Number passing all validations
            - strategies_failed: Number failing at least one validation
            - overall_pass_rate: Percentage of strategies passing all validations
            - validation_breakdown: Pass rates for each validation type
        """
        if not self.reports:
            return {
                'total_strategies': 0,
                'strategies_passed': 0,
                'strategies_failed': 0,
                'overall_pass_rate': 0.0,
                'validation_breakdown': {}
            }

        total = len(self.reports)
        passed = sum(1 for r in self.reports if r['overall_status']['overall_passed'])
        failed = total - passed

        # Calculate pass rates for each validation type
        breakdown = {}
        validation_types = [
            'out_of_sample',
            'walk_forward',
            'baseline_comparison',
            'bootstrap_ci',
            'bonferroni_correction'
        ]

        for val_type in validation_types:
            results = [
                r['validations'][val_type].get('validation_passed', False)
                for r in self.reports
                if r['validations'].get(val_type)
            ]
            if results:
                breakdown[val_type] = {
                    'total': len(results),
                    'passed': sum(results),
                    'pass_rate': sum(results) / len(results)
                }

        return {
            'total_strategies': total,
            'strategies_passed': passed,
            'strategies_failed': failed,
            'overall_pass_rate': passed / total if total > 0 else 0.0,
            'validation_breakdown': breakdown
        }

    def to_json(self) -> str:
        """
        Export all validation reports as JSON.

        Returns:
            JSON string with all validation reports and summary statistics
        """
        output = {
            'project_name': self.project_name,
            'generation_timestamp': datetime.now().isoformat(),
            'summary': self.generate_summary_statistics(),
            'reports': self.reports
        }

        return json.dumps(output, indent=2)

    def save_json(self, output_path: Path):
        """
        Save validation reports to JSON file.

        Args:
            output_path: Path to save JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

        logger.info(f"Saved validation report to {output_path}")

    def to_html(self) -> str:
        """
        Generate HTML validation report.

        Returns:
            HTML string with comprehensive validation report
        """
        summary = self.generate_summary_statistics()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.project_name} - Validation Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 20px;
        }}
        .summary {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .metric {{
            display: inline-block;
            margin: 10px 20px 10px 0;
        }}
        .metric-label {{
            font-weight: bold;
            color: #7f8c8d;
        }}
        .metric-value {{
            font-size: 1.3em;
            color: #2c3e50;
        }}
        .pass {{ color: #27ae60; font-weight: bold; }}
        .fail {{ color: #e74c3c; font-weight: bold; }}
        .warning {{ color: #f39c12; font-weight: bold; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .strategy-card {{
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .validation-section {{
            margin: 15px 0;
            padding: 10px;
            background-color: white;
            border-radius: 4px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.9em;
            font-weight: 600;
        }}
        .status-pass {{
            background-color: #d4edda;
            color: #155724;
        }}
        .status-fail {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            color: #7f8c8d;
            font-size: 0.9em;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{self.project_name}</h1>
        <p>Validation Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <h2>Summary Statistics</h2>
            <div class="metric">
                <span class="metric-label">Total Strategies:</span>
                <span class="metric-value">{summary['total_strategies']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Passed:</span>
                <span class="metric-value pass">{summary['strategies_passed']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Failed:</span>
                <span class="metric-value fail">{summary['strategies_failed']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Overall Pass Rate:</span>
                <span class="metric-value">{summary['overall_pass_rate']:.1%}</span>
            </div>
        </div>

        <h2>Validation Breakdown</h2>
        <table>
            <thead>
                <tr>
                    <th>Validation Type</th>
                    <th>Total</th>
                    <th>Passed</th>
                    <th>Pass Rate</th>
                </tr>
            </thead>
            <tbody>
"""

        # Add validation breakdown rows
        validation_names = {
            'out_of_sample': 'Out-of-Sample Validation',
            'walk_forward': 'Walk-Forward Analysis',
            'baseline_comparison': 'Baseline Comparison',
            'bootstrap_ci': 'Bootstrap Confidence Intervals',
            'bonferroni_correction': 'Bonferroni Correction'
        }

        for val_type, val_name in validation_names.items():
            if val_type in summary['validation_breakdown']:
                breakdown = summary['validation_breakdown'][val_type]
                pass_rate_class = 'pass' if breakdown['pass_rate'] >= 0.7 else 'warning' if breakdown['pass_rate'] >= 0.5 else 'fail'
                html += f"""
                <tr>
                    <td>{val_name}</td>
                    <td>{breakdown['total']}</td>
                    <td>{breakdown['passed']}</td>
                    <td class="{pass_rate_class}">{breakdown['pass_rate']:.1%}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>

        <h2>Individual Strategy Reports</h2>
"""

        # Add individual strategy reports
        for report in self.reports:
            status_class = 'status-pass' if report['overall_status']['overall_passed'] else 'status-fail'
            status_text = 'PASSED' if report['overall_status']['overall_passed'] else 'FAILED'

            html += f"""
        <div class="strategy-card">
            <h3>{report['strategy_name']}
                <span class="status-badge {status_class}">{status_text}</span>
            </h3>
            <p><strong>Iteration:</strong> {report['iteration_num']} |
               <strong>Timestamp:</strong> {report['timestamp']}</p>

            <div class="validation-section">
                <h4>Validation Summary</h4>
                <p>
                    <strong>Validations Passed:</strong> {report['overall_status']['passed_count']}/{report['overall_status']['total_validations']}
                    ({report['overall_status']['pass_rate']:.1%})
                </p>
"""

            if report['overall_status']['failures']:
                html += "                <p><strong>Failures:</strong></p><ul>\n"
                for failure in report['overall_status']['failures']:
                    html += f"                    <li>{failure}</li>\n"
                html += "                </ul>\n"

            html += "            </div>\n"

            # Add detailed validation results
            validations = report['validations']

            # Out-of-sample
            if validations.get('out_of_sample'):
                oos = validations['out_of_sample']
                html += f"""
            <div class="validation-section">
                <h4>Out-of-Sample Validation</h4>
                <p><strong>Status:</strong> <span class="{'pass' if oos.get('validation_passed') else 'fail'}">
                    {'PASSED' if oos.get('validation_passed') else 'FAILED'}</span></p>
                <p><strong>Consistency:</strong> {oos.get('consistency', 0):.4f}</p>
                <p><strong>Degradation Ratio:</strong> {oos.get('degradation_ratio', 0):.4f}</p>
                <p><strong>Periods Tested:</strong> {', '.join(oos.get('periods_tested', []))}</p>
            </div>
"""

            # Walk-forward
            if validations.get('walk_forward'):
                wf = validations['walk_forward']
                html += f"""
            <div class="validation-section">
                <h4>Walk-Forward Analysis</h4>
                <p><strong>Status:</strong> <span class="{'pass' if wf.get('validation_passed') else 'fail'}">
                    {'PASSED' if wf.get('validation_passed') else 'FAILED'}</span></p>
                <p><strong>Mean Sharpe:</strong> {wf.get('mean_sharpe', 0):.4f}</p>
                <p><strong>Stability Score:</strong> {wf.get('stability_score', 0):.4f}</p>
                <p><strong>Windows Tested:</strong> {wf.get('windows_tested', 0)}</p>
            </div>
"""

            # Baseline comparison
            if validations.get('baseline_comparison'):
                bl = validations['baseline_comparison']
                html += f"""
            <div class="validation-section">
                <h4>Baseline Comparison</h4>
                <p><strong>Status:</strong> <span class="{'pass' if bl.get('validation_passed') else 'fail'}">
                    {'PASSED' if bl.get('validation_passed') else 'FAILED'}</span></p>
                <p><strong>Strategy Sharpe:</strong> {bl.get('strategy_sharpe', 0):.4f}</p>
                <p><strong>Best Improvement:</strong> {bl.get('best_improvement', 0):.4f}</p>
            </div>
"""

            # Bootstrap CI
            if validations.get('bootstrap_ci'):
                bs = validations['bootstrap_ci']
                html += f"""
            <div class="validation-section">
                <h4>Bootstrap Confidence Intervals</h4>
                <p><strong>Status:</strong> <span class="{'pass' if bs.get('validation_passed') else 'fail'}">
                    {'PASSED' if bs.get('validation_passed') else 'FAILED'}</span></p>
                <p><strong>Sharpe Ratio:</strong> {bs.get('sharpe_ratio', 0):.4f}</p>
                <p><strong>95% CI:</strong> [{bs.get('ci_lower', 0):.4f}, {bs.get('ci_upper', 0):.4f}]</p>
                <p><strong>Validation Reason:</strong> {bs.get('validation_reason', 'N/A')}</p>
            </div>
"""

            # Bonferroni correction
            if validations.get('bonferroni_correction'):
                bf = validations['bonferroni_correction']
                html += f"""
            <div class="validation-section">
                <h4>Bonferroni Multiple Comparison Correction</h4>
                <p><strong>Status:</strong> <span class="{'pass' if bf.get('validation_passed') else 'fail'}">
                    {'PASSED' if bf.get('validation_passed') else 'FAILED'}</span></p>
                <p><strong>Sharpe Ratio:</strong> {bf.get('sharpe_ratio', 0):.4f}</p>
                <p><strong>Significance Threshold:</strong> {bf.get('significance_threshold', 0):.4f}</p>
                <p><strong>Adjusted Alpha:</strong> {bf.get('adjusted_alpha', 0):.6f}</p>
            </div>
"""

            html += "        </div>\n"

        html += f"""
        <div class="footer">
            <p>Generated by Phase 2 Validation Framework Integration</p>
            <p>Report generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""

        return html

    def save_html(self, output_path: Path):
        """
        Save validation report to HTML file.

        Args:
            output_path: Path to save HTML file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.to_html())

        logger.info(f"Saved HTML validation report to {output_path}")

    def get_strategies_by_status(self, passed: bool = True) -> List[Dict[str, Any]]:
        """
        Get list of strategies by pass/fail status.

        Args:
            passed: If True, return passed strategies; if False, return failed strategies

        Returns:
            List of strategy reports matching the status
        """
        return [
            report for report in self.reports
            if report['overall_status']['overall_passed'] == passed
        ]

    def clear(self):
        """Clear all stored validation reports."""
        self.reports.clear()
        logger.info("Cleared all validation reports")


__all__ = [
    'ValidationReportGenerator',
]
