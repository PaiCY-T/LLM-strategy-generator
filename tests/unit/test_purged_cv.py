"""
Unit tests for Purged Walk-Forward Cross-Validation.

P2.1.1 - RED phase: All tests should FAIL (ImportError expected).

Tests verify:
1. Split generation with 21-day purge gap
2. No overlap between train and test sets
3. Temporal ordering of test sets
4. Data leakage detection
5. Edge cases (insufficient data, invalid parameters, etc.)
"""

import pytest
import pandas as pd
import numpy as np
from src.validation.purged_cv import PurgedWalkForwardCV  # Will fail - doesn't exist yet


class TestPurgedWalkForwardCV:
    """Test suite for PurgedWalkForwardCV class."""

    @pytest.fixture
    def sample_data(self):
        """Create sample time-series data for testing."""
        # Create 3+ years of daily trading data (1000 trading days for flexibility)
        dates = pd.date_range('2020-01-01', periods=1000, freq='B')  # Business days
        data = pd.DataFrame({
            'price': np.random.randn(1000).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, 1000)
        }, index=dates)
        return data

    # === Basic Functionality Tests ===

    def test_initialization_with_default_parameters(self):
        """
        GIVEN default parameters
        WHEN creating PurgedWalkForwardCV instance
        THEN instance is created successfully with expected defaults
        """
        cv = PurgedWalkForwardCV()
        assert cv.n_splits == 5
        assert cv.purge_gap == 21
        assert cv.test_size == 252
        assert cv.min_train_size == 504

    def test_initialization_with_custom_parameters(self):
        """
        GIVEN custom parameters
        WHEN creating PurgedWalkForwardCV instance
        THEN parameters are set correctly
        """
        cv = PurgedWalkForwardCV(
            n_splits=3,
            purge_gap=10,
            test_size=126,
            min_train_size=252
        )
        assert cv.n_splits == 3
        assert cv.purge_gap == 10
        assert cv.test_size == 126
        assert cv.min_train_size == 252

    def test_split_returns_correct_number_of_splits(self, sample_data):
        """
        GIVEN sample data and n_splits=3
        WHEN calling split()
        THEN returns exactly 3 train-test pairs
        """
        cv = PurgedWalkForwardCV(n_splits=3, test_size=100, min_train_size=200, purge_gap=10)
        splits = list(cv.split(sample_data))
        assert len(splits) == 3

    def test_split_returns_train_and_test_indices(self, sample_data):
        """
        GIVEN sample data
        WHEN calling split()
        THEN each split returns (train_idx, test_idx) tuple of numpy arrays
        """
        cv = PurgedWalkForwardCV(n_splits=2, test_size=100, min_train_size=200, purge_gap=10)
        for train_idx, test_idx in cv.split(sample_data):
            assert isinstance(train_idx, np.ndarray)
            assert isinstance(test_idx, np.ndarray)
            assert len(train_idx) > 0
            assert len(test_idx) > 0

    def test_split_is_iterable(self, sample_data):
        """
        GIVEN sample data
        WHEN calling split()
        THEN returns an iterable (generator or list)
        """
        cv = PurgedWalkForwardCV(n_splits=2, test_size=100, min_train_size=200, purge_gap=10)
        splits = cv.split(sample_data)
        # Should be able to iterate
        first_split = next(iter(splits))
        assert len(first_split) == 2  # (train_idx, test_idx)

    # === Purge Gap Tests ===

    def test_purge_gap_enforced_between_train_and_test(self, sample_data):
        """
        GIVEN purge_gap=21
        WHEN generating splits
        THEN exactly 21 indices between train end and test start
        """
        cv = PurgedWalkForwardCV(n_splits=2, purge_gap=21, test_size=100, min_train_size=200)
        for train_idx, test_idx in cv.split(sample_data):
            gap_size = test_idx[0] - train_idx[-1] - 1
            assert gap_size == 21, f"Expected purge gap of 21, got {gap_size}"

    def test_purge_gap_zero_means_no_gap(self, sample_data):
        """
        GIVEN purge_gap=0
        WHEN generating splits
        THEN test starts immediately after train (no gap)
        """
        cv = PurgedWalkForwardCV(n_splits=2, purge_gap=0, test_size=100, min_train_size=200)
        for train_idx, test_idx in cv.split(sample_data):
            gap_size = test_idx[0] - train_idx[-1] - 1
            assert gap_size == 0, f"Expected no gap with purge_gap=0, got {gap_size}"

    def test_purge_gap_prevents_data_leakage(self, sample_data):
        """
        GIVEN purge_gap > 0
        WHEN generating splits
        THEN no index appears in both train and purge+test regions
        """
        cv = PurgedWalkForwardCV(n_splits=3, purge_gap=15, test_size=100, min_train_size=200)
        for train_idx, test_idx in cv.split(sample_data):
            # Calculate purge region
            purge_start = train_idx[-1] + 1
            purge_end = test_idx[0] - 1

            # Verify no overlap
            train_set = set(train_idx)
            purge_set = set(range(purge_start, purge_end + 1))
            test_set = set(test_idx)

            assert len(train_set & purge_set) == 0, "Train overlaps with purge"
            assert len(train_set & test_set) == 0, "Train overlaps with test"
            assert len(purge_set & test_set) == 0, "Purge overlaps with test"

    def test_purge_gap_consistent_across_all_splits(self, sample_data):
        """
        GIVEN purge_gap parameter
        WHEN generating multiple splits
        THEN purge gap is consistent across all splits
        """
        cv = PurgedWalkForwardCV(n_splits=4, purge_gap=15, test_size=100, min_train_size=200)
        gaps = []
        for train_idx, test_idx in cv.split(sample_data):
            gap_size = test_idx[0] - train_idx[-1] - 1
            gaps.append(gap_size)

        # All gaps should be exactly 15
        assert all(gap == 15 for gap in gaps), f"Inconsistent gaps: {gaps}"

    # === Temporal Ordering Tests ===

    def test_train_indices_before_test_indices(self, sample_data):
        """
        GIVEN any split
        WHEN checking temporal order
        THEN all train indices < all test indices
        """
        cv = PurgedWalkForwardCV(n_splits=3, purge_gap=10, test_size=100, min_train_size=200)
        for train_idx, test_idx in cv.split(sample_data):
            assert train_idx[-1] < test_idx[0], "Train must end before test starts"
            assert np.all(train_idx < test_idx[0]), "All train < first test"

    def test_train_indices_are_sorted(self, sample_data):
        """
        GIVEN any split
        WHEN checking train indices
        THEN train indices are in ascending order
        """
        cv = PurgedWalkForwardCV(n_splits=3, purge_gap=10, test_size=100, min_train_size=200)
        for train_idx, test_idx in cv.split(sample_data):
            assert np.all(np.diff(train_idx) > 0), "Train indices must be sorted ascending"

    def test_test_indices_are_sorted(self, sample_data):
        """
        GIVEN any split
        WHEN checking test indices
        THEN test indices are in ascending order
        """
        cv = PurgedWalkForwardCV(n_splits=3, purge_gap=10, test_size=100, min_train_size=200)
        for train_idx, test_idx in cv.split(sample_data):
            assert np.all(np.diff(test_idx) > 0), "Test indices must be sorted ascending"

    def test_test_sets_are_chronologically_ordered(self, sample_data):
        """
        GIVEN multiple splits
        WHEN checking test set ordering
        THEN each test set starts after previous test set ends
        """
        cv = PurgedWalkForwardCV(n_splits=3, purge_gap=10, test_size=100, min_train_size=200)
        splits = list(cv.split(sample_data))

        for i in range(len(splits) - 1):
            _, test_idx_current = splits[i]
            _, test_idx_next = splits[i + 1]

            # Next test starts after current test ends
            assert test_idx_next[0] > test_idx_current[-1], \
                "Test sets must be chronologically ordered"

    def test_train_indices_are_contiguous(self, sample_data):
        """
        GIVEN any split
        WHEN checking train indices
        THEN train indices form a contiguous sequence (no gaps)
        """
        cv = PurgedWalkForwardCV(n_splits=2, purge_gap=10, test_size=100, min_train_size=200)
        for train_idx, test_idx in cv.split(sample_data):
            # Check all differences are exactly 1
            assert np.all(np.diff(train_idx) == 1), "Train indices must be contiguous"

    def test_test_indices_are_contiguous(self, sample_data):
        """
        GIVEN any split
        WHEN checking test indices
        THEN test indices form a contiguous sequence (no gaps)
        """
        cv = PurgedWalkForwardCV(n_splits=2, purge_gap=10, test_size=100, min_train_size=200)
        for train_idx, test_idx in cv.split(sample_data):
            # Check all differences are exactly 1
            assert np.all(np.diff(test_idx) == 1), "Test indices must be contiguous"

    # === No Overlap Tests ===

    def test_no_overlap_between_consecutive_splits(self, sample_data):
        """
        GIVEN multiple splits
        WHEN checking all train-test pairs
        THEN no test index appears in multiple test sets
        """
        cv = PurgedWalkForwardCV(n_splits=3, purge_gap=10, test_size=100, min_train_size=200)
        splits = list(cv.split(sample_data))

        for i in range(len(splits)):
            train_i, test_i = splits[i]
            for j in range(i + 1, len(splits)):
                train_j, test_j = splits[j]

                # Check no test overlap between splits
                test_set_i = set(test_i)
                test_set_j = set(test_j)
                assert len(test_set_i & test_set_j) == 0, \
                    f"Test sets {i} and {j} should not overlap"

    def test_train_size_grows_with_expanding_window(self, sample_data):
        """
        GIVEN walk-forward CV (expanding window)
        WHEN checking train sizes across splits
        THEN train size increases with each split
        """
        cv = PurgedWalkForwardCV(n_splits=3, purge_gap=10, test_size=100, min_train_size=200)
        splits = list(cv.split(sample_data))

        train_sizes = [len(train_idx) for train_idx, _ in splits]

        # Each subsequent train should be larger (expanding window)
        for i in range(len(train_sizes) - 1):
            assert train_sizes[i + 1] > train_sizes[i], \
                f"Train size should grow: {train_sizes}"

    def test_test_size_remains_constant(self, sample_data):
        """
        GIVEN test_size parameter
        WHEN generating splits
        THEN all test sets have same size (except possibly last)
        """
        cv = PurgedWalkForwardCV(n_splits=3, purge_gap=10, test_size=100, min_train_size=200)
        splits = list(cv.split(sample_data))

        test_sizes = [len(test_idx) for _, test_idx in splits]

        # All test sizes should equal test_size parameter (except maybe last)
        for size in test_sizes[:-1]:  # Exclude last which might be smaller
            assert size == 100, f"Test size should be 100, got {size}"

    # === Edge Cases ===

    def test_insufficient_data_raises_error(self):
        """
        GIVEN data too short for min_train_size + purge_gap + test_size
        WHEN calling split()
        THEN raises ValueError with helpful message
        """
        # Create very short data (100 days)
        short_data = pd.DataFrame({
            'price': np.random.randn(100)
        }, index=pd.date_range('2020-01-01', periods=100, freq='B'))

        cv = PurgedWalkForwardCV(
            n_splits=2,
            purge_gap=21,
            test_size=252,
            min_train_size=504
        )

        with pytest.raises(ValueError) as exc_info:
            list(cv.split(short_data))

        assert "insufficient data" in str(exc_info.value).lower()

    def test_invalid_n_splits_raises_error(self):
        """
        GIVEN n_splits <= 0
        WHEN creating instance
        THEN raises ValueError
        """
        with pytest.raises(ValueError) as exc_info:
            PurgedWalkForwardCV(n_splits=0)

        assert "n_splits" in str(exc_info.value).lower()

    def test_negative_purge_gap_raises_error(self):
        """
        GIVEN negative purge_gap
        WHEN creating instance
        THEN raises ValueError
        """
        with pytest.raises(ValueError) as exc_info:
            PurgedWalkForwardCV(purge_gap=-10)

        assert "purge_gap" in str(exc_info.value).lower()

    def test_negative_test_size_raises_error(self):
        """
        GIVEN negative test_size
        WHEN creating instance
        THEN raises ValueError
        """
        with pytest.raises(ValueError) as exc_info:
            PurgedWalkForwardCV(test_size=-100)

        assert "test_size" in str(exc_info.value).lower()

    def test_negative_min_train_size_raises_error(self):
        """
        GIVEN negative min_train_size
        WHEN creating instance
        THEN raises ValueError
        """
        with pytest.raises(ValueError) as exc_info:
            PurgedWalkForwardCV(min_train_size=-200)

        assert "min_train_size" in str(exc_info.value).lower()

    def test_empty_dataframe_raises_error(self):
        """
        GIVEN empty DataFrame
        WHEN calling split()
        THEN raises ValueError
        """
        empty_data = pd.DataFrame()
        cv = PurgedWalkForwardCV(n_splits=2, purge_gap=10, test_size=50, min_train_size=100)

        with pytest.raises(ValueError) as exc_info:
            list(cv.split(empty_data))

        assert "empty" in str(exc_info.value).lower()

    def test_single_row_dataframe_raises_error(self):
        """
        GIVEN single-row DataFrame
        WHEN calling split()
        THEN raises ValueError
        """
        single_row = pd.DataFrame({'price': [100]})
        cv = PurgedWalkForwardCV(n_splits=1, purge_gap=0, test_size=1, min_train_size=1)

        with pytest.raises(ValueError) as exc_info:
            list(cv.split(single_row))

        assert "insufficient" in str(exc_info.value).lower()

    def test_purge_gap_larger_than_data_raises_error(self):
        """
        GIVEN purge_gap larger than available data
        WHEN calling split()
        THEN raises ValueError
        """
        small_data = pd.DataFrame({
            'price': np.random.randn(300)
        }, index=pd.date_range('2020-01-01', periods=300, freq='B'))

        cv = PurgedWalkForwardCV(
            n_splits=1,
            purge_gap=500,  # Larger than data
            test_size=50,
            min_train_size=100
        )

        with pytest.raises(ValueError) as exc_info:
            list(cv.split(small_data))

        assert "insufficient" in str(exc_info.value).lower() or "purge_gap" in str(exc_info.value).lower()

    # === Integration Tests ===

    def test_realistic_3year_backtest_scenario(self, sample_data):
        """
        GIVEN sufficient trading data (1000 trading days)
        WHEN using realistic parameters (1 year test, 2 year min train, 21 day purge)
        THEN generates valid splits
        """
        cv = PurgedWalkForwardCV(
            n_splits=2,
            purge_gap=21,
            test_size=252,  # 1 year test
            min_train_size=504  # 2 years minimum train
        )

        splits = list(cv.split(sample_data))
        assert len(splits) == 2

        # First split
        train_1, test_1 = splits[0]
        assert len(train_1) >= 504  # At least 2 years
        assert len(test_1) == 252   # Exactly 1 year

        # Second split
        train_2, test_2 = splits[1]
        assert len(train_2) > len(train_1)  # Expanding window
        assert len(test_2) <= 252  # Up to 1 year (might be shorter if data runs out)

    def test_works_with_datetime_index(self):
        """
        GIVEN DataFrame with DatetimeIndex
        WHEN calling split()
        THEN works correctly with datetime-indexed data
        """
        dates = pd.date_range('2020-01-01', periods=600, freq='B')
        data = pd.DataFrame({
            'price': np.random.randn(600),
            'volume': np.random.randint(1000, 10000, 600)
        }, index=dates)

        cv = PurgedWalkForwardCV(n_splits=2, purge_gap=10, test_size=100, min_train_size=200)
        splits = list(cv.split(data))

        assert len(splits) == 2
        # Verify indices are integers (positions), not datetime
        for train_idx, test_idx in splits:
            assert train_idx.dtype == np.int64 or train_idx.dtype == np.int32
            assert test_idx.dtype == np.int64 or test_idx.dtype == np.int32

    def test_works_with_integer_index(self):
        """
        GIVEN DataFrame with integer index
        WHEN calling split()
        THEN works correctly (uses positional indices)
        """
        data = pd.DataFrame({
            'price': np.random.randn(600),
            'volume': np.random.randint(1000, 10000, 600)
        })  # Default integer index

        cv = PurgedWalkForwardCV(n_splits=2, purge_gap=10, test_size=100, min_train_size=200)
        splits = list(cv.split(data))

        assert len(splits) == 2

    def test_min_train_size_respected_in_all_splits(self, sample_data):
        """
        GIVEN min_train_size parameter
        WHEN generating splits
        THEN all train sets meet minimum size requirement
        """
        cv = PurgedWalkForwardCV(n_splits=3, purge_gap=10, test_size=100, min_train_size=250)
        splits = list(cv.split(sample_data))

        for train_idx, test_idx in splits:
            assert len(train_idx) >= 250, f"Train size {len(train_idx)} < min_train_size 250"

    def test_indices_within_data_bounds(self, sample_data):
        """
        GIVEN sample data
        WHEN generating splits
        THEN all indices are within data bounds [0, len(data))
        """
        cv = PurgedWalkForwardCV(n_splits=3, purge_gap=10, test_size=100, min_train_size=200)
        splits = list(cv.split(sample_data))

        data_length = len(sample_data)
        for train_idx, test_idx in splits:
            # All indices should be >= 0
            assert np.all(train_idx >= 0), "Train indices contain negative values"
            assert np.all(test_idx >= 0), "Test indices contain negative values"

            # All indices should be < data_length
            assert np.all(train_idx < data_length), "Train indices exceed data length"
            assert np.all(test_idx < data_length), "Test indices exceed data length"
