"""Phase-1 dataset build orchestration."""

from datetime import date
from pathlib import Path

from dataset_builder.collectors import COLLECTORS
from dataset_builder.exporters import DatasetExporter
from dataset_builder.validators.dataset import DatasetValidator
from dataset_builder.benchmark import build_benchmark_dataset


def build_dataset(output_dir: Path, collection_date: str | None = None, check_urls: bool = False):
    collection_date = collection_date or date.today().isoformat()
    providers = [collector(collection_date=collection_date).collect() for collector in COLLECTORS]
    validator = DatasetValidator()
    issues = validator.validate(providers)
    if check_urls:
        issues.extend(issue for provider in providers for issue in validator.validate_urls(provider, True))
    errors = [issue for issue in issues if issue.severity == "error"]
    if errors:
        raise ValueError("Dataset validation failed: " + "; ".join(issue.message for issue in errors))
    metadata = DatasetExporter().export(providers, issues, Path(output_dir), collection_date)
    return providers, issues, metadata
