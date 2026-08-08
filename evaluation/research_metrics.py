"""Ranking metrics used for algorithm benchmarking."""
from __future__ import annotations
from math import log2
from statistics import mean
from typing import Sequence
def precision_at_k(predicted:Sequence[str], relevant:Sequence[str], k:int)->float: return sum(x in set(relevant) for x in predicted[:k])/max(k,1)
def recall_at_k(predicted, relevant, k): return sum(x in set(relevant) for x in predicted[:k])/max(len(set(relevant)),1)
def f1_at_k(predicted,relevant,k):
    p,r=precision_at_k(predicted,relevant,k),recall_at_k(predicted,relevant,k);return 2*p*r/(p+r) if p+r else 0.0
def average_precision(predicted,relevant):
    hits=0;return sum((hits:=hits+1)/i for i,x in enumerate(predicted,1) if x in set(relevant))/max(len(set(relevant)),1)
def reciprocal_rank(predicted,relevant): return next((1/i for i,x in enumerate(predicted,1) if x in set(relevant)),0.0)
def ndcg(predicted,relevant,k):
    rel=set(relevant); dcg=sum((1 if x in rel else 0)/log2(i+1) for i,x in enumerate(predicted[:k],1)); ideal=sum(1/log2(i+1) for i in range(1,min(k,len(rel))+1));return dcg/ideal if ideal else 0.0
def spearman(left,right):
    n=min(len(left),len(right));return 1-6*sum((left.index(x)-right.index(x))**2 for x in left[:n] if x in right)/max(n*(n*n-1),1)
def kendall_tau(left,right):
    common=[x for x in left if x in right]; total=len(common)*(len(common)-1)/2 or 1; concordant=sum((left.index(a)-left.index(b))*(right.index(a)-right.index(b))>0 for i,a in enumerate(common) for b in common[i+1:]);return 2*concordant/total-1
