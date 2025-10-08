"""
Unit tests for evolutionary prompts (Task 24).

Tests build_evolutionary_prompt() and _should_force_exploration() functions
to ensure correct prompt construction with champion preservation constraints.
"""

import pytest
from typing import Dict, List, Any
from datetime import datetime

from prompt_builder import PromptBuilder
from autonomous_loop import ChampionStrategy


# Test Fixtures

@pytest.fixture
def base_prompt() -> str:
    """Base strategy generation prompt."""
    return """
Generate a trading strategy using finlab data.

Requirements:
- Use data.get() to load data
- Create signal using fundamental factors
- Return valid pandas Series
"""


@pytest.fixture
def feedback_summary() -> str:
    """Sample feedback summary from previous iterations."""
    return """
Previous iteration feedback:
- Sharpe ratio: 0.85
- Suggestion: Improve risk management
"""


@pytest.fixture
def sample_champion() -> ChampionStrategy:
    """Sample champion strategy for testing."""
    return ChampionStrategy(
        iteration_num=3,
        code="# Champion code",
        parameters={
            'roe_type': 'smoothed',
            'roe_smoothing_window': 4,
            'liquidity_threshold': 150_000_000
        },
        metrics={'sharpe_ratio': 0.97, 'annual_return': 0.18},
        success_patterns=[
            "roe.rolling(window=4).mean() - 4-quarter smoothing reduces noise",
            "liquidity_filter > 150,000,000 TWD - Selects stable stocks",
            "revenue_yoy.ffill() - Forward-filled revenue data"
        ],
        timestamp=datetime.now().isoformat()
    )


@pytest.fixture
def sample_failure_patterns() -> List[str]:
    """Sample failure patterns from FailureTracker."""
    return [
        "Avoid: Removing ROE smoothing (increases noise) (learned from iter 2)",
        "Avoid: Relaxing liquidity filter to 80M (reduces stability) (learned from iter 4)"
    ]


# Core Tests (Task 24 Specification)

def test_exploration_mode_iteration_0_to_2(base_prompt, feedback_summary):
    """Test 1: Verify base prompt returned for iterations 0-2."""

    builder = PromptBuilder()

    for iteration in [0, 1, 2]:
        prompt = builder.build_evolutionary_prompt(
            iteration_num=iteration,
            champion=None,
            feedback_summary=feedback_summary,
            base_prompt=base_prompt,
            failure_patterns=None
        )

        # Should return base prompt + feedback (no evolutionary constraints)
        assert base_prompt in prompt, f"Base prompt missing in iteration {iteration}"
        assert feedback_summary in prompt, f"Feedback missing in iteration {iteration}"
        assert "LEARNING FROM SUCCESS" not in prompt, f"Unexpected champion context in iteration {iteration}"
        assert "PRESERVE" not in prompt, f"Unexpected preservation constraints in iteration {iteration}"


def test_exploitation_mode_iteration_3_plus(base_prompt, feedback_summary, sample_champion):
    """Test 2: Verify 4-section structure for iterations 3+."""

    builder = PromptBuilder()

    prompt = builder.build_evolutionary_prompt(
        iteration_num=7,  # Not divisible by 5, so won't force exploration
        champion=sample_champion,
        feedback_summary=feedback_summary,
        base_prompt=base_prompt,
        failure_patterns=None
    )

    # Section A: Champion Context
    assert "LEARNING FROM SUCCESS" in prompt, "Missing Section A header"
    assert f"CURRENT CHAMPION: Iteration {sample_champion.iteration_num}" in prompt, "Missing champion iteration"
    assert "Achieved Sharpe: 0.9700" in prompt, "Missing champion Sharpe"

    # Section B: Mandatory Preservation
    assert "MANDATORY REQUIREMENTS:" in prompt, "Missing Section B header"
    assert "PRESERVE these proven success factors:" in prompt, "Missing preservation directive"
    assert "roe.rolling(window=4)" in prompt, "Missing success pattern 1"
    assert "liquidity_filter > 150,000,000" in prompt, "Missing success pattern 2"
    assert "INCREMENTAL improvements" in prompt, "Missing incremental directive"

    # Section D: Improvement Focus (Section C tested separately)
    assert "EXPLORE these improvements" in prompt, "Missing Section D header"
    assert "Fine-tune factor weights" in prompt, "Missing improvement suggestion"

    # Base content should still be included
    assert base_prompt in prompt, "Base prompt missing"
    assert feedback_summary in prompt, "Feedback summary missing"


def test_diversity_forcing_iteration_5(base_prompt, feedback_summary, sample_champion):
    """Test 3: Verify exploration forced at iteration 5."""

    builder = PromptBuilder()

    prompt = builder.build_evolutionary_prompt(
        iteration_num=5,
        champion=sample_champion,
        feedback_summary=feedback_summary,
        base_prompt=base_prompt,
        failure_patterns=None
    )

    # Should force exploration mode
    assert "[EXPLORATION MODE: Try new approaches]" in prompt, "Missing exploration mode marker"
    assert base_prompt in prompt, "Base prompt missing"
    assert feedback_summary in prompt, "Feedback missing"

    # Should NOT have preservation constraints
    assert "PRESERVE" not in prompt, "Should not have preservation in exploration mode"
    assert "MANDATORY REQUIREMENTS" not in prompt, "Should not have requirements in exploration mode"


def test_diversity_forcing_iteration_10(base_prompt, feedback_summary, sample_champion):
    """Test 4: Verify exploration forced at iteration 10."""

    builder = PromptBuilder()

    prompt = builder.build_evolutionary_prompt(
        iteration_num=10,
        champion=sample_champion,
        feedback_summary=feedback_summary,
        base_prompt=base_prompt,
        failure_patterns=None
    )

    # Should force exploration mode (10 % 5 == 0)
    assert "[EXPLORATION MODE: Try new approaches]" in prompt, "Missing exploration mode marker"

    # Should NOT have preservation constraints
    assert "PRESERVE" not in prompt, "Should not have preservation in exploration mode"


def test_section_b_includes_all_patterns(base_prompt, feedback_summary, sample_champion):
    """Test 5: Verify all success patterns are listed in Section B."""

    builder = PromptBuilder()

    prompt = builder.build_evolutionary_prompt(
        iteration_num=7,  # Not divisible by 5
        champion=sample_champion,
        feedback_summary=feedback_summary,
        base_prompt=base_prompt,
        failure_patterns=None
    )

    # All 3 success patterns should be in the prompt
    assert "roe.rolling(window=4)" in prompt, "Missing pattern 1"
    assert "liquidity_filter > 150,000,000" in prompt, "Missing pattern 2"
    assert "revenue_yoy.ffill()" in prompt, "Missing pattern 3"

    # Patterns should be numbered
    assert "1." in prompt and "2." in prompt and "3." in prompt, "Patterns not numbered"


def test_section_c_uses_learned_failures(base_prompt, feedback_summary, sample_champion, sample_failure_patterns):
    """Test 6: Verify Section C uses learned failure patterns."""

    builder = PromptBuilder()

    prompt = builder.build_evolutionary_prompt(
        iteration_num=6,
        champion=sample_champion,
        feedback_summary=feedback_summary,
        base_prompt=base_prompt,
        failure_patterns=sample_failure_patterns
    )

    # Section C should use learned patterns
    assert "AVOID (from actual regressions):" in prompt, "Missing dynamic AVOID section"
    assert "Removing ROE smoothing" in prompt, "Missing failure pattern 1"
    assert "Relaxing liquidity filter" in prompt, "Missing failure pattern 2"
    assert "learned from iter" in prompt, "Missing iteration attribution"


def test_section_c_fallback_to_static(base_prompt, feedback_summary, sample_champion):
    """Test 7: Verify Section C fallback to static guidelines when no failures."""

    builder = PromptBuilder()

    prompt = builder.build_evolutionary_prompt(
        iteration_num=6,
        champion=sample_champion,
        feedback_summary=feedback_summary,
        base_prompt=base_prompt,
        failure_patterns=None  # No learned failures
    )

    # Should use static fallback guidelines
    assert "AVOID (general guidelines):" in prompt, "Missing static AVOID section"
    assert "Removing data smoothing" in prompt, "Missing static guideline 1"
    assert "Relaxing liquidity filters" in prompt, "Missing static guideline 2"
    assert "Over-complicated multi-factor" in prompt, "Missing static guideline 3"


# Edge Case Tests

def test_no_champion_returns_base_prompt(base_prompt, feedback_summary):
    """Test edge case: No champion exists (champion=None)."""

    builder = PromptBuilder()

    prompt = builder.build_evolutionary_prompt(
        iteration_num=10,  # High iteration but no champion
        champion=None,
        feedback_summary=feedback_summary,
        base_prompt=base_prompt,
        failure_patterns=None
    )

    # Should return base prompt (exploration mode)
    assert base_prompt in prompt, "Base prompt missing"
    assert feedback_summary in prompt, "Feedback missing"
    assert "PRESERVE" not in prompt, "Should not have preservation without champion"


def test_champion_with_empty_patterns(base_prompt, feedback_summary):
    """Test edge case: Champion with no success patterns."""

    champion_no_patterns = ChampionStrategy(
        iteration_num=2,
        code="# Code",
        parameters={'roe_type': 'raw'},
        metrics={'sharpe_ratio': 0.55},
        success_patterns=[],  # Empty
        timestamp=datetime.now().isoformat()
    )

    builder = PromptBuilder()

    prompt = builder.build_evolutionary_prompt(
        iteration_num=4,
        champion=champion_no_patterns,
        feedback_summary=feedback_summary,
        base_prompt=base_prompt,
        failure_patterns=None
    )

    # Should still generate prompt without crashing
    assert "LEARNING FROM SUCCESS" in prompt, "Missing champion context"
    assert "PRESERVE these proven success factors:" in prompt, "Missing preservation header"
    # No patterns listed, but header should be there


def test_should_force_exploration_logic():
    """Test _should_force_exploration() helper function."""

    builder = PromptBuilder()

    # Should return True for multiples of 5 (except 0)
    assert builder._should_force_exploration(5) is True, "Should force at iteration 5"
    assert builder._should_force_exploration(10) is True, "Should force at iteration 10"
    assert builder._should_force_exploration(15) is True, "Should force at iteration 15"

    # Should return False for non-multiples and iteration 0
    assert builder._should_force_exploration(0) is False, "Should not force at iteration 0"
    assert builder._should_force_exploration(1) is False, "Should not force at iteration 1"
    assert builder._should_force_exploration(4) is False, "Should not force at iteration 4"
    assert builder._should_force_exploration(6) is False, "Should not force at iteration 6"
    assert builder._should_force_exploration(9) is False, "Should not force at iteration 9"


def test_prompt_structure_consistency(base_prompt, feedback_summary, sample_champion):
    """Test that prompt structure is consistent across iterations."""

    builder = PromptBuilder()

    for iteration in [3, 4, 7, 8]:  # Non-exploration iterations
        prompt = builder.build_evolutionary_prompt(
            iteration_num=iteration,
            champion=sample_champion,
            feedback_summary=feedback_summary,
            base_prompt=base_prompt,
            failure_patterns=None
        )

        # All should have the same structure
        assert "LEARNING FROM SUCCESS" in prompt, f"Missing structure in iteration {iteration}"
        assert "MANDATORY REQUIREMENTS:" in prompt, f"Missing structure in iteration {iteration}"
        assert "EXPLORE these improvements" in prompt, f"Missing structure in iteration {iteration}"


def test_iteration_3_exact_behavior(base_prompt, feedback_summary, sample_champion):
    """Test iteration 3 specifically (first exploitation iteration)."""

    builder = PromptBuilder()

    prompt = builder.build_evolutionary_prompt(
        iteration_num=3,
        champion=sample_champion,
        feedback_summary=feedback_summary,
        base_prompt=base_prompt,
        failure_patterns=None
    )

    # Should be exploitation mode (not exploration)
    assert "LEARNING FROM SUCCESS" in prompt, "Should be in exploitation mode at iteration 3"
    assert "[EXPLORATION MODE" not in prompt, "Should not be forcing exploration at iteration 3"


def test_long_failure_patterns_list(base_prompt, feedback_summary, sample_champion):
    """Test handling of many failure patterns."""

    # Create 20 failure patterns
    many_failures = [f"Avoid: Pattern {i} (learned from iter {i})" for i in range(20)]

    builder = PromptBuilder()

    prompt = builder.build_evolutionary_prompt(
        iteration_num=8,
        champion=sample_champion,
        feedback_summary=feedback_summary,
        base_prompt=base_prompt,
        failure_patterns=many_failures
    )

    # All patterns should be included (no truncation in this method)
    assert "AVOID (from actual regressions):" in prompt, "Missing AVOID section"

    # Count how many patterns are in the prompt
    pattern_count = prompt.count("Avoid: Pattern")
    assert pattern_count == 20, f"Expected 20 patterns in prompt, got {pattern_count}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
