"""Aggregation phase implementation for IRNAM Algorithm 4."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Optional

from negotiation.models import AttributeSpec, Offer, SatisfactionResult
from negotiation.satisfaction import compute_satisfaction

logger = logging.getLogger(__name__)


@dataclass
class AggregationResult:
    accepted: bool
    offer: Offer
    satisfaction: SatisfactionResult
    reason: str

    def to_dict(self):
        return {
            "accepted": self.accepted,
            "offer": self.offer.to_dict(),
            "satisfaction": self.satisfaction.to_dict(),
            "reason": self.reason,
        }


class AggregationEngine:
    """Finalize offer X when user utility is at least CSP utility."""

    def aggregate(
        self,
        offer: Offer,
        specs: Iterable[AttributeSpec],
        satisfaction: Optional[SatisfactionResult] = None,
    ) -> AggregationResult:
        logger.info("Aggregation phase started for provider %s", offer.provider)
        computed = satisfaction or compute_satisfaction(offer.attributes, specs)
        if computed.user_satisfaction >= computed.provider_satisfaction:
            logger.info("Offer accepted by aggregation")
            return AggregationResult(True, offer, computed, "user satisfaction >= provider satisfaction")
        logger.info("Offer rejected by aggregation")
        return AggregationResult(False, offer, computed, "user satisfaction < provider satisfaction")
