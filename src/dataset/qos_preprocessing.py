"""Reusable mentor-QoS validation and decision-matrix preprocessing."""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

QOS_CRITERIA = {
    "availability": {"column": "Availability", "type": "benefit"},
    "reliability": {"column": "Reliability", "type": "benefit"},
    "throughput": {"column": "Throughput", "type": "benefit"},
    "response_time": {"column": "Response Time", "type": "cost"},
    "latency": {"column": "Latency", "type": "cost"},
    "documentation": {"column": "Documentation", "type": "benefit"},
    "best_practices": {"column": "Best Practices", "type": "benefit"},
}

@dataclass(frozen=True)
class PreprocessingReport:
    raw_records: int; valid_records: int; unique_services: int; invalid_rows_removed: int; missing_qos_values: int

def is_mentor_qos_schema(rows: Sequence[Mapping[str, Any]]) -> bool:
    return bool(rows) and all(any(key in rows[0] for key in (name, f"{name}_score")) for name in QOS_CRITERIA)

def preprocess_qos_rows(rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], PreprocessingReport]:
    """Drop invalid observations and mean-aggregate duplicate service observations."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list); missing = invalid = 0
    for row in rows:
        name = str(row.get("provider_name") or "").strip()
        values = {}
        for criterion in QOS_CRITERIA:
            value = row.get(criterion, row.get(f"{criterion}_score"))
            if not isinstance(value, (int, float)) or isinstance(value, bool): missing += 1; values = {}; break
            values[criterion] = float(value)
        if not name or not values: invalid += 1; continue
        grouped[name].append({**values, "wsdl_address": row.get("wsdl_address")})
    alternatives=[]
    for name, observations in grouped.items():
        alternatives.append({"provider_name": name, "service_name": name, "record_count": len(observations),
            **{criterion: sum(item[criterion] for item in observations)/len(observations) for criterion in QOS_CRITERIA},
            "wsdl_address": observations[0].get("wsdl_address")})
    return alternatives, PreprocessingReport(len(rows), sum(map(len, grouped.values())), len(grouped), invalid, missing)
