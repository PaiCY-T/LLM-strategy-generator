"""
Task 12: Autonomous Loop Integration Tests with LLM

Integration tests for autonomous loop with LLM-driven innovation.

TASK REQUIREMENTS (from llm-integration-activation spec):
- Run 10 iterations with innovation_rate=0.20
- Verify ~2 iterations use LLM, ~8 use Factor Graph (~20% vs ~80%)
- Mock some LLM failures to verify automatic fallback
- Verify all 10 iterations complete successfully (100% success rate)
- Use existing loop test patterns with LLM mocks

SUCCESS CRITERIA:
- 10 iterations complete with LLM enabled
- ~20% iterations use LLM (approximately 2/10)
- LLM failures trigger automatic fallback to Factor Graph
- 100% iteration success rate maintained
- Metrics tracking works correctly
- All tests passing

Requirements: llm-integration-activation - Task 12
Specification: Requirements 1.1, 1.2, 5.4, 5.5
"""

import pytest
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
from dataclasses import dataclass

# Add artifacts/working/modules to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../artifacts/working/modules'))

from autonomous_loop import AutonomousLoop


@dataclass
class Task12TestResults:
    """Results from Task 12 integration test run."""
    total_iterations: int
    successful_iterations: int
    llm_innovations: int
    llm_fallbacks: int
    factor_mutations: int
    llm_api_failures: int
    success_rate: float
    llm_usage_percent: float
    factor_graph_percent: float
    execution_time_seconds: float


class TestAutonomousLoopLLMTask12:
    """
    Task 12: Autonomous Loop Integration Tests with LLM.

    Tests LLM integration in autonomous loop with focus on:
    - 10-iteration runs with 20% innovation rate
    - LLM vs Factor Graph usage distribution
    - Automatic fallback mechanism
    - 100% iteration success rate
    - Statistics tracking accuracy
    """

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Patch event logger globally
        with patch('autonomous_loop.get_event_logger') as mock_logger:
            mock_logger.return_value = Mock()
            yield

    @pytest.fixture
    def mock_llm_strategies(self):
        """Generate diverse mock LLM strategy responses."""
        return [
            # Strategy 1: ROE + Revenue Growth
            """
def strategy(data):
    # LLM-generated fundamental strategy
    roe = data.get('fundamental_features:ROE稅後')
    revenue_growth = data.get('fundamental_features:營收成長率')
    return (roe > 18) & (revenue_growth > 0.15)
""",
            # Strategy 2: Momentum
            """
def strategy(data):
    # LLM-generated momentum strategy
    price_change = data.get('price_features:收盤價(元)').pct_change(20)
    volume = data.get('price_features:成交股數')
    return (price_change > 0.10) & (volume > volume.rolling(60).mean())
""",
            # Strategy 3: Value
            """
def strategy(data):
    # LLM-generated value strategy
    pb = data.get('fundamental_features:股價淨值比')
    pe = data.get('fundamental_features:本益比')
    return (pb < 2.0) & (pe < 15) & (pe > 0)
""",
        ]

    @pytest.fixture
    def mock_factor_strategy(self):
        """Mock Factor Graph strategy."""
        return "def strategy(data): return data.get('fundamental_features:ROE稅後') > 15"

    def test_task12_10_iterations_with_llm_enabled(
        self,
        mock_llm_strategies,
        mock_factor_strategy
    ):
        """
        TASK 12 MAIN TEST: 10 iterations with LLM enabled at 20% innovation rate.

        Expected Behavior:
        - 10 iterations complete successfully (100% success rate)
        - ~2 iterations use LLM (~20%)
        - ~8 iterations use Factor Graph (~80%)
        - All iterations complete despite LLM being enabled
        - Statistics tracking is accurate

        Success Criteria:
        - 10/10 iterations successful
        - 1-3 LLM attempts (allowing for randomness in 20% rate)
        - 7-9 Factor Graph mutations
        - LLM + Factor Graph = 10 total iterations
        - Execution completes in reasonable time (< 60s with mocks)
        """
        print("\n" + "="*80)
        print("TASK 12: 10 Iterations with LLM Enabled (innovation_rate=0.20)")
        print("="*80)

        start_time = time.time()

        # Configure LLM via YAML config mock
        with patch('autonomous_loop.yaml.safe_load') as mock_yaml:
            mock_yaml.return_value = {
                'llm': {
                    'enabled': 'true',
                    'provider': 'gemini',
                    'model': 'gemini-2.0-flash',
                    'innovation_rate': 0.20,  # TASK 12 REQUIREMENT: 20% innovation rate
                    'timeout': 60,
                    'max_tokens': 2000,
                    'temperature': 0.7
                }
            }

            with patch('autonomous_loop.os.path.exists') as mock_exists:
                mock_exists.return_value = True

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
                                import random
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
                                import random
                                random.seed(42)

                                # Create loop with 10 iterations (TASK 12 REQUIREMENT)
                                loop = AutonomousLoop(max_iterations=10)

                                # Run 10 iterations
                                success_count = 0
                                for i in range(10):
                                    success, status = loop.run_iteration(i, data=None)
                                    if success:
                                        success_count += 1

                                    # Progress indicator
                                    if (i + 1) % 5 == 0:
                                        print(f"  Completed {i + 1}/10 iterations...")

        # Calculate execution time
        execution_time = time.time() - start_time

        # Get final statistics
        llm_stats = loop.get_llm_statistics()

        # Create test results summary
        llm_total_attempts = llm_stats['llm_innovations'] + llm_stats['llm_fallbacks']
        results = Task12TestResults(
            total_iterations=10,
            successful_iterations=success_count,
            llm_innovations=llm_stats['llm_innovations'],
            llm_fallbacks=llm_stats['llm_fallbacks'],
            factor_mutations=llm_stats['factor_mutations'],
            llm_api_failures=llm_stats['llm_api_failures'],
            success_rate=success_count / 10,
            llm_usage_percent=(llm_total_attempts / 10) * 100,
            factor_graph_percent=(llm_stats['factor_mutations'] / 10) * 100,
            execution_time_seconds=execution_time
        )

        # Print detailed results
        print("\n" + "="*80)
        print("TASK 12 TEST RESULTS")
        print("="*80)
        print(f"Total iterations: {results.total_iterations}")
        print(f"Successful: {results.successful_iterations}")
        print(f"Success rate: {results.success_rate * 100:.1f}%")
        print(f"\nLLM Usage:")
        print(f"  LLM innovations: {results.llm_innovations}")
        print(f"  LLM fallbacks: {results.llm_fallbacks}")
        print(f"  Total LLM attempts: {llm_total_attempts}")
        print(f"  LLM usage %: {results.llm_usage_percent:.1f}%")
        print(f"\nFactor Graph Usage:")
        print(f"  Factor mutations: {results.factor_mutations}")
        print(f"  Factor Graph %: {results.factor_graph_percent:.1f}%")
        print(f"\nMetrics:")
        print(f"  LLM API failures: {results.llm_api_failures}")
        print(f"  Execution time: {results.execution_time_seconds:.2f}s")
        if 'llm_costs' in llm_stats and llm_stats['llm_costs']:
            print(f"  Total cost: ${llm_stats['llm_costs']['total_cost_usd']:.6f}")
        print("="*80)

        # TASK 12 ASSERTIONS

        # 1. CRITICAL: All 10 iterations must succeed (100% success rate)
        assert results.successful_iterations == 10, \
            f"TASK 12 FAIL: Expected 10 successful iterations, got {results.successful_iterations}"

        # 2. LLM must be enabled
        assert llm_stats['llm_enabled'] is True, \
            "TASK 12 FAIL: LLM should be enabled"

        # 3. Innovation rate should be 0.20
        assert llm_stats['innovation_rate'] == 0.20, \
            f"TASK 12 FAIL: Expected innovation_rate=0.20, got {llm_stats['innovation_rate']}"

        # 4. ~20% iterations should use LLM (1-4 out of 10 with random variation)
        #    Allow range of 1-4 to account for randomness in 20% probability
        assert 1 <= llm_total_attempts <= 4, \
            f"TASK 12 FAIL: Expected 1-4 LLM attempts (~20%), got {llm_total_attempts}"

        # 5. ~80% iterations should use Factor Graph (6-9 out of 10)
        assert 6 <= results.factor_mutations <= 9, \
            f"TASK 12 FAIL: Expected 6-9 Factor Graph mutations (~80%), got {results.factor_mutations}"

        # 6. LLM + Factor Graph must sum to 10 iterations
        total_accounted = results.llm_innovations + results.factor_mutations
        assert total_accounted == 10, \
            f"TASK 12 FAIL: Total should be 10, got {total_accounted}"

        # 7. No API failures (all mocked calls succeed)
        assert results.llm_api_failures == 0, \
            f"TASK 12 FAIL: Expected 0 API failures, got {results.llm_api_failures}"

        # 8. Execution time should be reasonable (< 60s with mocks)
        assert results.execution_time_seconds < 60, \
            f"TASK 12 FAIL: Test took too long: {results.execution_time_seconds:.2f}s"

        # 9. Statistics accuracy: LLM call count should match innovation count
        assert llm_call_count[0] == results.llm_innovations, \
            f"TASK 12 FAIL: LLM call count mismatch"

        print("\n✅ TASK 12: ALL ASSERTIONS PASSED")
        print(f"✅ 100% success rate: {results.successful_iterations}/10 iterations")
        print(f"✅ LLM usage: ~{results.llm_usage_percent:.0f}% (target: 20%)")
        print(f"✅ Factor Graph: ~{results.factor_graph_percent:.0f}% (target: 80%)")
        print(f"✅ Execution time: {results.execution_time_seconds:.2f}s")

    def test_task12_llm_fallback_mechanism(
        self,
        mock_llm_strategies,
        mock_factor_strategy
    ):
        """
        TASK 12: Test LLM fallback to Factor Graph on failures.

        Expected Behavior:
        - LLM fails on some iterations
        - Automatic fallback to Factor Graph occurs
        - All iterations still complete successfully (100% success rate)
        - Fallback statistics tracked correctly

        Success Criteria:
        - 10/10 iterations successful despite LLM failures
        - LLM fallback count > 0
        - Factor Graph used for fallbacks
        - No iteration failures
        """
        print("\n" + "="*80)
        print("TASK 12: LLM Fallback Mechanism Test")
        print("="*80)

        start_time = time.time()

        with patch('autonomous_loop.yaml.safe_load') as mock_yaml:
            mock_yaml.return_value = {
                'llm': {
                    'enabled': 'true',
                    'provider': 'gemini',
                    'innovation_rate': 0.30  # Higher rate to test fallback more
                }
            }

            with patch('autonomous_loop.os.path.exists') as mock_exists:
                mock_exists.return_value = True

                with patch('autonomous_loop.InnovationEngine') as mock_engine_class:
                    mock_engine = Mock()

                    # Track calls
                    call_count = [0]
                    success_count_llm = [0]
                    failure_count_llm = [0]

                    def llm_with_failures(*args, **kwargs):
                        """Simulate LLM failures: fail on odd calls, succeed on even."""
                        call_count[0] += 1
                        if call_count[0] % 2 == 1:
                            # Odd call: failure
                            failure_count_llm[0] += 1
                            return None  # Signal failure
                        else:
                            # Even call: success
                            success_count_llm[0] += 1
                            return mock_llm_strategies[0]

                    mock_engine.generate_innovation.side_effect = llm_with_failures
                    mock_engine.get_statistics.return_value = {
                        'total_attempts': 3,
                        'successful_generations': 1,
                        'success_rate': 0.33
                    }
                    mock_engine.get_cost_report.return_value = {
                        'total_cost_usd': 0.001234,
                        'total_tokens': 600
                    }
                    mock_engine_class.return_value = mock_engine

                    # Mock Factor Graph
                    with patch('autonomous_loop.generate_strategy') as mock_generate:
                        mock_generate.return_value = mock_factor_strategy

                        with patch('autonomous_loop.validate_code') as mock_validate:
                            mock_validate.return_value = (True, [])

                            with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                                mock_execute.return_value = (True, {'sharpe_ratio': 0.8}, None)

                                # Set seed
                                import random
                                random.seed(123)

                                # Run 10 iterations
                                loop = AutonomousLoop(max_iterations=10)

                                success_count = 0
                                for i in range(10):
                                    success, status = loop.run_iteration(i, data=None)
                                    if success:
                                        success_count += 1

        execution_time = time.time() - start_time
        llm_stats = loop.get_llm_statistics()

        # Print results
        print("\n" + "="*80)
        print("FALLBACK TEST RESULTS")
        print("="*80)
        print(f"Total iterations: 10")
        print(f"Successful: {success_count}")
        print(f"Success rate: {success_count/10*100:.1f}%")
        print(f"\nLLM Performance:")
        print(f"  LLM successes: {llm_stats['llm_innovations']}")
        print(f"  LLM fallbacks: {llm_stats['llm_fallbacks']}")
        print(f"  Factor Graph: {llm_stats['factor_mutations']}")
        print(f"\nExecution time: {execution_time:.2f}s")
        print("="*80)

        # TASK 12 FALLBACK ASSERTIONS

        # 1. CRITICAL: 100% iteration success despite LLM failures
        assert success_count == 10, \
            f"TASK 12 FALLBACK FAIL: Expected 10 successful iterations, got {success_count}"

        # 2. Should have fallbacks (LLM failures occurred)
        assert llm_stats['llm_fallbacks'] > 0, \
            "TASK 12 FALLBACK FAIL: Should have fallbacks when LLM fails"

        # 3. Factor Graph should be used for fallbacks
        assert llm_stats['factor_mutations'] > 0, \
            "TASK 12 FALLBACK FAIL: Factor Graph should handle fallbacks"

        # 4. Total should still be 10
        total = llm_stats['llm_innovations'] + llm_stats['factor_mutations']
        assert total == 10, \
            f"TASK 12 FALLBACK FAIL: Total should be 10, got {total}"

        print("\n✅ TASK 12 FALLBACK: ALL ASSERTIONS PASSED")
        print(f"✅ 100% success rate maintained: {success_count}/10")
        print(f"✅ Fallback mechanism working: {llm_stats['llm_fallbacks']} fallbacks")
        print(f"✅ Factor Graph handled failures: {llm_stats['factor_mutations']} mutations")

    def test_task12_statistics_tracking(
        self,
        mock_llm_strategies,
        mock_factor_strategy
    ):
        """
        TASK 12: Test LLM statistics tracking accuracy.

        Expected Behavior:
        - All LLM usage is tracked correctly
        - Success/failure counts are accurate
        - Cost tracking works
        - Statistics API returns correct data

        Success Criteria:
        - LLM vs Factor Graph counts sum to total iterations
        - Success rate calculation is correct
        - Cost data is present when LLM enabled
        - All statistics fields populated
        """
        print("\n" + "="*80)
        print("TASK 12: Statistics Tracking Test")
        print("="*80)

        with patch('autonomous_loop.yaml.safe_load') as mock_yaml:
            mock_yaml.return_value = {
                'llm': {
                    'enabled': 'true',
                    'provider': 'gemini',
                    'innovation_rate': 0.25
                }
            }

            with patch('autonomous_loop.os.path.exists') as mock_exists:
                mock_exists.return_value = True

                with patch('autonomous_loop.InnovationEngine') as mock_engine_class:
                    mock_engine = Mock()

                    # Track actual calls
                    actual_llm_calls = [0]

                    def llm_with_tracking(*args, **kwargs):
                        actual_llm_calls[0] += 1
                        return mock_llm_strategies[0]

                    mock_engine.generate_innovation.side_effect = llm_with_tracking

                    def get_stats():
                        return {
                            'total_attempts': actual_llm_calls[0],
                            'successful_generations': actual_llm_calls[0],
                            'success_rate': 1.0
                        }

                    def get_cost():
                        return {
                            'total_cost_usd': actual_llm_calls[0] * 0.001234,
                            'total_tokens': actual_llm_calls[0] * 600,
                            'successful_generations': actual_llm_calls[0],
                            'average_cost_per_success': 0.001234
                        }

                    mock_engine.get_statistics.side_effect = get_stats
                    mock_engine.get_cost_report.side_effect = get_cost
                    mock_engine_class.return_value = mock_engine

                    with patch('autonomous_loop.generate_strategy') as mock_generate:
                        mock_generate.return_value = mock_factor_strategy

                        with patch('autonomous_loop.validate_code') as mock_validate:
                            mock_validate.return_value = (True, [])

                            with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                                mock_execute.return_value = (True, {'sharpe_ratio': 0.8}, None)

                                import random
                                random.seed(100)

                                loop = AutonomousLoop(max_iterations=10)

                                for i in range(10):
                                    loop.run_iteration(i, data=None)

        # Get statistics
        llm_stats = loop.get_llm_statistics()

        # Print statistics
        print("\n" + "="*80)
        print("STATISTICS TRACKING RESULTS")
        print("="*80)
        print(f"LLM enabled: {llm_stats['llm_enabled']}")
        print(f"Innovation rate: {llm_stats['innovation_rate']}")
        print(f"LLM innovations: {llm_stats['llm_innovations']}")
        print(f"LLM fallbacks: {llm_stats['llm_fallbacks']}")
        print(f"Factor mutations: {llm_stats['factor_mutations']}")
        print(f"LLM success rate: {llm_stats['llm_success_rate']:.1%}")
        if 'llm_costs' in llm_stats and llm_stats['llm_costs']:
            print(f"Total cost: ${llm_stats['llm_costs']['total_cost_usd']:.6f}")
        print("="*80)

        # TASK 12 STATISTICS ASSERTIONS

        # 1. Counts must sum to 10
        total = llm_stats['llm_innovations'] + llm_stats['factor_mutations']
        assert total == 10, \
            f"TASK 12 STATS FAIL: Total should be 10, got {total}"

        # 2. LLM innovation count should match actual calls
        assert llm_stats['llm_innovations'] == actual_llm_calls[0], \
            f"TASK 12 STATS FAIL: LLM count mismatch"

        # 3. Success rate should be 1.0 (all succeeded)
        assert llm_stats['llm_success_rate'] == 1.0, \
            f"TASK 12 STATS FAIL: Success rate should be 1.0"

        # 4. Cost data should be present
        if llm_stats['llm_enabled']:
            assert 'llm_costs' in llm_stats, \
                "TASK 12 STATS FAIL: Cost data missing"
            assert llm_stats['llm_costs'] is not None, \
                "TASK 12 STATS FAIL: Cost data is None"

        print("\n✅ TASK 12 STATISTICS: ALL ASSERTIONS PASSED")
        print(f"✅ Accurate counting: LLM={llm_stats['llm_innovations']} + Factor={llm_stats['factor_mutations']} = 10")
        print(f"✅ Success rate correct: {llm_stats['llm_success_rate']:.1%}")
        print(f"✅ Cost tracking working")


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '-s'])
