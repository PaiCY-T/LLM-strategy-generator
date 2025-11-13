"""
Test Suite for Factor.execute() (Phase 2.0 Matrix-Native)
=========================================================

Comprehensive tests for Factor.execute() method with FinLabDataFrame container.
Tests cover container input/output, validation, error handling, and method chaining.

Test Coverage:
--------------
1. Basic Execution
   - Container input and output
   - Logic function execution
   - Method chaining

2. Input Validation
   - Missing input matrices
   - Input existence checks
   - Error messages with available matrices

3. Output Validation
   - Output matrix creation
   - Missing output detection
   - Multiple outputs

4. Error Handling
   - Logic function errors
   - Container type errors
   - Validation failures

Architecture: Phase 2.0 Matrix-Native Factor Graph System
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock

from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.finlab_dataframe import FinLabDataFrame


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_container():
    """Create sample container with test data."""
    dates = pd.date_range('2023-01-01', periods=50)
    symbols = ['2330', '2317', '2454']

    close = pd.DataFrame(
        np.random.randn(50, 3) * 10 + 100,
        index=dates,
        columns=symbols
    )

    container = FinLabDataFrame()
    container.add_matrix('close', close)
    return container


@pytest.fixture
def simple_factor():
    """Create simple factor for testing."""
    def logic(container, parameters):
        close = container.get_matrix('close')
        period = parameters['period']
        momentum = (close / close.shift(period)) - 1
        container.add_matrix('momentum', momentum)

    return Factor(
        id='momentum_10',
        name='Momentum 10',
        category=FactorCategory.MOMENTUM,
        inputs=['close'],
        outputs=['momentum'],
        logic=logic,
        parameters={'period': 10}
    )


# ============================================================================
# Basic Execution Tests
# ============================================================================

class TestBasicExecution:
    """Test basic Factor.execute() functionality."""

    def test_execute_accepts_container(self, sample_container, simple_factor):
        """Test that execute accepts FinLabDataFrame container."""
        # Should not raise
        result = simple_factor.execute(sample_container)

        assert result is not None
        assert isinstance(result, FinLabDataFrame)

    def test_execute_returns_container(self, sample_container, simple_factor):
        """Test that execute returns the container (method chaining)."""
        result = simple_factor.execute(sample_container)

        # Should return same container for chaining
        assert result == sample_container
        assert result.has_matrix('momentum')

    def test_execute_modifies_container_in_place(self, sample_container, simple_factor):
        """Test that execute modifies container in-place."""
        original_id = id(sample_container)

        result = simple_factor.execute(sample_container)

        # Same object
        assert id(result) == original_id
        assert sample_container.has_matrix('momentum')

    def test_logic_function_is_called(self, sample_container):
        """Test that logic function is executed."""
        logic_called = []

        def tracking_logic(container, parameters):
            logic_called.append(True)
            close = container.get_matrix('close')
            container.add_matrix('output', close * 1.1)

        factor = Factor(
            id='test', name='Test', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['output'],
            logic=tracking_logic, parameters={}
        )

        factor.execute(sample_container)

        assert len(logic_called) == 1

    def test_method_chaining(self, sample_container):
        """Test method chaining through multiple factors."""
        def logic1(container, parameters):
            close = container.get_matrix('close')
            container.add_matrix('output1', close * 1.1)

        def logic2(container, parameters):
            output1 = container.get_matrix('output1')
            container.add_matrix('output2', output1 * 1.1)

        factor1 = Factor(
            id='f1', name='F1', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['output1'], logic=logic1, parameters={}
        )

        factor2 = Factor(
            id='f2', name='F2', category=FactorCategory.MOMENTUM,
            inputs=['output1'], outputs=['output2'], logic=logic2, parameters={}
        )

        # Chain execution
        result = factor1.execute(sample_container)
        result = factor2.execute(result)

        assert sample_container.has_matrix('output1')
        assert sample_container.has_matrix('output2')


# ============================================================================
# Input Validation Tests
# ============================================================================

class TestInputValidation:
    """Test input matrix validation."""

    def test_missing_input_raises_keyerror(self, sample_container):
        """Test that missing input matrix raises KeyError."""
        def logic(container, parameters):
            container.get_matrix('nonexistent')

        factor = Factor(
            id='test', name='Test', category=FactorCategory.MOMENTUM,
            inputs=['nonexistent'], outputs=['output'],
            logic=logic, parameters={}
        )

        with pytest.raises(KeyError, match="Missing matrices"):
            factor.execute(sample_container)

    def test_error_message_lists_available_matrices(self, sample_container):
        """Test that error message lists available matrices."""
        def logic(container, parameters):
            pass

        factor = Factor(
            id='test', name='Test', category=FactorCategory.MOMENTUM,
            inputs=['missing1', 'missing2'], outputs=['output'],
            logic=logic, parameters={}
        )

        with pytest.raises(KeyError) as exc_info:
            factor.execute(sample_container)

        error_msg = str(exc_info.value)
        assert 'missing1' in error_msg or 'missing2' in error_msg
        assert 'Available' in error_msg
        assert 'close' in error_msg  # Should list available matrix

    def test_multiple_missing_inputs(self, sample_container):
        """Test multiple missing inputs are reported."""
        def logic(container, parameters):
            pass

        factor = Factor(
            id='test', name='Test', category=FactorCategory.MOMENTUM,
            inputs=['input1', 'input2', 'input3'], outputs=['output'],
            logic=logic, parameters={}
        )

        with pytest.raises(KeyError, match="Missing matrices"):
            factor.execute(sample_container)

    def test_partial_inputs_available(self, sample_container):
        """Test error when only some inputs are available."""
        # Add one input
        sample_container.add_matrix('input1', sample_container.get_matrix('close'))

        def logic(container, parameters):
            pass

        factor = Factor(
            id='test', name='Test', category=FactorCategory.MOMENTUM,
            inputs=['input1', 'input2'], outputs=['output'],
            logic=logic, parameters={}
        )

        with pytest.raises(KeyError, match="input2"):
            factor.execute(sample_container)


# ============================================================================
# Output Validation Tests
# ============================================================================

class TestOutputValidation:
    """Test output matrix validation."""

    def test_missing_output_raises_error(self, sample_container):
        """Test that missing output matrix raises RuntimeError."""
        def bad_logic(container, parameters):
            # Logic doesn't produce output
            pass

        factor = Factor(
            id='test', name='Test', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['expected_output'],
            logic=bad_logic, parameters={}
        )

        with pytest.raises(RuntimeError, match="did not produce"):
            factor.execute(sample_container)

    def test_multiple_outputs_validation(self, sample_container):
        """Test validation of multiple output matrices."""
        def partial_logic(container, parameters):
            close = container.get_matrix('close')
            # Only produce one of two expected outputs
            container.add_matrix('output1', close * 1.1)
            # Missing output2

        factor = Factor(
            id='test', name='Test', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['output1', 'output2'],
            logic=partial_logic, parameters={}
        )

        with pytest.raises(RuntimeError, match="output2"):
            factor.execute(sample_container)

    def test_all_outputs_produced(self, sample_container):
        """Test successful execution when all outputs are produced."""
        def complete_logic(container, parameters):
            close = container.get_matrix('close')
            container.add_matrix('output1', close * 1.1)
            container.add_matrix('output2', close * 1.2)
            container.add_matrix('output3', close * 1.3)

        factor = Factor(
            id='test', name='Test', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['output1', 'output2', 'output3'],
            logic=complete_logic, parameters={}
        )

        # Should not raise
        factor.execute(sample_container)

        assert sample_container.has_matrix('output1')
        assert sample_container.has_matrix('output2')
        assert sample_container.has_matrix('output3')


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling in Factor.execute()."""

    def test_logic_function_error_propagates(self, sample_container):
        """Test that errors in logic function propagate correctly."""
        def error_logic(container, parameters):
            raise ValueError("Intentional error in logic")

        factor = Factor(
            id='test', name='Test', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['output'],
            logic=error_logic, parameters={}
        )

        with pytest.raises(ValueError, match="Intentional error"):
            factor.execute(sample_container)

    def test_wrong_container_type_error(self, simple_factor):
        """Test that wrong container type raises error."""
        # Pass DataFrame instead of FinLabDataFrame
        wrong_container = pd.DataFrame({'close': [1, 2, 3]})

        with pytest.raises((AttributeError, TypeError)):
            simple_factor.execute(wrong_container)

    def test_none_container_error(self, simple_factor):
        """Test that None container raises error."""
        with pytest.raises((AttributeError, TypeError)):
            simple_factor.execute(None)

    def test_parameter_access_in_logic(self, sample_container):
        """Test that parameters are correctly passed to logic."""
        captured_params = []

        def param_logic(container, parameters):
            captured_params.append(parameters)
            close = container.get_matrix('close')
            period = parameters['test_period']
            container.add_matrix('output', close.rolling(period).mean())

        factor = Factor(
            id='test', name='Test', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['output'],
            logic=param_logic,
            parameters={'test_period': 20, 'other_param': 'value'}
        )

        factor.execute(sample_container)

        assert len(captured_params) == 1
        assert captured_params[0]['test_period'] == 20
        assert captured_params[0]['other_param'] == 'value'


# ============================================================================
# Integration with FinLabDataFrame Tests
# ============================================================================

class TestContainerIntegration:
    """Test integration with FinLabDataFrame operations."""

    def test_lazy_loading_in_factor(self):
        """Test that lazy loading works within factor execution."""
        mock_data = Mock()
        mock_data.get = Mock(return_value=pd.DataFrame(
            np.random.rand(10, 3),
            index=pd.date_range('2023-01-01', periods=10),
            columns=['A', 'B', 'C']
        ))

        container = FinLabDataFrame(data_module=mock_data)

        def lazy_logic(container, parameters):
            # This should trigger lazy loading
            close = container.get_matrix('close', lazy_load=True)
            container.add_matrix('output', close * 1.1)

        factor = Factor(
            id='test', name='Test', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['output'],
            logic=lazy_logic, parameters={}
        )

        factor.execute(container)

        # Lazy loading should have been triggered
        assert container.has_matrix('close')
        assert container.has_matrix('output')

    def test_shape_validation_in_factor(self, sample_container):
        """Test that shape validation occurs within factor."""
        def bad_shape_logic(container, parameters):
            close = container.get_matrix('close')
            # Create matrix with wrong shape
            wrong_shape = pd.DataFrame(np.random.rand(10, 10))  # Wrong shape
            container.add_matrix('bad_output', wrong_shape, validate=True)

        factor = Factor(
            id='test', name='Test', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['bad_output'],
            logic=bad_shape_logic, parameters={}
        )

        with pytest.raises(ValueError, match="does not match base shape"):
            factor.execute(sample_container)

    def test_multiple_factors_share_container(self, sample_container):
        """Test that multiple factors can work on same container."""
        def logic1(container, parameters):
            close = container.get_matrix('close')
            container.add_matrix('ma_short', close.rolling(5).mean())

        def logic2(container, parameters):
            close = container.get_matrix('close')
            container.add_matrix('ma_long', close.rolling(20).mean())

        def logic3(container, parameters):
            ma_short = container.get_matrix('ma_short')
            ma_long = container.get_matrix('ma_long')
            signal = (ma_short > ma_long).astype(float)
            container.add_matrix('signal', signal)

        factors = [
            Factor(id='f1', name='F1', category=FactorCategory.MOMENTUM,
                   inputs=['close'], outputs=['ma_short'], logic=logic1, parameters={}),
            Factor(id='f2', name='F2', category=FactorCategory.MOMENTUM,
                   inputs=['close'], outputs=['ma_long'], logic=logic2, parameters={}),
            Factor(id='f3', name='F3', category=FactorCategory.ENTRY,
                   inputs=['ma_short', 'ma_long'], outputs=['signal'], logic=logic3, parameters={})
        ]

        # Execute all factors on same container
        for factor in factors:
            factor.execute(sample_container)

        # All outputs should be present
        assert sample_container.has_matrix('ma_short')
        assert sample_container.has_matrix('ma_long')
        assert sample_container.has_matrix('signal')


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases in Factor.execute()."""

    def test_factor_with_no_inputs(self):
        """Test factor that requires no inputs."""
        container = FinLabDataFrame()

        def no_input_logic(container, parameters):
            # Generate constant output
            output = pd.DataFrame(
                [[1, 2, 3]] * 10,
                columns=['A', 'B', 'C']
            )
            container.add_matrix('constant', output)

        factor = Factor(
            id='constant', name='Constant', category=FactorCategory.ENTRY,
            inputs=[], outputs=['constant'],
            logic=no_input_logic, parameters={}
        )

        # Should work even with empty container
        factor.execute(container)
        assert container.has_matrix('constant')

    def test_factor_with_empty_parameters(self, sample_container):
        """Test factor with empty parameters dict."""
        def simple_logic(container, parameters):
            close = container.get_matrix('close')
            container.add_matrix('output', close * 2)

        factor = Factor(
            id='test', name='Test', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['output'],
            logic=simple_logic,
            parameters={}  # Empty parameters
        )

        # Should work
        factor.execute(sample_container)
        assert sample_container.has_matrix('output')

    def test_factor_modifying_input_matrix(self, sample_container):
        """Test that factor can't accidentally modify input matrix (immutability)."""
        original_close = sample_container.get_matrix('close').copy()

        def modifying_logic(container, parameters):
            close = container.get_matrix('close')
            # Try to modify (shouldn't affect container)
            close.iloc[0, 0] = 999
            container.add_matrix('output', close)

        factor = Factor(
            id='test', name='Test', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['output'],
            logic=modifying_logic, parameters={}
        )

        factor.execute(sample_container)

        # Original close should be unchanged in container
        # (This depends on FinLabDataFrame's copy-on-add behavior)
        current_close = sample_container.get_matrix('close')
        pd.testing.assert_frame_equal(current_close, original_close)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
