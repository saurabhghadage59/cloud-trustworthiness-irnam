"""Typed Oracle Cloud Infrastructure QoS snapshot from official public sources."""

from dataset_builder.collectors.base import OfficialSourceCollector, structured, unavailable
from dataset_builder.config.schema import OFFICIAL_COMPLIANCE, OFFICIAL_DOCUMENTATION, OFFICIAL_FEATURE, OFFICIAL_PRICING, OFFICIAL_REGION, OFFICIAL_SLA, OFFICIAL_SUPPORT

DOCS = "https://docs.oracle.com/en-us/iaas/Content/home.htm"


class OracleCollector(OfficialSourceCollector):
    provider_name = "Oracle Cloud Infrastructure (OCI)"
    attributes = {
        "availability_sla_percent": structured("Compute increased-availability data-plane SLA: 99.99%", 99.99, "https://www.oracle.com/contracts/docs/corporate_paas_iaas_public_cloud_services_soc.pdf", OFFICIAL_SLA, "medium"),
        "minimum_vm_price_usd_hour": unavailable("OCI flexible VM price requires both OCPU and memory quantities, and the brief does not define a minimum valid VM configuration.", "https://www.oracle.com/cloud/compute/pricing/", OFFICIAL_PRICING),
        "storage_price_usd_gb_month": unavailable("OCI publishes separate object, archive, block, file, performance, and request rates; no storage class was specified.", "https://www.oracle.com/cloud/storage/pricing/", OFFICIAL_PRICING),
        "region_count": structured("50 Commercial and Government Regions", 50, "https://www.oracle.com/cloud/distributed-cloud/service-availability/", OFFICIAL_REGION),
        "availability_zone_count": unavailable("OCI publishes Availability Domains per region but no authoritative global Availability Domain total.", "https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm", OFFICIAL_REGION),
        "gpu_support": structured("OCI GPU compute", True, "https://www.oracle.com/cloud/compute/gpu/", OFFICIAL_FEATURE),
        "container_support": structured("OCI Container Instances", True, "https://www.oracle.com/cloud/cloud-native/container-instances/", OFFICIAL_FEATURE),
        "kubernetes_support": structured("Oracle Container Engine for Kubernetes", True, "https://www.oracle.com/cloud/cloud-native/container-engine-kubernetes/", OFFICIAL_FEATURE),
        "auto_scaling": structured("OCI Compute autoscaling", True, "https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/autoscalinginstancepools.htm", OFFICIAL_FEATURE),
        "load_balancer": structured("OCI Load Balancer", True, "https://www.oracle.com/cloud/networking/load-balancing/", OFFICIAL_FEATURE),
        "monitoring": structured("OCI Monitoring", True, "https://docs.oracle.com/en-us/iaas/Content/Monitoring/home.htm", OFFICIAL_FEATURE),
        "backup": structured("OCI Block Volume backups", True, "https://docs.oracle.com/en-us/iaas/Content/Block/Concepts/blockvolumebackups.htm", OFFICIAL_FEATURE),
        "disaster_recovery": structured("OCI Full Stack Disaster Recovery", True, "https://www.oracle.com/cloud/full-stack-disaster-recovery/", OFFICIAL_FEATURE),
        "support_tier": structured("Oracle Premier Support", "Premier", "https://www.oracle.com/support/premier/", OFFICIAL_SUPPORT),
        "support_24x7": structured("24/7 service-request support under Oracle Premier Support", True, "https://www.oracle.com/support/premier/", OFFICIAL_SUPPORT),
        "security_certifications": structured("ISO/IEC 27001; SOC 2", ["ISO27001", "SOC2"], "https://www.oracle.com/corporate/cloud-compliance/", OFFICIAL_COMPLIANCE),
        "compliance_certifications": structured("HIPAA; PCI DSS; GDPR", ["HIPAA", "PCI DSS", "GDPR"], "https://www.oracle.com/corporate/cloud-compliance/", OFFICIAL_COMPLIANCE),
        "free_tier": structured("OCI Free Tier", True, "https://www.oracle.com/cloud/free/", OFFICIAL_DOCUMENTATION),
        "hybrid_cloud": structured("OCI Dedicated Region and Cloud@Customer hybrid deployment options", True, "https://www.oracle.com/cloud/cloud-at-customer/", OFFICIAL_FEATURE),
        "documentation_url": structured(DOCS, DOCS, DOCS, OFFICIAL_DOCUMENTATION),
        "source_url": structured(DOCS, DOCS, DOCS, OFFICIAL_DOCUMENTATION),
        "source_type": structured("Official Oracle documentation, pricing, SLA, region, support, feature, and compliance pages", "official_multi_source", DOCS, OFFICIAL_DOCUMENTATION),
    }
