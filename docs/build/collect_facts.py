"""Collect public-safe workspace facts for the documentation (table row counts, item list without IDs) -> facts1.json."""
import sys, json, struct, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import fab, mssql_python

st = json.loads(fab.STATE_PATH.read_text())
try:
    fab.lro("POST", f"/workspaces/{st['ws']}/sqlEndpoints/{st['lh_sql_endpoint_id']}/refreshMetadata", {})
except Exception as e:
    print("metadata sync:", str(e)[:200])
tok = fab.token(fab.SQL_RES).encode("utf-16-le")
con = mssql_python.connect(f"Server=tcp:{st['lh_sql_endpoint']},1433;Database=KyanosLakehouse;Encrypt=yes;",
                           attrs_before={1256: struct.pack(f"<I{len(tok)}s", len(tok), tok)})
cur = con.cursor()
cur.execute("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA IN ('pms','crm','erp','ext','gold') ORDER BY 1,2")
out = {"tables": {}}
for s, t in [tuple(r) for r in cur.fetchall()]:
    cur.execute(f"SELECT COUNT_BIG(*) FROM [{s}].[{t}]"); n = cur.fetchone()[0]
    cur.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='{t}' ORDER BY ORDINAL_POSITION")
    out["tables"][f"{s}.{t}"] = {"rows": int(n), "columns": [tuple(r) for r in cur.fetchall()]}
s, _, b = fab.http("GET", f"/workspaces/{st['ws']}/folders")
folders = {f["id"]: f["displayName"] for f in b.get("value", [])}
out["items"] = [{"type": i["type"], "name": re.sub(r"_[0-9a-f]{32}$", "_<id>", i["displayName"]), "folder": folders.get(i.get("folderId"), "(root)")} for i in fab.item_list(st["ws"])]
(pathlib.Path(__file__).parent / "facts1.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print("tables:", len(out["tables"]), "items:", len(out["items"]))
