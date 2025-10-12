"""Verify that the retry logic fix in claude_code_strategy_generator.py works correctly."""

import logging
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

import claude_code_strategy_generator as gen

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_retry_logic_with_mock_failures():
    """Test that retry logic executes correctly when template instantiation fails."""

    print("\n" + "=" * 80)
    print("TEST: Verify Retry Logic Fix")
    print("=" * 80)

    # Create a mock iteration history
    mock_history = [
        {
            'iteration': 19,
            'success': True,
            'metrics': {'sharpe_ratio': 1.5, 'annual_return': 0.15, 'max_drawdown': 0.10},
            'template': 'Momentum'
        }
    ]

    # Mock the template instantiation to fail twice, then succeed
    instantiation_call_count = [0]

    def mock_instantiate_and_generate(template_name, suggested_params, is_fallback):
        """Mock that fails twice, succeeds on third attempt."""
        instantiation_call_count[0] += 1
        call_num = instantiation_call_count[0]

        logger.info(f"Mock instantiation call #{call_num} for template: {template_name}")

        if call_num <= 2:
            # Fail first two attempts
            raise RuntimeError(f"Mock failure #{call_num}")
        else:
            # Succeed on third attempt
            logger.info(f"✅ Mock success on call #{call_num}")
            return "# Mock strategy code"

    # Patch dependencies
    with patch.object(gen, '_load_iteration_history', return_value=mock_history):
        with patch.object(gen, '_instantiate_and_generate', side_effect=mock_instantiate_and_generate):
            with patch('claude_code_strategy_generator.TemplateFeedbackIntegrator') as MockIntegrator:
                # Setup mock recommendation
                mock_recommendation = Mock()
                mock_recommendation.template_name = 'Turtle'
                mock_recommendation.suggested_params = {'entry_atr': 2.0}
                mock_recommendation.exploration_mode = False
                mock_recommendation.match_score = 0.85
                mock_recommendation.rationale = "Test recommendation"

                mock_integrator_instance = MockIntegrator.return_value
                mock_integrator_instance.recommend_template.return_value = mock_recommendation

                try:
                    # Execute the function for iteration 20 (template-based)
                    logger.info("\n🔄 Calling generate_strategy_with_claude_code(iteration=20)...")
                    code = gen.generate_strategy_with_claude_code(iteration=20, feedback="Test feedback")

                    # Verify results
                    print("\n" + "-" * 80)
                    print("VERIFICATION RESULTS:")
                    print("-" * 80)

                    success = True

                    # Check 1: Should have been called 3 times (2 failures + 1 success)
                    expected_calls = 3
                    if instantiation_call_count[0] == expected_calls:
                        print(f"✅ PASS: Retry logic executed {instantiation_call_count[0]} times (2 retries + 1 success)")
                    else:
                        print(f"❌ FAIL: Expected {expected_calls} calls, got {instantiation_call_count[0]}")
                        success = False

                    # Check 2: Should have returned code
                    if code == "# Mock strategy code":
                        print("✅ PASS: Strategy code returned successfully after retries")
                    else:
                        print(f"❌ FAIL: Expected '# Mock strategy code', got: {code[:50]}")
                        success = False

                    # Check 3: Verify recommendation was called
                    if mock_integrator_instance.recommend_template.called:
                        print("✅ PASS: Template recommendation system was called")
                    else:
                        print("❌ FAIL: Template recommendation was not called")
                        success = False

                    print("-" * 80)

                    if success:
                        print("\n🎉 ALL CHECKS PASSED - Retry logic fix verified!")
                        return True
                    else:
                        print("\n❌ SOME CHECKS FAILED")
                        return False

                except Exception as e:
                    print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
                    import traceback
                    traceback.print_exc()
                    return False


def test_max_retries_exhausted():
    """Test that RuntimeError is raised when max retries are exhausted."""

    print("\n" + "=" * 80)
    print("TEST: Verify Max Retries Exhaustion")
    print("=" * 80)

    # Mock iteration history
    mock_history = [
        {
            'iteration': 19,
            'success': True,
            'metrics': {'sharpe_ratio': 1.5, 'annual_return': 0.15, 'max_drawdown': 0.10},
            'template': 'Momentum'
        }
    ]

    # Mock that always fails
    def mock_instantiate_always_fails(template_name, suggested_params, is_fallback):
        raise RuntimeError("Persistent mock failure")

    # Patch dependencies
    with patch.object(gen, '_load_iteration_history', return_value=mock_history):
        with patch.object(gen, '_instantiate_and_generate', side_effect=mock_instantiate_always_fails):
            with patch('claude_code_strategy_generator.TemplateFeedbackIntegrator') as MockIntegrator:
                # Setup mock recommendation
                mock_recommendation = Mock()
                mock_recommendation.template_name = 'Factor'
                mock_recommendation.suggested_params = {}
                mock_recommendation.exploration_mode = False
                mock_recommendation.match_score = 0.75
                mock_recommendation.rationale = "Test"

                mock_integrator_instance = MockIntegrator.return_value
                mock_integrator_instance.recommend_template.return_value = mock_recommendation

                try:
                    # Should raise RuntimeError after MAX_RETRIES attempts
                    code = gen.generate_strategy_with_claude_code(iteration=20, feedback="")

                    print("❌ FAIL: Should have raised RuntimeError but succeeded")
                    return False

                except RuntimeError as e:
                    error_msg = str(e)

                    print("\n" + "-" * 80)
                    print("VERIFICATION RESULTS:")
                    print("-" * 80)

                    success = True

                    # Check 1: Error message mentions retry attempts
                    if "retry attempts" in error_msg.lower():
                        print("✅ PASS: RuntimeError raised with retry attempt information")
                    else:
                        print(f"❌ FAIL: Error message missing retry info: {error_msg}")
                        success = False

                    # Check 2: Error message mentions attempted templates
                    if "attempted templates" in error_msg.lower():
                        print("✅ PASS: Error message includes attempted templates list")
                    else:
                        print("❌ FAIL: Error message missing attempted templates")
                        success = False

                    print("-" * 80)
                    print(f"Error message: {error_msg}")
                    print("-" * 80)

                    if success:
                        print("\n🎉 ALL CHECKS PASSED - Max retries handling verified!")
                        return True
                    else:
                        print("\n❌ SOME CHECKS FAILED")
                        return False

                except Exception as e:
                    print(f"\n❌ TEST FAILED WITH UNEXPECTED EXCEPTION: {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
                    return False


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("RETRY LOGIC FIX VERIFICATION TEST SUITE")
    print("=" * 80)

    test1_passed = test_retry_logic_with_mock_failures()
    test2_passed = test_max_retries_exhausted()

    print("\n" + "=" * 80)
    print("FINAL RESULTS:")
    print("=" * 80)
    print(f"Test 1 (Retry Logic): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Max Retries): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("=" * 80)

    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED - Exception handling fix verified!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - Review implementation")
        sys.exit(1)
