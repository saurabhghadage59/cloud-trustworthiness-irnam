"""Domain models for the IRNAM negotiation phase.

The classes in this module are intentionally lightweight so the
recommendation phase can integrate by passing ordinary dictionaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional


DEFAULT_NEGOTIABLE_ATTRIBUTES = (
    "price",
    "availability",
    "security",
    "reliability",
    "response_time",
    "scalability",
    "support",
    "storage",
    "network",
)


STRATEGY_RHO = {
    "competitive": 0.9,
    "win_win": 1.0,
    "win-win": 1.0,
    "collaborative": 2.0,
}


LOWER_IS_BETTER_ATTRIBUTES = {
    "price",
    "cost",
    "response_time",
    "latency",
    "delay",
}


@dataclass(frozen=True)
class AttributeSpec:
    """Negotiable QoS attribute with party values, weights, and ranges."""

    name: str
    user_value: float
    provider_value: float
    user_weight: float = 1.0
    provider_weight: float = 1.0
    user_min: Optional[float] = None
    user_max: Optional[float] = None
    provider_min: Optional[float] = None
    provider_max: Optional[float] = None

    @property
    def lower_is_better(self) -> bool:
        canonical = self.name.strip().lower().replace("-", "_").replace(" ", "_")
        return canonical in LOWER_IS_BETTER_ATTRIBUTES


@dataclass
class Offer:
    """A negotiated offer X, represented as attribute values."""

    provider: str
    attributes: Dict[str, float]
    round_number: int = 0
    strategy: str = "win_win"
    concession: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "attributes": dict(self.attributes),
            "round_number": self.round_number,
            "strategy": self.strategy,
            "concession": self.concession,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass(frozen=True)
class SatisfactionResult:
    """Utility satisfaction for the user, provider, and both parties."""

    user_satisfaction: float
    provider_satisfaction: float
    overall_satisfaction: float

    @property
    def accepted_by_aggregation(self) -> bool:
        return self.user_satisfaction >= self.provider_satisfaction

    def to_dict(self) -> Dict[str, float]:
        return {
            "user_satisfaction": self.user_satisfaction,
            "provider_satisfaction": self.provider_satisfaction,
            "overall_satisfaction": self.overall_satisfaction,
        }


@dataclass
class NegotiationRound:
    """Trace data for one execution of Algorithm 3 step 4."""

    round_number: int
    offer: Offer
    user_aggregate: float
    provider_aggregate: float
    degree_of_difference: float
    concession: float
    accepted: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_number": self.round_number,
            "offer": self.offer.to_dict(),
            "user_aggregate": self.user_aggregate,
            "provider_aggregate": self.provider_aggregate,
            "degree_of_difference": self.degree_of_difference,
            "concession": self.concession,
            "accepted": self.accepted,
        }


@dataclass
class NegotiationConfig:
    """Configurable settings for Algorithm 3."""

    strategy: str = "win_win"
    max_rounds: int = 10
    deadline_seconds: Optional[float] = None
    acceptance_threshold: float = 0.5
    attributes: Optional[List[str]] = None
    rho: Optional[float] = None

    def effective_rho(self) -> float:
        if self.rho is not None:
            return float(self.rho)
        return STRATEGY_RHO.get(self.strategy, STRATEGY_RHO["win_win"])


@dataclass
class NegotiationResult:
    """Result returned by the negotiation engine."""

    provider: str
    success: bool
    final_offer: Optional[Offer]
    satisfaction: Optional[SatisfactionResult]
    rounds: List[NegotiationRound]
    strategy: str
    deadline_reached: bool = False
    reason: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    recommendation: Mapping[str, Any] = field(default_factory=dict)

    @property
    def negotiation_rounds(self) -> int:
        return len(self.rounds)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "success": self.success,
            "final_offer": self.final_offer.to_dict() if self.final_offer else None,
            "satisfaction": self.satisfaction.to_dict() if self.satisfaction else None,
            "rounds": [round_data.to_dict() for round_data in self.rounds],
            "negotiation_rounds": self.negotiation_rounds,
            "strategy": self.strategy,
            "deadline_reached": self.deadline_reached,
            "reason": self.reason,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "duration_seconds": (self.completed_at - self.started_at).total_seconds(),
            "recommendation": dict(self.recommendation),
        }
