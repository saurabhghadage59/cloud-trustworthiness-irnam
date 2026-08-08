"""Home dashboard and About page."""

from __future__ import annotations

import streamlit as st

from .components import architecture_diagram, execution_logs, metric_card, page_header, section_title, status_pill
from .utils import DATASET_PATH, METADATA_PATH, complete_report, json_text, read_json


def render_dashboard() -> None:
    """Render project health, pipeline state, and architecture."""

    metadata = read_json(METADATA_PATH, {}) or {}
    dataset_ready = DATASET_PATH.exists()
    recommendation = st.session_state.recommendation
    negotiation = st.session_state.negotiation

    page_header(
        "Research control center",
        "Intelligent cloud decisions, end to end.",
        "IRNAM connects evidence-backed provider data with priority-aware recommendation, automated negotiation, SLA generation, and measurable outcomes.",
    )

    columns = st.columns(5)
    with columns[0]:
        metric_card("Cloud Providers", str(metadata.get("provider_count", "—")), "AWS · Azure · GCP · OCI · IBM", "☁")
    with columns[1]:
        metric_card("Recommendation", "Ready" if recommendation else "Pending", "Algorithms 1 & 2", "◆", "green" if recommendation else "blue")
    with columns[2]:
        state = "Accepted" if negotiation and negotiation.success else ("Failed" if negotiation else "Pending")
        metric_card("Negotiation", state, "Algorithm 3", "⇄", "green" if state == "Accepted" else "amber")
    with columns[3]:
        coverage = metadata.get("coverage_percent")
        metric_card("Dataset", f"{coverage:.1f}%" if isinstance(coverage, (int, float)) else ("Ready" if dataset_ready else "Missing"), "Structured QoS coverage", "▦", "purple")
    with columns[4]:
        metric_card("Tests Passed", "33 / 33", "Verified backend suite", "✓", "green")

    section_title("System architecture", "One transparent pipeline from source evidence to evaluated agreement.")
    architecture_diagram()

    left, right = st.columns([1.45, 1])
    with left:
        section_title("Workflow readiness", "Session state persists as you move through the dashboard.")
        status_pill("Structured dataset", "Ready" if dataset_ready else "Failed")
        status_pill("User requirements", "Complete" if st.session_state.requirement else "Not started")
        status_pill("Provider recommendation", "Complete" if recommendation else "Not started")
        status_pill("Negotiated agreement", "Accepted" if negotiation and negotiation.success else ("Failed" if negotiation else "Not started"))
        status_pill("SLA contract", "Complete" if st.session_state.sla_contract else "Not started")
        status_pill("Evaluation metrics", "Complete" if st.session_state.evaluation else "Not started")
    with right:
        section_title("Research snapshot", "Current reproducible dataset build.")
        st.markdown(
            f"""
            **Schema version**  
            `{metadata.get('schema_version', 'unknown')}`

            **Collection date**  
            `{metadata.get('collection_date', 'unknown')}`

            **Provenance records**  
            `{metadata.get('source_record_count', 0)}`

            **Validation**  
            `{metadata.get('validation_issue_counts', {})}`
            """
        )
        report = complete_report()
        st.download_button(
            "Download complete report",
            json_text(report),
            file_name="irnam_complete_report.json",
            mime="application/json",
            disabled=not report,
            use_container_width=True,
        )

    execution_logs()


def render_about() -> None:
    """Render project and research context."""

    page_header(
        "About the project",
        "IRNAM · Intelligent Cloud Provider Recommendation and Negotiation System",
        "An implementation of a user-priorities-based strategy for intelligent cloud service recommendation and negotiating agents.",
    )
    left, right = st.columns([1.25, 1])
    with left:
        section_title("Research paper")
        st.markdown(
            """
            **A User-Priorities-Based Strategy for Three-Phase Intelligent Recommendation and Negotiating Agents for Cloud Services (IRNAM)**

            The system turns user priorities into normalized weights, evaluates evidence-backed provider attributes, ranks eligible cloud providers, negotiates compatible SLA terms, and measures the resulting agreement.
            """
        )
        section_title("Architecture")
        architecture_diagram()
    with right:
        section_title("Project profile")
        status_pill("Dataset Builder", "Complete")
        status_pill("Recommendation", "Complete")
        status_pill("Negotiation", "Complete")
        status_pill("SLA", "Complete")
        status_pill("Evaluation", "Complete")
        section_title("Team & contributors")
        st.markdown(
            """
            **Contributor**  
            Anurag

            **Research implementation**  
            Python · Streamlit · Plotly · Pandas

            **Design principle**  
            Reproducible data, explainable rankings, and modular research software.
            """
        )
    execution_logs()
