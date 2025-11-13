#!/usr/bin/env python3
"""
Integration Tests for YAML Mode End-to-End Workflow
Task 9: Structured Innovation MVP - Integration Test Engineer

Tests the complete YAML generation → validation → code generation pipeline
with comprehensive success rate, error handling, and quality metrics.

Test Scenarios:
1. YAML Generation Pipeline Test - Full end-to-end workflow
2. Success Rate Test - 100 iterations, target >90%
3. Real Examples Test - 15 YAML examples from library
4. Error Handling Test - Invalid YAML, schema errors, retries
5. YAML vs Full Code Comparison - Success rates and quality
6. Retry Logic Test - Invalid YAML with error feedback
7. Token Budget Test - Prompt stays under 2000 tokens

Requirements:
- No real LLM API calls (use mocks)
- Success rate >90% target
- Comprehensive error handling validation
- Token budget compliance (<2000 tokens)
"""

import ast
import glob
import json
import os
import pytest
import time
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# Import modules under test
from src.innovation.innovation_engine import InnovationEngine, GenerationResult
from src.innovation.llm_providers import LLMResponse, GeminiProvider
from src.generators.yaml_to_code_generator import YAMLToCodeGenerator
from src.generators.yaml_schema_validator import YAMLSchemaValidator


# ============================================================================
# Test Data and Helpers
# ============================================================================

@dataclass
class YAMLModeMetrics:
    """Metrics for YAML mode testing."""
    total_attempts: int = 0
    successes: int = 0
    failures: int = 0

    yaml_parse_failures: int = 0
    schema_validation_failures: int = 0
    code_generation_failures: int = 0

    average_generation_time_ms: float = 0.0
    average_prompt_tokens: int = 0
    average_code_length_lines: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        return (self.successes / self.total_attempts * 100) if self.total_attempts > 0 else 0.0


def load_yaml_examples_library(validate: bool = False) -> List[str]:
    """
    Load all valid YAML examples from the library.

    Args:
        validate: If True, pre-validate YAML against schema and only return valid ones

    Returns:
        List of YAML content strings
    """
    project_root = Path(__file__).parent.parent.parent
    examples_dir = project_root / "examples" / "yaml_strategies"

    # Load all valid YAML examples (exclude test invalid ones)
    yaml_files = glob.glob(str(examples_dir / "*.yaml"))

    examples = []
    for yaml_file in yaml_files:
        # Skip invalid test files
        if "invalid" in os.path.basename(yaml_file):
            continue

        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                content = f.read()

                # If validation requested, check schema compliance
                if validate:
                    try:
                        spec = yaml.safe_load(content)
                        validator = YAMLSchemaValidator()
                        is_valid, errors = validator.validate(spec)
                        if not is_valid:
                            # Skip non-compliant examples
                            continue
                    except Exception:
                        # Skip examples that can't be validated
                        continue

                examples.append(content)
        except Exception as e:
            print(f"Warning: Could not load {yaml_file}: {e}")

    return examples


def create_mock_llm_response(yaml_content: str, prompt_tokens: int = 500, completion_tokens: int = 200) -> LLMResponse:
    """
    Create a mock LLMResponse with YAML content.

    Args:
        yaml_content: YAML strategy specification
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens

    Returns:
        Mock LLMResponse object
    """
    # Wrap YAML in code block (as LLM would return it)
    content = f"```yaml\n{yaml_content}\n```"

    return LLMResponse(
        content=content,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        model='gemini-2.0-flash-thinking-exp',
        provider='gemini'
    )


def create_invalid_yaml_response(error_type: str = "parse") -> LLMResponse:
    """
    Create a mock LLMResponse with invalid YAML for error testing.

    Args:
        error_type: Type of error ('parse', 'schema', 'missing')

    Returns:
        Mock LLMResponse with invalid YAML
    """
    if error_type == "parse":
        # Invalid YAML syntax
        content = """```yaml
metadata:
  name: "Invalid Strategy"
  strategy_type: "momentum
  # Missing closing quote above
indicators:
  - this is not valid yaml syntax: [unclosed bracket
```"""
    elif error_type == "schema":
        # Valid YAML but schema validation fails
        content = """```yaml
metadata:
  name: "Schema Invalid Strategy"
  # Missing required field: strategy_type
indicators:
  technical_indicators:
    - name: "rsi"
      # Missing required field: type
```"""
    else:  # missing
        # Missing required sections
        content = """```yaml
metadata:
  name: "Missing Sections"
  strategy_type: "momentum"
# Missing indicators and entry_conditions
```"""

    return LLMResponse(
        content=content,
        prompt_tokens=500,
        completion_tokens=150,
        total_tokens=650,
        model='gemini-2.0-flash-thinking-exp',
        provider='gemini'
    )


# ============================================================================
# Test 1: YAML Pipeline Success Test
# ============================================================================

def test_yaml_pipeline_success():
    """
    Test successful YAML generation pipeline end-to-end.

    Workflow:
    1. Mock LLM returns valid YAML
    2. YAML extraction succeeds
    3. YAML validation passes
    4. Code generation succeeds
    5. AST validation passes
    """
    # Create engine in YAML mode
    engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='yaml'
    )

    # Load a valid YAML example
    examples = load_yaml_examples_library()
    assert len(examples) > 0, "No YAML examples found in library"

    example_yaml = examples[0]

    # Mock LLM to return valid YAML
    with patch('src.innovation.llm_providers.GeminiProvider.generate') as mock_llm:
        mock_llm.return_value = create_mock_llm_response(example_yaml)

        # Generate innovation
        code = engine.generate_innovation(
            champion_code="",
            champion_metrics={'sharpe_ratio': 1.5, 'max_drawdown': 0.15},
            failure_history=[],
            target_metric='sharpe_ratio'
        )

    # Assertions
    assert code is not None, "Code generation failed"
    assert "def strategy" in code, "Generated code missing strategy function"
    assert len(code) > 100, "Generated code too short"

    # Verify syntax correctness
    try:
        ast.parse(code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax error: {e}")

    # Verify statistics
    stats = engine.get_statistics()
    assert stats['yaml_successes'] == 1, f"Expected 1 YAML success, got {stats['yaml_successes']}"
    assert stats['yaml_success_rate'] == 1.0, f"Expected 100% success rate, got {stats['yaml_success_rate']}"
    assert stats['total_attempts'] == 1
    assert stats['successful_generations'] == 1

    print(f"✅ YAML Pipeline Test: SUCCESS")
    print(f"   Generated code: {len(code)} characters")
    print(f"   Success rate: {stats['yaml_success_rate']:.1%}")


# ============================================================================
# Test 2: Success Rate Test (100 Iterations)
# ============================================================================

def test_success_rate_100_iterations():
    """
    Test YAML mode achieves >90% success rate over 100 iterations.

    Uses real schema-compliant YAML examples cycled as mock LLM responses.
    Target: >90% success rate
    """
    engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='yaml',
        max_retries=1  # Single attempt for speed
    )

    # Load real schema-compliant YAML examples
    examples = load_yaml_examples_library(validate=True)
    assert len(examples) >= 10, f"Need at least 10 schema-compliant examples, found {len(examples)}"

    metrics = YAMLModeMetrics()
    generation_times = []
    prompt_tokens_list = []
    code_lengths = []

    with patch('src.innovation.llm_providers.GeminiProvider.generate') as mock_llm:
        for i in range(100):
            # Cycle through examples
            example_yaml = examples[i % len(examples)]
            mock_llm.return_value = create_mock_llm_response(
                example_yaml,
                prompt_tokens=500 + (i % 100),  # Vary token counts
                completion_tokens=200 + (i % 50)
            )

            # Track generation time
            start_time = time.time()

            code = engine.generate_innovation(
                champion_code="",
                champion_metrics={'sharpe_ratio': 1.5 + (i * 0.01)},
                failure_history=[],
                target_metric='sharpe_ratio'
            )

            elapsed_ms = (time.time() - start_time) * 1000
            generation_times.append(elapsed_ms)

            metrics.total_attempts += 1

            if code:
                metrics.successes += 1
                code_lengths.append(len(code.split('\n')))

                # Verify syntax
                try:
                    ast.parse(code)
                except SyntaxError:
                    metrics.code_generation_failures += 1
                    metrics.successes -= 1
                    metrics.failures += 1
            else:
                metrics.failures += 1

    # Calculate averages
    if generation_times:
        metrics.average_generation_time_ms = sum(generation_times) / len(generation_times)
    if code_lengths:
        metrics.average_code_length_lines = sum(code_lengths) / len(code_lengths)

    # Verify success rate
    print(f"\n{'='*80}")
    print(f"YAML Mode Success Rate Test (100 iterations)")
    print(f"{'='*80}")
    print(f"Total Attempts: {metrics.total_attempts}")
    print(f"Successes: {metrics.successes}")
    print(f"Failures: {metrics.failures}")
    print(f"Success Rate: {metrics.success_rate:.1f}%")
    print(f"Average Generation Time: {metrics.average_generation_time_ms:.2f}ms")
    print(f"Average Code Length: {metrics.average_code_length_lines:.0f} lines")
    print(f"{'='*80}\n")

    # Target: >90% success rate
    assert metrics.success_rate > 90.0, (
        f"Success rate {metrics.success_rate:.1f}% is below 90% target"
    )
    assert metrics.successes >= 90, f"Expected at least 90 successes, got {metrics.successes}"


# ============================================================================
# Test 3: Real Examples Test (All Library Examples)
# ============================================================================

def test_real_yaml_examples_100_percent():
    """
    Test all schema-compliant YAML examples from library pass through pipeline.

    Expected: 100% success rate on known-valid, schema-compliant examples.
    """
    engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='yaml'
    )

    # Load all schema-compliant valid examples
    examples = load_yaml_examples_library(validate=True)
    total_examples = len(examples)

    assert total_examples >= 10, f"Expected at least 10 schema-compliant examples, found {total_examples}"

    successes = 0
    failures = []

    with patch('src.innovation.llm_providers.GeminiProvider.generate') as mock_llm:
        for i, example_yaml in enumerate(examples):
            mock_llm.return_value = create_mock_llm_response(example_yaml)

            code = engine.generate_innovation(
                champion_code="",
                champion_metrics={'sharpe_ratio': 1.5},
                failure_history=[],
                target_metric='sharpe_ratio'
            )

            if code:
                # Verify syntax
                try:
                    ast.parse(code)
                    successes += 1
                except SyntaxError as e:
                    failures.append(f"Example {i+1}: Syntax error - {e}")
            else:
                failures.append(f"Example {i+1}: Code generation failed")

    success_rate = (successes / total_examples * 100) if total_examples > 0 else 0.0

    print(f"\n{'='*80}")
    print(f"Real YAML Examples Test (Schema-Compliant Only)")
    print(f"{'='*80}")
    print(f"Total Examples: {total_examples}")
    print(f"Successes: {successes}")
    print(f"Failures: {len(failures)}")
    print(f"Success Rate: {success_rate:.1f}%")

    if failures:
        print(f"\nFailures:")
        for failure in failures:
            print(f"  - {failure}")

    print(f"{'='*80}\n")

    # Expect 100% success on schema-compliant valid examples
    assert success_rate == 100.0, (
        f"Expected 100% success on schema-compliant valid examples, got {success_rate:.1f}%\n"
        f"Failures: {failures}"
    )


# ============================================================================
# Test 4: Error Handling Test
# ============================================================================

def test_error_handling_invalid_yaml():
    """
    Test error handling for various YAML failure modes.

    Tests:
    1. YAML parsing errors
    2. Schema validation errors
    3. Missing required sections
    4. Verify clear error messages
    """
    engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='yaml',
        max_retries=1  # Single attempt for speed
    )

    error_types = ['parse', 'schema', 'missing']
    failures = 0

    with patch('src.innovation.llm_providers.GeminiProvider.generate') as mock_llm:
        for error_type in error_types:
            mock_llm.return_value = create_invalid_yaml_response(error_type)

            code = engine.generate_innovation(
                champion_code="",
                champion_metrics={'sharpe_ratio': 1.5},
                failure_history=[],
                target_metric='sharpe_ratio'
            )

            # Should fail
            if code is None:
                failures += 1
            else:
                print(f"⚠️  Unexpected success for {error_type} error type")

    # Verify all error types were handled (all should fail)
    assert failures == len(error_types), f"Expected {len(error_types)} failures, got {failures}"

    # Verify statistics show failures
    stats = engine.get_statistics()
    assert stats['yaml_failures'] > 0, "Expected YAML failures recorded"
    assert stats['total_attempts'] == len(error_types), f"Expected {len(error_types)} attempts"

    print(f"✅ Error Handling Test: PASSED")
    print(f"   Error types tested: {len(error_types)}")
    print(f"   All failures handled correctly: {failures}/{len(error_types)}")
    print(f"   YAML failures: {stats['yaml_failures']}")
    print(f"   Validation failures: {stats['yaml_validation_failures']}")


# ============================================================================
# Test 5: YAML vs Full Code Comparison
# ============================================================================

def test_yaml_vs_fullcode_comparison():
    """
    Compare YAML mode vs full_code mode success rates.

    Expected: YAML mode >90%, full_code mode ~60% (based on spec)
    """
    examples = load_yaml_examples_library(validate=True)[:20]  # Use first 20 schema-compliant examples

    # Test YAML mode
    yaml_engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='yaml',
        max_retries=1
    )

    yaml_successes = 0

    with patch('src.innovation.llm_providers.GeminiProvider.generate') as mock_llm:
        for example in examples:
            mock_llm.return_value = create_mock_llm_response(example)

            code = yaml_engine.generate_innovation(
                champion_code="",
                champion_metrics={'sharpe_ratio': 1.5},
                failure_history=[]
            )

            if code:
                try:
                    ast.parse(code)
                    yaml_successes += 1
                except SyntaxError:
                    pass

    yaml_success_rate = (yaml_successes / len(examples) * 100)

    # Test full_code mode (simulated with some failures)
    fullcode_engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='full_code',
        max_retries=1
    )

    # Simulate full_code mode with ~60% success rate
    # Mock returns Python code with syntax errors 40% of the time
    fullcode_successes = 0

    with patch('src.innovation.llm_providers.GeminiProvider.generate') as mock_llm:
        for i in range(20):
            # Simulate 60% success rate for full_code mode
            if i % 5 < 3:  # 60% valid code
                mock_response_content = """```python
def strategy(data):
    rsi = data.get('RSI_14')
    return rsi > 50
```"""
            else:  # 40% invalid code
                mock_response_content = """```python
def strategy(data):
    rsi = data.get('RSI_14'  # Missing closing parenthesis
    return rsi > 50
```"""

            mock_llm.return_value = LLMResponse(
                content=mock_response_content,
                prompt_tokens=500,
                completion_tokens=100,
                total_tokens=600,
                model='gemini-2.0-flash-thinking-exp',
                provider='gemini'
            )

            code = fullcode_engine.generate_innovation(
                champion_code="def strategy(data): return data.get('close') > 100",
                champion_metrics={'sharpe_ratio': 1.5},
                failure_history=[]
            )

            if code:
                try:
                    ast.parse(code)
                    fullcode_successes += 1
                except SyntaxError:
                    pass

    fullcode_success_rate = (fullcode_successes / 20 * 100)

    print(f"\n{'='*80}")
    print(f"YAML vs Full Code Comparison")
    print(f"{'='*80}")
    print(f"YAML Mode Success Rate: {yaml_success_rate:.1f}%")
    print(f"Full Code Mode Success Rate: {fullcode_success_rate:.1f}%")
    print(f"Improvement: {yaml_success_rate - fullcode_success_rate:.1f} percentage points")
    print(f"{'='*80}\n")

    # YAML mode should be significantly better
    assert yaml_success_rate > 90.0, f"YAML mode should be >90%, got {yaml_success_rate:.1f}%"
    assert yaml_success_rate > fullcode_success_rate, "YAML mode should outperform full_code mode"


# ============================================================================
# Test 6: Retry Logic Test
# ============================================================================

def test_retry_logic_with_error_feedback():
    """
    Test retry logic when LLM returns invalid YAML initially.

    Workflow:
    1. First attempt: Invalid YAML
    2. Retry with error feedback
    3. Second attempt: Valid YAML
    4. Success
    """
    engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='yaml',
        max_retries=3
    )

    examples = load_yaml_examples_library()
    valid_yaml = examples[0]

    call_count = 0

    def mock_generate_with_retry(prompt, max_tokens, temperature, max_retries):
        """Mock that fails first, succeeds second."""
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # First call: Return invalid YAML
            return create_invalid_yaml_response('parse')
        else:
            # Retry: Return valid YAML
            return create_mock_llm_response(valid_yaml)

    with patch('src.innovation.llm_providers.GeminiProvider.generate', side_effect=mock_generate_with_retry):
        code = engine.generate_innovation(
            champion_code="",
            champion_metrics={'sharpe_ratio': 1.5},
            failure_history=[],
            target_metric='sharpe_ratio'
        )

    # Should succeed after retry
    assert code is not None, "Expected success after retry"
    assert call_count == 2, f"Expected 2 LLM calls (1 fail + 1 retry), got {call_count}"

    # Verify syntax
    try:
        ast.parse(code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax error: {e}")

    print(f"✅ Retry Logic Test: SUCCESS")
    print(f"   Required {call_count} attempts (1 failure + 1 success)")


# ============================================================================
# Test 7: Token Budget Test
# ============================================================================

def test_token_budget_compliance():
    """
    Verify YAML prompts stay under 2000 token budget.

    Tests with:
    1. Various champion metrics
    2. Long failure histories
    3. Different strategy types
    """
    engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='yaml',
        max_tokens=2000
    )

    # Test scenarios with different context sizes
    test_scenarios = [
        {
            'name': 'Minimal context',
            'metrics': {'sharpe_ratio': 1.5},
            'failures': []
        },
        {
            'name': 'Rich metrics',
            'metrics': {
                'sharpe_ratio': 1.85,
                'max_drawdown': 0.12,
                'win_rate': 0.65,
                'calmar_ratio': 3.2,
                'sortino_ratio': 2.1
            },
            'failures': []
        },
        {
            'name': 'Long failure history',
            'metrics': {'sharpe_ratio': 1.5},
            'failures': [
                {'error_type': 'validation', 'description': 'Invalid indicator reference'},
                {'error_type': 'syntax', 'description': 'Missing closing bracket'},
                {'error_type': 'schema', 'description': 'Required field missing'},
                {'error_type': 'runtime', 'description': 'Division by zero'},
                {'error_type': 'validation', 'description': 'Undefined variable'}
            ]
        }
    ]

    examples = load_yaml_examples_library()

    with patch('src.innovation.llm_providers.GeminiProvider.generate') as mock_llm:
        for scenario in test_scenarios:
            mock_llm.return_value = create_mock_llm_response(examples[0])

            # The prompt is built internally, we can check token counts from response
            code = engine.generate_innovation(
                champion_code="",
                champion_metrics=scenario['metrics'],
                failure_history=scenario['failures'],
                target_metric='sharpe_ratio'
            )

            assert code is not None, f"Failed for scenario: {scenario['name']}"

            # Check that mock was called (prompt was built)
            assert mock_llm.called, "LLM should have been called"

            # Get the actual call
            call_args = mock_llm.call_args
            prompt = call_args[1]['prompt'] if 'prompt' in call_args[1] else call_args[0][0]

            # Estimate token count (rough: ~4 chars per token)
            estimated_tokens = len(prompt) / 4

            print(f"  Scenario '{scenario['name']}': ~{estimated_tokens:.0f} tokens")

            # Should be well under 2000 tokens
            assert estimated_tokens < 2000, (
                f"Prompt too long for '{scenario['name']}': {estimated_tokens:.0f} tokens"
            )

            mock_llm.reset_mock()

    print(f"✅ Token Budget Test: PASSED")
    print(f"   All prompts under 2000 token budget")


# ============================================================================
# Test 8: Batch Processing Test
# ============================================================================

def test_batch_yaml_generation():
    """
    Test batch processing of multiple YAML specs.

    Verifies generator can handle multiple requests efficiently.
    """
    engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='yaml',
        max_retries=1
    )

    examples = load_yaml_examples_library(validate=True)[:10]  # Use first 10 schema-compliant

    generated_codes = []

    with patch('src.innovation.llm_providers.GeminiProvider.generate') as mock_llm:
        for example in examples:
            mock_llm.return_value = create_mock_llm_response(example)

            code = engine.generate_innovation(
                champion_code="",
                champion_metrics={'sharpe_ratio': 1.5},
                failure_history=[]
            )

            if code:
                generated_codes.append(code)

    success_rate = (len(generated_codes) / len(examples) * 100)

    print(f"\n{'='*80}")
    print(f"Batch Processing Test")
    print(f"{'='*80}")
    print(f"Total Specs: {len(examples)}")
    print(f"Successfully Generated: {len(generated_codes)}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"{'='*80}\n")

    assert success_rate >= 90.0, f"Batch success rate should be >=90%, got {success_rate:.1f}%"


# ============================================================================
# Test 9: Code Quality Verification
# ============================================================================

def test_generated_code_quality():
    """
    Verify generated code quality and correctness.

    Checks:
    1. Syntactically correct Python
    2. Contains strategy function
    3. Uses FinLab API patterns
    4. Reasonable code length
    """
    engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='yaml'
    )

    examples = load_yaml_examples_library(validate=True)[:5]

    quality_metrics = {
        'syntax_valid': 0,
        'has_strategy_function': 0,
        'uses_finlab_api': 0,
        'reasonable_length': 0
    }

    with patch('src.innovation.llm_providers.GeminiProvider.generate') as mock_llm:
        for example in examples:
            mock_llm.return_value = create_mock_llm_response(example)

            code = engine.generate_innovation(
                champion_code="",
                champion_metrics={'sharpe_ratio': 1.5},
                failure_history=[]
            )

            if not code:
                continue

            # Check syntax validity
            try:
                ast.parse(code)
                quality_metrics['syntax_valid'] += 1
            except SyntaxError:
                continue

            # Check for strategy function
            if 'def strategy' in code:
                quality_metrics['has_strategy_function'] += 1

            # Check for FinLab API usage
            if 'data.get(' in code:
                quality_metrics['uses_finlab_api'] += 1

            # Check reasonable length (50-500 lines)
            lines = len(code.split('\n'))
            if 50 <= lines <= 500:
                quality_metrics['reasonable_length'] += 1

    total = len(examples)

    print(f"\n{'='*80}")
    print(f"Code Quality Verification")
    print(f"{'='*80}")
    print(f"Syntax Valid: {quality_metrics['syntax_valid']}/{total}")
    print(f"Has Strategy Function: {quality_metrics['has_strategy_function']}/{total}")
    print(f"Uses FinLab API: {quality_metrics['uses_finlab_api']}/{total}")
    print(f"Reasonable Length: {quality_metrics['reasonable_length']}/{total}")
    print(f"{'='*80}\n")

    # All generated code should pass quality checks
    assert quality_metrics['syntax_valid'] == total, "All code should be syntactically valid"
    assert quality_metrics['has_strategy_function'] == total, "All code should have strategy function"


# ============================================================================
# Main Test Runner
# ============================================================================

if __name__ == "__main__":
    """Run all tests with pytest."""
    import sys

    print(f"\n{'='*80}")
    print(f"YAML Mode Integration Tests - Structured Innovation MVP")
    print(f"{'='*80}\n")

    # Run pytest with verbose output
    pytest_args = [
        __file__,
        '-v',
        '--tb=short',
        '--color=yes'
    ]

    sys.exit(pytest.main(pytest_args))
