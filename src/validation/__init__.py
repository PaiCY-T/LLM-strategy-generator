"""
Validation System for Strategy Templates
========================================

Comprehensive validation framework for strategy template quality assurance.

Components:
    - TemplateValidator: Base validator class with error categorization
    - ParameterValidator: Parameter validation with range and consistency checks
    - DataValidator: Data access validation with dataset existence checking
    - BacktestValidator: Backtest configuration validation with risk management
    - ValidationError: Error dataclass with severity and category
    - ValidationResult: Result container with status and findings
    - Severity: Error severity levels (CRITICAL | MODERATE | LOW)
    - Category: Error categories (parameter | architecture | data | backtest)

Usage:
    from src.validation import (
        ParameterValidator,
        ValidationResult,
        ValidationError,
        Severity,
        Category
    )

    # Create parameter validator
    validator = ParameterValidator()

    # Validate parameters
    validator.validate_parameters(
        parameters={'n_stocks': 30, 'holding_period': 20},
        template_name='TurtleTemplate'
    )

    # Check results
    result = validator.get_result()
    if not result.is_valid():
        for error in result.get_critical_errors():
            print(f"{error.severity}: {error.message}")

Validation Workflow:
    1. Parameter validation (ranges, types, consistency)
    2. Architecture validation (structure, patterns)
    3. Data access validation (dataset usage)
    4. Backtest configuration validation (settings)
    5. Result aggregation with severity assessment
"""

from .template_validator import (
    TemplateValidator,
    ValidationError,
    ValidationResult,
    Severity,
    Category
)
from .parameter_validator import ParameterValidator
from .data_validator import DataValidator
from .backtest_validator import BacktestValidator
from .turtle_validator import TurtleTemplateValidator
from .mastiff_validator import MastiffTemplateValidator
from .strategy_validator import StrategyValidator
from .fix_suggestor import FixSuggestor
from .sensitivity_tester import SensitivityTester, SensitivityResult
from .validation_logger import ValidationLogger, ValidationLog
from .integration import (
    ValidationIntegrator,
    BaselineIntegrator,
    BootstrapIntegrator,
    BonferroniIntegrator
)
from .validation_report import ValidationReportGenerator
from .stationary_bootstrap import (
    stationary_bootstrap,
    stationary_bootstrap_detailed
)
from .dynamic_threshold import DynamicThresholdCalculator
from .validation_result import ValidationResult as FieldValidationResult, FieldError, FieldWarning

__all__ = [
    'TemplateValidator',
    'ParameterValidator',
    'DataValidator',
    'BacktestValidator',
    'TurtleTemplateValidator',
    'MastiffTemplateValidator',
    'StrategyValidator',
    'FixSuggestor',
    'SensitivityTester',
    'SensitivityResult',
    'ValidationLogger',
    'ValidationLog',
    'ValidationError',
    'ValidationResult',
    'Severity',
    'Category',
    # Phase 2 Validation Framework Integration (Tasks 3-8, v1.1)
    'ValidationIntegrator',
    'BaselineIntegrator',
    'BootstrapIntegrator',
    'BonferroniIntegrator',
    'ValidationReportGenerator',
    # v1.1 Stationary Bootstrap (Task 1.1.2)
    'stationary_bootstrap',
    'stationary_bootstrap_detailed',
    # v1.1 Dynamic Threshold (Task 1.1.3)
    'DynamicThresholdCalculator',
    # Layer 2 Field Validator Data Structures (Task 8.3)
    'FieldValidationResult',
    'FieldError',
    'FieldWarning'
]
