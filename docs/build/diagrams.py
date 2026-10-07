"""Render documentation diagrams (architecture, ERD, lineage, build process) with matplotlib."""
import pathlib, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon

OUT = pathlib.Path(__file__).resolve().parent.parent / "images"
OUT.mkdir(exist_ok=True)
plt.rcParams["font.family"] = "Segoe UI"
NAVY, BLUE, TEAL, SAND, CORAL, INK, MUTED, BG, LINE = "#0B3C5D", "#0B4F8A", "#22A39F", "#F2A541", "#E4572E", "#1F2A44", "#5B6B82", "#F4F7FB", "#C9D3E0"
PURPLE = "#6C5B7B"


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h), dpi=200)
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    fig.patch.set_facecolor("white")
    return fig, ax


def rbox(ax, x, y, w, h, fc="#FFFFFF", ec=LINE, lw=1.2, r=0.12, z=2):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw, zorder=z)
    ax.add_patch(p); return p


def text(ax, x, y, s, size=9, color=INK, weight="normal", ha="center", va="center", z=5, style="normal"):
    ax.text(x, y, s, fontsize=size, color=color, fontweight=weight, ha=ha, va=va, zorder=z, fontstyle=style, linespacing=1.25)


def arrow(ax, p1, p2, color=MUTED, lw=1.6, style="-|>", rad=0.0, z=3, ls="-", ms=12):
    a = FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=ms, color=color, lw=lw, zorder=z,
                        connectionstyle=f"arc3,rad={rad}", linestyle=ls, shrinkA=2, shrinkB=2)
    ax.add_patch(a); return a


def card(ax, x, y, w, h, title, body, color, title_size=9.5, body_size=7.8):
    rbox(ax, x, y, w, h, fc="#FFFFFF", ec=color, lw=1.6)
    rbox(ax, x, y + h - 0.42, w, 0.42, fc=color, ec=color, lw=1.6)
    ax.add_patch(plt.Rectangle((x, y + h - 0.42), w, 0.2, fc=color, ec=color, zorder=2))
    text(ax, x + w / 2, y + h - 0.21, title, title_size, "#FFFFFF", "bold")
    text(ax, x + w / 2, y + (h - 0.42) / 2, body, body_size, INK)


# ------------------------------------------------------------------ 1. solution architecture
def architecture():
    fig, ax = canvas(18, 9.6)
    rbox(ax, 0.1, 0.1, 17.8, 9.4, fc=BG, ec=BG)
    for x, t in [(0.3, "SOURCES"), (3.75, "INGESTION"), (6.75, "ONELAKE · KyanosLakehouse"), (11.45, "ANALYTICS & AI"), (14.75, "CONSUMPTION")]:
        text(ax, x, 9.15, t, 10, NAVY, "bold", ha="left")
    # sources
    card(ax, 0.3, 6.85, 3.05, 1.95, "PMS on SQL Server", "KyanosPMS · Fabric SQL database\n(stand-in for Protel / on-prem DW)\n24 hotels · 483K reservations", BLUE)
    rbox(ax, 0.3, 5.95, 3.05, 0.65, fc="#FFF4EE", ec=CORAL, lw=1.2)
    text(ax, 1.82, 6.27, "Live PMS simulator (Python) · new bookings ~6 s", 7.3, CORAL)
    arrow(ax, (1.82, 6.6), (1.82, 6.85), CORAL, 1.6)
    card(ax, 0.3, 4.15, 3.05, 1.5, "Salesforce", "Privilege Club members (43K)\nService cases (17K)", TEAL)
    card(ax, 0.3, 2.35, 3.05, 1.5, "SAP ERP", "Monthly hotel costs\nby GL account (2.1K rows)", SAND)
    card(ax, 0.3, 0.55, 3.05, 1.5, "Airline schedules", "Weekly arriving seats per airport\n2025-26 actual · 2027 published", PURPLE)
    # ingestion
    card(ax, 3.75, 6.85, 2.65, 1.95, "Mirroring", "SQL → Delta in OneLake\nautomatic · near real time\nno ETL · no night batch", BLUE)
    card(ax, 3.75, 2.35, 2.65, 2.05, "File landing", "Files/landing/\nsalesforce · sap · external\n(CSV via OneLake DFS API)", TEAL)
    arrow(ax, (3.35, 7.8), (3.75, 7.8), BLUE, 2.2)
    for y in (4.9, 3.1, 1.3):
        arrow(ax, (3.35, y), (3.75, 3.35), MUTED, 1.5)
    # lakehouse
    rbox(ax, 6.75, 0.55, 4.3, 8.3, fc="#FFFFFF", ec=NAVY, lw=2)
    card(ax, 6.95, 6.3, 1.85, 2.3, "pms", "OneLake shortcut\n(zero copy) to the\nmirrored PMS:\nHotel · RoomType\nGuest · Reservation", BLUE, body_size=7.0)
    card(ax, 6.95, 2.25, 1.85, 2.3, "crm · erp · ext", "01_Ingest →\nprivilege_club_member\nguest_case\nhotel_cost_monthly\nairport_seat_capacity", TEAL, body_size=7.0)
    card(ax, 9.0, 2.25, 1.85, 6.35, "gold",
         "star schema\n\ndim_date\ndim_hotel\ndim_guest\ndim_airport\n\nfact_hotel_day\nfact_reservation\nfact_hotel_cost\nfact_guest_case\nfact_airport_seats\nfact_occupancy\n_forecast\n\niq_* entities\n(ontology)", NAVY, body_size=7.2)
    rbox(ax, 6.95, 0.75, 3.9, 1.2, fc="#EEF3F8", ec=LINE)
    text(ax, 8.9, 1.35, "Notebooks (PySpark)\n01 ingest · 02 build gold · 03 forecast · 04 IQ", 7.6, NAVY)
    arrow(ax, (6.4, 7.8), (6.95, 7.8), BLUE, 2.2)
    arrow(ax, (6.4, 3.4), (6.95, 3.4), TEAL, 2.2)
    arrow(ax, (8.8, 7.45), (9.0, 7.45), NAVY, 2.2); arrow(ax, (8.8, 3.4), (9.0, 3.4), NAVY, 2.2)
    # analytics & AI
    card(ax, 11.45, 6.6, 2.9, 2.0, "AI demand forecast", "Notebook 03 · scikit-learn\nbooking pace + airline seats\nMLflow experiment + model\nwrites fact_occupancy_forecast", CORAL, body_size=7.5)
    card(ax, 11.45, 3.9, 2.9, 2.2, "Semantic model", "Direct Lake on OneLake\n11 tables · 15 relationships\n53 measures · 2 RLS roles\n+ live pms.Reservation table", BLUE, body_size=7.5)
    card(ax, 11.45, 1.75, 2.9, 1.65, "Fabric IQ ontology", "6 entity types\n5 relationships\nbound to gold.iq_* tables", PURPLE, body_size=7.5)
    arrow(ax, (10.85, 7.5), (11.45, 7.5), CORAL, 2.0, style="<|-|>")
    arrow(ax, (10.85, 5.0), (11.45, 5.0), BLUE, 2.2)
    arrow(ax, (10.85, 2.6), (11.45, 2.6), PURPLE, 2.0)
    # consumption
    card(ax, 14.75, 6.15, 2.9, 2.45, "Power BI report", "5 pages · Aegean theme\nexecutive · scorecard · channels\n2027 AI outlook · live PMS\n+ Copilot in Power BI", NAVY, body_size=7.5)
    card(ax, 14.75, 3.9, 2.9, 1.95, "Data agent", "Kyanos Revenue & Guest\nAssistant · Greek / English\n→ Teams / M365 Copilot", TEAL, body_size=7.5)
    card(ax, 14.75, 1.75, 2.9, 1.65, "Ontology agent", "graph questions across hotels\nguests · stays · cases (preview)", PURPLE, body_size=7.5)
    arrow(ax, (14.35, 5.6), (14.75, 6.9), NAVY, 2.2)
    arrow(ax, (14.35, 4.9), (14.75, 4.9), TEAL, 2.2)
    arrow(ax, (14.35, 2.6), (14.75, 2.6), PURPLE, 2.0)
    rbox(ax, 11.45, 0.3, 6.2, 1.15, fc="#FFFFFF", ec=LINE)
    text(ax, 14.55, 0.87, "Platform: Fabric F8 capacity · Entra ID · workspace roles · RLS (Hotel GM / Region)\nOne copy of data in OneLake (Delta/Parquet) · Direct Lake reframes automatically on new commits", 7.5, INK)
    fig.savefig(OUT / "architecture.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


# ------------------------------------------------------------------ 2. semantic model ERD
ERD_TABLES = {
    "fact_hotel_day": (0.4, 15.0, 4.1, "fact", ["hotel_id  (FK)", "date  (FK)", "rooms_available · rooms_sold", "room_revenue · extras_revenue", "arrivals · is_actual"], 19),
    "fact_occupancy_forecast": (0.4, 11.6, 4.1, "fact", ["hotel_id  (FK)", "date  (FK)", "forecast_rooms_sold · otb_rooms", "ly_rooms_sold · seat_growth", "forecast_room_revenue"], 9),
    "fact_hotel_cost": (0.4, 8.2, 4.1, "fact", ["hotel_id  (FK)", "month_start  (FK)", "cost_category · gl_account", "amount_eur  (SAP)"], 5),
    "live_pms_reservation": (0.4, 5.2, 4.1, "live", ["HotelId  (FK)", "CreatedAt · BookingDate", "Channel · Status · RoomRevenue", "source: pms.Reservation (mirrored)"], 4),
    "dim_date": (7.1, 15.0, 3.8, "dim", ["date  (PK, date table)", "year · quarter · month", "year_month · week_start", "season · is_actual", "is_closed_ytd  (Jan–Sep)"], 0),
    "dim_hotel": (7.1, 10.9, 3.8, "dim", ["hotel_id  (PK)", "hotel_name · hotel_short_name", "region · destination · concept", "rooms · stars", "airport_code  (FK)", "gm_email  (RLS filter)"], 0),
    "dim_airport": (7.1, 5.6, 3.8, "dim", ["airport_code  (PK)", "airport_name · airport_region"], 0),
    "dim_guest": (13.5, 15.0, 4.1, "dim", ["guest_id  (PK)", "country · language", "loyalty_tier · is_member", "member_id  (Salesforce)"], 0),
    "fact_reservation": (13.5, 11.9, 4.1, "fact", ["guest_id  (FK)", "hotel_id  (FK)", "arrival_date  (FK)", "reservation_id · status", "channel · channel_group", "lead_time_days · nights"], 9),
    "fact_guest_case": (13.5, 8.1, 4.1, "fact", ["hotel_id  (FK)", "created_date  (FK)", "case_id · category", "sub_category · csat_score"], 4),
    "fact_airport_seats": (13.5, 4.9, 4.1, "fact", ["airport_code  (FK)", "week_start  (FK)", "arriving_seats · flights"], 3),
}
ERD_RELS = [("fact_hotel_day", "dim_hotel", "hotel_id"), ("fact_hotel_day", "dim_date", "date"),
            ("fact_occupancy_forecast", "dim_hotel", "hotel_id"), ("fact_occupancy_forecast", "dim_date", "date"),
            ("fact_hotel_cost", "dim_hotel", "hotel_id"), ("fact_hotel_cost", "dim_date", "month_start"),
            ("live_pms_reservation", "dim_hotel", "HotelId"),
            ("fact_reservation", "dim_hotel", "hotel_id"), ("fact_reservation", "dim_date", "arrival_date"), ("fact_reservation", "dim_guest", "guest_id"),
            ("fact_guest_case", "dim_hotel", "hotel_id"), ("fact_guest_case", "dim_date", "created_date"),
            ("fact_airport_seats", "dim_airport", "airport_code"), ("fact_airport_seats", "dim_date", "week_start"),
            ("dim_hotel", "dim_airport", "airport_code")]
KIND_COLOR = {"dim": NAVY, "fact": TEAL, "live": CORAL}
REL_COLOR = {"dim_date": BLUE, "dim_hotel": TEAL, "dim_airport": SAND, "dim_guest": CORAL}
ROW_H, HEAD_H = 0.38, 0.6


def erd():
    fig, ax = canvas(18, 15.4)
    geo, rowy = {}, {}
    for name, (x, ytop, w, kind, rows, nm) in ERD_TABLES.items():
        h = HEAD_H + ROW_H * len(rows) + (0.42 if nm else 0.12)
        y = ytop - h
        c = KIND_COLOR[kind]
        rbox(ax, x, y, w, h, fc="#FFFFFF", ec=c, lw=1.8, r=0.1)
        rbox(ax, x, ytop - HEAD_H, w, HEAD_H, fc=c, ec=c, lw=1.8, r=0.1)
        ax.add_patch(plt.Rectangle((x, ytop - HEAD_H), w, 0.28, fc=c, ec=c, zorder=2))
        text(ax, x + 0.15, ytop - HEAD_H / 2, name, 10.5, "#FFFFFF", "bold", ha="left")
        text(ax, x + w - 0.15, ytop - HEAD_H / 2, {"dim": "DIMENSION", "fact": "FACT", "live": "LIVE TABLE"}[kind], 6.5, "#DDE8F2", ha="right")
        for i, r in enumerate(rows):
            yy = ytop - HEAD_H - ROW_H * (i + 0.5) - 0.04
            pk, fk = "(PK" in r, "(FK" in r
            if pk or fk:
                ax.add_patch(plt.Rectangle((x + 0.06, yy - ROW_H / 2 + 0.03), w - 0.12, ROW_H - 0.06, fc="#EAF4F8" if fk else "#E7ECF4", ec="none", zorder=3))
                rbox(ax, x + 0.14, yy - 0.12, 0.36, 0.24, fc=NAVY if pk else TEAL, ec="none", r=0.05, z=4)
                text(ax, x + 0.32, yy, "PK" if pk else "FK", 6.3, "#FFFFFF", "bold")
                rowy[(name, r.split()[0])] = yy
            text(ax, x + 0.62, yy, r, 8.3, NAVY if pk else (TEAL if fk else INK), "bold" if (pk or fk) else "normal", ha="left")
        if nm:
            text(ax, x + 0.18, y + 0.24, f"Σ  {nm} measures", 8, CORAL, "bold", ha="left")
        geo[name] = (x, y, w, h)
    incoming = {}
    for f, d, c in ERD_RELS:
        incoming.setdefault(d, []).append((f, c))
    for d, fs in incoming.items():
        dx, dy, dw, dh = geo[d]
        pky = rowy.get((d, ERD_TABLES[d][4][0].split()[0]))
        col = REL_COLOR[d]
        left = [(f, c) for f, c in fs if geo[f][0] + geo[f][2] <= dx]
        right = [(f, c) for f, c in fs if geo[f][0] >= dx + dw]
        vert = [(f, c) for f, c in fs if (f, c) not in left and (f, c) not in right]
        for group, ex, sgn in ((left, dx, -1), (right, dx + dw, 1)):
            group = sorted(group, key=lambda fc: -rowy[(fc[0], fc[1])])
            n = len(group)
            for i, (f, c) in enumerate(group):
                ay = pky + 0.12 - (i * 0.42 if n > 1 else 0) if d != "dim_hotel" else dy + dh - HEAD_H - 0.25 - i * 0.45
                fx, fy, fw, fh = geo[f]
                fxe = fx + fw if sgn < 0 else fx
                fyc = rowy[(f, c)]
                arrow(ax, (ex, ay), (fxe, fyc), col, 1.9, ms=13)
                ax.plot([ex], [ay], "o", color=col, ms=6, zorder=6)
                text(ax, ex + 0.18 * sgn, ay + 0.17, "1", 9, col, "bold")
                text(ax, fxe - 0.2 * sgn, fyc + 0.2, "*", 12, col, "bold")
        for f, c in vert:
            fx, fy, fw, fh = geo[f]
            if fy > dy:   # fact above dimension (dim_hotel -> dim_airport case is handled below)
                p1, p2 = (dx + dw / 2, dy + dh), (fx + fw / 2, fy)
            else:
                p1, p2 = (dx + dw / 2, dy), (fx + fw / 2, fy + fh)
            arrow(ax, p1, p2, col, 1.9, ms=13); ax.plot([p1[0]], [p1[1]], "o", color=col, ms=6, zorder=6)
            text(ax, p1[0] + 0.2, p1[1] + (0.2 if fy > dy else -0.22), "1", 9, col, "bold")
            text(ax, p2[0] + 0.2, p2[1] - (0.28 if fy > dy else -0.28), "*", 12, col, "bold")
    rbox(ax, 0.4, 0.15, 17.2, 1.35, fc=BG, ec=LINE)
    items = [(BLUE, "dim_date – marked date table (time intelligence: SAMEPERIODLASTYEAR)"), (TEAL, "dim_hotel – conformed hotel dimension, RLS anchor"),
             (SAND, "dim_airport – airline seats + hotel → airport"), (CORAL, "dim_guest – PMS guest + Salesforce Privilege Club")]
    for i, (c, t) in enumerate(items):
        xx = 0.7 + (i % 2) * 8.6; yy = 1.15 - (i // 2) * 0.4
        ax.plot([xx, xx + 0.55], [yy, yy], color=c, lw=3); text(ax, xx + 0.7, yy, t, 8.6, INK, ha="left")
    text(ax, 0.7, 0.36, "All 15 relationships are many-to-one (* → 1), single cross-filter direction, active. Arrowheads show filter flow from dimension to fact; "
         "lines land on the exact FK column.", 8, MUTED, ha="left", style="italic")
    fig.savefig(OUT / "erd.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


# ------------------------------------------------------------------ 3. lineage
def lineage():
    fig, ax = canvas(17, 9.0)
    colx = [0.3, 4.3, 7.95, 11.4]
    for x, h in zip(colx, ["SOURCE (raw)", "LAKEHOUSE BRONZE / SILVER", "NOTEBOOK", "GOLD (serving)"]):
        text(ax, x, 8.7, h, 10, NAVY, "bold", ha="left")
    srcs = [("KyanosPMS (SQL)\npms.Hotel/RoomType/Guest/Reservation", BLUE, 7.3), ("privilege_club_members.csv\nguest_cases.csv", TEAL, 5.7),
            ("hotel_costs_monthly.csv", SAND, 4.3), ("airport_seat_capacity_weekly.csv", PURPLE, 2.9)]
    mids = [("pms.*  (schema shortcut,\nmirrored Delta – zero copy)", BLUE), ("crm.privilege_club_member\ncrm.guest_case", TEAL),
            ("erp.hotel_cost_monthly", SAND), ("ext.airport_seat_capacity", PURPLE)]
    for (t, c, y), (mt, _) in zip(srcs, mids):
        rbox(ax, colx[0], y, 3.4, 1.0, fc="#FFFFFF", ec=c, lw=1.6); text(ax, colx[0] + 1.7, y + 0.5, t, 8, INK)
        rbox(ax, colx[1], y, 3.0, 1.0, fc="#FFFFFF", ec=c, lw=1.6); text(ax, colx[1] + 1.5, y + 0.5, mt, 8, INK)
        arrow(ax, (colx[0] + 3.4, y + 0.5), (colx[1], y + 0.5), c, 1.9)
        arrow(ax, (colx[1] + 3.0, y + 0.5), (colx[2], 6.45), c, 1.4)
    text(ax, colx[0] + 3.7, 8.05, "Mirroring", 7.5, BLUE, style="italic")
    text(ax, colx[0] + 3.7, 6.45, "01_Ingest", 7.5, TEAL, style="italic")
    nbs = [("02_Build_Gold_Model\njoins · de-dup · stay explosion\nhotel calendar", NAVY, 5.75, 1.45), ("03_AI_Demand_Forecast_2027\nreads gold day · reservations · seats", CORAL, 3.45, 1.1),
           ("04_Fabric_IQ_Ontology_Entities\nreads gold facts & dims", PURPLE, 1.55, 1.1)]
    for t, c, y, h in nbs:
        rbox(ax, colx[2], y, 2.95, h, fc=c, ec=c); text(ax, colx[2] + 1.47, y + h / 2, t, 7.8, "#FFFFFF", "bold")
    golds = [("dim_date · dim_hotel · dim_airport · dim_guest", NAVY, 7.45, 0.65), ("fact_hotel_day · fact_reservation", NAVY, 6.6, 0.65),
             ("fact_hotel_cost · fact_guest_case · fact_airport_seats", NAVY, 5.75, 0.65), ("fact_occupancy_forecast", CORAL, 3.68, 0.65),
             ("iq_hotel · iq_airport · iq_vip_guest\niq_upcoming_stay · iq_open_case · iq_tour_operator", PURPLE, 1.6, 1.0)]
    for t, c, y, h in golds:
        rbox(ax, colx[3], y, 5.2, h, fc="#FFFFFF", ec=c, lw=1.6); text(ax, colx[3] + 2.6, y + h / 2, t, 8, INK)
    for y in (7.77, 6.92, 6.07):
        arrow(ax, (colx[2] + 2.95, 6.47), (colx[3], y), NAVY, 1.5)
    arrow(ax, (colx[2] + 2.95, 4.0), (colx[3], 4.0), CORAL, 1.9)
    arrow(ax, (colx[2] + 2.95, 2.1), (colx[3], 2.1), PURPLE, 1.9)
    rbox(ax, colx[3], 4.6, 5.2, 0.85, fc=BG, ec=LINE)
    text(ax, colx[3] + 2.6, 5.02, "Served by the Direct Lake semantic model (gold + pms.Reservation)\n→ Power BI report · data agent;  iq_* → Fabric IQ ontology", 7.4, INK)
    rbox(ax, 0.3, 0.3, 10.6, 0.95, fc=BG, ec=LINE)
    text(ax, 5.6, 0.77, "Data-quality rules in 02: de-duplicate Privilege Club IDs (99 duplicates) · one row per guest_id ·\nexplode stays into hotel-nights · open/closed hotel calendar · channel groups · active vs cancelled flags", 7.6, INK)
    fig.savefig(OUT / "lineage.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


# ------------------------------------------------------------------ 4. build process
def process():
    steps = [("1", "Generate data", "gen_data.py"), ("2", "Provision", "workspace · SQL DB\nlakehouse (schemas)"), ("3", "Load PMS", "load_pms.py\n483K rows (TDS)"),
             ("4", "Mirror + shortcut", "SQL → OneLake\nTables/pms"), ("5", "Land files", "OneLake DFS API"), ("6", "Notebooks", "01 · 02 · 03 · 04\nvia Jobs API"),
             ("7", "Semantic model", "TMDL · Direct Lake\nrefresh + DAX tests"), ("8", "Report", "PBIR · 5 pages\ncustom theme"), ("9", "Data agent", "definition API\n+ instructions"),
             ("10", "Ontology", "Fabric IQ\n6 entities"), ("11", "Simulator", "live bookings\nlatency ~13 s"), ("12", "Verify & docs", "portal screenshots\nrun sheet")]
    fig, ax = canvas(17, 5.0)
    w, h, gap = 2.6, 1.7, 0.18
    for i, (n, t, b) in enumerate(steps):
        row, col = divmod(i, 6)
        x = 0.3 + col * (w + gap); y = 2.75 - row * 2.25
        c = [NAVY, BLUE, TEAL, CORAL, SAND, PURPLE][col % 6] if row == 0 else [TEAL, NAVY, BLUE, PURPLE, CORAL, SAND][col % 6]
        pts = [(x, y), (x + w - 0.3, y), (x + w, y + h / 2), (x + w - 0.3, y + h), (x, y + h), (x + 0.3, y + h / 2)]
        ax.add_patch(Polygon(pts, closed=True, fc=c, ec="white", lw=2, zorder=2))
        text(ax, x + 0.55, y + h - 0.32, n, 13, NAVY if c == SAND else "#FFFFFF", "bold", ha="left")
        text(ax, x + w / 2 + 0.05, y + h / 2 + 0.12, t, 9.5, NAVY if c == SAND else "#FFFFFF", "bold")
        text(ax, x + w / 2 + 0.05, y + h / 2 - 0.42, b, 7.4, NAVY if c == SAND else "#F0F4F8")
    fig.savefig(OUT / "build-process.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


if __name__ == "__main__":
    architecture(); erd(); lineage(); process()
    print("diagrams written to", OUT)

