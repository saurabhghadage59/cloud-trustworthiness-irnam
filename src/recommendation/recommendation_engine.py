"""End-to-end IRNAM recommendation workflow for Algorithms 1 and 2."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import Requirement
from .ranking import ProviderRanker, RankedProvider
from .weights import WeightCalculator

logger = logging.getLogger(__name__)


DEFAULT_ATTRIBUTE_MAPPING = {
    "availability": "availability_sla_percent",
    "reliability": ("backup", "disaster_recovery"),
    "security": ("security_certifications", "compliance_certifications"),
    "cost": "minimum_vm_price_usd_hour",
    "response_time": (),
    "scalability": ("auto_scaling", "load_balancer", "region_count"),
    "support": ("support_24x7", "support_tier"),
    "storage": ("storage_price_usd_gb_month", "backup"),
    "network": ("availability_zone_count", "load_balancer"),
}

DEFAULT_DIRECTIONS = {
    "minimum_vm_price_usd_hour": "lower",
    "storage_price_usd_gb_month": "lower",
}

DEFAULT_ENUM_SCALES = {
    "support_tier": {
        "Basic": 1.0,
        "Developer": 2.0,
        "Standard": 3.0,
        "Business": 4.0,
        "Enhanced": 5.0,
        "Premium": 6.0,
        "Premier": 6.0,
        "Enterprise": 7.0,
    }
}


@dataclass(frozen=True)
class RecommendationResult(Mapping[str, Any]):
    """Recommendation output and Mapping contract consumed by NegotiationEngine."""

    recommended_provider: Optional[str]
    overall_score: float
    complete_ranking: List[RankedProvider]
    attribute_scores: Dict[str, float]
    reason_for_recommendation: str
    user_weights: Dict[str, float] = field(default_factory=dict)
    provider_weights: Dict[str, Dict[str, float]] = field(default_factory=dict)
    provider_attributes: Dict[str, Any] = field(default_factory=dict)
    filtered_out: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def ranking(self) -> List[RankedProvider]:
        """Return the complete provider ranking."""

        return self.complete_ranking

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the result for JSON or negotiation input."""

        return {
            "recommended_provider": self.recommended_provider,
            "provider": self.recommended_provider,
            "overall_score": self.overall_score,
            "complete_ranking": [entry.to_dict() for entry in self.complete_ranking],
            "ranking": [entry.to_dict() for entry in self.complete_ranking],
            "attribute_scores": dict(self.attribute_scores),
            "reason_for_recommendation": self.reason_for_recommendation,
            "reason": self.reason_for_recommendation,
            "weights": dict(self.user_weights),
            "user_priorities": dict(self.user_weights),
            "provider_weights": {name: dict(weights) for name, weights in self.provider_weights.items()},
            "provider_attributes": dict(self.provider_attributes),
            "filtered_out": {name: list(reasons) for name, reasons in self.filtered_out.items()},
        }

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.to_dict())

    def __len__(self) -> int:
        return len(self.to_dict())


class RecommendationEngine:
    """Load the QoS dataset, filter providers, and execute Algorithms 1 and 2."""

    def __init__(
        self,
        dataset_path: Optional[Path | str] = None,
        providers: Optional[Sequence[Mapping[str, Any]]] = None,
        attribute_mapping: Optional[Mapping[str, Any]] = None,
        directions: Optional[Mapping[str, str]] = None,
        enum_scales: Optional[Mapping[str, Mapping[Any, float]]] = None,
    ) -> None:
        self.dataset_path = Path(dataset_path) if dataset_path else Path(__file__).resolve().parents[2] / "outputs" / "cloud_dataset.json"
        self._providers = [dict(provider) for provider in providers] if providers is not None else None
        self.attribute_mapping = dict(attribute_mapping or DEFAULT_ATTRIBUTE_MAPPING)
        self.directions = dict(DEFAULT_DIRECTIONS)
        self.directions.update(directions or {})
        self.enum_scales = {name: dict(scale) for name, scale in (enum_scales or DEFAULT_ENUM_SCALES).items()}
        self.weight_calculator = WeightCalculator()
        self.ranker = ProviderRanker()

    def recommend(
        self,
        requirement: Requirement,
        mandatory_requirements: Optional[Mapping[str, Any]] = None,
        constraints: Optional[Mapping[str, Any]] = None,
        requested_services: Optional[Sequence[str]] = None,
        unavailable_providers: Optional[Sequence[str]] = None,
    ) -> RecommendationResult:
        """Run the complete recommendation workflow and return a negotiation-ready result.

        Filtering controls are optional to remain compatible with the current
        priority-only ``Requirement`` model. If future Requirement versions
        expose fields with these names, they are consumed automatically.
        """

        if not isinstance(requirement, Requirement):
            raise TypeError("requirement must be a Requirement object")
        logger.info("Recommendation Started")
        providers = self.load_dataset()
        logger.info("Dataset Loaded: %d providers", len(providers))

        user_weights = self.weight_calculator.calculate_user_weights(requirement)
        logger.info("Weights Generated: %d attributes", len(user_weights))

        mandatory = dict(mandatory_requirements or getattr(requirement, "mandatory_requirements", {}) or {})
        limits = dict(constraints or getattr(requirement, "constraints", {}) or {})
        services = list(requested_services or getattr(requirement, "requested_services", []) or [])
        unavailable = list(unavailable_providers or getattr(requirement, "unavailable_providers", []) or [])
        valid, filtered_out = self.filter_providers(providers, mandatory, limits, services, unavailable)
        logger.info("Providers Filtered: %d valid, %d excluded", len(valid), len(filtered_out))

        if not valid:
            reason = "No provider satisfies all mandatory requirements and constraints."
            logger.info("Recommendation Generated: no eligible provider")
            return RecommendationResult(None, 0.0, [], {}, reason, user_weights, {}, {}, filtered_out)

        mapped_fields = self._mapped_provider_fields(user_weights)
        provider_weights = self.weight_calculator.calculate_provider_weights(valid, mapped_fields, self.enum_scales)
        ranking = self.ranker.rank_providers(
            valid,
            user_weights,
            {attribute: self.attribute_mapping.get(attribute, attribute) for attribute in user_weights},
            self.directions,
            self.enum_scales,
        )
        logger.info("Ranking Completed: %d providers", len(ranking))

        best = ranking[0]
        reason = self.generate_explanation(best, ranking, user_weights)
        result = RecommendationResult(
            recommended_provider=best.provider,
            overall_score=best.overall_score,
            complete_ranking=ranking,
            attribute_scores=dict(best.attribute_scores),
            reason_for_recommendation=reason,
            user_weights=user_weights,
            provider_weights=provider_weights,
            provider_attributes=dict(best.provider_attributes),
            filtered_out=filtered_out,
        )
        logger.info("Recommendation Generated: %s", best.provider)
        return result

    def run(self, requirement: Requirement, **filters: Any) -> RecommendationResult:
        """Backward-compatible workflow alias for :meth:`recommend`."""

        return self.recommend(requirement, **filters)

    def load_dataset(self) -> List[Dict[str, Any]]:
        """Load and structurally validate the configured structured JSON dataset."""

        if self._providers is not None:
            providers = [dict(provider) for provider in self._providers]
        else:
            try:
                payload = json.loads(self.dataset_path.read_text(encoding="utf-8"))
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"Structured dataset not found: {self.dataset_path}") from exc
            except json.JSONDecodeError as exc:
                raise ValueError(f"Structured dataset is not valid JSON: {self.dataset_path}") from exc
            if not isinstance(payload, list):
                raise ValueError("Structured dataset root must be a list of providers")
            providers = [dict(provider) for provider in payload if isinstance(provider, Mapping)]
        if not providers:
            raise ValueError("Structured dataset contains no providers")
        if any(not self._provider_name(provider) for provider in providers):
            raise ValueError("Every dataset row must contain a provider name")
        return providers

    def filter_providers(
        self,
        providers: Sequence[Mapping[str, Any]],
        mandatory_requirements: Optional[Mapping[str, Any]] = None,
        constraints: Optional[Mapping[str, Any]] = None,
        requested_services: Optional[Sequence[str]] = None,
        unavailable_providers: Optional[Sequence[str]] = None,
    ) -> tuple[List[Dict[str, Any]], Dict[str, List[str]]]:
        """Return eligible providers and explicit exclusion reasons."""

        mandatory_requirements = mandatory_requirements or {}
        constraints = constraints or {}
        requested_services = requested_services or []
        unavailable = {str(name).strip().casefold() for name in (unavailable_providers or [])}
        valid: List[Dict[str, Any]] = []
        excluded: Dict[str, List[str]] = {}
        for provider in providers:
            name = self._provider_name(provider) or "unknown"
            reasons: List[str] = []
            if name.casefold() in unavailable:
                reasons.append("provider marked unavailable")
            for attribute, expected in mandatory_requirements.items():
                values = self._provider_values(provider, str(attribute))
                if not values or not all(self._matches(value, expected) for value in values):
                    reasons.append(f"mandatory requirement not met: {attribute}")
            for attribute, constraint in constraints.items():
                values = self._provider_values(provider, str(attribute))
                if not values or not all(self._matches(value, constraint) for value in values):
                    reasons.append(f"constraint not met: {attribute}")
            for service in requested_services:
                values = self._provider_values(provider, str(service))
                if not values or not any(value is True for value in values):
                    reasons.append(f"requested service unavailable: {service}")
            if reasons:
                excluded[name] = reasons
            else:
                valid.append(dict(provider))
        return valid, excluded

    @staticmethod
    def generate_explanation(best: RankedProvider, ranking: Sequence[RankedProvider], user_weights: Mapping[str, float]) -> str:
        """Generate a deterministic explanation from weighted attribute scores."""

        contributions = sorted(
            ((attribute, score * user_weights.get(attribute, 0.0), score) for attribute, score in best.attribute_scores.items()),
            key=lambda item: (-item[1], item[0]),
        )
        strongest = [attribute.replace("_", " ") for attribute, contribution, score in contributions if contribution > 0 and score > 0][:3]
        tie_count = sum(entry.rank == 1 for entry in ranking)
        tie_note = f"; tied with {tie_count - 1} other provider(s)" if tie_count > 1 else ""
        priority_note = ", ".join(strongest) if strongest else "the available structured attributes"
        return f"Recommended {best.provider} for the best overall evaluation score ({best.overall_score:.6f}){tie_note}; strongest priority matches: {priority_note}."

    def _provider_values(self, provider: Mapping[str, Any], attribute: str) -> List[Any]:
        if attribute in provider:
            return [provider.get(attribute)]
        specification = self.attribute_mapping.get(attribute, attribute)
        fields = self.ranker._mapping_fields(specification)
        return [provider.get(field_name) for field_name, _ in fields]

    def _mapped_provider_fields(self, user_weights: Mapping[str, float]) -> List[str]:
        fields = []
        for attribute in user_weights:
            fields.extend(name for name, _ in self.ranker._mapping_fields(self.attribute_mapping.get(attribute, attribute)))
        return list(dict.fromkeys(fields))

    @staticmethod
    def _matches(actual: Any, expected: Any) -> bool:
        if callable(expected):
            return bool(expected(actual))
        if isinstance(expected, Mapping):
            if actual is None:
                return False
            if "equals" in expected and actual != expected["equals"]:
                return False
            if "min" in expected and (not isinstance(actual, (int, float)) or isinstance(actual, bool) or actual < expected["min"]):
                return False
            if "max" in expected and (not isinstance(actual, (int, float)) or isinstance(actual, bool) or actual > expected["max"]):
                return False
            if "contains" in expected and expected["contains"] not in actual:
                return False
            if "in" in expected and actual not in expected["in"]:
                return False
            return True
        if isinstance(actual, (list, tuple, set, frozenset)):
            return expected in actual
        if isinstance(actual, str) and isinstance(expected, str):
            return actual.casefold() == expected.casefold()
        return actual == expected

    @staticmethod
    def _provider_name(provider: Mapping[str, Any]) -> Optional[str]:
        for key in ("provider_name", "provider", "name", "csp"):
            if provider.get(key):
                return str(provider[key])
        return None
