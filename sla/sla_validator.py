"""Validation for SLA inputs and generated contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping

from negotiation.utils import numeric
from sla.sla_contract import SLAContract


@dataclass
class SLAValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


class SLAValidator:
    def validate_sla(self, sla: Mapping[str, Any]) -> SLAValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        if not isinstance(sla, Mapping):
            return SLAValidationResult(False, ["SLA must be a mapping"], [])
        for key, value in sla.items():
            if isinstance(value, Mapping):
                raw_value = value.get("value")
                minimum = numeric(value.get("min"))
                maximum = numeric(value.get("max"))
                parsed_value = numeric(raw_value)
                if parsed_value is None and raw_value is not None:
                    warnings.append(f"{key} value is non-numeric and will not be negotiated")
                if minimum is not None and maximum is not None and minimum > maximum:
                    errors.append(f"{key} min cannot exceed max")
            elif numeric(value) is None:
                warnings.append(f"{key} is non-numeric and will not be negotiated")
        return SLAValidationResult(not errors, errors, warnings)

    def validate_contract(self, contract: SLAContract) -> SLAValidationResult:
        errors: List[str] = []
        if not contract.provider:
            errors.append("provider is required")
        if contract.agreement_status not in {"accepted", "rejected", "failed"}:
            errors.append("agreement_status must be accepted, rejected, or failed")
        if contract.agreement_status == "accepted" and not contract.negotiated_attributes:
            errors.append("accepted contracts must include negotiated attributes")
        if contract.negotiation_rounds < 0:
            errors.append("negotiation_rounds cannot be negative")
        return SLAValidationResult(not errors, errors, [])
