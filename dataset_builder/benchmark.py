"""Schema-inferred benchmark dataset builder for the canonical CSV source."""
from __future__ import annotations
import csv, json, hashlib
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any

def _coerce(value: str) -> Any:
    value=value.strip()
    if not value: return None
    if value.lower() in {"true","false"}: return value.lower()=="true"
    try:return float(value) if "." in value or "e" in value.lower() else int(value)
    except ValueError:return value

def build_benchmark_dataset(source: Path | str, output_dir: Path | str) -> dict[str, Any]:
    """Validate and export any tabular benchmark without schema-specific code."""
    source, output=Path(source),Path(output_dir); output.mkdir(parents=True,exist_ok=True)
    with source.open(encoding="utf-8",newline="") as handle:
        reader=csv.DictReader(handle); fields=reader.fieldnames or []; rows=[{k:_coerce(v or "") for k,v in row.items()} for row in reader]
    if not fields or not rows: raise ValueError("Benchmark dataset must contain a header and at least one row")
    issues=[]
    for i,row in enumerate(rows,2):
        if not any(row.values()): issues.append({"row":i,"severity":"error","message":"empty row"})
    numeric={field:[row[field] for row in rows if isinstance(row[field],(int,float)) and not isinstance(row[field],bool)] for field in fields}
    schema={field:{"type":"number" if values else "boolean" if all(isinstance(row[field],bool) or row[field] is None for row in rows) else "string","missing_count":sum(row[field] is None for row in rows),"direction":"cost" if any(x in field.lower() for x in ("cost","latency","response","loss","violation")) else "benefit"} for field,values in numeric.items()}
    stats={field:{"min":min(values),"max":max(values),"mean":mean(values),"median":median(values)} for field,values in numeric.items() if values}
    (output/"cloud_dataset.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
    (output/"dataset_statistics.json").write_text(json.dumps(stats,indent=2),encoding="utf-8")
    report={"source":str(source),"generated_at":datetime.now(timezone.utc).isoformat(),"row_count":len(rows),"schema":schema,"validation_issues":issues,"valid":not any(x["severity"]=="error" for x in issues),"sha256":hashlib.sha256(source.read_bytes()).hexdigest()}
    (output/"dataset_metadata.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    (output/"validation_report.json").write_text(json.dumps({"issues":issues,"valid":report["valid"]},indent=2),encoding="utf-8")
    (output/"preprocessing_log.json").write_text(json.dumps({"operations":["read_csv","coerce_types","infer_schema","validate","export_json"],"missing_values":{f:s["missing_count"] for f,s in schema.items()}},indent=2),encoding="utf-8")
    return report
