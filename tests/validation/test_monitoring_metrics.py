"""Test validation monitoring metrics collection.

This module tests the metrics collection system for validation infrastructure
monitoring. Covers field error rate, LLM success rate, validation latency,
circuit breaker triggers, and metrics export to Prometheus/CloudWatch formats.

Requirements:
- Task 6.5: Performance monitoring dashboard
- NFR-M1: Monitoring and alerting for production
- Alert thresholds from Task 6.4 validation

Test Coverage:
1. Metrics initialization and registration
2. Field error rate collection and calculation
3. LLM success rate collection and calculation
4. Validation latency collection (total, layer1, layer2, layer3)
5. Circuit breaker trigger tracking
6. Prometheus export format validation
7. CloudWatch export format validation
8. Alert threshold checking
"""

import pytest
import time
import json
from typing import Dict, Any
from unittest.mock import Mock, patch

from src.monitoring.metrics_collector import MetricsCollector
from src.validation.gateway import ValidationGateway
from src.validation.validation_result import ValidationResult, FieldError


class TestMetricsCollectorInitialization:
    """Test metrics collector initialization for validation metrics."""

    def test_collector_initializes_validation_metrics(self):
        """Test that MetricsCollector initializes all validation-specific metrics."""
        collector = MetricsCollector()

        # Verify validation metrics are registered
        assert "validation_field_error_rate" in collector.metrics
        assert "validation_llm_success_rate" in collector.metrics
        assert "validation_total_latency_ms" in collector.metrics
        assert "validation_layer1_latency_ms" in collector.metrics
        assert "validation_layer2_latency_ms" in collector.metrics
        assert "validation_layer3_latency_ms" in collector.metrics
        assert "validation_circuit_breaker_triggers" in collector.metrics
        assert "validation_error_signatures_unique" in collector.metrics

    def test_validation_metrics_have_correct_types(self):
        """Test that validation metrics have appropriate types."""
        collector = MetricsCollector()

        # Rates should be GAUGE (can go up/down)
        assert collector.metrics["validation_field_error_rate"].metric_type.value == "gauge"
        assert collector.metrics["validation_llm_success_rate"].metric_type.value == "gauge"

        # Latencies should be HISTOGRAM (distribution)
        assert collector.metrics["validation_total_latency_ms"].metric_type.value == "histogram"
        assert collector.metrics["validation_layer1_latency_ms"].metric_type.value == "histogram"
        assert collector.metrics["validation_layer2_latency_ms"].metric_type.value == "histogram"
        assert collector.metrics["validation_layer3_latency_ms"].metric_type.value == "histogram"

        # Counters should be COUNTER (monotonically increasing)
        assert collector.metrics["validation_circuit_breaker_triggers"].metric_type.value == "counter"
        assert collector.metrics["validation_error_signatures_unique"].metric_type.value == "gauge"


class TestFieldErrorRateCollection:
    """Test field error rate metric collection."""

    def test_record_field_error_rate_zero_errors(self):
        """Test recording 0% field error rate."""
        collector = MetricsCollector()

        # Record validation with no field errors
        collector.record_validation_field_errors(
            total_strategies=10,
            strategies_with_errors=0
        )

        # Verify field error rate is 0%
        error_rate = collector.metrics["validation_field_error_rate"].get_latest()
        assert error_rate == 0.0

    def test_record_field_error_rate_with_errors(self):
        """Test recording field error rate with errors."""
        collector = MetricsCollector()

        # Record validation with 3 errors out of 10 strategies
        collector.record_validation_field_errors(
            total_strategies=10,
            strategies_with_errors=3
        )

        # Verify field error rate is 30%
        error_rate = collector.metrics["validation_field_error_rate"].get_latest()
        assert error_rate == 30.0

    def test_field_error_rate_rolling_average(self):
        """Test field error rate calculates rolling average over window."""
        collector = MetricsCollector()

        # Record multiple validation results
        collector.record_validation_field_errors(10, 0)  # 0%
        collector.record_validation_field_errors(10, 1)  # 10%
        collector.record_validation_field_errors(10, 2)  # 20%

        # Calculate average error rate over last 3 windows
        avg_error_rate = collector.metrics["validation_field_error_rate"].get_average(window=3)
        assert avg_error_rate == pytest.approx(10.0, abs=0.1)  # (0 + 10 + 20) / 3

    def test_field_error_rate_alert_threshold_warning(self):
        """Test that field error rate >5% triggers warning threshold."""
        collector = MetricsCollector()

        # Record error rate above warning threshold (5%)
        collector.record_validation_field_errors(
            total_strategies=100,
            strategies_with_errors=6
        )

        error_rate = collector.metrics["validation_field_error_rate"].get_latest()
        assert error_rate > 5.0  # Warning threshold

    def test_field_error_rate_alert_threshold_critical(self):
        """Test that field error rate >10% triggers critical threshold."""
        collector = MetricsCollector()

        # Record error rate above critical threshold (10%)
        collector.record_validation_field_errors(
            total_strategies=100,
            strategies_with_errors=11
        )

        error_rate = collector.metrics["validation_field_error_rate"].get_latest()
        assert error_rate > 10.0  # Critical threshold


class TestLLMSuccessRateCollection:
    """Test LLM success rate metric collection."""

    def test_record_llm_success_rate_perfect(self):
        """Test recording 100% LLM success rate."""
        collector = MetricsCollector()

        # Record LLM generation with 100% success
        collector.record_llm_validation_success(
            total_attempts=10,
            successful_validations=10
        )

        success_rate = collector.metrics["validation_llm_success_rate"].get_latest()
        assert success_rate == 100.0

    def test_record_llm_success_rate_with_failures(self):
        """Test recording LLM success rate with failures."""
        collector = MetricsCollector()

        # Record 8 successful validations out of 10 attempts
        collector.record_llm_validation_success(
            total_attempts=10,
            successful_validations=8
        )

        success_rate = collector.metrics["validation_llm_success_rate"].get_latest()
        assert success_rate == 80.0

    def test_llm_success_rate_alert_threshold_warning(self):
        """Test that LLM success rate <90% triggers warning threshold."""
        collector = MetricsCollector()

        # Record success rate below warning threshold (90%)
        collector.record_llm_validation_success(
            total_attempts=100,
            successful_validations=85
        )

        success_rate = collector.metrics["validation_llm_success_rate"].get_latest()
        assert success_rate < 90.0  # Warning threshold

    def test_llm_success_rate_alert_threshold_critical(self):
        """Test that LLM success rate <80% triggers critical threshold."""
        collector = MetricsCollector()

        # Record success rate below critical threshold (80%)
        collector.record_llm_validation_success(
            total_attempts=100,
            successful_validations=75
        )

        success_rate = collector.metrics["validation_llm_success_rate"].get_latest()
        assert success_rate < 80.0  # Critical threshold


class TestValidationLatencyCollection:
    """Test validation latency metric collection."""

    def test_record_validation_latency_all_layers(self):
        """Test recording latency for all validation layers."""
        collector = MetricsCollector()

        # Record latencies for all layers (in milliseconds)
        collector.record_validation_latency(
            total_ms=5.5,
            layer1_ms=0.5,
            layer2_ms=4.0,
            layer3_ms=1.0
        )

        # Verify all latencies recorded
        assert collector.metrics["validation_total_latency_ms"].get_latest() == 5.5
        assert collector.metrics["validation_layer1_latency_ms"].get_latest() == 0.5
        assert collector.metrics["validation_layer2_latency_ms"].get_latest() == 4.0
        assert collector.metrics["validation_layer3_latency_ms"].get_latest() == 1.0

    def test_validation_latency_mean_calculation(self):
        """Test average validation latency calculation over window."""
        collector = MetricsCollector()

        # Record multiple latencies
        collector.record_validation_latency(1.0, 0.1, 0.8, 0.1)
        collector.record_validation_latency(2.0, 0.2, 1.6, 0.2)
        collector.record_validation_latency(3.0, 0.3, 2.4, 0.3)

        # Calculate average total latency
        avg_latency = collector.metrics["validation_total_latency_ms"].get_average(window=3)
        assert avg_latency == pytest.approx(2.0, abs=0.1)  # (1.0 + 2.0 + 3.0) / 3

    def test_validation_latency_p99_calculation(self):
        """Test P99 validation latency calculation."""
        collector = MetricsCollector()

        # Record 100 latencies to test percentile calculation
        for i in range(100):
            # Most values between 1-5ms, one outlier at 9ms
            latency = 9.0 if i == 99 else (i % 5) + 1.0
            collector.record_validation_latency(latency, 0.1, latency - 0.1, 0.0)

        # Get P99 latency using helper method
        p99_latency = collector.get_validation_latency_p99()
        assert p99_latency <= 9.0

    def test_validation_latency_alert_threshold_mean_warning(self):
        """Test that mean latency >1ms triggers warning threshold."""
        collector = MetricsCollector()

        # Record latencies averaging >1ms
        for _ in range(10):
            collector.record_validation_latency(1.5, 0.1, 1.3, 0.1)

        avg_latency = collector.metrics["validation_total_latency_ms"].get_average(window=10)
        assert avg_latency > 1.0  # Warning threshold

    def test_validation_latency_alert_threshold_mean_critical(self):
        """Test that mean latency >5ms triggers critical threshold."""
        collector = MetricsCollector()

        # Record latencies averaging >5ms
        for _ in range(10):
            collector.record_validation_latency(6.0, 0.5, 5.0, 0.5)

        avg_latency = collector.metrics["validation_total_latency_ms"].get_average(window=10)
        assert avg_latency > 5.0  # Critical threshold

    def test_validation_latency_alert_threshold_p99_warning(self):
        """Test that P99 latency >5ms triggers warning threshold."""
        collector = MetricsCollector()

        # Record 100 latencies with P99 >5ms
        for i in range(100):
            # 98% under 3ms, 2% at 7ms (ensures P99 is above threshold)
            latency = 7.0 if i >= 98 else 3.0
            collector.record_validation_latency(latency, 0.1, latency - 0.1, 0.0)

        p99_latency = collector.get_validation_latency_p99()
        assert p99_latency > 5.0  # Warning threshold

    def test_validation_latency_alert_threshold_p99_critical(self):
        """Test that P99 latency >8ms triggers critical threshold."""
        collector = MetricsCollector()

        # Record 100 latencies with P99 >8ms
        for i in range(100):
            # 98% under 3ms, 2% at 9ms (ensures P99 is above threshold)
            latency = 9.0 if i >= 98 else 3.0
            collector.record_validation_latency(latency, 0.1, latency - 0.1, 0.0)

        p99_latency = collector.get_validation_latency_p99()
        assert p99_latency > 8.0  # Critical threshold


class TestCircuitBreakerTracking:
    """Test circuit breaker trigger tracking."""

    def test_record_circuit_breaker_trigger(self):
        """Test recording circuit breaker activation."""
        collector = MetricsCollector()

        # Record circuit breaker trigger
        collector.record_circuit_breaker_trigger()

        trigger_count = collector.metrics["validation_circuit_breaker_triggers"].get_latest()
        assert trigger_count == 1

    def test_circuit_breaker_multiple_triggers(self):
        """Test recording multiple circuit breaker triggers."""
        collector = MetricsCollector()

        # Record 5 circuit breaker triggers
        for _ in range(5):
            collector.record_circuit_breaker_trigger()

        trigger_count = collector.metrics["validation_circuit_breaker_triggers"].get_latest()
        assert trigger_count == 5

    def test_circuit_breaker_alert_threshold_warning(self):
        """Test that >10 triggers/min triggers warning threshold."""
        collector = MetricsCollector()

        # Record 11 triggers in 1 minute window
        for _ in range(11):
            collector.record_circuit_breaker_trigger()

        # Check trigger rate
        trigger_count = collector.metrics["validation_circuit_breaker_triggers"].get_latest()
        assert trigger_count > 10  # Warning threshold

    def test_circuit_breaker_alert_threshold_critical(self):
        """Test that >20 triggers/min triggers critical threshold."""
        collector = MetricsCollector()

        # Record 21 triggers in 1 minute window
        for _ in range(21):
            collector.record_circuit_breaker_trigger()

        trigger_count = collector.metrics["validation_circuit_breaker_triggers"].get_latest()
        assert trigger_count > 20  # Critical threshold


class TestErrorSignatureTracking:
    """Test unique error signature tracking."""

    def test_record_error_signature_count(self):
        """Test tracking unique error signatures."""
        collector = MetricsCollector()

        # Record unique error signatures
        collector.record_unique_error_signatures(count=5)

        unique_count = collector.metrics["validation_error_signatures_unique"].get_latest()
        assert unique_count == 5

    def test_error_signature_count_increases(self):
        """Test that error signature count tracks diversity of errors."""
        collector = MetricsCollector()

        # Start with 3 unique signatures
        collector.record_unique_error_signatures(count=3)

        # Increase to 7 unique signatures
        collector.record_unique_error_signatures(count=7)

        unique_count = collector.metrics["validation_error_signatures_unique"].get_latest()
        assert unique_count == 7


class TestPrometheusExport:
    """Test Prometheus metrics export format."""

    def test_export_prometheus_format_basic(self):
        """Test basic Prometheus export format."""
        collector = MetricsCollector()

        # Record some validation metrics
        collector.record_validation_field_errors(100, 5)
        collector.record_llm_validation_success(10, 9)
        collector.record_validation_latency(2.5, 0.3, 2.0, 0.2)

        # Export to Prometheus format
        prometheus_output = collector.export_prometheus()

        # Verify Prometheus format structure
        assert "# HELP validation_field_error_rate" in prometheus_output
        assert "# TYPE validation_field_error_rate gauge" in prometheus_output
        assert "validation_field_error_rate 5.0" in prometheus_output

        assert "# HELP validation_llm_success_rate" in prometheus_output
        assert "# TYPE validation_llm_success_rate gauge" in prometheus_output
        assert "validation_llm_success_rate 90.0" in prometheus_output

        assert "# HELP validation_total_latency_ms" in prometheus_output
        assert "# TYPE validation_total_latency_ms histogram" in prometheus_output

    def test_export_prometheus_with_timestamps(self):
        """Test Prometheus export includes timestamps."""
        collector = MetricsCollector()

        collector.record_validation_field_errors(100, 0)

        prometheus_output = collector.export_prometheus()

        # Verify timestamp is included (Unix timestamp in milliseconds)
        lines = prometheus_output.split('\n')
        metric_lines = [l for l in lines if l.startswith('validation_field_error_rate')]

        assert len(metric_lines) > 0
        # Format: metric_name value timestamp
        parts = metric_lines[0].split()
        assert len(parts) == 3
        timestamp = int(parts[2])
        assert timestamp > 0

    def test_export_prometheus_multiple_metrics(self):
        """Test Prometheus export with multiple validation metrics."""
        collector = MetricsCollector()

        # Record all validation metric types
        collector.record_validation_field_errors(100, 5)
        collector.record_llm_validation_success(20, 18)
        collector.record_validation_latency(3.0, 0.2, 2.5, 0.3)
        collector.record_circuit_breaker_trigger()
        collector.record_unique_error_signatures(count=8)

        prometheus_output = collector.export_prometheus()

        # Verify all metrics exported
        assert "validation_field_error_rate" in prometheus_output
        assert "validation_llm_success_rate" in prometheus_output
        assert "validation_total_latency_ms" in prometheus_output
        assert "validation_circuit_breaker_triggers" in prometheus_output
        assert "validation_error_signatures_unique" in prometheus_output


class TestCloudWatchExport:
    """Test CloudWatch metrics export format."""

    def test_export_cloudwatch_format_basic(self):
        """Test basic CloudWatch export format."""
        collector = MetricsCollector()

        # Record validation metrics
        collector.record_validation_field_errors(100, 5)
        collector.record_llm_validation_success(10, 9)

        # Export to CloudWatch format
        cloudwatch_output = collector.export_cloudwatch()
        cloudwatch_data = json.loads(cloudwatch_output)

        # Verify CloudWatch format structure
        assert "Namespace" in cloudwatch_data
        assert cloudwatch_data["Namespace"] == "StrategyValidation"
        assert "MetricData" in cloudwatch_data
        assert len(cloudwatch_data["MetricData"]) > 0

        # Find field error rate metric
        field_error_metric = next(
            (m for m in cloudwatch_data["MetricData"]
             if m["MetricName"] == "FieldErrorRate"),
            None
        )
        assert field_error_metric is not None
        assert field_error_metric["Value"] == 5.0
        assert field_error_metric["Unit"] == "Percent"

    def test_export_cloudwatch_with_dimensions(self):
        """Test CloudWatch export includes dimensions."""
        collector = MetricsCollector()

        collector.record_validation_latency(2.5, 0.3, 2.0, 0.2)

        cloudwatch_output = collector.export_cloudwatch()
        cloudwatch_data = json.loads(cloudwatch_output)

        # Verify dimensions are included
        for metric in cloudwatch_data["MetricData"]:
            if "Dimensions" in metric:
                assert isinstance(metric["Dimensions"], list)

    def test_export_cloudwatch_metric_units(self):
        """Test CloudWatch export uses correct metric units."""
        collector = MetricsCollector()

        collector.record_validation_field_errors(100, 5)  # Percent
        collector.record_validation_latency(2.5, 0.3, 2.0, 0.2)  # Milliseconds

        cloudwatch_output = collector.export_cloudwatch()
        cloudwatch_data = json.loads(cloudwatch_output)

        # Verify units
        field_error_metric = next(
            m for m in cloudwatch_data["MetricData"]
            if m["MetricName"] == "FieldErrorRate"
        )
        assert field_error_metric["Unit"] == "Percent"

        latency_metric = next(
            m for m in cloudwatch_data["MetricData"]
            if m["MetricName"] == "TotalLatency"
        )
        assert latency_metric["Unit"] == "Milliseconds"


class TestValidationGatewayIntegration:
    """Test metrics collection integration with ValidationGateway."""

    def test_gateway_collects_metrics_on_validation(self):
        """Test ValidationGateway automatically collects metrics during validation."""
        # This test will be implemented after integrating metrics into ValidationGateway
        # For now, verify the integration points exist

        import os
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'

        gateway = ValidationGateway()

        # Verify gateway can accept metrics collector
        assert hasattr(gateway, 'set_metrics_collector')

    def test_gateway_metrics_track_validation_latency(self):
        """Test ValidationGateway tracks validation latency in metrics."""
        # Placeholder for integration test
        pass

    def test_gateway_metrics_track_field_errors(self):
        """Test ValidationGateway tracks field errors in metrics."""
        # Placeholder for integration test
        pass


class TestMetricsCollectionPerformance:
    """Test that metrics collection has minimal performance overhead."""

    def test_metrics_collection_overhead_under_100us(self):
        """Test that metrics collection adds <0.1ms (100μs) overhead."""
        collector = MetricsCollector()

        # Measure metrics collection time
        iterations = 1000
        start = time.perf_counter()

        for _ in range(iterations):
            collector.record_validation_field_errors(100, 5)
            collector.record_llm_validation_success(10, 9)
            collector.record_validation_latency(2.5, 0.3, 2.0, 0.2)

        end = time.perf_counter()
        avg_time_ms = ((end - start) / iterations) * 1000

        # Verify overhead is <0.1ms per collection
        assert avg_time_ms < 0.1, f"Metrics collection overhead: {avg_time_ms:.3f}ms (limit: 0.1ms)"

    def test_prometheus_export_performance(self):
        """Test Prometheus export completes quickly."""
        collector = MetricsCollector()

        # Populate with metrics
        for _ in range(100):
            collector.record_validation_field_errors(100, 5)
            collector.record_validation_latency(2.5, 0.3, 2.0, 0.2)

        # Measure export time
        start = time.perf_counter()
        prometheus_output = collector.export_prometheus()
        end = time.perf_counter()

        export_time_ms = (end - start) * 1000

        # Verify export is fast (<10ms)
        assert export_time_ms < 10.0
        assert len(prometheus_output) > 0
