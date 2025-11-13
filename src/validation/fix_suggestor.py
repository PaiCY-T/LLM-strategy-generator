"""
Fix Suggestion Generator for Validation Errors
===============================================

Generates actionable fix suggestions for common validation errors with code
examples, parameter ranges, and architecture patterns.

Features:
    - Missing parameter fixes with valid ranges from PARAM_GRID
    - Architecture violation fixes with correct pattern examples
    - Lookahead bias fixes with proper shift usage
    - Error category to fix template mapping
    - Formatted code snippets with syntax highlighting

Usage:
    from src.validation import FixSuggestor, ValidationError

    suggestor = FixSuggestor()
    error = ValidationError(...)
    suggestion = suggestor.generate_fix_suggestion(error)
    print(suggestion)

Requirements:
    - Requirement 3.4: Automated fix suggestion generation
"""

from typing import Dict, Any, Optional, List
from .template_validator import ValidationError, Category, Severity


class FixSuggestor:
    """
    Generate actionable fix suggestions for validation errors.

    Provides template-based fix suggestions for common validation errors,
    including missing parameters, architecture violations, and data access
    anti-patterns. Generates formatted code snippets and parameter guidance.

    Features:
        - Error category to fix template mapping
        - Parameter range guidance from template schemas
        - Architecture pattern examples
        - Lookahead bias detection and fixes
        - Formatted code snippets with examples

    Example:
        >>> suggestor = FixSuggestor()
        >>> error = ValidationError(
        ...     severity=Severity.CRITICAL,
        ...     category=Category.PARAMETER,
        ...     message="Missing required parameter 'n_stocks'",
        ...     context={'template': 'TurtleTemplate'}
        ... )
        >>> suggestion = suggestor.generate_fix_suggestion(error)
        >>> print(suggestion)
        FIX: Add 'n_stocks' parameter to your strategy parameters

        Parameter: n_stocks
        Type: int
        Valid Range: 5-20
        Optimal Range: 10-15
        Description: Number of stocks to select for portfolio

        Example:
        ```python
        parameters = {
            'n_stocks': 10,  # Optimal for risk-adjusted returns
            ...
        }
        ```
    """

    # Parameter schema definitions for fix suggestions
    PARAMETER_FIXES = {
        'TurtleTemplate': {
            'n_stocks': {
                'type': 'int',
                'range': '5-20',
                'optimal': '10-15',
                'description': 'Number of stocks to select for portfolio',
                'example': 10
            },
            'yield_threshold': {
                'type': 'float',
                'range': '4.0-8.0%',
                'optimal': '5.0-7.0%',
                'description': 'Minimum dividend yield threshold',
                'example': 6.0
            },
            'ma_short': {
                'type': 'int',
                'range': '10-30 days',
                'optimal': '15-25 days',
                'description': 'Short-term moving average period',
                'example': 20
            },
            'ma_long': {
                'type': 'int',
                'range': '40-80 days',
                'optimal': '50-70 days',
                'description': 'Long-term moving average period',
                'example': 60
            },
            'stop_loss': {
                'type': 'float',
                'range': '0.06-0.10 (6-10%)',
                'optimal': '0.06-0.08 (6-8%)',
                'description': 'Maximum loss per position',
                'example': 0.06
            },
            'take_profit': {
                'type': 'float',
                'range': '0.30-0.70 (30-70%)',
                'optimal': '0.40-0.60 (40-60%)',
                'description': 'Target profit per position',
                'example': 0.50
            }
        },
        'MastiffTemplate': {
            'n_stocks': {
                'type': 'int',
                'range': '3-10',
                'optimal': '5-8',
                'description': 'Number of stocks (concentrated positioning)',
                'example': 5
            },
            'stop_loss': {
                'type': 'float',
                'range': '0.10-0.20 (10-20%)',
                'optimal': '0.12-0.18 (12-18%)',
                'description': 'Maximum loss per position (higher for mean reversion)',
                'example': 0.15
            },
            'position_limit': {
                'type': 'float',
                'range': '0.15-0.30 (15-30%)',
                'optimal': '0.20-0.25 (20-25%)',
                'description': 'Maximum position size (high concentration)',
                'example': 0.20
            }
        }
    }

    # Architecture pattern fixes
    ARCHITECTURE_FIXES = {
        '6-layer AND filtering': """
FIX: Implement proper 6-layer AND filtering architecture

Required Layers:
1. **Yield Layer**: Dividend yield threshold filtering
2. **Technical Layer**: Moving average crossover signals
3. **Revenue Layer**: Revenue growth momentum
4. **Quality Layer**: Operational efficiency metrics
5. **Insider Layer**: Director shareholding changes
6. **Liquidity Layer**: Trading volume constraints

Example Implementation:
```python
# Layer 1: Dividend Yield
cond1 = yield_ratio >= params['yield_threshold']

# Layer 2: Technical Confirmation
cond2 = (close > sma_short) & (close > sma_long)

# Layer 3: Revenue Acceleration
cond3 = rev.average(params['rev_short']) > rev.average(params['rev_long'])

# Layer 4: Operating Margin Quality
cond4 = ope_earn >= params['op_margin_threshold']

# Layer 5: Director Confidence
cond5 = boss_hold >= params['director_threshold']

# Layer 6: Liquidity
cond6 = (vol.average(5) >= params['vol_min'] * 1000) &
        (vol.average(5) <= params['vol_max'] * 1000)

# Combine ALL layers with AND operator
cond_all = cond1 & cond2 & cond3 & cond4 & cond5 & cond6
```

**Critical**: All 6 layers must be combined with AND (&) operator, not OR (|)
        """,
        'contrarian_reversal': """
FIX: Implement proper contrarian reversal architecture

Required Components:
1. **Price High Filter**: Identify stocks creating 250-day highs
2. **Revenue Decline Filter**: Exclude sustained revenue decline
3. **Revenue Growth Filter**: Exclude excessive growth
4. **Revenue Bottom Detection**: Confirm recovery from lows
5. **Momentum Filter**: Ensure momentum not too negative
6. **Liquidity**: Adequate trading volume

Example Implementation:
```python
# Condition 1: Price High Filter
cond1 = (close == close.rolling(250).max())

# Condition 2: Revenue Decline Filter
cond2 = ~(rev_year_growth < -10).sustain(3)

# Condition 3: Revenue Growth Filter
cond3 = ~(rev_year_growth > 60).sustain(12, 8)

# Condition 4: Revenue Bottom Detection
cond4 = ((rev.rolling(12).min()) / (rev) < 0.8).sustain(3)

# Condition 5: Momentum Filter
cond5 = (rev_month_growth > -40).sustain(3)

# Condition 6: Liquidity
cond6 = vol_ma > 200 * 1000

# Combine all conditions with AND operator
cond_all = cond1 & cond2 & cond3 & cond4 & cond5 & cond6
```

**Critical**: Use .is_smallest() for LOW-volume contrarian selection, NOT .is_largest()
        """
    }

    # Lookahead bias fixes
    LOOKAHEAD_BIAS_FIXES = {
        'no_shift': """
FIX: Apply proper shift() to avoid lookahead bias

**Problem**: Using current period data to make decisions creates lookahead bias
**Solution**: Shift data by 1 period to use only historical information

Example Fix:
```python
# ❌ WRONG - Lookahead bias (using today's data to trade today)
signal = (close > close.average(20))

# ✅ CORRECT - Proper shift (using yesterday's data to trade today)
signal = (close.shift(1) > close.shift(1).average(20))

# Alternative: Shift the entire condition
signal = (close > close.average(20)).shift(1)
```

**Rule of Thumb**: Always shift data by 1 period before using it for trading signals
        """,
        'data_peek': """
FIX: Avoid data peeking in rolling calculations

**Problem**: Using future data in rolling windows creates lookahead bias
**Solution**: Ensure rolling calculations only use past data

Example Fix:
```python
# ❌ WRONG - Using future data in rolling window
max_future = close.rolling(window=5, min_periods=1).max()  # Includes future data

# ✅ CORRECT - Only use past data with proper shift
max_past = close.shift(1).rolling(window=5, min_periods=1).max()

# Alternative: Use finlab's built-in methods that handle shifting
max_past = close.average(5).shift(1)  # Automatically handles historical data
```

**Rule of Thumb**: Always verify that rolling calculations use only past data
        """
    }

    # Data access pattern fixes
    DATA_ACCESS_FIXES = {
        'duplicate_calls': """
FIX: Eliminate duplicate data.get() calls

**Problem**: Loading the same dataset multiple times reduces performance
**Solution**: Store dataset in a variable and reuse it

Example Fix:
```python
# ❌ WRONG - Duplicate data loading
close1 = data.get('price:收盤價')
close2 = data.get('price:收盤價')  # Duplicate!
signal = close1 > close2.average(20)

# ✅ CORRECT - Load once and reuse
close = data.get('price:收盤價')
signal = close > close.average(20)
```

**Performance Impact**: Each data.get() call has overhead. Reusing reduces execution time.
        """,
        'excessive_calls': """
FIX: Reduce excessive data.get() calls using DataCache

**Problem**: Too many data.get() calls (>10) cause performance degradation
**Solution**: Use DataCache for efficient data access and caching

Example Fix:
```python
# ❌ WRONG - Excessive individual data.get() calls (15+ calls)
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue = data.get('monthly_revenue:當月營收')
# ... 12 more data.get() calls ...

# ✅ CORRECT - Use DataCache for efficient access
from src.templates.data_cache import DataCache

cache = DataCache.get_instance()
close = cache.get('price:收盤價')
volume = cache.get('price:成交股數')
revenue = cache.get('monthly_revenue:當月營收')
# DataCache automatically handles caching and reuse
```

**Performance Impact**: DataCache reduces redundant data loading by ~60%
        """
    }

    def __init__(self):
        """Initialize fix suggestor with template mappings."""
        self.fix_templates = {
            Category.PARAMETER: self._generate_parameter_fix,
            Category.ARCHITECTURE: self._generate_architecture_fix,
            Category.DATA: self._generate_data_fix,
            Category.BACKTEST: self._generate_backtest_fix
        }

    def generate_fix_suggestion(
        self,
        error: ValidationError,
        template_name: Optional[str] = None
    ) -> str:
        """
        Generate actionable fix suggestion for validation error.

        Args:
            error: ValidationError object with severity, category, message, context
            template_name: Optional template name for parameter-specific fixes

        Returns:
            Formatted fix suggestion string with code examples

        Example:
            >>> error = ValidationError(
            ...     severity=Severity.CRITICAL,
            ...     category=Category.PARAMETER,
            ...     message="n_stocks must be between 5 and 20",
            ...     context={'parameter': 'n_stocks', 'value': 100}
            ... )
            >>> suggestion = suggestor.generate_fix_suggestion(error, 'TurtleTemplate')
            >>> print(suggestion)
            FIX: Set n_stocks to a value in range [5, 20]
            ...
        """
        # Get fix generator for this error category
        fix_generator = self.fix_templates.get(error.category)

        if not fix_generator:
            return self._generate_generic_fix(error)

        # Generate category-specific fix
        return fix_generator(error, template_name)

    def _generate_parameter_fix(
        self,
        error: ValidationError,
        template_name: Optional[str]
    ) -> str:
        """Generate fix for parameter validation errors."""
        context = error.context
        param_name = context.get('parameter', 'unknown')

        # Check if we have a fix template for this parameter
        if template_name and template_name in self.PARAMETER_FIXES:
            param_fixes = self.PARAMETER_FIXES[template_name]

            if param_name in param_fixes:
                fix_info = param_fixes[param_name]

                return f"""FIX: Add or correct '{param_name}' parameter

Parameter: {param_name}
Type: {fix_info['type']}
Valid Range: {fix_info['range']}
Optimal Range: {fix_info['optimal']}
Description: {fix_info['description']}

Example:
```python
parameters = {{
    '{param_name}': {fix_info['example']},  # {fix_info['description']}
    # ... other parameters ...
}}
```

**Suggestion**: {error.suggestion if error.suggestion else f"Set {param_name} within valid range"}
"""

        # Generic parameter fix
        return f"""FIX: Correct parameter '{param_name}'

Error: {error.message}
Suggestion: {error.suggestion if error.suggestion else 'Check parameter value and valid range'}

Context: {context}
"""

    def _generate_architecture_fix(
        self,
        error: ValidationError,
        template_name: Optional[str]
    ) -> str:
        """Generate fix for architecture validation errors."""
        context = error.context
        architecture_type = context.get('architecture', 'unknown')

        # Check for specific architecture pattern fixes
        if architecture_type in self.ARCHITECTURE_FIXES:
            return self.ARCHITECTURE_FIXES[architecture_type]

        # Check for specific layer/component issues
        layer = context.get('layer', context.get('component', 'unknown'))

        return f"""FIX: Correct architecture issue in {layer}

Error: {error.message}
Suggestion: {error.suggestion if error.suggestion else 'Verify architecture implementation'}

Required Components: {context.get('required_parameters', 'See documentation')}

**Architecture Type**: {architecture_type}
**Missing/Incorrect**: {layer}
"""

    def _generate_data_fix(
        self,
        error: ValidationError,
        template_name: Optional[str]
    ) -> str:
        """Generate fix for data access validation errors."""
        context = error.context
        dataset_key = context.get('dataset_key', '')

        # Check for duplicate calls
        if 'duplicate' in error.message.lower():
            return self.DATA_ACCESS_FIXES['duplicate_calls']

        # Check for excessive calls
        total_calls = context.get('total_calls', 0)
        if total_calls > 10:
            return self.DATA_ACCESS_FIXES['excessive_calls']

        # Dataset not found error
        if 'unknown dataset' in error.message.lower():
            similar_datasets = context.get('similar_datasets', [])
            suggestions_text = f"Did you mean: {', '.join(similar_datasets)}" if similar_datasets else "Check Finlab documentation"

            return f"""FIX: Use valid dataset key instead of '{dataset_key}'

Error: {error.message}

{suggestions_text}

Common Valid Datasets:
- 'price:收盤價' (Close price)
- 'price:成交股數' (Trading volume)
- 'monthly_revenue:當月營收' (Monthly revenue)
- 'monthly_revenue:去年同月增減(%)' (YoY revenue growth)
- 'fundamental_features:本益比' (P/E ratio)
- 'fundamental_features:營業利益率' (Operating margin)

Example:
```python
# ❌ WRONG
data = data.get('{dataset_key}')  # Invalid dataset key

# ✅ CORRECT
data = data.get('price:收盤價')  # Valid dataset key
```
"""

        # Generic data fix
        return f"""FIX: Correct data access issue

Error: {error.message}
Suggestion: {error.suggestion if error.suggestion else 'Verify dataset key and access pattern'}

Context: {context}
"""

    def _generate_backtest_fix(
        self,
        error: ValidationError,
        template_name: Optional[str]
    ) -> str:
        """Generate fix for backtest configuration errors."""
        context = error.context

        return f"""FIX: Correct backtest configuration

Error: {error.message}
Suggestion: {error.suggestion if error.suggestion else 'Verify backtest parameters'}

Valid Resample Frequencies: 'D' (daily), 'W-FRI' (weekly), 'M' (monthly), 'Q' (quarterly), 'Y' (yearly)

Risk Management Example:
```python
backtest_config = {{
    'resample': 'M',  # Monthly rebalancing
    'stop_loss': 0.06,  # 6% maximum loss
    'take_profit': 0.50,  # 50% target profit
    'position_limit': 0.125,  # 12.5% max position size
    'fee_ratio': 1.425/1000/3  # Taiwan stock transaction fee
}}
```

Context: {context}
"""

    def _generate_generic_fix(self, error: ValidationError) -> str:
        """Generate generic fix for unknown error categories."""
        return f"""FIX: Address validation error

Severity: {error.severity.value}
Category: {error.category.value}
Error: {error.message}

Suggestion: {error.suggestion if error.suggestion else 'Review error message and context'}

Context: {error.context}

**Line Number**: {error.line_number if error.line_number else 'N/A'}
"""

    def generate_batch_fixes(
        self,
        errors: List[ValidationError],
        template_name: Optional[str] = None
    ) -> str:
        """
        Generate fix suggestions for multiple errors.

        Args:
            errors: List of ValidationError objects
            template_name: Optional template name for context

        Returns:
            Formatted fix suggestion string for all errors

        Example:
            >>> errors = [error1, error2, error3]
            >>> suggestions = suggestor.generate_batch_fixes(errors, 'TurtleTemplate')
            >>> print(suggestions)
        """
        if not errors:
            return "No errors to fix ✅"

        fixes = [f"### Error {i+1}/{len(errors)}: {error.severity.value}\n{self.generate_fix_suggestion(error, template_name)}"
                 for i, error in enumerate(errors)]

        return f"""# Validation Error Fixes ({len(errors)} issues)

{chr(10).join(fixes)}

---

**Summary**: {len(errors)} errors found
- CRITICAL: {len([e for e in errors if e.severity == Severity.CRITICAL])}
- MODERATE: {len([e for e in errors if e.severity == Severity.MODERATE])}
- LOW: {len([e for e in errors if e.severity == Severity.LOW])}
"""
