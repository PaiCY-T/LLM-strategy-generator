#!/usr/bin/env python3
"""
Demo: Generate example feedback from real iteration data.

This demonstrates the quality and usefulness of the NL summary generator.
"""

import json
from iteration_engine import create_nl_summary


def main():
    # Load a real iteration
    with open("iteration_history.json", "r") as f:
        data = json.load(f)

    records = data.get("records", [])

    # Pick iteration 5 (has good mix of strengths/weaknesses)
    iteration_num = 5
    record = records[iteration_num]

    metrics = record.get("metrics", {})
    code = record.get("code", "")

    print("=" * 70)
    print(f"EXAMPLE FEEDBACK - Iteration {iteration_num}")
    print("=" * 70)
    print()
    print("INPUT METRICS:")
    print(json.dumps(metrics, indent=2))
    print()
    print("=" * 70)
    print("GENERATED FEEDBACK (for Claude):")
    print("=" * 70)
    print()

    feedback = create_nl_summary(metrics, code, iteration_num)
    print(feedback)
    print()
    print("=" * 70)
    print()

    # Count sections
    sections = ["Performance Summary", "What Worked", "What Didn't Work", "Suggestions"]
    sections_found = [s for s in sections if s in feedback]
    print(f"✅ Sections: {len(sections_found)}/4")
    print(f"✅ Length: {len(feedback)} characters")
    print(f"✅ Lines: {len(feedback.split(chr(10)))}")

    # Check actionability
    suggestions = [line for line in feedback.split("\n") if line.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "11."))]
    print(f"✅ Actionable suggestions: {len(suggestions)}")

    print()


if __name__ == "__main__":
    main()
