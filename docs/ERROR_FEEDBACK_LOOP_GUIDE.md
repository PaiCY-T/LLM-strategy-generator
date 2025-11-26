# Error Feedback Loop for LLM Config Generation

**Task 24.3: Error Feedback Loop Implementation**

This guide explains how to use the error feedback loop mechanism for LLM-generated YAML configuration validation and retry.

## Overview

The error feedback loop enables LLMs to automatically retry invalid YAML configuration generation with actionable error feedback. This significantly improves the success rate of LLM-generated configs by providing clear, structured error messages and retry prompts.

### Key Features

1. **Automatic Retry**: Validates YAML and retries with feedback when validation fails
2. **Clear Error Formatting**: Groups errors by severity (ERROR, WARNING, INFO) with suggestions
3. **Max Retry Limit**: Prevents infinite loops with configurable retry limits
4. **Error History Tracking**: Tracks all validation errors for debugging
5. **Thread-Safe**: Safe for concurrent usage across multiple threads
6. **Integration**: Works seamlessly with SchemaValidator from Layer 3

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Error Feedback Loop                       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐                                            │
│  │  LLM API    │                                            │
│  │  (OpenAI,   │                                            │
│  │   Gemini)   │                                            │
│  └─────┬───────┘                                            │
│        │                                                    │
│        ▼                                                    │
│  ┌──────────────────────────────────────┐                  │
│  │  1. Generate YAML Config             │                  │
│  └──────────────┬───────────────────────┘                  │
│                 │                                           │
│                 ▼                                           │
│  ┌──────────────────────────────────────┐                  │
│  │  2. Parse & Validate                 │                  │
│  │     (SchemaValidator)                │                  │
│  └──────────────┬───────────────────────┘                  │
│                 │                                           │
│        ┌────────┴──────────┐                               │
│        │                   │                               │
│        ▼                   ▼                               │
│   ┌─────────┐       ┌──────────────┐                      │
│   │ Valid?  │       │  Invalid?    │                      │
│   │ Success │       │  Generate    │                      │
│   └─────────┘       │  Retry Prompt│                      │
│                     └──────┬───────┘                      │
│                            │                               │
│                            ▼                               │
│                     ┌──────────────┐                      │
│                     │ Max Retries? │                      │
│                     └──────┬───────┘                      │
│                            │                               │
│                   ┌────────┴──────────┐                   │
│                   │                   │                   │
│                   ▼                   ▼                   │
│              ┌─────────┐       ┌──────────┐              │
│              │  Retry  │       │  Fail    │              │
│              │  (Loop) │       │  Return  │              │
│              └─────────┘       └──────────┘              │
│                                                            │
└──────────────────────────────────────────────────────────────┘
```

## Components

### 1. format_validation_errors()

Converts ValidationError objects to human-readable feedback for LLMs.

**Signature:**
```python
def format_validation_errors(errors: List[ValidationError]) -> str
```

**Features:**
- Groups errors by severity (ERROR, WARNING, INFO)
- Includes field paths, line numbers, and suggestions
- Returns empty string for empty error list
- Clear structure for LLM comprehension

**Example:**
```python
from src.prompts.error_feedback import format_validation_errors
from src.execution.schema_validator import ValidationError, ValidationSeverity

errors = [
    ValidationError(
        severity=ValidationSeverity.ERROR,
        message="Missing required key: 'name'",
        field_path="<root>",
        line_number=1,
        suggestion="Add 'name' to the top level of your YAML"
    ),
    ValidationError(
        severity=ValidationSeverity.ERROR,
        message="Invalid strategy type: 'invalid_type'",
        field_path="type",
        suggestion="Valid types are: factor_graph, llm_generated, hybrid"
    )
]

formatted = format_validation_errors(errors)
print(formatted)
```

**Output:**
```
=== ERRORS (2) ===

1. Missing required key: 'name'
   Field: <root>
   Line: 1
   Suggestion: Add 'name' to the top level of your YAML

2. Invalid strategy type: 'invalid_type'
   Field: type
   Suggestion: Valid types are: factor_graph, llm_generated, hybrid
```

### 2. generate_retry_prompt()

Generates retry prompt for LLM with original YAML and validation errors.

**Signature:**
```python
def generate_retry_prompt(
    original_yaml: str,
    validation_errors: List[ValidationError],
    attempt_number: int
) -> str
```

**Features:**
- Shows original YAML that failed validation
- Includes formatted validation errors
- Shows attempt number for context
- Provides clear instructions for correction
- Requests YAML-only output

**Example:**
```python
from src.prompts.error_feedback import generate_retry_prompt

original_yaml = """
name: Test Strategy
type: invalid_type
required_fields: []
"""

errors = [
    ValidationError(
        severity=ValidationSeverity.ERROR,
        message="Invalid strategy type: 'invalid_type'",
        field_path="type",
        suggestion="Valid types are: factor_graph, llm_generated, hybrid"
    )
]

retry_prompt = generate_retry_prompt(original_yaml, errors, attempt_number=1)
print(retry_prompt)
```

**Output:**
```
## YAML Validation Failed - Retry Required

**Attempt: 1**

Your previous YAML configuration had the following errors:

=== ERRORS (1) ===

1. Invalid strategy type: 'invalid_type'
   Field: type
   Suggestion: Valid types are: factor_graph, llm_generated, hybrid

## Your Original YAML:
```yaml
name: Test Strategy
type: invalid_type
required_fields: []
```

## Instructions:
Please fix the errors above and generate a corrected YAML configuration.
Follow the suggestions provided and ensure all required fields are present.

Return ONLY valid YAML. No explanations or comments.
```

### 3. ErrorFeedbackLoop Class

Orchestrates validation and retry workflow for LLM-generated YAML configs.

**Signature:**
```python
class ErrorFeedbackLoop:
    def __init__(self, max_retries: int = 3):
        ...

    def validate_and_retry(
        self,
        yaml_str: str,
        validator: SchemaValidator,
        llm_generate_func: Callable[[str], str]
    ) -> Tuple[bool, Optional[Dict], List[str]]:
        ...
```

**Features:**
- Automatic validation and retry loop
- Configurable max retry limit (default: 3)
- Error history tracking
- YAML parse error handling
- Thread-safe for concurrent usage

## Usage Examples

### Basic Usage: Single Retry

```python
from src.prompts.error_feedback import ErrorFeedbackLoop
from src.execution.schema_validator import SchemaValidator

# Initialize components
validator = SchemaValidator()
loop = ErrorFeedbackLoop(max_retries=3)

# Define LLM generate function
def generate_yaml(prompt: str) -> str:
    """Call your LLM API to generate YAML"""
    import openai

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a YAML config generator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content

# First attempt: LLM generates invalid YAML
invalid_yaml = """
name: "Momentum Strategy"
type: "momentum"  # Invalid type
required_fields: ["close"]  # Invalid field name
"""

# Validate with automatic retry
success, validated_config, error_history = loop.validate_and_retry(
    invalid_yaml,
    validator,
    generate_yaml
)

if success:
    print(f"✓ Validation successful after {len(error_history)} retries")
    print(f"Config: {validated_config}")
else:
    print(f"✗ Validation failed after {len(error_history)} attempts")
    for i, error in enumerate(error_history, 1):
        print(f"  Attempt {i}: {error}")
```

### Complete Two-Stage Workflow

```python
from src.prompts.error_feedback import ErrorFeedbackLoop
from src.prompts.prompt_formatter import (
    generate_field_selection_prompt,
    generate_config_creation_prompt
)
from src.execution.schema_validator import SchemaValidator
from src.config.data_fields import DataFieldManifest

# Initialize components
manifest = DataFieldManifest()
validator = SchemaValidator(manifest=manifest)
loop = ErrorFeedbackLoop(max_retries=3)

# Stage 1: Field selection
available_fields = manifest.get_fields_by_category('price')
stage1_prompt = generate_field_selection_prompt(available_fields, 'momentum')

# LLM selects fields (mock for example)
selected_fields = ["price:收盤價", "price:成交金額"]

# Stage 2: Config generation with error feedback
schema_example = open('src/config/strategy_schema.yaml').read()
stage2_prompt = generate_config_creation_prompt(
    selected_fields,
    'momentum',
    schema_example
)

# Generate initial YAML (may be invalid)
def llm_generate_with_retry(prompt: str) -> str:
    """Your LLM API call here"""
    # This is where you'd call OpenAI, Gemini, etc.
    import openai
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Get initial YAML from LLM
initial_yaml = llm_generate_with_retry(stage2_prompt)

# Validate with automatic retry on errors
success, validated_config, error_history = loop.validate_and_retry(
    initial_yaml,
    validator,
    llm_generate_with_retry
)

if success:
    print("✓ Config validated successfully!")
    print(f"Strategy name: {validated_config['name']}")
    print(f"Strategy type: {validated_config['type']}")
    print(f"Required fields: {validated_config['required_fields']}")
else:
    print("✗ Config validation failed after max retries")
    print("Error history:")
    for i, error in enumerate(error_history, 1):
        print(f"  {i}. {error}")
```

### Handling Max Retries Exceeded

```python
from src.prompts.error_feedback import ErrorFeedbackLoop
from src.execution.schema_validator import SchemaValidator

validator = SchemaValidator()
loop = ErrorFeedbackLoop(max_retries=2)

# Simulate stubborn LLM that keeps generating invalid YAML
def stubborn_llm(prompt: str) -> str:
    return """
name: Test
type: invalid_type
"""

invalid_yaml = stubborn_llm("")
success, validated_config, error_history = loop.validate_and_retry(
    invalid_yaml,
    validator,
    stubborn_llm
)

if not success:
    print(f"Validation failed after {len(error_history)} attempts")
    print("\nError history:")
    for i, error in enumerate(error_history, 1):
        print(f"  Attempt {i}: {error}")

    # Decide next action
    print("\nOptions:")
    print("1. Increase max_retries and try again")
    print("2. Use different LLM model or prompt")
    print("3. Manual intervention required")
    print("4. Fall back to template-based generation")
```

### Custom Retry Logic

```python
from src.prompts.error_feedback import ErrorFeedbackLoop
from src.execution.schema_validator import SchemaValidator

# Custom retry loop with logging
validator = SchemaValidator()
loop = ErrorFeedbackLoop(max_retries=5)

def llm_with_logging(prompt: str) -> str:
    """LLM with retry logging"""
    import logging

    # Log retry attempt
    if "Attempt:" in prompt:
        logging.info("LLM retry requested with error feedback")

    # Call LLM API
    response = your_llm_api.generate(prompt)

    # Log response
    logging.debug(f"LLM response: {response[:100]}...")

    return response

yaml_str = initial_yaml_from_llm()
success, config, errors = loop.validate_and_retry(
    yaml_str,
    validator,
    llm_with_logging
)
```

### Integration with Async LLMs

```python
import asyncio
from src.prompts.error_feedback import ErrorFeedbackLoop
from src.execution.schema_validator import SchemaValidator

async def async_llm_generate(prompt: str) -> str:
    """Async LLM API call"""
    # Example with async OpenAI client
    import openai

    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

async def validate_with_async_llm():
    """Wrapper for async LLM"""
    validator = SchemaValidator()
    loop = ErrorFeedbackLoop(max_retries=3)

    # Create sync wrapper for async function
    def sync_llm_wrapper(prompt: str) -> str:
        return asyncio.run(async_llm_generate(prompt))

    yaml_str = await async_llm_generate(initial_prompt)
    success, config, errors = loop.validate_and_retry(
        yaml_str,
        validator,
        sync_llm_wrapper
    )

    return success, config, errors

# Run async workflow
success, config, errors = asyncio.run(validate_with_async_llm())
```

## Error Handling Best Practices

### 1. Handle YAML Parse Errors

The ErrorFeedbackLoop automatically handles YAML parse errors:

```python
# Invalid YAML syntax
invalid_yaml = """
name: Test Strategy
type: factor_graph
  invalid_indent: true  # Syntax error
"""

success, config, errors = loop.validate_and_retry(
    invalid_yaml,
    validator,
    llm_generate
)

# Error history will include: "YAML parse error: ..."
```

### 2. Monitor Error History

Track error patterns for debugging:

```python
success, config, error_history = loop.validate_and_retry(
    yaml_str,
    validator,
    llm_generate
)

# Analyze error patterns
if not success:
    print(f"Failed after {len(error_history)} attempts")

    # Check for recurring errors
    if all("invalid_type" in err.lower() for err in error_history):
        print("Recurring error: LLM consistently generates invalid type")
        print("Action: Update prompt to emphasize valid types")

    # Check for different errors each time
    if len(set(error_history)) == len(error_history):
        print("Different errors each attempt - LLM is unstable")
        print("Action: Reduce temperature or use different model")
```

### 3. Graceful Degradation

Implement fallback strategies:

```python
def generate_config_with_fallback(prompt: str, max_retries: int = 3):
    """Try LLM with fallback to template"""
    loop = ErrorFeedbackLoop(max_retries=max_retries)
    validator = SchemaValidator()

    # Try LLM first
    initial_yaml = llm_generate(prompt)
    success, config, errors = loop.validate_and_retry(
        initial_yaml,
        validator,
        llm_generate
    )

    if success:
        return config

    # Fallback to template-based generation
    print(f"LLM failed after {len(errors)} attempts, using template fallback")
    template_config = load_template_config()

    return template_config
```

## Thread Safety

ErrorFeedbackLoop is thread-safe and can be used concurrently:

```python
from concurrent.futures import ThreadPoolExecutor
from src.prompts.error_feedback import ErrorFeedbackLoop
from src.execution.schema_validator import SchemaValidator

def process_yaml(yaml_str: str) -> bool:
    """Process YAML in separate thread"""
    validator = SchemaValidator()
    loop = ErrorFeedbackLoop(max_retries=3)

    success, config, errors = loop.validate_and_retry(
        yaml_str,
        validator,
        llm_generate
    )

    return success

# Process multiple YAMLs concurrently
yaml_configs = [yaml1, yaml2, yaml3]

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(process_yaml, yaml_configs))

print(f"Successful: {sum(results)}/{len(results)}")
```

## Performance Considerations

### Token Usage

Each retry consumes additional LLM tokens:
- Initial prompt: ~500 tokens
- Retry prompt: ~800 tokens (includes errors + original YAML)
- Average retries: 1-2 per config
- Total tokens per config: ~1,500-2,000 tokens

### Optimization Tips

1. **Set appropriate max_retries**: Default 3 is good balance
2. **Use specific error suggestions**: Helps LLM correct faster
3. **Monitor retry patterns**: Identify systematic issues
4. **Cache successful configs**: Avoid regenerating similar configs
5. **Use temperature=0.7**: Lower temperature for more consistent output

## Testing

Run the comprehensive test suite:

```bash
# Run all error feedback tests
python3 -m pytest tests/prompts/test_error_feedback.py -v

# Run specific test class
python3 -m pytest tests/prompts/test_error_feedback.py::TestErrorFeedbackLoop -v

# Run with coverage
python3 -m pytest tests/prompts/test_error_feedback.py --cov=src/prompts/error_feedback
```

## Integration Checklist

- [ ] SchemaValidator initialized with DataFieldManifest
- [ ] LLM generate function defined
- [ ] ErrorFeedbackLoop created with appropriate max_retries
- [ ] Error handling for max retries exceeded
- [ ] Logging configured for retry attempts
- [ ] Fallback strategy implemented
- [ ] Tests written for integration
- [ ] Performance monitoring added

## Troubleshooting

### Issue: LLM keeps generating same invalid YAML

**Solution:** Update retry prompt to be more specific:
```python
# Add more context to retry prompt
def enhanced_retry_prompt(yaml_str, errors, attempt):
    base_prompt = generate_retry_prompt(yaml_str, errors, attempt)

    # Add examples of valid YAML
    enhanced = base_prompt + "\n\n## Example Valid Config:\n" + example_yaml

    return enhanced
```

### Issue: Max retries exceeded frequently

**Solutions:**
1. Increase max_retries: `ErrorFeedbackLoop(max_retries=5)`
2. Use different LLM model (e.g., GPT-4 instead of GPT-3.5)
3. Improve initial prompt with more examples
4. Add schema example to Stage 2 prompt

### Issue: YAML parse errors persist

**Solution:** Add explicit YAML formatting instructions:
```python
# Add to prompt
prompt += """
IMPORTANT: Return valid YAML with proper indentation.
- Use 2 spaces for indentation (not tabs)
- Quote all string values
- Use proper list syntax with dashes
"""
```

## References

- **Task 23.3**: Prompt formatting functions
- **Task 24.1**: Two-stage prompting implementation
- **Task 24.2**: YAML validation implementation
- **Task 24.3**: Error feedback loop (this document)
- **Layer 1**: DataFieldManifest integration
- **Layer 3**: SchemaValidator integration

## Next Steps

After implementing error feedback loop:
1. Integrate with LLM strategy learning system (Task 25)
2. Add metrics tracking for retry success rates
3. Implement adaptive retry strategies based on error patterns
4. Create dashboard for monitoring validation failures
5. Optimize prompts based on error history analysis
