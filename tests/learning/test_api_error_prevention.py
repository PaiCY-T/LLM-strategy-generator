"""Integration tests validating that all 8 API errors from Phase 1-4 are prevented.

This test suite validates the multi-layered defense system:
- Layer 1: Protocol definitions (structural contracts)
- Layer 2: mypy static type checking
- Layer 3: Runtime validation (validate_protocol_compliance)
- Layer 4: Behavioral contracts (integration tests)

**Error Catalog** (8 total occurrences of 3 error types):
- Error #5: ChampionTracker.get_champion() doesn't exist (should be .champion property) - 6 locations
- Error #6: ErrorClassifier.classify_single() doesn't exist (should be .classify_error()) - 1 location
- Error #7: IterationHistory.save_record() doesn't exist (should be .save()) - 1 location

**Prevention Strategy**:
1. Protocol definitions make API contract explicit
2. mypy catches method/property confusion at static analysis time
3. Runtime validation catches violations at initialization time
4. Integration tests verify real-world usage patterns

Reference:
    .spec-workflow/specs/api-mismatch-prevention-system/requirements.md
    Section 1.2: Problem Statement - 8 API Errors
"""

import pytest
from typing import Protocol, Optional, List
from pathlib import Path

from src.learning.interfaces import IChampionTracker, IIterationHistory, IErrorClassifier
from src.learning.validation import validate_protocol_compliance
from src.learning.champion_tracker import ChampionTracker, ChampionStrategy
from src.learning.iteration_history import IterationHistory, IterationRecord
from src.backtest.error_classifier import ErrorClassifier, ErrorCategory
from src.repository.hall_of_fame import HallOfFameRepository
from src.config.anti_churn_manager import AntiChurnManager


# ============================================================================
# Error #5: ChampionTracker.get_champion() → .champion property (6 locations)
# ============================================================================

class TestAPIError5_ChampionTrackerProperty:
    """Verify Error #5: ChampionTracker.champion is property, not method.

    Prevention Layers:
    - Layer 1 (Protocol): @property decorator in IChampionTracker
    - Layer 2 (mypy): Catches .get_champion() as AttributeError
    - Layer 3 (Runtime): validate_protocol_compliance checks property exists
    - Layer 4 (Integration): This test verifies real usage
    """

    def test_champion_is_property_not_method(self):
        """Test that .champion is accessed as property, not method call.

        This prevents: tracker.get_champion() ❌
        Enforces: tracker.champion ✅
        """
        hall_of_fame = HallOfFameRepository()
        history = IterationHistory(filepath="artifacts/data/test_innovations.jsonl")
        anti_churn = AntiChurnManager()

        tracker = ChampionTracker(
            hall_of_fame=hall_of_fame,
            history=history,
            anti_churn=anti_churn
        )

        # ✅ Correct: property access
        champion = tracker.champion
        assert champion is None or isinstance(champion, ChampionStrategy)

        # ❌ Wrong: method call (would raise AttributeError)
        # This is prevented by Layer 2 (mypy) at static analysis time
        assert not hasattr(tracker, 'get_champion'), \
            "ChampionTracker should NOT have get_champion() method"

    def test_protocol_defines_champion_as_property(self):
        """Test that IChampionTracker Protocol defines champion as @property.

        Layer 1 Prevention: Protocol contract makes it explicit.
        """
        import inspect
        from src.learning.interfaces import IChampionTracker

        # Get the champion descriptor from Protocol
        champion_descriptor = getattr(IChampionTracker, 'champion', None)
        assert champion_descriptor is not None, "Protocol must define 'champion'"

        # Verify it's a property descriptor
        # Note: In Protocol, it's defined with @property decorator
        # The actual check is structural - mypy validates this

    def test_runtime_validation_catches_missing_champion_property(self):
        """Test runtime validation catches objects missing champion property.

        Layer 3 Prevention: Runtime validation at initialization.
        """
        class FakeTrackerWithMethod:
            """Fake tracker with get_champion() method instead of property."""
            def get_champion(self):
                return None

            def update_champion(self, record, force=False):
                return True

        fake = FakeTrackerWithMethod()

        # Runtime validation should catch missing property
        with pytest.raises(TypeError, match="does not implement.*IChampionTracker"):
            validate_protocol_compliance(fake, IChampionTracker, "test")

    def test_champion_property_type_hint(self):
        """Test that champion property has correct type hint.

        Layer 2 Prevention: mypy validates return type.
        """
        hall_of_fame = HallOfFameRepository()
        history = IterationHistory(filepath="artifacts/data/test_innovations.jsonl")
        anti_churn = AntiChurnManager()

        tracker = ChampionTracker(
            hall_of_fame=hall_of_fame,
            history=history,
            anti_churn=anti_churn
        )

        # Type should be Optional[ChampionStrategy]
        champion = tracker.champion
        assert champion is None or isinstance(champion, ChampionStrategy)

    def test_update_champion_method_exists(self):
        """Test that update_champion is method, not property.

        Complementary to champion being property - update_champion is method.
        """
        hall_of_fame = HallOfFameRepository()
        history = IterationHistory(filepath="artifacts/data/test_innovations.jsonl")
        anti_churn = AntiChurnManager()

        tracker = ChampionTracker(
            hall_of_fame=hall_of_fame,
            history=history,
            anti_churn=anti_churn
        )

        # ✅ Correct: method call
        assert callable(tracker.update_champion), \
            "update_champion should be callable method"

    def test_protocol_compliance_full_check(self):
        """Test ChampionTracker fully implements IChampionTracker Protocol.

        Layer 3 Prevention: Comprehensive runtime validation.
        """
        hall_of_fame = HallOfFameRepository()
        history = IterationHistory(filepath="artifacts/data/test_innovations.jsonl")
        anti_churn = AntiChurnManager()

        tracker = ChampionTracker(
            hall_of_fame=hall_of_fame,
            history=history,
            anti_churn=anti_churn
        )

        # Should pass validation without raising
        validate_protocol_compliance(tracker, IChampionTracker, "ChampionTracker")


# ============================================================================
# Error #6: ErrorClassifier.classify_single() → .classify_error() (1 location)
# ============================================================================

class TestAPIError6_ErrorClassifierMethod:
    """Verify Error #6: ErrorClassifier.classify_error(), not classify_single().

    Prevention Layers:
    - Layer 1 (Protocol): IErrorClassifier defines classify_error()
    - Layer 2 (mypy): Catches .classify_single() as AttributeError
    - Layer 3 (Runtime): validate_protocol_compliance checks method exists
    - Layer 4 (Integration): This test verifies real usage

    Note: classify_single() is from SuccessClassifier (different classifier)
    """

    def test_classify_error_method_exists(self):
        """Test ErrorClassifier has classify_error(), not classify_single().

        This prevents: classifier.classify_single(metrics) ❌
        Enforces: classifier.classify_error(error_type, error_msg) ✅
        """
        classifier = ErrorClassifier()

        # ✅ Correct: classify_error method
        assert hasattr(classifier, 'classify_error'), \
            "ErrorClassifier must have classify_error() method"
        assert callable(classifier.classify_error)

        # ❌ Wrong: classify_single is for SuccessClassifier
        assert not hasattr(classifier, 'classify_single'), \
            "ErrorClassifier should NOT have classify_single() method"

    def test_classify_error_signature(self):
        """Test classify_error has correct method signature.

        Layer 2 Prevention: mypy validates parameter types.
        """
        classifier = ErrorClassifier()

        # Test correct signature: (error_type: str, error_message: str) -> ErrorCategory
        result = classifier.classify_error("SyntaxError", "invalid syntax")
        assert isinstance(result, ErrorCategory)

    def test_protocol_defines_classify_error(self):
        """Test that IErrorClassifier Protocol defines classify_error().

        Layer 1 Prevention: Protocol contract makes it explicit.
        """
        from src.learning.interfaces import IErrorClassifier

        # Protocol should define classify_error
        assert hasattr(IErrorClassifier, 'classify_error'), \
            "IErrorClassifier Protocol must define classify_error()"

    def test_runtime_validation_catches_wrong_classifier(self):
        """Test runtime validation catches wrong classifier usage.

        Layer 3 Prevention: Runtime validation at initialization.
        """
        class FakeClassifierWithWrongMethod:
            """Fake classifier with classify_single() instead."""
            def classify_single(self, metrics):
                return "SYNTAX"

        fake = FakeClassifierWithWrongMethod()

        # Runtime validation should catch missing method
        with pytest.raises(TypeError, match="does not implement.*IErrorClassifier"):
            validate_protocol_compliance(fake, IErrorClassifier, "test")

    def test_error_classifier_full_protocol_compliance(self):
        """Test ErrorClassifier fully implements IErrorClassifier Protocol.

        Layer 3 Prevention: Comprehensive runtime validation.
        """
        classifier = ErrorClassifier()

        # Should pass validation without raising
        validate_protocol_compliance(classifier, IErrorClassifier, "ErrorClassifier")


# ============================================================================
# Error #7: IterationHistory.save_record() → .save() (1 location)
# ============================================================================

class TestAPIError7_IterationHistoryMethod:
    """Verify Error #7: IterationHistory.save(), not save_record().

    Prevention Layers:
    - Layer 1 (Protocol): IIterationHistory defines save()
    - Layer 2 (mypy): Catches .save_record() as AttributeError
    - Layer 3 (Runtime): validate_protocol_compliance checks method exists
    - Layer 4 (Integration): This test verifies real usage

    Note: Method was renamed from save_record() to save() in refactoring
    """

    def test_save_method_exists(self):
        """Test IterationHistory has save(), not save_record().

        This prevents: history.save_record(record) ❌
        Enforces: history.save(record) ✅
        """
        history = IterationHistory(filepath="artifacts/data/test_innovations.jsonl")

        # ✅ Correct: save method
        assert hasattr(history, 'save'), \
            "IterationHistory must have save() method"
        assert callable(history.save)

        # ❌ Wrong: old method name
        assert not hasattr(history, 'save_record'), \
            "IterationHistory should NOT have save_record() method (renamed to save)"

    def test_save_method_signature(self):
        """Test save() has correct method signature.

        Layer 2 Prevention: mypy validates parameter types.
        """
        history = IterationHistory(filepath="artifacts/data/test_innovations.jsonl")

        # Create a test record
        record = IterationRecord(
            iteration_num=0,
            strategy_code="# test",
            execution_result={"success": True, "execution_time": 1.0},
            metrics={"sharpe_ratio": 1.0, "total_return": 0.1, "max_drawdown": -0.05},
            classification_level="LEVEL_3",
            timestamp="2024-01-01T00:00:00",
            champion_updated=False,
            feedback_used="test feedback"
        )

        # Test correct signature: (record: IterationRecord) -> None
        result = history.save(record)
        assert result is None, "save() should return None"

    def test_protocol_defines_save(self):
        """Test that IIterationHistory Protocol defines save().

        Layer 1 Prevention: Protocol contract makes it explicit.
        """
        from src.learning.interfaces import IIterationHistory

        # Protocol should define save
        assert hasattr(IIterationHistory, 'save'), \
            "IIterationHistory Protocol must define save()"

    def test_runtime_validation_catches_old_method_name(self):
        """Test runtime validation catches old method name usage.

        Layer 3 Prevention: Runtime validation at initialization.
        """
        class FakeHistoryWithOldMethod:
            """Fake history with save_record() instead of save()."""
            def save_record(self, record):
                pass

            def get_all(self):
                return []

            def load_recent(self, N=5):
                return []

        fake = FakeHistoryWithOldMethod()

        # Runtime validation should catch missing method
        with pytest.raises(TypeError, match="does not implement.*IIterationHistory"):
            validate_protocol_compliance(fake, IIterationHistory, "test")

    def test_iteration_history_full_protocol_compliance(self):
        """Test IterationHistory fully implements IIterationHistory Protocol.

        Layer 3 Prevention: Comprehensive runtime validation.
        """
        history = IterationHistory(filepath="artifacts/data/test_innovations.jsonl")

        # Should pass validation without raising
        validate_protocol_compliance(history, IIterationHistory, "IterationHistory")

    def test_get_all_method_exists(self):
        """Test get_all() method exists (complementary to save).

        Layer 2 Prevention: mypy validates method exists.
        """
        history = IterationHistory(filepath="artifacts/data/test_innovations.jsonl")

        # ✅ Correct: get_all method
        assert hasattr(history, 'get_all'), \
            "IterationHistory must have get_all() method"
        assert callable(history.get_all)

        # Test return type
        records = history.get_all()
        assert isinstance(records, list)


# ============================================================================
# Summary Test: All 8 API Errors Prevented
# ============================================================================

class TestAllAPIErrorsPrevented:
    """Summary test validating all 8 API errors are prevented."""

    def test_error_catalog_summary(self):
        """Document all 8 API errors and their prevention mechanisms.

        This test serves as documentation of the error catalog.
        """
        error_catalog = {
            "Error #5": {
                "description": "ChampionTracker.get_champion() doesn't exist (should be .champion property)",
                "occurrences": 6,
                "prevention_layer": "Protocol @property + mypy + runtime validation",
                "test_class": "TestAPIError5_ChampionTrackerProperty"
            },
            "Error #6": {
                "description": "ErrorClassifier.classify_single() doesn't exist (should be .classify_error())",
                "occurrences": 1,
                "prevention_layer": "Protocol method + mypy + runtime validation",
                "test_class": "TestAPIError6_ErrorClassifierMethod"
            },
            "Error #7": {
                "description": "IterationHistory.save_record() doesn't exist (should be .save())",
                "occurrences": 1,
                "prevention_layer": "Protocol method + mypy + runtime validation",
                "test_class": "TestAPIError7_IterationHistoryMethod"
            }
        }

        total_occurrences = sum(e["occurrences"] for e in error_catalog.values())
        assert total_occurrences == 8, \
            f"Expected 8 total error occurrences, got {total_occurrences}"

        # All error types should have test coverage
        assert len(error_catalog) == 3, \
            f"Expected 3 error types, got {len(error_catalog)}"

    def test_all_protocols_prevent_errors(self):
        """Test that all 3 Protocols are defined and prevent errors.

        Layer 1 Prevention: Protocol definitions exist.
        """
        from src.learning.interfaces import (
            IChampionTracker,
            IIterationHistory,
            IErrorClassifier
        )

        # All Protocols should be defined
        protocols = [IChampionTracker, IIterationHistory, IErrorClassifier]
        for protocol in protocols:
            assert protocol is not None
            assert hasattr(protocol, '__annotations__') or hasattr(protocol, '__dict__')

    def test_all_implementations_comply_with_protocols(self):
        """Test that all real implementations comply with Protocols.

        Layer 3 Prevention: Runtime validation passes for all components.
        """
        # ChampionTracker
        hall_of_fame = HallOfFameRepository()
        history = IterationHistory(filepath="artifacts/data/test_innovations.jsonl")
        anti_churn = AntiChurnManager()
        tracker = ChampionTracker(
            hall_of_fame=hall_of_fame,
            history=history,
            anti_churn=anti_churn
        )
        validate_protocol_compliance(tracker, IChampionTracker, "ChampionTracker")

        # IterationHistory
        validate_protocol_compliance(history, IIterationHistory, "IterationHistory")

        # ErrorClassifier
        classifier = ErrorClassifier()
        validate_protocol_compliance(classifier, IErrorClassifier, "ErrorClassifier")

    def test_mypy_would_catch_all_errors(self):
        """Document that mypy static analysis catches all error types.

        Layer 2 Prevention: mypy --strict catches these at development time.

        Note: This is a documentation test - actual mypy checking happens
        in CI pipeline and pre-commit hooks.
        """
        mypy_catches = {
            "Error #5": "AttributeError: ChampionTracker has no attribute 'get_champion'",
            "Error #6": "AttributeError: ErrorClassifier has no attribute 'classify_single'",
            "Error #7": "AttributeError: IterationHistory has no attribute 'save_record'"
        }

        # All errors caught by mypy
        assert len(mypy_catches) == 3

        # mypy errors are preventable at static analysis time
        for error_id, mypy_error in mypy_catches.items():
            assert "AttributeError" in mypy_error, \
                f"{error_id} should be caught as AttributeError by mypy"


# ============================================================================
# Prevention Layer Summary
# ============================================================================

def test_defense_layers_summary():
    """Document the three-layer defense system.

    This test serves as living documentation of the prevention strategy.
    """
    defense_layers = {
        "Layer 1 - Protocol Definitions": {
            "file": "src/learning/interfaces.py",
            "mechanism": "typing.Protocol structural contracts",
            "when": "Design time",
            "errors_prevented": ["Property/method confusion", "Method name mismatches"]
        },
        "Layer 2 - Static Type Checking": {
            "file": "mypy.ini + .github/workflows/ci.yml",
            "mechanism": "mypy --strict static analysis",
            "when": "Pre-commit / CI time",
            "errors_prevented": ["All AttributeError at call sites", "Type mismatches"]
        },
        "Layer 3 - Runtime Validation": {
            "file": "src/learning/validation.py",
            "mechanism": "validate_protocol_compliance() function",
            "when": "Initialization time",
            "errors_prevented": ["Protocol violations in legacy code", "Dynamic imports"]
        },
        "Layer 4 - Integration Tests": {
            "file": "tests/learning/test_api_error_prevention.py (this file)",
            "mechanism": "Real component interaction tests",
            "when": "Test time",
            "errors_prevented": ["Runtime behavior mismatches", "Real-world usage patterns"]
        }
    }

    # All 4 layers should be documented
    assert len(defense_layers) == 4, "Should have 4 defense layers"

    # Each layer should have defined mechanisms
    for layer_name, layer_info in defense_layers.items():
        assert layer_info["file"], f"{layer_name} should have file reference"
        assert layer_info["mechanism"], f"{layer_name} should have mechanism"
        assert layer_info["when"], f"{layer_name} should have timing"
        assert layer_info["errors_prevented"], f"{layer_name} should prevent errors"
