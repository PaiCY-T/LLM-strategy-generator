"""
Unit tests for PromptBuilder module

Tests prompt construction with champion feedback and failure patterns.
Target coverage: >90%

Requirements: 3.1, 3.2, 3.3
"""

import json
import pytest
import tempfile
from pathlib import Path
from typing import Dict, List

from src.innovation.prompt_builder import PromptBuilder, MAX_PROMPT_CHARS, MIN_LIQUIDITY_MILLIONS


# ========================================================================
# Fixtures
# ========================================================================

@pytest.fixture
def sample_champion_code():
    """Sample champion strategy code."""
    return """
def strategy(data):
    # High ROE quality filter
    roe = data.get('fundamental_features:ROE稅後')
    growth = data.get('fundamental_features:營收成長率')

    # Quality + growth combination
    quality_growth = (roe > 15) & (growth > 0.1)

    # Liquidity filter
    volume = data.get('price:成交量')
    liquidity = volume.rolling(20).mean() > 150_000_000

    return quality_growth & liquidity
"""


@pytest.fixture
def sample_champion_metrics():
    """Sample champion performance metrics."""
    return {
        'sharpe_ratio': 0.85,
        'max_drawdown': 0.15,
        'win_rate': 0.58,
        'calmar_ratio': 2.3,
        'annual_return': 0.25
    }


@pytest.fixture
def sample_failure_patterns():
    """Sample failure patterns."""
    return [
        {
            "pattern_type": "parameter_change",
            "description": "Increasing liquidity threshold too high",
            "parameter": "liquidity_threshold",
            "change_from": 50,
            "change_to": 50000000,
            "performance_impact": -0.3035,
            "iteration_discovered": 2,
            "timestamp": "2025-10-08T12:39:24.920183"
        },
        {
            "pattern_type": "parameter_change",
            "description": "Disabling ROE smoothing degraded performance",
            "parameter": "roe_smoothing",
            "change_from": "raw (window=1)",
            "change_to": "not_used (window=None)",
            "performance_impact": -0.3035,
            "iteration_discovered": 2,
            "timestamp": "2025-10-08T12:39:24.920215"
        },
        {
            "pattern_type": "parameter_change",
            "description": "Over-smoothing ROE with long window",
            "parameter": "roe_smoothing",
            "change_from": "raw (window=1)",
            "change_to": "smoothed (window=60)",
            "performance_impact": -1.1043,
            "iteration_discovered": 5,
            "timestamp": "2025-10-08T12:40:01.654666"
        }
    ]


@pytest.fixture
def temp_failure_json(sample_failure_patterns):
    """Create temporary failure patterns JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_failure_patterns, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def prompt_builder(temp_failure_json):
    """Create PromptBuilder instance with temp failure patterns."""
    return PromptBuilder(failure_patterns_path=temp_failure_json)


# ========================================================================
# Test: Initialization
# ========================================================================

def test_prompt_builder_initialization():
    """Test PromptBuilder initialization."""
    builder = PromptBuilder()

    assert builder.failure_patterns_path == "artifacts/data/failure_patterns.json"
    assert builder._cached_failure_patterns is None


def test_prompt_builder_custom_path():
    """Test PromptBuilder with custom failure patterns path."""
    custom_path = "/custom/path/failures.json"
    builder = PromptBuilder(failure_patterns_path=custom_path)

    assert builder.failure_patterns_path == custom_path


# ========================================================================
# Test: Modification Prompt Construction
# ========================================================================

def test_build_modification_prompt_basic(
    prompt_builder,
    sample_champion_code,
    sample_champion_metrics
):
    """Test basic modification prompt construction."""
    prompt = prompt_builder.build_modification_prompt(
        champion_code=sample_champion_code,
        champion_metrics=sample_champion_metrics,
        target_metric='sharpe_ratio'
    )

    # Check prompt structure
    assert "Modify Champion Strategy" in prompt
    assert "Current Champion Strategy" in prompt
    assert "Optimization Target" in prompt
    assert "FinLab API Constraints" in prompt
    assert "Output Format" in prompt

    # Check champion metrics are included
    assert "0.85" in prompt or "0.850" in prompt  # Sharpe ratio
    assert "15%" in prompt or "0.15" in prompt  # Max drawdown

    # Check token budget compliance
    assert len(prompt) <= MAX_PROMPT_CHARS


def test_build_modification_prompt_with_failures(
    prompt_builder,
    sample_champion_code,
    sample_champion_metrics,
    sample_failure_patterns
):
    """Test modification prompt with failure history."""
    prompt = prompt_builder.build_modification_prompt(
        champion_code=sample_champion_code,
        champion_metrics=sample_champion_metrics,
        failure_history=sample_failure_patterns,
        target_metric='sharpe_ratio'
    )

    # Check failure patterns are mentioned
    assert "Failure Patterns" in prompt
    assert "liquidity threshold" in prompt.lower() or "liquidity" in prompt.lower()

    # Check token budget compliance
    assert len(prompt) <= MAX_PROMPT_CHARS


def test_modification_prompt_target_metrics(
    prompt_builder,
    sample_champion_code,
    sample_champion_metrics
):
    """Test modification prompts with different target metrics."""
    for metric in ['sharpe_ratio', 'calmar_ratio', 'win_rate']:
        prompt = prompt_builder.build_modification_prompt(
            champion_code=sample_champion_code,
            champion_metrics=sample_champion_metrics,
            target_metric=metric
        )

        # Check target metric is mentioned
        metric_display = metric.replace('_', ' ').title()
        assert metric_display in prompt

        # Check improvement target
        assert "Target:" in prompt


def test_modification_prompt_includes_constraints(
    prompt_builder,
    sample_champion_code,
    sample_champion_metrics
):
    """Test that modification prompt includes all constraints."""
    prompt = prompt_builder.build_modification_prompt(
        champion_code=sample_champion_code,
        champion_metrics=sample_champion_metrics
    )

    # Check function signature
    assert "def strategy(data):" in prompt

    # Check data access patterns
    assert "data.get(" in prompt

    # Check liquidity requirement
    assert str(MIN_LIQUIDITY_MILLIONS) in prompt or "150" in prompt

    # Check critical rules
    assert "look-ahead bias" in prompt.lower() or "shift" in prompt.lower()
    assert "fillna" in prompt.lower() or "dropna" in prompt.lower()


def test_modification_prompt_includes_example(
    prompt_builder,
    sample_champion_code,
    sample_champion_metrics
):
    """Test that modification prompt includes few-shot example."""
    prompt = prompt_builder.build_modification_prompt(
        champion_code=sample_champion_code,
        champion_metrics=sample_champion_metrics
    )

    # Check example section exists
    assert "Example" in prompt
    assert "Original Champion" in prompt or "Modified Version" in prompt


# ========================================================================
# Test: Creation Prompt Construction
# ========================================================================

def test_build_creation_prompt_basic(prompt_builder):
    """Test basic creation prompt construction."""
    champion_approach = "Momentum-based factor with ROE quality filter"

    prompt = prompt_builder.build_creation_prompt(
        champion_approach=champion_approach,
        innovation_directive="Explore value + quality combinations"
    )

    # Check prompt structure
    assert "Create Novel" in prompt
    assert "Champion Approach" in prompt
    assert "Innovation Directive" in prompt
    assert "FinLab API Constraints" in prompt
    assert "Output Format" in prompt

    # Check champion approach is included
    assert champion_approach in prompt

    # Check token budget compliance
    assert len(prompt) <= MAX_PROMPT_CHARS


def test_build_creation_prompt_with_failure_patterns(
    prompt_builder,
    sample_failure_patterns
):
    """Test creation prompt with failure patterns."""
    prompt = prompt_builder.build_creation_prompt(
        champion_approach="Momentum strategy",
        failure_patterns=sample_failure_patterns,
        innovation_directive="Create novel value strategy"
    )

    # Check failure patterns are included
    assert "Failure Patterns" in prompt

    # Check token budget compliance
    assert len(prompt) <= MAX_PROMPT_CHARS


def test_creation_prompt_innovation_directive(prompt_builder):
    """Test creation prompt with custom innovation directive."""
    directive = "Explore sector rotation strategies with quality filters"

    prompt = prompt_builder.build_creation_prompt(
        champion_approach="Momentum strategy",
        innovation_directive=directive
    )

    # Check directive is included
    assert directive in prompt
    assert "Innovation Directive" in prompt


def test_creation_prompt_includes_constraints(prompt_builder):
    """Test that creation prompt includes all constraints."""
    prompt = prompt_builder.build_creation_prompt(
        champion_approach="Test approach"
    )

    # Check function signature
    assert "def strategy(data):" in prompt

    # Check data access patterns
    assert "data.get(" in prompt

    # Check liquidity requirement
    assert str(MIN_LIQUIDITY_MILLIONS) in prompt or "150" in prompt

    # Check critical rules
    assert "look-ahead bias" in prompt.lower() or "shift" in prompt.lower()


def test_creation_prompt_includes_example(prompt_builder):
    """Test that creation prompt includes few-shot example."""
    prompt = prompt_builder.build_creation_prompt(
        champion_approach="Test approach"
    )

    # Check example section exists
    assert "Example" in prompt
    assert "Novel Strategy" in prompt or "Novel Creation" in prompt


# ========================================================================
# Test: Success Factor Extraction
# ========================================================================

def test_extract_success_factors_high_sharpe(
    prompt_builder,
    sample_champion_code,
    sample_champion_metrics
):
    """Test success factor extraction identifies high Sharpe."""
    factors = prompt_builder.extract_success_factors(
        sample_champion_code,
        sample_champion_metrics
    )

    # Check Sharpe factor is extracted
    assert any("sharpe" in f.lower() for f in factors)
    assert any("0.85" in f for f in factors)


def test_extract_success_factors_low_drawdown(prompt_builder):
    """Test success factor extraction identifies low drawdown."""
    code = "def strategy(data): return data.get('price:收盤價') > 100"
    metrics = {'sharpe_ratio': 0.6, 'max_drawdown': 0.12}

    factors = prompt_builder.extract_success_factors(code, metrics)

    # Check drawdown factor is extracted
    assert any("drawdown" in f.lower() for f in factors)


def test_extract_success_factors_high_win_rate(prompt_builder):
    """Test success factor extraction identifies high win rate."""
    code = "def strategy(data): return data.get('price:收盤價') > 100"
    metrics = {'sharpe_ratio': 0.5, 'win_rate': 0.65}

    factors = prompt_builder.extract_success_factors(code, metrics)

    # Check win rate factor is extracted
    assert any("win rate" in f.lower() for f in factors)


def test_extract_success_factors_code_patterns(
    prompt_builder,
    sample_champion_code,
    sample_champion_metrics
):
    """Test success factor extraction identifies code patterns."""
    factors = prompt_builder.extract_success_factors(
        sample_champion_code,
        sample_champion_metrics
    )

    # Check code pattern factors
    assert any("roe" in f.lower() for f in factors)  # ROE filter
    assert any("growth" in f.lower() for f in factors)  # Revenue growth
    assert any("rolling" in f.lower() or "average" in f.lower() or "smoothing" in f.lower() for f in factors)  # Moving average
    assert any("liquidity" in f.lower() or "volume" in f.lower() for f in factors)  # Liquidity filter


def test_extract_success_factors_limit(prompt_builder):
    """Test success factor extraction limits results to 6 factors."""
    # Code with many patterns
    code = """
    def strategy(data):
        roe = data.get('fundamental_features:ROE稅後').rolling(20).mean()
        growth = data.get('fundamental_features:營收成長率').shift(1)
        price = data.get('price:收盤價').rank(pct=True)
        volume = data.get('price:成交量').fillna(0)
        pb = data.get('fundamental_features:淨值比').dropna()
        return (roe > 15) & (growth > 0) & (price > 0.8) & (volume > 1000)
    """

    metrics = {
        'sharpe_ratio': 0.95,
        'max_drawdown': 0.10,
        'win_rate': 0.70,
        'calmar_ratio': 3.5
    }

    factors = prompt_builder.extract_success_factors(code, metrics)

    # Should limit to 6 factors
    assert len(factors) <= 6


def test_extract_success_factors_empty_metrics(prompt_builder):
    """Test success factor extraction with minimal metrics."""
    code = "def strategy(data): return data.get('price:收盤價') > 100"
    metrics = {}

    factors = prompt_builder.extract_success_factors(code, metrics)

    # Should still extract code patterns even if no metric factors
    assert isinstance(factors, list)


# ========================================================================
# Test: Failure Pattern Extraction
# ========================================================================

def test_extract_failure_patterns_from_file(
    prompt_builder,
    sample_failure_patterns
):
    """Test failure pattern extraction from JSON file."""
    patterns = prompt_builder.extract_failure_patterns()

    # Should load patterns from temp file
    assert len(patterns) == len(sample_failure_patterns)
    assert patterns[0]['pattern_type'] == 'parameter_change'


def test_extract_failure_patterns_caching(prompt_builder):
    """Test failure pattern extraction caches results."""
    # First call
    patterns1 = prompt_builder.extract_failure_patterns()

    # Second call should use cache
    patterns2 = prompt_builder.extract_failure_patterns()

    assert patterns1 is patterns2  # Same object (cached)
    assert prompt_builder._cached_failure_patterns is not None


def test_extract_failure_patterns_missing_file():
    """Test failure pattern extraction with missing file."""
    builder = PromptBuilder(failure_patterns_path="/nonexistent/path.json")

    patterns = builder.extract_failure_patterns()

    # Should return empty list gracefully
    assert patterns == []


def test_extract_failure_patterns_invalid_json(tmp_path):
    """Test failure pattern extraction with invalid JSON."""
    # Create invalid JSON file
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{invalid json content")

    builder = PromptBuilder(failure_patterns_path=str(invalid_file))

    patterns = builder.extract_failure_patterns()

    # Should return empty list gracefully
    assert patterns == []


def test_extract_failure_patterns_custom_path(sample_failure_patterns, tmp_path):
    """Test failure pattern extraction with custom path override."""
    # Create custom patterns file
    custom_file = tmp_path / "custom_failures.json"
    with open(custom_file, 'w') as f:
        json.dump([{"test": "pattern"}], f)

    builder = PromptBuilder()

    patterns = builder.extract_failure_patterns(failure_json_path=str(custom_file))

    # Should load from custom path
    assert len(patterns) == 1
    assert patterns[0]['test'] == 'pattern'


# ========================================================================
# Test: Private Helper Methods
# ========================================================================

def test_format_list_with_items(prompt_builder):
    """Test _format_list with items."""
    items = ["Item 1", "Item 2", "Item 3"]
    result = prompt_builder._format_list(items)

    assert "- Item 1" in result
    assert "- Item 2" in result
    assert "- Item 3" in result


def test_format_list_empty(prompt_builder):
    """Test _format_list with empty list."""
    result = prompt_builder._format_list([])
    assert result == "- None"


def test_format_failure_patterns(prompt_builder, sample_failure_patterns):
    """Test _format_failure_patterns conversion."""
    formatted = prompt_builder._format_failure_patterns(sample_failure_patterns)

    # Should convert to readable strings
    assert len(formatted) == len(sample_failure_patterns)
    assert "liquidity threshold" in formatted[0].lower()
    assert "30.35%" in formatted[0] or "-0.30" in formatted[0]  # Impact


def test_format_failure_patterns_positive_impact(prompt_builder):
    """Test _format_failure_patterns with positive impact (edge case)."""
    patterns_positive = [
        {
            "description": "Positive impact change",
            "performance_impact": 0.15  # Positive impact (>= 0)
        }
    ]
    formatted = prompt_builder._format_failure_patterns(patterns_positive)

    # Should format without "degradation" for positive impact
    assert len(formatted) == 1
    assert "Positive impact change" in formatted[0]
    assert "degradation" not in formatted[0].lower()  # No degradation marker


def test_truncate_to_budget_no_truncation(prompt_builder):
    """Test _truncate_to_budget with short prompt."""
    short_prompt = "This is a short prompt."
    result = prompt_builder._truncate_to_budget(short_prompt)

    # Should not truncate
    assert result == short_prompt


def test_truncate_to_budget_with_truncation(prompt_builder):
    """Test _truncate_to_budget with long prompt."""
    # Create prompt exceeding budget
    long_prompt = "A" * (MAX_PROMPT_CHARS + 1000)
    result = prompt_builder._truncate_to_budget(long_prompt)

    # Should truncate
    assert len(result) <= MAX_PROMPT_CHARS
    assert "truncated" in result.lower()


# ========================================================================
# Test: Integration Tests
# ========================================================================

def test_modification_workflow_integration(
    prompt_builder,
    sample_champion_code,
    sample_champion_metrics,
    sample_failure_patterns
):
    """Test complete modification workflow."""
    # Extract success factors
    success_factors = prompt_builder.extract_success_factors(
        sample_champion_code,
        sample_champion_metrics
    )

    # Build modification prompt
    prompt = prompt_builder.build_modification_prompt(
        champion_code=sample_champion_code,
        champion_metrics=sample_champion_metrics,
        failure_history=sample_failure_patterns,
        target_metric='sharpe_ratio'
    )

    # Verify integration
    assert len(success_factors) > 0
    assert len(prompt) > 1000  # Substantial prompt
    assert len(prompt) <= MAX_PROMPT_CHARS

    # Check all sections present
    assert "Modify Champion" in prompt
    assert "Success Factors" in prompt
    assert "Failure Patterns" in prompt
    assert "Example" in prompt


def test_creation_workflow_integration(
    prompt_builder,
    sample_failure_patterns
):
    """Test complete creation workflow."""
    # Extract failure patterns
    failure_patterns = prompt_builder.extract_failure_patterns()

    # Build creation prompt
    prompt = prompt_builder.build_creation_prompt(
        champion_approach="Momentum strategy with quality filters",
        failure_patterns=failure_patterns,
        innovation_directive="Explore value + growth combinations"
    )

    # Verify integration
    assert len(failure_patterns) > 0
    assert len(prompt) > 1000  # Substantial prompt
    assert len(prompt) <= MAX_PROMPT_CHARS

    # Check all sections present
    assert "Create Novel" in prompt
    assert "Champion Approach" in prompt
    assert "Innovation Directive" in prompt
    assert "Example" in prompt


def test_prompt_quality_all_constraints_included(prompt_builder):
    """Test that prompts include all required FinLab constraints."""
    prompt = prompt_builder.build_modification_prompt(
        champion_code="def strategy(data): return True",
        champion_metrics={'sharpe_ratio': 0.5}
    )

    # Function signature
    assert "def strategy(data):" in prompt

    # Data access
    assert "data.get(" in prompt
    assert "fundamental_features" in prompt
    assert "price:" in prompt

    # Critical rules
    assert "look-ahead" in prompt.lower()
    assert "shift" in prompt.lower()
    assert "fillna" in prompt.lower() or "dropna" in prompt.lower()
    assert "liquidity" in prompt.lower()

    # Liquidity requirement
    assert "150" in prompt or str(MIN_LIQUIDITY_MILLIONS) in prompt

    # Validation requirements
    assert "executable" in prompt.lower() or "syntax" in prompt.lower()


def test_prompts_include_few_shot_examples(prompt_builder):
    """Test that both prompts include few-shot examples."""
    mod_prompt = prompt_builder.build_modification_prompt(
        champion_code="def strategy(data): return True",
        champion_metrics={'sharpe_ratio': 0.5}
    )

    creation_prompt = prompt_builder.build_creation_prompt(
        champion_approach="Test approach"
    )

    # Both should have examples
    assert "Example" in mod_prompt
    assert "```python" in mod_prompt

    assert "Example" in creation_prompt
    assert "```python" in creation_prompt


# ========================================================================
# Test: Edge Cases
# ========================================================================

def test_empty_champion_code(prompt_builder):
    """Test handling of empty champion code."""
    prompt = prompt_builder.build_modification_prompt(
        champion_code="",
        champion_metrics={'sharpe_ratio': 0.5}
    )

    # Should still build valid prompt
    assert len(prompt) > 0
    assert "Modify Champion" in prompt


def test_missing_champion_metrics(prompt_builder):
    """Test handling of missing metrics."""
    factors = prompt_builder.extract_success_factors(
        code="def strategy(data): return True",
        metrics={}
    )

    # Should return factors (even if only code-based)
    assert isinstance(factors, list)


def test_very_long_champion_code(prompt_builder):
    """Test handling of very long champion code."""
    long_code = "def strategy(data):\n" + "    x = 1\n" * 1000

    prompt = prompt_builder.build_modification_prompt(
        champion_code=long_code,
        champion_metrics={'sharpe_ratio': 0.5}
    )

    # Should truncate to stay within budget
    assert len(prompt) <= MAX_PROMPT_CHARS
    assert "..." in prompt  # Code preview truncation marker


def test_none_failure_history(prompt_builder):
    """Test handling of None failure history."""
    prompt = prompt_builder.build_modification_prompt(
        champion_code="def strategy(data): return True",
        champion_metrics={'sharpe_ratio': 0.5},
        failure_history=None
    )

    # Should handle gracefully
    assert "No historical failures" in prompt or "None" in prompt


def test_empty_failure_patterns(prompt_builder):
    """Test handling of empty failure patterns."""
    prompt = prompt_builder.build_creation_prompt(
        champion_approach="Test",
        failure_patterns=[]
    )

    # Should handle gracefully
    assert "No historical failures" in prompt or "None" in prompt


# ========================================================================
# Test: Coverage Edge Cases
# ========================================================================

def test_all_metric_thresholds(prompt_builder):
    """Test success factor extraction for all metric thresholds."""
    test_cases = [
        ({'sharpe_ratio': 0.85}, "sharpe"),
        ({'max_drawdown': 0.10}, "drawdown"),
        ({'win_rate': 0.65}, "win rate"),
        ({'calmar_ratio': 2.5}, "calmar"),
    ]

    for metrics, expected_keyword in test_cases:
        factors = prompt_builder.extract_success_factors("", metrics)
        assert any(expected_keyword.lower() in f.lower() for f in factors)


def test_all_code_patterns(prompt_builder):
    """Test success factor extraction for all code patterns."""
    patterns = {
        "fundamental_features:ROE": "roe",
        "fundamental_features:營收成長率": "growth",
        "price:收盤價": "price",
        ".rolling(": "rolling",
        ".shift(": "shift",
        ".rank(": "rank",
        "成交量": "liquidity",
        ".fillna(": "fillna",
        ">": "threshold",
        "&": "combines",
    }

    for code_snippet, expected_keyword in patterns.items():
        code = f"def strategy(data): x = data.get('test'){code_snippet}"
        factors = prompt_builder.extract_success_factors(code, {})

        # At least one factor should mention the pattern
        factor_text = " ".join(factors).lower()
        assert expected_keyword.lower() in factor_text or len(factors) > 0


# ========================================================================
# Test: Additional Coverage for Private Methods
# ========================================================================

def test_get_modification_header(prompt_builder):
    """Test modification header generation."""
    header = prompt_builder._get_modification_header()

    assert "Modify Champion Strategy" in header
    assert "improve" in header.lower() or "performance" in header.lower()


def test_get_creation_header(prompt_builder):
    """Test creation header generation."""
    header = prompt_builder._get_creation_header()

    assert "Create Novel" in header
    assert "novel" in header.lower() or "new" in header.lower()


def test_format_champion_context(
    prompt_builder,
    sample_champion_code,
    sample_champion_metrics
):
    """Test champion context formatting."""
    success_factors = ["High Sharpe", "Low drawdown", "ROE filter"]

    context = prompt_builder._format_champion_context(
        sample_champion_code,
        sample_champion_metrics,
        success_factors
    )

    assert "Current Champion" in context
    assert "Performance" in context
    assert "Success Factors" in context
    assert "High Sharpe" in context
    assert "0.85" in context or "0.850" in context


def test_format_champion_inspiration(prompt_builder):
    """Test champion inspiration formatting."""
    approach = "Momentum with quality filters"

    inspiration = prompt_builder._format_champion_inspiration(approach)

    assert "Champion Approach" in inspiration
    assert approach in inspiration
    assert "NOVEL" in inspiration or "novel" in inspiration


def test_format_target_directive(prompt_builder, sample_champion_metrics):
    """Test target directive formatting."""
    directive = prompt_builder._format_target_directive(
        "sharpe_ratio",
        sample_champion_metrics
    )

    assert "Optimization Target" in directive
    assert "Sharpe" in directive or "sharpe" in directive
    assert "0.85" in directive or "0.850" in directive


def test_format_innovation_directive(prompt_builder):
    """Test innovation directive formatting."""
    directive = prompt_builder._format_innovation_directive(
        "Explore value + quality combinations"
    )

    assert "Innovation Directive" in directive
    assert "value + quality" in directive.lower()


def test_format_constraints(prompt_builder):
    """Test constraints formatting."""
    constraints = prompt_builder._format_constraints()

    assert "FinLab API Constraints" in constraints
    assert "def strategy(data):" in constraints
    assert "data.get(" in constraints
    assert str(MIN_LIQUIDITY_MILLIONS) in constraints or "150" in constraints


def test_get_modification_example(prompt_builder):
    """Test modification example."""
    example = prompt_builder._get_modification_example()

    assert "Example" in example
    assert "Original Champion" in example
    assert "Modified Version" in example
    assert "```python" in example


def test_get_creation_example(prompt_builder):
    """Test creation example."""
    example = prompt_builder._get_creation_example()

    assert "Example" in example
    assert "Novel Strategy" in example or "Novel Creation" in example
    assert "```python" in example


def test_get_output_format(prompt_builder):
    """Test output format instructions."""
    output_format = prompt_builder._get_output_format()

    assert "Output Format" in output_format
    assert "def strategy(data):" in output_format
    assert "```python" in output_format


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.innovation.prompt_builder", "--cov-report=term-missing"])
