
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any
from ...core.config import DATA, ensure_data_dirs
import csv, re, json
from pathlib import Path

router = APIRouter()
ensure_data_dirs()

REG_DIR = DATA / "registry"
REG_DIR.mkdir(parents=True, exist_ok=True)
PROJ_CSV = REG_DIR / "Project_Registry.csv"
TEAM_CSV = REG_DIR / "Team_Assignments.csv"
INDEX_JSON = REG_DIR / "index.json"

def read_csv(p: Path) -> List[Dict[str,str]]:
    if not p.exists(): return []
    with p.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def to_family(name: str) -> str:
    s = (name or "").lower()
    if any(k in s for k in ["bop","boppers","boppin","boppoed"]): return "BOP Family"
    if any(k in s for k in ["lazylarry","laziest","larry"]): return "LazyLarry Family"
    if "propulse" in s: return "Propulse Family"
    if "youtube" in s: return "YouTube Automations"
    if any(k in s for k in ["command","commander","iws","intelliwealth","autonomax","aimm","money-machine","global ai"]): return "Core Platforms"
    return "Experiments/Misc"

def bucket_pct(v: str) -> str:
    try: x = float(v)
    except: return "Unspecified"
    if x >= 90: return "90–100%"
    if x >= 70: return "70–89%"
    if x >= 40: return "40–69%"
    if x > 0:  return "1–39%"
    return "0%"

@router.get("/projects")
def projects() -> Dict[str, Any]:
    rows = read_csv(PROJ_CSV)
    groups = {"BOP Family":[], "LazyLarry Family":[], "Propulse Family":[],
              "YouTube Automations":[], "Core Platforms":[], "Experiments/Misc":[]}
    for r in rows:
        groups[to_family(r.get("name",""))].append(r)
    return {"count": len(rows), "items": rows, "groups": groups}

class PatchRow(BaseModel):
    project_id: str
    updates: Dict[str, str]

@router.post("/projects/patch")
def patch_row(req: PatchRow):
    rows = read_csv(PROJ_CSV)
    if not rows: raise HTTPException(404, "Registry empty or missing")
    idx = next((i for i,r in enumerate(rows) if r.get("project_id")==req.project_id), None)
    if idx is None: raise HTTPException(404, "Not found")
    rows[idx].update({k:str(v) for k,v in req.updates.items()})
    headers = list(rows[0].keys())
    with PROJ_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers); w.writeheader(); w.writerows(rows)
    return {"ok": True, "updated": rows[idx]}

@router.get("/projects/summary")
def summary():
    rows = read_csv(PROJ_CSV)
    fams = {}; chans = {}; cats = {}; status_buckets = {}; complete_buckets = {}
    for r in rows:
        fam = to_family(r.get("name","")); fams[fam] = fams.get(fam,0)+1
        channel = r.get("channel","") or "unspecified"; chans[channel] = chans.get(channel,0)+1
        cat = r.get("category","") or "unspecified"; cats[cat] = cats.get(cat,0)+1
        st = r.get("status","") or "unspecified"; status_buckets[st] = status_buckets.get(st,0)+1
        complete_buckets[bucket_pct(r.get("percent_complete",""))] = complete_buckets.get(bucket_pct(r.get("percent_complete","")),0)+1
    return {"families":fams,"channels":chans,"categories":cats,"status":status_buckets,"completion":complete_buckets,"total":len(rows)}

def tokenize_tasks(r: Dict[str,str]):
    tasks = []; seq = 1
    for key in ("tasks","actions","steps"):
        txt = r.get(key,"") or ""
        for line in txt.splitlines():
            s = line.strip().lstrip("-•").strip()
            if not s: continue
            verb = re.findall(r'^[A-Za-z]+', s)
            verb = (verb[0].lower() if verb else "do")
            code = f"T{seq:02d}_{verb}"
            tasks.append({"id": code, "title": s}); seq += 1
    return tasks

@router.get("/wbs")
def wbs(project_id: str = Query(..., description="Project ID from registry")):
    rows = read_csv(PROJ_CSV)
    target = next((r for r in rows if r.get("project_id")==project_id), None)
    if not target: raise HTTPException(404, "Project not found")
    nodes = []; edges = []
    nodes.append({"id": project_id, "label": target.get("name","Project")})
    phases = ["Pre-Dev/Hunting","Discovery","Offer Design","Asset Creation","Channel Packaging","Launch","Optimize"]
    for i,p in enumerate(phases, start=1):
        nid = f"P{i}"; nodes.append({"id":nid,"label":p}); edges.append({"from":project_id,"to":nid})
    tasks = tokenize_tasks(target)
    for t in tasks[:4]:  nodes.append({"id":t["id"],"label":t["title"]}); edges.append({"from":"P3","to":t["id"]})
    for t in tasks[4:8]: nodes.append({"id":t["id"],"label":t["title"]}); edges.append({"from":"P4","to":t["id"]})
    for t in tasks[8:12]:nodes.append({"id":t["id"],"label":t["title"]}); edges.append({"from":"P6","to":t["id"]})
    return {"project":{"id": project_id, "name": target.get("name")}, "nodes": nodes, "edges": edges}

# -------- Indexer & Team Endpoints --------

@router.get("/index/build")
def build_index() -> Dict[str, Any]:
    prows = read_csv(PROJ_CSV)
    if not prows: raise HTTPException(404, "Project_Registry.csv missing or empty")
    idx = []
    for r in prows:
        doc = {
            "project_id": r.get("project_id"),
            "name": r.get("name"),
            "family": to_family(r.get("name","")),
            "channel": r.get("channel",""),
            "category": r.get("category",""),
            "status": r.get("status",""),
            "percent_complete": r.get("percent_complete",""),
            "mission": r.get("mission",""),
            "strategies": r.get("strategies",""),
            "goals": r.get("goals",""),
            "tasks": r.get("tasks",""),
            "actions": r.get("actions",""),
            "steps": r.get("steps",""),
            "evidence_refs": r.get("evidence_refs",""),
        }
        # simple combined text for keyword search
        doc["text"] = " ".join([doc[k] for k in ["mission","strategies","goals","tasks","actions","steps"] if doc.get(k)])
        idx.append(doc)
    INDEX_JSON.write_text(json.dumps({"count": len(idx), "items": idx}, ensure_ascii=False, indent=2))
    return {"ok": True, "wrote": str(INDEX_JSON), "count": len(idx)}

@router.get("/index")
def get_index() -> Dict[str, Any]:
    if not INDEX_JSON.exists(): return {"count": 0, "items": []}
    try:
        return json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {"count": 0, "items": []}

@router.get("/team")
def team(project_id: str = Query(...)):
    rows = read_csv(TEAM_CSV)
    if not rows: return {"project_id": project_id, "members": []}
    members = [r for r in rows if r.get("project_id")==project_id]
    return {"project_id": project_id, "members": members}
