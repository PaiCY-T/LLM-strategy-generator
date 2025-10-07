"""Autonomous learning loop controller.

Orchestrates the complete workflow:
1. Generate strategy using LLM with feedback
2. Validate code with AST security validator
3. Execute in sandbox
4. Extract metrics
5. Record iteration
6. Build feedback for next iteration
7. Repeat until convergence or max iterations

This implements the core autonomous iteration logic for MVP.
"""

from typing import Optional, Tuple, Any
import time

from history import IterationHistory
from prompt_builder import PromptBuilder
from validate_code import validate_code
from sandbox_simple import execute_strategy_safe
from poc_claude_test import generate_strategy
from fix_dataset_keys import fix_dataset_keys


class AutonomousLoop:
    """Autonomous strategy generation and improvement loop."""

    def __init__(
        self,
        model: str = "google/gemini-2.5-flash",
        max_iterations: int = 10,
        history_file: str = "iteration_history.json"
    ):
        """Initialize autonomous loop.

        Args:
            model: LLM model to use for generation
            max_iterations: Maximum number of iterations
            history_file: Path to history JSON file
        """
        self.model = model
        self.max_iterations = max_iterations
        self.history = IterationHistory(history_file)
        self.prompt_builder = PromptBuilder()

    def run_iteration(
        self,
        iteration_num: int,
        data: Optional[Any] = None
    ) -> Tuple[bool, str]:
        """Run a single iteration of the loop.

        Args:
            iteration_num: Current iteration number (0-indexed)
            data: Finlab data object for execution (None for testing)

        Returns:
            Tuple of (success, status_message)
        """
        print(f"\n{'='*60}")
        print(f"ITERATION {iteration_num}")
        print(f"{'='*60}\n")

        # Step 1: Build prompt with feedback
        print("[1/6] Building prompt...")
        feedback_summary = self.history.generate_feedback_summary() if iteration_num > 0 else None
        prompt = self.prompt_builder.build_prompt(iteration_num, feedback_summary)
        print(f"✅ Prompt ready ({len(prompt)} chars)")

        # Step 2: Generate strategy
        print(f"\n[2/6] Generating strategy with {self.model}...")
        try:
            code = generate_strategy(
                iteration_num=iteration_num,
                history=feedback_summary or "",
                model=self.model
            )
            print(f"✅ Strategy generated ({len(code)} chars)")
        except Exception as e:
            error_msg = f"❌ Generation failed: {e}"
            print(error_msg)
            return False, error_msg

        # Step 2.5: Auto-fix incorrect dataset keys
        print(f"\n[2.5/6] Auto-fixing dataset keys...")
        fixed_code, fixes = fix_dataset_keys(code)
        if fixes:
            print(f"✅ Applied {len(fixes)} fixes:")
            for fix in fixes:
                print(f"   - {fix}")
            code = fixed_code
        else:
            print("✅ No fixes needed")

        # Step 3: Validate code
        print(f"\n[3/6] Validating code...")
        is_valid, validation_errors = validate_code(code)

        if is_valid:
            print("✅ Validation passed")
        else:
            print(f"❌ Validation failed ({len(validation_errors)} errors)")
            for error in validation_errors[:3]:  # Show first 3 errors
                print(f"   - {error}")

        # Step 4: Execute in sandbox (if validated)
        execution_success = False
        execution_error = None
        metrics = None

        if is_valid:
            print(f"\n[4/6] Executing in sandbox...")
            try:
                execution_success, metrics, execution_error = execute_strategy_safe(
                    code=code,
                    data=data,
                    timeout=120
                )

                if execution_success:
                    print("✅ Execution successful")
                    if metrics:
                        print(f"   Metrics: {list(metrics.keys())}")
                else:
                    print(f"❌ Execution failed")
                    if execution_error:
                        print(f"   Error: {execution_error[:100]}...")
            except Exception as e:
                execution_error = str(e)
                print(f"❌ Sandbox error: {e}")
        else:
            print(f"\n[4/6] Skipping execution (validation failed)")

        # Step 5: Build feedback
        print(f"\n[5/6] Building feedback...")
        feedback = self.prompt_builder.build_combined_feedback(
            validation_passed=is_valid,
            validation_errors=validation_errors,
            execution_success=execution_success,
            execution_error=execution_error,
            metrics=metrics
        )
        print(f"✅ Feedback generated ({len(feedback)} chars)")

        # Step 6: Record iteration
        print(f"\n[6/6] Recording iteration...")
        self.history.add_record(
            iteration_num=iteration_num,
            model=self.model,
            code=code,
            validation_passed=is_valid,
            validation_errors=validation_errors,
            execution_success=execution_success,
            execution_error=execution_error,
            metrics=metrics,
            feedback=feedback
        )
        print("✅ Iteration recorded")

        # Save generated code
        with open(f"generated_strategy_loop_iter{iteration_num}.py", 'w') as f:
            f.write(code)
        print(f"✅ Code saved to generated_strategy_loop_iter{iteration_num}.py")

        status = "SUCCESS" if (is_valid and execution_success) else "FAILED"
        return (is_valid and execution_success), status

    def run(self, data: Optional[Any] = None) -> dict:
        """Run the complete autonomous loop.

        Args:
            data: Finlab data object for execution (None for testing)

        Returns:
            Summary dictionary with loop statistics
        """
        print("\n" + "="*60)
        print("AUTONOMOUS LEARNING LOOP - START")
        print("="*60)
        print(f"Model: {self.model}")
        print(f"Max iterations: {self.max_iterations}")
        print()

        start_time = time.time()
        results = {
            'total_iterations': 0,
            'successful_iterations': 0,
            'failed_iterations': 0,
            'validation_failures': 0,
            'execution_failures': 0,
        }

        for i in range(self.max_iterations):
            success, status = self.run_iteration(i, data)

            results['total_iterations'] += 1
            if success:
                results['successful_iterations'] += 1
            else:
                results['failed_iterations'] += 1

                # Track failure types
                record = self.history.get_record(i)
                if record:
                    if not record.validation_passed:
                        results['validation_failures'] += 1
                    elif not record.execution_success:
                        results['execution_failures'] += 1

            # Brief pause between iterations
            if i < self.max_iterations - 1:
                time.sleep(1)

        elapsed = time.time() - start_time

        # Final summary
        print("\n" + "="*60)
        print("AUTONOMOUS LEARNING LOOP - COMPLETE")
        print("="*60)
        print(f"Total time: {elapsed:.1f}s")
        print(f"Total iterations: {results['total_iterations']}")
        print(f"✅ Successful: {results['successful_iterations']}")
        print(f"❌ Failed: {results['failed_iterations']}")
        print(f"   - Validation failures: {results['validation_failures']}")
        print(f"   - Execution failures: {results['execution_failures']}")

        # Success rate
        if results['total_iterations'] > 0:
            success_rate = results['successful_iterations'] / results['total_iterations'] * 100
            print(f"\nSuccess rate: {success_rate:.1f}%")

        # Best strategy
        successful = self.history.get_successful_iterations()
        if successful:
            print(f"\n🎉 Generated {len(successful)} successful strategies!")

            # Find best by Sharpe ratio if metrics available
            with_metrics = [s for s in successful if s.metrics and 'sharpe_ratio' in s.metrics]
            if with_metrics:
                best = max(with_metrics, key=lambda s: s.metrics['sharpe_ratio'])
                print(f"\n🏆 Best strategy: Iteration {best.iteration_num}")
                print(f"   Sharpe: {best.metrics['sharpe_ratio']:.4f}")
                print(f"   Return: {best.metrics.get('total_return', 'N/A')}")

        results['elapsed_time'] = elapsed
        return results


def main():
    """Test autonomous loop (without real finlab data)."""
    print("Testing autonomous loop...\n")
    print("Note: Running without real finlab data - execution will fail")
    print("      This tests the loop mechanism, not actual strategy performance\n")

    # Create loop with limited iterations for testing
    loop = AutonomousLoop(
        model="google/gemini-2.5-flash",
        max_iterations=3,
        history_file="test_loop_history.json"
    )

    # Clear previous test history
    loop.history.clear()

    # Run loop
    results = loop.run(data=None)

    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Loop completed: {results['total_iterations']} iterations")
    print(f"Time per iteration: {results['elapsed_time'] / results['total_iterations']:.1f}s")
    print("\n✅ Autonomous loop mechanism verified")


if __name__ == '__main__':
    main()
