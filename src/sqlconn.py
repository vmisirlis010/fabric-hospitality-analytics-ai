"""SQL connection helper for the KyanosPMS Fabric SQL database (Entra token via Azure CLI)."""
import json, struct, time, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import fab, mssql_python

STATE = json.loads(fab.STATE_PATH.read_text()) if fab.STATE_PATH.exists() else {}


def connect():
    if not STATE.get("sql_server"):
        raise SystemExit("SQL database not provisioned yet - run: python src/deploy.py infra")
    tok = fab.token(fab.SQL_RES).encode("utf-16-le")
    srv = STATE["sql_server"].split(",")[0]
    cs = f"Server=tcp:{srv},1433;Database={STATE['sql_db']};Encrypt=yes;TrustServerCertificate=no;"
    for attempt in range(5):
        try:
            return mssql_python.connect(cs, attrs_before={1256: struct.pack(f"<I{len(tok)}s", len(tok), tok)})
        except Exception as e:
            if attempt == 4: raise
            print("  connect retry:", str(e)[:200]); time.sleep(10)

