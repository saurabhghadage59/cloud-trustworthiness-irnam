"""User requirement collection and provider recommendation page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.recommendation import RecommendationEngine, UserRequirementProcessor

from .charts import heatmap_chart, overall_score_chart, priority_pie_chart, provider_comparison_chart, radar_chart
from .components import empty_state, execution_logs, metric_card, page_header, section_title
from .utils import clear_downstream, execute_with_logs, json_text


ATTRIBUTES = (
    "availability", "reliability", "security", "cost", "response_time",
    "scalability", "support", "storage", "network",
)
PRIORITIES = ("Very High", "High", "Medium", "Low", "Very Low")
DEFAULT_INDEX = {
    "availability": 0, "reliability": 1, "security": 1, "cost": 2,
    "response_time": 3, "scalability": 1, "support": 2, "storage": 3, "network": 2,
}


def render() -> None:
    """Render requirements form and recommendation analytics."""

    page_header(
        "Algorithms 1 & 2",
        "Find the cloud provider that fits your priorities.",
        "Set the relative importance of each QoS dimension. IRNAM converts your choices into normalized weights and evaluates the structured provider dataset.",
    )

    section_title("User requirements", "Every priority contributes to the final weighted evaluation score.")
    with st.form("requirements_form"):
        columns = st.columns(3)
        request = {}
        for index, attribute in enumerate(ATTRIBUTES):
            with columns[index % 3]:
                request[attribute] = st.selectbox(
                    attribute.replace("_", " ").title(),
                    PRIORITIES,
                    index=DEFAULT_INDEX[attribute],
                    key=f"priority_{attribute}",
                )
        submitted = st.form_submit_button("Generate recommendation", use_container_width=True)

    if submitted:
        try:
            with st.spinner("Evaluating cloud providers…"):
                def action():
                    requirement = UserRequirementProcessor().process(request)
                    recommendation = RecommendationEngine().recommend(requirement)
                    return requirement, recommendation

                requirement, recommendation = execute_with_logs("Recommendation", action)
                st.session_state.requirement = requirement
                st.session_state.recommendation = recommendation
                clear_downstream("recommendation")
            st.success(f"Recommendation generated: {recommendation.recommended_provider}")
        except FileNotFoundError:
            st.error("The structured dataset is missing. Rebuild it with `python -m dataset_builder`.")
        except (TypeError, ValueError, RuntimeError) as exc:
            st.error(f"Could not generate a recommendation: {exc}")

    result = st.session_state.recommendation
    if result is None:
        empty_state("◆", "No recommendation yet", "Choose your priorities and generate a recommendation to unlock rankings and analytics.")
        execution_logs()
        return

    section_title("Recommendation outcome")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Recommended Provider", result.recommended_provider or "—", "Ranked #1", "★", "green")
    with c2:
        metric_card("Overall Score", f"{result.overall_score:.3f}", "Weighted evaluation", "◎")
    with c3:
        metric_card("Providers Ranked", str(len(result.complete_ranking)), "Eligible providers", "▤", "purple")
    with c4:
        strongest = max(result.attribute_scores, key=result.attribute_scores.get).replace("_", " ").title()
        metric_card("Strongest Match", strongest, "Highest attribute fit", "↗", "amber")

    st.info(result.reason_for_recommendation, icon="💡")

    overview, analytics, details = st.tabs(["Overview", "Visual analytics", "Provider details"])
    with overview:
        ranking_rows = [
            {
                "Rank": entry.rank,
                "Provider": entry.provider,
                "Overall Score": entry.overall_score,
                "Top Match": max(entry.attribute_scores, key=entry.attribute_scores.get).replace("_", " ").title(),
            }
            for entry in result.complete_ranking
        ]
        st.dataframe(
            pd.DataFrame(ranking_rows),
            use_container_width=True,
            hide_index=True,
            column_config={"Overall Score": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.3f")},
        )
        left, right = st.columns(2)
        with left:
            st.plotly_chart(radar_chart(result.attribute_scores), use_container_width=True, config={"displayModeBar": False})
        with right:
            st.plotly_chart(overall_score_chart(result.complete_ranking), use_container_width=True, config={"displayModeBar": False})
    with analytics:
        st.plotly_chart(provider_comparison_chart(result.complete_ranking), use_container_width=True, config={"displayModeBar": False})
        left, right = st.columns([1, 1.5])
        with left:
            st.plotly_chart(priority_pie_chart(result.user_weights), use_container_width=True, config={"displayModeBar": False})
        with right:
            st.plotly_chart(heatmap_chart(result.complete_ranking), use_container_width=True, config={"displayModeBar": False})
    with details:
        details_frame = pd.DataFrame(
            [{"Attribute": key, "Value": str(value)} for key, value in result.provider_attributes.items()]
        )
        st.dataframe(details_frame, use_container_width=True, hide_index=True)

    st.download_button(
        "Download recommendation JSON",
        json_text(result),
        file_name="irnam_recommendation.json",
        mime="application/json",
    )
    execution_logs()
