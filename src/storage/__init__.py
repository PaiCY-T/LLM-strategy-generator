"""
Storage Layer for Finlab Backtesting Optimization System.

This module provides persistent storage for iteration history and strategy
versions using SQLite database with connection pooling and automatic backups.

Components:
    - StorageManager: Main interface for database operations
    - BackupScheduler: Automatic backup management
    - Connection pooling: Thread-safe connection management

Features:
    - Strategy version management with history tracking
    - Iteration result persistence with metrics and trades
    - Thread-safe connection pooling (5 connections)
    - Automatic daily backups with 30-day retention
    - JSON export/import for portability
    - ACID transaction guarantees

Example:
    >>> from src.storage import StorageManager
    >>> from pathlib import Path
    >>>
    >>> # Initialize storage
    >>> db_path = Path("./storage/backtest.db")
    >>> manager = StorageManager(db_path)
    >>>
    >>> # Save strategy version
    >>> strategy_id = manager.save_strategy_version(
    ...     name="Moving Average Crossover",
    ...     code="# Strategy code here",
    ...     parameters={"fast": 5, "slow": 20}
    ... )
    >>>
    >>> # Save iteration results
    >>> iteration_id = manager.save_iteration(
    ...     strategy_id=strategy_id,
    ...     iteration_number=1,
    ...     code="# Iteration code",
    ...     metrics={
    ...         "annualized_return": 0.15,
    ...         "sharpe_ratio": 1.2,
    ...         "max_drawdown": -0.10,
    ...         "win_rate": 0.55,
    ...         "total_trades": 100
    ...     },
    ...     trades=[...],
    ...     suggestions=[...]
    ... )
    >>>
    >>> # Load iteration
    >>> iteration = manager.load_iteration(iteration_id)
    >>>
    >>> # Export results
    >>> manager.export_results(
    ...     iteration_ids=[iteration_id],
    ...     output_path=Path("./results.json")
    ... )
    >>>
    >>> # Close connections (important!)
    >>> manager.close()
"""

# Import actual implementation
from src.storage.manager import StorageManager  # noqa: F401
from src.storage.backup import BackupScheduler  # noqa: F401

__all__ = ["StorageManager", "BackupScheduler"]
