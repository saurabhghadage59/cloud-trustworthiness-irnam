"""Terminal entry point for reproducible algorithm evaluation."""
from __future__ import annotations
import argparse
from pathlib import Path
from src.recommendation.recommendation_engine import RecommendationEngine
from .benchmark import run_benchmark

def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark IRNAM recommendation algorithms")
    parser.add_argument("--dataset", type=Path, default=Path("src/dataset/cloud_dataset.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--limit", type=int, default=0, help="Optional row limit for a quick run")
    args = parser.parse_args()
    providers = RecommendationEngine(dataset_path=args.dataset).load_dataset()
    if args.limit: providers = providers[:args.limit]
    weights = {"TrustScore": 0.5, "CostPerHourUSD": 0.5}
    rows = run_benchmark(providers, weights, {"CostPerHourUSD": "lower"}, args.output_dir)
    print(f"Benchmarked {len(rows)} algorithms on {len(providers)} rows; artifacts: {args.output_dir}")

if __name__ == "__main__": main()
