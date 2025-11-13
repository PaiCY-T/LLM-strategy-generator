"""
Exit Strategy Mutation Smoke Test

Tests the Phase 1 AST-based exit mutation framework.
Validates that mutations produce syntactically and semantically valid code.

Test Plan:
----------
1. Load momentum_exit_template.py code
2. Apply 10 different mutations
3. Validate each mutation succeeds
4. Report success rate and examples

Success Criteria:
-----------------
- ≥90% mutations produce valid code (9/10 succeed)
- No syntax errors in generated code
- Parameters stay within valid ranges
- Exit mechanisms remain logically sound
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.mutation import ExitMutationOperator, MutationConfig


def load_momentum_exit_code() -> str:
    """
    Load the reference momentum exit template code.

    Returns:
        Source code as string
    """
    template_path = Path(__file__).parent / "src" / "templates" / "momentum_exit_template.py"

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_method_code(full_code: str) -> str:
    """
    Extract just the _apply_exit_strategies method for testing.

    Args:
        full_code: Full template class code

    Returns:
        Just the exit method code
    """
    # For simplicity, we'll test the full code
    # In a real scenario, you might extract just the method
    return full_code


def run_smoke_test(num_mutations: int = 10) -> None:
    """
    Run smoke test with multiple mutations.

    Args:
        num_mutations: Number of mutations to test
    """
    print("=" * 80)
    print("EXIT STRATEGY MUTATION SMOKE TEST")
    print("=" * 80)
    print()

    # Load reference code
    print("[1/4] Loading momentum exit template...")
    try:
        original_code = load_momentum_exit_code()
        print(f"✓ Loaded {len(original_code)} characters of code")
    except Exception as e:
        print(f"✗ Failed to load code: {e}")
        return

    # Create operator
    print("\n[2/4] Initializing mutation operator...")
    operator = ExitMutationOperator(max_retries=3)
    print("✓ Operator initialized")

    # Detect baseline profile
    print("\n[3/4] Detecting baseline exit strategy profile...")
    try:
        profile = operator.detect_profile(original_code)
        print(f"✓ Detected mechanisms: {profile.mechanisms}")
        print(f"✓ Detected parameters: {profile.parameters}")
    except Exception as e:
        print(f"✗ Failed to detect profile: {e}")
        return

    # Run mutations
    print(f"\n[4/4] Running {num_mutations} mutations...")
    print("-" * 80)

    results = []
    for i in range(num_mutations):
        print(f"\nMutation {i+1}/{num_mutations}:")

        # Use different seeds for variety
        config = MutationConfig(seed=42 + i)

        try:
            result = operator.mutate_exit_strategy(original_code, config)
            results.append(result)

            if result.success:
                print(f"  ✓ SUCCESS (attempts: {result.attempts})")
                if result.warnings:
                    print(f"    Warnings: {len(result.warnings)}")
                    for warning in result.warnings[:2]:  # Show first 2
                        print(f"      - {warning}")
            else:
                print(f"  ✗ FAILED (attempts: {result.attempts})")
                if result.errors:
                    print(f"    Errors: {len(result.errors)}")
                    for error in result.errors[:2]:  # Show first 2
                        print(f"      - {error}")

        except Exception as e:
            print(f"  ✗ EXCEPTION: {e}")
            results.append(None)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    successful = sum(1 for r in results if r and r.success)
    failed = sum(1 for r in results if r and not r.success)
    exceptions = sum(1 for r in results if r is None)

    total_tests = len(results)
    success_rate = (successful / total_tests * 100) if total_tests > 0 else 0

    print(f"\nTotal mutations: {total_tests}")
    print(f"Successful: {successful} ({success_rate:.1f}%)")
    print(f"Failed validation: {failed}")
    print(f"Exceptions: {exceptions}")

    # Success criteria check
    print("\n" + "-" * 80)
    print("SUCCESS CRITERIA CHECK")
    print("-" * 80)

    criteria_met = success_rate >= 90.0
    print(f"Target: ≥90% success rate")
    print(f"Actual: {success_rate:.1f}%")
    print(f"Status: {'✓ PASS' if criteria_met else '✗ FAIL'}")

    # Show example mutations
    if successful > 0:
        print("\n" + "-" * 80)
        print("EXAMPLE SUCCESSFUL MUTATION")
        print("-" * 80)

        # Find first successful result
        for result in results:
            if result and result.success:
                print(result.summary())

                # Show a snippet of mutated code
                if result.code:
                    lines = result.code.split('\n')
                    method_start = None
                    for idx, line in enumerate(lines):
                        if '_apply_exit_strategies' in line:
                            method_start = idx
                            break

                    if method_start:
                        print("\nCode snippet (first 20 lines of method):")
                        print("-" * 80)
                        for line in lines[method_start:method_start+20]:
                            print(line)
                        print("...")

                break

    # Final verdict
    print("\n" + "=" * 80)
    if criteria_met:
        print("✓✓✓ SMOKE TEST PASSED ✓✓✓")
    else:
        print("✗✗✗ SMOKE TEST FAILED ✗✗✗")
    print("=" * 80)


if __name__ == '__main__':
    try:
        run_smoke_test(num_mutations=10)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
