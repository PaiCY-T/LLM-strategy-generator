"""
Unit tests for InnovationEngine structured mode (YAML generation).

Tests YAML mode integration with StructuredPromptBuilder and YAMLToCodeGenerator.
Validates mode selection, YAML workflow, retry logic, and statistics tracking.

Task 7 of structured-innovation-mvp spec.
Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.innovation.innovation_engine import InnovationEngine, GenerationResult
from src.innovation.llm_providers import LLMResponse


class TestInnovationEngineYAMLMode:
    """Test YAML mode initialization and configuration."""

    def test_yaml_mode_initialization(self):
        """Test that YAML mode initializes structured components."""
        engine = InnovationEngine(
            provider_name='gemini',
            generation_mode='yaml'
        )

        assert engine.generation_mode == 'yaml'
        assert engine.structured_prompt_builder is not None
        assert engine.yaml_generator is not None

    def test_full_code_mode_initialization(self):
        """Test that full_code mode does not initialize YAML components."""
        engine = InnovationEngine(
            provider_name='gemini',
            generation_mode='full_code'
        )

        assert engine.generation_mode == 'full_code'
        assert engine.structured_prompt_builder is None
        assert engine.yaml_generator is None

    def test_default_mode_is_full_code(self):
        """Test that default generation mode is full_code for backward compatibility."""
        engine = InnovationEngine(provider_name='gemini')

        assert engine.generation_mode == 'full_code'
        assert engine.structured_prompt_builder is None


class TestYAMLGenerationWorkflow:
    """Test YAML generation workflow end-to-end."""

    @patch('src.innovation.innovation_engine.YAMLToCodeGenerator')
    @patch('src.innovation.innovation_engine.StructuredPromptBuilder')
    def test_yaml_generation_success(self, mock_prompt_builder_class, mock_yaml_gen_class):
        """Test successful YAML generation workflow."""
        # Setup mocks
        mock_prompt_builder = Mock()
        mock_prompt_builder.build_compact_prompt.return_value = "Generate YAML strategy"
        mock_prompt_builder_class.return_value = mock_prompt_builder

        mock_yaml_gen = Mock()
        valid_python_code = "def strategy(data):\n    return data.get('price:收盤價') > 100"
        mock_yaml_gen.generate.return_value = (valid_python_code, [])
        mock_yaml_gen_class.return_value = mock_yaml_gen

        # Create engine
        engine = InnovationEngine(
            provider_name='gemini',
            generation_mode='yaml'
        )

        # Mock LLM response
        mock_response = LLMResponse(
            content="```yaml\nmetadata:\n  name: test_strategy\n  description: Test\n  strategy_type: momentum\n  rebalancing_frequency: M\n```",
            provider='gemini',
            model='gemini-pro',
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        engine.provider.generate = Mock(return_value=mock_response)

        # Test generation
        champion_metrics = {
            'sharpe_ratio': 1.5,
            'annual_return': 0.12,
            'max_drawdown': -0.15
        }

        code = engine.generate_innovation(
            champion_code="",  # Not used in YAML mode
            champion_metrics=champion_metrics,
            failure_history=None,
            target_metric='sharpe_ratio'
        )

        # Assertions
        assert code == valid_python_code
        assert engine.yaml_successes == 1
        assert engine.yaml_failures == 0
        assert engine.successful_generations == 1

    @patch('src.innovation.innovation_engine.YAMLToCodeGenerator')
    @patch('src.innovation.innovation_engine.StructuredPromptBuilder')
    def test_yaml_extraction_from_code_blocks(self, mock_prompt_builder_class, mock_yaml_gen_class):
        """Test YAML extraction from different code block formats."""
        # Setup mocks
        mock_prompt_builder = Mock()
        mock_prompt_builder.build_compact_prompt.return_value = "Generate YAML"
        mock_prompt_builder_class.return_value = mock_prompt_builder

        mock_yaml_gen = Mock()
        mock_yaml_gen.generate.return_value = ("def strategy(data): pass", [])
        mock_yaml_gen_class.return_value = mock_yaml_gen

        engine = InnovationEngine(
            provider_name='gemini',
            generation_mode='yaml'
        )

        # Test extraction from ```yaml block
        yaml_content = "metadata:\n  name: test\n  description: Test\n  strategy_type: momentum\n  rebalancing_frequency: M"
        response_text = f"```yaml\n{yaml_content}\n```"

        extracted = engine._extract_yaml(response_text)
        assert extracted == yaml_content

        # Test extraction from generic ``` block
        response_text = f"```\n{yaml_content}\n```"
        extracted = engine._extract_yaml(response_text)
        assert extracted == yaml_content

        # Test extraction without code blocks
        response_text = f"Here is the strategy:\n\n{yaml_content}\n\nThat's it."
        extracted = engine._extract_yaml(response_text)
        assert yaml_content in extracted

    @patch('src.innovation.innovation_engine.YAMLToCodeGenerator')
    @patch('src.innovation.innovation_engine.StructuredPromptBuilder')
    def test_yaml_validation_retry_logic(self, mock_prompt_builder_class, mock_yaml_gen_class):
        """Test retry logic on YAML validation failures."""
        # Setup mocks
        mock_prompt_builder = Mock()
        mock_prompt_builder.build_compact_prompt.return_value = "Generate YAML"
        mock_prompt_builder_class.return_value = mock_prompt_builder

        mock_yaml_gen = Mock()
        # First attempt fails validation, second succeeds
        mock_yaml_gen.generate.side_effect = [
            (None, ["Missing required field: metadata.name"]),
            ("def strategy(data): pass", [])
        ]
        mock_yaml_gen_class.return_value = mock_yaml_gen

        engine = InnovationEngine(
            provider_name='gemini',
            generation_mode='yaml',
            max_retries=3
        )

        # Mock LLM responses
        valid_yaml = "metadata:\n  name: test\n  description: Test\n  strategy_type: momentum\n  rebalancing_frequency: M"

        responses = [
            LLMResponse(
                content=f"```yaml\n{valid_yaml}\n```",
                provider='gemini',
                model='gemini-pro',
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150
            ),
            LLMResponse(
                content=f"```yaml\n{valid_yaml}\n```",
                provider='gemini',
                model='gemini-pro',
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150
            )
        ]
        engine.provider.generate = Mock(side_effect=responses)

        # Test generation with retry
        code = engine.generate_innovation(
            champion_code="",
            champion_metrics={'sharpe_ratio': 1.5},
            failure_history=None
        )

        # Should succeed on second attempt
        assert code == "def strategy(data): pass"
        assert engine.yaml_successes == 1
        assert engine.yaml_validation_failures == 1

    @patch('src.innovation.innovation_engine.YAMLToCodeGenerator')
    @patch('src.innovation.innovation_engine.StructuredPromptBuilder')
    def test_yaml_parsing_error_retry(self, mock_prompt_builder_class, mock_yaml_gen_class):
        """Test retry logic on YAML parsing errors."""
        # Setup mocks
        mock_prompt_builder = Mock()
        mock_prompt_builder.build_compact_prompt.return_value = "Generate YAML"
        mock_prompt_builder_class.return_value = mock_prompt_builder

        mock_yaml_gen = Mock()
        mock_yaml_gen.generate.return_value = ("def strategy(data): pass", [])
        mock_yaml_gen_class.return_value = mock_yaml_gen

        engine = InnovationEngine(
            provider_name='gemini',
            generation_mode='yaml',
            max_retries=3
        )

        # Mock LLM responses - first has invalid YAML, second is valid
        responses = [
            LLMResponse(
                content="```yaml\ninvalid: yaml: syntax:\n```",  # Invalid YAML
                provider='gemini',
                model='gemini-pro',
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150
            ),
            LLMResponse(
                content="```yaml\nmetadata:\n  name: test\n  description: Test\n  strategy_type: momentum\n  rebalancing_frequency: M\n```",
                provider='gemini',
                model='gemini-pro',
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150
            )
        ]
        engine.provider.generate = Mock(side_effect=responses)

        # Test generation
        code = engine.generate_innovation(
            champion_code="",
            champion_metrics={'sharpe_ratio': 1.5},
            failure_history=None
        )

        # Should succeed on second attempt
        assert code == "def strategy(data): pass"
        assert engine.yaml_validation_failures == 1


class TestModeSelection:
    """Test mode selection and routing."""

    @patch('src.innovation.innovation_engine.YAMLToCodeGenerator')
    @patch('src.innovation.innovation_engine.StructuredPromptBuilder')
    def test_yaml_mode_routes_to_yaml_generation(self, mock_prompt_builder_class, mock_yaml_gen_class):
        """Test that YAML mode routes to _generate_yaml_innovation."""
        # Setup mocks
        mock_prompt_builder = Mock()
        mock_prompt_builder.build_compact_prompt.return_value = "prompt"
        mock_prompt_builder_class.return_value = mock_prompt_builder

        mock_yaml_gen = Mock()
        mock_yaml_gen.generate.return_value = ("code", [])
        mock_yaml_gen_class.return_value = mock_yaml_gen

        engine = InnovationEngine(
            provider_name='gemini',
            generation_mode='yaml'
        )

        # Mock LLM response
        mock_response = LLMResponse(
            content="```yaml\nmetadata:\n  name: test\n  description: Test\n  strategy_type: momentum\n  rebalancing_frequency: M\n```",
            provider='gemini',
            model='gemini-pro',
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        engine.provider.generate = Mock(return_value=mock_response)

        # Spy on _generate_yaml_innovation
        with patch.object(engine, '_generate_yaml_innovation', wraps=engine._generate_yaml_innovation) as spy:
            engine.generate_innovation(
                champion_code="",
                champion_metrics={'sharpe_ratio': 1.5},
                failure_history=None
            )

            # Verify YAML method was called
            spy.assert_called_once()

    def test_full_code_mode_routes_to_full_code_generation(self):
        """Test that full_code mode routes to _generate_full_code_innovation."""
        engine = InnovationEngine(
            provider_name='gemini',
            generation_mode='full_code'
        )

        # Mock LLM response
        mock_response = LLMResponse(
            content="```python\ndef strategy(data):\n    return data.get('price:收盤價') > 100\n```",
            provider='gemini',
            model='gemini-pro',
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        engine.provider.generate = Mock(return_value=mock_response)

        # Spy on _generate_full_code_innovation
        with patch.object(engine, '_generate_full_code_innovation', wraps=engine._generate_full_code_innovation) as spy:
            engine.generate_innovation(
                champion_code="def old_strategy(data): pass",
                champion_metrics={'sharpe_ratio': 1.5},
                failure_history=None
            )

            # Verify full code method was called
            spy.assert_called_once()


class TestStatisticsTracking:
    """Test statistics tracking for different modes."""

    @patch('src.innovation.innovation_engine.YAMLToCodeGenerator')
    @patch('src.innovation.innovation_engine.StructuredPromptBuilder')
    def test_yaml_mode_statistics(self, mock_prompt_builder_class, mock_yaml_gen_class):
        """Test that YAML mode tracks mode-specific statistics."""
        # Setup mocks
        mock_prompt_builder = Mock()
        mock_prompt_builder.build_compact_prompt.return_value = "prompt"
        mock_prompt_builder_class.return_value = mock_prompt_builder

        mock_yaml_gen = Mock()
        mock_yaml_gen.generate.return_value = ("code", [])
        mock_yaml_gen_class.return_value = mock_yaml_gen

        engine = InnovationEngine(
            provider_name='gemini',
            generation_mode='yaml'
        )

        # Mock LLM response
        mock_response = LLMResponse(
            content="```yaml\nmetadata:\n  name: test\n  description: Test\n  strategy_type: momentum\n  rebalancing_frequency: M\n```",
            provider='gemini',
            model='gemini-pro',
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        engine.provider.generate = Mock(return_value=mock_response)

        # Generate
        engine.generate_innovation(
            champion_code="",
            champion_metrics={'sharpe_ratio': 1.5},
            failure_history=None
        )

        # Check statistics
        stats = engine.get_statistics()

        assert stats['generation_mode'] == 'yaml'
        assert 'yaml_successes' in stats
        assert 'yaml_failures' in stats
        assert 'yaml_validation_failures' in stats
        assert 'yaml_success_rate' in stats
        assert stats['yaml_successes'] == 1
        assert stats['yaml_failures'] == 0

    def test_full_code_mode_statistics_no_yaml_fields(self):
        """Test that full_code mode does not include YAML statistics."""
        engine = InnovationEngine(
            provider_name='gemini',
            generation_mode='full_code'
        )

        stats = engine.get_statistics()

        assert stats['generation_mode'] == 'full_code'
        assert 'yaml_successes' not in stats
        assert 'yaml_failures' not in stats
        assert 'yaml_validation_failures' not in stats

    @patch('src.innovation.innovation_engine.YAMLToCodeGenerator')
    @patch('src.innovation.innovation_engine.StructuredPromptBuilder')
    def test_yaml_success_rate_calculation(self, mock_prompt_builder_class, mock_yaml_gen_class):
        """Test YAML success rate calculation."""
        # Setup mocks
        mock_prompt_builder = Mock()
        mock_prompt_builder.build_compact_prompt.return_value = "prompt"
        mock_prompt_builder_class.return_value = mock_prompt_builder

        mock_yaml_gen = Mock()
        # First succeeds, second fails
        mock_yaml_gen.generate.side_effect = [
            ("code", []),
            (None, ["validation error"])
        ]
        mock_yaml_gen_class.return_value = mock_yaml_gen

        engine = InnovationEngine(
            provider_name='gemini',
            generation_mode='yaml',
            max_retries=1
        )

        # Mock LLM responses
        mock_response = LLMResponse(
            content="```yaml\nmetadata:\n  name: test\n  description: Test\n  strategy_type: momentum\n  rebalancing_frequency: M\n```",
            provider='gemini',
            model='gemini-pro',
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        engine.provider.generate = Mock(return_value=mock_response)

        # First generation (success)
        engine.generate_innovation(
            champion_code="",
            champion_metrics={'sharpe_ratio': 1.5},
            failure_history=None
        )

        # Second generation (failure)
        engine.generate_innovation(
            champion_code="",
            champion_metrics={'sharpe_ratio': 1.5},
            failure_history=None
        )

        # Check statistics
        stats = engine.get_statistics()
        assert stats['yaml_successes'] == 1
        assert stats['yaml_failures'] == 1
        assert stats['yaml_success_rate'] == 0.5


class TestFailurePatternIntegration:
    """Test failure pattern extraction for YAML prompts."""

    @patch('src.innovation.innovation_engine.YAMLToCodeGenerator')
    @patch('src.innovation.innovation_engine.StructuredPromptBuilder')
    def test_failure_patterns_passed_to_prompt_builder(self, mock_prompt_builder_class, mock_yaml_gen_class):
        """Test that failure patterns are extracted and passed to StructuredPromptBuilder."""
        # Setup mocks
        mock_prompt_builder = Mock()
        mock_prompt_builder.build_compact_prompt.return_value = "prompt"
        mock_prompt_builder_class.return_value = mock_prompt_builder

        mock_yaml_gen = Mock()
        mock_yaml_gen.generate.return_value = ("code", [])
        mock_yaml_gen_class.return_value = mock_yaml_gen

        engine = InnovationEngine(
            provider_name='gemini',
            generation_mode='yaml'
        )

        # Mock LLM response
        mock_response = LLMResponse(
            content="```yaml\nmetadata:\n  name: test\n  description: Test\n  strategy_type: momentum\n  rebalancing_frequency: M\n```",
            provider='gemini',
            model='gemini-pro',
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        engine.provider.generate = Mock(return_value=mock_response)

        # Create failure history
        failure_history = [
            {
                'error_type': 'validation_error',
                'description': 'Missing required field'
            },
            {
                'error_type': 'syntax_error',
                'description': 'Invalid YAML syntax'
            }
        ]

        # Generate
        engine.generate_innovation(
            champion_code="",
            champion_metrics={'sharpe_ratio': 1.5},
            failure_history=failure_history
        )

        # Verify failure patterns were passed to prompt builder
        call_args = mock_prompt_builder.build_compact_prompt.call_args
        assert call_args is not None
        failure_patterns = call_args[1]['failure_patterns']
        assert len(failure_patterns) == 2
        assert 'validation_error' in failure_patterns[0]
        assert 'syntax_error' in failure_patterns[1]


class TestResetStatistics:
    """Test statistics reset includes YAML fields."""

    @patch('src.innovation.innovation_engine.YAMLToCodeGenerator')
    @patch('src.innovation.innovation_engine.StructuredPromptBuilder')
    def test_reset_clears_yaml_statistics(self, mock_prompt_builder_class, mock_yaml_gen_class):
        """Test that reset_statistics clears YAML-specific counters."""
        # Setup mocks
        mock_prompt_builder = Mock()
        mock_prompt_builder.build_compact_prompt.return_value = "prompt"
        mock_prompt_builder_class.return_value = mock_prompt_builder

        mock_yaml_gen = Mock()
        mock_yaml_gen.generate.return_value = ("code", [])
        mock_yaml_gen_class.return_value = mock_yaml_gen

        engine = InnovationEngine(
            provider_name='gemini',
            generation_mode='yaml'
        )

        # Set some statistics
        engine.yaml_successes = 5
        engine.yaml_failures = 3
        engine.yaml_validation_failures = 2

        # Reset
        engine.reset_statistics()

        # Verify reset
        assert engine.yaml_successes == 0
        assert engine.yaml_failures == 0
        assert engine.yaml_validation_failures == 0


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_default_mode_unchanged(self):
        """Test that default behavior is unchanged (full_code mode)."""
        engine = InnovationEngine(provider_name='gemini')

        # Default should be full_code
        assert engine.generation_mode == 'full_code'

        # YAML components should not be initialized
        assert engine.structured_prompt_builder is None
        assert engine.yaml_generator is None

    def test_existing_methods_still_work(self):
        """Test that existing methods work in full_code mode."""
        engine = InnovationEngine(provider_name='gemini')

        # These should not raise errors
        stats = engine.get_statistics()
        assert 'generation_mode' in stats
        assert stats['generation_mode'] == 'full_code'

        engine.reset_statistics()
        assert engine.total_attempts == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
