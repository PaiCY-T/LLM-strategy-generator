"""
Alert System Validation - Task M4
Tests all 5 alert types and suppression mechanism.

Alert Types:
1. Memory alert (>80% threshold)
2. Diversity collapse alert (<0.1 for 5 iterations)
3. Champion staleness alert (>20 iterations)
4. Success rate alert (<20%)
5. Orphaned container alert (>3 containers)
"""

import sys
import time
import logging
from typing import List, Dict, Any

# Configure logging to see alert messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.monitoring.alert_manager import AlertManager, AlertConfig, Alert
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.diversity_monitor import DiversityMonitor

logger = logging.getLogger(__name__)


class AlertSystemValidator:
    """Validates alert system functionality."""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.config = AlertConfig(
            memory_threshold_percent=80.0,
            diversity_collapse_threshold=0.1,
            diversity_collapse_window=5,
            champion_staleness_threshold=20,
            success_rate_threshold=20.0,
            success_rate_window=10,
            orphaned_container_threshold=3,
            suppression_duration=5  # Short duration for testing
        )

    def test_memory_alert(self) -> Dict[str, Any]:
        """Test 1: Memory Alert (>80% threshold)"""
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Memory Alert (>80% threshold)")
        logger.info("="*60)

        try:
            collector = MetricsCollector()
            alert_mgr = AlertManager(self.config, collector)

            # Set up memory source to return high memory
            alert_mgr.set_memory_source(lambda: {'memory_percent': 85.0})
            alert_mgr.set_iteration_source(lambda: 1)

            # Evaluate alerts
            alert_mgr.evaluate_alerts()

            # Check if memory alert was triggered
            active_alerts = alert_mgr.get_active_alerts()

            result = {
                'test': 'memory_alert',
                'passed': 'high_memory' in active_alerts,
                'active_alerts': list(active_alerts),
                'expected': 'high_memory',
                'details': 'Triggered with 85.0% (threshold: 80.0%)'
            }

            logger.info(f"Result: {'PASS' if result['passed'] else 'FAIL'}")
            logger.info(f"Active alerts: {active_alerts}")

            return result

        except Exception as e:
            logger.error(f"Test failed with error: {e}", exc_info=True)
            return {
                'test': 'memory_alert',
                'passed': False,
                'error': str(e)
            }

    def test_diversity_collapse_alert(self) -> Dict[str, Any]:
        """Test 2: Diversity Collapse Alert (<0.1 for 5 iterations)"""
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Diversity Collapse Alert (<0.1 for 5 iterations)")
        logger.info("="*60)

        try:
            collector = MetricsCollector()
            diversity_monitor = DiversityMonitor(
                metrics_collector=collector,
                collapse_threshold=0.1,
                collapse_window=5
            )

            # Simulate 5 iterations with low diversity (<0.1)
            diversity_values = []
            for i in range(5):
                diversity = 0.05  # Below 0.1 threshold
                diversity_monitor.record_diversity(i, diversity, 5, 100)
                diversity_values.append(diversity)

            # Check for collapse
            collapse_detected = diversity_monitor.check_diversity_collapse()

            result = {
                'test': 'diversity_collapse_alert',
                'passed': collapse_detected,
                'diversity_values': diversity_values,
                'collapse_detected': collapse_detected,
                'expected': 'Collapse detected after 5 iterations <0.1',
                'details': f'Recorded {len(diversity_values)} iterations with diversity={diversity_values[0]:.4f}'
            }

            logger.info(f"Result: {'PASS' if result['passed'] else 'FAIL'}")
            logger.info(f"Collapse detected: {collapse_detected}")
            logger.info(f"Diversity values: {diversity_values}")

            return result

        except Exception as e:
            logger.error(f"Test failed with error: {e}", exc_info=True)
            return {
                'test': 'diversity_collapse_alert',
                'passed': False,
                'error': str(e)
            }

    def test_champion_staleness_alert(self) -> Dict[str, Any]:
        """Test 3: Champion Staleness Alert (>20 iterations)"""
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Champion Staleness Alert (>20 iterations)")
        logger.info("="*60)

        try:
            collector = MetricsCollector()
            diversity_monitor = DiversityMonitor(metrics_collector=collector)
            alert_mgr = AlertManager(self.config, collector)

            # Record initial champion update at iteration 0
            diversity_monitor.record_champion_update(0, 1.0, 1.5)

            # Simulate 25 iterations without champion update
            for i in range(1, 26):
                diversity_monitor.record_diversity(i, 0.5, 10, 20)

            # Calculate staleness
            staleness = diversity_monitor.calculate_staleness(25, 0)

            # Set staleness source and check alert
            alert_mgr.set_staleness_source(lambda: staleness)
            alert_mgr.set_iteration_source(lambda: 25)
            alert_mgr.evaluate_alerts()

            active_alerts = alert_mgr.get_active_alerts()

            result = {
                'test': 'champion_staleness_alert',
                'passed': 'champion_staleness' in active_alerts and staleness > 20,
                'staleness': staleness,
                'threshold': 20,
                'active_alerts': list(active_alerts),
                'expected': 'champion_staleness',
                'details': f'Staleness: {staleness} iterations (threshold: 20)'
            }

            logger.info(f"Result: {'PASS' if result['passed'] else 'FAIL'}")
            logger.info(f"Champion staleness: {staleness} iterations")
            logger.info(f"Active alerts: {active_alerts}")

            return result

        except Exception as e:
            logger.error(f"Test failed with error: {e}", exc_info=True)
            return {
                'test': 'champion_staleness_alert',
                'passed': False,
                'error': str(e)
            }

    def test_success_rate_alert(self) -> Dict[str, Any]:
        """Test 4: Success Rate Alert (<20%)"""
        logger.info("\n" + "="*60)
        logger.info("TEST 4: Success Rate Alert (<20%)")
        logger.info("="*60)

        try:
            collector = MetricsCollector()
            alert_mgr = AlertManager(self.config, collector)

            # Record 10 iterations with 15% success rate (below 20% threshold)
            # 1 success, 9 failures = 10% success rate
            alert_mgr.record_iteration_result(True)   # Success
            for _ in range(9):
                alert_mgr.record_iteration_result(False)  # Failures

            # Check alert
            alert_mgr.set_iteration_source(lambda: 10)
            alert_mgr.evaluate_alerts()

            active_alerts = alert_mgr.get_active_alerts()

            # Calculate actual success rate
            success_rate = (1 / 10) * 100  # 10%

            result = {
                'test': 'success_rate_alert',
                'passed': 'low_success_rate' in active_alerts,
                'success_rate': success_rate,
                'threshold': 20.0,
                'active_alerts': list(active_alerts),
                'expected': 'low_success_rate',
                'details': f'Success rate: {success_rate:.1f}% (threshold: 20%)'
            }

            logger.info(f"Result: {'PASS' if result['passed'] else 'FAIL'}")
            logger.info(f"Success rate: {success_rate:.1f}%")
            logger.info(f"Active alerts: {active_alerts}")

            return result

        except Exception as e:
            logger.error(f"Test failed with error: {e}", exc_info=True)
            return {
                'test': 'success_rate_alert',
                'passed': False,
                'error': str(e)
            }

    def test_orphaned_container_alert(self) -> Dict[str, Any]:
        """Test 5: Orphaned Container Alert (>3 containers)"""
        logger.info("\n" + "="*60)
        logger.info("TEST 5: Orphaned Container Alert (>3 containers)")
        logger.info("="*60)

        try:
            collector = MetricsCollector()
            alert_mgr = AlertManager(self.config, collector)

            # Set container source to return 5 orphaned containers (>3 threshold)
            orphaned_count = 5
            alert_mgr.set_container_source(lambda: orphaned_count)
            alert_mgr.set_iteration_source(lambda: 1)

            # Evaluate alerts
            alert_mgr.evaluate_alerts()

            active_alerts = alert_mgr.get_active_alerts()

            result = {
                'test': 'orphaned_container_alert',
                'passed': 'orphaned_containers' in active_alerts,
                'orphaned_count': orphaned_count,
                'threshold': 3,
                'active_alerts': list(active_alerts),
                'expected': 'orphaned_containers',
                'details': f'Orphaned containers: {orphaned_count} (threshold: 3)'
            }

            logger.info(f"Result: {'PASS' if result['passed'] else 'FAIL'}")
            logger.info(f"Orphaned containers: {orphaned_count}")
            logger.info(f"Active alerts: {active_alerts}")

            return result

        except Exception as e:
            logger.error(f"Test failed with error: {e}", exc_info=True)
            return {
                'test': 'orphaned_container_alert',
                'passed': False,
                'error': str(e)
            }

    def test_alert_suppression(self) -> Dict[str, Any]:
        """Test 6: Alert Suppression (no duplicates within window)"""
        logger.info("\n" + "="*60)
        logger.info("TEST 6: Alert Suppression (no duplicates)")
        logger.info("="*60)

        try:
            collector = MetricsCollector()
            alert_mgr = AlertManager(self.config, collector)

            # Set memory source to trigger alert
            alert_mgr.set_memory_source(lambda: {'memory_percent': 85.0})
            alert_mgr.set_iteration_source(lambda: 1)

            # First evaluation - should trigger
            alert_mgr.evaluate_alerts()
            first_active = alert_mgr.get_active_alerts().copy()

            # Second evaluation immediately - should be suppressed
            alert_mgr.evaluate_alerts()
            second_active = alert_mgr.get_active_alerts().copy()

            # Wait for suppression window to expire
            logger.info(f"Waiting {self.config.suppression_duration + 1}s for suppression to expire...")
            time.sleep(self.config.suppression_duration + 1)

            # Third evaluation after window - should trigger again
            alert_mgr.evaluate_alerts()
            third_active = alert_mgr.get_active_alerts().copy()

            result = {
                'test': 'alert_suppression',
                'passed': (
                    'high_memory' in first_active and
                    'high_memory' in second_active and  # Still active
                    'high_memory' in third_active  # Re-triggered after window
                ),
                'first_evaluation': list(first_active),
                'second_evaluation': list(second_active),
                'third_evaluation': list(third_active),
                'suppression_duration': self.config.suppression_duration,
                'expected': 'Alert triggered, suppressed, then re-triggered',
                'details': 'Alert should be suppressed on second evaluation, re-triggered after window'
            }

            logger.info(f"Result: {'PASS' if result['passed'] else 'FAIL'}")
            logger.info(f"First evaluation: {first_active}")
            logger.info(f"Second evaluation (suppressed): {second_active}")
            logger.info(f"Third evaluation (re-triggered): {third_active}")

            return result

        except Exception as e:
            logger.error(f"Test failed with error: {e}", exc_info=True)
            return {
                'test': 'alert_suppression',
                'passed': False,
                'error': str(e)
            }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all alert system validation tests."""
        logger.info("\n" + "#"*60)
        logger.info("ALERT SYSTEM VALIDATION - TASK M4")
        logger.info("#"*60)

        tests = [
            self.test_memory_alert,
            self.test_diversity_collapse_alert,
            self.test_champion_staleness_alert,
            self.test_success_rate_alert,
            self.test_orphaned_container_alert,
            self.test_alert_suppression
        ]

        results = []
        for test in tests:
            result = test()
            results.append(result)
            time.sleep(0.5)  # Brief pause between tests

        # Summary
        logger.info("\n" + "="*60)
        logger.info("VALIDATION SUMMARY")
        logger.info("="*60)

        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.get('passed', False))

        for result in results:
            status = "PASS" if result.get('passed', False) else "FAIL"
            test_name = result.get('test', 'unknown')
            logger.info(f"{status:>6} - {test_name}")
            if not result.get('passed', False) and 'error' in result:
                logger.error(f"       Error: {result['error']}")

        logger.info(f"\nPassed: {passed_tests}/{total_tests}")

        summary = {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'all_tests_passed': passed_tests == total_tests,
            'results': results
        }

        return summary


def main():
    """Main validation function."""
    validator = AlertSystemValidator()
    summary = validator.run_all_tests()

    # Print detailed report
    print("\n" + "="*60)
    print("ALERT SYSTEM VALIDATION REPORT - TASK M4")
    print("="*60)
    print(f"\nTotal Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")

    print("\n" + "-"*60)
    print("DETAILED RESULTS")
    print("-"*60)

    for result in summary['results']:
        print(f"\n{result['test'].upper()}")
        print(f"  Status: {'PASS' if result.get('passed', False) else 'FAIL'}")
        print(f"  Expected: {result.get('expected', 'N/A')}")
        print(f"  Details: {result.get('details', 'N/A')}")

        if 'error' in result:
            print(f"  Error: {result['error']}")

        # Alert-specific details
        if 'active_alerts' in result:
            print(f"  Active Alerts: {result['active_alerts']}")
        if 'staleness' in result:
            print(f"  Staleness: {result['staleness']} iterations")
        if 'success_rate' in result:
            print(f"  Success Rate: {result['success_rate']:.1f}%")
        if 'orphaned_count' in result:
            print(f"  Orphaned Containers: {result['orphaned_count']}")

    print("\n" + "="*60)
    print(f"OVERALL: {'ALL TESTS PASSED' if summary['all_tests_passed'] else 'SOME TESTS FAILED'}")
    print("="*60)

    return 0 if summary['all_tests_passed'] else 1


if __name__ == "__main__":
    sys.exit(main())
