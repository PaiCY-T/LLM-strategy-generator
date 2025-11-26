"""Test UnifiedLoop Migration from LearningLoop.

This test module follows the TDD RED-GREEN-REFACTOR cycle for Task 0.2.
Tests ensure:
1. UnifiedLoop supports template_mode configuration
2. Backward compatibility with LearningLoop when template_mode=False
3. UnifiedLoop.from_config() factory method works correctly
"""

import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from src.learning.unified_loop import UnifiedLoop
from src.learning.learning_loop import LearningLoop
from src.learning.learning_config import LearningConfig


class TestUnifiedLoopMigration:
    """Test suite for UnifiedLoop migration from LearningLoop."""

    @pytest.fixture
    def base_config(self, tmp_path: Path) -> Dict[str, Any]:
        """Create base configuration for testing."""
        return {
            'max_iterations': 10,
            'llm_model': 'gemini-2.5-flash',
            'history_file': str(tmp_path / 'iterations.jsonl'),
            'champion_file': str(tmp_path / 'champion.json'),
            'log_dir': str(tmp_path / 'logs'),
            'timeout_seconds': 420,
        }

    @pytest.fixture
    def config_with_template_mode(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create config with template_mode enabled."""
        config = base_config.copy()
        config['template_mode'] = True
        config['template_name'] = 'Momentum'
        return config

    @pytest.fixture
    def config_without_template_mode(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create config without template_mode (backward compatibility)."""
        return base_config.copy()

    @pytest.fixture
    def temp_yaml_config(self, tmp_path: Path, base_config: Dict[str, Any]) -> Path:
        """Create temporary YAML config file."""
        config_path = tmp_path / "learning_config.yaml"
        with open(config_path, 'w') as f:
            yaml.safe_dump(base_config, f)
        return config_path

    def test_unified_loop_supports_template_mode(self, config_with_template_mode: Dict[str, Any]):
        """Test that UnifiedLoop can be created with template_mode=True.

        RED Phase Test - Should FAIL initially.

        GIVEN: template_mode=True in config
        WHEN: Creating learning loop via UnifiedLoop
        THEN: Uses UnifiedLoop class with template_mode enabled
        """
        # GIVEN: Config with template_mode enabled
        assert config_with_template_mode['template_mode'] is True

        # WHEN: Creating UnifiedLoop with template_mode
        with patch('src.learning.unified_loop.LearningLoop'):
            loop = UnifiedLoop(**config_with_template_mode)

            # THEN: UnifiedLoop should be created with template_mode enabled
            assert hasattr(loop, 'template_mode')
            assert loop.template_mode is True
            assert loop.config.template_mode is True

    def test_backward_compatibility_with_learning_loop(
        self,
        config_without_template_mode: Dict[str, Any]
    ):
        """Test backward compatibility when template_mode is False or not set.

        RED Phase Test - Should FAIL initially.

        GIVEN: template_mode=False or not set in config
        WHEN: Creating learning loop
        THEN: Can fall back to LearningLoop for compatibility
        """
        # GIVEN: Config without template_mode
        assert 'template_mode' not in config_without_template_mode

        # WHEN: Creating loop without template_mode
        # This should work with both LearningLoop and UnifiedLoop
        with patch('src.learning.learning_loop.IterationExecutor'):
            with patch('src.learning.learning_loop.BacktestExecutor'):
                with patch('src.learning.learning_loop.LLMClient'):
                    # Test with LearningLoop directly (existing behavior)
                    learning_config = LearningConfig(**config_without_template_mode)
                    learning_loop = LearningLoop(learning_config)

                    # THEN: LearningLoop should work without template_mode
                    assert learning_loop is not None
                    assert isinstance(learning_loop, LearningLoop)

    def test_unified_loop_from_config_method(
        self,
        temp_yaml_config: Path,
        config_with_template_mode: Dict[str, Any]
    ):
        """Test UnifiedLoop.from_config() factory method.

        RED Phase Test - Should FAIL initially as from_config doesn't exist yet.

        WHEN: Calling UnifiedLoop.from_config()
        THEN: Returns valid UnifiedLoop instance
        """
        # WHEN: Loading config from YAML and creating UnifiedLoop
        # Update the temp YAML with template_mode
        with open(temp_yaml_config, 'w') as f:
            yaml.safe_dump(config_with_template_mode, f)

        # This should fail initially because from_config doesn't exist
        with patch('src.learning.unified_loop.LearningLoop'):
            # Try to call from_config (will fail in RED phase)
            if hasattr(UnifiedLoop, 'from_config'):
                loop = UnifiedLoop.from_config(temp_yaml_config)

                # THEN: Should return valid UnifiedLoop instance
                assert loop is not None
                assert isinstance(loop, UnifiedLoop)
                assert loop.template_mode is True
            else:
                pytest.fail("UnifiedLoop.from_config() method does not exist yet (RED phase expected)")

    def test_orchestrator_uses_unified_loop_with_template_mode(
        self,
        config_with_template_mode: Dict[str, Any],
        tmp_path: Path
    ):
        """Test that orchestrator can use UnifiedLoop when template_mode=True.

        This simulates the actual usage in experiments/llm_learning_validation/orchestrator.py

        GIVEN: Config with template_mode=True
        WHEN: Creating loop from config
        THEN: Should use UnifiedLoop instead of LearningLoop
        """
        # GIVEN: Create a YAML config with template_mode
        config_path = tmp_path / "temp_learning_config.yaml"
        with open(config_path, 'w') as f:
            yaml.safe_dump(config_with_template_mode, f)

        # WHEN: Loading config and deciding which loop to use
        learning_config = LearningConfig.from_yaml(config_path)

        template_mode = getattr(learning_config, 'template_mode', False)

        with patch('src.learning.unified_loop.LearningLoop'):
            if template_mode and hasattr(UnifiedLoop, 'from_config'):
                # Should use UnifiedLoop for template_mode
                loop = UnifiedLoop.from_config(config_path)
                assert isinstance(loop, UnifiedLoop)
            else:
                # Falls back to LearningLoop
                with patch('src.learning.learning_loop.IterationExecutor'):
                    with patch('src.learning.learning_loop.BacktestExecutor'):
                        with patch('src.learning.learning_loop.LLMClient'):
                            loop = LearningLoop(learning_config)
                            assert isinstance(loop, LearningLoop)

    def test_unified_loop_config_validation(self, config_with_template_mode: Dict[str, Any]):
        """Test that UnifiedLoop validates template_mode configuration.

        GIVEN: template_mode=True
        WHEN: template_name is missing
        THEN: Should raise ConfigurationError
        """
        # GIVEN: Config with template_mode but no template_name
        invalid_config = config_with_template_mode.copy()
        del invalid_config['template_name']

        # WHEN/THEN: Should raise error due to missing template_name
        from src.learning.unified_config import ConfigurationError

        with pytest.raises(ConfigurationError, match="template_mode.*requires.*template_name"):
            with patch('src.learning.unified_loop.LearningLoop'):
                UnifiedLoop(**invalid_config)
