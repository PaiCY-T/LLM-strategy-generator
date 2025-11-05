#!/usr/bin/env python3
"""
Structured Innovation Validator
Task 2.0: YAML/JSON-based Factor Definition Validator

This module validates LLM-generated factor definitions in YAML format,
reducing hallucination risk through schema-based validation.
"""

import yaml
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class ValidationResult:
    """Result of YAML factor validation."""
    success: bool
    factor_def: Optional[Dict] = None
    error: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class StructuredInnovationValidator:
    """
    Validate YAML/JSON factor definitions.

    Validation Layers:
    1. YAML Syntax - Parse and load YAML
    2. Schema Validation - Check required fields and types
    3. Field Availability - Verify fields exist in Finlab data
    4. Mathematical Validity - Ensure valid operations
    """

    # Supported operations
    VALID_OPERATIONS = {
        'multiply', 'divide', 'add', 'subtract',
        'power', 'log', 'abs'
    }

    # Supported null handling strategies
    VALID_NULL_HANDLING = {
        'drop', 'fill_zero', 'forward_fill',
        'backward_fill', 'mean'
    }

    # Supported outlier handling strategies
    VALID_OUTLIER_HANDLING = {
        'none', 'clip', 'winsorize', 'remove'
    }

    # Supported expected directions
    VALID_DIRECTIONS = {
        'higher_is_better', 'lower_is_better', 'neutral'
    }

    # Supported factor types
    VALID_FACTOR_TYPES = {
        'composite', 'derived', 'ratio', 'aggregate'
    }

    # Finlab available fields (placeholder - should be loaded from actual schema)
    DEFAULT_AVAILABLE_FIELDS = {
        # Fundamental fields
        'roe', 'roa', 'debt_to_equity', 'current_ratio',
        'revenue_growth', 'earnings_growth', 'operating_margin',
        'net_margin', 'gross_margin', 'asset_turnover',
        'inventory_turnover', 'receivables_turnover',

        # Price/Valuation fields
        'pe_ratio', 'pb_ratio', 'ps_ratio', 'pcf_ratio',
        'ev_to_ebitda', 'price_to_sales', 'price_to_book',

        # Cash flow fields
        'operating_cash_flow', 'free_cash_flow', 'net_income',
        'capex', 'dividends',

        # Technical fields
        'volume', 'close', 'high', 'low', 'open',
        'market_cap', 'shares_outstanding',

        # Quality indicators
        'dividend_yield', 'payout_ratio', 'retention_ratio',
        'return_on_capital', 'working_capital'
    }

    def __init__(self, data_schema: Optional[Dict[str, Any]] = None):
        """
        Initialize validator.

        Args:
            data_schema: Dictionary of available fields from Finlab data.
                        If None, uses DEFAULT_AVAILABLE_FIELDS.
        """
        if data_schema is not None:
            self.available_fields = set(data_schema.keys())
        else:
            self.available_fields = self.DEFAULT_AVAILABLE_FIELDS

    def validate(self, yaml_definition: str) -> ValidationResult:
        """
        Validate YAML factor definition through 4 layers.

        Args:
            yaml_definition: YAML string containing factor definition

        Returns:
            ValidationResult with success status and error details
        """
        warnings = []

        # Layer 1: YAML Syntax Validation
        try:
            factor_def = yaml.safe_load(yaml_definition)
        except yaml.YAMLError as e:
            return ValidationResult(
                success=False,
                error=f"YAML syntax error: {e}"
            )

        # Check if parsed successfully
        if factor_def is None:
            return ValidationResult(
                success=False,
                error="Empty YAML definition"
            )

        # Layer 2: Schema Validation
        schema_result = self._validate_schema(factor_def)
        if not schema_result[0]:
            return ValidationResult(
                success=False,
                error=schema_result[1]
            )
        warnings.extend(schema_result[2])

        # Layer 3: Field Availability Check
        field_result = self._validate_field_availability(factor_def)
        if not field_result[0]:
            return ValidationResult(
                success=False,
                error=field_result[1]
            )
        warnings.extend(field_result[2])

        # Layer 4: Mathematical Validity
        math_result = self._validate_mathematical_operations(factor_def)
        if not math_result[0]:
            return ValidationResult(
                success=False,
                error=math_result[1]
            )
        warnings.extend(math_result[2])

        return ValidationResult(
            success=True,
            factor_def=factor_def,
            warnings=warnings
        )

    def _validate_schema(self, factor_def: Dict) -> Tuple[bool, str, List[str]]:
        """
        Validate factor definition against schema.

        Returns:
            Tuple of (success: bool, error: str, warnings: List[str])
        """
        warnings = []

        # Check top-level 'factor' key
        if 'factor' not in factor_def:
            return False, "Missing required 'factor' key at top level", warnings

        factor = factor_def['factor']

        # Check required fields
        required_fields = ['name', 'description', 'type', 'components', 'constraints', 'metadata']
        for field in required_fields:
            if field not in factor:
                return False, f"Missing required field: '{field}'", warnings

        # Validate name
        name = factor['name']
        if not isinstance(name, str) or len(name) < 3 or len(name) > 100:
            return False, "Factor name must be string between 3-100 characters", warnings
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name):
            return False, "Factor name must start with letter/underscore and contain only alphanumeric/underscore", warnings

        # Validate description
        description = factor['description']
        if not isinstance(description, str) or len(description) < 10:
            return False, "Description must be string with at least 10 characters", warnings

        # Validate type
        factor_type = factor['type']
        if factor_type not in self.VALID_FACTOR_TYPES:
            return False, f"Invalid factor type '{factor_type}'. Must be one of: {self.VALID_FACTOR_TYPES}", warnings

        # Validate components
        components = factor['components']
        if not isinstance(components, list) or len(components) < 1:
            return False, "Components must be non-empty list", warnings

        for i, comp in enumerate(components):
            if not isinstance(comp, dict):
                return False, f"Component {i} must be dictionary", warnings
            if 'field' not in comp:
                return False, f"Component {i} missing required 'field' key", warnings

            # Validate operation (required for all components except first)
            if i > 0 and 'operation' not in comp:
                return False, f"Component {i} missing required 'operation' key", warnings

            if 'operation' in comp and comp['operation'] not in self.VALID_OPERATIONS:
                return False, f"Component {i} has invalid operation '{comp['operation']}'. Must be one of: {self.VALID_OPERATIONS}", warnings

        # Validate constraints
        constraints = factor['constraints']
        if not isinstance(constraints, dict):
            return False, "Constraints must be dictionary", warnings

        # Check null_handling
        if 'null_handling' in constraints:
            if constraints['null_handling'] not in self.VALID_NULL_HANDLING:
                return False, f"Invalid null_handling '{constraints['null_handling']}'. Must be one of: {self.VALID_NULL_HANDLING}", warnings

        # Check min/max values
        if 'min_value' in constraints and 'max_value' in constraints:
            if constraints['min_value'] >= constraints['max_value']:
                return False, "min_value must be less than max_value", warnings

        # Validate metadata
        metadata = factor['metadata']
        if not isinstance(metadata, dict):
            return False, "Metadata must be dictionary", warnings

        required_metadata = ['rationale', 'expected_direction']
        for field in required_metadata:
            if field not in metadata:
                return False, f"Metadata missing required field: '{field}'", warnings

        # Validate rationale
        rationale = metadata['rationale']
        if not isinstance(rationale, str) or len(rationale) < 20:
            return False, "Rationale must be string with at least 20 characters", warnings

        # Validate expected_direction
        direction = metadata['expected_direction']
        if direction not in self.VALID_DIRECTIONS:
            return False, f"Invalid expected_direction '{direction}'. Must be one of: {self.VALID_DIRECTIONS}", warnings

        return True, "", warnings

    def _validate_field_availability(self, factor_def: Dict) -> Tuple[bool, str, List[str]]:
        """
        Check that all referenced fields exist in available data.

        Returns:
            Tuple of (success: bool, error: str, warnings: List[str])
        """
        warnings = []
        components = factor_def['factor']['components']

        for i, comp in enumerate(components):
            field = comp['field']
            if field not in self.available_fields:
                return False, f"Component {i}: Field '{field}' not available in Finlab data. Available fields: {sorted(self.available_fields)}", warnings

        return True, "", warnings

    def _validate_mathematical_operations(self, factor_def: Dict) -> Tuple[bool, str, List[str]]:
        """
        Validate mathematical operations are valid.

        Returns:
            Tuple of (success: bool, error: str, warnings: List[str])
        """
        warnings = []
        components = factor_def['factor']['components']

        # Check for division by potentially zero fields
        for i, comp in enumerate(components[1:], 1):
            if comp.get('operation') == 'divide':
                dividend_field = comp['field']
                # Warn if dividing by fields that could be zero
                risky_denominators = {'net_income', 'revenue', 'earnings', 'free_cash_flow'}
                if dividend_field in risky_denominators:
                    warnings.append(
                        f"Component {i}: Division by '{dividend_field}' may cause issues if values are zero or negative. "
                        "Code generator will add NaN handling."
                    )

        # Check for log operations on potentially negative fields
        for i, comp in enumerate(components):
            if comp.get('operation') == 'log':
                field = comp['field']
                risky_fields = {'net_income', 'earnings', 'operating_cash_flow'}
                if field in risky_fields:
                    warnings.append(
                        f"Component {i}: Log operation on '{field}' may fail if values are negative or zero. "
                        "Consider adding constraints."
                    )

        # Check if factor has too many components (complexity warning)
        if len(components) > 5:
            warnings.append(
                f"Factor has {len(components)} components, which may be overly complex and prone to overfitting. "
                "Consider simplifying."
            )

        return True, "", warnings

    def generate_python_code(self, factor_def: Dict) -> str:
        """
        Generate Python code from validated YAML factor definition.

        Args:
            factor_def: Validated factor definition dictionary

        Returns:
            Python code string that can be executed to compute the factor
        """
        factor = factor_def['factor']
        components = factor['components']
        constraints = factor['constraints']

        code_lines = []
        code_lines.append("# Generated from YAML factor definition")
        code_lines.append(f"# Factor: {factor['name']}")
        code_lines.append(f"# Description: {factor['description']}")
        code_lines.append("")
        code_lines.append("import numpy as np")
        code_lines.append("import pandas as pd")
        code_lines.append("")

        # Initialize with first component
        first_field = components[0]['field']
        code_lines.append(f"# Start with base field: {first_field}")
        code_lines.append(f"result = data.get('{first_field}')")

        # Apply operations for remaining components
        for i, comp in enumerate(components[1:], 1):
            field = comp['field']
            operation = comp.get('operation', 'multiply')

            code_lines.append(f"# Apply {operation} with {field}")

            if operation == 'multiply':
                code_lines.append(f"result = result * data.get('{field}')")
            elif operation == 'divide':
                # Safe division with NaN handling
                code_lines.append(f"denominator = data.get('{field}').replace(0, np.nan)")
                code_lines.append(f"result = result / denominator")
            elif operation == 'add':
                code_lines.append(f"result = result + data.get('{field}')")
            elif operation == 'subtract':
                code_lines.append(f"result = result - data.get('{field}')")
            elif operation == 'power':
                coefficient = comp.get('coefficient', 2.0)
                code_lines.append(f"result = result ** {coefficient}")
            elif operation == 'log':
                code_lines.append(f"result = np.log(result.replace({{x: np.nan for x in result if x <= 0}})")
            elif operation == 'abs':
                code_lines.append(f"result = np.abs(result)")

        code_lines.append("")
        code_lines.append("# Apply constraints")

        # Apply min/max clipping
        if 'min_value' in constraints:
            min_val = constraints['min_value']
            code_lines.append(f"result = result.clip(lower={min_val})")
        if 'max_value' in constraints:
            max_val = constraints['max_value']
            code_lines.append(f"result = result.clip(upper={max_val})")

        # Apply null handling
        null_handling = constraints.get('null_handling', 'drop')
        code_lines.append(f"# Null handling: {null_handling}")
        if null_handling == 'fill_zero':
            code_lines.append("result = result.fillna(0)")
        elif null_handling == 'forward_fill':
            code_lines.append("result = result.fillna(method='ffill')")
        elif null_handling == 'backward_fill':
            code_lines.append("result = result.fillna(method='bfill')")
        elif null_handling == 'mean':
            code_lines.append("result = result.fillna(result.mean())")
        # 'drop' is default pandas behavior, no code needed

        code_lines.append("")
        code_lines.append("# Return final factor values")
        code_lines.append("factor_values = result")

        return "\n".join(code_lines)

    def get_available_fields(self) -> List[str]:
        """Get list of available fields from Finlab data."""
        return sorted(list(self.available_fields))

    def add_available_field(self, field: str) -> None:
        """Add a field to the available fields set."""
        self.available_fields.add(field)

    def remove_available_field(self, field: str) -> None:
        """Remove a field from the available fields set."""
        self.available_fields.discard(field)


# Standalone validation function
def validate_yaml_factor(yaml_str: str, data_schema: Optional[Dict] = None) -> ValidationResult:
    """
    Standalone function to validate YAML factor definition.

    Args:
        yaml_str: YAML string to validate
        data_schema: Optional data schema for field validation

    Returns:
        ValidationResult with success status and details
    """
    validator = StructuredInnovationValidator(data_schema)
    return validator.validate(yaml_str)


# Example usage
if __name__ == "__main__":
    # Example YAML factor definition
    example_yaml = """
factor:
  name: "Quality_Growth_Value_Composite"
  description: "ROE × Revenue Growth / P/E ratio"
  type: "composite"
  components:
    - field: "roe"
    - field: "revenue_growth"
      operation: "multiply"
    - field: "pe_ratio"
      operation: "divide"
  constraints:
    min_value: 0
    max_value: 100
    null_handling: "drop"
  metadata:
    rationale: "Combines profitability, growth momentum, and value"
    expected_direction: "higher_is_better"
"""

    # Validate
    validator = StructuredInnovationValidator()
    result = validator.validate(example_yaml)

    if result.success:
        print("✅ Validation PASSED")
        if result.warnings:
            print(f"⚠️  Warnings: {len(result.warnings)}")
            for warning in result.warnings:
                print(f"  - {warning}")

        # Generate Python code
        python_code = validator.generate_python_code(result.factor_def)
        print("\nGenerated Python Code:")
        print(python_code)
    else:
        print(f"❌ Validation FAILED: {result.error}")
