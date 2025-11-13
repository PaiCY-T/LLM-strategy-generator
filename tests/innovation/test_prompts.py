"""
Comprehensive Test Suite for Prompt Templates

Tests prompt generation, category-specific prompts, formatting utilities,
and code/rationale extraction.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from innovation.prompt_templates import (
    create_innovation_prompt,
    create_structured_innovation_prompt,
    format_top_factors,
    format_existing_factors,
    extract_code_and_rationale,
    INNOVATION_PROMPT_TEMPLATE,
    CATEGORY_PROMPTS
)


class TestPromptGeneration:
    """Test main prompt generation"""

    def test_basic_prompt_generation(self):
        """Test generating basic innovation prompt"""
        baseline_metrics = {
            'mean_sharpe': 0.680,
            'mean_calmar': 2.406,
            'mean_mdd': 0.20
        }

        prompt = create_innovation_prompt(
            baseline_metrics=baseline_metrics,
            existing_factors=[],
            top_factors=[]
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert 'Sharpe 0.680' in prompt
        assert 'Calmar 2.406' in prompt

    def test_prompt_with_top_factors(self):
        """Test prompt includes top factors context"""
        baseline_metrics = {'mean_sharpe': 0.680, 'mean_calmar': 2.406, 'mean_mdd': 0.20}

        top_factors = [
            {'code': "data.get('roe')", 'sharpe_ratio': 0.85},
            {'code': "data.get('pe_ratio')", 'sharpe_ratio': 0.78}
        ]

        prompt = create_innovation_prompt(
            baseline_metrics=baseline_metrics,
            existing_factors=[],
            top_factors=top_factors
        )

        assert 'Sharpe 0.850' in prompt
        assert 'data.get' in prompt

    def test_prompt_with_existing_factors(self):
        """Test prompt includes existing factors for novelty enforcement"""
        baseline_metrics = {'mean_sharpe': 0.680, 'mean_calmar': 2.406, 'mean_mdd': 0.20}

        existing_factors = [
            "data.get('fundamental_features:ROE稅後')",
            "data.get('price:收盤價').rolling(20).mean()"
        ]

        prompt = create_innovation_prompt(
            baseline_metrics=baseline_metrics,
            existing_factors=existing_factors,
            top_factors=[]
        )

        assert 'ROE稅後' in prompt
        assert 'rolling' in prompt

    def test_adaptive_thresholds(self):
        """Test prompt includes adaptive thresholds (1.2x baseline)"""
        baseline_metrics = {
            'mean_sharpe': 0.680,
            'mean_calmar': 2.406,
            'mean_mdd': 0.20
        }

        prompt = create_innovation_prompt(
            baseline_metrics=baseline_metrics,
            existing_factors=[],
            top_factors=[]
        )

        # Check for 1.2x threshold
        target_sharpe = 0.680 * 1.2  # 0.816
        assert '0.816' in prompt


class TestCategoryPrompts:
    """Test category-specific prompt generation"""

    def test_value_category_prompt(self):
        """Test value category prompt"""
        baseline_metrics = {'mean_sharpe': 0.680, 'mean_calmar': 2.406, 'mean_mdd': 0.20}

        prompt = create_innovation_prompt(
            baseline_metrics=baseline_metrics,
            existing_factors=[],
            top_factors=[],
            category='value'
        )

        assert 'Value Investing' in prompt
        assert 'P/E' in prompt or 'P/B' in prompt

    def test_quality_category_prompt(self):
        """Test quality category prompt"""
        baseline_metrics = {'mean_sharpe': 0.680, 'mean_calmar': 2.406, 'mean_mdd': 0.20}

        prompt = create_innovation_prompt(
            baseline_metrics=baseline_metrics,
            existing_factors=[],
            top_factors=[],
            category='quality'
        )

        assert 'Quality Investing' in prompt
        assert 'ROE' in prompt or 'ROA' in prompt

    def test_growth_category_prompt(self):
        """Test growth category prompt"""
        baseline_metrics = {'mean_sharpe': 0.680, 'mean_calmar': 2.406, 'mean_mdd': 0.20}

        prompt = create_innovation_prompt(
            baseline_metrics=baseline_metrics,
            existing_factors=[],
            top_factors=[],
            category='growth'
        )

        assert 'Growth Investing' in prompt
        assert 'growth' in prompt.lower()

    def test_momentum_category_prompt(self):
        """Test momentum category prompt"""
        baseline_metrics = {'mean_sharpe': 0.680, 'mean_calmar': 2.406, 'mean_mdd': 0.20}

        prompt = create_innovation_prompt(
            baseline_metrics=baseline_metrics,
            existing_factors=[],
            top_factors=[],
            category='momentum'
        )

        assert 'Momentum Investing' in prompt
        assert 'momentum' in prompt.lower()

    def test_mixed_category_prompt(self):
        """Test mixed category prompt"""
        baseline_metrics = {'mean_sharpe': 0.680, 'mean_calmar': 2.406, 'mean_mdd': 0.20}

        prompt = create_innovation_prompt(
            baseline_metrics=baseline_metrics,
            existing_factors=[],
            top_factors=[],
            category='mixed'
        )

        assert 'Multi-Factor' in prompt

    def test_all_categories_exist(self):
        """Test all category templates exist"""
        expected_categories = ['value', 'quality', 'growth', 'momentum', 'mixed']

        for category in expected_categories:
            assert category in CATEGORY_PROMPTS
            assert len(CATEGORY_PROMPTS[category]) > 50


class TestFormattingUtilities:
    """Test prompt formatting utility functions"""

    def test_format_top_factors_empty(self):
        """Test formatting empty top factors list"""
        result = format_top_factors([])
        assert 'No top factors yet' in result

    def test_format_top_factors_with_data(self):
        """Test formatting top factors with data"""
        top_factors = [
            {'code': 'factor_1', 'sharpe_ratio': 0.85},
            {'code': 'factor_2', 'sharpe_ratio': 0.72}
        ]

        result = format_top_factors(top_factors)

        assert '0.850' in result or '0.85' in result
        assert 'factor_1' in result

    def test_format_top_factors_max_limit(self):
        """Test formatting respects max_factors limit"""
        top_factors = [{'code': f'factor_{i}', 'sharpe_ratio': 0.8} for i in range(10)]

        result = format_top_factors(top_factors, max_factors=3)

        # Should only show top 3
        lines = result.split('\n')
        assert len(lines) <= 4  # 3 factors + possible header

    def test_format_existing_factors_empty(self):
        """Test formatting empty existing factors"""
        result = format_existing_factors([])
        assert 'No existing factors' in result

    def test_format_existing_factors_with_data(self):
        """Test formatting existing factors with data"""
        existing = [
            "data.get('roe')",
            "data.get('pe_ratio')"
        ]

        result = format_existing_factors(existing)

        assert 'roe' in result
        assert 'pe_ratio' in result

    def test_format_existing_factors_truncation(self):
        """Test long factor code is truncated"""
        long_code = "data.get('field') " * 20  # Very long code
        existing = [long_code]

        result = format_existing_factors(existing)

        # Should be truncated with ...
        assert '...' in result
        assert len(result) < len(long_code)


class TestCodeExtraction:
    """Test code and rationale extraction"""

    def test_basic_extraction(self):
        """Test basic code and rationale extraction"""
        response = """
```python
# Factor Code
factor = data.get('fundamental_features:ROE稅後') / data.get('fundamental_features:淨值比')

# Rationale
# Quality-adjusted value factor that identifies high ROE companies at reasonable valuations
```
"""

        code, rationale = extract_code_and_rationale(response)

        assert code is not None
        assert 'factor =' in code
        assert rationale is not None
        assert len(rationale) >= 20

    def test_extraction_with_multiline_rationale(self):
        """Test extracting code and rationale from multiline response"""
        response = """
```python
# Factor Code
factor = data.get('roe') * data.get('revenue_growth')

# Rationale
# This is a longer rationale
# that spans multiple lines
# and provides detailed explanation
```
"""

        code, rationale = extract_code_and_rationale(response)

        assert code is not None
        assert rationale is not None
        # Should get first valid rationale line
        assert len(rationale) >= 20

    def test_extraction_missing_rationale(self):
        """Test extraction when rationale is too short"""
        response = """
factor = data.get('roe')

# Short
"""

        code, rationale = extract_code_and_rationale(response)

        assert code is not None
        assert rationale is None  # Too short (<20 chars)

    def test_extraction_no_code(self):
        """Test extraction when no code is present"""
        response = """
# Just a comment with no factor code
"""

        code, rationale = extract_code_and_rationale(response)

        assert code is None
        assert rationale is None


class TestStructuredPrompt:
    """Test structured (YAML) prompt generation"""

    def test_structured_prompt_generation(self):
        """Test generating structured YAML prompt"""
        baseline_metrics = {
            'mean_sharpe': 0.680,
            'mean_calmar': 2.406,
            'mean_mdd': 0.20
        }

        available_fields = ['roe', 'pe_ratio', 'revenue_growth']

        prompt = create_structured_innovation_prompt(
            baseline_metrics=baseline_metrics,
            available_fields=available_fields
        )

        assert 'YAML' in prompt
        assert 'roe' in prompt
        assert 'pe_ratio' in prompt

    def test_structured_prompt_with_category(self):
        """Test structured prompt with category"""
        baseline_metrics = {'mean_sharpe': 0.680, 'mean_calmar': 2.406, 'mean_mdd': 0.20}
        available_fields = ['roe', 'pe_ratio']

        prompt = create_structured_innovation_prompt(
            baseline_metrics=baseline_metrics,
            available_fields=available_fields,
            category='quality'
        )

        assert 'quality' in prompt

    def test_structured_prompt_target_sharpe(self):
        """Test structured prompt includes target Sharpe"""
        baseline_metrics = {'mean_sharpe': 0.680, 'mean_calmar': 2.406, 'mean_mdd': 0.20}
        available_fields = []

        prompt = create_structured_innovation_prompt(
            baseline_metrics=baseline_metrics,
            available_fields=available_fields
        )

        # Should have 1.2x baseline = 0.816
        assert '0.816' in prompt


class TestPromptQuality:
    """Test prompt quality and completeness"""

    def test_prompt_includes_constraints(self):
        """Test prompt includes critical constraints"""
        baseline_metrics = {'mean_sharpe': 0.680, 'mean_calmar': 2.406, 'mean_mdd': 0.20}

        prompt = create_innovation_prompt(
            baseline_metrics=baseline_metrics,
            existing_factors=[],
            top_factors=[]
        )

        # Check for key constraints
        assert 'finlab' in prompt.lower()
        assert 'look-ahead' in prompt.lower() or 'bias' in prompt.lower()
        assert 'vectorized' in prompt.lower()

    def test_prompt_includes_novelty_requirement(self):
        """Test prompt enforces novelty"""
        baseline_metrics = {'mean_sharpe': 0.680, 'mean_calmar': 2.406, 'mean_mdd': 0.20}

        prompt = create_innovation_prompt(
            baseline_metrics=baseline_metrics,
            existing_factors=["factor1"],
            top_factors=[]
        )

        assert 'Novelty' in prompt or 'novel' in prompt.lower()
        assert 'existing' in prompt.lower()

    def test_prompt_includes_explainability_requirement(self):
        """Test prompt requires explainability"""
        baseline_metrics = {'mean_sharpe': 0.680, 'mean_calmar': 2.406, 'mean_mdd': 0.20}

        prompt = create_innovation_prompt(
            baseline_metrics=baseline_metrics,
            existing_factors=[],
            top_factors=[]
        )

        assert 'Explainability' in prompt or 'rationale' in prompt.lower()
        assert 'tautolog' in prompt.lower()

    def test_prompt_includes_example(self):
        """Test prompt includes example"""
        baseline_metrics = {'mean_sharpe': 0.680, 'mean_calmar': 2.406, 'mean_mdd': 0.20}

        prompt = create_innovation_prompt(
            baseline_metrics=baseline_metrics,
            existing_factors=[],
            top_factors=[]
        )

        assert 'Example' in prompt
        assert 'DO NOT COPY' in prompt


# Test execution
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
