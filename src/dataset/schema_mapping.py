"""Schema adapter for heterogeneous cloud-service QoS CSV datasets.

The recommendation layer consumes canonical snake-case names.  This adapter
keeps source headers intact while recognising common research-dataset aliases,
so future MCDM methods can reuse the exact same normalized row objects.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

COLUMN_MAPPING = {
    "provider": "provider_name", "provider name": "provider_name", "service name": "provider_name",
    "service": "provider_name", "name": "provider_name", "wsdl address": "wsdl_address",
    "availability": "availability", "reliability": "reliability", "throughput": "throughput",
    "throughputmbps": "throughput", "response time": "response_time", "response_time": "response_time",
    "responsetimems": "response_time", "latency": "latency", "latencyms": "latency",
    "documentation": "documentation", "documentation score": "documentation",
    "best practices": "best_practices", "best practice": "best_practices",
    "region": "region", "servicetype": "service_type", "service type": "service_type",
    "securityscore": "security", "security": "security", "costperhourusd": "cost", "cost": "cost",
    "scalabilityscore": "scalability", "scalability": "scalability", "supportscore": "support", "support": "support",
}

def canonical_column_name(name: str | None) -> str | None:
    """Return a canonical field for a header, or ``None`` for unknown/blank columns."""
    normalized = " ".join((name or "").strip().replace("_", " ").split()).casefold()
    return COLUMN_MAPPING.get(normalized)

def adapt_row(row: Mapping[str | None, Any]) -> dict[str, Any]:
    """Preserve raw fields and add canonical fields without dataset-specific branches."""
    adapted = {str(key): value for key, value in row.items() if key and str(key).strip()}
    for source, value in row.items():
        canonical = canonical_column_name(source)
        if canonical and canonical not in adapted:
            adapted[canonical] = value

    # A provider/service identifier is the only mandatory field.  Some public
    # SOAP corpora put a numeric service id in ``Service Name`` and a readable
    # service identifier in the WSDL column; prefer a non-URL textual identity.
    candidate = adapted.get("provider_name")
    wsdl = adapted.get("wsdl_address")
    if _is_numeric_identifier(candidate) and _is_text_identifier(wsdl):
        adapted["provider_name"] = wsdl
    return adapted

def _is_numeric_identifier(value: Any) -> bool:
    try:
        float(str(value).strip())
        return True
    except (TypeError, ValueError):
        return False

def _is_text_identifier(value: Any) -> bool:
    value = str(value or "").strip()
    return bool(value) and not _is_numeric_identifier(value) and "://" not in value
