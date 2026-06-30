"""Typed Google Cloud QoS snapshot from official public sources."""

from dataset_builder.collectors.base import OfficialSourceCollector, structured, unavailable
from dataset_builder.config.schema import OFFICIAL_COMPLIANCE, OFFICIAL_DOCUMENTATION, OFFICIAL_FEATURE, OFFICIAL_PRICING, OFFICIAL_REGION, OFFICIAL_SLA, OFFICIAL_SUPPORT

DOCS = "https://cloud.google.com/docs"


class GCPCollector(OfficialSourceCollector):
    provider_name = "Google Cloud Platform (GCP)"
    attributes = {
        "availability_sla_percent": structured("Premium Tier instances in multiple zones: >=99.99% monthly uptime", 99.99, "https://cloud.google.com/compute/sla", OFFICIAL_SLA),
        "minimum_vm_price_usd_hour": unavailable("Compute Engine pricing is SKU, configuration, operating-system, discount, and location dependent; the product page's rounded starting price is not an exact reproducible minimum.", "https://cloud.google.com/compute/vm-instance-pricing", OFFICIAL_PRICING),
        "storage_price_usd_gb_month": unavailable("Cloud Storage class and reference location were not specified; official prices vary by class, location, operation, and retrieval.", "https://cloud.google.com/storage/pricing", OFFICIAL_PRICING),
        "region_count": structured("43 Regions", 43, "https://cloud.google.com/about/locations", OFFICIAL_REGION),
        "availability_zone_count": structured("130 Zones", 130, "https://cloud.google.com/about/locations", OFFICIAL_REGION),
        "gpu_support": structured("Compute Engine GPU resources", True, "https://cloud.google.com/compute/docs/gpus", OFFICIAL_FEATURE),
        "container_support": structured("Cloud Run and container products", True, "https://cloud.google.com/products/containers", OFFICIAL_FEATURE),
        "kubernetes_support": structured("Google Kubernetes Engine", True, "https://cloud.google.com/kubernetes-engine", OFFICIAL_FEATURE),
        "auto_scaling": structured("Compute Engine managed instance group autoscaler", True, "https://cloud.google.com/compute/docs/autoscaler", OFFICIAL_FEATURE),
        "load_balancer": structured("Cloud Load Balancing", True, "https://cloud.google.com/load-balancing", OFFICIAL_FEATURE),
        "monitoring": structured("Cloud Monitoring", True, "https://cloud.google.com/monitoring", OFFICIAL_FEATURE),
        "backup": structured("Backup and DR Service", True, "https://cloud.google.com/backup-disaster-recovery", OFFICIAL_FEATURE),
        "disaster_recovery": structured("Disaster recovery planning guidance and Backup and DR", True, "https://cloud.google.com/architecture/dr-scenarios-planning-guide", OFFICIAL_FEATURE),
        "support_tier": structured("Premium Support", "Premium", "https://cloud.google.com/support", OFFICIAL_SUPPORT),
        "support_24x7": structured("24/7 support is available with qualifying support services", True, "https://cloud.google.com/support", OFFICIAL_SUPPORT),
        "security_certifications": structured("ISO/IEC 27001; SOC 2", ["ISO27001", "SOC2"], "https://cloud.google.com/security/compliance/offerings", OFFICIAL_COMPLIANCE),
        "compliance_certifications": structured("HIPAA; PCI DSS; GDPR", ["HIPAA", "PCI DSS", "GDPR"], "https://cloud.google.com/security/compliance/offerings", OFFICIAL_COMPLIANCE),
        "free_tier": structured("Google Cloud Free Program", True, "https://cloud.google.com/free", OFFICIAL_DOCUMENTATION),
        "hybrid_cloud": structured("Google Distributed Cloud and Anthos hybrid capabilities", True, "https://cloud.google.com/distributed-cloud", OFFICIAL_FEATURE),
        "documentation_url": structured(DOCS, DOCS, DOCS, OFFICIAL_DOCUMENTATION),
        "source_url": structured(DOCS, DOCS, DOCS, OFFICIAL_DOCUMENTATION),
        "source_type": structured("Official Google documentation, pricing, SLA, region, support, feature, and compliance pages", "official_multi_source", DOCS, OFFICIAL_DOCUMENTATION),
    }
