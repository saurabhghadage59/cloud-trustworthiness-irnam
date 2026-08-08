"""High-level SLA lifecycle manager for IRNAM."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from negotiation.models import NegotiationResult
from sla.sla_contract import SLAContract
from sla.sla_parser import SLAParser
from sla.sla_validator import SLAValidator

logger = logging.getLogger(__name__)


class SLAManager:
    def __init__(self, validator: Optional[SLAValidator] = None, parser: Optional[SLAParser] = None):
        self.validator = validator or SLAValidator()
        self.parser = parser or SLAParser()

    def create_contract(
        self,
        negotiation_result: NegotiationResult,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> SLAContract:
        status = "accepted" if negotiation_result.success else "failed"
        attributes = (
            negotiation_result.final_offer.attributes
            if negotiation_result.final_offer and negotiation_result.success
            else {}
        )
        satisfaction = (
            negotiation_result.satisfaction.to_dict()
            if negotiation_result.satisfaction
            else {}
        )
        contract = SLAContract(
            provider=negotiation_result.provider,
            negotiated_attributes=dict(attributes),
            negotiation_strategy=negotiation_result.strategy,
            negotiation_rounds=negotiation_result.negotiation_rounds,
            final_satisfaction=satisfaction,
            agreement_status=status,
            metadata={
                "reason": negotiation_result.reason,
                "sla_terms": self._recommended_sla_terms(negotiation_result.recommendation),
                **dict(metadata or {}),
            },
        )
        validation = self.validator.validate_contract(contract)
        if not validation.valid:
            raise ValueError("; ".join(validation.errors))
        logger.info("SLA Generated for provider %s", contract.provider)
        return contract

    @staticmethod
    def _recommended_sla_terms(recommendation: Mapping[str, Any]) -> Dict[str, Any]:
        """Carry benchmark QoS into an SLA summary without changing offers.

        This is intentionally metadata rather than a negotiated commitment: it
        preserves the original negotiation contract while documenting the
        measurable terms and an auditable violation-penalty basis.
        """
        attributes = recommendation.get("provider_attributes", {}) if recommendation else {}
        aliases = {
            "availability": ("Availability", "availability_sla_percent"), "response_time": ("ResponseTimeMs",),
            "latency": ("LatencyMs",), "support": ("SupportScore", "support_tier"),
            "scalability": ("ScalabilityScore",), "security": ("SecurityScore",),
            "reliability": ("Reliability",), "sla_violation_rate": ("SLAViolationRate",),
        }
        terms = {name: next((attributes[key] for key in keys if key in attributes), None) for name, keys in aliases.items()}
        violation_rate = terms.get("sla_violation_rate")
        terms["violation_penalty_policy"] = {
            "basis": "SLA violation rate", "rate_percent": violation_rate,
            "calculation": "service_credit = agreed_monthly_charge * violation_rate / 100",
        }
        return terms

    def parse_contract(self, source) -> SLAContract:
        return SLAContract.from_dict(self.parser.parse(source))

    def save_contract(self, contract: SLAContract, path: str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contract.to_json(), encoding="utf-8")

    def compare_contracts(self, left: SLAContract, right: SLAContract) -> Dict[str, Any]:
        return left.compare(right)
