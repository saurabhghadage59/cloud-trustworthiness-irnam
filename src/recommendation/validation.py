from __future__ import annotations

import logging
from typing import Iterable, Mapping, Optional, Sequence

from .models import DEFAULT_ATTRIBUTE_ORDER, RequirementPriority

logger = logging.getLogger(__name__)


class RequirementValidationError(ValueError):
    """Raised when user requirements are incomplete or invalid."""


class RequirementValidator:
    """Validate incoming user requirement payloads before parsing."""

    def __init__(self, supported_attributes: Optional[Iterable[str]] = None) -> None:
        self.supported_attributes = tuple(supported_attributes or DEFAULT_ATTRIBUTE_ORDER)

    def validate(self, request: object) -> None:
        """Validate a user requirement payload and raise a descriptive error if needed."""

        if not request:
            raise RequirementValidationError("Empty request: no requirements were provided")

        if isinstance(request, Mapping):
            payload = request
        elif isinstance(request, Sequence) and not isinstance(request, (str, bytes, bytearray)):
            payload = dict(request)
        else:
            raise RequirementValidationError("Request must be a mapping of attribute names to priorities")

        provided_names = {str(name).strip().lower() for name in payload.keys() if str(name).strip()}
        missing = [name for name in self.supported_attributes if name not in provided_names]
        if missing:
            raise RequirementValidationError(
                f"Missing required attributes: {', '.join(missing)}"
            )

        values = [str(value).strip() for value in payload.values() if str(value).strip()]
        if not values:
            raise RequirementValidationError("Empty request: no priority values were provided")

        seen_attributes = set()
        if isinstance(payload, Mapping):
            items = payload.items()
        else:
            items = payload
        for attribute_name, raw_value in items:
            normalized_name = str(attribute_name).strip().lower()
            if normalized_name in seen_attributes:
                raise RequirementValidationError(
                    f"Duplicate priorities: attribute '{attribute_name}' was provided more than once"
                )
            seen_attributes.add(normalized_name)
            try:
                RequirementPriority.from_value(str(raw_value))
            except ValueError as exc:
                raise RequirementValidationError(
                    f"Invalid priority value '{raw_value}' for attribute '{attribute_name}'"
                ) from exc

        logger.debug("Validated %d requirement attributes", len(payload))
