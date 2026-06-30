"""Typed AWS QoS snapshot from official public sources."""

from dataset_builder.collectors.base import OfficialSourceCollector, structured, unavailable
from dataset_builder.config.schema import OFFICIAL_COMPLIANCE, OFFICIAL_DOCUMENTATION, OFFICIAL_FEATURE, OFFICIAL_PRICING, OFFICIAL_REGION, OFFICIAL_SLA, OFFICIAL_SUPPORT

DOCS = "https://docs.aws.amazon.com/"


class AWSCollector(OfficialSourceCollector):
    provider_name = "Amazon Web Services (AWS)"
    attributes = {
        "availability_sla_percent": structured("Monthly Uptime Percentage of at least 99.99% for EC2 deployed across two or more AZs", 99.99, "https://aws.amazon.com/compute/sla/", OFFICIAL_SLA),
        "minimum_vm_price_usd_hour": unavailable("The official EC2 price table is dynamic and region, architecture, OS, and purchase-option dependent; no reproducible global minimum is published.", "https://aws.amazon.com/ec2/pricing/on-demand/", OFFICIAL_PRICING),
        "storage_price_usd_gb_month": unavailable("Storage class and reference region were not specified; AWS publishes multiple usage-dependent S3 rates rather than one storage price.", "https://aws.amazon.com/s3/pricing/", OFFICIAL_PRICING),
        "region_count": structured("39 launched Regions", 39, "https://aws.amazon.com/about-aws/global-infrastructure/", OFFICIAL_REGION),
        "availability_zone_count": structured("123 Availability Zones", 123, "https://aws.amazon.com/about-aws/global-infrastructure/", OFFICIAL_REGION),
        "gpu_support": structured("GPU-based accelerated computing instances", True, "https://aws.amazon.com/ec2/instance-types/accelerated-computing/", OFFICIAL_FEATURE),
        "container_support": structured("Amazon ECS and AWS Fargate", True, "https://aws.amazon.com/containers/services/", OFFICIAL_FEATURE),
        "kubernetes_support": structured("Amazon Elastic Kubernetes Service", True, "https://aws.amazon.com/eks/", OFFICIAL_FEATURE),
        "auto_scaling": structured("AWS Auto Scaling", True, "https://aws.amazon.com/autoscaling/", OFFICIAL_FEATURE),
        "load_balancer": structured("Elastic Load Balancing", True, "https://aws.amazon.com/elasticloadbalancing/", OFFICIAL_FEATURE),
        "monitoring": structured("Amazon CloudWatch", True, "https://aws.amazon.com/cloudwatch/", OFFICIAL_FEATURE),
        "backup": structured("AWS Backup", True, "https://aws.amazon.com/backup/", OFFICIAL_FEATURE),
        "disaster_recovery": structured("AWS Elastic Disaster Recovery", True, "https://aws.amazon.com/disaster-recovery/", OFFICIAL_FEATURE),
        "support_tier": structured("Enterprise Support", "Enterprise", "https://aws.amazon.com/premiumsupport/plans/", OFFICIAL_SUPPORT),
        "support_24x7": structured("24x7 access is included in qualifying paid AWS Support plans", True, "https://aws.amazon.com/premiumsupport/plans/", OFFICIAL_SUPPORT),
        "security_certifications": structured("ISO/IEC 27001; SOC 2", ["ISO27001", "SOC2"], "https://aws.amazon.com/compliance/programs/", OFFICIAL_COMPLIANCE),
        "compliance_certifications": structured("HIPAA; PCI DSS; GDPR", ["HIPAA", "PCI DSS", "GDPR"], "https://aws.amazon.com/compliance/programs/", OFFICIAL_COMPLIANCE),
        "free_tier": structured("AWS Free Tier", True, "https://aws.amazon.com/free/", OFFICIAL_DOCUMENTATION),
        "hybrid_cloud": structured("AWS Outposts extends AWS infrastructure and services on premises", True, "https://aws.amazon.com/outposts/", OFFICIAL_FEATURE),
        "documentation_url": structured(DOCS, DOCS, DOCS, OFFICIAL_DOCUMENTATION),
        "source_url": structured(DOCS, DOCS, DOCS, OFFICIAL_DOCUMENTATION),
        "source_type": structured("Official AWS documentation, pricing, SLA, region, support, feature, and compliance pages", "official_multi_source", DOCS, OFFICIAL_DOCUMENTATION),
    }
