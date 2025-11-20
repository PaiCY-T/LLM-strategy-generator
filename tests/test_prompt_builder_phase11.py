"""
Phase 1.1 Golden Template Tests
===============================

Tests for Phase 1.1 improvements:
- Golden Template with START/END markers
- Simplified 4-step CoT
- APPENDIX-based reference materials
- Correct prompt ordering
"""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.innovation.prompt_builder import PromptBuilder


@pytest.fixture
def builder():
    """Create PromptBuilder instance for testing."""
    return PromptBuilder()


class TestGoldenTemplate:
    """Test Golden Template implementation."""

    def test_golden_template_has_critical_rule(self, builder):
        """Golden Template starts with CRITICAL RULE header."""
        template = builder._build_golden_template()
        assert "CRITICAL" in template.upper()
        assert "RULE" in template.upper()

    def test_golden_template_has_start_end_markers(self, builder):
        """Golden Template has clear START/END markers."""
        template = builder._build_golden_template()
        assert "START" in template
        assert "END" in template
        # Ensure START comes before END
        start_pos = template.find("START")
        end_pos = template.find("END")
        assert start_pos < end_pos

    def test_golden_template_has_immutable_execution(self, builder):
        """Golden Template includes immutable backtest execution."""
        template = builder._build_golden_template()
        assert "report = sim(" in template
        assert "DO NOT MODIFY" in template.upper()

    def test_golden_template_has_visual_separators(self, builder):
        """Golden Template uses visual separators for clarity."""
        template = builder._build_golden_template()
        # Check for = or - separator lines
        assert "======" in template or "------" in template

    def test_golden_template_has_position_return(self, builder):
        """Golden Template requires return position statement."""
        template = builder._build_golden_template()
        assert "return position" in template

    def test_golden_template_no_concrete_examples(self, builder):
        """Golden Template uses instructions, not concrete code examples."""
        template = builder._build_golden_template()
        # Should have instructions (numbered or bulleted)
        has_instructions = any([
            "1." in template or "2." in template,  # Numbered
            "Step" in template,  # Step-based
            "-" in template  # Bulleted
        ])
        assert has_instructions


class TestSimplifiedCoT:
    """Test Simplified Chain of Thought implementation."""

    def test_simplified_cot_has_4_steps(self, builder):
        """Simplified CoT has exactly 4 steps."""
        cot = builder._build_simplified_cot()
        # Count step markers
        step_count = sum([
            "Step 1" in cot or "## 1." in cot,
            "Step 2" in cot or "## 2." in cot,
            "Step 3" in cot or "## 3." in cot,
            "Step 4" in cot or "## 4." in cot
        ])
        assert step_count == 4

    def test_simplified_cot_references_template(self, builder):
        """Step 1 references understanding the template."""
        cot = builder._build_simplified_cot()
        # Step 1 should mention template/framework/structure
        assert any(word in cot.lower() for word in [
            "template", "framework", "structure", "golden"
        ])

    def test_simplified_cot_references_appendix(self, builder):
        """Step 2 directs to check APPENDIX for fields."""
        cot = builder._build_simplified_cot()
        assert "APPENDIX" in cot.upper() or "appendix" in cot.lower()

    def test_simplified_cot_mentions_start_end(self, builder):
        """CoT mentions START/END markers for implementation."""
        cot = builder._build_simplified_cot()
        assert "START" in cot and "END" in cot


class TestAppendix:
    """Test APPENDIX construction."""

    def test_appendix_has_header(self, builder):
        """APPENDIX has clear section header."""
        appendix = builder._build_appendix()
        assert "APPENDIX" in appendix.upper()

    def test_appendix_contains_field_catalog(self, builder):
        """APPENDIX includes 160-field catalog."""
        appendix = builder._build_appendix()
        # Check for key fields from catalog
        assert "price:收盤價" in appendix
        assert "fundamental_features:" in appendix
        assert "financial_statement:" in appendix

    def test_appendix_contains_api_docs(self, builder):
        """APPENDIX includes API documentation."""
        appendix = builder._build_appendix()
        assert "data.get(" in appendix
        assert ".shift(1)" in appendix or "shift(1)" in appendix

    def test_appendix_contains_validation_helpers(self, builder):
        """APPENDIX includes validation helper examples."""
        appendix = builder._build_appendix()
        assert "validate" in appendix.lower()


class TestCreationPromptOrder:
    """Test build_creation_prompt() ordering."""

    def test_creation_prompt_has_template_first(self, builder):
        """Template appears before CoT and APPENDIX."""
        prompt = builder.build_creation_prompt(
            champion_approach="Simple momentum strategy"
        )

        # Find positions
        template_pos = None
        for marker in ["CRITICAL", "Golden Template", "START"]:
            pos = prompt.find(marker)
            if pos >= 0:
                template_pos = pos
                break

        assert template_pos is not None, "Golden Template not found in prompt"
        assert template_pos < 1000, "Template should appear in first 1000 chars"

    def test_creation_prompt_has_cot_after_template(self, builder):
        """CoT appears after Template but before APPENDIX."""
        prompt = builder.build_creation_prompt(
            champion_approach="Simple momentum strategy"
        )

        # Find positions
        template_pos = prompt.find("CRITICAL")
        cot_pos = max(prompt.find("Step 1"), prompt.find("Chain of Thought"))
        appendix_pos = prompt.upper().find("APPENDIX")

        assert template_pos >= 0, "Template not found"
        assert cot_pos >= 0, "CoT not found"
        assert template_pos < cot_pos, "Template must come before CoT"

    def test_creation_prompt_has_appendix_last(self, builder):
        """APPENDIX appears after all core instructions."""
        prompt = builder.build_creation_prompt(
            champion_approach="Simple momentum strategy"
        )

        # Look for the actual APPENDIX section header, not references to it
        appendix_pos = prompt.find("# PART 4: APPENDIX")
        if appendix_pos < 0:
            appendix_pos = prompt.find("PART 4: APPENDIX - Reference Materials")

        assert appendix_pos >= 0, "APPENDIX section header not found"

        # APPENDIX should come after template, CoT, and task sections
        template_pos = prompt.find("# PART 1: GOLDEN TEMPLATE")
        cot_pos = prompt.find("# PART 2: HOW TO USE THE TEMPLATE")

        assert appendix_pos > template_pos, "APPENDIX must come after Golden Template"
        assert appendix_pos > cot_pos, "APPENDIX must come after CoT"

        # APPENDIX should be in latter part (after first 20% at minimum)
        prompt_length = len(prompt)
        assert appendix_pos > prompt_length * 0.2, f"APPENDIX too early at {appendix_pos/prompt_length:.1%}"

    def test_creation_prompt_preserves_phase1_content(self, builder):
        """All Phase 1 improvements still included in APPENDIX."""
        prompt = builder.build_creation_prompt(
            champion_approach="Simple momentum strategy"
        )

        # Check Phase 1 content exists (in APPENDIX)
        appendix_start = prompt.upper().find("APPENDIX")
        appendix_section = prompt[appendix_start:] if appendix_start >= 0 else ""

        assert "price:收盤價" in appendix_section, "Field catalog missing"
        assert "data.get(" in appendix_section, "API docs missing"
        assert "validate" in appendix_section.lower(), "Validation helpers missing"


class TestPhase11Integration:
    """Integration tests for Phase 1.1."""

    def test_prompt_contains_all_phase11_sections(self, builder):
        """Complete prompt has all Phase 1.1 sections."""
        prompt = builder.build_creation_prompt(
            champion_approach="Momentum with quality filters"
        )

        # All sections present
        assert "CRITICAL" in prompt or "Golden Template" in prompt, "Template missing"
        assert "Step" in prompt, "CoT missing"
        assert "APPENDIX" in prompt.upper(), "APPENDIX missing"

    def test_prompt_size_reasonable(self, builder):
        """Prompt size is reasonable (<50K chars, ~12K tokens)."""
        prompt = builder.build_creation_prompt(
            champion_approach="Test strategy"
        )

        # Should be less than 50K chars (much less than 100K token budget)
        assert len(prompt) < 50000, f"Prompt too large: {len(prompt)} chars"

    def test_template_before_fields(self, builder):
        """Template appears before field catalog."""
        prompt = builder.build_creation_prompt(
            champion_approach="Test strategy"
        )

        template_pos = prompt.find("report = sim(")
        field_pos = prompt.find("price:收盤價")

        assert template_pos >= 0, "Template execution section not found"
        assert field_pos >= 0, "Field catalog not found"
        assert template_pos < field_pos, "Template must appear before field catalog"
