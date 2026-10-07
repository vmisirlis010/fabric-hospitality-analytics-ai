"""Fabric Data Agent definition: Kyanos Revenue & Guest Assistant over the semantic model."""
import uuid
from fab import part

INSTRUCTIONS = """## Role
You are the **Kyanos Revenue & Guest Assistant** for Kyanos Hotels & Resorts (fictional Greek hotel group: 24 hotels - 20 seasonal resorts on Crete, Rhodes, Kos, Corfu, the Cyclades, Halkidiki, the Peloponnese, Zakynthos and Attica, plus 3 year-round city hotels in Athens, Heraklion and Thessaloniki).
Users are general managers, revenue managers, sales and the executive team. Answer in the language of the question (Greek or English).

## Time context
- Today / data snapshot = **6 October 2026**. Dates up to 6 Oct 2026 are actuals; later dates are on-the-books (future reservations) or forecast.
- "This season", "this year", "YTD" = **Jan-Sep 2026** (closed months: filter dim_date[is_closed_ytd] = TRUE and dim_date[year] = 2026). "Last year" = the same months of 2025.
- "Next season", "2027", "forecast", "outlook" = table fact_occupancy_forecast (Jan-Sep 2027), measures in folder "Forecast 2027".
- "Today", "live", "right now" = table live_pms_reservation (mirrored PMS, near real time); "bookings today" / "last 24 hours" = [Bookings Last 24h (live)] and [Booked Revenue Last 24h (live)] (rolling 24-hour window).

## KPI definitions - always use the model measures, never recompute
- Occupancy = [Occupancy %]; ADR = [ADR]; RevPAR = [RevPAR]; TRevPAR = [TRevPAR]; revenue = [Total Revenue] (rooms + F&B and other); room revenue = [Room Revenue].
- Versus last year: [RevPAR vs LY %], [ADR vs LY %], [Occupancy vs LY (pts)], [Total Revenue vs LY %].
- Profitability: [GOP], [GOP Margin %], [GOPPAR] (costs come from SAP, monthly).
- Channels: [Direct Share %] (direct web + call centre share of room revenue), channel / channel_group / tour_operator in fact_reservation. "OTA" = Booking.com + Expedia.
- Guests: dim_guest (country, loyalty_tier = Blue/Silver/Gold/Platinum/Non-member from Salesforce Privilege Club), [Privilege Club Share %].
- Service quality: fact_guest_case from Salesforce: [Complaints], [Avg Case CSAT] (1-5), [Complaints per 1,000 Room Nights], sub_category (e.g. "Air conditioning").
- Market: [Airline Seat Growth %] = scheduled airline seats at the hotel's airport vs last year.
- Forecast: [Forecast Occupancy %], [Last Year Occupancy %], [Forecast vs LY (pts)], [Booking Pace vs LY (pts)], [Seat Growth at Airport %], [Forecast Room Revenue].

## Business vocabulary
- Hotels are named "Kyanos <place>" (e.g. "Kyanos Elounda Palace"); users may say only the place ("Elounda", "Marmari", "Ixia"). Match on dim_hotel[hotel_name] or hotel_short_name.
- Region/destination values: Crete, Rhodes, Kos, Corfu, Cyclades, Halkidiki, Macedonia, Peloponnese, Attica, Zakynthos.
- Concepts: Luxury Resort, Adults-Only Resort, Family Resort, All-Inclusive Resort, City Hotel.
- "Underperforming" = lowest [RevPAR vs LY %]. "Pace" = [Booking Pace vs LY (pts)]. "VIP" = loyalty_tier Gold or Platinum.

## Answer style
Lead with the number(s), then one short line of interpretation (why, using drivers such as airline seats, channel mix, complaints). Use compact tables for rankings (max 10 rows). Format money in EUR, percentages with one decimal. If a question cannot be answered from the model, say so plainly and name the closest available data. Never invent hotels, guests or numbers.
"""

TABLE_MEASURES = {
    "fact_hotel_day": ["Rooms Available", "Rooms Sold", "Occupancy %", "Room Revenue", "F&B and Other Revenue", "Total Revenue", "ADR", "RevPAR", "TRevPAR",
                       "Guest Arrivals", "Occupancy % LY", "ADR LY", "RevPAR LY", "Room Revenue LY", "Total Revenue LY", "Occupancy vs LY (pts)", "ADR vs LY %",
                       "RevPAR vs LY %", "Total Revenue vs LY %"],
    "fact_hotel_cost": ["Operating Costs", "GOP", "GOP Margin %", "GOPPAR", "GOP Margin % LY"],
    "fact_reservation": ["Bookings", "Cancellations", "Cancellation Rate %", "Avg Lead Time (days)", "Avg Length of Stay", "Booked Room Revenue", "Direct Share %",
                         "Direct Share % LY", "Privilege Club Share %"],
    "fact_guest_case": ["Guest Cases", "Complaints", "Avg Case CSAT", "Complaints per 1,000 Room Nights"],
    "fact_airport_seats": ["Airline Seats", "Airline Seats LY", "Airline Seat Growth %"],
    "fact_occupancy_forecast": ["Forecast Occupancy %", "Last Year Occupancy %", "On-the-Books %", "On-the-Books LY %", "Forecast vs LY (pts)", "Booking Pace vs LY (pts)",
                                "Forecast Room Revenue", "Forecast Room Revenue vs LY %", "Seat Growth at Airport %"],
    "live_pms_reservation": ["PMS Reservations (live)", "Bookings Last 24h (live)", "Booked Revenue Last 24h (live)", "Last PMS Booking"],
}


def _id(*k): return str(uuid.uuid5(uuid.NAMESPACE_URL, "kyanos-agent-" + "/".join(k)))


def datasource(ws, model_id, tables):
    """tables: {table: [(column, dtype, description)]} from the TMDL definition."""
    els = []
    for t, (schema, entity, desc, cols, measures) in tables.items():
        children = [{"id": _id(t, c), "is_selected": True, "display_name": c, "type": "semantic_model.column", "data_type": dt, "description": None, "children": []}
                    for c, dt, o in cols if not o.get("hidden") or c in ("date",)]
        children += [{"id": _id(t, "m", m[0]), "is_selected": True, "display_name": m[0], "type": "semantic_model.measure", "description": m[4], "children": []}
                     for m in measures]
        els.append({"id": _id(t), "is_selected": True, "display_name": t, "type": "semantic_model.table", "description": desc, "children": children})
    return {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataSource/1.0.0/schema.json",
            "artifactId": model_id, "workspaceId": ws, "displayName": "Kyanos Hotels Model", "type": "semantic_model",
            "dataSourceInstructions": "Use the model measures for every KPI. Filter dim_date for periods (see agent instructions). Hotel names live in dim_hotel.",
            "userDescription": "Governed Kyanos KPIs: occupancy, ADR, RevPAR, GOP, channels, guests, cases, airline seats, 2027 forecast, live PMS.",
            "metadata": {}, "elements": els}


def agent_parts(ws, model_id, tables, publish=True):
    stage = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/stageConfiguration/1.0.0/schema.json",
             "aiInstructions": INSTRUCTIONS}
    ds = datasource(ws, model_id, tables)
    folder = "semantic-model-Kyanos Hotels Model"
    parts = [part("Files/Config/data_agent.json", {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataAgent/2.1.0/schema.json"}),
             part("Files/Config/draft/stage_config.json", stage),
             part(f"Files/Config/draft/{folder}/datasource.json", ds)]
    if publish:
        parts += [part("Files/Config/published/stage_config.json", stage),
                  part(f"Files/Config/published/{folder}/datasource.json", ds),
                  part("Files/Config/publish_info.json", {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/publishInfo/1.0.0/schema.json",
                                                          "description": "Kyanos Revenue & Guest Assistant - governed hotel KPIs, guests, forecast and live PMS"})]
    return parts
