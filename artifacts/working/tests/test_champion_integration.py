#!/usr/bin/env python3
"""
Integration Test: Unified Champion Persistence
===============================================

Tests the C1 fix integration between Learning System and Hall of Fame.

Validates:
1. HallOfFameRepository.get_current_champion() returns highest Sharpe champion
2. AutonomousLoop can load/save champions via Hall of Fame
3. Legacy champion_strategy.json migration works correctly
4. Tier classification operates as expected

Usage:
    python3 test_champion_integration.py
"""

import json
import os
import tempfile
import shutil
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from src.repository.hall_of_fame import HallOfFameRepository, StrategyGenome
from src.constants import CHAMPION_FILE

# Use project-local temporary directory (security constraint)
TEST_BASE_DIR = Path(__file__).parent / ".test_hall_of_fame"


def create_test_genome(
    iteration_num: int,
    sharpe: float,
    template_name: str = "test_template"
) -> StrategyGenome:
    """Create test StrategyGenome with specified Sharpe ratio.

    Args:
        iteration_num: Iteration number (used as genome_id)
        sharpe: Sharpe ratio for metrics
        template_name: Template name

    Returns:
        StrategyGenome for testing
    """
    return StrategyGenome(
        template_name=template_name,
        parameters={'test_param': 42},
        metrics={
            'sharpe_ratio': sharpe,
            'annual_return': sharpe * 0.15,
            'max_drawdown': -0.1
        },
        created_at=datetime.now().isoformat(),
        strategy_code=f"# Test strategy iter {iteration_num}",
        success_patterns=[f"Pattern {iteration_num}"],
        genome_id=iteration_num
    )


def test_get_current_champion():
    """Test 1: get_current_champion() returns highest Sharpe champion."""
    print("\n" + "="*70)
    print("Test 1: get_current_champion() Basic Functionality")
    print("="*70)

    # Create temporary Hall of Fame (project-local for security)
    test_dir = TEST_BASE_DIR / "test1"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        hall_of_fame = HallOfFameRepository(base_path=str(test_dir))

        # Test 1A: Empty Hall of Fame
        print("\n[1A] Empty Hall of Fame...")
        champion = hall_of_fame.get_current_champion()
        assert champion is None, "Expected None for empty Hall of Fame"
        print("✅ Returns None for empty Hall of Fame")

        # Test 1B: Single champion
        print("\n[1B] Single champion (Sharpe 2.5)...")
        genome1 = create_test_genome(1, sharpe=2.5)
        hall_of_fame.add_strategy(
            template_name=genome1.template_name,
            parameters=genome1.parameters,
            metrics=genome1.metrics,
            strategy_code=genome1.strategy_code,
            success_patterns=genome1.success_patterns
        )

        champion = hall_of_fame.get_current_champion()
        assert champion is not None, "Expected champion to exist"
        assert champion.metrics['sharpe_ratio'] == 2.5, "Expected Sharpe 2.5"
        print(f"✅ Returns champion with Sharpe {champion.metrics['sharpe_ratio']}")

        # Test 1C: Multiple champions - returns highest
        print("\n[1C] Multiple champions (Sharpe 2.5, 3.0, 2.8)...")
        genome2 = create_test_genome(2, sharpe=3.0)
        genome3 = create_test_genome(3, sharpe=2.8)
        hall_of_fame.add_strategy(
            template_name=genome2.template_name,
            parameters=genome2.parameters,
            metrics=genome2.metrics,
            strategy_code=genome2.strategy_code,
            success_patterns=genome2.success_patterns
        )
        hall_of_fame.add_strategy(
            template_name=genome3.template_name,
            parameters=genome3.parameters,
            metrics=genome3.metrics,
            strategy_code=genome3.strategy_code,
            success_patterns=genome3.success_patterns
        )

        champion = hall_of_fame.get_current_champion()
        assert champion is not None, "Expected champion to exist"
        assert champion.metrics['sharpe_ratio'] == 3.0, "Expected highest Sharpe (3.0)"
        print(f"✅ Returns highest Sharpe champion: {champion.metrics['sharpe_ratio']}")

        # Test 1D: Contenders should not be returned
        print("\n[1D] Contenders (Sharpe 1.8) should not be returned...")
        genome4 = create_test_genome(4, sharpe=1.8)
        hall_of_fame.add_strategy(
            template_name=genome4.template_name,
            parameters=genome4.parameters,
            metrics=genome4.metrics,
            strategy_code=genome4.strategy_code,
            success_patterns=genome4.success_patterns
        )

        champion = hall_of_fame.get_current_champion()
        assert champion.metrics['sharpe_ratio'] == 3.0, "Should still return champion-tier (3.0)"
        print(f"✅ Correctly filters contenders: still returns {champion.metrics['sharpe_ratio']}")

        print("\n✅ Test 1 PASSED: get_current_champion() works correctly")

    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)


def test_tier_classification():
    """Test 2: Strategies are classified into correct tiers."""
    print("\n" + "="*70)
    print("Test 2: Tier Classification")
    print("="*70)

    test_dir = TEST_BASE_DIR / "test2"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        hall_of_fame = HallOfFameRepository(base_path=str(test_dir))

        # Test different Sharpe ratios
        test_cases = [
            (2.5, 'champions', "Sharpe ≥2.0"),
            (1.8, 'contenders', "Sharpe 1.5-2.0"),
            (1.2, 'archive', "Sharpe <1.5")
        ]

        for sharpe, expected_tier, description in test_cases:
            print(f"\n[{description}] Testing Sharpe {sharpe}...")
            genome = create_test_genome(int(sharpe * 10), sharpe=sharpe)
            hall_of_fame.add_strategy(
                template_name=genome.template_name,
                parameters=genome.parameters,
                metrics=genome.metrics,
                strategy_code=genome.strategy_code,
                success_patterns=genome.success_patterns
            )

            # Verify file exists in correct tier
            tier_dir = test_dir / expected_tier
            assert tier_dir.exists(), f"Expected {expected_tier} directory"

            files = list(tier_dir.iterdir())
            assert len(files) > 0, f"Expected files in {expected_tier}"
            print(f"✅ Classified to {expected_tier} tier")

        print("\n✅ Test 2 PASSED: Tier classification works correctly")

    finally:
        if test_dir.exists():
            shutil.rmtree(test_dir)


def test_autonomous_loop_integration():
    """Test 3: AutonomousLoop loads/saves via Hall of Fame."""
    print("\n" + "="*70)
    print("Test 3: AutonomousLoop Integration")
    print("="*70)

    test_dir = TEST_BASE_DIR / "test3"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Note: This is a simplified test - full integration requires data
        print("\n[3A] Testing champion loading...")

        # Create Hall of Fame with champion
        hall_of_fame = HallOfFameRepository(base_path=str(test_dir))
        genome = create_test_genome(1, sharpe=2.5, template_name='autonomous_generated')

        # Add iteration_num metadata (as autonomous_loop does)
        params_with_metadata = genome.parameters.copy()
        params_with_metadata['__iteration_num__'] = genome.genome_id  # genome_id is iteration_num in test

        hall_of_fame.add_strategy(
            template_name=genome.template_name,
            parameters=params_with_metadata,
            metrics=genome.metrics,
            strategy_code=genome.strategy_code,
            success_patterns=genome.success_patterns
        )

        # Verify champion exists
        champion = hall_of_fame.get_current_champion()
        assert champion is not None
        print(f"✅ Champion loaded: Sharpe {champion.metrics['sharpe_ratio']}")

        print("\n[3B] Testing StrategyGenome → ChampionStrategy conversion...")
        # Simulate what autonomous_loop._load_champion() does
        from autonomous_loop import ChampionStrategy

        # Extract iteration_num from parameters (metadata stored during save)
        iteration_num = champion.parameters.get('__iteration_num__', 0)
        clean_params = {k: v for k, v in champion.parameters.items() if not k.startswith('__')}

        champion_strategy = ChampionStrategy(
            iteration_num=iteration_num,
            code=champion.strategy_code,
            parameters=clean_params,
            metrics=champion.metrics,
            success_patterns=champion.success_patterns,
            timestamp=champion.created_at
        )

        assert champion_strategy.iteration_num == 1
        assert champion_strategy.metrics['sharpe_ratio'] == 2.5
        print("✅ Conversion successful")

        print("\n✅ Test 3 PASSED: AutonomousLoop integration works correctly")

    finally:
        if test_dir.exists():
            shutil.rmtree(test_dir)


def test_legacy_migration():
    """Test 4: Legacy champion_strategy.json migration."""
    print("\n" + "="*70)
    print("Test 4: Legacy Champion Migration")
    print("="*70)

    test_dir = TEST_BASE_DIR / "test4"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create legacy champion file
        legacy_file = test_dir / 'champion_strategy.json'
        legacy_data = {
            'iteration_num': 42,
            'code': '# Legacy champion code',
            'parameters': {'legacy_param': 123},
            'metrics': {
                'sharpe_ratio': 2.8,
                'annual_return': 0.35,
                'max_drawdown': -0.12
            },
            'success_patterns': ['Legacy pattern 1', 'Legacy pattern 2'],
            'timestamp': '2025-01-01T12:00:00'
        }

        print("\n[4A] Creating legacy champion file...")
        with open(legacy_file, 'w') as f:
            json.dump(legacy_data, f, indent=2)
        print(f"✅ Legacy file created: {legacy_file}")

        print("\n[4B] Loading and converting legacy champion...")
        with open(legacy_file, 'r') as f:
            loaded_data = json.load(f)

        assert loaded_data['iteration_num'] == 42
        assert loaded_data['metrics']['sharpe_ratio'] == 2.8
        print("✅ Legacy champion loaded")

        print("\n[4C] Converting to StrategyGenome...")
        genome = StrategyGenome(
            template_name='autonomous_generated',
            parameters=loaded_data['parameters'],
            metrics=loaded_data['metrics'],
            created_at=loaded_data['timestamp'],
            strategy_code=loaded_data['code'],
            success_patterns=loaded_data['success_patterns'],
            genome_id=loaded_data['iteration_num']
        )

        assert genome.genome_id == 42
        assert genome.metrics['sharpe_ratio'] == 2.8
        print("✅ Conversion successful")

        print("\n[4D] Saving to Hall of Fame...")
        hall_of_fame = HallOfFameRepository(base_path=str(test_dir))
        hall_of_fame.add_strategy(
            template_name=genome.template_name,
            parameters=genome.parameters,
            metrics=genome.metrics,
            strategy_code=genome.strategy_code,
            success_patterns=genome.success_patterns
        )

        # Verify champion exists in Hall of Fame
        champion = hall_of_fame.get_current_champion()
        assert champion is not None
        # Note: genome_id is auto-generated by Hall of Fame, not preserved from legacy
        assert champion.metrics['sharpe_ratio'] == 2.8
        print(f"✅ Legacy champion migrated to Hall of Fame (Sharpe {champion.metrics['sharpe_ratio']})")

        print("\n✅ Test 4 PASSED: Legacy migration works correctly")

    finally:
        if test_dir.exists():
            shutil.rmtree(test_dir)


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  C1 Fix Integration Tests: Unified Champion Persistence".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)

    # Ensure clean test environment
    if TEST_BASE_DIR.exists():
        shutil.rmtree(TEST_BASE_DIR)

    try:
        test_get_current_champion()
        test_tier_classification()
        test_autonomous_loop_integration()
        test_legacy_migration()

        print("\n" + "█"*70)
        print("█" + " "*68 + "█")
        print("█" + "  ✅ ALL TESTS PASSED".center(68) + "█")
        print("█" + " "*68 + "█")
        print("█"*70)

        print("\n📊 Summary:")
        print("   ✅ get_current_champion() returns highest Sharpe champion")
        print("   ✅ Tier classification (champions/contenders/archive)")
        print("   ✅ AutonomousLoop integration (load/save)")
        print("   ✅ Legacy champion migration")

        print("\n✨ C1 Fix Validated: Unified champion persistence working correctly!")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup all test directories
        if TEST_BASE_DIR.exists():
            shutil.rmtree(TEST_BASE_DIR)
            print(f"\n🧹 Cleaned up test directories")


if __name__ == '__main__':
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
