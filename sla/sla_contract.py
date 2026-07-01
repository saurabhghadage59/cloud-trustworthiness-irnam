"""SLA contract representation for finalized IRNAM agreements."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Mapping


@dataclass
class SLAContract:
    provider: str
    negotiated_attributes: Dict[str, float]
    negotiation_strategy: str
    negotiation_rounds: int
    final_satisfaction: Dict[str, float]
    agreement_status: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "negotiated_attributes": dict(self.negotiated_attributes),
            "negotiation_strategy": self.negotiation_strategy,
            "timestamp": self.timestamp.isoformat(),
            "negotiation_rounds": self.negotiation_rounds,
            "final_satisfaction": dict(self.final_satisfaction),
            "agreement_status": self.agreement_status,
            "metadata": dict(self.metadata),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SLAContract":
        timestamp = data.get("timestamp")
        parsed_timestamp = (
            datetime.fromisoformat(timestamp)
            if isinstance(timestamp, str)
            else datetime.now(timezone.utc)
        )
        return cls(
            provider=str(data.get("provider", "")),
            negotiated_attributes=dict(data.get("negotiated_attributes", {})),
            negotiation_strategy=str(data.get("negotiation_strategy", "win_win")),
            negotiation_rounds=int(data.get("negotiation_rounds", 0)),
            final_satisfaction=dict(data.get("final_satisfaction", {})),
            agreement_status=str(data.get("agreement_status", "unknown")),
            timestamp=parsed_timestamp,
            metadata=dict(data.get("metadata", {})),
        )

    @classmethod
    def from_json(cls, payload: str) -> "SLAContract":
        return cls.from_dict(json.loads(payload))

    def compare(self, other: "SLAContract") -> Dict[str, Any]:
        changed = {}
        all_attrs = set(self.negotiated_attributes) | set(other.negotiated_attributes)
        for attr in sorted(all_attrs):
            left = self.negotiated_attributes.get(attr)
            right = other.negotiated_attributes.get(attr)
            if left != right:
                changed[attr] = {"left": left, "right": right}
        return {
            "same_provider": self.provider == other.provider,
            "same_status": self.agreement_status == other.agreement_status,
            "changed_attributes": changed,
        }
