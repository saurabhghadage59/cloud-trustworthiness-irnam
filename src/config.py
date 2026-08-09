"""Central, dependency-free configuration for the research framework."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class FrameworkConfig:
    dataset_path: Path = ROOT / "src" / "dataset" / "cloud_dataset.csv"
    output_dir: Path = ROOT / "outputs"
    normalization: str = "minmax"
    random_seed: int = 42
    algorithm: str = "IRNAM_Weighted"
    benefit_attributes: tuple[str, ...] = ("Availability", "Reliability", "ThroughputMbps", "SecurityScore", "ComplianceScore", "SupportScore", "ScalabilityScore", "EnergyEfficiency", "CustomerRating", "TrustScore")
    cost_attributes: tuple[str, ...] = ("LatencyMs", "ResponseTimeMs", "PacketLossPct", "CostPerHourUSD", "SLAViolationRate")
    category_weights: Mapping[str, float] = field(default_factory=lambda: {"economic": 0.25, "performance": 0.35, "security_trust": 0.25, "service_quality": 0.15})
    ml_parameters: Mapping[str, object] = field(default_factory=dict)

DEFAULT_CONFIG = FrameworkConfig()
