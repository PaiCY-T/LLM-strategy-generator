"""
Test suite for PromptBuilder - Task 1.2 TDD Cycle

Tests API documentation section enhancement to include:
- ALL 160 fields from field catalog
- Python list format (not markdown)
- data.get() usage examples
- Field name hallucination warning

RED phase: Write failing tests first before implementation.
"""

import json
import pytest
from pathlib import Path
from src.innovation.prompt_builder import PromptBuilder


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def field_catalog():
    """Load field catalog fixture (160 fields from Task 1.1)."""
    catalog_path = Path(__file__).parent / "fixtures" / "finlab_fields.json"
    with open(catalog_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def prompt_builder():
    """Create PromptBuilder instance."""
    return PromptBuilder()


@pytest.fixture
def sample_champion_metrics():
    """Sample champion metrics for testing."""
    return {
        'sharpe_ratio': 0.85,
        'max_drawdown': 0.15,
        'win_rate': 0.58,
        'calmar_ratio': 2.3
    }


@pytest.fixture
def sample_champion_code():
    """Sample champion code for testing."""
    return """
def strategy(data):
    roe = data.get('fundamental_features:ROE')
    return roe > 15
"""


# ============================================================================
# Task 1.2 Tests - API Documentation Section Enhancement
# ============================================================================

class TestAPIDocumentationSection:
    """Tests for Task 1.2: API documentation section with ALL fields."""

    def test_prompt_contains_all_fields(
        self,
        prompt_builder,
        sample_champion_code,
        sample_champion_metrics,
        field_catalog
    ):
        """
        Test that prompt includes ALL 160 fields from catalog.

        Requirements:
        - REQ-1: Complete field catalog in prompts
        - Critical Fix #1: Show all available fields

        Verifies:
        - All 7 price fields present
        - All 52 fundamental_features fields present
        - All 101 financial_statement fields present
        - Total 160 fields documented
        """
        # Generate prompt
        prompt = prompt_builder.build_modification_prompt(
            champion_code=sample_champion_code,
            champion_metrics=sample_champion_metrics
        )

        # Count fields by category
        price_count = 0
        fundamental_count = 0
        financial_count = 0

        for field_name in field_catalog.keys():
            if field_name in prompt:
                if field_name.startswith('price:'):
                    price_count += 1
                elif field_name.startswith('fundamental_features:'):
                    fundamental_count += 1
                elif field_name.startswith('financial_statement:'):
                    financial_count += 1

        # Assert all fields are present
        assert price_count == 7, f"Expected 7 price fields, found {price_count}"
        assert fundamental_count == 52, f"Expected 52 fundamental_features fields, found {fundamental_count}"
        assert financial_count == 101, f"Expected 101 financial_statement fields, found {financial_count}"

        # Total count
        total_fields = price_count + fundamental_count + financial_count
        assert total_fields == 160, f"Expected 160 total fields, found {total_fields}"

    def test_api_documentation_uses_python_list_format(
        self,
        prompt_builder,
        sample_champion_code,
        sample_champion_metrics
    ):
        """
        Test that API documentation uses Python list format, NOT markdown.

        Requirements:
        - Task 1.2: Use Python list format

        Verifies:
        - Fields shown as Python list: ['field1', 'field2', ...]
        - NOT markdown bullets: - field1, - field2
        - Proper Python syntax with quotes and commas
        """
        prompt = prompt_builder.build_modification_prompt(
            champion_code=sample_champion_code,
            champion_metrics=sample_champion_metrics
        )

        # Check for Python list indicators
        assert "VALID_FIELDS = [" in prompt or "AVAILABLE_FIELDS = [" in prompt, \
            "Python list assignment not found"

        # Check for proper Python list syntax (quotes around field names)
        assert "'price:收盤價'" in prompt or '"price:收盤價"' in prompt, \
            "Field names not quoted in Python list format"

        # Verify NOT using markdown bullet format for field list
        # Allow bullets in other sections, but field list should be Python format
        field_section = self._extract_field_section(prompt)
        markdown_bullets_in_fields = field_section.count('\n- price:') + \
                                     field_section.count('\n- fundamental_features:') + \
                                     field_section.count('\n- financial_statement:')

        assert markdown_bullets_in_fields == 0, \
            f"Found {markdown_bullets_in_fields} markdown bullets in field list (should use Python list)"

    def test_api_documentation_includes_usage_examples(
        self,
        prompt_builder,
        sample_champion_code,
        sample_champion_metrics
    ):
        """
        Test that API documentation includes data.get() usage examples.

        Requirements:
        - Task 1.2: Add usage examples with data.get()

        Verifies:
        - At least 3 usage examples present
        - Examples use data.get() syntax
        - Examples demonstrate shift() for look-ahead bias prevention
        - Examples show different field categories
        """
        prompt = prompt_builder.build_modification_prompt(
            champion_code=sample_champion_code,
            champion_metrics=sample_champion_metrics
        )

        # Check for data.get() examples
        data_get_count = prompt.count("data.get(")
        assert data_get_count >= 3, \
            f"Expected at least 3 data.get() examples, found {data_get_count}"

        # Check for shift() usage example (avoid look-ahead bias)
        assert ".shift(1)" in prompt or ".shift(2)" in prompt, \
            "No shift() example found for look-ahead bias prevention"

        # Check for examples from different categories
        has_price_example = "data.get('price:" in prompt
        has_fundamental_example = "data.get('fundamental_features:" in prompt
        has_financial_example = "data.get('financial_statement:" in prompt

        assert has_price_example, "No price field example found"
        assert has_fundamental_example, "No fundamental_features field example found"
        # Financial statement example is optional (may not be in every prompt)

    def test_api_documentation_includes_hallucination_warning(
        self,
        prompt_builder,
        sample_champion_code,
        sample_champion_metrics
    ):
        """
        Test that API documentation includes field name hallucination warning.

        Requirements:
        - Task 1.2: Add warnings about field name hallucination
        - Critical Fix #2: Prevent inventing field names

        Verifies:
        - Warning text about NOT inventing field names
        - Instruction to use ONLY listed fields
        - Consequence of using invalid fields
        """
        prompt = prompt_builder.build_modification_prompt(
            champion_code=sample_champion_code,
            champion_metrics=sample_champion_metrics
        )

        # Check for hallucination warning keywords
        warning_indicators = [
            "do not invent" in prompt.lower(),
            "only use" in prompt.lower() or "use only" in prompt.lower(),
            "invalid field" in prompt.lower() or "non-existent field" in prompt.lower(),
            "hallucination" in prompt.lower() or "hallucinate" in prompt.lower(),
        ]

        # At least 2 warning indicators should be present
        warning_count = sum(warning_indicators)
        assert warning_count >= 2, \
            f"Expected at least 2 hallucination warning indicators, found {warning_count}"

        # Specific warning about field validity
        assert any(phrase in prompt.lower() for phrase in [
            "use only these field names",
            "only use field names from the list",
            "do not create field names",
            "must use exact field names",
        ]), "No specific field validity warning found"

    # Helper method
    def _extract_field_section(self, prompt: str) -> str:
        """Extract the field documentation section from prompt."""
        # Look for section containing field list
        if "VALID_FIELDS" in prompt:
            start = prompt.find("VALID_FIELDS")
            end = prompt.find("\n\n", start + 200)  # Find next section break
            return prompt[start:end] if end != -1 else prompt[start:]
        elif "AVAILABLE_FIELDS" in prompt:
            start = prompt.find("AVAILABLE_FIELDS")
            end = prompt.find("\n\n", start + 200)
            return prompt[start:end] if end != -1 else prompt[start:]
        else:
            # Fallback: return section with data.get examples
            return prompt


# ============================================================================
# Test Creation Prompt (same requirements)
# ============================================================================

class TestAPIDocumentationInCreationPrompt:
    """Verify API documentation also works in creation prompts."""

    def test_creation_prompt_contains_all_fields(
        self,
        prompt_builder,
        field_catalog
    ):
        """Test that creation prompt also includes ALL 160 fields."""
        prompt = prompt_builder.build_creation_prompt(
            champion_approach="Momentum-based with ROE filter",
            innovation_directive="Explore value + quality combinations"
        )

        # Count fields
        total_found = sum(1 for field in field_catalog.keys() if field in prompt)

        assert total_found == 160, \
            f"Expected 160 fields in creation prompt, found {total_found}"

    def test_creation_prompt_has_hallucination_warning(
        self,
        prompt_builder
    ):
        """Test that creation prompt includes hallucination warning."""
        prompt = prompt_builder.build_creation_prompt(
            champion_approach="Momentum-based with ROE filter"
        )

        # Check for warning
        assert any(phrase in prompt.lower() for phrase in [
            "do not invent",
            "only use",
            "use only",
            "exact field names"
        ]), "No hallucination warning in creation prompt"


# ============================================================================
# Integration Tests
# ============================================================================

class TestPromptBuilderIntegration:
    """Integration tests for complete prompt generation."""

    def test_modification_prompt_is_valid(
        self,
        prompt_builder,
        sample_champion_code,
        sample_champion_metrics
    ):
        """Test that modification prompt is well-formed and complete."""
        prompt = prompt_builder.build_modification_prompt(
            champion_code=sample_champion_code,
            champion_metrics=sample_champion_metrics
        )

        # Basic structure checks
        assert len(prompt) > 1000, "Prompt too short"
        assert "def strategy(data):" in prompt, "Missing strategy function signature"
        assert "return" in prompt, "Missing return statement example"

    def test_creation_prompt_is_valid(
        self,
        prompt_builder
    ):
        """Test that creation prompt is well-formed and complete."""
        prompt = prompt_builder.build_creation_prompt(
            champion_approach="Test approach"
        )

        # Basic structure checks
        assert len(prompt) > 1000, "Prompt too short"
        assert "def strategy(data):" in prompt, "Missing strategy function signature"
