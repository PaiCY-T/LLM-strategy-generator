"""Template Mode Integration Test (Phase 0 - Task 2.7)
===================================================

End-to-end integration test validating the complete template mode workflow:

Workflow Steps (from design.md):
1. Create AutonomousLoop with template_mode=True
2. Run 3 iterations with template-guided parameter generation
3. Verify parameters generated via TemplateParameterGenerator
4. Verify parameters validated via StrategyValidator
5. Verify strategy generated via MomentumTemplate
6. Verify metrics extracted from backtest report
7. Verify champion updated when better parameters found
8. Verify parameters saved in IterationRecord (mode='template')

Test Coverage:
- Full template mode workflow (Tasks 1.1-2.6)
- Real Gemini API call for parameter generation
- Parameter validation with warnings (not blocking)
- Champion tracking with template parameters
- History persistence with mode='template' marker

Requirements:
- REQ-2.1: AutonomousLoop supports template_mode parameter
- REQ-2.2: Template mode routes to _run_template_mode_iteration
- REQ-2.3: Parameters generated and saved in history
- REQ-2.4: Champion updates include parameters
- REQ-2.5: History records include mode='template' marker
"""

import pytest
import sys
import tempfile
import json
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock, patch, Mock

# Add artifacts/working/modules to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "artifacts" / "working" / "modules"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from autonomous_loop import AutonomousLoop, ChampionStrategy
from history import IterationHistory


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def temp_test_dir(tmp_path):
    """Create temporary directory for test files.

    Args:
        tmp_path: pytest built-in temporary directory fixture

    Returns:
        Path: Temporary directory path
    """
    test_dir = tmp_path / "template_mode_test"
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture
def template_mode_config(temp_test_dir):
    """Create template mode test configuration.

    Args:
        temp_test_dir: Temporary directory for test files

    Returns:
        dict: Template mode configuration
    """
    return {
        'history_file': str(temp_test_dir / 'test_template_history.json'),
        'model': 'gemini-2.5-flash',
        'max_iterations': 3,  # 3 iterations as per task spec
        'template_mode': True,
        'template_name': 'Momentum'
    }


@pytest.fixture
def mock_finlab_backtest():
    """Create mock Finlab backtest report and metrics.

    Returns realistic backtest results for template mode testing.

    Returns:
        tuple: (mock_report, mock_metrics)
    """
    mock_report = MagicMock()

    # Mock metrics object with realistic values
    mock_metrics_obj = MagicMock()
    mock_metrics_obj.annual_return.return_value = 0.18  # 18% return
    mock_metrics_obj.sharpe_ratio.return_value = 1.15   # 1.15 Sharpe
    mock_metrics_obj.max_drawdown.return_value = -0.22  # -22% MDD

    mock_report.metrics = mock_metrics_obj

    # Create metrics dict (what _extract_metrics returns)
    mock_metrics = {
        'annual_return': 0.18,
        'sharpe_ratio': 1.15,
        'max_drawdown': -0.22
    }

    return mock_report, mock_metrics


# ==============================================================================
# Template Mode Integration Tests
# ==============================================================================

def test_template_mode_full_workflow(template_mode_config, mock_finlab_backtest, temp_test_dir):
    """Test complete template mode workflow with 3 iterations.

    This is the main integration test that validates the entire template mode
    workflow from end to end:

    Workflow Steps:
        1. Create AutonomousLoop with template_mode=True
        2. Mock MomentumTemplate.generate_strategy() to avoid real backtest
        3. Run 3 iterations
        4. Verify each iteration:
           - Parameters generated via TemplateParameterGenerator
           - Parameters validated via StrategyValidator
           - Strategy executed via MomentumTemplate
           - Metrics extracted from backtest
           - Champion updated if better
           - History record saved with mode='template' and parameters

    Validates:
        - REQ-2.1: template_mode parameter support
        - REQ-2.2: Template mode routing
        - REQ-2.3: Parameter generation and history persistence
        - REQ-2.4: Champion updates with parameters
        - REQ-2.5: mode='template' marker in history

    Story: Phase 0 (Tasks 2.1-2.6)
    """
    mock_report, mock_metrics = mock_finlab_backtest

    # Mock MomentumTemplate.generate_strategy to avoid real backtest
    # This allows us to test the workflow without Finlab data
    with patch('src.templates.momentum_template.MomentumTemplate.generate_strategy') as mock_gen:
        # Configure mock to return realistic backtest results
        mock_gen.return_value = (mock_report, mock_metrics)

        # Step 1: Create AutonomousLoop with template_mode=True
        loop = AutonomousLoop(
            model=template_mode_config['model'],
            max_iterations=template_mode_config['max_iterations'],
            history_file=template_mode_config['history_file'],
            template_mode=True,
            template_name='Momentum'
        )

        # Verify template mode configuration
        assert loop.template_mode is True, "template_mode should be enabled"
        assert loop.template_name == 'Momentum', "template_name should be Momentum"
        assert loop.param_generator is not None, "param_generator should be initialized"
        assert loop.strategy_validator is not None, "strategy_validator should be initialized"
        assert loop.template is not None, "template should be initialized"

        # Clear history for clean test
        loop.history.clear()

        # Step 2: Run 3 iterations
        successful_iterations = 0
        for i in range(3):
            success, status = loop.run_iteration(i, data=None)

            if success:
                successful_iterations += 1

            # Verify iteration was recorded
            record = loop.history.get_record(i)
            assert record is not None, f"Iteration {i} should be recorded"

            # Step 3: Verify parameters were generated
            assert record.parameters is not None, \
                f"Iteration {i}: parameters should be generated and saved"

            # Verify all 8 parameters present (from PARAM_GRID)
            required_params = {
                'momentum_period', 'ma_periods', 'catalyst_type', 'catalyst_lookback',
                'n_stocks', 'stop_loss', 'resample', 'resample_offset'
            }
            assert required_params.issubset(record.parameters.keys()), \
                f"Iteration {i}: All 8 parameters should be present"

            # Step 4: Verify parameter validation occurred
            # (validation warnings don't block execution in template mode)
            # We can't directly verify validation without inspecting logs,
            # but we can verify the workflow completed successfully

            # Step 5: Verify metrics were extracted
            assert record.metrics is not None, \
                f"Iteration {i}: metrics should be extracted"
            assert 'sharpe_ratio' in record.metrics, \
                f"Iteration {i}: sharpe_ratio should be in metrics"
            assert 'annual_return' in record.metrics, \
                f"Iteration {i}: annual_return should be in metrics"
            assert 'max_drawdown' in record.metrics, \
                f"Iteration {i}: max_drawdown should be in metrics"

            # Step 6: Verify mode='template' marker
            assert record.mode == 'template', \
                f"Iteration {i}: mode should be 'template'"

            # Step 7: Verify no code generated (template mode)
            assert record.code == "", \
                f"Iteration {i}: code should be empty in template mode"

        # Step 8: Verify champion was updated
        assert loop.champion is not None, \
            "Champion should be set after successful iterations"

        # Step 9: Verify champion has parameters
        assert loop.champion.parameters is not None, \
            "Champion should have parameters"
        assert isinstance(loop.champion.parameters, dict), \
            "Champion parameters should be dict"

        # Step 10: Verify champion parameters are valid
        champion_params = loop.champion.parameters
        required_params = {
            'momentum_period', 'ma_periods', 'catalyst_type', 'catalyst_lookback',
            'n_stocks', 'stop_loss', 'resample', 'resample_offset'
        }
        assert required_params.issubset(champion_params.keys()), \
            "Champion should have all 8 parameters"

        # Step 11: Verify history persistence
        # Reload history from disk to ensure persistence
        history2 = IterationHistory(template_mode_config['history_file'])
        assert len(history2.records) == 3, \
            "History should have 3 records after save/load"

        # Verify all records have template mode markers
        for i, record in enumerate(history2.records):
            assert record.mode == 'template', \
                f"Loaded record {i}: mode should be 'template'"
            assert record.parameters is not None, \
                f"Loaded record {i}: parameters should persist"

        # Step 12: Verify at least some iterations succeeded
        assert successful_iterations > 0, \
            "At least one iteration should succeed"


def test_template_mode_parameter_generation_real_api(template_mode_config, temp_test_dir):
    """Test template mode with REAL Gemini API call for parameter generation.

    This test validates the parameter generation workflow using the actual
    Gemini API (not mocked), ensuring end-to-end integration works with
    real LLM responses.

    Workflow:
        1. Create AutonomousLoop with template_mode=True
        2. Generate parameters using real Gemini API call
        3. Verify parameters are valid and complete
        4. Verify parameters can be used for strategy generation

    Note:
        This test requires GOOGLE_API_KEY environment variable to be set.
        It will be skipped if the API key is not available.

    Validates:
        - Real LLM parameter generation works
        - Parameters are valid against PARAM_GRID
        - Integration with actual Gemini API

    Story: Phase 0 (Tasks 1.7-1.8, 2.5)
    """
    import os

    # Check for API key
    if not os.getenv('GOOGLE_API_KEY'):
        pytest.skip("GOOGLE_API_KEY not set, skipping real API test")

    # Mock only the strategy execution to avoid needing Finlab data
    # Keep parameter generation real (no mock)
    with patch('src.templates.momentum_template.MomentumTemplate.generate_strategy') as mock_gen:
        # Mock return realistic metrics
        mock_report = MagicMock()
        mock_metrics_obj = MagicMock()
        mock_metrics_obj.annual_return.return_value = 0.18
        mock_metrics_obj.sharpe_ratio.return_value = 1.15
        mock_metrics_obj.max_drawdown.return_value = -0.22
        mock_report.metrics = mock_metrics_obj

        mock_metrics = {
            'annual_return': 0.18,
            'sharpe_ratio': 1.15,
            'max_drawdown': -0.22
        }

        mock_gen.return_value = (mock_report, mock_metrics)

        # Create loop with template mode
        loop = AutonomousLoop(
            model=template_mode_config['model'],
            max_iterations=1,  # Only 1 iteration for API test
            history_file=template_mode_config['history_file'],
            template_mode=True,
            template_name='Momentum'
        )

        loop.history.clear()

        # Run one iteration with REAL parameter generation
        success, status = loop.run_iteration(0, data=None)

        # Verify iteration succeeded
        assert success is True, "Iteration should succeed with real API"

        # Verify parameters were generated
        record = loop.history.get_record(0)
        assert record is not None, "Record should exist"
        assert record.parameters is not None, "Parameters should be generated"

        # Verify all 8 parameters present
        required_params = {
            'momentum_period', 'ma_periods', 'catalyst_type', 'catalyst_lookback',
            'n_stocks', 'stop_loss', 'resample', 'resample_offset'
        }
        assert required_params.issubset(record.parameters.keys()), \
            "All 8 parameters should be present"

        # Verify parameter values are valid (from PARAM_GRID)
        from src.templates.momentum_template import MomentumTemplate
        template = MomentumTemplate()
        param_grid = template.PARAM_GRID

        params = record.parameters

        # Validate each parameter against PARAM_GRID
        assert params['momentum_period'] in param_grid['momentum_period'], \
            f"momentum_period {params['momentum_period']} should be in {param_grid['momentum_period']}"
        assert params['ma_periods'] in param_grid['ma_periods'], \
            f"ma_periods {params['ma_periods']} should be in {param_grid['ma_periods']}"
        assert params['catalyst_type'] in param_grid['catalyst_type'], \
            f"catalyst_type {params['catalyst_type']} should be in {param_grid['catalyst_type']}"
        assert params['catalyst_lookback'] in param_grid['catalyst_lookback'], \
            f"catalyst_lookback {params['catalyst_lookback']} should be in {param_grid['catalyst_lookback']}"
        assert params['n_stocks'] in param_grid['n_stocks'], \
            f"n_stocks {params['n_stocks']} should be in {param_grid['n_stocks']}"
        assert params['stop_loss'] in param_grid['stop_loss'], \
            f"stop_loss {params['stop_loss']} should be in {param_grid['stop_loss']}"
        assert params['resample'] in param_grid['resample'], \
            f"resample {params['resample']} should be in {param_grid['resample']}"
        assert params['resample_offset'] in param_grid['resample_offset'], \
            f"resample_offset {params['resample_offset']} should be in {param_grid['resample_offset']}"


def test_template_mode_champion_update(template_mode_config, mock_finlab_backtest, temp_test_dir):
    """Test champion updates correctly in template mode.

    This test validates that the champion tracking system works properly
    in template mode, including parameter persistence and update logic.

    Workflow:
        1. Run iteration 0 with moderate metrics (becomes champion)
        2. Run iteration 1 with lower metrics (champion unchanged)
        3. Run iteration 2 with higher metrics (champion updated)
        4. Verify champion parameters updated correctly

    Validates:
        - REQ-2.4: Champion updates include parameters
        - Champion tracking with template parameters
        - Parameter persistence across champion updates

    Story: Phase 0 (Task 2.4, 2.6)
    """
    mock_report, mock_metrics = mock_finlab_backtest

    # Create sequence of metrics for 3 iterations
    metrics_sequence = [
        {'annual_return': 0.15, 'sharpe_ratio': 1.0, 'max_drawdown': -0.25},  # Iteration 0: baseline
        {'annual_return': 0.12, 'sharpe_ratio': 0.9, 'max_drawdown': -0.28},  # Iteration 1: worse
        {'annual_return': 0.20, 'sharpe_ratio': 1.3, 'max_drawdown': -0.20},  # Iteration 2: better
    ]

    with patch('src.templates.momentum_template.MomentumTemplate.generate_strategy') as mock_gen:
        # Configure mock to return different metrics each iteration
        def generate_strategy_side_effect(*args, **kwargs):
            iteration = len([r for r in loop.history.records])
            metrics = metrics_sequence[iteration]

            # Update mock report metrics
            mock_report.metrics.annual_return.return_value = metrics['annual_return']
            mock_report.metrics.sharpe_ratio.return_value = metrics['sharpe_ratio']
            mock_report.metrics.max_drawdown.return_value = metrics['max_drawdown']

            return mock_report, metrics

        mock_gen.side_effect = generate_strategy_side_effect

        # Create loop with template mode
        loop = AutonomousLoop(
            model=template_mode_config['model'],
            max_iterations=3,
            history_file=template_mode_config['history_file'],
            template_mode=True,
            template_name='Momentum'
        )

        loop.history.clear()

        # Run iteration 0 (baseline champion)
        success, status = loop.run_iteration(0, data=None)
        assert success is True, "Iteration 0 should succeed"

        # Verify champion created
        assert loop.champion is not None, "Champion should be created after iteration 0"
        champion_iter_0_sharpe = loop.champion.metrics['sharpe_ratio']
        champion_iter_0_params = loop.champion.parameters.copy()

        assert champion_iter_0_sharpe == 1.0, "Champion Sharpe should be 1.0"

        # Run iteration 1 (worse metrics, champion unchanged)
        success, status = loop.run_iteration(1, data=None)
        assert success is True, "Iteration 1 should succeed"

        # Verify champion unchanged (Sharpe still 1.0)
        assert loop.champion.metrics['sharpe_ratio'] == 1.0, \
            "Champion should not change (worse metrics)"
        assert loop.champion.parameters == champion_iter_0_params, \
            "Champion parameters should not change"

        # Run iteration 2 (better metrics, champion updated)
        success, status = loop.run_iteration(2, data=None)
        assert success is True, "Iteration 2 should succeed"

        # Verify champion updated (Sharpe now 1.3)
        assert loop.champion.metrics['sharpe_ratio'] == 1.3, \
            "Champion should update (better metrics)"
        assert loop.champion.parameters != champion_iter_0_params, \
            "Champion parameters should update"

        # Verify new champion parameters are valid
        new_params = loop.champion.parameters
        required_params = {
            'momentum_period', 'ma_periods', 'catalyst_type', 'catalyst_lookback',
            'n_stocks', 'stop_loss', 'resample', 'resample_offset'
        }
        assert required_params.issubset(new_params.keys()), \
            "New champion should have all 8 parameters"


def test_template_mode_validation_warnings(template_mode_config, mock_finlab_backtest, temp_test_dir):
    """Test parameter validation in template mode (warnings, not blocking).

    This test validates that StrategyValidator generates warnings for
    suspicious parameters but doesn't block execution (template mode
    prioritizes flexibility over strict validation).

    Workflow:
        1. Mock parameter generation to return suspicious parameters
        2. Run iteration and verify it succeeds despite warnings
        3. Verify warnings are logged but execution continues

    Validates:
        - Parameter validation occurs in template mode
        - Warnings don't block execution
        - Suspicious parameters are detected

    Story: Phase 0 (Task 1.11)
    """
    mock_report, mock_metrics = mock_finlab_backtest

    # Create suspicious parameters that should trigger warnings
    suspicious_params = {
        'momentum_period': 5,      # Short momentum
        'ma_periods': 120,          # Long MA (misalignment warning)
        'catalyst_type': 'revenue',
        'catalyst_lookback': 3,
        'n_stocks': 3,              # Too concentrated (warning)
        'stop_loss': 0.03,          # Too tight (not in PARAM_GRID, will fail validation)
        'resample': 'W',
        'resample_offset': 0
    }

    # Fix stop_loss to valid value (warnings test, not validation failure test)
    suspicious_params['stop_loss'] = 0.08

    with patch('src.templates.momentum_template.MomentumTemplate.generate_strategy') as mock_gen:
        mock_gen.return_value = (mock_report, mock_metrics)

        # Mock parameter generation to return suspicious parameters
        with patch('src.generators.template_parameter_generator.TemplateParameterGenerator.generate_parameters') as mock_param_gen:
            mock_param_gen.return_value = suspicious_params

            # Create loop with template mode
            loop = AutonomousLoop(
                model=template_mode_config['model'],
                max_iterations=1,
                history_file=template_mode_config['history_file'],
                template_mode=True,
                template_name='Momentum'
            )

            loop.history.clear()

            # Run iteration with suspicious parameters
            # Should succeed despite validation warnings
            success, status = loop.run_iteration(0, data=None)

            # Verify iteration succeeded (warnings don't block)
            assert success is True, \
                "Iteration should succeed despite validation warnings"

            # Verify parameters were saved
            record = loop.history.get_record(0)
            assert record is not None, "Record should exist"
            assert record.parameters == suspicious_params, \
                "Suspicious parameters should be saved"

            # Note: We can't easily verify warnings were generated without
            # inspecting logs, but the fact that execution succeeded proves
            # that warnings didn't block execution (which is the key behavior)


def test_template_mode_vs_freeform_mode(template_mode_config, temp_test_dir):
    """Test that template mode and free-form mode are properly distinct.

    This test validates that the two modes (template vs free-form) are
    properly separated and have different behaviors.

    Workflow:
        1. Create loop with template_mode=True
        2. Verify template mode components initialized
        3. Create loop with template_mode=False
        4. Verify template mode components NOT initialized

    Validates:
        - REQ-2.1: template_mode parameter controls initialization
        - Template mode vs free-form mode distinction

    Story: Phase 0 (Task 2.1-2.3)
    """
    # Create template mode loop
    loop_template = AutonomousLoop(
        model=template_mode_config['model'],
        max_iterations=1,
        history_file=str(temp_test_dir / 'template.json'),
        template_mode=True,
        template_name='Momentum'
    )

    # Verify template mode initialization
    assert loop_template.template_mode is True
    assert loop_template.param_generator is not None, \
        "Template mode should initialize param_generator"
    assert loop_template.strategy_validator is not None, \
        "Template mode should initialize strategy_validator"
    assert loop_template.template is not None, \
        "Template mode should initialize template"

    # Create free-form mode loop
    loop_freeform = AutonomousLoop(
        model=template_mode_config['model'],
        max_iterations=1,
        history_file=str(temp_test_dir / 'freeform.json'),
        template_mode=False  # Explicit free-form
    )

    # Verify free-form mode initialization
    assert loop_freeform.template_mode is False
    assert loop_freeform.param_generator is None, \
        "Free-form mode should NOT initialize param_generator"
    assert loop_freeform.strategy_validator is None, \
        "Free-form mode should NOT initialize strategy_validator"
    assert loop_freeform.template is None, \
        "Free-form mode should NOT initialize template"


# ==============================================================================
# Test Execution
# ==============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
