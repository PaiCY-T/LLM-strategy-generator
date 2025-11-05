#!/usr/bin/env python3
"""
Simplified Task 12 test runner.
Creates temporary YAML config to enable LLM, then runs test.
"""

import sys
import os
import time
from unittest.mock import Mock, patch
import random
import tempfile
import yaml

# Add artifacts/working/modules to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'artifacts/working/modules'))

from autonomous_loop import AutonomousLoop


def run_task12_test():
    """Run Task 12: 10 iterations with LLM enabled at 20% innovation rate."""

    print("\n" + "="*80)
    print("TASK 12: 10 Iterations with LLM Enabled (innovation_rate=0.20)")
    print("="*80)

    # Mock LLM strategies
    mock_llm_strategies = [
        """
def strategy(data):
    # LLM-generated fundamental strategy
    roe = data.get('fundamental_features:ROE稅後')
    revenue_growth = data.get('fundamental_features:營收成長率')
    return (roe > 18) & (revenue_growth > 0.15)
""",
        """
def strategy(data):
    # LLM-generated momentum strategy
    price_change = data.get('price_features:收盤價(元)').pct_change(20)
    volume = data.get('price_features:成交股數')
    return (price_change > 0.10) & (volume > volume.rolling(60).mean())
""",
    ]

    mock_factor_strategy = "def strategy(data): return data.get('fundamental_features:ROE稅後') > 15"

    # Create temporary YAML config file with LLM enabled
    config_content = """
llm:
  enabled: true
  provider: gemini
  model: gemini-2.0-flash
  innovation_rate: 0.20
  timeout: 60
  max_tokens: 2000
  temperature: 0.7

sandbox:
  enabled: false

anti_churn:
  probation_period: 2
  probation_threshold: 0.10
  post_probation_threshold: 0.05
"""

    # Write temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_config_path = f.name

    try:
        start_time = time.time()

        # Patch the config path to use our temporary file
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True

            with patch('os.path.abspath') as mock_abspath:
                # Make abspath return our temp file path
                def mock_abspath_impl(path):
                    if 'learning_system.yaml' in path:
                        return temp_config_path
                    return os.path.abspath(path)

                mock_abspath.side_effect = mock_abspath_impl

                # Patch event logger
                with patch('autonomous_loop.get_event_logger') as mock_logger:
                    mock_logger.return_value = Mock()

                    # Mock InnovationEngine
                    with patch('autonomous_loop.InnovationEngine') as mock_engine_class:
                        mock_engine = Mock()

                        # Track LLM call count
                        llm_call_count = [0]

                        def llm_side_effect(*args, **kwargs):
                            """Cycle through mock LLM responses."""
                            response = mock_llm_strategies[llm_call_count[0] % len(mock_llm_strategies)]
                            llm_call_count[0] += 1
                            return response

                        mock_engine.generate_innovation.side_effect = llm_side_effect

                        # Mock statistics and costs
                        def get_stats():
                            return {
                                'total_attempts': llm_call_count[0],
                                'successful_generations': llm_call_count[0],
                                'success_rate': 1.0
                            }

                        def get_cost():
                            return {
                                'total_cost_usd': llm_call_count[0] * 0.001234,
                                'total_tokens': llm_call_count[0] * 600,
                                'successful_generations': llm_call_count[0],
                                'average_cost_per_success': 0.001234
                            }

                        mock_engine.get_statistics.side_effect = get_stats
                        mock_engine.get_cost_report.side_effect = get_cost
                        mock_engine_class.return_value = mock_engine

                        # Mock Factor Graph
                        with patch('autonomous_loop.generate_strategy') as mock_generate:
                            mock_generate.return_value = mock_factor_strategy

                            # Mock validation
                            with patch('autonomous_loop.validate_code') as mock_validate:
                                mock_validate.return_value = (True, [])

                                # Mock execution with varying metrics
                                def mock_execute_with_metrics(code, *args, **kwargs):
                                    sharpe = 0.7 + random.random() * 0.3  # 0.7 to 1.0
                                    return (True, {
                                        'sharpe_ratio': sharpe,
                                        'annual_return': 0.15 + random.random() * 0.15,
                                        'max_drawdown': -0.10 - random.random() * 0.10,
                                        'win_rate': 0.50 + random.random() * 0.15
                                    }, None)

                                with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                                    mock_execute.side_effect = mock_execute_with_metrics

                                    # Set random seed for reproducibility
                                    random.seed(42)

                                    # Create loop with 10 iterations
                                    loop = AutonomousLoop(max_iterations=10)

                                    # Verify LLM is enabled
                                    print(f"\nLLM enabled: {loop.llm_enabled}")
                                    print(f"Innovation rate: {loop.innovation_rate}")
                                    print(f"Innovation engine: {loop.innovation_engine is not None}")

                                    # Run 10 iterations
                                    print("\nRunning 10 iterations...")
                                    success_count = 0
                                    for i in range(10):
                                        success, status = loop.run_iteration(i, data=None)
                                        if success:
                                            success_count += 1

                                        if (i + 1) % 2 == 0:
                                            print(f"  Completed {i + 1}/10 iterations...")

        # Calculate execution time
        execution_time = time.time() - start_time

        # Get final statistics
        llm_stats = loop.get_llm_statistics()

        # Calculate metrics
        llm_total_attempts = llm_stats['llm_innovations'] + llm_stats['llm_fallbacks']
        success_rate = success_count / 10
        llm_usage_percent = (llm_total_attempts / 10) * 100
        factor_graph_percent = (llm_stats['factor_mutations'] / 10) * 100

        # Print detailed results
        print("\n" + "="*80)
        print("TASK 12 TEST RESULTS")
        print("="*80)
        print(f"Total iterations: 10")
        print(f"Successful: {success_count}")
        print(f"Success rate: {success_rate * 100:.1f}%")
        print(f"\nLLM Usage:")
        print(f"  LLM innovations: {llm_stats['llm_innovations']}")
        print(f"  LLM fallbacks: {llm_stats['llm_fallbacks']}")
        print(f"  Total LLM attempts: {llm_total_attempts}")
        print(f"  LLM usage %: {llm_usage_percent:.1f}%")
        print(f"\nFactor Graph Usage:")
        print(f"  Factor mutations: {llm_stats['factor_mutations']}")
        print(f"  Factor Graph %: {factor_graph_percent:.1f}%")
        print(f"\nMetrics:")
        print(f"  LLM API failures: {llm_stats['llm_api_failures']}")
        print(f"  Execution time: {execution_time:.2f}s")
        if 'llm_costs' in llm_stats and llm_stats['llm_costs']:
            print(f"  Total cost: ${llm_stats['llm_costs']['total_cost_usd']:.6f}")
        print("="*80)

        # TASK 12 ASSERTIONS
        all_passed = True
        failed_assertions = []

        # 1. All 10 iterations must succeed
        if success_count != 10:
            failed_assertions.append(f"Expected 10 successful iterations, got {success_count}")
            all_passed = False

        # 2. LLM must be enabled
        if not llm_stats['llm_enabled']:
            failed_assertions.append("LLM should be enabled")
            all_passed = False

        # 3. Innovation rate should be 0.20
        if llm_stats['innovation_rate'] != 0.20:
            failed_assertions.append(f"Expected innovation_rate=0.20, got {llm_stats['innovation_rate']}")
            all_passed = False

        # 4. ~20% iterations should use LLM (1-4 out of 10)
        if not (1 <= llm_total_attempts <= 4):
            failed_assertions.append(f"Expected 1-4 LLM attempts (~20%), got {llm_total_attempts}")
            all_passed = False

        # 5. ~80% iterations should use Factor Graph (6-9 out of 10)
        if not (6 <= llm_stats['factor_mutations'] <= 9):
            failed_assertions.append(f"Expected 6-9 Factor Graph mutations (~80%), got {llm_stats['factor_mutations']}")
            all_passed = False

        # 6. LLM + Factor Graph must sum to 10
        total_accounted = llm_stats['llm_innovations'] + llm_stats['factor_mutations']
        if total_accounted != 10:
            failed_assertions.append(f"Total should be 10, got {total_accounted}")
            all_passed = False

        # 7. No API failures
        if llm_stats['llm_api_failures'] != 0:
            failed_assertions.append(f"Expected 0 API failures, got {llm_stats['llm_api_failures']}")
            all_passed = False

        # 8. Execution time should be reasonable
        if execution_time >= 60:
            failed_assertions.append(f"Test took too long: {execution_time:.2f}s")
            all_passed = False

        # Print results
        print("\n" + "="*80)
        print("TASK 12 ASSERTION RESULTS")
        print("="*80)

        if all_passed:
            print("\n✅ TASK 12: ALL ASSERTIONS PASSED")
            print(f"✅ 100% success rate: {success_count}/10 iterations")
            print(f"✅ LLM usage: ~{llm_usage_percent:.0f}% (target: 20%)")
            print(f"✅ Factor Graph: ~{factor_graph_percent:.0f}% (target: 80%)")
            print(f"✅ Execution time: {execution_time:.2f}s")
            print("\n" + "="*80)
            return True
        else:
            print("\n❌ TASK 12: SOME ASSERTIONS FAILED")
            for i, failure in enumerate(failed_assertions, 1):
                print(f"  {i}. {failure}")
            print("\n" + "="*80)
            return False

    finally:
        # Clean up temporary config file
        if os.path.exists(temp_config_path):
            os.unlink(temp_config_path)


if __name__ == '__main__':
    success = run_task12_test()
    sys.exit(0 if success else 1)
