"""Comprehensive validation latency testing for Task 6.4

Tests validation performance across all 3 layers under various workloads:
- Simple strategies: <2ms
- Complex strategies: <5ms
- Nested strategies: <8ms
- Stress test (100 validations): Average <10ms
- 99th percentile: <10ms
- Individual layer performance (Layer 1: <1μs, Layer 2: <5ms, Layer 3: <5ms)

Requirements:
- NFR-P1: Total validation latency <10ms
- Layer 1: <1μs (nanosecond-level field lookups)
- Layer 2: <5ms (AST parsing and field validation)
- Layer 3: <5ms (YAML structure validation)
"""

import time
import pytest
import os
from typing import Dict, Any, List
from src.validation.gateway import ValidationGateway
from src.config.data_fields import DataFieldManifest


class TestValidationPerformance:
    """Task 6.4: Comprehensive validation performance testing"""

    @pytest.fixture(autouse=True)
    def setup_layers(self):
        """Enable all validation layers for performance testing"""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'
        yield
        # Cleanup
        os.environ.pop('ENABLE_VALIDATION_LAYER1', None)
        os.environ.pop('ENABLE_VALIDATION_LAYER2', None)
        os.environ.pop('ENABLE_VALIDATION_LAYER3', None)

    def test_simple_strategy_validation_under_2ms(self):
        """
        GIVEN a simple strategy with basic field usage
        WHEN validating through all 3 layers
        THEN total latency should be <2ms
        """
        gateway = ValidationGateway()

        # Simple strategy: basic field access, no complex logic
        simple_code = """
def strategy(data):
    close = data.get('close')
    return close > 100
"""

        # Simple YAML
        simple_yaml: Dict[str, Any] = {
            "name": "Simple Strategy",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [{"name": "threshold", "type": "int", "value": 100}],
            "logic": {"entry": "close > 100", "exit": "close < 90"}
        }

        # Measure total validation time
        start_time = time.perf_counter()

        # Layer 3: YAML validation
        yaml_errors = gateway.validate_yaml(simple_yaml)

        # Layer 2: Code validation
        code_result = gateway.validate_strategy(simple_code)

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        # Assert validation succeeded
        assert len(yaml_errors) == 0
        assert code_result.is_valid

        # Assert performance: simple strategy <2ms
        assert latency_ms < 2.0, f"Simple strategy validation took {latency_ms:.3f}ms, expected <2ms"

    def test_complex_strategy_validation_under_5ms(self):
        """
        GIVEN a complex strategy with multiple fields and logic
        WHEN validating through all 3 layers
        THEN total latency should be <5ms
        """
        gateway = ValidationGateway()

        # Complex strategy: multiple fields, conditions, calculations
        complex_code = """
def strategy(data):
    close = data.get('close')
    volume = data.get('volume')
    open_price = data.get('open')
    high = data.get('high')
    low = data.get('low')

    # Multiple conditions
    price_momentum = (close - open_price) / open_price
    volume_spike = volume > volume * 1.5
    price_range = (high - low) / low

    return (price_momentum > 0.02 and
            volume_spike and
            price_range > 0.03 and
            close > 100)
"""

        # Complex YAML with multiple parameters
        complex_yaml: Dict[str, Any] = {
            "name": "Complex Strategy",
            "type": "factor_graph",
            "required_fields": ["close", "volume", "open", "high", "low"],
            "parameters": [
                {"name": "momentum_threshold", "type": "float", "value": 0.02, "range": [0.01, 0.1]},
                {"name": "volume_multiplier", "type": "float", "value": 1.5, "range": [1.0, 3.0]},
                {"name": "range_threshold", "type": "float", "value": 0.03, "range": [0.01, 0.1]},
                {"name": "price_threshold", "type": "int", "value": 100, "range": [50, 200]}
            ],
            "logic": {
                "entry": "(close - open) / open > 0.02 and volume > 1000",
                "exit": "close < 90"
            }
        }

        # Measure total validation time
        start_time = time.perf_counter()

        # Layer 3: YAML validation
        yaml_errors = gateway.validate_yaml(complex_yaml)

        # Layer 2: Code validation
        code_result = gateway.validate_strategy(complex_code)

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        # Assert validation succeeded
        assert len(yaml_errors) == 0
        assert code_result.is_valid

        # Assert performance: complex strategy <5ms
        assert latency_ms < 5.0, f"Complex strategy validation took {latency_ms:.3f}ms, expected <5ms"

    def test_nested_strategy_validation_under_8ms(self):
        """
        GIVEN a nested strategy with complex logic and calculations
        WHEN validating through all 3 layers
        THEN total latency should be <8ms
        """
        gateway = ValidationGateway()

        # Nested strategy: nested conditions, multiple calculations
        nested_code = """
def strategy(data):
    close = data.get('close')
    volume = data.get('volume')
    open_price = data.get('open')
    high = data.get('high')
    low = data.get('low')

    # Nested calculations
    if close > open_price:
        momentum = (close - open_price) / open_price
        if momentum > 0.02:
            volume_ratio = volume / (volume * 0.5)
            if volume_ratio > 1.5:
                price_range = (high - low) / low
                if price_range > 0.03:
                    if close > 100:
                        return True

    return False
"""

        # Nested YAML with constraints
        nested_yaml: Dict[str, Any] = {
            "name": "Nested Strategy",
            "type": "factor_graph",
            "required_fields": ["close", "volume", "open", "high", "low"],
            "parameters": [
                {"name": "momentum_threshold", "type": "float", "value": 0.02, "range": [0.01, 0.1]},
                {"name": "volume_multiplier", "type": "float", "value": 1.5, "range": [1.0, 3.0]},
                {"name": "range_threshold", "type": "float", "value": 0.03, "range": [0.01, 0.1]},
                {"name": "price_threshold", "type": "int", "value": 100, "range": [50, 200]}
            ],
            "logic": {
                "entry": "(close - open) / open > 0.02 and volume > 1000",
                "exit": "close < 90",
                "dependencies": ["close", "volume", "open"]
            },
            "constraints": [
                {
                    "type": "field_dependency",
                    "condition": "close > open",
                    "severity": "critical",
                    "message": "Close must be greater than open"
                },
                {
                    "type": "volume_check",
                    "condition": "volume > 0",
                    "severity": "high",
                    "message": "Volume must be positive"
                }
            ]
        }

        # Measure total validation time
        start_time = time.perf_counter()

        # Layer 3: YAML validation (more complex with constraints)
        yaml_errors = gateway.validate_yaml(nested_yaml)

        # Layer 2: Code validation (more complex nested logic)
        code_result = gateway.validate_strategy(nested_code)

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        # Assert validation succeeded
        assert len(yaml_errors) == 0
        assert code_result.is_valid

        # Assert performance: nested strategy <8ms
        assert latency_ms < 8.0, f"Nested strategy validation took {latency_ms:.3f}ms, expected <8ms"

    def test_stress_test_100_validations_average_under_10ms(self):
        """
        GIVEN 100 strategy validations (mix of simple, complex, nested)
        WHEN validating all strategies
        THEN average latency should be <10ms per validation
        """
        gateway = ValidationGateway()

        # Mix of strategies (33 simple, 34 complex, 33 nested)
        simple_code = "def strategy(data): return data.get('close') > 100"
        complex_code = """
def strategy(data):
    close = data.get('close')
    volume = data.get('volume')
    return close > 100 and volume > 1000
"""
        nested_code = """
def strategy(data):
    if data.get('close') > data.get('open'):
        if data.get('volume') > 1000:
            return True
    return False
"""

        # Simple YAML
        simple_yaml: Dict[str, Any] = {
            "name": "Simple",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [{"name": "p", "type": "int", "value": 100}],
            "logic": {"entry": "close > 100", "exit": "close < 90"}
        }

        # Complex YAML
        complex_yaml: Dict[str, Any] = {
            "name": "Complex",
            "type": "factor_graph",
            "required_fields": ["close", "volume"],
            "parameters": [
                {"name": "p1", "type": "int", "value": 100},
                {"name": "p2", "type": "int", "value": 1000}
            ],
            "logic": {"entry": "close > 100 and volume > 1000", "exit": "close < 90"}
        }

        # Nested YAML
        nested_yaml: Dict[str, Any] = {
            "name": "Nested",
            "type": "factor_graph",
            "required_fields": ["close", "volume", "open"],
            "parameters": [{"name": "p", "type": "int", "value": 100}],
            "logic": {
                "entry": "close > open and volume > 1000",
                "exit": "close < 90",
                "dependencies": ["close", "open"]
            },
            "constraints": [
                {
                    "type": "check",
                    "condition": "close > open",
                    "severity": "high",
                    "message": "Check"
                }
            ]
        }

        # Run 100 validations
        iterations = 100
        latencies: List[float] = []

        for i in range(iterations):
            # Alternate between strategy types
            if i % 3 == 0:
                code = simple_code
                yaml_dict = simple_yaml
            elif i % 3 == 1:
                code = complex_code
                yaml_dict = complex_yaml
            else:
                code = nested_code
                yaml_dict = nested_yaml

            # Measure single validation
            start_time = time.perf_counter()

            yaml_errors = gateway.validate_yaml(yaml_dict)
            code_result = gateway.validate_strategy(code)

            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

        # Calculate average
        avg_latency = sum(latencies) / len(latencies)

        # Assert performance: average <10ms
        assert avg_latency < 10.0, f"Average validation latency {avg_latency:.3f}ms, expected <10ms"

    def test_99th_percentile_under_10ms(self):
        """
        GIVEN 1000 strategy validations
        WHEN measuring p50, p95, p99 latencies
        THEN p99 should be <10ms
        """
        gateway = ValidationGateway()

        # Use complex strategy for percentile testing
        code = """
def strategy(data):
    close = data.get('close')
    volume = data.get('volume')
    return close > 100 and volume > 1000
"""

        yaml_dict: Dict[str, Any] = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close", "volume"],
            "parameters": [{"name": "p", "type": "int", "value": 100}],
            "logic": {"entry": "close > 100", "exit": "close < 90"}
        }

        # Collect latencies
        iterations = 1000
        latencies: List[float] = []

        for _ in range(iterations):
            start_time = time.perf_counter()

            gateway.validate_yaml(yaml_dict)
            gateway.validate_strategy(code)

            end_time = time.perf_counter()
            latencies.append((end_time - start_time) * 1000)

        # Sort and calculate percentiles
        latencies.sort()
        p50 = latencies[int(iterations * 0.50)]
        p95 = latencies[int(iterations * 0.95)]
        p99 = latencies[int(iterations * 0.99)]

        # Assert performance targets
        assert p50 < 10.0, f"p50 {p50:.3f}ms exceeds 10ms"
        assert p95 < 10.0, f"p95 {p95:.3f}ms exceeds 10ms"
        assert p99 < 10.0, f"p99 {p99:.3f}ms exceeds 10ms"

    def test_layer1_performance_under_1us(self):
        """
        GIVEN Layer 1 (DataFieldManifest) field validation
        WHEN validating field names
        THEN latency should be <1μs (nanosecond-level dict lookups)
        """
        manifest = DataFieldManifest()

        # Test field validation performance
        iterations = 10000
        start_time = time.perf_counter()

        for _ in range(iterations):
            # Valid field
            is_valid, _ = manifest.validate_field_with_suggestion('close')
            assert is_valid

            # Invalid field
            is_valid, _ = manifest.validate_field_with_suggestion('invalid_field')
            assert not is_valid

        end_time = time.perf_counter()
        total_time_us = (end_time - start_time) * 1_000_000  # Convert to microseconds
        avg_time_us = total_time_us / (iterations * 2)  # 2 validations per iteration

        # Assert performance: <1μs per validation
        assert avg_time_us < 1.0, f"Layer 1 validation took {avg_time_us:.3f}μs, expected <1μs"

    def test_layer2_performance_under_5ms(self):
        """
        GIVEN Layer 2 (FieldValidator) code validation
        WHEN validating strategy code
        THEN latency should be <5ms
        """
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
        gateway = ValidationGateway()

        # Complex code for Layer 2 testing
        code = """
def strategy(data):
    close = data.get('close')
    volume = data.get('volume')
    open_price = data.get('open')
    high = data.get('high')
    low = data.get('low')

    momentum = (close - open_price) / open_price
    volume_spike = volume > 1000
    price_range = (high - low) / low

    return momentum > 0.02 and volume_spike and price_range > 0.03
"""

        # Measure Layer 2 performance
        iterations = 100
        latencies: List[float] = []

        for _ in range(iterations):
            start_time = time.perf_counter()
            result = gateway.validate_strategy(code)
            end_time = time.perf_counter()

            latencies.append((end_time - start_time) * 1000)
            assert result.is_valid

        avg_latency = sum(latencies) / len(latencies)

        # Assert performance: <5ms
        assert avg_latency < 5.0, f"Layer 2 validation took {avg_latency:.3f}ms, expected <5ms"

    def test_layer3_performance_under_5ms(self):
        """
        GIVEN Layer 3 (SchemaValidator) YAML validation
        WHEN validating YAML structure
        THEN latency should be <5ms
        """
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'
        gateway = ValidationGateway()

        # Complex YAML for Layer 3 testing
        yaml_dict: Dict[str, Any] = {
            "name": "Complex Strategy",
            "type": "factor_graph",
            "description": "A complex strategy with multiple parameters and constraints",
            "required_fields": ["close", "volume", "open", "high", "low"],
            "optional_fields": ["vwap", "twap"],
            "parameters": [
                {"name": "momentum_threshold", "type": "float", "value": 0.02, "range": [0.01, 0.1]},
                {"name": "volume_multiplier", "type": "float", "value": 1.5, "range": [1.0, 3.0]},
                {"name": "range_threshold", "type": "float", "value": 0.03, "range": [0.01, 0.1]},
                {"name": "price_threshold", "type": "int", "value": 100, "range": [50, 200]}
            ],
            "logic": {
                "entry": "(close - open) / open > 0.02 and volume > 1000",
                "exit": "close < 90",
                "dependencies": ["close", "volume", "open"]
            },
            "constraints": [
                {
                    "type": "field_dependency",
                    "condition": "close > open",
                    "severity": "critical",
                    "message": "Close must be greater than open"
                },
                {
                    "type": "volume_check",
                    "condition": "volume > 0",
                    "severity": "high",
                    "message": "Volume must be positive"
                },
                {
                    "type": "range_check",
                    "condition": "high >= low",
                    "severity": "critical",
                    "message": "High must be >= low"
                }
            ],
            "coverage_percentage": 85.5
        }

        # Measure Layer 3 performance
        iterations = 100
        latencies: List[float] = []

        for _ in range(iterations):
            start_time = time.perf_counter()
            errors = gateway.validate_yaml(yaml_dict)
            end_time = time.perf_counter()

            latencies.append((end_time - start_time) * 1000)
            assert len(errors) == 0

        avg_latency = sum(latencies) / len(latencies)

        # Assert performance: <5ms
        assert avg_latency < 5.0, f"Layer 3 validation took {avg_latency:.3f}ms, expected <5ms"

    def test_total_validation_latency_under_10ms(self):
        """
        GIVEN all 3 validation layers enabled
        WHEN validating complete strategy (YAML + Code)
        THEN total latency (Layer 1 + Layer 2 + Layer 3) should be <10ms
        """
        gateway = ValidationGateway()

        # Complete strategy validation
        code = """
def strategy(data):
    close = data.get('close')
    volume = data.get('volume')
    open_price = data.get('open')

    momentum = (close - open_price) / open_price
    volume_spike = volume > 1000

    return momentum > 0.02 and volume_spike and close > 100
"""

        yaml_dict: Dict[str, Any] = {
            "name": "Complete Strategy",
            "type": "factor_graph",
            "required_fields": ["close", "volume", "open"],
            "parameters": [
                {"name": "momentum_threshold", "type": "float", "value": 0.02},
                {"name": "volume_threshold", "type": "int", "value": 1000},
                {"name": "price_threshold", "type": "int", "value": 100}
            ],
            "logic": {
                "entry": "(close - open) / open > 0.02 and volume > 1000",
                "exit": "close < 90"
            }
        }

        # Measure total validation time (all 3 layers)
        iterations = 100
        latencies: List[float] = []

        for _ in range(iterations):
            start_time = time.perf_counter()

            # Layer 3: YAML validation
            yaml_errors = gateway.validate_yaml(yaml_dict)

            # Layer 2: Code validation (includes Layer 1 field lookups)
            code_result = gateway.validate_strategy(code)

            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

            # Assert validation succeeded
            assert len(yaml_errors) == 0
            assert code_result.is_valid

        # Calculate average and percentiles
        avg_latency = sum(latencies) / len(latencies)
        latencies.sort()
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]

        # Assert NFR-P1: Total validation latency <10ms
        assert avg_latency < 10.0, f"Average total latency {avg_latency:.3f}ms, expected <10ms (NFR-P1)"
        assert p95 < 10.0, f"p95 total latency {p95:.3f}ms, expected <10ms"
        assert p99 < 10.0, f"p99 total latency {p99:.3f}ms, expected <10ms"
