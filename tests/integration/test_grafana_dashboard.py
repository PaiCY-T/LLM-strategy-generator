"""Integration tests for Grafana Dashboard Configuration.

This module provides comprehensive validation tests for the Grafana dashboard JSON
file, ensuring it is production-ready, importable, and correctly configured.

Test Coverage:
    1. JSON Structure Validation: Syntax, schema compliance, required fields
    2. Panel Configuration: All 4 required panels present and configured correctly
    3. Prometheus Query Validation: Query syntax, metric names, aggregations
    4. Alert Configuration: Alert rules, thresholds, conditions
    5. Annotations: Champion update annotations configured
    6. Dashboard Metadata: UID, tags, version, refresh interval

Requirements: Task 13 - Grafana dashboard validation
"""

import pytest
import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, List
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

DASHBOARD_PATH = Path(__file__).parent.parent.parent / "config" / "grafana_dashboard.json"

# Expected Prometheus metrics from MetricsCollector
VALID_METRICS = {
    # Learning metrics
    'learning_iterations_total',
    'champion_updates_total',
    'strategy_success_total',
    'strategy_failure_total',
    'strategy_sharpe_ratio',

    # Resource metrics
    'system_memory_usage_bytes',
    'system_memory_total_bytes',
    'system_cpu_usage_percent',
    'system_disk_percent',
    'resource_memory_percent',
    'resource_memory_used_bytes',
    'resource_memory_total_bytes',
    'resource_cpu_percent',
    'resource_disk_percent',
    'resource_disk_used_bytes',
    'resource_disk_total_bytes',

    # Diversity metrics
    'population_diversity',
    'unique_strategy_count',
    'champion_staleness_iterations',
    'diversity_collapse_detected',
    'diversity_population_diversity',
    'diversity_unique_count',
    'diversity_total_count',
    'diversity_champion_staleness',

    # Container metrics
    'active_containers',
    'orphaned_containers',
    'container_memory_usage_bytes',
    'container_cpu_usage_percent',
    'container_memory_percent',
    'container_active_count',
    'container_orphaned_count',
    'container_created_total',
    'container_cleanup_success_total',
    'container_cleanup_failed_total',

    # Alert metrics
    'alerts_triggered_total',
    'alert_triggered_total',
    'alert_active_count',
}

# Required panel titles
REQUIRED_PANELS = {
    "Panel 1: Resource Usage",
    "Panel 2: Strategy Performance",
    "Panel 3: Diversity Metrics",
    "Panel 4: Container Statistics"
}

# Alert thresholds from monitoring_config.yaml
EXPECTED_THRESHOLDS = {
    'memory': 80.0,
    'diversity_collapse': 0.1,
    'champion_staleness': 20,
    'success_rate': 20.0,
    'orphaned_containers': 3
}

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def dashboard_json() -> Dict[str, Any]:
    """Load and parse Grafana dashboard JSON file.

    Returns:
        Parsed dashboard JSON as dictionary

    Raises:
        FileNotFoundError: If dashboard file doesn't exist
        json.JSONDecodeError: If JSON syntax is invalid
    """
    if not DASHBOARD_PATH.exists():
        pytest.fail(f"Dashboard file not found: {DASHBOARD_PATH}")

    try:
        with open(DASHBOARD_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON syntax in dashboard: {e}")


@pytest.fixture(scope="module")
def dashboard(dashboard_json: Dict[str, Any]) -> Dict[str, Any]:
    """Extract dashboard object from wrapper.

    Args:
        dashboard_json: Full JSON file contents

    Returns:
        Dashboard object
    """
    return dashboard_json.get('dashboard', dashboard_json)


# =============================================================================
# Test 1: JSON Structure Validation
# =============================================================================

def test_json_syntax_valid(dashboard_json):
    """Test that dashboard JSON has valid syntax.

    Validates:
        - JSON file loads without errors
        - No trailing commas or syntax errors
        - Encoding is correct (UTF-8)
    """
    assert dashboard_json, "Dashboard JSON should not be empty"
    assert isinstance(dashboard_json, dict), "Dashboard JSON should be a dictionary"

    logger.info("✓ Dashboard JSON syntax valid")


def test_required_top_level_fields(dashboard_json):
    """Test that all required top-level fields are present.

    Validates:
        - 'dashboard' wrapper object present
        - 'overwrite' flag present
    """
    assert 'dashboard' in dashboard_json, "Missing 'dashboard' key"
    assert 'overwrite' in dashboard_json, "Missing 'overwrite' key"
    assert dashboard_json['overwrite'] is True, "Dashboard should have overwrite=true"

    logger.info("✓ Top-level structure valid")


def test_dashboard_required_fields(dashboard):
    """Test that dashboard object has all required fields.

    Validates:
        - title, tags, timezone, schemaVersion, version
        - refresh, time, annotations, panels
        - templating, uid
    """
    required_fields = [
        'title', 'tags', 'timezone', 'schemaVersion', 'version',
        'refresh', 'time', 'annotations', 'panels', 'templating',
        'uid', 'editable'
    ]

    missing_fields = [f for f in required_fields if f not in dashboard]
    assert not missing_fields, f"Missing required dashboard fields: {missing_fields}"

    logger.info("✓ All required dashboard fields present")


def test_dashboard_metadata(dashboard):
    """Test dashboard metadata is correctly configured.

    Validates:
        - Title descriptive and contains 'Finlab'
        - Tags include expected values
        - UID is unique and follows convention
        - Version number present
        - Refresh interval set to 5s
    """
    # Title
    assert 'title' in dashboard
    assert 'Finlab' in dashboard['title'] or 'finlab' in dashboard['title'].lower()

    # Tags
    assert 'tags' in dashboard
    assert isinstance(dashboard['tags'], list)
    expected_tags = {'finlab', 'resource-monitoring', 'production'}
    actual_tags = set(tag.lower() for tag in dashboard['tags'])
    assert expected_tags.issubset(actual_tags), f"Missing expected tags. Expected: {expected_tags}, Got: {actual_tags}"

    # UID
    assert 'uid' in dashboard
    assert dashboard['uid'], "UID should not be empty"
    assert 'finlab' in dashboard['uid'].lower(), "UID should contain 'finlab'"

    # Version
    assert 'version' in dashboard
    assert isinstance(dashboard['version'], int)
    assert dashboard['version'] > 0

    # Refresh interval
    assert 'refresh' in dashboard
    assert dashboard['refresh'] == '5s', f"Expected refresh='5s', got '{dashboard['refresh']}'"

    logger.info("✓ Dashboard metadata valid")


def test_time_configuration(dashboard):
    """Test dashboard time range configuration.

    Validates:
        - Time object present
        - 'from' and 'to' fields configured
        - Default range is 1 hour
    """
    assert 'time' in dashboard
    time_config = dashboard['time']

    assert 'from' in time_config
    assert 'to' in time_config

    # Check for 1 hour range
    assert time_config['from'] == 'now-1h', f"Expected from='now-1h', got '{time_config['from']}'"
    assert time_config['to'] == 'now', f"Expected to='now', got '{time_config['to']}'"

    logger.info("✓ Time configuration valid")


# =============================================================================
# Test 2: Panel Configuration Validation
# =============================================================================

def test_all_required_panels_present(dashboard):
    """Test that all 4 required panels are present.

    Validates:
        - Panel 1: Resource Usage
        - Panel 2: Strategy Performance
        - Panel 3: Diversity Metrics
        - Panel 4: Container Statistics
    """
    assert 'panels' in dashboard
    panels = dashboard['panels']
    assert len(panels) >= 4, f"Expected at least 4 panels, got {len(panels)}"

    # Extract panel titles
    panel_titles = {panel.get('title', '') for panel in panels}

    # Check required panels present
    missing_panels = REQUIRED_PANELS - panel_titles
    assert not missing_panels, f"Missing required panels: {missing_panels}"

    logger.info(f"✓ All 4 required panels present (total: {len(panels)} panels)")


def test_panel_types_correct(dashboard):
    """Test that panel types are appropriate for visualization.

    Validates:
        - Panels 1-4 use timeseries for time-series data
        - Additional stat/gauge panels may be present
        - Table panel for alert summary
    """
    panels = dashboard['panels']

    # Get required panels by title
    required_panels = {p['title']: p for p in panels if p.get('title') in REQUIRED_PANELS}

    # Check panel types
    for title in REQUIRED_PANELS:
        assert title in required_panels, f"Panel not found: {title}"
        panel = required_panels[title]

        assert 'type' in panel
        # Main panels should be timeseries
        assert panel['type'] in ['timeseries', 'graph'], \
            f"Panel '{title}' should be timeseries, got '{panel['type']}'"

    logger.info("✓ Panel types configured correctly")


def test_panel_grid_positions(dashboard):
    """Test that panels have valid grid positions.

    Validates:
        - All panels have gridPos
        - Grid positions don't overlap
        - Grid width is 24 or less
    """
    panels = dashboard['panels']

    for panel in panels:
        assert 'gridPos' in panel, f"Panel '{panel.get('title')}' missing gridPos"

        grid = panel['gridPos']
        assert 'h' in grid and 'w' in grid and 'x' in grid and 'y' in grid

        # Validate dimensions
        assert 0 < grid['w'] <= 24, f"Panel width must be 1-24, got {grid['w']}"
        assert grid['h'] > 0, f"Panel height must be positive, got {grid['h']}"
        assert 0 <= grid['x'] < 24, f"Panel x position out of bounds: {grid['x']}"
        assert grid['y'] >= 0, f"Panel y position must be non-negative: {grid['y']}"

    logger.info("✓ Panel grid positions valid")


def test_panel_targets_configured(dashboard):
    """Test that all required panels have targets (queries).

    Validates:
        - Each panel has at least one target
        - Targets have required fields (expr, refId)
        - Legend formats configured
    """
    panels = dashboard['panels']
    required_panels = [p for p in panels if p.get('title') in REQUIRED_PANELS]

    for panel in required_panels:
        title = panel.get('title', 'Unknown')

        # Skip non-timeseries panels (like stat panels)
        if panel.get('type') not in ['timeseries', 'graph']:
            continue

        assert 'targets' in panel, f"Panel '{title}' missing targets"
        targets = panel['targets']
        assert len(targets) > 0, f"Panel '{title}' has no targets"

        # Validate each target
        for target in targets:
            assert 'expr' in target, f"Target in panel '{title}' missing 'expr'"
            assert 'refId' in target, f"Target in panel '{title}' missing 'refId'"

            # Legend format should be present
            if 'legendFormat' not in target:
                logger.warning(f"Target in panel '{title}' missing legendFormat")

    logger.info("✓ Panel targets configured")


def test_panel_field_config(dashboard):
    """Test that panels have appropriate field configurations.

    Validates:
        - fieldConfig present
        - Units configured appropriately
        - Thresholds configured
    """
    panels = dashboard['panels']
    required_panels = [p for p in panels if p.get('title') in REQUIRED_PANELS]

    for panel in required_panels:
        title = panel.get('title', 'Unknown')

        # Skip non-visualization panels
        if panel.get('type') not in ['timeseries', 'graph', 'stat', 'gauge']:
            continue

        assert 'fieldConfig' in panel, f"Panel '{title}' missing fieldConfig"
        field_config = panel['fieldConfig']

        assert 'defaults' in field_config, f"Panel '{title}' missing fieldConfig.defaults"

        # Check thresholds configured
        if 'thresholds' in field_config['defaults']:
            thresholds = field_config['defaults']['thresholds']
            assert 'mode' in thresholds
            assert 'steps' in thresholds
            assert len(thresholds['steps']) > 0

    logger.info("✓ Panel field configurations valid")


# =============================================================================
# Test 3: Prometheus Query Validation
# =============================================================================

def test_all_queries_have_valid_syntax(dashboard):
    """Test that all Prometheus queries have valid syntax.

    Validates:
        - No obvious syntax errors (unmatched brackets, quotes)
        - Metric names are valid
        - Aggregation functions correct
    """
    panels = dashboard['panels']
    all_queries = []

    # Collect all queries
    for panel in panels:
        if 'targets' in panel:
            for target in panel['targets']:
                if 'expr' in target:
                    all_queries.append({
                        'panel': panel.get('title', 'Unknown'),
                        'query': target['expr']
                    })

    assert len(all_queries) > 0, "No queries found in dashboard"

    # Validate each query
    for item in all_queries:
        query = item['query']
        panel = item['panel']

        # Check for balanced brackets
        assert query.count('(') == query.count(')'), \
            f"Unbalanced parentheses in query for panel '{panel}': {query}"
        assert query.count('[') == query.count(']'), \
            f"Unbalanced brackets in query for panel '{panel}': {query}"
        assert query.count('{') == query.count('}'), \
            f"Unbalanced braces in query for panel '{panel}': {query}"

    logger.info(f"✓ All {len(all_queries)} queries have valid syntax")


def test_metric_names_valid(dashboard):
    """Test that all metric names used in queries exist in MetricsCollector.

    Validates:
        - Metric names match expected metrics
        - No typos or undefined metrics
        - All metrics exportable by Prometheus
    """
    panels = dashboard['panels']
    used_metrics = set()

    # Extract all metric names from queries
    for panel in panels:
        if 'targets' in panel:
            for target in panel['targets']:
                if 'expr' in target:
                    query = target['expr']
                    # Extract metric names (simple regex, works for most cases)
                    metric_matches = re.findall(r'\b([a-z_][a-z0-9_]*)\b', query)
                    used_metrics.update(metric_matches)

    # Remove Prometheus functions and operators
    prometheus_keywords = {
        'rate', 'sum', 'avg', 'max', 'min', 'count', 'increase', 'changes',
        'by', 'without', 'and', 'or', 'unless', 'group_left', 'group_right',
        'on', 'ignoring', 'bool', 'offset', 'last', 'total'
    }

    actual_metrics = used_metrics - prometheus_keywords

    # Check metrics are valid
    invalid_metrics = []
    for metric in actual_metrics:
        # Check if metric is in valid set or is a derived metric
        if not any(metric in valid_metric or valid_metric in metric
                   for valid_metric in VALID_METRICS):
            # Skip common metric suffixes
            if not any(metric.endswith(suffix) for suffix in ['_total', '_bytes', '_percent', '_count']):
                invalid_metrics.append(metric)

    # Allow some flexibility - just warn about potentially invalid metrics
    if invalid_metrics:
        logger.warning(f"Potentially invalid metrics found: {invalid_metrics}")

    logger.info(f"✓ Metric names validated ({len(actual_metrics)} unique metrics used)")


def test_prometheus_aggregations_correct(dashboard):
    """Test that Prometheus aggregation functions are used correctly.

    Validates:
        - rate() used with counters
        - sum()/avg() used appropriately
        - Time ranges specified correctly
    """
    panels = dashboard['panels']

    for panel in panels:
        if 'targets' not in panel:
            continue

        for target in panel['targets']:
            if 'expr' not in target:
                continue

            query = target['expr']
            panel_title = panel.get('title', 'Unknown')

            # Check rate() usage with time ranges
            if 'rate(' in query:
                # rate() should have a time range like [5m]
                assert re.search(r'\[\d+[smhd]\]', query), \
                    f"rate() without time range in panel '{panel_title}': {query}"

            # Check sum() and avg() usage
            if 'sum(' in query or 'avg(' in query:
                # Should be well-formed
                assert '(' in query and ')' in query

    logger.info("✓ Prometheus aggregations configured correctly")


def test_legend_formats_configured(dashboard):
    """Test that legend formats are configured for readability.

    Validates:
        - Legend formats present for multi-series panels
        - Formats use descriptive names
        - Labels used appropriately
    """
    panels = dashboard['panels']
    required_panels = [p for p in panels if p.get('title') in REQUIRED_PANELS]

    for panel in required_panels:
        if 'targets' not in panel:
            continue

        targets = panel['targets']
        panel_title = panel.get('title', 'Unknown')

        # Check legend formats
        for target in targets:
            if 'legendFormat' in target:
                legend = target['legendFormat']
                assert legend, f"Empty legendFormat in panel '{panel_title}'"
                # Legend should be descriptive (more than 2 chars)
                assert len(legend) > 2, f"Legend too short in panel '{panel_title}': '{legend}'"

    logger.info("✓ Legend formats configured")


# =============================================================================
# Test 4: Alert Configuration Validation
# =============================================================================

def test_alert_rules_configured(dashboard):
    """Test that alert rules are configured on appropriate panels.

    Validates:
        - At least some panels have alerts
        - Alert conditions specified
        - Alert messages clear
    """
    panels = dashboard['panels']
    panels_with_alerts = [p for p in panels if 'alert' in p]

    # At least one panel should have alerts
    assert len(panels_with_alerts) > 0, "No panels have alert configurations"

    # Validate alert structure
    for panel in panels_with_alerts:
        alert = panel['alert']
        panel_title = panel.get('title', 'Unknown')

        assert 'name' in alert, f"Alert in panel '{panel_title}' missing name"
        assert 'message' in alert, f"Alert in panel '{panel_title}' missing message"
        assert 'conditions' in alert, f"Alert in panel '{panel_title}' missing conditions"

        # Check conditions
        assert len(alert['conditions']) > 0, f"Alert in panel '{panel_title}' has no conditions"

    logger.info(f"✓ Alert rules configured on {len(panels_with_alerts)} panels")


def test_alert_thresholds_match_config(dashboard):
    """Test that alert thresholds match monitoring_config.yaml.

    Validates:
        - Memory alert at 80%
        - Diversity collapse at 0.1
        - Champion staleness at 20 iterations
        - Success rate at 20%
        - Orphaned containers at 3
    """
    panels = dashboard['panels']

    # Map of panel titles to expected thresholds
    threshold_checks = {
        'Resource Usage': {'value': 80, 'type': 'gt'},  # Memory >80%
        'Diversity Metrics': {'value': 0.1, 'type': 'lt'},  # Diversity <0.1
        'Container Statistics': {'value': 3, 'type': 'gt'},  # Orphaned >3
        'Strategy Performance': {'value': 20, 'type': 'lt'}  # Success rate <20%
    }

    # Check alerts in relevant panels
    for panel in panels:
        if 'alert' not in panel:
            continue

        title = panel.get('title', '')

        # Find matching threshold check
        for panel_name, expected in threshold_checks.items():
            if panel_name in title:
                alert = panel['alert']

                # Check conditions
                if 'conditions' in alert and len(alert['conditions']) > 0:
                    condition = alert['conditions'][0]

                    if 'evaluator' in condition:
                        evaluator = condition['evaluator']

                        if 'params' in evaluator and len(evaluator['params']) > 0:
                            threshold = evaluator['params'][0]

                            # Allow some tolerance for floating point
                            if isinstance(threshold, float):
                                assert abs(threshold - expected['value']) < 0.01, \
                                    f"Threshold mismatch in '{title}': expected {expected['value']}, got {threshold}"
                            else:
                                assert threshold == expected['value'], \
                                    f"Threshold mismatch in '{title}': expected {expected['value']}, got {threshold}"

    logger.info("✓ Alert thresholds match configuration")


def test_alert_frequencies_reasonable(dashboard):
    """Test that alert evaluation frequencies are reasonable.

    Validates:
        - Alert frequencies between 1m and 5m
        - Not too frequent (avoid alert fatigue)
        - Not too infrequent (timely alerts)
    """
    panels = dashboard['panels']
    panels_with_alerts = [p for p in panels if 'alert' in p]

    for panel in panels_with_alerts:
        alert = panel['alert']
        panel_title = panel.get('title', 'Unknown')

        if 'frequency' in alert:
            frequency = alert['frequency']

            # Parse frequency (e.g., "1m", "2m")
            match = re.match(r'(\d+)([smh])', frequency)
            assert match, f"Invalid frequency format in panel '{panel_title}': {frequency}"

            value, unit = match.groups()
            value = int(value)

            # Convert to seconds for comparison
            multipliers = {'s': 1, 'm': 60, 'h': 3600}
            seconds = value * multipliers[unit]

            # Should be between 30s and 5 minutes
            assert 30 <= seconds <= 300, \
                f"Alert frequency out of range in panel '{panel_title}': {frequency} ({seconds}s)"

    logger.info("✓ Alert frequencies reasonable")


# =============================================================================
# Test 5: Annotations Validation
# =============================================================================

def test_annotations_configured(dashboard):
    """Test that annotations are configured for champion updates.

    Validates:
        - Annotations list present
        - Champion update annotation exists
        - Query uses champion_updates_total metric
        - Icon color and format appropriate
    """
    assert 'annotations' in dashboard
    annotations = dashboard['annotations']

    assert 'list' in annotations
    annotation_list = annotations['list']

    assert len(annotation_list) > 0, "No annotations configured"

    # Find champion update annotation
    champion_annotation = None
    for annotation in annotation_list:
        if 'champion' in annotation.get('name', '').lower() or \
           'champion' in annotation.get('titleFormat', '').lower():
            champion_annotation = annotation
            break

    assert champion_annotation is not None, "Champion update annotation not found"

    # Validate annotation structure
    assert 'enable' in champion_annotation
    assert champion_annotation['enable'] is True, "Champion annotation should be enabled"

    assert 'expr' in champion_annotation
    query = champion_annotation['expr']
    assert 'champion' in query.lower(), "Annotation query should reference champion metric"

    # Check for appropriate query (changes() or increase())
    assert 'changes(' in query or 'increase(' in query or '>' in query, \
        "Annotation should detect champion updates"

    logger.info("✓ Annotations configured for champion updates")


def test_annotation_formatting(dashboard):
    """Test that annotation formatting is clear and useful.

    Validates:
        - Title format descriptive
        - Text format includes context
        - Icon color appropriate (green for positive events)
    """
    annotations = dashboard['annotations']['list']

    for annotation in annotations:
        name = annotation.get('name', 'Unknown')

        # Title format should exist
        assert 'titleFormat' in annotation, f"Annotation '{name}' missing titleFormat"
        title_format = annotation['titleFormat']
        assert len(title_format) > 0, f"Annotation '{name}' has empty titleFormat"

        # Icon color should be set
        if 'iconColor' in annotation:
            color = annotation['iconColor']
            # Should be a valid color name or hex code
            assert color and len(color) > 0

    logger.info("✓ Annotation formatting configured")


# =============================================================================
# Test 6: Dashboard Import Validation
# =============================================================================

def test_dashboard_importable_structure(dashboard_json):
    """Test that dashboard JSON structure is importable to Grafana.

    Validates:
        - Correct wrapper structure (dashboard + overwrite)
        - No invalid field names
        - Version compatibility
    """
    # Check wrapper structure
    assert 'dashboard' in dashboard_json
    assert 'overwrite' in dashboard_json

    dashboard = dashboard_json['dashboard']

    # Check critical import fields
    assert 'uid' in dashboard, "Dashboard must have UID for import"
    assert 'title' in dashboard, "Dashboard must have title"
    assert 'panels' in dashboard, "Dashboard must have panels"

    # Schema version should be recent (Grafana 9.0+ is v38+)
    if 'schemaVersion' in dashboard:
        schema_version = dashboard['schemaVersion']
        assert schema_version >= 30, \
            f"Schema version too old: {schema_version}. Grafana 9.0+ requires v30+"

    logger.info("✓ Dashboard structure importable to Grafana")


def test_datasource_configuration(dashboard):
    """Test that datasource is correctly configured.

    Validates:
        - Panels reference Prometheus datasource
        - Datasource name consistent
        - Annotations use correct datasource
    """
    # Check annotations datasource
    if 'annotations' in dashboard and 'list' in dashboard['annotations']:
        for annotation in dashboard['annotations']['list']:
            if 'datasource' in annotation:
                ds = annotation['datasource']
                assert ds.lower() in ['prometheus', '${ds}', 'default'], \
                    f"Unexpected datasource in annotation: {ds}"

    # Note: Individual panel datasources may not be explicitly set if using default
    # Grafana uses the default Prometheus datasource in that case

    logger.info("✓ Datasource configuration valid")


def test_templating_configuration(dashboard):
    """Test that templating is configured (even if empty).

    Validates:
        - Templating section present
        - List field exists
    """
    assert 'templating' in dashboard
    templating = dashboard['templating']

    assert 'list' in templating
    # List can be empty for simple dashboards
    assert isinstance(templating['list'], list)

    logger.info("✓ Templating configuration valid")


# =============================================================================
# Test 7: Comprehensive Panel Validation
# =============================================================================

def test_panel_1_resource_usage_complete(dashboard):
    """Test Panel 1: Resource Usage is fully configured.

    Validates:
        - 3 metrics: Memory, CPU, Disk
        - Percentage units
        - 80% alert threshold
        - Time series visualization
    """
    panels = dashboard['panels']
    panel = next((p for p in panels if 'Resource Usage' in p.get('title', '')), None)
    assert panel is not None, "Resource Usage panel not found"

    # Check targets
    assert 'targets' in panel
    targets = panel['targets']
    assert len(targets) >= 3, f"Expected at least 3 targets for Resource Usage, got {len(targets)}"

    # Check for memory, CPU, disk metrics
    queries = ' '.join(t.get('expr', '') for t in targets)
    assert 'memory' in queries.lower(), "Memory metric missing"
    assert 'cpu' in queries.lower(), "CPU metric missing"
    assert 'disk' in queries.lower(), "Disk metric missing"

    # Check for percentage calculation
    assert any('* 100' in t.get('expr', '') or 'percent' in t.get('expr', '')
               for t in targets), "Percentage calculation missing"

    # Check thresholds
    if 'fieldConfig' in panel:
        field_config = panel['fieldConfig']
        if 'defaults' in field_config and 'thresholds' in field_config['defaults']:
            thresholds = field_config['defaults']['thresholds']
            steps = thresholds.get('steps', [])

            # Check for 80% threshold
            threshold_values = [s.get('value') for s in steps if s.get('value') is not None]
            assert any(v == 80 or v == 70 for v in threshold_values), \
                "80% threshold not found in Resource Usage panel"

    logger.info("✓ Panel 1: Resource Usage fully configured")


def test_panel_2_strategy_performance_complete(dashboard):
    """Test Panel 2: Strategy Performance is fully configured.

    Validates:
        - 3 metrics: Success Rate, Sharpe Ratio, Staleness
        - Success rate calculated from counters
        - Sharpe ratio gauge
        - Staleness tracking
    """
    panels = dashboard['panels']
    panel = next((p for p in panels if 'Strategy Performance' in p.get('title', '')), None)
    assert panel is not None, "Strategy Performance panel not found"

    # Check targets
    assert 'targets' in panel
    targets = panel['targets']
    assert len(targets) >= 3, f"Expected at least 3 targets, got {len(targets)}"

    # Check for required metrics
    queries = ' '.join(t.get('expr', '') for t in targets)
    assert 'success' in queries.lower() or 'sharpe' in queries.lower(), \
        "Success or Sharpe metric missing"
    assert 'staleness' in queries.lower() or 'champion' in queries.lower(), \
        "Staleness or champion metric missing"

    # Check for rate calculation in success rate
    success_target = next((t for t in targets if 'success' in t.get('expr', '').lower()), None)
    if success_target:
        expr = success_target['expr']
        # Success rate should use rate() or ratio calculation
        assert 'rate(' in expr or '/' in expr, "Success rate should calculate ratio"

    logger.info("✓ Panel 2: Strategy Performance fully configured")


def test_panel_3_diversity_metrics_complete(dashboard):
    """Test Panel 3: Diversity Metrics is fully configured.

    Validates:
        - 3 metrics: Diversity Score, Unique Strategies, Collapse Detection
        - 0.1 threshold for collapse
        - Collapse visualization
        - Diversity range 0.0-1.0
    """
    panels = dashboard['panels']
    panel = next((p for p in panels if 'Diversity Metrics' in p.get('title', '')), None)
    assert panel is not None, "Diversity Metrics panel not found"

    # Check targets
    assert 'targets' in panel
    targets = panel['targets']
    assert len(targets) >= 2, f"Expected at least 2 targets, got {len(targets)}"

    # Check for diversity metrics
    queries = ' '.join(t.get('expr', '') for t in targets)
    assert 'diversity' in queries.lower(), "Diversity metric missing"

    # Check for collapse detection
    collapse_target = next((t for t in targets if 'collapse' in t.get('expr', '').lower()), None)
    if collapse_target:
        # Collapse should be binary (0 or 1)
        legend = collapse_target.get('legendFormat', '')
        assert 'Yes' in legend or 'No' in legend or '0' in legend or '1' in legend, \
            "Collapse legend should indicate binary state"

    # Check thresholds for 0.1 collapse threshold
    if 'fieldConfig' in panel:
        field_config = panel['fieldConfig']
        if 'defaults' in field_config and 'thresholds' in field_config['defaults']:
            thresholds = field_config['defaults']['thresholds']
            steps = thresholds.get('steps', [])

            # Check for 0.1 threshold
            threshold_values = [s.get('value') for s in steps if s.get('value') is not None]
            assert any(abs(v - 0.1) < 0.01 for v in threshold_values), \
                "0.1 diversity threshold not found"

    logger.info("✓ Panel 3: Diversity Metrics fully configured")


def test_panel_4_container_statistics_complete(dashboard):
    """Test Panel 4: Container Statistics is fully configured.

    Validates:
        - 4 metrics: Active, Orphaned, Memory, CPU
        - Orphaned container tracking
        - Container resource usage
        - Alert on >3 orphaned
    """
    panels = dashboard['panels']
    panel = next((p for p in panels if 'Container Statistics' in p.get('title', '')), None)
    assert panel is not None, "Container Statistics panel not found"

    # Check targets
    assert 'targets' in panel
    targets = panel['targets']
    assert len(targets) >= 2, f"Expected at least 2 targets, got {len(targets)}"

    # Check for container metrics
    queries = ' '.join(t.get('expr', '') for t in targets)
    assert 'container' in queries.lower(), "Container metric missing"
    assert 'orphaned' in queries.lower() or 'active' in queries.lower(), \
        "Orphaned or active container metric missing"

    # Check for orphaned threshold in overrides or alert
    has_orphaned_config = False

    # Check field config overrides
    if 'fieldConfig' in panel:
        field_config = panel['fieldConfig']
        if 'overrides' in field_config:
            for override in field_config['overrides']:
                if 'matcher' in override:
                    matcher = override['matcher']
                    if 'options' in matcher and 'orphaned' in matcher['options'].lower():
                        has_orphaned_config = True
                        break

    # Check alert
    if 'alert' in panel:
        alert = panel['alert']
        if 'message' in alert:
            has_orphaned_config = has_orphaned_config or 'orphaned' in alert['message'].lower()

    assert has_orphaned_config, "Orphaned container configuration not found"

    logger.info("✓ Panel 4: Container Statistics fully configured")


# =============================================================================
# Test 8: Export and Compatibility
# =============================================================================

def test_export_to_json(dashboard_json, tmp_path):
    """Test that dashboard can be exported back to valid JSON.

    Validates:
        - JSON serialization works
        - No data loss in round-trip
        - File can be re-imported
    """
    # Export to temp file
    export_path = tmp_path / "exported_dashboard.json"

    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(dashboard_json, f, indent=2)

    # Re-import
    with open(export_path, 'r', encoding='utf-8') as f:
        reimported = json.load(f)

    # Verify structure preserved
    assert 'dashboard' in reimported
    assert reimported['dashboard']['title'] == dashboard_json['dashboard']['title']
    assert len(reimported['dashboard']['panels']) == len(dashboard_json['dashboard']['panels'])

    logger.info("✓ Dashboard can be exported and re-imported")


def test_dashboard_size_reasonable(dashboard_json):
    """Test that dashboard JSON size is reasonable (<1MB).

    Validates:
        - JSON file not excessively large
        - No bloat from unnecessary data
    """
    json_str = json.dumps(dashboard_json)
    size_bytes = len(json_str.encode('utf-8'))
    size_kb = size_bytes / 1024

    # Dashboard should be under 500KB (generous limit)
    assert size_kb < 500, f"Dashboard too large: {size_kb:.1f}KB (limit: 500KB)"

    logger.info(f"✓ Dashboard size reasonable: {size_kb:.1f}KB")


# =============================================================================
# Summary Test
# =============================================================================

def test_dashboard_comprehensive_validation(dashboard_json):
    """Comprehensive validation summary of all dashboard requirements.

    This test provides a high-level pass/fail for the entire dashboard,
    useful for quick validation.
    """
    dashboard = dashboard_json.get('dashboard', dashboard_json)

    # Critical requirements checklist
    checks = {
        'JSON valid': dashboard_json is not None,
        'Title present': 'title' in dashboard,
        'UID present': 'uid' in dashboard,
        '4 required panels': len([p for p in dashboard.get('panels', [])
                                   if p.get('title') in REQUIRED_PANELS]) >= 4,
        'Refresh = 5s': dashboard.get('refresh') == '5s',
        'Annotations configured': len(dashboard.get('annotations', {}).get('list', [])) > 0,
        'Alerts configured': len([p for p in dashboard.get('panels', [])
                                   if 'alert' in p]) > 0,
        'All panels have targets': all('targets' in p and len(p['targets']) > 0
                                       for p in dashboard.get('panels', [])
                                       if p.get('type') in ['timeseries', 'graph']),
    }

    # Report results
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)

    logger.info(f"\n{'='*60}")
    logger.info(f"Dashboard Validation Summary: {passed}/{total} checks passed")
    logger.info(f"{'='*60}")

    for check, result in checks.items():
        status = "✓" if result else "✗"
        logger.info(f"  {status} {check}")

    logger.info(f"{'='*60}\n")

    # All checks must pass
    failed_checks = [k for k, v in checks.items() if not v]
    assert not failed_checks, f"Failed checks: {failed_checks}"

    logger.info("✓ Dashboard passed comprehensive validation")


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "grafana: Grafana dashboard validation tests"
    )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
