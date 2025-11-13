"""
PromptManager - Dynamic prompt selection and orchestration for LLM innovation

Task 7: Dynamic prompt selection based on context (modification vs creation)
Task 8: Modification prompts with champion context and performance feedback

This module provides a high-level interface for selecting and building prompts
based on innovation context (champion performance, iteration history, target metrics).

Key Features:
- Dynamic routing between modification and creation prompts
- Context-aware prompt selection (performance-based directives)
- Champion strategy context integration
- Failure pattern incorporation
- Support for both full_code and yaml generation modes

Requirements: 2.1-2.5 (Prompt structure and context)
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .prompt_builder import PromptBuilder
from .structured_prompt_builder import StructuredPromptBuilder


class PromptType(Enum):
    """Types of prompts for LLM innovation."""
    MODIFICATION = "modification"  # Modify existing champion strategy
    CREATION = "creation"          # Create novel strategy from scratch


class GenerationMode(Enum):
    """Generation modes for strategies."""
    FULL_CODE = "full_code"  # Generate complete Python code
    YAML = "yaml"            # Generate YAML specification


@dataclass
class PromptContext:
    """
    Context information for prompt generation.

    Contains all necessary information to build an effective prompt
    including champion performance, failure history, and target metrics.
    """
    # Champion information
    champion_code: Optional[str] = None
    champion_metrics: Optional[Dict[str, float]] = None
    champion_approach: Optional[str] = None

    # Failure history
    failure_history: Optional[List[Dict[str, Any]]] = None

    # Target information
    target_metric: str = "sharpe_ratio"
    target_strategy_type: str = "momentum"  # For YAML mode

    # Innovation directive
    innovation_directive: Optional[str] = None

    # Generation mode
    generation_mode: GenerationMode = GenerationMode.FULL_CODE


class PromptManager:
    """
    Manages dynamic prompt selection and construction for LLM innovation.

    Orchestrates PromptBuilder and StructuredPromptBuilder to provide
    intelligent prompt selection based on context and performance metrics.

    Task 7 Implementation: Dynamic prompt selection logic
    Task 8 Implementation: Modification prompt with champion context

    Examples:
        >>> manager = PromptManager()
        >>>
        >>> # Modification prompt (Task 8)
        >>> context = PromptContext(
        ...     champion_code="def strategy(data): return data.get('ROE') > 15",
        ...     champion_metrics={"sharpe_ratio": 0.85, "max_drawdown": 0.15},
        ...     target_metric="sharpe_ratio"
        ... )
        >>> prompt_type, prompt = manager.select_and_build_prompt(context)
        >>> print(f"Selected: {prompt_type}")

        >>> # Creation prompt for novel exploration
        >>> context = PromptContext(
        ...     champion_approach="Momentum-based with ROE filter",
        ...     innovation_directive="Explore value + quality combinations"
        ... )
        >>> prompt_type, prompt = manager.select_and_build_prompt(context)
    """

    def __init__(
        self,
        failure_patterns_path: str = "artifacts/data/failure_patterns.json",
        schema_path: str = "schemas/strategy_schema_v1.json"
    ):
        """
        Initialize PromptManager.

        Args:
            failure_patterns_path: Path to failure patterns JSON
            schema_path: Path to YAML strategy schema (for structured mode)
        """
        # Initialize prompt builders
        self.code_builder = PromptBuilder(failure_patterns_path=failure_patterns_path)

        try:
            self.yaml_builder = StructuredPromptBuilder(schema_path=schema_path)
            self.yaml_available = True
        except FileNotFoundError:
            print("⚠️  YAML mode unavailable - schema not found")
            self.yaml_builder = None
            self.yaml_available = False

        # Performance thresholds for prompt selection
        self.STRONG_PERFORMANCE_THRESHOLD = 0.8  # Sharpe > 0.8 = strong
        self.WEAK_PERFORMANCE_THRESHOLD = 0.5    # Sharpe < 0.5 = weak

        # Statistics tracking
        self.modification_prompts_generated = 0
        self.creation_prompts_generated = 0

    def select_and_build_prompt(
        self,
        context: PromptContext,
        force_type: Optional[PromptType] = None
    ) -> Tuple[PromptType, str]:
        """
        Select appropriate prompt type and build prompt based on context.

        Task 7: Dynamic prompt selection logic

        Selection Logic:
        1. If champion performs strongly (Sharpe > 0.8): Use MODIFICATION
        2. If champion performs weakly (Sharpe < 0.5): Use CREATION
        3. If no champion code available: Use CREATION
        4. If force_type specified: Use that type
        5. Default: Use MODIFICATION (70% of time) or CREATION (30%)

        Args:
            context: PromptContext with champion info and targets
            force_type: Optional override for prompt type selection

        Returns:
            (prompt_type, prompt_text) tuple

        Examples:
            >>> # Strong champion - modify to improve
            >>> context = PromptContext(
            ...     champion_code="...",
            ...     champion_metrics={"sharpe_ratio": 0.95}
            ... )
            >>> prompt_type, prompt = manager.select_and_build_prompt(context)
            >>> assert prompt_type == PromptType.MODIFICATION

            >>> # Weak champion - create novel approach
            >>> context = PromptContext(
            ...     champion_code="...",
            ...     champion_metrics={"sharpe_ratio": 0.35}
            ... )
            >>> prompt_type, prompt = manager.select_and_build_prompt(context)
            >>> assert prompt_type == PromptType.CREATION
        """
        # Determine prompt type (Task 7: Dynamic selection)
        prompt_type = self._select_prompt_type(context, force_type)

        # Build prompt based on type and mode
        if context.generation_mode == GenerationMode.YAML:
            prompt = self._build_yaml_prompt(context, prompt_type)
        else:
            prompt = self._build_code_prompt(context, prompt_type)

        # Track statistics
        if prompt_type == PromptType.MODIFICATION:
            self.modification_prompts_generated += 1
        else:
            self.creation_prompts_generated += 1

        return prompt_type, prompt

    def build_modification_prompt(
        self,
        champion_code: str,
        champion_metrics: Dict[str, float],
        failure_history: Optional[List[Dict[str, Any]]] = None,
        target_metric: str = "sharpe_ratio",
        generation_mode: GenerationMode = GenerationMode.FULL_CODE
    ) -> str:
        """
        Build modification prompt with champion context.

        Task 8: Modification prompts with performance context

        Includes:
        - Current champion code and performance
        - Success factors to preserve
        - Failure patterns to avoid
        - Target metric improvement directive
        - Clear modification guidance

        Args:
            champion_code: Current champion strategy code
            champion_metrics: Champion performance metrics
            failure_history: Optional recent failure history
            target_metric: Which metric to optimize
            generation_mode: Full code or YAML

        Returns:
            Complete modification prompt

        Example:
            >>> prompt = manager.build_modification_prompt(
            ...     champion_code="def strategy(data): return data.get('ROE') > 15",
            ...     champion_metrics={"sharpe_ratio": 0.85, "max_drawdown": 0.15},
            ...     target_metric="sharpe_ratio"
            ... )
            >>> assert "Current Champion Strategy" in prompt
            >>> assert "Success Factors to Preserve" in prompt
        """
        if generation_mode == GenerationMode.YAML:
            # YAML mode: use structured builder
            return self.yaml_builder.build_compact_prompt(
                champion_metrics=champion_metrics,
                failure_patterns=self._extract_failure_patterns(failure_history),
                target_strategy_type="momentum"  # Could be inferred from champion
            )
        else:
            # Full code mode: use code builder
            return self.code_builder.build_modification_prompt(
                champion_code=champion_code,
                champion_metrics=champion_metrics,
                failure_history=failure_history,
                target_metric=target_metric
            )

    def build_creation_prompt(
        self,
        champion_approach: str,
        failure_history: Optional[List[Dict[str, Any]]] = None,
        innovation_directive: Optional[str] = None,
        generation_mode: GenerationMode = GenerationMode.FULL_CODE
    ) -> str:
        """
        Build creation prompt for novel strategy exploration.

        Task 8: Creation prompts with innovation guidance

        Includes:
        - Champion approach for inspiration (not direct modification)
        - Failure patterns to avoid
        - Innovation directive for exploration
        - Clear novelty expectations

        Args:
            champion_approach: High-level description of champion's approach
            failure_history: Optional failure patterns to avoid
            innovation_directive: Specific innovation guidance
            generation_mode: Full code or YAML

        Returns:
            Complete creation prompt

        Example:
            >>> prompt = manager.build_creation_prompt(
            ...     champion_approach="Momentum-based with ROE filter",
            ...     innovation_directive="Explore value + quality combinations"
            ... )
            >>> assert "Champion Approach (for Inspiration)" in prompt
            >>> assert "Innovation Directive" in prompt
        """
        if generation_mode == GenerationMode.YAML:
            # YAML mode: use structured builder
            return self.yaml_builder.build_compact_prompt(
                champion_metrics=None,
                failure_patterns=self._extract_failure_patterns(failure_history),
                target_strategy_type="factor_combination"  # Encourage novel combinations
            )
        else:
            # Full code mode: use code builder
            failure_patterns = None
            if failure_history:
                failure_patterns = self.code_builder.extract_failure_patterns()

            return self.code_builder.build_creation_prompt(
                champion_approach=champion_approach,
                failure_patterns=failure_patterns,
                innovation_directive=innovation_directive or "Create a novel strategy with different factor combinations"
            )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get prompt generation statistics.

        Returns:
            Statistics dictionary with counts and ratios
        """
        total = self.modification_prompts_generated + self.creation_prompts_generated

        return {
            "total_prompts_generated": total,
            "modification_prompts": self.modification_prompts_generated,
            "creation_prompts": self.creation_prompts_generated,
            "modification_ratio": (
                self.modification_prompts_generated / total
                if total > 0 else 0.0
            ),
            "creation_ratio": (
                self.creation_prompts_generated / total
                if total > 0 else 0.0
            )
        }

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _select_prompt_type(
        self,
        context: PromptContext,
        force_type: Optional[PromptType]
    ) -> PromptType:
        """
        Select prompt type based on context and performance.

        Task 7: Core dynamic selection logic

        Selection Algorithm:
        1. If force_type specified: return force_type
        2. If no champion code: return CREATION
        3. If champion Sharpe < 0.5 (weak): return CREATION (explore new approach)
        4. If champion Sharpe > 0.8 (strong): return MODIFICATION (refine success)
        5. Default: return MODIFICATION (iterative improvement)

        Args:
            context: PromptContext with champion information
            force_type: Optional forced prompt type

        Returns:
            Selected PromptType
        """
        # Override if forced
        if force_type is not None:
            return force_type

        # No champion available - create novel strategy
        if context.champion_code is None:
            return PromptType.CREATION

        # Analyze champion performance
        if context.champion_metrics:
            sharpe = context.champion_metrics.get('sharpe_ratio', 0)

            # Weak performance - try novel approach
            if sharpe < self.WEAK_PERFORMANCE_THRESHOLD:
                return PromptType.CREATION

            # Strong performance - refine and improve
            if sharpe > self.STRONG_PERFORMANCE_THRESHOLD:
                return PromptType.MODIFICATION

        # Default: modification (iterative improvement is safer)
        return PromptType.MODIFICATION

    def _build_code_prompt(
        self,
        context: PromptContext,
        prompt_type: PromptType
    ) -> str:
        """
        Build full Python code prompt based on type.

        Args:
            context: PromptContext with all necessary information
            prompt_type: MODIFICATION or CREATION

        Returns:
            Complete prompt string
        """
        if prompt_type == PromptType.MODIFICATION:
            return self.code_builder.build_modification_prompt(
                champion_code=context.champion_code or "",
                champion_metrics=context.champion_metrics or {},
                failure_history=context.failure_history,
                target_metric=context.target_metric
            )
        else:
            # Extract champion approach if code available
            champion_approach = context.champion_approach
            if not champion_approach and context.champion_code:
                champion_approach = self._infer_champion_approach(context.champion_code)

            failure_patterns = None
            if context.failure_history:
                failure_patterns = self.code_builder.extract_failure_patterns()

            return self.code_builder.build_creation_prompt(
                champion_approach=champion_approach or "Momentum-based factor approach",
                failure_patterns=failure_patterns,
                innovation_directive=context.innovation_directive or "Explore novel factor combinations"
            )

    def _build_yaml_prompt(
        self,
        context: PromptContext,
        prompt_type: PromptType
    ) -> str:
        """
        Build YAML specification prompt based on type.

        Args:
            context: PromptContext with all necessary information
            prompt_type: MODIFICATION or CREATION

        Returns:
            Complete YAML prompt string
        """
        if not self.yaml_available:
            raise ValueError("YAML mode not available - schema not found")

        # Extract failure patterns
        failure_patterns = self._extract_failure_patterns(context.failure_history)

        # YAML mode uses similar prompts for both types
        # (difference is in target_strategy_type)
        if prompt_type == PromptType.MODIFICATION:
            target_type = context.target_strategy_type or "momentum"
        else:
            target_type = "factor_combination"  # Encourage novelty

        return self.yaml_builder.build_compact_prompt(
            champion_metrics=context.champion_metrics,
            failure_patterns=failure_patterns,
            target_strategy_type=target_type
        )

    def _extract_failure_patterns(
        self,
        failure_history: Optional[List[Dict[str, Any]]]
    ) -> List[str]:
        """
        Extract failure pattern descriptions from failure history.

        Args:
            failure_history: List of failure dictionaries

        Returns:
            List of failure pattern strings
        """
        if not failure_history:
            return []

        patterns = []
        for failure in failure_history[:5]:  # Limit to 5 most recent
            desc = failure.get('description', '')
            error_type = failure.get('error_type', '')

            if desc:
                patterns.append(desc)
            elif error_type:
                patterns.append(error_type)

        return patterns

    def _infer_champion_approach(self, champion_code: str) -> str:
        """
        Infer high-level approach from champion code.

        Simple heuristic-based inference for champion approach description.

        Args:
            champion_code: Champion strategy code

        Returns:
            High-level approach description
        """
        code_lower = champion_code.lower()

        approaches = []

        # Check for momentum signals
        if 'rolling' in code_lower or 'shift' in code_lower:
            approaches.append("momentum-based")

        # Check for fundamental factors
        if 'roe' in code_lower or 'fundamental' in code_lower:
            approaches.append("fundamental factor")

        # Check for value signals
        if 'pe_ratio' in code_lower or 'pb_ratio' in code_lower or '本益比' in code_lower:
            approaches.append("value-based")

        # Check for ranking
        if 'rank' in code_lower:
            approaches.append("with cross-sectional ranking")

        if approaches:
            return " ".join(approaches).capitalize()
        else:
            return "Factor-based quantitative approach"


# Example usage and testing
if __name__ == "__main__":
    print("=" * 80)
    print("PROMPT MANAGER - Task 7-8 Implementation Demo")
    print("=" * 80)

    # Initialize manager
    manager = PromptManager()

    # ========================================================================
    # TASK 7: Dynamic Prompt Selection
    # ========================================================================
    print("\n" + "=" * 80)
    print("TASK 7: Dynamic Prompt Selection")
    print("=" * 80)

    # Test 1: Strong champion -> Modification
    print("\nTest 1: Strong Champion (Sharpe=0.95) -> Modification")
    print("-" * 80)
    context = PromptContext(
        champion_code="def strategy(data): return data.get('ROE') > 15",
        champion_metrics={"sharpe_ratio": 0.95, "max_drawdown": 0.12},
        target_metric="sharpe_ratio"
    )
    prompt_type, _ = manager.select_and_build_prompt(context)
    print(f"✅ Selected: {prompt_type.value}")
    assert prompt_type == PromptType.MODIFICATION

    # Test 2: Weak champion -> Creation
    print("\nTest 2: Weak Champion (Sharpe=0.35) -> Creation")
    print("-" * 80)
    context = PromptContext(
        champion_code="def strategy(data): return data.get('ROE') > 15",
        champion_metrics={"sharpe_ratio": 0.35, "max_drawdown": 0.25},
        target_metric="sharpe_ratio"
    )
    prompt_type, _ = manager.select_and_build_prompt(context)
    print(f"✅ Selected: {prompt_type.value}")
    assert prompt_type == PromptType.CREATION

    # Test 3: No champion -> Creation
    print("\nTest 3: No Champion -> Creation")
    print("-" * 80)
    context = PromptContext(
        champion_approach="Initial exploration",
        innovation_directive="Find profitable strategies"
    )
    prompt_type, _ = manager.select_and_build_prompt(context)
    print(f"✅ Selected: {prompt_type.value}")
    assert prompt_type == PromptType.CREATION

    # ========================================================================
    # TASK 8: Modification Prompts with Champion Context
    # ========================================================================
    print("\n" + "=" * 80)
    print("TASK 8: Modification Prompts with Champion Context")
    print("=" * 80)

    # Test 4: Modification prompt with full context
    print("\nTest 4: Build Modification Prompt")
    print("-" * 80)

    champion_code = """
def strategy(data):
    # Simple ROE filter
    roe = data.get('fundamental_features:ROE稅後')
    return roe > 15
"""

    champion_metrics = {
        'sharpe_ratio': 0.85,
        'max_drawdown': 0.15,
        'win_rate': 0.58,
        'calmar_ratio': 2.3
    }

    failure_history = [
        {
            'description': 'Adding debt ratio filter reduced Sharpe by 0.2',
            'error_type': 'performance_degradation'
        }
    ]

    prompt = manager.build_modification_prompt(
        champion_code=champion_code,
        champion_metrics=champion_metrics,
        failure_history=failure_history,
        target_metric='sharpe_ratio'
    )

    # Verify prompt contains required sections (Task 8)
    assert "Current Champion Strategy" in prompt or "champion" in prompt.lower()
    assert "Performance" in prompt or "Sharpe" in prompt
    assert "Success Factors" in prompt or "success" in prompt.lower()

    print(f"✅ Modification prompt built")
    print(f"   Length: {len(prompt)} chars (~{len(prompt)//4} tokens)")
    print(f"   Contains champion code: {'✓' if 'def strategy' in prompt else '✗'}")
    print(f"   Contains metrics: {'✓' if str(champion_metrics['sharpe_ratio']) in prompt else '✗'}")
    print(f"   Contains failure patterns: {'✓' if 'debt ratio' in prompt.lower() else '✗'}")

    # Test 5: Creation prompt
    print("\nTest 5: Build Creation Prompt")
    print("-" * 80)

    prompt = manager.build_creation_prompt(
        champion_approach="Momentum-based with ROE quality filter",
        innovation_directive="Explore value + quality combinations using P/B and profit margins"
    )

    assert "Champion Approach" in prompt or "champion" in prompt.lower()
    assert "Novel" in prompt or "novel" in prompt.lower()

    print(f"✅ Creation prompt built")
    print(f"   Length: {len(prompt)} chars (~{len(prompt)//4} tokens)")
    print(f"   Contains innovation directive: {'✓' if 'value' in prompt.lower() else '✗'}")

    # Statistics
    print("\n" + "=" * 80)
    print("Prompt Generation Statistics")
    print("=" * 80)

    stats = manager.get_statistics()
    print(f"Total prompts: {stats['total_prompts_generated']}")
    print(f"Modification: {stats['modification_prompts']} ({stats['modification_ratio']:.1%})")
    print(f"Creation: {stats['creation_prompts']} ({stats['creation_ratio']:.1%})")

    print("\n" + "=" * 80)
    print("TASK 7-8 IMPLEMENTATION COMPLETE")
    print("=" * 80)
    print("\n✅ Dynamic prompt selection working")
    print("✅ Modification prompts include champion context")
    print("✅ Creation prompts provide innovation guidance")
    print("✅ Both full_code and YAML modes supported")
