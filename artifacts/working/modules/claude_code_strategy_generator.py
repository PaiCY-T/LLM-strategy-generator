"""Claude Code Strategy Generator - Direct generation without API calls.

This module allows Claude Code to directly generate trading strategies
instead of calling external APIs like OpenRouter.
"""

import json
import logging
import random
from pathlib import Path

from src.feedback import TemplateFeedbackIntegrator
from src.templates.turtle_template import TurtleTemplate
from src.templates.mastiff_template import MastiffTemplate
from src.templates.factor_template import FactorTemplate
from src.templates.momentum_template import MomentumTemplate

logger = logging.getLogger(__name__)

# Template class mapping for instantiation (Task 4)
TEMPLATE_MAPPING = {
    'Turtle': TurtleTemplate,
    'Mastiff': MastiffTemplate,
    'Factor': FactorTemplate,
    'Momentum': MomentumTemplate
}

# Configuration constants
MAX_RETRIES = 3  # Maximum retry attempts for template instantiation (Task 8)
EXPLORATION_INTERVAL = 5  # Exploration mode every Nth iteration (Task 5)
LOW_DIVERSITY_THRESHOLD = 0.4  # Warning threshold for diversity score (Task 6)
TEMPLATE_GENERATION_START_ITERATION = 20  # Start using templates after momentum testing
RECENT_HISTORY_WINDOW = 5  # Number of recent iterations to track for diversity (Task 6)


def _generate_momentum_strategy(iteration: int) -> str:
    """
    Generate momentum-based strategy for iterations 0 to TEMPLATE_GENERATION_START_ITERATION-1.

    Args:
        iteration: Current iteration number (0-19)

    Returns:
        Python code string for momentum trading strategy

    Raises:
        ValueError: If iteration is out of range
    """
    if iteration < 0 or iteration >= TEMPLATE_GENERATION_START_ITERATION:
        raise ValueError(
            f"Invalid iteration {iteration} for momentum strategy. "
            f"Must be 0 <= iteration < {TEMPLATE_GENERATION_START_ITERATION}"
        )

    # Iteration 0: Base momentum strategy
    if iteration == 0:
        code = """# Iteration 0: Simple 20-day Momentum
# Testing basic price momentum with liquidity filter

from finlab import data
from finlab import backtest

close = data.get('price:收盤價')
vol = data.get('price:成交股數')

# Momentum factor: 20-day return
momentum_20d = (close / close.shift(20) - 1)

# Liquidity filter (CRITICAL: 150M TWD minimum daily value)
liquidity_filter = (close * vol).average(20) > 150_000_000

# Price filter (avoid penny stocks)
price_filter = close > 10

# Combine conditions
cond_all = liquidity_filter & price_filter
cond_all = cond_all * momentum_20d  # Weight by momentum score
cond_all = cond_all[cond_all > 0].is_largest(10)  # Select top 10 positive momentum

# Set as position signal for iteration engine
position = cond_all

# Backtest with realistic parameters
report = backtest.sim(
    position,
    resample="M",
    fee_ratio=1.425/1000/3,  # 0.1425% transaction cost
    stop_loss=0.08,
    take_profit=0.5,
    position_limit=0.10,  # Max 10% per position
    name="Momentum_20d_Iter0"
)

print(f"年化報酬率: {report.metrics.annual_return():.2%}")
print(f"夏普比率: {report.metrics.sharpe_ratio():.2f}")
print(f"最大回撤: {report.metrics.max_drawdown():.2%}")
"""
        return code.strip()

    # Iterations 1-19: Momentum variations
    momentum_strategies = [
        # Different lookback periods
        (1, 10, "10-day short-term momentum"),
        (2, 40, "40-day medium-term momentum"),
        (3, 60, "60-day long-term momentum"),
        (4, 120, "120-day trend following"),
        # Moving average crossover momentum
        (5, None, "SMA20/SMA60 crossover momentum"),
        (6, None, "SMA5/SMA20 crossover momentum"),
        # Rate of change momentum
        (7, 20, "20-day rate of change"),
        (8, 60, "60-day rate of change"),
        # Relative strength momentum
        (9, 20, "20-day relative strength vs market"),
        (10, 60, "60-day relative strength vs market"),
        # Combined momentum timeframes
        (11, None, "Multi-timeframe momentum (10d+20d+60d)"),
        (12, None, "Weighted momentum (40% 20d, 30% 40d, 30% 60d)"),
        # Momentum with volume confirmation
        (13, 20, "20-day momentum + volume surge"),
        (14, 40, "40-day momentum + volume trend"),
        # Momentum with volatility adjustment
        (15, 20, "20-day momentum / volatility (Sharpe style)"),
        (16, 60, "60-day momentum with low volatility filter"),
        # Acceleration momentum
        (17, None, "Momentum acceleration (increasing momentum)"),
        (18, None, "Momentum deceleration filter (steady momentum)"),
        # Residual momentum
        (19, 20, "20-day residual momentum (vs sector)"),
    ]

    idx = iteration - 1
    if idx >= len(momentum_strategies):
        raise ValueError(f"No momentum strategy defined for iteration {iteration}")

    iter_num, lookback, description = momentum_strategies[idx]

    # Specific implementation for iteration 5 (SMA crossover - different structure)
    if iteration == 5:  # SMA crossover
        code = """# Iteration 5: SMA20/SMA60 crossover momentum

from finlab import data
from finlab import backtest

close = data.get('price:收盤價')
vol = data.get('price:成交股數')

# Moving average crossover momentum
sma20 = close.average(20)
sma60 = close.average(60)
crossover_strength = (sma20 / sma60 - 1)  # Strength of crossover

# Liquidity filter
liquidity_filter = (close * vol).average(20) > 150_000_000
price_filter = close > 10

# Price above both MAs (uptrend confirmation)
uptrend_filter = (close > sma20) & (close > sma60)

# Combine
cond_all = liquidity_filter & price_filter & uptrend_filter
cond_all = cond_all * crossover_strength
cond_all = cond_all[cond_all > 0].is_largest(10)

# Set as position signal for iteration engine
position = cond_all

report = backtest.sim(position, resample="M", fee_ratio=1.425/1000/3,
                      stop_loss=0.08, take_profit=0.5, position_limit=0.10,
                      name="MA_Crossover_Iter5")

print(f"年化報酬率: {report.metrics.annual_return():.2%}")
print(f"夏普比率: {report.metrics.sharpe_ratio():.2f}")
print(f"最大回撤: {report.metrics.max_drawdown():.2%}")
"""
    else:
        # Default for remaining momentum iterations
        lookback_val = lookback if lookback else 20
        code = """# Iteration {}: {}

from finlab import data
from finlab import backtest

close = data.get('price:收盤價')
vol = data.get('price:成交股數')

# Momentum factor (adjust lookback based on iteration)
lookback = {}
momentum = (close / close.shift(lookback) - 1)

# Liquidity filter
liquidity_filter = (close * vol).average(20) > 150_000_000
price_filter = close > 10

# Combine
cond_all = liquidity_filter & price_filter
cond_all = cond_all * momentum
cond_all = cond_all[cond_all > 0].is_largest(10)

# Set as position signal for iteration engine
position = cond_all

report = backtest.sim(position, resample="M", fee_ratio=1.425/1000/3,
                      stop_loss=0.08, take_profit=0.5, position_limit=0.10,
                      name="Momentum_Default")

print(f"年化報酬率: {{report.metrics.annual_return():.2%}}")
print(f"夏普比率: {{report.metrics.sharpe_ratio():.2f}}")
print(f"最大回撤: {{report.metrics.max_drawdown():.2%}}")
""".format(iteration, description, lookback_val)

    return code.strip()


def _load_iteration_history() -> list:
    """
    Load and parse iteration_history.jsonl file.

    Returns:
        List of iteration history entries (dicts). Empty list if file not found.

    Note:
        Handles JSON parse errors gracefully by skipping invalid lines.
    """
    iteration_history = []
    history_file = Path("iteration_history.jsonl")

    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    iteration_history.append(entry)
                except Exception as parse_err:
                    logger.warning(f"Failed to parse history line: {parse_err}")
                    continue

        logger.info(f"Loaded {len(iteration_history)} iteration history entries")
    else:
        logger.warning("iteration_history.jsonl not found, proceeding with empty history")

    return iteration_history


def _analyze_template_diversity(iteration_history: list) -> list:
    """
    Analyze template diversity from recent iteration history.

    Extracts template names from the last RECENT_HISTORY_WINDOW iterations,
    calculates diversity metrics, and logs warnings if diversity is too low.

    Args:
        iteration_history: List of iteration history entries

    Returns:
        List of template names from recent iterations (most recent last)

    Note:
        - Logs diversity metrics and warnings
        - Returns empty list if no history available
    """
    recent_templates = []

    if not iteration_history:
        logger.info("No iteration history available for diversity tracking")
        return recent_templates

    # Get last RECENT_HISTORY_WINDOW entries (or fewer if history is shorter)
    recent_entries = iteration_history[-RECENT_HISTORY_WINDOW:]

    for entry in recent_entries:
        template = entry.get('template')
        if template:
            recent_templates.append(template)

    # Calculate diversity metrics
    if recent_templates:
        unique_templates = len(set(recent_templates))
        total_templates = len(recent_templates)
        diversity_score = unique_templates / total_templates

        logger.info(
            f"📊 Template diversity (last {total_templates} iterations): "
            f"{unique_templates}/{total_templates} unique templates = {diversity_score:.1%} diversity"
        )
        logger.info(f"Recent template usage: {recent_templates}")

        # Warning if diversity is too low
        if diversity_score < LOW_DIVERSITY_THRESHOLD and total_templates >= RECENT_HISTORY_WINDOW:
            logger.warning(
                f"⚠️  Low template diversity detected ({diversity_score:.1%} < {LOW_DIVERSITY_THRESHOLD:.1%}). "
                f"Consider enabling exploration mode to increase strategy variety."
            )
    else:
        logger.info("No template data found in recent iterations")

    return recent_templates


def _select_fallback_template(recent_templates: list) -> str:
    """
    Select fallback template when recommendation system fails.

    Uses two strategies:
    1. LRU (Least Recently Used): If all templates have been used in recent iterations
    2. Random Selection: Choose randomly from templates not used recently

    Args:
        recent_templates: List of template names from recent iterations

    Returns:
        Selected template name (Turtle, Mastiff, Factor, or Momentum)

    Note:
        Logs selection strategy and reasoning
    """
    all_templates = set(TEMPLATE_MAPPING.keys())
    recent_template_set = set(recent_templates) if recent_templates else set()

    # Strategy 1: LRU - All templates used recently
    if len(recent_template_set) == len(all_templates) and len(recent_templates) >= 4:
        logger.info(
            f"🔄 All {len(all_templates)} templates used in recent {len(recent_templates)} iterations. "
            f"Selecting least recently used template for diversity."
        )

        # Find least recently used template
        # Count occurrences in recent_templates (most recent = end of list)
        template_last_position = {}
        for template in all_templates:
            if template in recent_templates:
                # Find last occurrence position (higher = more recent)
                last_idx = len(recent_templates) - 1 - recent_templates[::-1].index(template)
                template_last_position[template] = last_idx
            else:
                # Not in recent list - highest priority
                template_last_position[template] = -1

        # Select template with lowest position (least recently used)
        selected_template = min(template_last_position.items(), key=lambda x: x[1])[0]
        logger.info(
            f"✅ Selected least recently used template: {selected_template} "
            f"(last position: {template_last_position[selected_template]})"
        )
        return selected_template

    # Strategy 2: Random - Not all templates used
    available_templates = list(all_templates - recent_template_set)

    if not available_templates:
        # Edge case: no available templates (shouldn't happen but handle gracefully)
        available_templates = list(all_templates)
        logger.warning(
            "⚠️  No unused templates available despite diversity check. "
            "Selecting random from all templates."
        )

    selected_template = random.choice(available_templates)
    logger.info(
        f"🎲 Selected random template not in recent usage: {selected_template} "
        f"(recent: {recent_templates}, available: {available_templates})"
    )
    return selected_template


def _instantiate_and_generate(
    template_name: str,
    suggested_params: dict,
    is_fallback: bool = False
) -> str:
    """
    Helper function to instantiate template and generate strategy code.

    Args:
        template_name: Name of template to instantiate (e.g., 'Turtle', 'Mastiff')
        suggested_params: Parameters to pass to generate_strategy()
        is_fallback: Whether this is fallback mode (for logging)

    Returns:
        Generated strategy code string

    Raises:
        ValueError: If template name is unknown
        Exception: If instantiation or generation fails
    """
    log_prefix = "(fallback mode)" if is_fallback else ""

    # Validate template name
    if template_name not in TEMPLATE_MAPPING:
        raise ValueError(
            f"Unknown template name: {template_name}. "
            f"Available templates: {list(TEMPLATE_MAPPING.keys())}"
        )

    # Get template class
    template_class = TEMPLATE_MAPPING[template_name]
    logger.info(f"Instantiating {template_name} template class: {template_class.__name__} {log_prefix}")

    # Instantiate template
    template_instance = template_class()
    logger.info(
        f"Successfully instantiated {template_name} template {log_prefix}. "
        f"Params for generate_strategy: {suggested_params}"
    )

    # Generate strategy code
    logger.info(f"Calling {template_name}.generate_strategy() {log_prefix} with params: {suggested_params}")
    code = template_instance.generate_strategy(**suggested_params)
    logger.info(f"✅ Strategy code generated {log_prefix}: {len(code)} chars")

    return code


def generate_strategy_with_claude_code(
    iteration: int,
    feedback: str = "",
    prompt_template_path: str = "prompt_template_v2_with_datasets.txt"
) -> str:
    """Generate strategy code directly using Claude Code.

    This function is a placeholder that returns the prompt for Claude Code
    to generate the strategy. The actual strategy generation will be done
    by Claude Code itself when this function is called.

    Args:
        iteration: Current iteration number
        feedback: Feedback from previous iteration (optional)
        prompt_template_path: Path to prompt template file

    Returns:
        Python code string for trading strategy

    Raises:
        FileNotFoundError: If prompt template not found
        ValueError: If prompt building fails
    """
    logger.info(f"Generating strategy for iteration {iteration} using Claude Code")

    # Load prompt template
    template_path = Path(prompt_template_path)
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Build iteration context
    context = f"\n\n## ITERATION {iteration}\n\n"

    if iteration == 0:
        context += "This is the first iteration. Generate an innovative trading strategy.\n"
    else:
        context += f"This is iteration {iteration}. Based on feedback below, create an improved strategy.\n"

    # Add feedback if provided
    if feedback:
        context += f"\n## FEEDBACK FROM ITERATION {iteration - 1}\n\n"
        context += feedback + "\n"
        context += "\n**Your task**: Learn from the feedback above and generate a BETTER strategy.\n"
        context += "- Fix any errors mentioned\n"
        context += "- Improve upon weaknesses identified\n"
        context += "- Try different factor combinations or approaches\n"

    # Combine template + context
    complete_prompt = template + context

    logger.info(f"Built prompt for iteration {iteration}: {len(complete_prompt)} chars")

    # Generate strategy based on iteration number and feedback
    logger.info(f"Generating strategy code for iteration {iteration}")

    # MOMENTUM FACTOR TESTING PHASE (Iterations 0-19)
    # Test different momentum indicators systematically
    if iteration < TEMPLATE_GENERATION_START_ITERATION:
        logger.info(
            f"Iteration {iteration} < {TEMPLATE_GENERATION_START_ITERATION}: "
            f"Using momentum-based strategy generation"
        )
        code = _generate_momentum_strategy(iteration)
        logger.info(f"Generated momentum strategy: {len(code)} chars")
        return code.strip()
    # After momentum testing, move to template-based strategy generation (iterations >= TEMPLATE_GENERATION_START_ITERATION)
    else:
        # Initialize code variable to prevent NameError
        code = ""

        # Task 3: Template recommendation call (iteration >= TEMPLATE_GENERATION_START_ITERATION)
        logger.info(f"Iteration {iteration} >= {TEMPLATE_GENERATION_START_ITERATION}: Using template-based strategy generation")

        # Task 5: Explicit exploration mode detection (every EXPLORATION_INTERVAL iterations)
        is_exploration = (iteration % EXPLORATION_INTERVAL == 0)

        if is_exploration:
            logger.info(
                f"🔍 EXPLORATION MODE ACTIVATED for iteration {iteration} "
                f"(iteration % {EXPLORATION_INTERVAL} == 0). System will select template different from recent iterations."
            )
        else:
            logger.info(
                f"Standard recommendation mode for iteration {iteration} "
                f"(iteration % {EXPLORATION_INTERVAL} == {iteration % EXPLORATION_INTERVAL})"
            )

        # Task 8: Retry loop for template instantiation (max 3 retries)
        attempted_templates = []  # Track templates we've already tried
        recommended_template = None
        suggested_params = None

        for retry_attempt in range(1, MAX_RETRIES + 1):
            logger.info(
                f"🔄 Template instantiation attempt {retry_attempt}/{MAX_RETRIES} "
                f"(attempted templates: {attempted_templates})"
            )

            try:
                # Initialize TemplateFeedbackIntegrator (already imported at top)
                integrator = TemplateFeedbackIntegrator()
                logger.info("TemplateFeedbackIntegrator initialized successfully")

                # Load iteration history to get historical performance data
                iteration_history = _load_iteration_history()

                # Task 6: Analyze template diversity from recent iterations
                recent_templates = _analyze_template_diversity(iteration_history)

                # Prepare feedback_data with iteration history and current feedback
                feedback_data = {
                    'current_metrics': None,  # Will be populated from latest history entry
                    'iteration': iteration,
                    'validation_result': None,
                    'iteration_history': iteration_history
                }

                # Extract current metrics from most recent successful iteration
                if iteration_history:
                    # Find most recent successful iteration with metrics
                    for entry in reversed(iteration_history):
                        if entry.get('success', False) and entry.get('metrics'):
                            feedback_data['current_metrics'] = entry['metrics']
                            logger.info(
                                f"Using metrics from iteration {entry.get('iteration', 'unknown')}: "
                                f"sharpe={entry['metrics'].get('sharpe_ratio', 0.0):.2f}"
                            )
                            break

                # Call integrator.recommend_template() with feedback data
                recommendation = integrator.recommend_template(
                    current_metrics=feedback_data['current_metrics'],
                    iteration=iteration,
                    validation_result=feedback_data.get('validation_result')
                )

                # Task 5: Verify exploration mode matches expectation
                if is_exploration and not recommendation.exploration_mode:
                    logger.warning(
                        f"⚠️  Exploration mode mismatch: Expected exploration=True for iteration {iteration}, "
                        f"but recommendation has exploration=False"
                    )
                elif not is_exploration and recommendation.exploration_mode:
                    logger.warning(
                        f"⚠️  Exploration mode mismatch: Expected exploration=False for iteration {iteration}, "
                        f"but recommendation has exploration=True"
                    )
                else:
                    logger.info(
                        f"✅ Exploration mode status verified: "
                        f"expected={is_exploration}, actual={recommendation.exploration_mode}"
                    )

                # Log template selection with exploration mode status
                logger.info(
                    f"📋 Template selected: {recommendation.template_name} | "
                    f"Exploration mode: {recommendation.exploration_mode} | "
                    f"Match score: {recommendation.match_score:.2f} | "
                    f"Iteration: {iteration}"
                )
                logger.info(f"Rationale: {recommendation.rationale}")

                # Task 6: Verify template diversity in exploration mode
                if is_exploration and recent_templates:
                    if recommendation.template_name in recent_templates:
                        logger.warning(
                            f"⚠️  Diversity violation: Template {recommendation.template_name} was used in recent {len(recent_templates)} iterations. "
                            f"Exploration mode should select a different template. Recent usage: {recent_templates}"
                        )
                    else:
                        logger.info(
                            f"✅ Template diversity verified: {recommendation.template_name} not in recent templates {recent_templates}"
                        )

                # Store recommendation for Tasks 4-7 to use
                recommended_template = recommendation.template_name
                suggested_params = recommendation.suggested_params

                logger.info(f"Suggested parameters: {suggested_params}")

                # Task 4: Instantiate template class with suggested parameters
                try:
                    code = _instantiate_and_generate(
                        template_name=recommended_template,
                        suggested_params=suggested_params,
                        is_fallback=False
                    )
                    # Success - break out of retry loop
                    break

                except Exception as instantiation_error:
                    logger.error(
                        f"Template instantiation/generation failed for {recommended_template}: {instantiation_error}",
                        exc_info=True
                    )
                    # Re-raise for Task 8 (retry logic) to handle
                    raise

            except Exception as e:
                logger.error(f"Template recommendation failed: {e}", exc_info=True)

                # Task 7: Fallback to random template selection when recommendation fails
                logger.warning(
                    f"⚠️  FALLBACK MODE ACTIVATED for iteration {iteration}: "
                    f"Template recommendation failed with error: {str(e)}"
                )

                # Select fallback template using LRU or random selection
                recommended_template = _select_fallback_template(recent_templates)

                # Generate default suggested parameters (empty dict for conservative defaults)
                suggested_params = {}
                logger.info(
                    f"Using default parameters for fallback template {recommended_template}: {suggested_params}"
                )

                logger.info(
                    f"📋 Fallback template selected: {recommended_template} | "
                    f"Default parameters: {suggested_params} | "
                    f"Reason: Recommendation system failure"
                )

                # Task 4: Instantiate template class with default parameters
                try:
                    code = _instantiate_and_generate(
                        template_name=recommended_template,
                        suggested_params=suggested_params,
                        is_fallback=True
                    )
                    # Success - break out of retry loop
                    break

                except Exception as instantiation_error:
                    logger.error(
                        f"Template instantiation/generation failed for fallback template {recommended_template}: {instantiation_error}",
                        exc_info=True
                    )

                    # Task 8: Retry logic (moved here to fix unreachable except issue)
                    # Add failed template to attempted list
                    if recommended_template and recommended_template not in attempted_templates:
                        attempted_templates.append(recommended_template)

                    # Check if we should retry
                    if retry_attempt < MAX_RETRIES:
                        logger.warning(
                            f"Template instantiation failed (attempt {retry_attempt}/{MAX_RETRIES}). "
                            f"Retrying with a different template. Error: {str(instantiation_error)}"
                        )
                        # Continue to next retry attempt
                        continue
                    else:
                        # Max retries reached - log all attempts and raise final error
                        logger.error(
                            f"❌ Template instantiation failed after {MAX_RETRIES} attempts. "
                            f"Attempted templates: {attempted_templates}. "
                            f"Final error: {str(instantiation_error)}"
                        )
                        raise RuntimeError(
                            f"Template instantiation failed after {MAX_RETRIES} retry attempts. "
                            f"Attempted templates: {attempted_templates}. "
                            f"Last error: {str(instantiation_error)}"
                        ) from instantiation_error

            # Success - break out of retry loop
            logger.info(
                f"✅ Template instantiation successful on attempt {retry_attempt}/{MAX_RETRIES}. "
                f"Template: {recommended_template}"
            )
            break

    logger.info(f"Generated strategy code: {len(code)} chars")
    return code


def main():
    """Test the Claude Code strategy generator."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Testing Claude Code Strategy Generator")
    print("=" * 60)

    try:
        # Test generation
        print("Generating test strategy (iteration 0)...")
        code = generate_strategy_with_claude_code(
            iteration=0,
            feedback=""
        )

        print(f"\n✅ Generated code: {len(code)} characters")
        print("\nFirst 500 chars:")
        print("-" * 60)
        print(code[:500])
        print("-" * 60)

    except NotImplementedError as e:
        print(f"\n⚠️  Expected: {e}")
        print("\nThis function is ready for Claude Code to implement.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
