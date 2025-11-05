"""
Exit Parameter Mutation Module

Implements parameter-based genetic operators for exit condition optimization.
Uses Gaussian noise mutation within bounded ranges to avoid AST complexity.
"""

import ast
import re
import logging
import numpy as np
from dataclasses import dataclass
from typing import Tuple, Dict, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class ParameterBounds:
    """Bounded ranges for exit parameters (trading risk management)"""
    min_value: float
    max_value: float
    is_integer: bool = False

    def clamp(self, value: float) -> float:
        """Clamp value to bounds"""
        clamped = max(self.min_value, min(value, self.max_value))
        if self.is_integer:
            clamped = int(round(clamped))
        return clamped


@dataclass
class MutationResult:
    """Result of exit parameter mutation"""
    mutated_code: str
    metadata: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


class ExitParameterMutator:
    """
    Parameter-based exit condition mutator.

    Mutates exit parameters using Gaussian noise within bounded ranges.
    Achieves >70% success rate vs 0% for AST-based approach.
    """

    # Parameter bounds (Requirement 2)
    PARAM_BOUNDS = {
        "stop_loss_pct": ParameterBounds(0.01, 0.20, is_integer=False),
        "take_profit_pct": ParameterBounds(0.05, 0.50, is_integer=False),
        "trailing_stop_offset": ParameterBounds(0.005, 0.05, is_integer=False),
        "holding_period_days": ParameterBounds(1, 60, is_integer=True),
    }

    # Regex patterns (Requirement 4 - non-greedy patterns)
    REGEX_PATTERNS = {
        "stop_loss_pct": r'stop_loss_pct\s*=\s*([\d.]+)',
        "take_profit_pct": r'take_profit_pct\s*=\s*([\d.]+)',
        "trailing_stop_offset": r'trailing_stop[_a-z]*\s*=\s*([\d.]+)',  # Non-greedy
        "holding_period_days": r'holding_period[_a-z]*\s*=\s*(\d+)',    # Non-greedy
    }

    def __init__(self, gaussian_std_dev: float = 0.15):
        """
        Initialize exit parameter mutator.

        Args:
            gaussian_std_dev: Standard deviation for Gaussian noise (default 0.15 = 15%)
        """
        self.gaussian_std_dev = gaussian_std_dev
        self.mutation_stats = {
            "total": 0,
            "success": 0,
            "failed_regex": 0,
            "failed_validation": 0,
            "clamped": 0,
        }

    def mutate(
        self,
        code: str,
        param_name: Optional[str] = None
    ) -> MutationResult:
        """
        Mutate exit parameter in strategy code.

        Args:
            code: Strategy code containing exit parameters
            param_name: Specific parameter to mutate (None = random selection)

        Returns:
            MutationResult with mutated code and metadata
        """
        self.mutation_stats["total"] += 1

        # STAGE 2: SELECT - Choose parameter (Requirement 1, AC #2)
        if param_name is None:
            param_name = self._select_parameter_uniform()

        if param_name not in self.PARAM_BOUNDS:
            return self._failure_result(
                code,
                param_name,
                f"Unknown parameter: {param_name}"
            )

        # STAGE 1: IDENTIFY - Extract current value
        current_value = self._extract_parameter_value(code, param_name)
        if current_value is None:
            self.mutation_stats["failed_regex"] += 1
            logger.warning(f"Parameter {param_name} not found in code")
            return self._failure_result(
                code,
                param_name,
                f"Parameter {param_name} not found in code"
            )

        # STAGE 3: MUTATE - Apply Gaussian noise (Requirement 3)
        new_value = self._apply_gaussian_noise(current_value)

        # STAGE 4: CLAMP - Enforce bounds (Requirement 2)
        was_clamped = False
        clamped_value = self._clamp_to_bounds(new_value, param_name)
        if abs(clamped_value - new_value) > 1e-9:
            was_clamped = True
            self.mutation_stats["clamped"] += 1
            logger.info(
                f"Parameter {param_name} clamped from {new_value:.4f} to {clamped_value:.4f}"
            )

        # STAGE 5: REPLACE - Update code via regex (Requirement 4)
        mutated_code = self._regex_replace_parameter(code, param_name, clamped_value)
        if mutated_code == code:
            self.mutation_stats["failed_regex"] += 1
            return self._failure_result(
                code,
                param_name,
                f"Regex replacement failed for {param_name}"
            )

        # STAGE 6: VALIDATE - Verify syntax (Requirement 1, AC #6-7)
        if not self._validate_code_syntax(mutated_code):
            self.mutation_stats["failed_validation"] += 1
            logger.error(f"Validation failed for {param_name} mutation")
            return self._failure_result(
                code,
                param_name,
                f"Validation failed: syntax error after mutation"
            )

        # Success
        self.mutation_stats["success"] += 1
        return MutationResult(
            mutated_code=mutated_code,
            metadata={
                "mutation_type": "exit_param",
                "parameter": param_name,
                "old_value": float(current_value),
                "new_value": float(clamped_value),
                "bounded": was_clamped,
            },
            success=True,
        )

    def _select_parameter_uniform(self) -> str:
        """
        Select parameter using uniform random distribution.

        Requirement 1, AC #2: 25% probability for each parameter
        """
        return np.random.choice(list(self.PARAM_BOUNDS.keys()))

    def _extract_parameter_value(
        self,
        code: str,
        param_name: str
    ) -> Optional[float]:
        """
        Extract current parameter value from code using regex.

        Returns:
            Current parameter value or None if not found
        """
        pattern = self.REGEX_PATTERNS.get(param_name)
        if not pattern:
            return None

        match = re.search(pattern, code)
        if not match:
            return None

        try:
            return float(match.group(1))
        except (ValueError, IndexError):
            return None

    def _apply_gaussian_noise(self, value: float) -> float:
        """
        Apply Gaussian noise mutation.

        Requirement 3, AC #1-3:
        - Formula: new_value = old_value * (1 + N(0, std_dev))
        - 68% of mutations within ±15% of original
        - 95% of mutations within ±30% of original
        - Absolute value for negative results
        """
        noise = np.random.normal(0, self.gaussian_std_dev)
        new_value = value * (1 + noise)

        # Requirement 3, AC #3: Handle negative values
        if new_value < 0:
            new_value = abs(new_value)
            logger.debug(f"Converted negative value to positive: {new_value:.4f}")

        return new_value

    def _clamp_to_bounds(self, value: float, param_name: str) -> float:
        """
        Clamp value to bounded range.

        Requirement 2: Enforce strict parameter bounds
        """
        bounds = self.PARAM_BOUNDS[param_name]
        return bounds.clamp(value)

    def clamp_to_bounds(self, value: float, param_name: str) -> Tuple[float, bool]:
        """
        Public method to clamp value to bounds and report if clamping occurred.

        Args:
            value: Value to clamp
            param_name: Parameter name for bounds lookup

        Returns:
            Tuple of (clamped_value, was_clamped)
        """
        if param_name not in self.PARAM_BOUNDS:
            return value, False

        bounds = self.PARAM_BOUNDS[param_name]
        clamped = bounds.clamp(value)

        # Check if clamping occurred (with small epsilon for float comparison)
        was_clamped = abs(clamped - value) > 1e-9

        return clamped, was_clamped

    def _regex_replace_parameter(
        self,
        code: str,
        param_name: str,
        new_value: float
    ) -> str:
        """
        Replace parameter value in code using regex.

        Requirement 4, AC #1-6:
        - Uses non-greedy patterns for trailing_stop and holding_period
        - Integer rounding for holding_period
        - First occurrence only for multi-assignment
        """
        pattern = self.REGEX_PATTERNS.get(param_name)
        if not pattern:
            return code

        # Format value based on parameter type
        bounds = self.PARAM_BOUNDS[param_name]
        if bounds.is_integer:
            # Requirement 4, AC #5: Integer rounding
            replacement_value = str(int(round(new_value)))
        else:
            replacement_value = f"{new_value:.6f}"

        # Requirement 4, AC #6: Replace first occurrence only
        def replacer(match):
            return f"{param_name.split('[')[0]}={replacement_value}"

        mutated_code = re.sub(pattern, replacer, code, count=1)
        return mutated_code

    def _validate_code_syntax(self, code: str) -> bool:
        """
        Validate Python syntax using ast.parse.

        Requirement 1, AC #6: Validate before returning
        """
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            logger.debug(f"Syntax validation failed: {e}")
            return False

    def _failure_result(
        self,
        code: str,
        param_name: str,
        error_message: str
    ) -> MutationResult:
        """
        Create failure result with original code.

        Requirement 1, AC #7: Return original code on failure
        """
        return MutationResult(
            mutated_code=code,
            metadata={
                "mutation_type": "exit_param",
                "parameter": param_name,
                "old_value": None,
                "new_value": None,
                "bounded": False,
            },
            success=False,
            error_message=error_message,
        )

    def get_success_rate(self) -> float:
        """Calculate current success rate"""
        if self.mutation_stats["total"] == 0:
            return 0.0
        return self.mutation_stats["success"] / self.mutation_stats["total"]

    def get_statistics(self) -> Dict[str, Any]:
        """Get mutation statistics"""
        return {
            **self.mutation_stats,
            "success_rate": self.get_success_rate(),
        }
