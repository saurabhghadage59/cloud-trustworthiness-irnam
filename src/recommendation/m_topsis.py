"""Multi-layered TOPSIS recommendation strategy for Algorithm 2."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import sqrt
from typing import Any, Dict, List, Optional

from .ranking import RankedProvider
from .weights import WeightCalculator


LOWER_IS_BETTER = {"lower", "min", "cost", "lower_is_better"}

DEFAULT_CATEGORY_MAPPING = {
    "economic": (
        "cost",
        "minimum_vm_price_usd_hour",
        "storage_price_usd_gb_month",
        "CostPerHourUSD",
        "SLAViolationRate",
    ),
    "performance": (
        "availability",
        "availability_sla_percent",
        "Availability",
        "reliability",
        "Reliability",
        "throughput",
        "ThroughputMbps",
        "response_time",
        "ResponseTimeMs",
        "latency",
        "LatencyMs",
        "network",
        "BandwidthMbps",
        "storage",
        "StorageGB",
        "region_count",
        "availability_zone_count",
    ),
    "security_trust": (
        "security",
        "SecurityScore",
        "compliance",
        "ComplianceScore",
        "security_certifications",
        "compliance_certifications",
        "trust_score",
        "TrustScore",
        "customer_rating",
        "CustomerRating",
        "backup",
        "disaster_recovery",
        "best_practices",
    ),
    "service_quality": (
        "support",
        "SupportScore",
        "support_24x7",
        "support_tier",
        "documentation",
        "scalability",
        "ScalabilityScore",
        "auto_scaling",
        "load_balancer",
        "EnergyEfficiency",
        "energy_efficiency",
    ),
}


class MultiLayeredTOPSISStrategy:
    """Rank providers by category-local TOPSIS and weighted consolidation."""

    name = "M-TOPSIS"

    def __init__(
        self,
        category_mapping: Optional[Mapping[str, Sequence[str]]] = None,
        category_weights: Optional[Mapping[str, float]] = None,
        enum_scales: Optional[Mapping[str, Mapping[Any, float]]] = None,
        tie_tolerance: float = 1e-12,
        **_: Any,
    ) -> None:
        self.category_mapping = {
            str(category): tuple(str(attribute) for attribute in attributes)
            for category, attributes in (category_mapping or DEFAULT_CATEGORY_MAPPING).items()
        }
        self.configured_category_weights = dict(category_weights or {})
        self.enum_scales = {name: dict(scale) for name, scale in (enum_scales or {}).items()}
        self.tie_tolerance = max(0.0, float(tie_tolerance))
        self.weight_calculator = WeightCalculator()
        self.providers: List[Dict[str, Any]] = []
        self.attributes: List[str] = []
        self.weights: Dict[str, float] = {}
        self.directions: Dict[str, str] = {}
        self.categories: Dict[str, List[str]] = {}
        self.category_weights: Dict[str, float] = {}
        self.category_scores: Dict[str, List[float]] = {}
        self.final_scores: List[float] = []

    def fit(
        self,
        providers: Sequence[Mapping[str, Any]],
        weights: Mapping[str, float],
        directions: Optional[Mapping[str, str]] = None,
    ) -> "MultiLayeredTOPSISStrategy":
        """Prepare category decision matrices using actual provider fields only."""

        self.providers = [dict(provider) for provider in providers]
        self.directions = dict(directions or {})
        raw_weights = {str(attribute): max(0.0, float(weight)) for attribute, weight in weights.items()}
        self.attributes = [
            attribute
            for attribute in raw_weights
            if any(self._number(provider.get(attribute), attribute) is not None for provider in self.providers)
        ]
        total = sum(raw_weights[attribute] for attribute in self.attributes)
        if total <= 0 and self.attributes:
            self.weights = {attribute: 1.0 / len(self.attributes) for attribute in self.attributes}
        else:
            self.weights = {attribute: raw_weights[attribute] / total for attribute in self.attributes}
        self.categories = self._active_categories()
        self.category_weights = self._normalized_category_weights()
        self.category_scores = {
            category: self._category_topsis_scores(attributes)
            for category, attributes in self.categories.items()
        }
        self.final_scores = [
            sum(self.category_weights.get(category, 0.0) * scores[index] for category, scores in self.category_scores.items())
            for index in range(len(self.providers))
        ]
        return self

    def score(self) -> List[float]:
        return list(self.final_scores)

    def rank(self) -> List[RankedProvider]:
        ordered = sorted(range(len(self.providers)), key=lambda index: (-self.final_scores[index], self._name(index).casefold()))
        ranking: List[RankedProvider] = []
        previous_score: Optional[float] = None
        current_rank = 0
        for index in ordered:
            if previous_score is None or abs(self.final_scores[index] - previous_score) > self.tie_tolerance:
                current_rank += 1
            ranking.append(RankedProvider(
                self._name(index),
                round(self.final_scores[index], 12),
                self._provider_attribute_scores(index),
                current_rank,
                dict(self.providers[index]),
            ))
            previous_score = self.final_scores[index]
        return ranking

    def rank_category(self, category: str) -> List[RankedProvider]:
        """Return the TOPSIS ranking for one active category."""

        if category not in self.category_scores:
            raise ValueError(f"Unknown or inactive M-TOPSIS category: {category}")
        scores = self.category_scores[category]
        ordered = sorted(range(len(self.providers)), key=lambda index: (-scores[index], self._name(index).casefold()))
        result: List[RankedProvider] = []
        previous_score: Optional[float] = None
        current_rank = 0
        for index in ordered:
            if previous_score is None or abs(scores[index] - previous_score) > self.tie_tolerance:
                current_rank += 1
            result.append(RankedProvider(self._name(index), round(scores[index], 12), {category: scores[index]}, current_rank, dict(self.providers[index])))
            previous_score = scores[index]
        return result

    def recommend(self) -> Optional[RankedProvider]:
        ranking = self.rank()
        return ranking[0] if ranking else None

    def explain(self) -> Dict[str, Any]:
        best = self.recommend()
        if not best:
            return {"algorithm": self.name, "reason": "no eligible providers"}
        best_index = next((index for index in range(len(self.providers)) if self._name(index) == best.provider), 0)
        return {
            "algorithm": self.name,
            "provider": best.provider,
            "score": best.overall_score,
            "category_scores": {category: scores[best_index] for category, scores in self.category_scores.items()},
            "category_weights": dict(self.category_weights),
        }

    def _category_topsis_scores(self, attributes: Sequence[str]) -> List[float]:
        if not self.providers:
            return []
        columns = [self._attribute_column(attribute) for attribute in attributes]
        local_weights = self._local_attribute_weights(attributes)
        weighted_columns: List[List[float]] = []
        for attribute, values in zip(attributes, columns):
            norm = sqrt(sum(value * value for value in values))
            normalized = [(value / norm) if norm else 0.0 for value in values]
            weighted_columns.append([value * local_weights[attribute] for value in normalized])

        ideal: List[float] = []
        worst: List[float] = []
        for attribute, values in zip(attributes, weighted_columns):
            if str(self.directions.get(attribute, "higher")).strip().lower() in LOWER_IS_BETTER:
                ideal.append(min(values))
                worst.append(max(values))
            else:
                ideal.append(max(values))
                worst.append(min(values))

        scores = []
        for provider_index in range(len(self.providers)):
            distance_best = sqrt(sum((weighted_columns[column][provider_index] - ideal[column]) ** 2 for column in range(len(attributes))))
            distance_worst = sqrt(sum((weighted_columns[column][provider_index] - worst[column]) ** 2 for column in range(len(attributes))))
            denominator = distance_best + distance_worst
            scores.append(1.0 if denominator == 0 else distance_worst / denominator)
        return scores

    def _active_categories(self) -> Dict[str, List[str]]:
        categories: Dict[str, List[str]] = {}
        for attribute in self.attributes:
            categories.setdefault(self._category_for(attribute), []).append(attribute)
        return categories

    def _category_for(self, attribute: str) -> str:
        normalized = attribute.casefold()
        for category, attributes in self.category_mapping.items():
            if normalized in {item.casefold() for item in attributes}:
                return category
        if any(token in normalized for token in ("cost", "price", "violation")):
            return "economic"
        if any(token in normalized for token in ("security", "compliance", "trust", "rating", "backup", "recovery")):
            return "security_trust"
        if any(token in normalized for token in ("support", "documentation", "scal", "energy")):
            return "service_quality"
        return "performance"

    def _normalized_category_weights(self) -> Dict[str, float]:
        active = list(self.categories)
        if not active:
            return {}
        if self.configured_category_weights:
            raw = {category: max(0.0, float(self.configured_category_weights.get(category, 0.0))) for category in active}
            total = sum(raw.values())
            if total > 0:
                return {category: raw[category] / total for category in active}
        raw = {category: sum(self.weights[attribute] for attribute in attributes) for category, attributes in self.categories.items()}
        total = sum(raw.values())
        return {category: (raw[category] / total if total else 1.0 / len(active)) for category in active}

    def _local_attribute_weights(self, attributes: Sequence[str]) -> Dict[str, float]:
        total = sum(self.weights[attribute] for attribute in attributes)
        if total <= 0:
            return {attribute: 1.0 / len(attributes) for attribute in attributes}
        return {attribute: self.weights[attribute] / total for attribute in attributes}

    def _attribute_column(self, attribute: str) -> List[float]:
        values = [self._number(provider.get(attribute), attribute) for provider in self.providers]
        present = [value for value in values if value is not None]
        lower_is_better = str(self.directions.get(attribute, "higher")).strip().lower() in LOWER_IS_BETTER
        missing_value = max(present) if lower_is_better and present else 0.0
        return [value if value is not None else missing_value for value in values]

    def _provider_attribute_scores(self, index: int) -> Dict[str, float]:
        return {category: scores[index] for category, scores in self.category_scores.items()}

    def _number(self, value: Any, attribute: str) -> Optional[float]:
        return self.weight_calculator.comparable_value(value, self.enum_scales.get(attribute))

    def _name(self, index: int) -> str:
        provider = self.providers[index]
        for key in ("provider_name", "provider", "name", "csp"):
            if provider.get(key):
                return str(provider[key])
        return f"provider_{index + 1}"


M_TOPSIS_ALIASES = {"m-topsis", "mtopsis", "m_topsis"}
