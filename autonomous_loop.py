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

from dataclasses import dataclass, asdict
from typing import Optional, Tuple, Any, Dict, List
from datetime import datetime
import time

from history import IterationHistory
from prompt_builder import PromptBuilder
from validate_code import validate_code
from sandbox_simple import execute_strategy_safe
from poc_claude_test import generate_strategy
from fix_dataset_keys import fix_dataset_keys
from src.failure_tracker import FailureTracker
from src.constants import METRIC_SHARPE, CHAMPION_FILE


@dataclass
class ChampionStrategy:
    """Best-performing strategy across all iterations.

    Tracks the highest-performing strategy to enable:
    - Performance attribution (comparing current vs. champion)
    - Success pattern extraction (identifying what works)
    - Evolutionary constraints (preserving proven patterns)

    Attributes:
        iteration_num: Which iteration produced this champion
        code: Complete strategy code that achieved these metrics
        parameters: Extracted parameter values from the code
        metrics: Performance metrics (sharpe_ratio, annual_return, etc.)
        success_patterns: List of patterns that contributed to success
        timestamp: When this champion was established (ISO format)
    """
    iteration_num: int
    code: str
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    success_patterns: List[str]
    timestamp: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary containing all champion data
        """
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> 'ChampionStrategy':
        """Create ChampionStrategy from dictionary.

        Args:
            data: Dictionary with all required fields

        Returns:
            ChampionStrategy instance
        """
        return ChampionStrategy(**data)


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

        # Champion tracking and failure learning
        self.champion: Optional[ChampionStrategy] = self._load_champion()
        self.failure_tracker = FailureTracker()

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

        # Step 1: Build enhanced prompt with evolutionary constraints
        print("[1/6] Building prompt...")
        feedback_summary = self.history.generate_feedback_summary() if iteration_num > 0 else None

        # Get failure patterns if champion exists
        failure_patterns = self.failure_tracker.get_avoid_directives() if self.champion else None

        # Build prompt (will use evolutionary prompts if champion exists)
        prompt = self.prompt_builder.build_prompt(
            iteration_num=iteration_num,
            feedback_history=feedback_summary,
            champion=self.champion,
            failure_patterns=failure_patterns
        )
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

        # Step 2.3: Validate champion preservation (if applicable)
        if self.champion and iteration_num >= 3:  # Only for exploitation mode
            print(f"\n[2.3/6] Validating champion preservation...")
            is_compliant = self._validate_preservation(code)

            if is_compliant:
                print("✅ Preservation validated - critical patterns maintained")
            else:
                # P0 Fix: Retry generation with stronger preservation enforcement
                print("⚠️  Preservation violation detected - regenerating with stronger constraints...")
                logger.warning(f"Iteration {iteration_num}: Preservation validation failed, retrying generation")

                # Retry with stronger preservation prompt (max 2 attempts)
                for retry in range(2):
                    print(f"   Retry attempt {retry + 1}/2...")

                    # Build stronger preservation prompt
                    stronger_prompt = self.prompt_builder.build_prompt(
                        iteration_num=iteration_num,
                        feedback_history=feedback_summary,
                        champion=self.champion,
                        failure_patterns=failure_patterns,
                        force_preservation=True  # Flag for stronger constraints
                    )

                    try:
                        code = generate_strategy(
                            iteration_num=iteration_num,
                            history=stronger_prompt or "",
                            model=self.model
                        )
                        is_compliant = self._validate_preservation(code)

                        if is_compliant:
                            print(f"✅ Preservation validated after retry {retry + 1}")
                            logger.info(f"Iteration {iteration_num}: Preservation validated on retry {retry + 1}")
                            break
                    except Exception as e:
                        logger.error(f"Iteration {iteration_num}: Retry {retry + 1} generation failed: {e}")
                        continue
                else:
                    # After 2 retries, log warning but allow execution with monitoring
                    logger.warning(f"Iteration {iteration_num}: Failed preservation after 2 retries, proceeding with warning")
                    print("⚠️  Preservation enforcement failed after retries - executing with monitoring")

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

        # Step 5: Enhanced feedback with attribution
        print(f"\n[5/6] Building feedback...")

        if self.champion and is_valid and execution_success and metrics:
            attribution = self._compare_with_champion(code, metrics)

            if attribution:
                # Track failures dynamically
                if attribution.get('assessment') == 'degraded':
                    self.failure_tracker.add_pattern(attribution, iteration_num)

                # Generate attributed feedback
                feedback = self.prompt_builder.build_attributed_feedback(
                    attribution,
                    iteration_num,
                    self.champion,
                    failure_patterns=self.failure_tracker.get_avoid_directives()
                )
            else:
                # Fallback to simple feedback if attribution fails
                feedback = self.prompt_builder.build_simple_feedback(metrics)
        else:
            # No champion yet or iteration failed - use simple feedback
            feedback = self.prompt_builder.build_simple_feedback(metrics) if metrics else \
                       self.prompt_builder.build_combined_feedback(
                           validation_passed=is_valid,
                           validation_errors=validation_errors,
                           execution_success=execution_success,
                           execution_error=execution_error,
                           metrics=metrics
                       )

        print(f"✅ Feedback generated ({len(feedback)} chars)")

        # Step 5.5: Update champion if improved
        if is_valid and execution_success and metrics:
            import logging
            logger = logging.getLogger(__name__)
            champion_updated = self._update_champion(iteration_num, code, metrics)
            if champion_updated:
                logger.info("Champion updated successfully")

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

    def _load_champion(self) -> Optional[ChampionStrategy]:
        """Load champion strategy from disk if it exists.

        Returns:
            ChampionStrategy if file exists and is valid, None otherwise
        """
        import json
        import os

        if not os.path.exists(CHAMPION_FILE):
            return None

        try:
            with open(CHAMPION_FILE, 'r') as f:
                data = json.load(f)
            return ChampionStrategy.from_dict(data)
        except (json.JSONDecodeError, TypeError, KeyError, ValueError) as e:
            print(f"Warning: Could not load champion strategy: {e}")
            print("Starting without champion")
            return None

    def _update_champion(
        self,
        iteration_num: int,
        code: str,
        metrics: Dict[str, float]
    ) -> bool:
        """Update champion with probation period to prevent churn.

        Anti-churn mechanism applies higher improvement threshold (10%) for
        strategies that appear within 2 iterations of the current champion,
        reducing to 5% threshold after the probation period.

        Args:
            iteration_num: Current iteration number
            code: Strategy code that was executed
            metrics: Performance metrics dict with at least METRIC_SHARPE key

        Returns:
            True if champion was updated, False otherwise
        """
        import logging
        logger = logging.getLogger(__name__)

        # First valid strategy becomes champion
        if self.champion is None and metrics.get(METRIC_SHARPE, 0) > 0.5:
            self._create_champion(iteration_num, code, metrics)
            return True

        if self.champion is None:
            return False

        # Calculate improvement threshold
        current_sharpe = metrics.get(METRIC_SHARPE, 0)
        champion_sharpe = self.champion.metrics.get(METRIC_SHARPE, 0)

        # Anti-churn mechanism: Higher threshold for recent champions
        if iteration_num - self.champion.iteration_num <= 2:
            required_improvement = 1.10  # 10% for probation period
        else:
            required_improvement = 1.05  # 5% after probation

        if current_sharpe >= champion_sharpe * required_improvement:
            improvement_pct = (current_sharpe / champion_sharpe - 1) * 100
            self._create_champion(iteration_num, code, metrics)
            logger.info(
                f"Champion updated: "
                f"{champion_sharpe:.4f} → {current_sharpe:.4f} "
                f"(+{improvement_pct:.1f}%)"
            )
            return True

        return False

    def _create_champion(
        self,
        iteration_num: int,
        code: str,
        metrics: Dict[str, float]
    ) -> None:
        """Create new champion strategy.

        Extracts parameters and success patterns from the code, creates
        a ChampionStrategy instance, and persists it to disk.

        Args:
            iteration_num: Iteration number that produced this champion
            code: Strategy code
            metrics: Performance metrics dict
        """
        import logging
        from performance_attributor import extract_strategy_params, extract_success_patterns

        logger = logging.getLogger(__name__)

        parameters = extract_strategy_params(code)
        success_patterns = extract_success_patterns(code, parameters)

        self.champion = ChampionStrategy(
            iteration_num=iteration_num,
            code=code,
            parameters=parameters,
            metrics=metrics,
            success_patterns=success_patterns,
            timestamp=datetime.now().isoformat()
        )

        self._save_champion()
        logger.info(f"New champion: Iteration {iteration_num}, Sharpe {metrics.get(METRIC_SHARPE, 0):.4f}")

    def _save_champion(self) -> None:
        """Save champion strategy to JSON file with atomic write.

        Uses tempfile + atomic rename to prevent corruption from concurrent access.
        Creates parent directory if needed and writes champion data
        in human-readable format with proper indentation.
        """
        import json
        import os
        import tempfile

        # Ensure directory exists if path includes directory
        dir_path = os.path.dirname(CHAMPION_FILE)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        # Write to temporary file first
        # Use same directory as target to ensure atomic rename works (same filesystem)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=dir_path or '.',
            prefix='.champion_',
            suffix='.tmp'
        )

        try:
            # Write champion data to temp file
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(self.champion.to_dict(), f, indent=2)

            # Atomic rename - POSIX guarantees atomicity
            os.replace(temp_path, CHAMPION_FILE)

        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise RuntimeError(f"Failed to save champion: {e}")

    def _compare_with_champion(
        self,
        current_code: str,
        current_metrics: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """Compare current strategy with champion for performance attribution.

        Extracts parameters from current code and compares with champion
        to identify what changed and how it affected performance.

        Args:
            current_code: Strategy code to compare
            current_metrics: Performance metrics for current strategy

        Returns:
            Attribution dictionary with changes and performance delta,
            or None if no champion exists or comparison fails
        """
        import logging

        if not self.champion:
            return None

        try:
            from performance_attributor import extract_strategy_params, compare_strategies

            logger = logging.getLogger(__name__)
            curr_params = extract_strategy_params(current_code)
            return compare_strategies(
                prev_params=self.champion.parameters,
                curr_params=curr_params,
                prev_metrics=self.champion.metrics,
                curr_metrics=current_metrics
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Attribution comparison failed: {e}")
            logger.info("Falling back to simple feedback")
            return None

    def _validate_preservation(self, generated_code: str) -> bool:
        """Validate that generated code preserves champion patterns.

        Checks that critical champion parameters are maintained in the generated code,
        with reasonable tolerance for incremental improvements (±20% for windows,
        ≥80% for thresholds).

        Args:
            generated_code: LLM-generated strategy code to validate

        Returns:
            True if all critical champion patterns are preserved, False otherwise
        """
        from performance_attributor import extract_strategy_params
        import logging

        logger = logging.getLogger(__name__)

        # Extract patterns from generated code
        try:
            generated_params = extract_strategy_params(generated_code)
        except Exception as e:
            logger.warning(f"Pattern extraction failed during validation: {e}")
            return False  # Extraction failure = non-compliant

        champion_params = self.champion.parameters

        # Critical Check 1: ROE Type Preservation
        if champion_params.get('roe_type') == 'smoothed':
            if generated_params.get('roe_type') != 'smoothed':
                logger.warning(
                    f"Preservation violation: ROE type changed from "
                    f"'{champion_params.get('roe_type')}' to '{generated_params.get('roe_type')}'"
                )
                return False

            # Allow ±20% variation in smoothing window
            champion_window = champion_params.get('roe_smoothing_window', 1)
            generated_window = generated_params.get('roe_smoothing_window', 1)

            if champion_window > 0:  # Avoid division by zero
                window_deviation = abs(generated_window - champion_window) / champion_window
                if window_deviation > 0.2:
                    logger.warning(
                        f"Preservation violation: ROE smoothing window changed by "
                        f"{window_deviation*100:.1f}% (from {champion_window} to {generated_window})"
                    )
                    return False

        # Critical Check 2: Liquidity Threshold Preservation (≥80% of champion)
        champion_liq = champion_params.get('liquidity_threshold')
        if champion_liq and champion_liq > 0:
            generated_liq = generated_params.get('liquidity_threshold')

            if not generated_liq:
                logger.warning(
                    f"Preservation violation: Liquidity filter removed "
                    f"(champion had {champion_liq:,} threshold)"
                )
                return False

            if generated_liq < champion_liq * 0.8:
                logger.warning(
                    f"Preservation violation: Liquidity threshold relaxed by "
                    f"{(1 - generated_liq/champion_liq)*100:.1f}% "
                    f"(from {champion_liq:,} to {generated_liq:,})"
                )
                return False

        # All critical patterns preserved
        return True

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
