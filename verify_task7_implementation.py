#!/usr/bin/env python3
"""
Verification script for Task 7 implementation.

Demonstrates InnovationEngine YAML mode integration:
- Mode selection (full_code vs yaml)
- YAML extraction from different formats
- Statistics tracking by mode
- Backward compatibility
"""

from src.innovation.innovation_engine import InnovationEngine


def verify_mode_initialization():
    """Verify mode initialization and component setup."""
    print("=" * 80)
    print("1. Verifying Mode Initialization")
    print("=" * 80)

    # Test YAML mode
    print("\n✓ Testing YAML mode initialization...")
    yaml_engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='yaml'
    )
    assert yaml_engine.generation_mode == 'yaml'
    assert yaml_engine.structured_prompt_builder is not None
    assert yaml_engine.yaml_generator is not None
    print("  YAML mode: ✅ StructuredPromptBuilder and YAMLToCodeGenerator initialized")

    # Test full code mode
    print("\n✓ Testing full code mode initialization...")
    code_engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='full_code'
    )
    assert code_engine.generation_mode == 'full_code'
    assert code_engine.structured_prompt_builder is None
    assert code_engine.yaml_generator is None
    print("  Full code mode: ✅ YAML components not initialized")

    # Test default mode
    print("\n✓ Testing default mode (backward compatibility)...")
    default_engine = InnovationEngine(provider_name='gemini')
    assert default_engine.generation_mode == 'full_code'
    assert default_engine.structured_prompt_builder is None
    print("  Default mode: ✅ Defaults to full_code")

    print("\n✅ Mode initialization verified!\n")


def verify_yaml_extraction():
    """Verify YAML extraction from different response formats."""
    print("=" * 80)
    print("2. Verifying YAML Extraction Logic")
    print("=" * 80)

    engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='yaml'
    )

    # Test 1: YAML in ```yaml block
    print("\n✓ Testing extraction from ```yaml block...")
    yaml_content = "metadata:\n  name: test\n  description: Test strategy"
    response1 = f"Here's the strategy:\n\n```yaml\n{yaml_content}\n```\n\nThat's it."
    extracted1 = engine._extract_yaml(response1)
    assert extracted1 == yaml_content
    print("  ✅ Extracted from ```yaml block")

    # Test 2: YAML in generic ``` block
    print("\n✓ Testing extraction from generic ``` block...")
    response2 = f"```\n{yaml_content}\n```"
    extracted2 = engine._extract_yaml(response2)
    assert extracted2 == yaml_content
    print("  ✅ Extracted from generic ``` block")

    # Test 3: YAML without code blocks
    print("\n✓ Testing extraction without code blocks...")
    response3 = f"Here is the strategy:\n\n{yaml_content}\n\nEnd of strategy."
    extracted3 = engine._extract_yaml(response3)
    assert yaml_content in extracted3
    print("  ✅ Extracted from plain text")

    print("\n✅ YAML extraction verified!\n")


def verify_statistics_tracking():
    """Verify statistics tracking for different modes."""
    print("=" * 80)
    print("3. Verifying Statistics Tracking")
    print("=" * 80)

    # YAML mode statistics
    print("\n✓ Testing YAML mode statistics...")
    yaml_engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='yaml'
    )
    yaml_stats = yaml_engine.get_statistics()

    assert yaml_stats['generation_mode'] == 'yaml'
    assert 'yaml_successes' in yaml_stats
    assert 'yaml_failures' in yaml_stats
    assert 'yaml_validation_failures' in yaml_stats
    assert 'yaml_success_rate' in yaml_stats
    print("  ✅ YAML mode includes mode-specific statistics")

    # Full code mode statistics
    print("\n✓ Testing full code mode statistics...")
    code_engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='full_code'
    )
    code_stats = code_engine.get_statistics()

    assert code_stats['generation_mode'] == 'full_code'
    assert 'yaml_successes' not in code_stats
    assert 'yaml_failures' not in code_stats
    print("  ✅ Full code mode excludes YAML statistics")

    print("\n✅ Statistics tracking verified!\n")


def verify_backward_compatibility():
    """Verify backward compatibility with existing code."""
    print("=" * 80)
    print("4. Verifying Backward Compatibility")
    print("=" * 80)

    print("\n✓ Testing default behavior unchanged...")
    engine = InnovationEngine(provider_name='gemini')

    # Verify default mode
    assert engine.generation_mode == 'full_code'
    print("  ✅ Default mode is full_code")

    # Verify YAML components not initialized
    assert engine.structured_prompt_builder is None
    assert engine.yaml_generator is None
    print("  ✅ YAML components not initialized by default")

    # Verify existing methods work
    stats = engine.get_statistics()
    assert 'generation_mode' in stats
    assert stats['generation_mode'] == 'full_code'
    print("  ✅ get_statistics() works")

    engine.reset_statistics()
    assert engine.total_attempts == 0
    print("  ✅ reset_statistics() works")

    print("\n✅ Backward compatibility verified!\n")


def verify_reset_statistics():
    """Verify statistics reset includes YAML fields."""
    print("=" * 80)
    print("5. Verifying Statistics Reset")
    print("=" * 80)

    print("\n✓ Testing reset clears YAML statistics...")
    engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='yaml'
    )

    # Set some statistics
    engine.yaml_successes = 5
    engine.yaml_failures = 3
    engine.yaml_validation_failures = 2

    # Reset
    engine.reset_statistics()

    # Verify reset
    assert engine.yaml_successes == 0
    assert engine.yaml_failures == 0
    assert engine.yaml_validation_failures == 0
    print("  ✅ YAML statistics cleared")

    print("\n✅ Statistics reset verified!\n")


def main():
    """Run all verification tests."""
    print("\n" + "=" * 80)
    print("TASK 7 IMPLEMENTATION VERIFICATION")
    print("InnovationEngine YAML Mode Integration")
    print("=" * 80 + "\n")

    try:
        verify_mode_initialization()
        verify_yaml_extraction()
        verify_statistics_tracking()
        verify_backward_compatibility()
        verify_reset_statistics()

        print("=" * 80)
        print("ALL VERIFICATIONS PASSED ✅")
        print("=" * 80)
        print("\nTask 7 Implementation Summary:")
        print("- ✅ YAML mode initialization")
        print("- ✅ Full code mode initialization")
        print("- ✅ Default mode (backward compatible)")
        print("- ✅ YAML extraction from multiple formats")
        print("- ✅ Mode-specific statistics tracking")
        print("- ✅ Statistics reset includes YAML fields")
        print("- ✅ Backward compatibility maintained")
        print("\nImplementation is complete and ready for use!")
        print("=" * 80 + "\n")

        return 0

    except AssertionError as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
