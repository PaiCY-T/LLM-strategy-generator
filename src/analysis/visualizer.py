"""
Analysis visualization with interactive plotly charts.

Creates visualizations for suggestions, impact analysis, and learning metrics.
"""

import logging
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from plotly.graph_objs import Figure  # type: ignore[import-not-found,import-untyped]
else:
    Figure = Any

from . import AnalysisReport, Suggestion

# Configure logging
logger = logging.getLogger(__name__)


class AnalysisVisualizer:
    """Creates visualizations for analysis results.

    Generates interactive plotly charts for suggestions, priorities,
    and learning metrics.
    """

    def __init__(self) -> None:
        """Initialize visualizer."""
        logger.info("AnalysisVisualizer initialized")

    def create_suggestion_chart(
        self,
        suggestions: List[Suggestion],
        max_suggestions: int = 10
    ) -> Figure:
        """Create scatter plot of suggestions by impact and difficulty.

        Args:
            suggestions: List of suggestions to visualize
            max_suggestions: Maximum number of suggestions to show

        Returns:
            Plotly figure
        """
        import plotly.graph_objects as go  # type: ignore[import-untyped,import-not-found]

        # Limit suggestions
        suggestions = suggestions[:max_suggestions]

        if not suggestions:
            logger.warning("No suggestions to visualize")
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(title="No Suggestions Available")
            return fig

        # Extract data
        titles = [s.title[:50] + "..." if len(s.title) > 50 else s.title
                  for s in suggestions]
        impact = [s.impact_score for s in suggestions]
        difficulty = [s.difficulty_score for s in suggestions]
        priority = [s.priority_score for s in suggestions]
        categories = [s.category.value for s in suggestions]

        # Create scatter plot
        fig = go.Figure(data=go.Scatter(
            x=difficulty,
            y=impact,
            mode='markers+text',
            marker=dict(
                size=[max(p * 5, 10) for p in priority],  # Size by priority
                color=priority,
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Priority Score"),
                line=dict(width=1, color='DarkSlateGrey')
            ),
            text=[f"{i+1}" for i in range(len(suggestions))],
            textposition="middle center",
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Impact: %{y:.1f}<br>"
                "Difficulty: %{x:.1f}<br>"
                "Priority: %{customdata[1]:.2f}<br>"
                "Category: %{customdata[2]}<br>"
                "<extra></extra>"
            ),
            customdata=[
                [titles[i], priority[i], categories[i]]
                for i in range(len(suggestions))
            ]
        ))

        # Update layout
        fig.update_layout(
            title="Suggestion Impact vs. Difficulty Analysis",
            xaxis_title="Implementation Difficulty (1-10)",
            yaxis_title="Expected Impact (1-10)",
            hovermode='closest',
            showlegend=False,
            width=800,
            height=600,
            # Add quadrant lines
            shapes=[
                # Vertical line at x=5
                dict(
                    type="line",
                    x0=5, x1=5,
                    y0=0, y1=10,
                    line=dict(color="gray", width=1, dash="dot")
                ),
                # Horizontal line at y=5
                dict(
                    type="line",
                    x0=0, x1=10,
                    y0=5, y1=5,
                    line=dict(color="gray", width=1, dash="dot")
                )
            ],
            annotations=[
                dict(
                    x=2.5, y=9,
                    text="<b>High Impact<br>Low Difficulty</b>",
                    showarrow=False,
                    font=dict(color="green", size=10)
                ),
                dict(
                    x=7.5, y=9,
                    text="<b>High Impact<br>High Difficulty</b>",
                    showarrow=False,
                    font=dict(color="orange", size=10)
                ),
                dict(
                    x=2.5, y=1,
                    text="<b>Low Impact<br>Low Difficulty</b>",
                    showarrow=False,
                    font=dict(color="gray", size=10)
                ),
                dict(
                    x=7.5, y=1,
                    text="<b>Low Impact<br>High Difficulty</b>",
                    showarrow=False,
                    font=dict(color="red", size=10)
                )
            ]
        )

        logger.info(f"Created suggestion chart with {len(suggestions)} suggestions")
        return fig

    def create_priority_chart(self, suggestions: List[Suggestion]) -> Figure:
        """Create bar chart of suggestions by priority.

        Args:
            suggestions: List of suggestions (should be pre-ranked)

        Returns:
            Plotly figure
        """
        import plotly.graph_objects as go  # type: ignore[import-untyped,import-not-found]

        if not suggestions:
            logger.warning("No suggestions to visualize")
            fig = go.Figure()
            fig.update_layout(title="No Suggestions Available")
            return fig

        # Extract data
        titles = [f"{i+1}. {s.title[:40]}..." if len(s.title) > 40
                  else f"{i+1}. {s.title}"
                  for i, s in enumerate(suggestions)]
        priorities = [s.priority_score for s in suggestions]
        colors = ['green' if p > 5 else 'orange' if p > 2 else 'red'
                  for p in priorities]

        # Create bar chart
        fig = go.Figure(data=go.Bar(
            x=priorities,
            y=titles,
            orientation='h',
            marker=dict(
                color=colors,
                line=dict(width=1, color='DarkSlateGrey')
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Priority Score: %{x:.2f}<br>"
                "<extra></extra>"
            )
        ))

        # Update layout
        fig.update_layout(
            title="Suggestions Ranked by Priority",
            xaxis_title="Priority Score",
            yaxis_title="",
            yaxis=dict(autorange="reversed"),  # Highest priority at top
            width=800,
            height=max(400, len(suggestions) * 40),
            showlegend=False
        )

        logger.info(f"Created priority chart with {len(suggestions)} suggestions")
        return fig

    def create_category_distribution(self, suggestions: List[Suggestion]) -> Figure:
        """Create pie chart of suggestions by category.

        Args:
            suggestions: List of suggestions

        Returns:
            Plotly figure
        """
        import plotly.graph_objects as go  # type: ignore[import-untyped,import-not-found]

        if not suggestions:
            logger.warning("No suggestions to visualize")
            fig = go.Figure()
            fig.update_layout(title="No Suggestions Available")
            return fig

        # Count by category
        category_counts: Dict[str, int] = {}
        for s in suggestions:
            cat = s.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Create pie chart
        fig = go.Figure(data=go.Pie(
            labels=list(category_counts.keys()),
            values=list(category_counts.values()),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Count: %{value}<br>"
                "Percentage: %{percent}<br>"
                "<extra></extra>"
            )
        ))

        fig.update_layout(
            title="Suggestion Distribution by Category",
            width=600,
            height=500
        )

        logger.info(f"Created category distribution with {len(category_counts)} categories")
        return fig

    def create_learning_metrics_chart(self, learning_insights: Dict[str, Any]) -> Figure:
        """Create visualization of learning metrics.

        Args:
            learning_insights: Learning insights from learning engine

        Returns:
            Plotly figure
        """
        import plotly.graph_objects as go  # type: ignore[import-untyped,import-not-found]
        from plotly.subplots import make_subplots  # type: ignore[import-untyped,import-not-found]

        if learning_insights["total_feedback"] == 0:
            logger.warning("No learning data to visualize")
            fig = go.Figure()
            fig.update_layout(title="No Learning Data Available")
            return fig

        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Overall Acceptance Rate",
                "Category Acceptance Rates",
                "Top Performing Categories",
                "Improvement Accuracy"
            ),
            specs=[
                [{"type": "indicator"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "indicator"}]
            ]
        )

        # 1. Overall acceptance rate (gauge)
        acceptance_rate = learning_insights["overall_acceptance_rate"]
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=acceptance_rate * 100,
                title={'text': "Acceptance Rate (%)"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 30], 'color': "lightgray"},
                        {'range': [30, 70], 'color': "lightblue"},
                        {'range': [70, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 50
                    }
                }
            ),
            row=1, col=1
        )

        # 2. Category acceptance rates
        category_insights = learning_insights["category_insights"]
        if category_insights:
            categories = list(category_insights.keys())
            rates = [
                category_insights[cat]["acceptance_rate"] * 100
                for cat in categories
            ]

            fig.add_trace(
                go.Bar(
                    x=categories,
                    y=rates,
                    marker_color='lightblue',
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Acceptance Rate: %{y:.1f}%<br>"
                        "<extra></extra>"
                    )
                ),
                row=1, col=2
            )

        # 3. Top categories by improvement
        top_categories = learning_insights.get("top_categories", [])
        if top_categories:
            top_cats = [c["category"] for c in top_categories]
            top_scores = [c["avg_improvement"] * 100 for c in top_categories]

            fig.add_trace(
                go.Bar(
                    x=top_cats,
                    y=top_scores,
                    marker_color='lightgreen',
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Avg Improvement: %{y:.2f}%<br>"
                        "<extra></extra>"
                    )
                ),
                row=2, col=1
            )

        # 4. Improvement accuracy (gauge)
        accuracy = learning_insights.get("improvement_accuracy", 0.0)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=accuracy * 100,
                title={'text': "Prediction Accuracy (%)"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 75], 'color': "lightyellow"},
                        {'range': [75, 100], 'color': "lightgreen"}
                    ]
                }
            ),
            row=2, col=2
        )

        # Update layout
        fig.update_layout(
            title_text="Learning Metrics Dashboard",
            showlegend=False,
            width=1000,
            height=800
        )

        logger.info("Created learning metrics chart")
        return fig

    def create_report_visualizations(
        self,
        report: AnalysisReport
    ) -> Dict[str, Figure]:
        """Create all visualizations for an analysis report.

        Args:
            report: Analysis report

        Returns:
            Dictionary mapping chart names to figures
        """
        visualizations = {
            "suggestion_scatter": self.create_suggestion_chart(report.suggestions),
            "priority_ranking": self.create_priority_chart(report.suggestions),
            "category_distribution": self.create_category_distribution(report.suggestions)
        }

        logger.info(f"Created {len(visualizations)} visualizations for report")
        return visualizations
