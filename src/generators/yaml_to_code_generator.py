"""
YAML to Code Generator Module
==============================

Complete YAML → Python code generation pipeline integrating schema validation,
Jinja2 template rendering, and AST syntax validation.

This module provides the YAMLToCodeGenerator class which orchestrates the entire
process of converting a declarative YAML strategy specification into executable
Python code:

1. YAML Schema Validation (via YAMLSchemaValidator)
2. Template Rendering (via YAMLToCodeTemplate)
3. AST Syntax Validation (via ast.parse)
4. Error Reporting and Recovery

Architecture:
-------------
The generator acts as a coordinator between validation and code generation components,
ensuring that only valid YAML specs produce code and that all generated code is
syntactically correct.

Key Features:
-------------
1. **Integrated Validation**: Uses YAMLSchemaValidator to ensure YAML specs
   conform to schema before code generation
2. **Template-Based Generation**: Leverages YAMLToCodeTemplate for consistent,
   maintainable code generation
3. **AST Validation**: Guarantees syntactically correct Python output
4. **Clear Error Reporting**: Returns actionable error messages for validation
   and generation failures
5. **File-Based or Dict-Based**: Supports both YAML file input and parsed dict input

Supported Strategy Types:
-------------------------
- momentum: Trend-following strategies with momentum indicators
- mean_reversion: Mean reversion strategies with overbought/oversold signals
- factor_combination: Multi-factor strategies combining fundamental and technical

Supported Position Sizing Methods:
-----------------------------------
- equal_weight: Uniform distribution across all positions
- factor_weighted: Weight by factor score
- risk_parity: Volatility-adjusted weights
- volatility_weighted: Inverse volatility weighting
- custom_formula: User-defined expressions

Requirements:
-------------
- Task 4 of structured-innovation-mvp spec
- Requirements 2.3: Syntactically correct Python code generation
- Requirements 2.4: Correct FinLab API usage
- Requirements 2.5: All indicator types and position sizing methods supported
- Requirements 5.2: Integration with validation and template modules

Usage:
------
>>> from src.generators.yaml_to_code_generator import YAMLToCodeGenerator
>>> from src.generators.yaml_schema_validator import YAMLSchemaValidator
>>>
>>> # Initialize with validator
>>> validator = YAMLSchemaValidator()
>>> generator = YAMLToCodeGenerator(validator)
>>>
>>> # Generate from YAML file
>>> code, errors = generator.generate_from_file('strategy.yaml')
>>> if errors:
...     for error in errors:
...         print(f"Error: {error}")
... else:
...     print(code)
>>>
>>> # Generate from parsed YAML dict
>>> import yaml
>>> with open('strategy.yaml') as f:
...     spec = yaml.safe_load(f)
>>> code, errors = generator.generate(spec)
"""

import ast
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from src.generators.yaml_schema_validator import YAMLSchemaValidator
from src.generators.yaml_to_code_template import YAMLToCodeTemplate

logger = logging.getLogger(__name__)


class YAMLToCodeGenerator:
    """
    Generate syntactically correct Python strategy code from YAML specifications.

    This class orchestrates the complete YAML → Python code pipeline:
    1. Validate YAML spec against JSON Schema
    2. Render Jinja2 template with validated spec data
    3. Validate generated Python code with AST parser
    4. Return code or actionable error messages

    The generator guarantees that all produced code is syntactically correct
    and follows FinLab API conventions.

    Attributes:
        validator (YAMLSchemaValidator): Schema validator for YAML validation
        template (YAMLToCodeTemplate): Jinja2 template renderer for code generation
        validate_semantics (bool): Whether to validate indicator references
    """

    def __init__(
        self,
        schema_validator: Optional[YAMLSchemaValidator] = None,
        validate_semantics: bool = True
    ):
        """
        Initialize the YAML to Code generator.

        Args:
            schema_validator: YAMLSchemaValidator instance. If None, creates default.
            validate_semantics: If True, validate indicator references (cross-field validation)

        Example:
            >>> validator = YAMLSchemaValidator()
            >>> generator = YAMLToCodeGenerator(validator)
        """
        # Use provided validator or create default
        if schema_validator is None:
            logger.info("No validator provided, creating default YAMLSchemaValidator")
            self.validator = YAMLSchemaValidator()
        else:
            self.validator = schema_validator

        # Create template renderer
        self.template = YAMLToCodeTemplate()

        # Semantic validation flag
        self.validate_semantics = validate_semantics

        logger.info("YAMLToCodeGenerator initialized successfully")

    def generate(
        self,
        yaml_spec: Dict[str, Any]
    ) -> Tuple[Optional[str], List[str]]:
        """
        Generate Python code from a validated YAML specification.

        This is the main method that coordinates the entire generation pipeline:
        1. Validate YAML spec against schema
        2. Optionally validate indicator references (semantic validation)
        3. Render Jinja2 template with spec data
        4. Validate generated code with AST parser
        5. Return code or errors

        Args:
            yaml_spec: Parsed YAML specification as dictionary
                Must contain at minimum: metadata, indicators, entry_conditions
                Optional: exit_conditions, position_sizing, risk_management

        Returns:
            Tuple of (code, errors):
                - code: Generated Python code string (None if errors)
                - errors: List of validation/generation error messages (empty if success)

        Example:
            >>> import yaml
            >>> with open('strategy.yaml') as f:
            ...     spec = yaml.safe_load(f)
            >>> code, errors = generator.generate(spec)
            >>> if not errors:
            ...     print("Generated code:")
            ...     print(code)
            ... else:
            ...     print("Errors:")
            ...     for error in errors:
            ...         print(f"  - {error}")
        """
        errors = []

        # Step 1: Validate YAML against schema
        logger.debug("Step 1: Validating YAML spec against schema")
        is_valid, validation_errors = self.validator.validate(yaml_spec)

        if not is_valid:
            logger.warning(f"YAML validation failed with {len(validation_errors)} error(s)")
            return None, validation_errors

        logger.info("YAML validation passed")

        # Step 2: Semantic validation (indicator references)
        if self.validate_semantics:
            logger.debug("Step 2: Validating indicator references (semantic validation)")
            semantic_valid, semantic_errors = self.validator.validate_indicator_references(yaml_spec)

            if not semantic_valid:
                logger.warning(f"Semantic validation failed: {len(semantic_errors)} error(s)")
                return None, semantic_errors

            logger.info("Semantic validation passed")

        # Step 3: Render Jinja2 template
        logger.debug("Step 3: Rendering Jinja2 template")
        try:
            code = self.template.generate(yaml_spec)
            logger.info(f"Template rendering successful ({len(code)} characters)")
        except Exception as e:
            error_msg = f"Template rendering failed: {str(e)}"
            logger.error(error_msg)
            return None, [error_msg]

        # Step 4: Validate generated code with AST
        logger.debug("Step 4: Validating generated Python code with AST")
        try:
            ast.parse(code)
            logger.info("AST validation passed - code is syntactically correct")
        except SyntaxError as e:
            error_msg = (
                f"Generated code has syntax error at line {e.lineno}: {e.msg}\n"
                f"Problematic code near: {e.text.strip() if e.text else 'N/A'}"
            )
            logger.error(error_msg)
            return None, [error_msg]

        # Success - return generated code
        logger.info("Code generation completed successfully")
        return code, []

    def generate_from_file(
        self,
        yaml_path: str
    ) -> Tuple[Optional[str], List[str]]:
        """
        Generate Python code from a YAML file.

        This method loads a YAML file, parses it, and calls generate() to produce code.
        It handles file I/O errors, YAML parsing errors, and delegates validation
        and generation to generate().

        Args:
            yaml_path: Path to YAML strategy specification file
                Can be relative or absolute path

        Returns:
            Tuple of (code, errors):
                - code: Generated Python code string (None if errors)
                - errors: List of error messages including file/parse errors (empty if success)

        Example:
            >>> code, errors = generator.generate_from_file('examples/yaml_strategies/momentum.yaml')
            >>> if not errors:
            ...     with open('generated_strategy.py', 'w') as f:
            ...         f.write(code)
            ...     print("Strategy code saved to generated_strategy.py")
            ... else:
            ...     print(f"Generation failed: {errors}")
        """
        yaml_path = Path(yaml_path)

        # Check if file exists
        if not yaml_path.exists():
            error_msg = f"YAML file not found: {yaml_path}"
            logger.error(error_msg)
            return None, [error_msg]

        logger.info(f"Loading YAML file: {yaml_path}")

        # Try to load and parse YAML file
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_spec = yaml.safe_load(f)

            logger.debug(f"YAML file loaded successfully: {yaml_path.name}")

        except yaml.YAMLError as e:
            error_msg = f"YAML parsing error in {yaml_path.name}: {str(e)}"
            logger.error(error_msg)
            return None, [error_msg]

        except Exception as e:
            error_msg = f"Error reading file {yaml_path.name}: {str(e)}"
            logger.error(error_msg)
            return None, [error_msg]

        # Delegate to generate() for validation and code generation
        return self.generate(yaml_spec)

    def generate_batch(
        self,
        yaml_specs: List[Dict[str, Any]]
    ) -> List[Tuple[Optional[str], List[str]]]:
        """
        Generate Python code from multiple YAML specifications in batch.

        This method processes multiple YAML specs and returns results for each.
        Useful for batch processing or testing multiple strategies at once.

        Args:
            yaml_specs: List of parsed YAML specification dictionaries

        Returns:
            List of (code, errors) tuples, one for each input spec
            Same format as generate() return value

        Example:
            >>> specs = [spec1, spec2, spec3]
            >>> results = generator.generate_batch(specs)
            >>> for i, (code, errors) in enumerate(results):
            ...     if not errors:
            ...         print(f"Spec {i+1}: Generated successfully")
            ...     else:
            ...         print(f"Spec {i+1}: Failed with {len(errors)} errors")
        """
        logger.info(f"Starting batch generation for {len(yaml_specs)} specs")

        results = []
        for i, spec in enumerate(yaml_specs):
            logger.debug(f"Processing spec {i+1}/{len(yaml_specs)}")
            code, errors = self.generate(spec)
            results.append((code, errors))

        success_count = sum(1 for code, errors in results if not errors)
        logger.info(
            f"Batch generation complete: {success_count}/{len(yaml_specs)} successful"
        )

        return results

    def generate_batch_from_files(
        self,
        yaml_paths: List[str]
    ) -> List[Tuple[Optional[str], List[str]]]:
        """
        Generate Python code from multiple YAML files in batch.

        This method processes multiple YAML files and returns results for each.
        Useful for batch processing entire directories of strategy specs.

        Args:
            yaml_paths: List of paths to YAML files

        Returns:
            List of (code, errors) tuples, one for each input file
            Same format as generate_from_file() return value

        Example:
            >>> import glob
            >>> yaml_files = glob.glob('examples/yaml_strategies/*.yaml')
            >>> results = generator.generate_batch_from_files(yaml_files)
            >>> for path, (code, errors) in zip(yaml_files, results):
            ...     if not errors:
            ...         output_path = path.replace('.yaml', '.py')
            ...         with open(output_path, 'w') as f:
            ...             f.write(code)
        """
        logger.info(f"Starting batch file generation for {len(yaml_paths)} files")

        results = []
        for i, path in enumerate(yaml_paths):
            logger.debug(f"Processing file {i+1}/{len(yaml_paths)}: {Path(path).name}")
            code, errors = self.generate_from_file(path)
            results.append((code, errors))

        success_count = sum(1 for code, errors in results if not errors)
        logger.info(
            f"Batch file generation complete: {success_count}/{len(yaml_paths)} successful"
        )

        return results

    def validate_only(
        self,
        yaml_spec: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate YAML spec without generating code.

        Useful for pre-validation before expensive operations or when you only
        need to check if a spec is valid.

        Args:
            yaml_spec: Parsed YAML specification as dictionary

        Returns:
            Tuple of (is_valid, errors):
                - is_valid: True if validation passes
                - errors: List of validation error messages (empty if valid)

        Example:
            >>> is_valid, errors = generator.validate_only(spec)
            >>> if is_valid:
            ...     print("Spec is valid, safe to generate code")
            ... else:
            ...     print(f"Spec has {len(errors)} validation errors")
        """
        # Schema validation
        is_valid, errors = self.validator.validate(yaml_spec)

        if not is_valid:
            return False, errors

        # Semantic validation
        if self.validate_semantics:
            semantic_valid, semantic_errors = self.validator.validate_indicator_references(
                yaml_spec
            )
            if not semantic_valid:
                return False, semantic_errors

        return True, []

    def get_generation_stats(
        self,
        results: List[Tuple[Optional[str], List[str]]]
    ) -> Dict[str, Any]:
        """
        Calculate statistics from batch generation results.

        Args:
            results: List of (code, errors) tuples from batch generation

        Returns:
            Dictionary with statistics:
                - total: Total number of specs processed
                - successful: Number of successful generations
                - failed: Number of failed generations
                - success_rate: Percentage of successful generations
                - error_types: Count of different error types

        Example:
            >>> results = generator.generate_batch(specs)
            >>> stats = generator.get_generation_stats(results)
            >>> print(f"Success rate: {stats['success_rate']:.1f}%")
            >>> print(f"Total: {stats['total']}, Success: {stats['successful']}, Failed: {stats['failed']}")
        """
        total = len(results)
        successful = sum(1 for code, errors in results if not errors)
        failed = total - successful

        # Categorize errors
        error_types = {}
        for code, errors in results:
            if errors:
                for error in errors:
                    # Extract error type from message
                    if "validation" in error.lower():
                        error_type = "validation_error"
                    elif "syntax" in error.lower():
                        error_type = "syntax_error"
                    elif "template" in error.lower():
                        error_type = "template_error"
                    elif "not found" in error.lower():
                        error_type = "file_not_found"
                    else:
                        error_type = "other_error"

                    error_types[error_type] = error_types.get(error_type, 0) + 1

        success_rate = (successful / total * 100) if total > 0 else 0.0

        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': success_rate,
            'error_types': error_types
        }
