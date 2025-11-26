"""Tests for auto-correction confidence scoring.

This module tests Task 9.3: Confidence scoring for auto-correction system.

Test Coverage:
- High confidence (>0.9) for exact COMMON_CORRECTIONS matches
- Medium confidence (0.7-0.9) for category-based corrections
- Low confidence (<0.7) for fuzzy string matches
- Zero confidence (0.0) for no matches
- Confidence level classification

TDD Status: RED - Tests written before implementation
"""
import pytest
from src.config.data_fields import DataFieldManifest


# Import AutoCorrector and CorrectionResult (to be implemented)
try:
    from src.validation.auto_corrector import AutoCorrector, CorrectionResult
except ImportError:
    # Will fail during RED phase - expected
    AutoCorrector = None
    CorrectionResult = None


@pytest.fixture
def manifest():
    """Create DataFieldManifest instance for testing."""
    return DataFieldManifest('tests/fixtures/finlab_fields.json')


@pytest.fixture
def corrector(manifest):
    """Create AutoCorrector instance for testing."""
    if AutoCorrector is None:
        pytest.skip("AutoCorrector not implemented yet (RED phase)")
    return AutoCorrector(manifest)


class TestConfidenceScoring:
    """Test confidence scoring for auto-correction suggestions."""

    def test_exact_match_has_high_confidence(self, corrector):
        """Test that exact COMMON_CORRECTIONS matches have >=0.95 confidence.

        'price:成交量' is a known common mistake in COMMON_CORRECTIONS.
        Should return high confidence (>=0.95) correction.
        """
        result = corrector.suggest_correction('price:成交量')
        assert result.suggested_field == 'price:成交金額'
        assert result.confidence >= 0.95
        assert result.confidence_level == 'high'
        assert result.reason == 'exact_match_common_correction'

    def test_common_correction_turnover_high_confidence(self, corrector):
        """Test common mistake 'turnover' has high confidence.

        'turnover' is in COMMON_CORRECTIONS and should map to 'price:成交金額'
        with high confidence (>=0.95).
        """
        result = corrector.suggest_correction('turnover')
        assert result.suggested_field == 'price:成交金額'
        assert result.confidence >= 0.95
        assert result.confidence_level == 'high'

    def test_common_correction_pe_ratio_high_confidence(self, corrector):
        """Test 'pe_ratio' common mistake has high confidence."""
        result = corrector.suggest_correction('pe_ratio')
        assert result.suggested_field == 'fundamental_features:本益比'
        assert result.confidence >= 0.95
        assert result.confidence_level == 'high'

    def test_partial_match_medium_confidence(self, corrector):
        """Test partial string matches have medium confidence (0.7-0.9).

        When a field name is a substring of a canonical name,
        it should return medium confidence.
        """
        # '成交' is substring of multiple price fields (成交金額, 成交股數, 成交筆數)
        # but not in COMMON_CORRECTIONS or valid aliases
        result = corrector.suggest_correction('成交')
        # Should match one of the 成交* fields via partial matching
        assert result.suggested_field is not None
        assert '成交' in result.suggested_field
        assert 0.7 <= result.confidence < 0.9
        assert result.confidence_level == 'medium'
        assert result.reason == 'partial_match'

    def test_fuzzy_match_low_confidence(self, corrector):
        """Test fuzzy string matches have low confidence (<0.7).

        Typos or close matches should return low confidence corrections.
        """
        # Typo: 'closing_pric' (missing 'e')
        result = corrector.suggest_correction('closing_pric')
        if result.suggested_field:
            assert result.confidence < 0.7
            assert result.confidence_level == 'low'
            assert 'fuzzy' in result.reason.lower()

    def test_no_match_zero_confidence(self, corrector):
        """Test no match returns None with 0 confidence."""
        result = corrector.suggest_correction('completely_invalid_xyz_123')
        assert result.suggested_field is None
        assert result.confidence == 0.0
        assert result.confidence_level == 'none'
        assert result.reason == 'no_match'

    def test_valid_field_returns_itself_high_confidence(self, corrector):
        """Test that already valid fields return themselves with 1.0 confidence."""
        result = corrector.suggest_correction('close')
        assert result.suggested_field == 'close'
        assert result.confidence == 1.0
        assert result.confidence_level == 'high'
        assert result.reason == 'valid_field'

    def test_confidence_level_classification(self, corrector):
        """Test confidence level classification thresholds."""
        # High: >= 0.9
        assert corrector.classify_confidence(0.95) == 'high'
        assert corrector.classify_confidence(0.9) == 'high'

        # Medium: >= 0.7
        assert corrector.classify_confidence(0.75) == 'medium'
        assert corrector.classify_confidence(0.7) == 'medium'

        # Low: > 0.0 and < 0.7
        assert corrector.classify_confidence(0.5) == 'low'
        assert corrector.classify_confidence(0.69) == 'low'

        # None: 0.0
        assert corrector.classify_confidence(0.0) == 'none'


class TestCorrectionResult:
    """Test CorrectionResult dataclass structure."""

    def test_correction_result_structure(self):
        """Test CorrectionResult has required attributes."""
        if CorrectionResult is None:
            pytest.skip("CorrectionResult not implemented yet (RED phase)")

        result = CorrectionResult(
            original_field='price:成交量',
            suggested_field='price:成交金額',
            confidence=0.95,
            confidence_level='high',
            reason='exact_match_common_correction'
        )

        assert result.original_field == 'price:成交量'
        assert result.suggested_field == 'price:成交金額'
        assert result.confidence == 0.95
        assert result.confidence_level == 'high'
        assert result.reason == 'exact_match_common_correction'

    def test_correction_result_none_suggestion(self):
        """Test CorrectionResult with no suggestion (None)."""
        if CorrectionResult is None:
            pytest.skip("CorrectionResult not implemented yet (RED phase)")

        result = CorrectionResult(
            original_field='invalid_xyz',
            suggested_field=None,
            confidence=0.0,
            confidence_level='none',
            reason='no_match'
        )

        assert result.original_field == 'invalid_xyz'
        assert result.suggested_field is None
        assert result.confidence == 0.0
        assert result.confidence_level == 'none'


class TestAutoCorrector:
    """Test AutoCorrector initialization and basic functionality."""

    def test_auto_corrector_initialization(self, manifest):
        """Test AutoCorrector initializes with DataFieldManifest."""
        if AutoCorrector is None:
            pytest.skip("AutoCorrector not implemented yet (RED phase)")

        corrector = AutoCorrector(manifest)
        assert corrector.manifest is manifest

    def test_auto_corrector_has_thresholds(self):
        """Test AutoCorrector has confidence threshold constants."""
        if AutoCorrector is None:
            pytest.skip("AutoCorrector not implemented yet (RED phase)")

        assert hasattr(AutoCorrector, 'HIGH_CONFIDENCE')
        assert hasattr(AutoCorrector, 'MEDIUM_CONFIDENCE_MIN')
        assert hasattr(AutoCorrector, 'LOW_CONFIDENCE_MIN')

        # Verify threshold values
        assert AutoCorrector.HIGH_CONFIDENCE >= 0.9
        assert AutoCorrector.MEDIUM_CONFIDENCE_MIN >= 0.7
        assert AutoCorrector.LOW_CONFIDENCE_MIN > 0.0
