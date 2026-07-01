"""Research-grade implementation of IRNAM Algorithm 3."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from negotiation.aggregation import AggregationEngine
from negotiation.concession import calculate_concession
from negotiation.models import NegotiationConfig, NegotiationResult, NegotiationRound
from negotiation.offer import generate_counter_offer
from negotiation.satisfaction import aggregated_scores, compute_satisfaction
from negotiation.utils import (
    build_attribute_specs,
    degree_of_difference,
    euclidean_distance,
    provider_name_from_recommendation,
)

logger = logging.getLogger(__name__)


class NegotiationEngine:
    """Execute IRNAM negotiation from Recommendation output plus SLA data."""

    def __init__(self, config: Optional[NegotiationConfig] = None):
        self.config = config or NegotiationConfig()
        self.aggregation_engine = AggregationEngine()

    def negotiate(
        self,
        recommendation: Optional[Mapping[str, Any]],
        user_sla: Mapping[str, Any],
        provider_sla: Mapping[str, Any],
    ) -> NegotiationResult:
        started_at = datetime.now(timezone.utc)
        wall_start = time.monotonic()
        provider = provider_name_from_recommendation(recommendation)
        logger.info("Negotiation Started for provider %s", provider)

        specs = build_attribute_specs(
            user_sla=user_sla,
            provider_sla=provider_sla,
            recommendation=recommendation,
            negotiable_attributes=self.config.attributes,
        )
        if not specs:
            completed_at = datetime.now(timezone.utc)
            return NegotiationResult(
                provider=provider,
                success=False,
                final_offer=None,
                satisfaction=None,
                rounds=[],
                strategy=self.config.strategy,
                reason="no shared negotiable attributes",
                started_at=started_at,
                completed_at=completed_at,
                recommendation=recommendation or {},
            )

        max_rounds = max(1, int(self.config.max_rounds))
        previous_offer = {spec.name: spec.provider_value for spec in specs}
        user_target = {spec.name: spec.user_value for spec in specs}
        previous_distance = euclidean_distance(previous_offer, user_target) or 1.0
        rounds = []
        final_offer = None
        final_satisfaction = None
        deadline_reached = False
        reason = "deadline reached"

        for round_number in range(1, max_rounds + 1):
            if self.config.deadline_seconds is not None:
                elapsed = time.monotonic() - wall_start
                if elapsed >= self.config.deadline_seconds:
                    deadline_reached = True
                    logger.info("Deadline Expired for provider %s", provider)
                    break

            current_distance = previous_distance if round_number == 1 else euclidean_distance(previous_offer, user_target)
            alpha = degree_of_difference(previous_distance, current_distance)
            negotiation_time = round_number / max_rounds
            probe_user_score, _ = aggregated_scores(previous_offer, specs)
            concession = calculate_concession(
                negotiation_time=negotiation_time,
                degree_of_difference=alpha,
                user_aggregate=probe_user_score,
                strategy=self.config.strategy,
                rho=self.config.rho,
            )
            logger.info("Concession Applied: %.6f", concession)

            offer = generate_counter_offer(
                provider=provider,
                specs=specs,
                concession=concession,
                round_number=round_number,
                strategy=self.config.strategy,
            )
            logger.info("Counter Offer generated for round %s", round_number)
            user_aggregate, provider_aggregate = aggregated_scores(offer.attributes, specs)
            satisfaction = compute_satisfaction(offer.attributes, specs)
            aggregation = self.aggregation_engine.aggregate(offer, specs, satisfaction)
            accepted = (
                user_aggregate * len(specs) >= self.config.acceptance_threshold
                and aggregation.accepted
            )
            rounds.append(
                NegotiationRound(
                    round_number=round_number,
                    offer=offer,
                    user_aggregate=user_aggregate,
                    provider_aggregate=provider_aggregate,
                    degree_of_difference=alpha,
                    concession=concession,
                    accepted=accepted,
                )
            )
            logger.info("Offer Generated for round %s", round_number)

            if accepted:
                logger.info("Agreement Reached for provider %s", provider)
                final_offer = offer
                final_satisfaction = satisfaction
                reason = "agreement reached"
                break

            previous_distance = max(current_distance, 1e-12)
            previous_offer = offer.attributes

        if final_offer is None and rounds:
            final_offer = rounds[-1].offer
            final_satisfaction = compute_satisfaction(final_offer.attributes, specs)

        completed_at = datetime.now(timezone.utc)
        success = bool(final_offer and rounds and rounds[-1].accepted)
        if not success and deadline_reached:
            reason = "deadline reached; request next provider"
        elif not success:
            reason = "agreement not reached; request next provider"

        return NegotiationResult(
            provider=provider,
            success=success,
            final_offer=final_offer if success else None,
            satisfaction=final_satisfaction if success else None,
            rounds=rounds,
            strategy=self.config.strategy,
            deadline_reached=deadline_reached,
            reason=reason,
            started_at=started_at,
            completed_at=completed_at,
            recommendation=recommendation or {},
        )
