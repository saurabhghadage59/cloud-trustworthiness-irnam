"""Executable end-to-end integration workflow for the IRNAM research system.

This module coordinates existing components only. Business logic remains in the
Dataset Builder, Recommendation, Negotiation, SLA, and Evaluation packages.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from evaluation import NegotiationEvaluator
from negotiation import NegotiationConfig, NegotiationEngine
from sla import SLAManager
from src.recommendation import RecommendationEngine, UserRequirementProcessor
from src.recommendation.models import DEFAULT_ATTRIBUTE_ORDER, Requirement

logger = logging.getLogger("irnam")


DEFAULT_PRIORITIES = {
    "availability": "very_high",
    "reliability": "high",
    "security": "high",
    "cost": "medium",
    "response_time": "low",
    "scalability": "high",
    "support": "medium",
    "storage": "low",
    "network": "medium",
}

# Integration aliases only: no scoring or normalization is performed here.
NEGOTIATION_ATTRIBUTE_MAP = {
    "availability_sla_percent": "availability",
    "minimum_vm_price_usd_hour": "price",
    "storage_price_usd_gb_month": "storage",
}


@dataclass(frozen=True)
class WorkflowResult:
    """Serializable result of one complete IRNAM demonstration run."""

    dataset_path: str
    provider_count: int
    requirement: Requirement
    recommendation: Any
    negotiation: Any
    sla_contract: Any
    evaluation: Any

    def to_dict(self) -> Dict[str, Any]:
        """Return the complete workflow output as JSON-ready data."""

        return {
            "dataset": {
                "path": self.dataset_path,
                "provider_count": self.provider_count,
            },
            "requirements": self.requirement.to_dict(),
            "recommendation": self.recommendation.to_dict(),
            "negotiation": self.negotiation.to_dict(),
            "sla": self.sla_contract.to_dict(),
            "evaluation": self.evaluation.to_dict(),
        }


def load_json_mapping(path: Path) -> Dict[str, Any]:
    """Load a JSON object from ``path`` with a clear integration error."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Input file is not valid JSON: {path}: {exc}") from exc
    if not isinstance(value, Mapping):
        raise ValueError(f"Input file must contain a JSON object: {path}")
    return dict(value)


def collect_user_requirements(
    processor: UserRequirementProcessor,
    requirements_path: Optional[Path] = None,
    interactive: bool = False,
) -> Requirement:
    """Collect priorities from JSON, interactive prompts, or demo defaults."""

    if requirements_path:
        priorities = load_json_mapping(requirements_path)
        logger.info("User requirements loaded from %s", requirements_path)
    elif interactive:
        priorities = {}
        print("Enter priority for each attribute: very_low, low, medium, high, very_high")
        for attribute in DEFAULT_ATTRIBUTE_ORDER:
            priorities[attribute] = input(f"{attribute}: ").strip()
        logger.info("User requirements collected interactively")
    else:
        priorities = dict(DEFAULT_PRIORITIES)
        logger.info("Using reproducible demonstration requirements")
    return processor.process(priorities)


def collect_user_sla(user_sla_path: Optional[Path] = None, interactive: bool = False) -> Dict[str, Any]:
    """Collect negotiable user targets without embedding provider assumptions."""

    if user_sla_path:
        user_sla = load_json_mapping(user_sla_path)
        logger.info("User SLA targets loaded from %s", user_sla_path)
        return user_sla
    if interactive:
        availability = float(input("Minimum availability target (percent, e.g. 99.9): ").strip())
        logger.info("User SLA target collected interactively")
        return {"availability": {"value": availability, "min": 0.0, "max": 100.0}}
    logger.info("Using reproducible demonstration SLA target")
    return {"availability": {"value": 99.9, "min": 0.0, "max": 100.0}}


def provider_sla_for_recommendation(
    recommendation: Any,
    provider_sla_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Select supplied provider SLA data or adapt compatible dataset fields."""

    provider_name = recommendation.recommended_provider
    if provider_sla_path:
        payload = load_json_mapping(provider_sla_path)
        candidates = payload.get("providers", payload)
        if isinstance(candidates, Mapping) and provider_name in candidates and isinstance(candidates[provider_name], Mapping):
            provider_sla = dict(candidates[provider_name])
        else:
            provider_sla = payload
        logger.info("Provider SLA loaded from %s", provider_sla_path)
        return provider_sla

    provider_sla: Dict[str, Any] = {}
    negotiation_weights: Dict[str, float] = {}
    provider_weights = recommendation.provider_weights.get(provider_name, {})
    for dataset_attribute, negotiation_attribute in NEGOTIATION_ATTRIBUTE_MAP.items():
        value = recommendation.provider_attributes.get(dataset_attribute)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            provider_sla[negotiation_attribute] = {"value": float(value)}
            weight = provider_weights.get(dataset_attribute)
            if isinstance(weight, (int, float)) and not isinstance(weight, bool):
                negotiation_weights[negotiation_attribute] = float(weight)
    if not provider_sla:
        raise ValueError(
            "The recommended provider has no numeric negotiable dataset values; "
            "provide --provider-sla with reviewed provider SLA input."
        )
    if negotiation_weights:
        provider_sla["weights"] = negotiation_weights
    logger.info("Provider SLA adapted from compatible structured dataset fields")
    return provider_sla


def run_workflow(
    dataset_path: Path,
    requirements_path: Optional[Path] = None,
    user_sla_path: Optional[Path] = None,
    provider_sla_path: Optional[Path] = None,
    interactive: bool = False,
    negotiation_config: Optional[NegotiationConfig] = None,
) -> WorkflowResult:
    """Execute Dataset → Recommendation → Negotiation → SLA → Evaluation."""

    logger.info("IRNAM workflow started")

    logger.info("Loading structured dataset")
    dataset_loader = RecommendationEngine(dataset_path=dataset_path)
    providers = dataset_loader.load_dataset()
    logger.info("Dataset loaded: %d providers", len(providers))

    logger.info("Collecting user requirements")
    processor = UserRequirementProcessor()
    requirement = collect_user_requirements(processor, requirements_path, interactive)
    user_sla = collect_user_sla(user_sla_path, interactive)

    logger.info("Generating recommendation")
    recommendation = RecommendationEngine(providers=providers).recommend(requirement)
    if not recommendation.recommended_provider:
        raise RuntimeError(recommendation.reason_for_recommendation)

    logger.info("Preparing negotiation for %s", recommendation.recommended_provider)
    provider_sla = provider_sla_for_recommendation(recommendation, provider_sla_path)
    negotiation = NegotiationEngine(negotiation_config or NegotiationConfig()).negotiate(
        recommendation,
        user_sla,
        provider_sla,
    )

    logger.info("Generating negotiated SLA")
    contract = SLAManager().create_contract(
        negotiation,
        metadata={
            "recommendation_score": recommendation.overall_score,
            "dataset_path": str(dataset_path),
        },
    )

    logger.info("Running evaluation")
    metrics = NegotiationEvaluator().evaluate([negotiation])
    logger.info("IRNAM workflow completed")
    return WorkflowResult(
        dataset_path=str(dataset_path),
        provider_count=len(providers),
        requirement=requirement,
        recommendation=recommendation,
        negotiation=negotiation,
        sla_contract=contract,
        evaluation=metrics,
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for the demonstration workflow."""

    parser = argparse.ArgumentParser(description="Run the complete IRNAM research workflow")
    parser.add_argument("--dataset", type=Path, default=Path("outputs/cloud_dataset.json"))
    parser.add_argument("--requirements", type=Path, help="JSON object containing all user priorities")
    parser.add_argument("--user-sla", type=Path, help="JSON object containing user negotiable targets")
    parser.add_argument("--provider-sla", type=Path, help="JSON provider SLA object or provider-keyed object")
    parser.add_argument("--interactive", action="store_true", help="Prompt for priorities and availability target")
    parser.add_argument("--strategy", choices=("competitive", "win_win", "collaborative"), default="win_win")
    parser.add_argument("--max-rounds", type=int, default=10)
    parser.add_argument("--acceptance-threshold", type=float, default=0.0)
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point. Return zero on success and a nonzero code on failure."""

    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    try:
        result = run_workflow(
            dataset_path=args.dataset,
            requirements_path=args.requirements,
            user_sla_path=args.user_sla,
            provider_sla_path=args.provider_sla,
            interactive=args.interactive,
            negotiation_config=NegotiationConfig(
                strategy=args.strategy,
                max_rounds=args.max_rounds,
                acceptance_threshold=args.acceptance_threshold,
            ),
        )
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    except KeyboardInterrupt:
        logger.warning("Workflow cancelled by user")
        return 130
    except (FileNotFoundError, TypeError, ValueError, RuntimeError) as exc:
        logger.exception("IRNAM workflow failed: %s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
