from __future__ import annotations

import logging
from typing import Dict, Mapping, Sequence

from .models import DEFAULT_ATTRIBUTE_ORDER, RequirementAttribute, RequirementPriority

logger = logging.getLogger(__name__)


class PriorityManager:
    """Assign and normalize priorities for all supported requirement attributes."""

    def __init__(self, attribute_order: tuple[str, ...] = DEFAULT_ATTRIBUTE_ORDER) -> None:
        self.attribute_order = attribute_order

    def assign(self, request: object) -> Dict[str, RequirementAttribute]:
        """Convert a raw request mapping or sequence into a structured attribute map."""

        payload = self._normalize_request(request)
        attributes: Dict[str, RequirementAttribute] = {}
        for name in self.attribute_order:
            raw_value = payload.get(name)
            if raw_value is None:
                continue
            priority = RequirementPriority.from_value(str(raw_value))
            attributes[name] = RequirementAttribute(
                name=name,
                priority=priority,
                raw_value=str(raw_value),
            )
        logger.debug("Assigned priorities to %d attributes", len(attributes))
        return attributes

    def _normalize_request(self, request: object) -> Mapping[str, object]:
        if isinstance(request, Mapping):
            return request
        if isinstance(request, Sequence) and not isinstance(request, (str, bytes, bytearray)):
            normalized: Dict[str, object] = {}
            for key, value in request:
                normalized_key = str(key).strip().lower()
                if normalized_key in normalized:
                    raise ValueError(f"Duplicate priorities: attribute '{key}' was provided more than once")
                normalized[normalized_key] = value
            return normalized
        raise TypeError("Request must be a mapping or sequence of attribute/value pairs")
