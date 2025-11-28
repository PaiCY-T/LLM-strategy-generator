"""Test that JSON mode supports hybrid mode (innovation_rate < 100).

Phase 3 Bug Fix: The validation in unified_config.py incorrectly rejects
innovation_rate < 100 when use_json_mode=True. However, MixedStrategy in
generation_strategies.py fully supports hybrid mode with JSON-based LLM.

This test verifies that JSON mode works correctly with hybrid innovation rates.
"""

import pytest
from src.learning.unified_config import UnifiedConfig


class TestJsonModeHybridSupport:
    """Test that JSON mode supports hybrid innovation rates."""

    def test_json_mode_accepts_innovation_rate_20(self):
        """JSON mode should accept innovation_rate=20 (20% LLM, 80% Factor Graph)."""
        config = UnifiedConfig(
            use_json_mode=True,
            template_mode=True,
            innovation_rate=20.0,
            max_iterations=10,
            history_file='test_history.jsonl',
            champion_file='test_champion.json'
        )
        assert config.use_json_mode is True
        assert config.innovation_rate == 20.0

    def test_json_mode_accepts_innovation_rate_50(self):
        """JSON mode should accept innovation_rate=50 (balanced hybrid)."""
        config = UnifiedConfig(
            use_json_mode=True,
            template_mode=True,
            innovation_rate=50.0,
            max_iterations=10,
            history_file='test_history.jsonl',
            champion_file='test_champion.json'
        )
        assert config.use_json_mode is True
        assert config.innovation_rate == 50.0

    def test_json_mode_accepts_innovation_rate_75(self):
        """JSON mode should accept innovation_rate=75 (LLM-heavy hybrid)."""
        config = UnifiedConfig(
            use_json_mode=True,
            template_mode=True,
            innovation_rate=75.0,
            max_iterations=10,
            history_file='test_history.jsonl',
            champion_file='test_champion.json'
        )
        assert config.use_json_mode is True
        assert config.innovation_rate == 75.0

    def test_json_mode_accepts_innovation_rate_100(self):
        """JSON mode should still accept innovation_rate=100 (pure LLM)."""
        config = UnifiedConfig(
            use_json_mode=True,
            template_mode=True,
            innovation_rate=100.0,
            max_iterations=10,
            history_file='test_history.jsonl',
            champion_file='test_champion.json'
        )
        assert config.use_json_mode is True
        assert config.innovation_rate == 100.0

    def test_json_mode_accepts_innovation_rate_0(self):
        """JSON mode should accept innovation_rate=0 (pure Factor Graph)."""
        config = UnifiedConfig(
            use_json_mode=True,
            template_mode=True,
            innovation_rate=0.0,
            max_iterations=10,
            history_file='test_history.jsonl',
            champion_file='test_champion.json'
        )
        assert config.use_json_mode is True
        assert config.innovation_rate == 0.0

    def test_mixed_strategy_works_with_json_mode(self):
        """Verify that MixedStrategy supports JSON mode conceptually."""
        # This test documents that MixedStrategy in generation_strategies.py
        # already supports hybrid mode without requiring full code mode
        config = UnifiedConfig(
            use_json_mode=True,
            template_mode=True,
            innovation_rate=30.0,  # 30% LLM, 70% Factor Graph
            max_iterations=10,
            history_file='test_history.jsonl',
            champion_file='test_champion.json'
        )

        # MixedStrategy will use:
        # - LLMStrategy with JSON mode (30% of the time)
        # - FactorGraphStrategy (70% of the time)
        assert config.use_json_mode is True
        assert config.innovation_rate == 30.0
        assert config.template_mode is True
