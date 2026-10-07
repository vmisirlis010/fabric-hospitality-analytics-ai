"""Collect live facts for the documentation: DAX query results, forecast metrics and per-hotel forecast summary."""
import sys, json, struct, pathlib, types, re
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import fab, mssql_python, pandas as pd, numpy as np

st = json.loads(fab.STATE_PATH.read_text())
PBI = "https://analysis.windows.net/powerbi/api"

QUERIES = [
    ("Season-to-date KPIs, 2026 vs 2025",
     "Headline KPIs for closed months (Jan–Sep) per year; validates time intelligence and the GOP join to SAP costs.",
     """EVALUATE
SUMMARIZECOLUMNS (
    dim_date[year],
    TREATAS ( { TRUE () }, dim_date[is_closed_ytd] ),
    TREATAS ( { 2025, 2026 }, dim_date[year] ),
    "Occupancy", [Occupancy %],
    "ADR", [ADR],
    "RevPAR", [RevPAR],
    "RevPAR vs LY", [RevPAR vs LY %],
    "Total Revenue", [Total Revenue],
    "GOP Margin", [GOP Margin %],
    "Direct Share", [Direct Share %]
)
ORDER BY dim_date[year]"""),
    ("Weakest hotels vs last year and airline seats",
     "Bottom three hotels by RevPAR growth with the seat change at their airport (TREATAS bridge dim_hotel → dim_airport).",
     """EVALUATE
TOPN (
    3,
    SUMMARIZECOLUMNS (
        dim_hotel[hotel_name],
        dim_hotel[airport_code],
        TREATAS ( { 2026 }, dim_date[year] ),
        TREATAS ( { TRUE () }, dim_date[is_closed_ytd] ),
        "RevPAR vs LY", [RevPAR vs LY %],
        "Occupancy vs LY (pts)", [Occupancy vs LY (pts)],
        "Airline Seat Growth", [Airline Seat Growth %]
    ),
    [RevPAR vs LY], ASC
)
ORDER BY [RevPAR vs LY] ASC"""),
    ("Guest cases at Kyanos Kos Marmari (2026)",
     "Salesforce case mix for one hotel; surfaces the air-conditioning complaint cluster.",
     """EVALUATE
TOPN (
    4,
    SUMMARIZECOLUMNS (
        fact_guest_case[sub_category],
        TREATAS ( { "Kyanos Kos Marmari" }, dim_hotel[hotel_name] ),
        TREATAS ( { 2026 }, dim_date[year] ),
        "Cases", [Guest Cases],
        "Avg CSAT", [Avg Case CSAT]
    ),
    [Cases], DESC
)
ORDER BY [Cases] DESC"""),
    ("Summer 2027 AI forecast – top movers",
     "Hotels with the largest forecast occupancy change vs 2026 and their drivers.",
     """EVALUATE
TOPN (
    5,
    SUMMARIZECOLUMNS (
        dim_hotel[hotel_name],
        "Forecast Occ", [Forecast Occupancy %],
        "2026 Occ", [Last Year Occupancy %],
        "Change (pts)", [Forecast vs LY (pts)],
        "Seat Growth", [Seat Growth at Airport %],
        "Pace vs LY", [Booking Pace vs LY (pts)]
    ),
    [Change (pts)], DESC
)
ORDER BY [Change (pts)] DESC"""),
    ("Group-level 2027 outlook",
     "Single-row summary of the forecast page cards.",
     """EVALUATE
ROW (
    "Forecast Occ 2027", [Forecast Occupancy %],
    "Actual Occ 2026", [Last Year Occupancy %],
    "On the books", [On-the-Books %],
    "Forecast Room Revenue", [Forecast Room Revenue],
    "vs 2026", [Forecast Room Revenue vs LY %]
)"""),
    ("Privilege Club tier mix (2026)",
     "Stays by Salesforce loyalty tier through dim_guest.",
     """EVALUATE
SUMMARIZECOLUMNS (
    dim_guest[loyalty_tier],
    TREATAS ( { 2026 }, dim_date[year] ),
    TREATAS ( { TRUE () }, dim_date[is_closed_ytd] ),
    "Stays", [Bookings]
)
ORDER BY [Stays] DESC"""),
    ("GOP margin by hotel concept (2026 vs 2025)",
     "Profitability by concept combining PMS revenue and SAP costs.",
     """EVALUATE
SUMMARIZECOLUMNS (
    dim_hotel[concept],
    TREATAS ( { 2026 }, dim_date[year] ),
    TREATAS ( { TRUE () }, dim_date[is_closed_ytd] ),
    "GOP Margin", [GOP Margin %],
    "GOP Margin LY", [GOP Margin % LY],
    "GOPPAR", [GOPPAR]
)
ORDER BY [GOP Margin] DESC"""),
    ("Live PMS – last 24 hours by hotel",
     "Rolling 24-hour window over the mirrored PMS table (Direct Lake, no refresh needed).",
     """EVALUATE
TOPN (
    5,
    SUMMARIZECOLUMNS (
        dim_hotel[hotel_short_name],
        "Bookings 24h", [Bookings Last 24h (live)],
        "Revenue 24h", [Booked Revenue Last 24h (live)]
    ),
    [Bookings 24h], DESC
)
ORDER BY [Bookings 24h] DESC"""),
]


def dax(q):
    s, _, b = fab.http("POST", f"https://api.powerbi.com/v1.0/myorg/groups/{st['ws']}/datasets/{st['model']}/executeQueries",
                       {"queries": [{"query": q}], "serializerSettings": {"includeNulls": True}}, res=PBI)
    if s != 200:
        return {"error": str(b)[:500]}
    rows = b["results"][0]["tables"][0]["rows"]
    return [{k.split("[")[-1].rstrip("]"): v for k, v in r.items()} for r in rows]


out = {"queries": []}
for title, purpose, q in QUERIES:
    res = dax(q)
    out["queries"].append({"title": title, "purpose": purpose, "dax": q, "result": res})
    print(title, "->", (res[:2] if isinstance(res, list) else res))

# forecast metrics: replicate notebook 03 locally on the same gold data
tok = fab.token(fab.SQL_RES).encode("utf-16-le")
con = mssql_python.connect(f"Server=tcp:{st['lh_sql_endpoint']},1433;Database=KyanosLakehouse;Encrypt=yes;",
                           attrs_before={1256: struct.pack(f"<I{len(tok)}s", len(tok), tok)})
cur = con.cursor()
def q(sql):
    cur.execute(sql); cols = [c[0] for c in cur.description]
    return pd.DataFrame([tuple(r) for r in cur.fetchall()], columns=cols)
frames = {"res": q("SELECT hotel_id, booking_date, arrival_date, nights, status, cancel_date FROM gold.fact_reservation WHERE confirmation_no NOT LIKE 'KL%'"),
          "day": q("SELECT * FROM gold.fact_hotel_day"), "hotel": q("SELECT * FROM gold.dim_hotel"), "seats": q("SELECT * FROM gold.fact_airport_seats")}
for c in ["rooms_available", "rooms_sold", "room_revenue", "extras_revenue", "total_revenue"]:
    frames["day"][c] = pd.to_numeric(frames["day"][c])
import notebooks as N
code = "\n\n".join(src for kind, src in N.NB03 if kind == "code")
code = code.replace('spark.table("gold.fact_reservation").select("hotel_id", "booking_date", "arrival_date", "nights", "status", "cancel_date").toPandas()', 'FR["res"]')
code = code.replace('spark.table("gold.fact_hotel_day").toPandas()', 'FR["day"]').replace('spark.table("gold.dim_hotel").toPandas()', 'FR["hotel"]')
code = code.replace('spark.table("gold.fact_airport_seats").toPandas()', 'FR["seats"]')
code = code.replace("import pandas as pd, numpy as np, mlflow, mlflow.sklearn\nfrom pyspark.sql import functions as F\n", "import pandas as pd, numpy as np\n")
code = code.split("score[\"forecast_occ\"]")[0]
code = code.replace('mlflow.set_experiment("kyanos-occupancy-forecast")', '')
code = code.replace('with mlflow.start_run(run_name="pace-model-summer-2027") as run:', 'if True:')
code = re.sub(r"\n    mlflow\.[^\n]*", "", code)
g = {"FR": frames}
exec(code, g)
out["forecast_metrics"] = {"train_rows": int(len(g["train"])), "score_rows": int(len(g["score"])), "mae_pts": round(g["mae"] * 100, 2),
                           "naive_mae_pts": round(g["base"] * 100, 2), "features": g["FEATURES"], "monotonic": g["MONOTONIC"], "params": g["params"]}
print(out["forecast_metrics"])
fc = q("""SELECT h.hotel_name, h.airport_code, ROUND(AVG(f.forecast_occ)*100,1) AS fc, ROUND(AVG(f.ly_occ)*100,1) AS ly,
          ROUND(AVG(f.seat_growth)*100,1) AS seats, ROUND(AVG(f.pace_vs_ly)*100,1) AS pace
          FROM gold.fact_occupancy_forecast f JOIN gold.dim_hotel h ON h.hotel_id = f.hotel_id GROUP BY h.hotel_name, h.airport_code""")
fc["delta"] = (fc.fc.astype(float) - fc.ly.astype(float)).round(1)
out["forecast_by_hotel"] = fc.sort_values("delta", ascending=False).astype(str).values.tolist()
(pathlib.Path(__file__).parent / "facts2.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
print("saved")
