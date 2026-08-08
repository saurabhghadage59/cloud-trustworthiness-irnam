"""Reusable visual components for the Streamlit dashboard."""

from __future__ import annotations

import html

import streamlit as st
import streamlit.components.v1 as components

from .utils import ROOT


def load_styles() -> None:
    """Inject the application stylesheet."""

    css_path = ROOT / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def page_header(eyebrow: str, title: str, description: str) -> None:
    """Render a consistent page title block."""

    st.markdown(
        f"""
        <div class="page-header">
          <div class="eyebrow">{html.escape(eyebrow)}</div>
          <h1>{html.escape(title)}</h1>
          <p>{html.escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, note: str = "", icon: str = "◈", tone: str = "blue") -> None:
    """Render a compact SaaS-style metric card."""

    st.markdown(
        f"""
        <div class="metric-card tone-{tone}">
          <div class="metric-top"><span class="metric-icon">{icon}</span><span>{html.escape(label)}</span></div>
          <div class="metric-value">{html.escape(str(value))}</div>
          <div class="metric-note">{html.escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, subtitle: str = "") -> None:
    """Render a section heading."""

    st.markdown(
        f'<div class="section-title"><h2>{html.escape(title)}</h2><p>{html.escape(subtitle)}</p></div>',
        unsafe_allow_html=True,
    )


def empty_state(icon: str, title: str, message: str) -> None:
    """Show a friendly prerequisite or empty-data message."""

    st.markdown(
        f"""
        <div class="empty-state">
          <div class="empty-icon">{icon}</div>
          <h3>{html.escape(title)}</h3>
          <p>{html.escape(message)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_pill(label: str, status: str) -> None:
    """Render a colored state indicator."""

    normalized = status.lower().replace(" ", "-")
    st.markdown(
        f'<div class="status-row"><span>{html.escape(label)}</span><span class="status-pill status-{normalized}">{html.escape(status)}</span></div>',
        unsafe_allow_html=True,
    )


def architecture_diagram() -> None:
    """Render the IRNAM pipeline as a responsive HTML component."""

    nodes = [
        ("01", "Dataset", "Structured QoS"),
        ("02", "Recommendation", "Algorithms 1 & 2"),
        ("03", "Negotiation", "Algorithm 3"),
        ("04", "SLA", "Contract"),
        ("05", "Evaluation", "Research metrics"),
    ]
    cards = "".join(
        f'<div class="node"><span>{number}</span><strong>{name}</strong><small>{detail}</small></div>'
        + ('<div class="arrow">→</div>' if index < len(nodes) - 1 else "")
        for index, (number, name, detail) in enumerate(nodes)
    )
    components.html(
        f"""
        <style>
          *{{box-sizing:border-box}} body{{margin:0;font-family:Inter,Segoe UI,sans-serif;background:transparent}}
          .flow{{display:flex;align-items:center;gap:12px;padding:22px;background:linear-gradient(135deg,#f7fbff,#edf5ff);border:1px solid #dbeafe;border-radius:18px;overflow-x:auto}}
          .node{{min-width:145px;flex:1;background:white;border:1px solid #dbeafe;border-radius:14px;padding:18px;box-shadow:0 8px 22px rgba(30,64,175,.07)}}
          .node span{{font-size:11px;color:#2563eb;font-weight:800;letter-spacing:.12em}} .node strong{{display:block;color:#0f172a;font-size:15px;margin:8px 0 4px}} .node small{{color:#64748b;font-size:12px}}
          .arrow{{color:#60a5fa;font-size:24px;font-weight:300}} @media(max-width:760px){{.flow{{align-items:stretch}}}}
        </style><div class="flow">{cards}</div>
        """,
        height=175,
    )


def execution_logs() -> None:
    """Display backend execution logs in a compact expandable panel."""

    logs = st.session_state.get("execution_logs", [])
    with st.expander(f"Execution logs · {len(logs)} run(s)", expanded=False):
        if logs:
            st.code("\n\n".join(logs[-8:]), language="text")
        else:
            st.caption("Backend execution logs will appear here after an action.")
