#!/usr/bin/env python3
"""
Phase 3 GO/NO-GO Decision Evaluation Script (Task 5.2)
======================================================

Command-line script that evaluates Phase 3 GO/NO-GO decision based on:
1. Fixed validation results
2. Duplicate detection report
3. Diversity analysis report

This script is part of the validation-framework-critical-fixes specification.

Requirements:
    - REQ-5 (Acceptance Criteria): Phase 3 GO/NO-GO Decision

Features:
    - Loads all three required input reports
    - Runs DecisionFramework.evaluate()
    - Generates comprehensive decision document (Markdown)
    - Outputs decision to console with color coding
    - Includes mitigation strategies if CONDITIONAL GO
    - Lists blocking issues if NO-GO
    - Exit codes: 0=GO, 1=CONDITIONAL_GO, 2=NO_GO

Usage:
    python3 scripts/evaluate_phase3_decision.py \
        --validation-results phase2_validated_results_20251101_132244.json \
        --duplicate-report duplicate_report.json \
        --diversity-report diversity_report_corrected.json \
        --output phase3_decision_report.md

Author: AI Assistant
Date: 2025-11-03
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.decision_framework import (
    DecisionFramework,
    DecisionReport
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ANSI color codes for console output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Evaluate Phase 3 GO/NO-GO decision based on validation, duplicate, and diversity reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard usage
  python3 scripts/evaluate_phase3_decision.py \\
      --validation-results phase2_validated_results_20251101_132244.json \\
      --duplicate-report duplicate_report.json \\
      --diversity-report diversity_report_corrected.json \\
      --output phase3_decision_report.md

  # Verbose mode
  python3 scripts/evaluate_phase3_decision.py \\
      --validation-results phase2_validated_results_20251101_132244.json \\
      --duplicate-report duplicate_report.json \\
      --diversity-report diversity_report_corrected.json \\
      --output phase3_decision_report.md \\
      --verbose

Exit Codes:
  0 - GO decision
  1 - CONDITIONAL_GO decision
  2 - NO_GO decision
  3 - Error (missing files, invalid JSON, etc.)
        """
    )

    parser.add_argument(
        '--validation-results',
        type=str,
        required=True,
        help='Path to fixed validation results JSON file'
    )

    parser.add_argument(
        '--duplicate-report',
        type=str,
        required=True,
        help='Path to duplicate detection report JSON file'
    )

    parser.add_argument(
        '--diversity-report',
        type=str,
        required=True,
        help='Path to diversity analysis report JSON file'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='phase3_decision_report.md',
        help='Output path for decision document (default: phase3_decision_report.md)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    return parser.parse_args()


def load_json_file(file_path: Path, description: str) -> Dict[str, Any]:
    """Load and parse a JSON file.

    Args:
        file_path: Path to JSON file
        description: Description for error messages

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not valid JSON
    """
    if not file_path.exists():
        raise FileNotFoundError(f"{description} not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded {description} from {file_path}")
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {description} ({file_path}): {e}")


def validate_json_schema(
    validation_results: Dict[str, Any],
    duplicate_report: Dict[str, Any],
    diversity_report: Dict[str, Any]
) -> None:
    """Validate that all required JSON fields are present.

    Args:
        validation_results: Validation results dict
        duplicate_report: Duplicate report dict
        diversity_report: Diversity report dict

    Raises:
        ValueError: If required fields are missing
    """
    missing_fields = []

    # Validate validation results
    if 'summary' not in validation_results:
        missing_fields.append('validation_results.summary')
    if 'strategies_validation' not in validation_results:
        missing_fields.append('validation_results.strategies_validation')

    # Validate duplicate report
    if 'total_strategies' not in duplicate_report:
        missing_fields.append('duplicate_report.total_strategies')

    # Validate diversity report
    if 'diversity_score' not in diversity_report:
        missing_fields.append('diversity_report.diversity_score')
    if 'total_strategies' not in diversity_report:
        missing_fields.append('diversity_report.total_strategies')

    # avg_correlation can be at top level or in metrics
    has_avg_correlation = (
        'avg_correlation' in diversity_report or
        ('metrics' in diversity_report and 'avg_correlation' in diversity_report['metrics'])
    )
    if not has_avg_correlation:
        missing_fields.append('diversity_report.avg_correlation (or metrics.avg_correlation)')

    if missing_fields:
        raise ValueError(f"Missing required fields in input JSON: {', '.join(missing_fields)}")


def get_timestamp() -> str:
    """Get current timestamp for document.

    Returns:
        Formatted timestamp string
    """
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def generate_comprehensive_decision_document(
    decision_report: DecisionReport,
    validation_results: Dict[str, Any],
    duplicate_report: Dict[str, Any],
    diversity_report: Dict[str, Any]
) -> str:
    """Generate comprehensive decision document with all analysis details.

    Args:
        decision_report: DecisionReport from decision framework
        validation_results: Validation results dict
        duplicate_report: Duplicate report dict
        diversity_report: Diversity report dict

    Returns:
        Markdown-formatted comprehensive decision document
    """
    lines = []

    # Header
    lines.extend([
        "# Phase 3 GO/NO-GO Decision Report",
        "",
        f"**Decision**: **{decision_report.decision}**",
        f"**Risk Level**: {decision_report.risk_level}",
        f"**Date**: {get_timestamp()}",
        "",
    ])

    # Executive Summary
    lines.extend([
        "## Executive Summary",
        "",
    ])

    if decision_report.decision == "GO":
        lines.append("System is **READY** for Phase 3 progression. All critical criteria met.")
    elif decision_report.decision == "CONDITIONAL_GO":
        lines.append("System meets **MINIMAL** criteria for Phase 3 with mitigation plan required.")
    else:
        lines.append("System is **NOT READY** for Phase 3. Blocking issues must be resolved.")

    lines.extend(["", ""])

    # Rationale
    lines.extend([
        "### Decision Rationale",
        "",
        decision_report.summary,
        "",
    ])

    # Key Metrics
    lines.extend([
        "## Key Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Strategies | {decision_report.total_strategies} |",
        f"| Unique Strategies | {decision_report.unique_strategies} |",
        f"| Diversity Score | {decision_report.diversity_score:.1f}/100 |",
        f"| Average Correlation | {decision_report.avg_correlation:.3f} |",
        f"| Factor Diversity | {decision_report.factor_diversity:.3f} |",
        f"| Risk Diversity | {decision_report.risk_diversity:.3f} |",
        f"| Execution Success Rate | {decision_report.execution_success_rate:.1f}% |",
        "",
    ])

    # Criteria Evaluation
    lines.extend([
        "## Criteria Evaluation",
        "",
        "### Criteria Met",
        "",
    ])

    for criterion in decision_report.criteria_met:
        lines.append(f"- ✅ **{criterion.name}**: {criterion.actual:.2f} {criterion.comparison} {criterion.threshold} ({criterion.weight})")

    if decision_report.criteria_failed:
        lines.extend([
            "",
            "### Criteria Failed",
            "",
        ])
        for criterion in decision_report.criteria_failed:
            lines.append(f"- ❌ **{criterion.name}**: {criterion.actual:.2f} {criterion.comparison} {criterion.threshold} ({criterion.weight})")

    lines.extend(["", ""])

    # Detailed Analysis
    lines.extend([
        "## Detailed Analysis",
        "",
        "### Validation Framework Status",
        "",
        f"- **Total Strategies Executed**: {validation_results.get('summary', {}).get('total', 0)}",
        f"- **Execution Success Rate**: {decision_report.execution_success_rate:.1f}%",
        f"- **Validation Framework Fixed**: {'✅ Yes' if decision_report.validation_fixed else '❌ No'}",
        "",
        "### Duplicate Detection",
        "",
        f"- **Total Strategies Analyzed**: {duplicate_report.get('total_strategies', 0)}",
        f"- **Duplicate Groups Found**: {len(duplicate_report.get('duplicate_groups', []))}",
        f"- **Unique Strategies**: {decision_report.unique_strategies}",
        "",
        "### Diversity Analysis",
        "",
        f"- **Factor Diversity**: {decision_report.factor_diversity:.3f}",
        f"- **Risk Diversity**: {decision_report.risk_diversity:.3f}",
        f"- **Overall Diversity Score**: {decision_report.diversity_score:.1f}/100",
        f"- **Recommendation**: {diversity_report.get('recommendation', 'UNKNOWN')}",
        "",
    ])

    # Warnings
    warnings = diversity_report.get('warnings', [])
    if warnings:
        lines.extend([
            "### Warnings",
            "",
        ])
        for warning in warnings:
            lines.append(f"- ⚠️ {warning}")
        lines.extend(["", ""])

    # Blocking Issues (if NO-GO)
    if decision_report.criteria_failed and decision_report.decision == "NO-GO":
        lines.extend([
            "## Blocking Issues",
            "",
            "The following critical issues must be addressed before proceeding:",
            "",
        ])
        for i, criterion in enumerate(decision_report.criteria_failed, 1):
            if criterion.weight == "CRITICAL":
                lines.append(f"{i}. **{criterion.name}**: {criterion.actual:.2f} {criterion.comparison} {criterion.threshold}")
        lines.extend(["", ""])

    # Mitigation Strategies and Recommendations
    if decision_report.recommendations:
        title = "## Mitigation Strategies" if decision_report.decision == "CONDITIONAL_GO" else "## Recommendations"
        lines.extend([
            title,
            "",
        ])
        for i, recommendation in enumerate(decision_report.recommendations, 1):
            lines.append(f"{i}. {recommendation}")
        lines.extend(["", ""])

    # Warnings (if any)
    if decision_report.warnings:
        lines.extend([
            "## Warnings",
            "",
        ])
        for warning in decision_report.warnings:
            lines.append(f"- ⚠️ {warning}")
        lines.extend(["", ""])

    # Additional Context
    lines.extend([
        "## Additional Context",
        "",
        "### Input Files",
        "",
        "This decision was based on the following analysis reports:",
        "- Validation results (fixed threshold logic)",
        "- Duplicate detection report",
        "- Diversity analysis report",
        "",
        "### Decision Framework Criteria",
        "",
        "**GO Criteria:**",
        "- Minimum 3 unique strategies",
        "- Diversity score >= 60",
        "- Average correlation < 0.8",
        "- Validation framework fixed",
        "- 100% execution success rate",
        "",
        "**CONDITIONAL GO Criteria:**",
        "- Minimum 3 unique strategies",
        "- Diversity score >= 40",
        "- Average correlation < 0.8",
        "- Validation framework fixed",
        "- 100% execution success rate",
        "",
        "**NO-GO:**",
        "- Any critical criterion fails",
        "",
    ])

    # Footer
    lines.extend([
        "---",
        "",
        "*This document was automatically generated by `scripts/evaluate_phase3_decision.py` (Task 5.2)*",
        "",
    ])

    return '\n'.join(lines)


def print_console_summary(decision_report: DecisionReport) -> None:
    """Print color-coded console summary of decision.

    Args:
        decision_report: DecisionReport from decision framework
    """
    print()
    print("=" * 80)
    print(f"{Colors.BOLD}PHASE 3 GO/NO-GO DECISION{Colors.END}")
    print("=" * 80)
    print()

    # Decision with color
    if decision_report.decision == "GO":
        decision_color = Colors.GREEN
        decision_icon = "✅"
    elif decision_report.decision == "CONDITIONAL_GO":
        decision_color = Colors.YELLOW
        decision_icon = "⚠️"
    else:
        decision_color = Colors.RED
        decision_icon = "❌"

    print(f"{Colors.BOLD}Decision:{Colors.END} {decision_color}{decision_icon} {decision_report.decision}{Colors.END}")
    print(f"{Colors.BOLD}Risk Level:{Colors.END} {decision_report.risk_level}")
    print()

    # Key metrics
    print(f"{Colors.BOLD}Key Metrics:{Colors.END}")
    print(f"  Unique Strategies:   {decision_report.unique_strategies}")
    print(f"  Diversity Score:     {decision_report.diversity_score:.1f}/100")
    print(f"  Average Correlation: {decision_report.avg_correlation:.3f}")
    print()

    # Criteria evaluation
    print(f"{Colors.BOLD}Criteria Evaluation:{Colors.END}")
    passed_count = len(decision_report.criteria_met)
    failed_count = len(decision_report.criteria_failed)
    total_count = passed_count + failed_count
    print(f"  Passed: {passed_count}/{total_count}")

    critical_failed = [c for c in decision_report.criteria_failed if c.weight == "CRITICAL"]
    if critical_failed:
        print(f"  {Colors.RED}Critical Failures: {len(critical_failed)}{Colors.END}")
        for criterion in critical_failed:
            print(f"    - {criterion.name}: {criterion.actual:.2f} {criterion.comparison} {criterion.threshold}")
    print()

    # Blocking Issues (if NO-GO)
    if decision_report.decision == "NO-GO" and critical_failed:
        print(f"{Colors.RED}{Colors.BOLD}Blocking Issues:{Colors.END}")
        for i, criterion in enumerate(critical_failed, 1):
            print(f"  {i}. {criterion.name}: {criterion.actual:.2f} {criterion.comparison} {criterion.threshold}")
        print()

    # Recommendations
    if decision_report.recommendations:
        title = "Mitigation Strategies" if decision_report.decision == "CONDITIONAL_GO" else "Recommendations"
        print(f"{Colors.YELLOW if decision_report.decision == 'CONDITIONAL_GO' else Colors.BLUE}{Colors.BOLD}{title}:{Colors.END}")
        for i, rec in enumerate(decision_report.recommendations[:3], 1):  # Show first 3
            print(f"  {i}. {rec}")
        if len(decision_report.recommendations) > 3:
            print(f"  ... and {len(decision_report.recommendations) - 3} more (see decision document)")
        print()

    print("=" * 80)
    print()


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0=GO, 1=CONDITIONAL_GO, 2=NO_GO, 3=ERROR)
    """
    # Parse arguments
    args = parse_arguments()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 80)
    logger.info("Phase 3 GO/NO-GO Decision Evaluation (Task 5.2)")
    logger.info("=" * 80)

    try:
        # Convert paths
        validation_path = Path(args.validation_results)
        duplicate_path = Path(args.duplicate_report)
        diversity_path = Path(args.diversity_report)
        output_path = Path(args.output)

        # Load input files
        logger.info("Loading input files...")
        validation_results = load_json_file(validation_path, "validation results")
        duplicate_report = load_json_file(duplicate_path, "duplicate report")
        diversity_report = load_json_file(diversity_path, "diversity report")

        # Validate JSON schemas
        logger.info("Validating JSON schemas...")
        validate_json_schema(validation_results, duplicate_report, diversity_report)

        # Initialize decision framework
        logger.info("Initializing decision framework...")
        framework = DecisionFramework()

        # Evaluate decision
        logger.info("Evaluating GO/NO-GO criteria...")
        decision_report = framework.evaluate(
            validation_results=validation_results,
            duplicate_report=duplicate_report,
            diversity_report=diversity_report
        )

        # Log key metrics
        logger.info(
            f"Metrics: unique={decision_report.unique_strategies}, "
            f"diversity={decision_report.diversity_score:.1f}, "
            f"corr={decision_report.avg_correlation:.3f}"
        )

        # Generate comprehensive decision document
        logger.info("Generating comprehensive decision document...")
        comprehensive_doc = generate_comprehensive_decision_document(
            decision_report,
            validation_results,
            duplicate_report,
            diversity_report
        )

        # Write decision document
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(comprehensive_doc)
        logger.info(f"Decision document saved to {output_path}")

        # Print console summary
        print_console_summary(decision_report)

        # Determine exit code
        if decision_report.decision == "GO":
            logger.info("✅ GO decision - System ready for Phase 3")
            return 0
        elif decision_report.decision == "CONDITIONAL_GO":
            logger.warning("⚠️ CONDITIONAL GO - Proceed with mitigation plan")
            return 1
        else:
            logger.error("❌ NO-GO - Blocking issues must be resolved")
            return 2

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 3
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return 3
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 3


if __name__ == '__main__':
    sys.exit(main())
