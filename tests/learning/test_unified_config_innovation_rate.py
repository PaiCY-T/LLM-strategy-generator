"""
TDD Phase 1 (RED): Unit tests for UnifiedConfig.innovation_rate parameter

These tests are EXPECTED TO FAIL initially, as innovation_rate has not been implemented yet.
"""
import pytest
from src.learning.unified_config import UnifiedConfig
from src.learning.unified_config import ConfigurationError


def test_innovation_rate_default_value():
    """Test innovation_rate default value is 100.0 (backward compatible)"""
    config = UnifiedConfig()
    assert config.innovation_rate == 100.0


def test_innovation_rate_custom_value():
    """Test custom innovation_rate value can be set"""
    config = UnifiedConfig(innovation_rate=50.0)
    assert config.innovation_rate == 50.0


def test_innovation_rate_range_validation_valid():
    """Test innovation_rate accepts valid range (0.0-100.0)"""
    # Minimum
    config_min = UnifiedConfig(innovation_rate=0.0)
    assert config_min.innovation_rate == 0.0

    # Middle
    config_mid = UnifiedConfig(innovation_rate=50.0)
    assert config_mid.innovation_rate == 50.0

    # Maximum
    config_max = UnifiedConfig(innovation_rate=100.0)
    assert config_max.innovation_rate == 100.0


def test_innovation_rate_range_validation_invalid():
    """Test innovation_rate rejects invalid range (<0.0 or >100.0)"""
    # Below minimum
    with pytest.raises(ValueError, match="innovation_rate must be between 0.0 and 100.0"):
        UnifiedConfig(innovation_rate=-1.0)

    # Above maximum
    with pytest.raises(ValueError, match="innovation_rate must be between 0.0 and 100.0"):
        UnifiedConfig(innovation_rate=101.0)


def test_use_json_mode_requires_pure_template():
    """Test use_json_mode=True supports all innovation_rate values (Phase 3 fix)"""
    # Pure LLM mode (innovation_rate=100)
    config_pure = UnifiedConfig(
        use_json_mode=True,
        template_mode=True,
        innovation_rate=100.0
    )
    assert config_pure.use_json_mode is True
    assert config_pure.innovation_rate == 100.0

    # Phase 3 fix: JSON mode now supports hybrid mode via MixedStrategy
    # Hybrid mode (innovation_rate=50) should work with JSON mode
    config_hybrid = UnifiedConfig(
        use_json_mode=True,
        template_mode=True,
        innovation_rate=50.0
    )
    assert config_hybrid.use_json_mode is True
    assert config_hybrid.innovation_rate == 50.0

    # Pure Factor Graph mode (innovation_rate=0) should also work
    config_fg = UnifiedConfig(
        use_json_mode=True,
        template_mode=True,
        innovation_rate=0.0
    )
    assert config_fg.use_json_mode is True
    assert config_fg.innovation_rate == 0.0


def test_to_dict_includes_innovation_rate():
    """Test to_dict() includes innovation_rate parameter"""
    config = UnifiedConfig(innovation_rate=75.0)
    config_dict = config.to_dict()

    assert 'innovation_rate' in config_dict
    assert config_dict['innovation_rate'] == 75.0


def test_innovation_rate_boundary_values():
    """Test edge cases at boundary values"""
    # Just above minimum
    config_low = UnifiedConfig(innovation_rate=0.1)
    assert config_low.innovation_rate == 0.1

    # Just below maximum
    config_high = UnifiedConfig(innovation_rate=99.9)
    assert config_high.innovation_rate == 99.9


def test_backward_compatibility():
    """Test backward compatibility - not setting innovation_rate maintains existing behavior"""
    config_old = UnifiedConfig()  # Don't set innovation_rate
    config_new = UnifiedConfig(innovation_rate=100.0)

    # Both should have same innovation_rate
    assert config_old.innovation_rate == config_new.innovation_rate == 100.0
