"""
Decision Framework for GO/NO-GO Assessment
===========================================

Implements deterministic decision logic for Phase 3 progression based on:
- Strategy validation results
- Duplicate detection analysis
- Diversity metrics

This module is part of the validation-framework-critical-fixes specification (Task 5.1).

Key Components:
    - DecisionFramework: Main class for GO/NO-GO decision logic
    - DecisionReport: Dataclass for decision results
    - Deterministic criteria evaluation
    - Risk assessment
    - Markdown report generation

Usage:
    from src.analysis.decision_framework import DecisionFramework

    framework = DecisionFramework()
    decision = framework.evaluate(
        validation_results=validation_data,
        duplicate_report=duplicate_data,
        diversity_report=diversity_data
    )

    print(f"Decision: {decision.decision}")
    print(f"Risk Level: {decision.risk_level}")

    # Generate markdown report
    markdown = decision.generate_markdown()

Author: AI Assistant
Date: 2025-11-03
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DecisionCriteria:
    """Individual decision criterion with threshold and actual value.

    Attributes:
        name: Criterion name
        threshold: Required threshold value
        actual: Actual measured value
        comparison: Comparison operator (">=", "<=", "<", ">", "==")
        passed: Whether criterion is met
        weight: Importance weight ("CRITICAL", "HIGH", "MEDIUM", "LOW")
    """
    name: str
    threshold: float
    actual: float
    comparison: str
    passed: bool
    weight: str


@dataclass
class DecisionReport:
    """Comprehensive decision report for GO/NO-GO assessment.

    Attributes:
        decision: Final decision ("GO", "CONDITIONAL_GO", "NO-GO")
        risk_level: Risk assessment ("LOW", "MEDIUM", "HIGH")
        total_strategies: Total strategies analyzed
        unique_strategies: Number of unique validated strategies
        diversity_score: Overall diversity score (0-100)
        avg_correlation: Average pairwise correlation (0-1)
        factor_diversity: Factor diversity score (0-1)
        risk_diversity: Risk profile diversity (0-1)
        validation_fixed: Whether validation framework is fixed
        execution_success_rate: Percentage of successful executions
        criteria_met: List of criteria that passed
        criteria_failed: List of criteria that failed
        warnings: List of warning messages
        recommendations: List of recommended actions
        summary: Executive summary text
    """
    decision: str
    risk_level: str
    total_strategies: int
    unique_strategies: int
    diversity_score: float
    avg_correlation: float
    factor_diversity: float
    risk_diversity: float
    validation_fixed: bool
    execution_success_rate: float
    criteria_met: List[DecisionCriteria] = field(default_factory=list)
    criteria_failed: List[DecisionCriteria] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary: str = ""

    def generate_markdown(self) -> str:
        """Generate markdown decision document.

        Returns:
            Formatted markdown report
        """
        # Determine status emoji
        status_emoji = {
            "GO": "🟢",
            "CONDITIONAL_GO": "🟡",
            "NO-GO": "🔴"
        }.get(self.decision, "⚪")

        risk_emoji = {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🔴"
        }.get(self.risk_level, "⚪")

        lines = [
            "# Phase 3 GO/NO-GO Decision Report",
            "",
            f"**Decision**: {status_emoji} **{self.decision}**",
            f"**Risk Level**: {risk_emoji} **{self.risk_level}**",
            f"**Date**: {self._get_timestamp()}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            self.summary,
            "",
            "---",
            "",
            "## Decision Criteria Evaluation",
            "",
            "### Criteria Assessment",
            "",
            "| Criterion | Threshold | Actual | Status | Weight |",
            "|-----------|-----------|--------|--------|--------|",
        ]

        # Add all criteria (met and failed)
        all_criteria = sorted(
            self.criteria_met + self.criteria_failed,
            key=lambda c: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(c.weight, 4)
        )

        for criterion in all_criteria:
            status = "✅ PASS" if criterion.passed else "❌ FAIL"
            threshold_str = self._format_threshold(criterion.threshold, criterion.comparison)
            actual_str = self._format_value(criterion.actual, criterion.name)
            lines.append(
                f"| **{criterion.name}** | {threshold_str} | {actual_str} | {status} | {criterion.weight} |"
            )

        # Pass rate
        total_criteria = len(all_criteria)
        passed_criteria = len(self.criteria_met)
        pass_rate = (passed_criteria / total_criteria * 100) if total_criteria > 0 else 0

        lines.extend([
            "",
            f"**Overall Assessment**: {passed_criteria}/{total_criteria} criteria passed ({pass_rate:.0f}%)",
            "",
            "### Decision Matrix",
            "",
            "```",
            "IF diversity_score >= 60 AND unique_strategies >= 3 AND avg_correlation < 0.8",
            "  → GO (Optimal)",
            "",
            "ELSE IF diversity_score >= 40 AND unique_strategies >= 3 AND avg_correlation < 0.8",
            "  → CONDITIONAL GO (Acceptable with monitoring)",
            "",
            "ELSE",
            "  → NO-GO (Insufficient diversity or quality)",
            "```",
            "",
            f"**Result**: {self.decision}",
            "",
            "---",
            "",
            "## Detailed Metrics",
            "",
            "### Strategy Population",
            "",
            f"- **Total Strategies**: {self.total_strategies}",
            f"- **Unique Validated Strategies**: {self.unique_strategies}",
            f"- **Validation Success Rate**: {self.execution_success_rate:.1f}%",
            "",
            "### Diversity Analysis",
            "",
            f"- **Overall Diversity Score**: {self.diversity_score:.2f}/100",
            f"- **Factor Diversity**: {self.factor_diversity:.3f}",
            f"- **Average Correlation**: {self.avg_correlation:.3f}",
            f"- **Risk Diversity**: {self.risk_diversity:.3f}",
            "",
            "### System Status",
            "",
            f"- **Validation Framework Fixed**: {'Yes ✅' if self.validation_fixed else 'No ❌'}",
            "",
        ])

        # Warnings section
        if self.warnings:
            lines.extend([
                "---",
                "",
                "## Warnings",
                "",
            ])
            for i, warning in enumerate(self.warnings, 1):
                lines.append(f"{i}. ⚠️ {warning}")
            lines.append("")

        # Recommendations section
        if self.recommendations:
            lines.extend([
                "---",
                "",
                "## Recommendations",
                "",
            ])
            for i, rec in enumerate(self.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        # Risk assessment section
        lines.extend([
            "---",
            "",
            "## Risk Assessment",
            "",
            f"**Risk Level**: {self.risk_level}",
            "",
        ])

        if self.risk_level == "HIGH":
            lines.extend([
                "**Critical Risks Identified**:",
                "",
                "- **Overfitting Risk**: Low diversity may lead to narrow pattern recognition",
                "- **Correlated Failure Risk**: Similar strategies may fail simultaneously",
                "- **Limited Learning Signal**: Insufficient variety for robust learning",
                "",
                "**Mitigation Required**: Address diversity issues before proceeding to Phase 3",
            ])
        elif self.risk_level == "MEDIUM":
            lines.extend([
                "**Moderate Risks Identified**:",
                "",
                "- **Diversity Concerns**: Marginal diversity requires close monitoring",
                "- **Quality Trade-offs**: May need to balance quality vs diversity",
                "",
                "**Mitigation Recommended**: Monitor diversity metrics during Phase 3 execution",
            ])
        else:  # LOW
            lines.extend([
                "**Low Risk Profile**:",
                "",
                "- Sufficient diversity and quality for Phase 3 progression",
                "- Validated strategies show good variety",
                "- System is operating within acceptable parameters",
            ])

        lines.extend([
            "",
            "---",
            "",
            "## Next Steps",
            "",
        ])

        if self.decision == "GO":
            lines.extend([
                "✅ **Proceed to Phase 3**",
                "",
                "1. Initiate Phase 3 learning system",
                "2. Monitor diversity metrics during execution",
                "3. Continue validation framework",
                "4. Track performance improvements",
            ])
        elif self.decision == "CONDITIONAL_GO":
            lines.extend([
                "🟡 **Conditional Proceed to Phase 3**",
                "",
                "1. Proceed with enhanced monitoring",
                "2. Implement diversity tracking dashboard",
                "3. Set up early warning alerts for diversity degradation",
                "4. Plan for mid-phase diversity assessment",
                "5. Prepare contingency plan if diversity drops further",
            ])
        else:  # NO-GO
            lines.extend([
                "🔴 **Do NOT Proceed to Phase 3**",
                "",
                "1. Analyze root cause of low diversity",
                "2. Adjust Phase 2 parameters to promote diversity",
                "3. Re-run Phase 2 with diversity-focused configuration",
                "4. Re-evaluate decision after improvements",
                "5. Target diversity score ≥ 40 (CONDITIONAL GO) or ≥ 60 (GO)",
            ])

        lines.extend([
            "",
            "---",
            "",
            f"**Generated**: {self._get_timestamp()}",
            f"**Decision Framework Version**: 1.0.0",
            "",
        ])

        return "\n".join(lines)

    def _format_threshold(self, value: float, comparison: str) -> str:
        """Format threshold value with comparison operator."""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        elif value == int(value):
            return f"{comparison}{int(value)}"
        else:
            return f"{comparison}{value:.2f}"

    def _format_value(self, value: float, name: str) -> str:
        """Format actual value based on metric type."""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        elif "success rate" in name.lower() or "percentage" in name.lower():
            return f"{value:.1f}%"
        elif value == int(value):
            return str(int(value))
        else:
            return f"{value:.3f}"

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")


class DecisionFramework:
    """GO/NO-GO decision framework for Phase 3 progression.

    Implements deterministic decision logic based on:
    - Minimum unique strategies (≥3)
    - Diversity score thresholds (≥60 for GO, ≥40 for CONDITIONAL GO)
    - Correlation threshold (<0.8)
    - Validation framework status (fixed)
    - Execution success rate (100%)

    Decision Logic:
        GO: All optimal criteria met
        CONDITIONAL GO: Minimal criteria met (diversity 40-59)
        NO-GO: Any critical criterion fails

    Example:
        >>> framework = DecisionFramework()
        >>> decision = framework.evaluate(
        ...     validation_results=validation_data,
        ...     duplicate_report=duplicate_data,
        ...     diversity_report=diversity_data
        ... )
        >>> print(f"Decision: {decision.decision}")
        >>>
        >>> # Save markdown report
        >>> with open("decision_report.md", "w") as f:
        ...     f.write(decision.generate_markdown())
    """

    # Decision thresholds
    MIN_UNIQUE_STRATEGIES = 3
    DIVERSITY_THRESHOLD_GO = 60.0
    DIVERSITY_THRESHOLD_CONDITIONAL = 40.0
    CORRELATION_THRESHOLD = 0.8
    FACTOR_DIVERSITY_THRESHOLD = 0.5
    RISK_DIVERSITY_THRESHOLD = 0.3
    EXECUTION_SUCCESS_RATE = 100.0

    def __init__(self):
        """Initialize the DecisionFramework."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def evaluate(
        self,
        validation_results: Dict[str, Any],
        duplicate_report: Dict[str, Any],
        diversity_report: Dict[str, Any]
    ) -> DecisionReport:
        """Evaluate GO/NO-GO decision based on all criteria.

        Args:
            validation_results: Validation results dict
            duplicate_report: Duplicate detection results
            diversity_report: Diversity analysis results

        Returns:
            DecisionReport with comprehensive decision analysis
        """
        self.logger.info("Starting GO/NO-GO decision evaluation...")

        # Extract metrics
        metrics = self._extract_metrics(validation_results, duplicate_report, diversity_report)

        # Check GO criteria
        go_result = self.check_go_criteria(metrics)

        # Check CONDITIONAL GO criteria if GO failed
        if not go_result["passed"]:
            conditional_result = self.check_conditional_criteria(metrics)
            if conditional_result["passed"]:
                decision = "CONDITIONAL_GO"
                criteria_met = conditional_result["criteria_met"]
                criteria_failed = conditional_result["criteria_failed"]
            else:
                decision = "NO-GO"
                criteria_met = conditional_result["criteria_met"]
                criteria_failed = conditional_result["criteria_failed"]
        else:
            decision = "GO"
            criteria_met = go_result["criteria_met"]
            criteria_failed = go_result["criteria_failed"]

        # Assess risk
        risk_level = self.assess_risk(decision, criteria_met, criteria_failed)

        # Generate warnings and recommendations
        warnings = self._generate_warnings(metrics, criteria_failed)
        recommendations = self._generate_recommendations(decision, metrics, criteria_failed)

        # Generate summary
        summary = self._generate_summary(decision, metrics, criteria_failed)

        # Create decision report
        report = DecisionReport(
            decision=decision,
            risk_level=risk_level,
            total_strategies=metrics["total_strategies"],
            unique_strategies=metrics["unique_strategies"],
            diversity_score=metrics["diversity_score"],
            avg_correlation=metrics["avg_correlation"],
            factor_diversity=metrics["factor_diversity"],
            risk_diversity=metrics["risk_diversity"],
            validation_fixed=metrics["validation_fixed"],
            execution_success_rate=metrics["execution_success_rate"],
            criteria_met=criteria_met,
            criteria_failed=criteria_failed,
            warnings=warnings,
            recommendations=recommendations,
            summary=summary
        )

        self.logger.info(f"Decision evaluation complete: {decision} (Risk: {risk_level})")
        return report

    def check_go_criteria(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Check all GO criteria (optimal case).

        Args:
            metrics: Extracted metrics dict

        Returns:
            Dict with "passed" (bool), "criteria_met" (list), "criteria_failed" (list)
        """
        criteria_met = []
        criteria_failed = []

        # Criterion 1: Minimum unique strategies
        unique_criterion = DecisionCriteria(
            name="Minimum Unique Strategies",
            threshold=self.MIN_UNIQUE_STRATEGIES,
            actual=metrics["unique_strategies"],
            comparison="≥",
            passed=metrics["unique_strategies"] >= self.MIN_UNIQUE_STRATEGIES,
            weight="CRITICAL"
        )
        if unique_criterion.passed:
            criteria_met.append(unique_criterion)
        else:
            criteria_failed.append(unique_criterion)

        # Criterion 2: Diversity score (GO threshold)
        diversity_criterion = DecisionCriteria(
            name="Diversity Score (GO)",
            threshold=self.DIVERSITY_THRESHOLD_GO,
            actual=metrics["diversity_score"],
            comparison="≥",
            passed=metrics["diversity_score"] >= self.DIVERSITY_THRESHOLD_GO,
            weight="HIGH"
        )
        if diversity_criterion.passed:
            criteria_met.append(diversity_criterion)
        else:
            criteria_failed.append(diversity_criterion)

        # Criterion 3: Average correlation
        correlation_criterion = DecisionCriteria(
            name="Average Correlation",
            threshold=self.CORRELATION_THRESHOLD,
            actual=metrics["avg_correlation"],
            comparison="<",
            passed=metrics["avg_correlation"] < self.CORRELATION_THRESHOLD,
            weight="MEDIUM"
        )
        if correlation_criterion.passed:
            criteria_met.append(correlation_criterion)
        else:
            criteria_failed.append(correlation_criterion)

        # Criterion 4: Factor diversity
        factor_criterion = DecisionCriteria(
            name="Factor Diversity",
            threshold=self.FACTOR_DIVERSITY_THRESHOLD,
            actual=metrics["factor_diversity"],
            comparison="≥",
            passed=metrics["factor_diversity"] >= self.FACTOR_DIVERSITY_THRESHOLD,
            weight="HIGH"
        )
        if factor_criterion.passed:
            criteria_met.append(factor_criterion)
        else:
            criteria_failed.append(factor_criterion)

        # Criterion 5: Risk diversity
        risk_criterion = DecisionCriteria(
            name="Risk Diversity",
            threshold=self.RISK_DIVERSITY_THRESHOLD,
            actual=metrics["risk_diversity"],
            comparison="≥",
            passed=metrics["risk_diversity"] >= self.RISK_DIVERSITY_THRESHOLD,
            weight="MEDIUM"
        )
        if risk_criterion.passed:
            criteria_met.append(risk_criterion)
        else:
            criteria_failed.append(risk_criterion)

        # Criterion 6: Validation framework fixed
        validation_criterion = DecisionCriteria(
            name="Validation Framework Fixed",
            threshold=True,
            actual=metrics["validation_fixed"],
            comparison="=",
            passed=metrics["validation_fixed"],
            weight="CRITICAL"
        )
        if validation_criterion.passed:
            criteria_met.append(validation_criterion)
        else:
            criteria_failed.append(validation_criterion)

        # Criterion 7: Execution success rate
        execution_criterion = DecisionCriteria(
            name="Execution Success Rate",
            threshold=self.EXECUTION_SUCCESS_RATE,
            actual=metrics["execution_success_rate"],
            comparison="≥",
            passed=metrics["execution_success_rate"] >= self.EXECUTION_SUCCESS_RATE,
            weight="HIGH"
        )
        if execution_criterion.passed:
            criteria_met.append(execution_criterion)
        else:
            criteria_failed.append(execution_criterion)

        # All criteria must pass for GO
        passed = len(criteria_failed) == 0

        return {
            "passed": passed,
            "criteria_met": criteria_met,
            "criteria_failed": criteria_failed
        }

    def check_conditional_criteria(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Check CONDITIONAL GO criteria (minimal acceptable case).

        Args:
            metrics: Extracted metrics dict

        Returns:
            Dict with "passed" (bool), "criteria_met" (list), "criteria_failed" (list)
        """
        criteria_met = []
        criteria_failed = []

        # Criterion 1: Minimum unique strategies (CRITICAL)
        unique_criterion = DecisionCriteria(
            name="Minimum Unique Strategies",
            threshold=self.MIN_UNIQUE_STRATEGIES,
            actual=metrics["unique_strategies"],
            comparison="≥",
            passed=metrics["unique_strategies"] >= self.MIN_UNIQUE_STRATEGIES,
            weight="CRITICAL"
        )
        if unique_criterion.passed:
            criteria_met.append(unique_criterion)
        else:
            criteria_failed.append(unique_criterion)

        # Criterion 2: Diversity score (CONDITIONAL threshold)
        diversity_criterion = DecisionCriteria(
            name="Diversity Score (CONDITIONAL)",
            threshold=self.DIVERSITY_THRESHOLD_CONDITIONAL,
            actual=metrics["diversity_score"],
            comparison="≥",
            passed=metrics["diversity_score"] >= self.DIVERSITY_THRESHOLD_CONDITIONAL,
            weight="HIGH"
        )
        if diversity_criterion.passed:
            criteria_met.append(diversity_criterion)
        else:
            criteria_failed.append(diversity_criterion)

        # Criterion 3: Average correlation (CRITICAL for CONDITIONAL)
        correlation_criterion = DecisionCriteria(
            name="Average Correlation",
            threshold=self.CORRELATION_THRESHOLD,
            actual=metrics["avg_correlation"],
            comparison="<",
            passed=metrics["avg_correlation"] < self.CORRELATION_THRESHOLD,
            weight="CRITICAL"
        )
        if correlation_criterion.passed:
            criteria_met.append(correlation_criterion)
        else:
            criteria_failed.append(correlation_criterion)

        # Criterion 4: Validation framework fixed (CRITICAL)
        validation_criterion = DecisionCriteria(
            name="Validation Framework Fixed",
            threshold=True,
            actual=metrics["validation_fixed"],
            comparison="=",
            passed=metrics["validation_fixed"],
            weight="CRITICAL"
        )
        if validation_criterion.passed:
            criteria_met.append(validation_criterion)
        else:
            criteria_failed.append(validation_criterion)

        # Criterion 5: Execution success rate (CRITICAL for CONDITIONAL)
        execution_criterion = DecisionCriteria(
            name="Execution Success Rate",
            threshold=self.EXECUTION_SUCCESS_RATE,
            actual=metrics["execution_success_rate"],
            comparison="≥",
            passed=metrics["execution_success_rate"] >= self.EXECUTION_SUCCESS_RATE,
            weight="CRITICAL"
        )
        if execution_criterion.passed:
            criteria_met.append(execution_criterion)
        else:
            criteria_failed.append(execution_criterion)

        # Additional informational criteria (not required for CONDITIONAL GO)
        factor_criterion = DecisionCriteria(
            name="Factor Diversity",
            threshold=self.FACTOR_DIVERSITY_THRESHOLD,
            actual=metrics["factor_diversity"],
            comparison="≥",
            passed=metrics["factor_diversity"] >= self.FACTOR_DIVERSITY_THRESHOLD,
            weight="MEDIUM"
        )
        if factor_criterion.passed:
            criteria_met.append(factor_criterion)
        else:
            criteria_failed.append(factor_criterion)

        risk_criterion = DecisionCriteria(
            name="Risk Diversity",
            threshold=self.RISK_DIVERSITY_THRESHOLD,
            actual=metrics["risk_diversity"],
            comparison="≥",
            passed=metrics["risk_diversity"] >= self.RISK_DIVERSITY_THRESHOLD,
            weight="LOW"
        )
        if risk_criterion.passed:
            criteria_met.append(risk_criterion)
        else:
            criteria_failed.append(risk_criterion)

        # All CRITICAL criteria must pass for CONDITIONAL GO
        critical_failed = [c for c in criteria_failed if c.weight == "CRITICAL"]
        passed = len(critical_failed) == 0

        return {
            "passed": passed,
            "criteria_met": criteria_met,
            "criteria_failed": criteria_failed
        }

    def assess_risk(
        self,
        decision: str,
        criteria_met: List[DecisionCriteria],
        criteria_failed: List[DecisionCriteria]
    ) -> str:
        """Assess risk level based on decision and criteria.

        Args:
            decision: Decision result ("GO", "CONDITIONAL_GO", "NO-GO")
            criteria_met: List of criteria that passed
            criteria_failed: List of criteria that failed

        Returns:
            Risk level ("LOW", "MEDIUM", "HIGH")
        """
        if decision == "NO-GO":
            return "HIGH"

        if decision == "CONDITIONAL_GO":
            # Check how many HIGH/CRITICAL criteria failed
            high_priority_failed = [
                c for c in criteria_failed
                if c.weight in ("CRITICAL", "HIGH")
            ]
            if len(high_priority_failed) >= 2:
                return "MEDIUM"
            else:
                return "MEDIUM"  # CONDITIONAL GO is always at least MEDIUM risk

        # GO decision
        if len(criteria_failed) == 0:
            return "LOW"
        else:
            # Some non-critical criteria failed
            return "LOW"

    def _extract_metrics(
        self,
        validation_results: Dict[str, Any],
        duplicate_report: Dict[str, Any],
        diversity_report: Dict[str, Any]
    ) -> Dict[str, float]:
        """Extract metrics from input data.

        Args:
            validation_results: Validation results dict
            duplicate_report: Duplicate detection results
            diversity_report: Diversity analysis results

        Returns:
            Dict of extracted metrics
        """
        # Extract from diversity report
        total_strategies = diversity_report.get("total_strategies", 0)
        diversity_score = diversity_report.get("diversity_score", 0.0)
        avg_correlation = diversity_report.get("avg_correlation", 1.0)
        factor_diversity = diversity_report.get("factor_diversity", 0.0)
        risk_diversity = diversity_report.get("risk_diversity", 0.0)

        # Calculate unique strategies (total - duplicates)
        duplicate_groups = duplicate_report.get("duplicate_groups", [])
        duplicate_count = sum(
            len(group.get("strategies", [])) - 1
            for group in duplicate_groups
        )
        unique_strategies = max(0, total_strategies - duplicate_count)

        # Check validation framework status
        # Assume fixed if Bonferroni threshold is correct (0.5)
        validation_fixed = validation_results.get("validation_statistics", {}).get("bonferroni_threshold", 0.0) == 0.5

        # Calculate execution success rate
        # Read directly from metrics (more reliable than counting strategies)
        execution_success_rate = validation_results.get("metrics", {}).get("execution_success_rate", 0.0) * 100

        # Fallback: count successful strategies if metrics not available
        if execution_success_rate == 0.0:
            strategies_validation = validation_results.get("strategies_validation", [])
            summary = validation_results.get("summary", {})
            successful = summary.get("successful", 0)
            total = summary.get("total", len(strategies_validation))
            if total > 0:
                execution_success_rate = (successful / total) * 100
            else:
                execution_success_rate = 100.0  # Default to 100% if no data

        return {
            "total_strategies": total_strategies,
            "unique_strategies": unique_strategies,
            "diversity_score": diversity_score,
            "avg_correlation": avg_correlation,
            "factor_diversity": factor_diversity,
            "risk_diversity": risk_diversity,
            "validation_fixed": validation_fixed,
            "execution_success_rate": execution_success_rate
        }

    def _generate_warnings(
        self,
        metrics: Dict[str, float],
        criteria_failed: List[DecisionCriteria]
    ) -> List[str]:
        """Generate warning messages based on failed criteria.

        Args:
            metrics: Extracted metrics dict
            criteria_failed: List of failed criteria

        Returns:
            List of warning messages
        """
        warnings = []

        for criterion in criteria_failed:
            if criterion.name == "Diversity Score (GO)":
                warnings.append(
                    f"Diversity score {metrics['diversity_score']:.1f}/100 is below "
                    f"optimal threshold ({self.DIVERSITY_THRESHOLD_GO})"
                )
            elif criterion.name == "Diversity Score (CONDITIONAL)":
                warnings.append(
                    f"Diversity score {metrics['diversity_score']:.1f}/100 is below "
                    f"minimum threshold ({self.DIVERSITY_THRESHOLD_CONDITIONAL})"
                )
            elif criterion.name == "Factor Diversity":
                warnings.append(
                    f"Low factor diversity detected: {metrics['factor_diversity']:.3f} < "
                    f"{self.FACTOR_DIVERSITY_THRESHOLD}"
                )
            elif criterion.name == "Risk Diversity":
                warnings.append(
                    f"Low risk diversity detected: {metrics['risk_diversity']:.3f} < "
                    f"{self.RISK_DIVERSITY_THRESHOLD}"
                )
            elif criterion.name == "Average Correlation":
                warnings.append(
                    f"High correlation detected: {metrics['avg_correlation']:.3f} > "
                    f"{self.CORRELATION_THRESHOLD}"
                )
            elif criterion.name == "Minimum Unique Strategies":
                warnings.append(
                    f"Insufficient unique strategies: {metrics['unique_strategies']} < "
                    f"{self.MIN_UNIQUE_STRATEGIES}"
                )
            elif criterion.name == "Validation Framework Fixed":
                warnings.append("Validation framework is not properly fixed")
            elif criterion.name == "Execution Success Rate":
                warnings.append(
                    f"Execution success rate below 100%: {metrics['execution_success_rate']:.1f}%"
                )

        return warnings

    def _generate_recommendations(
        self,
        decision: str,
        metrics: Dict[str, float],
        criteria_failed: List[DecisionCriteria]
    ) -> List[str]:
        """Generate recommendations based on decision and failed criteria.

        Args:
            decision: Decision result
            metrics: Extracted metrics dict
            criteria_failed: List of failed criteria

        Returns:
            List of recommendations
        """
        recommendations = []

        if decision == "NO-GO":
            recommendations.append(
                "**PRIMARY ACTION**: Do not proceed to Phase 3 until diversity issues are resolved"
            )

            if metrics["diversity_score"] < self.DIVERSITY_THRESHOLD_CONDITIONAL:
                recommendations.append(
                    "Increase diversity by adjusting Phase 2 mutation parameters to explore "
                    "more diverse strategy patterns"
                )

            if metrics["factor_diversity"] < self.FACTOR_DIVERSITY_THRESHOLD:
                recommendations.append(
                    "Promote factor diversity by ensuring mutations explore different factor "
                    "combinations more aggressively"
                )

            if metrics["unique_strategies"] < self.MIN_UNIQUE_STRATEGIES:
                recommendations.append(
                    "Increase population size or adjust validation thresholds to retain more "
                    "unique validated strategies"
                )

            recommendations.append(
                "Re-run Phase 2 with diversity-focused configuration, targeting diversity "
                f"score ≥ {self.DIVERSITY_THRESHOLD_CONDITIONAL}"
            )

        elif decision == "CONDITIONAL_GO":
            recommendations.append(
                "**PRIMARY ACTION**: Proceed to Phase 3 with enhanced diversity monitoring"
            )
            recommendations.append(
                "Implement real-time diversity tracking dashboard to detect degradation early"
            )
            recommendations.append(
                "Set up alerts if diversity score drops below 35/100 during Phase 3 execution"
            )

            if metrics["diversity_score"] < 50:
                recommendations.append(
                    "Consider increasing mutation diversity rates to improve variety during Phase 3"
                )

        else:  # GO
            recommendations.append(
                "**PRIMARY ACTION**: Proceed to Phase 3 with standard monitoring"
            )
            recommendations.append(
                "Continue tracking diversity metrics to ensure sustained quality"
            )
            recommendations.append(
                "Maintain current mutation and validation parameters"
            )

        return recommendations

    def _generate_summary(
        self,
        decision: str,
        metrics: Dict[str, float],
        criteria_failed: List[DecisionCriteria]
    ) -> str:
        """Generate executive summary text.

        Args:
            decision: Decision result
            metrics: Extracted metrics dict
            criteria_failed: List of failed criteria

        Returns:
            Summary text
        """
        if decision == "GO":
            return (
                f"After comprehensive evaluation of {metrics['total_strategies']} strategies "
                f"({metrics['unique_strategies']} unique), the system meets all GO criteria. "
                f"Diversity score of {metrics['diversity_score']:.1f}/100 exceeds the optimal "
                f"threshold ({self.DIVERSITY_THRESHOLD_GO}), correlation is acceptable "
                f"({metrics['avg_correlation']:.3f} < {self.CORRELATION_THRESHOLD}), and "
                f"validation framework is properly configured. **Phase 3 is approved for "
                f"immediate progression.**"
            )
        elif decision == "CONDITIONAL_GO":
            return (
                f"After comprehensive evaluation of {metrics['total_strategies']} strategies "
                f"({metrics['unique_strategies']} unique), the system meets minimum criteria "
                f"for conditional progression. Diversity score of {metrics['diversity_score']:.1f}/100 "
                f"meets the conditional threshold ({self.DIVERSITY_THRESHOLD_CONDITIONAL}) but "
                f"falls below optimal ({self.DIVERSITY_THRESHOLD_GO}). **Phase 3 progression "
                f"is approved with enhanced monitoring and diversity tracking requirements.**"
            )
        else:  # NO-GO
            failed_critical = [c for c in criteria_failed if c.weight == "CRITICAL"]
            failed_high = [c for c in criteria_failed if c.weight == "HIGH"]

            primary_issue = "diversity insufficient" if metrics["diversity_score"] < self.DIVERSITY_THRESHOLD_CONDITIONAL else "critical criteria not met"

            return (
                f"After comprehensive evaluation of {metrics['total_strategies']} strategies "
                f"({metrics['unique_strategies']} unique), the system does not meet minimum "
                f"criteria for Phase 3 progression. Diversity score of {metrics['diversity_score']:.1f}/100 "
                f"is below the minimum threshold ({self.DIVERSITY_THRESHOLD_CONDITIONAL}). "
                f"{len(failed_critical)} critical criteria and {len(failed_high)} high-priority "
                f"criteria failed. **Phase 3 is NOT approved.** Primary issue: {primary_issue}."
            )

    def generate_decision_document(
        self,
        decision_report: DecisionReport,
        output_path: str
    ) -> None:
        """Generate and save markdown decision document to file.

        Args:
            decision_report: DecisionReport instance
            output_path: Path to save markdown document
        """
        markdown = decision_report.generate_markdown()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)

        self.logger.info(f"Decision document saved to {output_path}")


__all__ = [
    "DecisionFramework",
    "DecisionReport",
    "DecisionCriteria"
]
