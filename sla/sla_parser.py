"""Parsing and serialization helpers for SLA objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Union

from sla.sla_contract import SLAContract


class SLAParser:
    def parse(self, source: Union[str, Path, Mapping[str, Any], SLAContract]) -> Dict[str, Any]:
        if isinstance(source, SLAContract):
            return source.to_dict()
        if isinstance(source, Mapping):
            return dict(source)
        text = str(source)
        if text.lstrip().startswith(("{", "[")):
            return json.loads(text)
        path = Path(text)
        if path.exists():
            text = path.read_text(encoding="utf-8")
        return json.loads(text)

    def serialize(self, sla: Union[Mapping[str, Any], SLAContract], *, indent: int = 2) -> str:
        if isinstance(sla, SLAContract):
            return sla.to_json(indent=indent)
        return json.dumps(dict(sla), indent=indent, sort_keys=True)
