"""Create the pms schema in KyanosPMS (the stand-in for the on-prem PMS on SQL Server) and bulk load it."""
import pathlib, sys, time, datetime as dt
import pandas as pd, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from sqlconn import connect

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"

DDL = """
IF SCHEMA_ID('pms') IS NULL EXEC('CREATE SCHEMA pms');
IF OBJECT_ID('dbo.t_perf') IS NOT NULL DROP TABLE dbo.t_perf;
IF OBJECT_ID('pms.Reservation') IS NOT NULL DROP TABLE pms.Reservation;
IF OBJECT_ID('pms.Guest') IS NOT NULL DROP TABLE pms.Guest;
IF OBJECT_ID('pms.RoomType') IS NOT NULL DROP TABLE pms.RoomType;
IF OBJECT_ID('pms.Hotel') IS NOT NULL DROP TABLE pms.Hotel;
CREATE TABLE pms.Hotel (
  HotelId INT NOT NULL PRIMARY KEY, HotelCode VARCHAR(10) NOT NULL, HotelName NVARCHAR(80) NOT NULL, Destination NVARCHAR(40), Region NVARCHAR(40),
  Airport CHAR(3), Stars TINYINT, Concept NVARCHAR(40), Rooms INT, Latitude DECIMAL(9,6), Longitude DECIMAL(9,6),
  OpenMMDD CHAR(5), CloseMMDD CHAR(5), IsSeasonal BIT, GeneralManager NVARCHAR(60), GMEmail NVARCHAR(80));
CREATE TABLE pms.RoomType (
  RoomTypeId INT NOT NULL PRIMARY KEY, HotelId INT NOT NULL, RoomTypeCode VARCHAR(6), RoomTypeName NVARCHAR(60), RoomCount INT, RateMultiplier DECIMAL(5,2));
CREATE TABLE pms.Guest (
  GuestId INT NOT NULL PRIMARY KEY, FirstName NVARCHAR(40), LastName NVARCHAR(40), Email NVARCHAR(120), Country CHAR(2), CountryName NVARCHAR(40),
  Language NVARCHAR(20), LoyaltyNumber VARCHAR(12) NULL, CreatedAt DATETIME2(3));
CREATE TABLE pms.Reservation (
  ReservationId BIGINT NOT NULL PRIMARY KEY, ConfirmationNo VARCHAR(12) NOT NULL, HotelId INT NOT NULL, RoomTypeId INT NOT NULL, GuestId INT NOT NULL,
  BookingDate DATE NOT NULL, ArrivalDate DATE NOT NULL, DepartureDate DATE NOT NULL, Nights INT NOT NULL, Adults TINYINT, Children TINYINT,
  Channel NVARCHAR(30), MarketSegment NVARCHAR(30), TourOperator NVARCHAR(40) NULL, BoardType NVARCHAR(20), RateAmount DECIMAL(10,2),
  RoomRevenue DECIMAL(12,2), ExtrasRevenue DECIMAL(12,2), Status NVARCHAR(15), CancelDate DATE NULL, CreatedAt DATETIME2(3), ModifiedAt DATETIME2(3));
"""


def py(v):
    if v is None: return None
    if isinstance(v, float) and np.isnan(v): return None
    if isinstance(v, (np.integer,)): return int(v)
    if isinstance(v, (np.floating,)): return None if np.isnan(v) else float(v)
    if isinstance(v, np.bool_): return bool(v)
    if isinstance(v, pd.Timestamp): return None if pd.isna(v) else v.to_pydatetime().replace(microsecond=(v.microsecond // 1000) * 1000)
    if v is pd.NaT: return None
    return v


def load(cur, table, df, batch=20000):
    t0 = time.time()
    cols = list(df.columns)
    data = [tuple(py(x) for x in row) for row in df.itertuples(index=False, name=None)]
    # executemany with an Entra-token connection (mssql-python bulkcopy opens a second connection without the token)
    q = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})"
    for i in range(0, len(data), batch):
        cur.executemany(q, data[i:i + batch]); cur.connection.commit()
    how = "executemany"
    cur.connection.commit()
    print(f"  {table}: {len(df):,} rows in {time.time() - t0:.0f}s ({how})")


def main():
    """Drop/create the pms schema tables and load data/ into them (about 5 minutes for ~740K rows)."""
    con = connect(); cur = con.cursor()
    for stmt in [s for s in DDL.split(";\n") if s.strip()]:
        cur.execute(stmt)
    con.commit(); print("  schema created")
    load(cur, "pms.Hotel", pd.read_csv(DATA / "pms_hotel.csv"))
    load(cur, "pms.RoomType", pd.read_csv(DATA / "pms_roomtype.csv"))
    g = pd.read_parquet(DATA / "pms_guest.parquet"); g["LoyaltyNumber"] = g.LoyaltyNumber.where(g.LoyaltyNumber.notna(), None)
    load(cur, "pms.Guest", g)
    r = pd.read_parquet(DATA / "pms_reservation.parquet")
    r["TourOperator"] = r.TourOperator.where(r.TourOperator.notna(), None)
    r["CancelDate"] = r.CancelDate.where(r.CancelDate.notna(), None)
    load(cur, "pms.Reservation", r)
    cur.execute("SELECT COUNT(*) FROM pms.Reservation"); print("  check:", cur.fetchone()[0])
    cur.execute("CREATE INDEX IX_Res_Booking ON pms.Reservation(BookingDate) INCLUDE (HotelId, Status)"); con.commit()


if __name__ == "__main__":
    main()
