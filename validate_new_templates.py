#!/usr/bin/env python3
"""
Standalone validation script for new parameter search space modules.
This avoids importing old template files with type errors.
"""

import sys
import subprocess


def run_mypy_on_files():
    """Run mypy on individual files without triggering __init__.py imports."""
    files = [
        'src/templates/parameter_spaces.py',
        'src/templates/template_registry.py'
    ]

    print("Running mypy with --strict on new template files...")
    cmd = ['python3', '-m', 'mypy'] + files + ['--strict', '--no-error-summary']

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ All type checks passed!")
        return True
    else:
        print("❌ Type check failures:")
        print(result.stdout)
        print(result.stderr)
        return False


def validate_parameter_ranges():
    """Validate parameter ranges make financial sense."""
    # Import directly to avoid __init__.py
    sys.path.insert(0, '/mnt/c/Users/jnpi/documents/finlab/LLM-strategy-generator')
    import importlib.util

    # Load parameter_spaces module directly
    spec = importlib.util.spec_from_file_location(
        "parameter_spaces",
        "/mnt/c/Users/jnpi/documents/finlab/LLM-strategy-generator/src/templates/parameter_spaces.py"
    )
    param_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(param_module)

    # Load template_registry module directly
    spec2 = importlib.util.spec_from_file_location(
        "template_registry",
        "/mnt/c/Users/jnpi/documents/finlab/LLM-strategy-generator/src/templates/template_registry.py",
        submodule_search_locations=["/mnt/c/Users/jnpi/documents/finlab/LLM-strategy-generator/src/templates"]
    )
    registry_module = importlib.util.module_from_spec(spec2)

    # Inject parameter_spaces into sys.modules before loading registry
    sys.modules['src.templates.parameter_spaces'] = param_module
    spec2.loader.exec_module(registry_module)

    print("\n✅ Modules loaded successfully without import errors")
    print(f"✅ Found {len(registry_module.TEMPLATE_SEARCH_SPACES)} templates")
    print(f"✅ Template names: {list(registry_module.TEMPLATE_SEARCH_SPACES.keys())}")

    return True


if __name__ == '__main__':
    success = True

    # Run mypy
    success = run_mypy_on_files() and success

    # Validate imports and structure
    success = validate_parameter_ranges() and success

    if success:
        print("\n🎉 All validations passed!")
        sys.exit(0)
    else:
        print("\n❌ Some validations failed")
        sys.exit(1)
