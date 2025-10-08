"""Prompt builder with learning feedback for autonomous iteration.

Constructs prompts that incorporate feedback from previous iterations,
enabling the AI to learn from past successes and failures.
"""

from typing import Optional, Dict, List, Any
from pathlib import Path


class PromptBuilder:
    """Builds prompts with iteration feedback for continuous improvement."""

    def __init__(self, template_file: str = "prompt_template_v1.txt"):
        """Initialize prompt builder.

        Args:
            template_file: Path to base prompt template
        """
        # Use path relative to this script's location
        self.template_file = Path(__file__).parent / template_file
        self.base_template = self._load_template()

    def _load_template(self) -> str:
        """Load base template from file.

        Returns:
            Template content as string
        """
        try:
            with open(self.template_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file not found: {self.template_file}")

    def build_prompt(
        self,
        iteration_num: int = 0,
        feedback_history: Optional[str] = None,
        champion: Optional[Any] = None,
        failure_patterns: Optional[List[str]] = None,
        force_preservation: bool = False
    ) -> str:
        """Build prompt with iteration feedback and evolutionary constraints.

        Routes to either basic prompt (early iterations) or evolutionary prompt
        (iterations 3+ with champion) for intelligent exploration/exploitation balance.

        Args:
            iteration_num: Current iteration number
            feedback_history: Summary of previous iterations (optional)
            champion: ChampionStrategy instance (None for early iterations)
            failure_patterns: List of AVOID directives from FailureTracker (optional)
            force_preservation: If True, use stronger preservation constraints (for retries)

        Returns:
            Complete prompt string ready for LLM
        """
        # Start with base template
        base_template = self.base_template

        # Build feedback summary
        feedback_summary = ""
        if iteration_num == 0:
            feedback_summary = "\n\n## Current Iteration\n\n"
            feedback_summary += "This is the first iteration. Create an innovative trading strategy.\n"
        else:
            feedback_summary = f"\n\n## Current Iteration: {iteration_num}\n\n"
            feedback_summary += "Based on feedback from previous iterations, create an improved strategy.\n"

        if feedback_history:
            feedback_summary += "\n## Previous Iterations Feedback\n\n"
            feedback_summary += feedback_history + "\n"
            feedback_summary += "\n**Task**: Learn from the above feedback and create a DIFFERENT strategy.\n"
            feedback_summary += "- If validation errors occurred, avoid those patterns\n"
            feedback_summary += "- If execution succeeded, try different factor combinations\n"
            feedback_summary += "- Explore different datasets and filtering approaches\n"
            feedback_summary += "- Maintain code quality and avoid look-ahead bias\n"

        # Use evolutionary prompts if champion exists (iterations 3+)
        if champion is not None or iteration_num >= 3:
            return self.build_evolutionary_prompt(
                iteration_num=iteration_num,
                champion=champion,
                feedback_summary=feedback_summary,
                base_prompt=base_template,
                failure_patterns=failure_patterns,
                force_preservation=force_preservation
            )

        # Otherwise, use basic prompt (iterations 0-2)
        return base_template + feedback_summary

    def build_validation_feedback(
        self,
        validation_passed: bool,
        validation_errors: list
    ) -> str:
        """Build feedback message from validation results.

        Args:
            validation_passed: Whether validation passed
            validation_errors: List of validation error messages

        Returns:
            Formatted feedback string
        """
        if validation_passed:
            return "✅ Validation: PASSED - Code meets all security requirements"

        feedback = "❌ Validation: FAILED\n"
        feedback += "Errors found:\n"
        for error in validation_errors:
            feedback += f"- {error}\n"

        feedback += "\nRequired fixes:\n"
        if any("import" in e.lower() for e in validation_errors):
            feedback += "- Remove all import statements (data.get() provides all needed data)\n"
        if any("shift" in e.lower() and "negative" in e.lower() for e in validation_errors):
            feedback += "- Use only positive shift values: .shift(1), .shift(2), etc.\n"
        if any("exec" in e.lower() or "eval" in e.lower() for e in validation_errors):
            feedback += "- Remove exec(), eval(), and other dangerous functions\n"

        return feedback

    def build_execution_feedback(
        self,
        execution_success: bool,
        execution_error: Optional[str],
        metrics: Optional[dict]
    ) -> str:
        """Build feedback message from execution results.

        Args:
            execution_success: Whether execution succeeded
            execution_error: Error message if execution failed
            metrics: Extracted metrics if execution succeeded

        Returns:
            Formatted feedback string
        """
        if not execution_success:
            feedback = "❌ Execution: FAILED\n"
            if execution_error:
                feedback += f"Error: {execution_error}\n"

                # Provide hints based on error type
                if "NoneType" in execution_error and "get" in execution_error:
                    feedback += "\nLikely cause: Invalid dataset key or data object is None\n"
                    feedback += "Check that all data.get() keys match available datasets\n"
                elif "AttributeError" in execution_error:
                    feedback += "\nLikely cause: Calling method on wrong data type\n"
                    feedback += "Verify DataFrame operations match finlab data structure\n"

            return feedback

        feedback = "✅ Execution: SUCCESS\n"

        if metrics:
            feedback += "Metrics:\n"
            for key, value in metrics.items():
                if isinstance(value, float):
                    feedback += f"- {key}: {value:.4f}\n"
                else:
                    feedback += f"- {key}: {value}\n"

            # Performance evaluation
            sharpe = metrics.get('sharpe_ratio', 0)
            if sharpe > 1.5:
                feedback += "\n📈 Performance: EXCELLENT (Sharpe > 1.5)\n"
            elif sharpe > 1.0:
                feedback += "\n📊 Performance: GOOD (Sharpe > 1.0)\n"
            elif sharpe > 0.5:
                feedback += "\n📉 Performance: MODERATE (Sharpe > 0.5)\n"
            else:
                feedback += "\n⚠️ Performance: NEEDS IMPROVEMENT (Low Sharpe)\n"

        return feedback

    def build_combined_feedback(
        self,
        validation_passed: bool,
        validation_errors: list,
        execution_success: bool,
        execution_error: Optional[str],
        metrics: Optional[dict]
    ) -> str:
        """Build complete feedback from validation and execution results.

        Args:
            validation_passed: Whether validation passed
            validation_errors: List of validation error messages
            execution_success: Whether execution succeeded
            execution_error: Error message if execution failed
            metrics: Extracted metrics if execution succeeded

        Returns:
            Combined feedback string
        """
        feedback = self.build_validation_feedback(validation_passed, validation_errors)
        feedback += "\n\n"

        if validation_passed:
            feedback += self.build_execution_feedback(execution_success, execution_error, metrics)

        return feedback

    def build_attributed_feedback(
        self,
        attribution: Dict[str, Any],
        iteration_num: int,
        champion: Any,
        failure_patterns: Optional[List[str]] = None
    ) -> str:
        """Build attributed feedback comparing current strategy to champion.

        Generates comprehensive feedback using performance attribution to explain
        what changed and how it affected performance relative to the champion.

        Args:
            attribution: Attribution dict from compare_strategies()
            iteration_num: Current iteration number
            champion: ChampionStrategy instance
            failure_patterns: List of AVOID directives from FailureTracker

        Returns:
            Formatted attributed feedback string
        """
        from performance_attributor import generate_attribution_feedback
        from src.constants import METRIC_SHARPE

        # Generate attribution analysis
        feedback = generate_attribution_feedback(
            attribution,
            iteration_num,
            champion.iteration_num
        )
        feedback += "\n\n"

        # Add champion context
        feedback += "## CURRENT CHAMPION\n\n"
        feedback += f"Iteration: {champion.iteration_num}\n"
        champion_sharpe = champion.metrics.get(METRIC_SHARPE, 0)
        feedback += f"Sharpe Ratio: {champion_sharpe:.4f}\n"
        feedback += f"Established: {champion.timestamp}\n"

        # Add success patterns if available
        if champion.success_patterns:
            feedback += "\nProven Success Patterns:\n"
            for pattern in champion.success_patterns[:5]:  # Top 5 patterns
                feedback += f"- {pattern}\n"

        # Add failure patterns to avoid
        if failure_patterns:
            feedback += "\n## AVOID (Learned from Past Failures)\n\n"
            for pattern in failure_patterns[:10]:  # Top 10 recent failures
                feedback += f"- {pattern}\n"

        return feedback

    def build_simple_feedback(self, metrics: Optional[Dict[str, float]]) -> str:
        """Build simple feedback when no champion exists for comparison.

        Used in early iterations before a champion is established,
        or when attribution comparison fails.

        Args:
            metrics: Performance metrics dict

        Returns:
            Simple formatted feedback string
        """
        from src.constants import METRIC_SHARPE

        if not metrics:
            return "No champion yet. Focus on creating a valid strategy with positive Sharpe ratio."

        feedback = "## PERFORMANCE METRICS\n\n"

        sharpe = metrics.get(METRIC_SHARPE, 0)
        feedback += f"Sharpe Ratio: {sharpe:.4f}\n"

        for key, value in metrics.items():
            if key != METRIC_SHARPE:
                if isinstance(value, float):
                    feedback += f"{key}: {value:.4f}\n"
                else:
                    feedback += f"{key}: {value}\n"

        feedback += "\n## NEXT STEPS\n\n"
        if sharpe > 0.5:
            feedback += "Good start! This strategy will become the champion.\n"
            feedback += "Continue exploring different approaches to find improvements.\n"
        else:
            feedback += "Strategy shows weak performance. Try:\n"
            feedback += "- Different factor combinations\n"
            feedback += "- Alternative data sources\n"
            feedback += "- Improved filtering or smoothing\n"

        return feedback

    def build_evolutionary_prompt(
        self,
        iteration_num: int,
        champion: Optional[Any],
        feedback_summary: str,
        base_prompt: str,
        failure_patterns: Optional[List[str]] = None,
        force_preservation: bool = False
    ) -> str:
        """Build prompt with champion preservation constraints.

        Creates evolutionary prompts that balance exploration and exploitation:
        - Iterations 0-2: Pure exploration (no constraints)
        - Iteration 3+: Exploitation with champion preservation
        - Every 5th iteration: Forced exploration to avoid local optima
        - force_preservation=True: Use MUCH stronger preservation constraints (for retries)

        Args:
            iteration_num: Current iteration number (0-indexed)
            champion: ChampionStrategy instance or None
            feedback_summary: Previous iteration feedback
            base_prompt: Base strategy generation prompt
            failure_patterns: List of AVOID directives from FailureTracker
            force_preservation: If True, use stronger preservation constraints (for retries)

        Returns:
            Complete prompt string with evolutionary constraints
        """
        from src.constants import METRIC_SHARPE

        # Exploration mode for early iterations or no champion
        if iteration_num < 3 or champion is None:
            return base_prompt + "\n\n" + feedback_summary

        # Diversity forcing every 5th iteration
        if self._should_force_exploration(iteration_num):
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Forcing exploration mode (iteration {iteration_num})")
            return base_prompt + "\n\n[EXPLORATION MODE: Try new approaches]\n\n" + feedback_summary

        # Exploitation mode: Build evolutionary prompt
        sections = []

        # Section A: Champion Context
        sections.append("=" * 60)
        sections.append("LEARNING FROM SUCCESS")
        sections.append("=" * 60)
        sections.append(f"CURRENT CHAMPION: Iteration {champion.iteration_num}")
        champion_sharpe = champion.metrics.get(METRIC_SHARPE, 0)
        sections.append(f"Achieved Sharpe: {champion_sharpe:.4f}")
        sections.append("")

        # Section B: Mandatory Preservation (stronger constraints if force_preservation=True)
        if force_preservation:
            sections.append("⚠️  CRITICAL PRESERVATION REQUIREMENTS (RETRY MODE) ⚠️")
            sections.append("")
            sections.append("ABSOLUTE REQUIREMENTS - DO NOT DEVIATE:")
            sections.append("1. EXACT PRESERVATION of these proven success factors:")
            for i, pattern in enumerate(champion.success_patterns, 1):
                sections.append(f"   {i}. {pattern}")
                # Parse pattern to extract exact values for enforcement
                if "liquidity_filter" in pattern.lower():
                    sections.append(f"      → MUST use EXACT threshold from champion (NO reductions allowed)")
                if "roe" in pattern.lower() and "rolling" in pattern.lower():
                    sections.append(f"      → MUST preserve EXACT smoothing window from champion")
            sections.append("")
            sections.append("2. MINIMAL changes allowed:")
            sections.append("   - Adjust weights ONLY by ±5% maximum")
            sections.append("   - NO changes to critical filters (liquidity, price, volume)")
            sections.append("   - Add ONLY complementary factors (keep ALL existing factors)")
            sections.append("   - Explain EVERY change with inline comments")
            sections.append("")
            sections.append("⚠️  This is a retry after preservation violation - follow constraints exactly! ⚠️")
            sections.append("")
        else:
            sections.append("MANDATORY REQUIREMENTS:")
            sections.append("1. PRESERVE these proven success factors:")
            for i, pattern in enumerate(champion.success_patterns, 1):
                sections.append(f"   {i}. {pattern}")
            sections.append("")
            sections.append("2. Make ONLY INCREMENTAL improvements")
            sections.append("   - Adjust weights/thresholds by ±10-20%")
            sections.append("   - Add complementary factors WITHOUT removing proven ones")
            sections.append("   - Explain changes with inline comments")
            sections.append("")

        # Section C: Failure Avoidance (DYNAMIC)
        if failure_patterns:  # Use learned patterns
            sections.append("AVOID (from actual regressions):")
            for pattern in failure_patterns:
                sections.append(f"   - {pattern}")
        elif iteration_num > 3:  # Fallback to static list
            sections.append("AVOID (general guidelines):")
            sections.append("   - Removing data smoothing (increases noise)")
            sections.append("   - Relaxing liquidity filters (reduces stability)")
            sections.append("   - Over-complicated multi-factor combinations")
        sections.append("")

        # Section D: Improvement Focus
        sections.append("EXPLORE these improvements (while preserving above):")
        sections.append("   - Fine-tune factor weights (e.g., momentum vs value balance)")
        sections.append("   - Add quality filters (debt ratio, profit margin stability)")
        sections.append("   - Optimize threshold values (within ±20% of current)")
        sections.append("=" * 60)
        sections.append("")

        # Combine: Evolutionary constraints + Base prompt + Feedback
        evolutionary_prompt = "\n".join(sections)
        return evolutionary_prompt + base_prompt + "\n\n" + feedback_summary

    def _should_force_exploration(self, iteration_num: int) -> bool:
        """Every 5th iteration: force exploration to prevent local optima.

        Args:
            iteration_num: Current iteration number (0-indexed)

        Returns:
            True if should force exploration, False otherwise
        """
        return iteration_num > 0 and iteration_num % 5 == 0


def main():
    """Test prompt builder."""
    print("Testing prompt builder...\n")

    builder = PromptBuilder()

    # Test 1: First iteration (no feedback)
    print("=" * 60)
    print("Test 1: First iteration")
    print("=" * 60)
    prompt0 = builder.build_prompt(iteration_num=0)
    print(f"Prompt length: {len(prompt0)} characters")
    print(f"Contains 'first iteration': {'first iteration' in prompt0.lower()}")
    print()

    # Test 2: Validation feedback
    print("=" * 60)
    print("Test 2: Validation feedback")
    print("=" * 60)
    feedback = builder.build_validation_feedback(
        validation_passed=False,
        validation_errors=["Line 1: Import statement not allowed: import os"]
    )
    print(feedback)
    print()

    # Test 3: Execution feedback with metrics
    print("=" * 60)
    print("Test 3: Execution feedback")
    print("=" * 60)
    feedback = builder.build_execution_feedback(
        execution_success=True,
        execution_error=None,
        metrics={'sharpe_ratio': 1.5, 'total_return': 0.20, 'max_drawdown': -0.15}
    )
    print(feedback)
    print()

    # Test 4: Iteration with feedback history
    print("=" * 60)
    print("Test 4: Second iteration with feedback")
    print("=" * 60)
    history_feedback = """Previous iterations: 1
- Validated: 0/1
- Executed successfully: 0/1

Common validation errors:
- Import statement not allowed (1x)"""

    prompt1 = builder.build_prompt(iteration_num=1, feedback_history=history_feedback)
    print(f"Prompt length: {len(prompt1)} characters")
    print(f"Contains feedback: {'Previous iterations' in prompt1}")
    print(f"Contains learning task: {'Learn from' in prompt1}")
    print()

    print("✅ All tests complete")


if __name__ == '__main__':
    main()
