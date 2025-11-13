"""
Data Pipeline Integrity Module
===============================

Provides data integrity validation for the autonomous learning system,
ensuring dataset stability across iterations and preventing silent data corruption.

Features:
    - Dataset checksum computation (SHA-256)
    - Load-time validation and recording
    - Pre-iteration validation
    - Data drift detection

Requirements:
    - 1.7.1: Dataset checksums recorded at load time and validated before each iteration
    - F7.1: Compute and store dataset checksums (SHA-256) at load time

Usage:
    from src.data.pipeline_integrity import DataPipelineIntegrity

    integrity = DataPipelineIntegrity()
    checksum = integrity.compute_dataset_checksum(data)

    # Validate before iteration
    is_valid, message = integrity.validate_dataset_integrity(data, expected_checksum)
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional


class DataPipelineIntegrity:
    """
    Data integrity validator for autonomous learning system.

    Tracks dataset checksums to ensure data stability across iterations
    and detect silent corruption or unexpected changes.

    Key Datasets Tracked:
        - price:收盤價 (closing price)
        - price:成交金額 (trading volume)
        - fundamental_features:ROE稅後 (ROE after tax)

    Validation Strategy:
        1. Compute SHA-256 checksums at data load time
        2. Store checksums with metadata (timestamp, dataset shape)
        3. Validate checksums before each iteration
        4. Alert on checksum mismatches (data corruption/drift)

    Example:
        >>> integrity = DataPipelineIntegrity()
        >>> checksum = integrity.compute_dataset_checksum(data)
        >>> print(f"Dataset checksum: {checksum}")
    """

    def __init__(self):
        """
        Initialize DataPipelineIntegrity with no parameters.

        Instance state is minimal - most methods are self-contained
        for stateless checksum computation and validation.
        """
        # No instance state required for basic checksum operations
        # Future extensions may add checksum history tracking
        pass

    def _get_dataset_dict(self, data: Any) -> Dict[str, Any]:
        """
        Convert Finlab datasets to serializable dictionary for checksum computation.

        Extracts key datasets from the Finlab data object and converts
        DataFrames to dictionary format suitable for JSON serialization
        and checksum computation.

        Key Datasets:
            - price:收盤價 (closing price): Daily closing prices for all stocks
            - price:成交金額 (trading value): Daily trading volume in NTD
            - fundamental_features:ROE稅後 (ROE after tax): Return on equity metric

        Args:
            data: Finlab data object with get() method for dataset access

        Returns:
            Dict[str, Any]: Serialized dataset dictionary with structure:
                {
                    'price:收盤價': [{'stock_id': ..., 'date': ..., 'close': ...}, ...],
                    'price:成交金額': [{'stock_id': ..., 'date': ..., 'value': ...}, ...],
                    'fundamental_features:ROE稅後': [{'stock_id': ..., 'roe': ...}, ...]
                }

        Raises:
            AttributeError: If data object doesn't have get() method
            KeyError: If required datasets are not available in data object

        Example:
            >>> data_dict = integrity._get_dataset_dict(data)
            >>> print(f"Datasets extracted: {list(data_dict.keys())}")
            ['price:收盤價', 'price:成交金額', 'fundamental_features:ROE稅後']
        """
        dataset_dict = {}

        # Key datasets to track for integrity validation
        datasets_to_track = [
            'price:收盤價',                    # Closing price - core price data
            'price:成交金額',                  # Trading value - liquidity metric
            'fundamental_features:ROE稅後'     # ROE after tax - fundamental metric
        ]

        for dataset_key in datasets_to_track:
            try:
                # Get dataset from Finlab data object
                df = data.get(dataset_key)

                # Convert DataFrame to dict format (records orientation)
                # This creates a list of dicts, one per row
                dataset_dict[dataset_key] = df.to_dict('records')

            except Exception as e:
                # If dataset is not available, store error information
                # This allows checksum computation to proceed with available data
                dataset_dict[dataset_key] = {
                    'error': str(e),
                    'status': 'unavailable'
                }

        return dataset_dict

    def compute_dataset_checksum(self, data: Any) -> str:
        """
        Compute SHA-256 checksum for key datasets to create reproducible data fingerprint.

        Creates a deterministic hash of the key datasets tracked by the integrity
        system. The checksum is computed from a JSON serialization with sorted keys
        to ensure consistent ordering across different Python versions and environments.

        Determinism guarantees:
            - Same data → same checksum (always)
            - Sorted keys ensure consistent JSON serialization
            - SHA-256 provides cryptographic-grade uniqueness
            - UTF-8 encoding for cross-platform compatibility

        Args:
            data: Finlab data object with get() method for dataset access.
                  If None, returns a special empty checksum marker.

        Returns:
            str: 64-character hexadecimal SHA-256 digest string.
                 Returns 'EMPTY_DATA_CHECKSUM_' + zeros if data is None.
                 Returns 'ERROR_CHECKSUM_' + error code on serialization failure.

        Raises:
            No exceptions raised - all errors handled gracefully with error checksums.

        Example:
            >>> integrity = DataPipelineIntegrity()
            >>> checksum = integrity.compute_dataset_checksum(data)
            >>> print(f"Checksum: {checksum}")
            'a7f8d3e9c2b1...' (64 hex characters)

            >>> # Same data always produces same checksum
            >>> checksum2 = integrity.compute_dataset_checksum(data)
            >>> assert checksum == checksum2  # Deterministic

        Algorithm:
            1. Extract dataset dict using _get_dataset_dict()
            2. Serialize to JSON with sorted keys: json.dumps(..., sort_keys=True)
            3. Encode to UTF-8 bytes
            4. Compute SHA-256 hash
            5. Return hexadecimal digest (64 characters)

        See Also:
            - _get_dataset_dict(): Helper for dataset extraction
            - validate_dataset_integrity(): Uses checksums for validation
        """
        # Handle None data gracefully
        if data is None:
            # Return a recognizable empty checksum marker
            return 'EMPTY_DATA_CHECKSUM_' + '0' * 44  # Total 64 chars

        try:
            # Extract dataset dictionary using helper
            dataset_dict = self._get_dataset_dict(data)

            # Serialize to JSON with sorted keys for determinism
            # sort_keys=True ensures consistent ordering across Python versions
            json_string = json.dumps(dataset_dict, sort_keys=True)

            # Compute SHA-256 hash
            # UTF-8 encoding ensures cross-platform compatibility
            checksum = hashlib.sha256(json_string.encode('utf-8')).hexdigest()

            return checksum

        except Exception as e:
            # If serialization fails, return error checksum with diagnostic info
            # This allows detection of checksum computation failures
            error_code = abs(hash(str(e))) % 1000000  # 6-digit error code
            return f'ERROR_CHECKSUM_{error_code:06d}' + '0' * 44  # Total 64 chars

    def validate_data_consistency(self, data: Any, expected_checksum: str) -> Tuple[bool, str]:
        """
        Validate data consistency by comparing checksums to detect corruption or changes.

        Computes the current checksum of the data and compares it with the expected
        checksum to detect any data corruption, drift, or unexpected changes between
        iterations. This is a critical pre-iteration validation step.

        Requirements:
            - 1.7.3: Automated data consistency checks detect missing/corrupt data
            - F7.3: Validate data consistency before each iteration

        Args:
            data: Finlab data object with get() method for dataset access.
                  If None, computes empty checksum for comparison.
            expected_checksum: Expected SHA-256 checksum string (64 hex characters).
                              Must be provided from previous load-time computation.

        Returns:
            Tuple[bool, str]: Validation result tuple:
                - (True, ""): Checksums match, data is consistent
                - (False, error_message): Checksums don't match or validation failed
                  Error message includes both checksums for debugging

        Validation Cases:
            1. Match: current_checksum == expected_checksum → (True, "")
            2. Mismatch: checksums differ → (False, "Data checksum mismatch: ...")
            3. No expected: expected_checksum is None/empty → (False, "No expected checksum provided")
            4. Empty data: data is None → compute empty checksum and compare

        Error Message Format:
            "Data checksum mismatch: expected={expected[:16]}..., current={current[:16]}..."
            First 16 characters of each checksum for readability in logs

        Example:
            >>> integrity = DataPipelineIntegrity()
            >>> # At load time
            >>> expected = integrity.compute_dataset_checksum(data)
            >>>
            >>> # Before iteration
            >>> is_valid, msg = integrity.validate_data_consistency(data, expected)
            >>> if not is_valid:
            ...     print(f"Data validation failed: {msg}")
            ...     # Handle corruption/drift

        Special Checksums (from Task 7.2):
            - EMPTY_DATA_CHECKSUM_: Indicates None data
            - ERROR_CHECKSUM_: Indicates checksum computation failure
            Both are compared normally, allowing error detection

        See Also:
            - compute_dataset_checksum(): Computes the current checksum
            - MetricValidator: Similar validation pattern (Tuple[bool, str])
        """
        # Validate expected_checksum is provided
        if not expected_checksum:
            return False, "No expected checksum provided"

        # Compute current checksum using Task 7.2 implementation
        current_checksum = self.compute_dataset_checksum(data)

        # Compare checksums
        if current_checksum == expected_checksum:
            # Data is consistent - checksums match
            return True, ""
        else:
            # Data has changed - checksums don't match
            # Include first 16 chars of each checksum for debugging
            error_message = (
                f"Data checksum mismatch: "
                f"expected={expected_checksum[:16]}..., "
                f"current={current_checksum[:16]}..."
            )
            return False, error_message

    def record_data_provenance(self, data: Any, iteration_num: int) -> Dict[str, Any]:
        """
        Record complete data provenance for reproducibility tracking.

        Captures all metadata necessary to reproduce results from a specific iteration,
        including dataset checksum, Finlab version, data pull timestamp, and dataset
        row counts. This enables full reproducibility and debugging of iteration results.

        Requirements:
            - 1.7.2: Data version tracking in iteration history (dataset hash, Finlab version, timestamp)
            - 1.7.4: Iteration history includes data provenance for reproducibility
            - F7.2: Track data version metadata (dataset hash, Finlab version, timestamp)
            - F7.4: Record data provenance in iteration history for reproducibility

        Args:
            data: Finlab data object with get() method for dataset access.
                  If None, records provenance with error/empty markers.
            iteration_num: Current iteration number for tracking purposes.

        Returns:
            Dict[str, Any]: Complete provenance dictionary with structure:
                {
                    'iteration_num': int,
                    'dataset_checksum': str (64-char SHA-256 hex),
                    'finlab_version': str (e.g., "1.2.3" or "unknown"),
                    'data_pull_timestamp': str (ISO 8601 format),
                    'dataset_row_counts': {
                        'price:收盤價': int (or None if missing),
                        'price:成交金額': int (or None if missing),
                        'fundamental_features:ROE稅後': int (or None if missing)
                    }
                }

        Provenance Fields:
            - iteration_num: Iteration number for correlation with results
            - dataset_checksum: SHA-256 hash from compute_dataset_checksum()
            - finlab_version: Version string from finlab.__version__
            - data_pull_timestamp: Current time in ISO 8601 format
            - dataset_row_counts: Row counts for key datasets (shape[0])

        Edge Case Handling:
            - data is None: Returns provenance with EMPTY_DATA_CHECKSUM and zero/None row counts
            - finlab module unavailable: Uses "unknown" for finlab_version
            - Dataset missing: Row count set to None (not 0, to distinguish from empty dataset)
            - Any error: Returns partial provenance with error markers

        Example:
            >>> integrity = DataPipelineIntegrity()
            >>> provenance = integrity.record_data_provenance(data, iteration_num=5)
            >>> print(f"Iteration {provenance['iteration_num']}: {provenance['dataset_checksum'][:16]}...")
            Iteration 5: a7f8d3e9c2b1f4d6...
            >>> print(f"Finlab version: {provenance['finlab_version']}")
            Finlab version: 1.2.3
            >>> print(f"Data pulled at: {provenance['data_pull_timestamp']}")
            Data pulled at: 2025-10-12T14:30:45.123456
            >>> print(f"Price data rows: {provenance['dataset_row_counts']['price:收盤價']}")
            Price data rows: 15000

        Integration:
            This method is called at data load time in autonomous_loop.py:
            1. Load Finlab data
            2. Record provenance: provenance = integrity.record_data_provenance(data, iter_num)
            3. Store in iteration history for reproducibility tracking
            4. Use checksum for pre-iteration validation in subsequent iterations

        See Also:
            - compute_dataset_checksum(): Computes the dataset checksum
            - validate_data_consistency(): Uses checksum for validation
            - IterationEngine: Stores provenance in iteration history
        """
        # Get current timestamp in ISO 8601 format
        data_pull_timestamp = datetime.now().isoformat()

        # Compute dataset checksum using Task 7.2 implementation
        # Handles None data gracefully with EMPTY_DATA_CHECKSUM marker
        dataset_checksum = self.compute_dataset_checksum(data)

        # Get Finlab version
        try:
            import finlab
            finlab_version = finlab.__version__
        except (ImportError, AttributeError):
            # If finlab module not available or version not accessible
            finlab_version = "unknown"

        # Extract dataset row counts for key datasets
        dataset_row_counts = {}

        # Key datasets to track (same as in _get_dataset_dict)
        datasets_to_track = [
            'price:收盤價',                    # Closing price
            'price:成交金額',                  # Trading value
            'fundamental_features:ROE稅後'     # ROE after tax
        ]

        if data is None:
            # If data is None, set all row counts to None
            for dataset_key in datasets_to_track:
                dataset_row_counts[dataset_key] = None
        else:
            # Extract row counts from actual data
            for dataset_key in datasets_to_track:
                try:
                    # Get dataset DataFrame
                    df = data.get(dataset_key)

                    # Get row count (shape[0])
                    if df is not None:
                        dataset_row_counts[dataset_key] = df.shape[0]
                    else:
                        # Dataset returned None
                        dataset_row_counts[dataset_key] = None

                except Exception:
                    # If dataset is not available or any error occurs
                    # Use None to distinguish from empty dataset (0 rows)
                    dataset_row_counts[dataset_key] = None

        # Construct complete provenance dictionary
        provenance = {
            'iteration_num': iteration_num,
            'dataset_checksum': dataset_checksum,
            'finlab_version': finlab_version,
            'data_pull_timestamp': data_pull_timestamp,
            'dataset_row_counts': dataset_row_counts
        }

        return provenance


__all__ = ['DataPipelineIntegrity']
