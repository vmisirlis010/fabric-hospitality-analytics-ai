"""Notebook sources for the Kyanos demo (Fabric git format)."""
import json

AS_OF = "2026-10-06"


def notebook(cells, ws, lh, lh_name):
    dep = {"lakehouse": {"default_lakehouse": lh, "default_lakehouse_name": lh_name, "default_lakehouse_workspace_id": ws,
                         "known_lakehouses": [{"id": lh}]}}
    meta = json.dumps({"kernel_info": {"name": "synapse_pyspark"}, "dependencies": dep}, indent=2)
    out = ["# Fabric notebook source\n", "# METADATA ********************\n", "\n".join("# META " + l for l in meta.splitlines()) + "\n"]
    cm = "\n".join("# META " + l for l in json.dumps({"language": "python", "language_group": "synapse_pyspark"}, indent=2).splitlines())
    for kind, src in cells:
        if kind == "md":
            out.append("# MARKDOWN ********************\n")
            out.append("\n".join("# " + l if l else "#" for l in src.strip().splitlines()) + "\n")
        else:
            out.append("# CELL ********************\n")
            out.append(src.strip() + "\n")
            out.append("# METADATA ********************\n")
            out.append(cm + "\n")
    return "\n".join(out)


NB01 = [
    ("md", """# 01 · Ingest Salesforce, SAP and airport data
**Kyanos Hotels & Resorts** – unified data platform demo

| Source | Arrives as | Lands in |
|---|---|---|
| Protel-style PMS on SQL Server | **Mirroring** (near real time, no ETL) | `pms` schema – OneLake shortcut, zero copy |
| Salesforce (Privilege Club, guest cases) | API export / connector | `crm` schema |
| SAP (monthly hotel P&L costs) | file drop | `erp` schema |
| Airline seat capacity (incl. published Summer 2027 schedule) | external data | `ext` schema |
"""),
    ("code", """from pyspark.sql import functions as F
for s in ["crm", "erp", "ext"]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {s}")

def land(path, table, casts=None):
    df = spark.read.option("header", True).option("inferSchema", True).csv(f"Files/landing/{path}")
    for c, t in (casts or {}).items():
        df = df.withColumn(c, F.col(c).cast(t))
    df = df.withColumn("_ingested_at", F.current_timestamp()).withColumn("_source_file", F.lit(path))
    df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(table)
    print(f"{table:32s} {df.count():>8,} rows")

land("salesforce/privilege_club_members.csv", "crm.privilege_club_member", {"join_date": "date", "marketing_opt_in": "boolean"})
land("salesforce/guest_cases.csv", "crm.guest_case", {"created_date": "date", "csat_score": "int"})
land("sap/hotel_costs_monthly.csv", "erp.hotel_cost_monthly", {"posting_month": "date", "amount_eur": "decimal(14,2)", "gl_account": "string"})
land("external/airport_seat_capacity_weekly.csv", "ext.airport_seat_capacity", {"week_start": "date"})"""),
    ("code", """# The PMS arrives through Mirroring - already Delta in OneLake, nothing to copy
display(spark.sql("SELECT Status, COUNT(*) AS reservations, ROUND(SUM(RoomRevenue)/1e6,1) AS room_revenue_m FROM pms.Reservation GROUP BY Status ORDER BY 2 DESC"))"""),
]

NB02 = [
    ("md", f"""# 02 · Build the gold model
Joins PMS (mirrored), Salesforce, SAP and airport data into one conformed star schema in the `gold` schema.
Power BI reads it with **Direct Lake** – no import refresh, no 05:00–08:00 window.

Snapshot date of the demo data: **{AS_OF}**"""),
    ("code", f"""from pyspark.sql import functions as F, Window as W
AS_OF = "{AS_OF}"
spark.sql("CREATE SCHEMA IF NOT EXISTS gold")
hotel, rt, guest, res = [spark.table(f"pms.{{t}}") for t in ["Hotel", "RoomType", "Guest", "Reservation"]]
members, cases = spark.table("crm.privilege_club_member"), spark.table("crm.guest_case")
cost, seats = spark.table("erp.hotel_cost_monthly"), spark.table("ext.airport_seat_capacity")

def save(df, name):
    df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"gold.{{name}}")
    print(f"gold.{{name:28s}} {{spark.table('gold.' + name).count():>9,}} rows")"""),
    ("code", """# dim_date
d = spark.sql("SELECT explode(sequence(to_date('2025-01-01'), to_date('2027-12-31'), interval 1 day)) AS date")
asof_month = int(AS_OF[5:7])
dim_date = (d.select("date",
        F.year("date").alias("year"),
        F.concat(F.lit("Q"), F.quarter("date")).alias("quarter"),
        F.month("date").alias("month_num"),
        F.date_format("date", "MMM").alias("month"),
        F.date_format("date", "yyyy-MM").alias("year_month"),
        F.trunc("date", "month").alias("month_start"),
        F.date_trunc("week", "date").cast("date").alias("week_start"),
        F.dayofweek("date").alias("weekday_num"),
        F.date_format("date", "EEE").alias("weekday"),
        F.when(F.month("date").isin(7, 8), "Peak").when(F.month("date").isin(6, 9), "High")
         .when(F.month("date").isin(4, 5, 10), "Shoulder").otherwise("Winter").alias("season"),
        (F.col("date") <= F.lit(AS_OF)).alias("is_actual"),
        (F.month("date") < asof_month).alias("is_closed_ytd")))
save(dim_date, "dim_date")

# dim_hotel / dim_airport
AIRPORTS = [("HER","Heraklion","Crete"),("CHQ","Chania","Crete"),("RHO","Rhodes","Rhodes"),("KGS","Kos","Kos"),("CFU","Corfu","Corfu"),
            ("JMK","Mykonos","Cyclades"),("JTR","Santorini","Cyclades"),("SKG","Thessaloniki","Macedonia"),("GPA","Araxos (Patras)","Peloponnese"),
            ("KLX","Kalamata","Peloponnese"),("ATH","Athens","Attica"),("ZTH","Zakynthos","Zakynthos")]
dim_airport = spark.createDataFrame(AIRPORTS, "airport_code string, airport_name string, airport_region string")
save(dim_airport, "dim_airport")
dim_hotel = hotel.select(F.col("HotelId").alias("hotel_id"), F.col("HotelCode").alias("hotel_code"), F.col("HotelName").alias("hotel_name"),
    F.regexp_replace("HotelName", "^Kyanos ", "").alias("hotel_short_name"), F.col("Destination").alias("destination"), F.col("Region").alias("region"),
    F.col("Airport").alias("airport_code"), F.col("Stars").cast("int").alias("stars"), F.col("Concept").alias("concept"), F.col("Rooms").alias("rooms"),
    F.col("Latitude").cast("double").alias("latitude"), F.col("Longitude").cast("double").alias("longitude"),
    F.when(F.col("IsSeasonal"), "Seasonal resort").otherwise("Year-round").alias("operating_model"),
    F.col("GeneralManager").alias("general_manager"), F.col("GMEmail").alias("gm_email"))
save(dim_hotel, "dim_hotel")"""),
    ("code", """# dim_guest  (PMS guest profile + Salesforce Privilege Club)
# Data quality: a few loyalty numbers are duplicated across Salesforce accounts -> keep one member record per id
m = (members.dropDuplicates(["member_id"])
     .select(F.col("member_id"), F.col("tier"), F.col("marketing_opt_in"), F.col("top_preference"), F.col("lifetime_nights"), F.col("join_date")))
dim_guest = (guest.join(m, guest.LoyaltyNumber == m.member_id, "left")
    .select(F.col("GuestId").alias("guest_id"), F.concat_ws(" ", "FirstName", "LastName").alias("guest_name"), F.col("Email").alias("email"),
            F.col("Country").alias("country_code"), F.col("CountryName").alias("country"), F.col("Language").alias("language"),
            F.col("LoyaltyNumber").alias("member_id"), F.col("member_id").isNotNull().alias("is_member"),
            F.coalesce("tier", F.lit("Non-member")).alias("loyalty_tier"), F.coalesce("marketing_opt_in", F.lit(False)).alias("marketing_opt_in"),
            "top_preference", F.coalesce("lifetime_nights", F.lit(0)).alias("lifetime_nights"))
    .dropDuplicates(["guest_id"]))
save(dim_guest, "dim_guest")

# fact_reservation
rtn = rt.select(F.col("RoomTypeId"), F.col("RoomTypeName").alias("room_type"))
fact_res = (res.join(rtn, "RoomTypeId", "left").select(
    F.col("ReservationId").alias("reservation_id"), F.col("ConfirmationNo").alias("confirmation_no"), F.col("HotelId").alias("hotel_id"),
    F.col("GuestId").alias("guest_id"), "room_type", F.col("BookingDate").alias("booking_date"), F.col("ArrivalDate").alias("arrival_date"),
    F.col("DepartureDate").alias("departure_date"), F.col("Nights").alias("nights"),
    F.datediff("ArrivalDate", "BookingDate").alias("lead_time_days"), F.col("Channel").alias("channel"),
    F.when(F.col("Channel").startswith("Direct"), "Direct").when(F.col("Channel").isin("Booking.com", "Expedia"), "OTA")
     .when(F.col("Channel").isin("Tour Operator", "Wholesaler"), "Tour Operator & Wholesale").otherwise("Corporate & MICE").alias("channel_group"),
    F.col("MarketSegment").alias("market_segment"), F.col("TourOperator").alias("tour_operator"), F.col("BoardType").alias("board_type"),
    F.col("Adults").cast("int").alias("adults"), F.col("Children").cast("int").alias("children"), F.col("Status").alias("status"),
    (F.col("Status") == "Cancelled").alias("is_cancelled"), F.col("Status").isin("Checked-Out", "In-House", "Confirmed").alias("is_active"),
    F.col("RateAmount").cast("double").alias("rate_amount"), F.col("RoomRevenue").cast("double").alias("room_revenue"),
    F.col("ExtrasRevenue").cast("double").alias("extras_revenue"), F.col("CancelDate").alias("cancel_date"), F.col("CreatedAt").alias("created_at")))
save(fact_res, "fact_reservation")"""),
    ("code", """# fact_hotel_day: one row per hotel per calendar day (rooms available vs sold, revenue, arrivals)
act = spark.table("gold.fact_reservation").where("is_active")
nights = (act.withColumn("i", F.explode(F.sequence(F.lit(0), F.col("nights") - 1)))
    .select("hotel_id", F.date_add("arrival_date", F.col("i")).alias("date"),
            (F.col("room_revenue") / F.col("nights")).alias("rr"), (F.col("extras_revenue") / F.col("nights")).alias("xr")))
sold = nights.groupBy("hotel_id", "date").agg(F.count("*").alias("rooms_sold"), F.sum("rr").alias("room_revenue"), F.sum("xr").alias("extras_revenue"))
arr = act.groupBy("hotel_id", F.col("arrival_date").alias("date")).agg(F.count("*").alias("arrivals"))
cal = (spark.table("gold.dim_date").select("date").crossJoin(hotel.select(F.col("HotelId").alias("hotel_id"), "Rooms", "OpenMMDD", "CloseMMDD", "Airport")))
md = F.date_format("date", "MM-dd")
cal = cal.withColumn("is_open", (md >= F.col("OpenMMDD")) & (md <= F.col("CloseMMDD")))
fact_day = (cal.join(sold, ["hotel_id", "date"], "left").join(arr, ["hotel_id", "date"], "left")
    .select("hotel_id", "date", F.when(F.col("is_open"), F.col("Rooms")).otherwise(0).alias("rooms_available"),
            F.coalesce("rooms_sold", F.lit(0)).alias("rooms_sold"), F.round(F.coalesce("room_revenue", F.lit(0.0)), 2).alias("room_revenue"),
            F.round(F.coalesce("extras_revenue", F.lit(0.0)), 2).alias("extras_revenue"), F.coalesce("arrivals", F.lit(0)).alias("arrivals"),
            (F.col("date") <= F.lit(AS_OF)).alias("is_actual"))
    .withColumn("total_revenue", F.round(F.col("room_revenue") + F.col("extras_revenue"), 2)))
save(fact_day, "fact_hotel_day")"""),
    ("code", """# fact_hotel_cost (SAP), fact_guest_case (Salesforce), fact_airport_seats (external)
hid = hotel.select(F.col("HotelId").alias("hotel_id"), F.col("HotelCode"))
save(cost.join(hid, cost.plant == hid.HotelCode).select("hotel_id", F.col("posting_month").alias("month_start"), "cost_category", "gl_account",
                                                       F.col("amount_eur").cast("double").alias("amount_eur")), "fact_hotel_cost")
save(cases.join(hid, cases.hotel_code == hid.HotelCode).select("case_id", "confirmation_no", "hotel_id", "created_date", "category", "sub_category",
                                                             "origin", "status", "csat_score"), "fact_guest_case")
save(seats.where("week_start >= '2025-01-01'").select("airport_code", "week_start", F.col("scheduled_arriving_seats").alias("arriving_seats"), F.col("scheduled_flights").alias("flights"),
                  "season_year", "data_status"), "fact_airport_seats")"""),
]

NB03 = [
    ("md", f"""# 03 · AI demand forecast – Summer 2027
**Question from revenue management:** *how full will each hotel be next season, given what is already on the books and what the airlines have scheduled?*

Booking-pace model (gradient boosting, tracked in MLflow) – predicts the **change in occupancy vs last year** for every hotel-night from:
* **booking pace** – rooms on the books today vs. the same point last year (snapshot {AS_OF})
* **airline seat capacity** change at the hotel's airport (published Summer 2027 schedules)
* last-year final occupancy, month, weekday, hotel concept

Output → `gold.fact_occupancy_forecast` → Power BI page *2027 Demand Outlook*."""),
    ("code", f"""import pandas as pd, numpy as np, mlflow, mlflow.sklearn
from pyspark.sql import functions as F
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
AS_OF = pd.Timestamp("{AS_OF}")
res = spark.table("gold.fact_reservation").select("hotel_id", "booking_date", "arrival_date", "nights", "status", "cancel_date").toPandas()
day = spark.table("gold.fact_hotel_day").toPandas()
hotel = spark.table("gold.dim_hotel").toPandas()
seats = spark.table("gold.fact_airport_seats").toPandas()
for c in ["booking_date", "arrival_date", "cancel_date"]: res[c] = pd.to_datetime(res[c])
day["date"] = pd.to_datetime(day["date"]); seats["week_start"] = pd.to_datetime(seats["week_start"])
print(len(res), "reservations,", len(day), "hotel-days")"""),
    ("code", """def otb_as_of(snap):
    \"\"\"Rooms on the books per hotel-night as they stood on the snapshot date.\"\"\"
    r = res[(res.booking_date <= snap) & ((res.cancel_date.isna()) | (res.cancel_date > snap)) & (res.status != "No-Show")]
    r = r.loc[r.index.repeat(r.nights)].copy()
    r["date"] = r.arrival_date + pd.to_timedelta(r.groupby(level=0).cumcount(), unit="D")
    return r.groupby(["hotel_id", "date"]).size().rename("otb_rooms").reset_index()

def frame(year):
    snap = AS_OF - pd.DateOffset(years=2027 - year)
    f = day[(day.date.dt.year == year) & (day.rooms_available > 0)][["hotel_id", "date", "rooms_available", "rooms_sold", "room_revenue"]].copy()
    f = f.merge(otb_as_of(snap), on=["hotel_id", "date"], how="left").fillna({"otb_rooms": 0})
    ly_otb = otb_as_of(snap - pd.DateOffset(years=1)).rename(columns={"otb_rooms": "ly_otb_rooms"})
    ly_otb["date"] = ly_otb.date + pd.Timedelta(days=364)
    f = f.merge(ly_otb, on=["hotel_id", "date"], how="left").fillna({"ly_otb_rooms": 0})
    ly = day[["hotel_id", "date", "rooms_sold", "rooms_available", "room_revenue"]].rename(columns={"rooms_sold": "ly_rooms_sold", "rooms_available": "ly_rooms_available", "room_revenue": "ly_room_revenue"})
    ly["date"] = ly.date + pd.Timedelta(days=364)  # same weekday last year
    f = f.merge(ly, on=["hotel_id", "date"], how="left")
    f = f.merge(hotel[["hotel_id", "airport_code", "concept", "stars", "rooms"]], on="hotel_id")
    f["week_start"] = f.date - pd.to_timedelta(f.date.dt.weekday, unit="D")
    s = seats[["airport_code", "week_start", "arriving_seats"]]
    s_ly = s.assign(week_start=s.week_start + pd.Timedelta(days=364)).rename(columns={"arriving_seats": "ly_seats"})
    f = f.merge(s, on=["airport_code", "week_start"], how="left").merge(s_ly, on=["airport_code", "week_start"], how="left")
    f["seat_growth"] = (f.arriving_seats / f.ly_seats - 1).fillna(0)
    f["otb_occ"] = f.otb_rooms / f.rooms_available
    f["ly_occ"] = (f.ly_rooms_sold / f.ly_rooms_available).replace([np.inf], np.nan)
    f["pace_vs_ly"] = (f.otb_rooms - f.ly_otb_rooms) / f.rooms_available
    f["occ"] = f.rooms_sold / f.rooms_available
    f["delta_vs_ly"] = f.occ - f.ly_occ
    f["month"], f["weekday"] = f.date.dt.month, f.date.dt.weekday
    f["concept_code"] = f.concept.astype("category").cat.codes
    f["snapshot"] = snap
    return f

train = frame(2026); train = train[(train.date <= AS_OF) & train.ly_occ.notna() & (train.ly_rooms_available > 0)].copy()
score = frame(2027); score = score[score.date <= "2027-09-30"].copy()
score["ly_occ"] = score.ly_occ.fillna(score.groupby("hotel_id").ly_occ.transform("mean")).fillna(score.otb_occ)

def smooth(df_):
    df_ = df_.sort_values(["hotel_id", "date"]).reset_index(drop=True)
    for c in ["pace_vs_ly", "seat_growth"]:
        df_[c + "_28d"] = df_.groupby("hotel_id")[c].transform(lambda x: x.rolling(28, min_periods=1, center=True).mean())
    df_["headroom"] = 1 - df_["ly_occ"]
    return df_

train, score = smooth(train), smooth(score)
FEATURES = ["seat_growth_28d", "pace_vs_ly_28d", "headroom"]
MONOTONIC = [1, 1, 0]   # more seats / stronger pace can only push the forecast up
TARGET = "delta_vs_ly"
print("training rows:", len(train), " scoring rows:", len(score))"""),
    ("code", """mlflow.set_experiment("kyanos-occupancy-forecast")
params = dict(max_iter=300, learning_rate=0.04, max_leaf_nodes=15, min_samples_leaf=60, l2_regularization=1.0)
mask = np.random.default_rng(7).random(len(train)) < 0.8
with mlflow.start_run(run_name="pace-model-summer-2027") as run:
    model = HistGradientBoostingRegressor(**params, monotonic_cst=MONOTONIC, random_state=7)
    model.fit(train.loc[mask, FEATURES], train.loc[mask, TARGET])
    pred = np.clip(train.loc[~mask, "ly_occ"] + model.predict(train.loc[~mask, FEATURES]), 0, 1)
    mae = mean_absolute_error(train.loc[~mask, "occ"], pred)
    base = mean_absolute_error(train.loc[~mask, "occ"], train.loc[~mask, "ly_occ"])
    mlflow.log_params({**params, "features": ",".join(FEATURES), "target": TARGET, "snapshot": str(AS_OF.date())})
    mlflow.log_metric("mae_occupancy_pts", round(mae * 100, 2))
    mlflow.log_metric("naive_same_as_last_year_mae_pts", round(base * 100, 2))
    model.fit(train[FEATURES], train[TARGET])
    mlflow.sklearn.log_model(model, "model", registered_model_name="kyanos-occupancy-forecast", input_example=train[FEATURES].head(5))
print(f"Holdout MAE {mae*100:.1f} occupancy points vs. naive 'same as last year' {base*100:.1f}")"""),
    ("code", """score["forecast_occ"] = np.clip(score.ly_occ + model.predict(score[FEATURES]), score.otb_occ, 0.995)
score["forecast_rooms_sold"] = (score.forecast_occ * score.rooms_available).round(0)
adr_ly = (score.ly_room_revenue / score.ly_rooms_sold).replace([np.inf, -np.inf], np.nan)
score["forecast_room_revenue"] = (score.forecast_rooms_sold * adr_ly.fillna(adr_ly.mean()) * 1.04).round(2)
cols = ["hotel_id", "date", "rooms_available", "otb_rooms", "ly_otb_rooms", "forecast_rooms_sold", "forecast_room_revenue",
        "ly_rooms_sold", "ly_room_revenue", "seat_growth", "pace_vs_ly", "otb_occ", "forecast_occ", "ly_occ"]
out = score[cols].copy()
for c in cols[2:]:
    out[c] = out[c].astype("float64")
out["hotel_id"] = out.hotel_id.astype("int32")
out["date"] = out.date.dt.date
out["model_run_id"] = run.info.run_id
out["snapshot_date"] = AS_OF.date()
sdf = spark.createDataFrame(out)
sdf.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold.fact_occupancy_forecast")
display(spark.sql(\"\"\"SELECT h.hotel_name, ROUND(AVG(f.forecast_occ)*100,1) AS forecast_occ_pct, ROUND(AVG(f.ly_occ)*100,1) AS ly_occ_pct,
                ROUND(AVG(f.seat_growth)*100,1) AS airline_seat_growth_pct
               FROM gold.fact_occupancy_forecast f JOIN gold.dim_hotel h USING (hotel_id) GROUP BY h.hotel_name ORDER BY AVG(f.forecast_occ) - AVG(f.ly_occ) DESC\"\"\"))"""),
]

NB04 = [
    ("md", """# 04 · Fabric IQ – ontology entities
Business-friendly entity tables for the **Kyanos ontology** (Fabric IQ): hotels, airports, VIP guests (Gold/Platinum Privilege Club),
their upcoming stays, open guest cases and tour operators. The ontology turns tables into connected business concepts that
agents and people can navigate – e.g. *"which Platinum guests arrive this month at a hotel with open air-conditioning cases?"*"""),
    ("code", f"""from pyspark.sql import functions as F
AS_OF = "{AS_OF}"
h, d, g = spark.table("gold.dim_hotel"), spark.table("gold.fact_hotel_day"), spark.table("gold.dim_guest")
r, c, a, s = spark.table("gold.fact_reservation"), spark.table("gold.fact_guest_case"), spark.table("gold.dim_airport"), spark.table("gold.fact_airport_seats")
def save(df, name):
    df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"gold.{{name}}")
    print(f"gold.{{name:22s}} {{spark.table('gold.' + name).count():>7,}} rows")

ytd = lambda y: (F.year("date") == y) & (F.month("date") <= 9)
k26 = d.where(ytd(2026)).groupBy("hotel_id").agg((F.sum("room_revenue") / F.sum("rooms_available")).alias("revpar_2026"), (F.sum("rooms_sold") / F.sum("rooms_available")).alias("occupancy_2026"))
k25 = d.where(ytd(2025)).groupBy("hotel_id").agg((F.sum("room_revenue") / F.sum("rooms_available")).alias("revpar_2025"))
cs = c.groupBy("hotel_id").agg(F.round(F.avg("csat_score"), 2).alias("avg_case_csat"), F.sum(F.when(F.col("status") == "Open", 1).otherwise(0)).alias("open_cases"))
save(h.join(k26, "hotel_id").join(k25, "hotel_id").join(cs, "hotel_id", "left").select(
    F.col("hotel_id").cast("long"), "hotel_code", "hotel_name", "destination", "region", "concept", F.col("stars").cast("long"), F.col("rooms").cast("long"),
    "airport_code", "general_manager", F.round("occupancy_2026", 4).alias("occupancy_2026"), F.round("revpar_2026", 2).alias("revpar_2026"),
    F.round(F.col("revpar_2026") / F.col("revpar_2025") - 1, 4).alias("revpar_vs_ly"), F.col("avg_case_csat").cast("double"), F.col("open_cases").cast("long")), "iq_hotel")

sy = s.groupBy("airport_code").agg(*[F.sum(F.when(F.col("season_year") == y, F.col("arriving_seats"))).alias(f"s{{y}}") for y in (2025, 2026, 2027)])
save(a.join(sy, "airport_code").select("airport_code", "airport_name", "airport_region",
     F.round(F.col("s2026") / F.col("s2025") - 1, 4).alias("seat_growth_2026"), F.round(F.col("s2027") / F.col("s2026") - 1, 4).alias("seat_growth_2027")), "iq_airport")

vip = g.where(F.col("loyalty_tier").isin("Gold", "Platinum"))
up = (r.where(F.col("is_active") & (F.col("arrival_date") > F.lit(AS_OF)) & (F.col("arrival_date") <= F.lit("2027-09-30")))
       .join(vip.select("guest_id"), "guest_id"))
save(vip.join(up.select("guest_id").distinct(), "guest_id").select(F.col("guest_id").cast("long"), "guest_name", "country", "language", "loyalty_tier", "member_id",
     F.col("lifetime_nights").cast("long"), "top_preference"), "iq_vip_guest")
tos = r.where(F.col("tour_operator").isNotNull()).select("tour_operator").distinct().withColumn("tour_operator_id", F.upper(F.regexp_replace("tour_operator", "[^A-Za-z]", "")).substr(1, 8))
save(up.join(tos, "tour_operator", "left").select(F.col("reservation_id").cast("long"), "confirmation_no", F.col("hotel_id").cast("long"), F.col("guest_id").cast("long"),
     F.date_format("arrival_date", "yyyy-MM-dd").alias("arrival_date"), F.col("nights").cast("long"), "room_type", "channel", "board_type",
     F.round("room_revenue", 2).alias("room_revenue"), "tour_operator_id"), "iq_upcoming_stay")

MARKET = {{"SunVoyage Holidays": "United Kingdom", "Nordic Breeze Travel": "Sweden", "Alpenreisen Touristik": "Germany", "Mare Viaggi": "Italy",
          "Albion Sun Tours": "United Kingdom", "Benelux Zon Reizen": "Netherlands"}}
tn = r.where(F.col("tour_operator").isNotNull() & F.col("is_active")).groupBy("tour_operator").agg(
    F.sum(F.when(F.year("arrival_date") == 2026, F.col("nights"))).alias("room_nights_2026"),
    F.sum(F.when(F.year("arrival_date") == 2027, F.col("nights"))).alias("otb_room_nights_2027"))
mk = spark.createDataFrame(list(MARKET.items()), "tour_operator string, home_market string")
save(tos.join(tn, "tour_operator").join(mk, "tour_operator", "left").select("tour_operator_id", F.col("tour_operator").alias("tour_operator_name"), "home_market",
     F.col("room_nights_2026").cast("long"), F.col("otb_room_nights_2027").cast("long")), "iq_tour_operator")

guest_of = r.select("confirmation_no", F.col("guest_id").alias("res_guest_id"))
save(c.where(F.col("status") == "Open").join(guest_of, "confirmation_no", "left").select("case_id", F.col("hotel_id").cast("long"),
     F.date_format("created_date", "yyyy-MM-dd").alias("created_date"), "category", "sub_category", "origin", "status",
     F.col("csat_score").cast("long"), F.col("res_guest_id").cast("long").alias("guest_id")), "iq_open_case")"""),
]


