#!/usr/bin/env python3
"""
Quick validation test for Task 6.2 script (2 iterations)
This verifies the validation script works before running the full 30-iteration test.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "artifacts" / "working" / "modules"))

def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")

    try:
        from autonomous_loop import AutonomousLoop
        from history import IterationHistory
        print("  ✅ Core modules imported successfully")
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False

    try:
        from src.config.experiment_config import ExperimentConfig
        print("  ✅ ExperimentConfig imported successfully")
    except ImportError as e:
        print(f"  ❌ ExperimentConfig import failed: {e}")
        return False

    return True

def test_configuration():
    """Test that configuration file exists and is valid."""
    print("\nTesting configuration...")

    config_path = project_root / "config" / "learning_system.yaml"
    if not config_path.exists():
        print(f"  ❌ Config file not found: {config_path}")
        return False

    print(f"  ✅ Config file exists: {config_path}")

    # Try to load it
    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check key settings
        sandbox_enabled = config.get('sandbox', {}).get('enabled', False)
        llm_enabled = config.get('llm', {}).get('enabled', False)

        print(f"  ℹ️  Sandbox enabled: {sandbox_enabled}")
        print(f"  ℹ️  LLM enabled: {llm_enabled}")

        return True
    except Exception as e:
        print(f"  ❌ Failed to load config: {e}")
        return False

def test_docker():
    """Test that Docker is available."""
    print("\nTesting Docker availability...")

    try:
        import docker
        client = docker.from_env()
        client.ping()
        print("  ✅ Docker daemon is running")

        # Check for base image
        try:
            client.images.get("finlab-sandbox:latest")
            print("  ✅ finlab-sandbox:latest image found")
        except docker.errors.ImageNotFound:
            print("  ⚠️  finlab-sandbox:latest image not found")
            print("     The system will attempt to build it or fall back to direct execution")

        return True
    except Exception as e:
        print(f"  ⚠️  Docker not available: {e}")
        print("     System will fall back to direct execution")
        return True  # Not critical, system has fallback

def test_api_key():
    """Test that API key is configured."""
    print("\nTesting API key configuration...")

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        print("  ⚠️  OPENROUTER_API_KEY not set")
        print("     Set with: export OPENROUTER_API_KEY='your-key-here'")
        return False

    print("  ✅ OPENROUTER_API_KEY is configured")
    return True

def test_autonomous_loop_initialization():
    """Test that AutonomousLoop can be initialized."""
    print("\nTesting AutonomousLoop initialization...")

    try:
        from autonomous_loop import AutonomousLoop

        # Try to create instance
        loop = AutonomousLoop(
            model="gemini-2.5-flash",
            max_iterations=2,
            history_file="test_quick_validation_history.json",
            template_mode=False
        )

        print("  ✅ AutonomousLoop initialized successfully")
        print(f"     Sandbox enabled: {loop.sandbox_enabled}")
        print(f"     LLM enabled: {loop.llm_enabled}")

        # Cleanup
        test_history = project_root / "test_quick_validation_history.json"
        if test_history.exists():
            test_history.unlink()

        return True
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_quick_validation():
    """Run 2-iteration validation to test the script."""
    print("\n" + "="*70)
    print("Running 2-iteration quick validation...")
    print("="*70)

    try:
        from autonomous_loop import AutonomousLoop

        loop = AutonomousLoop(
            model="gemini-2.5-flash",
            max_iterations=2,
            history_file="test_quick_validation_history.json",
            template_mode=False
        )

        print("\n🚀 Running 2 test iterations...")

        success_count = 0
        for iteration in range(2):
            print(f"\nIteration {iteration}/2")
            print("-" * 50)

            try:
                success, status = loop.run_iteration(iteration, data=None)
                if success:
                    success_count += 1
                    print(f"  ✅ Iteration {iteration}: SUCCESS")
                else:
                    print(f"  ⚠️  Iteration {iteration}: FAILED ({status})")
            except Exception as e:
                print(f"  ❌ Iteration {iteration}: EXCEPTION - {e}")

        print("\n" + "="*70)
        print(f"Quick validation complete: {success_count}/2 successful")
        print("="*70)

        # Cleanup
        test_history = project_root / "test_quick_validation_history.json"
        if test_history.exists():
            test_history.unlink()
            print("Cleaned up test history file")

        if success_count >= 1:
            print("\n✅ Validation script appears to be working!")
            print("   You can now run the full 30-iteration test:")
            print("   python run_task_6_2_validation.py")
            return True
        else:
            print("\n⚠️  No iterations succeeded. Please investigate before running full test.")
            return False

    except Exception as e:
        print(f"\n❌ Quick validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all quick tests."""
    print("="*70)
    print("TASK 6.2 QUICK VALIDATION TEST")
    print("="*70)

    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Docker", test_docker),
        ("API Key", test_api_key),
        ("Initialization", test_autonomous_loop_initialization)
    ]

    results = {}
    for name, test_func in tests:
        results[name] = test_func()

    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)

    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:20s} {status}")

    critical_pass = results["Imports"] and results["Configuration"]

    if critical_pass:
        print("\n✅ Critical tests passed!")

        if results["API Key"]:
            print("\n" + "="*70)
            print("Ready to run 2-iteration validation test? (y/n)")
            response = input("> ")

            if response.lower() == 'y':
                success = run_quick_validation()
                return 0 if success else 1
            else:
                print("Skipped quick validation.")
                return 0
        else:
            print("\n⚠️  API key not configured. Please set OPENROUTER_API_KEY before running validation.")
            return 1
    else:
        print("\n❌ Critical tests failed. Please fix issues before running validation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
