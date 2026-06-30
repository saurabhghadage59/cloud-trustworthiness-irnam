"""Typed Microsoft Azure QoS snapshot from official public sources."""

from dataset_builder.collectors.base import OfficialSourceCollector, structured, unavailable
from dataset_builder.config.schema import OFFICIAL_COMPLIANCE, OFFICIAL_DOCUMENTATION, OFFICIAL_FEATURE, OFFICIAL_PRICING, OFFICIAL_REGION, OFFICIAL_SLA, OFFICIAL_SUPPORT

DOCS = "https://learn.microsoft.com/en-us/azure/"


class AzureCollector(OfficialSourceCollector):
    provider_name = "Microsoft Azure"
    attributes = {
        "availability_sla_percent": structured("99.99% uptime SLA for virtual machines using Availability Zones", 99.99, "https://azure.microsoft.com/en-us/explore/global-infrastructure/availability-zones/", OFFICIAL_SLA),
        "minimum_vm_price_usd_hour": unavailable("Azure VM prices are dynamically calculated by region, currency, operating system, agreement, and VM size; no exact global minimum is published.", "https://azure.microsoft.com/en-us/pricing/details/virtual-machines/linux/", OFFICIAL_PRICING),
        "storage_price_usd_gb_month": unavailable("Storage service, redundancy, access tier, and reference region were not specified; Azure publishes multiple rates.", "https://azure.microsoft.com/en-us/pricing/details/storage/", OFFICIAL_PRICING),
        "region_count": unavailable("Microsoft publishes '70+ Azure regions', which is not an exact machine-readable count.", "https://azure.microsoft.com/en-us/explore/global-infrastructure/", OFFICIAL_REGION),
        "availability_zone_count": unavailable("Microsoft publishes zone support by region but no authoritative global availability-zone total.", "https://learn.microsoft.com/en-us/azure/reliability/regions-list", OFFICIAL_REGION),
        "gpu_support": structured("GPU-accelerated Azure VM sizes", True, "https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/gpu-accelerated/", OFFICIAL_FEATURE),
        "container_support": structured("Azure Container Instances and Azure Container Apps", True, "https://azure.microsoft.com/en-us/products/category/containers/", OFFICIAL_FEATURE),
        "kubernetes_support": structured("Azure Kubernetes Service", True, "https://azure.microsoft.com/en-us/products/kubernetes-service/", OFFICIAL_FEATURE),
        "auto_scaling": structured("Azure Monitor autoscale", True, "https://learn.microsoft.com/en-us/azure/azure-monitor/autoscale/autoscale-overview", OFFICIAL_FEATURE),
        "load_balancer": structured("Azure Load Balancer", True, "https://azure.microsoft.com/en-us/products/load-balancer/", OFFICIAL_FEATURE),
        "monitoring": structured("Azure Monitor", True, "https://azure.microsoft.com/en-us/products/monitor/", OFFICIAL_FEATURE),
        "backup": structured("Azure Backup", True, "https://azure.microsoft.com/en-us/products/backup/", OFFICIAL_FEATURE),
        "disaster_recovery": structured("Azure Site Recovery", True, "https://azure.microsoft.com/en-us/products/site-recovery/", OFFICIAL_FEATURE),
        "support_tier": structured("Enterprise support options", "Enterprise", "https://azure.microsoft.com/en-us/support/plans/", OFFICIAL_SUPPORT),
        "support_24x7": structured("24x7 technical support is available in qualifying paid plans", True, "https://azure.microsoft.com/en-us/support/plans/", OFFICIAL_SUPPORT),
        "security_certifications": structured("ISO/IEC 27001; SOC 2", ["ISO27001", "SOC2"], "https://learn.microsoft.com/en-us/azure/compliance/", OFFICIAL_COMPLIANCE),
        "compliance_certifications": structured("HIPAA; PCI DSS; GDPR", ["HIPAA", "PCI DSS", "GDPR"], "https://learn.microsoft.com/en-us/azure/compliance/", OFFICIAL_COMPLIANCE),
        "free_tier": structured("Azure free account and free services", True, "https://azure.microsoft.com/en-us/pricing/free-services/", OFFICIAL_DOCUMENTATION),
        "hybrid_cloud": structured("Azure Arc hybrid and multicloud management", True, "https://azure.microsoft.com/en-us/products/azure-arc/", OFFICIAL_FEATURE),
        "documentation_url": structured(DOCS, DOCS, DOCS, OFFICIAL_DOCUMENTATION),
        "source_url": structured(DOCS, DOCS, DOCS, OFFICIAL_DOCUMENTATION),
        "source_type": structured("Official Microsoft documentation, pricing, SLA, region, support, feature, and compliance pages", "official_multi_source", DOCS, OFFICIAL_DOCUMENTATION),
    }
