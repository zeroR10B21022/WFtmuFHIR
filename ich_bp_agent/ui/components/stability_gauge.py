"""
Stability Score Gauge Component
"""
import plotly.graph_objects as go


def create_stability_gauge(
    score: float,
    title: str = "穩定度分數",
) -> go.Figure:
    """
    Create a gauge chart for stability score

    Args:
        score: Stability score (0-100)
        title: Chart title

    Returns:
        Plotly Figure object
    """
    # Determine color based on score
    if score >= 80:
        bar_color = "#4caf50"  # Green
    elif score >= 60:
        bar_color = "#ff9800"  # Orange
    elif score >= 40:
        bar_color = "#ff5722"  # Deep Orange
    else:
        bar_color = "#f44336"  # Red

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        number={'font': {'size': 40}, 'suffix': '/100'},
        gauge={
            'axis': {
                'range': [0, 100],
                'tickwidth': 1,
                'tickcolor': "darkgray",
                'dtick': 20,
            },
            'bar': {'color': bar_color, 'thickness': 0.75},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(244, 67, 54, 0.3)'},
                {'range': [40, 60], 'color': 'rgba(255, 152, 0, 0.3)'},
                {'range': [60, 80], 'color': 'rgba(255, 235, 59, 0.3)'},
                {'range': [80, 100], 'color': 'rgba(76, 175, 80, 0.3)'},
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80,
            },
        },
    ))

    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig


def create_mini_gauge(
    score: float,
    label: str = "",
    height: int = 150,
) -> go.Figure:
    """
    Create a mini gauge for dashboard cards

    Args:
        score: Score value (0-100)
        label: Label text
        height: Chart height

    Returns:
        Plotly Figure object
    """
    # Determine color
    if score >= 80:
        color = "#4caf50"
    elif score >= 60:
        color = "#ff9800"
    elif score >= 40:
        color = "#ff5722"
    else:
        color = "#f44336"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'size': 24}},
        gauge={
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': color, 'thickness': 0.8},
            'bgcolor': "#e0e0e0",
            'borderwidth': 0,
        },
    ))

    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        annotations=[
            dict(
                text=label,
                x=0.5,
                y=-0.1,
                font=dict(size=12),
                showarrow=False,
            )
        ] if label else [],
    )

    return fig
