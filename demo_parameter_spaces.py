#!/usr/bin/env python3
"""
Demo script to show parameter search space output examples.
"""

import sys
import optuna
import importlib.util
import json


def load_modules():
    """Load modules without __init__.py imports."""
    # Load parameter_spaces
    spec = importlib.util.spec_from_file_location(
        "parameter_spaces",
        "/mnt/c/Users/jnpi/documents/finlab/LLM-strategy-generator/src/templates/parameter_spaces.py"
    )
    param_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(param_module)

    # Load template_registry
    spec2 = importlib.util.spec_from_file_location(
        "template_registry",
        "/mnt/c/Users/jnpi/documents/finlab/LLM-strategy-generator/src/templates/template_registry.py"
    )
    registry_module = importlib.util.module_from_spec(spec2)

    # Inject parameter_spaces into sys.modules
    sys.modules['src.templates.parameter_spaces'] = param_module
    spec2.loader.exec_module(registry_module)

    return param_module, registry_module


def demo_template_search_space(template_name, search_space_fn):
    """Demonstrate a template's search space with 3 sample trials."""
    print(f"\n{'='*70}")
    print(f"Template: {template_name}")
    print(f"{'='*70}")

    study = optuna.create_study(direction='maximize', sampler=optuna.samplers.RandomSampler(seed=42))

    for i in range(3):
        trial = study.ask()
        params = search_space_fn(trial)

        print(f"\nSample {i+1}:")
        print(json.dumps(params, indent=2))

        # Count parameters
        if i == 0:
            print(f"\nParameter count: {len(params)}")
            print(f"Parameter names: {list(params.keys())}")


def main():
    """Run demo for all templates."""
    param_module, registry_module = load_modules()

    print("="*70)
    print("PARAMETER SEARCH SPACE DEMO")
    print("="*70)
    print(f"\nTotal templates: {len(registry_module.TEMPLATE_SEARCH_SPACES)}")
    print(f"Template names: {list(registry_module.TEMPLATE_SEARCH_SPACES.keys())}")

    # Demo each template
    for template_name, search_space_fn in registry_module.TEMPLATE_SEARCH_SPACES.items():
        demo_template_search_space(template_name, search_space_fn)

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    # Count total parameters across all templates
    study = optuna.create_study(direction='maximize')
    total_params = 0
    for template_name, search_space_fn in registry_module.TEMPLATE_SEARCH_SPACES.items():
        trial = study.ask()
        params = search_space_fn(trial)
        param_count = len(params)
        total_params += param_count
        print(f"{template_name}: {param_count} parameters")

    print(f"\nTotal parameters across all templates: {total_params}")
    print(f"Average parameters per template: {total_params / len(registry_module.TEMPLATE_SEARCH_SPACES):.1f}")


if __name__ == '__main__':
    main()
