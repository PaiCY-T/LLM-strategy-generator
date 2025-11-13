"""LLM Strategy Generator with API Routing Validation.

Provides validation functions to ensure model names match provider capabilities,
preventing API routing errors that cause 404 responses.

Bug Context:
- Bug #2: anthropic models sent to Google API cause 404 errors
- This module provides validation to prevent misrouted API calls

Requirements: R2 (LLM API routing configuration)
Task: docker-integration-test-framework Task 3.1
"""


def _validate_model_provider_match(provider: str, model: str) -> None:
    """Validate model name matches provider capabilities.

    Prevents API routing errors by ensuring model names are compatible with
    the configured LLM provider. For example, prevents sending anthropic/*
    models to the Google Gemini API which only supports gemini-* models.

    Args:
        provider: LLM provider name (e.g., 'google', 'openrouter', 'openai')
        model: Model name (e.g., 'gemini-2.5-flash', 'anthropic/claude-3.5-sonnet')

    Raises:
        ValueError: If model/provider combination is invalid

    Validation Rules:
        - google/gemini: Only accepts gemini-* models
        - openrouter: Accepts any model format (acts as proxy)
        - openai: Only accepts gpt-*, o1-*, o3-* models
        - Provider names are case-insensitive
        - Empty provider or model raises ValueError
        - Unknown provider raises ValueError

    Examples:
        >>> _validate_model_provider_match('google', 'gemini-2.5-flash')  # OK
        >>> _validate_model_provider_match('google', 'anthropic/claude-3.5-sonnet')  # Raises ValueError
        >>> _validate_model_provider_match('openrouter', 'anthropic/claude-3.5-sonnet')  # OK
        >>> _validate_model_provider_match('openai', 'gpt-4')  # OK
        >>> _validate_model_provider_match('openai', 'gemini-2.5-flash')  # Raises ValueError
    """
    # Validate inputs are not empty
    if not provider or not provider.strip():
        raise ValueError("Provider name cannot be empty")

    if not model or not model.strip():
        raise ValueError("Model name cannot be empty")

    # Normalize provider name to lowercase for case-insensitive comparison
    provider_normalized = provider.strip().lower()

    # Define provider validation rules
    if provider_normalized in ('google', 'gemini'):
        # Google/Gemini provider: only accepts gemini-* models
        if not model.startswith('gemini-') and not model.startswith('gemini/'):
            raise ValueError(
                f"Model '{model}' is not compatible with provider '{provider}'. "
                f"Google/Gemini provider only supports gemini-* models. "
                f"For anthropic models, use provider='openrouter' instead."
            )

    elif provider_normalized == 'openrouter':
        # OpenRouter is a proxy service - accepts any model format
        # No validation needed, all models are valid
        pass

    elif provider_normalized == 'openai':
        # OpenAI provider: only accepts gpt-*, o1-*, o3-* models
        model_lower = model.lower()
        is_valid_openai_model = (
            model_lower.startswith('gpt-') or
            model_lower.startswith('o1-') or
            model_lower.startswith('o3-') or
            model_lower.startswith('openai/gpt-') or
            model_lower.startswith('openai/o1-') or
            model_lower.startswith('openai/o3-')
        )

        if not is_valid_openai_model:
            raise ValueError(
                f"Model '{model}' is not compatible with provider '{provider}'. "
                f"OpenAI provider only supports gpt-*, o1-*, o3-* models. "
                f"For other models, use provider='openrouter' instead."
            )

    else:
        # Unknown provider
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Supported providers: google, gemini, openrouter, openai"
        )
