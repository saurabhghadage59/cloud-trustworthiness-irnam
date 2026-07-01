"""Algorithm-2 evaluation scoring, aggregation, and provider ranking."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .weights import WeightCalculator


@dataclass(frozen=True)
class RankedProvider:
    """One provider's Algorithm-2 result."""

    provider: str
    overall_score: float
    attribute_scores: Dict[str, float]
    rank: int
    provider_attributes: Dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON- and negotiation-friendly representation."""

        return {
            "provider": self.provider,
            "overall_score": self.overall_score,
            "attribute_scores": dict(self.attribute_scores),
            "rank": self.rank,
            "provider_attributes": dict(self.provider_attributes),
        }


class ProviderRanker:
    """Evaluate typed provider values and produce a dense ranking.

    For numeric benefit attributes, ``e=(x-min)/(max-min)``. For cost
    attributes, ``e=(max-x)/(max-min)``. Equal non-null columns score 1.0;
    missing values score 0.0. Booleans map to 1/0, arrays to cardinality, and
    enums require an explicit numeric scale. The overall score is
    ``O_i=sum_j(user_weight_j * evaluation_ij)``.
    """

    def __init__(self, tie_tolerance: float = 1e-12) -> None:
        self.tie_tolerance = max(0.0, float(tie_tolerance))
        self.weight_calculator = WeightCalculator()

    def evaluation_scores(
        self,
        providers: Sequence[Mapping[str, Any]],
        attribute_mapping: Mapping[str, Any],
        directions: Optional[Mapping[str, str]] = None,
        enum_scales: Optional[Mapping[str, Mapping[Any, float]]] = None,
    ) -> List[Dict[str, float]]:
        """Calculate a 0..1 evaluation score for every user attribute/provider."""

        directions = directions or {}
        enum_scales = enum_scales or {}
        column_cache: Dict[str, List[float]] = {}

        def column(field_name: str) -> List[float]:
            if field_name not in column_cache:
                values = [
                    self.weight_calculator.comparable_value(provider.get(field_name), enum_scales.get(field_name))
                    for provider in providers
                ]
                column_cache[field_name] = self._normalize_column(values, directions.get(field_name, "higher"))
            return column_cache[field_name]

        results = [dict() for _ in providers]
        for user_attribute, specification in attribute_mapping.items():
            fields = self._mapping_fields(specification)
            for provider_index in range(len(providers)):
                weighted = [(column(field)[provider_index], coefficient) for field, coefficient in fields]
                denominator = sum(coefficient for _, coefficient in weighted)
                results[provider_index][user_attribute] = (
                    sum(score * coefficient for score, coefficient in weighted) / denominator
                    if denominator > 0 else 0.0
                )
        return results

    @staticmethod
    def overall_evaluation_score(attribute_scores: Mapping[str, float], user_weights: Mapping[str, float]) -> float:
        """Compute the weighted Algorithm-2 overall evaluation score."""

        return sum(float(user_weights.get(attribute, 0.0)) * float(score) for attribute, score in attribute_scores.items())

    def rank_providers(
        self,
        providers: Sequence[Mapping[str, Any]],
        user_weights: Mapping[str, float],
        attribute_mapping: Optional[Mapping[str, Any]] = None,
        directions: Optional[Mapping[str, str]] = None,
        enum_scales: Optional[Mapping[str, Mapping[Any, float]]] = None,
    ) -> List[RankedProvider]:
        """Evaluate providers, sort descending, and assign dense tie-aware ranks."""

        mapping = attribute_mapping or {attribute: attribute for attribute in user_weights}
        scores = self.evaluation_scores(providers, mapping, directions, enum_scales)
        evaluated = []
        for index, (provider, attribute_scores) in enumerate(zip(providers, scores)):
            evaluated.append((
                self._provider_name(provider, index),
                self.overall_evaluation_score(attribute_scores, user_weights),
                attribute_scores,
                dict(provider),
            ))
        evaluated.sort(key=lambda item: (-item[1], item[0].casefold()))

        ranking: List[RankedProvider] = []
        previous_score: Optional[float] = None
        current_rank = 0
        for provider, overall, attribute_scores, raw in evaluated:
            if previous_score is None or abs(overall - previous_score) > self.tie_tolerance:
                current_rank += 1
            ranking.append(RankedProvider(provider, round(overall, 12), attribute_scores, current_rank, raw))
            previous_score = overall
        return ranking

    def rank(self, *args: Any, **kwargs: Any) -> List[RankedProvider]:
        """Backward-compatible alias for :meth:`rank_providers`."""

        return self.rank_providers(*args, **kwargs)

    def calculate_evaluation_score(
        self,
        value: Any,
        peer_values: Sequence[Any],
        direction: str = "higher",
        enum_scale: Optional[Mapping[Any, float]] = None,
    ) -> float:
        """Evaluate one typed value against its provider-column peers."""

        comparable = self.weight_calculator.comparable_value(value, enum_scale)
        peers = [self.weight_calculator.comparable_value(item, enum_scale) for item in peer_values]
        return self._normalize_column([comparable, *peers], direction)[0]

    calculate_overall_score = overall_evaluation_score
    calculate_overall_evaluation_score = overall_evaluation_score

    @staticmethod
    def _normalize_column(values: Sequence[Optional[float]], direction: str) -> List[float]:
        present = [value for value in values if value is not None]
        if not present:
            return [0.0 for _ in values]
        minimum, maximum = min(present), max(present)
        lower_is_better = str(direction).strip().lower() in {"lower", "min", "cost", "lower_is_better"}
        normalized = []
        for value in values:
            if value is None:
                normalized.append(0.0)
            elif maximum == minimum:
                normalized.append(1.0)
            elif lower_is_better:
                normalized.append((maximum - value) / (maximum - minimum))
            else:
                normalized.append((value - minimum) / (maximum - minimum))
        return normalized

    @staticmethod
    def _mapping_fields(specification: Any) -> List[tuple[str, float]]:
        if isinstance(specification, str):
            return [(specification, 1.0)]
        if isinstance(specification, Mapping):
            return [(str(name), max(0.0, float(weight))) for name, weight in specification.items()]
        if isinstance(specification, Sequence) and not isinstance(specification, (str, bytes, bytearray)):
            return [(str(name), 1.0) for name in specification]
        return []

    @staticmethod
    def _provider_name(provider: Mapping[str, Any], index: int) -> str:
        for key in ("provider_name", "provider", "name", "csp"):
            if provider.get(key):
                return str(provider[key])
        return f"provider_{index + 1}"


RankingEngine = ProviderRanker
