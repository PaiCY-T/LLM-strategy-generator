"""
Unit Tests for Factor Base Class

Tests factor creation, validation, and execution according to Task A.1 acceptance criteria.

Test Cases (from Task A.1):
1. Create Factor with valid inputs → success
2. validate_inputs() with available columns → True
3. validate_inputs() with missing columns → False
4. execute() transforms DataFrame → new columns added
5. Invalid category → type error
6. Missing required fields → validation error
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any

from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.factor import Factor


# ======================================================================
# Test Fixtures
# ======================================================================

@pytest.fixture
def sample_data():
    """Sample OHLCV data for testing."""
    return pd.DataFrame({
        "open": [100, 102, 101, 103, 105],
        "high": [102, 104, 103, 105, 107],
        "low": [99, 101, 100, 102, 104],
        "close": [101, 103, 102, 104, 106],
        "volume": [1000, 1100, 1050, 1150, 1200]
    })


@pytest.fixture
def simple_sma_logic():
    """Simple moving average logic function."""
    def add_sma(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result = data.copy()
        period = params.get("period", 20)
        result["sma"] = result["close"].rolling(window=period).mean()
        return result
    return add_sma


@pytest.fixture
def rsi_logic():
    """RSI indicator logic function."""
    def calculate_rsi(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result = data.copy()
        period = params.get("period", 14)

        # Calculate RSI
        delta = result["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)  # Avoid division by zero
        result["rsi"] = 100 - (100 / (1 + rs))

        # Generate signals
        overbought = params.get("overbought", 70)
        oversold = params.get("oversold", 30)
        result["rsi_signal"] = (
            (result["rsi"] > overbought).astype(int) -
            (result["rsi"] < oversold).astype(int)
        )

        return result
    return calculate_rsi


# ======================================================================
# Test Case 1: Create Factor with valid inputs → success
# ======================================================================

def test_create_factor_with_valid_inputs(simple_sma_logic):
    """Test creating a Factor with all required fields."""
    factor = Factor(
        id="sma_20",
        name="Simple Moving Average 20",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["sma"],
        logic=simple_sma_logic,
        parameters={"period": 20},
        description="20-period simple moving average"
    )

    assert factor.id == "sma_20"
    assert factor.name == "Simple Moving Average 20"
    assert factor.category == FactorCategory.MOMENTUM
    assert factor.inputs == ["close"]
    assert factor.outputs == ["sma"]
    assert callable(factor.logic)
    assert factor.parameters == {"period": 20}
    assert factor.description == "20-period simple moving average"


def test_create_factor_minimal_required_fields(simple_sma_logic):
    """Test creating a Factor with only required fields (no optional description)."""
    factor = Factor(
        id="test_factor",
        name="Test Factor",
        category=FactorCategory.SIGNAL,
        inputs=["close"],
        outputs=["signal"],
        logic=simple_sma_logic
    )

    assert factor.id == "test_factor"
    assert factor.parameters == {}  # Default empty dict
    assert factor.description == ""  # Default empty string


# ======================================================================
# Test Case 2: validate_inputs() with available columns → True
# ======================================================================

def test_validate_inputs_all_available(simple_sma_logic):
    """Test validate_inputs returns True when all required inputs are available."""
    factor = Factor(
        id="sma_20",
        name="SMA 20",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["sma"],
        logic=simple_sma_logic,
        parameters={"period": 20}
    )

    available_columns = ["open", "high", "low", "close", "volume"]
    assert factor.validate_inputs(available_columns) is True


def test_validate_inputs_multiple_requirements(rsi_logic):
    """Test validate_inputs with factor requiring multiple input columns."""
    factor = Factor(
        id="multi_input",
        name="Multi Input Factor",
        category=FactorCategory.MOMENTUM,
        inputs=["high", "low", "close"],
        outputs=["indicator"],
        logic=rsi_logic
    )

    available_columns = ["open", "high", "low", "close", "volume"]
    assert factor.validate_inputs(available_columns) is True


# ======================================================================
# Test Case 3: validate_inputs() with missing columns → False
# ======================================================================

def test_validate_inputs_missing_column(simple_sma_logic):
    """Test validate_inputs returns False when required input is missing."""
    factor = Factor(
        id="sma_20",
        name="SMA 20",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["sma"],
        logic=simple_sma_logic
    )

    # Missing 'close' column
    available_columns = ["open", "high", "low", "volume"]
    assert factor.validate_inputs(available_columns) is False


def test_validate_inputs_multiple_missing(rsi_logic):
    """Test validate_inputs with multiple missing inputs."""
    factor = Factor(
        id="multi_input",
        name="Multi Input Factor",
        category=FactorCategory.MOMENTUM,
        inputs=["high", "low", "close", "volume", "special_column"],
        outputs=["indicator"],
        logic=rsi_logic
    )

    # Missing 'special_column'
    available_columns = ["open", "high", "low", "close", "volume"]
    assert factor.validate_inputs(available_columns) is False


# ======================================================================
# Test Case 4: execute() transforms DataFrame → new columns added
# ======================================================================

def test_execute_adds_output_columns(sample_data, simple_sma_logic):
    """Test execute adds output columns to DataFrame."""
    factor = Factor(
        id="sma_5",
        name="SMA 5",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["sma"],
        logic=simple_sma_logic,
        parameters={"period": 3}
    )

    result = factor.execute(sample_data)

    # Check new column is added
    assert "sma" in result.columns

    # Check original columns preserved
    assert "open" in result.columns
    assert "close" in result.columns

    # Check SMA values are calculated
    assert not result["sma"].isna().all()


def test_execute_multiple_outputs(sample_data, rsi_logic):
    """Test execute with factor producing multiple output columns."""
    factor = Factor(
        id="rsi_14",
        name="RSI 14",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["rsi", "rsi_signal"],
        logic=rsi_logic,
        parameters={"period": 3, "overbought": 70, "oversold": 30}
    )

    result = factor.execute(sample_data)

    # Check both outputs are added
    assert "rsi" in result.columns
    assert "rsi_signal" in result.columns

    # Check RSI values are in expected range (0-100)
    rsi_values = result["rsi"].dropna()
    if len(rsi_values) > 0:
        assert rsi_values.min() >= 0
        assert rsi_values.max() <= 100


def test_execute_preserves_original_data(sample_data, simple_sma_logic):
    """Test execute does not modify original input data."""
    original_columns = set(sample_data.columns)
    original_close = sample_data["close"].copy()

    factor = Factor(
        id="sma_20",
        name="SMA 20",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["sma"],
        logic=simple_sma_logic,
        parameters={"period": 3}
    )

    result = factor.execute(sample_data)

    # Original data should be unchanged
    assert set(sample_data.columns) == original_columns
    assert sample_data["close"].equals(original_close)

    # Result should have new column
    assert "sma" in result.columns


def test_execute_raises_on_missing_inputs(sample_data, simple_sma_logic):
    """Test execute raises KeyError when required inputs are missing."""
    factor = Factor(
        id="invalid",
        name="Invalid Factor",
        category=FactorCategory.MOMENTUM,
        inputs=["close", "nonexistent_column"],
        outputs=["output"],
        logic=simple_sma_logic
    )

    with pytest.raises(KeyError) as exc_info:
        factor.execute(sample_data)

    assert "nonexistent_column" in str(exc_info.value)


# ======================================================================
# Test Case 5: Invalid category → type error
# ======================================================================

def test_invalid_category_type_error(simple_sma_logic):
    """Test Factor creation raises TypeError for invalid category."""
    with pytest.raises(TypeError) as exc_info:
        Factor(
            id="test",
            name="Test",
            category="invalid_string",  # Should be FactorCategory enum
            inputs=["close"],
            outputs=["signal"],
            logic=simple_sma_logic
        )

    assert "FactorCategory" in str(exc_info.value)


def test_valid_category_all_enum_values(simple_sma_logic):
    """Test Factor creation succeeds with all valid FactorCategory values."""
    for category in FactorCategory:
        factor = Factor(
            id=f"test_{category.value}",
            name=f"Test {category.value}",
            category=category,
            inputs=["close"],
            outputs=["output"],
            logic=simple_sma_logic
        )
        assert factor.category == category


# ======================================================================
# Test Case 6: Missing required fields → validation error
# ======================================================================

def test_missing_id_raises_error(simple_sma_logic):
    """Test Factor creation raises ValueError when id is empty."""
    with pytest.raises(ValueError) as exc_info:
        Factor(
            id="",  # Empty id
            name="Test",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["signal"],
            logic=simple_sma_logic
        )

    assert "id cannot be empty" in str(exc_info.value)


def test_missing_name_raises_error(simple_sma_logic):
    """Test Factor creation raises ValueError when name is empty."""
    with pytest.raises(ValueError) as exc_info:
        Factor(
            id="test",
            name="",  # Empty name
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["signal"],
            logic=simple_sma_logic
        )

    assert "name cannot be empty" in str(exc_info.value)


def test_empty_inputs_raises_error(simple_sma_logic):
    """Test Factor creation raises ValueError when inputs list is empty."""
    with pytest.raises(ValueError) as exc_info:
        Factor(
            id="test",
            name="Test",
            category=FactorCategory.MOMENTUM,
            inputs=[],  # Empty inputs
            outputs=["signal"],
            logic=simple_sma_logic
        )

    assert "at least one input" in str(exc_info.value)


def test_empty_outputs_raises_error(simple_sma_logic):
    """Test Factor creation raises ValueError when outputs list is empty."""
    with pytest.raises(ValueError) as exc_info:
        Factor(
            id="test",
            name="Test",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=[],  # Empty outputs
            logic=simple_sma_logic
        )

    assert "at least one output" in str(exc_info.value)


def test_non_callable_logic_raises_error():
    """Test Factor creation raises TypeError when logic is not callable."""
    with pytest.raises(TypeError) as exc_info:
        Factor(
            id="test",
            name="Test",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["signal"],
            logic="not_a_function"  # Not callable
        )

    assert "must be callable" in str(exc_info.value)


# ======================================================================
# Additional Edge Case Tests
# ======================================================================

def test_duplicate_inputs_raises_error(simple_sma_logic):
    """Test Factor creation raises ValueError when inputs contain duplicates."""
    with pytest.raises(ValueError) as exc_info:
        Factor(
            id="test",
            name="Test",
            category=FactorCategory.MOMENTUM,
            inputs=["close", "volume", "close"],  # Duplicate 'close'
            outputs=["signal"],
            logic=simple_sma_logic
        )

    assert "duplicates" in str(exc_info.value)


def test_duplicate_outputs_raises_error(simple_sma_logic):
    """Test Factor creation raises ValueError when outputs contain duplicates."""
    with pytest.raises(ValueError) as exc_info:
        Factor(
            id="test",
            name="Test",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["signal", "value", "signal"],  # Duplicate 'signal'
            logic=simple_sma_logic
        )

    assert "duplicates" in str(exc_info.value)


def test_invalid_id_format_raises_error(simple_sma_logic):
    """Test Factor creation raises ValueError for invalid id format."""
    with pytest.raises(ValueError) as exc_info:
        Factor(
            id="invalid id with spaces",  # Spaces not allowed
            name="Test",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["signal"],
            logic=simple_sma_logic
        )

    assert "alphanumeric" in str(exc_info.value).lower()


def test_factor_repr(simple_sma_logic):
    """Test Factor __repr__ returns useful developer representation."""
    factor = Factor(
        id="sma_20",
        name="SMA 20",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["sma"],
        logic=simple_sma_logic,
        parameters={"period": 20}
    )

    repr_str = repr(factor)
    assert "sma_20" in repr_str
    assert "SMA 20" in repr_str
    assert "MOMENTUM" in repr_str
    assert "close" in repr_str
    assert "sma" in repr_str


def test_factor_str(simple_sma_logic):
    """Test Factor __str__ returns human-readable representation."""
    factor = Factor(
        id="sma_20",
        name="SMA 20",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["sma"],
        logic=simple_sma_logic
    )

    str_repr = str(factor)
    assert "SMA 20" in str_repr
    assert "close" in str_repr
    assert "sma" in str_repr


def test_execute_logic_exception_handling(sample_data):
    """Test execute wraps logic exceptions with context."""
    def faulty_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        raise RuntimeError("Intentional error for testing")

    factor = Factor(
        id="faulty",
        name="Faulty Factor",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["output"],
        logic=faulty_logic
    )

    with pytest.raises(RuntimeError) as exc_info:
        factor.execute(sample_data)

    error_msg = str(exc_info.value)
    assert "faulty" in error_msg.lower()
    assert "execution failed" in error_msg.lower()


def test_execute_missing_outputs_raises_error(sample_data):
    """Test execute raises RuntimeError when logic doesn't produce expected outputs."""
    def incomplete_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        return data.copy()  # Doesn't add expected 'output' column

    factor = Factor(
        id="incomplete",
        name="Incomplete Factor",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["output", "another_output"],
        logic=incomplete_logic
    )

    with pytest.raises(RuntimeError) as exc_info:
        factor.execute(sample_data)

    error_msg = str(exc_info.value)
    assert "did not produce" in error_msg.lower()
    assert "output" in error_msg or "another_output" in error_msg
