"""Terminal training entry point for the portable ML recommendation model."""
from __future__ import annotations
import argparse
from pathlib import Path
from ..recommendation_engine import RecommendationEngine
from .models import MLRecommendationModel

def main() -> None:
    parser=argparse.ArgumentParser(description="Train an IRNAM trust-score model")
    parser.add_argument("--dataset",type=Path,default=Path("src/dataset/cloud_dataset.csv"))
    parser.add_argument("--model-path",type=Path,default=Path("outputs/trained_models/trust_score_model.pkl"))
    parser.add_argument("--target",default="TrustScore")
    args=parser.parse_args()
    rows=RecommendationEngine(dataset_path=args.dataset).load_dataset()
    model=MLRecommendationModel(target=args.target).fit(rows)
    model.save(args.model_path)
    print({"model":model.estimator_name,"rows":len(rows),"metrics":model.validate(rows),"model_path":str(args.model_path)})

if __name__ == "__main__": main()
