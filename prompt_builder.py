"""Prompt builder with learning feedback for autonomous iteration.

Constructs prompts that incorporate feedback from previous iterations,
enabling the AI to learn from past successes and failures.
"""

from typing import Optional
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
        feedback_history: Optional[str] = None
    ) -> str:
        """Build prompt with iteration feedback.

        Args:
            iteration_num: Current iteration number
            feedback_history: Summary of previous iterations (optional)

        Returns:
            Complete prompt string ready for LLM
        """
        # Start with base template
        prompt = self.base_template

        # Add iteration context
        if iteration_num == 0:
            iteration_context = "\n\n## Current Iteration\n\n"
            iteration_context += "This is the first iteration. Create an innovative trading strategy.\n"
        else:
            iteration_context = f"\n\n## Current Iteration: {iteration_num}\n\n"
            iteration_context += "Based on feedback from previous iterations, create an improved strategy.\n"

        # Add feedback history if available
        if feedback_history:
            iteration_context += "\n## Previous Iterations Feedback\n\n"
            iteration_context += feedback_history + "\n"
            iteration_context += "\n**Task**: Learn from the above feedback and create a DIFFERENT strategy.\n"
            iteration_context += "- If validation errors occurred, avoid those patterns\n"
            iteration_context += "- If execution succeeded, try different factor combinations\n"
            iteration_context += "- Explore different datasets and filtering approaches\n"
            iteration_context += "- Maintain code quality and avoid look-ahead bias\n"

        # Construct final prompt
        final_prompt = prompt + iteration_context

        return final_prompt

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
