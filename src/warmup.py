"""Pre-demo warm-up: frame the Direct Lake model, sync the lakehouse SQL endpoint, and run a few DAX queries so first clicks are fast."""
import json, sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import fab

st = json.loads(fab.STATE_PATH.read_text())
PBI, API = "https://analysis.windows.net/powerbi/api", "https://api.powerbi.com/v1.0/myorg"

s, _, _ = fab.http("POST", f"{API}/groups/{st['ws']}/datasets/{st['model']}/refreshes", {"type": "full"}, res=PBI)
print("model reframe requested:", s)
try:
    fab.lro("POST", f"/workspaces/{st['ws']}/sqlEndpoints/{st['lh_sql_endpoint_id']}/refreshMetadata", {})
    print("lakehouse SQL endpoint metadata synced")
except Exception as e:
    print("SQL endpoint sync:", str(e)[:200])
time.sleep(30)
for q in ["EVALUATE ROW(\"rev\", [Total Revenue], \"occ\", [Occupancy %], \"revpar\", [RevPAR])",
          "EVALUATE ROW(\"fc\", [Forecast Occupancy %], \"live\", [PMS Reservations (live)], \"today\", [Bookings Last 24h (live)])"]:
    s, _, b = fab.http("POST", f"{API}/groups/{st['ws']}/datasets/{st['model']}/executeQueries", {"queries": [{"query": q}]}, res=PBI)
    print("warm query:", s, b["results"][0]["tables"][0]["rows"] if s == 200 else str(b)[:300])
