"""Tests for AutonomousLoop JSON mode integration (Task 7.2).

This module tests the integration of JSON Parameter Output mode into AutonomousLoop.
"""
import sys
import warnings
import pytest

# Suppress ResourceWarnings from unclosed file handlers (existing issue in codebase)
warnings.filterwarnings('ignore', category=ResourceWarning)

# Add working modules to path
sys.path.insert(0, 'artifacts/working/modules')


class TestAutonomousLoopJsonModeIntegration:
    """Tests for JSON mode integration in AutonomousLoop."""

    def test_import_autonomous_loop(self):
        """Test that AutonomousLoop can be imported."""
        from autonomous_loop import AutonomousLoop
        assert AutonomousLoop is not None

    def test_init_without_json_mode(self):
        """Test initialization with JSON mode disabled (default)."""
        from autonomous_loop import AutonomousLoop

        loop = AutonomousLoop(
            model='gemini-2.5-flash',
            max_iterations=1,
            template_mode=True,
            template_name='Momentum',
            use_json_mode=False
        )

        assert loop.use_json_mode == False
        assert loop.param_generator is not None
        assert loop.param_generator.use_json_mode == False

    def test_init_with_json_mode(self):
        """Test initialization with JSON mode enabled."""
        from autonomous_loop import AutonomousLoop

        loop = AutonomousLoop(
            model='gemini-2.5-flash',
            max_iterations=1,
            template_mode=True,
            template_name='Momentum',
            use_json_mode=True
        )

        assert loop.use_json_mode == True
        assert loop.param_generator is not None
        assert loop.param_generator.use_json_mode == True

    def test_json_mode_components_initialized(self):
        """Test that JSON mode components are properly initialized."""
        from autonomous_loop import AutonomousLoop

        loop = AutonomousLoop(
            model='gemini-2.5-flash',
            max_iterations=1,
            template_mode=True,
            template_name='Momentum',
            use_json_mode=True
        )

        # Verify JSON mode components exist
        assert hasattr(loop.param_generator, 'code_generator')
        assert hasattr(loop.param_generator, 'prompt_builder')
        assert hasattr(loop.param_generator, 'error_feedback')

        # Verify they are not None
        assert loop.param_generator.code_generator is not None
        assert loop.param_generator.prompt_builder is not None
        assert loop.param_generator.error_feedback is not None

    def test_freeform_mode_backward_compatible(self):
        """Test that free-form mode still works (backward compatibility)."""
        from autonomous_loop import AutonomousLoop

        loop = AutonomousLoop(
            model='gemini-2.5-flash',
            max_iterations=1,
            template_mode=False  # Free-form mode
        )

        # In free-form mode, param_generator should be None
        assert loop.param_generator is None
        assert loop.template_mode == False

    def test_default_json_mode_is_false(self):
        """Test that default use_json_mode is False for backward compatibility."""
        from autonomous_loop import AutonomousLoop

        # Initialize without specifying use_json_mode
        loop = AutonomousLoop(
            model='gemini-2.5-flash',
            max_iterations=1,
            template_mode=True,
            template_name='Momentum'
            # use_json_mode not specified - should default to False
        )

        assert loop.use_json_mode == False
        assert loop.param_generator.use_json_mode == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
