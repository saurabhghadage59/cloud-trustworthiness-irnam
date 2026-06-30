"""Deterministic typed dataset, provenance, statistics, coverage, and report exports."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from dataset_builder.config.schema import ARRAY_FIELDS, ATTRIBUTE_FIELDS, BOOLEAN_FIELDS, NUMERIC_FIELDS, PROVENANCE_FIELDS, SCHEMA_VERSION


def _json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _csv_value(value):
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return value


class DatasetExporter:
    def export(self, providers, issues, output_dir: Path, collection_date: str):
        output_dir.mkdir(parents=True, exist_ok=True)
        rows = [provider.as_dict() for provider in providers]
        json_payload = _json_bytes(rows)
        (output_dir / "cloud_dataset.json").write_bytes(json_payload)

        with (output_dir / "cloud_dataset.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=ATTRIBUTE_FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows({key: _csv_value(value) for key, value in row.items()} for row in rows)

        source_rows = [source.as_dict() for provider in providers for source in provider.sources]
        with (output_dir / "sources.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=PROVENANCE_FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows({key: _csv_value(value) for key, value in row.items()} for row in source_rows)

        coverage = self._coverage(providers, rows)
        statistics = self._statistics(rows, source_rows)
        (output_dir / "coverage_report.json").write_bytes(_json_bytes(coverage))
        (output_dir / "dataset_statistics.json").write_bytes(_json_bytes(statistics))

        metadata = {
            "schema_version": SCHEMA_VERSION,
            "collection_date": collection_date,
            "provider_count": len(providers),
            "attribute_count": len(ATTRIBUTE_FIELDS),
            "source_record_count": len(source_rows),
            "missing_value_count": coverage["missing_value_count"],
            "coverage_percent": coverage["coverage_percent"],
            "validation_issue_counts": dict(sorted(Counter(i.severity for i in issues).items())),
            "cloud_dataset_json_sha256": hashlib.sha256(json_payload).hexdigest(),
        }
        (output_dir / "dataset_metadata.json").write_bytes(_json_bytes(metadata))
        (output_dir / "dataset_report.md").write_text(
            self._report(rows, source_rows, issues, collection_date, coverage), encoding="utf-8", newline="\n"
        )
        return metadata

    @staticmethod
    def _coverage(providers, rows):
        total = len(rows) * len(ATTRIBUTE_FIELDS)
        by_attribute = {}
        for attribute in ATTRIBUTE_FIELDS:
            missing_providers = [row["provider_name"] for row in rows if row[attribute] is None]
            reasons = {}
            for provider in providers:
                if getattr(provider, attribute) is None:
                    record = next(source for source in provider.sources if source.attribute == attribute)
                    reasons[provider.provider_name] = record.reason
            present = len(rows) - len(missing_providers)
            by_attribute[attribute] = {
                "present_count": present,
                "missing_count": len(missing_providers),
                "coverage_percent": round(100 * present / len(rows), 2) if rows else 0.0,
                "missing_providers": missing_providers,
                "missing_reasons": reasons,
            }
        missing = sum(item["missing_count"] for item in by_attribute.values())
        return {
            "total_value_count": total,
            "collected_value_count": total - missing,
            "missing_value_count": missing,
            "coverage_percent": round(100 * (total - missing) / total, 2) if total else 0.0,
            "by_attribute": by_attribute,
        }

    @staticmethod
    def _statistics(rows, source_rows):
        numeric = {}
        for attribute in NUMERIC_FIELDS:
            values = [row[attribute] for row in rows if row[attribute] is not None]
            numeric[attribute] = {
                "count": len(values),
                "minimum": min(values) if values else None,
                "maximum": max(values) if values else None,
                "mean": round(sum(values) / len(values), 6) if values else None,
            }
        boolean = {
            attribute: {
                "true": sum(row[attribute] is True for row in rows),
                "false": sum(row[attribute] is False for row in rows),
                "null": sum(row[attribute] is None for row in rows),
            }
            for attribute in sorted(BOOLEAN_FIELDS)
        }
        certifications = {
            attribute: dict(sorted(Counter(item for row in rows if row[attribute] for item in row[attribute]).items()))
            for attribute in sorted(ARRAY_FIELDS)
        }
        return {
            "numeric_fields": numeric,
            "boolean_fields": boolean,
            "support_tier_counts": dict(sorted(Counter(row["support_tier"] for row in rows if row["support_tier"]).items())),
            "certification_counts": certifications,
            "source_type_counts": dict(sorted(Counter(row["source_type"] for row in source_rows).items())),
            "confidence_counts": dict(sorted(Counter(row["confidence"] for row in source_rows).items())),
        }

    @staticmethod
    def _report(rows, source_rows, issues, collection_date, coverage):
        missing_items = [(name, item) for name, item in coverage["by_attribute"].items() if item["missing_count"]]
        source_counts = Counter(row["source_type"] for row in source_rows)
        lines = [
            "# IRNAM Structured QoS Dataset Report", "", f"Collection date: {collection_date}", "",
            "## Data quality summary", "", f"- Providers: {len(rows)}", f"- Typed attributes per provider: {len(ATTRIBUTE_FIELDS)}",
            f"- Collected values: {coverage['collected_value_count']}/{coverage['total_value_count']}",
            f"- Coverage: {coverage['coverage_percent']:.2f}%", f"- Validation errors: {sum(i.severity == 'error' for i in issues)}",
            f"- Validation warnings: {sum(i.severity == 'warning' for i in issues)}", "",
            "## Collected metrics", "", "| Attribute | Coverage | Missing |", "|---|---:|---:|",
        ]
        lines.extend(f"| {name} | {item['coverage_percent']:.2f}% | {item['missing_count']} |" for name, item in coverage["by_attribute"].items())
        lines += ["", "## Missing attributes and unsupported metrics", ""]
        if missing_items:
            for attribute, item in missing_items:
                lines.append(f"### {attribute}")
                lines.append("")
                for provider, reason in item["missing_reasons"].items():
                    lines.append(f"- {provider}: {reason}")
                lines.append("")
        else:
            lines.append("None.")
        lines += ["", "## Source summary", "", "| Source type | Attribute records |", "|---|---:|"]
        lines.extend(f"| {source_type} | {count} |" for source_type, count in sorted(source_counts.items()))
        lines += ["", "## Validation findings", ""]
        lines += [f"- [{i.severity}] {i.provider}.{i.attribute}: {i.message}" for i in issues] or ["No validation findings."]
        lines += ["", "Values are typed but unnormalised. No ranking, weighting, recommendation, negotiation, or SLA evaluation is performed.", ""]
        return "\n".join(lines)
