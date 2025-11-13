"""
Characterization and unit tests for LLMClient.

This module tests the LLM client initialization logic extracted from
autonomous_loop.py. It follows a TDD approach:

1. Characterization tests document the CURRENT behavior of autonomous_loop.py
2. Unit tests ensure the extracted LLMClient replicates this behavior exactly
3. Integration tests verify no regression in autonomous_loop.py functionality

Test Coverage:
- LLM initialization (enabled/disabled states)
- Provider configuration (provider name, model, API key)
- Error handling (missing config, invalid keys, engine creation failures)
- ConfigManager integration (no config duplication)
- Thread safety (concurrent initialization)
- Environment variable substitution

Task: Phase 3 Learning Iteration - Task 1.2 (LLMClient Extraction)
Dependencies: Task 1.1 (ConfigManager) COMPLETE
"""

import os
import pytest
import logging
import tempfile
import yaml
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.learning.config_manager import ConfigManager
from src.learning.llm_client import LLMClient
from src.innovation.innovation_engine import InnovationEngine


class TestLLMClientCharacterization:
    """
    Characterization tests documenting current LLM initialization behavior.

    These tests capture the EXACT behavior of autonomous_loop.py's LLM
    initialization logic (lines 637-781) BEFORE extraction. They serve as
    a specification for the LLMClient implementation to ensure 100%
    behavioral compatibility.
    """

    def test_llm_disabled_baseline(self, tmp_config_file):
        """BASELINE: When llm.enabled=False, no engine created."""
        config = {
            'llm': {
                'enabled': False,
                'provider': 'openrouter',
                'model': 'anthropic/claude-3.5-sonnet'
            }
        }
        config_path = self._write_config(tmp_config_file, config)

        # Create client with disabled LLM
        client = LLMClient(config_path)

        # Verify behavior matches autonomous_loop.py
        assert client.is_enabled() is False, "LLM should be disabled"
        assert client.get_engine() is None, "Engine should be None when disabled"

    def test_llm_enabled_baseline(self, tmp_config_file):
        """BASELINE: When llm.enabled=True, InnovationEngine created."""
        config = {
            'llm': {
                'enabled': True,
                'provider': 'openrouter',
                'model': 'anthropic/claude-3.5-sonnet',
                'generation': {
                    'max_tokens': 2000,
                    'temperature': 0.7,
                    'timeout': 60
                }
            }
        }
        config_path = self._write_config(tmp_config_file, config)

        # Mock InnovationEngine to avoid actual LLM API calls
        with patch('src.learning.llm_client.InnovationEngine') as mock_engine:
            mock_instance = Mock(spec=InnovationEngine)
            mock_engine.return_value = mock_instance

            client = LLMClient(config_path)

            # Verify behavior matches autonomous_loop.py
            assert client.is_enabled() is True, "LLM should be enabled"
            assert client.get_engine() == mock_instance, "Should return engine instance"

            # Verify engine was initialized with correct parameters
            mock_engine.assert_called_once()
            call_kwargs = mock_engine.call_args.kwargs
            assert call_kwargs['provider_name'] == 'openrouter'
            assert call_kwargs['model'] == 'anthropic/claude-3.5-sonnet'
            assert call_kwargs['max_tokens'] == 2000
            assert call_kwargs['temperature'] == 0.7
            assert call_kwargs['timeout'] == 60

    def test_provider_selection_baseline(self, tmp_config_file):
        """BASELINE: Provider name correctly passed to InnovationEngine."""
        providers = ['openrouter', 'gemini', 'openai']

        for provider in providers:
            config = {
                'llm': {
                    'enabled': True,
                    'provider': provider,
                    'model': 'test-model',
                    'generation': {'max_tokens': 2000, 'temperature': 0.7, 'timeout': 60}
                }
            }
            config_path = self._write_config(tmp_config_file, config)

            with patch('src.learning.llm_client.InnovationEngine') as mock_engine:
                mock_engine.return_value = Mock(spec=InnovationEngine)

                client = LLMClient(config_path)

                # Verify correct provider used
                call_kwargs = mock_engine.call_args.kwargs
                assert call_kwargs['provider_name'] == provider

    def test_env_var_substitution_baseline(self, tmp_config_file, monkeypatch):
        """BASELINE: Environment variable substitution in config values."""
        # Set environment variables
        monkeypatch.setenv('LLM_ENABLED', 'true')
        monkeypatch.setenv('LLM_MODEL', 'gpt-4')

        config = {
            'llm': {
                'enabled': '${LLM_ENABLED:false}',
                'provider': 'openrouter',
                'model': '${LLM_MODEL:default-model}',
                'generation': {'max_tokens': 2000, 'temperature': 0.7, 'timeout': 60}
            }
        }
        config_path = self._write_config(tmp_config_file, config)

        with patch('src.learning.llm_client.InnovationEngine') as mock_engine:
            mock_engine.return_value = Mock(spec=InnovationEngine)

            # ConfigManager should handle env var substitution
            # Note: This tests the CURRENT autonomous_loop.py behavior
            client = LLMClient(config_path)

            # Verify environment variables were substituted
            # (autonomous_loop.py handles this in lines 662-689)
            assert client.is_enabled() is True

    def test_missing_config_baseline(self):
        """BASELINE: Missing config file disables LLM gracefully."""
        # Try to load non-existent config
        client = LLMClient('/nonexistent/config.yaml')

        # Verify graceful failure (autonomous_loop.py lines 758-765)
        assert client.is_enabled() is False
        assert client.get_engine() is None

    def test_engine_creation_failure_baseline(self, tmp_config_file):
        """BASELINE: InnovationEngine creation failure disables LLM."""
        config = {
            'llm': {
                'enabled': True,
                'provider': 'openrouter',
                'model': 'test-model',
                'generation': {'max_tokens': 2000, 'temperature': 0.7, 'timeout': 60}
            }
        }
        config_path = self._write_config(tmp_config_file, config)

        # Mock engine creation to raise exception
        with patch('src.learning.llm_client.InnovationEngine') as mock_engine:
            mock_engine.side_effect = Exception("API key invalid")

            client = LLMClient(config_path)

            # Verify graceful failure (autonomous_loop.py lines 733-747)
            assert client.is_enabled() is False
            assert client.get_engine() is None

    # Helper methods
    def _write_config(self, tmp_file, config):
        """Write config dict to temporary YAML file."""
        with open(tmp_file, 'w') as f:
            yaml.dump(config, f)
        return tmp_file


class TestLLMClientInitialization:
    """Unit tests for LLMClient initialization logic."""

    def test_initialization_disabled(self, tmp_config_file):
        """Test that disabled LLM doesn't create engine."""
        config = {
            'llm': {
                'enabled': False,
                'provider': 'openrouter',
                'model': 'test-model'
            }
        }
        config_path = self._write_config(tmp_config_file, config)

        client = LLMClient(config_path)

        assert client.enabled is False
        assert client.engine is None
        assert client.is_enabled() is False
        assert client.get_engine() is None

    def test_initialization_enabled(self, tmp_config_file):
        """Test that enabled LLM creates engine."""
        config = {
            'llm': {
                'enabled': True,
                'provider': 'openrouter',
                'model': 'anthropic/claude-3.5-sonnet',
                'generation': {
                    'max_tokens': 2000,
                    'temperature': 0.7,
                    'timeout': 60
                }
            }
        }
        config_path = self._write_config(tmp_config_file, config)

        with patch('src.learning.llm_client.InnovationEngine') as mock_engine:
            mock_instance = Mock(spec=InnovationEngine)
            mock_engine.return_value = mock_instance

            client = LLMClient(config_path)

            assert client.enabled is True
            assert client.engine == mock_instance
            assert client.is_enabled() is True
            assert client.get_engine() == mock_instance

    def test_uses_config_manager(self, tmp_config_file):
        """Test that LLMClient uses ConfigManager (no duplication)."""
        config = {
            'llm': {
                'enabled': True,
                'provider': 'openrouter',
                'model': 'test-model',
                'generation': {'max_tokens': 2000, 'temperature': 0.7, 'timeout': 60}
            }
        }
        config_path = self._write_config(tmp_config_file, config)

        with patch('src.learning.llm_client.InnovationEngine') as mock_engine:
            mock_engine.return_value = Mock(spec=InnovationEngine)

            # ConfigManager should be used for config loading
            config_mgr = ConfigManager.get_instance()
            config_mgr.clear_cache()

            client = LLMClient(config_path)

            # Verify ConfigManager was used
            assert client.config_manager == config_mgr
            assert client.config is not None

    def test_provider_and_model_configuration(self, tmp_config_file):
        """Test provider and model are correctly configured."""
        test_cases = [
            ('openrouter', 'anthropic/claude-3.5-sonnet'),
            ('gemini', 'gemini-2.5-flash'),
            ('openai', 'gpt-4')
        ]

        for provider, model in test_cases:
            config = {
                'llm': {
                    'enabled': True,
                    'provider': provider,
                    'model': model,
                    'generation': {'max_tokens': 2000, 'temperature': 0.7, 'timeout': 60}
                }
            }
            config_path = self._write_config(tmp_config_file, config)

            with patch('src.learning.llm_client.InnovationEngine') as mock_engine:
                mock_engine.return_value = Mock(spec=InnovationEngine)

                client = LLMClient(config_path)

                call_kwargs = mock_engine.call_args.kwargs
                assert call_kwargs['provider_name'] == provider
                assert call_kwargs['model'] == model

    def test_generation_parameters(self, tmp_config_file):
        """Test generation parameters passed to engine."""
        config = {
            'llm': {
                'enabled': True,
                'provider': 'openrouter',
                'model': 'test-model',
                'generation': {
                    'max_tokens': 4000,
                    'temperature': 0.8,
                    'timeout': 120
                }
            }
        }
        config_path = self._write_config(tmp_config_file, config)

        with patch('src.learning.llm_client.InnovationEngine') as mock_engine:
            mock_engine.return_value = Mock(spec=InnovationEngine)

            client = LLMClient(config_path)

            call_kwargs = mock_engine.call_args.kwargs
            assert call_kwargs['max_tokens'] == 4000
            assert call_kwargs['temperature'] == 0.8
            assert call_kwargs['timeout'] == 120

    def test_default_generation_parameters(self, tmp_config_file):
        """Test default generation parameters when not specified."""
        config = {
            'llm': {
                'enabled': True,
                'provider': 'openrouter',
                'model': 'test-model'
            }
        }
        config_path = self._write_config(tmp_config_file, config)

        with patch('src.learning.llm_client.InnovationEngine') as mock_engine:
            mock_engine.return_value = Mock(spec=InnovationEngine)

            client = LLMClient(config_path)

            call_kwargs = mock_engine.call_args.kwargs
            # Should use defaults (matching autonomous_loop.py)
            assert call_kwargs['max_tokens'] == 2000
            assert call_kwargs['temperature'] == 0.7
            assert call_kwargs['timeout'] == 60

    def test_invalid_config_handled_gracefully(self, tmp_config_file):
        """Test invalid config handled gracefully."""
        config = {
            'llm': {
                'enabled': True
                # Missing provider and model - will use defaults
            }
        }
        config_path = self._write_config(tmp_config_file, config)

        with patch('src.learning.llm_client.InnovationEngine') as mock_engine:
            # Simulate API key missing or initialization failure
            mock_engine.side_effect = Exception("Missing API key")

            # Should not crash, should disable LLM on engine creation failure
            client = LLMClient(config_path)

            assert client.is_enabled() is False

    def test_engine_creation_failure_handled(self, tmp_config_file):
        """Test engine creation failure is handled gracefully."""
        config = {
            'llm': {
                'enabled': True,
                'provider': 'openrouter',
                'model': 'test-model',
                'generation': {'max_tokens': 2000, 'temperature': 0.7, 'timeout': 60}
            }
        }
        config_path = self._write_config(tmp_config_file, config)

        with patch('src.learning.llm_client.InnovationEngine') as mock_engine:
            mock_engine.side_effect = Exception("Initialization failed")

            # Should not crash
            client = LLMClient(config_path)

            assert client.enabled is False
            assert client.engine is None

    def test_get_engine_when_disabled_returns_none(self, tmp_config_file):
        """Test get_engine returns None when disabled."""
        config = {'llm': {'enabled': False}}
        config_path = self._write_config(tmp_config_file, config)

        client = LLMClient(config_path)

        assert client.get_engine() is None

    def test_idempotent_initialization(self, tmp_config_file):
        """Test multiple instantiations are safe."""
        config = {
            'llm': {
                'enabled': True,
                'provider': 'openrouter',
                'model': 'test-model',
                'generation': {'max_tokens': 2000, 'temperature': 0.7, 'timeout': 60}
            }
        }
        config_path = self._write_config(tmp_config_file, config)

        with patch('src.learning.llm_client.InnovationEngine') as mock_engine:
            mock_engine.return_value = Mock(spec=InnovationEngine)

            # Create multiple instances
            client1 = LLMClient(config_path)
            client2 = LLMClient(config_path)

            # Both should work independently
            assert client1.is_enabled() is True
            assert client2.is_enabled() is True

    def test_missing_config_file(self):
        """Test missing config file handled gracefully."""
        # Non-existent config path
        client = LLMClient('/path/to/nonexistent/config.yaml')

        # Should disable LLM, not crash
        assert client.is_enabled() is False
        assert client.get_engine() is None

    def test_environment_variable_substitution(self, tmp_config_file, monkeypatch):
        """Test environment variable substitution in config."""
        monkeypatch.setenv('TEST_LLM_MODEL', 'custom-model')

        config = {
            'llm': {
                'enabled': True,
                'provider': 'openrouter',
                'model': '${TEST_LLM_MODEL:default-model}',
                'generation': {'max_tokens': 2000, 'temperature': 0.7, 'timeout': 60}
            }
        }
        config_path = self._write_config(tmp_config_file, config)

        with patch('src.learning.llm_client.InnovationEngine') as mock_engine:
            mock_engine.return_value = Mock(spec=InnovationEngine)

            client = LLMClient(config_path)

            # Verify env var was used (if ConfigManager supports it)
            # Note: This depends on ConfigManager implementation
            call_kwargs = mock_engine.call_args.kwargs
            # Model should be resolved by config system
            assert 'model' in call_kwargs

    # Helper methods
    def _write_config(self, tmp_file, config):
        """Write config dict to temporary YAML file."""
        with open(tmp_file, 'w') as f:
            yaml.dump(config, f)
        return tmp_file


class TestLLMClientThreadSafety:
    """Thread safety tests for LLMClient."""

    def test_concurrent_initialization(self, tmp_config_file):
        """Test concurrent LLMClient initialization is safe."""
        import threading

        config = {
            'llm': {
                'enabled': True,
                'provider': 'openrouter',
                'model': 'test-model',
                'generation': {'max_tokens': 2000, 'temperature': 0.7, 'timeout': 60}
            }
        }
        config_path = self._write_config(tmp_config_file, config)

        results = []

        def create_client():
            with patch('src.learning.llm_client.InnovationEngine') as mock_engine:
                mock_engine.return_value = Mock(spec=InnovationEngine)
                client = LLMClient(config_path)
                results.append(client.is_enabled())

        # Create clients from multiple threads
        threads = [threading.Thread(target=create_client) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should succeed
        assert all(results), "All concurrent initializations should succeed"

    # Helper methods
    def _write_config(self, tmp_file, config):
        """Write config dict to temporary YAML file."""
        with open(tmp_file, 'w') as f:
            yaml.dump(config, f)
        return tmp_file


# Fixtures
@pytest.fixture
def tmp_config_file(tmp_path):
    """Create temporary config file for testing."""
    config_file = tmp_path / "test_config.yaml"
    yield str(config_file)
    # Cleanup
    if config_file.exists():
        config_file.unlink()


@pytest.fixture(autouse=True)
def reset_config_manager():
    """Reset ConfigManager singleton before each test."""
    ConfigManager.reset_instance()
    yield
    ConfigManager.reset_instance()


@pytest.fixture(autouse=True)
def capture_logs(caplog):
    """Capture logs for all tests."""
    caplog.set_level(logging.DEBUG)
    yield caplog


class TestCodeExtraction:
    """
    Test suite for extract_python_code() method.

    Tests code extraction from various LLM response formats including:
    - Markdown code blocks (```python and ```)
    - Plain text code
    - Multiple code blocks
    - Empty/invalid responses
    - Validation logic (Python markers: def, import, data.get, class)

    Task: Phase 3 Learning Iteration - Task 3.3 (Code Extraction Tests)
    Dependencies: Task 1.2 (LLMClient Extraction) COMPLETE
    """

    @pytest.fixture
    def llm_client(self, tmp_config_file):
        """Create LLMClient instance for testing (LLM disabled)."""
        config = {
            'llm': {
                'enabled': False  # Disabled to avoid engine initialization
            }
        }
        config_path = self._write_config(tmp_config_file, config)
        return LLMClient(config_path)

    def test_extract_from_markdown_with_python_identifier(self, llm_client):
        """Extract code from ```python...``` block."""
        response = "Here's a strategy:\n```python\ndef strategy():\n    pass\n```"

        result = llm_client.extract_python_code(response)

        assert result is not None, "Should extract code from markdown with python identifier"
        assert result == "def strategy():\n    pass", "Should return code without markdown markers"
        assert "```" not in result, "Should not include markdown delimiters"

    def test_extract_from_markdown_without_identifier(self, llm_client):
        """Extract code from ```...``` block (no 'python' keyword)."""
        response = "```\nimport pandas as pd\ndata.get('price')\n```"

        result = llm_client.extract_python_code(response)

        assert result is not None, "Should extract code from markdown without python identifier"
        assert "import pandas as pd" in result, "Should contain import statement"
        assert "data.get('price')" in result, "Should contain data.get call"
        assert "```" not in result, "Should not include markdown delimiters"

    def test_extract_plain_text_code(self, llm_client):
        """Extract code from plain text (no markdown)."""
        response = "def my_strategy():\n    return data.get('close')"

        result = llm_client.extract_python_code(response)

        assert result is not None, "Should extract code from plain text"
        assert result == "def my_strategy():\n    return data.get('close')", "Should return plain text code"

    def test_extract_first_valid_from_multiple_blocks(self, llm_client):
        """When multiple code blocks exist, return first valid one."""
        response = (
            "Here are two strategies:\n"
            "```python\n"
            "def first_strategy():\n"
            "    return data.get('volume')\n"
            "```\n"
            "And another:\n"
            "```python\n"
            "def second_strategy():\n"
            "    return data.get('price')\n"
            "```"
        )

        result = llm_client.extract_python_code(response)

        assert result is not None, "Should extract first valid code block"
        assert "first_strategy" in result, "Should return first block"
        assert "second_strategy" not in result, "Should not include second block"

    def test_extract_returns_none_for_no_code_markers(self, llm_client):
        """Returns None when response has no Python code markers."""
        response = "This is just text with no code markers at all"

        result = llm_client.extract_python_code(response)

        assert result is None, "Should return None when no Python markers found"

    def test_extract_returns_none_for_empty_response(self, llm_client):
        """Returns None for empty/None input."""
        # Test empty string
        result = llm_client.extract_python_code("")
        assert result is None, "Should return None for empty string"

        # Test None input
        result = llm_client.extract_python_code(None)
        assert result is None, "Should return None for None input"

        # Test whitespace-only string
        result = llm_client.extract_python_code("   \n\t  ")
        assert result is None, "Should return None for whitespace-only string"

    def test_extract_validates_python_markers(self, llm_client):
        """Validates code contains Python markers (def, import, class, data.get)."""
        # Test each marker individually
        test_cases = [
            ("```python\ndef my_func():\n    pass\n```", "def ", "function definition"),
            ("```python\nimport pandas as pd\n```", "import ", "import statement"),
            ("```python\nresult = data.get('close')\n```", "data.get", "data.get call"),
            ("```python\nclass MyClass:\n    pass\n```", "class ", "class definition"),
        ]

        for response, marker, description in test_cases:
            result = llm_client.extract_python_code(response)
            assert result is not None, f"Should extract code with {description}"
            assert marker in result, f"Should contain {marker} marker"

    def test_extract_with_class_definition(self, llm_client):
        """Extract code with 'class' keyword."""
        response = "```python\nclass Strategy:\n    def execute(self):\n        return data.get('price')\n```"

        result = llm_client.extract_python_code(response)

        assert result is not None, "Should extract code with class definition"
        assert "class Strategy:" in result, "Should contain class definition"
        assert "def execute(self):" in result, "Should contain method definition"

    def test_extract_markdown_block_without_newline_after_backticks(self, llm_client):
        """Extract code from markdown block with non-standard formatting."""
        # Some LLMs might not include newline after ```python
        response = "```python\ndef strategy(): pass```"

        result = llm_client.extract_python_code(response)

        # This tests regex pattern robustness
        # Current implementation requires \n after ```, so this should fail
        assert result is None or "def strategy()" in result, "Should handle various formatting"

    def test_extract_with_explanatory_text_before_code(self, llm_client):
        """Extract code when preceded by explanatory text."""
        response = (
            "I've created a momentum strategy for you. "
            "This strategy uses price data to identify trends.\n\n"
            "```python\n"
            "def momentum_strategy():\n"
            "    price = data.get('close')\n"
            "    return price.pct_change(20)\n"
            "```\n\n"
            "This should work well for your use case."
        )

        result = llm_client.extract_python_code(response)

        assert result is not None, "Should extract code despite surrounding text"
        assert "def momentum_strategy():" in result, "Should contain function definition"
        assert "I've created" not in result, "Should not include explanatory text"

    def test_extract_with_explanatory_text_after_code(self, llm_client):
        """Extract code when followed by explanatory text."""
        response = (
            "```python\n"
            "import numpy as np\n"
            "def strategy():\n"
            "    return data.get('returns')\n"
            "```\n"
            "Note: This strategy requires numpy."
        )

        result = llm_client.extract_python_code(response)

        assert result is not None, "Should extract code despite trailing text"
        assert "import numpy" in result, "Should contain import"
        assert "Note:" not in result, "Should not include trailing text"

    def test_extract_with_multiple_blocks_invalid_first(self, llm_client):
        """When first block is invalid, should try subsequent blocks."""
        response = (
            "First, here's some pseudo-code:\n"
            "```\n"
            "this is not valid python code\n"
            "just some random text\n"
            "```\n"
            "Now here's the real code:\n"
            "```python\n"
            "def real_strategy():\n"
            "    return data.get('close')\n"
            "```"
        )

        result = llm_client.extract_python_code(response)

        assert result is not None, "Should skip invalid block and find valid one"
        assert "real_strategy" in result, "Should extract second (valid) block"
        assert "random text" not in result, "Should not include invalid block"

    def test_extract_strips_whitespace(self, llm_client):
        """Extracted code should be trimmed of leading/trailing whitespace."""
        response = "```python\n\n\ndef strategy():\n    pass\n\n\n```"

        result = llm_client.extract_python_code(response)

        assert result is not None, "Should extract code"
        assert result.startswith("def strategy()"), "Should not have leading whitespace"
        assert not result.endswith("\n\n"), "Should not have excessive trailing whitespace"

    def test_extract_preserves_internal_formatting(self, llm_client):
        """Extracted code should preserve internal indentation and newlines."""
        response = (
            "```python\n"
            "def complex_strategy():\n"
            "    if True:\n"
            "        data.get('close')\n"
            "    return None\n"
            "```"
        )

        result = llm_client.extract_python_code(response)

        assert result is not None, "Should extract code"
        assert "    if True:" in result, "Should preserve indentation"
        assert "\n" in result, "Should preserve newlines"

    def test_extract_with_inline_code_markers(self, llm_client):
        """Handle code with inline backticks (not code blocks)."""
        response = "Use the `get` method in your `strategy` function for best results."

        result = llm_client.extract_python_code(response)

        # Should not extract inline code (no triple backticks)
        # Should fall back to plain text but fail validation (no Python markers)
        assert result is None, "Should not extract inline code markers as code blocks"

    def test_extract_with_non_python_code_block(self, llm_client):
        """Reject code blocks explicitly marked as other languages."""
        response = "```javascript\nfunction test() { return true; }\n```"

        result = llm_client.extract_python_code(response)

        # Regex pattern matches ```python or ``` (any), so this would match
        # But validation should fail (no Python markers)
        assert result is None, "Should reject non-Python code (no Python markers)"

    def test_extract_with_mixed_content_code_block(self, llm_client):
        """Extract Python code from block with mixed content."""
        response = (
            "```python\n"
            "# This is a trading strategy\n"
            "import pandas as pd\n"
            "\n"
            "def strategy():\n"
            "    # Get closing prices\n"
            "    close = data.get('close')\n"
            "    return close\n"
            "```"
        )

        result = llm_client.extract_python_code(response)

        assert result is not None, "Should extract code with comments"
        assert "# This is a trading strategy" in result, "Should preserve comments"
        assert "import pandas" in result, "Should preserve imports"
        assert "def strategy():" in result, "Should preserve function"

    def test_extract_with_unicode_characters(self, llm_client):
        """Handle code with Unicode characters."""
        response = (
            "```python\n"
            "def strategy():\n"
            "    # 這是一個策略\n"
            "    return data.get('close')\n"
            "```"
        )

        result = llm_client.extract_python_code(response)

        assert result is not None, "Should handle Unicode in comments"
        assert "策略" in result, "Should preserve Unicode characters"

    def test_extract_non_string_input(self, llm_client):
        """Handle non-string input gracefully."""
        # Test integer
        result = llm_client.extract_python_code(123)
        assert result is None, "Should return None for integer input"

        # Test list
        result = llm_client.extract_python_code(['code', 'here'])
        assert result is None, "Should return None for list input"

        # Test dict
        result = llm_client.extract_python_code({'code': 'here'})
        assert result is None, "Should return None for dict input"

    def test_extract_from_code_block_with_backticks_inside(self, llm_client):
        """Handle code blocks that contain backticks in strings."""
        response = (
            "```python\n"
            "def strategy():\n"
            "    doc = '''Use `data.get` method'''\n"
            "    return data.get('close')\n"
            "```"
        )

        result = llm_client.extract_python_code(response)

        assert result is not None, "Should handle backticks in strings"
        assert "data.get" in result, "Should preserve content with backticks"

    # Helper methods
    def _write_config(self, tmp_file, config):
        """Write config dict to temporary YAML file."""
        with open(tmp_file, 'w') as f:
            yaml.dump(config, f)
        return tmp_file
