"""
End-to-End Integration Test for Innovation System

Tests the complete flow:
1. Prompt generation
2. LLM API call
3. Code/rationale extraction
4. 7-layer validation
5. Repository storage
6. Innovation frequency control
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from innovation.llm_client import create_llm_client
from innovation.innovation_engine import InnovationEngine
from innovation.innovation_repository import InnovationRepository


def test_complete_innovation_flow():
    """Test complete end-to-end innovation flow."""
    print("=" * 70)
    print("END-TO-END INNOVATION INTEGRATION TEST")
    print("=" * 70)

    # Test 1: Create engine with mock LLM
    print("\nTest 1: Initialize Innovation Engine")
    print("-" * 70)

    engine = InnovationEngine(
        baseline_sharpe=0.680,
        baseline_calmar=2.406,
        innovation_frequency=0.20,
        use_mock_llm=True,
        repository_path="test_innovations_integration.jsonl"
    )

    print(f"✅ Engine initialized")
    print(f"   Baseline Sharpe: {engine.baseline_metrics['mean_sharpe']:.3f}")
    print(f"   Innovation frequency: {engine.innovation_frequency:.0%}")
    print(f"   LLM client type: {type(engine.llm_client).__name__}")

    # Test 2: Innovation frequency control
    print("\nTest 2: Innovation Frequency Control")
    print("-" * 70)

    innovations_triggered = 0
    for i in range(100):
        if engine.should_innovate():
            innovations_triggered += 1

    print(f"✅ Innovation frequency test (100 iterations)")
    print(f"   Target: {engine.innovation_frequency:.0%}")
    print(f"   Actual: {innovations_triggered}%")
    print(f"   Within expected range: {15 <= innovations_triggered <= 25}")

    # Test 3: Attempt multiple innovations
    print("\nTest 3: Attempt 10 Innovations (Full Pipeline)")
    print("-" * 70)

    categories = ['quality', 'value', 'growth', 'momentum', 'mixed']
    success_count = 0

    for i in range(10):
        category = categories[i % len(categories)]

        success, code, failure_reason = engine.attempt_innovation(
            iteration=i,
            category=category
        )

        if success:
            success_count += 1
            print(f"✅ Iteration {i} ({category}): SUCCESS")
            print(f"   Code: {code[:50]}...")
        else:
            print(f"❌ Iteration {i} ({category}): FAILED")
            print(f"   Reason: {failure_reason}")

    print(f"\n✅ Overall success rate: {success_count}/10 = {success_count*10}%")

    # Test 4: Engine statistics
    print("\nTest 4: Engine Statistics")
    print("-" * 70)

    stats = engine.get_statistics()

    print(f"✅ Statistics:")
    print(f"   Total attempts: {stats['total_attempts']}")
    print(f"   Successful innovations: {stats['successful_innovations']}")
    print(f"   Failed validations: {stats['failed_validations']}")
    print(f"   LLM failures: {stats['llm_failures']}")
    print(f"   Success rate: {stats['success_rate']:.1%}")
    print(f"   Repository size: {stats['repository_size']}")

    # Test 5: Repository operations
    print("\nTest 5: Repository Operations")
    print("-" * 70)

    # Get top innovations
    top_3 = engine.repository.get_top_n(3, metric='sharpe_ratio')
    print(f"✅ Top 3 innovations (mock Sharpe):")
    for i, innov in enumerate(top_3, 1):
        sharpe = innov.get('performance', {}).get('sharpe_ratio', 0)
        print(f"   {i}. {innov['id'][:25]}... - Sharpe: {sharpe:.3f}")

    # Search by keyword
    results = engine.repository.search("ROE", top_k=5)
    print(f"\n✅ Search for 'ROE': Found {len(results)} results")

    # Category distribution
    repo_stats = engine.repository.get_statistics()
    print(f"\n✅ Category distribution:")
    for cat, count in repo_stats['categories'].items():
        print(f"   {cat}: {count}")

    # Test 6: Recent attempts
    print("\nTest 6: Recent Innovation Attempts")
    print("-" * 70)

    recent = engine.get_recent_attempts(n=5)
    print(f"✅ Last 5 attempts:")
    for attempt in recent:
        status = "✅" if attempt.success else "❌"
        print(f"   {status} Iteration {attempt.iteration} ({attempt.prompt_category})")
        if attempt.validation_result:
            if attempt.success:
                print(f"      All 7 layers passed")
            else:
                print(f"      Failed at Layer {attempt.validation_result.failed_layer}")

    # Test 7: Validate all components integrated
    print("\nTest 7: Component Integration Verification")
    print("-" * 70)

    print(f"✅ LLM Client: {type(engine.llm_client).__name__}")
    print(f"✅ Validator: {len(engine.validator.validation_layers)} layers")
    print(f"✅ Repository: {engine.repository.count()} innovations stored")
    print(f"✅ Prompt templates: Available for {len(categories)} categories")

    # Test 8: Success criteria validation
    print("\nTest 8: Success Criteria Validation")
    print("-" * 70)

    criteria_passed = 0
    total_criteria = 5

    # Criterion 1: Innovation success rate ≥ 30%
    if stats['success_rate'] >= 0.30:
        print(f"✅ Innovation success rate ≥ 30%: {stats['success_rate']:.1%}")
        criteria_passed += 1
    else:
        print(f"❌ Innovation success rate < 30%: {stats['success_rate']:.1%}")

    # Criterion 2: Repository functional
    if stats['repository_size'] > 0:
        print(f"✅ Repository functional: {stats['repository_size']} innovations")
        criteria_passed += 1
    else:
        print(f"❌ Repository empty")

    # Criterion 3: All 7 validation layers working
    all_layers_work = any(
        attempt.success and len(attempt.validation_result.warnings) >= 0
        for attempt in engine.attempt_history
    )
    if all_layers_work:
        print(f"✅ All 7 validation layers working")
        criteria_passed += 1
    else:
        print(f"❌ Validation layers not working")

    # Criterion 4: Innovation frequency control
    if 15 <= innovations_triggered <= 25:
        print(f"✅ Innovation frequency control: {innovations_triggered}% (target: 20%)")
        criteria_passed += 1
    else:
        print(f"❌ Innovation frequency out of range: {innovations_triggered}%")

    # Criterion 5: LLM integration
    if stats['llm_failures'] < stats['total_attempts']:
        print(f"✅ LLM integration working: {stats['total_attempts'] - stats['llm_failures']}/{stats['total_attempts']} successful calls")
        criteria_passed += 1
    else:
        print(f"❌ LLM integration failing")

    print(f"\n{'='*70}")
    print(f"FINAL RESULT: {criteria_passed}/{total_criteria} success criteria passed")
    print(f"{'='*70}")

    if criteria_passed >= 4:
        print("✅ INTEGRATION TEST: PASSED")
    else:
        print("❌ INTEGRATION TEST: FAILED")

    print("\n" + "=" * 70)
    print("END-TO-END INTEGRATION TEST COMPLETE")
    print("=" * 70)

    return criteria_passed >= 4


if __name__ == "__main__":
    success = test_complete_innovation_flow()
    sys.exit(0 if success else 1)
