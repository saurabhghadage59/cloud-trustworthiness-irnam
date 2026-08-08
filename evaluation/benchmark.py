from __future__ import annotations
import csv,json,time,tracemalloc
from pathlib import Path
from typing import Mapping,Sequence,Any
from src.recommendation.algorithms import create_strategy
from src.recommendation.ranking import RankedProvider
from .research_metrics import *
def run_benchmark(providers:Sequence[Mapping[str,Any]], weights:Mapping[str,float], directions:Mapping[str,str], output_dir:Path|str, baseline_ranking: Sequence[RankedProvider] | None = None, pre_normalized: bool = False):
    output=Path(output_dir);output.mkdir(parents=True,exist_ok=True); rows=[]; results={}
    if not providers: raise ValueError("Benchmark requires at least one filtered provider")
    for name in ("IRNAM_Weighted","TOPSIS","AHP","VIKOR","PROMETHEE II","ELECTRE","SAW","Weighted Product Model"):
        tracemalloc.start();started=time.perf_counter()
        ranking = list(baseline_ranking) if name == "IRNAM_Weighted" and baseline_ranking is not None else create_strategy(name, pre_normalized=pre_normalized).fit(providers,weights,directions).rank()
        current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        if baseline_ranking is not None and name == "IRNAM_Weighted" and ranking[0].provider != baseline_ranking[0].provider: raise RuntimeError("IRNAM comparison is inconsistent with recommendation")
        results[name]=[r.to_dict() for r in ranking];rows.append({"algorithm":name,"top_provider":ranking[0].provider,"top_score":ranking[0].overall_score,"execution_seconds":time.perf_counter()-started,"memory_bytes":peak,"rank":ranking[0].rank,"provider_count":len(providers)})
    with (output/"comparison.csv").open("w",newline="",encoding="utf-8") as f:csv.DictWriter(f,fieldnames=rows[0]).writeheader();csv.DictWriter(f,fieldnames=rows[0]).writerows(rows)
    (output/"recommendation_results.json").write_text(json.dumps(results,indent=2),encoding="utf-8");(output/"evaluation_report.json").write_text(json.dumps(rows,indent=2),encoding="utf-8");(output/"evaluation_report.csv").write_text((output/"comparison.csv").read_text(encoding="utf-8"),encoding="utf-8")
    (output/"benchmark_report.md").write_text("# Algorithm benchmark\n\n"+"\n".join(f"- {x['algorithm']}: **{x['top_provider']}** ({x['top_score']:.4f})" for x in rows),encoding="utf-8")
    # Spreadsheet and portable HTML plots are execution artifacts, not a
    # prerequisite for the ranking algorithms themselves.
    try:
        import pandas as pd
        pd.DataFrame(rows).to_excel(output / "comparison.xlsx", index=False)
    except ImportError:
        pass
    try:
        import plotly.express as px
        plots = output / "plots"; plots.mkdir(exist_ok=True)
        frame = __import__("pandas").DataFrame(rows)
        px.bar(frame, x="algorithm", y="top_score", title="Algorithm comparison").write_html(plots / "algorithm_comparison.html")
        px.bar(frame, x="algorithm", y="execution_seconds", title="Execution time").write_html(plots / "execution_time.html")
    except ImportError:
        pass
    return rows
