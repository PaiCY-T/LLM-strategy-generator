"""Unit tests for AlertManager and alert system.

Tests alert generation, delivery, rate limiting, and storage
for multi-template evolution monitoring (Phase 6, Task 42).
"""

import pytest
import time
import json
from pathlib import Path
from src.monitoring.alerts import (
    AlertManager,
    Alert,
    AlertSeverity,
    AlertChannel,
    create_fitness_drop_alert,
    create_diversity_collapse_alert,
    create_no_improvement_alert,
    create_system_error_alert
)


@pytest.fixture
def temp_alert_file(tmp_path):
    """Create temporary alert file."""
    return tmp_path / "test_alerts.json"


@pytest.fixture
def alert_manager(temp_alert_file):
    """Create alert manager with file output."""
    return AlertManager(
        alert_file=temp_alert_file,
        channels=[AlertChannel.LOG, AlertChannel.FILE],
        min_severity=AlertSeverity.LOW,
        rate_limit_seconds=2  # Short rate limit for testing
    )


class TestAlertCreation:
    """Test alert creation and basic properties."""

    def test_create_alert_basic(self, alert_manager):
        """Test basic alert creation."""
        alert = alert_manager.send_alert(
            severity=AlertSeverity.MEDIUM,
            alert_type="test_alert",
            message="Test alert message",
            generation=5,
            details={'key': 'value'}
        )

        assert alert is not None
        assert alert.severity == AlertSeverity.MEDIUM
        assert alert.alert_type == "test_alert"
        assert alert.message == "Test alert message"
        assert alert.generation == 5
        assert alert.details == {'key': 'value'}
        assert alert.acknowledged is False

    def test_alert_to_dict(self):
        """Test alert dictionary conversion."""
        alert = Alert(
            timestamp=time.time(),
            severity=AlertSeverity.HIGH,
            alert_type="fitness_drop",
            message="Fitness dropped 30%",
            generation=10
        )

        alert_dict = alert.to_dict()

        assert alert_dict['severity'] == 'high'
        assert alert_dict['alert_type'] == 'fitness_drop'
        assert alert_dict['message'] == 'Fitness dropped 30%'
        assert alert_dict['generation'] == 10
        assert 'datetime' in alert_dict

    def test_alert_to_log_message(self):
        """Test alert log message formatting."""
        alert = Alert(
            timestamp=time.time(),
            severity=AlertSeverity.CRITICAL,
            alert_type="system_error",
            message="System crash detected",
            generation=15
        )

        log_msg = alert.to_log_message()

        assert 'CRITICAL' in log_msg
        assert 'Gen 15' in log_msg
        assert 'system_error' in log_msg
        assert 'System crash detected' in log_msg


class TestSeverityFiltering:
    """Test severity-based alert filtering."""

    def test_filter_low_severity(self):
        """Test low severity alerts are filtered."""
        manager = AlertManager(
            min_severity=AlertSeverity.MEDIUM,
            rate_limit_seconds=1
        )

        # LOW severity should be filtered
        alert = manager.send_alert(
            severity=AlertSeverity.LOW,
            alert_type="test",
            message="Low severity alert"
        )

        assert alert is None
        assert len(manager.alert_history) == 0

    def test_allow_equal_severity(self):
        """Test alerts with minimum severity are allowed."""
        manager = AlertManager(
            min_severity=AlertSeverity.MEDIUM,
            rate_limit_seconds=1
        )

        # MEDIUM severity should pass
        alert = manager.send_alert(
            severity=AlertSeverity.MEDIUM,
            alert_type="test",
            message="Medium severity alert"
        )

        assert alert is not None
        assert len(manager.alert_history) == 1

    def test_allow_higher_severity(self):
        """Test alerts with higher severity are allowed."""
        manager = AlertManager(
            min_severity=AlertSeverity.MEDIUM,
            rate_limit_seconds=1
        )

        # HIGH and CRITICAL should pass
        alert1 = manager.send_alert(
            severity=AlertSeverity.HIGH,
            alert_type="test",
            message="High severity alert"
        )

        alert2 = manager.send_alert(
            severity=AlertSeverity.CRITICAL,
            alert_type="test2",
            message="Critical severity alert"
        )

        assert alert1 is not None
        assert alert2 is not None
        assert len(manager.alert_history) == 2


class TestRateLimiting:
    """Test alert rate limiting functionality."""

    def test_rate_limiting_same_type(self, alert_manager):
        """Test rate limiting for same alert type."""
        # First alert should go through
        alert1 = alert_manager.send_alert(
            severity=AlertSeverity.MEDIUM,
            alert_type="fitness_drop",
            message="First alert"
        )

        # Second alert of same type should be rate-limited
        alert2 = alert_manager.send_alert(
            severity=AlertSeverity.MEDIUM,
            alert_type="fitness_drop",
            message="Second alert (should be blocked)"
        )

        assert alert1 is not None
        assert alert2 is None
        assert len(alert_manager.alert_history) == 1

    def test_rate_limiting_different_types(self, alert_manager):
        """Test different alert types not rate-limited."""
        # Different alert types should both go through
        alert1 = alert_manager.send_alert(
            severity=AlertSeverity.MEDIUM,
            alert_type="fitness_drop",
            message="Fitness drop alert"
        )

        alert2 = alert_manager.send_alert(
            severity=AlertSeverity.MEDIUM,
            alert_type="diversity_collapse",
            message="Diversity collapse alert"
        )

        assert alert1 is not None
        assert alert2 is not None
        assert len(alert_manager.alert_history) == 2

    def test_rate_limit_expiry(self, alert_manager):
        """Test rate limit expires after timeout."""
        # First alert
        alert1 = alert_manager.send_alert(
            severity=AlertSeverity.MEDIUM,
            alert_type="fitness_drop",
            message="First alert"
        )

        # Wait for rate limit to expire (2 seconds + buffer)
        time.sleep(2.5)

        # Second alert should go through
        alert2 = alert_manager.send_alert(
            severity=AlertSeverity.MEDIUM,
            alert_type="fitness_drop",
            message="Second alert (should succeed)"
        )

        assert alert1 is not None
        assert alert2 is not None
        assert len(alert_manager.alert_history) == 2


class TestAlertChannels:
    """Test alert delivery through different channels."""

    def test_log_channel(self, temp_alert_file, caplog):
        """Test alert delivery to log channel."""
        manager = AlertManager(
            alert_file=temp_alert_file,
            channels=[AlertChannel.LOG],
            rate_limit_seconds=1
        )

        manager.send_alert(
            severity=AlertSeverity.HIGH,
            alert_type="test",
            message="Test log message"
        )

        # Check log output
        assert "Test log message" in caplog.text

    def test_file_channel(self, temp_alert_file):
        """Test alert delivery to file channel."""
        manager = AlertManager(
            alert_file=temp_alert_file,
            channels=[AlertChannel.FILE],
            rate_limit_seconds=1
        )

        manager.send_alert(
            severity=AlertSeverity.MEDIUM,
            alert_type="test",
            message="Test file alert"
        )

        # Check file was created and contains alert
        assert temp_alert_file.exists()
        alerts = json.loads(temp_alert_file.read_text())
        assert len(alerts) == 1
        assert alerts[0]['message'] == "Test file alert"

    def test_multiple_channels(self, temp_alert_file, caplog):
        """Test alert delivery to multiple channels."""
        manager = AlertManager(
            alert_file=temp_alert_file,
            channels=[AlertChannel.LOG, AlertChannel.FILE],
            rate_limit_seconds=1
        )

        manager.send_alert(
            severity=AlertSeverity.HIGH,
            alert_type="test",
            message="Multi-channel alert"
        )

        # Check both log and file
        assert "Multi-channel alert" in caplog.text
        assert temp_alert_file.exists()
        alerts = json.loads(temp_alert_file.read_text())
        assert len(alerts) == 1


class TestAlertStorage:
    """Test alert history and storage."""

    def test_alert_history_tracking(self, alert_manager):
        """Test alert history is tracked."""
        alert_manager.send_alert(
            severity=AlertSeverity.MEDIUM,
            alert_type="test1",
            message="First alert"
        )

        alert_manager.send_alert(
            severity=AlertSeverity.HIGH,
            alert_type="test2",
            message="Second alert"
        )

        assert len(alert_manager.alert_history) == 2

    def test_file_size_limiting(self, temp_alert_file):
        """Test alert file size is limited to 1000 entries."""
        manager = AlertManager(
            alert_file=temp_alert_file,
            channels=[AlertChannel.FILE],
            rate_limit_seconds=0  # No rate limiting for this test
        )

        # Send 1500 alerts
        for i in range(1500):
            manager.send_alert(
                severity=AlertSeverity.LOW,
                alert_type=f"test_{i}",  # Different types to bypass rate limiting
                message=f"Alert {i}"
            )

        # File should contain only last 1000
        alerts = json.loads(temp_alert_file.read_text())
        assert len(alerts) == 1000
        # Should have alerts 500-1499
        assert alerts[0]['message'] == "Alert 500"
        assert alerts[-1]['message'] == "Alert 1499"

    def test_get_recent_alerts(self, alert_manager):
        """Test getting recent alerts."""
        # Send 15 alerts
        for i in range(15):
            alert_manager.send_alert(
                severity=AlertSeverity.LOW,
                alert_type=f"test_{i}",
                message=f"Alert {i}"
            )

        # Get last 5
        recent = alert_manager.get_recent_alerts(count=5)

        assert len(recent) == 5
        assert recent[-1].message == "Alert 14"

    def test_get_recent_alerts_with_severity_filter(self, alert_manager):
        """Test getting recent alerts with severity filter."""
        # Send mixed severity alerts
        alert_manager.send_alert(severity=AlertSeverity.LOW, alert_type="test1", message="Low 1")
        alert_manager.send_alert(severity=AlertSeverity.HIGH, alert_type="test2", message="High 1")
        alert_manager.send_alert(severity=AlertSeverity.LOW, alert_type="test3", message="Low 2")
        alert_manager.send_alert(severity=AlertSeverity.CRITICAL, alert_type="test4", message="Critical 1")

        # Get only HIGH and above
        high_alerts = alert_manager.get_recent_alerts(count=10, min_severity=AlertSeverity.HIGH)

        assert len(high_alerts) == 2
        assert all(a.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] for a in high_alerts)


class TestAlertSummary:
    """Test alert summary statistics."""

    def test_empty_summary(self, alert_manager):
        """Test summary with no alerts."""
        summary = alert_manager.get_alert_summary()

        assert summary['total_alerts'] == 0

    def test_summary_with_alerts(self, alert_manager):
        """Test summary with multiple alerts."""
        alert_manager.send_alert(severity=AlertSeverity.LOW, alert_type="test1", message="Low")
        alert_manager.send_alert(severity=AlertSeverity.MEDIUM, alert_type="test2", message="Medium")
        alert_manager.send_alert(severity=AlertSeverity.HIGH, alert_type="test3", message="High")
        alert_manager.send_alert(severity=AlertSeverity.CRITICAL, alert_type="test4", message="Critical")

        summary = alert_manager.get_alert_summary()

        assert summary['total_alerts'] == 4
        assert summary['by_severity']['low'] == 1
        assert summary['by_severity']['medium'] == 1
        assert summary['by_severity']['high'] == 1
        assert summary['by_severity']['critical'] == 1
        assert summary['by_type']['test1'] == 1

    def test_clear_old_alerts(self, alert_manager):
        """Test clearing old alerts."""
        # Send alert now
        alert_manager.send_alert(severity=AlertSeverity.LOW, alert_type="recent", message="Recent")

        # Manually add old alert (24 hours ago)
        old_alert = Alert(
            timestamp=time.time() - (25 * 3600),  # 25 hours ago
            severity=AlertSeverity.LOW,
            alert_type="old",
            message="Old alert"
        )
        alert_manager.alert_history.insert(0, old_alert)

        # Clear alerts older than 24 hours
        cleared = alert_manager.clear_old_alerts(max_age_hours=24)

        assert cleared == 1
        assert len(alert_manager.alert_history) == 1
        assert alert_manager.alert_history[0].alert_type == "recent"


class TestCustomHandlers:
    """Test custom alert handlers."""

    def test_add_custom_handler(self, alert_manager):
        """Test adding custom alert handler."""
        handled_alerts = []

        def custom_handler(alert):
            handled_alerts.append(alert)

        alert_manager.add_custom_handler(custom_handler)

        alert_manager.send_alert(
            severity=AlertSeverity.HIGH,
            alert_type="test",
            message="Test alert"
        )

        assert len(handled_alerts) == 1
        assert handled_alerts[0].message == "Test alert"

    def test_multiple_custom_handlers(self, alert_manager):
        """Test multiple custom handlers."""
        handler1_calls = []
        handler2_calls = []

        def handler1(alert):
            handler1_calls.append(alert)

        def handler2(alert):
            handler2_calls.append(alert)

        alert_manager.add_custom_handler(handler1)
        alert_manager.add_custom_handler(handler2)

        alert_manager.send_alert(
            severity=AlertSeverity.MEDIUM,
            alert_type="test",
            message="Test"
        )

        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1


class TestAlertHelperFunctions:
    """Test predefined alert helper functions."""

    def test_fitness_drop_alert_triggers(self, alert_manager):
        """Test fitness drop alert is triggered correctly."""
        # 30% drop should trigger (threshold is 20%)
        alert = create_fitness_drop_alert(
            manager=alert_manager,
            generation=5,
            prev_fitness=2.0,
            current_fitness=1.4
        )

        assert alert is not None
        assert alert.severity == AlertSeverity.MEDIUM
        assert alert.alert_type == "fitness_drop"
        assert "30.0%" in alert.message

    def test_fitness_drop_alert_severity(self, alert_manager):
        """Test fitness drop alert severity levels."""
        # 60% drop should be HIGH severity
        alert = create_fitness_drop_alert(
            manager=alert_manager,
            generation=5,
            prev_fitness=2.0,
            current_fitness=0.8
        )

        assert alert.severity == AlertSeverity.HIGH

    def test_diversity_collapse_alert(self, alert_manager):
        """Test diversity collapse alert."""
        alert = create_diversity_collapse_alert(
            manager=alert_manager,
            generation=10,
            diversity=0.05,
            threshold=0.1
        )

        assert alert is not None
        assert alert.severity == AlertSeverity.HIGH
        assert alert.alert_type == "diversity_collapse"

    def test_no_improvement_alert(self, alert_manager):
        """Test no improvement alert."""
        alert = create_no_improvement_alert(
            manager=alert_manager,
            generation=50,
            last_improvement_generation=30,
            threshold_generations=20
        )

        assert alert is not None
        assert alert.severity == AlertSeverity.LOW
        assert alert.alert_type == "no_improvement"
        assert "20 generations" in alert.message

    def test_system_error_alert(self, alert_manager):
        """Test system error alert."""
        alert = create_system_error_alert(
            manager=alert_manager,
            generation=5,
            error_type="RuntimeError",
            error_message="Out of memory"
        )

        assert alert is not None
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.alert_type == "system_error"
        assert "RuntimeError" in alert.message
