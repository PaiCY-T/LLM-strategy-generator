"""
Unit tests for DataPipelineIntegrity - Story 7: Data Pipeline Integrity.

This module tests the DataPipelineIntegrity's ability to compute dataset checksums,
validate data consistency, and record complete data provenance for reproducibility.

Design Reference: learning-system-enhancement/spec.md
Tasks Reference: learning-system-enhancement/tasks.md lines 389-396 (Task 7.7)
Requirements Reference: 1.7.1-1.7.4, F7.1-F7.4 (data integrity system)
"""

import pytest
import hashlib
import json
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
import numpy as np

from src.data.pipeline_integrity import DataPipelineIntegrity


# ==============================================================================
# Test Fixtures
# ==============================================================================

@pytest.fixture
def integrity():
    """Create DataPipelineIntegrity instance for testing."""
    return DataPipelineIntegrity()


@pytest.fixture
def mock_finlab_data():
    """
    Create mock Finlab data object with realistic DataFrames.

    Returns:
        Mock object with:
        - get() method returning DataFrames for key datasets
        - Key datasets: price:收盤價, price:成交金額, fundamental_features:ROE稅後
    """
    # Create mock data object
    mock_data = Mock()

    # Create realistic DataFrames for key datasets
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    stocks = ['2330', '2317', '2454', '2308', '2303']

    # Price data: 收盤價 (closing price)
    closing_price_df = pd.DataFrame(
        np.random.uniform(100, 500, (100, 5)),
        index=dates,
        columns=stocks
    )

    # Trading value: 成交金額
    trading_value_df = pd.DataFrame(
        np.random.uniform(1e6, 1e9, (100, 5)),
        index=dates,
        columns=stocks
    )

    # ROE data: ROE稅後
    roe_df = pd.DataFrame(
        np.random.uniform(0.05, 0.25, (100, 5)),
        index=dates,
        columns=stocks
    )

    # Configure mock to return appropriate DataFrames
    def get_dataset(key):
        if key == 'price:收盤價':
            return closing_price_df
        elif key == 'price:成交金額':
            return trading_value_df
        elif key == 'fundamental_features:ROE稅後':
            return roe_df
        else:
            raise KeyError(f"Unknown dataset: {key}")

    mock_data.get = Mock(side_effect=get_dataset)

    return mock_data


@pytest.fixture
def mock_finlab_data_simple():
    """
    Create simple mock Finlab data with deterministic values for testing.

    Returns:
        Mock object with simple, predictable DataFrames
    """
    mock_data = Mock()

    # Simple deterministic DataFrames
    simple_df1 = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    simple_df2 = pd.DataFrame({'C': [7, 8, 9], 'D': [10, 11, 12]})
    simple_df3 = pd.DataFrame({'E': [13, 14, 15], 'F': [16, 17, 18]})

    def get_dataset(key):
        if key == 'price:收盤價':
            return simple_df1
        elif key == 'price:成交金額':
            return simple_df2
        elif key == 'fundamental_features:ROE稅後':
            return simple_df3
        else:
            raise KeyError(f"Unknown dataset: {key}")

    mock_data.get = Mock(side_effect=get_dataset)

    return mock_data


@pytest.fixture
def mock_finlab_data_modified():
    """
    Create modified version of simple mock data (for consistency testing).

    Returns:
        Mock object with slightly modified DataFrames
    """
    mock_data = Mock()

    # Modified DataFrames (last value changed)
    modified_df1 = pd.DataFrame({'A': [1, 2, 999], 'B': [4, 5, 6]})  # Changed
    simple_df2 = pd.DataFrame({'C': [7, 8, 9], 'D': [10, 11, 12]})
    simple_df3 = pd.DataFrame({'E': [13, 14, 15], 'F': [16, 17, 18]})

    def get_dataset(key):
        if key == 'price:收盤價':
            return modified_df1
        elif key == 'price:成交金額':
            return simple_df2
        elif key == 'fundamental_features:ROE稅後':
            return simple_df3
        else:
            raise KeyError(f"Unknown dataset: {key}")

    mock_data.get = Mock(side_effect=get_dataset)

    return mock_data


@pytest.fixture
def mock_finlab_data_missing_datasets():
    """
    Create mock Finlab data with missing datasets (error handling test).

    Returns:
        Mock object that raises exceptions for some datasets
    """
    mock_data = Mock()

    simple_df1 = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

    def get_dataset(key):
        if key == 'price:收盤價':
            return simple_df1
        else:
            raise KeyError(f"Dataset not available: {key}")

    mock_data.get = Mock(side_effect=get_dataset)

    return mock_data


# ==============================================================================
# Test: compute_dataset_checksum - Determinism
# ==============================================================================

def test_compute_dataset_checksum_determinism(integrity, mock_finlab_data_simple):
    """
    Test compute_dataset_checksum produces same checksum for identical data.

    Requirement: 1.7.1 - Deterministic checksums for reproducibility
    """
    # Act
    checksum1 = integrity.compute_dataset_checksum(mock_finlab_data_simple)
    checksum2 = integrity.compute_dataset_checksum(mock_finlab_data_simple)

    # Assert
    assert checksum1 == checksum2, "Same data should produce identical checksums"
    assert len(checksum1) == 64, "Checksum should be 64-character SHA-256 hex digest"
    assert checksum1.isalnum(), "Checksum should be alphanumeric (hex)"


def test_compute_dataset_checksum_determinism_multiple_calls(integrity, mock_finlab_data):
    """Test determinism across multiple checksum computations."""
    # Act - Compute checksum 5 times
    checksums = [
        integrity.compute_dataset_checksum(mock_finlab_data)
        for _ in range(5)
    ]

    # Assert
    assert len(set(checksums)) == 1, "All checksums should be identical"
    assert all(len(cs) == 64 for cs in checksums), "All checksums should be 64 chars"


def test_compute_dataset_checksum_format(integrity, mock_finlab_data_simple):
    """Test checksum format (64-character SHA-256 hex digest)."""
    # Act
    checksum = integrity.compute_dataset_checksum(mock_finlab_data_simple)

    # Assert
    assert isinstance(checksum, str), "Checksum should be string"
    assert len(checksum) == 64, "SHA-256 hex digest is 64 characters"
    assert all(c in '0123456789abcdef' for c in checksum), \
        "Checksum should be lowercase hexadecimal"


# ==============================================================================
# Test: compute_dataset_checksum - Different Data
# ==============================================================================

def test_compute_dataset_checksum_different_data(
    integrity, mock_finlab_data_simple, mock_finlab_data_modified
):
    """
    Test compute_dataset_checksum produces different checksums for different data.

    Requirement: F7.1 - Unique checksums detect data changes
    """
    # Act
    checksum1 = integrity.compute_dataset_checksum(mock_finlab_data_simple)
    checksum2 = integrity.compute_dataset_checksum(mock_finlab_data_modified)

    # Assert
    assert checksum1 != checksum2, "Different data should produce different checksums"


def test_compute_dataset_checksum_sensitive_to_changes(integrity):
    """Test checksum sensitivity to small data changes."""
    # Arrange - Create two mock data objects with tiny difference
    mock_data1 = Mock()
    mock_data2 = Mock()

    df1 = pd.DataFrame({'A': [1.000000], 'B': [2.000000]})
    df2 = pd.DataFrame({'A': [1.000001], 'B': [2.000000]})  # Tiny change

    mock_data1.get = Mock(side_effect=lambda k: df1)
    mock_data2.get = Mock(side_effect=lambda k: df2)

    # Act
    checksum1 = integrity.compute_dataset_checksum(mock_data1)
    checksum2 = integrity.compute_dataset_checksum(mock_data2)

    # Assert
    assert checksum1 != checksum2, "Checksum should be sensitive to small changes"


# ==============================================================================
# Test: compute_dataset_checksum - None Data
# ==============================================================================

def test_compute_dataset_checksum_none_data(integrity):
    """
    Test compute_dataset_checksum handles None data gracefully.

    Requirement: F7.1 - Robust error handling
    """
    # Act
    checksum = integrity.compute_dataset_checksum(None)

    # Assert
    assert checksum == 'EMPTY_DATA_CHECKSUM_' + '0' * 44, \
        "None data should return empty checksum marker"
    assert len(checksum) == 64, "Empty checksum should also be 64 characters"


def test_compute_dataset_checksum_none_data_determinism(integrity):
    """Test that None data always produces same empty checksum."""
    # Act
    checksum1 = integrity.compute_dataset_checksum(None)
    checksum2 = integrity.compute_dataset_checksum(None)

    # Assert
    assert checksum1 == checksum2, "None data should produce consistent checksum"
    assert checksum1.startswith('EMPTY_DATA_CHECKSUM_'), \
        "Should have recognizable empty marker"


# ==============================================================================
# Test: compute_dataset_checksum - Error Handling
# ==============================================================================

def test_compute_dataset_checksum_missing_datasets(
    integrity, mock_finlab_data_missing_datasets
):
    """Test checksum computation with missing datasets."""
    # Act
    checksum = integrity.compute_dataset_checksum(mock_finlab_data_missing_datasets)

    # Assert
    assert isinstance(checksum, str), "Should return string even with missing datasets"
    assert len(checksum) == 64, "Checksum should be 64 characters"
    # Should not start with ERROR_CHECKSUM_ since graceful handling
    assert not checksum.startswith('ERROR_CHECKSUM_'), \
        "Missing datasets should be handled gracefully, not as error"


def test_compute_dataset_checksum_serialization_error(integrity):
    """Test checksum computation with non-serializable data."""
    # Arrange - Create mock that raises exception in to_dict
    mock_data = Mock()
    mock_df = Mock()
    mock_df.to_dict = Mock(side_effect=Exception("Serialization failed"))
    mock_data.get = Mock(return_value=mock_df)

    # Act
    checksum = integrity.compute_dataset_checksum(mock_data)

    # Assert
    assert checksum.startswith('ERROR_CHECKSUM_'), \
        "Serialization errors should return error checksum"
    assert len(checksum) == 64, "Error checksum should also be 64 characters"


# ==============================================================================
# Test: validate_data_consistency - Matching Checksums
# ==============================================================================

def test_validate_data_consistency_matching_checksums(integrity, mock_finlab_data_simple):
    """
    Test validate_data_consistency returns (True, "") for matching checksums.

    Requirement: 1.7.3 - Automated consistency checks
    """
    # Arrange
    expected_checksum = integrity.compute_dataset_checksum(mock_finlab_data_simple)

    # Act
    is_valid, error_msg = integrity.validate_data_consistency(
        mock_finlab_data_simple, expected_checksum
    )

    # Assert
    assert is_valid, "Matching checksums should validate successfully"
    assert error_msg == "", "No error message for matching checksums"


def test_validate_data_consistency_same_data_multiple_times(
    integrity, mock_finlab_data_simple
):
    """Test consistency validation across multiple validations."""
    # Arrange
    expected_checksum = integrity.compute_dataset_checksum(mock_finlab_data_simple)

    # Act - Validate multiple times
    results = [
        integrity.validate_data_consistency(mock_finlab_data_simple, expected_checksum)
        for _ in range(3)
    ]

    # Assert
    assert all(is_valid for is_valid, _ in results), \
        "All validations should pass for same data"
    assert all(error_msg == "" for _, error_msg in results), \
        "No error messages for valid data"


# ==============================================================================
# Test: validate_data_consistency - Mismatched Checksums
# ==============================================================================

def test_validate_data_consistency_mismatched_checksums(
    integrity, mock_finlab_data_simple, mock_finlab_data_modified
):
    """
    Test validate_data_consistency returns (False, error_message) for mismatched checksums.

    Requirement: 1.7.3 - Detect data corruption/drift
    """
    # Arrange - Get checksum from original data
    expected_checksum = integrity.compute_dataset_checksum(mock_finlab_data_simple)

    # Act - Validate with modified data
    is_valid, error_msg = integrity.validate_data_consistency(
        mock_finlab_data_modified, expected_checksum
    )

    # Assert
    assert not is_valid, "Mismatched checksums should fail validation"
    assert error_msg != "", "Should have error message for mismatch"
    assert "Data checksum mismatch" in error_msg, \
        "Error message should indicate mismatch"


def test_validate_data_consistency_error_message_format(
    integrity, mock_finlab_data_simple, mock_finlab_data_modified
):
    """Test error message includes both checksums for debugging."""
    # Arrange
    expected_checksum = integrity.compute_dataset_checksum(mock_finlab_data_simple)

    # Act
    is_valid, error_msg = integrity.validate_data_consistency(
        mock_finlab_data_modified, expected_checksum
    )

    # Assert
    assert "expected=" in error_msg, "Error should include expected checksum"
    assert "current=" in error_msg, "Error should include current checksum"
    assert expected_checksum[:16] in error_msg, \
        "Error should include first 16 chars of expected checksum"


def test_validate_data_consistency_detects_corruption(integrity, mock_finlab_data_simple):
    """Test validation detects data corruption."""
    # Arrange - Get initial checksum
    expected_checksum = integrity.compute_dataset_checksum(mock_finlab_data_simple)

    # Simulate data corruption by using wrong expected checksum
    corrupted_checksum = "a" * 64  # Different checksum

    # Act
    is_valid, error_msg = integrity.validate_data_consistency(
        mock_finlab_data_simple, corrupted_checksum
    )

    # Assert
    assert not is_valid, "Should detect data corruption"
    assert "mismatch" in error_msg.lower(), "Should indicate checksum mismatch"


# ==============================================================================
# Test: validate_data_consistency - No Expected Checksum
# ==============================================================================

def test_validate_data_consistency_no_expected_checksum(
    integrity, mock_finlab_data_simple
):
    """Test validation handles missing expected checksum."""
    # Act
    is_valid, error_msg = integrity.validate_data_consistency(
        mock_finlab_data_simple, None
    )

    # Assert
    assert not is_valid, "Should fail when no expected checksum provided"
    assert "No expected checksum provided" in error_msg


def test_validate_data_consistency_empty_expected_checksum(
    integrity, mock_finlab_data_simple
):
    """Test validation handles empty string expected checksum."""
    # Act
    is_valid, error_msg = integrity.validate_data_consistency(
        mock_finlab_data_simple, ""
    )

    # Assert
    assert not is_valid, "Should fail when expected checksum is empty string"
    assert "No expected checksum provided" in error_msg


# ==============================================================================
# Test: validate_data_consistency - None Data
# ==============================================================================

def test_validate_data_consistency_none_data_matches(integrity):
    """Test validation with None data matching empty checksum."""
    # Arrange
    empty_checksum = integrity.compute_dataset_checksum(None)

    # Act
    is_valid, error_msg = integrity.validate_data_consistency(None, empty_checksum)

    # Assert
    assert is_valid, "None data should match its empty checksum"
    assert error_msg == ""


def test_validate_data_consistency_none_data_mismatch(integrity, mock_finlab_data_simple):
    """Test validation detects None data vs. real data mismatch."""
    # Arrange - Get checksum from real data
    expected_checksum = integrity.compute_dataset_checksum(mock_finlab_data_simple)

    # Act - Validate None data against real data checksum
    is_valid, error_msg = integrity.validate_data_consistency(None, expected_checksum)

    # Assert
    assert not is_valid, "None data should not match real data checksum"
    assert "mismatch" in error_msg.lower()


# ==============================================================================
# Test: record_data_provenance - Required Fields
# ==============================================================================

def test_record_data_provenance_all_fields_present(integrity, mock_finlab_data_simple):
    """
    Test record_data_provenance returns all required fields.

    Requirement: 1.7.4 - Complete provenance for reproducibility
    """
    # Act
    provenance = integrity.record_data_provenance(mock_finlab_data_simple, iteration_num=5)

    # Assert - Check all required fields present
    required_fields = [
        'iteration_num',
        'dataset_checksum',
        'finlab_version',
        'data_pull_timestamp',
        'dataset_row_counts'
    ]
    for field in required_fields:
        assert field in provenance, f"Missing required field: {field}"


def test_record_data_provenance_field_types(integrity, mock_finlab_data_simple):
    """Test provenance fields have correct types."""
    # Act
    provenance = integrity.record_data_provenance(mock_finlab_data_simple, iteration_num=10)

    # Assert
    assert isinstance(provenance['iteration_num'], int), "iteration_num should be int"
    assert isinstance(provenance['dataset_checksum'], str), "checksum should be str"
    assert isinstance(provenance['finlab_version'], str), "version should be str"
    assert isinstance(provenance['data_pull_timestamp'], str), "timestamp should be str"
    assert isinstance(provenance['dataset_row_counts'], dict), "row_counts should be dict"


def test_record_data_provenance_iteration_number(integrity, mock_finlab_data_simple):
    """Test iteration_num is correctly recorded."""
    # Act
    provenance1 = integrity.record_data_provenance(mock_finlab_data_simple, iteration_num=5)
    provenance2 = integrity.record_data_provenance(mock_finlab_data_simple, iteration_num=10)

    # Assert
    assert provenance1['iteration_num'] == 5
    assert provenance2['iteration_num'] == 10


# ==============================================================================
# Test: record_data_provenance - Dataset Checksum
# ==============================================================================

def test_record_data_provenance_dataset_checksum(integrity, mock_finlab_data_simple):
    """Test dataset_checksum matches compute_dataset_checksum result."""
    # Arrange
    expected_checksum = integrity.compute_dataset_checksum(mock_finlab_data_simple)

    # Act
    provenance = integrity.record_data_provenance(mock_finlab_data_simple, iteration_num=1)

    # Assert
    assert provenance['dataset_checksum'] == expected_checksum, \
        "Provenance checksum should match computed checksum"
    assert len(provenance['dataset_checksum']) == 64, \
        "Checksum should be 64-character SHA-256"


# ==============================================================================
# Test: record_data_provenance - Finlab Version
# ==============================================================================

@patch('src.data.pipeline_integrity.finlab')
def test_record_data_provenance_finlab_version(mock_finlab, integrity, mock_finlab_data_simple):
    """Test finlab_version extraction from finlab module."""
    # Arrange
    mock_finlab.__version__ = "1.2.3"

    # Act
    provenance = integrity.record_data_provenance(mock_finlab_data_simple, iteration_num=1)

    # Assert
    assert provenance['finlab_version'] == "1.2.3", \
        "Should extract finlab version from module"


@patch('src.data.pipeline_integrity.finlab', side_effect=ImportError())
def test_record_data_provenance_finlab_version_unavailable(
    mock_finlab, integrity, mock_finlab_data_simple
):
    """Test finlab_version handling when finlab module unavailable."""
    # Act
    provenance = integrity.record_data_provenance(mock_finlab_data_simple, iteration_num=1)

    # Assert
    assert provenance['finlab_version'] == "unknown", \
        "Should use 'unknown' when finlab module unavailable"


# ==============================================================================
# Test: record_data_provenance - Timestamp
# ==============================================================================

def test_record_data_provenance_timestamp_format(integrity, mock_finlab_data_simple):
    """Test data_pull_timestamp is in ISO 8601 format."""
    # Act
    provenance = integrity.record_data_provenance(mock_finlab_data_simple, iteration_num=1)

    # Assert
    timestamp = provenance['data_pull_timestamp']
    # Should be parseable as ISO 8601
    parsed_time = datetime.fromisoformat(timestamp)
    assert isinstance(parsed_time, datetime), "Timestamp should be valid ISO 8601"


def test_record_data_provenance_timestamp_recent(integrity, mock_finlab_data_simple):
    """Test timestamp is recent (within last minute)."""
    # Arrange
    before_time = datetime.now()

    # Act
    provenance = integrity.record_data_provenance(mock_finlab_data_simple, iteration_num=1)

    # Arrange
    after_time = datetime.now()
    timestamp = datetime.fromisoformat(provenance['data_pull_timestamp'])

    # Assert
    assert before_time <= timestamp <= after_time, \
        "Timestamp should be between before and after times"


# ==============================================================================
# Test: record_data_provenance - Dataset Row Counts
# ==============================================================================

def test_record_data_provenance_dataset_row_counts(integrity, mock_finlab_data_simple):
    """Test dataset_row_counts extraction."""
    # Act
    provenance = integrity.record_data_provenance(mock_finlab_data_simple, iteration_num=1)

    # Assert
    row_counts = provenance['dataset_row_counts']

    # Check all tracked datasets present
    tracked_datasets = [
        'price:收盤價',
        'price:成交金額',
        'fundamental_features:ROE稅後'
    ]
    for dataset_key in tracked_datasets:
        assert dataset_key in row_counts, f"Missing row count for {dataset_key}"

    # Check row counts are integers or None
    for dataset_key, count in row_counts.items():
        assert count is None or isinstance(count, (int, np.integer)), \
            f"Row count for {dataset_key} should be int or None"


def test_record_data_provenance_row_counts_correct(integrity):
    """Test row counts match actual DataFrame shapes."""
    # Arrange - Create mock with known row counts
    mock_data = Mock()
    df1 = pd.DataFrame({'A': [1, 2, 3]})  # 3 rows
    df2 = pd.DataFrame({'B': [4, 5, 6, 7]})  # 4 rows
    df3 = pd.DataFrame({'C': [8, 9]})  # 2 rows

    def get_dataset(key):
        if key == 'price:收盤價':
            return df1
        elif key == 'price:成交金額':
            return df2
        elif key == 'fundamental_features:ROE稅後':
            return df3
        else:
            raise KeyError(f"Unknown dataset: {key}")

    mock_data.get = Mock(side_effect=get_dataset)

    # Act
    provenance = integrity.record_data_provenance(mock_data, iteration_num=1)

    # Assert
    assert provenance['dataset_row_counts']['price:收盤價'] == 3
    assert provenance['dataset_row_counts']['price:成交金額'] == 4
    assert provenance['dataset_row_counts']['fundamental_features:ROE稅後'] == 2


# ==============================================================================
# Test: record_data_provenance - None Data
# ==============================================================================

def test_record_data_provenance_none_data(integrity):
    """Test provenance recording with None data."""
    # Act
    provenance = integrity.record_data_provenance(None, iteration_num=0)

    # Assert
    assert provenance['iteration_num'] == 0
    assert provenance['dataset_checksum'].startswith('EMPTY_DATA_CHECKSUM_')
    assert provenance['finlab_version'] in ['unknown', '1.2.3']  # Depends on environment
    assert isinstance(provenance['data_pull_timestamp'], str)

    # All row counts should be None
    row_counts = provenance['dataset_row_counts']
    for dataset_key in row_counts:
        assert row_counts[dataset_key] is None, \
            "Row counts should be None for None data"


# ==============================================================================
# Test: record_data_provenance - Missing Datasets
# ==============================================================================

def test_record_data_provenance_missing_datasets(
    integrity, mock_finlab_data_missing_datasets
):
    """Test provenance recording with missing datasets."""
    # Act
    provenance = integrity.record_data_provenance(
        mock_finlab_data_missing_datasets, iteration_num=1
    )

    # Assert
    row_counts = provenance['dataset_row_counts']

    # First dataset should have row count
    assert row_counts['price:收盤價'] == 3, "Available dataset should have row count"

    # Missing datasets should have None
    assert row_counts['price:成交金額'] is None, \
        "Missing dataset should have None row count"
    assert row_counts['fundamental_features:ROE稅後'] is None, \
        "Missing dataset should have None row count"


# ==============================================================================
# Test: Integration and Edge Cases
# ==============================================================================

def test_full_integrity_workflow(integrity, mock_finlab_data_simple):
    """
    Test complete integrity workflow: compute checksum, record provenance, validate.

    Requirement: 1.7.1-1.7.4 - Full data integrity system
    """
    # Step 1: Compute initial checksum at load time
    initial_checksum = integrity.compute_dataset_checksum(mock_finlab_data_simple)

    # Step 2: Record provenance
    provenance = integrity.record_data_provenance(mock_finlab_data_simple, iteration_num=1)

    # Step 3: Validate consistency before iteration
    is_valid, error_msg = integrity.validate_data_consistency(
        mock_finlab_data_simple, initial_checksum
    )

    # Assert
    assert provenance['dataset_checksum'] == initial_checksum
    assert is_valid, f"Data should be consistent: {error_msg}"
    assert error_msg == ""


def test_integrity_detects_data_drift(
    integrity, mock_finlab_data_simple, mock_finlab_data_modified
):
    """Test integrity system detects data drift between iterations."""
    # Step 1: Record provenance at iteration 1
    provenance1 = integrity.record_data_provenance(mock_finlab_data_simple, iteration_num=1)

    # Step 2: Simulate data drift - validate with modified data
    is_valid, error_msg = integrity.validate_data_consistency(
        mock_finlab_data_modified, provenance1['dataset_checksum']
    )

    # Assert
    assert not is_valid, "Should detect data drift"
    assert "mismatch" in error_msg.lower()


def test_provenance_reproducibility(integrity, mock_finlab_data_simple):
    """Test provenance provides sufficient information for reproducibility."""
    # Act
    provenance = integrity.record_data_provenance(mock_finlab_data_simple, iteration_num=5)

    # Assert - All key reproducibility fields present
    assert provenance['iteration_num'] == 5, "Need iteration number"
    assert len(provenance['dataset_checksum']) == 64, "Need data fingerprint"
    assert provenance['finlab_version'], "Need library version"
    assert provenance['data_pull_timestamp'], "Need timestamp"
    assert provenance['dataset_row_counts'], "Need dataset shapes"


def test_empty_dataframe_handling(integrity):
    """Test handling of empty DataFrames."""
    # Arrange - Create mock with empty DataFrames
    mock_data = Mock()
    empty_df = pd.DataFrame()
    mock_data.get = Mock(return_value=empty_df)

    # Act
    checksum = integrity.compute_dataset_checksum(mock_data)
    provenance = integrity.record_data_provenance(mock_data, iteration_num=1)

    # Assert
    assert isinstance(checksum, str), "Should handle empty DataFrames"
    assert len(checksum) == 64, "Checksum should still be 64 chars"
    assert provenance['dataset_row_counts']['price:收盤價'] == 0, \
        "Empty DataFrame should have 0 rows (not None)"


def test_checksum_uniqueness_across_different_data(integrity):
    """Test checksums are unique across different data configurations."""
    # Arrange - Create 3 different mock data objects
    mock_data_list = []
    for i in range(3):
        mock_data = Mock()
        df = pd.DataFrame({'A': [i, i+1, i+2]})  # Different data for each
        mock_data.get = Mock(return_value=df)
        mock_data_list.append(mock_data)

    # Act
    checksums = [integrity.compute_dataset_checksum(d) for d in mock_data_list]

    # Assert
    assert len(set(checksums)) == 3, "All checksums should be unique"


def test_provenance_consistency_across_calls(integrity, mock_finlab_data_simple):
    """Test provenance checksum is consistent with compute_dataset_checksum."""
    # Act - Call both methods multiple times
    checksums = [integrity.compute_dataset_checksum(mock_finlab_data_simple) for _ in range(3)]
    provenances = [
        integrity.record_data_provenance(mock_finlab_data_simple, iteration_num=i)
        for i in range(3)
    ]

    # Assert
    # All direct checksums should match
    assert len(set(checksums)) == 1, "compute_dataset_checksum should be deterministic"

    # All provenance checksums should match direct checksums
    for provenance in provenances:
        assert provenance['dataset_checksum'] in checksums, \
            "Provenance checksum should match direct computation"
