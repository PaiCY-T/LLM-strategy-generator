# LLM Configuration Quick Reference

## Quick Start (3 Steps)

### 1. Set API Key (Choose One Provider)
```bash
# OpenRouter (recommended)
export OPENROUTER_API_KEY="sk-or-v1-..."

# OR Gemini
export GOOGLE_API_KEY="AIza..."

# OR OpenAI
export OPENAI_API_KEY="sk-..."
```

### 2. Enable LLM in Config
Edit `config/learning_system.yaml`:
```yaml
llm:
  enabled: true
  provider: openrouter  # or gemini, openai
  innovation_rate: 0.2  # 20% of iterations use LLM
```

### 3. Run Your System
```bash
python run_autonomous_loop.py
```

---

## Configuration Options

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| `enabled` | `false` | true/false | Enable/disable LLM innovation |
| `provider` | `openrouter` | openrouter, gemini, openai | LLM provider selection |
| `innovation_rate` | `0.20` | 0.0-1.0 | % of iterations using LLM |
| `fallback.enabled` | `true` | true/false | Auto-fallback to Factor Graph |
| `fallback.max_retries` | `3` | 0+ | Retry attempts on rate limits |
| `fallback.retry_delay` | `2` | 0+ | Retry delay (seconds) |
| `generation.max_tokens` | `2000` | 100-10000 | Max response tokens |
| `generation.temperature` | `0.7` | 0.0-2.0 | Creativity level |
| `generation.timeout` | `60` | 10-600 | API timeout (seconds) |

---

## Provider Comparison

| Feature | OpenRouter | Gemini | OpenAI |
|---------|-----------|--------|--------|
| **Models** | Claude, GPT-4, etc. | Gemini 2.5 Flash/Pro | GPT-4, GPT-4 Turbo |
| **Cost** | $$ | $ | $$$ |
| **Speed** | Fast | Very Fast | Fast |
| **Quality** | Excellent | Excellent | Excellent |
| **Best For** | Production | Cost-effective | High accuracy |

---

## Environment Variables

### OpenRouter
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
export LLM_MODEL="anthropic/claude-3.5-sonnet"  # optional
```

### Gemini
```bash
export GOOGLE_API_KEY="AIza..."
export LLM_MODEL="gemini-2.5-flash"  # optional
```

### OpenAI
```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_ORG_ID="org-..."  # optional
export LLM_MODEL="gpt-4"  # optional
```

---

## Cost Control

### Reduce LLM Usage
```yaml
llm:
  innovation_rate: 0.1  # 10% instead of 20%
```

### Disable LLM Temporarily
```yaml
llm:
  enabled: false
```

### Use Cheaper Model
```yaml
llm:
  provider: gemini
  model: gemini-2.5-flash  # Faster and cheaper than Pro
```

---

## Troubleshooting

### LLM Not Working?
1. Check API key is set: `echo $OPENROUTER_API_KEY`
2. Verify LLM enabled: `grep "enabled: true" config/learning_system.yaml`
3. Check logs for errors: `tail -f logs/autonomous_loop.log`

### Rate Limit Errors?
```yaml
llm:
  fallback:
    max_retries: 5  # Increase from 3
    retry_delay: 5  # Increase from 2
```

### Too Expensive?
```yaml
llm:
  innovation_rate: 0.1  # Reduce from 0.2
  provider: gemini      # Switch to cheaper provider
```

### Invalid Responses?
```yaml
llm:
  generation:
    temperature: 0.5  # Reduce from 0.7 for more deterministic output
```

---

## Testing Your Setup

```bash
# Run config validation tests
python3 -m pytest tests/config/test_llm_config.py -v

# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config/learning_system.yaml'))"

# Check API key is set
echo "OpenRouter: ${OPENROUTER_API_KEY:+SET}" 
echo "Gemini: ${GOOGLE_API_KEY:+SET}"
echo "OpenAI: ${OPENAI_API_KEY:+SET}"
```

---

## Security Best Practices

✅ **DO**:
- Use environment variables for API keys
- Rotate API keys regularly
- Keep API keys in `.env` or secrets manager
- Use `${ENV_VAR}` syntax in config

❌ **DON'T**:
- Hardcode API keys in config files
- Commit API keys to git
- Share API keys in logs or messages
- Use production keys in development

---

## Files Reference

| File | Purpose |
|------|---------|
| `config/learning_system.yaml` | Main configuration |
| `schemas/llm_config_schema.json` | Validation schema |
| `tests/config/test_llm_config.py` | Configuration tests |
| `docs/LLM_INTEGRATION.md` | Full documentation |

---

## Support

- Full Documentation: `docs/LLM_INTEGRATION.md`
- Task Spec: `.spec-workflow/specs/llm-integration-activation/`
- Test Suite: `tests/config/test_llm_config.py`
- Schema: `schemas/llm_config_schema.json`

---

**Last Updated**: 2025-10-27
**Version**: Task 6 Complete
**Status**: Production Ready
