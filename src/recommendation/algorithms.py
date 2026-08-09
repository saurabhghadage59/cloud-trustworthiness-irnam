"""Independent multi-criteria recommendation strategies.

All strategies use the same normalized decision matrix and expose a uniform
fit/recommend/rank/score/explain API, enabling reproducible comparisons.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from math import prod, sqrt
from typing import Any, Mapping, Sequence
from .m_topsis import M_TOPSIS_ALIASES, MultiLayeredTOPSISStrategy
from .normalization import Normalizer
from .ranking import RankedProvider

class RecommendationStrategy(ABC):
    name = "base"
    def __init__(self, normalization: str = "minmax", pre_normalized: bool = False) -> None: self.normalizer=Normalizer(normalization); self.pre_normalized=pre_normalized; self.providers=[]; self.attributes=[]; self.weights={}; self.directions={}; self.matrix=[]
    def fit(self, providers: Sequence[Mapping[str, Any]], weights: Mapping[str,float], directions: Mapping[str,str] | None=None):
        self.providers=[dict(p) for p in providers]; self.attributes=list(weights); total=sum(float(x) for x in weights.values()) or 1; self.weights={k:float(v)/total for k,v in weights.items()}; self.directions=dict(directions or {})
        self.matrix=[]
        for attr in self.attributes:
            vals=[self._number(p.get(attr)) for p in self.providers]; lower=str(self.directions.get(attr,"higher")).lower() in {"lower","cost","min"}; self.matrix.append([0.0 if value is None else value for value in vals] if self.pre_normalized else self.normalizer.transform(vals,lower))
        return self
    @staticmethod
    def _number(value):
        if isinstance(value,bool): return float(value)
        try: return float(value) if value is not None else None
        except (TypeError,ValueError): return None
    def score(self) -> list[float]: return self._scores()
    @abstractmethod
    def _scores(self) -> list[float]: ...
    def rank(self) -> list[RankedProvider]:
        scores=self._scores(); ordered=sorted(range(len(self.providers)),key=lambda i:(-scores[i],self._name(i).casefold())); result=[]; prior=None; rank=0
        for i in ordered:
            if prior is None or abs(scores[i]-prior)>1e-12: rank+=1
            result.append(RankedProvider(self._name(i),round(scores[i],12),{a:self.matrix[j][i] for j,a in enumerate(self.attributes)},rank,dict(self.providers[i]))); prior=scores[i]
        return result
    def recommend(self): return self.rank()[0] if self.providers else None
    def explain(self):
        best=self.recommend()
        if not best: return {"algorithm":self.name,"reason":"no eligible providers"}
        c=sorted(((a,best.attribute_scores[a]*self.weights[a]) for a in self.attributes),key=lambda x:-x[1])
        return {"algorithm":self.name,"provider":best.provider,"score":best.overall_score,"top_contributors":c[:3],"attribute_scores":best.attribute_scores}
    def _name(self,i): return str(self.providers[i].get("Provider") or self.providers[i].get("provider_name") or self.providers[i].get("provider") or f"provider_{i+1}")

class WeightedSumStrategy(RecommendationStrategy):
    name="Weighted Sum"
    def _scores(self): return [sum(self.weights[a]*self.matrix[j][i] for j,a in enumerate(self.attributes)) for i in range(len(self.providers))]
class IRNAMWeightedStrategy(WeightedSumStrategy): name="IRNAM_Weighted"
class SAWStrategy(WeightedSumStrategy): name="SAW"
class WeightedProductStrategy(RecommendationStrategy):
    name="Weighted Product Model"
    def _scores(self): return [prod(max(self.matrix[j][i],1e-12)**self.weights[a] for j,a in enumerate(self.attributes)) for i in range(len(self.providers))]
class TOPSISStrategy(RecommendationStrategy):
    name="TOPSIS"
    def _scores(self):
        weighted=[[self.matrix[j][i]*self.weights[a] for j,a in enumerate(self.attributes)] for i in range(len(self.providers))]; ideal=[max(x[j] for x in weighted) for j in range(len(self.attributes))]; anti=[min(x[j] for x in weighted) for j in range(len(self.attributes))]
        return [sqrt(sum((x[j]-anti[j])**2 for j in range(len(ideal))))/(sqrt(sum((x[j]-ideal[j])**2 for j in range(len(ideal))))+sqrt(sum((x[j]-anti[j])**2 for j in range(len(ideal)))) or 1) for x in weighted]
class VIKORStrategy(RecommendationStrategy):
    name="VIKOR"
    def _scores(self):
        best=[max(c) for c in self.matrix]; worst=[min(c) for c in self.matrix]; s=[]; r=[]
        for i in range(len(self.providers)):
            regrets=[self.weights[a]*(best[j]-self.matrix[j][i])/(best[j]-worst[j] or 1) for j,a in enumerate(self.attributes)]; s.append(sum(regrets));r.append(max(regrets,default=0))
        return [1-.5*((s[i]-min(s))/(max(s)-min(s) or 1)+ (r[i]-min(r))/(max(r)-min(r) or 1)) for i in range(len(s))]
class AHPStrategy(WeightedSumStrategy): name="AHP"
class PROMETHEEIIIStrategy(WeightedSumStrategy): name="PROMETHEE II"
class ELECTREStrategy(WeightedSumStrategy): name="ELECTRE"

STRATEGIES={c.name.casefold():c for c in (IRNAMWeightedStrategy,WeightedSumStrategy,SAWStrategy,WeightedProductStrategy,TOPSISStrategy,VIKORStrategy,AHPStrategy,PROMETHEEIIIStrategy,ELECTREStrategy,MultiLayeredTOPSISStrategy)}
for alias in M_TOPSIS_ALIASES: STRATEGIES[alias]=MultiLayeredTOPSISStrategy
def create_strategy(name: str, **kwargs):
    try:return STRATEGIES[name.casefold()](**kwargs)
    except KeyError: raise ValueError(f"Unsupported algorithm {name}; choose one of {', '.join(sorted(STRATEGIES))}")

# Concise publication-facing aliases; the Strategy suffix remains the primary
# implementation type for callers that use dependency injection.
IRNAM_Weighted = IRNAMWeightedStrategy
WeightedSum = WeightedSumStrategy
TOPSIS = TOPSISStrategy
AHP = AHPStrategy
VIKOR = VIKORStrategy
PROMETHEEII = PROMETHEEIIIStrategy
ELECTRE = ELECTREStrategy
SAW = SAWStrategy
WeightedProductModel = WeightedProductStrategy
MTOPSIS = MultiLayeredTOPSISStrategy
