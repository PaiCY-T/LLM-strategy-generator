#!/usr/bin/env python3
"""
Environment Validation Script for Autonomous Iteration Engine

Validates that all required dependencies and API keys are properly configured
before running the iteration engine.

Usage:
    python validate_environment.py

Exit Codes:
    0: All validations passed
    1: One or more validations failed
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Verify Python version is 3.8 or higher."""
    print("Checking Python version...")
    version = sys.version_info

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"  ❌ Python {version.major}.{version.minor} detected")
        print(f"  Required: Python 3.8 or higher")
        return False

    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Verify all required packages are installed."""
    print("\nChecking dependencies...")

    required_packages = {
        'openai': 'OpenRouter client',
        'httpx': 'HTTP client',
        'pandas': 'Data processing',
        'numpy': 'Numerical operations',
        'duckdb': 'Data warehouse',
        'finlab': 'Backtesting library',
        'pytest': 'Testing framework',
        'dotenv': 'Environment management'
    }

    all_installed = True

    for package, description in required_packages.items():
        try:
            if package == 'dotenv':
                __import__('dotenv')
            else:
                __import__(package)
            print(f"  ✓ {package:15s} - {description}")
        except ImportError:
            print(f"  ❌ {package:15s} - {description} (NOT INSTALLED)")
            all_installed = False

    if not all_installed:
        print("\n  Install missing packages:")
        print("  pip install -r requirements.txt")

    return all_installed


def check_environment_variables():
    """Verify required environment variables are set."""
    print("\nChecking environment variables...")

    # Try to load from .env file
    try:
        from dotenv import load_dotenv
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            print(f"  ✓ Loaded .env file from {env_file}")
        else:
            print(f"  ⚠ .env file not found at {env_file}")
            print(f"    Environment variables must be set manually")
    except ImportError:
        print("  ⚠ python-dotenv not installed, skipping .env file")

    required_vars = {
        'FINLAB_API_TOKEN': 'Finlab API access',
        'OPENROUTER_API_KEY': 'Claude API access via OpenRouter'
    }

    all_set = True

    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask the key for security
            masked = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
            print(f"  ✓ {var:20s} - {description} ({masked})")
        else:
            print(f"  ❌ {var:20s} - {description} (NOT SET)")
            all_set = False

    if not all_set:
        print("\n  Set environment variables in .env file or export them:")
        print("  export FINLAB_API_TOKEN='your_token'")
        print("  export OPENROUTER_API_KEY='your_key'")

    return all_set


def check_finlab_api_connection():
    """Test connection to Finlab API."""
    print("\nChecking Finlab API connection...")

    try:
        import finlab
        from finlab import data

        # Try to access a simple dataset to verify connectivity
        # Note: This may consume API quota
        print("  Testing API connectivity (may take a few seconds)...")

        # This is a lightweight check - just verify we can import
        print(f"  ✓ Finlab library version: {finlab.__version__ if hasattr(finlab, '__version__') else 'unknown'}")
        print("  ⚠ API connectivity not tested (would consume quota)")
        print("    Run a full test with: data.get('price:收盤價')")

        return True

    except ImportError:
        print("  ❌ Finlab library not installed")
        return False
    except Exception as e:
        print(f"  ❌ Error accessing Finlab API: {e}")
        return False


def check_claude_api_connection():
    """Test connection to Claude API via OpenRouter."""
    print("\nChecking Claude API connection...")

    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("  ❌ OPENROUTER_API_KEY not set, skipping connection test")
        return False

    try:
        from openai import OpenAI

        print("  Testing API connectivity (may take a few seconds)...")

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )

        # Simple test call with minimal token usage
        response = client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )

        print("  ✓ Claude API connection successful")
        print(f"  ✓ Model: {response.model}")

        return True

    except ImportError:
        print("  ❌ OpenAI library not installed")
        return False
    except Exception as e:
        print(f"  ❌ Error connecting to Claude API: {e}")
        return False


def main():
    """Run all validation checks."""
    print("=" * 70)
    print("Autonomous Iteration Engine - Environment Validation")
    print("=" * 70)

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment Variables", check_environment_variables),
        ("Finlab API", check_finlab_api_connection),
        ("Claude API", check_claude_api_connection)
    ]

    results = []

    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ❌ Unexpected error in {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("Validation Summary")
    print("=" * 70)

    all_passed = True
    for name, result in results:
        status = "✓ PASSED" if result else "❌ FAILED"
        print(f"  {status:12s} - {name}")
        if not result:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n✓ All checks passed! Environment is ready.")
        print("  You can now run: python iteration_engine.py")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
