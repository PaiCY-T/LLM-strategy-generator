"""Test AST validator against generated strategies."""

from validate_code import validate_code

# Test all generated strategies
strategy_files = [
    'generated_strategy_iter0.py',
    'generated_strategy_iter1.py',
    'generated_strategy_iter2.py',
    'generated_strategy_iter3.py',
    'generated_strategy_iter4.py',
]

print("Validating generated strategies...\n")

for filename in strategy_files:
    try:
        with open(filename, 'r') as f:
            code = f.read()

        is_valid, errors = validate_code(code)

        if is_valid:
            print(f"✅ {filename}: VALID")
        else:
            print(f"❌ {filename}: INVALID")
            for error in errors:
                print(f"   - {error}")
    except FileNotFoundError:
        print(f"⚠️  {filename}: File not found")
    except Exception as e:
        print(f"❌ {filename}: Error reading file - {e}")

    print()

print("Validation complete.")
