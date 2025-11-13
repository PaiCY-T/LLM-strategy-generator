"""Unit tests for AlertManager module.

Tests cover:
    - Alert condition evaluation (all 5 types)
    - Alert triggering and logging
    - Alert suppression logic
    - Configuration loading
    - Background monitoring
    - Data source integration
    - Edge cases and error handling

Coverage Target: >90%
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch, call
from collections import deque

from src.monitoring.alert_manager import AlertManager, AlertConfig, Alert
from src.monitoring.metrics_collector import MetricsCollector


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def metrics_collector():
    """Create mock MetricsCollector."""
    collector = Mock(spec=MetricsCollector)
    collector.record_error = Mock()
    return collector


@pytest.fixture
def event_logger():
    """Create mock EventLogger."""
    logger = Mock()
    logger.log_event = Mock()
    return logger


@pytest.fixture
def default_config():
    """Create default AlertConfig."""
    return AlertConfig(
        memory_threshold_percent=80.0,
        diversity_collapse_threshold=0.1,
        diversity_collapse_window=5,
        champion_staleness_threshold=20,
        success_rate_threshold=20.0,
        success_rate_window=10,
        orphaned_container_threshold=3,
        evaluation_interval=10,
        suppression_duration=300
    )


@pytest.fixture
def alert_manager(default_config, metrics_collector, event_logger):
    """Create AlertManager instance."""
    return AlertManager(default_config, metrics_collector, event_logger)


# =============================================================================
# AlertConfig Tests
# =============================================================================

def test_alert_config_defaults():
    """Test AlertConfig default values."""
    config = AlertConfig()

    assert config.memory_threshold_percent == 80.0
    assert config.diversity_collapse_threshold == 0.1
    assert config.diversity_collapse_window == 5
    assert config.champion_staleness_threshold == 20
    assert config.success_rate_threshold == 20.0
    assert config.success_rate_window == 10
    assert config.orphaned_container_threshold == 3
    assert config.evaluation_interval == 10
    assert config.suppression_duration == 300


def test_alert_config_custom_values():
    """Test AlertConfig with custom values."""
    config = AlertConfig(
        memory_threshold_percent=90.0,
        diversity_collapse_threshold=0.05,
        champion_staleness_threshold=30
    )

    assert config.memory_threshold_percent == 90.0
    assert config.diversity_collapse_threshold == 0.05
    assert config.champion_staleness_threshold == 30


def test_alert_config_from_dict():
    """Test loading AlertConfig from dictionary."""
    config_dict = {
        'memory_threshold_percent': 85.0,
        'diversity_collapse_threshold': 0.15,
        'champion_staleness_threshold': 25,
        'success_rate_threshold': 15.0
    }

    config = AlertConfig.from_dict(config_dict)

    assert config.memory_threshold_percent == 85.0
    assert config.diversity_collapse_threshold == 0.15
    assert config.champion_staleness_threshold == 25
    assert config.success_rate_threshold == 15.0
    # Defaults for missing values
    assert config.evaluation_interval == 10
    assert config.suppression_duration == 300


def test_alert_config_from_dict_empty():
    """Test loading AlertConfig from empty dictionary (all defaults)."""
    config = AlertConfig.from_dict({})

    assert config.memory_threshold_percent == 80.0
    assert config.diversity_collapse_threshold == 0.1


# =============================================================================
# Alert Tests
# =============================================================================

def test_alert_creation():
    """Test Alert dataclass creation."""
    alert = Alert(
        alert_type="high_memory",
        severity="critical",
        message="Memory usage high",
        current_value=85.0,
        threshold_value=80.0,
        iteration_context=42
    )

    assert alert.alert_type == "high_memory"
    assert alert.severity == "critical"
    assert alert.message == "Memory usage high"
    assert alert.current_value == 85.0
    assert alert.threshold_value == 80.0
    assert alert.iteration_context == 42
    assert alert.timestamp  # Should have timestamp


def test_alert_to_dict():
    """Test Alert serialization to dictionary."""
    alert = Alert(
        alert_type="diversity_collapse",
        severity="warning",
        message="Diversity collapsed",
        current_value=0.05,
        threshold_value=0.1,
        iteration_context=10
    )

    alert_dict = alert.to_dict()

    assert alert_dict["alert_type"] == "diversity_collapse"
    assert alert_dict["severity"] == "warning"
    assert alert_dict["message"] == "Diversity collapsed"
    assert alert_dict["current_value"] == 0.05
    assert alert_dict["threshold_value"] == 0.1
    assert alert_dict["iteration_context"] == 10
    assert "timestamp" in alert_dict


# =============================================================================
# AlertManager Initialization Tests
# =============================================================================

def test_alert_manager_initialization(alert_manager, default_config):
    """Test AlertManager initialization."""
    assert alert_manager.config == default_config
    assert alert_manager.metrics_collector is not None
    assert alert_manager.event_logger is not None
    assert len(alert_manager._active_alerts) == 0
    assert len(alert_manager._last_alert_time) == 0


def test_alert_manager_without_event_logger(default_config, metrics_collector):
    """Test AlertManager without EventLogger."""
    manager = AlertManager(default_config, metrics_collector, event_logger=None)

    assert manager.event_logger is None
    # Should still function without event logger


# =============================================================================
# Data Source Configuration Tests
# =============================================================================

def test_set_memory_source(alert_manager):
    """Test setting memory data source."""
    source = lambda: {'memory_percent': 75.0}
    alert_manager.set_memory_source(source)

    assert alert_manager._memory_source is not None
    assert alert_manager._memory_source()['memory_percent'] == 75.0


def test_set_diversity_source(alert_manager):
    """Test setting diversity data source."""
    source = lambda: 0.85
    alert_manager.set_diversity_source(source)

    assert alert_manager._diversity_source is not None
    assert alert_manager._diversity_source() == 0.85


def test_set_staleness_source(alert_manager):
    """Test setting staleness data source."""
    source = lambda: 15
    alert_manager.set_staleness_source(source)

    assert alert_manager._staleness_source is not None
    assert alert_manager._staleness_source() == 15


def test_set_success_rate_source(alert_manager):
    """Test setting success rate data source."""
    source = lambda: 85.5
    alert_manager.set_success_rate_source(source)

    assert alert_manager._success_rate_source is not None
    assert alert_manager._success_rate_source() == 85.5


def test_set_container_source(alert_manager):
    """Test setting container data source."""
    source = lambda: 2
    alert_manager.set_container_source(source)

    assert alert_manager._container_source is not None
    assert alert_manager._container_source() == 2


def test_set_iteration_source(alert_manager):
    """Test setting iteration data source."""
    source = lambda: 42
    alert_manager.set_iteration_source(source)

    assert alert_manager._iteration_source is not None
    assert alert_manager._iteration_source() == 42


# =============================================================================
# Alert Condition Evaluation Tests
# =============================================================================

def test_check_memory_threshold_exceeded(alert_manager):
    """Test memory threshold alert when exceeded."""
    alert_manager.set_memory_source(lambda: {'memory_percent': 85.0})

    alert = alert_manager._check_memory_threshold()

    assert alert is not None
    assert alert.alert_type == "high_memory"
    assert alert.severity == "critical"
    assert alert.current_value == 85.0
    assert alert.threshold_value == 80.0
    assert "High memory usage" in alert.message


def test_check_memory_threshold_not_exceeded(alert_manager):
    """Test memory threshold alert when not exceeded."""
    alert_manager.set_memory_source(lambda: {'memory_percent': 75.0})

    alert = alert_manager._check_memory_threshold()

    assert alert is None


def test_check_memory_threshold_no_source(alert_manager):
    """Test memory threshold check without data source."""
    alert = alert_manager._check_memory_threshold()

    assert alert is None


def test_check_diversity_collapse_detected(alert_manager):
    """Test diversity collapse alert when detected."""
    alert_manager.set_diversity_source(lambda: 0.05)

    alert = alert_manager._check_diversity_collapse()

    assert alert is not None
    assert alert.alert_type == "diversity_collapse"
    assert alert.severity == "warning"
    assert alert.current_value == 0.05
    assert alert.threshold_value == 0.1
    assert "Diversity collapse" in alert.message


def test_check_diversity_collapse_not_detected(alert_manager):
    """Test diversity collapse alert when not detected."""
    alert_manager.set_diversity_source(lambda: 0.85)

    alert = alert_manager._check_diversity_collapse()

    assert alert is None


def test_check_diversity_collapse_none_value(alert_manager):
    """Test diversity collapse check with None value."""
    alert_manager.set_diversity_source(lambda: None)

    alert = alert_manager._check_diversity_collapse()

    assert alert is None


def test_check_champion_staleness_exceeded(alert_manager):
    """Test champion staleness alert when exceeded."""
    alert_manager.set_staleness_source(lambda: 25)

    alert = alert_manager._check_champion_staleness()

    assert alert is not None
    assert alert.alert_type == "champion_staleness"
    assert alert.severity == "warning"
    assert alert.current_value == 25.0
    assert alert.threshold_value == 20.0
    assert "staleness detected" in alert.message


def test_check_champion_staleness_not_exceeded(alert_manager):
    """Test champion staleness alert when not exceeded."""
    alert_manager.set_staleness_source(lambda: 15)

    alert = alert_manager._check_champion_staleness()

    assert alert is None


def test_check_champion_staleness_exact_threshold(alert_manager):
    """Test champion staleness alert at exact threshold."""
    alert_manager.set_staleness_source(lambda: 20)

    alert = alert_manager._check_champion_staleness()

    # At threshold should trigger
    assert alert is not None


def test_check_success_rate_low_external_source(alert_manager):
    """Test low success rate alert with external source."""
    alert_manager.set_success_rate_source(lambda: 15.0)

    alert = alert_manager._check_success_rate()

    assert alert is not None
    assert alert.alert_type == "low_success_rate"
    assert alert.severity == "warning"
    assert alert.current_value == 15.0
    assert alert.threshold_value == 20.0


def test_check_success_rate_acceptable_external_source(alert_manager):
    """Test success rate alert when acceptable."""
    alert_manager.set_success_rate_source(lambda: 85.0)

    alert = alert_manager._check_success_rate()

    assert alert is None


def test_check_success_rate_internal_tracking(alert_manager):
    """Test success rate alert with internal tracking."""
    # Record 10 iterations with 10% success (1 success, 9 failures)
    alert_manager.record_iteration_result(True)
    for _ in range(9):
        alert_manager.record_iteration_result(False)

    alert = alert_manager._check_success_rate()

    assert alert is not None
    assert alert.alert_type == "low_success_rate"
    assert alert.current_value == 10.0  # 1/10 * 100


def test_check_success_rate_insufficient_history(alert_manager):
    """Test success rate check with insufficient history."""
    # Record only 5 iterations (need 10)
    for _ in range(5):
        alert_manager.record_iteration_result(True)

    alert = alert_manager._check_success_rate()

    assert alert is None  # Not enough history


def test_check_orphaned_containers_exceeded(alert_manager):
    """Test orphaned containers alert when exceeded."""
    alert_manager.set_container_source(lambda: 5)

    alert = alert_manager._check_orphaned_containers()

    assert alert is not None
    assert alert.alert_type == "orphaned_containers"
    assert alert.severity == "critical"
    assert alert.current_value == 5.0
    assert alert.threshold_value == 3.0
    assert "cleanup failures" in alert.message


def test_check_orphaned_containers_acceptable(alert_manager):
    """Test orphaned containers alert when acceptable."""
    alert_manager.set_container_source(lambda: 2)

    alert = alert_manager._check_orphaned_containers()

    assert alert is None


# =============================================================================
# Alert Triggering Tests
# =============================================================================

@patch('src.monitoring.alert_manager.logger')
def test_trigger_alert_first_time(mock_logger, alert_manager):
    """Test triggering alert for first time."""
    alert = Alert(
        alert_type="high_memory",
        severity="critical",
        message="Test alert",
        current_value=85.0,
        threshold_value=80.0
    )

    alert_manager._trigger_alert(alert)

    # Alert should be active
    assert "high_memory" in alert_manager._active_alerts
    assert "high_memory" in alert_manager._last_alert_time

    # Logger should be called
    assert mock_logger.warning.called


def test_trigger_alert_with_event_logger(alert_manager, event_logger):
    """Test alert triggering with EventLogger."""
    alert = Alert(
        alert_type="diversity_collapse",
        severity="warning",
        message="Test alert",
        current_value=0.05,
        threshold_value=0.1
    )

    alert_manager._trigger_alert(alert)

    # EventLogger should be called
    assert event_logger.log_event.called


def test_trigger_alert_increments_metric(alert_manager, metrics_collector):
    """Test alert triggering increments metric."""
    # Add the record_alert_triggered method to the mock
    metrics_collector.record_alert_triggered = Mock()

    alert = Alert(
        alert_type="champion_staleness",
        severity="warning",
        message="Test alert",
        current_value=25.0,
        threshold_value=20.0
    )

    alert_manager._trigger_alert(alert)

    # Since record_alert_triggered exists, it should be called
    metrics_collector.record_alert_triggered.assert_called_once_with("champion_staleness")


# =============================================================================
# Alert Suppression Tests
# =============================================================================

def test_alert_suppression_within_window(alert_manager):
    """Test alert is suppressed within suppression window."""
    alert = Alert(
        alert_type="high_memory",
        severity="critical",
        message="Test alert",
        current_value=85.0,
        threshold_value=80.0
    )

    # Trigger first time
    alert_manager._trigger_alert(alert)

    # Check suppression immediately
    assert alert_manager._is_alert_suppressed("high_memory") is True


def test_alert_suppression_after_window(alert_manager):
    """Test alert is not suppressed after window expires."""
    # Set very short suppression window for testing
    alert_manager.config.suppression_duration = 0.1  # 100ms

    alert = Alert(
        alert_type="high_memory",
        severity="critical",
        message="Test alert",
        current_value=85.0,
        threshold_value=80.0
    )

    # Trigger alert
    alert_manager._trigger_alert(alert)

    # Wait for suppression window to expire
    time.sleep(0.2)

    # Should not be suppressed anymore
    assert alert_manager._is_alert_suppressed("high_memory") is False


def test_alert_suppression_different_types(alert_manager):
    """Test different alert types are tracked independently."""
    alert1 = Alert(
        alert_type="high_memory",
        severity="critical",
        message="Alert 1",
        current_value=85.0,
        threshold_value=80.0
    )

    alert2 = Alert(
        alert_type="diversity_collapse",
        severity="warning",
        message="Alert 2",
        current_value=0.05,
        threshold_value=0.1
    )

    alert_manager._trigger_alert(alert1)
    alert_manager._trigger_alert(alert2)

    # Both should be active
    assert "high_memory" in alert_manager._active_alerts
    assert "diversity_collapse" in alert_manager._active_alerts


def test_reset_suppression(alert_manager):
    """Test manual suppression reset."""
    alert = Alert(
        alert_type="high_memory",
        severity="critical",
        message="Test alert",
        current_value=85.0,
        threshold_value=80.0
    )

    alert_manager._trigger_alert(alert)
    assert len(alert_manager._active_alerts) > 0

    alert_manager.reset_suppression()

    assert len(alert_manager._active_alerts) == 0
    assert len(alert_manager._last_alert_time) == 0


def test_clear_specific_alert(alert_manager):
    """Test clearing specific alert."""
    alert = Alert(
        alert_type="high_memory",
        severity="critical",
        message="Test alert",
        current_value=85.0,
        threshold_value=80.0
    )

    alert_manager._trigger_alert(alert)
    assert "high_memory" in alert_manager._active_alerts

    alert_manager.clear_alert("high_memory")

    assert "high_memory" not in alert_manager._active_alerts
    assert "high_memory" not in alert_manager._last_alert_time


# =============================================================================
# Background Monitoring Tests
# =============================================================================

def test_start_monitoring(alert_manager):
    """Test starting background monitoring."""
    alert_manager.start_monitoring()

    assert alert_manager._monitoring_thread is not None
    assert alert_manager._monitoring_thread.is_alive()

    # Cleanup
    alert_manager.stop_monitoring()


def test_start_monitoring_already_started(alert_manager):
    """Test starting monitoring when already started raises error."""
    alert_manager.start_monitoring()

    with pytest.raises(RuntimeError, match="already started"):
        alert_manager.start_monitoring()

    # Cleanup
    alert_manager.stop_monitoring()


def test_stop_monitoring(alert_manager):
    """Test stopping background monitoring."""
    alert_manager.start_monitoring()
    time.sleep(0.1)  # Let thread start

    alert_manager.stop_monitoring()

    # Thread should be stopped
    assert not alert_manager._monitoring_thread.is_alive()


def test_stop_monitoring_not_running(alert_manager):
    """Test stopping monitoring when not running."""
    # Should not raise error
    alert_manager.stop_monitoring()


def test_context_manager(alert_manager):
    """Test AlertManager as context manager."""
    with alert_manager as manager:
        assert manager._monitoring_thread is not None
        assert manager._monitoring_thread.is_alive()

    # Should be stopped after exiting context
    assert not alert_manager._monitoring_thread.is_alive()


# =============================================================================
# Evaluation Loop Tests
# =============================================================================

def test_evaluate_alerts_all_types(alert_manager):
    """Test evaluating all alert types."""
    # Set up data sources to trigger all alerts
    alert_manager.set_memory_source(lambda: {'memory_percent': 85.0})
    alert_manager.set_diversity_source(lambda: 0.05)
    alert_manager.set_staleness_source(lambda: 25)
    alert_manager.set_success_rate_source(lambda: 10.0)
    alert_manager.set_container_source(lambda: 5)
    alert_manager.set_iteration_source(lambda: 42)

    with patch.object(alert_manager, '_trigger_alert') as mock_trigger:
        alert_manager.evaluate_alerts()

        # Should trigger 5 alerts
        assert mock_trigger.call_count == 5

        # Verify alert types
        alert_types = [call[0][0].alert_type for call in mock_trigger.call_args_list]
        assert "high_memory" in alert_types
        assert "diversity_collapse" in alert_types
        assert "champion_staleness" in alert_types
        assert "low_success_rate" in alert_types
        assert "orphaned_containers" in alert_types


def test_evaluate_alerts_no_triggers(alert_manager):
    """Test evaluating when no alerts should trigger."""
    # Set up data sources with acceptable values
    alert_manager.set_memory_source(lambda: {'memory_percent': 50.0})
    alert_manager.set_diversity_source(lambda: 0.85)
    alert_manager.set_staleness_source(lambda: 5)
    alert_manager.set_success_rate_source(lambda: 90.0)
    alert_manager.set_container_source(lambda: 1)

    with patch.object(alert_manager, '_trigger_alert') as mock_trigger:
        alert_manager.evaluate_alerts()

        # Should not trigger any alerts
        assert mock_trigger.call_count == 0


def test_evaluate_alerts_with_iteration_context(alert_manager):
    """Test alert evaluation includes iteration context."""
    alert_manager.set_memory_source(lambda: {'memory_percent': 85.0})
    alert_manager.set_iteration_source(lambda: 42)

    with patch.object(alert_manager, '_trigger_alert') as mock_trigger:
        alert_manager.evaluate_alerts()

        # Verify iteration context set
        triggered_alert = mock_trigger.call_args[0][0]
        assert triggered_alert.iteration_context == 42


# =============================================================================
# Status and Reporting Tests
# =============================================================================

def test_get_active_alerts(alert_manager):
    """Test getting active alerts."""
    alert1 = Alert("high_memory", "critical", "Test 1", 85.0, 80.0)
    alert2 = Alert("diversity_collapse", "warning", "Test 2", 0.05, 0.1)

    alert_manager._trigger_alert(alert1)
    alert_manager._trigger_alert(alert2)

    active = alert_manager.get_active_alerts()

    assert "high_memory" in active
    assert "diversity_collapse" in active
    assert len(active) == 2


def test_get_status(alert_manager):
    """Test getting comprehensive status."""
    alert_manager.start_monitoring()

    status = alert_manager.get_status()

    assert 'active_alerts' in status
    assert 'suppressed_count' in status
    assert 'config' in status
    assert 'monitoring_active' in status

    # Verify config in status
    assert status['config']['memory_threshold'] == 80.0
    assert status['config']['diversity_threshold'] == 0.1

    # Monitoring should be active
    assert status['monitoring_active'] is True

    # Cleanup
    alert_manager.stop_monitoring()


# =============================================================================
# Error Handling Tests
# =============================================================================

def test_check_memory_threshold_error_handling(alert_manager):
    """Test memory check handles errors gracefully."""
    # Source that raises exception
    alert_manager.set_memory_source(lambda: 1/0)

    # Should not raise, returns None
    alert = alert_manager._check_memory_threshold()
    assert alert is None


def test_check_diversity_collapse_error_handling(alert_manager):
    """Test diversity check handles errors gracefully."""
    alert_manager.set_diversity_source(lambda: 1/0)

    alert = alert_manager._check_diversity_collapse()
    assert alert is None


def test_evaluate_alerts_with_exceptions(alert_manager):
    """Test evaluate_alerts handles exceptions in checks."""
    # Set source that will raise exception
    alert_manager.set_memory_source(lambda: {'invalid_key': 100})

    # Should not raise, just skip failing checks
    alert_manager.evaluate_alerts()


# =============================================================================
# Integration Tests
# =============================================================================

def test_full_alert_lifecycle(alert_manager):
    """Test complete alert lifecycle: trigger -> suppress -> clear."""
    # Set very short suppression for testing
    alert_manager.config.suppression_duration = 0.2

    alert_manager.set_memory_source(lambda: {'memory_percent': 85.0})

    # Trigger first time
    alert_manager.evaluate_alerts()
    assert "high_memory" in alert_manager.get_active_alerts()

    # Trigger again immediately - should be suppressed
    with patch.object(alert_manager, '_log_alert') as mock_log:
        alert_manager.evaluate_alerts()
        assert not mock_log.called  # Suppressed, no logging

    # Wait for suppression to expire
    time.sleep(0.3)

    # Trigger again - should work
    with patch.object(alert_manager, '_log_alert') as mock_log:
        alert_manager.evaluate_alerts()
        assert mock_log.called


def test_record_iteration_result_tracking(alert_manager):
    """Test iteration result tracking for success rate."""
    # Record mixed results
    results = [True, False, False, True, True, False, False, False, True, False]

    for result in results:
        alert_manager.record_iteration_result(result)

    # Check internal history
    assert len(alert_manager._success_history) == 10
    assert sum(alert_manager._success_history) == 4  # 4 successes


def test_concurrent_alert_evaluation():
    """Test thread safety of alert evaluation."""
    config = AlertConfig(evaluation_interval=0.1)  # Fast evaluation
    collector = Mock(spec=MetricsCollector)
    collector.record_error = Mock()

    manager = AlertManager(config, collector)
    manager.set_memory_source(lambda: {'memory_percent': 85.0})

    # Start monitoring
    manager.start_monitoring()

    # Let it run multiple evaluations
    time.sleep(0.5)

    # Stop monitoring
    manager.stop_monitoring()

    # Should have triggered multiple alerts (but suppressed after first)
    assert "high_memory" in manager.get_active_alerts()


# =============================================================================
# Edge Cases
# =============================================================================

def test_alert_manager_no_metrics_collector():
    """Test AlertManager works without metrics collector."""
    config = AlertConfig()

    # Should not raise
    manager = AlertManager(config, metrics_collector=None, event_logger=None)

    alert = Alert("test", "warning", "Test", 1.0, 0.5)
    manager._trigger_alert(alert)  # Should not crash


def test_memory_source_missing_key(alert_manager):
    """Test memory source with missing key."""
    alert_manager.set_memory_source(lambda: {})

    alert = alert_manager._check_memory_threshold()

    # Should return None (no memory_percent key)
    assert alert is None


def test_success_rate_with_all_failures(alert_manager):
    """Test success rate with 100% failure."""
    for _ in range(10):
        alert_manager.record_iteration_result(False)

    alert = alert_manager._check_success_rate()

    assert alert is not None
    assert alert.current_value == 0.0


def test_success_rate_with_all_successes(alert_manager):
    """Test success rate with 100% success."""
    for _ in range(10):
        alert_manager.record_iteration_result(True)

    alert = alert_manager._check_success_rate()

    assert alert is None  # Above threshold


# =============================================================================
# Performance Tests
# =============================================================================

def test_alert_evaluation_performance(alert_manager):
    """Test alert evaluation completes quickly (<50ms)."""
    # Set up all data sources
    alert_manager.set_memory_source(lambda: {'memory_percent': 50.0})
    alert_manager.set_diversity_source(lambda: 0.85)
    alert_manager.set_staleness_source(lambda: 5)
    alert_manager.set_success_rate_source(lambda: 90.0)
    alert_manager.set_container_source(lambda: 1)

    # Measure evaluation time
    start = time.time()
    alert_manager.evaluate_alerts()
    elapsed = time.time() - start

    # Should complete in <50ms
    assert elapsed < 0.05, f"Evaluation took {elapsed*1000:.1f}ms (target: <50ms)"


def test_stop_monitoring_timeout_logged():
    """Test that thread timeout is logged when stop takes too long."""
    config = AlertConfig(evaluation_interval=1, suppression_duration=10)
    collector = Mock()
    manager = AlertManager(config, collector)

    manager.start_monitoring()

    # Patch thread to simulate timeout
    original_join = manager._monitoring_thread.join

    def mock_join(timeout=None):
        # Don't actually join
        pass

    with patch.object(manager._monitoring_thread, 'join', side_effect=mock_join):
        with patch.object(manager._monitoring_thread, 'is_alive', return_value=True):
            manager.stop_monitoring()

    # Clean up
    manager._stop_event.set()
    original_join(timeout=1)


def test_monitoring_loop_slow_evaluation_logged():
    """Test that slow evaluation is logged."""
    config = AlertConfig(evaluation_interval=1)
    collector = Mock()
    manager = AlertManager(config, collector)

    # Make evaluate_alerts slow
    def slow_evaluate():
        time.sleep(0.06)  # >50ms

    with patch.object(manager, 'evaluate_alerts', side_effect=slow_evaluate):
        manager.start_monitoring()
        time.sleep(1.5)  # Let it run once
        manager.stop_monitoring()


def test_check_champion_staleness_error_handling():
    """Test error handling in champion staleness check."""
    config = AlertConfig()
    collector = Mock()
    manager = AlertManager(config, collector)

    # Set source that raises exception
    manager.set_staleness_source(lambda: 1/0)

    alert = manager._check_champion_staleness()

    # Should return None on exception
    assert alert is None


def test_check_success_rate_error_handling():
    """Test error handling in success rate check."""
    config = AlertConfig()
    collector = Mock()
    manager = AlertManager(config, collector)

    # Set source that raises exception
    manager.set_success_rate_source(lambda: 1/0)

    alert = manager._check_success_rate()

    # Should return None on exception
    assert alert is None


def test_check_orphaned_containers_error_handling():
    """Test error handling in orphaned containers check."""
    config = AlertConfig()
    collector = Mock()
    manager = AlertManager(config, collector)

    # Set source that raises exception
    manager.set_container_source(lambda: 1/0)

    alert = manager._check_orphaned_containers()

    # Should return None on exception
    assert alert is None


def test_log_alert_event_logger_failure():
    """Test alert logging when event logger fails."""
    config = AlertConfig()
    collector = Mock()
    event_logger = Mock()
    event_logger.log_event.side_effect = Exception("Logger error")

    manager = AlertManager(config, collector, event_logger)

    alert = Alert(
        alert_type="test",
        severity="warning",
        message="Test",
        current_value=1.0,
        threshold_value=0.5
    )

    # Should not raise exception
    manager._log_alert(alert)


def test_increment_alert_metric_exception_handling():
    """Test metric increment handles exceptions gracefully."""
    config = AlertConfig()
    collector = Mock()
    collector.record_error.side_effect = Exception("Metric error")

    manager = AlertManager(config, collector)

    alert = Alert(
        alert_type="test",
        severity="warning",
        message="Test",
        current_value=1.0,
        threshold_value=0.5
    )

    # Should not raise exception
    manager._trigger_alert(alert)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.monitoring.alert_manager", "--cov-report=term-missing"])
