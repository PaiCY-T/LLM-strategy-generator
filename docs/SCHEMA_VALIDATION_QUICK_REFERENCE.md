# Schema Validation Quick Reference Guide

## Quick Start

```python
from src.execution import SchemaValidator

# Create validator
validator = SchemaValidator()

# Validate YAML
errors = validator.validate(yaml_dict)

# Check results
if not errors:
    print("✅ Valid")
else:
    for error in errors:
        print(f"{error.severity}: {error.message}")
```

## Required YAML Structure

```yaml
name: "Strategy Name"                    # Required: string
type: "factor_graph"                     # Required: factor_graph|llm_generated|hybrid
description: "Strategy description"      # Optional: string

required_fields:                         # Required: list
  - "close"                             # String or dict format
  - canonical_name: "price:收盤價"
    alias: "close"
    usage: "entry_exit"

parameters:                              # Required: list
  - name: "period"                      # Required: string
    type: "int"                         # Required: int|float|bool|str|list
    value: 20                           # Required: matches type
    default: 14                         # Optional: matches type
    range: [5, 100]                     # Optional: [min, max] for numeric

logic:                                   # Required: dict
  entry: "close > 100"                  # Required: string (code)
  exit: "close < 90"                    # Required: string (code)
  dependencies: ["close"]               # Optional: list of strings

constraints:                             # Optional: list
  - type: "field_dependency"            # Required: string
    condition: "close > volume"         # Required: string
    severity: "critical"                # Required: critical|high|medium|low
    message: "Error message"            # Required: string

optional_fields:                         # Optional: list
  - "volume"

coverage_percentage: 75                  # Optional: 0-100
```

## Validation Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `validate(yaml_dict)` | Full validation | List[ValidationError] |
| `validate_yaml_structure(yaml_dict)` | Check required keys | List[ValidationError] |
| `validate_field_types(yaml_dict)` | Check data types | List[ValidationError] |
| `validate_required_fields(fields)` | Validate field names | List[ValidationError] |
| `validate_parameters(params)` | Validate parameters | List[ValidationError] |
| `validate_logic(logic)` | Validate logic | List[ValidationError] |
| `validate_constraints(constraints)` | Validate constraints | List[ValidationError] |

## Common Errors

### Missing Required Keys
```python
# Error
yaml_dict = {"name": "Test"}

# Fix
yaml_dict = {
    "name": "Test",
    "type": "factor_graph",
    "required_fields": [],
    "parameters": [],
    "logic": {"entry": "", "exit": ""}
}
```

### Invalid Strategy Type
```python
# Error
"type": "invalid_type"

# Fix
"type": "factor_graph"  # or "llm_generated" or "hybrid"
```

### Wrong Data Type
```python
# Error
"required_fields": "not_a_list"

# Fix
"required_fields": ["close", "volume"]
```

### Invalid Parameter
```python
# Error
{
    "name": "period",
    "type": "invalid_type",
    "value": 20
}

# Fix
{
    "name": "period",
    "type": "int",
    "value": 20,
    "range": [5, 100]
}
```

### Parameter Value Out of Range
```python
# Error
{
    "name": "period",
    "type": "int",
    "value": 200,
    "range": [5, 100]
}

# Fix
{
    "name": "period",
    "type": "int",
    "value": 50,  # Within [5, 100]
    "range": [5, 100]
}
```

### Missing Logic Entry/Exit
```python
# Error
"logic": {"entry": "close > 100"}

# Fix
"logic": {
    "entry": "close > 100",
    "exit": "close < 90"
}
```

### Invalid Constraint Severity
```python
# Error
{
    "type": "field_dependency",
    "condition": "close > 0",
    "severity": "invalid",
    "message": "Test"
}

# Fix
{
    "type": "field_dependency",
    "condition": "close > 0",
    "severity": "critical",  # or "high", "medium", "low"
    "message": "Test"
}
```

## Integration Examples

### With DataFieldManifest
```python
from src.execution import SchemaValidator
from src.config.data_fields import DataFieldManifest

manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')
validator = SchemaValidator(manifest=manifest)

errors = validator.validate(yaml_dict)
# Gets field suggestions: "Did you mean 'close'?"
```

### With FieldValidator
```python
from src.execution import SchemaValidator
from src.validation.field_validator import FieldValidator
from src.config.data_fields import DataFieldManifest

manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')
field_validator = FieldValidator(manifest)
validator = SchemaValidator(field_validator=field_validator)

errors = validator.validate(yaml_dict)
# Validates entry/exit code with line numbers
```

### Full Integration
```python
from src.execution import SchemaValidator
from src.validation.field_validator import FieldValidator
from src.config.data_fields import DataFieldManifest

# Initialize with both integrations
manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')
field_validator = FieldValidator(manifest)
validator = SchemaValidator(
    manifest=manifest,
    field_validator=field_validator
)

# Comprehensive validation
errors = validator.validate(yaml_dict)

# Process errors
for error in errors:
    print(f"{error.severity.value.upper()}: {error.message}")
    if error.field_path:
        print(f"  Field: {error.field_path}")
    if error.line_number:
        print(f"  Line: {error.line_number}")
    if error.suggestion:
        print(f"  💡 {error.suggestion}")
```

## Error Severity Levels

```python
from src.execution import ValidationSeverity

ValidationSeverity.ERROR    # Critical issues that prevent execution
ValidationSeverity.WARNING  # Issues that should be reviewed
ValidationSeverity.INFO     # Informational messages
```

## Error Structure

```python
from src.execution import ValidationError

error = ValidationError(
    severity=ValidationSeverity.ERROR,      # ERROR|WARNING|INFO
    message="Error description",             # Human-readable message
    field_path="parameters[0].name",         # Location in YAML
    line_number=42,                          # Optional: line number
    suggestion="Try using 'correct_name'"    # Optional: suggestion
)

# String formatting
print(error)
# Output:
# ERROR: Error description
#   Field: parameters[0].name
#   Line: 42
#   Suggestion: Try using 'correct_name'
```

## Performance Tips

1. **Validate Early**: Run validation before expensive operations
2. **Cache Validators**: Reuse SchemaValidator instances
3. **Batch Validation**: Validate multiple YAMLs with same validator
4. **Optional Integrations**: Use integrations only when needed

## Testing

```python
import pytest
from src.execution import SchemaValidator

def test_valid_schema():
    validator = SchemaValidator()
    yaml_dict = {
        "name": "Test",
        "type": "factor_graph",
        "required_fields": ["close"],
        "parameters": [],
        "logic": {"entry": "close > 100", "exit": "close < 90"}
    }
    errors = validator.validate(yaml_dict)
    assert len(errors) == 0

def test_invalid_schema():
    validator = SchemaValidator()
    yaml_dict = {"name": "Test"}  # Missing required keys
    errors = validator.validate(yaml_dict)
    assert len(errors) > 0
```

## See Also

- **Full Documentation**: `docs/TASK_20_3_SCHEMA_VALIDATION_COMPLETE.md`
- **Usage Examples**: `examples/schema_validator_usage.py`
- **Test Suite**: `tests/execution/test_schema_validation.py`
- **Implementation**: `src/execution/schema_validator.py`
