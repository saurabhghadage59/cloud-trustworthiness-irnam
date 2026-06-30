"""Typed provider QoS and per-attribute provenance models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from dataset_builder.config.schema import ATTRIBUTE_FIELDS


@dataclass(frozen=True)
class SourceRecord:
    """Evidence and parsing audit trail for one provider attribute.

    ``collected_value`` remains the sixth-compatible legacy parsed-value field.
    New exports expose it as ``parsed_value``.
    """

    provider: str
    attribute: str
    collected_value: Any
    source_url: Optional[str]
    source_type: str
    collection_date: str
    original_value: Any = None
    confidence: str = "high"
    reason: Optional[str] = None

    @property
    def parsed_value(self) -> Any:
        return self.collected_value

    def as_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "attribute": self.attribute,
            "original_value": self.original_value,
            "parsed_value": self.parsed_value,
            "collection_date": self.collection_date,
            "source_url": self.source_url,
            "source_type": self.source_type,
            "confidence": self.confidence,
            "reason": self.reason,
        }


@dataclass
class Provider:
    """One immediately consumable, deliberately unnormalised QoS row."""

    provider_name: str
    availability_sla_percent: Optional[float] = None
    minimum_vm_price_usd_hour: Optional[float] = None
    storage_price_usd_gb_month: Optional[float] = None
    region_count: Optional[int] = None
    availability_zone_count: Optional[int] = None
    gpu_support: Optional[bool] = None
    container_support: Optional[bool] = None
    kubernetes_support: Optional[bool] = None
    auto_scaling: Optional[bool] = None
    load_balancer: Optional[bool] = None
    monitoring: Optional[bool] = None
    backup: Optional[bool] = None
    disaster_recovery: Optional[bool] = None
    support_tier: Optional[str] = None
    support_24x7: Optional[bool] = None
    security_certifications: Optional[List[str]] = None
    compliance_certifications: Optional[List[str]] = None
    free_tier: Optional[bool] = None
    hybrid_cloud: Optional[bool] = None
    documentation_url: Optional[str] = None
    collection_date: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    sources: List[SourceRecord] = field(default_factory=list, repr=False)

    def as_dict(self) -> Dict[str, Any]:
        return {name: getattr(self, name) for name in ATTRIBUTE_FIELDS}

    # Read-only Phase-1 aliases retained for downstream compatibility.
    @property
    def availability_sla(self):
        return self.availability_sla_percent

    @property
    def compute_pricing(self):
        return self.minimum_vm_price_usd_hour

    @property
    def storage_pricing(self):
        return self.storage_price_usd_gb_month

    @property
    def regions(self):
        return self.region_count

    @property
    def availability_zones(self):
        return self.availability_zone_count

    @property
    def support_plans(self):
        return self.support_tier

    @property
    def last_updated(self):
        return self.collection_date
