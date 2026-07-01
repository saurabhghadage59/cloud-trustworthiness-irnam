# IRNAM Structured Cloud QoS Dataset Builder

This repository implements the dataset-building phase of *A User-Priorities-Based Strategy for Three-Phase Intelligent Recommendation and Negotiating Agents for Cloud Services (IRNAM)*. It produces a typed, machine-readable QoS snapshot for AWS, Microsoft Azure, Google Cloud, Oracle Cloud, and IBM Cloud using reviewed public official sources.

The builder does **not** normalize, score, rank, recommend, negotiate, calculate weights, or evaluate SLA compliance. Existing prototype modules outside `dataset_builder/` are not used by this pipeline.

## Architecture

The existing collector → model → validator → exporter architecture is retained:

1. Provider collectors declare an original source value, typed parsed value, source, confidence, and optional missing-value reason.
2. The common `Provider` model exposes numeric, boolean, enum, array, URL, and date fields directly to downstream code.
3. Validators enforce numeric ranges, integer types, boolean types, support-tier enums, certification arrays, unique providers, provenance completeness, `NULL` reasons, and URL structure.
4. Exporters produce deterministic JSON/CSV datasets, provenance, coverage, statistics, metadata, and a Markdown quality report.

Collectors never export files. Each collector returns the same `Provider` model and exactly one `SourceRecord` per canonical attribute.

## Metric definitions

The dataset uses these comparison rules so values are not silently mixed across incompatible scopes:

- `availability_sla_percent`: published multi-zone compute/VM monthly uptime commitment. This is a service/configuration SLA, not a provider-wide observed availability metric.
- `minimum_vm_price_usd_hour`: exact published minimum hourly VM price only when a reproducible valid configuration and scope can be established. Dynamic or ambiguous values remain `NULL`.
- `storage_price_usd_gb_month`: exact USD/GB-month only when storage class and location are unambiguous. Otherwise `NULL`.
- `region_count` and `availability_zone_count`: exact official global counts only. Marketing lower bounds such as `70+` remain `NULL`.
- Feature and support fields: `true`, `false`, or `null`; `true` means the provider officially offers the capability, not that every service or region supports it.
- `support_tier`: highest named general support tier found in the reviewed official support-plan page; it is a controlled enum, not a quality score.
- Certifications: JSON arrays of canonical labels. They indicate documented provider programs or offerings, not automatic compliance of a customer's workload.

No missing numeric value is estimated. The reason and evidence URL are retained in `sources.csv` and `coverage_report.json`.

## Folder structure

```text
dataset_builder/
  collectors/     provider-specific official-source snapshots
  parsers/        compatibility raw-value parsing helpers
  validators/     type, range, provenance, enum, and URL validation
  exporters/      deterministic dataset/report writers
  models/         typed Provider and SourceRecord models
  config/         canonical schema and controlled vocabularies
  utils/          shared utility namespace
  logs/           runtime log location
data/             optional reviewed input snapshots
outputs/          generated research artifacts
tests/            collector, validator, and exporter tests
```

## Rebuild and test

Python 3.10 or newer is required; the builder uses only the standard library.

```powershell
python -m unittest discover -s tests -p "test_dataset_builder.py" -v
python -m unittest discover -s tests -v
python -m dataset_builder --collection-date 2026-06-30 --output-dir outputs
```

A fixed ISO collection date makes the snapshot reproducible. Add `--check-urls` for optional live reachability checks; these are excluded from the deterministic default because provider sites can reject `HEAD` requests or be temporarily unavailable.

Generated artifacts:

- `cloud_dataset.csv` and `cloud_dataset.json`: typed provider rows.
- `sources.csv`: original value, parsed value, evidence, confidence, and missing reason for every provider/attribute pair.
- `dataset_statistics.json`: numeric summaries, boolean counts, enums, certifications, source types, and confidence counts.
- `coverage_report.json`: total and per-attribute coverage with provider-level missing reasons.
- `dataset_metadata.json`: schema version, counts, validation summary, and dataset SHA-256.
- `dataset_report.md`: human-readable coverage, unsupported metrics, sources, and validation findings.

## Backward compatibility

Phase-1 read-only names (`availability_sla`, `compute_pricing`, `storage_pricing`, `regions`, `availability_zones`, `support_plans`, and `last_updated`) remain available as `Provider` properties. They return the corresponding typed Phase-2 value. The legacy three-argument collector `value()` helper and six-argument `SourceRecord` construction order are also retained.

## Add or update a provider

1. Add or edit `dataset_builder/collectors/<provider>.py` using `structured()` for defensible values and `unavailable()` for unresolved values.
2. Preserve source wording as `original_value`; put only a typed value in `parsed_value`.
3. Never convert bounds, dynamic calculator output, or an unspecified configuration into an exact metric.
4. Register new collectors in `dataset_builder/collectors/__init__.py` (the current research phase remains limited to five providers).
5. Extend tests, rebuild, and inspect `sources.csv`, `coverage_report.json`, and `dataset_report.md`.

Pricing, locations, support plans, certifications, and products change. Every published dataset must be treated as a dated research snapshot and re-reviewed against official sources.

## Recommendation phase (Algorithms 1 and 2)

The completed `src/recommendation/` package consumes the structured JSON dataset without parsing natural-language provider descriptions.

Algorithm 1 assigns a positive score to each priority (`very_low=1` through `very_high=5`) and normalizes it:

```text
user_weight[j] = priority_score[j] / sum(priority_scores)
```

Algorithm 2 converts each comparable provider column to an evaluation score in `[0, 1]`. Benefit attributes use `(x-min)/(max-min)` and cost attributes use `(max-x)/(max-min)`. Equal non-null columns score `1`; unavailable values score `0` and are never estimated. Booleans map to `1/0`, arrays use cardinality, and enums use explicit controlled scales. The overall score is:

```text
overall_score[i] = sum(user_weight[j] * evaluation_score[i,j])
```

Providers are sorted by overall score and receive dense ranks, so tied providers share a rank. Filtering occurs before ranking and supports mandatory values, min/max/equality/containment constraints, requested service flags, and unavailable-provider exclusions.

```python
from src.recommendation import RecommendationEngine, UserRequirementProcessor

requirement = UserRequirementProcessor().process({
    "availability": "very_high",
    "reliability": "high",
    "security": "high",
    "cost": "medium",
    "response_time": "low",
    "scalability": "high",
    "support": "medium",
    "storage": "low",
    "network": "medium",
})

result = RecommendationEngine().recommend(
    requirement,
    requested_services=["kubernetes_support"],
    unavailable_providers=[],
)

negotiation_input = result  # RecommendationResult implements Mapping[str, Any].
```

`RecommendationResult` contains the recommended provider, overall score, full ranking, attribute scores, normalized user weights, dataset-derived provider weights, raw provider attributes, filtering reasons, and a deterministic explanation. It can be passed directly to `NegotiationEngine`; negotiation is never started automatically.

## End-to-end demonstration

The root `main.py` is the integration layer for the complete research workflow:

```text
Dataset → User Requirements → Recommendation → Negotiation → SLA → Evaluation
```

Run the reproducible built-in demonstration:

```powershell
python main.py
```

Use `python main.py --help` to supply a dataset path, user-priority JSON, user-SLA JSON, provider-SLA JSON, negotiation strategy, round limit, or interactive input. The command logs each phase and prints one JSON object containing the dataset summary, requirements, recommendation, negotiation trace, generated SLA, and evaluation metrics.

## Negotiation, aggregation, and SLA phase

The `negotiation/`, `sla/`, and `evaluation/` packages implement the IRNAM phases after Recommendation. The implementation consumes Recommendation output as a plain dictionary and does not duplicate ranking or dataset logic.

Typical flow:

```python
from negotiation import NegotiationConfig, NegotiationEngine
from sla import SLAManager
from evaluation import calculate_negotiation_metrics

recommendation = {
    "recommended_provider": "CSP1",
    "overall_score": 0.21,
    "user_priorities": {"price": 0.46, "security": 0.26},
}

user_sla = {
    "price": {"value": 100, "min": 95, "max": 120},
    "security": {"value": 90, "min": 85, "max": 95},
}

provider_sla = {
    "price": {"value": 125, "min": 105, "max": 130},
    "security": {"value": 75, "min": 70, "max": 80},
    "weights": {"price": 0.46, "security": 0.04},
}

engine = NegotiationEngine(NegotiationConfig(strategy="win_win", max_rounds=10))
result = engine.negotiate(recommendation, user_sla, provider_sla)

contract = SLAManager().create_contract(result)
metrics = calculate_negotiation_metrics([result])
```

Algorithm 3 is represented by `NegotiationEngine.negotiate()`: it extracts negotiable attributes, normalizes values, computes party aggregated evaluation scores, calculates the degree of difference, applies configurable concession strategies (`competitive`, `win_win`, `collaborative`), generates counter offers, and stops on agreement or deadline.

Algorithm 4 is represented by `AggregationEngine.aggregate()`: it accepts a final offer only when user satisfaction is greater than or equal to provider satisfaction. `SLAManager.create_contract()` then serializes the accepted result into a JSON-ready SLA contract containing provider, negotiated attributes, strategy, timestamp, rounds, satisfaction, and agreement status.
