"""Command-line entry point for rebuilding the Phase-1 dataset."""

import argparse
from pathlib import Path

from dataset_builder.build import build_dataset


def main():
    parser = argparse.ArgumentParser(description="Build the IRNAM Phase-1 cloud provider dataset")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--collection-date", help="ISO date for reproducible snapshots (YYYY-MM-DD)")
    parser.add_argument("--check-urls", action="store_true", help="Perform optional network URL checks")
    args = parser.parse_args()
    providers, issues, metadata = build_dataset(args.output_dir, args.collection_date, args.check_urls)
    print(f"Exported {len(providers)} providers to {args.output_dir} ({len(issues)} findings).")
    print(f"Dataset SHA-256: {metadata['cloud_dataset_json_sha256']}")


if __name__ == "__main__":
    main()
