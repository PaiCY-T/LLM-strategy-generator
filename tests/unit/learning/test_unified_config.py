"""Unit tests for UnifiedConfig.

Tests configuration validation, conversion, and backward compatibility.

Test Coverage:
    - Configuration initialization
    - Validation rules
    - Conversion to LearningConfig
    - Default values
    - Error handling
"""

import pytest
from src.learning.unified_config import UnifiedConfig, ConfigurationError


class TestUnifiedConfigInitialization:
    """Test UnifiedConfig initialization."""

    def test_default_initialization(self):
        """Test initialization with default values."""
        config = UnifiedConfig()

        assert config.max_iterations == 10
        assert config.llm_model == "gemini-2.5-flash"
        assert config.template_mode is False
        assert config.use_json_mode is False
        assert config.enable_learning is True

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        config = UnifiedConfig(
            max_iterations=50,
            llm_model="gpt-4",
            template_mode=True,
            template_name="Factor",
            use_json_mode=True
        )

        assert config.max_iterations == 50
        assert config.llm_model == "gpt-4"
        assert config.template_mode is True
        assert config.template_name == "Factor"
        assert config.use_json_mode is True


class TestUnifiedConfigValidation:
    """Test UnifiedConfig validation logic."""

    def test_template_mode_requires_template_name(self):
        """Test that template_mode=True requires template_name."""
        with pytest.raises(ConfigurationError, match="template_mode=True requires template_name"):
            UnifiedConfig(template_mode=True, template_name="")

    def test_json_mode_requires_template_mode(self):
        """Test that use_json_mode=True requires template_mode=True."""
        with pytest.raises(ConfigurationError, match="use_json_mode=True requires template_mode=True"):
            UnifiedConfig(use_json_mode=True, template_mode=False)

    def test_history_file_required(self):
        """Test that history_file must be specified."""
        with pytest.raises(ConfigurationError, match="history_file is required"):
            UnifiedConfig(history_file="")

    def test_champion_file_required(self):
        """Test that champion_file must be specified."""
        with pytest.raises(ConfigurationError, match="champion_file is required"):
            UnifiedConfig(champion_file="")

    def test_max_iterations_positive(self):
        """Test that max_iterations must be positive."""
        with pytest.raises(ConfigurationError, match="max_iterations must be > 0"):
            UnifiedConfig(max_iterations=0)

    def test_max_iterations_not_too_large(self):
        """Test that max_iterations cannot exceed 1000."""
        with pytest.raises(ConfigurationError, match="max_iterations too large"):
            UnifiedConfig(max_iterations=1001)

    def test_valid_config_passes_validation(self):
        """Test that valid configuration passes validation."""
        # Should not raise
        config = UnifiedConfig(
            max_iterations=100,
            template_mode=True,
            template_name="Momentum",
            use_json_mode=True
        )
        assert config.max_iterations == 100


class TestUnifiedConfigConversion:
    """Test conversion to LearningConfig."""

    def test_to_learning_config_basic(self):
        """Test basic conversion to LearningConfig."""
        config = UnifiedConfig(max_iterations=50)
        learning_config = config.to_learning_config()

        assert learning_config.max_iterations == 50
        assert learning_config.llm_model == "gemini-2.5-flash"

    def test_to_learning_config_with_template_mode(self):
        """Test conversion preserves template mode settings."""
        config = UnifiedConfig(
            max_iterations=100,
            template_mode=True,
            template_name="Momentum",
            use_json_mode=True,
            history_window=20
        )
        learning_config = config.to_learning_config()

        assert learning_config.max_iterations == 100
        assert learning_config.history_window == 20

    def test_to_learning_config_preserves_backtest_settings(self):
        """Test conversion preserves backtest configuration."""
        config = UnifiedConfig(
            timeout_seconds=600,
            start_date="2020-01-01",
            end_date="2024-12-31",
            fee_ratio=0.002,
            tax_ratio=0.004
        )
        learning_config = config.to_learning_config()

        assert learning_config.timeout_seconds == 600
        assert learning_config.start_date == "2020-01-01"
        assert learning_config.end_date == "2024-12-31"
        assert learning_config.fee_ratio == 0.002
        assert learning_config.tax_ratio == 0.004


class TestUnifiedConfigToDict:
    """Test to_dict() method."""

    def test_to_dict_includes_all_parameters(self):
        """Test that to_dict includes all configuration parameters."""
        config = UnifiedConfig()
        config_dict = config.to_dict()

        # Check key parameters
        assert "max_iterations" in config_dict
        assert "llm_model" in config_dict
        assert "template_mode" in config_dict
        assert "use_json_mode" in config_dict
        assert "enable_learning" in config_dict

    def test_to_dict_masks_api_key(self):
        """Test that to_dict masks API key."""
        config = UnifiedConfig(api_key="secret_key_12345")
        config_dict = config.to_dict()

        assert config_dict["api_key"] == "***"

    def test_to_dict_with_no_api_key(self):
        """Test that to_dict handles None API key."""
        config = UnifiedConfig(api_key=None)
        config_dict = config.to_dict()

        assert config_dict["api_key"] is None


class TestUnifiedConfigEdgeCases:
    """Test edge cases and special scenarios."""

    def test_template_name_with_template_mode_disabled(self):
        """Test that template_name is ignored when template_mode=False."""
        # Should not raise, template_name is ignored
        config = UnifiedConfig(template_mode=False, template_name="Momentum")
        assert config.template_mode is False
        assert config.template_name == "Momentum"  # Stored but not validated

    def test_config_with_all_features_enabled(self):
        """Test configuration with all features enabled."""
        config = UnifiedConfig(
            max_iterations=200,
            template_mode=True,
            template_name="Momentum",
            use_json_mode=True,
            enable_learning=True,
            enable_monitoring=True,
            use_docker=True
        )

        assert config.template_mode is True
        assert config.use_json_mode is True
        assert config.enable_learning is True
        assert config.enable_monitoring is True
        assert config.use_docker is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
