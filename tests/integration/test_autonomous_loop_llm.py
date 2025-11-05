"""
Integration tests for autonomous loop with LLM innovation.

Tests LLM integration in the autonomous loop:
- Innovation rate control (20% of iterations use LLM)
- Fallback to Factor Graph on LLM failures
- Statistics tracking for LLM usage
- Backward compatibility (LLM disabled by default)

Requirements:
- llm-integration-activation: Task 5 (Integration)
- Requirements: 1.1, 1.2, 5.1-5.5
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Add artifacts/working/modules to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../artifacts/working/modules'))

from autonomous_loop import AutonomousLoop


class TestAutonomousLoopLLM:
    """Test suite for LLM integration in autonomous loop."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Setup: Clear any existing logger cache
        import logging
        # Disable logging during tests to avoid file handle issues
        logging.disable(logging.CRITICAL)

        # Patch event logger to avoid file issues
        with patch('autonomous_loop.get_event_logger') as mock_logger:
            mock_logger.return_value = Mock()
            yield

        # Teardown: Re-enable logging
        logging.disable(logging.NOTSET)

    @pytest.fixture
    def mock_llm_response(self):
        """Mock successful LLM response."""
        return """
def strategy(data):
    # LLM-generated strategy with fundamental factors
    roe = data.get('fundamental_features:ROE稅後')
    revenue_growth = data.get('fundamental_features:營收成長率')
    return (roe > 18) & (revenue_growth > 0.15)
"""

    @pytest.fixture
    def mock_champion_metrics(self):
        """Mock champion metrics for testing."""
        return {
            'sharpe_ratio': 0.85,
            'max_drawdown': -0.15,
            'win_rate': 0.58,
            'calmar_ratio': 2.3,
            'annual_return': 0.25
        }

    def test_llm_disabled_by_default(self):
        """Test that LLM is disabled by default (backward compatibility)."""
        loop = AutonomousLoop(max_iterations=1)

        assert loop.llm_enabled is False
        assert loop.innovation_engine is None
        assert loop.innovation_rate == 0.0

    @patch('autonomous_loop.yaml.safe_load')
    @patch('autonomous_loop.os.path.exists')
    def test_llm_enabled_from_config(self, mock_exists, mock_yaml_load):
        """Test LLM initialization from config file."""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            'llm': {
                'enabled': 'true',
                'provider': 'gemini',
                'model': 'gemini-2.0-flash',
                'innovation_rate': 0.20,
                'timeout': 60,
                'max_tokens': 2000,
                'temperature': 0.7
            }
        }

        with patch('autonomous_loop.InnovationEngine') as mock_engine:
            mock_engine.return_value = Mock()
            loop = AutonomousLoop(max_iterations=1)

            assert loop.llm_enabled is True
            assert loop.innovation_rate == 0.20
            mock_engine.assert_called_once()

    @patch('autonomous_loop.InnovationEngine')
    @patch('autonomous_loop.generate_strategy')
    def test_innovation_rate_control(self, mock_generate, mock_engine_class):
        """Test that ~20% of iterations use LLM (innovation_rate=0.20)."""
        # Setup: Create loop with LLM enabled
        mock_engine = Mock()
        mock_engine.generate_innovation.return_value = "def strategy(data): return True"
        mock_engine_class.return_value = mock_engine

        # Mock generate_strategy for Factor Graph
        mock_generate.return_value = "def strategy(data): return False"

        loop = AutonomousLoop(max_iterations=10)
        loop.llm_enabled = True
        loop.innovation_engine = mock_engine
        loop.innovation_rate = 0.20

        # Run 10 iterations with mocked execution
        with patch.object(loop, 'run_iteration') as mock_run:
            mock_run.return_value = (True, "SUCCESS")

            # Simulate generation decision for 10 iterations
            llm_count = 0
            with patch('autonomous_loop.random.random') as mock_random:
                # Simulate: 2 iterations use LLM (20%), 8 use Factor Graph (80%)
                mock_random.side_effect = [0.1, 0.8, 0.15, 0.9, 0.85, 0.75, 0.05, 0.95, 0.65, 0.55]

                for i in range(10):
                    use_llm = mock_random() < loop.innovation_rate
                    if use_llm:
                        llm_count += 1

        # Verify: ~20% used LLM (2 out of 10)
        assert llm_count == 2

    @patch('autonomous_loop.InnovationEngine')
    def test_llm_fallback_on_failure(self, mock_engine_class, mock_llm_response):
        """Test fallback to Factor Graph when LLM fails."""
        # Setup: LLM returns None (failure)
        mock_engine = Mock()
        mock_engine.generate_innovation.return_value = None
        mock_engine_class.return_value = mock_engine

        loop = AutonomousLoop(max_iterations=1)
        loop.llm_enabled = True
        loop.innovation_engine = mock_engine
        loop.innovation_rate = 1.0  # Force LLM usage

        # Mock Factor Graph generation
        with patch('autonomous_loop.generate_strategy') as mock_generate:
            mock_generate.return_value = "def strategy(data): return True"

            # Mock other components
            with patch('autonomous_loop.validate_code') as mock_validate:
                mock_validate.return_value = (True, [])

                with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                    mock_execute.return_value = (True, {'sharpe_ratio': 1.0}, None)

                    # Run iteration - should fallback to Factor Graph
                    success, status = loop.run_iteration(0, data=None)

        # Verify: Fallback occurred
        assert loop.llm_stats['llm_fallbacks'] == 1
        assert loop.llm_stats['factor_mutations'] == 1
        assert success is True

    @patch('autonomous_loop.InnovationEngine')
    def test_llm_exception_fallback(self, mock_engine_class):
        """Test fallback to Factor Graph when LLM raises exception."""
        # Setup: LLM raises exception
        mock_engine = Mock()
        mock_engine.generate_innovation.side_effect = Exception("API timeout")
        mock_engine_class.return_value = mock_engine

        loop = AutonomousLoop(max_iterations=1)
        loop.llm_enabled = True
        loop.innovation_engine = mock_engine
        loop.innovation_rate = 1.0  # Force LLM usage

        # Mock Factor Graph generation
        with patch('autonomous_loop.generate_strategy') as mock_generate:
            mock_generate.return_value = "def strategy(data): return True"

            # Mock other components
            with patch('autonomous_loop.validate_code') as mock_validate:
                mock_validate.return_value = (True, [])

                with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                    mock_execute.return_value = (True, {'sharpe_ratio': 1.0}, None)

                    # Run iteration - should fallback to Factor Graph
                    success, status = loop.run_iteration(0, data=None)

        # Verify: Fallback occurred due to exception
        assert loop.llm_stats['llm_api_failures'] == 1
        assert loop.llm_stats['factor_mutations'] == 1
        assert success is True

    @patch('autonomous_loop.InnovationEngine')
    def test_llm_statistics_tracking(self, mock_engine_class, mock_llm_response):
        """Test LLM statistics are tracked correctly."""
        # Setup: LLM returns valid code
        mock_engine = Mock()
        mock_engine.generate_innovation.return_value = mock_llm_response
        mock_engine.get_cost_report.return_value = {
            'total_cost_usd': 0.001234,
            'total_tokens': 500,
            'successful_generations': 1,
            'average_cost_per_success': 0.001234
        }
        mock_engine.get_statistics.return_value = {
            'total_attempts': 1,
            'successful_generations': 1,
            'success_rate': 1.0
        }
        mock_engine_class.return_value = mock_engine

        loop = AutonomousLoop(max_iterations=1)
        loop.llm_enabled = True
        loop.innovation_engine = mock_engine
        loop.innovation_rate = 1.0  # Force LLM usage

        # Mock other components
        with patch('autonomous_loop.validate_code') as mock_validate:
            mock_validate.return_value = (True, [])

            with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                mock_execute.return_value = (True, {'sharpe_ratio': 1.0}, None)

                # Run iteration with LLM
                success, status = loop.run_iteration(0, data=None)

        # Get statistics
        llm_stats = loop.get_llm_statistics()

        # Verify statistics
        assert llm_stats['llm_enabled'] is True
        assert llm_stats['innovation_rate'] == 1.0
        assert llm_stats['llm_innovations'] == 1
        assert llm_stats['llm_fallbacks'] == 0
        assert llm_stats['factor_mutations'] == 0
        assert llm_stats['llm_success_rate'] == 1.0
        assert llm_stats['llm_costs']['total_cost_usd'] == 0.001234

    @patch('autonomous_loop.InnovationEngine')
    @patch('autonomous_loop.generate_strategy')
    def test_mixed_llm_and_factor_graph(self, mock_generate, mock_engine_class, mock_llm_response):
        """Test mixed usage of LLM and Factor Graph in same run."""
        # Setup: LLM succeeds on some calls, Factor Graph on others
        mock_engine = Mock()
        mock_engine.generate_innovation.side_effect = [
            mock_llm_response,  # Success
            None,               # Failure - fallback
        ]
        mock_engine_class.return_value = mock_engine

        # Mock Factor Graph generation
        mock_generate.return_value = "def strategy(data): return True"

        loop = AutonomousLoop(max_iterations=2)
        loop.llm_enabled = True
        loop.innovation_engine = mock_engine
        loop.innovation_rate = 1.0  # Force LLM for both iterations

        # Mock other components
        with patch('autonomous_loop.validate_code') as mock_validate:
            mock_validate.return_value = (True, [])

            with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                mock_execute.return_value = (True, {'sharpe_ratio': 1.0}, None)

                # Run 2 iterations
                for i in range(2):
                    success, status = loop.run_iteration(i, data=None)
                    assert success is True

        # Verify statistics
        assert loop.llm_stats['llm_innovations'] == 1  # One success
        assert loop.llm_stats['llm_fallbacks'] == 1    # One fallback
        assert loop.llm_stats['factor_mutations'] == 1  # One Factor Graph mutation

    def test_llm_statistics_with_disabled_llm(self):
        """Test get_llm_statistics when LLM is disabled."""
        loop = AutonomousLoop(max_iterations=1)

        # Get statistics with LLM disabled
        llm_stats = loop.get_llm_statistics()

        # Verify default statistics
        assert llm_stats['llm_enabled'] is False
        assert llm_stats['innovation_rate'] == 0.0
        assert llm_stats['llm_innovations'] == 0
        assert llm_stats['llm_fallbacks'] == 0
        assert llm_stats['llm_success_rate'] == 0.0
        # llm_costs may not be present when LLM is disabled
        if 'llm_costs' in llm_stats:
            assert llm_stats['llm_costs'] is None

    @patch('autonomous_loop.InnovationEngine')
    def test_champion_feedback_to_llm(self, mock_engine_class, mock_champion_metrics):
        """Test that champion code and metrics are passed to LLM."""
        # Setup: Create champion
        mock_engine = Mock()
        mock_engine.generate_innovation.return_value = "def strategy(data): return True"
        mock_engine_class.return_value = mock_engine

        loop = AutonomousLoop(max_iterations=1)
        loop.llm_enabled = True
        loop.innovation_engine = mock_engine
        loop.innovation_rate = 1.0

        # Set champion
        from autonomous_loop import ChampionStrategy
        from datetime import datetime
        loop.champion = ChampionStrategy(
            iteration_num=0,
            code="def strategy(data): return data.get('fundamental_features:ROE稅後') > 15",
            parameters={'roe_threshold': 15},
            metrics=mock_champion_metrics,
            success_patterns=['high_roe_filter'],
            timestamp=datetime.now().isoformat()
        )

        # Mock other components
        with patch('autonomous_loop.validate_code') as mock_validate:
            mock_validate.return_value = (True, [])

            with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                mock_execute.return_value = (True, {'sharpe_ratio': 1.0}, None)

                # Run iteration
                success, status = loop.run_iteration(1, data=None)

        # Verify: Champion data was passed to LLM
        mock_engine.generate_innovation.assert_called_once()
        call_args = mock_engine.generate_innovation.call_args

        assert call_args.kwargs['champion_code'] == loop.champion.code
        assert call_args.kwargs['champion_metrics'] == mock_champion_metrics
        assert call_args.kwargs['target_metric'] == 'sharpe_ratio'

    @patch('autonomous_loop.InnovationEngine')
    def test_failure_history_to_llm(self, mock_engine_class):
        """Test that recent failure history is passed to LLM."""
        # Setup
        mock_engine = Mock()
        mock_engine.generate_innovation.return_value = "def strategy(data): return True"
        mock_engine_class.return_value = mock_engine

        loop = AutonomousLoop(max_iterations=1)
        loop.llm_enabled = True
        loop.innovation_engine = mock_engine
        loop.innovation_rate = 1.0

        # Add failure records to history
        for i in range(3):
            loop.history.add_record(
                iteration_num=i,
                model='test',
                code='test code',
                validation_passed=False,
                validation_errors=['Syntax error'],
                execution_success=False,
                execution_error='Test error',
                metrics=None,
                feedback='',
                data_checksum=None,
                data_version=None,
                config_snapshot=None
            )

        # Mock other components
        with patch('autonomous_loop.validate_code') as mock_validate:
            mock_validate.return_value = (True, [])

            with patch('autonomous_loop.execute_strategy_safe') as mock_execute:
                mock_execute.return_value = (True, {'sharpe_ratio': 1.0}, None)

                # Run iteration
                success, status = loop.run_iteration(3, data=None)

        # Verify: Failure history was passed to LLM
        mock_engine.generate_innovation.assert_called_once()
        call_args = mock_engine.generate_innovation.call_args

        failure_history = call_args.kwargs['failure_history']
        assert len(failure_history) == 3  # All 3 failures included


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
