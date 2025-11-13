# LLMConfig Quick Start Guide

## Overview

LLMConfig provides centralized configuration management for LLM integration in the FinLab trading system. It handles API provider configuration, parameter validation, and environment variable substitution.

## Quick Setup

### 1. Set Environment Variable

```bash
# For OpenRouter (recommended)
export OPENROUTER_API_KEY="sk-or-your-api-key-here"

# For Google Gemini
export GOOGLE_API_KEY="AIza-your-api-key-here"
# OR
export GEMINI_API_KEY="AIza-your-api-key-here"

# For OpenAI
export OPENAI_API_KEY="sk-your-api-key-here"
```

### 2. Update Configuration (Optional)

Edit `config/learning_system.yaml`:

```yaml
llm:
  provider: openrouter  # or gemini, openai
  model: anthropic/claude-3.5-sonnet
  innovation_rate: 0.20  # 20% of iterations use LLM
  timeout: 60
  max_tokens: 2000
  temperature: 0.7
```

### 3. Use in Code

```python
from src.innovation import LLMConfig

# Load configuration
config = LLMConfig.from_yaml("config/learning_system.yaml")

# Access parameters
print(f"Using {config.provider} with model {config.model}")
print(f"Innovation rate: {config.innovation_rate}")

# Use in iteration loop
if random.random() < config.innovation_rate:
    # Use LLM innovation
    strategy = llm_provider.generate(config)
else:
    # Use Factor Graph mutation
    strategy = factor_graph.mutate()
```

## Configuration Parameters

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `provider` | str | openrouter, gemini, openai | openrouter | LLM API provider |
| `model` | str | - | Provider-specific | Model name to use |
| `innovation_rate` | float | 0.0-1.0 | 0.20 | Percentage of iterations using LLM |
| `timeout` | int | >0 | 60 | API call timeout (seconds) |
| `max_tokens` | int | >0 | 2000 | Maximum response tokens |
| `temperature` | float | 0.0-2.0 | 0.7 | Sampling temperature |

## Provider Configuration

### OpenRouter (Recommended)

```yaml
llm:
  provider: openrouter
  model: anthropic/claude-3.5-sonnet  # or openai/gpt-4o, etc.
```

Environment variable: `OPENROUTER_API_KEY`

**Pros**: Access to multiple models, good pricing, reliable
**Cons**: Requires internet connection

### Google Gemini

```yaml
llm:
  provider: gemini
  model: gemini-2.0-flash-thinking-exp  # or gemini-1.5-pro
```

Environment variable: `GOOGLE_API_KEY` or `GEMINI_API_KEY`

**Pros**: Fast, thinking mode available, good for experimentation
**Cons**: May have rate limits on free tier

### OpenAI

```yaml
llm:
  provider: openai
  model: gpt-4o  # or gpt-4-turbo-preview
```

Environment variable: `OPENAI_API_KEY`

**Pros**: High quality, well-documented API
**Cons**: Higher cost, requires OpenAI account

## Error Handling

```python
from src.innovation import LLMConfig

try:
    config = LLMConfig.from_yaml("config/learning_system.yaml")
except FileNotFoundError:
    print("Config file not found - check path")
except KeyError as e:
    print(f"Missing required config: {e}")
except ValueError as e:
    print(f"Invalid configuration: {e}")
    # Fall back to Factor Graph only
    config = None
```

## Common Issues

### "API key not found"

**Problem**: Environment variable not set

**Solution**:
```bash
# Check if variable is set
echo $OPENROUTER_API_KEY

# Set the variable
export OPENROUTER_API_KEY="your-key-here"
```

### "Invalid provider"

**Problem**: Provider name misspelled or not supported

**Solution**: Use one of: `openrouter`, `gemini`, `openai`

### "innovation_rate must be between 0.0 and 1.0"

**Problem**: Rate is negative or greater than 1.0

**Solution**: Set to a value between 0.0 (disabled) and 1.0 (100% LLM)

### "Configuration file not found"

**Problem**: Path is incorrect or file doesn't exist

**Solution**:
```python
# Use absolute path
config = LLMConfig.from_yaml("/full/path/to/config/learning_system.yaml")

# Or ensure relative path is correct from project root
config = LLMConfig.from_yaml("config/learning_system.yaml")
```

## Security Best Practices

1. **Never commit API keys to git**
   - Use environment variables only
   - Add `.env` to `.gitignore`

2. **Use separate keys for dev/prod**
   ```bash
   # Development
   export OPENROUTER_API_KEY="sk-dev-key"

   # Production
   export OPENROUTER_API_KEY="sk-prod-key"
   ```

3. **Rotate keys regularly**
   - Change API keys every 90 days
   - Revoke old keys after rotation

4. **Monitor API usage**
   - Set up billing alerts
   - Track costs per iteration

## Testing

Run tests to verify configuration:

```bash
# Run all LLMConfig tests
python3 -m pytest tests/innovation/test_llm_config.py -v

# Run specific test category
python3 -m pytest tests/innovation/test_llm_config.py -k "test_valid"

# Check a specific test
python3 -m pytest tests/innovation/test_llm_config.py::TestLLMConfigValidation::test_valid_config_openrouter
```

## Advanced Usage

### Programmatic Configuration

```python
from src.innovation.llm_config import LLMConfig

# Create config directly (not recommended - use YAML)
config = LLMConfig(
    provider='openrouter',
    model='anthropic/claude-3.5-sonnet',
    api_key='sk-test-key',
    innovation_rate=0.20,
    timeout=60,
    max_tokens=2000,
    temperature=0.7
)
```

### Export Configuration

```python
# Get dictionary (API key redacted)
config_dict = config.to_dict()
print(config_dict)
# {'provider': 'openrouter', 'model': 'claude', 'api_key': '***REDACTED***', ...}

# Get string representation (API key redacted)
print(config)
# LLMConfig(provider='openrouter', model='claude', api_key='***REDACTED***', ...)
```

### Load API Key Directly

```python
# Load API key for a specific provider
api_key = LLMConfig._load_api_key('openrouter')
# Returns value of OPENROUTER_API_KEY environment variable
```

## Integration Examples

### In Autonomous Loop

```python
from src.innovation import LLMConfig

class AutonomousLoop:
    def __init__(self):
        # Load config at initialization
        self.llm_config = LLMConfig.from_yaml("config/learning_system.yaml")

    def run_iteration(self, iteration_num):
        # Use LLM for specified percentage of iterations
        if random.random() < self.llm_config.innovation_rate:
            return self._llm_innovation()
        else:
            return self._factor_graph_mutation()
```

### With InnovationEngine

```python
from src.innovation import LLMConfig, InnovationEngine

# Initialize engine with config
config = LLMConfig.from_yaml("config/learning_system.yaml")
engine = InnovationEngine(config)

# Generate strategy
strategy = engine.generate(
    champion_code=champion,
    champion_metrics=metrics,
    directive="modify"
)
```

## FAQ

**Q: Can I disable LLM and use only Factor Graph?**

A: Yes, set `innovation_rate: 0.0` in the config.

**Q: What's the recommended innovation_rate?**

A: Start with 0.20 (20%) to balance innovation and cost.

**Q: Which provider is cheapest?**

A: OpenRouter typically offers the best price/quality ratio.

**Q: Can I use multiple models?**

A: Not currently - select one model per configuration.

**Q: How do I change providers?**

A: Update `provider` and `model` in config, set appropriate environment variable.

**Q: What if my API key expires?**

A: The system will fall back to Factor Graph mutation (Task 6).

---

**See Also**:
- Full implementation: `TASK_4_LLM_CONFIG_IMPLEMENTATION.md`
- Requirements: `.spec-workflow/specs/llm-integration-activation/requirements.md`
- Tests: `tests/innovation/test_llm_config.py`
