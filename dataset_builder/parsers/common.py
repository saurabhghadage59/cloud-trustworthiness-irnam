"""Conservative parsing helpers that never infer missing values."""

from typing import Any, Optional


def parse_raw_value(value: Any) -> Optional[str]:
    """Convert a collected scalar to a stripped string without normalising it."""
    if value is None:
        return None
    parsed = str(value).strip()
    return parsed or None
