"""
TDD RED Phase: Tests for strategy code validation.

These tests verify that generated strategy code avoids common DataFrame errors.
"""

import pytest
import ast
import re


class TestStrategyCodeValidation:
    """Test suite for strategy code validation to prevent runtime errors."""

    def test_detects_unsafe_dataframe_comparison(self):
        """
        GIVEN strategy code with unsafe DataFrame comparison
        WHEN validating the code
        THEN should detect the unsafe pattern
        """
        # Arrange - code with unsafe comparison pattern
        unsafe_code = '''
position = cond_combined.where(cond_combined).fillna(False)
position = position.where(final_rank == final_rank.max()).is_largest(10)
'''

        # Act
        from src.innovation.strategy_validator import StrategyCodeValidator
        validator = StrategyCodeValidator()
        issues = validator.validate(unsafe_code)

        # Assert
        assert len(issues) > 0
        assert any('DataFrame comparison' in issue or 'where' in issue for issue in issues)

    def test_allows_safe_is_largest_pattern(self):
        """
        GIVEN strategy code with safe is_largest pattern
        WHEN validating the code
        THEN should pass validation
        """
        # Arrange - safe pattern
        safe_code = '''
cond1 = (sma_short > sma_long)
cond2 = (close > sma_short)
position = (cond1 & cond2).is_largest(10)
'''

        # Act
        from src.innovation.strategy_validator import StrategyCodeValidator
        validator = StrategyCodeValidator()
        issues = validator.validate(safe_code)

        # Assert - should have no critical issues
        critical_issues = [i for i in issues if 'critical' in i.lower()]
        assert len(critical_issues) == 0

    def test_detects_rank_comparison_mismatch(self):
        """
        GIVEN strategy code comparing rank result with scalar incorrectly
        WHEN validating the code
        THEN should detect potential mismatch
        """
        # Arrange - problematic rank comparison
        unsafe_code = '''
final_rank = (mom3m.rank(pct=True) + value_pe.rank(pct=True)) / 2
position = position.where(final_rank == final_rank.max())
'''

        # Act
        from src.innovation.strategy_validator import StrategyCodeValidator
        validator = StrategyCodeValidator()
        issues = validator.validate(unsafe_code)

        # Assert
        assert len(issues) > 0

    def test_detects_chained_where_fillna_pattern(self):
        """
        GIVEN strategy code with risky .where().fillna() chain
        WHEN validating the code
        THEN should warn about potential issues
        """
        # Arrange
        risky_code = '''
position = cond_combined.where(cond_combined).fillna(False)
'''

        # Act
        from src.innovation.strategy_validator import StrategyCodeValidator
        validator = StrategyCodeValidator()
        issues = validator.validate(risky_code)

        # Assert - should detect this pattern
        assert any('where' in issue.lower() or 'fillna' in issue.lower() for issue in issues)


class TestPromptAntiPatternGuidance:
    """Tests for anti-pattern guidance in prompts."""

    def test_prompt_warns_against_where_comparison(self):
        """
        GIVEN prompt builder
        WHEN building creation prompt
        THEN should include warning about .where(df == df.max()) anti-pattern
        """
        # Act
        from src.innovation.prompt_builder import PromptBuilder
        builder = PromptBuilder()
        prompt = builder.build_creation_prompt(
            champion_approach="test momentum strategy"
        )

        # Assert
        assert 'where' in prompt.lower() or 'comparison' in prompt.lower()
        # Should warn against comparing DataFrames
        assert any(term in prompt.lower() for term in ['anti-pattern', 'forbidden', 'avoid', "don't use"])

    def test_prompt_shows_correct_selection_pattern(self):
        """
        GIVEN prompt builder
        WHEN building creation prompt
        THEN should show correct pattern for top-N selection
        """
        # Act
        from src.innovation.prompt_builder import PromptBuilder
        builder = PromptBuilder()
        prompt = builder.build_creation_prompt(
            champion_approach="test momentum strategy"
        )

        # Assert - should show is_largest() as correct pattern
        assert 'is_largest' in prompt


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
