from __future__ import annotations

import logging
from typing import Mapping

from .models import DEFAULT_ATTRIBUTE_ORDER, Requirement, RequirementAttribute

logger = logging.getLogger(__name__)


class RequirementParser:
    """Parse validated raw requests into a structured Requirement object."""

    def __init__(self, attribute_order: tuple[str, ...] = DEFAULT_ATTRIBUTE_ORDER) -> None:
        self.attribute_order = attribute_order

    def parse(self, request: Mapping[str, object], attributes: Mapping[str, RequirementAttribute]) -> Requirement:
        """Create a Requirement object from validated attributes and raw input."""

        ordered_names = [name for name in self.attribute_order if name in attributes]
        priority_values = {name: attributes[name].priority.value for name in ordered_names}
        requirement = Requirement(
            attributes=dict(attributes),
            attribute_names=ordered_names,
            priority_values=priority_values,
        )
        logger.debug("Parsed requirement with %d attributes", len(ordered_names))
        return requirement
