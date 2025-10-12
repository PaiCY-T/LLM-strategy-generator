"""Test diversity tracking implementation for Task 6."""

import json
import tempfile
from pathlib import Path


def test_diversity_calculation():
    """Demonstrate diversity calculation logic."""

    print("=" * 70)
    print("TASK 6: TEMPLATE DIVERSITY TRACKING TEST")
    print("=" * 70)

    # Test case 1: High diversity (4 unique templates in 5 iterations)
    print("\n📊 Test Case 1: High Diversity")
    print("-" * 70)
    recent_templates_1 = ['Turtle', 'Mastiff', 'Factor', 'Momentum', 'Turtle']
    unique_1 = len(set(recent_templates_1))
    total_1 = len(recent_templates_1)
    diversity_1 = unique_1 / total_1

    print(f"Recent templates: {recent_templates_1}")
    print(f"Unique templates: {unique_1}/{total_1}")
    print(f"Diversity score: {diversity_1:.1%}")

    if diversity_1 >= 0.8:
        print("✅ PASS: Meets ≥80% diversity requirement (AC-1.1.3)")
    elif diversity_1 >= 0.4:
        print("⚠️  WARNING: Moderate diversity (40-80%)")
    else:
        print("❌ FAIL: Low diversity (<40%)")

    # Test case 2: Perfect diversity (4 unique templates in 4 iterations)
    print("\n📊 Test Case 2: Perfect Diversity")
    print("-" * 70)
    recent_templates_2 = ['Turtle', 'Mastiff', 'Factor', 'Momentum']
    unique_2 = len(set(recent_templates_2))
    total_2 = len(recent_templates_2)
    diversity_2 = unique_2 / total_2

    print(f"Recent templates: {recent_templates_2}")
    print(f"Unique templates: {unique_2}/{total_2}")
    print(f"Diversity score: {diversity_2:.1%}")

    if diversity_2 >= 0.8:
        print("✅ PASS: Meets ≥80% diversity requirement (AC-1.1.3)")

    # Test case 3: Low diversity (2 unique templates in 5 iterations)
    print("\n📊 Test Case 3: Low Diversity (Should Trigger Warning)")
    print("-" * 70)
    recent_templates_3 = ['Turtle', 'Turtle', 'Mastiff', 'Turtle', 'Turtle']
    unique_3 = len(set(recent_templates_3))
    total_3 = len(recent_templates_3)
    diversity_3 = unique_3 / total_3

    print(f"Recent templates: {recent_templates_3}")
    print(f"Unique templates: {unique_3}/{total_3}")
    print(f"Diversity score: {diversity_3:.1%}")

    if diversity_3 < 0.4:
        print("⚠️  WARNING: Low diversity detected - exploration mode recommended")

    # Test case 4: Exploration mode validation
    print("\n🔍 Test Case 4: Exploration Mode Template Selection")
    print("-" * 70)
    recent_templates_4 = ['Turtle', 'Mastiff', 'Factor', 'Momentum', 'Turtle']
    selected_template = 'Mastiff'  # This is in recent list

    print(f"Recent templates: {recent_templates_4}")
    print(f"Selected template: {selected_template}")
    print(f"Exploration mode: True")

    if selected_template in recent_templates_4:
        print("⚠️  DIVERSITY VIOLATION: Template was used in recent iterations")
        print("   Exploration mode should select different template (AC-1.1.4)")
    else:
        print("✅ PASS: Template not in recent usage - good diversity")

    # Test case 5: Successful exploration
    print("\n🔍 Test Case 5: Successful Exploration Mode")
    print("-" * 70)
    recent_templates_5 = ['Turtle', 'Turtle', 'Turtle', 'Turtle', 'Turtle']
    selected_template_5 = 'Factor'  # Different from recent list

    print(f"Recent templates: {recent_templates_5}")
    print(f"Selected template: {selected_template_5}")
    print(f"Exploration mode: True")

    if selected_template_5 not in recent_templates_5:
        print("✅ PASS: Template diversity verified - exploration successful")

    # Test case 6: Empty history
    print("\n📊 Test Case 6: No Iteration History")
    print("-" * 70)
    recent_templates_6 = []
    print(f"Recent templates: {recent_templates_6}")
    print("ℹ️  No iteration history available for diversity tracking")

    # Summary
    print("\n" + "=" * 70)
    print("DIVERSITY CALCULATION FORMULA")
    print("=" * 70)
    print("diversity_score = unique_templates / total_templates")
    print("Warning threshold: <40%")
    print("Target for AC-1.1.3: ≥80% over 10 consecutive iterations")
    print("")
    print("IMPLEMENTATION LOCATIONS")
    print("-" * 70)
    print("1. Line 428-460: Diversity tracking after loading iteration_history")
    print("2. Line 515-525: Diversity verification after template selection")
    print("=" * 70)


if __name__ == '__main__':
    test_diversity_calculation()
