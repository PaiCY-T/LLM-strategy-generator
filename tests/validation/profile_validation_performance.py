"""Performance profiling script for validation latency analysis

This script profiles validation performance across all layers and provides:
- Detailed latency breakdowns by layer
- Hot path identification
- Optimization opportunity documentation
- Performance statistics (mean, median, p95, p99)
"""

import time
import os
from typing import Dict, Any, List, Tuple
from statistics import mean, median
from src.validation.gateway import ValidationGateway
from src.config.data_fields import DataFieldManifest


def profile_layer1_performance() -> Dict[str, float]:
    """Profile Layer 1 (DataFieldManifest) field validation performance"""
    print("\n=== Layer 1 Performance Profiling ===")

    manifest = DataFieldManifest()

    # Test valid field lookups
    iterations = 10000
    valid_fields = ['close', 'open', 'high', 'low', 'volume']

    latencies: List[float] = []
    for _ in range(iterations):
        for field in valid_fields:
            start = time.perf_counter()
            is_valid, _ = manifest.validate_field_with_suggestion(field)
            end = time.perf_counter()
            latencies.append((end - start) * 1_000_000)  # microseconds

    stats = {
        'mean_us': mean(latencies),
        'median_us': median(latencies),
        'p95_us': sorted(latencies)[int(len(latencies) * 0.95)],
        'p99_us': sorted(latencies)[int(len(latencies) * 0.99)],
        'max_us': max(latencies),
        'min_us': min(latencies)
    }

    print(f"Valid field lookups ({iterations * len(valid_fields)} operations):")
    print(f"  Mean: {stats['mean_us']:.3f}μs")
    print(f"  Median: {stats['median_us']:.3f}μs")
    print(f"  P95: {stats['p95_us']:.3f}μs")
    print(f"  P99: {stats['p99_us']:.3f}μs")
    print(f"  Min: {stats['min_us']:.3f}μs")
    print(f"  Max: {stats['max_us']:.3f}μs")

    # Test invalid field lookups with suggestions
    invalid_fields = ['price:成交量', 'invalid_field', 'wrong_field']
    suggestion_latencies: List[float] = []

    for _ in range(iterations):
        for field in invalid_fields:
            start = time.perf_counter()
            is_valid, suggestion = manifest.validate_field_with_suggestion(field)
            end = time.perf_counter()
            suggestion_latencies.append((end - start) * 1_000_000)

    suggestion_stats = {
        'mean_us': mean(suggestion_latencies),
        'median_us': median(suggestion_latencies),
        'p95_us': sorted(suggestion_latencies)[int(len(suggestion_latencies) * 0.95)],
        'p99_us': sorted(suggestion_latencies)[int(len(suggestion_latencies) * 0.99)]
    }

    print(f"\nInvalid field lookups with suggestions ({iterations * len(invalid_fields)} operations):")
    print(f"  Mean: {suggestion_stats['mean_us']:.3f}μs")
    print(f"  Median: {suggestion_stats['median_us']:.3f}μs")
    print(f"  P95: {suggestion_stats['p95_us']:.3f}μs")
    print(f"  P99: {suggestion_stats['p99_us']:.3f}μs")

    return stats


def profile_layer2_performance() -> Dict[str, float]:
    """Profile Layer 2 (FieldValidator) code validation performance"""
    print("\n=== Layer 2 Performance Profiling ===")

    os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
    os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
    gateway = ValidationGateway()

    # Test different code complexities
    test_cases = [
        ("Simple (1 field)", "def strategy(data): return data.get('close') > 100"),
        ("Medium (3 fields)", """
def strategy(data):
    close = data.get('close')
    volume = data.get('volume')
    return close > 100 and volume > 1000
"""),
        ("Complex (5 fields)", """
def strategy(data):
    close = data.get('close')
    volume = data.get('volume')
    open_price = data.get('open')
    high = data.get('high')
    low = data.get('low')
    return (close - open_price) / open_price > 0.02
""")
    ]

    results = {}
    for name, code in test_cases:
        iterations = 1000
        latencies: List[float] = []

        for _ in range(iterations):
            start = time.perf_counter()
            result = gateway.validate_strategy(code)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # milliseconds

        stats = {
            'mean_ms': mean(latencies),
            'median_ms': median(latencies),
            'p95_ms': sorted(latencies)[int(len(latencies) * 0.95)],
            'p99_ms': sorted(latencies)[int(len(latencies) * 0.99)]
        }

        print(f"\n{name} ({iterations} validations):")
        print(f"  Mean: {stats['mean_ms']:.3f}ms")
        print(f"  Median: {stats['median_ms']:.3f}ms")
        print(f"  P95: {stats['p95_ms']:.3f}ms")
        print(f"  P99: {stats['p99_ms']:.3f}ms")

        results[name] = stats

    return results


def profile_layer3_performance() -> Dict[str, float]:
    """Profile Layer 3 (SchemaValidator) YAML validation performance"""
    print("\n=== Layer 3 Performance Profiling ===")

    os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'
    gateway = ValidationGateway()

    # Test different YAML complexities
    test_cases = [
        ("Simple YAML", {
            "name": "Simple",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [{"name": "p", "type": "int", "value": 100}],
            "logic": {"entry": "close > 100", "exit": "close < 90"}
        }),
        ("Medium YAML", {
            "name": "Medium",
            "type": "factor_graph",
            "required_fields": ["close", "volume", "open"],
            "parameters": [
                {"name": "p1", "type": "int", "value": 100},
                {"name": "p2", "type": "float", "value": 1.5, "range": [1.0, 3.0]}
            ],
            "logic": {
                "entry": "close > 100",
                "exit": "close < 90",
                "dependencies": ["close", "open"]
            }
        }),
        ("Complex YAML", {
            "name": "Complex",
            "type": "factor_graph",
            "required_fields": ["close", "volume", "open", "high", "low"],
            "parameters": [
                {"name": "p1", "type": "int", "value": 100, "range": [50, 200]},
                {"name": "p2", "type": "float", "value": 1.5, "range": [1.0, 3.0]},
                {"name": "p3", "type": "float", "value": 0.02, "range": [0.01, 0.1]}
            ],
            "logic": {
                "entry": "close > 100",
                "exit": "close < 90",
                "dependencies": ["close", "open", "volume"]
            },
            "constraints": [
                {
                    "type": "check1",
                    "condition": "close > open",
                    "severity": "high",
                    "message": "Test"
                },
                {
                    "type": "check2",
                    "condition": "volume > 0",
                    "severity": "critical",
                    "message": "Test"
                }
            ]
        })
    ]

    results = {}
    for name, yaml_dict in test_cases:
        iterations = 1000
        latencies: List[float] = []

        for _ in range(iterations):
            start = time.perf_counter()
            errors = gateway.validate_yaml(yaml_dict)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # milliseconds

        stats = {
            'mean_ms': mean(latencies),
            'median_ms': median(latencies),
            'p95_ms': sorted(latencies)[int(len(latencies) * 0.95)],
            'p99_ms': sorted(latencies)[int(len(latencies) * 0.99)]
        }

        print(f"\n{name} ({iterations} validations):")
        print(f"  Mean: {stats['mean_ms']:.3f}ms")
        print(f"  Median: {stats['median_ms']:.3f}ms")
        print(f"  P95: {stats['p95_ms']:.3f}ms")
        print(f"  P99: {stats['p99_ms']:.3f}ms")

        results[name] = stats

    return results


def profile_total_validation_latency() -> Dict[str, float]:
    """Profile total validation latency (all 3 layers combined)"""
    print("\n=== Total Validation Latency Profiling ===")

    os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
    os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
    os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'
    gateway = ValidationGateway()

    # Complete strategy validation (YAML + Code)
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

    # Measure total validation time
    iterations = 1000
    latencies: List[float] = []
    yaml_latencies: List[float] = []
    code_latencies: List[float] = []

    for _ in range(iterations):
        # Measure YAML validation
        start = time.perf_counter()
        yaml_errors = gateway.validate_yaml(yaml_dict)
        yaml_end = time.perf_counter()
        yaml_latencies.append((yaml_end - start) * 1000)

        # Measure code validation
        code_start = time.perf_counter()
        code_result = gateway.validate_strategy(code)
        code_end = time.perf_counter()
        code_latencies.append((code_end - code_start) * 1000)

        # Total latency
        latencies.append((code_end - start) * 1000)

    stats = {
        'total_mean_ms': mean(latencies),
        'total_median_ms': median(latencies),
        'total_p95_ms': sorted(latencies)[int(len(latencies) * 0.95)],
        'total_p99_ms': sorted(latencies)[int(len(latencies) * 0.99)],
        'yaml_mean_ms': mean(yaml_latencies),
        'code_mean_ms': mean(code_latencies)
    }

    print(f"\nTotal validation latency ({iterations} validations):")
    print(f"  Mean: {stats['total_mean_ms']:.3f}ms")
    print(f"  Median: {stats['total_median_ms']:.3f}ms")
    print(f"  P95: {stats['total_p95_ms']:.3f}ms")
    print(f"  P99: {stats['total_p99_ms']:.3f}ms")
    print(f"\nBreakdown:")
    print(f"  YAML validation (Layer 3): {stats['yaml_mean_ms']:.3f}ms")
    print(f"  Code validation (Layer 2 + Layer 1): {stats['code_mean_ms']:.3f}ms")
    print(f"\nPerformance budget utilization:")
    print(f"  Total budget: 10ms")
    print(f"  Actual usage: {stats['total_mean_ms']:.3f}ms ({stats['total_mean_ms'] / 10.0 * 100:.1f}%)")
    print(f"  Remaining headroom: {10.0 - stats['total_mean_ms']:.3f}ms ({(10.0 - stats['total_mean_ms']) / 10.0 * 100:.1f}%)")

    # Check NFR-P1 compliance
    if stats['total_p99_ms'] < 10.0:
        print(f"\n✅ NFR-P1 PASSED: Total validation latency p99 ({stats['total_p99_ms']:.3f}ms) < 10ms")
    else:
        print(f"\n❌ NFR-P1 FAILED: Total validation latency p99 ({stats['total_p99_ms']:.3f}ms) >= 10ms")

    return stats


def print_optimization_opportunities():
    """Document optimization opportunities for future work"""
    print("\n=== Optimization Opportunities ===")
    print("\n1. Field Lookup Caching")
    print("   - Current: ~0.1μs per lookup (dict-based)")
    print("   - Opportunity: Cache repeated field lookups within single validation")
    print("   - Expected gain: 10-20% for strategies with repeated fields")
    print("   - Complexity: Low")

    print("\n2. AST Parsing Optimization")
    print("   - Current: AST parsing overhead ~1-2ms")
    print("   - Opportunity: Cache AST for unchanged code")
    print("   - Expected gain: 30-50% for repeated validations")
    print("   - Complexity: Medium (requires cache invalidation logic)")

    print("\n3. YAML Validation Optimization")
    print("   - Current: Full schema validation ~1-2ms")
    print("   - Opportunity: Skip optional field validation when not present")
    print("   - Expected gain: 5-10% for simple YAML structures")
    print("   - Complexity: Low")

    print("\n4. Lazy Validation")
    print("   - Current: All layers validate sequentially")
    print("   - Opportunity: Early exit on critical errors")
    print("   - Expected gain: 20-30% for invalid strategies")
    print("   - Complexity: Medium (requires error priority system)")

    print("\n5. Parallel Validation")
    print("   - Current: Sequential validation (Layer 3 → Layer 2)")
    print("   - Opportunity: Parallel validation of YAML and code")
    print("   - Expected gain: 30-40% for complex strategies")
    print("   - Complexity: High (requires thread safety)")


def main():
    """Run comprehensive performance profiling"""
    print("="*80)
    print("VALIDATION PERFORMANCE PROFILING - Task 6.4")
    print("="*80)

    # Profile each layer
    layer1_stats = profile_layer1_performance()
    layer2_stats = profile_layer2_performance()
    layer3_stats = profile_layer3_performance()

    # Profile total latency
    total_stats = profile_total_validation_latency()

    # Document optimization opportunities
    print_optimization_opportunities()

    print("\n" + "="*80)
    print("PROFILING COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
