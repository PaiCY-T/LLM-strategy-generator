#!/usr/bin/env python3
"""
LLM Setup Validation Script

Validates LLM integration configuration including:
- API key configuration (environment variables)
- learning_system.yaml configuration
- API connectivity for all 3 providers (OpenRouter, Gemini, OpenAI)
- Provider-specific model availability

Task: LLM Integration Activation - Task 14
Requirements: All configuration requirements (2.1-2.4)

Usage:
    python scripts/validate_llm_setup.py                    # Full validation
    python scripts/validate_llm_setup.py --provider gemini   # Test specific provider
    python scripts/validate_llm_setup.py --skip-connectivity # Config check only
    python scripts/validate_llm_setup.py --verbose          # Detailed output

Exit Codes:
    0: All validations passed
    1: Configuration error (API keys, YAML config)
    2: Connectivity error (API call failed)
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.innovation.llm_providers import (
        OpenRouterProvider,
        GeminiProvider,
        OpenAIProvider,
        LLMProviderInterface
    )
    PROVIDERS_AVAILABLE = True
except ImportError as e:
    PROVIDERS_AVAILABLE = False
    IMPORT_ERROR = str(e)


# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {text}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.RESET} {text}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {text}")


def check_imports() -> Tuple[bool, str]:
    """Check if LLM provider modules are importable."""
    if not PROVIDERS_AVAILABLE:
        return False, f"Failed to import LLM providers: {IMPORT_ERROR}"
    return True, "LLM provider modules imported successfully"


def check_env_vars(verbose: bool = False) -> Tuple[bool, Dict[str, bool], List[str]]:
    """
    Check for API key environment variables.

    Returns:
        Tuple of (all_present, status_dict, messages)
    """
    print_header("Environment Variables Check")

    env_vars = {
        'OPENROUTER_API_KEY': {
            'name': 'OpenRouter',
            'docs': 'https://openrouter.ai/keys',
            'export': 'export OPENROUTER_API_KEY="your-key-here"'
        },
        'GOOGLE_API_KEY': {
            'name': 'Google Gemini',
            'docs': 'https://makersuite.google.com/app/apikey',
            'export': 'export GOOGLE_API_KEY="your-key-here"',
            'alternatives': ['GEMINI_API_KEY']
        },
        'OPENAI_API_KEY': {
            'name': 'OpenAI',
            'docs': 'https://platform.openai.com/api-keys',
            'export': 'export OPENAI_API_KEY="your-key-here"'
        }
    }

    status = {}
    messages = []
    any_present = False

    for var, info in env_vars.items():
        value = os.getenv(var)

        # Check alternatives
        if not value and 'alternatives' in info:
            for alt in info['alternatives']:
                value = os.getenv(alt)
                if value:
                    var = alt  # Use alternative name
                    break

        status[var] = bool(value)

        if value:
            any_present = True
            # Mask key for security
            masked = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
            print_success(f"{info['name']:15s} ({var}): {masked}")
            if verbose:
                messages.append(f"{info['name']} API key configured")
        else:
            print_warning(f"{info['name']:15s} ({var}): Not configured")
            messages.append(f"{info['name']} API key missing")
            if verbose:
                print(f"  {Colors.YELLOW}Set with:{Colors.RESET} {info['export']}")
                print(f"  {Colors.YELLOW}Get key:{Colors.RESET} {info['docs']}")

    if not any_present:
        print_error("No API keys configured")
        messages.append("At least one provider API key is required")
        return False, status, messages

    return True, status, messages


def check_config(verbose: bool = False) -> Tuple[bool, Optional[Dict], List[str]]:
    """
    Check learning_system.yaml LLM configuration.

    Returns:
        Tuple of (valid, config_dict, messages)
    """
    print_header("Configuration File Check")

    config_path = Path(__file__).parent.parent / 'config' / 'learning_system.yaml'
    messages = []

    if not config_path.exists():
        print_error(f"Config file not found: {config_path}")
        messages.append("learning_system.yaml missing")
        return False, None, messages

    print_success(f"Config file found: {config_path}")

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print_error(f"YAML parsing error: {e}")
        messages.append(f"Invalid YAML syntax: {e}")
        return False, None, messages

    # Check for llm section
    if 'llm' not in config:
        print_error("Missing 'llm' section in config")
        messages.append("Add 'llm' section to learning_system.yaml")
        return False, None, messages

    llm_config = config['llm']
    print_success("LLM section found in config")

    # Validate required fields
    required_fields = {
        'enabled': bool,
        'provider': str,
        'innovation_rate': (int, float),
    }

    all_valid = True
    for field, expected_type in required_fields.items():
        if field not in llm_config:
            print_warning(f"Missing field: llm.{field}")
            messages.append(f"Missing llm.{field} in config")
            all_valid = False
        else:
            value = llm_config[field]
            # Expand environment variables
            if isinstance(value, str) and value.startswith('${'):
                # Extract default value or use the variable name
                parts = value[2:-1].split(':')
                env_var = parts[0]
                default = parts[1] if len(parts) > 1 else None
                expanded = os.getenv(env_var, default)

                # Convert to appropriate type
                if field == 'enabled':
                    value = expanded.lower() in ('true', '1', 'yes') if expanded else False
                elif field == 'innovation_rate':
                    value = float(expanded) if expanded else 0.2
                else:
                    value = expanded

            if not isinstance(value, expected_type):
                print_warning(f"Invalid type for llm.{field}: expected {expected_type}, got {type(value)}")
                messages.append(f"llm.{field} has wrong type")
                all_valid = False
            else:
                print_success(f"llm.{field} = {value}")
                if verbose:
                    messages.append(f"llm.{field} configured correctly")

    # Validate innovation_rate range
    innovation_rate = llm_config.get('innovation_rate', 0.2)
    if isinstance(innovation_rate, str):
        # Extract from env var syntax
        if innovation_rate.startswith('${'):
            parts = innovation_rate[2:-1].split(':')
            default = parts[1] if len(parts) > 1 else '0.2'
            innovation_rate = float(os.getenv(parts[0], default))

    if not (0.0 <= innovation_rate <= 1.0):
        print_error(f"innovation_rate out of range: {innovation_rate} (must be 0.0-1.0)")
        messages.append("innovation_rate must be between 0.0 and 1.0")
        all_valid = False

    # Validate provider
    provider = llm_config.get('provider', 'openrouter')
    if isinstance(provider, str) and provider.startswith('${'):
        parts = provider[2:-1].split(':')
        provider = os.getenv(parts[0], parts[1] if len(parts) > 1 else 'openrouter')

    valid_providers = ['openrouter', 'gemini', 'openai']
    if provider not in valid_providers:
        print_error(f"Invalid provider: {provider} (must be one of {valid_providers})")
        messages.append(f"provider must be one of {valid_providers}")
        all_valid = False

    # Check provider-specific config
    if provider in llm_config:
        provider_config = llm_config[provider]
        print_success(f"Provider-specific config found for: {provider}")

        if 'api_key' in provider_config:
            api_key_value = provider_config['api_key']
            if isinstance(api_key_value, str) and api_key_value.startswith('${'):
                env_var = api_key_value[2:-1].split(':')[0]
                print_info(f"API key configured via environment variable: {env_var}")
            else:
                print_warning(f"API key hardcoded in config (security risk!)")
                messages.append("Do not hardcode API keys in config files")

        if 'model' in provider_config:
            model = provider_config['model']
            if isinstance(model, str) and model.startswith('${'):
                parts = model[2:-1].split(':')
                model = os.getenv(parts[0], parts[1] if len(parts) > 1 else 'unknown')
            print_info(f"Model configured: {model}")
    else:
        print_warning(f"No provider-specific config for: {provider}")
        messages.append(f"Consider adding llm.{provider} section for detailed configuration")

    return all_valid, llm_config, messages


def test_connectivity(
    provider_name: Optional[str] = None,
    verbose: bool = False
) -> Tuple[bool, Dict[str, bool], List[str]]:
    """
    Test API connectivity for configured providers.

    Args:
        provider_name: Test specific provider only, or None for all
        verbose: Print detailed output

    Returns:
        Tuple of (all_successful, status_dict, messages)
    """
    print_header("API Connectivity Check")

    if not PROVIDERS_AVAILABLE:
        print_error("Cannot test connectivity - LLM providers not available")
        return False, {}, ["LLM provider modules not imported"]

    providers_to_test = {}
    messages = []

    # Determine which providers to test
    if provider_name:
        provider_name = provider_name.lower()
        if provider_name == 'openrouter':
            api_key = os.getenv('OPENROUTER_API_KEY')
            if api_key:
                providers_to_test['openrouter'] = (OpenRouterProvider, api_key)
        elif provider_name == 'gemini':
            api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            if api_key:
                providers_to_test['gemini'] = (GeminiProvider, api_key)
        elif provider_name == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                providers_to_test['openai'] = (OpenAIProvider, api_key)
        else:
            print_error(f"Unknown provider: {provider_name}")
            return False, {}, [f"Unknown provider: {provider_name}"]

        if not providers_to_test:
            print_error(f"No API key configured for {provider_name}")
            return False, {}, [f"{provider_name} API key not configured"]
    else:
        # Test all configured providers
        if os.getenv('OPENROUTER_API_KEY'):
            providers_to_test['openrouter'] = (OpenRouterProvider, os.getenv('OPENROUTER_API_KEY'))
        if os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY'):
            api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            providers_to_test['gemini'] = (GeminiProvider, api_key)
        if os.getenv('OPENAI_API_KEY'):
            providers_to_test['openai'] = (OpenAIProvider, os.getenv('OPENAI_API_KEY'))

    if not providers_to_test:
        print_warning("No providers configured for testing")
        return True, {}, ["No API keys configured"]

    status = {}
    all_successful = True

    # Simple test prompt
    test_prompt = "Hello! Please respond with 'OK' if you can read this message."

    for name, (provider_class, api_key) in providers_to_test.items():
        print(f"\nTesting {name.upper()}...")

        try:
            # Initialize provider
            if verbose:
                print_info(f"Initializing {provider_class.__name__}...")

            provider = provider_class(api_key=api_key, timeout=30)

            # Make test API call
            if verbose:
                print_info(f"Making test API call...")

            response = provider.generate(test_prompt, max_tokens=50)

            # Validate response
            if response and response.content:
                print_success(f"{name.upper()} connectivity OK")
                print_info(f"  Model: {response.model}")
                print_info(f"  Tokens: {response.total_tokens} (prompt: {response.prompt_tokens}, completion: {response.completion_tokens})")

                if verbose:
                    print_info(f"  Response: {response.content[:100]}...")

                # Estimate cost
                cost = provider.estimate_cost(response.prompt_tokens, response.completion_tokens)
                print_info(f"  Cost: ${cost:.6f}")

                status[name] = True
                messages.append(f"{name} API is working")
            else:
                print_error(f"{name.upper()} returned empty response")
                status[name] = False
                messages.append(f"{name} returned empty response")
                all_successful = False

        except ValueError as e:
            # Configuration error (API key, etc.)
            print_error(f"{name.upper()} configuration error: {e}")
            status[name] = False
            messages.append(f"{name} configuration error: {e}")
            all_successful = False

        except Exception as e:
            # API call error
            error_msg = str(e)
            print_error(f"{name.upper()} API error: {error_msg}")
            status[name] = False

            # Provide helpful error messages
            if 'authentication' in error_msg.lower() or 'api key' in error_msg.lower():
                messages.append(f"{name} authentication failed - check API key")
                print_info("  Verify your API key is correct and active")
            elif 'timeout' in error_msg.lower():
                messages.append(f"{name} connection timeout")
                print_info("  Check your internet connection")
            elif 'rate limit' in error_msg.lower():
                messages.append(f"{name} rate limit exceeded")
                print_info("  Wait a moment and try again")
            else:
                messages.append(f"{name} API error: {error_msg}")

            all_successful = False

    return all_successful, status, messages


def generate_report(
    imports_ok: bool,
    env_ok: bool,
    config_ok: bool,
    connectivity_ok: bool,
    env_status: Dict[str, bool],
    connectivity_status: Dict[str, bool],
    messages: List[str],
    verbose: bool = False
) -> None:
    """Generate final validation report."""
    print_header("Validation Report")

    # Overall status
    all_checks = [imports_ok, env_ok, config_ok, connectivity_ok]
    overall_status = all(all_checks)

    print("\nValidation Summary:")
    print(f"  Imports:      {Colors.GREEN + '✓ PASS' + Colors.RESET if imports_ok else Colors.RED + '✗ FAIL' + Colors.RESET}")
    print(f"  Environment:  {Colors.GREEN + '✓ PASS' + Colors.RESET if env_ok else Colors.RED + '✗ FAIL' + Colors.RESET}")
    print(f"  Config:       {Colors.GREEN + '✓ PASS' + Colors.RESET if config_ok else Colors.RED + '✗ FAIL' + Colors.RESET}")
    print(f"  Connectivity: {Colors.GREEN + '✓ PASS' + Colors.RESET if connectivity_ok else Colors.RED + '✗ FAIL' + Colors.RESET}")

    # Provider status
    if env_status or connectivity_status:
        print("\nProvider Status:")
        all_providers = set(list(env_status.keys()) + list(connectivity_status.keys()))

        for provider in ['OPENROUTER_API_KEY', 'GOOGLE_API_KEY', 'OPENAI_API_KEY']:
            provider_name = provider.replace('_API_KEY', '').lower()
            env_configured = env_status.get(provider, False)
            api_working = connectivity_status.get(provider_name, False)

            if env_configured:
                status = f"{Colors.GREEN}✓{Colors.RESET} Configured"
                if connectivity_status:  # Only show API status if we tested connectivity
                    if api_working:
                        status += f" & {Colors.GREEN}✓{Colors.RESET} Working"
                    else:
                        status += f" & {Colors.RED}✗{Colors.RESET} API Error"
            else:
                status = f"{Colors.YELLOW}○{Colors.RESET} Not configured"

            print(f"  {provider_name.capitalize():12s}: {status}")

    # Recommendations
    if not overall_status:
        print(f"\n{Colors.BOLD}Recommendations:{Colors.RESET}")

        if not imports_ok:
            print(f"  {Colors.RED}1.{Colors.RESET} Fix import errors - ensure LLM provider modules are available")
            print(f"     Run: python -m pytest tests/innovation/test_llm_providers.py -v")

        if not env_ok:
            print(f"  {Colors.RED}2.{Colors.RESET} Configure at least one API key:")
            print(f"     export OPENROUTER_API_KEY='your-key-here'")
            print(f"     export GOOGLE_API_KEY='your-key-here'")
            print(f"     export OPENAI_API_KEY='your-key-here'")

        if not config_ok:
            print(f"  {Colors.RED}3.{Colors.RESET} Fix learning_system.yaml configuration:")
            print(f"     Ensure 'llm' section has all required fields")
            print(f"     See config/learning_system.yaml for reference")

        if not connectivity_ok:
            print(f"  {Colors.RED}4.{Colors.RESET} Fix API connectivity issues:")
            for provider, working in connectivity_status.items():
                if not working:
                    print(f"     - {provider}: Check API key and network connectivity")
    else:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All validations passed!{Colors.RESET}")
        print(f"\n{Colors.GREEN}LLM integration is properly configured and ready to use.{Colors.RESET}")
        print(f"\nTo enable LLM innovation:")
        print(f"  1. Set llm.enabled: true in config/learning_system.yaml")
        print(f"  2. Or set environment variable: export LLM_ENABLED=true")
        print(f"  3. Run your autonomous loop with LLM-driven innovation")

    # Verbose messages
    if verbose and messages:
        print(f"\n{Colors.BOLD}Detailed Messages:{Colors.RESET}")
        for msg in messages:
            print(f"  • {msg}")


def main():
    """Main validation workflow."""
    parser = argparse.ArgumentParser(
        description="Validate LLM integration setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                         # Full validation (all providers)
  %(prog)s --provider openrouter   # Test OpenRouter only
  %(prog)s --provider gemini       # Test Gemini only
  %(prog)s --skip-connectivity     # Config check only (no API calls)
  %(prog)s --verbose               # Detailed output

Exit codes:
  0 = Success (all checks passed)
  1 = Configuration error
  2 = Connectivity error
"""
    )

    parser.add_argument(
        '--provider',
        choices=['openrouter', 'gemini', 'openai'],
        help='Test specific provider only'
    )
    parser.add_argument(
        '--skip-connectivity',
        action='store_true',
        help='Skip API connectivity tests (config check only)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed output'
    )

    args = parser.parse_args()

    print(f"{Colors.BOLD}LLM Setup Validation{Colors.RESET}")
    print(f"Task: LLM Integration Activation - Task 14\n")

    all_messages = []

    # Check 1: Imports
    imports_ok, import_msg = check_imports()
    if not imports_ok:
        print_header("Import Check")
        print_error(import_msg)
        all_messages.append(import_msg)
        env_ok = config_ok = connectivity_ok = False
        env_status = {}
        connectivity_status = {}
    else:
        print_header("Import Check")
        print_success(import_msg)
        all_messages.append(import_msg)

        # Check 2: Environment variables
        env_ok, env_status, env_messages = check_env_vars(args.verbose)
        all_messages.extend(env_messages)

        # Check 3: Configuration file
        config_ok, config, config_messages = check_config(args.verbose)
        all_messages.extend(config_messages)

        # Check 4: API connectivity (unless skipped)
        if args.skip_connectivity:
            print_header("API Connectivity Check")
            print_info("Skipped (--skip-connectivity flag)")
            connectivity_ok = True
            connectivity_status = {}
        else:
            connectivity_ok, connectivity_status, conn_messages = test_connectivity(
                args.provider,
                args.verbose
            )
            all_messages.extend(conn_messages)

    # Generate report
    generate_report(
        imports_ok,
        env_ok,
        config_ok,
        connectivity_ok,
        env_status,
        connectivity_status,
        all_messages,
        args.verbose
    )

    # Determine exit code
    if not imports_ok or not env_ok or not config_ok:
        sys.exit(1)  # Configuration error
    elif not connectivity_ok:
        sys.exit(2)  # Connectivity error
    else:
        sys.exit(0)  # Success


if __name__ == '__main__':
    main()
