from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


DEFAULT_ATTRIBUTE_ORDER = (
    "availability",
    "reliability",
    "security",
    "cost",
    "response_time",
    "scalability",
    "support",
    "storage",
    "network",
)


class RequirementPriority(str, Enum):
    """Supported user priority levels for requirement processing."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

    @classmethod
    def from_value(cls, value: str) -> "RequirementPriority":
        """Parse a user-facing priority into the enum representation."""

        normalized = cls._normalize(value)
        for priority in cls:
            if priority.value == normalized:
                return priority
        raise ValueError(f"Unsupported priority value: {value}")

    @classmethod
    def _normalize(cls, value: str) -> str:
        if value is None:
            raise ValueError("Priority value cannot be empty")
        normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in {"very_high", "veryhigh"}:
            return cls.VERY_HIGH.value
        if normalized in {"very_low", "verylow"}:
            return cls.VERY_LOW.value
        return normalized

    @property
    def display_name(self) -> str:
        """Return a human-readable form of the priority."""

        return self.value.replace("_", " ").title()


@dataclass(frozen=True)
class RequirementAttribute:
    """A single requirement attribute and its assigned priority."""

    name: str
    priority: RequirementPriority
    raw_value: str


@dataclass
class Requirement:
    """Structured user requirements produced by the requirement processor."""

    attributes: Dict[str, RequirementAttribute] = field(default_factory=dict)
    attribute_names: List[str] = field(default_factory=list)
    priority_values: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        """Serialize the requirement into a dictionary for downstream consumers."""

        return {
            "attribute_names": list(self.attribute_names),
            "priority_values": dict(self.priority_values),
            "attributes": {
                name: {
                    "name": attribute.name,
                    "priority": attribute.priority.value,
                    "raw_value": attribute.raw_value,
                }
                for name, attribute in self.attributes.items()
            },
        }
