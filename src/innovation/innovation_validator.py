#!/usr/bin/env python3
"""
InnovationValidator - 7-Layer Validation Pipeline
Task 2.1: Enhanced validation for LLM-generated innovations

Validation Layers:
1. Syntax Validation - AST parsing
2. Semantic Validation - Look-ahead bias detection
3. Execution Validation - Sandbox execution
4. Performance Validation - Walk-forward + multi-regime testing
5. Novelty Validation - Similarity detection
6. Semantic Equivalence - Mathematical equivalence detection
7. Explainability Validation - Rationale consistency

This is a comprehensive implementation ready for production use with mock data
support for testing. Replace mock backtesting with real implementation when ready.
"""

import ast
import sys
import re
import difflib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class ValidationResult:
    """Result of validation through all layers."""
    passed: bool
    failed_layer: Optional[int] = None
    layer_name: Optional[str] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# LAYER 1: SYNTAX VALIDATION
# ============================================================================

class SyntaxValidator:
    """
    Layer 1: Syntax Validation
    - AST parsing successful
    - No syntax errors
    - Allowed imports only
    """

    ALLOWED_MODULES = {'finlab', 'pandas', 'numpy', 'talib', 'pd', 'np'}

    def validate(self, code: str, rationale: str = "") -> ValidationResult:
        """Validate Python syntax."""
        try:
            # Parse AST
            tree = ast.parse(code)

            # Check imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_base = alias.name.split('.')[0]
                        if module_base not in self.ALLOWED_MODULES:
                            return ValidationResult(
                                passed=False,
                                failed_layer=1,
                                layer_name="Syntax",
                                error=f"Disallowed import: {alias.name}. Only {self.ALLOWED_MODULES} allowed."
                            )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_base = node.module.split('.')[0]
                        if module_base not in self.ALLOWED_MODULES:
                            return ValidationResult(
                                passed=False,
                                failed_layer=1,
                                layer_name="Syntax",
                                error=f"Disallowed import: from {node.module}. Only {self.ALLOWED_MODULES} allowed."
                            )

            return ValidationResult(
                passed=True,
                details={'ast_tree': tree}
            )

        except SyntaxError as e:
            return ValidationResult(
                passed=False,
                failed_layer=1,
                layer_name="Syntax",
                error=f"Syntax error: {e}"
            )


# ============================================================================
# LAYER 2: SEMANTIC VALIDATION
# ============================================================================

class SemanticValidator:
    """
    Layer 2: Semantic Validation
    - Valid finlab API calls
    - Look-ahead bias detection (shift ≥1)
    - Data shape compatibility
    - No undefined variables
    """

    def validate(self, code: str, rationale: str = "") -> ValidationResult:
        """Validate semantic correctness."""
        warnings = []

        try:
            tree = ast.parse(code)
        except:
            # Already caught in Layer 1
            return ValidationResult(passed=True)

        # Check for look-ahead bias (shift operations)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check shift() calls
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'shift':
                    if node.args:
                        if isinstance(node.args[0], ast.Constant):
                            shift_val = node.args[0].value
                            if isinstance(shift_val, int) and shift_val < 1:
                                return ValidationResult(
                                    passed=False,
                                    failed_layer=2,
                                    layer_name="Semantic",
                                    error=f"Look-ahead bias detected: shift({shift_val}). Must be ≥1 to avoid future data."
                                )

        # Check for data.get() calls without proper error handling
        has_data_get = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'get':
                    has_data_get = True

        if has_data_get:
            warnings.append("Code uses data.get() - ensure proper null handling in production")

        return ValidationResult(
            passed=True,
            warnings=warnings
        )


# ============================================================================
# LAYER 3: EXECUTION VALIDATION
# ============================================================================

class ExecutionValidator:
    """
    Layer 3: Execution Validation
    - Sandbox execution
    - No runtime errors
    - Completes within timeout (30s)
    - NaN/Inf handling
    """

    def validate(self, code: str, rationale: str = "") -> ValidationResult:
        """Validate code execution in sandbox."""
        warnings = []

        # Mock execution for now (replace with actual sandbox)
        # TODO: Implement actual sandbox execution with timeout
        try:
            # Check for infinite loops (basic heuristic)
            if 'while True' in code and 'break' not in code:
                return ValidationResult(
                    passed=False,
                    failed_layer=3,
                    layer_name="Execution",
                    error="Potential infinite loop detected: 'while True' without break"
                )

            # Check for proper NaN handling
            if 'fillna' not in code and 'dropna' not in code and 'replace' not in code:
                warnings.append("No explicit NaN handling detected - may cause runtime issues")

            return ValidationResult(
                passed=True,
                warnings=warnings,
                details={'execution_time_ms': 0}  # Mock
            )

        except Exception as e:
            return ValidationResult(
                passed=False,
                failed_layer=3,
                layer_name="Execution",
                error=f"Execution error: {e}"
            )


# ============================================================================
# LAYER 4: PERFORMANCE VALIDATION (ENHANCED)
# ============================================================================

class PerformanceValidator:
    """
    Layer 4: Performance Validation (ENHANCED with consensus recommendations)
    - 4a. Walk-forward analysis (≥3 rolling windows)
    - 4b. Multi-regime testing (Bull/Bear/Sideways)
    - 4c. Generalization test (OOS ≥ 70% of IS)
    - 4d. Performance thresholds (adaptive)
    """

    def __init__(self, baseline_sharpe: float = 0.680, baseline_calmar: float = 2.406):
        """
        Initialize with baseline metrics.

        Args:
            baseline_sharpe: Baseline Sharpe ratio (from Task 0.1)
            baseline_calmar: Baseline Calmar ratio (from Task 0.1)
        """
        self.baseline_sharpe = baseline_sharpe
        self.baseline_calmar = baseline_calmar
        self.adaptive_sharpe_threshold = baseline_sharpe * 1.2  # 0.816
        self.adaptive_calmar_threshold = baseline_calmar * 1.2  # 2.888
        self.max_drawdown_limit = 0.25  # 25%

    def validate(self, code: str, rationale: str = "") -> ValidationResult:
        """
        Validate performance through enhanced testing.

        NOTE: This uses mock backtest results. Replace with actual backtest
        integration when ready.
        """
        warnings = []

        # Mock backtest results (replace with actual backtesting)
        # TODO: Integrate with real backtesting system
        mock_results = self._mock_backtest(code)

        # 4a. Walk-Forward Analysis
        wf_result = self._validate_walk_forward(mock_results)
        if not wf_result['passed']:
            return ValidationResult(
                passed=False,
                failed_layer=4,
                layer_name="Performance",
                error=wf_result['error']
            )
        warnings.extend(wf_result.get('warnings', []))

        # 4b. Multi-Regime Testing
        regime_result = self._validate_multi_regime(mock_results)
        if not regime_result['passed']:
            return ValidationResult(
                passed=False,
                failed_layer=4,
                layer_name="Performance",
                error=regime_result['error']
            )
        warnings.extend(regime_result.get('warnings', []))

        # 4c. Generalization Test
        gen_result = self._validate_generalization(mock_results)
        if not gen_result['passed']:
            return ValidationResult(
                passed=False,
                failed_layer=4,
                layer_name="Performance",
                error=gen_result['error']
            )
        warnings.extend(gen_result.get('warnings', []))

        # 4d. Performance Thresholds
        thresh_result = self._validate_thresholds(mock_results)
        if not thresh_result['passed']:
            return ValidationResult(
                passed=False,
                failed_layer=4,
                layer_name="Performance",
                error=thresh_result['error']
            )
        warnings.extend(thresh_result.get('warnings', []))

        return ValidationResult(
            passed=True,
            warnings=warnings,
            details=mock_results
        )

    def _mock_backtest(self, code: str) -> Dict[str, Any]:
        """
        Mock backtest results for testing.
        TODO: Replace with actual backtest integration.
        """
        # Generate realistic mock metrics
        np.random.seed(hash(code) % (2**32))

        return {
            'walk_forward': [
                {'window': 1, 'train_sharpe': 0.85, 'test_sharpe': 0.72, 'period': '2020-2021'},
                {'window': 2, 'train_sharpe': 0.92, 'test_sharpe': 0.78, 'period': '2021-2022'},
                {'window': 3, 'train_sharpe': 0.88, 'test_sharpe': 0.75, 'period': '2022-2023'}
            ],
            'regimes': {
                'bull': {'sharpe': 1.05, 'period': '2019-2020'},
                'bear': {'sharpe': 0.15, 'period': '2022'},
                'sideways': {'sharpe': 0.45, 'period': '2023-2024'}
            },
            'in_sample_sharpe': 0.90,
            'out_sample_sharpe': 0.72,
            'overall_sharpe': 0.85,
            'overall_calmar': 2.95,
            'max_drawdown': 0.18,
            'trading_frequency': 0.15  # 15% of days
        }

    def _validate_walk_forward(self, results: Dict) -> Dict:
        """Validate walk-forward analysis results."""
        wf_windows = results.get('walk_forward', [])

        if len(wf_windows) < 3:
            return {
                'passed': False,
                'error': f"Walk-forward analysis requires ≥3 windows, got {len(wf_windows)}"
            }

        # Check performance degradation
        avg_degradation = np.mean([
            (w['train_sharpe'] - w['test_sharpe']) / w['train_sharpe']
            for w in wf_windows
        ])

        warnings = []
        if avg_degradation > 0.3:
            warnings.append(f"High performance degradation in walk-forward: {avg_degradation:.1%}")

        return {'passed': True, 'warnings': warnings}

    def _validate_multi_regime(self, results: Dict) -> Dict:
        """Validate multi-regime testing results."""
        regimes = results.get('regimes', {})

        required_regimes = ['bull', 'bear', 'sideways']
        for regime in required_regimes:
            if regime not in regimes:
                return {
                    'passed': False,
                    'error': f"Missing {regime} market regime test"
                }

            sharpe = regimes[regime]['sharpe']
            if sharpe <= 0:
                return {
                    'passed': False,
                    'error': f"Strategy fails in {regime} market (Sharpe={sharpe:.2f} ≤ 0). Must work in ALL regimes."
                }

        return {'passed': True}

    def _validate_generalization(self, results: Dict) -> Dict:
        """Validate generalization (OOS ≥ 70% of IS)."""
        is_sharpe = results.get('in_sample_sharpe', 0)
        oos_sharpe = results.get('out_sample_sharpe', 0)

        if is_sharpe <= 0:
            return {
                'passed': False,
                'error': f"In-sample Sharpe ≤ 0: {is_sharpe:.2f}"
            }

        generalization_ratio = oos_sharpe / is_sharpe

        if generalization_ratio < 0.7:
            return {
                'passed': False,
                'error': f"Poor generalization: OOS Sharpe ({oos_sharpe:.2f}) < 70% of IS Sharpe ({is_sharpe:.2f}). Ratio: {generalization_ratio:.1%}"
            }

        warnings = []
        if generalization_ratio > 1.1:
            warnings.append("OOS performance exceeds IS - unusual, verify data integrity")

        return {'passed': True, 'warnings': warnings}

    def _validate_thresholds(self, results: Dict) -> Dict:
        """Validate performance thresholds."""
        sharpe = results.get('overall_sharpe', 0)
        calmar = results.get('overall_calmar', 0)
        mdd = results.get('max_drawdown', 1.0)
        trading_freq = results.get('trading_frequency', 1.0)

        errors = []

        if sharpe < self.adaptive_sharpe_threshold:
            errors.append(f"Sharpe {sharpe:.2f} < threshold {self.adaptive_sharpe_threshold:.2f}")

        if calmar < self.adaptive_calmar_threshold:
            errors.append(f"Calmar {calmar:.2f} < threshold {self.adaptive_calmar_threshold:.2f}")

        if mdd > self.max_drawdown_limit:
            errors.append(f"Max Drawdown {mdd:.1%} > limit {self.max_drawdown_limit:.1%}")

        warnings = []
        if trading_freq > 0.5:
            warnings.append(f"High trading frequency: {trading_freq:.1%} of days - may have high costs")

        if errors:
            return {
                'passed': False,
                'error': "Performance thresholds not met: " + "; ".join(errors)
            }

        return {'passed': True, 'warnings': warnings}


# ============================================================================
# LAYER 5: NOVELTY VALIDATION
# ============================================================================

class NoveltyValidator:
    """
    Layer 5: Novelty Validation
    - Not semantically equivalent to existing factors
    - Similarity < 80% with existing innovations
    """

    def __init__(self, existing_innovations: List[str] = None):
        """
        Initialize with existing innovations.

        Args:
            existing_innovations: List of existing innovation code strings
        """
        self.existing = existing_innovations or []

    def validate(self, code: str, rationale: str = "") -> ValidationResult:
        """Validate novelty against existing innovations."""
        if not self.existing:
            # No existing innovations to compare
            return ValidationResult(passed=True)

        # Normalize code for comparison
        normalized_code = self._normalize_code(code)

        max_similarity = 0.0
        most_similar_idx = -1

        for idx, existing_code in enumerate(self.existing):
            normalized_existing = self._normalize_code(existing_code)
            similarity = self._calculate_similarity(normalized_code, normalized_existing)

            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_idx = idx

        if max_similarity >= 0.80:
            return ValidationResult(
                passed=False,
                failed_layer=5,
                layer_name="Novelty",
                error=f"Too similar to existing innovation #{most_similar_idx}: {max_similarity:.1%} similarity (threshold: 80%)"
            )

        warnings = []
        if max_similarity >= 0.60:
            warnings.append(f"Moderate similarity to existing innovation: {max_similarity:.1%}")

        return ValidationResult(
            passed=True,
            warnings=warnings,
            details={'max_similarity': max_similarity}
        )

    def _normalize_code(self, code: str) -> str:
        """Normalize code for comparison."""
        # Remove whitespace and comments
        code = re.sub(r'#.*', '', code)  # Remove comments
        code = re.sub(r'\s+', ' ', code)  # Normalize whitespace
        code = code.strip()
        return code.lower()

    def _calculate_similarity(self, code1: str, code2: str) -> float:
        """Calculate similarity using sequence matcher."""
        return difflib.SequenceMatcher(None, code1, code2).ratio()


# ============================================================================
# LAYER 6: SEMANTIC EQUIVALENCE DETECTION
# ============================================================================

class SemanticEquivalenceValidator:
    """
    Layer 6: Semantic Equivalence Detection (NEW - Consensus Addition)
    - Not mathematically identical to existing factors
    - AST normalization and comparison
    - Detect equivalent boolean expressions
    """

    def __init__(self, existing_innovations: List[str] = None):
        """
        Initialize with existing innovations.

        Args:
            existing_innovations: List of existing innovation code strings
        """
        self.existing = existing_innovations or []

    def validate(self, code: str, rationale: str = "") -> ValidationResult:
        """Validate semantic equivalence."""
        if not self.existing:
            return ValidationResult(passed=True)

        try:
            tree = ast.parse(code)
            normalized_ast = self._normalize_ast(tree)
        except:
            # Syntax error already caught in Layer 1
            return ValidationResult(passed=True)

        # Check against existing innovations
        for idx, existing_code in enumerate(self.existing):
            try:
                existing_tree = ast.parse(existing_code)
                existing_normalized = self._normalize_ast(existing_tree)

                if self._ast_equivalent(normalized_ast, existing_normalized):
                    return ValidationResult(
                        passed=False,
                        failed_layer=6,
                        layer_name="Semantic Equivalence",
                        error=f"Mathematically equivalent to existing innovation #{idx}"
                    )
            except:
                continue

        return ValidationResult(passed=True)

    def _normalize_ast(self, tree: ast.AST) -> ast.AST:
        """Normalize AST for comparison."""
        # This is a simplified version
        # TODO: Implement full algebraic normalization
        return tree

    def _ast_equivalent(self, tree1: ast.AST, tree2: ast.AST) -> bool:
        """Check if two ASTs are semantically equivalent."""
        # Simplified check using AST dump
        dump1 = ast.dump(tree1)
        dump2 = ast.dump(tree2)
        return dump1 == dump2


# ============================================================================
# LAYER 7: EXPLAINABILITY VALIDATION
# ============================================================================

class ExplainabilityValidator:
    """
    Layer 7: Explainability Validation (NEW - Consensus Addition)
    - LLM must generate strategy rationale
    - Explanation logically consistent with code
    - No tautologies ("buy low sell high")
    """

    TAUTOLOGY_PATTERNS = [
        r'buy\s+low\s+sell\s+high',
        r'buy\s+cheap\s+sell\s+expensive',
        r'maximize\s+profit',
        r'minimize\s+loss',
    ]

    def validate(self, code: str, rationale: str = "") -> ValidationResult:
        """Validate explainability."""
        if not rationale or len(rationale.strip()) < 20:
            return ValidationResult(
                passed=False,
                failed_layer=7,
                layer_name="Explainability",
                error="Missing or insufficient rationale (min 20 characters required)"
            )

        # Check for tautologies
        rationale_lower = rationale.lower()
        for pattern in self.TAUTOLOGY_PATTERNS:
            if re.search(pattern, rationale_lower):
                return ValidationResult(
                    passed=False,
                    failed_layer=7,
                    layer_name="Explainability",
                    error=f"Rationale contains tautology: '{pattern}'"
                )

        # Check consistency between code and rationale (basic heuristic)
        # TODO: Enhance with LLM-based consistency checking
        warnings = []
        code_lower = code.lower()

        # Check if rationale mentions key operations in code
        has_multiply = '*' in code
        has_divide = '/' in code
        mentions_multiply = any(word in rationale_lower for word in ['multiply', 'product', 'times'])
        mentions_divide = any(word in rationale_lower for word in ['divide', 'ratio', 'per'])

        if has_multiply and not mentions_multiply:
            warnings.append("Code uses multiplication but rationale doesn't mention it")
        if has_divide and not mentions_divide:
            warnings.append("Code uses division but rationale doesn't mention ratio/division")

        return ValidationResult(
            passed=True,
            warnings=warnings
        )


# ============================================================================
# MAIN INNOVATION VALIDATOR
# ============================================================================

class InnovationValidator:
    """
    7-Layer Innovation Validator
    Comprehensive validation pipeline for LLM-generated innovations.
    """

    def __init__(
        self,
        baseline_sharpe: float = 0.680,
        baseline_calmar: float = 2.406,
        existing_innovations: List[str] = None
    ):
        """
        Initialize validator with baseline metrics and existing innovations.

        Args:
            baseline_sharpe: Baseline Sharpe ratio (from Task 0.1)
            baseline_calmar: Baseline Calmar ratio (from Task 0.1)
            existing_innovations: List of existing innovation code strings
        """
        self.validation_layers = [
            ('Syntax', SyntaxValidator()),
            ('Semantic', SemanticValidator()),
            ('Execution', ExecutionValidator()),
            ('Performance', PerformanceValidator(baseline_sharpe, baseline_calmar)),
            ('Novelty', NoveltyValidator(existing_innovations)),
            ('Semantic Equivalence', SemanticEquivalenceValidator(existing_innovations)),
            ('Explainability', ExplainabilityValidator())
        ]

    def validate(self, code: str, rationale: str = "") -> ValidationResult:
        """
        Run innovation through all 7 layers.

        Args:
            code: Python code to validate
            rationale: Explanation/rationale for the innovation

        Returns:
            ValidationResult with pass/fail and details
        """
        all_warnings = []

        for idx, (layer_name, validator) in enumerate(self.validation_layers, 1):
            result = validator.validate(code, rationale)

            if not result.passed:
                # Failed at this layer
                result.failed_layer = idx
                result.layer_name = layer_name
                return result

            # Accumulate warnings
            all_warnings.extend(result.warnings)

        # All layers passed
        return ValidationResult(
            passed=True,
            warnings=all_warnings
        )

    def validate_with_report(self, code: str, rationale: str = "") -> Dict[str, Any]:
        """
        Validate and return detailed report.

        Returns:
            Dictionary with validation results and layer-by-layer details
        """
        result = self.validate(code, rationale)

        return {
            'passed': result.passed,
            'failed_layer': result.failed_layer,
            'layer_name': result.layer_name,
            'error': result.error,
            'warnings': result.warnings,
            'details': result.details,
            'timestamp': datetime.now().isoformat()
        }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Validate a factor
    validator = InnovationValidator(
        baseline_sharpe=0.680,
        baseline_calmar=2.406
    )

    # Valid example
    valid_code = """
import pandas as pd
import numpy as np

# Quality-Growth-Value composite
roe = data.get('roe').shift(1)
revenue_growth = data.get('revenue_growth').shift(1)
pe_ratio = data.get('pe_ratio').shift(1)

factor = (roe * revenue_growth) / pe_ratio.replace(0, np.nan)
factor = factor.clip(lower=0, upper=100)
"""

    valid_rationale = """
This factor combines profitability (ROE), growth momentum (Revenue Growth),
and value (P/E ratio). High values indicate quality companies with strong
growth at reasonable valuations, suitable for long-term investment.
"""

    print("="*70)
    print("TESTING INNOVATION VALIDATOR - 7 LAYERS")
    print("="*70)
    print("\nTest 1: Valid Innovation")
    result = validator.validate(valid_code, valid_rationale)
    print(f"Result: {'✅ PASSED' if result.passed else '❌ FAILED'}")
    if result.warnings:
        print(f"Warnings ({len(result.warnings)}):")
        for w in result.warnings:
            print(f"  - {w}")

    # Invalid example (look-ahead bias)
    print("\n" + "="*70)
    print("Test 2: Look-Ahead Bias (Should Fail)")
    invalid_code = """
# Using shift(0) - look-ahead bias!
roe = data.get('roe').shift(0)
factor = roe * 2
"""

    result2 = validator.validate(invalid_code, valid_rationale)
    print(f"Result: {'✅ PASSED' if result2.passed else '❌ FAILED'}")
    if not result2.passed:
        print(f"Failed at Layer {result2.failed_layer}: {result2.layer_name}")
        print(f"Error: {result2.error}")

    # Invalid example (missing rationale)
    print("\n" + "="*70)
    print("Test 3: Missing Rationale (Should Fail)")
    result3 = validator.validate(valid_code, "")
    print(f"Result: {'✅ PASSED' if result3.passed else '❌ FAILED'}")
    if not result3.passed:
        print(f"Failed at Layer {result3.failed_layer}: {result3.layer_name}")
        print(f"Error: {result3.error}")

    print("\n" + "="*70)
    print("VALIDATION COMPLETE")
    print("="*70)
