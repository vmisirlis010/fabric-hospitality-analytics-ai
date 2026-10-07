# AGENTS.md – runbook for coding agents

This file tells an AI coding agent (or a human) exactly how to deploy, verify, change and operate this demo. Every step is scripted and idempotent, so **no portal clicks are required**.

## 1. Goal and success criteria

The goal is to deploy the *Kyanos Hotels & Resorts* Microsoft Fabric demo into a new workspace.

Deployment is successful when `python src/deploy.py status` prints:
- **17 items**: SQLDatabase, Lakehouse ×2, Notebook ×4, MLExperiment, MLModel, SemanticModel, Report, DataAgent, Ontology, GraphModel and SQLEndpoint ×3;
- a model check like this:

```
model check: [{'[reservations]': 482961, '[revenue_2026]': 418613919.27, '[forecast_occ_2027]': 0.8598}]
```

`reservations` goes up once the live simulator has run. `forecast_occ_2027` may differ in the 3rd decimal between scikit-learn versions.

## 2. Prerequisites – check before starting

| Check | Command | Expected |
|---|---|---|
| Python ≥ 3.10 | `python --version` | 3.10 – 3.14 |
| Python packages | `pip install -r requirements.txt` | installs pandas, numpy, pyarrow, mssql-python |
| Azure CLI signed in | `az account show --query "{tenant:tenantId, user:user.name}"` | the target tenant |
| Fabric token | `az account get-access-token --resource https://api.fabric.microsoft.com --query expiresOn` | a timestamp (no error) |
| Fabric capacity ID | `az rest --method get --url https://api.fabric.microsoft.com/v1/capacities --resource https://api.fabric.microsoft.com --query "value[?state=='Active'].{name:displayName,id:id,sku:sku}"` | at least one **Active** F-SKU (F2+) |

The deploying identity needs permission to create workspaces on that capacity. The tenant settings for SQL database, Copilot / Azure OpenAI, data agent and Ontology must be enabled; if they are not, the `agent` or `ontology` step fails with a clear 4xx error.

## 3. Configure

```powershell
Copy-Item config.example.json config.json
```

Edit `config.json`:

| Key | Required | Meaning |
|---|---|---|
| `capacityId` | yes | GUID of the Fabric capacity |
| `workspaceName` | no | Default `Kyanos Hotels - Analytics & AI Demo`. An existing workspace with this name is reused. |
| `subscription` | no | Azure subscription name or ID, used to pick the tenant for `az account get-access-token` |
| `tenantId` | no | Alternative to `subscription` |
| `stateFile` | no | Default `.state.json`. Stores the IDs of the deployed items; use a different file per workspace. |

To deploy a second copy side by side, create e.g. `config.test.json` with another `workspaceName` and `stateFile`, and run with the environment variable `KYANOS_CONFIG=<path to config.test.json>`.

## 4. Deploy

```powershell
python src/gen_data.py          # ~40 s; writes data/*.parquet|csv (deterministic, seed 20261007)
python src/deploy.py all        # ~20 min on F4; prints a header per step
```

Expected step output and timings (from a clean test run on an F4):

| Step | Expect | Typical time |
|---|---|---|
| `infra` | `workspace created`, `created Lakehouse KyanosLakehouse`, `created SQLDatabase KyanosPMS` | 1–2 min |
| `pms` | `pms.Guest: 255,848 rows`, `pms.Reservation: 482,961 rows`, `check: 482961` | 6 min |
| `wait-mirror` | `mirrored tables in OneLake: ['Hotel', 'RoomType', 'Guest', 'Reservation']` | seconds |
| `landing` | 4 × `uploaded Files/landing/...` | < 1 min |
| `shortcut` | `schema shortcut Tables/pms -> 201` | seconds |
| `notebooks` | 4 × `created Notebook ...` | < 1 min |
| `run` | `Completed` for 01, 02, 03 (and 04) | 1–3 min each |
| `model` | `created SemanticModel Kyanos Hotels Model`, `reframe: Completed` | 1 min |
| `report`, `agent`, `ontology` | `created ...` | < 1 min each |
| `folders`, `status` | folder moves, item list, model check (see §1) | < 1 min |

The deployment is **resumable**. If a step fails, fix the cause and re-run just that step and the ones after it, e.g. `python src/deploy.py model report agent run-nb4 ontology folders status`. Re-running `pms` **drops and reloads** the PMS tables, which also deletes live simulator bookings.

## 5. Verify (optional deeper checks)

```powershell
python src/warmup.py                 # reframes the model, syncs the SQL endpoint, prints two KPI queries
./demo-control.ps1 burst 5 KYN-OLY   # writes 5 bookings; they should appear in the model within ~15 s
```

DAX check through the Power BI REST API (IDs are in the state file):

```python
import sys, json; sys.path.insert(0, "src"); import fab
st = json.loads(fab.STATE_PATH.read_text())
q = 'EVALUATE ROW("bookings24h", [Bookings Last 24h (live)], "occ2026", CALCULATE([Occupancy %], dim_date[year]=2026, dim_date[is_closed_ytd]))'
print(fab.http("POST", f"https://api.powerbi.com/v1.0/myorg/groups/{st['ws']}/datasets/{st['model']}/executeQueries",
               {"queries": [{"query": q}]}, res="https://analysis.windows.net/powerbi/api")[2])
```

Expected: `occ2026 ≈ 0.843`.

## 6. How the code is organised

| File | Responsibility |
|---|---|
| `src/fab.py` | Config loading (`KYANOS_CONFIG`), Azure CLI tokens per audience, `http()` with retry, `lro()` for long-running operations, `get_definition()` |
| `src/deploy.py` | Ordered, idempotent steps (`ORDER` list). `upsert()` creates an item or calls `updateDefinition` |
| `src/gen_data.py` | All synthetic data and the built-in business stories |
| `src/load_pms.py` / `src/sqlconn.py` | PMS DDL and loader; Entra-token TDS connection (`attrs_before={1256: token}`) |
| `src/notebooks.py` | Notebook cells (`NB01`–`NB04`) rendered to Fabric git format |
| `src/model.py` | `TABLES` (columns, measures with DAX, format, folder, description), `RELS`, RLS roles → TMDL parts |
| `src/report.py` | `build()` returns pages and visuals; `report_parts()` → PBIR parts + custom theme |
| `src/agent.py` | Data agent instructions + `semantic_model` data source (draft + published) |
| `src/ontology.py` | Entity types, lakehouse bindings (schema `gold`), relationships |
| `src/pms_live_sim.py` | Live simulator (`run`, `burst`, `status`, `reset`) |
| `docs/build/` | `collect.py` (DAX results), `collect_facts.py` (row counts), `export_meta.py`, `diagrams.py`, `build_docs.js` (Word document) |

## 7. Making changes safely

- **Add or change a measure:** edit `TABLES` in `src/model.py`.
  - Measure names must not clash (case-insensitively) with a column name in the same table.
  - Use `DIVIDE(x - LY, LY)` for growth measures.
  - Then run `python src/deploy.py model` and validate with a DAX query.
- **Add a report visual:** edit `build()` in `src/report.py`, using the `Page.add` / `Page.kpi` helpers and existing role names (`Category`, `Y`, `Values`, `Series`, `X`, `Size`, `Group`, `Rows`). Then run `python src/deploy.py report` and **hard-reload** the browser.
- **Change notebook code:**
  1. Edit `src/notebooks.py` and keep every cell at column 0 indentation.
  2. Compile-check: `python -c "import sys; sys.path.insert(0,'src'); import notebooks as N; [compile(s,'c','exec') for nb in (N.NB01,N.NB02,N.NB03,N.NB04) for k,s in nb if k=='code']"`.
  3. Run `python src/deploy.py notebooks run-nb2` (or the affected notebook), followed by `model` if gold columns changed.
- **Change data:** edit `src/gen_data.py`, then run `python src/gen_data.py`, followed by `python src/deploy.py pms wait-mirror landing run model`.
- **Never commit** `config.json`, `.state*.json`, `data/` or `docs/private/` – they are git-ignored.

## 8. Known pitfalls (already handled – keep them handled)

| Pitfall | Handling |
|---|---|
| `mssql-python` `bulkcopy` opens a second connection without the Entra token | Loader uses `executemany` in 20K batches |
| Duplicate Privilege Club IDs between Salesforce and the PMS break the many-to-one relationship to `dim_guest` | Notebook 02 de-duplicates members and guests |
| Airline seats do not react to hotel filters (single-direction snowflake) | `TREATAS(VALUES(dim_hotel[airport_code]), dim_airport[airport_code])` |
| `TODAY()` filters empty the live page on a new day | Rolling 24-hour window with `NOW() - 1` and `COALESCE(…, 0)` |
| Lakehouse SQL endpoint metadata sync is lazy for shortcut tables | Direct Lake is unaffected; `warmup` calls `refreshMetadata` |
| Workspace folder names reject `·`, `&`, `.` and `-` | Folder names use letters, digits and spaces only |
| Ontology child items (lakehouse, graph) cannot be moved alone | They move with the ontology |

## 9. Operating the demo

```powershell
./demo-control.ps1 warmup | start | burst [N] [HOTELCODE] | status | stop | reset
```

Hotel codes look like `KYN-OLY`, `KYN-ELO`, `KYN-MAR` (see `data/pms_hotel.csv`). The talk track is in `docs/DEMO_SCRIPT.md`.

## 10. Clean up

Delete the workspace (this removes every item, including the SQL database):

```python
import sys, json; sys.path.insert(0, "src"); import fab
st = json.loads(fab.STATE_PATH.read_text()); print(fab.http("DELETE", f"/workspaces/{st['ws']}")[0])
```

Then delete the state file.
