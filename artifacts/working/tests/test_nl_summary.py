#!/usr/bin/env python3
"""
Test script for create_nl_summary() function.

This script tests the NL summary generator with real iteration data
from iteration_history.json to verify:
1. Summary is specific and cites actual metrics
2. Feedback is actionable with concrete suggestions
3. Historical comparison works correctly
4. Feedback quality is balanced (strengths + weaknesses)
"""

import json
import sys
from typing import Dict, Any

# Import the function we're testing
from iteration_engine import create_nl_summary


def load_test_data() -> list:
    """Load real iteration data from history file."""
    try:
        with open("iteration_history.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("records", [])
    except FileNotFoundError:
        print("❌ Error: iteration_history.json not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Failed to parse JSON: {e}")
        sys.exit(1)


def test_nl_summary_with_real_data():
    """Test NL summary generation with real iteration data."""
    print("=" * 70)
    print("🧪 Testing NL Summary Generator")
    print("=" * 70)
    print()

    # Load test data
    records = load_test_data()

    if not records:
        print("❌ No iteration records found")
        return False

    print(f"✅ Loaded {len(records)} iteration records")
    print()

    # Test with different iterations
    test_cases = [
        (0, "First iteration (no history)"),
        (1, "Second iteration (with history)"),
        (min(5, len(records) - 1), "Mid iteration (with history)")
    ]

    for iteration_num, description in test_cases:
        if iteration_num >= len(records):
            continue

        print("=" * 70)
        print(f"Test Case: {description}")
        print(f"Iteration: {iteration_num}")
        print("=" * 70)
        print()

        # Get iteration data
        record = records[iteration_num]
        metrics = record.get("metrics", {})
        code = record.get("code", "")

        # Generate summary
        try:
            feedback = create_nl_summary(metrics, code, iteration_num)

            # Display summary
            print("📝 Generated Feedback:")
            print("-" * 70)
            print(feedback)
            print("-" * 70)
            print()

            # Validate feedback quality
            print("🔍 Quality Checks:")
            checks_passed = 0
            total_checks = 6

            # Check 1: Non-empty
            if feedback and len(feedback) > 100:
                print("✅ Feedback is substantive (>100 chars)")
                checks_passed += 1
            else:
                print("❌ Feedback is too short or empty")

            # Check 2: Contains metrics
            if any(str(metrics.get(m, 0)) in feedback for m in ["sharpe_ratio", "total_return", "max_drawdown"]):
                print("✅ Contains specific metrics")
                checks_passed += 1
            else:
                print("❌ Missing specific metrics")

            # Check 3: Has sections
            required_sections = ["Performance Summary", "What Worked", "What Didn't Work", "Suggestions"]
            sections_found = sum(1 for s in required_sections if s in feedback)
            if sections_found >= 3:
                print(f"✅ Has {sections_found}/{len(required_sections)} required sections")
                checks_passed += 1
            else:
                print(f"❌ Missing sections ({sections_found}/{len(required_sections)})")

            # Check 4: Actionable suggestions
            if "**" in feedback or any(word in feedback for word in ["Consider", "Try", "Add", "Improve"]):
                print("✅ Contains actionable suggestions")
                checks_passed += 1
            else:
                print("❌ Missing actionable suggestions")

            # Check 5: Balanced (has both positives and negatives)
            has_positive = any(emoji in feedback for emoji in ["✅", "EXCELLENT", "GOOD"])
            has_negative = any(emoji in feedback for emoji in ["⚠️", "POOR", "needs improvement"])
            if has_positive and has_negative:
                print("✅ Balanced feedback (positives + negatives)")
                checks_passed += 1
            else:
                print("❌ Unbalanced feedback")

            # Check 6: Historical comparison (for iterations > 0)
            if iteration_num > 0:
                if "Historical Context" in feedback or "Previous Iteration" in feedback:
                    print("✅ Includes historical comparison")
                    checks_passed += 1
                else:
                    print("❌ Missing historical comparison")
            else:
                print("✅ No historical comparison needed (first iteration)")
                checks_passed += 1

            # Summary
            score = (checks_passed / total_checks) * 100
            print()
            print(f"🎯 Quality Score: {checks_passed}/{total_checks} ({score:.0f}%)")

            if score >= 80:
                print("✅ PASS - High quality feedback")
            elif score >= 60:
                print("⚠️  MARGINAL - Acceptable but could improve")
            else:
                print("❌ FAIL - Feedback quality below standards")

            print()

        except Exception as e:
            print(f"❌ Error generating feedback: {e}")
            import traceback
            traceback.print_exc()
            return False

    return True


def test_edge_cases():
    """Test edge cases and error handling."""
    print("=" * 70)
    print("🧪 Testing Edge Cases")
    print("=" * 70)
    print()

    # Test 1: Empty metrics
    print("Test 1: Empty metrics")
    try:
        feedback = create_nl_summary({}, "# No code", 0)
        if feedback:
            print("✅ Handles empty metrics gracefully")
        else:
            print("❌ Returns empty feedback for empty metrics")
    except Exception as e:
        print(f"❌ Error with empty metrics: {e}")

    # Test 2: Missing optional fields
    print("\nTest 2: Missing optional fields")
    try:
        minimal_metrics = {
            "sharpe_ratio": 1.2,
            "total_return": 0.3
        }
        feedback = create_nl_summary(minimal_metrics, "# Minimal code", 0)
        if feedback:
            print("✅ Handles missing optional fields")
        else:
            print("❌ Fails with minimal metrics")
    except Exception as e:
        print(f"❌ Error with minimal metrics: {e}")

    # Test 3: Very long code
    print("\nTest 3: Very long code (>10KB)")
    try:
        long_code = "# " + "A" * 10000
        feedback = create_nl_summary({"sharpe_ratio": 1.0}, long_code, 0)
        if feedback:
            print("✅ Handles long code efficiently")
        else:
            print("❌ Fails with long code")
    except Exception as e:
        print(f"❌ Error with long code: {e}")

    print()


if __name__ == "__main__":
    print("\n🚀 Natural Language Summary Generator Test Suite\n")

    # Run main tests
    success = test_nl_summary_with_real_data()

    # Run edge case tests
    test_edge_cases()

    print()
    print("=" * 70)
    if success:
        print("✅ All tests completed successfully")
    else:
        print("❌ Some tests failed")
    print("=" * 70)
    print()
