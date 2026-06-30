"""Typed IBM Cloud QoS snapshot from official public sources."""

from dataset_builder.collectors.base import OfficialSourceCollector, structured, unavailable
from dataset_builder.config.schema import OFFICIAL_COMPLIANCE, OFFICIAL_DOCUMENTATION, OFFICIAL_FEATURE, OFFICIAL_PRICING, OFFICIAL_REGION, OFFICIAL_SLA, OFFICIAL_SUPPORT

DOCS = "https://cloud.ibm.com/docs"
LOCATIONS = "https://cloud.ibm.com/docs/overview?topic=overview-locations"


class IBMCollector(OfficialSourceCollector):
    provider_name = "IBM Cloud"
    attributes = {
        "availability_sla_percent": structured("IBM regional services distributed across three zones generally provide 99.99% tier-3 availability", 99.99, LOCATIONS, OFFICIAL_SLA),
        "minimum_vm_price_usd_hour": unavailable("IBM VPC virtual-server pricing is profile, operating-system, location, and configuration dependent and no exact global minimum is published.", "https://www.ibm.com/products/virtual-servers/pricing", OFFICIAL_PRICING),
        "storage_price_usd_gb_month": unavailable("IBM Cloud storage pricing varies by service, class, location, capacity, and usage; no storage class was specified.", "https://www.ibm.com/products/cloud-object-storage/pricing", OFFICIAL_PRICING),
        "region_count": structured("MZR table lists Dallas, Sao Paulo, Toronto, Washington DC, Frankfurt, London, Madrid, Sydney, Tokyo, Chennai, Montreal, Mumbai, and Osaka", 13, LOCATIONS, OFFICIAL_REGION, "medium"),
        "availability_zone_count": structured("The official region table lists 40 universal zones across the 13 MZR and single-campus MZR entries", 40, LOCATIONS, OFFICIAL_REGION, "medium"),
        "gpu_support": structured("GPU instance profiles for IBM Cloud VPC", True, "https://cloud.ibm.com/docs/vpc?topic=vpc-profiles", OFFICIAL_FEATURE),
        "container_support": structured("IBM Cloud Code Engine", True, "https://www.ibm.com/products/code-engine", OFFICIAL_FEATURE),
        "kubernetes_support": structured("IBM Cloud Kubernetes Service", True, "https://www.ibm.com/products/kubernetes-service", OFFICIAL_FEATURE),
        "auto_scaling": structured("VPC instance-group autoscaling", True, "https://cloud.ibm.com/docs/vpc?topic=vpc-creating-auto-scale-instance-group", OFFICIAL_FEATURE),
        "load_balancer": structured("IBM Cloud Load Balancer for VPC", True, "https://cloud.ibm.com/docs/vpc?topic=vpc-nlb-vs-elb", OFFICIAL_FEATURE),
        "monitoring": structured("IBM Cloud Monitoring", True, "https://cloud.ibm.com/docs/monitoring", OFFICIAL_FEATURE),
        "backup": structured("IBM Cloud Backup for VPC", True, "https://cloud.ibm.com/docs/vpc?topic=vpc-backup-service-about", OFFICIAL_FEATURE),
        "disaster_recovery": structured("IBM Cloud disaster-recovery architecture guidance", True, "https://www.ibm.com/architectures/hybrid/dr", OFFICIAL_FEATURE),
        "support_tier": structured("Premium support plan", "Premium", "https://www.ibm.com/cloud/support", OFFICIAL_SUPPORT),
        "support_24x7": structured("24x7 support is available in qualifying IBM Cloud support plans", True, "https://www.ibm.com/cloud/support", OFFICIAL_SUPPORT),
        "security_certifications": structured("ISO/IEC 27001; SOC 2", ["ISO27001", "SOC2"], "https://www.ibm.com/cloud/compliance", OFFICIAL_COMPLIANCE),
        "compliance_certifications": structured("HIPAA; PCI DSS; GDPR", ["HIPAA", "PCI DSS", "GDPR"], "https://www.ibm.com/cloud/compliance", OFFICIAL_COMPLIANCE),
        "free_tier": structured("IBM Cloud free account and Lite plans", True, "https://www.ibm.com/cloud/free", OFFICIAL_DOCUMENTATION),
        "hybrid_cloud": structured("IBM Cloud hybrid and multicloud platform capabilities", True, "https://cloud.ibm.com/docs/overview?topic=overview-whatis-platform", OFFICIAL_FEATURE),
        "documentation_url": structured(DOCS, DOCS, DOCS, OFFICIAL_DOCUMENTATION),
        "source_url": structured(DOCS, DOCS, DOCS, OFFICIAL_DOCUMENTATION),
        "source_type": structured("Official IBM documentation, pricing, SLA, region, support, feature, and compliance pages", "official_multi_source", DOCS, OFFICIAL_DOCUMENTATION),
    }
