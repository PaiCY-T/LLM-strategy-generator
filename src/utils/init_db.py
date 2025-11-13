"""
Database Schema Initialization for Finlab Backtesting Optimization System.

This module provides functionality to initialize the SQLite database schema
with all required tables and indexes for storing iteration history and
strategy versions.

Features:
    - Idempotent schema creation (safe to run multiple times)
    - Comprehensive indexes for query optimization
    - Foreign key constraints for data integrity
    - Automatic schema versioning support
    - Transaction-based initialization for atomicity

Tables:
    - strategies: Strategy code and version history
    - iterations: Backtest iteration results
    - metrics: Performance metrics per iteration
    - suggestions: AI improvement suggestions
    - trades: Individual trade records

Example:
    >>> from src.utils.init_db import initialize_database
    >>> db_path = Path("./storage/backtest.db")
    >>> initialize_database(db_path)
    >>> # Database is now ready for use
"""

import sqlite3
from pathlib import Path
from typing import Optional

from src.utils.exceptions import StorageError
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Schema version for future migrations
SCHEMA_VERSION = 1


def initialize_database(
    db_path: Path, force_recreate: bool = False
) -> None:
    """
    Initialize the SQLite database with required schema.

    Creates all tables and indexes needed for the backtesting system.
    This function is idempotent - safe to call multiple times.
    If force_recreate is True, drops all existing tables first.

    Args:
        db_path: Path to the SQLite database file
        force_recreate: If True, drop all tables before creating
                       (WARNING: destroys all data)

    Raises:
        StorageError: If database initialization fails

    Example:
        >>> db_path = Path("./storage/backtest.db")
        >>> initialize_database(db_path)
        >>> # Database ready for use
        >>>
        >>> # Force recreation (testing only)
        >>> initialize_database(db_path, force_recreate=True)
    """
    try:
        # Create parent directory if needed
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect to database
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys

        try:
            if force_recreate:
                logger.warning("Force recreating database schema")
                _drop_all_tables(conn)

            _create_tables(conn)
            _create_indexes(conn)
            _set_schema_version(conn, SCHEMA_VERSION)

            conn.commit()
            logger.info(
                f"Database initialized successfully at {db_path} "
                f"(schema version {SCHEMA_VERSION})"
            )

        except Exception as e:
            conn.rollback()
            raise StorageError(
                f"Failed to initialize database schema: {e}"
            ) from e
        finally:
            conn.close()

    except sqlite3.Error as e:
        raise StorageError(
            f"Database connection failed for {db_path}: {e}"
        ) from e


def _drop_all_tables(conn: sqlite3.Connection) -> None:
    """
    Drop all tables from the database.

    WARNING: This destroys all data. Only use for testing or migration.

    Args:
        conn: Active database connection
    """
    tables = ["trades", "suggestions", "metrics", "iterations", "strategies"]
    for table in tables:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    logger.debug("All tables dropped")


def _create_tables(conn: sqlite3.Connection) -> None:
    """
    Create all required tables if they don't exist.

    Args:
        conn: Active database connection
    """
    # Strategies table: stores strategy code and version history
    conn.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            strategy_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            parameters JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            parent_strategy_id TEXT,
            FOREIGN KEY (parent_strategy_id)
                REFERENCES strategies(strategy_id)
        )
    """)

    # Iterations table: stores backtest iteration results
    conn.execute("""
        CREATE TABLE IF NOT EXISTS iterations (
            iteration_id TEXT PRIMARY KEY,
            strategy_id TEXT NOT NULL,
            iteration_number INTEGER NOT NULL,
            code TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (strategy_id)
                REFERENCES strategies(strategy_id)
        )
    """)

    # Metrics table: stores performance metrics per iteration
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
            iteration_id TEXT NOT NULL,
            annualized_return REAL,
            sharpe_ratio REAL,
            max_drawdown REAL,
            win_rate REAL,
            total_trades INTEGER,
            FOREIGN KEY (iteration_id)
                REFERENCES iterations(iteration_id)
        )
    """)

    # Suggestions table: stores AI improvement suggestions
    conn.execute("""
        CREATE TABLE IF NOT EXISTS suggestions (
            suggestion_id INTEGER PRIMARY KEY AUTOINCREMENT,
            iteration_id TEXT NOT NULL,
            priority TEXT CHECK(priority IN ('high', 'medium', 'low')),
            description TEXT NOT NULL,
            specific_changes TEXT,
            expected_impact TEXT,
            rationale TEXT,
            learning_references JSON,
            FOREIGN KEY (iteration_id)
                REFERENCES iterations(iteration_id)
        )
    """)

    # Trades table: stores individual trade records
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            iteration_id TEXT NOT NULL,
            stock_code TEXT NOT NULL,
            entry_date DATE,
            exit_date DATE,
            entry_price REAL,
            exit_price REAL,
            position_size INTEGER,
            profit_loss REAL,
            FOREIGN KEY (iteration_id)
                REFERENCES iterations(iteration_id)
        )
    """)

    logger.debug("All tables created successfully")


def _create_indexes(conn: sqlite3.Connection) -> None:
    """
    Create indexes for query optimization.

    Args:
        conn: Active database connection
    """
    indexes = [
        (
            "idx_iterations_strategy",
            "CREATE INDEX IF NOT EXISTS idx_iterations_strategy "
            "ON iterations(strategy_id)"
        ),
        (
            "idx_metrics_iteration",
            "CREATE INDEX IF NOT EXISTS idx_metrics_iteration "
            "ON metrics(iteration_id)"
        ),
        (
            "idx_suggestions_iteration",
            "CREATE INDEX IF NOT EXISTS idx_suggestions_iteration "
            "ON suggestions(iteration_id)"
        ),
        (
            "idx_trades_iteration",
            "CREATE INDEX IF NOT EXISTS idx_trades_iteration "
            "ON trades(iteration_id)"
        ),
        (
            "idx_strategies_parent",
            "CREATE INDEX IF NOT EXISTS idx_strategies_parent "
            "ON strategies(parent_strategy_id)"
        ),
    ]

    for index_name, create_sql in indexes:
        conn.execute(create_sql)
        logger.debug(f"Index {index_name} created")

    logger.debug("All indexes created successfully")


def _set_schema_version(
    conn: sqlite3.Connection, version: int
) -> None:
    """
    Store schema version in database for future migrations.

    Args:
        conn: Active database connection
        version: Schema version number
    """
    # Create schema_version table if it doesn't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert or update version
    conn.execute(
        "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
        (version,)
    )
    logger.debug(f"Schema version set to {version}")


def get_schema_version(db_path: Path) -> Optional[int]:
    """
    Retrieve the current schema version from the database.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        Current schema version, or None if not set

    Raises:
        StorageError: If database query fails

    Example:
        >>> db_path = Path("./storage/backtest.db")
        >>> version = get_schema_version(db_path)
        >>> print(f"Schema version: {version}")
    """
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.execute(
                "SELECT version FROM schema_version LIMIT 1"
            )
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    except sqlite3.OperationalError:
        # Table doesn't exist
        return None
    except sqlite3.Error as e:
        raise StorageError(
            f"Failed to query schema version: {e}"
        ) from e
