"""
Integration tests for feedback generation (Task 17).

Tests the complete feedback generation pipeline:
- Attributed feedback with champion and failure patterns
- Simple feedback without champion
- Graceful fallback on attribution errors
"""

import pytest
from typing import Dict, List, Any
from datetime import datetime

# Import modules under test
from prompt_builder import PromptBuilder
from autonomous_loop import ChampionStrategy
from performance_attributor import (
    extract_strategy_params,
    compare_strategies,
    generate_attribution_feedback
)


# Test Fixtures

@pytest.fixture
def sample_champion_code() -> str:
    """Sample champion strategy code for testing."""
    return """
# Champion Strategy (Iteration 3, Sharpe 0.97)

# Data loading
data = data.get('price:收盤價')
roe = data.get('fundamental_features:ROE綜合損益')
revenue = data.get('fundamental_features:營收成長率')
trading_value = data.get('price:成交金額')

# Liquidity filter (critical)
liquidity_filter = trading_value > 100_000_000

# ROE smoothing (critical)
roe_smoothed = roe.rolling(window=4).mean()

# Revenue forward fill (moderate)
revenue_filled = revenue.ffill()

# Combine signals
value_factor = 1 / data.get('fundamental_features:本益比')
combined_signal = roe_smoothed * 0.6 + value_factor * 0.4

# Apply filters
signal = combined_signal[liquidity_filter & revenue_filled.notna()]
"""


@pytest.fixture
def sample_current_code() -> str:
    """Sample current strategy code for comparison."""
    return """
# Current Strategy (Iteration 5)

data = data.get('price:收盤價')
roe = data.get('fundamental_features:ROE綜合損益')
revenue = data.get('fundamental_features:營收成長率')
trading_value = data.get('price:成交金額')

# Liquidity filter - CHANGED to 80M (relaxed)
liquidity_filter = trading_value > 80_000_000

# ROE smoothing - PRESERVED
roe_smoothed = roe.rolling(window=4).mean()

# Revenue handling - CHANGED to dropna
revenue_clean = revenue.dropna()

# Combine signals - CHANGED weights
value_factor = 1 / data.get('fundamental_features:本益比')
combined_signal = roe_smoothed * 0.7 + value_factor * 0.3

signal = combined_signal[liquidity_filter & revenue_clean.notna()]
"""


@pytest.fixture
def champion_metrics() -> Dict[str, float]:
    """Sample champion performance metrics."""
    return {
        'sharpe_ratio': 0.97,
        'annual_return': 0.18,
        'max_drawdown': -0.12,
        'win_rate': 0.55
    }


@pytest.fixture
def current_metrics_improved() -> Dict[str, float]:
    """Sample current metrics (improved)."""
    return {
        'sharpe_ratio': 1.02,
        'annual_return': 0.21,
        'max_drawdown': -0.10,
        'win_rate': 0.58
    }


@pytest.fixture
def current_metrics_degraded() -> Dict[str, float]:
    """Sample current metrics (degraded)."""
    return {
        'sharpe_ratio': 0.85,
        'annual_return': 0.14,
        'max_drawdown': -0.18,
        'win_rate': 0.48
    }


@pytest.fixture
def sample_champion(sample_champion_code, champion_metrics) -> ChampionStrategy:
    """Sample ChampionStrategy instance."""
    params = extract_strategy_params(sample_champion_code)

    return ChampionStrategy(
        iteration_num=3,
        code=sample_champion_code,
        parameters=params,
        metrics=champion_metrics,
        success_patterns=[
            "roe.rolling(window=4).mean() - 4-quarter smoothing reduces quarterly noise",
            "liquidity_filter > 100,000,000 TWD - Selects stable, high-volume stocks",
            "revenue_yoy.ffill() - Forward-filled revenue data handles missing values",
            "1 / pe_ratio - Value factor using inverse P/E ratio"
        ],
        timestamp=datetime.now().isoformat()
    )


@pytest.fixture
def sample_failure_patterns() -> List[str]:
    """Sample failure patterns from previous iterations."""
    return [
        "Avoid: Relaxing liquidity filter to 80,000,000 (reduces stability) (learned from iter 4)",
        "Avoid: Removing ROE smoothing (increases noise) (learned from iter 2)",
        "Avoid: Changing revenue_handling from forward_filled to dropna (learned from iter 5)"
    ]


# Integration Tests

def test_attributed_feedback_with_champion(
    sample_champion,
    sample_current_code,
    current_metrics_improved
):
    """Test 1: Verify complete attributed feedback generation."""

    builder = PromptBuilder()

    # Extract current parameters and compare
    curr_params = extract_strategy_params(sample_current_code)
    attribution = compare_strategies(
        prev_params=sample_champion.parameters,
        curr_params=curr_params,
        prev_metrics=sample_champion.metrics,
        curr_metrics=current_metrics_improved
    )

    # Generate attributed feedback
    feedback = builder.build_attributed_feedback(
        attribution=attribution,
        iteration_num=5,
        champion=sample_champion,
        failure_patterns=None
    )

    # Verify feedback structure
    assert "CURRENT CHAMPION" in feedback, "Missing champion context"
    assert "Iteration: 3" in feedback, "Missing champion iteration"
    assert "Sharpe Ratio: 0.9700" in feedback, "Missing champion Sharpe"
    assert "Proven Success Patterns:" in feedback, "Missing success patterns section"

    # Verify success patterns included
    assert "roe.rolling(window=4)" in feedback, "Missing ROE smoothing pattern"
    assert "liquidity_filter > 100,000,000" in feedback, "Missing liquidity pattern"

    # Verify attribution analysis included
    # (Attribution feedback format comes from generate_attribution_feedback)
    assert len(feedback) > 200, "Feedback too short - missing attribution analysis"


def test_attributed_feedback_with_failure_patterns(
    sample_champion,
    sample_current_code,
    current_metrics_degraded,
    sample_failure_patterns
):
    """Test 2: Verify failure patterns included in feedback."""

    builder = PromptBuilder()

    # Extract and compare (degraded performance)
    curr_params = extract_strategy_params(sample_current_code)
    attribution = compare_strategies(
        prev_params=sample_champion.parameters,
        curr_params=curr_params,
        prev_metrics=sample_champion.metrics,
        curr_metrics=current_metrics_degraded
    )

    # Generate feedback with failure patterns
    feedback = builder.build_attributed_feedback(
        attribution=attribution,
        iteration_num=6,
        champion=sample_champion,
        failure_patterns=sample_failure_patterns
    )

    # Verify AVOID section present
    assert "AVOID (Learned from Past Failures)" in feedback, "Missing AVOID section"

    # Verify failure patterns included
    assert "Relaxing liquidity filter" in feedback, "Missing liquidity failure pattern"
    assert "Removing ROE smoothing" in feedback, "Missing ROE failure pattern"
    assert "learned from iter" in feedback, "Missing iteration attribution"

    # Verify limit of 10 patterns enforced (we only have 3)
    failure_count = feedback.count("learned from iter")
    assert failure_count == 3, f"Expected 3 failure patterns, got {failure_count}"


def test_simple_feedback_without_champion(champion_metrics):
    """Test 3: Verify simple feedback format when no champion exists."""

    builder = PromptBuilder()

    # Generate simple feedback
    feedback = builder.build_simple_feedback(metrics=champion_metrics)

    # Verify simple feedback structure
    assert "## PERFORMANCE METRICS" in feedback, "Missing metrics header"
    assert "Sharpe Ratio: 0.9700" in feedback, "Missing Sharpe ratio"
    assert "## NEXT STEPS" in feedback, "Missing next steps section"

    # Verify guidance for low Sharpe
    low_sharpe_metrics = {'sharpe_ratio': 0.45, 'annual_return': 0.08}
    feedback_low = builder.build_simple_feedback(metrics=low_sharpe_metrics)
    assert "Strategy shows weak performance" in feedback_low, "Missing weak performance guidance"
    assert "Different factor combinations" in feedback_low, "Missing improvement suggestions"


def test_feedback_fallback_on_attribution_error(sample_champion):
    """Test 4: Verify graceful fallback when attribution fails."""

    builder = PromptBuilder()

    # Simulate attribution failure by passing invalid attribution dict
    # (In practice, this would come from _compare_with_champion returning None)

    # When attribution is None, autonomous_loop should call build_simple_feedback
    # This test verifies that simple feedback works as a fallback

    simple_metrics = {
        'sharpe_ratio': 0.88,
        'annual_return': 0.16,
        'max_drawdown': -0.14
    }

    feedback = builder.build_simple_feedback(metrics=simple_metrics)

    # Verify fallback feedback is complete
    assert "## PERFORMANCE METRICS" in feedback, "Fallback missing metrics"
    assert "Sharpe Ratio: 0.8800" in feedback, "Fallback missing Sharpe"
    assert "## NEXT STEPS" in feedback, "Fallback missing next steps"

    # Verify it doesn't contain attribution-specific content
    assert "CURRENT CHAMPION" not in feedback, "Fallback should not have champion context"
    assert "AVOID" not in feedback, "Fallback should not have failure patterns"


# Edge Case Tests

def test_attributed_feedback_empty_success_patterns(
    sample_champion,
    sample_current_code,
    current_metrics_improved
):
    """Test edge case: Champion with no success patterns."""

    builder = PromptBuilder()

    # Create champion with empty patterns
    champion_no_patterns = ChampionStrategy(
        iteration_num=1,
        code=sample_champion.code,
        parameters=sample_champion.parameters,
        metrics=sample_champion.metrics,
        success_patterns=[],  # Empty
        timestamp=datetime.now().isoformat()
    )

    curr_params = extract_strategy_params(sample_current_code)
    attribution = compare_strategies(
        prev_params=champion_no_patterns.parameters,
        curr_params=curr_params,
        prev_metrics=champion_no_patterns.metrics,
        curr_metrics=current_metrics_improved
    )

    feedback = builder.build_attributed_feedback(
        attribution=attribution,
        iteration_num=2,
        champion=champion_no_patterns,
        failure_patterns=None
    )

    # Should still generate feedback without crashing
    assert "CURRENT CHAMPION" in feedback, "Missing champion section"
    # When empty patterns, header should not be printed
    assert "Proven Success Patterns:" not in feedback, "Empty patterns should not show header"
    # Verify it doesn't crash with empty patterns


def test_simple_feedback_none_metrics():
    """Test edge case: Simple feedback with None metrics."""

    builder = PromptBuilder()

    feedback = builder.build_simple_feedback(metrics=None)

    # Should return guidance message
    assert "No champion yet" in feedback, "Missing no-champion message"
    assert "positive Sharpe ratio" in feedback, "Missing guidance"


def test_attributed_feedback_many_failure_patterns(
    sample_champion,
    sample_current_code,
    current_metrics_degraded
):
    """Test edge case: More than 10 failure patterns (should truncate)."""

    builder = PromptBuilder()

    # Create 15 failure patterns
    many_patterns = [
        f"Avoid: Pattern {i} from iteration {i}"
        for i in range(15)
    ]

    curr_params = extract_strategy_params(sample_current_code)
    attribution = compare_strategies(
        prev_params=sample_champion.parameters,
        curr_params=curr_params,
        prev_metrics=sample_champion.metrics,
        curr_metrics=current_metrics_degraded
    )

    feedback = builder.build_attributed_feedback(
        attribution=attribution,
        iteration_num=10,
        champion=sample_champion,
        failure_patterns=many_patterns
    )

    # Should only include first 10 patterns
    pattern_count = feedback.count("Avoid: Pattern")
    assert pattern_count == 10, f"Expected 10 patterns (truncated), got {pattern_count}"


# Performance Tests

def test_feedback_generation_performance(
    sample_champion,
    sample_current_code,
    current_metrics_improved,
    sample_failure_patterns
):
    """Test that feedback generation completes in reasonable time."""

    import time

    builder = PromptBuilder()

    curr_params = extract_strategy_params(sample_current_code)
    attribution = compare_strategies(
        prev_params=sample_champion.parameters,
        curr_params=curr_params,
        prev_metrics=sample_champion.metrics,
        curr_metrics=current_metrics_improved
    )

    start = time.time()
    feedback = builder.build_attributed_feedback(
        attribution=attribution,
        iteration_num=7,
        champion=sample_champion,
        failure_patterns=sample_failure_patterns
    )
    elapsed = time.time() - start

    # Should complete in <100ms
    assert elapsed < 0.1, f"Feedback generation too slow: {elapsed:.3f}s"
    assert len(feedback) > 0, "No feedback generated"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
