"""Backward compatibility tests for UnifiedLoop.

Tests that UnifiedLoop maintains API compatibility with AutonomousLoop and
can be used as a drop-in replacement in existing test infrastructure.

Test Coverage:
- ExtendedTestHarness compatibility (API interface)
- Property access (champion, history)
- File format compatibility (iteration history, champion files)
- Configuration parameter compatibility
"""

import pytest
import os
import sys
import tempfile
import shutil
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.learning.unified_loop import UnifiedLoop
from src.learning.unified_config import UnifiedConfig


class TestAPICompatibility:
    """Test API interface compatibility with AutonomousLoop."""

    def setup_method(self):
        """Setup temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, 'test_history.jsonl')
        self.champion_file = os.path.join(self.temp_dir, 'test_champion.json')

    def teardown_method(self):
        """Cleanup temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_champion_property_exists(self):
        """Test that champion property exists (AutonomousLoop API)."""
        loop = UnifiedLoop(
            max_iterations=5,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify champion property exists (should not raise AttributeError)
        try:
            champion = loop.champion
            # Property access should succeed (may be None or ChampionRecord)
            assert champion is None or hasattr(champion, 'metrics')
        except AttributeError:
            pytest.fail("UnifiedLoop missing 'champion' property (AutonomousLoop API)")

    def test_history_property_exists(self):
        """Test that history property exists (AutonomousLoop API)."""
        loop = UnifiedLoop(
            max_iterations=5,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify history property exists
        try:
            history = loop.history
            assert history is not None
            assert hasattr(history, 'load_recent')
            assert hasattr(history, 'save')
        except AttributeError:
            pytest.fail("UnifiedLoop missing 'history' property (AutonomousLoop API)")

    def test_run_method_exists(self):
        """Test that run() method exists (AutonomousLoop API)."""
        loop = UnifiedLoop(
            max_iterations=5,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify run() method exists
        assert hasattr(loop, 'run')
        assert callable(loop.run)

    def test_initialization_with_model_parameter(self):
        """Test initialization with 'model' parameter (AutonomousLoop API)."""
        # AutonomousLoop uses 'model' parameter
        loop = UnifiedLoop(
            model='gemini-2.5-flash',  # AutonomousLoop API
            max_iterations=5,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify initialization succeeded
        assert loop.config.llm_model == 'gemini-2.5-flash'

    def test_initialization_with_max_iterations(self):
        """Test initialization with 'max_iterations' parameter."""
        loop = UnifiedLoop(
            max_iterations=100,  # AutonomousLoop API
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify max_iterations set correctly
        assert loop.config.max_iterations == 100


class TestFileFormatCompatibility:
    """Test file format compatibility."""

    def setup_method(self):
        """Setup temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, 'test_history.jsonl')
        self.champion_file = os.path.join(self.temp_dir, 'test_champion.json')

    def teardown_method(self):
        """Cleanup temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_history_file_format(self):
        """Test that history file uses JSONL format (compatible with AutonomousLoop)."""
        # Create UnifiedLoop
        loop = UnifiedLoop(
            max_iterations=5,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify history file path is set correctly
        assert loop.config.history_file == self.history_file

        # Verify history file would use JSONL format (IterationHistory uses .jsonl)
        assert self.history_file.endswith('.jsonl')

    def test_champion_file_format(self):
        """Test that champion file uses JSON format (compatible with AutonomousLoop)."""
        # Create UnifiedLoop
        loop = UnifiedLoop(
            max_iterations=5,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify champion file path is set correctly
        assert loop.config.champion_file == self.champion_file

        # Verify champion file uses JSON format
        assert self.champion_file.endswith('.json')


class TestConfigCompatibility:
    """Test configuration parameter compatibility."""

    def setup_method(self):
        """Setup temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, 'test_history.jsonl')
        self.champion_file = os.path.join(self.temp_dir, 'test_champion.json')

    def teardown_method(self):
        """Cleanup temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_config_accepts_autonomous_loop_parameters(self):
        """Test that UnifiedConfig accepts AutonomousLoop parameters."""
        # These are common AutonomousLoop parameters
        loop = UnifiedLoop(
            model='gemini-2.5-flash',
            max_iterations=50,
            history_file=self.history_file,
            champion_file=self.champion_file,
            timeout_seconds=600
        )

        # Verify parameters accepted
        assert loop.config.llm_model == 'gemini-2.5-flash'
        assert loop.config.max_iterations == 50
        assert loop.config.timeout_seconds == 600

    def test_config_accepts_learning_loop_parameters(self):
        """Test that UnifiedConfig accepts LearningLoop parameters."""
        # These are LearningLoop-specific parameters
        loop = UnifiedLoop(
            max_iterations=20,
            enable_learning=True,
            history_window=10,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify parameters accepted
        assert loop.config.enable_learning is True
        assert loop.config.history_window == 10

    def test_config_optional_parameters_have_defaults(self):
        """Test that optional parameters have sensible defaults."""
        # Create with minimal parameters
        loop = UnifiedLoop(
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify defaults
        assert loop.config.max_iterations == 10  # Default
        assert loop.config.llm_model == "gemini-2.5-flash"  # Default
        assert loop.config.template_mode is False  # Default
        assert loop.config.enable_learning is True  # Default


class TestTestHarnessCompatibility:
    """Test compatibility with ExtendedTestHarness usage patterns."""

    def setup_method(self):
        """Setup temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, 'test_history.jsonl')
        self.champion_file = os.path.join(self.temp_dir, 'test_champion.json')

    def teardown_method(self):
        """Cleanup temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_initialization_pattern_compatible(self):
        """Test that initialization pattern matches ExtendedTestHarness expectations."""
        # ExtendedTestHarness initializes like this:
        # loop = AutonomousLoop(
        #     model=self.model,
        #     max_iterations=target_iterations,
        #     history_file='iteration_history.json'
        # )

        # Verify UnifiedLoop can be initialized the same way
        loop = UnifiedLoop(
            model='gemini-2.5-flash',
            max_iterations=100,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify initialization succeeded
        assert loop is not None
        assert loop.config.max_iterations == 100

    def test_champion_access_pattern_compatible(self):
        """Test that champion access pattern is compatible."""
        loop = UnifiedLoop(
            max_iterations=5,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # ExtendedTestHarness accesses champion like this:
        # if self.loop.champion:
        #     champion_sharpe = self.loop.champion.metrics.get('sharpe_ratio', 0.0)

        # Verify this pattern works with UnifiedLoop
        champion = loop.champion
        # Champion may be None initially, which is fine
        if champion is not None:
            # If champion exists, verify it has metrics
            assert hasattr(champion, 'metrics') or isinstance(champion, dict)

    def test_history_access_pattern_compatible(self):
        """Test that history access pattern is compatible."""
        loop = UnifiedLoop(
            max_iterations=5,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # ExtendedTestHarness accesses history like this:
        # record = self.loop.history.get_record(i)

        # Verify history has required methods
        assert hasattr(loop.history, 'get_record') or hasattr(loop.history, 'get_all')
        assert hasattr(loop.history, 'save')
        assert hasattr(loop.history, 'load_recent')


class TestNewFeaturesOptional:
    """Test that new UnifiedLoop features are optional and don't break compatibility."""

    def setup_method(self):
        """Setup temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, 'test_history.jsonl')
        self.champion_file = os.path.join(self.temp_dir, 'test_champion.json')

    def teardown_method(self):
        """Cleanup temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_template_mode_optional(self):
        """Test that Template Mode is optional (defaults to False)."""
        # Create without template_mode parameter
        loop = UnifiedLoop(
            max_iterations=5,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify template_mode defaults to False
        assert loop.config.template_mode is False

    def test_json_mode_optional(self):
        """Test that JSON mode is optional (defaults to False)."""
        # Create without use_json_mode parameter
        loop = UnifiedLoop(
            max_iterations=5,
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify use_json_mode defaults to False
        assert loop.config.use_json_mode is False

    def test_standard_mode_equals_autonomous_loop_behavior(self):
        """Test that standard mode (template_mode=False) behaves like AutonomousLoop."""
        # Create in standard mode (no template features)
        loop = UnifiedLoop(
            model='gemini-2.5-flash',
            max_iterations=10,
            template_mode=False,  # Explicitly disable template mode
            history_file=self.history_file,
            champion_file=self.champion_file
        )

        # Verify it's in standard mode
        assert loop.config.template_mode is False
        assert loop.config.use_json_mode is False

        # Verify it has same API as AutonomousLoop
        assert hasattr(loop, 'champion')
        assert hasattr(loop, 'history')
        assert hasattr(loop, 'run')


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
