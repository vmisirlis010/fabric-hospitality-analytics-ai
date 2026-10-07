"""Export model / report / agent / ontology / PMS metadata from the deployment code into meta.json."""
import sys, json, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import pandas as pd
import model as MD, report as RP, agent as AG, ontology as ON, load_pms as LP, notebooks as NB

meta = {}
meta["model_tables"] = []
for t, (schema, entity, desc, cols, measures) in MD.TABLES.items():
    meta["model_tables"].append({"name": t, "schema": schema, "entity": entity, "description": desc,
        "columns": [{"name": c, "type": ty, "hidden": bool(o.get("hidden")), "key": bool(o.get("key")), "sort": o.get("sort"), "category": o.get("cat"), "format": o.get("fmt")} for c, ty, o in cols],
        "measures": [{"name": m[0], "dax": m[1], "format": m[2], "folder": m[3], "description": m[4]} for m in measures]})
meta["relationships"] = [{"from_table": a, "from_col": ac, "to_table": b, "to_col": bc} for a, ac, b, bc in MD.RELS]
meta["roles"] = [{"name": "Crete Region Manager", "table": "dim_hotel", "filter": '[region] = "Crete"'},
                 {"name": "Hotel General Manager", "table": "dim_hotel", "filter": "[gm_email] = USERPRINCIPALNAME()"}]
pages = RP.build()
meta["report_pages"] = []
for p in pages:
    vis = []
    for v in p.visuals:
        vv = v["visual"]; t = None
        try: t = vv["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"].strip("'")
        except Exception: pass
        proj = []
        for role in vv.get("query", {}).get("queryState", {}).values():
            for pr in role["projections"]:
                proj.append(pr.get("displayName") or pr["nativeQueryRef"])
        if vv["visualType"] == "textbox" and not proj: continue
        vis.append({"type": vv["visualType"], "title": t, "fields": proj})
    flt = []
    for f in p.filters:
        vals = [w for w in json.dumps(f["filter"]).split('"Value": "')[1:]]
        flt.append(f'{f["field"]["Column"]["Expression"]["SourceRef"]["Entity"]}[{f["field"]["Column"]["Property"]}] = ' + ", ".join(x.split('"')[0] for x in vals))
    meta["report_pages"].append({"id": p.pid, "name": p.name, "filters": flt, "visuals": vis})
meta["theme"] = RP.THEME
meta["agent_instructions"] = AG.INSTRUCTIONS
meta["agent_measures"] = AG.TABLE_MEASURES
meta["ontology"] = {"entities": [{"name": n, "table": t, "key": k, "display": d, "properties": len(ON.SCHEMAS[t])} for n, t, k, d in ON.ENTITIES],
                    "relationships": [{"name": r[0], "source": r[1], "target": r[2], "table": r[3], "source_key": r[4], "fk": r[5]} for r in ON.RELS]}
ddl = LP.DDL
tables = {}
for m in re.finditer(r"CREATE TABLE (pms\.\w+) \((.*?)\);", ddl, re.S):
    cols = [c.strip() for c in re.split(r",\s*(?![^()]*\))", m.group(2).replace("\n", " ")) if c.strip()]
    tables[m.group(1)] = cols
meta["pms_ddl"] = tables
meta["hotels"] = pd.read_csv(ROOT / "data" / "pms_hotel.csv").to_dict("records")
meta["notebooks"] = {name: [{"kind": k, "src": s} for k, s in cells] for name, cells in
                     [("01_Ingest_Salesforce_SAP_Airports", NB.NB01), ("02_Build_Gold_Model", NB.NB02), ("03_AI_Demand_Forecast_2027", NB.NB03), ("04_Fabric_IQ_Ontology_Entities", NB.NB04)]}
(pathlib.Path(__file__).parent / "meta.json").write_text(json.dumps(meta, indent=1, default=str), encoding="utf-8")
print("tables", len(meta["model_tables"]), "measures", sum(len(t["measures"]) for t in meta["model_tables"]), "rels", len(meta["relationships"]), "pages", len(meta["report_pages"]))
