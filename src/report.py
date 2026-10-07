"""PBIR definition of the 'Kyanos Hotels - Commercial Performance' Power BI report."""
import json
from fab import part

NAVY, BLUE, TEAL, SAND, CORAL, INK, MUTED, BG, LINE = "#0B3C5D", "#0B4F8A", "#22A39F", "#F2A541", "#E4572E", "#1F2A44", "#5B6B82", "#EEF3F8", "#E1E7EF"
SCHEMA_V = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json"

THEME = {
    "name": "Kyanos Aegean",
    "dataColors": [BLUE, TEAL, SAND, CORAL, "#7A9E7E", "#6C5B7B", "#4FA3D9", "#B8C4D6", "#2E6F95", "#C97B63"],
    "background": "#FFFFFF", "foreground": INK, "tableAccent": BLUE,
    "good": "#2E9E6A", "bad": "#D64545", "neutral": SAND, "maximum": BLUE, "center": "#9FC3E7", "minimum": "#E8F1FA",
    "textClasses": {
        "callout": {"fontSize": 24, "fontFace": "Segoe UI Semibold", "color": NAVY},
        "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": INK},
        "header": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": INK},
        "label": {"fontSize": 10, "fontFace": "Segoe UI", "color": MUTED},
    },
}


def L(v): return {"expr": {"Literal": {"Value": v}}}
def S(v): return L("'" + v.replace("'", "''") + "'")
def C(hexcolor): return {"solid": {"color": S(hexcolor)}}
def props(**kw): return [{"properties": kw}]


def col(entity, prop, name=None):
    p = {"field": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}, "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop}
    if name: p["displayName"] = name
    return p


def mea(entity, prop, name=None):
    p = {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}, "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop}
    if name: p["displayName"] = name
    return p


def container(title=None, bg="#FFFFFF", border=True, subtitle=None):
    o = {"background": props(show=L("true"), color=C(bg), transparency=L("0D")),
         "border": props(show=L("true" if border else "false"), color=C(LINE), radius=L("10D")),
         "dropShadow": props(show=L("false")),
         "padding": props(top=L("8D"), bottom=L("6D"), left=L("10D"), right=L("10D"))}
    if title:
        o["title"] = props(show=L("true"), text=S(title), fontSize=L("11D"), fontColor=C(INK), bold=L("true"))
    else:
        o["title"] = props(show=L("false"))
    if subtitle:
        o["subTitle"] = props(show=L("true"), text=S(subtitle), fontSize=L("9D"), fontColor=C(MUTED))
    return o


class Page:
    def __init__(self, pid, name, filters=None):
        self.pid, self.name, self.visuals, self.n, self.filters = pid, name, [], 0, filters or []

    def add(self, vtype, x, y, w, h, query=None, objects=None, cobj=None, sort=None, vfilters=None):
        self.n += 1
        vid = f"{self.pid}v{self.n:02d}"
        v = {"visualType": vtype}
        if query is not None:
            v["query"] = {"queryState": query}
            if sort:
                v["query"]["sortDefinition"] = {"sort": [{"field": f["field"], "direction": d} for f, d in sort], "isDefaultSort": False}
        if objects: v["objects"] = objects
        v["visualContainerObjects"] = cobj if cobj is not None else container()
        v["drillFilterOtherVisuals"] = True
        body = {"$schema": SCHEMA_V, "name": vid, "position": {"x": x, "y": y, "z": 1000 + self.n, "height": h, "width": w, "tabOrder": 1000 + self.n},
                "visual": v}
        if vfilters: body["filterConfig"] = {"filters": vfilters}
        self.visuals.append(body)
        return self

    # ---- building blocks
    def header(self, title, subtitle):
        paras = [{"textRuns": [{"value": "KYANOS", "textStyle": {"fontWeight": "bold", "fontSize": "11pt", "color": "#9FD4F5"}},
                               {"value": "   HOTELS & RESORTS", "textStyle": {"fontSize": "11pt", "color": "#9FD4F5"}}]},
                 {"textRuns": [{"value": title, "textStyle": {"fontWeight": "bold", "fontSize": "18pt", "color": "#FFFFFF"}}]},
                 {"textRuns": [{"value": subtitle, "textStyle": {"fontSize": "10pt", "color": "#D7E6F2"}}]}]
        return self.add("textbox", 0, 0, 1280, 86, objects={"general": [{"properties": {"paragraphs": paras}}]},
                        cobj={"background": props(show=L("true"), color=C(NAVY), transparency=L("0D")), "border": props(show=L("false")),
                              "title": props(show=L("false")), "padding": props(top=L("8D"), left=L("18D"))})

    def note(self, x, y, w, h, text, size="9pt", color=MUTED, bold=False):
        st = {"fontSize": size, "color": color}
        if bold: st["fontWeight"] = "bold"
        return self.add("textbox", x, y, w, h, objects={"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": text, "textStyle": st}]}]}}]},
                        cobj={"background": props(show=L("false")), "border": props(show=L("false")), "title": props(show=L("false"))})

    def kpi(self, x, y, w, entity, measure, label, sub_entity=None, sub_measure=None, sub_label=None, h=118):
        clear = {"background": props(show=L("false")), "border": props(show=L("false")), "title": props(show=L("false")),
                 "padding": props(top=L("0D"), bottom=L("0D"), left=L("4D"), right=L("4D"))}
        self.add("textbox", x, y, w, h, objects={"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": " "}]}]}}]},
                 cobj={**container(), "padding": props(top=L("0D"))})
        top_h = 70 if sub_measure else h - 8
        self.add("card", x + 4, y + 4, w - 8, top_h, {"Values": {"projections": [mea(entity, measure, label)]}},
                 objects={"labels": props(fontSize=L("22D"), color=C(NAVY)), "categoryLabels": props(show=L("true"), fontSize=L("10D"), color=C(MUTED))},
                 cobj=clear)
        if sub_measure:
            self.add("card", x + 4, y + 70, w - 8, h - 74, {"Values": {"projections": [mea(sub_entity or entity, sub_measure, sub_label)]}},
                     objects={"labels": props(fontSize=L("12D"), color=C(TEAL)), "categoryLabels": props(show=L("true"), fontSize=L("8D"), color=C(MUTED))},
                     cobj=clear)
        return self


def cat_filter(entity, prop, values, name):
    lit = [[{"Literal": {"Value": v}}] for v in values]
    return {"name": name, "field": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}, "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "t", "Entity": entity, "Type": 0}],
                       "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": prop}}],
                                                       "Values": lit}}}]}}


def labels_on(**extra):
    return {"labels": props(show=L("true"), **extra)}


def build():
    pages = []
    YTD = [cat_filter("dim_date", "year", ["2026L"], "fYear"), cat_filter("dim_date", "is_closed_ytd", ["true"], "fYtd")]

    # 1 ---------------------------------------------------------------- Executive overview
    p = Page("p1", "Executive Overview", YTD)
    p.header("Commercial performance · 2026 season to date", "Jan–Sep 2026 vs Jan–Sep 2025  ·  24 hotels  ·  PMS (mirrored) + Salesforce + SAP unified in OneLake  ·  Direct Lake")
    k = [("fact_hotel_day", "Total Revenue", "Total revenue", "Total Revenue vs LY %", "vs last year"),
         ("fact_hotel_day", "Occupancy %", "Occupancy", "Occupancy vs LY (pts)", "pts vs last year"),
         ("fact_hotel_day", "ADR", "ADR", "ADR vs LY %", "vs last year"),
         ("fact_hotel_day", "RevPAR", "RevPAR", "RevPAR vs LY %", "vs last year"),
         ("fact_hotel_cost", "GOP Margin %", "GOP margin", "GOP Margin % LY", "last year"),
         ("fact_reservation", "Direct Share %", "Direct booking share", "Direct Share % LY", "last year")]
    for i, (e, m, lab, sm, sl) in enumerate(k):
        p.kpi(16 + i * 210, 98, 200, e, m, lab, e, sm, sl)
    p.add("lineChart", 16, 232, 760, 236,
          {"Category": {"projections": [col("dim_date", "month")]},
           "Y": {"projections": [mea("fact_hotel_day", "Total Revenue", "2026"), mea("fact_hotel_day", "Total Revenue LY", "2025")]}},
          objects={"dataPoint": [{"properties": {"fill": C(BLUE)}, "selector": {"metadata": "fact_hotel_day.Total Revenue"}},
                                 {"properties": {"fill": C("#B8C4D6")}, "selector": {"metadata": "fact_hotel_day.Total Revenue LY"}}],
                   "legend": props(show=L("true"), position=S("Top")), "lineStyles": props(strokeWidth=L("3D"), showMarker=L("true"))},
          cobj=container("Total revenue by month — 2026 vs 2025"))
    p.add("treemap", 16, 478, 370, 228,
          {"Group": {"projections": [col("dim_hotel", "region", "Destination")]}, "Values": {"projections": [mea("fact_hotel_day", "Total Revenue")]}},
          objects={"labels": props(show=L("true"), fontSize=L("9D")), "categoryLabels": props(show=L("true"), fontSize=L("10D")), "legend": props(show=L("false"))},
          cobj=container("Revenue mix by destination"))
    p.add("clusteredColumnChart", 396, 478, 380, 228,
          {"Category": {"projections": [col("dim_hotel", "concept")]}, "Y": {"projections": [mea("fact_hotel_cost", "GOP Margin %"), mea("fact_hotel_cost", "GOP Margin % LY")]}},
          objects={"legend": props(show=L("true"), position=S("Top")), "labels": props(show=L("true"), fontSize=L("8D")),
                   "dataPoint": [{"properties": {"fill": C(TEAL)}, "selector": {"metadata": "fact_hotel_cost.GOP Margin %"}},
                                 {"properties": {"fill": C("#B8C4D6")}, "selector": {"metadata": "fact_hotel_cost.GOP Margin % LY"}}]},
          cobj=container("GOP margin by hotel concept (SAP)"))
    p.add("barChart", 786, 232, 478, 474,
          {"Category": {"projections": [col("dim_hotel", "hotel_short_name", "Hotel")]}, "Y": {"projections": [mea("fact_hotel_day", "RevPAR vs LY %", "RevPAR vs LY")]}},
          objects={"labels": props(show=L("true"), fontSize=L("8D")), "dataPoint": props(fill=C(BLUE)),
                   "categoryAxis": props(fontSize=L("8D")), "valueAxis": props(show=L("false"))},
          cobj=container("RevPAR growth vs last year, by hotel", subtitle="Kos & Zakynthos lost airline seats in 2026"),
          sort=[(mea("fact_hotel_day", "RevPAR vs LY %"), "Ascending")])
    pages.append(p)

    # 2 ---------------------------------------------------------------- Hotel scorecard
    p = Page("p2", "Hotel Scorecard", YTD)
    p.header("Hotel scorecard", "One version of the truth for all 24 hotels · Jan–Sep 2026 · click a hotel to cross-filter guest cases")
    p.add("tableEx", 16, 98, 1248, 332,
          {"Values": {"projections": [col("dim_hotel", "hotel_name", "Hotel"), col("dim_hotel", "region", "Region"), col("dim_hotel", "concept", "Concept"),
                                      mea("fact_hotel_day", "Occupancy %", "Occupancy"), mea("fact_hotel_day", "Occupancy vs LY (pts)", "Occ vs LY"),
                                      mea("fact_hotel_day", "ADR", "ADR"), mea("fact_hotel_day", "ADR vs LY %", "ADR vs LY"),
                                      mea("fact_hotel_day", "RevPAR", "RevPAR"), mea("fact_hotel_day", "RevPAR vs LY %", "RevPAR vs LY"),
                                      mea("fact_hotel_cost", "GOP Margin %", "GOP %"), mea("fact_hotel_cost", "GOPPAR", "GOPPAR"),
                                      mea("fact_guest_case", "Avg Case CSAT", "Case CSAT"), mea("fact_guest_case", "Complaints per 1,000 Room Nights", "Complaints /1k RN")]}},
          objects={"values": props(fontSize=L("9D")), "columnHeaders": props(fontSize=L("9D"), fontColor=C("#FFFFFF"), backColor=C(BLUE)),
                   "total": props(totals=L("true")), "grid": props(rowPadding=L("2D"))},
          cobj=container("Hotel KPIs vs last year"),
          sort=[(mea("fact_hotel_day", "RevPAR vs LY %"), "Ascending")])
    p.add("scatterChart", 16, 440, 620, 266,
          {"Category": {"projections": [col("dim_hotel", "hotel_short_name", "Hotel")]}, "X": {"projections": [mea("fact_hotel_day", "Occupancy %")]},
           "Y": {"projections": [mea("fact_hotel_day", "ADR")]}, "Size": {"projections": [mea("fact_hotel_day", "Total Revenue")]},
           "Series": {"projections": [col("dim_hotel", "concept")]}},
          objects={"categoryLabels": props(show=L("true"), fontSize=L("7D")), "legend": props(show=L("true"), position=S("Top"))},
          cobj=container("Rate vs volume — ADR by occupancy (bubble = revenue)"))
    p.add("barChart", 646, 440, 618, 266,
          {"Category": {"projections": [col("fact_guest_case", "sub_category", "Case type")]}, "Y": {"projections": [mea("fact_guest_case", "Guest Cases")]},
           "Series": {"projections": [col("fact_guest_case", "category")]}},
          objects={"labels": props(show=L("true"), fontSize=L("8D")), "legend": props(show=L("true"), position=S("Top"))},
          cobj=container("Salesforce guest cases by type", subtitle="Select Kos Marmari above: air-conditioning complaint cluster"),
          sort=[(mea("fact_guest_case", "Guest Cases"), "Descending")])
    pages.append(p)

    # 3 ---------------------------------------------------------------- Channels & guests
    p = Page("p3", "Channels & Guests", YTD)
    p.header("Channels & guests", "Booking channels from the PMS · Privilege Club profile from Salesforce · stays arriving Jan–Sep 2026")
    p.kpi(16, 98, 200, "fact_reservation", "Direct Share %", "Direct booking share", "fact_reservation", "Direct Share % LY", "last year")
    p.kpi(226, 98, 200, "fact_reservation", "Privilege Club Share %", "Privilege Club stays")
    p.kpi(436, 98, 200, "fact_reservation", "Avg Lead Time (days)", "Avg lead time (days)")
    p.kpi(646, 98, 200, "fact_reservation", "Avg Length of Stay", "Avg length of stay")
    p.kpi(856, 98, 200, "fact_reservation", "Cancellation Rate %", "Cancellation rate")
    p.kpi(1066, 98, 198, "fact_reservation", "Bookings", "Stays")
    p.add("lineChart", 16, 232, 620, 230,
          {"Category": {"projections": [col("dim_date", "month")]},
           "Y": {"projections": [mea("fact_reservation", "Direct Share %", "2026"), mea("fact_reservation", "Direct Share % LY", "2025")]}},
          objects={"dataPoint": [{"properties": {"fill": C(TEAL)}, "selector": {"metadata": "fact_reservation.Direct Share %"}},
                                 {"properties": {"fill": C("#B8C4D6")}, "selector": {"metadata": "fact_reservation.Direct Share % LY"}}],
                   "legend": props(show=L("true"), position=S("Top")), "lineStyles": props(strokeWidth=L("3D"), showMarker=L("true")),
                   "labels": props(show=L("true"), fontSize=L("8D"))},
          cobj=container("Direct booking share by month — the direct strategy is working"))
    p.add("barChart", 646, 232, 618, 230,
          {"Category": {"projections": [col("fact_reservation", "channel", "Channel")]}, "Y": {"projections": [mea("fact_reservation", "Booked Room Revenue", "Room revenue")]}},
          objects={"labels": props(show=L("true"), fontSize=L("8D")), "dataPoint": props(fill=C(BLUE))},
          cobj=container("Room revenue by booking channel"), sort=[(mea("fact_reservation", "Booked Room Revenue"), "Descending")])
    p.add("donutChart", 16, 472, 400, 234,
          {"Category": {"projections": [col("dim_guest", "loyalty_tier", "Tier")]}, "Y": {"projections": [mea("fact_reservation", "Bookings", "Stays")]}},
          objects={"legend": props(show=L("true"), position=S("Right")), "labels": props(show=L("true"), labelStyle=S("Percent of total"))},
          cobj=container("Stays by Privilege Club tier (Salesforce)"))
    p.add("clusteredColumnChart", 426, 472, 420, 234,
          {"Category": {"projections": [col("fact_reservation", "channel_group", "Channel group")]}, "Y": {"projections": [mea("fact_reservation", "Avg Lead Time (days)", "Lead time")]}},
          objects={"labels": props(show=L("true")), "dataPoint": props(fill=C(SAND))},
          cobj=container("Average booking lead time (days)"), sort=[(mea("fact_reservation", "Avg Lead Time (days)"), "Descending")])
    p.add("barChart", 856, 472, 408, 234,
          {"Category": {"projections": [col("dim_guest", "country", "Country")]}, "Y": {"projections": [mea("fact_reservation", "Bookings", "Stays")]}},
          objects={"labels": props(show=L("true"), fontSize=L("7D")), "dataPoint": props(fill=C(TEAL)), "categoryAxis": props(fontSize=L("8D"))},
          cobj=container("Source markets"), sort=[(mea("fact_reservation", "Bookings"), "Descending")])
    pages.append(p)

    # 4 ---------------------------------------------------------------- 2027 outlook (AI)
    p = Page("p4", "2027 Demand Outlook (AI)",
             [cat_filter("dim_date", "year", ["2027L"], "fYear"), cat_filter("dim_date", "is_closed_ytd", ["true"], "fYtd")])
    p.header("Summer 2027 demand outlook · AI forecast",
             "Gradient-boosting pace model (MLflow) · booking pace vs last year + published airline seat capacity · snapshot 6 Oct 2026 · Jan–Sep 2027")
    p.kpi(16, 98, 200, "fact_occupancy_forecast", "Forecast Occupancy %", "Forecast occupancy 2027", "fact_occupancy_forecast", "Forecast vs LY (pts)", "pts vs 2026")
    p.kpi(226, 98, 200, "fact_occupancy_forecast", "Last Year Occupancy %", "2026 actual occupancy")
    p.kpi(436, 98, 200, "fact_occupancy_forecast", "On-the-Books %", "Already on the books", "fact_occupancy_forecast", "Booking Pace vs LY (pts)", "pace vs LY (pts)")
    p.kpi(646, 98, 200, "fact_occupancy_forecast", "Forecast Room Revenue", "Forecast room revenue", "fact_occupancy_forecast", "Forecast Room Revenue vs LY %", "vs 2026")
    p.kpi(856, 98, 200, "fact_airport_seats", "Airline Seat Growth %", "Airline seats vs 2026")
    p.note(1066, 98, 198, 120, "How to read: the model starts from 2026 actuals and adjusts each hotel-night for booking pace and airline seat capacity at the hotel's airport.", "8pt")
    p.add("lineChart", 16, 232, 620, 236,
          {"Category": {"projections": [col("dim_date", "month")]},
           "Y": {"projections": [mea("fact_occupancy_forecast", "Forecast Occupancy %", "Forecast 2027"), mea("fact_occupancy_forecast", "Last Year Occupancy %", "Actual 2026"),
                                 mea("fact_occupancy_forecast", "On-the-Books %", "On the books today")]}},
          objects={"dataPoint": [{"properties": {"fill": C(CORAL)}, "selector": {"metadata": "fact_occupancy_forecast.Forecast Occupancy %"}},
                                 {"properties": {"fill": C("#9AA9BF")}, "selector": {"metadata": "fact_occupancy_forecast.Last Year Occupancy %"}},
                                 {"properties": {"fill": C(TEAL)}, "selector": {"metadata": "fact_occupancy_forecast.On-the-Books %"}}],
                   "legend": props(show=L("true"), position=S("Top")), "lineStyles": props(strokeWidth=L("3D"), showMarker=L("true"))},
          cobj=container("Occupancy by month — forecast vs 2026 actual vs booked so far"))
    p.add("clusteredColumnChart", 646, 232, 618, 236,
          {"Category": {"projections": [col("dim_airport", "airport_name", "Airport")]}, "Y": {"projections": [mea("fact_airport_seats", "Airline Seat Growth %", "Seat growth")]}},
          objects={"labels": props(show=L("true"), fontSize=L("8D")), "dataPoint": props(fill=C(BLUE))},
          cobj=container("Published airline seat capacity, Summer 2027 vs 2026"), sort=[(mea("fact_airport_seats", "Airline Seat Growth %"), "Descending")])
    p.add("barChart", 16, 478, 620, 228,
          {"Category": {"projections": [col("dim_hotel", "hotel_short_name", "Hotel")]}, "Y": {"projections": [mea("fact_occupancy_forecast", "Forecast vs LY (pts)", "Forecast vs 2026 (pts)")]}},
          objects={"labels": props(show=L("true"), fontSize=L("7D")), "dataPoint": props(fill=C(CORAL)), "categoryAxis": props(fontSize=L("7D"))},
          cobj=container("Forecast occupancy change vs 2026, by hotel"), sort=[(mea("fact_occupancy_forecast", "Forecast vs LY (pts)"), "Descending")])
    p.add("tableEx", 646, 478, 618, 228,
          {"Values": {"projections": [col("dim_hotel", "hotel_short_name", "Hotel"), col("dim_hotel", "airport_code", "Airport"),
                                      mea("fact_occupancy_forecast", "Seat Growth at Airport %", "Seats"), mea("fact_occupancy_forecast", "Booking Pace vs LY (pts)", "Pace"),
                                      mea("fact_occupancy_forecast", "Last Year Occupancy %", "2026"), mea("fact_occupancy_forecast", "Forecast Occupancy %", "2027 fcst"),
                                      mea("fact_occupancy_forecast", "Forecast Room Revenue", "Fcst room rev")]}},
          objects={"values": props(fontSize=L("8D")), "columnHeaders": props(fontSize=L("8D"), fontColor=C("#FFFFFF"), backColor=C(NAVY)), "total": props(totals=L("true"))},
          cobj=container("Drivers per hotel"), sort=[(mea("fact_occupancy_forecast", "Seat Growth at Airport %"), "Descending")])
    pages.append(p)

    # 5 ---------------------------------------------------------------- Live PMS
    p = Page("p5", "Live PMS Feed")
    p.header("Live from the PMS · no overnight batch",
             "SQL → OneLake Mirroring → Direct Lake: new reservations appear here seconds after they are saved in the PMS (refresh visuals)")
    p.kpi(16, 98, 300, "live_pms_reservation", "Bookings Last 24h (live)", "Bookings in the last 24 hours")
    p.kpi(326, 98, 300, "live_pms_reservation", "Booked Revenue Last 24h (live)", "Room revenue booked, last 24 hours")
    p.kpi(636, 98, 300, "live_pms_reservation", "PMS Reservations (live)", "Reservations in the PMS")
    p.kpi(946, 98, 318, "live_pms_reservation", "Last PMS Booking", "Latest booking saved at (UTC)")
    p.add("tableEx", 16, 196, 760, 510,
          {"Values": {"projections": [col("live_pms_reservation", "CreatedAt", "Saved at (UTC)"), col("live_pms_reservation", "ConfirmationNo", "Confirmation"),
                                      col("dim_hotel", "hotel_short_name", "Hotel"), col("live_pms_reservation", "Channel", "Channel"),
                                      col("live_pms_reservation", "ArrivalDate", "Arrival"), col("live_pms_reservation", "Nights", "Nights"),
                                      col("live_pms_reservation", "BoardType", "Board"), col("live_pms_reservation", "Status", "Status")]}},
          objects={"values": props(fontSize=L("9D")), "columnHeaders": props(fontSize=L("9D"), fontColor=C("#FFFFFF"), backColor=C(NAVY)), "total": props(totals=L("false"))},
          cobj=container("Latest reservations in the PMS"),
          sort=[(col("live_pms_reservation", "CreatedAt"), "Descending")],
          vfilters=[cat_filter("live_pms_reservation", "Status", ["'Confirmed'"], "fStatus")])
    p.add("barChart", 786, 196, 478, 300,
          {"Category": {"projections": [col("dim_hotel", "hotel_short_name", "Hotel")]}, "Y": {"projections": [mea("live_pms_reservation", "Bookings Last 24h (live)", "Bookings, last 24h")]}},
          objects={"labels": props(show=L("true"), fontSize=L("8D")), "dataPoint": props(fill=C(TEAL)), "categoryAxis": props(fontSize=L("8D"))},
          cobj=container("Bookings in the last 24 hours, by hotel"), sort=[(mea("live_pms_reservation", "Bookings Last 24h (live)"), "Descending")])
    p.add("donutChart", 786, 506, 478, 200,
          {"Category": {"projections": [col("live_pms_reservation", "Channel")]}, "Y": {"projections": [mea("live_pms_reservation", "Bookings Last 24h (live)", "Bookings, last 24h")]}},
          objects={"legend": props(show=L("true"), position=S("Right")), "labels": props(show=L("true"), labelStyle=S("Data value"))},
          cobj=container("Last 24 hours bookings by channel"))
    pages.append(p)
    return pages


def report_parts(model_id, name):
    pages = build()
    report = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/1.2.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.61", "type": "SharedResources"},
                            "customTheme": {"name": "KyanosAegean.json", "reportVersionAtImport": "5.61", "type": "RegisteredResources"}},
        "layoutOptimization": "None",
        "objects": {"section": [{"properties": {"verticalAlignment": S("Top")}}]},
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources", "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources", "items": [{"name": "KyanosAegean.json", "path": "KyanosAegean.json", "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True},
    }
    parts = [
        part("definition.pbir", {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
                                 "version": "4.0", "datasetReference": {"byConnection": {"connectionString": f"semanticmodelid={model_id}"}}}),
        part("definition/version.json", {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"}),
        part("definition/report.json", report),
        part("StaticResources/RegisteredResources/KyanosAegean.json", THEME),
        part("definition/pages/pages.json", {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
                                             "pageOrder": [p.pid for p in pages], "activePageName": pages[0].pid}),
    ]
    for p in pages:
        pg = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/1.3.0/schema.json",
              "name": p.pid, "displayName": p.name, "displayOption": "FitToPage", "height": 720, "width": 1280,
              "objects": {"background": props(color=C(BG), transparency=L("0D")), "outspace": props(color=C(BG))}}
        if p.filters:
            pg["filterConfig"] = {"filters": p.filters}
        parts.append(part(f"definition/pages/{p.pid}/page.json", pg))
        for v in p.visuals:
            parts.append(part(f"definition/pages/{p.pid}/visuals/{v['name']}/visual.json", v))
    return parts

