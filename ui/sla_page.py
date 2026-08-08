"""SLA contract presentation and export page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .components import empty_state, execution_logs, metric_card, page_header, section_title
from .utils import json_text


def render() -> None:
    """Render the generated SLA contract."""

    page_header(
        "Agreement contract",
        "Review the negotiated service-level agreement.",
        "The SLA Manager validates and serializes the final negotiation outcome into a portable research contract.",
    )
    contract = st.session_state.sla_contract
    if contract is None:
        empty_state("▣", "No SLA generated", "Complete a negotiation to generate and validate an SLA contract.")
        execution_logs()
        return

    accepted = contract.agreement_status == "accepted"
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Provider", contract.provider, "Recommended CSP", "☁")
    with c2:
        metric_card("Agreement", contract.agreement_status.title(), "Validated contract", "✓" if accepted else "!", "green" if accepted else "amber")
    with c3:
        metric_card("Strategy", contract.negotiation_strategy.replace("_", " ").title(), "Negotiation policy", "⇄", "purple")
    with c4:
        metric_card("Rounds", str(contract.negotiation_rounds), "Time to outcome", "↻")

    left, right = st.columns([1.35, 1])
    with left:
        section_title("Negotiated attributes")
        if contract.negotiated_attributes:
            st.dataframe(
                pd.DataFrame([{"Attribute": key.replace("_", " ").title(), "Agreed Value": value} for key, value in contract.negotiated_attributes.items()]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("No attributes were finalized because agreement was not reached.")
    with right:
        section_title("Contract metadata")
        st.markdown(f"**Timestamp**  \n`{contract.timestamp.isoformat()}`")
        st.markdown(f"**Agreement status**  \n`{contract.agreement_status}`")
        st.markdown("**Metadata**")
        st.json(contract.metadata, expanded=False)

    st.download_button(
        "Download SLA JSON",
        contract.to_json(),
        file_name=f"irnam_sla_{contract.provider.lower().replace(' ', '_')}.json",
        mime="application/json",
    )
    execution_logs()
