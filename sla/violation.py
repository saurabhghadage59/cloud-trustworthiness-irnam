"""Simple SLA violation checks for operationalized contracts."""

from __future__ import annotations

from typing import Dict, Mapping


def detect_violations(contract_attributes: Mapping[str, float], observed_attributes: Mapping[str, float]) -> Dict[str, Dict[str, float]]:
    violations: Dict[str, Dict[str, float]] = {}
    for attr, expected in contract_attributes.items():
        if attr not in observed_attributes:
            continue
        observed = observed_attributes[attr]
        if observed != expected:
            violations[attr] = {"expected": expected, "observed": observed}
    return violations
