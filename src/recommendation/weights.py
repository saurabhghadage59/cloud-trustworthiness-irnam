"""Generic user and provider weighting for IRNAM Algorithms 1 and 2."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from numbers import Real
from typing import Any, Dict, Iterable, Optional

from .models import Requirement, RequirementPriority


PRIORITY_SCORES = {
    RequirementPriority.VERY_LOW.value: 1.0,
    RequirementPriority.LOW.value: 2.0,
    RequirementPriority.MEDIUM.value: 3.0,
    RequirementPriority.HIGH.value: 4.0,
    RequirementPriority.VERY_HIGH.value: 5.0,
}


class WeightCalculator:
    """Calculate normalized weights without assuming any attribute names.

    User weight formula for attribute ``j`` is ``w_j = p_j / sum(p)``, where
    ``p_j`` is the positive numeric priority score. Provider weights normalize
    comparable provider values per attribute: ``v_ij / sum_i(v_ij)`` after
    converting booleans to 0/1 and arrays to their cardinality. Missing or
    unsupported values contribute zero and are never estimated.
    """

    def calculate_user_weights(self, priorities: Requirement | Mapping[str, Any]) -> Dict[str, float]:
        """Return normalized user weights for any non-empty attribute mapping."""

        raw = self._priority_mapping(priorities)
        scores = {str(name): self._priority_score(value) for name, value in raw.items()}
        if not scores:
            raise ValueError("At least one user priority is required")
        if any(score < 0 for score in scores.values()):
            raise ValueError("Priority scores cannot be negative")
        total = sum(scores.values())
        if total <= 0:
            equal = 1.0 / len(scores)
            return {name: equal for name in scores}
        return {name: score / total for name, score in scores.items()}

    def calculate_provider_weights(
        self,
        providers: Sequence[Mapping[str, Any]],
        attributes: Optional[Iterable[str]] = None,
        enum_scales: Optional[Mapping[str, Mapping[Any, float]]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """Return per-provider, per-attribute dataset-derived weights.

        Each attribute column sums to one when it has positive comparable data.
        Columns containing only unavailable values remain zero.
        """

        if not providers:
            return {}
        names = [self._provider_name(provider, index) for index, provider in enumerate(providers)]
        selected = list(attributes or self._discover_attributes(providers))
        scales = enum_scales or {}
        result = {name: {} for name in names}
        for attribute in selected:
            values = [self.comparable_value(provider.get(attribute), scales.get(attribute)) for provider in providers]
            total = sum(value for value in values if value is not None and value > 0)
            for name, value in zip(names, values):
                result[name][attribute] = (value / total) if value is not None and value > 0 and total else 0.0
        return result

    def calculate(self, priorities: Requirement | Mapping[str, Any]) -> Dict[str, float]:
        """Backward-compatible alias for :meth:`calculate_user_weights`."""

        return self.calculate_user_weights(priorities)

    calculate_weights = calculate_user_weights
    compute_user_weights = calculate_user_weights
    compute_provider_weights = calculate_provider_weights

    @staticmethod
    def comparable_value(value: Any, enum_scale: Optional[Mapping[Any, float]] = None) -> Optional[float]:
        """Convert a typed dataset value to a non-negative comparable scalar."""

        if value is None:
            return None
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, Real):
            return max(0.0, float(value))
        if isinstance(value, (list, tuple, set, frozenset)):
            return float(len(value))
        if enum_scale is not None and value in enum_scale:
            return max(0.0, float(enum_scale[value]))
        return None

    @staticmethod
    def _priority_mapping(priorities: Requirement | Mapping[str, Any]) -> Mapping[str, Any]:
        if isinstance(priorities, Requirement):
            return {name: attribute.priority for name, attribute in priorities.attributes.items()}
        if isinstance(priorities, Mapping):
            return priorities
        raise TypeError("Priorities must be a Requirement or mapping")

    @staticmethod
    def _priority_score(value: Any) -> float:
        if hasattr(value, "priority"):
            value = value.priority
        if isinstance(value, RequirementPriority):
            return PRIORITY_SCORES[value.value]
        if isinstance(value, Real) and not isinstance(value, bool):
            return float(value)
        normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in PRIORITY_SCORES:
            return PRIORITY_SCORES[normalized]
        try:
            return float(normalized)
        except ValueError as exc:
            raise ValueError(f"Unsupported priority value: {value}") from exc

    @staticmethod
    def _discover_attributes(providers: Sequence[Mapping[str, Any]]) -> Iterable[str]:
        ignored = {"provider", "provider_name", "name", "source_url", "source_type", "documentation_url", "collection_date"}
        return sorted({str(key) for provider in providers for key in provider if str(key) not in ignored})

    @staticmethod
    def _provider_name(provider: Mapping[str, Any], index: int) -> str:
        for key in ("provider_name", "provider", "name", "csp"):
            if provider.get(key):
                return str(provider[key])
        return f"provider_{index + 1}"
