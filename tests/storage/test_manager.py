"""
Unit tests for StorageManager with in-memory SQLite.

Tests cover:
    - Strategy version saving and loading
    - Iteration saving with metrics, trades, suggestions
    - Connection pooling behavior
    - Export/import functionality
    - Error handling and edge cases
    - Thread safety of connection pool

Uses in-memory SQLite (:memory:) for fast, isolated tests.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

from src.storage.manager import StorageManager
from src.utils.exceptions import StorageError


@pytest.fixture
def temp_db_path() -> Path:
    """
    Create temporary database path for testing.

    Returns:
        Path to temporary database file
    """
    with tempfile.NamedTemporaryFile(
        suffix=".db", delete=False
    ) as f:
        return Path(f.name)


@pytest.fixture
def manager(temp_db_path: Path) -> StorageManager:
    """
    Create StorageManager instance for testing.

    Args:
        temp_db_path: Path to temporary database

    Returns:
        Initialized StorageManager

    Yields:
        StorageManager instance
    """
    mgr = StorageManager(temp_db_path, pool_size=3)
    yield mgr
    mgr.close()
    # Clean up temp file
    if temp_db_path.exists():
        temp_db_path.unlink()


@pytest.fixture
def sample_strategy() -> Dict[str, Any]:
    """
    Create sample strategy data for testing.

    Returns:
        Dictionary with strategy data
    """
    return {
        "name": "Test Strategy",
        "code": "# Test strategy code\npass",
        "parameters": {"fast": 5, "slow": 20, "threshold": 0.02},
    }


@pytest.fixture
def sample_iteration_data() -> Dict[str, Any]:
    """
    Create sample iteration data for testing.

    Returns:
        Dictionary with iteration data
    """
    return {
        "code": "# Iteration code\npass",
        "metrics": {
            "annualized_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.10,
            "win_rate": 0.55,
            "total_trades": 100,
        },
        "trades": [
            {
                "stock_code": "2330",
                "entry_date": "2024-01-01",
                "exit_date": "2024-01-15",
                "entry_price": 500.0,
                "exit_price": 520.0,
                "position_size": 1000,
                "profit_loss": 20000.0,
            },
            {
                "stock_code": "2317",
                "entry_date": "2024-01-05",
                "exit_date": "2024-01-20",
                "entry_price": 100.0,
                "exit_price": 95.0,
                "position_size": 500,
                "profit_loss": -2500.0,
            },
        ],
        "suggestions": [
            {
                "priority": "high",
                "description": "Improve entry logic",
                "specific_changes": "Add volume filter",
                "expected_impact": "Reduce false signals",
                "rationale": "Volume confirms price movement",
                "learning_references": [
                    "Volume analysis techniques",
                    "Price-volume relationship"
                ],
            },
            {
                "priority": "medium",
                "description": "Optimize position sizing",
                "specific_changes": None,
                "expected_impact": None,
                "rationale": None,
                "learning_references": None,
            },
        ],
    }


class TestStorageManagerInitialization:
    """Test StorageManager initialization and setup."""

    def test_init_creates_database(self, temp_db_path: Path) -> None:
        """Test that initialization creates database file."""
        assert not temp_db_path.exists()

        manager = StorageManager(temp_db_path)
        try:
            assert temp_db_path.exists()
        finally:
            manager.close()

    def test_init_with_pool_size(self, temp_db_path: Path) -> None:
        """Test initialization with custom pool size."""
        manager = StorageManager(temp_db_path, pool_size=7)
        try:
            assert manager.pool_size == 7
        finally:
            manager.close()

    def test_close_multiple_times(self, manager: StorageManager) -> None:
        """Test that close() can be called multiple times safely."""
        manager.close()
        manager.close()  # Should not raise


class TestStrategyVersionManagement:
    """Test strategy version saving and retrieval."""

    def test_save_strategy_version_basic(
        self, manager: StorageManager, sample_strategy: Dict[str, Any]
    ) -> None:
        """Test saving a basic strategy version."""
        strategy_id = manager.save_strategy_version(
            name=sample_strategy["name"],
            code=sample_strategy["code"],
        )

        assert strategy_id is not None
        assert isinstance(strategy_id, str)
        assert len(strategy_id) == 36  # UUID format

    def test_save_strategy_version_with_parameters(
        self, manager: StorageManager, sample_strategy: Dict[str, Any]
    ) -> None:
        """Test saving strategy with parameters."""
        strategy_id = manager.save_strategy_version(
            name=sample_strategy["name"],
            code=sample_strategy["code"],
            parameters=sample_strategy["parameters"],
        )

        assert strategy_id is not None

    def test_save_strategy_version_with_parent(
        self, manager: StorageManager, sample_strategy: Dict[str, Any]
    ) -> None:
        """Test saving strategy with parent reference."""
        # Save parent strategy
        parent_id = manager.save_strategy_version(
            name="Parent Strategy",
            code="# Parent code",
        )

        # Save child strategy
        child_id = manager.save_strategy_version(
            name=sample_strategy["name"],
            code=sample_strategy["code"],
            parent_strategy_id=parent_id,
        )

        assert child_id is not None
        assert child_id != parent_id

    def test_save_multiple_strategies(
        self, manager: StorageManager
    ) -> None:
        """Test saving multiple strategies."""
        ids = []
        for i in range(5):
            strategy_id = manager.save_strategy_version(
                name=f"Strategy {i}",
                code=f"# Code {i}",
            )
            ids.append(strategy_id)

        # All IDs should be unique
        assert len(ids) == len(set(ids))


class TestIterationManagement:
    """Test iteration saving and loading."""

    def test_save_iteration_complete(
        self,
        manager: StorageManager,
        sample_strategy: Dict[str, Any],
        sample_iteration_data: Dict[str, Any],
    ) -> None:
        """Test saving a complete iteration with all data."""
        # First save strategy
        strategy_id = manager.save_strategy_version(
            name=sample_strategy["name"],
            code=sample_strategy["code"],
        )

        # Save iteration
        iteration_id = manager.save_iteration(
            strategy_id=strategy_id,
            iteration_number=1,
            **sample_iteration_data,
        )

        assert iteration_id is not None
        assert isinstance(iteration_id, str)

    def test_save_multiple_iterations(
        self,
        manager: StorageManager,
        sample_strategy: Dict[str, Any],
        sample_iteration_data: Dict[str, Any],
    ) -> None:
        """Test saving multiple iterations for same strategy."""
        strategy_id = manager.save_strategy_version(
            name=sample_strategy["name"],
            code=sample_strategy["code"],
        )

        iteration_ids = []
        for i in range(3):
            iteration_id = manager.save_iteration(
                strategy_id=strategy_id,
                iteration_number=i + 1,
                **sample_iteration_data,
            )
            iteration_ids.append(iteration_id)

        # All IDs should be unique
        assert len(iteration_ids) == len(set(iteration_ids))

    def test_load_iteration_complete(
        self,
        manager: StorageManager,
        sample_strategy: Dict[str, Any],
        sample_iteration_data: Dict[str, Any],
    ) -> None:
        """Test loading a complete iteration."""
        # Save strategy and iteration
        strategy_id = manager.save_strategy_version(
            name=sample_strategy["name"],
            code=sample_strategy["code"],
        )
        iteration_id = manager.save_iteration(
            strategy_id=strategy_id,
            iteration_number=1,
            **sample_iteration_data,
        )

        # Load iteration
        loaded = manager.load_iteration(iteration_id)

        # Verify basic fields
        assert loaded["iteration_id"] == iteration_id
        assert loaded["strategy_id"] == strategy_id
        assert loaded["iteration_number"] == 1
        assert loaded["code"] == sample_iteration_data["code"]

        # Verify metrics
        assert loaded["metrics"]["annualized_return"] == 0.15
        assert loaded["metrics"]["sharpe_ratio"] == 1.2

        # Verify trades
        assert len(loaded["trades"]) == 2
        assert loaded["trades"][0]["stock_code"] == "2330"

        # Verify suggestions
        assert len(loaded["suggestions"]) == 2
        assert loaded["suggestions"][0]["priority"] == "high"
        assert loaded["suggestions"][0]["learning_references"] == [
            "Volume analysis techniques",
            "Price-volume relationship"
        ]

    def test_load_nonexistent_iteration(
        self, manager: StorageManager
    ) -> None:
        """Test loading iteration that doesn't exist."""
        with pytest.raises(StorageError) as exc_info:
            manager.load_iteration("nonexistent-id")

        assert "not found" in str(exc_info.value).lower()

    def test_load_strategy_history(
        self,
        manager: StorageManager,
        sample_strategy: Dict[str, Any],
        sample_iteration_data: Dict[str, Any],
    ) -> None:
        """Test loading all iterations for a strategy."""
        strategy_id = manager.save_strategy_version(
            name=sample_strategy["name"],
            code=sample_strategy["code"],
        )

        # Save 3 iterations
        for i in range(3):
            manager.save_iteration(
                strategy_id=strategy_id,
                iteration_number=i + 1,
                **sample_iteration_data,
            )

        # Load history
        history = manager.load_strategy_history(strategy_id)

        assert len(history) == 3
        assert history[0]["iteration_number"] == 1
        assert history[1]["iteration_number"] == 2
        assert history[2]["iteration_number"] == 3


class TestExportImport:
    """Test export and import functionality."""

    def test_export_single_iteration(
        self,
        manager: StorageManager,
        sample_strategy: Dict[str, Any],
        sample_iteration_data: Dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Test exporting a single iteration to JSON."""
        # Save data
        strategy_id = manager.save_strategy_version(
            name=sample_strategy["name"],
            code=sample_strategy["code"],
        )
        iteration_id = manager.save_iteration(
            strategy_id=strategy_id,
            iteration_number=1,
            **sample_iteration_data,
        )

        # Export
        output_path = tmp_path / "export.json"
        manager.export_results(
            iteration_ids=[iteration_id],
            output_path=output_path,
        )

        # Verify file exists and contains valid JSON
        assert output_path.exists()
        with output_path.open("r") as f:
            data = json.load(f)

        assert data["iteration_count"] == 1
        assert len(data["iterations"]) == 1

    def test_export_multiple_iterations(
        self,
        manager: StorageManager,
        sample_strategy: Dict[str, Any],
        sample_iteration_data: Dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Test exporting multiple iterations."""
        strategy_id = manager.save_strategy_version(
            name=sample_strategy["name"],
            code=sample_strategy["code"],
        )

        iteration_ids = []
        for i in range(3):
            iteration_id = manager.save_iteration(
                strategy_id=strategy_id,
                iteration_number=i + 1,
                **sample_iteration_data,
            )
            iteration_ids.append(iteration_id)

        # Export all
        output_path = tmp_path / "export.json"
        manager.export_results(
            iteration_ids=iteration_ids,
            output_path=output_path,
        )

        # Verify
        with output_path.open("r") as f:
            data = json.load(f)

        assert data["iteration_count"] == 3

    def test_export_invalid_format(
        self,
        manager: StorageManager,
        tmp_path: Path,
    ) -> None:
        """Test export with invalid format."""
        output_path = tmp_path / "export.xml"
        with pytest.raises(ValueError) as exc_info:
            manager.export_results(
                iteration_ids=[],
                output_path=output_path,
                format="xml",
            )

        assert "unsupported" in str(exc_info.value).lower()

    def test_import_results(
        self,
        manager: StorageManager,
        sample_strategy: Dict[str, Any],
        sample_iteration_data: Dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Test importing results from JSON file."""
        # First export some data
        strategy_id = manager.save_strategy_version(
            name=sample_strategy["name"],
            code=sample_strategy["code"],
        )
        iteration_id = manager.save_iteration(
            strategy_id=strategy_id,
            iteration_number=1,
            **sample_iteration_data,
        )

        export_path = tmp_path / "export.json"
        manager.export_results(
            iteration_ids=[iteration_id],
            output_path=export_path,
        )

        # Import into new manager
        import_db = tmp_path / "import.db"
        import_manager = StorageManager(import_db)
        try:
            imported_ids = import_manager.import_results(export_path)

            assert len(imported_ids) == 1
            # Note: imported IDs will be different (new UUIDs)
            assert imported_ids[0] != iteration_id

            # Verify data was imported correctly
            loaded = import_manager.load_iteration(imported_ids[0])
            assert loaded["metrics"]["sharpe_ratio"] == 1.2

        finally:
            import_manager.close()


class TestConnectionPooling:
    """Test connection pooling behavior."""

    def test_connection_pool_reuse(
        self,
        manager: StorageManager,
        sample_strategy: Dict[str, Any],
    ) -> None:
        """Test that connections are reused from pool."""
        # Perform multiple operations
        for i in range(10):
            manager.save_strategy_version(
                name=f"Strategy {i}",
                code="# Code",
            )

        # Should complete without exhausting pool

    def test_connection_pool_concurrent_access(
        self,
        manager: StorageManager,
        sample_strategy: Dict[str, Any],
    ) -> None:
        """Test concurrent access to connection pool."""
        import threading

        results: List[str] = []
        errors: List[Exception] = []

        def save_strategy(index: int) -> None:
            try:
                strategy_id = manager.save_strategy_version(
                    name=f"Strategy {index}",
                    code="# Code",
                )
                results.append(strategy_id)
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=save_strategy, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify all succeeded
        assert len(errors) == 0
        assert len(results) == 10

    def test_closed_manager_raises_error(
        self, manager: StorageManager
    ) -> None:
        """Test that using closed manager raises error."""
        manager.close()

        with pytest.raises(StorageError) as exc_info:
            manager.save_strategy_version(
                name="Test",
                code="# Code",
            )

        assert "closed" in str(exc_info.value).lower()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_trades_list(
        self,
        manager: StorageManager,
        sample_strategy: Dict[str, Any],
        sample_iteration_data: Dict[str, Any],
    ) -> None:
        """Test saving iteration with empty trades list."""
        strategy_id = manager.save_strategy_version(
            name=sample_strategy["name"],
            code=sample_strategy["code"],
        )

        # Modify to have empty trades
        data = sample_iteration_data.copy()
        data["trades"] = []

        iteration_id = manager.save_iteration(
            strategy_id=strategy_id,
            iteration_number=1,
            **data,
        )

        # Load and verify
        loaded = manager.load_iteration(iteration_id)
        assert len(loaded["trades"]) == 0

    def test_empty_suggestions_list(
        self,
        manager: StorageManager,
        sample_strategy: Dict[str, Any],
        sample_iteration_data: Dict[str, Any],
    ) -> None:
        """Test saving iteration with empty suggestions."""
        strategy_id = manager.save_strategy_version(
            name=sample_strategy["name"],
            code=sample_strategy["code"],
        )

        data = sample_iteration_data.copy()
        data["suggestions"] = []

        iteration_id = manager.save_iteration(
            strategy_id=strategy_id,
            iteration_number=1,
            **data,
        )

        loaded = manager.load_iteration(iteration_id)
        assert len(loaded["suggestions"]) == 0

    def test_none_parameters(
        self, manager: StorageManager
    ) -> None:
        """Test saving strategy with None parameters."""
        strategy_id = manager.save_strategy_version(
            name="Test",
            code="# Code",
            parameters=None,
        )

        assert strategy_id is not None

    def test_unicode_content(
        self, manager: StorageManager
    ) -> None:
        """Test handling of Unicode/Chinese characters."""
        strategy_id = manager.save_strategy_version(
            name="測試策略",  # Chinese: Test Strategy
            code="# 中文註解\npass",  # Chinese comment
            parameters={"名稱": "數值"},  # Chinese keys
        )

        assert strategy_id is not None
