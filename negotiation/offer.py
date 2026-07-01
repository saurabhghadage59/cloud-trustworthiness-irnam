"""Offer generation for Algorithm 3."""

from __future__ import annotations

from typing import Dict, Iterable

from negotiation.concession import concession_to_offer_value
from negotiation.models import AttributeSpec, Offer


def generate_counter_offer(
    provider: str,
    specs: Iterable[AttributeSpec],
    concession: float,
    round_number: int,
    strategy: str,
) -> Offer:
    """Generate new offer X after applying concession theta."""

    attributes: Dict[str, float] = {}
    for spec in specs:
        attributes[spec.name] = concession_to_offer_value(
            spec.user_value,
            spec.provider_value,
            concession,
        )
    return Offer(
        provider=provider,
        attributes=attributes,
        round_number=round_number,
        strategy=strategy,
        concession=concession,
    )
