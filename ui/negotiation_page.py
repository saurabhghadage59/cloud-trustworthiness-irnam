"""Negotiation execution and trace visualization page."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from evaluation import NegotiationEvaluator
from main import provider_sla_for_recommendation
from negotiation import NegotiationConfig, NegotiationEngine
from sla import SLAManager

from .charts import negotiation_timeline
from .components import empty_state, execution_logs, metric_card, page_header, section_title
from .utils import execute_with_logs, json_text


def render() -> None:
    """Render strategy controls and the complete negotiation trace."""

    page_header(
        "Algorithm 3",
        "Negotiate the recommended cloud agreement.",
        "Select a strategy and target. The existing NegotiationEngine generates concessions, counter-offers, satisfaction scores, and a final agreement decision.",
    )
    recommendation = st.session_state.recommendation
    if recommendation is None:
        empty_state("⇄", "Recommendation required", "Generate a provider recommendation before starting negotiation.")
        execution_logs()
        return

    section_title("Negotiation setup", f"Recommended counterparty: {recommendation.recommended_provider}")
    with st.form("negotiation_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            strategy = st.selectbox("Negotiation strategy", ("win_win", "competitive", "collaborative"), format_func=lambda x: x.replace("_", " ").title())
        with c2:
            availability = st.slider("Minimum availability target (%)", 90.0, 100.0, 99.9, 0.01)
        with c3:
            max_rounds = st.slider("Maximum rounds", 1, 20, 10)
        start = st.form_submit_button("Start negotiation", use_container_width=True)

    if start:
        try:
            with st.spinner("Negotiating SLA terms…"):
                def action():
                    provider_sla = provider_sla_for_recommendation(recommendation)
                    user_sla = {"availability": {"value": availability, "min": 0.0, "max": 100.0}}
                    negotiation = NegotiationEngine(
                        NegotiationConfig(strategy=strategy, max_rounds=max_rounds, acceptance_threshold=0.0)
                    ).negotiate(recommendation, user_sla, provider_sla)
                    contract = SLAManager().create_contract(
                        negotiation,
                        metadata={"recommendation_score": recommendation.overall_score},
                    )
                    evaluation = NegotiationEvaluator().evaluate([negotiation])
                    return negotiation, contract, evaluation

                negotiation, contract, evaluation = execute_with_logs("Negotiation, SLA & evaluation", action)
                st.session_state.negotiation = negotiation
                st.session_state.sla_contract = contract
                st.session_state.evaluation = evaluation
            if negotiation.success:
                st.success("Agreement reached and SLA generated.")
            else:
                st.warning(f"Negotiation ended without agreement: {negotiation.reason}")
        except (TypeError, ValueError, RuntimeError) as exc:
            st.error(f"Negotiation could not be completed: {exc}")

    result = st.session_state.negotiation
    if result is None:
        empty_state("↻", "Negotiation not started", "Configure the negotiation and start the agent to view the offer timeline.")
        execution_logs()
        return

    section_title("Negotiation outcome")
    satisfaction = result.satisfaction
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Agreement Status", "Accepted" if result.success else "Failed", result.reason, "✓" if result.success else "!", "green" if result.success else "amber")
    with c2:
        metric_card("Rounds", str(result.negotiation_rounds), f"Strategy: {result.strategy}", "↻")
    with c3:
        metric_card("User Satisfaction", f"{satisfaction.user_satisfaction:.1%}" if satisfaction else "—", "Final utility", "◉", "purple")
    with c4:
        metric_card("Provider Satisfaction", f"{satisfaction.provider_satisfaction:.1%}" if satisfaction else "—", "Final utility", "◇", "blue")

    if result.rounds:
        st.plotly_chart(negotiation_timeline(result.rounds), use_container_width=True, config={"displayModeBar": False})
        section_title("Offer history", "Round-by-round concessions and generated attributes.")
        rows = []
        for item in result.rounds:
            rows.append({
                "Round": item.round_number,
                "Concession": item.concession,
                "User Utility": item.user_aggregate,
                "Provider Utility": item.provider_aggregate,
                "Accepted": item.accepted,
                "Offer": json.dumps(item.offer.attributes),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.download_button("Download negotiation JSON", json_text(result), "irnam_negotiation.json", "application/json")
    execution_logs()
