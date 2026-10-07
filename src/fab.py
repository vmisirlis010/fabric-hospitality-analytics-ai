"""Minimal Fabric REST helper (Azure CLI auth) for the Kyanos Hotels demo."""
import base64, json, os, subprocess, time, urllib.request, urllib.error, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG_PATH = pathlib.Path(os.environ.get("KYANOS_CONFIG", ROOT / "config.json"))
if not CFG_PATH.exists():
    raise SystemExit(f"{CFG_PATH} not found - copy config.example.json to config.json and set capacityId")
CFG = json.loads(CFG_PATH.read_text(encoding="utf-8"))
SUB = CFG.get("subscription") or None
TENANT = CFG.get("tenantId") or None
STATE_PATH = ROOT / CFG.get("stateFile", ".state.json")
API = "https://api.fabric.microsoft.com/v1"
FABRIC = "https://api.fabric.microsoft.com"
SQL_RES = "https://database.windows.net/"
STORAGE = "https://storage.azure.com/"

_tok = {}


def token(res=FABRIC):
    """Azure CLI token for the given audience (refreshed every 25 minutes)."""
    t = _tok.get(res)
    if not t or time.time() - t[1] > 1500:
        cmd = ["az", "account", "get-access-token", "--resource", res, "--query", "accessToken", "-o", "tsv"]
        if SUB:
            cmd += ["--subscription", SUB]
        elif TENANT:
            cmd += ["--tenant", TENANT]
        v = subprocess.check_output(cmd, shell=(os.name == "nt"), text=True).strip()
        _tok[res] = (v, time.time())
    return _tok[res][0]


def http(method, url, body=None, res=FABRIC, raw=None, headers=None, timeout=180):
    if not url.startswith("http"):
        url = API + url
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    h = {"Authorization": f"Bearer {token(res)}"}
    if raw is None:
        h["Content-Type"] = "application/json"
    if headers:
        h.update(headers)
    for attempt in range(6):
        req = urllib.request.Request(url, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                txt = r.read().decode("utf-8", "replace")
                try:
                    js = json.loads(txt) if txt else None
                except json.JSONDecodeError:
                    js = txt
                return r.status, dict(r.headers), js
        except urllib.error.HTTPError as e:
            txt = e.read().decode("utf-8", "replace")
            if e.code == 429 or (e.code >= 500 and attempt < 3):
                time.sleep(int(e.headers.get("Retry-After", 10)) if e.code == 429 else 5)
                continue
            return e.code, dict(e.headers), txt
    return 599, {}, "retries exhausted"


def lro(method, url, body=None, wait=900):
    s, h, b = http(method, url, body)
    if s in (200, 201):
        return b
    if s != 202:
        raise RuntimeError(f"{method} {url} -> {s} {str(b)[:1500]}")
    loc = h.get("Location") or h.get("location")
    t0 = time.time()
    while time.time() - t0 < wait:
        time.sleep(min(int(h.get("Retry-After", 3) or 3), 10))
        s2, _, st = http("GET", loc)
        status = st.get("status") if isinstance(st, dict) else None
        if status == "Succeeded":
            s3, _, res = http("GET", loc.rstrip("/") + "/result")
            return res if s3 == 200 else st
        if status in ("Failed", "Cancelled"):
            raise RuntimeError(f"LRO failed: {json.dumps(st)[:1500]}")
        if s2 == 200 and status is None and isinstance(st, dict) and "id" in st:
            return st
    raise RuntimeError("LRO timeout")


def b64(content):
    if not isinstance(content, (str, bytes)):
        content = json.dumps(content, indent=2, ensure_ascii=False)
    if isinstance(content, str):
        content = content.encode("utf-8")
    return base64.b64encode(content).decode()


def part(path, content):
    return {"path": path, "payload": b64(content), "payloadType": "InlineBase64"}


def get_definition(ws, item_id, fmt=None):
    url = f"/workspaces/{ws}/items/{item_id}/getDefinition" + (f"?format={fmt}" if fmt else "")
    res = lro("POST", url)
    out = {}
    for p in res["definition"]["parts"]:
        out[p["path"]] = base64.b64decode(p["payload"]).decode("utf-8", "replace")
    return out


def items(ws):
    s, _, b = http("GET", f"/workspaces/{ws}/items")
    return {(i["type"], i["displayName"]): i["id"] for i in b["value"]}


def item_list(ws):
    return http("GET", f"/workspaces/{ws}/items")[2]["value"]
