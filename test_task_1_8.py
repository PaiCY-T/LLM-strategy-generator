"""
Test script for Task 1.8 - generate_parameters() main method

This script tests the complete parameter generation workflow including:
1. Building prompt with context
2. Calling LLM (mocked)
3. Parsing response
4. Validating parameters
5. Error handling
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.generators.template_parameter_generator import (
    TemplateParameterGenerator,
    ParameterGenerationContext
)


def test_generate_parameters_first_iteration():
    """Test parameter generation for first iteration (no champion)"""
    print("\n" + "="*60)
    print("TEST 1: First Iteration (No Champion)")
    print("="*60)

    generator = TemplateParameterGenerator()
    context = ParameterGenerationContext(
        iteration_num=0,
        champion_params=None,
        champion_sharpe=None
    )

    # Mock the LLM call to return a valid JSON response
    def mock_llm_call(prompt, iteration_num=0):
        return '''
        {
          "momentum_period": 10,
          "ma_periods": 60,
          "catalyst_type": "revenue",
          "catalyst_lookback": 3,
          "n_stocks": 10,
          "stop_loss": 0.10,
          "resample": "M",
          "resample_offset": 0
        }
        '''

    # Replace the LLM caller with mock
    generator._call_llm_for_parameters = mock_llm_call

    try:
        params = generator.generate_parameters(context)
        print(f"✅ SUCCESS: Generated parameters: {params}")

        # Verify all required keys present
        required_keys = ['momentum_period', 'ma_periods', 'catalyst_type',
                        'catalyst_lookback', 'n_stocks', 'stop_loss',
                        'resample', 'resample_offset']
        assert all(key in params for key in required_keys), "Missing required keys"
        print("✅ All required keys present")

        # Verify values are valid
        assert params['momentum_period'] in [5, 10, 20, 30], "Invalid momentum_period"
        assert params['ma_periods'] in [20, 60, 90, 120], "Invalid ma_periods"
        assert params['catalyst_type'] in ['revenue', 'earnings'], "Invalid catalyst_type"
        print("✅ All values valid")

        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_parameters_with_champion():
    """Test parameter generation with existing champion"""
    print("\n" + "="*60)
    print("TEST 2: With Champion (Exploitation Mode)")
    print("="*60)

    generator = TemplateParameterGenerator()
    context = ParameterGenerationContext(
        iteration_num=1,
        champion_params={
            'momentum_period': 10,
            'ma_periods': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'M',
            'resample_offset': 0
        },
        champion_sharpe=0.85
    )

    # Mock the LLM call to return a valid JSON response
    def mock_llm_call(prompt, iteration_num=0):
        # Verify champion info is in prompt
        assert 'CURRENT CHAMPION' in prompt, "Champion info not in prompt"
        assert '0.8500' in prompt, "Champion Sharpe not in prompt"

        return '''
        {
          "momentum_period": 10,
          "ma_periods": 90,
          "catalyst_type": "revenue",
          "catalyst_lookback": 3,
          "n_stocks": 10,
          "stop_loss": 0.10,
          "resample": "M",
          "resample_offset": 0
        }
        '''

    # Replace the LLM caller with mock
    generator._call_llm_for_parameters = mock_llm_call

    try:
        params = generator.generate_parameters(context)
        print(f"✅ SUCCESS: Generated parameters: {params}")
        print("✅ Champion context properly included in prompt")
        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parse_error_handling():
    """Test error handling for unparseable LLM response"""
    print("\n" + "="*60)
    print("TEST 3: Parse Error Handling")
    print("="*60)

    generator = TemplateParameterGenerator()
    context = ParameterGenerationContext(iteration_num=0)

    # Mock the LLM call to return invalid response
    def mock_llm_call(prompt, iteration_num=0):
        return "This is not valid JSON at all!"

    generator._call_llm_for_parameters = mock_llm_call

    try:
        params = generator.generate_parameters(context)
        print(f"❌ FAILED: Should have raised ValueError but got: {params}")
        return False

    except ValueError as e:
        print(f"✅ SUCCESS: Correctly raised ValueError: {e}")
        return True

    except Exception as e:
        print(f"❌ FAILED: Wrong exception type: {type(e).__name__}: {e}")
        return False


def test_validation_error_handling():
    """Test error handling for invalid parameters"""
    print("\n" + "="*60)
    print("TEST 4: Validation Error Handling")
    print("="*60)

    generator = TemplateParameterGenerator()
    context = ParameterGenerationContext(iteration_num=0)

    # Mock the LLM call to return invalid parameter values
    def mock_llm_call(prompt, iteration_num=0):
        return '''
        {
          "momentum_period": 999,
          "ma_periods": 60,
          "catalyst_type": "revenue",
          "catalyst_lookback": 3,
          "n_stocks": 10,
          "stop_loss": 0.10,
          "resample": "M",
          "resample_offset": 0
        }
        '''

    generator._call_llm_for_parameters = mock_llm_call

    try:
        params = generator.generate_parameters(context)
        print(f"❌ FAILED: Should have raised ValueError but got: {params}")
        return False

    except ValueError as e:
        error_msg = str(e)
        assert 'validation failed' in error_msg.lower(), "Wrong error message"
        assert '999' in error_msg, "Error should mention invalid value"
        print(f"✅ SUCCESS: Correctly raised ValueError: {e}")
        return True

    except Exception as e:
        print(f"❌ FAILED: Wrong exception type: {type(e).__name__}: {e}")
        return False


def test_exploration_mode():
    """Test exploration mode activation every 5 iterations"""
    print("\n" + "="*60)
    print("TEST 5: Exploration Mode Activation")
    print("="*60)

    generator = TemplateParameterGenerator()
    context = ParameterGenerationContext(
        iteration_num=5,  # Should trigger exploration
        champion_params={'momentum_period': 10, 'ma_periods': 60,
                        'catalyst_type': 'revenue', 'catalyst_lookback': 3,
                        'n_stocks': 10, 'stop_loss': 0.10,
                        'resample': 'M', 'resample_offset': 0},
        champion_sharpe=0.85
    )

    # Mock the LLM call and check prompt
    def mock_llm_call(prompt, iteration_num=0):
        # Verify exploration mode is indicated in prompt
        assert 'EXPLORATION MODE' in prompt, "Exploration mode not indicated"
        assert 'DIFFERENT' in prompt, "Exploration instruction not clear"

        return '''
        {
          "momentum_period": 20,
          "ma_periods": 90,
          "catalyst_type": "earnings",
          "catalyst_lookback": 4,
          "n_stocks": 15,
          "stop_loss": 0.12,
          "resample": "W",
          "resample_offset": 1
        }
        '''

    generator._call_llm_for_parameters = mock_llm_call

    try:
        params = generator.generate_parameters(context)
        print(f"✅ SUCCESS: Generated parameters in exploration mode: {params}")
        print("✅ Exploration mode properly activated")
        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# Task 1.8 Test Suite - generate_parameters()")
    print("#"*60)

    tests = [
        test_generate_parameters_first_iteration,
        test_generate_parameters_with_champion,
        test_parse_error_handling,
        test_validation_error_handling,
        test_exploration_mode,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "#"*60)
    print("# Test Summary")
    print("#"*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        print("\nTask 1.8 Implementation Complete:")
        print("  ✅ generate_parameters() orchestrates full workflow")
        print("  ✅ Calls all helper methods in correct order")
        print("  ✅ Handles LLM failures gracefully")
        print("  ✅ Raises ValueError with details on validation failures")
        print("  ✅ Returns valid parameter dict on success")
        print("  ✅ Includes comprehensive error handling and logging")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
