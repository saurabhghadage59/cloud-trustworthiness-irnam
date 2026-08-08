"""Plotly chart factory functions for IRNAM UI pages."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import pandas as pd
import plotly.graph_objects as go


BLUE = "#2563EB"
CYAN = "#06B6D4"
NAVY = "#0F172A"
MUTED = "#64748B"
GRID = "#E2E8F0"
PALETTE = [BLUE, CYAN, "#8B5CF6", "#14B8A6", "#F59E0B"]


def _finish(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=24, r=24, t=48, b=24),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color=NAVY),
        hoverlabel=dict(bgcolor="white", font_color=NAVY),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def radar_chart(attribute_scores: Mapping[str, float], title: str = "Priority fit") -> go.Figure:
    labels = [name.replace("_", " ").title() for name in attribute_scores]
    values = list(attribute_scores.values())
    if values:
        labels.append(labels[0])
        values.append(values[0])
    fig = go.Figure(go.Scatterpolar(r=values, theta=labels, fill="toself", line_color=BLUE, fillcolor="rgba(37,99,235,.18)"))
    fig.update_polars(radialaxis=dict(range=[0, 1], gridcolor=GRID, tickfont=dict(color=MUTED)), angularaxis=dict(gridcolor=GRID))
    fig.update_layout(title=title, showlegend=False)
    return _finish(fig, 390)


def overall_score_chart(ranking: Sequence[Any]) -> go.Figure:
    providers = [entry.provider for entry in ranking][::-1]
    scores = [entry.overall_score for entry in ranking][::-1]
    colors = ["#BFDBFE"] * len(scores)
    if colors:
        colors[-1] = BLUE
    fig = go.Figure(go.Bar(x=scores, y=providers, orientation="h", marker_color=colors, text=[f"{score:.3f}" for score in scores], textposition="outside"))
    fig.update_xaxes(range=[0, max(1.0, max(scores, default=1) * 1.15)], gridcolor=GRID, title="Overall score")
    fig.update_yaxes(title=None)
    fig.update_layout(title="Provider ranking", showlegend=False)
    return _finish(fig, 370)


def provider_comparison_chart(ranking: Sequence[Any]) -> go.Figure:
    frame = pd.DataFrame({entry.provider: entry.attribute_scores for entry in ranking}).fillna(0)
    fig = go.Figure()
    for index, provider in enumerate(frame.columns):
        fig.add_trace(go.Bar(name=provider, x=[name.replace("_", " ").title() for name in frame.index], y=frame[provider], marker_color=PALETTE[index % len(PALETTE)]))
    fig.update_yaxes(range=[0, 1.05], gridcolor=GRID, title="Evaluation score")
    fig.update_layout(title="Provider comparison", barmode="group")
    return _finish(fig, 410)


def priority_pie_chart(weights: Mapping[str, float]) -> go.Figure:
    fig = go.Figure(go.Pie(labels=[name.replace("_", " ").title() for name in weights], values=list(weights.values()), hole=.58, marker_colors=PALETTE * 3, textinfo="percent"))
    fig.update_layout(title="User priority distribution", annotations=[dict(text="Weights", x=.5, y=.5, font_size=14, showarrow=False)])
    return _finish(fig, 390)


def heatmap_chart(ranking: Sequence[Any]) -> go.Figure:
    if not ranking:
        return _finish(go.Figure(), 350)
    attributes = list(ranking[0].attribute_scores)
    values = [[entry.attribute_scores.get(attribute, 0.0) for attribute in attributes] for entry in ranking]
    fig = go.Figure(go.Heatmap(z=values, x=[a.replace("_", " ").title() for a in attributes], y=[entry.provider for entry in ranking], colorscale=[[0, "#EFF6FF"], [1, BLUE]], zmin=0, zmax=1, colorbar=dict(title="Score")))
    fig.update_layout(title="Attribute score heatmap")
    return _finish(fig, 350)


def negotiation_timeline(rounds: Sequence[Any]) -> go.Figure:
    numbers = [item.round_number for item in rounds]
    concessions = [item.concession for item in rounds]
    user_scores = [item.user_aggregate for item in rounds]
    provider_scores = [item.provider_aggregate for item in rounds]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=numbers, y=user_scores, mode="lines+markers", name="User utility", line=dict(color=BLUE, width=3)))
    fig.add_trace(go.Scatter(x=numbers, y=provider_scores, mode="lines+markers", name="Provider utility", line=dict(color=CYAN, width=3)))
    fig.add_trace(go.Bar(x=numbers, y=concessions, name="Concession", marker_color="rgba(139,92,246,.25)"))
    fig.update_xaxes(title="Negotiation round", dtick=1, gridcolor=GRID)
    fig.update_yaxes(title="Normalized value", gridcolor=GRID)
    fig.update_layout(title="Negotiation timeline", barmode="overlay")
    return _finish(fig, 400)


def gauge_chart(value: float, title: str, color: str = BLUE) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value * 100,
        number={"suffix": "%", "font": {"size": 28, "color": NAVY}},
        title={"text": title, "font": {"size": 14, "color": MUTED}},
        gauge={"axis": {"range": [0, 100], "visible": False}, "bar": {"color": color, "thickness": .28}, "bgcolor": "#EAF2FF", "borderwidth": 0},
    ))
    return _finish(fig, 220)
