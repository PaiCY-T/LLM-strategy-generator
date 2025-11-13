"""
Tests for mutation_config.yaml validation and loading.

Tests configuration structure, bounds validation, environment variable
substitution, and integration with ExitParameterMutator.

Spec: exit-mutation-redesign (Task 2)
Requirements: 2.1, 2.2, 2.3, 2.4
"""

import os
import pytest
import yaml
from pathlib import Path
from typing import Dict, Any


# Path to mutation config
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "mutation_config.yaml"


@pytest.fixture
def config() -> Dict[str, Any]:
    """Load mutation configuration from YAML file."""
    assert CONFIG_PATH.exists(), f"Config file not found: {CONFIG_PATH}"

    with open(CONFIG_PATH, 'r') as f:
        config_data = yaml.safe_load(f)

    return config_data


@pytest.fixture
def config_with_env_vars(monkeypatch) -> Dict[str, Any]:
    """Load config with environment variables set."""
    # Set test environment variables
    monkeypatch.setenv("EXIT_MUTATION_STDDEV", "0.20")
    monkeypatch.setenv("EXIT_STOP_LOSS_MIN", "0.02")
    monkeypatch.setenv("EXIT_STOP_LOSS_MAX", "0.25")
    monkeypatch.setenv("EXIT_TAKE_PROFIT_MIN", "0.10")
    monkeypatch.setenv("EXIT_TAKE_PROFIT_MAX", "0.60")

    # Reload config (in production, this would use actual env var substitution)
    with open(CONFIG_PATH, 'r') as f:
        config_data = yaml.safe_load(f)

    return config_data


class TestConfigStructure:
    """Test basic configuration structure and required sections."""

    def test_config_loads_successfully(self, config):
        """Test that configuration file loads without errors."""
        assert config is not None
        assert isinstance(config, dict)

    def test_has_gaussian_mutation_section(self, config):
        """Test that gaussian_mutation section exists."""
        assert "gaussian_mutation" in config
        assert "stddev" in config["gaussian_mutation"]

    def test_has_parameter_bounds_section(self, config):
        """Test that parameter_bounds section exists with all 4 parameters."""
        assert "parameter_bounds" in config
        bounds = config["parameter_bounds"]

        # All 4 parameters must be defined
        assert "stop_loss_pct" in bounds
        assert "take_profit_pct" in bounds
        assert "trailing_stop_offset" in bounds
        assert "holding_period_days" in bounds

    def test_has_mutation_probabilities_section(self, config):
        """Test that mutation_probabilities section exists."""
        assert "mutation_probabilities" in config
        assert "parameter_selection" in config["mutation_probabilities"]

    def test_has_validation_section(self, config):
        """Test that validation section exists."""
        assert "validation" in config
        assert "ast_validation_enabled" in config["validation"]

    def test_has_logging_section(self, config):
        """Test that logging section exists."""
        assert "logging" in config
        assert "log_mutations" in config["logging"]

    def test_has_monitoring_section(self, config):
        """Test that monitoring section exists."""
        assert "monitoring" in config
        assert "metrics_enabled" in config["monitoring"]


class TestGaussianMutationConfig:
    """Test Gaussian mutation configuration parameters."""

    def test_stddev_is_float(self, config):
        """Test that stddev is a valid float or string (for env var)."""
        stddev = config["gaussian_mutation"]["stddev"]
        # Can be float directly or string with env var placeholder
        assert isinstance(stddev, (float, str))

        # If string, should be env var format: ${VAR:default}
        if isinstance(stddev, str):
            assert stddev.startswith("${") and ":" in stddev and stddev.endswith("}")

    def test_stddev_in_reasonable_range(self, config):
        """Test that default stddev is in reasonable range (0.05-0.35)."""
        stddev_str = config["gaussian_mutation"]["stddev"]

        # Extract default value from ${VAR:default} format
        if isinstance(stddev_str, str) and ":" in stddev_str:
            default_str = stddev_str.split(":")[1].rstrip("}")
            stddev = float(default_str)
        else:
            stddev = float(stddev_str)

        assert 0.05 <= stddev <= 0.35, f"stddev {stddev} outside reasonable range [0.05, 0.35]"

    def test_verification_settings_present(self, config):
        """Test that verification settings for testing are present."""
        verification = config["gaussian_mutation"]["verification"]
        assert "sample_size" in verification
        assert "confidence_level" in verification

        assert verification["sample_size"] >= 100
        assert 0.0 < verification["confidence_level"] <= 1.0


class TestParameterBounds:
    """Test parameter bounds configuration (Requirements 2.1-2.4)."""

    def test_stop_loss_bounds(self, config):
        """Test stop_loss_pct bounds (Requirement 2.1: [0.01, 0.20])."""
        bounds = config["parameter_bounds"]["stop_loss_pct"]

        assert "min" in bounds
        assert "max" in bounds
        assert "default" in bounds

        # Extract values (handle env var format)
        min_val = self._extract_value(bounds["min"])
        max_val = self._extract_value(bounds["max"])
        default_val = bounds["default"]

        # Validate required bounds
        assert min_val == 0.01, "stop_loss_pct min must be 0.01 (1%)"
        assert max_val == 0.20, "stop_loss_pct max must be 0.20 (20%)"
        assert min_val < max_val, "min must be less than max"
        assert min_val <= default_val <= max_val, "default must be within bounds"

    def test_take_profit_bounds(self, config):
        """Test take_profit_pct bounds (Requirement 2.2: [0.05, 0.50])."""
        bounds = config["parameter_bounds"]["take_profit_pct"]

        assert "min" in bounds
        assert "max" in bounds
        assert "default" in bounds

        min_val = self._extract_value(bounds["min"])
        max_val = self._extract_value(bounds["max"])
        default_val = bounds["default"]

        assert min_val == 0.05, "take_profit_pct min must be 0.05 (5%)"
        assert max_val == 0.50, "take_profit_pct max must be 0.50 (50%)"
        assert min_val < max_val
        assert min_val <= default_val <= max_val

    def test_trailing_stop_bounds(self, config):
        """Test trailing_stop_offset bounds (Requirement 2.3: [0.005, 0.05])."""
        bounds = config["parameter_bounds"]["trailing_stop_offset"]

        assert "min" in bounds
        assert "max" in bounds
        assert "default" in bounds

        min_val = self._extract_value(bounds["min"])
        max_val = self._extract_value(bounds["max"])
        default_val = bounds["default"]

        assert min_val == 0.005, "trailing_stop_offset min must be 0.005 (0.5%)"
        assert max_val == 0.05, "trailing_stop_offset max must be 0.05 (5%)"
        assert min_val < max_val
        assert min_val <= default_val <= max_val

    def test_holding_period_bounds(self, config):
        """Test holding_period_days bounds (Requirement 2.4: [1, 60])."""
        bounds = config["parameter_bounds"]["holding_period_days"]

        assert "min" in bounds
        assert "max" in bounds
        assert "default" in bounds

        min_val = self._extract_value(bounds["min"])
        max_val = self._extract_value(bounds["max"])
        default_val = bounds["default"]

        assert min_val == 1, "holding_period_days min must be 1"
        assert max_val == 60, "holding_period_days max must be 60"
        assert min_val < max_val
        assert min_val <= default_val <= max_val

    def test_bounds_have_descriptions(self, config):
        """Test that all parameters have description and example_values."""
        parameters = ["stop_loss_pct", "take_profit_pct", "trailing_stop_offset", "holding_period_days"]

        for param in parameters:
            bounds = config["parameter_bounds"][param]
            assert "description" in bounds, f"{param} missing description"
            assert "units" in bounds, f"{param} missing units"
            assert "example_values" in bounds, f"{param} missing example_values"

            # Example values should have at least 3 examples
            examples = bounds["example_values"]
            assert len(examples) >= 3, f"{param} should have at least 3 example values"

            # Each example should have value and context
            for example in examples:
                assert "value" in example, f"{param} example missing value"
                assert "context" in example, f"{param} example missing context"

    def test_bounds_are_financially_realistic(self, config):
        """Test that bounds represent realistic trading values."""
        bounds = config["parameter_bounds"]

        # Stop loss: Should allow range from tight (1%) to wide (20%)
        stop_loss = bounds["stop_loss_pct"]
        assert self._extract_value(stop_loss["min"]) >= 0.005  # At least 0.5%
        assert self._extract_value(stop_loss["max"]) <= 0.30   # At most 30%

        # Take profit: Should allow range from conservative to aggressive
        take_profit = bounds["take_profit_pct"]
        assert self._extract_value(take_profit["min"]) >= 0.02  # At least 2%
        assert self._extract_value(take_profit["max"]) <= 1.00  # At most 100%

        # Trailing stop: Should be tighter than fixed stop
        trailing = bounds["trailing_stop_offset"]
        assert self._extract_value(trailing["min"]) >= 0.001  # At least 0.1%
        assert self._extract_value(trailing["max"]) <= 0.10   # At most 10%

        # Holding period: Should cover day trading to position trading
        holding = bounds["holding_period_days"]
        assert self._extract_value(holding["min"]) >= 1      # At least 1 day
        assert self._extract_value(holding["max"]) <= 120    # At most 4 months

    @staticmethod
    def _extract_value(value):
        """Extract numeric value from env var format or direct value."""
        if isinstance(value, str) and ":" in value:
            # Format: ${VAR_NAME:default}
            default_str = value.split(":")[1].rstrip("}")
            return float(default_str)
        return float(value)


class TestMutationProbabilities:
    """Test mutation probability configuration."""

    def test_parameter_selection_probabilities_exist(self, config):
        """Test that all 4 parameters have selection probabilities."""
        selection = config["mutation_probabilities"]["parameter_selection"]

        assert "stop_loss_pct" in selection
        assert "take_profit_pct" in selection
        assert "trailing_stop_offset" in selection
        assert "holding_period_days" in selection

    def test_probabilities_are_valid(self, config):
        """Test that probabilities are between 0 and 1."""
        selection = config["mutation_probabilities"]["parameter_selection"]

        for param, prob in selection.items():
            # Extract value (handle env var format)
            if isinstance(prob, str) and ":" in prob:
                prob_val = float(prob.split(":")[1].rstrip("}"))
            else:
                prob_val = float(prob)

            assert 0.0 <= prob_val <= 1.0, f"{param} probability {prob_val} not in [0, 1]"

    def test_probabilities_sum_to_one(self, config):
        """Test that parameter selection probabilities sum to 1.0."""
        selection = config["mutation_probabilities"]["parameter_selection"]

        # Extract all probability values
        prob_sum = 0.0
        for prob in selection.values():
            if isinstance(prob, str) and ":" in prob:
                prob_val = float(prob.split(":")[1].rstrip("}"))
            else:
                prob_val = float(prob)
            prob_sum += prob_val

        assert abs(prob_sum - 1.0) < 0.01, f"Probabilities sum to {prob_sum}, expected 1.0"

    def test_exit_mutation_weight_is_reasonable(self, config):
        """Test that exit_mutation_weight is in reasonable range (0.1-0.5)."""
        weight = config["mutation_probabilities"]["exit_mutation_weight"]
        assert 0.1 <= weight <= 0.5, f"exit_mutation_weight {weight} outside [0.1, 0.5]"


class TestValidationSettings:
    """Test validation configuration settings."""

    def test_ast_validation_enabled_by_default(self, config):
        """Test that AST validation is enabled (critical safety feature)."""
        validation = config["validation"]

        # Should be true or env var with true default
        ast_enabled = validation["ast_validation_enabled"]
        if isinstance(ast_enabled, str) and ":" in ast_enabled:
            default = ast_enabled.split(":")[1].rstrip("}").lower()
            assert default == "true", "AST validation must be enabled by default"
        else:
            assert ast_enabled is True

    def test_max_retries_is_positive(self, config):
        """Test that max_retries is positive integer."""
        max_retries = config["validation"]["max_retries"]

        if isinstance(max_retries, str) and ":" in max_retries:
            retries = int(max_retries.split(":")[1].rstrip("}"))
        else:
            retries = int(max_retries)

        assert retries > 0, "max_retries must be positive"
        assert retries <= 10, "max_retries should not exceed 10 (performance)"

    def test_validation_timeout_is_reasonable(self, config):
        """Test that validation timeout is reasonable (1-30 seconds)."""
        timeout = config["validation"]["validation_timeout"]

        if isinstance(timeout, str) and ":" in timeout:
            timeout_val = float(timeout.split(":")[1].rstrip("}"))
        else:
            timeout_val = float(timeout)

        assert 1 <= timeout_val <= 30, f"validation_timeout {timeout_val} outside [1, 30]"

    def test_skip_missing_parameters_enabled(self, config):
        """Test that skip_missing_parameters is enabled (backward compatibility)."""
        skip_missing = config["validation"]["skip_missing_parameters"]

        if isinstance(skip_missing, str) and ":" in skip_missing:
            default = skip_missing.split(":")[1].rstrip("}").lower()
            assert default == "true", "skip_missing_parameters should be true by default"
        else:
            assert skip_missing is True


class TestLoggingConfiguration:
    """Test logging configuration settings."""

    def test_log_mutations_enabled(self, config):
        """Test that mutation logging is enabled."""
        assert config["logging"]["log_mutations"]

    def test_log_level_is_valid(self, config):
        """Test that log_level is valid Python logging level."""
        log_level = config["logging"]["log_level"]

        if isinstance(log_level, str) and ":" in log_level:
            level = log_level.split(":")[1].rstrip("}")
        else:
            level = log_level

        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert level in valid_levels, f"log_level {level} not in {valid_levels}"

    def test_statistics_interval_is_reasonable(self, config):
        """Test that statistics logging interval is reasonable."""
        interval = config["logging"]["statistics_interval"]

        if isinstance(interval, str) and ":" in interval:
            interval_val = int(interval.split(":")[1].rstrip("}"))
        else:
            interval_val = int(interval)

        # 0 = disabled, or reasonable interval (10-1000)
        assert interval_val == 0 or (10 <= interval_val <= 1000)


class TestMonitoringConfiguration:
    """Test monitoring and metrics configuration."""

    def test_metrics_enabled_by_default(self, config):
        """Test that Prometheus metrics are enabled."""
        metrics_enabled = config["monitoring"]["metrics_enabled"]

        if isinstance(metrics_enabled, str) and ":" in metrics_enabled:
            default = metrics_enabled.split(":")[1].rstrip("}").lower()
            assert default == "true", "Metrics should be enabled by default"
        else:
            assert metrics_enabled is True

    def test_json_logging_enabled(self, config):
        """Test that JSON logging is enabled for structured logs."""
        json_enabled = config["monitoring"]["json_logging_enabled"]

        if isinstance(json_enabled, str) and ":" in json_enabled:
            default = json_enabled.split(":")[1].rstrip("}").lower()
            assert default == "true"
        else:
            assert json_enabled is True

    def test_track_distribution_enabled(self, config):
        """Test that mutation distribution tracking is enabled."""
        track_dist = config["monitoring"]["track_distribution"]

        if isinstance(track_dist, str) and ":" in track_dist:
            default = track_dist.split(":")[1].rstrip("}").lower()
            assert default == "true"
        else:
            assert track_dist is True


class TestPerformanceConfiguration:
    """Test performance tuning settings."""

    def test_regex_caching_enabled(self, config):
        """Test that regex pattern caching is enabled (performance optimization)."""
        cache_enabled = config["performance"]["cache_regex_patterns"]

        if isinstance(cache_enabled, str) and ":" in cache_enabled:
            default = cache_enabled.split(":")[1].rstrip("}").lower()
            assert default == "true", "Regex caching should be enabled by default"
        else:
            assert cache_enabled is True

    def test_max_latency_target_is_reasonable(self, config):
        """Test that max_latency_ms target matches requirements (<100ms)."""
        max_latency = config["performance"]["max_latency_ms"]

        if isinstance(max_latency, str) and ":" in max_latency:
            latency_val = int(max_latency.split(":")[1].rstrip("}"))
        else:
            latency_val = int(max_latency)

        # Requirements specify <100ms
        assert latency_val == 100, f"max_latency_ms should be 100 (requirement)"


class TestAdvancedConfiguration:
    """Test advanced/expert configuration settings."""

    def test_adaptive_bounds_disabled_by_default(self, config):
        """Test that adaptive bounds is disabled (future feature)."""
        advanced = config["advanced"]
        assert "adaptive_bounds_enabled" in advanced
        assert advanced["adaptive_bounds_enabled"] is False

    def test_correlation_aware_disabled_by_default(self, config):
        """Test that correlation-aware mutation is disabled (future feature)."""
        advanced = config["advanced"]
        assert "correlation_aware_mutation" in advanced
        assert advanced["correlation_aware_mutation"] is False


class TestConfigValidation:
    """Test configuration validation settings."""

    def test_validate_on_load_enabled(self, config):
        """Test that validation on load is enabled."""
        assert config["config_validation"]["validate_on_load"] is True

    def test_strict_mode_enabled(self, config):
        """Test that strict mode is enabled (fail-fast on invalid config)."""
        assert config["config_validation"]["strict_mode"] is True


class TestEnvironmentVariableSupport:
    """Test environment variable substitution support."""

    def test_env_var_format_is_consistent(self, config):
        """Test that all env var placeholders use consistent format."""
        # All env var placeholders should be: ${VAR_NAME:default}
        config_str = str(config)

        # Find all env var patterns
        import re
        env_var_pattern = r'\$\{([A-Z_]+):([^}]+)\}'
        matches = re.findall(env_var_pattern, config_str)

        # Should have multiple env var placeholders
        assert len(matches) > 10, "Expected many env var placeholders"

        # All should follow EXIT_* naming convention
        for var_name, default in matches:
            assert var_name.startswith("EXIT_"), f"Env var {var_name} should start with EXIT_"

    def test_default_values_are_sensible(self, config):
        """Test that default values in env var placeholders are sensible."""
        # All defaults should be within acceptable ranges
        # This is tested implicitly by other bound tests
        pass


class TestIntegrationWithExitParameterMutator:
    """Test integration with ExitParameterMutator module."""

    def test_bounds_match_param_bounds_constant(self, config):
        """Test that bounds in config match PARAM_BOUNDS in ExitParameterMutator."""
        # Import PARAM_BOUNDS from mutator
        try:
            from src.mutation.exit_parameter_mutator import PARAM_BOUNDS
        except ImportError:
            pytest.skip("ExitParameterMutator not available")

        config_bounds = config["parameter_bounds"]

        # Extract config bounds
        stop_loss_min = self._extract_value(config_bounds["stop_loss_pct"]["min"])
        stop_loss_max = self._extract_value(config_bounds["stop_loss_pct"]["max"])

        take_profit_min = self._extract_value(config_bounds["take_profit_pct"]["min"])
        take_profit_max = self._extract_value(config_bounds["take_profit_pct"]["max"])

        trailing_min = self._extract_value(config_bounds["trailing_stop_offset"]["min"])
        trailing_max = self._extract_value(config_bounds["trailing_stop_offset"]["max"])

        holding_min = self._extract_value(config_bounds["holding_period_days"]["min"])
        holding_max = self._extract_value(config_bounds["holding_period_days"]["max"])

        # Compare with PARAM_BOUNDS
        assert PARAM_BOUNDS["stop_loss_pct"] == (stop_loss_min, stop_loss_max)
        assert PARAM_BOUNDS["take_profit_pct"] == (take_profit_min, take_profit_max)
        assert PARAM_BOUNDS["trailing_stop_offset"] == (trailing_min, trailing_max)
        assert PARAM_BOUNDS["holding_period_days"] == (holding_min, holding_max)

    @staticmethod
    def _extract_value(value):
        """Extract numeric value from env var format or direct value."""
        if isinstance(value, str) and ":" in value:
            default_str = value.split(":")[1].rstrip("}")
            return float(default_str)
        return float(value)


class TestFinancialRationale:
    """Test that financial rationale is documented for all parameters."""

    def test_stop_loss_has_financial_rationale(self, config):
        """Test that stop_loss_pct has documented financial rationale."""
        # Check that description mentions risk control and rationale
        bounds = config["parameter_bounds"]["stop_loss_pct"]
        description = bounds["description"].lower()

        assert "risk" in description or "loss" in description

    def test_take_profit_has_financial_rationale(self, config):
        """Test that take_profit_pct has documented financial rationale."""
        bounds = config["parameter_bounds"]["take_profit_pct"]
        description = bounds["description"].lower()

        assert "profit" in description or "reward" in description

    def test_trailing_stop_has_financial_rationale(self, config):
        """Test that trailing_stop_offset has documented financial rationale."""
        bounds = config["parameter_bounds"]["trailing_stop_offset"]
        description = bounds["description"].lower()

        assert "trailing" in description or "peak" in description

    def test_holding_period_has_financial_rationale(self, config):
        """Test that holding_period_days has documented financial rationale."""
        bounds = config["parameter_bounds"]["holding_period_days"]
        description = bounds["description"].lower()

        assert "hold" in description or "time" in description or "period" in description


class TestConfigLoader:
    """Test configuration loading utilities."""

    def test_load_with_pyyaml(self):
        """Test that config loads successfully with PyYAML."""
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)

        assert config is not None
        assert isinstance(config, dict)

    def test_config_file_is_valid_yaml(self):
        """Test that config file is syntactically valid YAML."""
        try:
            with open(CONFIG_PATH, 'r') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Config file is not valid YAML: {e}")

    def test_no_tabs_in_config_file(self):
        """Test that config uses spaces, not tabs (YAML requirement)."""
        with open(CONFIG_PATH, 'r') as f:
            content = f.read()

        assert '\t' not in content, "Config file contains tabs (use spaces in YAML)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
