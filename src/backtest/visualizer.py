"""
Backtest visualization generator using Plotly.

Creates interactive charts for backtest analysis including:
- Equity curve (cumulative returns over time)
- Drawdown chart (underwater equity)
- Trade distribution (profit/loss histogram)
"""

import logging
from typing import TYPE_CHECKING, Any, Dict

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from plotly.graph_objs import Figure  # type: ignore[import-not-found]
    import plotly.graph_objs as go  # type: ignore[import-not-found]
else:
    Figure = Any
    try:
        import plotly.graph_objs as go  # type: ignore[import-not-found]
    except ImportError:
        go = None  # type: ignore[assignment]

from ..backtest import BacktestResult

# Configure logging
logger = logging.getLogger(__name__)


def generate_visualizations(backtest_result: BacktestResult) -> Dict[str, Figure]:
    """Generate visualization charts for backtest results.

    Creates three main charts:
    1. Equity curve - cumulative returns over time
    2. Drawdown chart - underwater equity chart
    3. Trade distribution - profit/loss histogram

    Args:
        backtest_result: Result from backtest execution

    Returns:
        Dictionary mapping chart names to Plotly figures:
        - 'equity_curve': Line chart of cumulative returns
        - 'drawdown': Area chart of drawdown over time
        - 'trade_distribution': Histogram of trade returns

    Example:
        >>> charts = generate_visualizations(backtest_result)
        >>> charts['equity_curve'].show()
    """
    # Check if plotly is available
    if go is None:
        logger.error("Plotly not available, cannot generate visualizations")
        return {
            'equity_curve': _create_error_figure('Equity Curve', 'Plotly not installed'),
            'drawdown': _create_error_figure('Drawdown', 'Plotly not installed'),
            'trade_distribution': _create_error_figure('Trade Distribution', 'Plotly not installed')
        }

    charts = {}

    # Generate equity curve chart
    try:
        charts['equity_curve'] = _create_equity_curve_chart(
            backtest_result.equity_curve
        )
    except Exception as e:
        logger.error(f"Failed to create equity curve chart: {e}")
        charts['equity_curve'] = _create_error_figure(
            "Equity Curve",
            f"Failed to generate chart: {e}"
        )

    # Generate drawdown chart
    try:
        charts['drawdown'] = _create_drawdown_chart(
            backtest_result.equity_curve
        )
    except Exception as e:
        logger.error(f"Failed to create drawdown chart: {e}")
        charts['drawdown'] = _create_error_figure(
            "Drawdown",
            f"Failed to generate chart: {e}"
        )

    # Generate trade distribution chart
    try:
        charts['trade_distribution'] = _create_trade_distribution_chart(
            backtest_result.trade_records
        )
    except Exception as e:
        logger.error(f"Failed to create trade distribution chart: {e}")
        charts['trade_distribution'] = _create_error_figure(
            "Trade Distribution",
            f"Failed to generate chart: {e}"
        )

    return charts


def _create_equity_curve_chart(equity_curve: pd.Series) -> Figure:
    """Create equity curve line chart.

    Args:
        equity_curve: Series of equity values over time

    Returns:
        Plotly Figure with equity curve
    """
    if len(equity_curve) == 0:
        return _create_error_figure(
            "Equity Curve",
            "No equity data available"
        )

    # Calculate cumulative returns
    if equity_curve.iloc[0] != 0:
        cumulative_returns = (equity_curve / equity_curve.iloc[0] - 1) * 100
    else:
        cumulative_returns = pd.Series([0] * len(equity_curve), index=equity_curve.index)

    # Create line chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=equity_curve.index,
        y=cumulative_returns.values,
        mode='lines',
        name='Cumulative Returns',
        line=dict(color='#2196F3', width=2),
        hovertemplate='<b>Date</b>: %{x}<br>' +
                      '<b>Return</b>: %{y:.2f}%<br>' +
                      '<extra></extra>'
    ))

    # Add zero line
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        opacity=0.5
    )

    # Update layout
    fig.update_layout(
        title='Equity Curve - Cumulative Returns',
        xaxis_title='Date',
        yaxis_title='Cumulative Return (%)',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )

    return fig


def _create_drawdown_chart(equity_curve: pd.Series) -> Figure:
    """Create drawdown area chart (underwater equity).

    Args:
        equity_curve: Series of equity values over time

    Returns:
        Plotly Figure with drawdown chart
    """
    if len(equity_curve) == 0:
        return _create_error_figure(
            "Drawdown",
            "No equity data available"
        )

    # Calculate drawdown
    running_max = equity_curve.expanding().max()
    drawdown = (equity_curve - running_max) / running_max * 100

    # Create area chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=equity_curve.index,
        y=drawdown.values,
        mode='lines',
        name='Drawdown',
        fill='tozeroy',
        line=dict(color='#F44336', width=0),
        fillcolor='rgba(244, 67, 54, 0.3)',
        hovertemplate='<b>Date</b>: %{x}<br>' +
                      '<b>Drawdown</b>: %{y:.2f}%<br>' +
                      '<extra></extra>'
    ))

    # Add zero line
    fig.add_hline(
        y=0,
        line_dash="solid",
        line_color="gray",
        opacity=0.5
    )

    # Update layout
    fig.update_layout(
        title='Drawdown - Underwater Equity',
        xaxis_title='Date',
        yaxis_title='Drawdown (%)',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )

    return fig


def _create_trade_distribution_chart(trade_records: pd.DataFrame) -> Figure:
    """Create trade profit/loss distribution histogram.

    Args:
        trade_records: DataFrame of trade records

    Returns:
        Plotly Figure with trade distribution histogram
    """
    if len(trade_records) == 0:
        return _create_error_figure(
            "Trade Distribution",
            "No trade data available"
        )

    # Find P&L column
    pnl_col = None
    for col in ['pnl', 'profit_loss', 'return_pct', 'returns']:
        if col in trade_records.columns:
            pnl_col = col
            break

    if pnl_col is None:
        return _create_error_figure(
            "Trade Distribution",
            "No profit/loss column found in trade records"
        )

    pnl_values = trade_records[pnl_col]

    # Create histogram with color-coded bars
    fig = go.Figure()

    # Calculate bin colors (green for profit, red for loss)
    pnl_array = pnl_values.to_numpy()
    hist, bin_edges = np.histogram(pnl_array, bins=30)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    colors = ['#4CAF50' if bc >= 0 else '#F44336' for bc in bin_centers]

    fig.add_trace(go.Histogram(
        x=pnl_values.tolist(),
        nbinsx=30,
        name='Trades',
        marker=dict(
            color=colors,
            line=dict(color='white', width=1)
        ),
        hovertemplate='<b>Return Range</b>: %{x:.2f}%<br>' +
                      '<b>Count</b>: %{y}<br>' +
                      '<extra></extra>'
    ))

    # Add zero line
    fig.add_vline(
        x=0,
        line_dash="dash",
        line_color="gray",
        opacity=0.7
    )

    # Update layout
    fig.update_layout(
        title='Trade Distribution - Profit/Loss',
        xaxis_title='Trade Return (%)',
        yaxis_title='Number of Trades',
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        bargap=0.1
    )

    return fig


def _create_error_figure(title: str, message: str) -> Any:
    """Create error placeholder figure.

    Args:
        title: Chart title
        message: Error message to display

    Returns:
        Plotly Figure with error message or dict if plotly unavailable
    """
    if go is None:
        return {'title': title, 'error': message}

    fig = go.Figure()

    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color="red")
    )

    fig.update_layout(
        title=title,
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    return fig
