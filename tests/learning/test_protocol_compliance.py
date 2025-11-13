"""Protocol Compliance Tests - TDD RED Phase.

This test module validates that core learning components implement their
respective Protocol interfaces, enabling runtime type checking and API
contract enforcement.

**TDD Phase: RED (Write Failing Tests First)**

Test Objectives:
    1. Verify ChampionTracker implements IChampionTracker Protocol
    2. Verify IterationHistory implements IIterationHistory Protocol
    3. Verify ErrorClassifier implements IErrorClassifier Protocol

Expected Behavior (RED Phase):
    - All tests should FAIL with ImportError (Protocols don't exist yet)
    - This is DESIRED - we're writing tests before implementation
    - Next phase (GREEN) will create minimal Protocol definitions

Design Reference:
    See .spec-workflow/specs/api-mismatch-prevention-system/DESIGN_IMPROVEMENTS.md
    Section 1: Runtime Validation with @runtime_checkable Protocols
"""

import pytest
from typing import Protocol, runtime_checkable


def test_champion_tracker_implements_protocol() -> None:
    """Test that ChampionTracker implements IChampionTracker Protocol.

    **TDD Phase: RED**
    Expected to FAIL with ImportError - IChampionTracker doesn't exist yet.

    This test verifies:
    - ChampionTracker can be checked against IChampionTracker at runtime
    - isinstance() works correctly with @runtime_checkable Protocol
    - Champion tracker provides required interface methods

    Next Step (GREEN Phase):
    - Create src/learning/interfaces.py
    - Define IChampionTracker Protocol with:
      - .champion property (returns Optional[ChampionStrategy])
      - .update_champion() method
    """
    # This import will FAIL - Protocol doesn't exist yet (RED phase)
    from src.learning.interfaces import IChampionTracker
    from src.learning.champion_tracker import ChampionTracker
    from src.repository.hall_of_fame import HallOfFameRepository
    from src.learning.iteration_history import IterationHistory
    from src.config.anti_churn_manager import AntiChurnManager

    # Create real ChampionTracker instance
    hall_of_fame = HallOfFameRepository()
    history = IterationHistory(filepath="artifacts/data/test_innovations.jsonl")
    anti_churn = AntiChurnManager()

    champion_tracker = ChampionTracker(
        hall_of_fame=hall_of_fame,
        history=history,
        anti_churn=anti_churn
    )

    # Runtime Protocol check - should pass once Protocol is defined
    assert isinstance(champion_tracker, IChampionTracker), \
        "ChampionTracker must implement IChampionTracker Protocol"


def test_iteration_history_implements_protocol() -> None:
    """Test that IterationHistory implements IIterationHistory Protocol.

    **TDD Phase: RED**
    Expected to FAIL with ImportError - IIterationHistory doesn't exist yet.

    This test verifies:
    - IterationHistory can be checked against IIterationHistory at runtime
    - isinstance() works correctly with @runtime_checkable Protocol
    - Iteration history provides required interface methods

    Next Step (GREEN Phase):
    - Create src/learning/interfaces.py
    - Define IIterationHistory Protocol with:
      - .save() method
      - .get_all() method
      - .load_recent() method
    """
    # This import will FAIL - Protocol doesn't exist yet (RED phase)
    from src.learning.interfaces import IIterationHistory
    from src.learning.iteration_history import IterationHistory

    # Create real IterationHistory instance
    iteration_history = IterationHistory(filepath="artifacts/data/test_innovations.jsonl")

    # Runtime Protocol check - should pass once Protocol is defined
    assert isinstance(iteration_history, IIterationHistory), \
        "IterationHistory must implement IIterationHistory Protocol"


def test_error_classifier_implements_protocol() -> None:
    """Test that ErrorClassifier implements IErrorClassifier Protocol.

    **TDD Phase: RED**
    Expected to FAIL with ImportError - IErrorClassifier doesn't exist yet.

    This test verifies:
    - ErrorClassifier can be checked against IErrorClassifier at runtime
    - isinstance() works correctly with @runtime_checkable Protocol
    - Error classifier provides required interface methods

    Next Step (GREEN Phase):
    - Create src/learning/interfaces.py
    - Define IErrorClassifier Protocol with:
      - .classify_error() method
    """
    # This import will FAIL - Protocol doesn't exist yet (RED phase)
    from src.learning.interfaces import IErrorClassifier
    from src.backtest.error_classifier import ErrorClassifier

    # Create real ErrorClassifier instance
    error_classifier = ErrorClassifier()

    # Runtime Protocol check - should pass once Protocol is defined
    assert isinstance(error_classifier, IErrorClassifier), \
        "ErrorClassifier must implement IErrorClassifier Protocol"
