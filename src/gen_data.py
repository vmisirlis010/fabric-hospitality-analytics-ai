"""Generate the Kyanos Hotels & Resorts (fictional) demo dataset.

Snapshot date (AS_OF) = 2026-10-06: stays before it are realised, future stays are on-the-books (OTB).
Built-in stories:
  * Kos (KGS) and Zakynthos (ZTH) lost airline seats in 2026 -> RevPAR below last year.
  * Summer 2027 seat capacity is up strongly at Chania, Araxos and Kalamata -> forecast up.
  * Direct-booking share grows in 2026 (direct strategy working).
  * Kyanos Kos Marmari has an air-conditioning complaint cluster in Salesforce cases.
"""
import numpy as np, pandas as pd, pathlib, datetime as dt

OUT = pathlib.Path(__file__).resolve().parent.parent / "data"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(20261007)
AS_OF = pd.Timestamp("2026-10-06")
D0, D1 = pd.Timestamp("2025-01-01"), pd.Timestamp("2027-12-31")
DAYS = pd.date_range(D0, D1, freq="D")
ND = len(DAYS)

# ------------------------------------------------------------------ hotels
H = [  # code, name, destination, region, airport, stars, concept, rooms, base_adr, open, close, lat, lon, perf
    ("ELO", "Kyanos Elounda Palace", "Elounda", "Crete", "HER", 5, "Luxury Resort", 280, 420, "04-01", "11-05", 35.2650, 25.7230, 1.00),
    ("AGN", "Kyanos Agios Nikolaos Bay", "Agios Nikolaos", "Crete", "HER", 5, "Luxury Resort", 220, 310, "04-05", "10-31", 35.1900, 25.7160, 0.99),
    ("HER", "Kyanos Heraklion City", "Heraklion", "Crete", "HER", 4, "City Hotel", 160, 140, None, None, 35.3390, 25.1330, 1.00),
    ("RET", "Kyanos Rethymno Mare", "Rethymno", "Crete", "CHQ", 4, "Family Resort", 380, 190, "04-10", "10-31", 35.3700, 24.5400, 0.98),
    ("CHA", "Kyanos Chania Kalyves", "Chania", "Crete", "CHQ", 4, "Family Resort", 240, 175, "04-15", "10-25", 35.4560, 24.1700, 0.97),
    ("MAL", "Kyanos Malia Riviera", "Malia", "Crete", "HER", 4, "All-Inclusive Resort", 420, 165, "04-10", "10-31", 35.2930, 25.4630, 1.01),
    ("IXI", "Kyanos Rhodes Ixia Grand", "Ixia", "Rhodes", "RHO", 5, "Luxury Resort", 360, 260, "04-01", "11-01", 36.4170, 28.1890, 0.99),
    ("LIN", "Kyanos Lindos Blue", "Lindos", "Rhodes", "RHO", 5, "Adults-Only Resort", 180, 340, "04-10", "10-31", 36.0920, 28.0860, 1.02),
    ("FAL", "Kyanos Faliraki Family", "Faliraki", "Rhodes", "RHO", 4, "All-Inclusive Resort", 450, 155, "04-15", "10-31", 36.3420, 28.2020, 0.98),
    ("MAR", "Kyanos Kos Marmari", "Marmari", "Kos", "KGS", 4, "All-Inclusive Resort", 400, 150, "04-20", "10-25", 36.8750, 27.1650, 0.95),
    ("PSA", "Kyanos Kos Psalidi Suites", "Psalidi", "Kos", "KGS", 5, "Luxury Resort", 200, 230, "04-20", "10-31", 36.8660, 27.3080, 0.97),
    ("DAS", "Kyanos Corfu Dassia", "Dassia", "Corfu", "CFU", 5, "Luxury Resort", 320, 240, "04-25", "10-25", 39.6870, 19.8380, 0.99),
    ("KAV", "Kyanos Kavos Lagoon", "Kavos", "Corfu", "CFU", 4, "All-Inclusive Resort", 260, 140, "05-01", "10-15", 39.3850, 20.1190, 0.96),
    ("PAL", "Kyanos Paleokastritsa", "Paleokastritsa", "Corfu", "CFU", 4, "Family Resort", 150, 185, "04-25", "10-25", 39.6720, 19.7090, 0.98),
    ("ORN", "Kyanos Mykonos Ornos", "Ornos", "Cyclades", "JMK", 5, "Luxury Resort", 120, 520, "04-25", "10-31", 37.4240, 25.3200, 1.02),
    ("CAL", "Kyanos Santorini Caldera", "Imerovigli", "Cyclades", "JTR", 5, "Adults-Only Resort", 90, 610, "04-01", "11-05", 36.4320, 25.4230, 1.03),
    ("KAS", "Kyanos Kassandra Palace", "Kassandra", "Halkidiki", "SKG", 5, "Luxury Resort", 340, 250, "05-01", "10-15", 40.0210, 23.4370, 1.00),
    ("SIT", "Kyanos Sithonia Beach", "Sithonia", "Halkidiki", "SKG", 4, "Family Resort", 300, 160, "05-01", "10-10", 40.0640, 23.8560, 0.99),
    ("THE", "Kyanos Thessaloniki Center", "Thessaloniki", "Macedonia", "SKG", 4, "City Hotel", 180, 125, None, None, 40.6330, 22.9410, 1.00),
    ("OLY", "Kyanos Olympia Riviera", "Kyllini", "Peloponnese", "GPA", 5, "Family Resort", 380, 230, "04-01", "10-31", 37.9190, 21.1270, 0.97),
    ("MES", "Kyanos Messinia Bay", "Messinia", "Peloponnese", "KLX", 5, "Luxury Resort", 260, 290, "04-01", "11-01", 36.9790, 21.6640, 0.98),
    ("ACR", "Kyanos Athens Acropolis", "Athens", "Attica", "ATH", 5, "City Hotel", 210, 230, None, None, 37.9690, 23.7290, 1.01),
    ("VOU", "Kyanos Vouliagmeni Riviera", "Vouliagmeni", "Attica", "ATH", 5, "Luxury Resort", 150, 380, "03-15", "11-30", 37.8100, 23.7800, 1.00),
    ("ZAK", "Kyanos Zakynthos Laganas", "Laganas", "Zakynthos", "ZTH", 4, "All-Inclusive Resort", 260, 145, "05-01", "10-20", 37.7300, 20.8730, 0.94),
]
GM_FIRST = ["Giorgos", "Maria", "Nikos", "Eleni", "Kostas", "Katerina", "Dimitris", "Sofia", "Yannis", "Anna", "Petros", "Christina"]
GM_LAST = ["Andreou", "Papadaki", "Stavrou", "Georgiou", "Alexiou", "Nikolaou", "Vlachou", "Karras", "Manolakis", "Dimou", "Pappas", "Raptis"]
hotels = []
for i, h in enumerate(H, 1):
    code, name, dest, reg, ap, stars, concept, rooms, adr, op, cl, lat, lon, perf = h
    gm = f"{GM_FIRST[i % 12]} {GM_LAST[(i * 5) % 12]}"
    hotels.append(dict(HotelId=i, HotelCode=f"KYN-{code}", HotelName=name, Destination=dest, Region=reg, Airport=ap, Stars=stars,
                       Concept=concept, Rooms=rooms, Latitude=lat, Longitude=lon, OpenMMDD=op or "01-01", CloseMMDD=cl or "12-31",
                       IsSeasonal=int(op is not None), GeneralManager=gm, GMEmail=f"gm.{code.lower()}@kyanos-hotels.example",
                       _adr=adr * 0.78, _perf=perf))
hdf = pd.DataFrame(hotels)

# ------------------------------------------------------------------ airport seat capacity (weekly arriving seats)
AP = {"HER": 52000, "CHQ": 21000, "RHO": 38000, "KGS": 19000, "CFU": 30000, "JMK": 9000, "JTR": 14000,
      "SKG": 42000, "GPA": 4500, "KLX": 5200, "ATH": 160000, "ZTH": 14000}
G26 = {"HER": .05, "CHQ": .07, "RHO": .03, "KGS": -.13, "CFU": .04, "JMK": .03, "JTR": .02, "SKG": .06, "GPA": .04, "KLX": .08, "ATH": .06, "ZTH": -.11}
G27 = {"HER": .08, "CHQ": .13, "RHO": .04, "KGS": -.03, "CFU": .06, "JMK": .02, "JTR": .01, "SKG": .09, "GPA": .16, "KLX": .11, "ATH": .05, "ZTH": -.02}
SEAS_AP = np.array([.22, .22, .28, .55, .80, .95, 1.0, 1.0, .92, .70, .30, .22])  # leisure airports by month
SEAS_ATH = np.array([.70, .70, .78, .90, .95, 1.0, 1.0, .98, .97, .92, .78, .75])
weeks = pd.date_range("2024-12-30", D1, freq="W-MON")
seat_rows = []
for ap, base in AP.items():
    for w in weeks:
        m = w.month - 1
        s = (SEAS_ATH if ap == "ATH" else SEAS_AP)[m]
        yf = 1.0 if w.year <= 2025 else (1 + G26[ap]) * (1 + G27[ap] if w.year >= 2027 else 1)
        seats = base * s * yf * rng.normal(1, 0.025)
        seat_rows.append(dict(airport_code=ap, week_start=w.date(), scheduled_arriving_seats=int(seats),
                              scheduled_flights=int(seats / rng.uniform(172, 186)), season_year=w.year,
                              data_status="Published schedule" if w > AS_OF else "Actual"))
seats = pd.DataFrame(seat_rows)

# ------------------------------------------------------------------ room types
RT_RESORT = [("STD", "Standard Garden View", .38, 1.00), ("SUP", "Superior Sea View", .30, 1.28), ("FAM", "Family Room", .14, 1.40),
             ("DLX", "Deluxe Sea View Bungalow", .10, 1.75), ("STE", "Suite with Private Pool", .08, 2.60)]
RT_CITY = [("CLS", "Classic Room", .50, 1.00), ("SUP", "Superior Room", .30, 1.22), ("EXE", "Executive Room", .15, 1.55), ("STE", "Junior Suite", .05, 2.30)]
rts, rid = [], 1
for h in hotels:
    tpl = RT_CITY if h["Concept"] == "City Hotel" else RT_RESORT
    if h["Concept"] == "Adults-Only Resort":
        tpl = [t if t[0] != "FAM" else ("DLX2", "Deluxe Sea View Room", .14, 1.45) for t in tpl]
    left = h["Rooms"]
    for k, (c, n, share, mult) in enumerate(tpl):
        cnt = left if k == len(tpl) - 1 else int(round(h["Rooms"] * share))
        left -= cnt
        rts.append(dict(RoomTypeId=rid, HotelId=h["HotelId"], RoomTypeCode=c, RoomTypeName=n, RoomCount=cnt, RateMultiplier=mult)); rid += 1
rtdf = pd.DataFrame(rts)

# ------------------------------------------------------------------ demand curves
OCC_RESORT = np.array([0, 0, .42, .55, .74, .89, .965, .975, .91, .68, .45, 0])
OCC_CITY = np.array([.56, .60, .67, .79, .85, .86, .82, .76, .89, .88, .71, .67])
ADR_RESORT = np.array([.7, .7, .72, .76, .86, 1.06, 1.32, 1.42, 1.06, .82, .72, .7])
ADR_CITY = np.array([.80, .82, .90, 1.0, 1.08, 1.12, 1.05, .95, 1.12, 1.10, .92, .90])
month_idx = DAYS.month.values - 1
dow = DAYS.dayofweek.values
yr = DAYS.year.values


def open_mask(h):
    if not h["IsSeasonal"]:
        return np.ones(ND, bool)
    md = DAYS.strftime("%m-%d").values
    return (md >= h["OpenMMDD"]) & (md <= h["CloseMMDD"])


def target_occ(h):
    ap = h["Airport"]
    if h["Concept"] == "City Hotel":
        base = OCC_CITY[month_idx] * np.where(dow >= 4, 1.06, 0.97)
    else:
        base = OCC_RESORT[month_idx] * np.where(dow == 5, 1.02, 1.0)
    yf = np.where(yr == 2025, 1.0, np.where(yr == 2026, 1 + 0.55 * G26[ap], (1 + 0.55 * G26[ap]) * (1 + 0.6 * G27[ap])))
    wk = rng.normal(1, 0.035, ND // 7 + 2).repeat(7)[:ND]
    t = base * h["_perf"] * yf * wk * rng.normal(1, 0.02, ND)
    return np.clip(t, 0, 0.995) * open_mask(h)


CHANNELS = ["Direct - Web", "Direct - Call Centre", "Booking.com", "Expedia", "Tour Operator", "Wholesaler", "Corporate & MICE"]
MIX = {"Luxury Resort": [.30, .08, .19, .08, .22, .07, .06], "Adults-Only Resort": [.32, .07, .21, .09, .21, .06, .04],
       "Family Resort": [.20, .05, .19, .07, .40, .07, .02], "All-Inclusive Resort": [.15, .04, .18, .07, .47, .08, .01],
       "City Hotel": [.20, .04, .34, .12, .02, .06, .22]}
LEAD_MEAN = np.array([80, 55, 42, 38, 190, 140, 25])
CH_RATE = np.array([1.04, 1.02, 1.0, 1.0, .74, .78, .92])
CANCEL = np.array([.10, .07, .24, .19, .07, .09, .06])
BOARDS = ["Bed & Breakfast", "Half Board", "All Inclusive"]
BOARD_MIX = {"Luxury Resort": [.48, .40, .12], "Adults-Only Resort": [.52, .38, .10], "Family Resort": [.15, .40, .45],
             "All-Inclusive Resort": [.06, .14, .80], "City Hotel": [1, 0, 0]}
BOARD_RATE = np.array([1.0, 1.22, 1.55])
EXTRAS = np.array([62, 34, 14])  # spend per adult-night outside the board
TOUR_OPS = ["SunVoyage Holidays", "Nordic Breeze Travel", "Alpenreisen Touristik", "Mare Viaggi", "Albion Sun Tours", "Benelux Zon Reizen"]
LOS_R = (np.array([2, 3, 4, 5, 6, 7, 8, 10, 11, 14]), np.array([.03, .07, .12, .14, .10, .30, .06, .08, .03, .07]))
LOS_C = (np.array([1, 2, 3, 4, 5]), np.array([.30, .32, .22, .11, .05]))

COUNTRIES = {  # code: name, language, weight
    "GB": ("United Kingdom", "English"), "DE": ("Germany", "German"), "GR": ("Greece", "Greek"), "FR": ("France", "French"),
    "IT": ("Italy", "Italian"), "NL": ("Netherlands", "Dutch"), "PL": ("Poland", "Polish"), "US": ("United States", "English"),
    "IL": ("Israel", "Hebrew"), "SE": ("Sweden", "Swedish"), "NO": ("Norway", "Norwegian"), "RS": ("Serbia", "Serbian"),
    "BG": ("Bulgaria", "Bulgarian"), "RO": ("Romania", "Romanian"), "AT": ("Austria", "German"), "CH": ("Switzerland", "German"),
    "BE": ("Belgium", "Dutch"), "CY": ("Cyprus", "Greek"), "AU": ("Australia", "English"), "CZ": ("Czechia", "Czech"),
}
CC = list(COUNTRIES)
def cmix(region, concept):
    w = dict(GB=.20, DE=.18, GR=.10, FR=.07, IT=.05, NL=.06, PL=.05, US=.04, IL=.03, SE=.04, NO=.02, RS=.01, BG=.01, RO=.02, AT=.04, CH=.03, BE=.03, CY=.01, AU=.01, CZ=.02)
    if region == "Halkidiki": w.update(RS=.12, BG=.10, RO=.10, GR=.16, DE=.14, GB=.06)
    if region in ("Rhodes", "Kos"): w.update(GB=.26, SE=.07, NO=.05, IL=.08)
    if region == "Corfu": w.update(GB=.30, IT=.10)
    if region == "Cyclades": w.update(US=.20, AU=.05, GB=.16, FR=.10)
    if region in ("Attica", "Macedonia"): w.update(GR=.24, US=.12, CY=.05)
    if region == "Peloponnese": w.update(DE=.22, AT=.06, CH=.05)
    p = np.array([w[c] for c in CC]); return p / p.sum()

FIRST = {"GB": ["Oliver", "Amelia", "Harry", "Isla", "George", "Emily", "Jack", "Sophie", "James", "Lucy"],
         "DE": ["Lukas", "Mia", "Felix", "Hannah", "Jonas", "Lena", "Paul", "Laura", "Max", "Anna"],
         "GR": ["Giorgos", "Maria", "Nikos", "Eleni", "Kostas", "Katerina", "Dimitris", "Sofia", "Panos", "Ioanna"],
         "FR": ["Louis", "Chloe", "Hugo", "Lea", "Jules", "Manon", "Arthur", "Camille", "Theo", "Ines"],
         "IT": ["Marco", "Giulia", "Luca", "Chiara", "Matteo", "Sara", "Andrea", "Francesca", "Davide", "Elena"],
         "US": ["Michael", "Emma", "Daniel", "Olivia", "Ethan", "Ava", "Ryan", "Madison", "Tyler", "Grace"]}
LAST = {"GB": ["Smith", "Taylor", "Brown", "Wilson", "Evans", "Walker", "Wright", "Hughes", "Green", "Hall"],
        "DE": ["Muller", "Schmidt", "Weber", "Fischer", "Wagner", "Becker", "Hoffmann", "Koch", "Richter", "Klein"],
        "GR": ["Papadopoulos", "Nikolaidis", "Georgiou", "Vasileiou", "Karagiannis", "Dimitriou", "Oikonomou", "Pappas", "Makris", "Lambrou"],
        "FR": ["Martin", "Bernard", "Dubois", "Moreau", "Laurent", "Girard", "Roux", "Fournier", "Mercier", "Blanc"],
        "IT": ["Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo", "Ricci", "Marino", "Greco"],
        "US": ["Johnson", "Miller", "Davis", "Garcia", "Anderson", "Thomas", "Moore", "Jackson", "White", "Harris"]}
NAMEKEY = {"AT": "DE", "CH": "DE", "CY": "GR", "AU": "GB", "BE": "FR", "NL": "DE", "PL": "DE", "SE": "GB", "NO": "GB",
           "RS": "GR", "BG": "GR", "RO": "IT", "IL": "US", "CZ": "DE"}

# ------------------------------------------------------------------ reservations (inventory-consistent)
res = []
for h in hotels:
    tocc = target_occ(h)
    city = h["Concept"] == "City Hotel"
    los_v, los_p = LOS_C if city else LOS_R
    for rt in rtdf[rtdf.HotelId == h["HotelId"]].itertuples():
        cap = rt.RoomCount
        occ = np.zeros(ND + 40, np.int32)
        om = np.append(open_mask(h), np.zeros(40, bool))
        tgt = np.round(tocc * cap).astype(int)
        for d in range(ND):
            need = tgt[d] - occ[d]
            if need <= 0: continue
            los_draw = rng.choice(los_v, size=need, p=los_p)
            for los in los_draw:
                L = 0
                while L < los and om[d + L] and occ[d + L] < cap: L += 1
                if L == 0: break
                occ[d:d + L] += 1
                res.append((h["HotelId"], rt.RoomTypeId, d, L))
r = pd.DataFrame(res, columns=["HotelId", "RoomTypeId", "d", "Nights"])
print("stays generated:", len(r))

r = r.merge(hdf[["HotelId", "Concept", "Region", "_adr"]], on="HotelId").merge(rtdf[["RoomTypeId", "RateMultiplier", "RoomTypeCode"]], on="RoomTypeId")
r["ArrivalDate"] = DAYS[r.d.values]
n = len(r)
ch = np.empty(n, int); bd = np.empty(n, int)
for concept, mix in MIX.items():
    m = (r.Concept == concept).values
    p = np.array(mix, float)
    ch[m] = rng.choice(7, size=m.sum(), p=p / p.sum())
    bd[m] = rng.choice(3, size=m.sum(), p=BOARD_MIX[concept])
# direct strategy: in 2026+ shift ~12% of OTA bookings to direct web
shift = (r.ArrivalDate.dt.year.values >= 2026) & np.isin(ch, [2, 3]) & (rng.random(n) < 0.12)
ch[shift] = 0
lead = np.clip(rng.lognormal(np.log(LEAD_MEAN[ch]) - 0.18, 0.66), 0, 430).astype(int)
lead = np.where(r.Concept.values == "City Hotel", (lead * 0.45).astype(int), lead)
r["Channel"] = np.array(CHANNELS)[ch]; r["_ch"] = ch
r["BoardType"] = np.array(BOARDS)[bd]; r["_bd"] = bd
r["BookingDate"] = r.ArrivalDate - pd.to_timedelta(lead, unit="D")
r["DepartureDate"] = r.ArrivalDate + pd.to_timedelta(r.Nights, unit="D")
mi = r.ArrivalDate.dt.month.values - 1
seas = np.where(r.Concept.values == "City Hotel", ADR_CITY[mi], ADR_RESORT[mi])
soft = r.HotelId.isin([10, 11, 24]).values  # Kos & Zakynthos held rates flat in 2026 to defend volume
yfac = np.select([r.ArrivalDate.dt.year.values == 2025, r.ArrivalDate.dt.year.values == 2026], [1.0, np.where(soft, 0.99, 1.065)], np.where(soft, 1.03, 1.11))
rate = r._adr.values * r.RateMultiplier.values * seas * CH_RATE[ch] * BOARD_RATE[bd] * yfac * rng.normal(1, 0.05, n)
r["RateAmount"] = np.round(rate, 2)
r["RoomRevenue"] = np.round(rate * r.Nights.values, 2)
fam = np.isin(r.Concept.values, ["Family Resort", "All-Inclusive Resort"])
r["Adults"] = np.where(r.Concept.values == "City Hotel", rng.choice([1, 2], n, p=[.45, .55]), 2)
r["Children"] = np.where(fam & np.isin(r.RoomTypeCode.values, ["FAM", "SUP", "DLX", "STE"]), rng.choice([0, 1, 2], n, p=[.25, .35, .40]), 0)
r["Children"] = np.where(r.Concept.values == "Adults-Only Resort", 0, r.Children)
seg = np.select([np.isin(ch, [4, 5]), ch == 6], ["Tour Operator", "Corporate & MICE"], "Leisure Individual")
r["MarketSegment"] = seg
r["TourOperator"] = np.where(ch == 4, np.array(TOUR_OPS)[rng.integers(0, len(TOUR_OPS), n)], None)
r["Status"] = "Checked-Out"
r["CancelDate"] = pd.NaT

# cancellations (did not consume inventory)
pc = CANCEL[ch] / (1 - CANCEL[ch])
cx = r[rng.random(n) < pc].copy()
cx["Status"] = "Cancelled"
span = (cx.ArrivalDate - cx.BookingDate).dt.days.clip(lower=1).values
cx["CancelDate"] = cx.BookingDate + pd.to_timedelta((rng.random(len(cx)) * span).astype(int), unit="D")
r = pd.concat([r, cx], ignore_index=True)

# snapshot logic
book_ok = r.BookingDate <= AS_OF
r = r[book_ok].copy()
fut_cancel = (r.Status == "Cancelled") & (r.CancelDate > AS_OF)
r.loc[fut_cancel, "Status"] = "Confirmed"; r.loc[fut_cancel, "CancelDate"] = pd.NaT
act = r.Status != "Cancelled"
r.loc[act & (r.ArrivalDate > AS_OF), "Status"] = "Confirmed"
r.loc[act & (r.ArrivalDate <= AS_OF) & (r.DepartureDate > AS_OF), "Status"] = "In-House"
past = act & (r.DepartureDate <= AS_OF)
ns = past & (rng.random(len(r)) < 0.008)
r.loc[ns, "Status"] = "No-Show"
nights_done = np.where(r.Status == "Checked-Out", r.Nights, np.where(r.Status == "In-House", (AS_OF - r.ArrivalDate).dt.days, 0))
pax = r.Adults.values + 0.5 * r.Children.values
lux = np.where(r.Concept.values == "Luxury Resort", 1.35, np.where(r.Concept.values == "Adults-Only Resort", 1.25, 1.0))
r["ExtrasRevenue"] = np.round(EXTRAS[r._bd.values] * lux * pax * nights_done * rng.normal(1, 0.18, len(r)).clip(0.3), 2)
r.loc[r.Status.isin(["Cancelled", "No-Show"]), ["ExtrasRevenue"]] = 0
r.loc[r.Status == "No-Show", "RoomRevenue"] = r.loc[r.Status == "No-Show", "RateAmount"]
r.loc[r.Status == "Cancelled", "RoomRevenue"] = 0

r = r.sort_values(["BookingDate", "ArrivalDate"]).reset_index(drop=True)
r["ReservationId"] = np.arange(1, len(r) + 1) + 4_000_000
r["ConfirmationNo"] = ["KY" + format(x, "07d") for x in rng.integers(1_000_000, 9_999_999, len(r))]
ts = r.BookingDate + pd.to_timedelta(rng.integers(7 * 3600, 23 * 3600, len(r)), unit="s")
r["CreatedAt"] = ts
r["ModifiedAt"] = np.where(r.Status == "Cancelled", r.CancelDate + pd.Timedelta(hours=10), ts)
r.loc[r.Status.isin(["Checked-Out", "No-Show"]), "ModifiedAt"] = r.DepartureDate + pd.Timedelta(hours=11)
print("reservations kept:", len(r), r.Status.value_counts().to_dict())

# ------------------------------------------------------------------ guests (repeaters biased to the head of each country pool)
gid_next, pools, guests = 1, {}, []
hreg = hdf.set_index("HotelId").Region.to_dict(); hcon = hdf.set_index("HotelId").Concept.to_dict()
r["Country"] = ""
for hid in hdf.HotelId:
    m = (r.HotelId == hid).values
    r.loc[m, "Country"] = rng.choice(CC, size=m.sum(), p=cmix(hreg[hid], hcon[hid]))
gid = np.empty(len(r), np.int64)
for c in CC:
    m = (r.Country == c).values
    k = m.sum()
    pool = max(int(k * 0.78), 1)
    idx = np.floor(pool * rng.random(k) ** 1.6).astype(int)
    gid[m] = gid_next + idx
    nk = NAMEKEY.get(c, c)
    fn, ln = FIRST[nk], LAST[nk]
    for j in range(pool):
        g = gid_next + j
        f, l = fn[(g * 7) % 10], ln[(g * 13 + j // 10) % 10]
        guests.append((g, f, l, f"{f}.{l}{g % 9973}@example.com".lower(), c, COUNTRIES[c][0], COUNTRIES[c][1]))
    gid_next += pool
r["GuestId"] = gid
gdf = pd.DataFrame(guests, columns=["GuestId", "FirstName", "LastName", "Email", "Country", "CountryName", "Language"])
gdf = gdf[gdf.GuestId.isin(r.GuestId)]
stays = r[r.Status.isin(["Checked-Out", "In-House", "Confirmed"])].groupby("GuestId").agg(n=("ReservationId", "size"), ltv=("RoomRevenue", "sum"), nights=("Nights", "sum"))
gdf = gdf.merge(stays, left_on="GuestId", right_index=True, how="left").fillna({"n": 0, "ltv": 0, "nights": 0})
pm = np.clip(0.06 + 0.16 * (gdf.n.values - 1), 0.06, 0.9)
mem = rng.random(len(gdf)) < pm
gdf["LoyaltyNumber"] = np.where(mem, ["KC" + format(x, "07d") for x in rng.integers(1_000_000, 9_999_999, len(gdf))], None)
first_book = r.groupby("GuestId").CreatedAt.min()
gdf["CreatedAt"] = gdf.GuestId.map(first_book)
print("guests:", len(gdf), "members:", int(mem.sum()))

# ------------------------------------------------------------------ Salesforce CRM export
members = gdf[gdf.LoyaltyNumber.notna()].copy()
tier = np.select([members.nights >= 40, members.nights >= 21, members.nights >= 10], ["Platinum", "Gold", "Silver"], "Blue")
PREF = ["Sea view", "Late check-out", "Quiet room", "Spa treatments", "Kids club", "Fine dining", "Airport transfer", "High floor"]
crm_members = pd.DataFrame(dict(
    member_id=members.LoyaltyNumber, email=members.Email, first_name=members.FirstName, last_name=members.LastName,
    country_code=members.Country, tier=tier,
    join_date=(pd.Timestamp("2018-03-01") + pd.to_timedelta(rng.integers(0, 3100, len(members)), unit="D")).date,
    lifetime_nights=members.nights.astype(int), lifetime_room_revenue=members.ltv.round(2),
    preferred_language=members.Language, marketing_opt_in=rng.random(len(members)) < 0.71,
    top_preference=np.array(PREF)[rng.integers(0, len(PREF), len(members))],
    sf_account_id=["001KY" + format(x, "010d") for x in rng.integers(10**9, 10**10 - 1, len(members))]))
crm_members.loc[crm_members.join_date > AS_OF.date(), "join_date"] = AS_OF.date()

CASE_CAT = ["Room cleanliness", "Noise", "Food & beverage", "Check-in delay", "Air conditioning", "Wi-Fi", "Special request", "Compliment - staff", "Billing"]
CASE_P = np.array([.13, .10, .14, .10, .08, .08, .15, .17, .05])
done = r[r.Status.isin(["Checked-Out", "In-House"])]
cases = done[rng.random(len(done)) < 0.045].copy()
cat = rng.choice(len(CASE_CAT), size=len(cases), p=CASE_P)
kos = (cases.HotelId == 10).values & (cases.ArrivalDate.dt.year.values == 2026)
cat[kos & (rng.random(len(cases)) < 0.35)] = 4  # A/C complaint cluster at Kos Marmari
cats = np.array(CASE_CAT)[cat]
csat = np.where(cats == "Compliment - staff", rng.choice([4, 5], len(cases), p=[.2, .8]),
                np.where(np.isin(cats, ["Special request"]), rng.choice([3, 4, 5], len(cases), p=[.2, .4, .4]), rng.choice([1, 2, 3, 4], len(cases), p=[.18, .32, .32, .18])))
hcode = hdf.set_index("HotelId").HotelCode.to_dict()
crm_cases = pd.DataFrame(dict(
    case_id=["500KY" + format(x, "010d") for x in rng.integers(10**9, 10**10 - 1, len(cases))],
    confirmation_no=cases.ConfirmationNo.values, hotel_code=cases.HotelId.map(hcode).values,
    created_date=(cases.ArrivalDate + pd.to_timedelta((rng.random(len(cases)) * cases.Nights.values).astype(int), unit="D")).dt.date.values,
    category=np.where(cats == "Compliment - staff", "Compliment", np.where(cats == "Special request", "Request", "Complaint")),
    sub_category=cats, origin=rng.choice(["Front desk", "Email", "Guest app", "Phone", "Social media"], len(cases), p=[.42, .2, .2, .1, .08]),
    status=np.where(cases.Status.values == "In-House", rng.choice(["Open", "Closed"], len(cases), p=[.6, .4]), "Closed"),
    csat_score=csat))

# ------------------------------------------------------------------ SAP ERP monthly costs
real = r[r.Status.isin(["Checked-Out", "In-House", "No-Show"])].copy()
real["month"] = real.ArrivalDate.dt.to_period("M").dt.to_timestamp()
mrev = real.groupby(["HotelId", "month"]).agg(room=("RoomRevenue", "sum"), extras=("ExtrasRevenue", "sum")).reset_index()
ota = real[real.Channel.isin(["Booking.com", "Expedia"])].groupby(["HotelId", "month"]).RoomRevenue.sum().rename("ota")
to = real[real.Channel.isin(["Tour Operator", "Wholesaler"])].groupby(["HotelId", "month"]).RoomRevenue.sum().rename("to")
mrev = mrev.merge(ota, on=["HotelId", "month"], how="left").merge(to, on=["HotelId", "month"], how="left").fillna(0)
mrev = mrev.merge(hdf[["HotelId", "HotelCode", "Rooms", "Concept"]], on="HotelId")
cost_rows = []
for x in mrev.itertuples():
    if x.month > AS_OF: continue
    tot = x.room + x.extras
    e_y = 1.12 if x.month.year >= 2026 else 1.0
    lines = {"Payroll": x.Rooms * (2900 if x.Concept != "City Hotel" else 2300) * rng.normal(1, .04) * (1.05 if x.month.year >= 2026 else 1),
             "Food & beverage cost of sales": (x.extras + 0.18 * x.room) * 0.38 * rng.normal(1, .05),
             "Energy & utilities": x.Rooms * 30 * 14.5 * e_y * rng.normal(1, .06) * (1.25 if x.month.month in (7, 8) else 1),
             "Commissions": 0.17 * x.ota + 0.06 * x.to,
             "Maintenance & repairs": tot * 0.035 * rng.normal(1, .2),
             "Sales & marketing": tot * 0.025 * rng.normal(1, .1)}
    for k, v in lines.items():
        cost_rows.append(dict(company_code="KY01", plant=x.HotelCode, fiscal_period=x.month.strftime("%Y-%m"), posting_month=x.month.date(),
                              gl_account={"Payroll": "600100", "Food & beverage cost of sales": "500200", "Energy & utilities": "610300",
                                          "Commissions": "620400", "Maintenance & repairs": "630500", "Sales & marketing": "640600"}[k],
                              cost_category=k, amount_eur=round(max(v, 0), 2)))
erp = pd.DataFrame(cost_rows)

# ------------------------------------------------------------------ write
pms_res = r[["ReservationId", "ConfirmationNo", "HotelId", "RoomTypeId", "GuestId", "BookingDate", "ArrivalDate", "DepartureDate", "Nights",
             "Adults", "Children", "Channel", "MarketSegment", "TourOperator", "BoardType", "RateAmount", "RoomRevenue", "ExtrasRevenue",
             "Status", "CancelDate", "CreatedAt", "ModifiedAt"]].copy()
for c in ["BookingDate", "ArrivalDate", "DepartureDate", "CancelDate"]:
    pms_res[c] = pms_res[c].dt.date
pms_res.to_parquet(OUT / "pms_reservation.parquet", index=False)
hdf.drop(columns=[c for c in hdf.columns if c.startswith("_")]).to_csv(OUT / "pms_hotel.csv", index=False)
rtdf.to_csv(OUT / "pms_roomtype.csv", index=False)
gdf[["GuestId", "FirstName", "LastName", "Email", "Country", "CountryName", "Language", "LoyaltyNumber", "CreatedAt"]].to_parquet(OUT / "pms_guest.parquet", index=False)
crm_members.to_csv(OUT / "salesforce_privilege_club_members.csv", index=False)
crm_cases.to_csv(OUT / "salesforce_guest_cases.csv", index=False)
erp.to_csv(OUT / "sap_hotel_costs_monthly.csv", index=False)
seats.to_csv(OUT / "airport_seat_capacity_weekly.csv", index=False)
print("done:", {f.name: f.stat().st_size for f in OUT.iterdir()})


