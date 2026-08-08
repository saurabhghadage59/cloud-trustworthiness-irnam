"""Reusable, direction-aware numeric normalization strategies."""
from __future__ import annotations
from statistics import median
from typing import Iterable

class Normalizer:
    SUPPORTED = {"minmax", "zscore", "robust", "decimal"}
    def __init__(self, method: str = "minmax") -> None:
        self.method = method.lower().replace("-", "")
        if self.method not in self.SUPPORTED: raise ValueError(f"Unknown normalization method: {method}")
    def transform(self, values: Iterable[float | None], lower_is_better: bool = False) -> list[float]:
        source = list(values); present = [float(v) for v in source if v is not None]
        if not present: return [0.0] * len(source)
        if self.method == "minmax":
            lo, hi = min(present), max(present); raw = [0.5 if hi == lo else (float(v)-lo)/(hi-lo) for v in source if v is not None]
        elif self.method == "zscore":
            mean = sum(present)/len(present); sd = (sum((x-mean)**2 for x in present)/len(present))**.5 or 1.0
            z = [(x-mean)/sd for x in present]; lo, hi = min(z), max(z); raw = [0.5 if hi == lo else (x-lo)/(hi-lo) for x in z]
        elif self.method == "robust":
            med = median(present); ordered=sorted(present); q1=ordered[len(ordered)//4]; q3=ordered[(3*len(ordered))//4]; scale=q3-q1 or 1.0
            z=[(x-med)/scale for x in present]; lo,hi=min(z),max(z); raw=[0.5 if hi==lo else (x-lo)/(hi-lo) for x in z]
        else:
            factor=10 ** len(str(int(max(abs(x) for x in present))))
            raw=[x/factor for x in present]
        it=iter(raw); result=[next(it) if v is not None else 0.0 for v in source]
        return [1.0-x if lower_is_better else x for x in result]

def normalize(values: Iterable[float | None], method: str = "minmax", lower_is_better: bool = False) -> list[float]:
    return Normalizer(method).transform(values, lower_is_better)
