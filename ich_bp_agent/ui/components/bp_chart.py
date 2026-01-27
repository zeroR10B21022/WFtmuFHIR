"""
Blood Pressure Trend Chart Component
"""
import plotly.graph_objects as go
from typing import List, Tuple
from datetime import datetime


def create_bp_trend_chart(
    readings: List,  # List of BPReading
    target_systolic: Tuple[int, int],
    target_diastolic: Tuple[int, int],
    title: str = "血壓趨勢圖",
) -> go.Figure:
    """
    Create an interactive blood pressure trend chart

    Args:
        readings: List of BP readings
        target_systolic: (min, max) target range for systolic
        target_diastolic: (min, max) target range for diastolic
        title: Chart title

    Returns:
        Plotly Figure object
    """
    # Sort readings by timestamp
    sorted_readings = sorted(readings, key=lambda x: x.timestamp)

    # Extract data
    timestamps = [r.timestamp for r in sorted_readings]
    systolic_values = [r.systolic for r in sorted_readings]
    diastolic_values = [r.diastolic for r in sorted_readings]

    fig = go.Figure()

    # Add target range bands
    # Systolic target band
    fig.add_hrect(
        y0=target_systolic[0],
        y1=target_systolic[1],
        fillcolor="rgba(76, 175, 80, 0.1)",
        line_width=0,
        annotation_text="收縮壓目標範圍",
        annotation_position="top left",
    )

    # Diastolic target band
    fig.add_hrect(
        y0=target_diastolic[0],
        y1=target_diastolic[1],
        fillcolor="rgba(33, 150, 243, 0.1)",
        line_width=0,
        annotation_text="舒張壓目標範圍",
        annotation_position="bottom left",
    )

    # Add systolic line
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=systolic_values,
        mode='lines+markers',
        name='收縮壓',
        line=dict(color='#e53935', width=2),
        marker=dict(size=8),
        hovertemplate='%{x|%m/%d %H:%M}<br>收縮壓: %{y} mmHg<extra></extra>',
    ))

    # Add diastolic line
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=diastolic_values,
        mode='lines+markers',
        name='舒張壓',
        line=dict(color='#1e88e5', width=2),
        marker=dict(size=8),
        hovertemplate='%{x|%m/%d %H:%M}<br>舒張壓: %{y} mmHg<extra></extra>',
    ))

    # Add alert threshold lines
    fig.add_hline(
        y=180,
        line_dash="dash",
        line_color="darkred",
        annotation_text="高血壓危象",
        annotation_position="right",
    )

    fig.add_hline(
        y=90,
        line_dash="dash",
        line_color="orange",
        annotation_text="低血壓警戒",
        annotation_position="right",
    )

    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=18),
        ),
        xaxis_title="日期時間",
        yaxis_title="血壓 (mmHg)",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        yaxis=dict(
            range=[50, 200],
            dtick=20,
        ),
    )

    return fig


def create_mini_bp_chart(
    readings: List,
    height: int = 200,
) -> go.Figure:
    """
    Create a mini BP chart for dashboard cards

    Args:
        readings: List of BP readings (last 7 days)
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    sorted_readings = sorted(readings, key=lambda x: x.timestamp)[-14:]  # Last 14 readings

    timestamps = [r.timestamp for r in sorted_readings]
    systolic_values = [r.systolic for r in sorted_readings]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=timestamps,
        y=systolic_values,
        mode='lines',
        name='收縮壓',
        line=dict(color='#e53935', width=2),
        fill='tozeroy',
        fillcolor='rgba(229, 57, 53, 0.1)',
    ))

    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    return fig
