"""Test suite for Task 3.2.4: Validation error logging"""

import logging
import pytest
from src.backtest.validation import log_validation_error


class TestValidationLogging:
    """SV-2.5: Validation errors logged with field, value, constraint"""

    def test_log_validation_error_includes_field_name(self, caplog):
        """WHEN logging validation error THEN includes field name"""
        with caplog.at_level(logging.WARNING):
            log_validation_error("sharpe_ratio", 15.0, "sharpe_ratio 15.0 is out of valid range [-10, 10]")

        assert "sharpe_ratio" in caplog.text

    def test_log_validation_error_includes_value(self, caplog):
        """WHEN logging validation error THEN includes actual value"""
        with caplog.at_level(logging.WARNING):
            log_validation_error("sharpe_ratio", 15.0, "sharpe_ratio 15.0 is out of valid range [-10, 10]")

        assert "15.0" in caplog.text

    def test_log_validation_error_includes_error_message(self, caplog):
        """WHEN logging validation error THEN includes constraint description"""
        with caplog.at_level(logging.WARNING):
            error_msg = "sharpe_ratio 15.0 is out of valid range [-10, 10]"
            log_validation_error("sharpe_ratio", 15.0, error_msg)

        assert "[-10, 10]" in caplog.text or "range" in caplog.text.lower()

    def test_log_validation_error_uses_warning_level(self, caplog):
        """WHEN logging validation error THEN uses WARNING level"""
        with caplog.at_level(logging.WARNING):
            log_validation_error("max_drawdown", 0.5, "max_drawdown must be <= 0")

        assert len(caplog.records) > 0
        assert caplog.records[0].levelname == "WARNING"

    def test_log_validation_error_formats_none_value(self, caplog):
        """WHEN value is None THEN logs appropriately"""
        with caplog.at_level(logging.WARNING):
            # This shouldn't normally happen, but test edge case
            log_validation_error("sharpe_ratio", None, "unexpected None")

        assert "None" in caplog.text or "null" in caplog.text.lower()

    def test_log_validation_error_handles_special_values(self, caplog):
        """WHEN value is NaN/Inf THEN logs appropriately"""
        with caplog.at_level(logging.WARNING):
            log_validation_error("sharpe_ratio", float('nan'), "invalid NaN")

        assert "nan" in caplog.text.lower()

        caplog.clear()

        with caplog.at_level(logging.WARNING):
            log_validation_error("sharpe_ratio", float('inf'), "invalid inf")

        assert "inf" in caplog.text.lower()
