import csv
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from dataset_builder.build import build_dataset
from dataset_builder.collectors import COLLECTORS
from dataset_builder.config.schema import ATTRIBUTE_FIELDS, BOOLEAN_FIELDS
from dataset_builder.models.provider import Provider, SourceRecord
from dataset_builder.validators.dataset import DatasetValidator


class CollectorTests(unittest.TestCase):
    def test_all_collectors_return_typed_provider_with_complete_provenance(self):
        for collector in COLLECTORS:
            provider = collector("2026-06-30").collect()
            self.assertIsInstance(provider, Provider)
            self.assertEqual(len(provider.sources), len(ATTRIBUTE_FIELDS))
            self.assertEqual(provider.collection_date, "2026-06-30")
            self.assertEqual(provider.last_updated, "2026-06-30")  # Phase-1 alias
            self.assertIsInstance(provider.availability_sla_percent, float)
            for attribute in BOOLEAN_FIELDS:
                self.assertIn(getattr(provider, attribute), (True, False, None))
            for source in provider.sources:
                if source.parsed_value is None:
                    self.assertTrue(source.reason)
                    self.assertEqual(source.confidence, "unavailable")

    def test_certifications_are_arrays(self):
        for collector in COLLECTORS:
            provider = collector("2026-06-30").collect()
            self.assertIsInstance(provider.security_certifications, list)
            self.assertIsInstance(provider.compliance_certifications, list)


class ValidatorTests(unittest.TestCase):
    def test_duplicate_provider_is_error(self):
        provider = COLLECTORS[0]("2026-06-30").collect()
        issues = DatasetValidator().validate([provider, provider])
        self.assertIn("duplicate_provider", {issue.code for issue in issues})

    def test_malformed_url_is_error(self):
        provider = COLLECTORS[0]("2026-06-30").collect()
        original = provider.sources[0]
        provider.sources[0] = SourceRecord(original.provider, original.attribute, original.collected_value, "not-a-url", original.source_type, original.collection_date)
        issues = DatasetValidator().validate_urls(provider)
        self.assertIn("broken_url", {issue.code for issue in issues})

    def test_numeric_range_is_enforced(self):
        provider = COLLECTORS[0]("2026-06-30").collect()
        provider.availability_sla_percent = 101.0
        issues = DatasetValidator().validate_provider(provider)
        self.assertIn("invalid_numeric_range", {issue.code for issue in issues})

    def test_support_enum_is_enforced(self):
        provider = COLLECTORS[0]("2026-06-30").collect()
        provider.support_tier = "Ultra"
        issues = DatasetValidator().validate_provider(provider)
        self.assertIn("invalid_enum", {issue.code for issue in issues})

    def test_provider_can_represent_schema_adapted_qos_row(self):
        provider = Provider.from_qos_row({
            "Service Name": "CatalogService", "Availability": 99.5, "Reliability": 91,
            "Throughput": 30, "Response Time": 40, "Latency": 15,
            "Documentation": 88, "Best Practices": 93,
        })
        self.assertEqual("CatalogService", provider.provider_name)
        self.assertEqual(40, provider.as_qos_dict()["response_time"])


class ExporterTests(unittest.TestCase):
    def test_build_exports_all_required_artifacts(self):
        with TemporaryDirectory() as directory:
            output = Path(directory)
            providers, issues, metadata = build_dataset(output, "2026-06-30")
            expected = {
                "cloud_dataset.csv", "cloud_dataset.json", "dataset_statistics.json",
                "dataset_metadata.json", "sources.csv", "coverage_report.json", "dataset_report.md",
            }
            self.assertEqual(expected, {path.name for path in output.iterdir()})
            rows = json.loads((output / "cloud_dataset.json").read_text(encoding="utf-8"))
            self.assertEqual(5, len(rows))
            self.assertIsInstance(rows[0]["gpu_support"], bool)
            self.assertIsInstance(rows[0]["security_certifications"], list)
            with (output / "sources.csv").open(encoding="utf-8") as handle:
                source_rows = list(csv.DictReader(handle))
            self.assertEqual(5 * len(ATTRIBUTE_FIELDS), len(source_rows))
            self.assertIn("original_value", source_rows[0])
            self.assertIn("parsed_value", source_rows[0])
            self.assertIn("confidence", source_rows[0])
            self.assertEqual(5, metadata["provider_count"])
            self.assertFalse([issue for issue in issues if issue.severity == "error"])

    def test_coverage_records_null_reasons(self):
        with TemporaryDirectory() as directory:
            output = Path(directory)
            build_dataset(output, "2026-06-30")
            coverage = json.loads((output / "coverage_report.json").read_text(encoding="utf-8"))
            pricing = coverage["by_attribute"]["minimum_vm_price_usd_hour"]
            self.assertEqual(5, pricing["missing_count"])
            self.assertEqual(5, len(pricing["missing_reasons"]))


if __name__ == "__main__":
    unittest.main()
