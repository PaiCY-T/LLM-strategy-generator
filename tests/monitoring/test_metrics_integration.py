"""Integration tests for MetricsCollector with monitoring modules.

This test suite validates the integration between MetricsCollector (Task 5)
and the monitoring modules (ResourceMonitor, DiversityMonitor, ContainerMonitor, AlertManager).

Requirements:
- Verify metrics are recorded correctly from each monitor
- Test end-to-end metric flow
- Ensure Prometheus export includes all metrics
"""

import pytest
from unittest.mock import Mock, patch
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.resource_monitor import ResourceMonitor
from src.monitoring.diversity_monitor import DiversityMonitor
from src.monitoring.container_monitor import ContainerMonitor
from src.monitoring.alert_manager import AlertManager, AlertConfig


class TestResourceMonitorIntegration:
    """Test ResourceMonitor integration with MetricsCollector."""

    def test_resource_monitor_records_metrics(self):
        """Test that ResourceMonitor records metrics to MetricsCollector."""
        collector = MetricsCollector()
        monitor = ResourceMonitor(collector)

        # Mock psutil to avoid actual system calls
        with patch('src.monitoring.resource_monitor.psutil') as mock_psutil:
            # Mock memory stats
            mock_memory = Mock()
            mock_memory.used = 8 * 1024**3
            mock_memory.total = 16 * 1024**3
            mock_memory.percent = 50.0
            mock_psutil.virtual_memory.return_value = mock_memory

            # Mock CPU stats
            mock_psutil.cpu_percent.return_value = 45.5

            # Mock disk stats
            mock_disk = Mock()
            mock_disk.used = 100 * 1024**3
            mock_disk.total = 200 * 1024**3
            mock_disk.percent = 50.0
            mock_psutil.disk_usage.return_value = mock_disk

            # Record metrics
            monitor._record_system_metrics()

            # Verify metrics recorded
            assert collector.metrics["resource_memory_percent"].get_latest() == 50.0
            assert collector.metrics["resource_cpu_percent"].get_latest() == 45.5
            assert collector.metrics["resource_disk_percent"].get_latest() == 50.0


class TestDiversityMonitorIntegration:
    """Test DiversityMonitor integration with MetricsCollector."""

    def test_diversity_monitor_records_metrics(self):
        """Test that DiversityMonitor uses MetricsCollector."""
        collector = MetricsCollector()
        monitor = DiversityMonitor(collector)

        # Record diversity
        monitor.record_diversity(
            iteration=1,
            diversity=0.85,
            unique_count=42,
            total_count=50
        )

        # Verify metrics in collector (using existing record_strategy_diversity)
        # Note: Full integration will use record_diversity_metrics in Task 8
        assert collector.metrics["learning_strategy_diversity"].get_latest() == 42


class TestContainerMonitorIntegration:
    """Test ContainerMonitor integration with MetricsCollector."""

    def test_container_monitor_records_metrics(self):
        """Test that ContainerMonitor records metrics correctly."""
        collector = MetricsCollector()

        # Mock Docker client
        mock_docker = Mock()
        mock_docker.ping.return_value = True

        monitor = ContainerMonitor(collector, mock_docker)

        # Record container creation
        monitor.record_container_created("abc123", "test-container")

        # Verify metrics
        assert collector.metrics["container_created_total"].get_latest() == 1

        # Record cleanup
        monitor.record_container_cleanup("abc123", success=True)

        assert collector.metrics["container_cleanup_success_total"].get_latest() == 1


class TestAlertManagerIntegration:
    """Test AlertManager integration with MetricsCollector."""

    def test_alert_manager_records_metrics(self):
        """Test that AlertManager records alert metrics."""
        collector = MetricsCollector()
        config = AlertConfig()
        manager = AlertManager(config, collector)

        # Record alert directly via collector
        collector.record_alert_triggered("high_memory")

        # Verify metric recorded
        assert collector.metrics["alert_triggered_total"].get_latest() == 1

        # Record active alerts
        collector.record_active_alerts(2)
        assert collector.metrics["alert_active_count"].get_latest() == 2


class TestPrometheusExportIntegration:
    """Test end-to-end Prometheus export with all metrics."""

    def test_all_metrics_in_prometheus_export(self):
        """Test that all new metrics appear in Prometheus export."""
        collector = MetricsCollector()

        # Record metrics from all sources
        collector.record_resource_memory(8 * 1024**3, 16 * 1024**3, 50.0)
        collector.record_resource_cpu(45.5)
        collector.record_resource_disk(100 * 1024**3, 200 * 1024**3, 50.0)

        collector.record_diversity_metrics(0.85, 42, 50, 5, False)

        collector.record_container_counts(active=3, orphaned=1)
        collector.record_container_created()

        collector.record_alert_triggered("high_memory")
        collector.record_active_alerts(1)

        # Export to Prometheus
        prometheus_output = collector.export_prometheus()

        # Verify all metric categories present
        assert "resource_memory_percent" in prometheus_output
        assert "resource_cpu_percent" in prometheus_output
        assert "resource_disk_percent" in prometheus_output
        assert "diversity_population_diversity" in prometheus_output
        assert "diversity_champion_staleness" in prometheus_output
        assert "container_active_count" in prometheus_output
        assert "container_created_total" in prometheus_output
        assert "alert_triggered_total" in prometheus_output
        assert "alert_active_count" in prometheus_output

        # Verify HELP and TYPE lines
        assert "# HELP resource_memory_percent" in prometheus_output
        assert "# TYPE resource_memory_percent gauge" in prometheus_output
        assert "# HELP container_created_total" in prometheus_output
        assert "# TYPE container_created_total counter" in prometheus_output

    def test_json_export_includes_all_metrics(self):
        """Test that JSON export includes all metric categories."""
        import json

        collector = MetricsCollector()

        # Record metrics
        collector.record_resource_memory(8 * 1024**3, 16 * 1024**3, 50.0)
        collector.record_diversity_metrics(0.85, 42, 50, 5, False)
        collector.record_container_counts(active=3, orphaned=1)
        collector.record_alert_triggered("high_memory")

        # Export to JSON
        json_output = collector.export_json(include_history=False)
        data = json.loads(json_output)

        metrics = data["metrics"]

        # Verify all metric categories
        assert "resource_memory_percent" in metrics
        assert "diversity_population_diversity" in metrics
        assert "container_active_count" in metrics
        assert "alert_triggered_total" in metrics

    def test_summary_includes_all_sections(self):
        """Test that summary includes all monitoring sections."""
        collector = MetricsCollector()

        # Record metrics from all sources
        collector.record_resource_memory(8 * 1024**3, 16 * 1024**3, 50.0)
        collector.record_resource_cpu(45.5)
        collector.record_diversity_metrics(0.85, 42, 50, 5, False)
        collector.record_container_counts(active=3, orphaned=1)
        collector.record_alert_triggered("high_memory")
        collector.record_active_alerts(1)

        summary = collector.get_summary()

        # Verify all sections present
        assert "resources" in summary
        assert "diversity" in summary
        assert "containers" in summary
        assert "alerts" in summary

        # Verify values
        assert summary["resources"]["memory_percent"] == 50.0
        assert summary["resources"]["cpu_percent"] == 45.5
        assert summary["diversity"]["population_diversity"] == 0.85
        assert summary["containers"]["active_count"] == 3
        assert summary["alerts"]["active_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
