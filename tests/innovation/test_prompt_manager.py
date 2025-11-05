"""
Unit tests for PromptManager - Tasks 7-8

Tests dynamic prompt selection, modification prompts, and creation prompts.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.innovation.prompt_manager import (
    PromptManager,
    PromptContext,
    PromptType,
    GenerationMode
)


@pytest.fixture
def prompt_manager():
    """Create PromptManager instance for testing."""
    return PromptManager()


@pytest.fixture
def strong_champion_context():
    """Context with strong champion performance (Sharpe > 0.8)."""
    return PromptContext(
        champion_code="def strategy(data): return data.get('ROE') > 15",
        champion_metrics={
            "sharpe_ratio": 0.95,
            "max_drawdown": 0.12,
            "win_rate": 0.65
        },
        target_metric="sharpe_ratio"
    )


@pytest.fixture
def weak_champion_context():
    """Context with weak champion performance (Sharpe < 0.5)."""
    return PromptContext(
        champion_code="def strategy(data): return data.get('ROE') > 15",
        champion_metrics={
            "sharpe_ratio": 0.35,
            "max_drawdown": 0.25,
            "win_rate": 0.45
        },
        target_metric="sharpe_ratio"
    )


@pytest.fixture
def no_champion_context():
    """Context with no champion available."""
    return PromptContext(
        champion_approach="Initial exploration",
        innovation_directive="Find profitable strategies"
    )


class TestPromptManagerInitialization:
    """Test PromptManager initialization."""

    def test_initialization_default_paths(self):
        """Test initialization with default paths."""
        manager = PromptManager()

        assert manager.code_builder is not None
        assert manager.modification_prompts_generated == 0
        assert manager.creation_prompts_generated == 0

    def test_initialization_custom_paths(self):
        """Test initialization with custom paths."""
        manager = PromptManager(
            failure_patterns_path="custom/path/failures.json",
            schema_path="custom/path/schema.json"
        )

        assert manager.code_builder is not None


class TestDynamicPromptSelection:
    """Test Task 7: Dynamic prompt selection based on context."""

    def test_strong_champion_selects_modification(self, prompt_manager, strong_champion_context):
        """Test that strong champion (Sharpe > 0.8) selects MODIFICATION."""
        prompt_type, _ = prompt_manager.select_and_build_prompt(strong_champion_context)

        assert prompt_type == PromptType.MODIFICATION

    def test_weak_champion_selects_creation(self, prompt_manager, weak_champion_context):
        """Test that weak champion (Sharpe < 0.5) selects CREATION."""
        prompt_type, _ = prompt_manager.select_and_build_prompt(weak_champion_context)

        assert prompt_type == PromptType.CREATION

    def test_no_champion_selects_creation(self, prompt_manager, no_champion_context):
        """Test that missing champion selects CREATION."""
        prompt_type, _ = prompt_manager.select_and_build_prompt(no_champion_context)

        assert prompt_type == PromptType.CREATION

    def test_medium_champion_defaults_to_modification(self, prompt_manager):
        """Test that medium champion (0.5 < Sharpe < 0.8) defaults to MODIFICATION."""
        context = PromptContext(
            champion_code="def strategy(data): return data.get('ROE') > 15",
            champion_metrics={"sharpe_ratio": 0.65},
            target_metric="sharpe_ratio"
        )

        prompt_type, _ = prompt_manager.select_and_build_prompt(context)

        assert prompt_type == PromptType.MODIFICATION

    def test_force_type_override(self, prompt_manager, strong_champion_context):
        """Test that force_type parameter overrides selection logic."""
        # Strong champion would normally select MODIFICATION
        # But force CREATION
        prompt_type, _ = prompt_manager.select_and_build_prompt(
            strong_champion_context,
            force_type=PromptType.CREATION
        )

        assert prompt_type == PromptType.CREATION


class TestModificationPrompts:
    """Test Task 8: Modification prompts with champion context."""

    def test_modification_prompt_includes_champion_code(self, prompt_manager):
        """Test that modification prompt includes champion code."""
        champion_code = "def strategy(data): return data.get('ROE') > 15"
        champion_metrics = {"sharpe_ratio": 0.85, "max_drawdown": 0.15}

        prompt = prompt_manager.build_modification_prompt(
            champion_code=champion_code,
            champion_metrics=champion_metrics
        )

        # Should contain champion context
        assert "champion" in prompt.lower() or "current" in prompt.lower()
        assert len(prompt) > 500  # Prompt should be substantial

    def test_modification_prompt_includes_metrics(self, prompt_manager):
        """Test that modification prompt includes performance metrics."""
        champion_code = "def strategy(data): return data.get('ROE') > 15"
        champion_metrics = {
            "sharpe_ratio": 0.85,
            "max_drawdown": 0.15,
            "win_rate": 0.58
        }

        prompt = prompt_manager.build_modification_prompt(
            champion_code=champion_code,
            champion_metrics=champion_metrics
        )

        # Should mention metrics
        assert "sharpe" in prompt.lower() or "0.85" in prompt

    def test_modification_prompt_includes_success_factors(self, prompt_manager):
        """Test that modification prompt identifies success factors."""
        champion_code = """
def strategy(data):
    roe = data.get('fundamental_features:ROE稅後')
    return roe > 15
"""
        champion_metrics = {"sharpe_ratio": 0.95, "max_drawdown": 0.12}

        prompt = prompt_manager.build_modification_prompt(
            champion_code=champion_code,
            champion_metrics=champion_metrics
        )

        # Should mention success factors
        assert "success" in prompt.lower() or "preserve" in prompt.lower()

    def test_modification_prompt_includes_failure_patterns(self, prompt_manager):
        """Test that modification prompt includes failure patterns to avoid."""
        champion_code = "def strategy(data): return data.get('ROE') > 15"
        champion_metrics = {"sharpe_ratio": 0.85}
        failure_history = [
            {
                'description': 'Adding debt ratio filter reduced Sharpe by 0.2',
                'error_type': 'performance_degradation'
            }
        ]

        prompt = prompt_manager.build_modification_prompt(
            champion_code=champion_code,
            champion_metrics=champion_metrics,
            failure_history=failure_history
        )

        # Should mention failures
        assert "avoid" in prompt.lower() or "failure" in prompt.lower()

    def test_modification_prompt_includes_target_metric(self, prompt_manager):
        """Test that modification prompt mentions target metric."""
        champion_code = "def strategy(data): return data.get('ROE') > 15"
        champion_metrics = {"sharpe_ratio": 0.85, "max_drawdown": 0.15}

        prompt = prompt_manager.build_modification_prompt(
            champion_code=champion_code,
            champion_metrics=champion_metrics,
            target_metric="calmar_ratio"
        )

        # Should mention target metric
        assert "calmar" in prompt.lower() or "target" in prompt.lower()

    def test_modification_prompt_token_budget(self, prompt_manager):
        """Test that modification prompt stays within token budget (<2000 tokens)."""
        champion_code = "def strategy(data): return data.get('ROE') > 15"
        champion_metrics = {"sharpe_ratio": 0.85}

        prompt = prompt_manager.build_modification_prompt(
            champion_code=champion_code,
            champion_metrics=champion_metrics
        )

        # Rough token estimate: 1 token ≈ 4 characters
        estimated_tokens = len(prompt) // 4
        assert estimated_tokens < 2000


class TestCreationPrompts:
    """Test Task 8: Creation prompts with innovation guidance."""

    def test_creation_prompt_includes_champion_approach(self, prompt_manager):
        """Test that creation prompt includes champion approach for inspiration."""
        champion_approach = "Momentum-based with ROE quality filter"

        prompt = prompt_manager.build_creation_prompt(
            champion_approach=champion_approach
        )

        # Should mention champion approach
        assert "champion" in prompt.lower() or "approach" in prompt.lower()
        assert len(prompt) > 500

    def test_creation_prompt_includes_innovation_directive(self, prompt_manager):
        """Test that creation prompt includes innovation directive."""
        innovation_directive = "Explore value + quality combinations using P/B and profit margins"

        prompt = prompt_manager.build_creation_prompt(
            champion_approach="Momentum-based",
            innovation_directive=innovation_directive
        )

        # Should mention innovation directive
        assert "novel" in prompt.lower() or "innovation" in prompt.lower()

    def test_creation_prompt_includes_failure_patterns(self, prompt_manager):
        """Test that creation prompt includes failure patterns to avoid."""
        failure_history = [
            {
                'description': 'Over-trading with daily rebalancing',
                'error_type': 'high_turnover'
            }
        ]

        prompt = prompt_manager.build_creation_prompt(
            champion_approach="Momentum-based",
            failure_history=failure_history
        )

        # Should mention failures
        assert "avoid" in prompt.lower() or "failure" in prompt.lower()

    def test_creation_prompt_token_budget(self, prompt_manager):
        """Test that creation prompt stays within token budget (<2000 tokens)."""
        prompt = prompt_manager.build_creation_prompt(
            champion_approach="Momentum-based with ROE filter"
        )

        # Rough token estimate: 1 token ≈ 4 characters
        estimated_tokens = len(prompt) // 4
        assert estimated_tokens < 2000


class TestYAMLMode:
    """Test YAML generation mode prompts."""

    def test_yaml_modification_prompt(self, prompt_manager):
        """Test YAML mode modification prompt generation."""
        champion_metrics = {"sharpe_ratio": 0.85, "max_drawdown": 0.15}

        prompt = prompt_manager.build_modification_prompt(
            champion_code="",  # Code not used in YAML mode
            champion_metrics=champion_metrics,
            generation_mode=GenerationMode.YAML
        )

        # Should mention YAML or metadata
        assert "yaml" in prompt.lower() or "metadata" in prompt.lower()

    def test_yaml_creation_prompt(self, prompt_manager):
        """Test YAML mode creation prompt generation."""
        prompt = prompt_manager.build_creation_prompt(
            champion_approach="Momentum-based",
            generation_mode=GenerationMode.YAML
        )

        # Should mention YAML or metadata
        assert "yaml" in prompt.lower() or "metadata" in prompt.lower()

    def test_yaml_mode_with_context(self, prompt_manager):
        """Test YAML mode through select_and_build_prompt."""
        context = PromptContext(
            champion_code="def strategy(data): return data.get('ROE') > 15",  # Need champion code for MODIFICATION
            champion_metrics={"sharpe_ratio": 0.85},
            generation_mode=GenerationMode.YAML,
            target_strategy_type="momentum"
        )

        prompt_type, prompt = prompt_manager.select_and_build_prompt(context)

        assert prompt_type == PromptType.MODIFICATION
        assert "yaml" in prompt.lower() or "metadata" in prompt.lower()


class TestStatistics:
    """Test prompt generation statistics tracking."""

    def test_statistics_initialization(self, prompt_manager):
        """Test that statistics start at zero."""
        stats = prompt_manager.get_statistics()

        assert stats['total_prompts_generated'] == 0
        assert stats['modification_prompts'] == 0
        assert stats['creation_prompts'] == 0

    def test_statistics_track_modification(self, prompt_manager, strong_champion_context):
        """Test that modification prompts are tracked."""
        prompt_manager.select_and_build_prompt(strong_champion_context)

        stats = prompt_manager.get_statistics()
        assert stats['modification_prompts'] == 1
        assert stats['creation_prompts'] == 0

    def test_statistics_track_creation(self, prompt_manager, no_champion_context):
        """Test that creation prompts are tracked."""
        prompt_manager.select_and_build_prompt(no_champion_context)

        stats = prompt_manager.get_statistics()
        assert stats['modification_prompts'] == 0
        assert stats['creation_prompts'] == 1

    def test_statistics_track_multiple(self, prompt_manager, strong_champion_context, no_champion_context):
        """Test that multiple prompts are tracked correctly."""
        prompt_manager.select_and_build_prompt(strong_champion_context)  # Modification
        prompt_manager.select_and_build_prompt(no_champion_context)      # Creation
        prompt_manager.select_and_build_prompt(strong_champion_context)  # Modification

        stats = prompt_manager.get_statistics()
        assert stats['total_prompts_generated'] == 3
        assert stats['modification_prompts'] == 2
        assert stats['creation_prompts'] == 1
        assert abs(stats['modification_ratio'] - 2/3) < 0.01
        assert abs(stats['creation_ratio'] - 1/3) < 0.01


class TestPromptContext:
    """Test PromptContext dataclass."""

    def test_context_default_values(self):
        """Test that PromptContext has sensible defaults."""
        context = PromptContext()

        assert context.champion_code is None
        assert context.champion_metrics is None
        assert context.target_metric == "sharpe_ratio"
        assert context.generation_mode == GenerationMode.FULL_CODE

    def test_context_full_specification(self):
        """Test that PromptContext can be fully specified."""
        context = PromptContext(
            champion_code="def strategy(data): pass",
            champion_metrics={"sharpe_ratio": 0.85},
            champion_approach="Momentum-based",
            failure_history=[],
            target_metric="calmar_ratio",
            target_strategy_type="factor_combination",
            innovation_directive="Explore value factors",
            generation_mode=GenerationMode.YAML
        )

        assert context.champion_code == "def strategy(data): pass"
        assert context.champion_metrics["sharpe_ratio"] == 0.85
        assert context.target_metric == "calmar_ratio"
        assert context.generation_mode == GenerationMode.YAML


class TestChampionApproachInference:
    """Test champion approach inference from code."""

    def test_infer_momentum_approach(self, prompt_manager):
        """Test inference of momentum-based approach."""
        code = """
def strategy(data):
    close = data.get('price:收盤價')
    return close.rolling(20).mean() > close.shift(1)
"""
        approach = prompt_manager._infer_champion_approach(code)

        assert "momentum" in approach.lower()

    def test_infer_fundamental_approach(self, prompt_manager):
        """Test inference of fundamental factor approach."""
        code = """
def strategy(data):
    roe = data.get('fundamental_features:ROE稅後')
    return roe > 15
"""
        approach = prompt_manager._infer_champion_approach(code)

        assert "fundamental" in approach.lower()

    def test_infer_value_approach(self, prompt_manager):
        """Test inference of value-based approach."""
        code = """
def strategy(data):
    pe = data.get('fundamental_features:本益比')
    return pe < 15
"""
        approach = prompt_manager._infer_champion_approach(code)

        assert "value" in approach.lower()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_champion_code(self, prompt_manager):
        """Test handling of empty champion code."""
        prompt = prompt_manager.build_modification_prompt(
            champion_code="",
            champion_metrics={"sharpe_ratio": 0.85}
        )

        assert len(prompt) > 0  # Should still generate valid prompt

    def test_missing_champion_metrics(self, prompt_manager):
        """Test handling of missing champion metrics."""
        prompt = prompt_manager.build_modification_prompt(
            champion_code="def strategy(data): pass",
            champion_metrics={}
        )

        assert len(prompt) > 0  # Should still generate valid prompt

    def test_none_failure_history(self, prompt_manager):
        """Test handling of None failure history."""
        prompt = prompt_manager.build_modification_prompt(
            champion_code="def strategy(data): pass",
            champion_metrics={"sharpe_ratio": 0.85},
            failure_history=None
        )

        assert len(prompt) > 0

    def test_empty_failure_history(self, prompt_manager):
        """Test handling of empty failure history."""
        prompt = prompt_manager.build_modification_prompt(
            champion_code="def strategy(data): pass",
            champion_metrics={"sharpe_ratio": 0.85},
            failure_history=[]
        )

        assert len(prompt) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
