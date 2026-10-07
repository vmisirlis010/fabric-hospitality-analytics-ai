"""Live PMS simulator: writes new reservations into KyanosPMS (SQL) so they flow SQL -> OneLake (mirroring) -> Direct Lake.

usage:  python src/pms_live_sim.py run [--every 6]       continuous trickle of bookings (Ctrl+C to stop)
        python src/pms_live_sim.py burst [N] [HOTELCODE]  tour-operator group block, e.g. burst 25 KYN-OLY
        python src/pms_live_sim.py status                 rows written by the simulator
        python src/pms_live_sim.py reset                  delete simulator rows (ConfirmationNo starting 'KL')
"""
import sys, time, random, datetime as dt, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from sqlconn import connect

CHANNELS = [("Direct - Web", "Leisure Individual", .26), ("Booking.com", "Leisure Individual", .24), ("Expedia", "Leisure Individual", .08),
            ("Tour Operator", "Tour Operator", .20), ("Direct - Call Centre", "Leisure Individual", .06), ("Corporate & MICE", "Corporate & MICE", .10),
            ("Wholesaler", "Tour Operator", .06)]
TOUR_OPS = ["SunVoyage Holidays", "Nordic Breeze Travel", "Alpenreisen Touristik", "Mare Viaggi", "Albion Sun Tours", "Benelux Zon Reizen"]
CH_RATE = {"Direct - Web": 1.04, "Direct - Call Centre": 1.02, "Booking.com": 1.0, "Expedia": 1.0, "Tour Operator": .74, "Wholesaler": .78, "Corporate & MICE": .92}
ADR_M = [.7, .7, .72, .76, .86, 1.06, 1.32, 1.42, 1.06, .82, .72, .7]


class Sim:
    def __init__(self):
        self.con = connect(); self.t0 = time.time()
        cur = self.con.cursor()
        cur.execute("SELECT h.HotelId, h.HotelCode, h.Concept, h.OpenMMDD, h.CloseMMDD, AVG(r.RateAmount / rt.RateMultiplier) FROM pms.Hotel h "
                    "JOIN pms.Reservation r ON r.HotelId = h.HotelId JOIN pms.RoomType rt ON rt.RoomTypeId = r.RoomTypeId "
                    "WHERE r.ArrivalDate >= '2026-06-01' AND r.Channel = 'Booking.com' GROUP BY h.HotelId, h.HotelCode, h.Concept, h.OpenMMDD, h.CloseMMDD")
        self.hotels = [dict(id=r[0], code=r[1], concept=r[2], open=r[3], close=r[4], base=float(r[5])) for r in cur.fetchall()]
        cur.execute("SELECT RoomTypeId, HotelId, RoomTypeCode, RateMultiplier FROM pms.RoomType")
        self.rts = {}
        for r in cur.fetchall(): self.rts.setdefault(r[1], []).append((r[0], r[2], float(r[3])))
        cur.execute("SELECT MIN(GuestId), MAX(GuestId) FROM pms.Guest"); self.gmin, self.gmax = cur.fetchone()

    def ensure(self):
        if time.time() - self.t0 > 40 * 60:  # Entra tokens expire - reconnect proactively
            try: self.con.close()
            except Exception: pass
            self.con = connect(); self.t0 = time.time()

    def next_id(self, cur):
        cur.execute("SELECT MAX(ReservationId) FROM pms.Reservation"); return int(cur.fetchone()[0]) + 1

    def arrival_for(self, h):
        today = dt.date.today()
        for _ in range(50):
            if h["concept"] == "City Hotel":
                d = today + dt.timedelta(days=random.randint(1, 75))
            else:
                d = dt.date(2027, random.choice([5, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 10]), random.randint(1, 28))
            if h["open"] <= d.strftime("%m-%d") <= h["close"]: return d
        return today + dt.timedelta(days=30)

    def booking(self, rid, h=None, channel=None, nights=None):
        h = h or random.choice(self.hotels)
        ch, seg, _ = channel or random.choices(CHANNELS, weights=[c[2] for c in CHANNELS])[0]
        if h["concept"] == "City Hotel" and ch in ("Tour Operator", "Wholesaler"): ch, seg = "Booking.com", "Leisure Individual"
        rt = random.choice(self.rts[h["id"]])
        arr = self.arrival_for(h)
        n = nights or (random.choice([1, 2, 2, 3, 4]) if h["concept"] == "City Hotel" else random.choice([3, 4, 5, 7, 7, 7, 10, 14]))
        board = "Bed & Breakfast" if h["concept"] == "City Hotel" else ("All Inclusive" if "All-Inclusive" in h["concept"] else random.choice(["Bed & Breakfast", "Half Board"]))
        rate = round(h["base"] * rt[2] * ADR_M[arr.month - 1] / 1.06 * CH_RATE[ch] * random.uniform(.94, 1.08), 2)
        now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None, microsecond=0)
        return (rid, f"KL{random.randint(1000000, 9999999)}", h["id"], rt[0], random.randint(self.gmin, self.gmax), dt.date.today(), arr, arr + dt.timedelta(days=n), n,
                2, random.choice([0, 0, 1, 2]) if h["concept"] in ("Family Resort", "All-Inclusive Resort") else 0, ch, seg,
                random.choice(TOUR_OPS) if ch == "Tour Operator" else None, board, rate, round(rate * n, 2), 0.0, "Confirmed", None, now, now)

    def insert(self, rows):
        cur = self.con.cursor()
        cur.executemany("INSERT INTO pms.Reservation (ReservationId, ConfirmationNo, HotelId, RoomTypeId, GuestId, BookingDate, ArrivalDate, DepartureDate, Nights, "
                        "Adults, Children, Channel, MarketSegment, TourOperator, BoardType, RateAmount, RoomRevenue, ExtrasRevenue, Status, CancelDate, CreatedAt, ModifiedAt) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        self.con.commit()

    def run(self, every=6.0):
        print(f"Live PMS simulator - a new booking every ~{every:.0f}s (Ctrl+C to stop)")
        while True:
            try:
                self.ensure(); cur = self.con.cursor(); rid = self.next_id(cur)
                k = random.choice([1, 1, 1, 2, 3])
                rows = [self.booking(rid + i) for i in range(k)]
                self.insert(rows)
                hc = {h["id"]: h["code"] for h in self.hotels}
                for r in rows:
                    print(f"{r[20]:%H:%M:%S}  {r[1]}  {hc[r[2]]:8s} {r[11]:20s} arr {r[6]}  {r[8]:>2}n  EUR {r[16]:>9,.0f}", flush=True)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print("  reconnecting:", str(e)[:160]); time.sleep(5)
                try: self.con = connect(); self.t0 = time.time()
                except Exception as e2: print("  reconnect failed:", str(e2)[:160])
            time.sleep(random.uniform(every * .6, every * 1.4))

    def burst(self, n=25, code="KYN-OLY"):
        h = next(x for x in self.hotels if x["code"] == code)
        cur = self.con.cursor(); rid = self.next_id(cur)
        rows = [self.booking(rid + i, h, ("Tour Operator", "Tour Operator", 0), 7) for i in range(n)]
        op = random.choice(TOUR_OPS)
        rows = [r[:13] + (op,) + r[14:] for r in rows]
        self.insert(rows)
        print(f"Group block: {n} rooms x 7 nights at {code} from {op}, EUR {sum(r[16] for r in rows):,.0f}")

    def status(self):
        cur = self.con.cursor()
        cur.execute("SELECT COUNT(*), COALESCE(SUM(RoomRevenue),0), MAX(CreatedAt) FROM pms.Reservation WHERE ConfirmationNo LIKE 'KL%'")
        print("simulator rows: %s  revenue EUR %s  last: %s" % tuple(cur.fetchone()))

    def reset(self):
        cur = self.con.cursor(); cur.execute("DELETE FROM pms.Reservation WHERE ConfirmationNo LIKE 'KL%'"); self.con.commit()
        print("simulator rows deleted")


if __name__ == "__main__":
    a = sys.argv[1:] or ["run"]
    s = Sim()
    if a[0] == "run":
        every = float(a[a.index("--every") + 1]) if "--every" in a else 6.0
        s.run(every)
    elif a[0] == "burst":
        s.burst(int(a[1]) if len(a) > 1 else 25, a[2] if len(a) > 2 else "KYN-OLY")
    elif a[0] == "status": s.status()
    elif a[0] == "reset": s.reset()

