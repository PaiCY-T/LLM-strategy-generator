"""Test Template Mode configuration validation for experiment configs.

This test validates that all experiment configuration files include the new
template_mode and template_name parameters required by UnifiedConfig.

RED Phase Test:
- test_all_configs_have_template_mode_parameter: Verify all configs have template_mode
- test_template_mode_configs_have_template_name: Validate template_name when enabled

Expected to FAIL initially until config files are updated.
"""

import os
import pytest
import yaml
from pathlib import Path
from typing import Dict, Any, List


# Config directory path
CONFIG_DIR = Path(__file__).parent.parent.parent / "experiments" / "llm_learning_validation"

# Target config files (7 files as per task specification)
TARGET_CONFIGS = [
    "config_fg_only_10.yaml",
    "config_phase1_fg_only_20.yaml",
    "config_phase1_hybrid_20.yaml",
    "config_phase1_llm_only_20.yaml",
    "config_pilot_fg_only_20.yaml",
    "config_pilot_hybrid_20.yaml",
    "config_pilot_llm_only_20.yaml",
]


def load_config(config_name: str) -> Dict[str, Any]:
    """Load YAML configuration file.

    Args:
        config_name: Name of the config file

    Returns:
        Parsed YAML configuration dictionary
    """
    config_path = CONFIG_DIR / config_name
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_all_config_files() -> List[str]:
    """Get all target config files that exist.

    Returns:
        List of existing config file names
    """
    existing_configs = []
    for config_name in TARGET_CONFIGS:
        config_path = CONFIG_DIR / config_name
        if config_path.exists():
            existing_configs.append(config_name)
    return existing_configs


class TestTemplateModeConfigs:
    """Test suite for Template Mode configuration validation."""

    def test_all_configs_have_template_mode_parameter(self):
        """Test that all config files include template_mode parameter.

        RED Phase Test - Expected to FAIL initially.

        GIVEN: All config files in experiments/llm_learning_validation/
        WHEN: Loading each config file
        THEN: Each must contain 'template_mode' parameter with default value False
        """
        existing_configs = get_all_config_files()

        # Verify we found all target configs
        assert len(existing_configs) == len(TARGET_CONFIGS), (
            f"Expected {len(TARGET_CONFIGS)} config files, found {len(existing_configs)}"
        )

        # Check each config file
        missing_template_mode = []
        for config_name in existing_configs:
            config = load_config(config_name)

            # Check if template_mode exists (could be nested or at root level)
            has_template_mode = (
                'template_mode' in config or  # Root level
                ('llm' in config and 'template_mode' in config.get('llm', {})) or  # Nested in llm
                ('experimental' in config and 'template_mode' in config.get('experimental', {}))  # Nested in experimental
            )

            if not has_template_mode:
                missing_template_mode.append(config_name)

        # Assert all configs have template_mode
        assert len(missing_template_mode) == 0, (
            f"The following configs are missing 'template_mode' parameter: "
            f"{', '.join(missing_template_mode)}\n"
            f"Expected: All {len(TARGET_CONFIGS)} configs should have 'template_mode: false'"
        )

    def test_template_mode_configs_have_template_name(self):
        """Test that configs with template_mode=true have valid template_name.

        RED Phase Test - Expected to PASS (no configs have template_mode=true yet).

        GIVEN: Config files with template_mode: true
        WHEN: Loading config
        THEN: Must have valid template_name parameter (not null/empty)
        """
        existing_configs = get_all_config_files()

        # Check each config file
        invalid_template_name = []
        for config_name in existing_configs:
            config = load_config(config_name)

            # Get template_mode value (check root, llm, and experimental sections)
            template_mode = (
                config.get('template_mode', False) or
                config.get('llm', {}).get('template_mode', False) or
                config.get('experimental', {}).get('template_mode', False)
            )

            # If template_mode is enabled, validate template_name
            if template_mode:
                template_name = (
                    config.get('template_name') or
                    config.get('llm', {}).get('template_name') or
                    config.get('experimental', {}).get('template_name')
                )

                # Validate template_name is not None, null, or empty
                if template_name is None or template_name == "null" or str(template_name).strip() == "":
                    invalid_template_name.append(config_name)

        # Assert all template_mode=true configs have valid template_name
        assert len(invalid_template_name) == 0, (
            f"The following configs have template_mode=true but missing/invalid template_name: "
            f"{', '.join(invalid_template_name)}\n"
            f"Expected: When template_mode=true, template_name must be specified "
            f"(e.g., 'Momentum', 'MeanReversion')"
        )

    def test_config_files_exist(self):
        """Test that all expected config files exist."""
        existing_configs = get_all_config_files()
        missing_configs = set(TARGET_CONFIGS) - set(existing_configs)

        assert len(missing_configs) == 0, (
            f"Missing config files: {', '.join(missing_configs)}"
        )

    def test_config_yaml_syntax(self):
        """Test that all config files have valid YAML syntax."""
        existing_configs = get_all_config_files()

        invalid_yaml = []
        for config_name in existing_configs:
            try:
                load_config(config_name)
            except yaml.YAMLError as e:
                invalid_yaml.append((config_name, str(e)))

        assert len(invalid_yaml) == 0, (
            f"Invalid YAML syntax in: {', '.join([name for name, _ in invalid_yaml])}"
        )


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
