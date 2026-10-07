"""Deploy the Kyanos Hotels & Resorts (fictional) Microsoft Fabric Analytics & AI demo.

Everything, in order (resumable - safe to re-run):
    python src/deploy.py all

Individual steps (same order as `all`):
    infra        workspace, schema-enabled lakehouse, Fabric SQL database (the "PMS")
    pms          create pms.* tables in the SQL database and load the generated data
    wait-mirror  wait until the SQL tables are replicated to OneLake (Delta)
    landing      upload Salesforce / SAP / airline CSVs to Files/landing
    shortcut     Tables/pms schema shortcut -> mirrored SQL tables (zero copy)
    notebooks    create / update notebooks 01-04
    run          run notebooks 01 (ingest), 02 (gold), 03 (AI forecast)
    model        Direct Lake semantic model (TMDL) + reframe
    report       Power BI report (PBIR)
    agent        Fabric data agent over the semantic model
    run-nb4      run notebook 04 (ontology entity tables)
    ontology     Fabric IQ ontology
    folders      organise the workspace into folders
    status       print item list and key row counts
Single notebook runs: run-nb1 | run-nb2 | run-nb3 | run-nb4
Config: config.json (or a file named in the KYANOS_CONFIG environment variable).
"""
import json, sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import fab
from fab import http, lro, part, ROOT, CFG

ORDER = ["infra", "pms", "wait-mirror", "landing", "shortcut", "notebooks", "run", "model", "report", "agent", "run-nb4", "ontology", "folders", "status"]
STEPS = sys.argv[1:] or ["status"]
if "all" in STEPS:
    STEPS = ORDER
unknown = [s for s in STEPS if s not in ORDER + ["run-nb1", "run-nb2", "run-nb3"]]
if unknown:
    sys.exit(f"unknown step(s): {unknown}\n{__doc__}")

STATE_F = fab.STATE_PATH
state = json.loads(STATE_F.read_text()) if STATE_F.exists() else {}
def save(): STATE_F.write_text(json.dumps(state, indent=2))

WS_NAME = CFG.get("workspaceName", "Kyanos Hotels - Analytics & AI Demo")
LH, SQLDB = "KyanosLakehouse", "KyanosPMS"
MODEL_NAME, REPORT_NAME = "Kyanos Hotels Model", "Kyanos Hotels - Commercial Performance"
AGENT_NAME, ONTO_NAME = "Kyanos Revenue & Guest Assistant", "KyanosHotelsOntology"
DATA = ROOT / "data"
PBI = "https://analysis.windows.net/powerbi/api"
PBI_API = "https://api.powerbi.com/v1.0/myorg"


def step(name):
    if name in STEPS:
        print(f"\n== {name} " + "=" * (60 - len(name)), flush=True)
        return True
    return False


def ws_id():
    s, _, b = http("GET", "/workspaces")
    ws = next((w["id"] for w in b["value"] if w["displayName"] == WS_NAME), None)
    if not ws:
        cap = CFG.get("capacityId", "")
        if not cap or set(cap.replace("-", "")) == {"0"}:
            sys.exit("config.json: set capacityId to your Fabric capacity GUID (see AGENTS.md section 2)")
        s, _, b = http("POST", "/workspaces", {"displayName": WS_NAME, "capacityId": CFG["capacityId"],
                                              "description": "Kyanos Hotels & Resorts (fictional) - unified hotel data, Power BI, forecasting and data agents on Microsoft Fabric"})
        if s not in (200, 201): raise RuntimeError(f"create workspace -> {s} {b}")
        ws = b["id"]; print("  workspace created", ws)
    return ws


WS = state.get("ws") or ws_id()
state["ws"] = WS; save()


def items(): return fab.items(WS)


def upsert(item_type, name, parts=None, fmt=None, description="", creation=None):
    ex = items().get((item_type, name))
    d = {"parts": parts} if parts else None
    if d and fmt: d["format"] = fmt
    if ex:
        if d: lro("POST", f"/workspaces/{WS}/items/{ex}/updateDefinition", {"definition": d})
        print(f"  updated {item_type:14s} {name}"); return ex
    body = {"displayName": name, "type": item_type, "description": description}
    if d: body["definition"] = d
    if creation: body["creationPayload"] = creation
    r = lro("POST", f"/workspaces/{WS}/items", body)
    iid = (r or {}).get("id") or items()[(item_type, name)]
    print(f"  created {item_type:14s} {name}  {iid}"); return iid


def onelake_put(rel_path, raw: bytes):
    base = f"https://onelake.dfs.fabric.microsoft.com/{WS}/{state['lh']}/{rel_path}"
    for m, u, data, hdr in [("PUT", f"{base}?resource=file", b"", {}),
                            ("PATCH", f"{base}?action=append&position=0", raw, {"Content-Type": "application/octet-stream"}),
                            ("PATCH", f"{base}?action=flush&position={len(raw)}", b"", {})]:
        s, _, b = http(m, u, res=fab.STORAGE, raw=data, headers={"x-ms-version": "2021-08-06", **hdr}, timeout=600)
        if s not in (200, 201, 202): raise RuntimeError(f"onelake {m} {rel_path} -> {s} {b}")


def onelake_exists(item_id, rel_dir):
    s, _, b = http("GET", f"https://onelake.dfs.fabric.microsoft.com/{WS}?resource=filesystem&recursive=false&directory={item_id}/{rel_dir}",
                   res=fab.STORAGE, headers={"x-ms-version": "2021-08-06"})
    return s == 200 and isinstance(b, dict) and len(b.get("paths", [])) > 0


def run_notebook(nb_id, timeout=2400):
    for attempt in range(3):
        s, h, b = http("POST", f"/workspaces/{WS}/items/{nb_id}/jobs/instances?jobType=RunNotebook", {})
        if s == 202: break
        print(f"  start notebook -> {s}, retrying"); time.sleep(30)
    else:
        raise RuntimeError(f"run notebook -> {s} {b}")
    loc, t0 = h["Location"], time.time()
    while time.time() - t0 < timeout:
        time.sleep(20)
        st = http("GET", loc)[2]
        if isinstance(st, dict) and st.get("status") in ("Completed", "Failed", "Cancelled", "Deduped"):
            return st
    raise RuntimeError("notebook timeout")


def refresh_model(mid, wait=900):
    s, h, b = http("POST", f"{PBI_API}/groups/{WS}/datasets/{mid}/refreshes", {"type": "full"}, res=PBI)
    if s not in (200, 202): raise RuntimeError(f"refresh -> {s} {b}")
    t0 = time.time()
    while time.time() - t0 < wait:
        time.sleep(8)
        s, _, b = http("GET", f"{PBI_API}/groups/{WS}/datasets/{mid}/refreshes?$top=1", res=PBI)
        st = b["value"][0] if isinstance(b, dict) and b.get("value") else {}
        if st.get("status") in ("Completed", "Failed", "Disabled", "Cancelled"):
            return st
    return {"status": "timeout"}


# ---------------------------------------------------------------- steps
if step("infra"):
    if not state.get("lh"):
        state["lh"] = upsert("Lakehouse", LH, description="Kyanos unified lakehouse: PMS (shortcut), Salesforce CRM, SAP ERP, airport seat capacity, gold model",
                             creation={"enableSchemas": True})
    if not state.get("sqldb"):
        state["sqldb"] = upsert("SQLDatabase", SQLDB, description="Stand-in for the on-premises PMS / SQL Server data warehouse. Replicated to OneLake automatically (Mirroring).")
    save()
    for _ in range(60):
        s, _, b = http("GET", f"/workspaces/{WS}/sqlDatabases/{state['sqldb']}")
        props = (b or {}).get("properties", {}) if isinstance(b, dict) else {}
        if props.get("serverFqdn") and props.get("databaseName"):
            state["sql_server"], state["sql_db"] = props["serverFqdn"], props["databaseName"]
            break
        time.sleep(10)
    for _ in range(60):
        s, _, b = http("GET", f"/workspaces/{WS}/lakehouses/{state['lh']}")
        sep = b["properties"].get("sqlEndpointProperties") or {}
        if sep.get("connectionString") and sep.get("id"):
            state["lh_sql_endpoint"], state["lh_sql_endpoint_id"] = sep["connectionString"], sep["id"]
            break
        time.sleep(10)
    save()
    print(json.dumps({k: state.get(k) for k in ["ws", "lh", "sqldb", "sql_server", "sql_db", "lh_sql_endpoint"]}, indent=1))

if step("pms"):
    if not (DATA / "pms_reservation.parquet").exists():
        sys.exit("data/ is empty - run: python src/gen_data.py")
    import load_pms
    load_pms.main()

if step("wait-mirror"):
    t0 = time.time()
    while time.time() - t0 < 900:
        ready = [t for t in ["Hotel", "RoomType", "Guest", "Reservation"] if onelake_exists(state["sqldb"], f"Tables/pms/{t}/_delta_log")]
        print(f"  mirrored tables in OneLake: {ready}", flush=True)
        if len(ready) == 4: break
        time.sleep(20)
    else:
        sys.exit("mirroring did not complete within 15 minutes")

LANDING = {"salesforce_privilege_club_members.csv": "Files/landing/salesforce/privilege_club_members.csv",
           "salesforce_guest_cases.csv": "Files/landing/salesforce/guest_cases.csv",
           "sap_hotel_costs_monthly.csv": "Files/landing/sap/hotel_costs_monthly.csv",
           "airport_seat_capacity_weekly.csv": "Files/landing/external/airport_seat_capacity_weekly.csv"}

if step("landing"):
    for src, dst in LANDING.items():
        onelake_put(dst, (DATA / src).read_bytes()); print("  uploaded", dst)

if step("shortcut"):
    body = {"path": "Tables", "name": "pms", "target": {"oneLake": {"workspaceId": WS, "itemId": state["sqldb"], "path": "Tables/pms"}}}
    s, _, b = http("POST", f"/workspaces/{WS}/items/{state['lh']}/shortcuts?shortcutConflictPolicy=CreateOrOverwrite", body)
    print("  schema shortcut Tables/pms ->", s)
    if s not in (200, 201):
        print("  schema shortcut failed, creating table shortcuts:", str(b)[:300])
        for t in ["Hotel", "RoomType", "Guest", "Reservation"]:
            body = {"path": "Tables/pms", "name": t, "target": {"oneLake": {"workspaceId": WS, "itemId": state["sqldb"], "path": f"Tables/pms/{t}"}}}
            s, _, b = http("POST", f"/workspaces/{WS}/items/{state['lh']}/shortcuts?shortcutConflictPolicy=CreateOrOverwrite", body)
            print("  table shortcut", t, s, "" if s in (200, 201) else str(b)[:200])

NOTEBOOKS = [("nb1", "01_Ingest_Salesforce_SAP_Airports"), ("nb2", "02_Build_Gold_Model"), ("nb3", "03_AI_Demand_Forecast_2027"),
             ("nb4", "04_Fabric_IQ_Ontology_Entities")]

if step("notebooks"):
    import notebooks as N
    cells = {"nb1": N.NB01, "nb2": N.NB02, "nb3": N.NB03, "nb4": N.NB04}
    for key, name in NOTEBOOKS:
        for _, src in cells[key]:
            pass
        state[key] = upsert("Notebook", name, [part("notebook-content.py", N.notebook(cells[key], WS, state["lh"], LH))], "fabricGitSource")
    save()

for key, name in NOTEBOOKS:
    if (key != "nb4" and "run" in STEPS) or f"run-{key}" in STEPS:
        print(f"\n== run {name}", flush=True)
        t0 = time.time()
        st = run_notebook(state[key])
        print(f"  {st.get('status')} in {time.time() - t0:.0f}s", st.get("failureReason") or "")
        if st.get("status") != "Completed": sys.exit(f"{name} failed - open the notebook run in Fabric (Monitor) for the cell error")

if step("model"):
    import model as MD
    state["model"] = upsert("SemanticModel", MODEL_NAME, MD.model_parts(WS, state["lh"]), "TMDL",
                            description="Direct Lake model over the Kyanos gold layer + live PMS table. Measures: Occupancy, ADR, RevPAR, GOP, pace, forecast.")
    save()
    st = refresh_model(state["model"])
    print("  reframe:", st.get("status"), str(st.get("serviceExceptionJson") or "")[:800])

if step("report"):
    import report as RP
    state["report"] = upsert("Report", REPORT_NAME, RP.report_parts(state["model"], REPORT_NAME),
                             description="Executive overview, hotel scorecard, channels & guests, Summer 2027 AI outlook, live PMS feed.")
    save()

if step("agent"):
    import agent as AG, model as MD
    state["agent"] = upsert("DataAgent", AGENT_NAME, AG.agent_parts(WS, state["model"], MD.TABLES),
                            description="Ask in Greek or English about occupancy, ADR, RevPAR, GOP, channels, guests, complaints, 2027 forecast and live PMS bookings.")
    save()

if step("ontology"):
    import ontology as ON
    try:
        state["onto"] = upsert("Ontology", ONTO_NAME, ON.ontology_parts(WS, state["lh"], True),
                               description="Fabric IQ ontology: hotels, airports, VIP guests, upcoming stays, open cases, tour operators")
    except Exception as e:
        print("  ontology with display names failed, retrying without:", str(e)[:400])
        state["onto"] = upsert("Ontology", ONTO_NAME, ON.ontology_parts(WS, state["lh"], False))
    save()

FOLDERS = {"1 Sources PMS on SQL": [("SQLDatabase", SQLDB)],
           "2 OneLake unified data": [("Lakehouse", LH), ("Notebook", NOTEBOOKS[0][1]), ("Notebook", NOTEBOOKS[1][1])],
           "3 AI forecasting": [("Notebook", NOTEBOOKS[2][1]), ("MLExperiment", "kyanos-occupancy-forecast"), ("MLModel", "kyanos-occupancy-forecast")],
           "4 Power BI": [("SemanticModel", MODEL_NAME), ("Report", REPORT_NAME)],
           "5 Agents and Fabric IQ": [("DataAgent", AGENT_NAME), ("Ontology", ONTO_NAME), ("Notebook", NOTEBOOKS[3][1])]}

if step("folders"):
    s, _, b = http("GET", f"/workspaces/{WS}/folders")
    existing = {f["displayName"]: f["id"] for f in (b.get("value", []) if isinstance(b, dict) else [])}
    idx = {(i["type"], i["displayName"]): i for i in fab.item_list(WS)}
    for name, members in FOLDERS.items():
        fid = existing.get(name)
        if not fid:
            s, _, b = http("POST", f"/workspaces/{WS}/folders", {"displayName": name})
            fid = b.get("id") if isinstance(b, dict) else None
            if not fid: print("  folder", name, s, str(b)[:200]); continue
        for key in members:
            it = idx.get(key)
            if not it: print("  (missing)", key[1]); continue
            if it.get("folderId") == fid: continue
            s, _, b = http("POST", f"/workspaces/{WS}/items/{it['id']}/move", {"targetFolderId": fid})
            print(f"  {name:24s} <- {key[1]}", "" if s in (200, 202) else f"{s} {str(b)[:150]}")

if step("status"):
    for i in sorted(fab.item_list(WS), key=lambda i: (i["type"], i["displayName"])):
        print(f"  {i['type']:16s} {i['displayName']}")
    if state.get("model"):
        q = "EVALUATE ROW(\"reservations\", [PMS Reservations (live)], \"revenue_2026\", CALCULATE([Total Revenue], dim_date[year] = 2026), \"forecast_occ_2027\", [Forecast Occupancy %])"
        s, _, b = http("POST", f"{PBI_API}/groups/{WS}/datasets/{state['model']}/executeQueries", {"queries": [{"query": q}]}, res=PBI)
        print("  model check:", b["results"][0]["tables"][0]["rows"] if s == 200 else f"{s} {str(b)[:300]}")
    print(f"\n  workspace: https://app.fabric.microsoft.com/groups/{WS}/list")
    if state.get("report"):
        print(f"  report:    https://app.fabric.microsoft.com/groups/{WS}/reports/{state['report']}")
    if state.get("agent"):
        print(f"  agent:     https://app.fabric.microsoft.com/groups/{WS}/aiskills/{state['agent']}")

