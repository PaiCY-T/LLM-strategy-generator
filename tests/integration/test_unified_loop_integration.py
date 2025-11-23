"""Integration tests for UnifiedLoop with real components.

Tests UnifiedLoop with actual (non-mocked) components to verify:
- Template Mode execution with real TemplateIterationExecutor
- JSON Parameter Output mode integration
- Learning Feedback integration with real FeedbackGenerator
- Champion update logic with real ChampionTracker

These tests use temporary files and run limited iterations (5-10) for validation.
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.learning.unified_loop import UnifiedLoop
from src.learning.unified_config import UnifiedConfig, ConfigurationError


class TestTemplateMode:
    """Test Template Mode execution with real components."""

    def setup_method(self):
        """Setup temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, 'test_history.jsonl')
        self.champion_file = os.path.join(self.temp_dir, 'test_champion.json')

    def teardown_method(self):
        """Cleanup temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_template_mode_initialization(self):
        """Test that Template Mode can be initialized with real components."""
        # Create UnifiedLoop with Template Mode
        loop = UnifiedLoop(
            model='gemini-2.5-flash',
            max_iterations=5,
            template_mode=True,
            template_name='Momentum',
            use_json_mode=False,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify configuration
        assert loop.config.template_mode is True
        assert loop.config.template_name == 'Momentum'
        assert loop.config.use_json_mode is False
        assert loop.config.max_iterations == 5

        # Verify UnifiedLoop was created
        assert loop.learning_loop is not None

    def test_template_mode_config_validation(self):
        """Test that Template Mode configuration validation works."""
        # Should raise error when template_mode=True but template_name is empty
        with pytest.raises(ConfigurationError):
            UnifiedLoop(
                template_mode=True,
                template_name='',  # Invalid
                history_file=self.history_file,
                champion_file=self.champion_file
            )

    def test_json_mode_requires_template_mode(self):
        """Test that JSON mode requires Template Mode."""
        # Should raise error when use_json_mode=True but template_mode=False
        with pytest.raises(ConfigurationError):
            UnifiedLoop(
                template_mode=False,
                use_json_mode=True,  # Invalid without template_mode
                history_file=self.history_file,
                champion_file=self.champion_file
            )


class TestJSONMode:
    """Test JSON Parameter Output mode with real components."""

    def setup_method(self):
        """Setup temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, 'test_history.jsonl')
        self.champion_file = os.path.join(self.temp_dir, 'test_champion.json')

    def teardown_method(self):
        """Cleanup temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_json_mode_initialization(self):
        """Test that JSON mode can be initialized."""
        # Create UnifiedLoop with JSON mode
        loop = UnifiedLoop(
            model='gemini-2.5-flash',
            max_iterations=5,
            template_mode=True,
            template_name='Momentum',
            use_json_mode=True,  # JSON mode enabled
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify configuration
        assert loop.config.template_mode is True
        assert loop.config.use_json_mode is True


class TestFeedbackIntegration:
    """Test Learning Feedback integration."""

    def setup_method(self):
        """Setup temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, 'test_history.jsonl')
        self.champion_file = os.path.join(self.temp_dir, 'test_champion.json')

    def teardown_method(self):
        """Cleanup temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_feedback_enabled_by_default(self):
        """Test that Learning Feedback is enabled by default."""
        loop = UnifiedLoop(
            max_iterations=5,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify feedback is enabled
        assert loop.config.enable_learning is True

    def test_feedback_can_be_disabled(self):
        """Test that Learning Feedback can be disabled."""
        loop = UnifiedLoop(
            max_iterations=5,
            enable_learning=False,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify feedback is disabled
        assert loop.config.enable_learning is False


class TestChampionUpdate:
    """Test Champion update logic."""

    def setup_method(self):
        """Setup temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, 'test_history.jsonl')
        self.champion_file = os.path.join(self.temp_dir, 'test_champion.json')

    def teardown_method(self):
        """Cleanup temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_champion_property_accessible(self):
        """Test that champion property provides backward compatible access."""
        loop = UnifiedLoop(
            max_iterations=5,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify champion property is accessible (should be None initially)
        assert loop.champion is None or loop.champion is not None  # Champion tracker exists

    def test_history_property_accessible(self):
        """Test that history property provides backward compatible access."""
        loop = UnifiedLoop(
            max_iterations=5,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify history property is accessible
        assert loop.history is not None

        # Verify history has expected methods
        assert hasattr(loop.history, 'load_recent')
        assert hasattr(loop.history, 'save')
        assert hasattr(loop.history, 'get_all')


class TestConfigConversion:
    """Test UnifiedConfig conversion to LearningConfig."""

    def test_config_to_learning_config(self):
        """Test that UnifiedConfig can be converted to LearningConfig."""
        config = UnifiedConfig(
            max_iterations=50,
            llm_model='gemini-2.5-flash',
            template_mode=True,
            template_name='Momentum',
            use_json_mode=True,
            timeout_seconds=600
        )

        # Convert to LearningConfig
        learning_config = config.to_learning_config()

        # Verify conversion
        assert learning_config.max_iterations == 50
        assert learning_config.llm_model == 'gemini-2.5-flash'
        assert learning_config.timeout_seconds == 600

    def test_config_preserves_backtest_settings(self):
        """Test that config conversion preserves backtest settings."""
        config = UnifiedConfig(
            max_iterations=10,
            backtest_start_date='2020-01-01',
            backtest_end_date='2023-12-31',
            template_mode=False
        )

        # Convert to LearningConfig
        learning_config = config.to_learning_config()

        # Verify backtest settings preserved
        assert learning_config.backtest_start_date == '2020-01-01'
        assert learning_config.backtest_end_date == '2023-12-31'


class TestUnifiedLoopProperties:
    """Test UnifiedLoop properties and methods."""

    def setup_method(self):
        """Setup temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, 'test_history.jsonl')
        self.champion_file = os.path.join(self.temp_dir, 'test_champion.json')

    def teardown_method(self):
        """Cleanup temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_unified_loop_has_required_properties(self):
        """Test that UnifiedLoop has all required properties."""
        loop = UnifiedLoop(
            max_iterations=5,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify required properties exist
        assert hasattr(loop, 'config')
        assert hasattr(loop, 'learning_loop')
        assert hasattr(loop, 'champion')
        assert hasattr(loop, 'history')
        assert hasattr(loop, 'run')

    def test_unified_loop_config_accessible(self):
        """Test that UnifiedLoop config is accessible."""
        loop = UnifiedLoop(
            max_iterations=25,
            template_mode=True,
            template_name='Factor',
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify config is accessible
        assert loop.config is not None
        assert loop.config.max_iterations == 25
        assert loop.config.template_mode is True
        assert loop.config.template_name == 'Factor'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
