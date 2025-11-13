"""Runtime Validation Tests - TDD RED Phase.

This test module validates the validate_protocol_compliance() function
for runtime Protocol validation with diagnostic messages.

**TDD Phase: RED (Write Failing Tests First)**

Test Objectives:
    1. Verify validate_protocol_compliance() exists and works
    2. Test successful validation (object implements Protocol)
    3. Test failed validation (object missing required methods)
    4. Test diagnostic messages include missing attributes

Expected Behavior (RED Phase):
    - Tests should FAIL with ImportError (function doesn't exist yet)
    - This is DESIRED - we're writing tests before implementation

Design Reference:
    See .spec-workflow/specs/api-mismatch-prevention-system/DESIGN_IMPROVEMENTS.md
    Section 1.3: Runtime Validation Function
"""

import pytest
from typing import Protocol, runtime_checkable


def test_validate_protocol_compliance_function_exists() -> None:
    """Test that validate_protocol_compliance function exists.

    **TDD Phase: RED**
    Expected to FAIL with ImportError - function doesn't exist yet.

    Next Step (GREEN Phase):
    - Create src/learning/validation.py
    - Implement validate_protocol_compliance(obj, protocol, context)
    """
    # This import will FAIL - function doesn't exist yet (RED phase)
    from src.learning.validation import validate_protocol_compliance

    # Function should exist
    assert callable(validate_protocol_compliance)


def test_validate_protocol_compliance_passes_for_valid_object() -> None:
    """Test validation passes when object implements Protocol.

    **TDD Phase: RED**
    Expected to FAIL with ImportError initially.

    Once function exists, this test validates successful validation
    when object correctly implements the Protocol interface.
    """
    from src.learning.validation import validate_protocol_compliance
    from src.learning.interfaces import IChampionTracker
    from src.learning.champion_tracker import ChampionTracker
    from src.repository.hall_of_fame import HallOfFameRepository
    from src.learning.iteration_history import IterationHistory
    from src.config.anti_churn_manager import AntiChurnManager

    # Create valid object
    hall_of_fame = HallOfFameRepository()
    history = IterationHistory(filepath="artifacts/data/test_innovations.jsonl")
    anti_churn = AntiChurnManager()
    tracker = ChampionTracker(hall_of_fame=hall_of_fame, history=history, anti_churn=anti_churn)

    # Validation should pass (no exception raised)
    validate_protocol_compliance(tracker, IChampionTracker, context="test")


def test_validate_protocol_compliance_fails_for_invalid_object() -> None:
    """Test validation fails when object missing required methods.

    **TDD Phase: RED**
    Expected to FAIL with ImportError initially.

    Once function exists, this test validates that validation raises
    TypeError when object doesn't implement Protocol.
    """
    from src.learning.validation import validate_protocol_compliance
    from src.learning.interfaces import IChampionTracker

    # Create invalid object (missing required methods)
    class FakeTracker:
        """Fake tracker missing update_champion method."""
        def __init__(self) -> None:
            self.champion = None

    fake_tracker = FakeTracker()

    # Validation should fail with TypeError
    with pytest.raises(TypeError) as exc_info:
        validate_protocol_compliance(fake_tracker, IChampionTracker, context="test")

    # Error message should mention missing attributes
    error_msg = str(exc_info.value)
    assert "update_champion" in error_msg, \
        "Error message should mention missing 'update_champion' method"


def test_validate_protocol_compliance_diagnostic_message() -> None:
    """Test that validation error includes diagnostic details.

    **TDD Phase: RED**
    Expected to FAIL with ImportError initially.

    Once function exists, this test validates that error messages
    include helpful diagnostic information about missing attributes.
    """
    from src.learning.validation import validate_protocol_compliance
    from src.learning.interfaces import IIterationHistory

    # Create object missing multiple methods
    class FakeHistory:
        """Fake history missing save and get_all methods."""
        def load_recent(self, N: int = 5) -> list:
            return []

    fake_history = FakeHistory()

    # Validation should fail with detailed error message
    with pytest.raises(TypeError) as exc_info:
        validate_protocol_compliance(fake_history, IIterationHistory, context="FakeHistory")

    error_msg = str(exc_info.value)

    # Error message should include context
    assert "FakeHistory" in error_msg, \
        "Error message should include context identifier"

    # Error message should mention missing methods
    assert "save" in error_msg, \
        "Error message should mention missing 'save' method"
    assert "get_all" in error_msg, \
        "Error message should mention missing 'get_all' method"


def test_validate_protocol_compliance_with_none_object() -> None:
    """Test validation handles None gracefully.

    **TDD Phase: RED**
    Expected to FAIL with ImportError initially.

    Once function exists, this test validates that passing None
    raises appropriate TypeError.
    """
    from src.learning.validation import validate_protocol_compliance
    from src.learning.interfaces import IChampionTracker

    # Validation should fail for None
    with pytest.raises(TypeError) as exc_info:
        validate_protocol_compliance(None, IChampionTracker, context="test")

    error_msg = str(exc_info.value)
    assert "None" in error_msg or "NoneType" in error_msg
