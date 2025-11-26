"""LLM Learning Validation Experiment Orchestrator.

Manages A/B/C testing across 3 experimental groups:
- Hybrid (30% LLM innovation rate)
- FG-Only (0% LLM - baseline control)
- LLM-Only (100% LLM - maximum innovation)

Coordinates:
1. Learning loop execution per group
2. Novelty score calculation
3. Statistical analysis
4. Report generation
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from experiments.llm_learning_validation.config import ExperimentConfig
from src.repository.novelty_scorer import NoveltyScorer
# Statistical analysis modules - optional for basic run
try:
    from src.analysis.statistical.mann_whitney import MannWhitneyAnalyzer
    from src.analysis.statistical.mann_kendall import MannKendallAnalyzer
    STATS_AVAILABLE = True
except ImportError:
    MannWhitneyAnalyzer = None
    MannKendallAnalyzer = None
    STATS_AVAILABLE = False
from src.learning.learning_config import LearningConfig
from src.learning.learning_loop import LearningLoop
from src.learning.unified_loop import UnifiedLoop
# Reporting modules - optional for basic run
try:
    from src.reporting.html_generator import HTMLReportGenerator
    from src.visualization.experiment_plots import ExperimentVisualizer
    REPORTING_AVAILABLE = True
except ImportError:
    HTMLReportGenerator = None
    ExperimentVisualizer = None
    REPORTING_AVAILABLE = False

logger = logging.getLogger(__name__)


class ExperimentOrchestrator:
    """Orchestrates LLM learning validation experiment."""

    def __init__(self, experiment_config_path: Path):
        """Initialize orchestrator.

        Args:
            experiment_config_path: Path to experiment config YAML
        """
        self.exp_config = ExperimentConfig.load(experiment_config_path)
        self.base_learning_config_path = self.exp_config.get_path('learning_config')
        self.results_dir = self.exp_config.get_path('results_dir')
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

        logger.info("=" * 70)
        logger.info("LLM Learning Validation Experiment Orchestrator")
        logger.info("=" * 70)
        logger.info(f"Experiment: {self.exp_config.name}")
        logger.info(f"Groups: {list(self.exp_config.groups.keys())}")
        logger.info(f"Phases: {list(self.exp_config.phases.keys())}")

    def _setup_logging(self):
        """Configure logging for orchestrator only."""
        # Get logger for this module only (avoid global config)
        log = logging.getLogger(__name__)
        log.setLevel(logging.INFO)

        # Only add handlers if not already configured
        if not log.handlers:
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

            # File handler
            file_handler = logging.FileHandler(self.results_dir / "orchestrator.log")
            file_handler.setFormatter(formatter)
            log.addHandler(file_handler)

            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            log.addHandler(console_handler)

        # Prevent propagation to root logger
        log.propagate = False

    def run_pilot(self):
        """Execute pilot phase (300 iterations across 3 groups)."""
        logger.info("\n" + "=" * 70)
        logger.info("PILOT PHASE EXECUTION")
        logger.info("=" * 70)

        phase_config = self.exp_config.phases['pilot']

        # Execute each group
        group_results = {}
        for group_name, group_config in self.exp_config.groups.items():
            logger.info(f"\n--- Executing Group: {group_name.upper()} ---")
            logger.info(f"Innovation Rate: {group_config.innovation_rate * 100:.0f}%")
            logger.info(f"Runs: {phase_config.num_runs} × {phase_config.iterations_per_run} iterations")

            group_results[group_name] = self._run_group(
                group_name=group_name,
                innovation_rate=group_config.innovation_rate,
                num_runs=phase_config.num_runs,
                iterations_per_run=phase_config.iterations_per_run
            )

        # Save pilot results
        pilot_results_path = self.results_dir / "pilot_results.json"
        with open(pilot_results_path, 'w') as f:
            json.dump(group_results, f, indent=2)

        logger.info(f"\n✓ Pilot results saved: {pilot_results_path}")

        return group_results

    def _run_group(
        self,
        group_name: str,
        innovation_rate: float,
        num_runs: int,
        iterations_per_run: int
    ) -> Dict:
        """Execute learning iterations for one experimental group.

        Args:
            group_name: Group identifier (hybrid/fg_only/llm_only)
            innovation_rate: LLM innovation rate (0.0-1.0)
            num_runs: Number of independent runs
            iterations_per_run: Iterations per run

        Returns:
            Dict with results for this group
        """
        group_results = {
            'group_name': group_name,
            'innovation_rate': innovation_rate,
            'num_runs': num_runs,
            'iterations_per_run': iterations_per_run,
            'runs': []
        }

        for run_idx in range(num_runs):
            logger.info(f"\nRun {run_idx + 1}/{num_runs}")

            # Setup unique output paths for this run
            run_id = f"{group_name}_run{run_idx + 1}"
            history_file = self.results_dir / f"{run_id}_history.jsonl"
            champion_file = self.results_dir / f"{run_id}_champion.json"

            try:
                # Execute learning loop
                iterations = self._execute_learning_loop(
                    innovation_rate=innovation_rate,
                    max_iterations=iterations_per_run,
                    history_file=history_file,
                    champion_file=champion_file
                )

                # Calculate novelty scores
                iterations_with_novelty = self._calculate_novelty_scores(iterations)

                group_results['runs'].append({
                    'run_id': run_id,
                    'iterations': iterations_with_novelty,
                    'history_file': str(history_file),
                    'champion_file': str(champion_file)
                })

                logger.info(f"✓ Run {run_idx + 1} complete: {len(iterations)} iterations")

            except Exception as e:
                logger.error(f"✗ Run {run_idx + 1} failed: {e}", exc_info=True)
                group_results['runs'].append({
                    'run_id': run_id,
                    'error': str(e)
                })

        return group_results

    def _execute_learning_loop(
        self,
        innovation_rate: float,
        max_iterations: int,
        history_file: Path,
        champion_file: Path
    ) -> List[Dict]:
        """Execute learning loop with specified innovation rate.

        Args:
            innovation_rate: LLM innovation rate (0.0-1.0)
            max_iterations: Number of iterations to run
            history_file: Path to save iteration history
            champion_file: Path to save champion strategy

        Returns:
            List of iteration records
        """
        # Load base learning config
        with open(self.base_learning_config_path) as f:
            config_data = yaml.safe_load(f)

        # Override parameters for this experiment run
        config_data['learning_loop']['max_iterations'] = max_iterations
        config_data['learning_loop']['history']['file'] = str(history_file)
        config_data['learning_loop']['champion']['file'] = str(champion_file)
        config_data['llm']['innovation_rate'] = innovation_rate

        # Enable/disable LLM based on innovation_rate
        config_data['llm']['enabled'] = (innovation_rate > 0.0)

        # Apply experimental features from experiment config
        # Check if Factor Graph is disabled (Phase 1: Architectural incompatibility)
        experimental = self.exp_config.experimental or {}

        if not experimental.get('use_factor_graph', True):
            logger.info("⚠️  Factor Graph temporarily disabled (experimental.use_factor_graph=false)")
            logger.info("    Reason: Architectural incompatibility with FinLab data structure")
            logger.info("    See: docs/FACTOR_GRAPH_COMPREHENSIVE_ANALYSIS.md")
            # Force LLM-only generation by setting use_factor_graph flag
            config_data['experimental'] = {'use_factor_graph': False}

        # Save temporary config
        temp_config_path = self.results_dir / "temp_learning_config.yaml"
        with open(temp_config_path, 'w') as f:
            yaml.safe_dump(config_data, f)

        # Execute learning loop
        learning_config = LearningConfig.from_yaml(temp_config_path)

        # Use UnifiedLoop if template_mode is enabled, otherwise use LearningLoop
        template_mode = getattr(learning_config, 'template_mode', False)
        if template_mode:
            logger.info(f"Using UnifiedLoop (template_mode=True, template={learning_config.template_name})")
            learning_loop = UnifiedLoop.from_config(temp_config_path)
        else:
            logger.info("Using LearningLoop (template_mode=False, backward compatibility)")
            learning_loop = LearningLoop(learning_config)

        learning_loop.run()

        # Load iteration history
        iterations = []
        if history_file.exists():
            with open(history_file) as f:
                for line in f:
                    iterations.append(json.loads(line))

        return iterations

    def _calculate_novelty_scores(self, iterations: List[Dict]) -> List[Dict]:
        """Calculate novelty scores for all iterations.

        Args:
            iterations: List of iteration records

        Returns:
            Iterations with novelty scores added
        """
        # Load templates for baseline comparison
        template_codes = self._load_template_codes()

        # Initialize novelty scorer
        scorer = NoveltyScorer()

        # Calculate novelty for each iteration
        for iteration in iterations:
            if 'code' in iteration:
                novelty_score, novelty_details = scorer.calculate_novelty_score(iteration['code'], template_codes)
                iteration['novelty_score'] = novelty_score
                iteration['novelty_details'] = novelty_details

        return iterations

    def _load_template_codes(self) -> List[str]:
        """Load Factor Graph template codes for baseline comparison.

        Returns:
            List of template strategy codes
        """
        # Load templates from configured directory
        template_dir = self.exp_config.get_path('template_dir')
        template_codes = []

        if template_dir.exists():
            for template_file in template_dir.glob("*.py"):
                template_codes.append(template_file.read_text())
        else:
            logger.warning(f"Template directory not found: {template_dir}")

        return template_codes

    def analyze_pilot(self):
        """Analyze pilot results and generate comprehensive report."""
        logger.info("\n" + "=" * 70)
        logger.info("PILOT PHASE ANALYSIS")
        logger.info("=" * 70)

        # Load pilot results
        pilot_results_path = self.results_dir / "pilot_results.json"
        with open(pilot_results_path) as f:
            group_results = json.load(f)

        # Extract data by group
        group_data = self._extract_group_data(group_results)

        # Statistical tests (optional)
        statistical_results = None
        if STATS_AVAILABLE:
            statistical_results = self._run_statistical_tests(group_data)
        else:
            logger.warning("Statistical modules not available - skipping analysis")

        # Generate visualizations (optional)
        image_paths = []
        if REPORTING_AVAILABLE:
            viz = ExperimentVisualizer(self.results_dir)

            image_paths.append(viz.plot_learning_curves(
                {name: data['sharpe_ratios'] for name, data in group_data.items()},
                title="Pilot Phase: Learning Curves by Group"
            ))

            image_paths.append(viz.plot_distribution_comparison(
                {name: data['sharpe_ratios'] for name, data in group_data.items()},
                title="Pilot Phase: Sharpe Ratio Distributions"
            ))

            # Generate HTML report
            report_gen = HTMLReportGenerator(self.results_dir)
            report_path = report_gen.generate_report(
                title="LLM Learning Validation - Pilot Phase Results",
                phase="Pilot (300 iterations)",
                executive_summary=self._generate_executive_summary(
                    group_data, statistical_results
                ),
                statistical_results=statistical_results,
                image_paths=image_paths,
                group_comparisons=self._generate_group_comparisons(group_data),
                recommendations=self._generate_recommendations(statistical_results) if statistical_results else ""
            )

            logger.info(f"\n✓ Analysis report generated: {report_path}")
            return report_path
        else:
            logger.warning("Reporting modules not available - skipping visualizations and HTML report")
            logger.info(f"\n✓ Results saved to: {self.results_dir / 'pilot_results.json'}")
            return str(self.results_dir / "pilot_results.json")

    def _extract_group_data(self, group_results: Dict) -> Dict:
        """Extract Sharpe ratios and novelty scores by group.

        Args:
            group_results: Results from all groups

        Returns:
            Dict mapping group names to extracted data
        """
        group_data = {}

        for group_name, group_result in group_results.items():
            sharpe_ratios = []
            novelty_scores = []

            for run in group_result.get('runs', []):
                if 'iterations' in run:
                    for iteration in run['iterations']:
                        if 'sharpe_ratio' in iteration:
                            sharpe_ratios.append(iteration['sharpe_ratio'])
                        if 'novelty_score' in iteration:
                            novelty_scores.append(iteration['novelty_score'])

            group_data[group_name] = {
                'sharpe_ratios': sharpe_ratios,
                'novelty_scores': novelty_scores,
                'n': len(sharpe_ratios)
            }

        return group_data

    def _run_statistical_tests(self, group_data: Dict) -> Dict:
        """Run Mann-Whitney and Mann-Kendall tests.

        Args:
            group_data: Extracted data by group

        Returns:
            Dict with statistical test results
        """
        if not STATS_AVAILABLE:
            return {}

        # Mann-Whitney U tests (pairwise comparisons)
        mw_results = MannWhitneyAnalyzer.compare_all_pairs({
            name: data['sharpe_ratios']
            for name, data in group_data.items()
        })

        # Mann-Kendall trend tests
        mk_results = MannKendallAnalyzer.detect_trends_by_group({
            name: data['sharpe_ratios']
            for name, data in group_data.items()
        })

        return {
            'mann_whitney': mw_results,
            'mann_kendall': mk_results
        }

    def _generate_executive_summary(
        self,
        group_data: Dict,
        statistical_results: Dict
    ) -> str:
        """Generate executive summary HTML."""
        summary = "<h3>Key Findings</h3><ul>"

        # Sample size
        total_iterations = sum(data['n'] for data in group_data.values())
        summary += f"<li>Total iterations: {total_iterations}</li>"

        # Group medians
        for name, data in group_data.items():
            median = np.median(data['sharpe_ratios'])
            summary += f"<li>{name}: median Sharpe = {median:.4f} (n={data['n']})</li>"

        # Significant differences
        sig_count = sum(
            1 for result in statistical_results['mann_whitney'].values()
            if result.significant
        )
        summary += f"<li>Significant pairwise differences: {sig_count}/3</li>"

        summary += "</ul>"
        return summary

    def _generate_group_comparisons(self, group_data: Dict) -> Dict:
        """Generate group comparison table data."""
        comparisons = {}
        for name, data in group_data.items():
            comparisons[name] = {
                'n': data['n'],
                'median_sharpe': float(np.median(data['sharpe_ratios'])),
                'mean_sharpe': float(np.mean(data['sharpe_ratios'])),
                'std_sharpe': float(np.std(data['sharpe_ratios'])),
                'mean_novelty': float(np.mean(data['novelty_scores'])) if data['novelty_scores'] else 'N/A'
            }

        return comparisons

    def _generate_recommendations(self, statistical_results: Dict) -> str:
        """Generate recommendations for go/no-go decision."""
        # Count significant results
        sig_count = sum(
            1 for result in statistical_results['mann_whitney'].values()
            if result.significant
        )

        trend_count = sum(
            1 for result in statistical_results['mann_kendall'].values()
            if result.significant and result.trend == 'increasing'
        )

        if sig_count >= 2 and trend_count >= 1:
            return "<p><strong>Recommendation: GO</strong> - Strong signal detected. Proceed to Full Study.</p>"
        elif sig_count >= 1:
            return "<p><strong>Recommendation: CONDITIONAL GO</strong> - Moderate signal. Consider refinement before Full Study.</p>"
        else:
            return "<p><strong>Recommendation: NO-GO</strong> - Insufficient signal. Refine methodology before proceeding.</p>"


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="LLM Learning Validation Orchestrator")
    parser.add_argument(
        '--phase',
        choices=['pilot', 'full'],
        help="Phase to execute"
    )
    parser.add_argument(
        '--analyze',
        choices=['pilot', 'full'],
        help="Phase to analyze"
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=Path("experiments/llm_learning_validation/config.yaml"),
        help="Experiment config path"
    )

    args = parser.parse_args()

    orchestrator = ExperimentOrchestrator(args.config)

    if args.phase == 'pilot':
        orchestrator.run_pilot()
    elif args.analyze == 'pilot':
        orchestrator.analyze_pilot()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
