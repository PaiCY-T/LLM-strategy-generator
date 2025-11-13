# Structured Innovation API Reference

**Version**: 1.0.0
**Last Updated**: 2025-10-26
**Status**: Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [YAMLSchemaValidator](#yamlschemavalidator)
3. [YAMLToCodeGenerator](#yamltocodegenerator)
4. [StructuredPromptBuilder](#structuredpromptbuilder)
5. [InnovationEngine (YAML Mode)](#innovationengine-yaml-mode)
6. [Error Handling](#error-handling)
7. [Examples](#examples)

---

## Overview

The Structured Innovation API provides programmatic access to YAML-based strategy generation, validation, and code generation. The API consists of four main components:

1. **YAMLSchemaValidator**: Validates YAML specs against JSON Schema
2. **YAMLToCodeGenerator**: Generates Python code from validated YAML
3. **StructuredPromptBuilder**: Builds LLM prompts for YAML generation
4. **InnovationEngine**: Orchestrates LLM-driven YAML strategy generation

### Quick Start

```python
from src.generators.yaml_schema_validator import YAMLSchemaValidator
from src.generators.yaml_to_code_generator import YAMLToCodeGenerator
from src.innovation.innovation_engine import InnovationEngine

# Validate and generate code
validator = YAMLSchemaValidator()
generator = YAMLToCodeGenerator(validator)

code, errors = generator.generate_from_file('strategy.yaml')

# Use in InnovationEngine
engine = InnovationEngine(
    provider_name='gemini',
    generation_mode='yaml'
)

new_code = engine.generate_innovation(
    champion_code="",
    champion_metrics={'sharpe_ratio': 1.5},
    failure_history=[]
)
```

---

## YAMLSchemaValidator

### Class Overview

Validates YAML strategy specifications against JSON Schema Draft-07.

**Module**: `src.generators.yaml_schema_validator`

**Features**:
- Schema validation with draft-07 support
- Clear error messages with field paths
- YAML parsing error handling
- Schema caching for performance
- Semantic validation (cross-field references)

### Constructor

```python
YAMLSchemaValidator(
    schema_path: Optional[Path] = None,
    strict_mode: bool = True
)
```

**Parameters**:
- `schema_path` (Optional[Path]): Path to JSON Schema file. If `None`, uses default `schemas/strategy_schema_v1.json`.
- `strict_mode` (bool): If `True`, require all recommended fields. If `False`, only required fields. Default: `True`.

**Raises**:
- `FileNotFoundError`: If schema file doesn't exist
- `json.JSONDecodeError`: If schema file is invalid JSON

**Example**:
```python
from pathlib import Path
from src.generators.yaml_schema_validator import YAMLSchemaValidator

# Use default schema path
validator = YAMLSchemaValidator()

# Use custom schema path
custom_schema = Path('custom/schemas/strategy_v2.json')
validator = YAMLSchemaValidator(schema_path=custom_schema)

# Permissive mode (only required fields)
permissive_validator = YAMLSchemaValidator(strict_mode=False)
```

### Methods

#### `validate(yaml_spec, return_detailed_errors=True)`

Validate a parsed YAML specification against the schema.

**Signature**:
```python
def validate(
    self,
    yaml_spec: Dict[str, Any],
    return_detailed_errors: bool = True
) -> Tuple[bool, List[str]]
```

**Parameters**:
- `yaml_spec` (Dict[str, Any]): Parsed YAML specification as dictionary
- `return_detailed_errors` (bool): If `True`, return detailed error messages with paths. Default: `True`.

**Returns**:
- `Tuple[bool, List[str]]`:
  - `is_valid` (bool): `True` if validation passes, `False` otherwise
  - `error_messages` (List[str]): List of error messages (empty if valid)

**Example**:
```python
import yaml

# Load YAML file
with open('strategy.yaml') as f:
    spec = yaml.safe_load(f)

# Validate
validator = YAMLSchemaValidator()
is_valid, errors = validator.validate(spec)

if is_valid:
    print("✅ YAML is valid")
else:
    print("❌ Validation errors:")
    for error in errors:
        print(f"  - {error}")
```

**Output**:
```
❌ Validation errors:
  - metadata: Missing required field 'rebalancing_frequency'
  - entry_conditions.ranking_rules.0.field: Field 'momentum' not found in indicators
```

#### `load_and_validate(yaml_path, return_detailed_errors=True)`

Load YAML file and validate against schema.

**Signature**:
```python
def load_and_validate(
    self,
    yaml_path: str,
    return_detailed_errors: bool = True
) -> Tuple[bool, List[str]]
```

**Parameters**:
- `yaml_path` (str): Path to YAML file
- `return_detailed_errors` (bool): If `True`, return detailed error messages. Default: `True`.

**Returns**:
- `Tuple[bool, List[str]]`: Same as `validate()`

**Example**:
```python
validator = YAMLSchemaValidator()
is_valid, errors = validator.load_and_validate('examples/yaml_strategies/momentum.yaml')

if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

#### `get_validation_errors(spec)`

Get only validation error messages (without success/failure bool).

**Signature**:
```python
def get_validation_errors(
    self,
    spec: Dict[str, Any]
) -> List[str]
```

**Parameters**:
- `spec` (Dict[str, Any]): Parsed YAML specification

**Returns**:
- `List[str]`: List of error messages (empty if valid)

**Example**:
```python
validator = YAMLSchemaValidator()
errors = validator.get_validation_errors(spec)

for error in errors:
    print(f"Validation error: {error}")
```

#### `validate_indicator_references(spec)`

Validate that all indicator references in conditions exist in indicators section.

This is semantic validation beyond JSON Schema (cross-field validation).

**Signature**:
```python
def validate_indicator_references(
    self,
    spec: Dict[str, Any]
) -> Tuple[bool, List[str]]
```

**Parameters**:
- `spec` (Dict[str, Any]): Parsed YAML specification

**Returns**:
- `Tuple[bool, List[str]]`:
  - `is_valid` (bool): `True` if all references are valid
  - `error_messages` (List[str]): List of reference errors (empty if valid)

**Example**:
```python
validator = YAMLSchemaValidator()

# First validate schema
is_valid, schema_errors = validator.validate(spec)

if is_valid:
    # Then validate indicator references
    refs_valid, ref_errors = validator.validate_indicator_references(spec)

    if not refs_valid:
        print("Reference errors:")
        for error in ref_errors:
            print(f"  - {error}")
```

**Output**:
```
Reference errors:
  - entry_conditions.ranking_rules: Field 'momentum_20' not found in indicators
  - position_sizing.weighting_field: Field 'quality_score' not found in indicators
```

### Properties

#### `schema`

Get the loaded JSON Schema.

**Returns**:
- `Dict`: JSON Schema dictionary

**Example**:
```python
validator = YAMLSchemaValidator()
schema = validator.schema

print(f"Schema version: {schema.get('version')}")
print(f"Required fields: {schema.get('required')}")
```

#### `schema_version`

Get the schema version.

**Returns**:
- `str`: Schema version string

**Example**:
```python
validator = YAMLSchemaValidator()
print(f"Using schema version: {validator.schema_version}")
# Output: Using schema version: 1.0.0
```

---

## YAMLToCodeGenerator

### Class Overview

Generate syntactically correct Python strategy code from YAML specifications.

**Module**: `src.generators.yaml_to_code_generator`

**Features**:
- Integrated validation (uses YAMLSchemaValidator)
- Template-based generation (Jinja2)
- AST syntax validation (guarantees valid Python)
- Clear error reporting
- Batch processing support

### Constructor

```python
YAMLToCodeGenerator(
    schema_validator: Optional[YAMLSchemaValidator] = None,
    validate_semantics: bool = True
)
```

**Parameters**:
- `schema_validator` (Optional[YAMLSchemaValidator]): YAMLSchemaValidator instance. If `None`, creates default.
- `validate_semantics` (bool): If `True`, validate indicator references (cross-field validation). Default: `True`.

**Example**:
```python
from src.generators.yaml_schema_validator import YAMLSchemaValidator
from src.generators.yaml_to_code_generator import YAMLToCodeGenerator

# Use default validator
generator = YAMLToCodeGenerator()

# Use custom validator
validator = YAMLSchemaValidator()
generator = YAMLToCodeGenerator(validator)

# Skip semantic validation for performance
fast_generator = YAMLToCodeGenerator(validate_semantics=False)
```

### Methods

#### `generate(yaml_spec)`

Generate Python code from a validated YAML specification.

**Signature**:
```python
def generate(
    self,
    yaml_spec: Dict[str, Any]
) -> Tuple[Optional[str], List[str]]
```

**Parameters**:
- `yaml_spec` (Dict[str, Any]): Parsed YAML specification as dictionary

**Returns**:
- `Tuple[Optional[str], List[str]]`:
  - `code` (Optional[str]): Generated Python code string, or `None` if errors
  - `errors` (List[str]): List of validation/generation error messages (empty if success)

**Example**:
```python
import yaml

with open('strategy.yaml') as f:
    spec = yaml.safe_load(f)

generator = YAMLToCodeGenerator()
code, errors = generator.generate(spec)

if code:
    print("✅ Generated code successfully!")
    print(code[:500])  # Print first 500 chars

    # Save to file
    with open('generated_strategy.py', 'w') as f:
        f.write(code)
else:
    print("❌ Generation failed:")
    for error in errors:
        print(f"  - {error}")
```

**Pipeline Steps**:
1. Validate YAML against schema
2. Validate indicator references (if `validate_semantics=True`)
3. Render Jinja2 template with spec data
4. Validate generated code with AST parser
5. Return code or errors

#### `generate_from_file(yaml_path)`

Generate Python code directly from a YAML file.

**Signature**:
```python
def generate_from_file(
    self,
    yaml_path: str
) -> Tuple[Optional[str], List[str]]
```

**Parameters**:
- `yaml_path` (str): Path to YAML strategy specification file

**Returns**:
- `Tuple[Optional[str], List[str]]`: Same as `generate()`

**Example**:
```python
generator = YAMLToCodeGenerator()
code, errors = generator.generate_from_file('examples/yaml_strategies/momentum_example.yaml')

if not errors:
    # Execute the generated code
    exec(code)

    # Or backtest it
    from src.backtest.metrics import calculate_metrics
    metrics = calculate_metrics(code, data)
    print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
```

#### `generate_batch(yaml_specs)`

Generate Python code from multiple YAML specifications in batch.

**Signature**:
```python
def generate_batch(
    self,
    yaml_specs: List[Dict[str, Any]]
) -> List[Tuple[Optional[str], List[str]]]
```

**Parameters**:
- `yaml_specs` (List[Dict[str, Any]]): List of parsed YAML specification dictionaries

**Returns**:
- `List[Tuple[Optional[str], List[str]]]`: List of (code, errors) tuples, one for each input spec

**Example**:
```python
import yaml

# Load multiple specs
specs = []
for path in ['spec1.yaml', 'spec2.yaml', 'spec3.yaml']:
    with open(path) as f:
        specs.append(yaml.safe_load(f))

# Generate batch
generator = YAMLToCodeGenerator()
results = generator.generate_batch(specs)

# Process results
for i, (code, errors) in enumerate(results):
    if code:
        print(f"✅ Spec {i+1}: Generated successfully ({len(code)} chars)")
    else:
        print(f"❌ Spec {i+1}: Failed with {len(errors)} errors")
```

#### `generate_batch_from_files(yaml_paths)`

Generate Python code from multiple YAML files in batch.

**Signature**:
```python
def generate_batch_from_files(
    self,
    yaml_paths: List[str]
) -> List[Tuple[Optional[str], List[str]]]
```

**Parameters**:
- `yaml_paths` (List[str]): List of paths to YAML files

**Returns**:
- `List[Tuple[Optional[str], List[str]]]`: List of (code, errors) tuples

**Example**:
```python
import glob

# Get all YAML files in directory
yaml_files = glob.glob('examples/yaml_strategies/*.yaml')

# Generate code for all
generator = YAMLToCodeGenerator()
results = generator.generate_batch_from_files(yaml_files)

# Save generated code
for path, (code, errors) in zip(yaml_files, results):
    if code:
        output_path = path.replace('.yaml', '.py')
        with open(output_path, 'w') as f:
            f.write(code)
        print(f"✅ Generated: {output_path}")
    else:
        print(f"❌ Failed: {path}")
        for error in errors:
            print(f"    - {error}")
```

#### `validate_only(yaml_spec)`

Validate YAML spec without generating code.

**Signature**:
```python
def validate_only(
    self,
    yaml_spec: Dict[str, Any]
) -> Tuple[bool, List[str]]
```

**Parameters**:
- `yaml_spec` (Dict[str, Any]): Parsed YAML specification

**Returns**:
- `Tuple[bool, List[str]]`:
  - `is_valid` (bool): `True` if validation passes
  - `errors` (List[str]): List of validation error messages (empty if valid)

**Example**:
```python
import yaml

with open('strategy.yaml') as f:
    spec = yaml.safe_load(f)

generator = YAMLToCodeGenerator()
is_valid, errors = generator.validate_only(spec)

if is_valid:
    print("✅ Spec is valid, safe to generate code")
    # Proceed with expensive backtest preparation
else:
    print(f"❌ Spec has {len(errors)} validation errors")
    for error in errors:
        print(f"  - {error}")
```

#### `get_generation_stats(results)`

Calculate statistics from batch generation results.

**Signature**:
```python
def get_generation_stats(
    self,
    results: List[Tuple[Optional[str], List[str]]]
) -> Dict[str, Any]
```

**Parameters**:
- `results` (List[Tuple[Optional[str], List[str]]]): List of (code, errors) tuples from batch generation

**Returns**:
- `Dict[str, Any]`: Statistics dictionary with keys:
  - `total` (int): Total number of specs processed
  - `successful` (int): Number of successful generations
  - `failed` (int): Number of failed generations
  - `success_rate` (float): Percentage of successful generations
  - `error_types` (Dict[str, int]): Count of different error types

**Example**:
```python
import glob

yaml_files = glob.glob('test_specs/*.yaml')
generator = YAMLToCodeGenerator()
results = generator.generate_batch_from_files(yaml_files)

# Get statistics
stats = generator.get_generation_stats(results)

print(f"Total specs: {stats['total']}")
print(f"Successful: {stats['successful']}")
print(f"Failed: {stats['failed']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
print(f"\nError breakdown:")
for error_type, count in stats['error_types'].items():
    print(f"  - {error_type}: {count}")
```

**Output**:
```
Total specs: 50
Successful: 47
Failed: 3
Success rate: 94.0%

Error breakdown:
  - validation_error: 2
  - syntax_error: 1
```

---

## StructuredPromptBuilder

### Class Overview

Build prompts specifically for YAML strategy generation by LLMs.

**Module**: `src.innovation.structured_prompt_builder`

**Features**:
- Include JSON Schema to constrain LLM output
- Provide strategy examples (momentum, mean_reversion, factor_combination)
- Include champion feedback and failure patterns
- Token budget control (<2000 tokens)
- Compact and full prompt modes

### Constructor

```python
StructuredPromptBuilder(
    schema_path: str = "schemas/strategy_schema_v1.json"
)
```

**Parameters**:
- `schema_path` (str): Path to JSON Schema file (relative to project root). Default: `"schemas/strategy_schema_v1.json"`.

**Raises**:
- `FileNotFoundError`: If schema file or example files not found

**Example**:
```python
from src.innovation.structured_prompt_builder import StructuredPromptBuilder

# Use default schema
builder = StructuredPromptBuilder()

# Use custom schema
builder = StructuredPromptBuilder(
    schema_path="custom/schemas/strategy_v2.json"
)
```

### Methods

#### `build_yaml_generation_prompt(champion_metrics, failure_patterns, target_strategy_type)`

Build prompt for LLM to generate YAML strategy.

**Signature**:
```python
def build_yaml_generation_prompt(
    self,
    champion_metrics: Optional[Dict] = None,
    failure_patterns: Optional[List[str]] = None,
    target_strategy_type: str = "momentum"
) -> str
```

**Parameters**:
- `champion_metrics` (Optional[Dict]): Current champion metrics (`sharpe_ratio`, `annual_return`, `max_drawdown`, etc.). Default: `{'sharpe_ratio': 1.5, 'annual_return': 0.15, 'max_drawdown': -0.20}`.
- `failure_patterns` (Optional[List[str]]): List of failure patterns to avoid (max 5 used). Default: Sample patterns.
- `target_strategy_type` (str): Type of strategy to generate (`"momentum"`, `"mean_reversion"`, or `"factor_combination"`). Default: `"momentum"`.

**Returns**:
- `str`: Complete prompt string for LLM

**Example**:
```python
builder = StructuredPromptBuilder()

# Custom champion metrics
champion = {
    'sharpe_ratio': 2.48,
    'annual_return': 0.25,
    'max_drawdown': -0.12
}

# Recent failures
failures = [
    "Overtrading with >200 trades/year caused high slippage",
    "Large drawdowns when ignoring liquidity filters",
    "RSI threshold of 80 too aggressive (rarely triggered)"
]

# Build prompt
prompt = builder.build_yaml_generation_prompt(
    champion_metrics=champion,
    failure_patterns=failures,
    target_strategy_type="factor_combination"
)

# Send to LLM
from src.innovation.llm_providers import create_provider
provider = create_provider('gemini')
response = provider.generate(prompt, max_tokens=2000)

print(response.text)  # YAML strategy
```

**Prompt Structure**:
1. Introduction: Target strategy type, champion metrics to beat
2. Failure Patterns: Recent failures to avoid
3. Schema Section: Critical schema fields and validation rules
4. Examples Section: 1-2 complete YAML examples
5. Instructions: Clear guidance on YAML format and constraints

#### `build_compact_prompt(champion_metrics, failure_patterns, target_strategy_type)`

Build compact prompt under 2000 tokens.

Uses abbreviated schema and single example for token efficiency.

**Signature**:
```python
def build_compact_prompt(
    self,
    champion_metrics: Optional[Dict] = None,
    failure_patterns: Optional[List[str]] = None,
    target_strategy_type: str = "momentum"
) -> str
```

**Parameters**: Same as `build_yaml_generation_prompt()`

**Returns**:
- `str`: Compact prompt string (<2000 tokens)

**Example**:
```python
builder = StructuredPromptBuilder()

# Build compact prompt
compact = builder.build_compact_prompt(
    champion_metrics={'sharpe_ratio': 1.8},
    failure_patterns=["Overtrading", "Large drawdowns"],
    target_strategy_type="momentum"
)

print(f"Token count: ~{builder.count_tokens(compact)}")
# Output: Token count: ~1800
```

#### `get_example(strategy_type)`

Get a specific example YAML.

**Signature**:
```python
def get_example(
    self,
    strategy_type: str
) -> str
```

**Parameters**:
- `strategy_type` (str): Type of strategy example to retrieve (`"momentum"`, `"mean_reversion"`, or `"factor_combination"`)

**Returns**:
- `str`: YAML example content

**Example**:
```python
builder = StructuredPromptBuilder()

# Get momentum example
momentum_yaml = builder.get_example("momentum")
print(momentum_yaml)

# Get mean reversion example
mean_rev_yaml = builder.get_example("mean_reversion")
print(mean_rev_yaml)
```

#### `count_tokens(text)`

Estimate token count (rough approximation: 1 token ≈ 4 chars).

**Signature**:
```python
def count_tokens(
    self,
    text: str
) -> int
```

**Parameters**:
- `text` (str): Text to count tokens for

**Returns**:
- `int`: Approximate token count

**Example**:
```python
builder = StructuredPromptBuilder()

prompt = builder.build_yaml_generation_prompt()
token_count = builder.count_tokens(prompt)

print(f"Prompt token count: ~{token_count}")
# Output: Prompt token count: ~3500

# Check if under budget
if token_count > 2000:
    # Use compact version
    compact = builder.build_compact_prompt()
    print(f"Compact token count: ~{builder.count_tokens(compact)}")
```

---

## InnovationEngine (YAML Mode)

### Class Overview

LLM-driven innovation engine with YAML generation mode.

**Module**: `src.innovation.innovation_engine`

**YAML Mode Features**:
- LLM generates YAML specs (not full Python code)
- Automatic YAML validation
- Automatic code generation from validated YAML
- Retry logic with error feedback
- >90% success rate (vs ~60% for full code mode)
- Statistics tracking

### Constructor

```python
InnovationEngine(
    provider_name: str = 'gemini',
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    max_retries: int = 3,
    timeout: int = 60,
    max_tokens: int = 2000,
    temperature: float = 0.7,
    failure_patterns_path: str = "artifacts/data/failure_patterns.json",
    generation_mode: str = 'full_code'
)
```

**Parameters**:
- `provider_name` (str): LLM provider (`'openrouter'`, `'gemini'`, or `'openai'`). Default: `'gemini'`.
- `model` (Optional[str]): Model name (uses provider default if None)
- `api_key` (Optional[str]): API key (reads from env if None)
- `max_retries` (int): Maximum retry attempts on failures. Default: `3`.
- `timeout` (int): Request timeout in seconds. Default: `60`.
- `max_tokens` (int): Maximum tokens in LLM response. Default: `2000`.
- `temperature` (float): Sampling temperature 0.0-1.0. Default: `0.7`.
- `failure_patterns_path` (str): Path to failure patterns JSON. Default: `"artifacts/data/failure_patterns.json"`.
- `generation_mode` (str): Generation mode (`'full_code'` or `'yaml'`). Default: `'full_code'`.

**Example**:
```python
from src.innovation.innovation_engine import InnovationEngine

# YAML mode with Gemini
engine = InnovationEngine(
    provider_name='gemini',
    generation_mode='yaml',
    max_retries=3,
    temperature=0.7
)

# YAML mode with OpenAI
engine_openai = InnovationEngine(
    provider_name='openai',
    model='gpt-4',
    generation_mode='yaml',
    max_retries=5
)

# Full code mode (legacy)
engine_code = InnovationEngine(
    provider_name='gemini',
    generation_mode='full_code'
)
```

### Methods

#### `generate_innovation(champion_code, champion_metrics, failure_history, target_metric)`

Generate improved strategy code using LLM with feedback loop.

In YAML mode:
1. Build YAML generation prompt with schema and examples
2. Call LLM to generate YAML spec
3. Extract YAML from response
4. Validate YAML against schema
5. Generate Python code from validated YAML
6. Return code or retry (up to `max_retries`)

**Signature**:
```python
def generate_innovation(
    self,
    champion_code: str,
    champion_metrics: Dict[str, float],
    failure_history: Optional[List[Dict[str, Any]]] = None,
    target_metric: str = "sharpe_ratio"
) -> Optional[str]
```

**Parameters**:
- `champion_code` (str): Current champion strategy code (not used in YAML mode, but kept for API compatibility)
- `champion_metrics` (Dict[str, float]): Champion performance metrics (`sharpe_ratio`, `max_drawdown`, `win_rate`, etc.)
- `failure_history` (Optional[List[Dict[str, Any]]]): Optional list of recent failures (last 3). Default: `None`.
- `target_metric` (str): Which metric to optimize. Default: `"sharpe_ratio"`.

**Returns**:
- `Optional[str]`: Generated strategy code as string, or `None` if all attempts failed

**Example**:
```python
from src.innovation.innovation_engine import InnovationEngine

# Initialize YAML mode
engine = InnovationEngine(
    provider_name='gemini',
    generation_mode='yaml',
    max_retries=3
)

# Champion metrics
champion_metrics = {
    'sharpe_ratio': 1.85,
    'annual_return': 0.18,
    'max_drawdown': -0.15,
    'win_rate': 0.58
}

# Recent failures
failure_history = [
    {
        'reason': 'Overtrading',
        'description': '>150 trades/year caused high transaction costs'
    },
    {
        'reason': 'Large drawdown',
        'description': 'Max drawdown -25% exceeded risk limits'
    }
]

# Generate new strategy
code = engine.generate_innovation(
    champion_code="",  # Not used in YAML mode
    champion_metrics=champion_metrics,
    failure_history=failure_history,
    target_metric="sharpe_ratio"
)

if code:
    print("✅ LLM generated valid strategy!")
    print(code[:300])

    # Backtest the generated code
    from src.backtest.metrics import calculate_metrics
    metrics = calculate_metrics(code, data)
    print(f"\nNew strategy metrics:")
    print(f"  Sharpe: {metrics['sharpe_ratio']:.2f}")
    print(f"  Return: {metrics['annual_return']:.1%}")
else:
    print("⚠️ All LLM attempts failed, falling back to mutation")
    # Fallback to factor graph mutation
```

**YAML Mode Pipeline**:
1. **Prompt Building**: Include schema, examples, champion metrics, failure patterns
2. **LLM Call**: Generate YAML spec (max_tokens=2000)
3. **YAML Extraction**: Regex extraction from LLM response
4. **Schema Validation**: Validate against JSON Schema
5. **Semantic Validation**: Check indicator references
6. **Code Generation**: Jinja2 template rendering
7. **AST Validation**: Ensure syntactically correct Python
8. **Retry on Failure**: Up to `max_retries` attempts with error feedback

### Statistics Properties

**YAML Mode Statistics**:
```python
engine = InnovationEngine(generation_mode='yaml')

# After generating strategies...
print(f"Total attempts: {engine.total_attempts}")
print(f"Successful: {engine.successful_generations}")
print(f"Failed: {engine.failed_generations}")
print(f"Success rate: {engine.successful_generations / engine.total_attempts:.1%}")

# YAML-specific stats
print(f"YAML successes: {engine.yaml_successes}")
print(f"YAML failures: {engine.yaml_failures}")
print(f"YAML validation failures: {engine.yaml_validation_failures}")

# Cost tracking
print(f"Total cost: ${engine.total_cost_usd:.2f}")
print(f"Total tokens: {engine.total_tokens}")
```

### Generation Mode Comparison

**YAML Mode**:
```python
engine = InnovationEngine(generation_mode='yaml')
# - LLM generates YAML spec
# - Schema-validated before code generation
# - >90% success rate
# - Eliminates API hallucinations
```

**Full Code Mode** (Legacy):
```python
engine = InnovationEngine(generation_mode='full_code')
# - LLM generates complete Python code
# - Direct AST validation
# - ~60% success rate
# - More flexible but error-prone
```

**When to Use Each**:
- **YAML Mode** (Recommended): Default for most strategies, higher success rate
- **Full Code Mode**: For highly custom strategies requiring complex logic not expressible in YAML

---

## Error Handling

### Validation Errors

**Schema Validation Errors**:
```python
validator = YAMLSchemaValidator()
is_valid, errors = validator.validate(spec)

if not is_valid:
    for error in errors:
        # Error format: "field_path: Error message"
        # Examples:
        # - "metadata: Missing required field 'rebalancing_frequency'"
        # - "indicators.technical_indicators.0.period: Must be between 1 and 250"
        # - "entry_conditions.threshold_rules.0.condition: Invalid syntax"
        print(f"Validation error: {error}")
```

**Semantic Validation Errors**:
```python
validator = YAMLSchemaValidator()
refs_valid, ref_errors = validator.validate_indicator_references(spec)

if not refs_valid:
    for error in ref_errors:
        # Error format: "section.field: Field 'name' not found in indicators"
        # Example: "entry_conditions.ranking_rules: Field 'momentum_20' not found in indicators"
        print(f"Reference error: {error}")
```

### Code Generation Errors

**Template Rendering Errors**:
```python
generator = YAMLToCodeGenerator()
code, errors = generator.generate(spec)

if not code:
    for error in errors:
        if "Template rendering failed" in error:
            # Jinja2 template error
            print(f"Template error: {error}")
```

**AST Syntax Errors**:
```python
generator = YAMLToCodeGenerator()
code, errors = generator.generate(spec)

if not code:
    for error in errors:
        if "syntax error" in error:
            # Generated code has invalid Python syntax
            print(f"Syntax error: {error}")
```

### LLM Generation Errors

**YAML Extraction Failures**:
```python
engine = InnovationEngine(generation_mode='yaml')
code = engine.generate_innovation(
    champion_code="",
    champion_metrics=metrics,
    failure_history=[]
)

if code is None:
    # Check statistics
    if engine.yaml_validation_failures > 0:
        print("LLM generated invalid YAML")
    if engine.api_failures > 0:
        print("API call failures")
```

**Retry Logic**:
```python
# InnovationEngine automatically retries on failures
engine = InnovationEngine(
    generation_mode='yaml',
    max_retries=3  # Up to 3 retry attempts
)

# Retries occur on:
# - YAML extraction failure
# - Schema validation failure
# - Semantic validation failure
# - Code generation failure
```

---

## Examples

### Example 1: Basic Validation and Generation

```python
from src.generators.yaml_schema_validator import YAMLSchemaValidator
from src.generators.yaml_to_code_generator import YAMLToCodeGenerator
import yaml

# Load YAML spec
with open('examples/yaml_strategies/momentum_example.yaml') as f:
    spec = yaml.safe_load(f)

# Validate
validator = YAMLSchemaValidator()
is_valid, errors = validator.validate(spec)

if is_valid:
    print("✅ YAML is valid")

    # Generate code
    generator = YAMLToCodeGenerator(validator)
    code, gen_errors = generator.generate(spec)

    if code:
        print("✅ Code generated successfully")

        # Save to file
        with open('generated_strategy.py', 'w') as f:
            f.write(code)

        print(f"Code saved to generated_strategy.py ({len(code)} chars)")
    else:
        print("❌ Code generation failed:")
        for error in gen_errors:
            print(f"  - {error}")
else:
    print("❌ YAML validation failed:")
    for error in errors:
        print(f"  - {error}")
```

### Example 2: Batch Processing

```python
from src.generators.yaml_to_code_generator import YAMLToCodeGenerator
import glob

# Get all YAML files
yaml_files = glob.glob('examples/yaml_strategies/*.yaml')

# Generate code for all
generator = YAMLToCodeGenerator()
results = generator.generate_batch_from_files(yaml_files)

# Get statistics
stats = generator.get_generation_stats(results)

print(f"Processed {stats['total']} files:")
print(f"  ✅ Successful: {stats['successful']}")
print(f"  ❌ Failed: {stats['failed']}")
print(f"  Success rate: {stats['success_rate']:.1f}%")

# Save successful generations
for path, (code, errors) in zip(yaml_files, results):
    if code:
        output_path = path.replace('.yaml', '.py')
        with open(output_path, 'w') as f:
            f.write(code)
        print(f"Saved: {output_path}")
```

### Example 3: LLM-Driven Generation

```python
from src.innovation.innovation_engine import InnovationEngine

# Initialize YAML mode
engine = InnovationEngine(
    provider_name='gemini',
    generation_mode='yaml',
    max_retries=3,
    temperature=0.7
)

# Champion to beat
champion_metrics = {
    'sharpe_ratio': 2.1,
    'annual_return': 0.22,
    'max_drawdown': -0.14
}

# Recent failures to avoid
failures = [
    "RSI threshold 80 too aggressive (rarely triggered)",
    "Insufficient liquidity filter caused slippage",
    "Sector concentration >40% violated risk limits"
]

# Generate new strategy
code = engine.generate_innovation(
    champion_code="",
    champion_metrics=champion_metrics,
    failure_history=failures,
    target_metric="sharpe_ratio"
)

if code:
    print("✅ LLM generated valid strategy!")

    # Backtest
    from src.backtest.metrics import calculate_metrics
    metrics = calculate_metrics(code, data)

    print(f"\nNew strategy metrics:")
    print(f"  Sharpe: {metrics['sharpe_ratio']:.2f}")
    print(f"  Return: {metrics['annual_return']:.1%}")
    print(f"  Max DD: {metrics['max_drawdown']:.1%}")

    # Check if improvement
    if metrics['sharpe_ratio'] > champion_metrics['sharpe_ratio']:
        print("\n🎉 New champion!")
    else:
        print("\nNot better than champion")
else:
    print("⚠️ All attempts failed, falling back to mutation")

# Print statistics
print(f"\nGeneration statistics:")
print(f"  Total attempts: {engine.total_attempts}")
print(f"  Successes: {engine.successful_generations}")
print(f"  Failures: {engine.failed_generations}")
print(f"  Success rate: {engine.successful_generations / engine.total_attempts:.1%}")
print(f"  Total cost: ${engine.total_cost_usd:.4f}")
```

### Example 4: Custom Validation

```python
from src.generators.yaml_schema_validator import YAMLSchemaValidator
import yaml

# Load spec
with open('strategy.yaml') as f:
    spec = yaml.safe_load(f)

# Create validator
validator = YAMLSchemaValidator()

# Step 1: Schema validation
is_valid, schema_errors = validator.validate(spec)

if not is_valid:
    print("Schema validation failed:")
    for error in schema_errors:
        print(f"  - {error}")
    exit(1)

# Step 2: Semantic validation (indicator references)
refs_valid, ref_errors = validator.validate_indicator_references(spec)

if not refs_valid:
    print("Indicator reference validation failed:")
    for error in ref_errors:
        print(f"  - {error}")
    exit(1)

# Step 3: Custom business logic validation
def validate_business_logic(spec):
    """Custom validation rules."""
    errors = []

    # Rule: Momentum strategies should use RSI
    if spec['metadata']['strategy_type'] == 'momentum':
        has_rsi = any(
            ind.get('type') == 'RSI'
            for ind in spec.get('indicators', {}).get('technical_indicators', [])
        )
        if not has_rsi:
            errors.append("Momentum strategies should include RSI indicator")

    # Rule: Max positions should be reasonable
    max_pos = spec.get('position_sizing', {}).get('max_positions', 20)
    if max_pos > 50:
        errors.append(f"Max positions ({max_pos}) too high (>50)")

    return len(errors) == 0, errors

logic_valid, logic_errors = validate_business_logic(spec)

if not logic_valid:
    print("Business logic validation failed:")
    for error in logic_errors:
        print(f"  - {error}")
    exit(1)

print("✅ All validation passed!")
```

### Example 5: Prompt Customization

```python
from src.innovation.structured_prompt_builder import StructuredPromptBuilder

# Initialize prompt builder
builder = StructuredPromptBuilder()

# Customize for specific scenario
champion_metrics = {
    'sharpe_ratio': 2.5,
    'annual_return': 0.28,
    'max_drawdown': -0.11,
    'win_rate': 0.62
}

failure_patterns = [
    "Short-term momentum (<10 days) too noisy",
    "RSI overbought threshold 70 too conservative",
    "Equal weight underperforms factor weighted for quality strategies"
]

# Build prompt for factor combination
prompt = builder.build_yaml_generation_prompt(
    champion_metrics=champion_metrics,
    failure_patterns=failure_patterns,
    target_strategy_type="factor_combination"
)

# Check token count
token_count = builder.count_tokens(prompt)
print(f"Prompt token count: ~{token_count}")

if token_count > 2000:
    # Use compact version
    prompt = builder.build_compact_prompt(
        champion_metrics=champion_metrics,
        failure_patterns=failure_patterns[:2],  # Limit failures
        target_strategy_type="factor_combination"
    )
    print(f"Compact token count: ~{builder.count_tokens(prompt)}")

# Send to LLM
from src.innovation.llm_providers import create_provider

provider = create_provider('gemini')
response = provider.generate(prompt, max_tokens=2000, temperature=0.7)

print("LLM Response:")
print(response.text[:500])
```

---

## Version History

**v1.0.0** (2025-10-26):
- Initial API release
- YAMLSchemaValidator with draft-07 support
- YAMLToCodeGenerator with Jinja2 templates
- StructuredPromptBuilder for LLM prompts
- InnovationEngine YAML mode integration
- Comprehensive error handling
- Batch processing support

---

**For user guide, see**: [STRUCTURED_INNOVATION.md](STRUCTURED_INNOVATION.md)

**For YAML schema reference, see**: [YAML_STRATEGY_GUIDE.md](YAML_STRATEGY_GUIDE.md)

**Happy Coding! 🚀**
