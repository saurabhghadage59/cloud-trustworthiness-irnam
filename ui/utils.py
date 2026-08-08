"""UI-only state, serialization, and logging helpers."""

from __future__ import annotations

import io
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, TypeVar

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "outputs" / "cloud_dataset.json"
METADATA_PATH = ROOT / "outputs" / "dataset_metadata.json"

T = TypeVar("T")

SESSION_DEFAULTS = {
    "requirement": None,
    "recommendation": None,
    "negotiation": None,
    "sla_contract": None,
    "evaluation": None,
    "execution_logs": [],
}


def initialize_session_state() -> None:
    """Create all cross-page state keys once."""

    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = list(value) if isinstance(value, list) else value


def read_json(path: Path, default: Any = None) -> Any:
    """Read JSON for dashboard metadata without leaking filesystem errors."""

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def json_text(value: Any) -> str:
    """Serialize backend objects for download."""

    if hasattr(value, "to_dict"):
        value = value.to_dict()
    return json.dumps(value, indent=2, sort_keys=True, default=str)


def execute_with_logs(label: str, action: Callable[[], T]) -> T:
    """Execute a backend call and persist its log records for the UI."""

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s · %(name)s · %(message)s"))
    root_logger = logging.getLogger()
    previous_level = root_logger.level
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    started = datetime.now().strftime("%H:%M:%S")
    try:
        result = action()
        outcome = "Completed"
        return result
    except Exception:
        outcome = "Failed"
        raise
    finally:
        root_logger.removeHandler(handler)
        root_logger.setLevel(previous_level)
        captured = stream.getvalue().strip()
        entry = f"[{started}] {label} — {outcome}"
        if captured:
            entry += f"\n{captured}"
        st.session_state.execution_logs.append(entry)


def clear_downstream(from_stage: str) -> None:
    """Invalidate dependent results when an upstream stage changes."""

    order = ["recommendation", "negotiation", "sla_contract", "evaluation"]
    if from_stage not in order:
        return
    for key in order[order.index(from_stage) + 1 :]:
        st.session_state[key] = None


def complete_report() -> dict[str, Any]:
    """Build a single downloadable report from current session results."""

    report = {}
    for key in ("requirement", "recommendation", "negotiation", "sla_contract", "evaluation"):
        value = st.session_state.get(key)
        if value is not None:
            report[key] = value.to_dict() if hasattr(value, "to_dict") else value
    return report
