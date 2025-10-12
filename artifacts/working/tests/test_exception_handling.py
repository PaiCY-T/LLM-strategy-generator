"""
Test to verify the exception handling bug in claude_code_strategy_generator.py

This test demonstrates that the second 'except Exception' at line 788
is unreachable because the first 'except Exception' at line 745 catches
all exceptions first.
"""

def test_double_except_bug():
    """
    Simulates the problematic exception handling structure.
    """
    retry_count = 0
    max_retries = 3

    print("Testing double except Exception bug...")
    print("=" * 60)

    for retry_attempt in range(1, max_retries + 1):
        print(f"\nRetry attempt {retry_attempt}/{max_retries}")

        try:
            # Simulate main operation that fails
            print("  [Try Block 1] Attempting main operation...")
            raise ValueError("Main operation failed!")

        except Exception as e:  # First except - catches ALL exceptions
            print(f"  [Except Block 1] Caught: {e}")
            print("  [Except Block 1] Attempting fallback...")

            try:
                # Simulate fallback that also fails
                raise RuntimeError("Fallback also failed!")
            except Exception as fallback_error:
                print(f"    [Inner Except] Caught fallback error: {fallback_error}")
                print("    [Inner Except] Re-raising...")
                raise  # Re-raise to trigger retry logic

        except Exception as retry_error:  # Second except - UNREACHABLE!
            print(f"  [Except Block 2 - RETRY LOGIC] This should handle retries")
            print(f"  [Except Block 2] Caught: {retry_error}")
            retry_count += 1

            if retry_attempt < max_retries:
                print(f"  [Except Block 2] Retrying ({retry_attempt}/{max_retries})...")
                continue
            else:
                print(f"  [Except Block 2] Max retries reached!")
                raise

    print("\n" + "=" * 60)
    print(f"Retry count: {retry_count}")
    print(f"Expected: {max_retries}, Actual: {retry_count}")
    print(f"Bug confirmed: {retry_count == 0}")


def test_correct_exception_handling():
    """
    Demonstrates the correct way to handle this scenario.
    """
    max_retries = 3

    print("\n\nTesting CORRECT exception handling...")
    print("=" * 60)

    for retry_attempt in range(1, max_retries + 1):
        print(f"\nRetry attempt {retry_attempt}/{max_retries}")
        success = False

        try:
            # Simulate main operation that fails
            print("  [Try] Attempting main operation...")
            raise ValueError("Main operation failed!")

        except Exception as e:
            print(f"  [Except] Caught: {e}")
            print("  [Except] Attempting fallback...")

            try:
                # Simulate fallback that also fails
                raise RuntimeError("Fallback also failed!")
            except Exception as fallback_error:
                print(f"    [Inner Except] Caught fallback error: {fallback_error}")

                # CORRECT: Retry logic INSIDE the first except block
                if retry_attempt < max_retries:
                    print(f"    [Inner Except] Retrying ({retry_attempt}/{max_retries})...")
                    continue  # Continue to next retry attempt
                else:
                    print(f"    [Inner Except] Max retries reached! Raising final error.")
                    raise RuntimeError(
                        f"Failed after {max_retries} attempts"
                    ) from fallback_error

        if success:
            break

    print("\n" + "=" * 60)
    print("Correct handling demonstrated")


if __name__ == '__main__':
    try:
        test_double_except_bug()
    except Exception as e:
        print(f"\n❌ Test crashed (expected): {e}")
        print("This demonstrates the bug - program crashes instead of retrying")

    print("\n\n" + "=" * 80)

    try:
        test_correct_exception_handling()
    except Exception as e:
        print(f"\n✅ Test completed with controlled error (expected): {e}")
        print("This demonstrates correct handling - retries work properly")
