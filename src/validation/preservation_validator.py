"""Preservation Validator for Enhanced Champion Preservation.

This module provides PreservationValidator to validate champion preservation
with behavioral similarity checks beyond parameter matching.

Requirements: F2.1 (behavioral checks), F2.2 (false positive detection), F2.3 (preservation reports)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd


@dataclass
class BehavioralCheck:
    """Single behavioral similarity check result."""
    check_name: str  # "sharpe_similarity", "turnover_similarity", etc.
    passed: bool
    champion_value: float
    generated_value: float
    threshold: float
    deviation_pct: float
    reason: str


@dataclass
class PreservationReport:
    """Detailed preservation validation report."""
    is_preserved: bool

    # Parameter preservation
    parameter_checks: Dict[str, Tuple[bool, str]]  # {param: (passed, reason)}
    critical_params_preserved: List[str]
    missing_params: List[str]

    # Behavioral similarity
    behavioral_checks: List[BehavioralCheck]
    behavioral_similarity_score: float  # 0.0-1.0

    # False positive detection
    false_positive_risk: float  # 0.0-1.0 risk score
    false_positive_indicators: List[str]

    # Recommendations
    recommendations: List[str]  # Actionable guidance
    requires_manual_review: bool

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def summary(self) -> str:
        """Human-readable summary."""
        status = "✅ PRESERVED" if self.is_preserved else "❌ NOT PRESERVED"
        param_status = f"{len([p for p, (passed, _) in self.parameter_checks.items() if passed])}/{len(self.parameter_checks)} params"
        behavioral_status = f"similarity {self.behavioral_similarity_score:.2%}"
        return f"{status} | {param_status} | {behavioral_status}"


class PreservationValidator:
    """Validate champion preservation with behavioral similarity checks.

    Enhanced preservation validation that checks both parameter preservation
    and behavioral similarity to reduce false positives and detect meaningful
    preservation violations.

    Attributes:
        sharpe_tolerance: Maximum allowed deviation for Sharpe ratio (default ±10%)
        turnover_tolerance: Maximum allowed deviation for turnover (default ±20%)
        concentration_tolerance: Maximum allowed change in concentration (default ±15%)
    """

    def __init__(
        self,
        sharpe_tolerance: float = 0.10,
        turnover_tolerance: float = 0.20,
        concentration_tolerance: float = 0.15
    ):
        """Initialize PreservationValidator with tolerance thresholds.

        Args:
            sharpe_tolerance: Sharpe ratio deviation tolerance (default 0.10 = ±10%)
            turnover_tolerance: Portfolio turnover tolerance (default 0.20 = ±20%)
            concentration_tolerance: Position concentration tolerance (default 0.15 = ±15%)
        """
        self.sharpe_tolerance = sharpe_tolerance
        self.turnover_tolerance = turnover_tolerance
        self.concentration_tolerance = concentration_tolerance

    def validate_preservation(
        self,
        generated_code: str,
        champion: Any,  # ChampionStrategy from autonomous_loop.py
        execution_metrics: Optional[Dict[str, float]] = None
    ) -> Tuple[bool, PreservationReport]:
        """Enhanced preservation validation with behavioral checks.

        Args:
            generated_code: LLM-generated code to validate
            champion: Current champion strategy
            execution_metrics: Optional runtime metrics for behavioral validation

        Returns:
            (is_preserved, PreservationReport)

        Validation report includes:
        - parameter_preservation: Critical params maintained
        - behavioral_similarity: Performance within ±10%, turnover within ±20%
        - position_patterns: Concentration patterns maintained
        - false_positive_indicators: Flags potential false positives
        """
        from artifacts.working.modules.performance_attributor import extract_strategy_params

        parameter_checks = {}
        critical_params_preserved = []
        missing_params = []
        behavioral_checks = []
        behavioral_similarity_score = 0.0
        false_positive_indicators = []
        recommendations = []

        # Step 1: Extract parameters from generated code
        try:
            generated_params = extract_strategy_params(generated_code)
        except Exception as e:
            report = PreservationReport(
                is_preserved=False,
                parameter_checks={'extraction_error': (False, f"Failed to extract params: {e}")},
                critical_params_preserved=[],
                missing_params=[],
                behavioral_checks=[],
                behavioral_similarity_score=0.0,
                false_positive_risk=1.0,
                false_positive_indicators=[f"Parameter extraction failed: {e}"],
                recommendations=["Fix code structure to enable parameter extraction"],
                requires_manual_review=True
            )
            return (False, report)

        champion_params = champion.parameters

        # Step 2: Check parameter preservation
        # Critical Check 1: ROE Type Preservation
        champ_roe_type = champion_params.get('roe_type')
        gen_roe_type = generated_params.get('roe_type')

        if champ_roe_type == 'smoothed':
            if gen_roe_type == 'smoothed':
                # Check smoothing window (allow ±20% variation)
                champ_window = champion_params.get('roe_smoothing_window', 1)
                gen_window = generated_params.get('roe_smoothing_window', 1)

                if champ_window > 0:
                    window_deviation = abs(gen_window - champ_window) / champ_window

                    if window_deviation <= 0.2:
                        parameter_checks['roe_smoothing'] = (True, f"Window preserved: {gen_window} (within ±20%)")
                        critical_params_preserved.append('roe_smoothing')
                    else:
                        parameter_checks['roe_smoothing'] = (False, f"Window changed by {window_deviation*100:.1f}%: {champ_window} → {gen_window}")
                else:
                    parameter_checks['roe_smoothing'] = (True, "Window preserved")
                    critical_params_preserved.append('roe_smoothing')
            else:
                parameter_checks['roe_type'] = (False, f"ROE type changed: {champ_roe_type} → {gen_roe_type}")
                missing_params.append('roe_smoothing')
        else:
            parameter_checks['roe_type'] = (True, f"ROE type preserved: {gen_roe_type}")

        # Critical Check 2: Liquidity Threshold Preservation (≥80% of champion)
        champ_liq = champion_params.get('liquidity_threshold')
        gen_liq = generated_params.get('liquidity_threshold')

        if champ_liq and champ_liq > 0:
            if gen_liq:
                if gen_liq >= champ_liq * 0.8:
                    parameter_checks['liquidity_threshold'] = (True, f"Threshold preserved: {gen_liq:,} (≥80% of {champ_liq:,})")
                    critical_params_preserved.append('liquidity_threshold')
                else:
                    threshold_reduction = (1 - gen_liq / champ_liq) * 100
                    parameter_checks['liquidity_threshold'] = (False, f"Threshold relaxed by {threshold_reduction:.1f}%: {champ_liq:,} → {gen_liq:,}")
            else:
                parameter_checks['liquidity_threshold'] = (False, f"Liquidity filter removed (champion had {champ_liq:,})")
                missing_params.append('liquidity_threshold')
        else:
            parameter_checks['liquidity_threshold'] = (True, "No liquidity filter in champion")

        # Step 3: Check behavioral similarity (if metrics provided)
        if execution_metrics:
            is_similar, deviation_details = self.check_behavioral_similarity(
                champion_metrics=champion.metrics,
                generated_metrics=execution_metrics,
                champion_positions=None,  # Not available yet
                generated_positions=None
            )

            # Convert deviation details to BehavioralCheck objects
            if 'sharpe_status' in deviation_details:
                behavioral_checks.append(BehavioralCheck(
                    check_name='sharpe_similarity',
                    passed='sharpe_similarity' in deviation_details.get('checks_passed', []),
                    champion_value=champion.metrics.get('sharpe_ratio', 0),
                    generated_value=execution_metrics.get('sharpe_ratio', 0),
                    threshold=self.sharpe_tolerance,
                    deviation_pct=float(deviation_details.get('sharpe_deviation_pct', '0').rstrip('%')),
                    reason=deviation_details['sharpe_status']
                ))

            # Calculate behavioral similarity score (0.0-1.0)
            checks_passed = deviation_details.get('checks_passed', [])
            checks_total = len(checks_passed) + len(deviation_details.get('checks_failed', []))
            if checks_total > 0:
                behavioral_similarity_score = len(checks_passed) / checks_total
            else:
                behavioral_similarity_score = 0.0
        else:
            behavioral_similarity_score = 0.5  # Neutral score when no metrics

        # Step 4: Calculate false positive risk
        # High risk if parameters pass but behavioral checks fail
        param_pass_count = sum(1 for passed, _ in parameter_checks.values() if passed)
        param_total = len(parameter_checks)
        param_score = param_pass_count / param_total if param_total > 0 else 0

        # Agreement: both high or both low = low risk, mismatch = high risk
        if execution_metrics:
            if param_score > 0.8 and behavioral_similarity_score < 0.5:
                false_positive_risk = 0.8
                false_positive_indicators.append("Parameters preserved but behavioral similarity low")
            elif param_score < 0.5 and behavioral_similarity_score > 0.8:
                false_positive_risk = 0.7
                false_positive_indicators.append("Parameters changed but behavior still similar")
            else:
                false_positive_risk = max(0, 1.0 - min(param_score, behavioral_similarity_score))
        else:
            # No behavioral data - rely on parameters only
            false_positive_risk = 1.0 - param_score

        # Step 5: Generate recommendations
        if len(missing_params) > 0:
            recommendations.append(f"Restore missing critical parameters: {', '.join(missing_params)}")

        failed_params = [name for name, (passed, _) in parameter_checks.items() if not passed]
        if failed_params:
            recommendations.append(f"Fix parameter violations: {', '.join(failed_params)}")

        if execution_metrics and behavioral_similarity_score < 0.7:
            recommendations.append("Behavioral deviation detected - verify strategy logic alignment")

        if false_positive_risk > 0.5:
            recommendations.append("High false positive risk - manual review recommended")

        # Step 6: Determine overall preservation status
        critical_params_ok = len(missing_params) == 0 and all(
            passed for name, (passed, _) in parameter_checks.items()
            if name in ['roe_type', 'roe_smoothing', 'liquidity_threshold']
        )

        behavioral_ok = (not execution_metrics) or (behavioral_similarity_score >= 0.7)

        is_preserved = critical_params_ok and behavioral_ok

        # Build report
        report = PreservationReport(
            is_preserved=is_preserved,
            parameter_checks=parameter_checks,
            critical_params_preserved=critical_params_preserved,
            missing_params=missing_params,
            behavioral_checks=behavioral_checks,
            behavioral_similarity_score=behavioral_similarity_score,
            false_positive_risk=false_positive_risk,
            false_positive_indicators=false_positive_indicators,
            recommendations=recommendations,
            requires_manual_review=(false_positive_risk > 0.7 or not is_preserved)
        )

        return (is_preserved, report)

    def check_behavioral_similarity(
        self,
        champion_metrics: Dict[str, float],
        generated_metrics: Dict[str, float],
        champion_positions: Optional[pd.DataFrame] = None,
        generated_positions: Optional[pd.DataFrame] = None
    ) -> Tuple[bool, Dict[str, str]]:
        """Check behavioral similarity beyond just metrics.

        Checks:
        - Sharpe within ±10%
        - Portfolio turnover within ±20%
        - Position concentration patterns maintained

        Args:
            champion_metrics: Champion strategy metrics
            generated_metrics: Generated strategy metrics
            champion_positions: Champion position DataFrame (optional)
            generated_positions: Generated position DataFrame (optional)

        Returns:
            (is_similar, deviation_details)
        """
        deviation_details = {}
        checks_passed = []
        checks_failed = []

        # Check 1: Sharpe Ratio Similarity (±10%)
        champ_sharpe = champion_metrics.get('sharpe_ratio', 0)
        gen_sharpe = generated_metrics.get('sharpe_ratio', 0)

        if champ_sharpe > 0:
            sharpe_deviation = abs(gen_sharpe - champ_sharpe) / champ_sharpe

            if sharpe_deviation <= self.sharpe_tolerance:
                checks_passed.append('sharpe_similarity')
                deviation_details['sharpe_status'] = f"✅ Within ±{self.sharpe_tolerance*100:.0f}% ({sharpe_deviation*100:.1f}%)"
            else:
                checks_failed.append('sharpe_similarity')
                deviation_details['sharpe_status'] = f"❌ Exceeds ±{self.sharpe_tolerance*100:.0f}% ({sharpe_deviation*100:.1f}%)"

            deviation_details['sharpe_deviation_pct'] = f"{sharpe_deviation*100:.1f}%"
        else:
            deviation_details['sharpe_status'] = "⚠️ Champion Sharpe is zero"

        # Check 2: Portfolio Turnover Similarity (±20%)
        # Calculate turnover from positions if available
        if champion_positions is not None and generated_positions is not None:
            try:
                champ_turnover = self._calculate_turnover(champion_positions)
                gen_turnover = self._calculate_turnover(generated_positions)

                if champ_turnover > 0:
                    turnover_deviation = abs(gen_turnover - champ_turnover) / champ_turnover

                    if turnover_deviation <= self.turnover_tolerance:
                        checks_passed.append('turnover_similarity')
                        deviation_details['turnover_status'] = f"✅ Within ±{self.turnover_tolerance*100:.0f}% ({turnover_deviation*100:.1f}%)"
                    else:
                        checks_failed.append('turnover_similarity')
                        deviation_details['turnover_status'] = f"❌ Exceeds ±{self.turnover_tolerance*100:.0f}% ({turnover_deviation*100:.1f}%)"

                    deviation_details['turnover_deviation_pct'] = f"{turnover_deviation*100:.1f}%"
                else:
                    deviation_details['turnover_status'] = "⚠️ Champion turnover is zero"
            except Exception as e:
                deviation_details['turnover_status'] = f"⚠️ Turnover calculation failed: {e}"
        else:
            deviation_details['turnover_status'] = "ℹ️ Position data not available"

        # Check 3: Position Concentration Patterns (±15%)
        if champion_positions is not None and generated_positions is not None:
            try:
                champ_concentration = self._calculate_concentration(champion_positions)
                gen_concentration = self._calculate_concentration(generated_positions)

                if champ_concentration > 0:
                    concentration_deviation = abs(gen_concentration - champ_concentration) / champ_concentration

                    if concentration_deviation <= self.concentration_tolerance:
                        checks_passed.append('concentration_similarity')
                        deviation_details['concentration_status'] = f"✅ Within ±{self.concentration_tolerance*100:.0f}% ({concentration_deviation*100:.1f}%)"
                    else:
                        checks_failed.append('concentration_similarity')
                        deviation_details['concentration_status'] = f"❌ Exceeds ±{self.concentration_tolerance*100:.0f}% ({concentration_deviation*100:.1f}%)"

                    deviation_details['concentration_deviation_pct'] = f"{concentration_deviation*100:.1f}%"
                else:
                    deviation_details['concentration_status'] = "⚠️ Champion concentration is zero"
            except Exception as e:
                deviation_details['concentration_status'] = f"⚠️ Concentration calculation failed: {e}"
        else:
            deviation_details['concentration_status'] = "ℹ️ Position data not available"

        # Overall similarity: at least Sharpe must pass
        is_similar = 'sharpe_similarity' in checks_passed and len(checks_failed) == 0

        deviation_details['checks_passed'] = checks_passed
        deviation_details['checks_failed'] = checks_failed

        return (is_similar, deviation_details)

    def _calculate_turnover(self, positions: pd.DataFrame) -> float:
        """Calculate portfolio turnover from positions DataFrame.

        Turnover = sum of absolute position changes between periods.

        Args:
            positions: DataFrame with position weights over time

        Returns:
            Average turnover rate (0.0-1.0+)
        """
        if positions.empty or len(positions) < 2:
            return 0.0

        # Calculate position changes
        position_changes = positions.diff().abs()

        # Sum changes per period and take mean
        turnover = position_changes.sum(axis=1).mean()

        return turnover

    def _calculate_concentration(self, positions: pd.DataFrame) -> float:
        """Calculate position concentration (Herfindahl index).

        Concentration = sum of squared position weights.
        Higher values indicate more concentrated portfolios.

        Args:
            positions: DataFrame with position weights over time

        Returns:
            Average concentration index (0.0-1.0)
        """
        if positions.empty:
            return 0.0

        # Calculate squared weights
        squared_weights = positions ** 2

        # Sum per period and take mean
        concentration = squared_weights.sum(axis=1).mean()

        return concentration
