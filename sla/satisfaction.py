"""Compatibility wrapper for negotiation satisfaction equations."""

from negotiation.satisfaction import (
    aggregated_scores,
    compute_satisfaction,
    normalized_offer_for_party,
    party_weights,
)

__all__ = [
    "aggregated_scores",
    "compute_satisfaction",
    "normalized_offer_for_party",
    "party_weights",
]
