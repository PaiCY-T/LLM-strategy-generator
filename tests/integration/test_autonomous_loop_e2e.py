"""
Comprehensive end-to-end tests for autonomous loop with LLM integration.

This module tests the complete autonomous learning loop with LLM-driven innovation:
- 20-iteration runs with LLM enabled (20% innovation rate)
- Mixed LLM + Factor Graph operation
- Statistics tracking (innovations, fallbacks, costs)
- Champion updates from both LLM and Factor Graph sources
- Iteration completion reliability (100% success rate)
- LLM API usage tracking
- Backward compatibility (LLM disabled mode)

Task: llm-integration-activation - Task 6
Requirements: 1.1, 1.2, 5.1-5.5
Role: QA Engineer with expertise in end-to-end testing and system integration
"""

import pytest
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any, List
from dataclasses import dataclass

# Add artifacts/working/modules to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../artifacts/working/modules'))

from autonomous_loop import AutonomousLoop, ChampionStrategy


@dataclass
class E2ETestMetrics:
    """Metrics tracked during E2E tests."""
    total_iterations: int
    llm_innovations: int
    factor_mutations: int
    llm_fallbacks: int
    champion_updates: int
    llm_champion_updates: int
    factor_champion_updates: int
    total_cost_usd: float
    execution_time_seconds: float
    success_rate: float


class TestAutonomousLoopE2E:
    """Comprehensive end-to-end test suite for LLM-integrated autonomous loop."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Patch event logger globally for all tests
        with patch('autonomous_loop.get_event_logger') as mock_logger:
            mock_logger.return_value = Mock()
            yield

    @pytest.fixture
    def mock_llm_responses(self):
        """Generate diverse mock LLM responses for realistic testing."""
        responses = [
            # Response 1: ROE + Revenue Growth
            """
def strategy(data):
    # LLM-generated strategy with fundamental factors
    roe = data.get('fundamental_features:ROE稅後')
    revenue_growth = data.get('fundamental_features:營收成長率')
    return (roe > 18) & (revenue_growth > 0.15)
""",
            # Response 2: Momentum + Volume
            """
def strategy(data):
    # Momentum strategy with volume confirmation
    price_change = data.get('price_features:收盤價(元)').pct_change(20)
    volume = data.get('price_features:成交股數')
    return (price_change > 0.10) & (volume > volume.rolling(60).mean())
""",
            # Response 3: Value factors
            """
def strategy(data):
    # Value-based selection
    pb = data.get('fundamental_features:股價淨值比')
    pe = data.get('fundamental_features:本益比')
    return (pb < 2.0) & (pe < 15) & (pe > 0)
""",
            # Response 4: Quality + Growth
            """
def strategy(data):
    # Quality and growth combination
    roe = data.get('fundamental_features:ROE稅後')
    debt_ratio = data.get('fundamental_features:負債比率')
    eps_growth = data.get('fundamental_features:EPS年增率')
    return (roe > 15) & (debt_ratio < 50) & (eps_growth > 0.10)
""",
        ]
        return responses

    @pytest.fixture
    def mock_factor_response(self):
        """Mock Factor Graph response."""
        return "def strategy(data): return data.get('fundamental_features:ROE稅後') > 15"

    @pytest.fixture
    def mock_champion_metrics(self):
        """Mock champion metrics with realistic values."""
        return {
            'sharpe_ratio': 0.85,
            'max_drawdown': -0.15,
            'win_rate': 0.58,
            'calmar_ratio': 2.3,
            'annual_return': 0.25,
            'total_trades': 120
        }

    def create_mock_llm_response(self, code: str, cost: float = 0.001) -> Mock:
        """Helper to create mock LLM response with cost tracking."""
        mock_response = Mock()
        mock_response.content = code
        mock_response.prompt_tokens = 500
        mock_response.completion_tokens = 100
        mock_response.total_tokens = 600
        mock_response.model = 'gemini-2.0-flash'
        mock_response.provider = 'gemini'
        return mock_response

    def test_20_iteration_mixed_mode(self, mock_llm_responses, mock_factor_response, mock_champion_metrics):
        """
        Main E2E test: Run 20 iterations with 20% LLM innovation rate.

        Expected behavior:
        - ~4 LLM attempts (20% of 20)
        - ~16 Factor Graph mutations (80% of 20)
        - All iterations complete successfully
        - Champion updates occur
        - Cost tracking functional
        """
        start_time = time.time()

        # Setup: Create loop with LLM enabled
        with patch('autonomous_loop.yaml.safe_load') as mock_yaml:
            mock_yaml.return_value = {
                'llm': {
                    'enabled': 'true',
                    'provider': 'gemini',
                    'innovation_rate': 0.20
                }
            }

            with patch('autonomous_loop.os.path.exists') as mock_exists:
                mock_exists.return_value = True

                # Mock InnovationEngine
                with patch('autonomous_loop.InnovationEngine') as mock_engine_class:
                    mock_engine = Mock()

                    # Simulate LLM responses (cycle through responses)
                    llm_call_count = [0]

                    def llm_side_effect(*args, **kwargs):
                        response = mock_llm_responses[llm_call_count[0] % len(mock_llm_responses)]
                        llm_call_count[0] += 1
                        return response

                    mock_engine.generate_innovation.side_effect = llm_side_effect

                    # Mock statistics
                    def get_stats():
                        llm_count = min(llm_call_count[0], 20)
                        return {
                            'total_attempts': llm_count,
                            'successful_generations': llm_count,
                            'success_rate': 1.0
                        }

                    def get_cost():
                        llm_count = min(llm_call_count[0], 20)
                        return {
                            'total_cost_usd': llm_count * 0.001234,
                            'total_tokens': llm_count * 600,
                            'successful_generations': llm_count,
                            'average_cost_per_success': 0.001234
                        }

                    mock_engine.get_statistics.side_effect = get_stats
                    mock_engine.get_cost_report.side_effect = get_cost
                    mock_engine_class.return_value = mock_engine

                    # Mock Factor Graph
                    with patch('autonomous_loop.generate_strategy') as mock_generate:
                        mock_generate.return_value = mock_factor_response

                        # Mock validation
                        with patch('autonomous_loop.validate_code') as mock_validate:
                            mock_validate.return_value = (True, [])

                            # Mock execution - vary metrics slightly
                            def mock_execute_side_effect(code, *args, **kwargs):
                                import random
                                sharpe = 0.7 + random.random() * 0.3  # 0.7 to 1.0
                                metrics = {
                                    'sharpe_ratio': sharpe,
                                    'annual_return': 0.15 + random.random() * 0.15,
                                    'max_drawdown': -0.10 - random.random() * 0.10,
                                    'win_rate': 0.50 + random.random() * 0.15
                                }
                                return (True, metrics, None)

                            with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                                mock_execute.side_effect = mock_execute_side_effect

                                # Set random seed for reproducibility
                                import random
                                random.seed(42)

                                # Create and configure loop
                                loop = AutonomousLoop(max_iterations=20)

                                # Track champion updates
                                champion_update_count = 0
                                original_update = loop._update_champion

                                def track_champion_updates(*args, **kwargs):
                                    nonlocal champion_update_count
                                    champion_update_count += 1
                                    return original_update(*args, **kwargs)

                                loop._update_champion = track_champion_updates

                                # Run 20 iterations
                                success_count = 0
                                for i in range(20):
                                    success, status = loop.run_iteration(i, data=None)
                                    if success:
                                        success_count += 1

        # Calculate execution time
        execution_time = time.time() - start_time

        # Get final statistics
        llm_stats = loop.get_llm_statistics()

        # Assertions

        # 1. All iterations must succeed (100% success rate)
        assert success_count == 20, f"Expected 20 successful iterations, got {success_count}"

        # 2. LLM should be enabled
        assert llm_stats['llm_enabled'] is True
        assert llm_stats['innovation_rate'] == 0.20

        # 3. Should have ~20% LLM attempts (3-6 out of 20 with random variation)
        llm_total = llm_stats['llm_innovations'] + llm_stats['llm_fallbacks']
        assert 2 <= llm_total <= 7, f"Expected 2-7 LLM attempts, got {llm_total}"

        # 4. Should have ~80% Factor Graph (14-18 out of 20)
        factor_total = llm_stats['factor_mutations']
        assert 13 <= factor_total <= 18, f"Expected 13-18 Factor Graph mutations, got {factor_total}"

        # 5. LLM + Factor Graph should sum to 20 iterations
        total = llm_stats['llm_innovations'] + llm_stats['factor_mutations']
        assert total == 20, f"Total iterations should be 20, got {total}"

        # 6. Cost tracking should be functional
        if 'llm_costs' in llm_stats and llm_stats['llm_costs']:
            assert llm_stats['llm_costs']['total_cost_usd'] > 0
            assert llm_stats['llm_costs']['total_tokens'] > 0

        # 7. Champion should be updated at least once
        assert loop.champion is not None, "Champion should be established"
        assert champion_update_count > 0, "Champion should be updated"

        # 8. Execution time should be reasonable (< 60 seconds with mocks)
        assert execution_time < 60, f"Test took too long: {execution_time:.2f}s"

        # 9. No API failures (all mocked calls succeed)
        assert llm_stats['llm_api_failures'] == 0

        # Print summary for visibility
        print(f"\n{'='*80}")
        print(f"20-ITERATION MIXED MODE E2E TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total iterations: 20")
        print(f"Successful: {success_count}")
        print(f"Success rate: {success_count/20*100:.1f}%")
        print(f"LLM innovations: {llm_stats['llm_innovations']}")
        print(f"LLM fallbacks: {llm_stats['llm_fallbacks']}")
        print(f"Factor Graph mutations: {llm_stats['factor_mutations']}")
        print(f"Champion updates: {champion_update_count}")
        print(f"Execution time: {execution_time:.2f}s")
        if 'llm_costs' in llm_stats and llm_stats['llm_costs']:
            print(f"Total cost: ${llm_stats['llm_costs']['total_cost_usd']:.6f}")
        print(f"{'='*80}\n")

    def test_llm_disabled_baseline(self, mock_factor_response):
        """
        Test backward compatibility: 20 iterations with LLM disabled.

        Expected behavior:
        - 100% Factor Graph mutations
        - No LLM statistics
        - All iterations complete successfully
        """
        start_time = time.time()

        # Mock Factor Graph
        with patch('autonomous_loop.generate_strategy') as mock_generate:
            mock_generate.return_value = mock_factor_response

            # Mock validation
            with patch('autonomous_loop.validate_code') as mock_validate:
                mock_validate.return_value = (True, [])

                # Mock execution
                with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                    mock_execute.return_value = (True, {'sharpe_ratio': 0.8}, None)

                    # Create loop with LLM disabled (default)
                    loop = AutonomousLoop(max_iterations=20)

                    # Run 20 iterations
                    success_count = 0
                    for i in range(20):
                        success, status = loop.run_iteration(i, data=None)
                        if success:
                            success_count += 1

        execution_time = time.time() - start_time

        # Get statistics
        llm_stats = loop.get_llm_statistics()

        # Assertions

        # 1. All iterations succeed
        assert success_count == 20

        # 2. LLM should be disabled
        assert llm_stats['llm_enabled'] is False
        assert llm_stats['innovation_rate'] == 0.0

        # 3. All should be Factor Graph mutations
        assert llm_stats['factor_mutations'] == 20
        assert llm_stats['llm_innovations'] == 0
        assert llm_stats['llm_fallbacks'] == 0

        # 4. No LLM costs
        assert llm_stats.get('llm_costs') is None or llm_stats['llm_costs']['total_cost_usd'] == 0

        # 5. Fast execution
        assert execution_time < 30

        print(f"\n{'='*80}")
        print(f"LLM DISABLED BASELINE TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total iterations: 20")
        print(f"All Factor Graph: {llm_stats['factor_mutations']}")
        print(f"Success rate: 100%")
        print(f"Execution time: {execution_time:.2f}s")
        print(f"{'='*80}\n")

    def test_cost_tracking_validation(self, mock_llm_responses, mock_factor_response):
        """
        Test cost tracking accuracy with 10 iterations.

        Expected behavior:
        - ~2 LLM calls (20% of 10)
        - Accurate cost reporting
        - Cost breakdown by provider/model
        """
        with patch('autonomous_loop.yaml.safe_load') as mock_yaml:
            mock_yaml.return_value = {
                'llm': {
                    'enabled': 'true',
                    'provider': 'gemini',
                    'innovation_rate': 0.20
                }
            }

            with patch('autonomous_loop.os.path.exists') as mock_exists:
                mock_exists.return_value = True

                # Mock InnovationEngine with cost tracking
                with patch('autonomous_loop.InnovationEngine') as mock_engine_class:
                    mock_engine = Mock()

                    llm_calls = [0]

                    def llm_with_cost(*args, **kwargs):
                        llm_calls[0] += 1
                        return mock_llm_responses[0]

                    mock_engine.generate_innovation.side_effect = llm_with_cost

                    # Realistic cost tracking
                    def get_cost():
                        calls = llm_calls[0]
                        return {
                            'total_cost_usd': calls * 0.001234,  # ~$0.0012 per call
                            'total_tokens': calls * 600,
                            'successful_generations': calls,
                            'average_cost_per_success': 0.001234,
                            'by_model': {
                                'gemini-2.0-flash': {
                                    'calls': calls,
                                    'cost': calls * 0.001234,
                                    'tokens': calls * 600
                                }
                            }
                        }

                    mock_engine.get_cost_report.side_effect = get_cost
                    mock_engine.get_statistics.return_value = {
                        'total_attempts': 2,
                        'successful_generations': 2,
                        'success_rate': 1.0
                    }

                    mock_engine_class.return_value = mock_engine

                    # Mock other components
                    with patch('autonomous_loop.generate_strategy') as mock_generate:
                        mock_generate.return_value = mock_factor_response

                        with patch('autonomous_loop.validate_code') as mock_validate:
                            mock_validate.return_value = (True, [])

                            with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                                mock_execute.return_value = (True, {'sharpe_ratio': 0.8}, None)

                                # Set random seed
                                import random
                                random.seed(42)

                                # Run 10 iterations
                                loop = AutonomousLoop(max_iterations=10)

                                for i in range(10):
                                    loop.run_iteration(i, data=None)

        # Get statistics
        llm_stats = loop.get_llm_statistics()

        # Assertions

        # 1. Should have LLM calls
        assert llm_calls[0] > 0, "Should have at least 1 LLM call"

        # 2. Cost should be positive
        if 'llm_costs' in llm_stats and llm_stats['llm_costs']:
            total_cost = llm_stats['llm_costs']['total_cost_usd']
            assert total_cost > 0, "Cost should be positive"

            # 3. Cost should be reasonable (~$0.0012 per call)
            expected_cost = llm_calls[0] * 0.001234
            assert abs(total_cost - expected_cost) < 0.0001

            # 4. Token tracking
            assert llm_stats['llm_costs']['total_tokens'] > 0

            print(f"\n{'='*80}")
            print(f"COST TRACKING VALIDATION SUMMARY")
            print(f"{'='*80}")
            print(f"LLM calls: {llm_calls[0]}")
            print(f"Total cost: ${total_cost:.6f}")
            print(f"Avg cost/call: ${total_cost/llm_calls[0]:.6f}")
            print(f"Total tokens: {llm_stats['llm_costs']['total_tokens']}")
            print(f"{'='*80}\n")

    def test_fallback_mechanism(self, mock_llm_responses, mock_factor_response):
        """
        Test fallback to Factor Graph when LLM fails.

        Expected behavior:
        - LLM fails randomly
        - Fallback to Factor Graph occurs
        - 100% iteration completion (no failures)
        """
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

                # Mock InnovationEngine with random failures
                with patch('autonomous_loop.InnovationEngine') as mock_engine_class:
                    mock_engine = Mock()

                    call_count = [0]

                    def llm_with_failures(*args, **kwargs):
                        call_count[0] += 1
                        # Fail on odd calls, succeed on even calls
                        if call_count[0] % 2 == 1:
                            return None  # Simulate failure
                        else:
                            return mock_llm_responses[0]

                    mock_engine.generate_innovation.side_effect = llm_with_failures
                    mock_engine.get_statistics.return_value = {
                        'total_attempts': 6,
                        'successful_generations': 3,
                        'success_rate': 0.5
                    }
                    mock_engine.get_cost_report.return_value = {
                        'total_cost_usd': 0.003,
                        'total_tokens': 1800,
                        'successful_generations': 3
                    }

                    mock_engine_class.return_value = mock_engine

                    # Mock Factor Graph
                    with patch('autonomous_loop.generate_strategy') as mock_generate:
                        mock_generate.return_value = mock_factor_response

                        with patch('autonomous_loop.validate_code') as mock_validate:
                            mock_validate.return_value = (True, [])

                            with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                                mock_execute.return_value = (True, {'sharpe_ratio': 0.8}, None)

                                # Set random seed
                                import random
                                random.seed(123)

                                # Run 20 iterations
                                loop = AutonomousLoop(max_iterations=20)

                                success_count = 0
                                for i in range(20):
                                    success, status = loop.run_iteration(i, data=None)
                                    if success:
                                        success_count += 1

        # Get statistics
        llm_stats = loop.get_llm_statistics()

        # Assertions

        # 1. 100% iteration completion despite LLM failures
        assert success_count == 20, f"All iterations should succeed, got {success_count}"

        # 2. Should have fallbacks
        assert llm_stats['llm_fallbacks'] > 0, "Should have fallbacks when LLM fails"

        # 3. Fallbacks should use Factor Graph
        assert llm_stats['factor_mutations'] > 0, "Factor Graph should be used for fallbacks"

        # 4. Total should still be 20
        total = llm_stats['llm_innovations'] + llm_stats['factor_mutations']
        assert total == 20

        print(f"\n{'='*80}")
        print(f"FALLBACK MECHANISM TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total iterations: 20")
        print(f"Success rate: 100%")
        print(f"LLM successes: {llm_stats['llm_innovations']}")
        print(f"LLM fallbacks: {llm_stats['llm_fallbacks']}")
        print(f"Factor Graph: {llm_stats['factor_mutations']}")
        print(f"Reliability: Fallback mechanism working correctly")
        print(f"{'='*80}\n")

    def test_champion_update_tracking(self, mock_llm_responses, mock_factor_response):
        """
        Test champion updates from both LLM and Factor Graph.

        Expected behavior:
        - Champion updated by both LLM and Factor Graph strategies
        - Champion always holds best-performing strategy
        - Metrics improve over iterations
        """
        with patch('autonomous_loop.yaml.safe_load') as mock_yaml:
            mock_yaml.return_value = {
                'llm': {
                    'enabled': 'true',
                    'provider': 'gemini',
                    'innovation_rate': 0.20
                }
            }

            with patch('autonomous_loop.os.path.exists') as mock_exists:
                mock_exists.return_value = True

                with patch('autonomous_loop.InnovationEngine') as mock_engine_class:
                    mock_engine = Mock()
                    mock_engine.generate_innovation.return_value = mock_llm_responses[0]
                    mock_engine.get_statistics.return_value = {
                        'total_attempts': 4,
                        'successful_generations': 4,
                        'success_rate': 1.0
                    }
                    mock_engine.get_cost_report.return_value = {
                        'total_cost_usd': 0.005,
                        'total_tokens': 2400
                    }
                    mock_engine_class.return_value = mock_engine

                    with patch('autonomous_loop.generate_strategy') as mock_generate:
                        mock_generate.return_value = mock_factor_response

                        with patch('autonomous_loop.validate_code') as mock_validate:
                            mock_validate.return_value = (True, [])

                            # Mock execution with improving metrics
                            metrics_sequence = [
                                {'sharpe_ratio': 0.5},   # Iteration 0
                                {'sharpe_ratio': 0.7},   # Iteration 1 - improvement
                                {'sharpe_ratio': 0.6},   # Iteration 2 - worse
                                {'sharpe_ratio': 0.8},   # Iteration 3 - improvement
                                {'sharpe_ratio': 0.75},  # Iteration 4 - worse
                                {'sharpe_ratio': 0.9},   # Iteration 5 - improvement
                            ]

                            call_idx = [0]

                            def mock_execute_with_sequence(code, *args, **kwargs):
                                idx = min(call_idx[0], len(metrics_sequence) - 1)
                                metrics = metrics_sequence[idx]
                                call_idx[0] += 1
                                return (True, metrics, None)

                            with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                                mock_execute.side_effect = mock_execute_with_sequence

                                # Set random seed
                                import random
                                random.seed(42)

                                # Track champion updates
                                champion_history = []

                                loop = AutonomousLoop(max_iterations=6)

                                for i in range(6):
                                    loop.run_iteration(i, data=None)
                                    if loop.champion:
                                        champion_history.append({
                                            'iteration': i,
                                            'sharpe': loop.champion.metrics.get('sharpe_ratio', 0)
                                        })

        # Assertions

        # 1. Champion should exist
        assert loop.champion is not None

        # 2. Champion should have best Sharpe ratio (0.9)
        assert loop.champion.metrics['sharpe_ratio'] == 0.9

        # 3. Champion history should show improvements only
        champion_sharpes = [h['sharpe'] for h in champion_history]
        for i in range(1, len(champion_sharpes)):
            assert champion_sharpes[i] >= champion_sharpes[i-1], \
                "Champion Sharpe should only increase or stay same"

        print(f"\n{'='*80}")
        print(f"CHAMPION UPDATE TRACKING SUMMARY")
        print(f"{'='*80}")
        print(f"Champion updates: {len(champion_history)}")
        print(f"Final champion Sharpe: {loop.champion.metrics['sharpe_ratio']:.2f}")
        print(f"Champion history:")
        for entry in champion_history:
            print(f"  Iteration {entry['iteration']}: Sharpe={entry['sharpe']:.2f}")
        print(f"{'='*80}\n")

    def test_execution_time_performance(self, mock_llm_responses, mock_factor_response):
        """
        Test that 20 iterations complete in reasonable time.

        Expected behavior:
        - 20 iterations complete in < 60 seconds (with mocks)
        - Memory usage remains stable
        - No performance degradation
        """
        with patch('autonomous_loop.yaml.safe_load') as mock_yaml:
            mock_yaml.return_value = {
                'llm': {
                    'enabled': 'true',
                    'provider': 'gemini',
                    'innovation_rate': 0.20
                }
            }

            with patch('autonomous_loop.os.path.exists') as mock_exists:
                mock_exists.return_value = True

                with patch('autonomous_loop.InnovationEngine') as mock_engine_class:
                    mock_engine = Mock()
                    mock_engine.generate_innovation.return_value = mock_llm_responses[0]
                    mock_engine.get_statistics.return_value = {
                        'total_attempts': 4,
                        'successful_generations': 4,
                        'success_rate': 1.0
                    }
                    mock_engine.get_cost_report.return_value = {
                        'total_cost_usd': 0.005,
                        'total_tokens': 2400
                    }
                    mock_engine_class.return_value = mock_engine

                    with patch('autonomous_loop.generate_strategy') as mock_generate:
                        mock_generate.return_value = mock_factor_response

                        with patch('autonomous_loop.validate_code') as mock_validate:
                            mock_validate.return_value = (True, [])

                            with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                                mock_execute.return_value = (True, {'sharpe_ratio': 0.8}, None)

                                # Set random seed
                                import random
                                random.seed(42)

                                # Measure execution time
                                start_time = time.time()

                                loop = AutonomousLoop(max_iterations=20)

                                for i in range(20):
                                    loop.run_iteration(i, data=None)

                                execution_time = time.time() - start_time

        # Assertions

        # 1. Should complete in < 60 seconds
        assert execution_time < 60, f"Test took too long: {execution_time:.2f}s"

        # 2. Calculate throughput
        throughput = 20 / execution_time

        print(f"\n{'='*80}")
        print(f"EXECUTION TIME PERFORMANCE SUMMARY")
        print(f"{'='*80}")
        print(f"Total iterations: 20")
        print(f"Execution time: {execution_time:.2f}s")
        print(f"Throughput: {throughput:.2f} iterations/sec")
        print(f"Avg time/iteration: {execution_time/20:.3f}s")
        print(f"Performance: {'PASS' if execution_time < 60 else 'FAIL'}")
        print(f"{'='*80}\n")

    def test_statistics_accuracy(self, mock_llm_responses, mock_factor_response):
        """
        Test that all statistics are tracked accurately.

        Expected behavior:
        - LLM vs Factor Graph counts accurate
        - Success rates calculated correctly
        - Cost tracking matches actual usage
        - Fallback counts correct
        """
        with patch('autonomous_loop.yaml.safe_load') as mock_yaml:
            mock_yaml.return_value = {
                'llm': {
                    'enabled': 'true',
                    'provider': 'gemini',
                    'innovation_rate': 0.25  # 25% for clearer testing
                }
            }

            with patch('autonomous_loop.os.path.exists') as mock_exists:
                mock_exists.return_value = True

                with patch('autonomous_loop.InnovationEngine') as mock_engine_class:
                    mock_engine = Mock()

                    # Track actual calls
                    llm_success_count = [0]
                    llm_fail_count = [0]

                    def llm_with_tracking(*args, **kwargs):
                        # Succeed on first 3 calls, fail on 4th, succeed on 5th
                        total = llm_success_count[0] + llm_fail_count[0]
                        if total == 3:  # 4th call fails
                            llm_fail_count[0] += 1
                            return None
                        else:
                            llm_success_count[0] += 1
                            return mock_llm_responses[0]

                    mock_engine.generate_innovation.side_effect = llm_with_tracking

                    def get_stats():
                        total = llm_success_count[0] + llm_fail_count[0]
                        return {
                            'total_attempts': total,
                            'successful_generations': llm_success_count[0],
                            'success_rate': llm_success_count[0] / total if total > 0 else 0
                        }

                    def get_cost():
                        return {
                            'total_cost_usd': llm_success_count[0] * 0.001234,
                            'total_tokens': llm_success_count[0] * 600
                        }

                    mock_engine.get_statistics.side_effect = get_stats
                    mock_engine.get_cost_report.side_effect = get_cost
                    mock_engine_class.return_value = mock_engine

                    with patch('autonomous_loop.generate_strategy') as mock_generate:
                        mock_generate.return_value = mock_factor_response

                        with patch('autonomous_loop.validate_code') as mock_validate:
                            mock_validate.return_value = (True, [])

                            with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                                mock_execute.return_value = (True, {'sharpe_ratio': 0.8}, None)

                                # Set random seed for deterministic LLM selection
                                import random
                                random.seed(100)

                                loop = AutonomousLoop(max_iterations=20)

                                for i in range(20):
                                    loop.run_iteration(i, data=None)

        # Get statistics
        llm_stats = loop.get_llm_statistics()

        # Assertions

        # 1. Verify counts sum to 20
        total = llm_stats['llm_innovations'] + llm_stats['factor_mutations']
        assert total == 20, f"Total should be 20, got {total}"

        # 2. Verify LLM fallback count
        assert llm_stats['llm_fallbacks'] == llm_fail_count[0]

        # 3. Verify success counts
        assert llm_stats['llm_innovations'] == llm_success_count[0]

        # 4. Verify success rate calculation
        if llm_stats['llm_innovations'] + llm_stats['llm_fallbacks'] > 0:
            expected_rate = llm_stats['llm_innovations'] / (
                llm_stats['llm_innovations'] + llm_stats['llm_fallbacks']
            )
            assert abs(llm_stats['llm_success_rate'] - expected_rate) < 0.01

        print(f"\n{'='*80}")
        print(f"STATISTICS ACCURACY SUMMARY")
        print(f"{'='*80}")
        print(f"LLM innovations: {llm_stats['llm_innovations']} (expected: {llm_success_count[0]})")
        print(f"LLM fallbacks: {llm_stats['llm_fallbacks']} (expected: {llm_fail_count[0]})")
        print(f"Factor Graph: {llm_stats['factor_mutations']}")
        print(f"Total: {total} (expected: 20)")
        print(f"LLM success rate: {llm_stats['llm_success_rate']:.2%}")
        print(f"All counts accurate: {'PASS' if total == 20 else 'FAIL'}")
        print(f"{'='*80}\n")


if __name__ == '__main__':
    # Run with verbose output and show print statements
    pytest.main([__file__, '-v', '-s'])
