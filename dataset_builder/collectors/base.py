"""Base class for deterministic, typed official-source collectors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Mapping, Optional

from dataset_builder.config.schema import ATTRIBUTE_FIELDS, COLLECTION_METADATA, MANUAL_VERIFICATION
from dataset_builder.models.provider import Provider, SourceRecord
from dataset_builder.validators.dataset import DatasetValidator


@dataclass(frozen=True)
class CollectedAttribute:
    original_value: Any
    parsed_value: Any
    source_url: Optional[str]
    source_type: str
    confidence: str = "high"
    reason: Optional[str] = None


class CollectionError(ValueError):
    """Raised when a collector produces structurally invalid data."""


class OfficialSourceCollector:
    provider_name = ""
    attributes: Mapping[str, CollectedAttribute] = {}

    def __init__(self, collection_date: Optional[str] = None):
        self.collection_date = collection_date or date.today().isoformat()

    def collect_metadata(self) -> Dict[str, CollectedAttribute]:
        return dict(self.attributes)

    def collect(self) -> Provider:
        metadata = self.collect_metadata()
        metadata.setdefault("provider_name", structured(self.provider_name, self.provider_name, None, COLLECTION_METADATA))
        metadata.setdefault("collection_date", structured(self.collection_date, self.collection_date, None, COLLECTION_METADATA))
        values = {attribute: metadata[attribute].parsed_value if attribute in metadata else None for attribute in ATTRIBUTE_FIELDS}
        values["provider_name"] = self.provider_name

        sources = []
        for attribute in ATTRIBUTE_FIELDS:
            item = metadata.get(attribute)
            sources.append(SourceRecord(
                provider=self.provider_name,
                attribute=attribute,
                collected_value=item.parsed_value if item else None,
                source_url=item.source_url if item else None,
                source_type=item.source_type if item else MANUAL_VERIFICATION,
                collection_date=self.collection_date,
                original_value=item.original_value if item else None,
                confidence=item.confidence if item else "unavailable",
                reason=item.reason if item else "Collector did not supply this attribute.",
            ))
        provider = Provider(**values, sources=sources)
        errors = [issue for issue in DatasetValidator().validate_provider(provider) if issue.severity == "error"]
        if errors:
            raise CollectionError("; ".join(issue.message for issue in errors))
        return provider


def structured(original_value: Any, parsed_value: Any, url: Optional[str], source_type: str, confidence: str = "high") -> CollectedAttribute:
    return CollectedAttribute(original_value, parsed_value, url, source_type, confidence)


def unavailable(reason: str, url: Optional[str], source_type: str) -> CollectedAttribute:
    return CollectedAttribute(None, None, url, source_type, "unavailable", reason)


def value(raw: Any, url: Optional[str], source_type: str) -> CollectedAttribute:
    """Phase-1 helper retained for third-party collector compatibility."""
    return structured(raw, raw, url, source_type)
