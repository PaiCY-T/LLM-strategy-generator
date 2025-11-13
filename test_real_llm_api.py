#!/usr/bin/env python3
"""
Real LLM API Validation Test

Tests YAML mode with actual API calls to validate >90% success rate.
Measures real costs, performance, and quality.

Usage:
    python3 test_real_llm_api.py --provider gemini --iterations 10
"""

import argparse
import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.innovation.innovation_engine import InnovationEngine
from src.generators.yaml_schema_validator import YAMLSchemaValidator
from src.generators.yaml_to_code_generator import YAMLToCodeGenerator


class RealAPITestResults:
    """Track real API test results."""

    def __init__(self):
        self.attempts = 0
        self.successes = 0
        self.failures = 0
        self.total_cost = 0.0
        self.total_time = 0.0
        self.errors = []
        self.generated_codes = []

    def add_success(self, cost: float, time: float, code: str):
        """Record successful generation."""
        self.attempts += 1
        self.successes += 1
        self.total_cost += cost
        self.total_time += time
        self.generated_codes.append(code)

    def add_failure(self, error: str, cost: float = 0.0, time: float = 0.0):
        """Record failed generation."""
        self.attempts += 1
        self.failures += 1
        self.total_cost += cost
        self.total_time += time
        self.errors.append(error)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        return self.successes / max(1, self.attempts)

    @property
    def avg_cost_per_attempt(self) -> float:
        """Average cost per attempt."""
        return self.total_cost / max(1, self.attempts)

    @property
    def avg_time_per_attempt(self) -> float:
        """Average time per attempt (seconds)."""
        return self.total_time / max(1, self.attempts)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'total_attempts': self.attempts,
            'successes': self.successes,
            'failures': self.failures,
            'success_rate': self.success_rate,
            'total_cost_usd': self.total_cost,
            'avg_cost_per_attempt_usd': self.avg_cost_per_attempt,
            'total_time_seconds': self.total_time,
            'avg_time_per_attempt_seconds': self.avg_time_per_attempt,
            'errors': self.errors,
            'generated_code_count': len(self.generated_codes)
        }


def test_yaml_mode_real_api(provider: str, model: Optional[str], iterations: int) -> RealAPITestResults:
    """
    Test YAML mode with real API calls.

    Args:
        provider: LLM provider ('gemini', 'openrouter', 'openai')
        model: Specific model name (optional, uses provider default if None)
        iterations: Number of generations to attempt

    Returns:
        Test results
    """
    print(f"\n{'='*70}")
    print(f"YAML Mode Real API Validation")
    print(f"{'='*70}")
    print(f"Provider: {provider}")
    print(f"Model: {model or '(default)'}")
    print(f"Iterations: {iterations}")
    print(f"Target: >90% success rate")
    print(f"{'='*70}\n")

    # Initialize InnovationEngine in YAML mode
    print(f"[1/3] Initializing InnovationEngine (YAML mode)...")
    try:
        engine = InnovationEngine(
            provider_name=provider,
            model=model,
            generation_mode='yaml',
            max_retries=3,
            temperature=0.7
        )
        print(f"✅ Engine initialized successfully")
        print(f"   Using model: {engine.provider.model}\n")
    except Exception as e:
        print(f"❌ Failed to initialize engine: {e}")
        sys.exit(1)

    # Test champion metrics (realistic values)
    champion_metrics = {
        'sharpe_ratio': 1.5,
        'annual_return': 0.25,
        'max_drawdown': 0.15,
        'win_rate': 0.55
    }

    # Failure patterns to avoid
    failure_patterns = [
        'overtrading',
        'large_drawdowns',
        'low_sharpe_ratio'
    ]

    results = RealAPITestResults()

    print(f"[2/3] Running {iterations} iterations with real API calls...")
    print(f"{'='*70}\n")

    for i in range(iterations):
        print(f"Iteration {i+1}/{iterations}:")
        start_time = time.time()

        try:
            # Generate innovation
            code = engine.generate_innovation(
                champion_code="",  # Empty for new generation
                champion_metrics=champion_metrics,
                failure_history=None
            )

            elapsed_time = time.time() - start_time

            # Get cost from engine statistics
            stats = engine.get_statistics()
            cost = stats.get('total_cost_usd', 0.0)

            if code:
                # Success
                results.add_success(
                    cost=cost,
                    time=elapsed_time,
                    code=code
                )
                print(f"  ✅ SUCCESS - {elapsed_time:.2f}s, ${cost:.6f}")
                print(f"     Code length: {len(code)} chars")
            else:
                # Failure
                results.add_failure(
                    error="No code generated",
                    cost=cost,
                    time=elapsed_time
                )
                print(f"  ❌ FAILURE - No code generated")

        except Exception as e:
            elapsed_time = time.time() - start_time
            results.add_failure(
                error=str(e),
                time=elapsed_time
            )
            print(f"  ❌ ERROR - {e}")

        # Progress indicator
        current_rate = results.success_rate * 100
        print(f"     Progress: {results.successes}/{results.attempts} " +
              f"({current_rate:.1f}%)\n")

        # Small delay to avoid rate limits
        if i < iterations - 1:
            time.sleep(1)

    print(f"{'='*70}")
    print(f"[3/3] Test Complete\n")

    return results


def print_results(results: RealAPITestResults):
    """Print formatted test results."""
    print(f"\n{'='*70}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*70}\n")

    # Success metrics
    print(f"Success Metrics:")
    print(f"  Total Attempts:  {results.attempts}")
    print(f"  Successes:       {results.successes}")
    print(f"  Failures:        {results.failures}")
    success_rate = results.success_rate * 100
    print(f"  Success Rate:    {success_rate:.1f}%")

    # Target validation
    target_met = "✅ TARGET MET" if success_rate >= 90 else "❌ BELOW TARGET"
    print(f"  Target (>90%):   {target_met}\n")

    # Cost metrics
    print(f"Cost Metrics:")
    print(f"  Total Cost:      ${results.total_cost:.6f}")
    print(f"  Avg per Attempt: ${results.avg_cost_per_attempt:.6f}\n")

    # Performance metrics
    print(f"Performance Metrics:")
    print(f"  Total Time:      {results.total_time:.2f}s")
    print(f"  Avg per Attempt: {results.avg_time_per_attempt:.2f}s")
    print(f"  Throughput:      {results.attempts / results.total_time:.2f} gen/s\n")

    # Generated code stats
    if results.generated_codes:
        avg_code_length = sum(len(c) for c in results.generated_codes) / len(results.generated_codes)
        print(f"Generated Code:")
        print(f"  Total Generated: {len(results.generated_codes)}")
        print(f"  Avg Length:      {avg_code_length:.0f} chars\n")

    # Errors (if any)
    if results.errors:
        print(f"Errors ({len(results.errors)}):")
        error_counts = {}
        for error in results.errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {error}: {count}x")
        print()

    print(f"{'='*70}\n")


def save_results(results: RealAPITestResults, provider: str, model: str, output_file: str):
    """Save results to JSON file."""
    data = {
        'test_type': 'real_llm_api_validation',
        'provider': provider,
        'model': model,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'results': results.to_dict()
    }

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Results saved to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Test YAML mode with real LLM API calls'
    )
    parser.add_argument(
        '--provider',
        default='openrouter',
        choices=['gemini', 'openrouter', 'openai'],
        help='LLM provider to test (default: openrouter)'
    )
    parser.add_argument(
        '--model',
        default=None,
        help='Specific model name (uses provider default if not specified). ' +
             'Examples: x-ai/grok-4-fast, anthropic/claude-3.5-sonnet, google/gemini-2.0-flash-exp'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=10,
        help='Number of generation iterations (default: 10)'
    )
    parser.add_argument(
        '--output',
        default='real_llm_api_validation_results.json',
        help='Output JSON file (default: real_llm_api_validation_results.json)'
    )

    args = parser.parse_args()

    # Run test
    results = test_yaml_mode_real_api(
        provider=args.provider,
        model=args.model,
        iterations=args.iterations
    )

    # Print results
    print_results(results)

    # Save results
    save_results(results, args.provider, args.model or 'default', args.output)

    # Exit code based on success
    if results.success_rate >= 0.90:
        print("✅ TEST PASSED - Success rate ≥90%")
        sys.exit(0)
    else:
        print(f"❌ TEST FAILED - Success rate {results.success_rate*100:.1f}% < 90%")
        sys.exit(1)


if __name__ == '__main__':
    main()
