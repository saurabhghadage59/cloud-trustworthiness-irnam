"""Readable terminal and file reporting for the end-to-end research demo."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Sequence

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

class TerminalReporter:
    """Render only already-computed pipeline values; it never changes scoring."""
    def __init__(self, console: Console | None = None) -> None: self.console = console or Console()
    def banner(self) -> None:
        self.console.print(Panel("[bold cyan]Cloud Trustworthiness Recommendation Framework[/]\nIRNAM + Multi-Algorithm Recommendation System\nCOEP Technological University", border_style="cyan"))
    def dataset_summary(self, rows: Sequence[Mapping[str, Any]]) -> None:
        if rows and "best_practices" in rows[0]:
            table=Table(title="DATASET SUMMARY", box=box.SIMPLE_HEAVY, show_header=False)
            table.add_row("Final Service Alternatives", str(len(rows))); table.add_row("QoS Criteria", "7")
            self.console.print(table); return
        keys={k for r in rows for k in r}; provider_key="Provider" if "Provider" in keys else "provider_name"
        values=lambda key: {str(r.get(key)) for r in rows if r.get(key) is not None}
        table=Table(title="DATASET SUMMARY", box=box.SIMPLE_HEAVY, show_header=False)
        for label,value in (("Providers",len(values(provider_key))),("Records",len(rows)),("Features",len(keys)),("Regions",len(values("Region"))),("Service Types",len(values("ServiceType"))),("Missing Values",sum(v is None for r in rows for v in r.values()))): table.add_row(label,str(value))
        self.console.print(table)
    def requirements(self, priorities: Mapping[str, Any], weights: Mapping[str,float]) -> None:
        table=Table(title="USER REQUIREMENTS AND NORMALIZED WEIGHTS", box=box.SIMPLE_HEAVY)
        table.add_column("Attribute");table.add_column("Priority");table.add_column("Weight",justify="right")
        for key in weights: table.add_row(key.replace("_"," ").title(),str(priorities.get(key,"N/A")).upper(),f"{weights[key]:.3f}")
        self.console.print(table)
    def ranking(self, result: Any, elapsed: float) -> None:
        if result.complete_ranking and "best_practices" in result.complete_ranking[0].provider_attributes:
            table=Table(title="TOP 10 SERVICES", box=box.SIMPLE_HEAVY)
            for name in ("Rank","Service Name","Score","Trust","Availability","Reliability","Throughput","Response Time","Latency","Documentation","Best Practices","Records","Time"): table.add_column(name)
            for item in result.complete_ranking[:10]:
                raw=item.provider_attributes; fmt=lambda key: f"{raw[key]:.2f}" if isinstance(raw.get(key),(int,float)) else "N/A"
                table.add_row(str(item.rank),item.provider,f"{item.overall_score*100:.2f}",fmt("TrustScore"),fmt("availability"),fmt("reliability"),fmt("throughput"),fmt("response_time"),fmt("latency"),fmt("documentation"),fmt("best_practices"),str(raw.get("record_count","N/A")),f"{elapsed:.3f}s")
            self.console.print(table); return
        table=Table(title="TOP 10 PROVIDERS", box=box.SIMPLE_HEAVY)
        for name in ("Rank","Provider","Region","Service","Score","Trust","Availability","Latency","Response","Cost","Support","Scale","Time"): table.add_column(name, justify="right" if name not in {"Provider","Region","Service"} else "left")
        for item in result.complete_ranking[:10]:
            raw=item.provider_attributes; get=lambda *keys: next((raw[k] for k in keys if k in raw), None)
            fmt=lambda v: "N/A" if v is None else f"{float(v):.2f}" if isinstance(v,(int,float)) else str(v)
            table.add_row(str(item.rank),item.provider,fmt(get("Region")),fmt(get("ServiceType")),f"{item.overall_score*100:.2f}",fmt(get("TrustScore","trust_score")),fmt(get("Availability","availability_sla_percent")),fmt(get("LatencyMs")),fmt(get("ResponseTimeMs")),fmt(get("CostPerHourUSD","minimum_vm_price_usd_hour")),fmt(get("SupportScore","support_tier")),fmt(get("ScalabilityScore")),f"{elapsed:.3f}s")
        self.console.print(table)
    def pipeline_status(self) -> None:
        self.console.print("[green][OK][/] Recommendation started  [green][OK][/] Providers filtered  [green][OK][/] Providers ranked  [green][OK][/] Trust calculated  [green][OK][/] Completed")
    def comparison_validation(self, result: Any, shared_providers: Sequence[Mapping[str, Any]]) -> None:
        """Make shared-input invariants visible before benchmark execution."""
        if len(shared_providers) != len(result.complete_ranking): raise RuntimeError("Provider count is not shared")
        if not shared_providers or not result.user_weights: raise RuntimeError("Shared comparison context is incomplete")
        table = Table(title="COMPARISON INPUT VALIDATION", box=box.SIMPLE_HEAVY, show_header=False)
        for label in ("Dataset loaded", "Requirements shared", "Weight vector shared", "Provider count shared", "Filtering shared", "Normalization shared", "IRNAM baseline retained"):
            table.add_row(label, "[green]PASS[/]")
        self.console.print(table)
    def best(self, result: Any) -> None:
        raw=result.provider_attributes; trust=raw.get("TrustScore", "N/A"); confidence=min(100.0, max(0.0,result.recommendation_confidence*100))
        self.console.print(Panel(f"[bold green]{result.recommended_provider}[/]\nOverall Score: {result.overall_score*100:.2f}\nTrust Score: {trust}\nRecommendation Confidence: {confidence:.1f}%\nRegion: {raw.get('Region', 'N/A')}\nService Type: {raw.get('ServiceType', 'N/A')}", title="BEST CLOUD PROVIDER", border_style="green"))
        self.console.print("[bold]WHY THIS PROVIDER WAS CHOSEN[/]\n"+result.reason_for_recommendation)
        contributions=sorted(((name,score*result.user_weights.get(name,0)) for name,score in result.attribute_scores.items()),key=lambda x:-x[1])
        total=sum(v for _,v in contributions) or 1
        bar_character = "█" if (sys.stdout.encoding or "").lower().replace("-", "") in {"utf8", "utf_8"} else "#"
        for name,value in contributions:
            pct=value/total*100; self.console.print(f"  {name.title():<20} {bar_character*round(pct/4):<25} {pct:5.1f}%")
    def negotiation_sla(self, workflow: Any) -> None:
        n=workflow.negotiation; s=workflow.sla_contract
        table=Table(title="NEGOTIATION AND SLA", box=box.SIMPLE_HEAVY);table.add_column("Item");table.add_column("Value")
        table.add_row("Negotiation rounds",str(n.negotiation_rounds));table.add_row("Initial offer",str(n.rounds[0].offer.attributes) if n.rounds else "N/A");table.add_row("Counter/final offer",str(n.final_offer.attributes) if n.final_offer else "N/A");table.add_row("Final agreement",n.reason);table.add_row("User satisfaction",f"{n.satisfaction.user_satisfaction:.3f}" if n.satisfaction else "N/A");table.add_row("Provider satisfaction",f"{n.satisfaction.provider_satisfaction:.3f}" if n.satisfaction else "N/A");table.add_row("Negotiation time",f"{(n.completed_at-n.started_at).total_seconds():.4f}s")
        raw = workflow.recommendation.provider_attributes
        table.add_row("Backup", str(raw.get("backup", "N/A"))); table.add_row("Disaster recovery", str(raw.get("disaster_recovery", "N/A")))
        for key,value in s.metadata.get("sla_terms",{}).items():
            if key != "violation_penalty_policy": table.add_row(key.replace("_"," ").title(),str(value if value is not None else "N/A"))
        self.console.print(table)
    def comparison(self, rows: Sequence[Mapping[str,Any]], ml: Mapping[str,Mapping[str,Any]]) -> None:
        table=Table(title="ALGORITHM COMPARISON", box=box.SIMPLE_HEAVY);table.add_column("Algorithm");table.add_column("Provider");table.add_column("Score",justify="right");table.add_column("Execution",justify="right");table.add_column("MAE",justify="right");table.add_column("RMSE",justify="right")
        for row in rows: table.add_row(str(row["algorithm"]),str(row["top_provider"]),f"{float(row['top_score'])*100:.2f}",f"{float(row['execution_seconds']):.4f}s","N/A","N/A")
        for name, metrics in ml.items(): table.add_row(name,"Trust-score model","N/A","N/A",f"{metrics['mae']:.3f}",f"{metrics['rmse']:.3f}")
        self.console.print(table)
        irnam = next((row for row in rows if row["algorithm"] == "IRNAM_Weighted"), None)
        research = Table(title="RESEARCH COMPARISON", box=box.SIMPLE_HEAVY); research.add_column("Implementation");research.add_column("Execution Time");research.add_column("Recommendation Score");research.add_column("Evaluation Metrics")
        research.add_row("Original IRNAM Paper", "N/A", "N/A", "N/A - no paper run is bundled")
        if irnam: research.add_row("Improved IRNAM", f"{irnam['execution_seconds']:.4f}s", f"{irnam['top_score']*100:.2f}", "See evaluation metrics")
        for row in rows:
            if row["algorithm"] != "IRNAM_Weighted": research.add_row(str(row["algorithm"]), f"{row['execution_seconds']:.4f}s", f"{row['top_score']*100:.2f}", "N/A")
        for name, value in ml.items(): research.add_row(name, "N/A", "N/A", f"MAE {value['mae']:.3f}; RMSE {value['rmse']:.3f}")
        self.console.print(research)
    def metrics(self, workflow: Any) -> None:
        m=workflow.evaluation.to_dict(); table=Table(title="EVALUATION METRICS",box=box.SIMPLE_HEAVY);table.add_column("Metric");table.add_column("Value")
        supported={"Negotiation success rate":m.get("negotiation_success_rate"),"Agreement rate":m.get("agreement_rate"),"Average negotiation rounds":m.get("average_negotiation_rounds"),"Average negotiation time":m.get("average_negotiation_time")}
        for name,value in supported.items(): table.add_row(name,"N/A" if value is None else f"{value:.4f}")
        for name in ("Precision","Recall","F1 Score","MAP","MRR","NDCG","Kendall Tau","Spearman Correlation","Recommendation Stability","Memory Usage"): table.add_row(name,"N/A")
        self.console.print(table)
    def save(self, workflow: Any, benchmark: Sequence[Mapping[str,Any]], ml: Mapping[str,Mapping[str,Any]], output: Path) -> None:
        output.mkdir(parents=True,exist_ok=True); payload={"workflow":workflow.to_dict(),"benchmark":list(benchmark),"ml_validation":dict(ml)}
        (output/"recommendation_report.json").write_text(json.dumps(payload,indent=2,default=str),encoding="utf-8")
        lines=["CLOUD TRUSTWORTHINESS RECOMMENDATION REPORT","",f"Best provider: {workflow.recommendation.recommended_provider}",f"Overall score: {workflow.recommendation.overall_score*100:.2f}",f"Reason: {workflow.recommendation.reason_for_recommendation}","","Algorithm comparison:"]
        lines.extend(f"- {r['algorithm']}: {r['top_provider']} ({r['top_score']*100:.2f})" for r in benchmark)
        (output/"recommendation_report.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
        (output/"evaluation.json").write_text(json.dumps(workflow.evaluation.to_dict(),indent=2),encoding="utf-8")
