# LLM Integration Guide

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Configuration](#configuration)
5. [Usage Guide](#usage-guide)
6. [Provider Setup](#provider-setup)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)
9. [API Reference](#api-reference)
10. [Monitoring & Metrics](#monitoring--metrics)

---

## Overview

The LLM Integration system enables the autonomous learning loop to generate novel trading strategies using Large Language Models. It provides a hybrid approach combining LLM innovation (20% of iterations) with Factor Graph mutation (80% baseline), ensuring stability through automatic fallback mechanisms.

### Key Features

- 🤖 **Multi-Provider Support**: OpenRouter, Google Gemini, OpenAI
- 🎯 **Controlled Innovation**: Configurable innovation rate (default 20%)
- 🛡️ **Automatic Fallback**: Factor Graph mutation on LLM failures
- 💰 **Cost Management**: < $0.10 per iteration
- 📊 **Feedback Loop**: Champion tracking and failure pattern avoidance
- 🔒 **Secure**: Environment variable API keys, no code execution before validation

### Value Proposition

**Without LLM**: System is limited to predefined Factor Graph templates - can only combine existing factors in known ways.

**With LLM**: System can discover novel strategies beyond templates - new indicator combinations, creative position sizing, innovative risk management approaches.

**Risk Mitigation**: 100% iteration success guaranteed through automatic fallback to Factor Graph when LLM fails.

---

## Architecture

### Components

```
┌────────────────────────────────────────────────────────────┐
│                   Autonomous Loop                           │
│                                                             │
│  ┌─────────────────────┐      ┌────────────────────────┐  │
│  │  Iteration Decision │      │   Fallback on Error     │  │
│  │  (Iter % 5 == 0)    │──────▶  Factor Graph Mutation │  │
│  └──────────┬──────────┘      └────────────────────────┘  │
│             │                                               │
│             ▼                                               │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           InnovationEngine                           │  │
│  │  ┌──────────────────────┬─────────────────────────┐ │  │
│  │  │   PromptBuilder      │    LLM Provider         │ │  │
│  │  │  - Champion Context  │  - OpenRouter/Gemini/   │ │  │
│  │  │  - Failure Patterns  │    OpenAI Abstraction   │ │  │
│  │  │  - Few-Shot Examples │  - Retry Logic          │ │  │
│  │  └──────────────────────┴─────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────┘  │
│             │                                               │
│             ▼                                               │
│  ┌─────────────────────────────────────────────────────┐  │
│  │     Validation Pipeline (AST, Schema, Safety)        │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Iteration Start**: Autonomous loop checks if LLM should be used (every 5th iteration)
2. **Context Gathering**: InnovationEngine receives champion code, metrics, failure history
3. **Prompt Construction**: PromptBuilder generates contextual prompt with feedback
4. **LLM API Call**: LLMProvider sends prompt to configured provider (OpenRouter/Gemini/OpenAI)
5. **Code Extraction**: Response parser extracts Python code using regex
6. **Validation**: AST syntax check → Schema validation → Safety verification
7. **Execution or Fallback**: Valid code proceeds to backtest; failures trigger Factor Graph fallback

---

## Installation & Setup

### Prerequisites

- Python 3.9+
- FinLab system installed and configured
- API key from at least one provider (OpenRouter recommended)

### Quick Setup (5 minutes)

#### Step 1: Install Dependencies

```bash
# Already included in requirements.txt
pip install requests pyyaml jsonschema
```

#### Step 2: Set Environment Variable

Choose your provider and set the corresponding API key:

```bash
# Option A: OpenRouter (Recommended - supports multiple models)
export OPENROUTER_API_KEY="sk-or-v1-your-api-key-here"

# Option B: Google Gemini (Fast and cost-effective)
export GOOGLE_API_KEY="AIza-your-api-key-here"
# OR
export GEMINI_API_KEY="AIza-your-api-key-here"

# Option C: OpenAI (Most capable)
export OPENAI_API_KEY="sk-your-api-key-here"
```

**Security Note**: Never commit API keys to git. Always use environment variables.

#### Step 3: Enable in Configuration

Edit `config/learning_system.yaml`:

```yaml
llm:
  enabled: true                              # Enable LLM integration
  provider: openrouter                       # openrouter | gemini | openai
  model: google/gemini-2.5-flash-lite       # Provider-specific model
  innovation_rate: 0.20                      # 20% of iterations
  timeout: 60                                # API timeout in seconds
  max_tokens: 2000                           # Max response tokens
  temperature: 0.1                           # Lower = more deterministic
  fallback_to_factor_graph: true            # Auto-fallback on errors
```

#### Step 4: Verify Setup

```bash
# Test LLM connectivity (dry-run mode, no execution)
python3 run_phase0_smoke_test.py

# Check for successful API connection
grep "LLM API Connectivity" artifacts/phase0_test_SUCCESS.log
# Expected: ✅ TC-P0-03: LLM API Connectivity
```

---

## Configuration

### Full Configuration Reference

```yaml
llm:
  # --- Core Settings ---
  enabled: true                              # Enable/disable LLM integration
  provider: openrouter                       # API provider selection
  model: google/gemini-2.5-flash-lite       # Model name
  api_key_env: OPENROUTER_API_KEY           # Environment variable name

  # --- Innovation Settings ---
  innovation_rate: 0.20                      # Fraction of iterations using LLM
  innovation_mode: hybrid                    # hybrid | llm_only | disabled

  # --- Generation Parameters ---
  max_tokens: 2000                           # Maximum response length
  temperature: 0.1                           # 0.0 = deterministic, 1.0 = creative
  timeout: 60                                # API call timeout (seconds)
  max_retries: 3                             # Retry attempts on rate limits
  retry_delay: 5                             # Initial retry delay (seconds)

  # --- Fallback Settings ---
  fallback_to_factor_graph: true            # Auto-fallback on failures
  disable_on_auth_failure: true             # Disable if API key invalid
  high_failure_threshold: 0.5               # Warning threshold (50% failures)

  # --- Prompt Engineering ---
  modification_prompt_template: src/innovation/prompts/modification_template.txt
  creation_prompt_template: src/innovation/prompts/creation_template.txt
  include_few_shot_examples: true           # Add example strategies to prompts

  # --- Cost Management ---
  max_cost_per_iteration: 0.10              # Cost limit per iteration ($)
  track_cumulative_cost: true               # Track total spend
```

### Provider-Specific Settings

#### OpenRouter Configuration

```yaml
llm:
  provider: openrouter
  model: google/gemini-2.5-flash-lite       # Recommended: Fast + cheap
  # OR
  # model: anthropic/claude-3.5-sonnet      # More capable but expensive
  # model: x-ai/grok-code-fast-1            # Alternative
  api_key_env: OPENROUTER_API_KEY
  timeout: 60
```

**Cost**: ~$0.0001 per request (gemini-2.5-flash-lite)

#### Google Gemini Configuration

```yaml
llm:
  provider: gemini
  model: gemini-2.5-flash-lite              # Fast and cheap
  # OR
  # model: gemini-2.5-pro                   # More capable
  api_key_env: GOOGLE_API_KEY               # or GEMINI_API_KEY
  timeout: 30
```

**Cost**: ~$0.0001 per request (flash-lite)

#### OpenAI Configuration

```yaml
llm:
  provider: openai
  model: gpt-4.1                            # Most capable
  # OR
  # model: gpt-5                            # Latest version
  # model: gpt-5-mini                       # Faster/cheaper
  api_key_env: OPENAI_API_KEY
  timeout: 60
```

**Cost**: ~$0.01 - $0.05 per request (model-dependent)

---

## Usage Guide

### Basic Usage

Once configured, LLM integration works automatically within the autonomous loop:

```python
# Run autonomous loop (LLM auto-activates every 5th iteration)
python3 -m artifacts.working.modules.autonomous_loop \
    --config config/learning_system.yaml \
    --generations 20
```

### Manual LLM Innovation

For testing or specific use cases:

```python
from src.innovation import InnovationEngine, LLMConfig
from src.innovation.llm_providers import OpenRouterProvider

# 1. Load configuration
config = LLMConfig.from_yaml("config/learning_system.yaml")

# 2. Initialize provider
provider = OpenRouterProvider(
    api_key=config.get_api_key(),
    model=config.model
)

# 3. Create innovation engine
engine = InnovationEngine(llm_provider=provider)

# 4. Generate strategy with feedback
champion_code = """
def strategy(data, position):
    # Current champion strategy
    ...
"""

result = engine.generate_with_feedback(
    champion_code=champion_code,
    champion_metrics={"sharpe": 1.52, "max_drawdown": -0.15},
    failure_history=["Avoid: High drawdown strategies", "Avoid: Over-trading"],
    innovation_directive="modify"
)

print(f"Generated code: {result.code}")
print(f"Success: {result.success}")
```

### Innovation Modes

#### 1. Modify Mode (Default)

Improve existing champion strategy:

```python
result = engine.generate_with_feedback(
    champion_code=champion_code,
    champion_metrics=champion_metrics,
    innovation_directive="modify",  # ← Modify existing
    target_metric="sharpe"
)
```

**Prompt Focus**: Parameter adjustments, factor additions/removals, entry/exit refinements

#### 2. Create Mode

Generate novel strategy:

```python
result = engine.generate_with_feedback(
    champion_code=champion_code,  # Used as inspiration only
    innovation_directive="create",  # ← Create new
    novelty_guidance="Explore alternative risk management approaches"
)
```

**Prompt Focus**: Novel indicator combinations, creative position sizing, new risk frameworks

---

## Provider Setup

### OpenRouter (Recommended)

**Pros**: Access to multiple models (Claude, Gemini, GPT, Grok), simple pricing, reliable

**Setup**:
1. Sign up at https://openrouter.ai/
2. Generate API key
3. Add credits ($5 minimum, lasts ~50,000 requests with flash-lite)
4. Export key: `export OPENROUTER_API_KEY="sk-or-v1-..."`

**Model Recommendations**:
- **Best Value**: `google/gemini-2.5-flash-lite` ($0.0001/request)
- **Most Capable**: `anthropic/claude-3.5-sonnet` ($0.01/request)
- **Alternative**: `x-ai/grok-code-fast-1` ($0.001/request)

### Google Gemini

**Pros**: Free tier available, very fast, good code generation

**Setup**:
1. Go to https://makersuite.google.com/app/apikey
2. Create API key
3. Export key: `export GOOGLE_API_KEY="AIza..."`

**Model Recommendations**:
- **Fast**: `gemini-2.5-flash-lite` (Free tier: 1500 requests/day)
- **Capable**: `gemini-2.5-pro` (Free tier: 50 requests/day)

### OpenAI

**Pros**: Most capable models, best reasoning

**Setup**:
1. Sign up at https://platform.openai.com/
2. Generate API key
3. Add credits
4. Export key: `export OPENAI_API_KEY="sk-..."`

**Model Recommendations**:
- **Latest**: `gpt-5` ($0.05/request)
- **Balanced**: `gpt-4.1` ($0.03/request)
- **Fast**: `gpt-5-mini` ($0.01/request)

---

## Troubleshooting

### Common Issues

#### 1. "API Key Environment Variable Not Set"

**Error**:
```
❌ TC-P0-01: API Key Environment Variable
    API key not set or invalid
```

**Solution**:
```bash
# Check if key is set
echo $OPENROUTER_API_KEY

# Set key in current session
export OPENROUTER_API_KEY="your-key-here"

# Persist across sessions (add to ~/.bashrc or ~/.zshrc)
echo 'export OPENROUTER_API_KEY="your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

#### 2. "LLM API Connectivity Failed"

**Error**:
```
❌ TC-P0-03: LLM API Connectivity
    OpenRouter API error None: 400 Client Error: Bad Request
```

**Possible Causes**:
- Invalid API key
- Incorrect model name
- Network connectivity issues
- Insufficient credits

**Solutions**:
```bash
# Verify API key is valid
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models

# Check model name
# Correct: google/gemini-2.5-flash-lite
# Wrong:   google/gemini-2.0-flash-lite  (doesn't exist)

# Test connectivity
ping openrouter.ai
```

#### 3. "Code Generation Failed or Empty"

**Error**:
```
❌ TC-P0-07: Code Generation
    Code generation failed or empty
```

**Root Causes**:
- LLM generates invalid condition types (e.g., "greater_than" instead of "threshold")
- LLM ignores schema constraints
- Temperature too high (too creative)

**Solutions**:
```yaml
# Lower temperature for more deterministic output
llm:
  temperature: 0.1  # Was 0.7

# Use more prescriptive prompts (already implemented in Phase 0 fixes)
# Update prompt templates with explicit examples
```

#### 4. "High LLM Failure Rate Warning"

**Warning**:
```
⚠️ High LLM failure rate (60%), consider reducing innovation_rate
```

**Solution**:
```yaml
# Reduce LLM usage temporarily
llm:
  innovation_rate: 0.10  # Was 0.20 (10% instead of 20%)

# OR disable LLM entirely
llm:
  enabled: false
```

#### 5. "Timeout Errors"

**Error**:
```
LLM API timeout after 60 seconds
```

**Solutions**:
```yaml
# Increase timeout
llm:
  timeout: 120  # Was 60

# Reduce max_tokens
llm:
  max_tokens: 1000  # Was 2000 (faster generation)
```

---

## Best Practices

### 1. Start Conservative

```yaml
# Initial configuration
llm:
  enabled: true
  innovation_rate: 0.10              # Start with 10%, increase to 20% after validation
  temperature: 0.1                   # Low temperature for consistency
  max_tokens: 1000                   # Shorter = faster + cheaper
  fallback_to_factor_graph: true    # Always enabled for safety
```

### 2. Monitor Metrics

Track LLM performance:

```python
# Check metrics after each run
import json

with open('iteration_history.json') as f:
    history = json.load(f)

llm_iterations = [it for it in history if it.get('used_llm')]
success_rate = sum(1 for it in llm_iterations if it['success']) / len(llm_iterations)

print(f"LLM Success Rate: {success_rate:.1%}")
```

### 3. Cost Management

```yaml
# Enable cost tracking
llm:
  track_cumulative_cost: true
  max_cost_per_iteration: 0.10      # Abort if single iteration exceeds $0.10

# Use cheap models for development
llm:
  model: google/gemini-2.5-flash-lite  # $0.0001/request

# Upgrade for production
llm:
  model: anthropic/claude-3.5-sonnet   # $0.01/request (100x more expensive)
```

### 4. Prompt Engineering

**Good Prompts**:
- Include champion context: "Current Sharpe: 1.52, preserve ROE smoothing"
- Specify constraints: "Liquidity >150M, monthly rebalancing"
- Add examples: "Example successful modification: ... Example successful creation: ..."
- Be prescriptive: "MUST use threshold type, NOT greater_than"

**Bad Prompts**:
- Too vague: "Make it better"
- No constraints: "Generate any strategy"
- No examples: "Here's some code, improve it"

### 5. Phase 0 Testing Before Production

Always run Phase 0 smoke test before enabling LLM in production:

```bash
# Phase 0: Dry-run mode (ZERO execution risk)
python3 run_phase0_smoke_test.py

# Check results
cat artifacts/phase0_test_SUCCESS.log

# If pass rate < 80%, investigate before proceeding
```

---

## API Reference

### LLMConfig

```python
from src.innovation import LLMConfig

# Load from YAML
config = LLMConfig.from_yaml("config/learning_system.yaml")

# Access properties
config.enabled              # bool: LLM enabled
config.provider             # str: openrouter | gemini | openai
config.model                # str: Model name
config.innovation_rate      # float: 0.0-1.0
config.temperature          # float: 0.0-1.0
config.max_tokens           # int: Max response tokens
config.timeout              # int: API timeout seconds

# Get API key from environment
api_key = config.get_api_key()  # Reads from environment variable
```

### LLMProvider

```python
from src.innovation.llm_providers import OpenRouterProvider, GeminiProvider, OpenAIProvider

# Initialize provider
provider = OpenRouterProvider(
    api_key="your-api-key",
    model="google/gemini-2.5-flash-lite"
)

# Generate response
response = provider.generate(
    prompt="Generate a momentum trading strategy",
    max_tokens=2000,
    temperature=0.1
)

# Access response
print(response.content)      # str: Generated text
print(response.model)        # str: Model used
print(response.tokens_used)  # int: Tokens consumed
print(response.cost)         # float: Cost in USD
```

### InnovationEngine

```python
from src.innovation import InnovationEngine

# Initialize with provider
engine = InnovationEngine(llm_provider=provider)

# Generate with feedback
result = engine.generate_with_feedback(
    champion_code=str,               # Current best strategy
    champion_metrics=dict,           # {"sharpe": 1.52, "max_drawdown": -0.15}
    failure_history=list[str],       # ["Avoid: ..."]
    innovation_directive=str,        # "modify" | "create"
    target_metric=str                # "sharpe" | "calmar" | "win_rate"
)

# Check result
result.success           # bool: Generation successful
result.code              # str: Generated Python code
result.error_message     # str: Error if failed
result.fallback_used     # bool: Factor Graph used instead
```

---

## Monitoring & Metrics

### Prometheus Metrics

LLM integration exports the following metrics:

```
# LLM API Calls
llm_api_calls_total{provider="openrouter", model="gemini-2.5-flash-lite", status="success"}
llm_api_calls_total{provider="openrouter", model="gemini-2.5-flash-lite", status="failure"}

# LLM Response Time
llm_response_time_seconds{provider="openrouter", model="gemini-2.5-flash-lite"}

# LLM Token Usage
llm_tokens_used_total{provider="openrouter", model="gemini-2.5-flash-lite"}

# LLM Cost
llm_cost_usd_total{provider="openrouter", model="gemini-2.5-flash-lite"}

# Validation Results
llm_code_validation_total{status="pass"}
llm_code_validation_total{status="fail_syntax"}
llm_code_validation_total{status="fail_schema"}
llm_code_validation_total{status="fail_safety"}

# Fallback Events
llm_fallback_to_factor_graph_total{reason="api_error"}
llm_fallback_to_factor_graph_total{reason="validation_error"}
llm_fallback_to_factor_graph_total{reason="timeout"}
```

### Log Messages

```bash
# Successful LLM generation
INFO  [Innovation] LLM generation successful (iteration 5, 1.2s, $0.0001)

# Fallback to Factor Graph
WARN  [Innovation] LLM unavailable for iteration 10, falling back to Factor Graph mutation

# High failure rate warning
WARN  [Innovation] High LLM failure rate (60% over 10 iterations), consider reducing innovation_rate

# Cost warning
WARN  [Innovation] LLM cost for iteration 15 ($0.12) exceeds max_cost_per_iteration ($0.10)
```

### Dashboard Tracking

Key metrics to monitor on Grafana dashboard:

1. **LLM Success Rate**: Target >70%
2. **Average Response Time**: Target <2 seconds
3. **Cost Per Iteration**: Target <$0.10
4. **Fallback Frequency**: Target <20%
5. **Validation Pass Rate**: Target >90%

---

## FAQ

### Q: Why only 20% LLM usage?

**A**: Conservative rollout to contain risk. LLM failures don't stall iterations due to Factor Graph fallback. Can increase to 50%+ after validation.

### Q: Which provider is cheapest?

**A**: OpenRouter with `google/gemini-2.5-flash-lite` (~$0.0001 per request). Google Gemini direct API also offers free tier (1500 requests/day).

### Q: Can I use multiple providers?

**A**: Not simultaneously, but you can switch providers by changing `config/learning_system.yaml`. Future enhancement may support A/B testing multiple providers.

### Q: What happens if LLM generates invalid code?

**A**: Validation pipeline catches it (AST → Schema → Safety checks), logs the failure, and automatically falls back to Factor Graph mutation. Iteration never stalls.

### Q: Can I disable LLM temporarily?

**A**: Yes, set `llm.enabled: false` in config. System falls back to 100% Factor Graph mutation.

### Q: How do I know if LLM is working?

**A**: Check `iteration_history.json` for `"used_llm": true` entries, or monitor Prometheus metric `llm_api_calls_total`.

---

## Next Steps

1. **Phase 0 Testing** (5 min, $0.10, ZERO risk):
   ```bash
   python3 run_phase0_smoke_test.py
   ```

2. **Phase 1 Testing** (30 min, $0.20):
   - Requires Docker Security Tier 1 fixes
   - 12 test cases with container isolation

3. **Production Deployment**:
   - Start with `innovation_rate: 0.10`
   - Monitor success rate for 20 iterations
   - Increase to 0.20 if >70% success

4. **Advanced Features**:
   - Custom prompt templates
   - A/B testing multiple models
   - Structured innovation (YAML/JSON) - Phase 2a

---

## References

- **Spec**: `.spec-workflow/specs/llm-integration-activation/`
- **Quick Start**: `docs/LLM_CONFIG_QUICK_START.md`
- **Phase 0 Testing**: `run_phase0_smoke_test.py`
- **Provider APIs**:
  - OpenRouter: https://openrouter.ai/docs
  - Gemini: https://ai.google.dev/docs
  - OpenAI: https://platform.openai.com/docs

---

**Document Version**: 1.0
**Created**: 2025-10-27
**Last Updated**: 2025-10-27
**Maintained By**: FinLab Team
