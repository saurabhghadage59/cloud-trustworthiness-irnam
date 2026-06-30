# IRNAM Structured QoS Dataset Report

Collection date: 2026-06-30

## Data quality summary

- Providers: 5
- Typed attributes per provider: 24
- Collected values: 107/120
- Coverage: 89.17%
- Validation errors: 0
- Validation warnings: 13

## Collected metrics

| Attribute | Coverage | Missing |
|---|---:|---:|
| provider_name | 100.00% | 0 |
| availability_sla_percent | 100.00% | 0 |
| minimum_vm_price_usd_hour | 0.00% | 5 |
| storage_price_usd_gb_month | 0.00% | 5 |
| region_count | 80.00% | 1 |
| availability_zone_count | 60.00% | 2 |
| gpu_support | 100.00% | 0 |
| container_support | 100.00% | 0 |
| kubernetes_support | 100.00% | 0 |
| auto_scaling | 100.00% | 0 |
| load_balancer | 100.00% | 0 |
| monitoring | 100.00% | 0 |
| backup | 100.00% | 0 |
| disaster_recovery | 100.00% | 0 |
| support_tier | 100.00% | 0 |
| support_24x7 | 100.00% | 0 |
| security_certifications | 100.00% | 0 |
| compliance_certifications | 100.00% | 0 |
| free_tier | 100.00% | 0 |
| hybrid_cloud | 100.00% | 0 |
| documentation_url | 100.00% | 0 |
| collection_date | 100.00% | 0 |
| source_url | 100.00% | 0 |
| source_type | 100.00% | 0 |

## Missing attributes and unsupported metrics

### minimum_vm_price_usd_hour

- Amazon Web Services (AWS): The official EC2 price table is dynamic and region, architecture, OS, and purchase-option dependent; no reproducible global minimum is published.
- Microsoft Azure: Azure VM prices are dynamically calculated by region, currency, operating system, agreement, and VM size; no exact global minimum is published.
- Google Cloud Platform (GCP): Compute Engine pricing is SKU, configuration, operating-system, discount, and location dependent; the product page's rounded starting price is not an exact reproducible minimum.
- Oracle Cloud Infrastructure (OCI): OCI flexible VM price requires both OCPU and memory quantities, and the brief does not define a minimum valid VM configuration.
- IBM Cloud: IBM VPC virtual-server pricing is profile, operating-system, location, and configuration dependent and no exact global minimum is published.

### storage_price_usd_gb_month

- Amazon Web Services (AWS): Storage class and reference region were not specified; AWS publishes multiple usage-dependent S3 rates rather than one storage price.
- Microsoft Azure: Storage service, redundancy, access tier, and reference region were not specified; Azure publishes multiple rates.
- Google Cloud Platform (GCP): Cloud Storage class and reference location were not specified; official prices vary by class, location, operation, and retrieval.
- Oracle Cloud Infrastructure (OCI): OCI publishes separate object, archive, block, file, performance, and request rates; no storage class was specified.
- IBM Cloud: IBM Cloud storage pricing varies by service, class, location, capacity, and usage; no storage class was specified.

### region_count

- Microsoft Azure: Microsoft publishes '70+ Azure regions', which is not an exact machine-readable count.

### availability_zone_count

- Microsoft Azure: Microsoft publishes zone support by region but no authoritative global availability-zone total.
- Oracle Cloud Infrastructure (OCI): OCI publishes Availability Domains per region but no authoritative global Availability Domain total.


## Source summary

| Source type | Attribute records |
|---|---:|
| collection_metadata | 10 |
| official_compliance_documentation | 10 |
| official_documentation | 20 |
| official_feature_documentation | 45 |
| official_pricing | 10 |
| official_region_documentation | 10 |
| official_sla_documentation | 5 |
| official_support_documentation | 10 |

## Validation findings

- [warning] Amazon Web Services (AWS).minimum_vm_price_usd_hour: minimum_vm_price_usd_hour is NULL
- [warning] Amazon Web Services (AWS).storage_price_usd_gb_month: storage_price_usd_gb_month is NULL
- [warning] Microsoft Azure.minimum_vm_price_usd_hour: minimum_vm_price_usd_hour is NULL
- [warning] Microsoft Azure.storage_price_usd_gb_month: storage_price_usd_gb_month is NULL
- [warning] Microsoft Azure.region_count: region_count is NULL
- [warning] Microsoft Azure.availability_zone_count: availability_zone_count is NULL
- [warning] Google Cloud Platform (GCP).minimum_vm_price_usd_hour: minimum_vm_price_usd_hour is NULL
- [warning] Google Cloud Platform (GCP).storage_price_usd_gb_month: storage_price_usd_gb_month is NULL
- [warning] Oracle Cloud Infrastructure (OCI).minimum_vm_price_usd_hour: minimum_vm_price_usd_hour is NULL
- [warning] Oracle Cloud Infrastructure (OCI).storage_price_usd_gb_month: storage_price_usd_gb_month is NULL
- [warning] Oracle Cloud Infrastructure (OCI).availability_zone_count: availability_zone_count is NULL
- [warning] IBM Cloud.minimum_vm_price_usd_hour: minimum_vm_price_usd_hour is NULL
- [warning] IBM Cloud.storage_price_usd_gb_month: storage_price_usd_gb_month is NULL

Values are typed but unnormalised. No ranking, weighting, recommendation, negotiation, or SLA evaluation is performed.
