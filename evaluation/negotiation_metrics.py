"""Metrics for evaluating IRNAM negotiation experiments."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any, Dict, Iterable, List


def _as_dict(result: Any) -> Dict[str, Any]:
    return result.to_dict() if hasattr(result, "to_dict") else dict(result)


@dataclass
class NegotiationMetrics:
    negotiation_success_rate: float
    average_negotiation_time: float
    average_negotiation_rounds: float
    concession_statistics: Dict[str, float]
    user_satisfaction: float
    provider_satisfaction: float
    agreement_rate: float
    total_runs: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "negotiation_success_rate": self.negotiation_success_rate,
            "average_negotiation_time": self.average_negotiation_time,
            "average_negotiation_rounds": self.average_negotiation_rounds,
            "concession_statistics": dict(self.concession_statistics),
            "user_satisfaction": self.user_satisfaction,
            "provider_satisfaction": self.provider_satisfaction,
            "agreement_rate": self.agreement_rate,
            "total_runs": self.total_runs,
        }


def calculate_negotiation_metrics(results: Iterable[Any]) -> NegotiationMetrics:
    rows: List[Dict[str, Any]] = [_as_dict(result) for result in results]
    if not rows:
        return NegotiationMetrics(0.0, 0.0, 0.0, {}, 0.0, 0.0, 0.0, 0)

    successes = [row for row in rows if row.get("success")]
    durations = [float(row.get("duration_seconds", 0.0)) for row in rows]
    rounds = [float(row.get("negotiation_rounds", 0.0)) for row in rows]
    concessions = [
        float(round_data.get("concession", 0.0))
        for row in rows
        for round_data in row.get("rounds", [])
    ]
    user_satisfaction = [
        float(row.get("satisfaction", {}).get("user_satisfaction", 0.0))
        for row in successes
        if row.get("satisfaction")
    ]
    provider_satisfaction = [
        float(row.get("satisfaction", {}).get("provider_satisfaction", 0.0))
        for row in successes
        if row.get("satisfaction")
    ]

    concession_stats = {}
    if concessions:
        concession_stats = {
            "min": min(concessions),
            "max": max(concessions),
            "avg": mean(concessions),
            "count": float(len(concessions)),
        }

    success_rate = len(successes) / len(rows)
    return NegotiationMetrics(
        negotiation_success_rate=success_rate,
        average_negotiation_time=mean(durations) if durations else 0.0,
        average_negotiation_rounds=mean(rounds) if rounds else 0.0,
        concession_statistics=concession_stats,
        user_satisfaction=mean(user_satisfaction) if user_satisfaction else 0.0,
        provider_satisfaction=mean(provider_satisfaction) if provider_satisfaction else 0.0,
        agreement_rate=success_rate,
        total_runs=len(rows),
    )
