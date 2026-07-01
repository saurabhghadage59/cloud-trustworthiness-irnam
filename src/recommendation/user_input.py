from __future__ import annotations

import logging
from typing import Mapping

from .models import Requirement
from .priority_manager import PriorityManager
from .requirement_parser import RequirementParser
from .validation import RequirementValidationError, RequirementValidator

logger = logging.getLogger(__name__)


class UserRequirementProcessor:
    """Process user-supplied requirement priorities into a Requirement object."""

    def __init__(self) -> None:
        self.validator = RequirementValidator()
        self.priority_manager = PriorityManager()
        self.requirement_parser = RequirementParser()

    def process(self, request: Mapping[str, object]) -> Requirement:
        """Validate, normalize, and parse a raw requirement request."""

        try:
            self.validator.validate(request)
            attributes = self.priority_manager.assign(request)
        except ValueError as exc:
            raise RequirementValidationError(str(exc)) from exc
        requirement = self.requirement_parser.parse(request, attributes)
        logger.info("Processed requirement request with %d attributes", len(requirement.attributes))
        return requirement
