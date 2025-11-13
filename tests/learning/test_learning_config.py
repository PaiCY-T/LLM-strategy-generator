"""
Tests for Phase 6 LearningConfig (Task 6.2)

Tests configuration management:
- 21 parameter validation
- YAML loading (nested and flat structures)
- Environment variable support
- Default values
- Error handling
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.learning.learning_config import LearningConfig


class TestLearningConfigDefaults:
    """Test default configuration values."""

    def test_default_values(self):
        """Test all 21 default values are set correctly."""
        config = LearningConfig()

        # Loop Control
        assert config.max_iterations == 20
        assert config.continue_on_error is False

        # LLM Configuration
        assert config.llm_model == "gemini-2.5-flash"
        assert config.api_key is None
        assert config.llm_timeout == 60
        assert config.llm_temperature == 0.7
        assert config.llm_max_tokens == 4000

        # Innovation Mode
        assert config.innovation_mode is True
        assert config.innovation_rate == 100
        assert config.llm_retry_count == 3

        # Backtest Configuration
        assert config.timeout_seconds == 420
        assert config.start_date == "2018-01-01"
        assert config.end_date == "2024-12-31"
        assert config.fee_ratio == 0.001425
        assert config.tax_ratio == 0.003
        assert config.resample == "M"

        # History & Files
        assert config.history_file == "artifacts/data/innovations.jsonl"
        assert config.history_window == 5
        assert config.champion_file == "artifacts/data/champion.json"
        assert config.log_dir == "logs"
        assert config.config_file == "config/learning_system.yaml"

        # Logging
        assert config.log_level == "INFO"
        assert config.log_to_file is True
        assert config.log_to_console is True


class TestLearningConfigValidation:
    """Test configuration parameter validation."""

    def test_max_iterations_validation(self):
        """Test max_iterations must be 1-1000."""
        # Valid cases
        LearningConfig(max_iterations=1)
        LearningConfig(max_iterations=100)
        LearningConfig(max_iterations=1000)

        # Invalid cases
        with pytest.raises(ValueError, match="max_iterations must be > 0"):
            LearningConfig(max_iterations=0)

        with pytest.raises(ValueError, match="max_iterations must be > 0"):
            LearningConfig(max_iterations=-1)

        with pytest.raises(ValueError, match="max_iterations too large"):
            LearningConfig(max_iterations=1001)

    def test_innovation_rate_validation(self):
        """Test innovation_rate must be 0-100."""
        # Valid cases
        LearningConfig(innovation_rate=0)
        LearningConfig(innovation_rate=50)
        LearningConfig(innovation_rate=100)

        # Invalid cases
        with pytest.raises(ValueError, match="innovation_rate must be 0-100"):
            LearningConfig(innovation_rate=-1)

        with pytest.raises(ValueError, match="innovation_rate must be 0-100"):
            LearningConfig(innovation_rate=101)

    def test_timeout_validation(self):
        """Test timeout parameters must be >= minimum values."""
        # Valid cases
        LearningConfig(timeout_seconds=60)
        LearningConfig(timeout_seconds=420)
        LearningConfig(llm_timeout=10)
        LearningConfig(llm_timeout=60)

        # Invalid cases
        with pytest.raises(ValueError, match="timeout_seconds must be >= 60"):
            LearningConfig(timeout_seconds=59)

        with pytest.raises(ValueError, match="llm_timeout must be >= 10"):
            LearningConfig(llm_timeout=9)

    def test_temperature_validation(self):
        """Test llm_temperature must be 0.0-2.0."""
        # Valid cases
        LearningConfig(llm_temperature=0.0)
        LearningConfig(llm_temperature=0.7)
        LearningConfig(llm_temperature=2.0)

        # Invalid cases
        with pytest.raises(ValueError, match="llm_temperature must be 0.0-2.0"):
            LearningConfig(llm_temperature=-0.1)

        with pytest.raises(ValueError, match="llm_temperature must be 0.0-2.0"):
            LearningConfig(llm_temperature=2.1)

    def test_date_format_validation(self):
        """Test date parameters must be YYYY-MM-DD format."""
        # Valid cases
        LearningConfig(start_date="2018-01-01", end_date="2024-12-31")

        # Invalid cases
        with pytest.raises(ValueError, match="start_date invalid format"):
            LearningConfig(start_date="2018/01/01")

        with pytest.raises(ValueError, match="end_date invalid format"):
            LearningConfig(end_date="31-12-2024")

        with pytest.raises(ValueError, match="start_date invalid format"):
            LearningConfig(start_date="not-a-date")

    def test_resample_validation(self):
        """Test resample must be D/W/M."""
        # Valid cases
        LearningConfig(resample="D")
        LearningConfig(resample="W")
        LearningConfig(resample="M")

        # Invalid cases
        with pytest.raises(ValueError, match="resample must be D/W/M"):
            LearningConfig(resample="H")

        with pytest.raises(ValueError, match="resample must be D/W/M"):
            LearningConfig(resample="daily")

    def test_fee_tax_validation(self):
        """Test fee and tax ratios must be 0.0-0.1."""
        # Valid cases
        LearningConfig(fee_ratio=0.0, tax_ratio=0.0)
        LearningConfig(fee_ratio=0.001425, tax_ratio=0.003)
        LearningConfig(fee_ratio=0.099, tax_ratio=0.099)

        # Invalid cases
        with pytest.raises(ValueError, match="fee_ratio must be 0-0.1"):
            LearningConfig(fee_ratio=-0.001)

        with pytest.raises(ValueError, match="fee_ratio must be 0-0.1"):
            LearningConfig(fee_ratio=0.11)

        with pytest.raises(ValueError, match="tax_ratio must be 0-0.1"):
            LearningConfig(tax_ratio=-0.001)

        with pytest.raises(ValueError, match="tax_ratio must be 0-0.1"):
            LearningConfig(tax_ratio=0.11)

    def test_history_window_validation(self):
        """Test history_window must be >= 1."""
        # Valid cases
        LearningConfig(history_window=1)
        LearningConfig(history_window=5)

        # Invalid cases
        with pytest.raises(ValueError, match="history_window must be >= 1"):
            LearningConfig(history_window=0)

    def test_log_level_validation(self):
        """Test log_level must be valid Python logging level."""
        # Valid cases
        LearningConfig(log_level="DEBUG")
        LearningConfig(log_level="INFO")
        LearningConfig(log_level="WARNING")
        LearningConfig(log_level="ERROR")
        LearningConfig(log_level="CRITICAL")

        # Invalid cases
        with pytest.raises(ValueError, match="log_level must be one of"):
            LearningConfig(log_level="TRACE")

        with pytest.raises(ValueError, match="log_level must be one of"):
            LearningConfig(log_level="debug")  # lowercase not allowed

    def test_retry_count_validation(self):
        """Test llm_retry_count must be >= 1."""
        # Valid cases
        LearningConfig(llm_retry_count=1)
        LearningConfig(llm_retry_count=3)

        # Invalid cases
        with pytest.raises(ValueError, match="llm_retry_count must be >= 1"):
            LearningConfig(llm_retry_count=0)


class TestLearningConfigYAMLLoading:
    """Test YAML configuration loading."""

    def test_flat_structure_loading(self):
        """Test loading flat YAML structure (backward compatibility)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
max_iterations: 50
continue_on_error: true
llm_model: gpt-4
llm_timeout: 120
innovation_rate: 80
history_window: 10
log_level: DEBUG
            """)
            config_path = f.name

        try:
            config = LearningConfig.from_yaml(config_path)

            assert config.max_iterations == 50
            assert config.continue_on_error is True
            assert config.llm_model == "gpt-4"
            assert config.llm_timeout == 120
            assert config.innovation_rate == 80
            assert config.history_window == 10
            assert config.log_level == "DEBUG"

        finally:
            os.unlink(config_path)

    def test_nested_structure_loading(self):
        """Test loading nested YAML structure (learning_system.yaml format)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
learning_loop:
  max_iterations: 100
  continue_on_error: true
  history:
    file: custom/history.jsonl
    window: 10
  champion:
    file: custom/champion.json
  backtest:
    timeout_seconds: 600
    resample: W
  logging:
    log_dir: custom_logs
    log_level: DEBUG
    log_to_file: false
  llm:
    retry_count: 5

llm:
  enabled: true
  model: gpt-4o
  innovation_rate: 0.5
  generation:
    timeout: 120
    temperature: 0.8
    max_tokens: 8000

backtest:
  default_start_date: "2020-01-01"
  default_end_date: "2023-12-31"
  transaction_costs:
    default_fee_ratio: 0.002
    default_tax_ratio: 0.004
            """)
            config_path = f.name

        try:
            config = LearningConfig.from_yaml(config_path)

            # Loop Control
            assert config.max_iterations == 100
            assert config.continue_on_error is True

            # LLM Configuration
            assert config.llm_model == "gpt-4o"
            assert config.llm_timeout == 120
            assert config.llm_temperature == 0.8
            assert config.llm_max_tokens == 8000

            # Innovation Mode (0.5 * 100 = 50)
            assert config.innovation_mode is True
            assert config.innovation_rate == 50
            assert config.llm_retry_count == 5

            # Backtest Configuration
            assert config.timeout_seconds == 600
            assert config.start_date == "2020-01-01"
            assert config.end_date == "2023-12-31"
            assert config.fee_ratio == 0.002
            assert config.tax_ratio == 0.004
            assert config.resample == "W"

            # History & Files
            assert config.history_file == "custom/history.jsonl"
            assert config.history_window == 10
            assert config.champion_file == "custom/champion.json"
            assert config.log_dir == "custom_logs"

            # Logging
            assert config.log_level == "DEBUG"
            assert config.log_to_file is False
            assert config.log_to_console is True  # default

        finally:
            os.unlink(config_path)

    def test_missing_file_uses_defaults(self):
        """Test missing config file falls back to defaults."""
        config = LearningConfig.from_yaml("nonexistent.yaml")

        assert config.max_iterations == 20  # default
        assert config.log_level == "INFO"  # default

    def test_empty_file_uses_defaults(self):
        """Test empty config file falls back to defaults."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # Empty file
            config_path = f.name

        try:
            config = LearningConfig.from_yaml(config_path)
            assert config.max_iterations == 20  # default

        finally:
            os.unlink(config_path)

    def test_invalid_yaml_raises_error(self):
        """Test invalid YAML syntax raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: syntax: [[[")
            config_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid YAML format"):
                LearningConfig.from_yaml(config_path)

        finally:
            os.unlink(config_path)


class TestLearningConfigEnvironmentVariables:
    """Test environment variable support."""

    def test_api_key_from_env_gemini(self, monkeypatch):
        """Test API key loaded from GEMINI_API_KEY."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("max_iterations: 10")
            config_path = f.name

        try:
            config = LearningConfig.from_yaml(config_path)
            assert config.api_key == "test-gemini-key"

        finally:
            os.unlink(config_path)

    def test_api_key_from_env_openai(self, monkeypatch):
        """Test API key loaded from OPENAI_API_KEY."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("max_iterations: 10")
            config_path = f.name

        try:
            config = LearningConfig.from_yaml(config_path)
            assert config.api_key == "test-openai-key"

        finally:
            os.unlink(config_path)

    def test_api_key_priority_gemini_first(self, monkeypatch):
        """Test GEMINI_API_KEY takes priority over OPENAI_API_KEY."""
        monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
        monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("max_iterations: 10")
            config_path = f.name

        try:
            config = LearningConfig.from_yaml(config_path)
            assert config.api_key == "gemini-key"

        finally:
            os.unlink(config_path)


class TestLearningConfigToDict:
    """Test configuration serialization."""

    def test_to_dict_includes_all_parameters(self):
        """Test to_dict() includes all 21 parameters."""
        config = LearningConfig()
        config_dict = config.to_dict()

        # Check all keys present
        expected_keys = {
            "max_iterations", "continue_on_error",
            "llm_model", "api_key", "llm_timeout", "llm_temperature", "llm_max_tokens",
            "innovation_mode", "innovation_rate", "llm_retry_count",
            "timeout_seconds", "start_date", "end_date", "fee_ratio", "tax_ratio", "resample",
            "history_file", "history_window", "champion_file", "log_dir",
            "log_level", "log_to_file", "log_to_console"
        }

        assert set(config_dict.keys()) == expected_keys

    def test_api_key_masked_in_dict(self):
        """Test API key is masked in to_dict() output."""
        config = LearningConfig(api_key="secret-api-key-12345")
        config_dict = config.to_dict()

        assert config_dict["api_key"] == "***"

    def test_to_dict_with_no_api_key(self):
        """Test to_dict() handles None API key."""
        config = LearningConfig()
        config_dict = config.to_dict()

        assert config_dict["api_key"] is None
