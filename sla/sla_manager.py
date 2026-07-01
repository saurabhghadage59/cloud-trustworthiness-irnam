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
                **dict(metadata or {}),
            },
        )
        validation = self.validator.validate_contract(contract)
        if not validation.valid:
            raise ValueError("; ".join(validation.errors))
        logger.info("SLA Generated for provider %s", contract.provider)
        return contract

    def parse_contract(self, source) -> SLAContract:
        return SLAContract.from_dict(self.parser.parse(source))

    def save_contract(self, contract: SLAContract, path: str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contract.to_json(), encoding="utf-8")

    def compare_contracts(self, left: SLAContract, right: SLAContract) -> Dict[str, Any]:
        return left.compare(right)
