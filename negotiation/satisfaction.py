"""Satisfaction and utility equations for IRNAM negotiation."""

from __future__ import annotations

from typing import Dict, Iterable, Mapping, Tuple

from negotiation.models import AttributeSpec, SatisfactionResult
from negotiation.utils import aggregate_evaluated_value, normalize


def normalized_offer_for_party(
    offer_attributes: Mapping[str, float],
    specs: Iterable[AttributeSpec],
    party: str,
) -> Dict[str, float]:
    """Normalize offer X for either USER or CSP ranges."""

    values: Dict[str, float] = {}
    for spec in specs:
        if spec.name not in offer_attributes:
            continue
        if party == "provider":
            minimum = spec.provider_min if spec.provider_min is not None else min(spec.user_value, spec.provider_value)
            maximum = spec.provider_max if spec.provider_max is not None else max(spec.user_value, spec.provider_value)
        else:
            minimum = spec.user_min if spec.user_min is not None else min(spec.user_value, spec.provider_value)
            maximum = spec.user_max if spec.user_max is not None else max(spec.user_value, spec.provider_value)
        values[spec.name] = normalize(float(offer_attributes[spec.name]), minimum, maximum)
    return values


def party_weights(specs: Iterable[AttributeSpec], party: str) -> Dict[str, float]:
    if party == "provider":
        return {spec.name: spec.provider_weight for spec in specs}
    return {spec.name: spec.user_weight for spec in specs}


def aggregated_scores(
    offer_attributes: Mapping[str, float],
    specs: Iterable[AttributeSpec],
) -> Tuple[float, float]:
    specs = list(specs)
    user_score = aggregate_evaluated_value(
        normalized_offer_for_party(offer_attributes, specs, "user"),
        party_weights(specs, "user"),
    )
    provider_score = aggregate_evaluated_value(
        normalized_offer_for_party(offer_attributes, specs, "provider"),
        party_weights(specs, "provider"),
    )
    return user_score, provider_score


def compute_satisfaction(
    offer_attributes: Mapping[str, float],
    specs: Iterable[AttributeSpec],
) -> SatisfactionResult:
    """Compute utility satisfaction used by Algorithm 4."""

    user_score, provider_score = aggregated_scores(offer_attributes, specs)
    return SatisfactionResult(
        user_satisfaction=user_score,
        provider_satisfaction=provider_score,
        overall_satisfaction=(user_score + provider_score) / 2,
    )
