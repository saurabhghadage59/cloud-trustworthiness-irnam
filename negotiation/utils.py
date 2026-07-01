"""Utility functions shared by the IRNAM negotiation modules."""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from negotiation.models import AttributeSpec, DEFAULT_NEGOTIABLE_ATTRIBUTES


def canonical_attribute(name: str) -> str:
    return name.strip().lower().replace("-", "_").replace(" ", "_")


def numeric(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize(value: float, minimum: float, maximum: float) -> float:
    """Normalize x using the paper's eta=(x-min)/(max-min) equation."""

    if maximum == minimum:
        return 1.0
    return max(0.0, min(1.0, (value - minimum) / (maximum - minimum)))


def aggregate_evaluated_value(
    normalized_values: Mapping[str, float],
    weights: Mapping[str, float],
) -> float:
    """Compute Abar=(1/k) sum(eta_attr * w_attr)."""

    if not normalized_values:
        return 0.0
    total = 0.0
    for attr, value in normalized_values.items():
        total += value * weights.get(attr, 1.0)
    return total / len(normalized_values)


def euclidean_distance(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    attrs = set(left) & set(right)
    if not attrs:
        return 0.0
    return math.sqrt(sum((left[attr] - right[attr]) ** 2 for attr in attrs))


def degree_of_difference(previous_distance: float, current_distance: float) -> float:
    """Compute alpha from Algorithm 3.

    alpha = 1 - ((D(Xn-1, Yn) - D(Xn, Yn)) / D(Xn-1, Yn))
    which simplifies to D(Xn, Yn) / D(Xn-1, Yn).
    """

    if previous_distance <= 0:
        return 0.0
    return max(0.0, min(1.0, current_distance / previous_distance))


def extract_values(data: Any) -> Dict[str, float]:
    """Extract numeric attributes from dict-like SLA or provider rows."""

    if data is None:
        return {}
    if hasattr(data, "attributes"):
        data = getattr(data, "attributes")
    if not isinstance(data, Mapping):
        return {}

    extracted: Dict[str, float] = {}
    for key, value in data.items():
        if isinstance(value, Mapping) and "value" in value:
            value = value.get("value")
        parsed = numeric(value)
        if parsed is not None:
            extracted[canonical_attribute(str(key))] = parsed
    return extracted


def extract_weights(data: Any, fallback_attributes: Iterable[str]) -> Dict[str, float]:
    """Extract attribute weights from common recommendation/SLA shapes."""

    if not isinstance(data, Mapping):
        return {attr: 1.0 for attr in fallback_attributes}

    candidates = [
        data.get("weights"),
        data.get("user_priorities"),
        data.get("attribute_weights"),
    ]
    if isinstance(data.get("priorities"), Mapping):
        candidates.append(data.get("priorities"))

    weights: Dict[str, float] = {}
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        for key, value in candidate.items():
            parsed = numeric(value)
            if parsed is not None:
                weights[canonical_attribute(str(key))] = parsed

    for attr in fallback_attributes:
        weights.setdefault(attr, 1.0)
    return weights


def extract_ranges(data: Any) -> Dict[str, Tuple[Optional[float], Optional[float]]]:
    """Extract per-attribute ranges from SLA dictionaries when present."""

    ranges: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
    if not isinstance(data, Mapping):
        return ranges
    for key, value in data.items():
        if not isinstance(value, Mapping):
            continue
        minimum = numeric(value.get("min"))
        maximum = numeric(value.get("max"))
        if minimum is not None or maximum is not None:
            ranges[canonical_attribute(str(key))] = (minimum, maximum)
    explicit = data.get("ranges")
    if isinstance(explicit, Mapping):
        for key, value in explicit.items():
            if isinstance(value, Mapping):
                ranges[canonical_attribute(str(key))] = (
                    numeric(value.get("min")),
                    numeric(value.get("max")),
                )
            elif isinstance(value, (list, tuple)) and len(value) >= 2:
                ranges[canonical_attribute(str(key))] = (numeric(value[0]), numeric(value[1]))
    return ranges


def build_attribute_specs(
    user_sla: Mapping[str, Any],
    provider_sla: Mapping[str, Any],
    recommendation: Optional[Mapping[str, Any]] = None,
    negotiable_attributes: Optional[Iterable[str]] = None,
) -> List[AttributeSpec]:
    """Build AttributeSpec objects from recommendation, user SLA, and provider SLA."""

    recommendation = recommendation or {}
    provider_attributes = recommendation.get("provider_attributes")
    if isinstance(provider_attributes, Mapping):
        provider_source = {**provider_sla, **provider_attributes}
    else:
        provider_source = provider_sla

    user_values = extract_values(user_sla)
    provider_values = extract_values(provider_source)
    if not provider_values:
        provider_values = extract_values(provider_sla)

    allowed = {
        canonical_attribute(attr)
        for attr in (negotiable_attributes or DEFAULT_NEGOTIABLE_ATTRIBUTES)
    }
    shared = sorted((set(user_values) & set(provider_values)) & allowed)
    if not shared:
        shared = sorted(set(user_values) & set(provider_values))

    user_weights = extract_weights({**recommendation, **user_sla}, shared)
    provider_weights = extract_weights(provider_sla, shared)
    user_ranges = extract_ranges(user_sla)
    provider_ranges = extract_ranges(provider_sla)

    specs: List[AttributeSpec] = []
    for attr in shared:
        user_value = user_values[attr]
        provider_value = provider_values[attr]
        inferred_min = min(user_value, provider_value)
        inferred_max = max(user_value, provider_value)
        if inferred_min == inferred_max:
            inferred_min = 0.0 if inferred_min >= 0 else inferred_min - 1.0
            inferred_max = provider_value if provider_value != inferred_min else inferred_min + 1.0

        user_min, user_max = user_ranges.get(attr, (None, None))
        provider_min, provider_max = provider_ranges.get(attr, (None, None))
        specs.append(
            AttributeSpec(
                name=attr,
                user_value=user_value,
                provider_value=provider_value,
                user_weight=user_weights.get(attr, 1.0),
                provider_weight=provider_weights.get(attr, user_weights.get(attr, 1.0)),
                user_min=user_min if user_min is not None else inferred_min,
                user_max=user_max if user_max is not None else inferred_max,
                provider_min=provider_min if provider_min is not None else inferred_min,
                provider_max=provider_max if provider_max is not None else inferred_max,
            )
        )
    return specs


def provider_name_from_recommendation(recommendation: Optional[Mapping[str, Any]]) -> str:
    if not recommendation:
        return "unknown"
    for key in ("recommended_provider", "provider", "name", "csp"):
        if recommendation.get(key):
            return str(recommendation[key])
    return "unknown"
