"""Validation for typed QoS rows, provenance, enums, ranges, and URLs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from numbers import Real
from typing import List, Sequence
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from dataset_builder.config.schema import (
    ARRAY_FIELDS, ATTRIBUTE_FIELDS, BOOLEAN_FIELDS, CONFIDENCE_LEVELS, INTEGER_FIELDS,
    NUMERIC_FIELDS, SUPPORT_TIERS,
)
from dataset_builder.models.provider import Provider


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    provider: str
    attribute: str
    message: str

    def as_dict(self):
        return asdict(self)


class DatasetValidator:
    def validate_provider(self, provider: Provider) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for attribute in ATTRIBUTE_FIELDS:
            current = getattr(provider, attribute)
            if current is None:
                issues.append(ValidationIssue("warning", "missing_value", provider.provider_name, attribute, f"{attribute} is NULL"))

        for attribute, (minimum, maximum) in NUMERIC_FIELDS.items():
            current = getattr(provider, attribute)
            if current is None:
                continue
            valid_type = isinstance(current, Real) and not isinstance(current, bool)
            if attribute in INTEGER_FIELDS:
                valid_type = isinstance(current, int) and not isinstance(current, bool)
            if not valid_type or current < minimum or (maximum is not None and current > maximum):
                issues.append(ValidationIssue("error", "invalid_numeric_range", provider.provider_name, attribute, f"{attribute} has invalid numeric value {current!r}"))

        for attribute in BOOLEAN_FIELDS:
            current = getattr(provider, attribute)
            if current is not None and not isinstance(current, bool):
                issues.append(ValidationIssue("error", "invalid_boolean", provider.provider_name, attribute, f"{attribute} must be True, False, or NULL"))

        if provider.support_tier is not None and provider.support_tier not in SUPPORT_TIERS:
            issues.append(ValidationIssue("error", "invalid_enum", provider.provider_name, "support_tier", f"Unknown support tier: {provider.support_tier}"))

        for attribute in ARRAY_FIELDS:
            current = getattr(provider, attribute)
            if current is not None and (not isinstance(current, list) or any(not isinstance(item, str) for item in current)):
                issues.append(ValidationIssue("error", "invalid_array", provider.provider_name, attribute, f"{attribute} must be an array of strings or NULL"))

        source_attributes = [record.attribute for record in provider.sources]
        if len(set(source_attributes)) != len(source_attributes):
            issues.append(ValidationIssue("error", "duplicate_provenance", provider.provider_name, "sources", "An attribute has duplicate provenance records"))
        for attribute in ATTRIBUTE_FIELDS:
            if attribute not in source_attributes:
                issues.append(ValidationIssue("error", "missing_provenance", provider.provider_name, attribute, f"{attribute} has no provenance record"))
        for record in provider.sources:
            if record.attribute in ATTRIBUTE_FIELDS and record.parsed_value != getattr(provider, record.attribute):
                issues.append(ValidationIssue("error", "provenance_mismatch", provider.provider_name, record.attribute, "Parsed provenance value does not match provider value"))
            if record.confidence not in CONFIDENCE_LEVELS:
                issues.append(ValidationIssue("error", "invalid_confidence", provider.provider_name, record.attribute, f"Unknown confidence: {record.confidence}"))
            if record.parsed_value is None and not record.reason:
                issues.append(ValidationIssue("error", "missing_null_reason", provider.provider_name, record.attribute, "NULL value must record a reason"))
        return issues

    def validate(self, providers: Sequence[Provider]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        seen = set()
        for provider in providers:
            key = provider.provider_name.strip().casefold()
            if key in seen:
                issues.append(ValidationIssue("error", "duplicate_provider", provider.provider_name, "provider_name", "Provider appears more than once"))
            seen.add(key)
            issues.extend(self.validate_provider(provider))
            issues.extend(self.validate_urls(provider))
        return issues

    def validate_urls(self, provider: Provider, check_reachability: bool = False, timeout: float = 5.0) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        urls = {record.source_url for record in provider.sources if record.source_url}
        urls.update(url for url in (provider.documentation_url, provider.source_url) if url)
        for url in sorted(urls):
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.netloc:
                issues.append(ValidationIssue("error", "broken_url", provider.provider_name, "source_url", f"Invalid URL: {url}"))
                continue
            if check_reachability:
                try:
                    request = Request(url, method="HEAD", headers={"User-Agent": "IRNAM-Dataset-Builder/2.0"})
                    with urlopen(request, timeout=timeout) as response:
                        if response.status >= 400:
                            raise OSError(f"HTTP {response.status}")
                except Exception as exc:
                    issues.append(ValidationIssue("warning", "broken_url", provider.provider_name, "source_url", f"Could not verify {url}: {exc}"))
        return issues
