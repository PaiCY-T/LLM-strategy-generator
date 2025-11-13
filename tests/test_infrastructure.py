"""
Infrastructure tests to verify test setup is working correctly.

These tests verify that pytest, fixtures, and the test environment
are configured properly.
"""

import logging
from pathlib import Path

import pytest


@pytest.mark.unit
def test_tmp_path_fixture(tmp_path: Path) -> None:
    """
    Test that pytest's tmp_path fixture works.

    Args:
        tmp_path: pytest built-in temporary directory fixture
    """
    assert tmp_path.exists()
    assert tmp_path.is_dir()

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    assert test_file.exists()
    assert test_file.read_text() == "test content"


@pytest.mark.unit
def test_mock_settings_fixture(mock_settings) -> None:  # type: ignore[no-untyped-def]
    """
    Test that mock_settings fixture provides correct configuration.

    Args:
        mock_settings: Mock Settings fixture
    """
    # Test Finlab config
    assert mock_settings.finlab_api_token == "test-finlab-token"
    assert isinstance(mock_settings.finlab.storage_path, Path)

    # Test logging config
    assert mock_settings.log_level == "DEBUG"
    assert isinstance(mock_settings.logging.log_dir, Path)

    # Test Analysis config
    assert mock_settings.claude_api_key == "test-claude-key"
    assert mock_settings.analysis.claude_model == "claude-sonnet-4.5"


@pytest.mark.unit
def test_logger_fixture(test_logger: logging.Logger) -> None:
    """
    Test that test_logger fixture provides working logger.

    Args:
        test_logger: Test logger fixture
    """
    assert test_logger.name == "test"
    assert test_logger.level == logging.DEBUG

    # Test that logging doesn't raise errors
    test_logger.debug("Debug message")
    test_logger.info("Info message")
    test_logger.warning("Warning message")
    test_logger.error("Error message")
    test_logger.critical("Critical message")


@pytest.mark.unit
def test_temp_log_file_fixture(temp_log_file: Path) -> None:
    """
    Test that temp_log_file fixture provides valid path.

    Args:
        temp_log_file: Temporary log file fixture
    """
    assert temp_log_file.suffix == ".log"
    assert temp_log_file.name == "test.log"

    # Write to log file
    temp_log_file.write_text("log content")
    assert temp_log_file.exists()
    assert temp_log_file.read_text() == "log content"


@pytest.mark.unit
def test_temp_database_fixture(temp_database: Path) -> None:
    """
    Test that temp_database fixture provides valid path.

    Args:
        temp_database: Temporary database fixture
    """
    assert temp_database.suffix == ".db"
    assert temp_database.name == "test.db"

    # Database path should be in temp directory
    assert temp_database.parent.exists()
