"""Canonical typed QoS schema shared by collectors, validators, and exporters."""

SCHEMA_VERSION = "2.0.0"

ATTRIBUTE_FIELDS = (
    "provider_name",
    "availability_sla_percent",
    "minimum_vm_price_usd_hour",
    "storage_price_usd_gb_month",
    "region_count",
    "availability_zone_count",
    "gpu_support",
    "container_support",
    "kubernetes_support",
    "auto_scaling",
    "load_balancer",
    "monitoring",
    "backup",
    "disaster_recovery",
    "support_tier",
    "support_24x7",
    "security_certifications",
    "compliance_certifications",
    "free_tier",
    "hybrid_cloud",
    "documentation_url",
    "collection_date",
    "source_url",
    "source_type",
)

NUMERIC_FIELDS = {
    "availability_sla_percent": (0.0, 100.0),
    "minimum_vm_price_usd_hour": (0.0, None),
    "storage_price_usd_gb_month": (0.0, None),
    "region_count": (0, None),
    "availability_zone_count": (0, None),
}

INTEGER_FIELDS = {"region_count", "availability_zone_count"}

BOOLEAN_FIELDS = {
    "gpu_support", "container_support", "kubernetes_support", "auto_scaling",
    "load_balancer", "monitoring", "backup", "disaster_recovery", "support_24x7",
    "free_tier", "hybrid_cloud",
}

ARRAY_FIELDS = {"security_certifications", "compliance_certifications"}

SUPPORT_TIERS = {"Basic", "Developer", "Standard", "Business", "Enhanced", "Premium", "Premier", "Enterprise"}
CONFIDENCE_LEVELS = {"high", "medium", "low", "unavailable"}

PROVENANCE_FIELDS = (
    "provider", "attribute", "original_value", "parsed_value", "collection_date",
    "source_url", "source_type", "confidence", "reason",
)

MANUAL_VERIFICATION = "manual_verification_required"
OFFICIAL_DOCUMENTATION = "official_documentation"
OFFICIAL_PRICING = "official_pricing"
OFFICIAL_FEATURE = "official_feature_documentation"
OFFICIAL_COMPLIANCE = "official_compliance_documentation"
OFFICIAL_SLA = "official_sla_documentation"
OFFICIAL_REGION = "official_region_documentation"
OFFICIAL_SUPPORT = "official_support_documentation"
COLLECTION_METADATA = "collection_metadata"
