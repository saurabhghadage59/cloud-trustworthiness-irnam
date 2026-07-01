"""Backward-compatible facade for the IRNAM negotiation engine."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from negotiation.concession import calculate_concession
from negotiation.models import NegotiationConfig
from negotiation.negotiation_engine import NegotiationEngine


class NegotiationAgent:

    def __init__(
        self,
        user_requirements,
        provider_offer,
        recommendation: Optional[Mapping[str, Any]] = None,
        config: Optional[NegotiationConfig] = None,
    ):
        self.user = user_requirements
        self.provider = provider_offer
        self.recommendation = recommendation or {"recommended_provider": "provider"}
        self.config = config

    def negotiate(self):
        """Return final offer attributes.

        The original prototype returned only a dictionary of attributes. This
        facade keeps that behavior while the research-grade result is available
        through negotiate_result().
        """

        result = self.negotiate_result()
        if result.success and result.final_offer:
            return result.final_offer.attributes

        final_offer = {}
        for attribute in self.user:
            if attribute not in self.provider:
                continue
            user_value = self.user[attribute]
            provider_value = self.provider[attribute]
            final_offer[attribute] = calculate_concession(
                user_value,
                provider_value
            )
        return final_offer

    def negotiate_result(self):
        engine = NegotiationEngine(self.config)
        return engine.negotiate(self.recommendation, self.user, self.provider)
