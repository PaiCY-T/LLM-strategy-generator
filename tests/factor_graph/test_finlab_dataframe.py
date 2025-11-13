"""
Unit Tests for FinLabDataFrame Container
========================================

Tests the matrix-native container for Factor Graph V2.

Test Coverage:
- Container initialization
- Matrix addition and retrieval
- Shape validation
- Type validation
- Error handling
- Lazy loading
- Metadata management
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from src.factor_graph.finlab_dataframe import FinLabDataFrame


class TestFinLabDataFrameInit:
    """Test FinLabDataFrame initialization."""

    def test_init_default(self):
        """Test default initialization."""
        container = FinLabDataFrame()

        assert container._matrices == {}
        assert container._data_module is None
        assert container._base_shape is None
        assert container._metadata == {}

    def test_init_with_data_module(self):
        """Test initialization with data module."""
        mock_data = Mock()
        container = FinLabDataFrame(data_module=mock_data)

        assert container._data_module == mock_data

    def test_init_with_base_shape(self):
        """Test initialization with base shape."""
        container = FinLabDataFrame(base_shape=(100, 50))

        assert container._base_shape == (100, 50)


class TestAddMatrix:
    """Test adding matrices to container."""

    def test_add_first_matrix_establishes_shape(self):
        """Test that first matrix establishes base shape."""
        container = FinLabDataFrame()
        matrix = pd.DataFrame(np.random.rand(100, 50))

        container.add_matrix('test', matrix)

        assert container._base_shape == (100, 50)
        assert 'test' in container._matrices

    def test_add_matrix_with_matching_shape(self):
        """Test adding matrix with matching shape."""
        container = FinLabDataFrame()
        matrix1 = pd.DataFrame(np.random.rand(100, 50))
        matrix2 = pd.DataFrame(np.random.rand(100, 50))

        container.add_matrix('first', matrix1)
        container.add_matrix('second', matrix2)

        assert len(container._matrices) == 2
        assert container._base_shape == (100, 50)

    def test_add_matrix_with_mismatched_shape_raises_error(self):
        """Test that mismatched shape raises ValueError."""
        container = FinLabDataFrame()
        matrix1 = pd.DataFrame(np.random.rand(100, 50))
        matrix2 = pd.DataFrame(np.random.rand(100, 60))  # Different shape

        container.add_matrix('first', matrix1)

        with pytest.raises(ValueError, match="does not match base shape"):
            container.add_matrix('second', matrix2)

    def test_add_matrix_without_validation(self):
        """Test adding matrix without shape validation."""
        container = FinLabDataFrame()
        matrix1 = pd.DataFrame(np.random.rand(100, 50))
        matrix2 = pd.DataFrame(np.random.rand(100, 60))

        container.add_matrix('first', matrix1)
        container.add_matrix('second', matrix2, validate=False)

        # Should succeed without validation
        assert len(container._matrices) == 2

    def test_add_matrix_wrong_type_raises_error(self):
        """Test that non-DataFrame raises TypeError."""
        container = FinLabDataFrame()

        with pytest.raises(TypeError, match="Expected pd.DataFrame"):
            container.add_matrix('test', [1, 2, 3])

    def test_add_duplicate_matrix_raises_error(self):
        """Test that duplicate name raises KeyError."""
        container = FinLabDataFrame()
        matrix = pd.DataFrame(np.random.rand(100, 50))

        container.add_matrix('test', matrix)

        with pytest.raises(KeyError, match="already exists"):
            container.add_matrix('test', matrix)

    def test_add_matrix_creates_copy(self):
        """Test that added matrix is copied (immutability)."""
        container = FinLabDataFrame()
        matrix = pd.DataFrame(np.random.rand(100, 50))
        original_value = matrix.iloc[0, 0]

        container.add_matrix('test', matrix)

        # Modify original matrix
        matrix.iloc[0, 0] = 999

        # Container should have original value
        assert container.get_matrix('test').iloc[0, 0] == original_value


class TestGetMatrix:
    """Test retrieving matrices from container."""

    def test_get_existing_matrix(self):
        """Test getting existing matrix."""
        container = FinLabDataFrame()
        matrix = pd.DataFrame(np.random.rand(100, 50))

        container.add_matrix('test', matrix)
        retrieved = container.get_matrix('test')

        pd.testing.assert_frame_equal(retrieved, matrix)

    def test_get_nonexistent_matrix_raises_error(self):
        """Test that getting nonexistent matrix raises KeyError."""
        container = FinLabDataFrame()

        with pytest.raises(KeyError, match="not found in container"):
            container.get_matrix('nonexistent')

    def test_get_matrix_without_lazy_load(self):
        """Test getting matrix with lazy_load=False."""
        container = FinLabDataFrame()

        with pytest.raises(KeyError):
            container.get_matrix('nonexistent', lazy_load=False)


class TestHasMatrix:
    """Test checking matrix existence."""

    def test_has_matrix_existing(self):
        """Test has_matrix returns True for existing matrix."""
        container = FinLabDataFrame()
        matrix = pd.DataFrame(np.random.rand(100, 50))

        container.add_matrix('test', matrix)

        assert container.has_matrix('test') is True

    def test_has_matrix_nonexistent(self):
        """Test has_matrix returns False for nonexistent matrix."""
        container = FinLabDataFrame()

        assert container.has_matrix('nonexistent') is False


class TestListMatrices:
    """Test listing all matrices."""

    def test_list_matrices_empty(self):
        """Test listing matrices in empty container."""
        container = FinLabDataFrame()

        assert container.list_matrices() == []

    def test_list_matrices_with_data(self):
        """Test listing matrices with data."""
        container = FinLabDataFrame()
        matrix = pd.DataFrame(np.random.rand(100, 50))

        container.add_matrix('close', matrix)
        container.add_matrix('momentum', matrix)

        matrices = container.list_matrices()
        assert set(matrices) == {'close', 'momentum'}


class TestGetShape:
    """Test getting container shape."""

    def test_get_shape_empty_container(self):
        """Test get_shape returns None for empty container."""
        container = FinLabDataFrame()

        assert container.get_shape() is None

    def test_get_shape_with_data(self):
        """Test get_shape returns base shape."""
        container = FinLabDataFrame()
        matrix = pd.DataFrame(np.random.rand(100, 50))

        container.add_matrix('test', matrix)

        assert container.get_shape() == (100, 50)

    def test_get_shape_with_predefined_base_shape(self):
        """Test get_shape with predefined base shape."""
        container = FinLabDataFrame(base_shape=(4563, 2661))

        assert container.get_shape() == (4563, 2661)


class TestUpdateMatrix:
    """Test updating existing matrices."""

    def test_update_existing_matrix(self):
        """Test updating existing matrix."""
        container = FinLabDataFrame()
        matrix1 = pd.DataFrame(np.ones((100, 50)))
        matrix2 = pd.DataFrame(np.zeros((100, 50)))

        container.add_matrix('test', matrix1)
        container.update_matrix('test', matrix2)

        updated = container.get_matrix('test')
        assert updated.iloc[0, 0] == 0.0

    def test_update_nonexistent_matrix_raises_error(self):
        """Test that updating nonexistent matrix raises KeyError."""
        container = FinLabDataFrame()
        matrix = pd.DataFrame(np.random.rand(100, 50))

        with pytest.raises(KeyError, match="does not exist"):
            container.update_matrix('nonexistent', matrix)

    def test_update_matrix_with_wrong_shape_raises_error(self):
        """Test that updating with wrong shape raises ValueError."""
        container = FinLabDataFrame()
        matrix1 = pd.DataFrame(np.random.rand(100, 50))
        matrix2 = pd.DataFrame(np.random.rand(100, 60))

        container.add_matrix('test', matrix1)

        with pytest.raises(ValueError, match="does not match base shape"):
            container.update_matrix('test', matrix2)


class TestRemoveMatrix:
    """Test removing matrices."""

    def test_remove_existing_matrix(self):
        """Test removing existing matrix."""
        container = FinLabDataFrame()
        matrix = pd.DataFrame(np.random.rand(100, 50))

        container.add_matrix('test', matrix)
        container.remove_matrix('test')

        assert not container.has_matrix('test')

    def test_remove_nonexistent_matrix_raises_error(self):
        """Test that removing nonexistent matrix raises KeyError."""
        container = FinLabDataFrame()

        with pytest.raises(KeyError, match="does not exist"):
            container.remove_matrix('nonexistent')


class TestMetadata:
    """Test metadata management."""

    def test_set_and_get_metadata(self):
        """Test setting and getting metadata."""
        container = FinLabDataFrame()

        container.set_metadata('backtest_period', '2020-2024')
        period = container.get_metadata('backtest_period')

        assert period == '2020-2024'

    def test_get_metadata_with_default(self):
        """Test getting nonexistent metadata with default."""
        container = FinLabDataFrame()

        value = container.get_metadata('nonexistent', default='default_value')

        assert value == 'default_value'

    def test_get_metadata_nonexistent_returns_none(self):
        """Test getting nonexistent metadata returns None."""
        container = FinLabDataFrame()

        value = container.get_metadata('nonexistent')

        assert value is None


class TestLazyLoading:
    """Test lazy loading functionality."""

    def test_lazy_load_close_matrix(self):
        """Test lazy loading 'close' matrix."""
        mock_data = Mock()
        mock_close = pd.DataFrame(np.random.rand(100, 50))
        mock_data.get.return_value = mock_close

        container = FinLabDataFrame(data_module=mock_data)

        # Request 'close' matrix (should trigger lazy load)
        retrieved = container.get_matrix('close')

        mock_data.get.assert_called_once_with('price:收盤價')
        pd.testing.assert_frame_equal(retrieved, mock_close)

    def test_lazy_load_unsupported_matrix(self):
        """Test lazy loading unsupported matrix raises KeyError."""
        mock_data = Mock()
        container = FinLabDataFrame(data_module=mock_data)

        with pytest.raises(KeyError):
            container.get_matrix('unsupported_matrix')

    def test_lazy_load_without_data_module(self):
        """Test lazy loading without data module raises KeyError."""
        container = FinLabDataFrame()  # No data module

        with pytest.raises(KeyError):
            container.get_matrix('close')


class TestRepresentation:
    """Test string representations."""

    def test_repr(self):
        """Test developer-friendly representation."""
        container = FinLabDataFrame()
        matrix = pd.DataFrame(np.random.rand(100, 50))

        container.add_matrix('close', matrix)
        container.add_matrix('momentum', matrix)

        repr_str = repr(container)

        assert 'FinLabDataFrame' in repr_str
        assert 'close' in repr_str
        assert 'momentum' in repr_str
        assert 'shape=(100, 50)' in repr_str

    def test_str_empty(self):
        """Test human-readable representation of empty container."""
        container = FinLabDataFrame()

        str_rep = str(container)

        assert 'empty' in str_rep.lower()

    def test_str_with_matrices(self):
        """Test human-readable representation with matrices."""
        container = FinLabDataFrame()
        matrix = pd.DataFrame(np.random.rand(100, 50))

        container.add_matrix('close', matrix)

        str_rep = str(container)

        assert 'close' in str_rep
        assert '(100, 50)' in str_rep


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_typical_factor_pipeline_flow(self):
        """Test typical flow: add close, calculate momentum, calculate position."""
        container = FinLabDataFrame()

        # Simulate FinLab data
        dates = pd.date_range('2020-01-01', periods=100)
        symbols = [f'STOCK_{i}' for i in range(50)]
        close = pd.DataFrame(
            np.random.rand(100, 50) * 100,
            index=dates,
            columns=symbols
        )

        # Add close price
        container.add_matrix('close', close)

        # Calculate momentum (factor logic would do this)
        momentum = (close / close.shift(20)) - 1
        container.add_matrix('momentum', momentum)

        # Calculate position signal
        position = (momentum > 0.05).astype(float)
        container.add_matrix('position', position)

        # Verify all matrices exist
        assert container.has_matrix('close')
        assert container.has_matrix('momentum')
        assert container.has_matrix('position')

        # Verify shapes match
        assert container.get_matrix('close').shape == (100, 50)
        assert container.get_matrix('momentum').shape == (100, 50)
        assert container.get_matrix('position').shape == (100, 50)
