"""Purged walk-forward cross-validation for time series data.

This module implements cross-validation strategies that prevent data leakage
in financial time series backtesting through purge gaps.
"""

from typing import Iterator, Tuple
import numpy as np
import numpy.typing as npt
import pandas as pd


class PurgedWalkForwardCV:
    """Purged walk-forward cross-validation for time series data.

    Implements walk-forward cross-validation with purge gap to prevent
    data leakage in financial time series backtesting.

    The purge gap ensures no information from the test period can leak into
    training by removing data points between train and test sets.

    Examples:
        >>> import pandas as pd
        >>> import numpy as np
        >>> dates = pd.date_range('2020-01-01', periods=756, freq='B')
        >>> data = pd.DataFrame({'price': np.random.randn(756)}, index=dates)
        >>>
        >>> cv = PurgedWalkForwardCV(
        ...     n_splits=2,
        ...     purge_gap=21,       # 21 trading days purge
        ...     test_size=252,      # 1 year test period
        ...     min_train_size=504  # 2 years minimum training
        ... )
        >>>
        >>> for train_idx, test_idx in cv.split(data):
        ...     train_data = data.iloc[train_idx]
        ...     test_data = data.iloc[test_idx]
        ...     # Backtest strategy on test_data
    """

    def __init__(
        self,
        n_splits: int = 5,
        purge_gap: int = 21,
        test_size: int = 252,
        min_train_size: int = 504
    ):
        """Initialize purged walk-forward cross-validator.

        Args:
            n_splits: Number of train-test splits to generate
            purge_gap: Number of periods to purge between train and test
            test_size: Number of periods in each test set
            min_train_size: Minimum number of periods in training set

        Raises:
            ValueError: If any parameter is invalid (negative, zero splits, etc.)
        """
        # Validate n_splits
        if n_splits <= 0:
            raise ValueError(f"n_splits must be positive, got {n_splits}")

        # Validate purge_gap
        if purge_gap < 0:
            raise ValueError(f"purge_gap must be non-negative, got {purge_gap}")

        # Validate test_size
        if test_size <= 0:
            raise ValueError(f"test_size must be positive, got {test_size}")

        # Validate min_train_size
        if min_train_size <= 0:
            raise ValueError(f"min_train_size must be positive, got {min_train_size}")

        self.n_splits = n_splits
        self.purge_gap = purge_gap
        self.test_size = test_size
        self.min_train_size = min_train_size

    def split(self, data: pd.DataFrame) -> Iterator[Tuple[npt.NDArray[np.int_], npt.NDArray[np.int_]]]:
        """Generate train-test splits with purge gap.

        Args:
            data: Time series DataFrame (can have datetime or integer index)

        Yields:
            Tuple of (train_indices, test_indices) where indices are integer positions

        Raises:
            ValueError: If data is empty or insufficient for requested splits

        Algorithm:
            1. Start with min_train_size for first training set
            2. Add purge_gap after training set
            3. Add test_size for test set
            4. For next split, expand training window to include previous test
            5. Repeat until n_splits generated or data exhausted
        """
        # Validate data
        if data is None or len(data) == 0:
            raise ValueError("Cannot split empty data")

        # Work with positional indices
        n = len(data)

        # Validate sufficient data for at least one split
        min_required = self.min_train_size + self.purge_gap + 1  # Need at least 1 test point
        if n < min_required:
            raise ValueError(
                f"Insufficient data: need at least {min_required} points "
                f"(min_train={self.min_train_size} + purge={self.purge_gap} + 1), got {n}"
            )

        # Generate n_splits
        for split_idx in range(self.n_splits):
            # Calculate train end (expanding window)
            train_end = self.min_train_size + split_idx * self.test_size

            # Test indices: after purge gap
            test_start = train_end + self.purge_gap

            # Check if we have enough data for this split (need at least 1 test point)
            if test_start >= n:
                break  # Not enough data for this split

            # Train indices: from start to train_end
            train_idx = np.arange(0, train_end)

            # Test end: either full test_size or remaining data
            test_end = min(test_start + self.test_size, n)
            test_idx = np.arange(test_start, test_end)

            yield train_idx, test_idx
