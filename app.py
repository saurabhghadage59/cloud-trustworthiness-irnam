"""IRNAM professional Streamlit dashboard."""

from __future__ import annotations

import streamlit as st

from ui.components import load_styles
from ui.dashboard import render_about, render_dashboard
from ui.evaluation_page import render as render_evaluation
from ui.negotiation_page import render as render_negotiation
from ui.recommendation_page import render as render_recommendation
from ui.sla_page import render as render_sla
from ui.utils import initialize_session_state


st.set_page_config(
    page_title="IRNAM · Cloud Intelligence",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "IRNAM · Intelligent Cloud Provider Recommendation and Negotiation System"},
)

load_styles()
initialize_session_state()

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
          <span class="brand-mark">I</span><h2>IRNAM</h2>
          <p>Intelligent cloud provider recommendation & negotiation.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page = st.radio(
        "Navigation",
        ("Dashboard", "Recommendation", "Negotiation", "SLA", "Evaluation", "About"),
        label_visibility="collapsed",
    )
    st.markdown(
        """
        <div class="sidebar-footer">
          <strong>IEEE Research System</strong><br>
          Dataset schema v2.0 · Python<br>
          Evidence-backed cloud intelligence
        </div>
        """,
        unsafe_allow_html=True,
    )

ROUTES = {
    "Dashboard": render_dashboard,
    "Recommendation": render_recommendation,
    "Negotiation": render_negotiation,
    "SLA": render_sla,
    "Evaluation": render_evaluation,
    "About": render_about,
}

try:
    ROUTES[page]()
except FileNotFoundError:
    st.error("The structured dataset could not be found. Run `python -m dataset_builder` and reload the app.")
except Exception as exc:
    st.error(f"The page could not be rendered: {exc}")
    with st.expander("Technical details"):
        st.exception(exc)
