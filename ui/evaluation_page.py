"""Evaluation metrics and research summary page."""

from __future__ import annotations

import streamlit as st

from .charts import gauge_chart
from .components import empty_state, execution_logs, metric_card, page_header, section_title
from .utils import complete_report, json_text


def render() -> None:
    """Render negotiation metrics with gauges and progress indicators."""

    page_header(
        "Research evaluation",
        "Measure the quality of the negotiated outcome.",
        "Evaluation summarizes agreement, efficiency, concession behavior, and party satisfaction using the existing metrics module.",
    )
    metrics = st.session_state.evaluation
    if metrics is None:
        empty_state("◉", "No evaluation available", "Run a negotiation to calculate satisfaction and agreement metrics.")
        execution_logs()
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Agreement Rate", f"{metrics.agreement_rate:.1%}", "Successful agreements", "✓", "green")
    with c2:
        metric_card("Success Rate", f"{metrics.negotiation_success_rate:.1%}", f"{metrics.total_runs} evaluated run(s)", "↗")
    with c3:
        metric_card("Average Rounds", f"{metrics.average_negotiation_rounds:.1f}", "Negotiation efficiency", "↻", "purple")
    with c4:
        metric_card("Execution Time", f"{metrics.average_negotiation_time * 1000:.1f} ms", "Average duration", "◷", "amber")

    section_title("Satisfaction gauges", "Normalized utility achieved by each party.")
    gauges = st.columns(3)
    overall = (metrics.user_satisfaction + metrics.provider_satisfaction) / 2
    with gauges[0]:
        st.plotly_chart(gauge_chart(metrics.user_satisfaction, "User satisfaction"), use_container_width=True, config={"displayModeBar": False})
    with gauges[1]:
        st.plotly_chart(gauge_chart(metrics.provider_satisfaction, "Provider satisfaction", "#06B6D4"), use_container_width=True, config={"displayModeBar": False})
    with gauges[2]:
        st.plotly_chart(gauge_chart(overall, "Overall satisfaction", "#8B5CF6"), use_container_width=True, config={"displayModeBar": False})

    section_title("Progress summary")
    st.caption("Agreement rate")
    st.progress(metrics.agreement_rate)
    st.caption("Negotiation success")
    st.progress(metrics.negotiation_success_rate)
    st.caption("Overall satisfaction")
    st.progress(overall)

    if metrics.concession_statistics:
        section_title("Concession statistics")
        st.json(metrics.concession_statistics, expanded=True)

    st.download_button(
        "Download complete report JSON",
        json_text(complete_report()),
        file_name="irnam_complete_report.json",
        mime="application/json",
    )
    execution_logs()
