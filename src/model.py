"""TMDL definition of the Kyanos Hotels Direct Lake semantic model."""

S, I, D, B, DT, DEC = "string", "int64", "double", "boolean", "dateTime", "decimal"
EUR, EUR2, PCT, PTS, INT = "\\€#,0", "\\€#,0.00", "0.0%", "+0.0%;-0.0%;0.0%", "#,0"

# table -> (schema, entity, description, [(column, type, opts)], [measures (name, expr, fmt, folder, description)])
TABLES = {
    "dim_date": ("gold", "dim_date", "Calendar 2025-2027. Snapshot (today) is 6 Oct 2026; is_closed_ytd = Jan-Sep closed months.", [
        ("date", DT, {"key": True, "fmt": "dd mmm yyyy"}), ("year", I, {"none": True}), ("quarter", S, {}), ("month_num", I, {"hidden": True, "none": True}),
        ("month", S, {"sort": "month_num"}), ("year_month", S, {}), ("month_start", DT, {"fmt": "mmm yyyy"}), ("week_start", DT, {"fmt": "dd mmm yyyy"}),
        ("weekday_num", I, {"hidden": True, "none": True}), ("weekday", S, {"sort": "weekday_num"}), ("season", S, {}),
        ("is_actual", B, {}), ("is_closed_ytd", B, {})], []),
    "dim_hotel": ("gold", "dim_hotel", "The 24 Kyanos hotels and resorts with destination, airport, concept and general manager.", [
        ("hotel_id", I, {"hidden": True, "none": True}), ("hotel_code", S, {}), ("hotel_name", S, {}), ("hotel_short_name", S, {}), ("destination", S, {}),
        ("region", S, {"cat": "StateOrProvince"}), ("airport_code", S, {}), ("stars", I, {"none": True}), ("concept", S, {}), ("rooms", I, {"none": True}),
        ("latitude", D, {"cat": "Latitude", "none": True}), ("longitude", D, {"cat": "Longitude", "none": True}), ("operating_model", S, {}),
        ("general_manager", S, {}), ("gm_email", S, {})], []),
    "dim_airport": ("gold", "dim_airport", "Greek airports serving the hotels.", [
        ("airport_code", S, {}), ("airport_name", S, {}), ("airport_region", S, {})], []),
    "dim_guest": ("gold", "dim_guest", "Guest profile from the PMS enriched with Salesforce Privilege Club membership.", [
        ("guest_id", I, {"hidden": True, "none": True}), ("guest_name", S, {}), ("email", S, {}), ("country_code", S, {}), ("country", S, {"cat": "Country"}),
        ("language", S, {}), ("member_id", S, {}), ("is_member", B, {}), ("loyalty_tier", S, {}), ("marketing_opt_in", B, {}),
        ("top_preference", S, {}), ("lifetime_nights", I, {"none": True})], []),
    "fact_hotel_day": ("gold", "fact_hotel_day", "One row per hotel per day: rooms available vs sold and revenue. Future dates hold on-the-books business.", [
        ("hotel_id", I, {"hidden": True, "none": True}), ("date", DT, {"hidden": True}), ("rooms_available", I, {"hidden": True}), ("rooms_sold", I, {"hidden": True}),
        ("room_revenue", D, {"hidden": True}), ("extras_revenue", D, {"hidden": True}), ("arrivals", I, {"hidden": True}), ("is_actual", B, {"hidden": True}),
        ("total_revenue", D, {"hidden": True})], [
        ("Rooms Available", "SUM(fact_hotel_day[rooms_available])", INT, "KPIs", "Saleable room nights (hotel open days x rooms)."),
        ("Rooms Sold", "SUM(fact_hotel_day[rooms_sold])", INT, "KPIs", "Occupied room nights (on-the-books for future dates)."),
        ("Occupancy %", "DIVIDE([Rooms Sold], [Rooms Available])", PCT, "KPIs", "Rooms sold / rooms available."),
        ("Room Revenue", "SUM(fact_hotel_day[room_revenue])", EUR, "KPIs", "Accommodation revenue in EUR."),
        ("F&B and Other Revenue", "SUM(fact_hotel_day[extras_revenue])", EUR, "KPIs", "Food & beverage, spa and other outlet revenue in EUR."),
        ("Total Revenue", "SUM(fact_hotel_day[total_revenue])", EUR, "KPIs", "Room + F&B and other revenue in EUR."),
        ("ADR", "DIVIDE([Room Revenue], [Rooms Sold])", EUR2, "KPIs", "Average daily rate = room revenue / rooms sold."),
        ("RevPAR", "DIVIDE([Room Revenue], [Rooms Available])", EUR2, "KPIs", "Revenue per available room = room revenue / rooms available."),
        ("TRevPAR", "DIVIDE([Total Revenue], [Rooms Available])", EUR2, "KPIs", "Total revenue per available room."),
        ("Guest Arrivals", "SUM(fact_hotel_day[arrivals])", INT, "KPIs", "Number of arriving reservations."),
        ("Occupancy % LY", "CALCULATE([Occupancy %], SAMEPERIODLASTYEAR(dim_date[date]))", PCT, "Last Year", "Occupancy for the same period last year."),
        ("ADR LY", "CALCULATE([ADR], SAMEPERIODLASTYEAR(dim_date[date]))", EUR2, "Last Year", "ADR for the same period last year."),
        ("RevPAR LY", "CALCULATE([RevPAR], SAMEPERIODLASTYEAR(dim_date[date]))", EUR2, "Last Year", "RevPAR for the same period last year."),
        ("Room Revenue LY", "CALCULATE([Room Revenue], SAMEPERIODLASTYEAR(dim_date[date]))", EUR, "Last Year", "Room revenue same period last year."),
        ("Total Revenue LY", "CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(dim_date[date]))", EUR, "Last Year", "Total revenue same period last year."),
        ("Occupancy vs LY (pts)", "IF(NOT ISBLANK([Occupancy % LY]), [Occupancy %] - [Occupancy % LY])", PTS, "Last Year", "Change in occupancy vs last year, in percentage points."),
        ("ADR vs LY %", "DIVIDE([ADR] - [ADR LY], [ADR LY])", PTS, "Last Year", "ADR growth vs last year."),
        ("RevPAR vs LY %", "DIVIDE([RevPAR] - [RevPAR LY], [RevPAR LY])", PTS, "Last Year", "RevPAR growth vs last year."),
        ("Total Revenue vs LY %", "DIVIDE([Total Revenue] - [Total Revenue LY], [Total Revenue LY])", PTS, "Last Year", "Total revenue growth vs last year."),
    ]),
    "fact_hotel_cost": ("gold", "fact_hotel_cost", "Monthly operating costs per hotel from SAP (payroll, F&B cost of sales, energy, commissions, maintenance, marketing).", [
        ("hotel_id", I, {"hidden": True, "none": True}), ("month_start", DT, {"hidden": True}), ("cost_category", S, {}), ("gl_account", S, {}),
        ("amount_eur", D, {"hidden": True})], [
        ("Operating Costs", "SUM(fact_hotel_cost[amount_eur])", EUR, "P&L", "Operating costs from SAP in EUR."),
        ("GOP", "[Total Revenue] - [Operating Costs]", EUR, "P&L", "Gross operating profit = total revenue - operating costs."),
        ("GOP Margin %", "DIVIDE([GOP], [Total Revenue])", PCT, "P&L", "GOP as a share of total revenue."),
        ("GOPPAR", "DIVIDE([GOP], [Rooms Available])", EUR2, "P&L", "Gross operating profit per available room."),
        ("GOP Margin % LY", "CALCULATE([GOP Margin %], SAMEPERIODLASTYEAR(dim_date[date]))", PCT, "P&L", "GOP margin same period last year."),
    ]),
    "fact_reservation": ("gold", "fact_reservation", "Every PMS reservation (incl. cancellations) with channel, segment, board, lead time and revenue.", [
        ("reservation_id", I, {"hidden": True, "none": True}), ("confirmation_no", S, {}), ("hotel_id", I, {"hidden": True, "none": True}),
        ("guest_id", I, {"hidden": True, "none": True}), ("room_type", S, {}), ("booking_date", DT, {"fmt": "dd mmm yyyy"}),
        ("arrival_date", DT, {"fmt": "dd mmm yyyy"}), ("departure_date", DT, {"fmt": "dd mmm yyyy"}), ("nights", I, {"none": True}),
        ("lead_time_days", I, {"none": True}), ("channel", S, {}), ("channel_group", S, {}), ("market_segment", S, {}), ("tour_operator", S, {}),
        ("board_type", S, {}), ("adults", I, {"none": True}), ("children", I, {"none": True}), ("status", S, {}), ("is_cancelled", B, {"hidden": True}),
        ("is_active", B, {"hidden": True}), ("rate_amount", D, {"hidden": True}), ("room_revenue", D, {"hidden": True}), ("extras_revenue", D, {"hidden": True}),
        ("cancel_date", DT, {"fmt": "dd mmm yyyy"}), ("created_at", DT, {"hidden": True})], [
        ("Bookings", "CALCULATE(COUNTROWS(fact_reservation), fact_reservation[is_active])", INT, "Bookings", "Active reservations (not cancelled / no-show), by arrival date."),
        ("Cancellations", "CALCULATE(COUNTROWS(fact_reservation), fact_reservation[is_cancelled])", INT, "Bookings", "Cancelled reservations."),
        ("Cancellation Rate %", "DIVIDE([Cancellations], [Cancellations] + [Bookings])", PCT, "Bookings", "Cancelled / all reservations."),
        ("Avg Lead Time (days)", "CALCULATE(AVERAGE(fact_reservation[lead_time_days]), fact_reservation[is_active])", "0", "Bookings", "Average days between booking and arrival."),
        ("Avg Length of Stay", "CALCULATE(AVERAGE(fact_reservation[nights]), fact_reservation[is_active])", "0.0", "Bookings", "Average nights per stay."),
        ("Booked Room Revenue", "CALCULATE(SUM(fact_reservation[room_revenue]), fact_reservation[is_active])", EUR, "Bookings", "Room revenue of active reservations."),
        ("Direct Share %", "DIVIDE(CALCULATE([Booked Room Revenue], fact_reservation[channel_group] = \"Direct\"), [Booked Room Revenue])", PCT, "Bookings",
         "Share of room revenue booked direct (web + call centre)."),
        ("Direct Share % LY", "CALCULATE([Direct Share %], SAMEPERIODLASTYEAR(dim_date[date]))", PCT, "Bookings", "Direct share same period last year."),
        ("Privilege Club Share %", "DIVIDE(CALCULATE([Bookings], dim_guest[is_member] = TRUE()), [Bookings])", PCT, "Guests", "Share of stays by Privilege Club members."),
    ]),
    "fact_guest_case": ("gold", "fact_guest_case", "Salesforce Service Cloud guest cases (complaints, requests, compliments) with CSAT.", [
        ("case_id", S, {}), ("confirmation_no", S, {}), ("hotel_id", I, {"hidden": True, "none": True}), ("created_date", DT, {"fmt": "dd mmm yyyy"}),
        ("category", S, {}), ("sub_category", S, {}), ("origin", S, {}), ("status", S, {}), ("csat_score", I, {"none": True})], [
        ("Guest Cases", "COUNTROWS(fact_guest_case)", INT, "Guests", "Number of Salesforce guest cases."),
        ("Complaints", "CALCULATE([Guest Cases], fact_guest_case[category] = \"Complaint\")", INT, "Guests", "Guest complaints."),
        ("Avg Case CSAT", "AVERAGE(fact_guest_case[csat_score])", "0.00", "Guests", "Average case satisfaction score (1-5)."),
        ("Complaints per 1,000 Room Nights", "DIVIDE([Complaints], [Rooms Sold]) * 1000", "0.00", "Guests", "Complaints normalised by occupied room nights."),
    ]),
    "fact_airport_seats": ("gold", "fact_airport_seats", "Weekly scheduled arriving airline seats per airport (2027 = published schedules).", [
        ("airport_code", S, {"hidden": True}), ("week_start", DT, {"hidden": True}), ("arriving_seats", I, {"hidden": True}), ("flights", I, {"hidden": True}),
        ("season_year", I, {"none": True, "hidden": True}), ("data_status", S, {})], [
        ("Airline Seats", "CALCULATE(SUM(fact_airport_seats[arriving_seats]), TREATAS(VALUES(dim_hotel[airport_code]), dim_airport[airport_code]))", INT, "Market", "Scheduled arriving airline seats."),
        ("Airline Seats LY", "CALCULATE([Airline Seats], SAMEPERIODLASTYEAR(dim_date[date]))", INT, "Market", "Arriving seats same period last year."),
        ("Airline Seat Growth %", "DIVIDE([Airline Seats] - [Airline Seats LY], [Airline Seats LY])", PTS, "Market", "Change in scheduled arriving seats vs last year."),
    ]),
    "fact_occupancy_forecast": ("gold", "fact_occupancy_forecast", "AI occupancy forecast per hotel-day for Jan-Sep 2027 (booking pace + airline seats model, MLflow).", [
        ("hotel_id", I, {"hidden": True, "none": True}), ("date", DT, {"hidden": True}), ("rooms_available", D, {"hidden": True}), ("otb_rooms", D, {"hidden": True}),
        ("ly_otb_rooms", D, {"hidden": True}), ("forecast_rooms_sold", D, {"hidden": True}), ("forecast_room_revenue", D, {"hidden": True}),
        ("ly_rooms_sold", D, {"hidden": True}), ("ly_room_revenue", D, {"hidden": True}), ("seat_growth", D, {"hidden": True}), ("pace_vs_ly", D, {"hidden": True}),
        ("otb_occ", D, {"hidden": True}), ("forecast_occ", D, {"hidden": True}), ("ly_occ", D, {"hidden": True}), ("model_run_id", S, {"hidden": True}),
        ("snapshot_date", DT, {"hidden": True})], [
        ("Forecast Occupancy %", "DIVIDE(SUM(fact_occupancy_forecast[forecast_rooms_sold]), SUM(fact_occupancy_forecast[rooms_available]))", PCT, "Forecast 2027",
         "AI forecast occupancy for 2027."),
        ("Last Year Occupancy %", "DIVIDE(SUM(fact_occupancy_forecast[ly_rooms_sold]), SUM(fact_occupancy_forecast[rooms_available]))", PCT, "Forecast 2027",
         "Actual occupancy of the same weekdays in 2026."),
        ("On-the-Books %", "DIVIDE(SUM(fact_occupancy_forecast[otb_rooms]), SUM(fact_occupancy_forecast[rooms_available]))", PCT, "Forecast 2027",
         "Occupancy already booked for 2027 as of 6 Oct 2026."),
        ("On-the-Books LY %", "DIVIDE(SUM(fact_occupancy_forecast[ly_otb_rooms]), SUM(fact_occupancy_forecast[rooms_available]))", PCT, "Forecast 2027",
         "Occupancy that was booked for 2026 at the same point last year."),
        ("Forecast vs LY (pts)", "[Forecast Occupancy %] - [Last Year Occupancy %]", PTS, "Forecast 2027", "Forecast occupancy change vs 2026, in points."),
        ("Booking Pace vs LY (pts)", "[On-the-Books %] - [On-the-Books LY %]", PTS, "Forecast 2027", "On-the-books ahead (+) or behind (-) last year's pace."),
        ("Forecast Room Revenue", "SUM(fact_occupancy_forecast[forecast_room_revenue])", EUR, "Forecast 2027", "Forecast 2027 room revenue (LY ADR +4%)."),
        ("Forecast Room Revenue vs LY %", "DIVIDE([Forecast Room Revenue] - SUM(fact_occupancy_forecast[ly_room_revenue]), SUM(fact_occupancy_forecast[ly_room_revenue]))", PTS, "Forecast 2027",
         "Forecast room revenue growth vs 2026."),
        ("Seat Growth at Airport %", "DIVIDE(SUMX(fact_occupancy_forecast, fact_occupancy_forecast[seat_growth] * fact_occupancy_forecast[rooms_available]), SUM(fact_occupancy_forecast[rooms_available]))",
         PTS, "Forecast 2027", "Airline seat capacity change at the hotel's airport, Summer 2027 vs 2026."),
    ]),
    "live_pms_reservation": ("pms", "Reservation", "LIVE: the PMS reservation table mirrored from SQL in near real time (no ETL).", [
        ("ReservationId", I, {"hidden": True, "none": True}), ("ConfirmationNo", S, {}), ("HotelId", I, {"hidden": True, "none": True}),
        ("GuestId", I, {"hidden": True, "none": True}), ("BookingDate", DT, {"fmt": "dd mmm yyyy"}), ("ArrivalDate", DT, {"fmt": "dd mmm yyyy"}),
        ("Nights", I, {"none": True}), ("Channel", S, {}), ("MarketSegment", S, {}), ("BoardType", S, {}), ("RoomRevenue", DEC, {"hidden": True}),
        ("Status", S, {}), ("CreatedAt", DT, {"fmt": "dd mmm yyyy hh:nn:ss"})], [
        ("PMS Reservations (live)", "COUNTROWS(live_pms_reservation)", INT, "Live PMS", "All reservations currently in the PMS."),
        ("Bookings Last 24h (live)", "VAR cutoff = NOW() - 1 RETURN COALESCE(CALCULATE(COUNTROWS(live_pms_reservation), live_pms_reservation[CreatedAt] >= cutoff), 0)", INT, "Live PMS",
         "Reservations saved in the PMS in the last 24 hours (rolling)."),
        ("Booked Revenue Last 24h (live)", "VAR cutoff = NOW() - 1 RETURN COALESCE(CALCULATE(SUM(live_pms_reservation[RoomRevenue]), live_pms_reservation[CreatedAt] >= cutoff), 0)", EUR, "Live PMS",
         "Room revenue of reservations saved in the last 24 hours (rolling)."),
        ("Last PMS Booking", "FORMAT(MAX(live_pms_reservation[CreatedAt]), \"dd mmm yyyy hh:nn:ss\")", None, "Live PMS", "Timestamp of the latest reservation in the PMS."),
    ]),
}

RELS = [("fact_hotel_day", "hotel_id", "dim_hotel", "hotel_id"), ("fact_hotel_day", "date", "dim_date", "date"),
        ("fact_reservation", "hotel_id", "dim_hotel", "hotel_id"), ("fact_reservation", "arrival_date", "dim_date", "date"),
        ("fact_reservation", "guest_id", "dim_guest", "guest_id"),
        ("fact_hotel_cost", "hotel_id", "dim_hotel", "hotel_id"), ("fact_hotel_cost", "month_start", "dim_date", "date"),
        ("fact_guest_case", "hotel_id", "dim_hotel", "hotel_id"), ("fact_guest_case", "created_date", "dim_date", "date"),
        ("fact_airport_seats", "airport_code", "dim_airport", "airport_code"), ("fact_airport_seats", "week_start", "dim_date", "date"),
        ("fact_occupancy_forecast", "hotel_id", "dim_hotel", "hotel_id"), ("fact_occupancy_forecast", "date", "dim_date", "date"),
        ("dim_hotel", "airport_code", "dim_airport", "airport_code"),
        ("live_pms_reservation", "HotelId", "dim_hotel", "hotel_id")]


def q(name):
    return f"'{name}'" if any(c in name for c in " %&-(),.'/") else name


def table_tmdl(name):
    schema, entity, desc, cols, measures = TABLES[name]
    out = [f"/// {desc}", f"table {q(name)}"]
    if name == "dim_date":
        out.append("\tdataCategory: Time")
    out.append("")
    for mname, expr, fmt, folder, mdesc in measures:
        out.append(f"\t/// {mdesc}")
        out.append(f"\tmeasure {q(mname)} = {expr}")
        if fmt: out.append(f"\t\tformatString: {fmt}")
        out.append(f"\t\tdisplayFolder: {folder}")
        out.append("")
    for c, t, o in cols:
        out.append(f"\tcolumn {q(c)}")
        out.append(f"\t\tdataType: {t}")
        if o.get("key"): out.append("\t\tisKey")
        if o.get("hidden"): out.append("\t\tisHidden")
        if o.get("fmt"): out.append(f"\t\tformatString: {o['fmt']}")
        if o.get("cat"): out.append(f"\t\tdataCategory: {o['cat']}")
        if o.get("none") or t in (B,) or (t == I and o.get("hidden")): out.append("\t\tsummarizeBy: none")
        if o.get("sort"): out.append(f"\t\tsortByColumn: {o['sort']}")
        out.append(f"\t\tsourceColumn: {c}")
        out.append("")
    out += [f"\tpartition {q(name)} = entity", "\t\tmode: directLake", "\t\tsource", f"\t\t\tentityName: {entity}",
            f"\t\t\tschemaName: {schema}", "\t\t\texpressionSource: DL_Lakehouse", ""]
    return "\n".join(out)


def model_parts(ws, lh):
    from fab import part
    parts = [
        part("definition.pbism", {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
                                  "version": "4.2", "settings": {}}),
        part("definition/database.tmdl", "database\n\tcompatibilityLevel: 1702\n"),
        part("definition/model.tmdl", "model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tdiscourageImplicitMeasures\n\tsourceQueryCulture: en-US\n\n"
             + "\n".join(f"ref table {q(t)}" for t in TABLES) + "\n\nref role 'Crete Region Manager'\nref role 'Hotel General Manager'\n"),
        part("definition/expressions.tmdl", "expression DL_Lakehouse =\n\t\tlet\n\t\t\tSource = AzureStorage.DataLake(\"https://onelake.dfs.fabric.microsoft.com/"
             f"{ws}/{lh}\", [HierarchicalNavigation=true])\n\t\tin\n\t\t\tSource\n"),
        part("definition/relationships.tmdl", "\n".join(
            f"relationship r_{a}_{ac}_{b}\n\tfromColumn: {q(a)}.{q(ac)}\n\ttoColumn: {q(b)}.{q(bc)}\n" for a, ac, b, bc in RELS)),
        part("definition/roles/Crete Region Manager.tmdl", "role 'Crete Region Manager'\n\tmodelPermission: read\n\n\ttablePermission dim_hotel = [region] = \"Crete\"\n"),
        part("definition/roles/Hotel General Manager.tmdl", "role 'Hotel General Manager'\n\tmodelPermission: read\n\n\ttablePermission dim_hotel = [gm_email] = USERPRINCIPALNAME()\n"),
    ]
    for t in TABLES:
        parts.append(part(f"definition/tables/{t}.tmdl", table_tmdl(t)))
    return parts



