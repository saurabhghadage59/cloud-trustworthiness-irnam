"""Evaluation facade for IRNAM negotiation runs."""

from __future__ import annotations

from typing import Any, Iterable

from evaluation.negotiation_metrics import NegotiationMetrics, calculate_negotiation_metrics


class NegotiationEvaluator:
    def evaluate(self, results: Iterable[Any]) -> NegotiationMetrics:
        return calculate_negotiation_metrics(results)


__all__ = ["NegotiationEvaluator", "NegotiationMetrics", "calculate_negotiation_metrics"]
