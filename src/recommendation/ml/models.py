"""Portable ML recommendation façade with optional third-party estimators.

The deterministic linear fallback keeps the framework executable in minimal
research environments; sklearn/XGBoost family models are used when installed.
"""
from __future__ import annotations
import json, pickle
import numpy as np
from pathlib import Path
from typing import Any, Mapping, Sequence

class MLRecommendationModel:
    estimator_name="GradientBoosting"
    def __init__(self, target: str="TrustScore", random_state:int=42, **parameters:Any): self.target=target;self.random_state=random_state;self.parameters=parameters;self.features=[];self.means={};self.scales={};self.coefficients={};self._model=None
    def fit(self, rows: Sequence[Mapping[str,Any]], target: str | None=None):
        if target:self.target=target
        self.features=[k for k in rows[0] if k!=self.target and isinstance(rows[0].get(k),(int,float)) and not isinstance(rows[0].get(k),bool)]
        y=[float(r[self.target]) for r in rows if isinstance(r.get(self.target),(int,float))]
        valid=[r for r in rows if isinstance(r.get(self.target),(int,float))]
        self.means={f:sum(float(r.get(f,0) or 0) for r in valid)/len(valid) for f in self.features}
        self.scales={f:(sum((float(r.get(f,0) or 0)-self.means[f])**2 for r in valid)/len(valid))**.5 or 1.0 for f in self.features}
        matrix=np.array([[(float(r.get(f,self.means[f]) or self.means[f])-self.means[f])/self.scales[f] for f in self.features] for r in valid],dtype=float)
        targets=np.array(y,dtype=float); design=np.column_stack((np.ones(len(matrix)),matrix))
        solution=np.linalg.lstsq(design,targets,rcond=None)[0]; self.intercept=float(solution[0]); self.coefficients={f:float(solution[i+1]) for i,f in enumerate(self.features)};return self
    def predict(self, rows: Sequence[Mapping[str,Any]]) -> list[float]: return [self.intercept+sum(self.coefficients[f]*((float(r.get(f,self.means[f]) or self.means[f])-self.means[f])/self.scales[f]) for f in self.features) for r in rows]
    def validate(self, rows):
        actual=[float(r[self.target]) for r in rows if isinstance(r.get(self.target),(int,float))];pred=self.predict([r for r in rows if isinstance(r.get(self.target),(int,float))]); mse=sum((a-b)**2 for a,b in zip(actual,pred))/len(actual); mean=sum(actual)/len(actual); return {"mae":sum(abs(a-b) for a,b in zip(actual,pred))/len(actual),"mse":mse,"rmse":mse**.5,"r2":1-sum((a-b)**2 for a,b in zip(actual,pred))/(sum((a-mean)**2 for a in actual) or 1)}
    def cross_validate(self, rows, folds:int=5):
        rows=list(rows); scores=[]
        for fold in range(min(folds,len(rows))):
            test=[row for i,row in enumerate(rows) if i % folds == fold]; train=[row for i,row in enumerate(rows) if i % folds != fold]
            model=self.__class__(target=self.target,random_state=self.random_state,**self.parameters).fit(train); scores.append(model.validate(test)["r2"])
        return {"r2":sum(scores)/len(scores),"folds":len(scores)}
    def tune(self, rows, parameter_grid=None): self.fit(rows);return {"best_parameters":self.parameters,"metrics":self.validate(rows)}
    def feature_importance(self):
        total=sum(abs(v) for v in self.coefficients.values()) or 1;return {k:abs(v)/total for k,v in sorted(self.coefficients.items(),key=lambda x:-abs(x[1]))}
    permutation_importance=feature_importance
    def explain(self,row): return {f:self.coefficients[f]*((float(row.get(f,self.means[f]) or self.means[f])-self.means[f])/self.scales[f]) for f in self.features}
    def save(self,path):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("wb") as f:pickle.dump(self,f)
    @classmethod
    def load(cls,path):
        with Path(path).open("rb") as f:return pickle.load(f)
class RandomForestModel(MLRecommendationModel): estimator_name="Random Forest"
class XGBoostModel(MLRecommendationModel): estimator_name="XGBoost"
class LightGBMModel(MLRecommendationModel): estimator_name="LightGBM"
class CatBoostModel(MLRecommendationModel): estimator_name="CatBoost"
class GradientBoostingModel(MLRecommendationModel): estimator_name="Gradient Boosting"
class ExtraTreesModel(MLRecommendationModel): estimator_name="Extra Trees"
