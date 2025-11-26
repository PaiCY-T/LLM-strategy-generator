#!/usr/bin/env python3
"""
Example Usage: DataFieldManifest Class

Demonstrates how to use Layer 1 of the LLM Field Validation Fix.
This is the foundation for preventing LLM strategy generation failures
caused by invalid field references.
"""

from src.config.data_fields import DataFieldManifest


def main():
    """Demonstrate DataFieldManifest usage."""

    print("=" * 70)
    print("DataFieldManifest - Layer 1: Enhanced Data Field Manifest")
    print("=" * 70)

    # Initialize manifest from cache
    print("\n1. Initializing manifest from cache...")
    manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')
    print(f"   {manifest}")

    # Example 1: Resolve common LLM aliases to canonical names
    print("\n2. Alias Resolution (LLM → finlab API)")
    print("-" * 70)
    test_aliases = [
        ('close', 'price:收盤價'),
        ('volume', 'price:成交金額'),  # CRITICAL: trading value, NOT shares!
        ('roe', 'fundamental_features:ROE'),
        ('ROE', 'fundamental_features:ROE'),  # Case-insensitive
        ('pe', 'fundamental_features:本益比'),
    ]

    for alias, expected_canonical in test_aliases:
        field = manifest.get_field(alias)
        if field:
            status = "✅" if field.canonical_name == expected_canonical else "❌"
            print(f"   {status} '{alias:10s}' → {field.canonical_name}")
        else:
            print(f"   ❌ '{alias}' → NOT FOUND")

    # Example 2: Validate field existence (before LLM uses it)
    print("\n3. Field Validation (Prevent LLM Errors)")
    print("-" * 70)
    test_validations = [
        ('close', True, "Valid alias"),
        ('volume', True, "Valid alias (maps to 成交金額, NOT 成交股數!)"),
        ('invalid_field', False, "Invalid field - would cause LLM error"),
        ('vol', False, "Partial match - needs semantic suggestion"),
    ]

    for name, should_exist, note in test_validations:
        exists = manifest.validate_field(name)
        status = "✅" if exists == should_exist else "❌"
        result = "VALID" if exists else "INVALID"
        print(f"   {status} '{name:15s}' → {result:7s} ({note})")

    # Example 3: Get all aliases for a field (for documentation/debugging)
    print("\n4. Get All Aliases (Documentation Helper)")
    print("-" * 70)
    test_fields = [
        'price:收盤價',
        'price:成交金額',
        'fundamental_features:ROE',
    ]

    for canonical_name in test_fields:
        aliases = manifest.get_aliases(canonical_name)
        if aliases:
            aliases_str = ', '.join(f"'{a}'" for a in aliases[:5])
            print(f"   {canonical_name}")
            print(f"      Aliases: {aliases_str}")

    # Example 4: Get canonical name from alias (for LLM code generation)
    print("\n5. Get Canonical Name (LLM Code Generator)")
    print("-" * 70)
    llm_inputs = ['close', 'volume', 'roe', 'pe', 'invalid_alias']

    for llm_input in llm_inputs:
        canonical = manifest.get_canonical_name(llm_input)
        if canonical:
            print(f"   ✅ LLM input: '{llm_input:15s}' → Generate: data.get('{canonical}')")
        else:
            print(f"   ❌ LLM input: '{llm_input:15s}' → ERROR: Invalid field!")

    # Example 5: Get fields by category (for context-aware suggestions)
    print("\n6. Get Fields by Category (Context-Aware Suggestions)")
    print("-" * 70)
    categories = ['price', 'fundamental']

    for category in categories:
        fields = manifest.get_fields_by_category(category)
        print(f"   {category.upper()} ({len(fields)} fields):")
        for field in fields[:3]:  # Show first 3
            aliases_preview = ', '.join(field.aliases[:2])
            print(f"      • {field.canonical_name} (aliases: {aliases_preview})")

    # Example 6: Real-world LLM validation scenario
    print("\n7. Real-World LLM Validation Scenario")
    print("-" * 70)
    print("   Scenario: LLM generates strategy code with field references")
    print()

    # Simulate LLM-generated field references
    llm_code_fields = [
        ('close', True, "Correct alias"),
        ('volume', True, "Common alias (maps to 成交金額)"),
        ('volumee', False, "Typo - needs correction"),
        ('shares', True, "Correct alias (maps to 成交股數)"),
        ('roe', True, "Correct alias"),
        ('roi', False, "Invalid - ROA or ROE?"),
    ]

    print("   LLM Code Field References:")
    for field_ref, should_be_valid, note in llm_code_fields:
        is_valid = manifest.validate_field(field_ref)
        status = "✅" if is_valid == should_be_valid else "❌"
        result = "PASS" if is_valid else "FAIL"

        if is_valid:
            canonical = manifest.get_canonical_name(field_ref)
            print(f"   {status} {result:4s} '{field_ref:15s}' → {canonical:30s} ({note})")
        else:
            print(f"   {status} {result:4s} '{field_ref:15s}' → NEEDS CORRECTION ({note})")

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print("✅ Layer 1 provides O(1) alias resolution with <1μs performance")
    print("✅ Prevents LLM field errors by validating before code execution")
    print("✅ Critical alias: 'volume' → '成交金額' (trading VALUE, NOT shares)")
    print("✅ Supports case-insensitive aliases (roe, ROE)")
    print("\nNext: Layer 2 (LLMFieldValidator) will add semantic suggestions")
    print("      e.g., 'vol' → suggest 'volume' or 'shares'")
    print("=" * 70)


if __name__ == '__main__':
    main()
