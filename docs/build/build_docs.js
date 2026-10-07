// Build the Kyanos Fabric solution documentation (.docx) from meta.json, facts2.json, _facts.json and rendered images.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, ImageRun, AlignmentType,
  PageOrientation, Header, Footer, PageNumber, BorderStyle, HeadingLevel, TableLayoutType, VerticalAlign, PageBreak,
} = require("docx");

const B = __dirname, DOCS = path.join(B, ".."), IMG = path.join(DOCS, "images"), SHOTS = IMG;
const meta = JSON.parse(fs.readFileSync(path.join(B, "meta.json"), "utf8"));
const f2 = JSON.parse(fs.readFileSync(path.join(B, "facts2.json"), "utf8"));
const f1 = JSON.parse(fs.readFileSync(path.join(B, "facts1.json"), "utf8"));

const NAVY = "0B3C5D", BLUE = "0B4F8A", TEAL = "22A39F", CORAL = "E4572E", INK = "1F2A44", MUTED = "5B6B82", ZEBRA = "F3F6FA", CODEBG = "F4F6F9", LINE = "C9D3E0";
const FONT = "Segoe UI", MONO = "Consolas";
const PORTRAIT_W = 9638; // twips of usable width (A4, 2cm margins)
const LAND_W = 14570;

// ---------------------------------------------------------------- helpers
const run = (t, o = {}) => new TextRun({ text: t, font: o.mono ? MONO : FONT, size: o.size || 20, bold: o.bold, italics: o.italic, color: o.color || INK, break: o.br });
function P(content, o = {}) {
  const runs = Array.isArray(content) ? content : [run(content, o)];
  return new Paragraph({ children: runs, spacing: { after: o.after ?? 120, before: o.before ?? 0, line: o.line ?? 290 }, alignment: o.align, keepNext: o.keepNext, indent: o.indent });
}
// rich text: **bold** and `code`
function R(text, o = {}) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean);
  return P(parts.map(s => s.startsWith("**") ? run(s.slice(2, -2), { ...o, bold: true }) : s.startsWith("`") ? run(s.slice(1, -1), { ...o, mono: true, color: BLUE, size: (o.size || 20) - 2 }) : run(s, o)), o);
}
let h1n = 0, h2n = 0, h3n = 0;
function H1(t) { h1n++; h2n = 0; h3n = 0; return new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, spacing: { before: 0, after: 200 }, children: [run(`${h1n}. ${t}`, { size: 36, bold: true, color: NAVY })] }); }
function H1nb(t) { h1n++; h2n = 0; h3n = 0; return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 0, after: 200 }, children: [run(`${h1n}. ${t}`, { size: 36, bold: true, color: NAVY })] }); }
function H2(t) { h2n++; h3n = 0; return new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, spacing: { before: 280, after: 120 }, children: [run(`${h1n}.${h2n} ${t}`, { size: 27, bold: true, color: BLUE })] }); }
function H3(t) { h3n++; return new Paragraph({ heading: HeadingLevel.HEADING_3, keepNext: true, spacing: { before: 200, after: 80 }, children: [run(`${h1n}.${h2n}.${h3n} ${t}`, { size: 23, bold: true, color: TEAL })] }); }
function bullet(text, lvl = 0) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean);
  return new Paragraph({ numbering: { reference: "bul", level: lvl }, spacing: { after: 60, line: 280 },
    children: parts.map(s => s.startsWith("**") ? run(s.slice(2, -2), { bold: true }) : s.startsWith("`") ? run(s.slice(1, -1), { mono: true, color: BLUE, size: 18 }) : run(s)) });
}
function numbered(text) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean);
  return new Paragraph({ numbering: { reference: "num", level: 0 }, spacing: { after: 60, line: 280 },
    children: parts.map(s => s.startsWith("**") ? run(s.slice(2, -2), { bold: true }) : s.startsWith("`") ? run(s.slice(1, -1), { mono: true, color: BLUE, size: 18 }) : run(s)) });
}
const cellBorders = { top: { style: BorderStyle.SINGLE, size: 4, color: LINE }, bottom: { style: BorderStyle.SINGLE, size: 4, color: LINE },
  left: { style: BorderStyle.SINGLE, size: 4, color: LINE }, right: { style: BorderStyle.SINGLE, size: 4, color: LINE } };
function cellParas(v, o) {
  const s = v === null || v === undefined ? "" : String(v);
  return s.split("\n").map(line => new Paragraph({ spacing: { after: 20, line: 250 }, alignment: o.align,
    children: [run(line, { size: o.size || 17, bold: o.bold, color: o.color, mono: o.mono })] }));
}
function table(headers, rows, widths, o = {}) {
  const W = o.total || PORTRAIT_W;
  const ws = widths.map(p => Math.round(W * p));
  const head = new TableRow({ tableHeader: true, children: headers.map((h, i) => new TableCell({ width: { size: ws[i], type: WidthType.DXA }, borders: cellBorders,
    shading: { type: ShadingType.CLEAR, fill: o.headFill || NAVY, color: "auto" }, margins: { top: 60, bottom: 60, left: 90, right: 90 },
    children: cellParas(h, { bold: true, color: "FFFFFF", size: o.size || 17 }) })) });
  const body = rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((v, i) => new TableCell({ width: { size: ws[i], type: WidthType.DXA }, borders: cellBorders,
    shading: ri % 2 ? { type: ShadingType.CLEAR, fill: ZEBRA, color: "auto" } : undefined, margins: { top: 50, bottom: 50, left: 90, right: 90 },
    children: cellParas(v, { size: o.size || 17, mono: (o.monoCols || []).includes(i), color: (o.monoCols || []).includes(i) ? BLUE : INK, bold: (o.boldCols || []).includes(i) }) })) }));
  return new Table({ rows: [head, ...body], width: { size: W, type: WidthType.DXA }, columnWidths: ws, layout: TableLayoutType.FIXED });
}
function code(text, o = {}) {
  const W = o.total || PORTRAIT_W;
  const lines = text.replace(/\t/g, "    ").split("\n");
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W], layout: TableLayoutType.FIXED, rows: [new TableRow({ cantSplit: lines.length < 45, children: [new TableCell({
    width: { size: W, type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill: CODEBG, color: "auto" },
    borders: { top: { style: BorderStyle.SINGLE, size: 4, color: LINE }, bottom: { style: BorderStyle.SINGLE, size: 4, color: LINE },
      left: { style: BorderStyle.SINGLE, size: 18, color: o.accent || TEAL }, right: { style: BorderStyle.SINGLE, size: 4, color: LINE } },
    margins: { top: 80, bottom: 80, left: 140, right: 100 },
    children: lines.map(l => new Paragraph({ spacing: { after: 0, line: 240 }, children: [run(l.length ? l : " ", { mono: true, size: o.size || 16, color: "24303F" })] })) })] })] });
}
function callout(title, text, color = TEAL) {
  return new Table({ width: { size: PORTRAIT_W, type: WidthType.DXA }, columnWidths: [PORTRAIT_W], layout: TableLayoutType.FIXED, rows: [new TableRow({ children: [new TableCell({
    width: { size: PORTRAIT_W, type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill: "EEF6F6", color: "auto" },
    borders: { top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }, bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      left: { style: BorderStyle.SINGLE, size: 24, color }, right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" } },
    margins: { top: 100, bottom: 100, left: 180, right: 140 },
    children: [P([run(title, { bold: true, color })], { after: 40 }), ...text.split("\n").map(t => R(t, { after: 30, size: 19 }))] })] })] });
}
function pngSize(file) { const b = fs.readFileSync(file); return [b.readUInt32BE(16), b.readUInt32BE(20)]; }
function figure(file, widthPx, caption, maxH = 99999) {
  const [w, h] = pngSize(file);
  if (widthPx * h / w > maxH) widthPx = Math.round(maxH * w / h);
  return [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 60 }, keepNext: true,
    children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width: widthPx, height: Math.round(widthPx * h / w) } })] }),
    P([run(caption, { italic: true, size: 17, color: MUTED })], { align: AlignmentType.CENTER, after: 200 })];
}
const sp = (n = 120) => new Paragraph({ spacing: { after: n }, children: [] });
const fmtPct = v => v === null || v === undefined ? "–" : (v * 100).toFixed(1) + "%";
const fmtPts = v => v === null || v === undefined ? "–" : (v >= 0 ? "+" : "") + (v * 100).toFixed(1) + " pts";
const fmtEur = v => v === null || v === undefined ? "–" : "€" + Math.round(v).toLocaleString("en-US");
const fmtNum = v => v === null || v === undefined ? "–" : Number(v).toLocaleString("en-US", { maximumFractionDigits: 2 });
function fmtVal(k, v) {
  if (v === null || v === undefined) return "(blank)";
  if (typeof v !== "number") return String(v);
  if (k.toLowerCase() === "year") return String(v);
  const kl = k.toLowerCase();
  if (kl.includes("revenue") || kl === "adr" || kl === "revpar" || kl === "goppar") return kl.includes("vs") ? fmtPct(v) : (Math.abs(v) > 10000 ? fmtEur(v) : "€" + v.toFixed(2));
  if (kl.includes("pts") || kl.includes("pace")) return fmtPts(v);
  if (Math.abs(v) <= 1.5 && !Number.isInteger(v)) return fmtPct(v);
  return fmtNum(v);
}

// ---------------------------------------------------------------- facts
const T = f1.tables;
const rows = n => (T[n] ? T[n].rows.toLocaleString("en-US") : "–");
const items = f1.items;
const kpi = f2.queries[0].result;
const k25 = kpi.find(r => r.year === 2025), k26 = kpi.find(r => r.year === 2026);
const fm = f2.forecast_metrics;
const outlook = f2.queries[4].result[0];
const WS_ID = "<workspaceId>";

// ---------------------------------------------------------------- content
const cover = [
  sp(240),
  P([run("KYANOS  HOTELS & RESORTS", { size: 22, bold: true, color: TEAL })], { after: 120 }),
  P([run("Unified Data & AI Platform on Microsoft Fabric", { size: 52, bold: true, color: NAVY })], { after: 160, line: 400 }),
  P([run("Solution documentation – architecture, data model, DAX, AI and build process", { size: 28, color: BLUE })], { after: 600 }),
  table(["Item", "Value"], [
    ["Document", "Solution documentation · version 1.0"],
    ["Date", "7 October 2026"],
    ["Author", "Vangelis Misirlis"],
    ["Workspace", "\"Kyanos Hotels - Analytics & AI Demo\" (tested on F4 and F8 capacities)"],
    ["Purpose", "Reference demo for hotel groups: real-time PMS integration, unified analytics, AI forecasting and data agents"],
    ["Data", "Fully synthetic. Kyanos Hotels & Resorts, its hotels, guests and partners are fictional."],
  ], [0.28, 0.72]),
  sp(80),
  P([run("Contents", { size: 26, bold: true, color: NAVY })], { after: 100 }),
  ...["Executive summary", "Solution architecture", "Data sources and synthetic data", "Ingestion: PMS mirroring, shortcut and file landing",
    "Lakehouse design and data lineage", "Notebooks and transformation logic", "Semantic model and table relationships", "DAX measure catalog",
    "DAX queries (validation and analysis)", "Power BI report", "AI demand forecast", "Fabric data agent", "Fabric IQ ontology",
    "Live PMS simulator and demo operations", "Build and deployment process", "Issues encountered and resolutions", "Important considerations",
    "Appendices: item inventory, column dictionary, code excerpts, glossary"].map((t, i) => P([run(`${i + 1}.  ${t}`, { size: 19, color: INK })], { after: 10, line: 260 })),
];

const execSummary = [
  H1nb("Executive summary"),
  R("This document describes an end-to-end Microsoft Fabric solution built for a hotel group. It shows how a group that today runs an on-premises PMS and SQL Server data warehouse with a nightly batch (the 05:00–08:00 window) can move to **one copy of the data in OneLake**, **near real-time reporting**, **AI forecasting** and **natural-language access**, without re-platforming its operational systems."),
  H2("What was built"),
  bullet("**Operational source** – `KyanosPMS`, a Fabric SQL database standing in for an on-premises PMS / SQL Server, holding 24 hotels, 117 room types, 255,848 guests and 483K reservations. It is replicated to OneLake automatically (Mirroring)."),
  bullet("**Unified lakehouse** – `KyanosLakehouse` (schema-enabled) combining the PMS (zero-copy shortcut), Salesforce (Privilege Club, service cases), SAP (monthly hotel costs) and airline seat capacity, refined into a gold star schema by PySpark notebooks."),
  bullet("**Governed semantic model** – `Kyanos Hotels Model`: Direct Lake on OneLake, 11 tables, 15 relationships, 53 DAX measures (Occupancy, ADR, RevPAR, GOP, pace, forecast, live KPIs) and 2 row-level-security roles."),
  bullet("**Power BI report** – 5 pages with a custom Aegean theme: Executive Overview, Hotel Scorecard, Channels & Guests, 2027 Demand Outlook (AI) and Live PMS Feed."),
  bullet("**AI demand forecast** – a gradient-boosting booking-pace model (MLflow-tracked and registered) that forecasts 2027 occupancy per hotel-night from booking pace and published airline seat capacity."),
  bullet("**Fabric data agent** – \"Kyanos Revenue & Guest Assistant\" answering Greek and English questions over the same governed model."),
  bullet("**Fabric IQ ontology** – six business entities (Hotel, Airport, VIP guest, Upcoming stay, Open case, Tour operator) with five relationships."),
  bullet("**Live simulator** – a Python process writing new bookings into the PMS; they appear in Power BI in about **13 seconds**."),
  H2("Headline results in the demo data"),
  table(["KPI (Jan–Sep closed months)", "2025", "2026", "Change"], [
    ["Total revenue", fmtEur(k25["Total Revenue"]), fmtEur(k26["Total Revenue"]), fmtPct(k26["Total Revenue"] / k25["Total Revenue"] - 1)],
    ["Occupancy", fmtPct(k25.Occupancy), fmtPct(k26.Occupancy), fmtPts(k26.Occupancy - k25.Occupancy)],
    ["ADR", "€" + k25.ADR.toFixed(2), "€" + k26.ADR.toFixed(2), fmtPct(k26.ADR / k25.ADR - 1)],
    ["RevPAR", "€" + k25.RevPAR.toFixed(2), "€" + k26.RevPAR.toFixed(2), fmtPct(k26["RevPAR vs LY"])],
    ["GOP margin", fmtPct(k25["GOP Margin"]), fmtPct(k26["GOP Margin"]), fmtPts(k26["GOP Margin"] - k25["GOP Margin"])],
    ["Direct booking share", fmtPct(k25["Direct Share"]), fmtPct(k26["Direct Share"]), fmtPts(k26["Direct Share"] - k25["Direct Share"])],
  ], [0.4, 0.2, 0.2, 0.2]),
  sp(80),
  table(["2027 outlook (AI forecast, Jan–Sep)", "Value"], [
    ["Forecast occupancy 2027", fmtPct(outlook["Forecast Occ 2027"])], ["Actual occupancy 2026 (same weekdays)", fmtPct(outlook["Actual Occ 2026"])],
    ["Already on the books (snapshot 6 Oct 2026)", fmtPct(outlook["On the books"])], ["Forecast room revenue", fmtEur(outlook["Forecast Room Revenue"]) + "  (" + fmtPct(outlook["vs 2026"]) + " vs 2026)"],
    ["Model accuracy (holdout MAE)", `${fm.mae_pts} occupancy points vs ${fm.naive_mae_pts} for "same as last year"`],
  ], [0.55, 0.45]),
  H2("Key design decisions"),
  bullet("**Mirror, don't extract.** Operational SQL data lands in OneLake continuously; the nightly copy and the 05:00–08:00 window disappear."),
  bullet("**Zero-copy unification.** The PMS is exposed in the lakehouse through a schema-level OneLake shortcut, so there is one physical copy."),
  bullet("**Direct Lake semantic model.** Power BI reads Delta tables directly – no import refresh, and new commits are framed automatically."),
  bullet("**One set of KPI definitions.** Report, Copilot and the data agent all use the same 53 measures, so numbers match everywhere."),
  bullet("**AI on the same platform.** Forecasting runs in a notebook on the same capacity and writes back to gold; MLflow tracks and registers the model."),
];

const arch = [
  H1("Solution architecture"),
  R("The solution follows a five-layer flow: **Sources → Ingestion → OneLake → Analytics & AI → Consumption**, all inside one Fabric workspace on an F8 capacity. The workspace is organised into folders that mirror these layers."),
];
const archFig = figure(path.join(IMG, "architecture.png"), 960, "Figure 1 – Solution architecture", 520);
const archDetails = [
  H2("Layer-by-layer description"),
  table(["Layer", "Fabric item(s)", "Role", "Key facts"], [
    ["Sources", "KyanosPMS (SQL database); CSV extracts", "Operational PMS; Salesforce, SAP and airline data", "PMS is the system of record for stays and revenue; others arrive as files"],
    ["Ingestion", "Mirroring; OneLake shortcut; OneLake DFS API", "Continuous replication of SQL tables; file landing", "Mirrored Delta committed within seconds of each insert"],
    ["OneLake", "KyanosLakehouse (schemas pms, crm, erp, ext, gold)", "Single copy of data; medallion refinement", "24 tables incl. 10 gold model tables and 6 iq_* entities"],
    ["Transformation", "Notebooks 01, 02, 04 (PySpark)", "Typing, conformance, data quality, star schema", "Run via the Fabric Jobs API; ~1–3 min each on F8"],
    ["AI", "Notebook 03; MLflow experiment + model", "Occupancy forecast for Jan–Sep 2027", "HistGradientBoosting with monotonic constraints"],
    ["Semantic layer", "Kyanos Hotels Model (Direct Lake)", "Governed KPIs, relationships, RLS", "11 tables, 15 relationships, 53 measures, 2 roles"],
    ["Consumption", "Power BI report; data agent; ontology", "Dashboards, Copilot, natural-language Q&A, graph", "Greek and English questions; Teams / M365 Copilot publishable"],
  ], [0.16, 0.25, 0.26, 0.33]),
  H2("Design principles"),
  bullet("**One copy of data:** Delta/Parquet in OneLake is read by Spark, SQL, Power BI (Direct Lake), the data agent and the ontology."),
  bullet("**Near real time where it matters:** the PMS is mirrored; the semantic model includes the live `pms.Reservation` table for the Live PMS page."),
  bullet("**Schema-enabled lakehouse:** schemas separate sources (`pms`, `crm`, `erp`, `ext`) from serving tables (`gold`)."),
  bullet("**Governed metrics:** every KPI is a model measure with description and display folder; visuals and agents never recompute KPIs."),
  bullet("**Security by design:** RLS anchored on `dim_hotel` (per-hotel GM and per-region roles); workspace roles control authoring."),
  bullet("**Everything as code:** every item is deployed through Fabric REST APIs from Python, making the demo repeatable in any tenant."),
  H2("Workspace organisation"),
  table(["Folder", "Items"], [
    ["1 Sources PMS on SQL", "KyanosPMS (SQL database + its SQL analytics endpoint)"],
    ["2 OneLake unified data", "KyanosLakehouse, 01_Ingest_Salesforce_SAP_Airports, 02_Build_Gold_Model"],
    ["3 AI forecasting", "03_AI_Demand_Forecast_2027, MLflow experiment and registered model kyanos-occupancy-forecast"],
    ["4 Power BI", "Kyanos Hotels Model (semantic model), Kyanos Hotels - Commercial Performance (report)"],
    ["5 Agents and Fabric IQ", "Kyanos Revenue & Guest Assistant (data agent), KyanosHotelsOntology (+ its lakehouse and graph model), 04_Fabric_IQ_Ontology_Entities"],
  ], [0.3, 0.7]),
];

const hotelRows = meta.hotels.map(h => [h.HotelCode, h.HotelName, h.Region, h.Airport, h.Concept, String(h.Rooms), h.IsSeasonal ? `${h.OpenMMDD} → ${h.CloseMMDD}` : "Year-round"]);
const dataSec = [
  H1("Data sources and synthetic data"),
  R("All data is generated by `src/gen_data.py` with a fixed random seed, so the dataset is reproducible. The **snapshot date is 6 October 2026**: stays before it are realised (checked-out or in-house), later stays are on-the-books (OTB) business."),
  H2("Hotel portfolio"),
  table(["Code", "Hotel", "Region", "Airport", "Concept", "Rooms", "Season"], hotelRows, [0.1, 0.25, 0.11, 0.08, 0.2, 0.08, 0.18], { size: 15 }),
  H2("Data volumes"),
  table(["Dataset", "System", "Rows", "Notes"], [
    ["pms.Hotel / pms.RoomType", "PMS (SQL)", "24 / 117", "Resorts: 5 room types; city hotels: 4"],
    ["pms.Guest", "PMS (SQL)", rows("pms.Guest"), "Fictional names, emails at example.com, 20 source markets"],
    ["pms.Reservation", "PMS (SQL)", rows("pms.Reservation"), "Arrivals 2025-01-01 → 2027; includes cancellations, no-shows, in-house, OTB; plus live simulator rows"],
    ["privilege_club_members.csv", "Salesforce", rows("crm.privilege_club_member"), "Tier Blue/Silver/Gold/Platinum by lifetime nights; 99 duplicate member IDs (deliberate data-quality issue)"],
    ["guest_cases.csv", "Salesforce", rows("crm.guest_case"), "Complaints, requests, compliments with CSAT 1–5"],
    ["hotel_costs_monthly.csv", "SAP", rows("erp.hotel_cost_monthly"), "6 cost categories by GL account per hotel-month"],
    ["airport_seat_capacity_weekly.csv", "External", rows("ext.airport_seat_capacity"), "12 airports; weekly arriving seats; 2027 = published schedules"],
  ], [0.27, 0.13, 0.12, 0.48]),
  H2("Generation logic"),
  bullet("**Inventory-consistent occupancy:** for each hotel, room type and day a target occupancy is drawn (monthly seasonality × weekday × hotel performance × year factor × noise). Arrivals are created until the target is met, with length of stay truncated at full nights or hotel closure – occupancy can never exceed capacity."),
  bullet("**Seasonality:** resorts peak in July–August (96–98%) and close between November and March/April; city hotels run all year with a weekday/weekend pattern."),
  bullet("**Channels and lead times:** channel mix depends on concept (tour operators dominate all-inclusive resorts, OTAs and corporate dominate city hotels). Lead times are log-normal per channel (tour operators ≈190 days, OTAs ≈40 days)."),
  bullet("**Prices:** ADR = base rate × room-type multiplier × monthly season factor × channel factor × board factor × year factor (+6.5% in 2026) × noise."),
  bullet("**Cancellations and snapshot:** cancellation rates per channel (Booking.com 24%, tour operators 7%). Only bookings made on or before the snapshot are kept; future cancellations stay as Confirmed."),
  bullet("**Extras revenue:** F&B and other spend per adult-night depends on board type and hotel concept, realised only for stayed nights."),
  bullet("**SAP costs:** payroll per room, F&B cost of sales (38%), energy (+12% in 2026), OTA/TO commissions, maintenance and marketing – producing a ~40% GOP margin."),
  H2("Built-in business stories"),
  table(["Story", "How it appears", "Where to show it"], [
    ["Airlines cut seats to Kos and Zakynthos in 2026", "KGS −13%, ZTH −10% seats; RevPAR −6% to −8%; rates held flat", "Executive Overview, Hotel Scorecard, data agent"],
    ["Direct booking strategy is working", "≈12% of OTA demand shifts to direct web in 2026; direct share 34.5% → 38.3%", "Channels & Guests"],
    ["Air-conditioning issue at Kos Marmari", "35% of its 2026 cases are A/C complaints (151 vs 37 for the next category)", "Hotel Scorecard (click the hotel)"],
    ["Summer 2027 seat growth", "Araxos +15%, Chania +12%, Kalamata +11% → forecast up; Kos still declining", "2027 Demand Outlook (AI)"],
    ["Data-quality issue between CRM and PMS", "99 duplicate Privilege Club IDs", "Notebook 02 (de-duplication)"],
  ], [0.3, 0.45, 0.25]),
];

const pmsTables = Object.entries(meta.pms_ddl);
const ingest = [
  H1("Ingestion: PMS mirroring, shortcut and file landing"),
  H2("PMS database (KyanosPMS)"),
  R("`KyanosPMS` is a **Fabric SQL database** (SQL Server engine). It plays the role of the customer's on-premises Protel/SQL Server. All tables have primary keys – a prerequisite for mirroring from SQL Server 2016–2022."),
  ...pmsTables.flatMap(([t, cols]) => [H3(t), table(["Column definition"], cols.map(c => [c]), [1.0], { monoCols: [0], size: 15 })]),
  H2("Loading the PMS"),
  bullet("`src/load_pms.py` creates the `pms` schema and tables, then loads hotels, room types, 255,848 guests and 482,961 reservations."),
  bullet("Connectivity uses **mssql-python** (bundled driver, no ODBC install) with an **Entra access token** from the Azure CLI passed as `SQL_COPT_SS_ACCESS_TOKEN` (attribute 1256)."),
  bullet("Throughput: ~2,000–6,700 rows/s with `executemany` (bulk copy opened a second connection without the token, so the loader falls back automatically). Total load time ≈ 5 min 40 s."),
  bullet("An index `IX_Res_Booking (BookingDate) INCLUDE (HotelId, Status)` supports the simulator and booking-date queries."),
  H2("Mirroring to OneLake"),
  R("A Fabric SQL database replicates every table to OneLake as Delta automatically. Measured: a new Delta log version appeared **within seconds** of an insert, and the Direct Lake model showed **12 new bookings 13 seconds** after they were written."),
  callout("Customer equivalent (SQL Server 2022 on-premises)", "Use the **Mirrored database** item for SQL Server through the on-premises data gateway already used for Power BI. Mirroring SQL Server 2016–2022 relies on **CDC**, needs a **primary key** on every mirrored table, runs from the **primary replica** of an availability group, and requires CDC to be re-enabled after DDL changes. See section 17."),
  H2("Schema-level OneLake shortcut"),
  R("The lakehouse exposes the PMS through **one shortcut at `Tables/pms`** pointing to the SQL database's `Tables/pms` folder. All four PMS tables (and any future table) appear in the lakehouse as `pms.Hotel`, `pms.RoomType`, `pms.Guest`, `pms.Reservation` – **zero copy**."),
  code(`POST /v1/workspaces/{ws}/items/{lakehouseId}/shortcuts?shortcutConflictPolicy=CreateOrOverwrite
{
  "path": "Tables",
  "name": "pms",
  "target": { "oneLake": { "workspaceId": "{ws}", "itemId": "{sqlDatabaseId}", "path": "Tables/pms" } }
}`),
  H2("File landing (Salesforce, SAP, airlines)"),
  table(["Source file", "Landing path", "Bronze/silver table"], [
    ["salesforce_privilege_club_members.csv", "Files/landing/salesforce/privilege_club_members.csv", "crm.privilege_club_member"],
    ["salesforce_guest_cases.csv", "Files/landing/salesforce/guest_cases.csv", "crm.guest_case"],
    ["sap_hotel_costs_monthly.csv", "Files/landing/sap/hotel_costs_monthly.csv", "erp.hotel_cost_monthly"],
    ["airport_seat_capacity_weekly.csv", "Files/landing/external/airport_seat_capacity_weekly.csv", "ext.airport_seat_capacity"],
  ], [0.3, 0.45, 0.25], { monoCols: [1, 2] }),
  R("Files are uploaded with the **OneLake DFS API** (create → append → flush, `x-ms-version: 2021-08-06`, storage audience token). In production Salesforce would use the Data Factory Salesforce connector or Copy job instead of hand-coded API extracts."),
];

const lhRows = Object.entries(T).map(([k, v]) => {
  const [s, t] = k.split(".");
  const role = s === "pms" ? "Shortcut → mirrored PMS" : s === "gold" ? (t.startsWith("iq_") ? "Ontology entity" : t.startsWith("dim_") ? "Gold dimension" : "Gold fact") : "Bronze/silver (typed landing)";
  return [s, t, v.rows.toLocaleString("en-US"), String(v.columns.length), role];
});
const lakehouse = [
  H1("Lakehouse design and data lineage"),
  R("`KyanosLakehouse` is created with `enableSchemas: true`. Schemas separate source-aligned data from serving data:"),
  table(["Schema", "Purpose", "Written by"], [
    ["pms", "Mirrored PMS tables (shortcut, read-only)", "Mirroring"], ["crm", "Salesforce Privilege Club and cases", "01_Ingest"], ["erp", "SAP monthly costs", "01_Ingest"],
    ["ext", "Airline seat capacity", "01_Ingest"], ["gold", "Star schema for BI + forecast + ontology entities", "02, 03, 04"],
  ], [0.15, 0.55, 0.3]),
  H2("Table inventory"),
  table(["Schema", "Table", "Rows", "Cols", "Role"], lhRows, [0.1, 0.32, 0.14, 0.08, 0.36], { monoCols: [1], size: 15 }),
  R("Row counts were taken from the lakehouse SQL analytics endpoint on 7 Oct 2026 (pms.Reservation includes live simulator bookings).", { size: 17, color: MUTED }),
];
const lineageFig = [H2("Data lineage"), ...figure(path.join(IMG, "lineage.png"), 640, "Figure 2 – Data lineage from source to gold")];

const nb = [
  H1("Notebooks and transformation logic"),
  R("Four PySpark notebooks are deployed in Fabric git format (`notebook-content.py`) with the lakehouse attached as default, and executed with the **Jobs API** (`jobType=RunNotebook`). Typical duration on F8: 65–170 seconds."),
  table(["Notebook", "Inputs", "Outputs", "Key logic"], [
    ["01_Ingest_Salesforce_SAP_Airports", "Files/landing/*.csv; pms.Reservation (check)", "crm.*, erp.*, ext.*", "CSV with schema inference + explicit casts; lineage columns _ingested_at, _source_file"],
    ["02_Build_Gold_Model", "pms.*, crm.*, erp.*, ext.*", "gold.dim_* and gold.fact_* (10 tables)", "Conformed dimensions, data-quality de-dup, stay explosion to hotel-nights, hotel calendar"],
    ["03_AI_Demand_Forecast_2027", "gold.fact_reservation, fact_hotel_day, dim_hotel, fact_airport_seats", "gold.fact_occupancy_forecast; MLflow run + registered model", "Booking-pace model, see section 11"],
    ["04_Fabric_IQ_Ontology_Entities", "gold dims and facts", "gold.iq_* (6 tables)", "Business entities for the ontology (VIP guests, upcoming stays, open cases …)"],
  ], [0.22, 0.24, 0.22, 0.32], { size: 15 }),
  H2("Gold table derivations"),
  table(["Gold table", "Grain", "Derivation"], [
    ["dim_date", "Day 2025-01-01 → 2027-12-31", "Generated sequence; year, quarter, month, week_start, weekday, season (Peak/High/Shoulder/Winter), is_actual (≤ snapshot), is_closed_ytd (month < October)"],
    ["dim_hotel", "Hotel", "pms.Hotel renamed; short name; operating model; GM name and email (RLS)"],
    ["dim_airport", "Airport", "12 airports with name and region"],
    ["dim_guest", "Guest", "pms.Guest LEFT JOIN de-duplicated crm.privilege_club_member on loyalty number; tier, opt-in, preference; dropDuplicates(guest_id)"],
    ["fact_reservation", "Reservation", "pms.Reservation + room type; lead_time_days; channel_group (Direct / OTA / Tour Operator & Wholesale / Corporate & MICE); is_cancelled, is_active"],
    ["fact_hotel_day", "Hotel × day", "Active stays exploded into nights (revenue spread evenly) + arrivals, cross-joined with the hotel open/closed calendar → rooms_available, rooms_sold, revenue"],
    ["fact_hotel_cost", "Hotel × month × cost line", "SAP plant code mapped to hotel_id; amount in EUR"],
    ["fact_guest_case", "Case", "Salesforce case with hotel_id via hotel code; category, sub_category, CSAT"],
    ["fact_airport_seats", "Airport × week", "Weekly arriving seats and flights (2025+)"],
    ["fact_occupancy_forecast", "Hotel × day (Jan–Sep 2027)", "Notebook 03 output: OTB, LY, forecast rooms and revenue, drivers, model_run_id"],
  ], [0.2, 0.2, 0.6], { monoCols: [0], size: 15 }),
  H2("Data-quality rules"),
  bullet("**Duplicate loyalty IDs:** 99 Privilege Club IDs are duplicated across Salesforce accounts. Without handling, the join produced duplicate `guest_id` values and broke the many-to-one relationship in the model. Notebook 02 keeps one member record per ID and one row per guest."),
  bullet("**Stay explosion:** each active reservation becomes one row per night, so occupancy and RevPAR are exact at day level."),
  bullet("**Hotel calendar:** `rooms_available` is zero when a seasonal hotel is closed, so occupancy is never diluted by closed days."),
  bullet("**Status logic:** only Checked-Out, In-House and Confirmed stays count as active; cancellations and no-shows are excluded from occupancy."),
];

// ---- semantic model
const relRows = meta.relationships.map(r => [`${r.from_table}[${r.from_col}]`, `${r.to_table}[${r.to_col}]`, "Many-to-one (*:1)", "Single", "Active"]);
const modelSec = [
  H1("Semantic model and table relationships"),
  table(["Property", "Value"], [
    ["Name", "Kyanos Hotels Model"], ["Storage mode", "Direct Lake on OneLake (expression DL_Lakehouse → AzureStorage.DataLake on the lakehouse)"],
    ["Compatibility level", "1702 · culture en-US · discourageImplicitMeasures"], ["Definition format", "TMDL, deployed with the Fabric items API (format TMDL)"],
    ["Tables / relationships / measures", "11 / 15 / 53"], ["Date table", "dim_date (dataCategory Time, date column isKey)"],
    ["Refresh", "None scheduled. Direct Lake reframes automatically on new Delta commits; a full refresh (reframe) is requested after each deployment"],
    ["Security", "RLS roles: Crete Region Manager, Hotel General Manager"],
  ], [0.3, 0.7]),
  sp(60),
  code(`expression DL_Lakehouse =
    let
        Source = AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/${WS_ID}/<lakehouseId>", [HierarchicalNavigation=true])
    in
        Source

partition fact_hotel_day = entity
    mode: directLake
    source
        entityName: fact_hotel_day
        schemaName: gold
        expressionSource: DL_Lakehouse`),
];
const erdFig = figure(path.join(IMG, "erd.png"), 960, "Figure 3 – Table relationship diagram of the semantic model (Direct Lake)", 600);
const modelSec2 = [
  H2("Relationships"),
  table(["From (many)", "To (one)", "Cardinality", "Cross-filter", "State"], relRows, [0.34, 0.26, 0.16, 0.12, 0.12], { monoCols: [0, 1], size: 15 }),
  H2("Relationship design notes"),
  bullet("**Star schema with conformed dimensions.** `dim_hotel` and `dim_date` are shared by all facts, so one slicer filters revenue, costs, cases, forecast and live data consistently."),
  bullet("**Different date roles per fact:** stays by `arrival_date`, costs by `month_start`, cases by `created_date`, seats by `week_start`, hotel-day and forecast by `date`. Last-year measures therefore work for every fact."),
  bullet("**Snowflake to airports:** `dim_hotel[airport_code]` → `dim_airport`. Because filters flow only from `dim_airport` to `dim_hotel`, airline-seat measures use `TREATAS(VALUES(dim_hotel[airport_code]), dim_airport[airport_code])` to respond to hotel filters without a bidirectional relationship."),
  bullet("**Live table:** `live_pms_reservation` maps directly to the mirrored `pms.Reservation` (schema `pms`) and joins only to `dim_hotel` – it powers the Live PMS Feed page without any refresh."),
  bullet("**All single-direction:** no bidirectional or many-to-many relationships, so there are no ambiguous paths and RLS on `dim_hotel` propagates to every fact."),
  H2("Row-level security"),
  table(["Role", "Table filter", "Use"], meta.roles.map(r => [r.name, `${r.table}${r.filter.startsWith("[") ? "" : ""} : ${r.filter}`, r.name.includes("General") ? "Each GM sees only their own hotel (gm_email = signed-in user)" : "Regional manager sees the 6 Crete hotels"]),
    [0.25, 0.4, 0.35], { monoCols: [1] }),
  R("Role members are assigned in the Power BI service. Test with **Security → Test as role** on the semantic model.", { size: 18, color: MUTED }),
  H2("Column conventions"),
  bullet("Keys and raw numeric columns on facts are **hidden**; users work with measures and dimension attributes."),
  bullet("`dim_date[month]` sorts by `month_num`, `dim_date[weekday]` by `weekday_num`; `dim_hotel` latitude/longitude carry geographic data categories."),
  bullet("Numeric key columns use `summarizeBy: none` to avoid implicit aggregation; `discourageImplicitMeasures` is enabled."),
];

// ---- measure catalog
const measureSec = [H1("DAX measure catalog"),
  R("All 53 measures are defined in TMDL with a description and display folder. They are grouped below by host table. Formats use EUR, percentages with one decimal, and signed percentage points for changes.")];
for (const t of meta.model_tables) {
  if (!t.measures.length) continue;
  measureSec.push(H2(`${t.name}  (${t.measures.length} measures)`));
  measureSec.push(table(["Measure", "DAX expression", "Format", "Description"],
    t.measures.map(m => [m.name, m.dax, (m.format || "text").replace(/\\/g, ""), m.description]), [0.2, 0.44, 0.1, 0.26], { monoCols: [1], boldCols: [0], size: 15 }));
}
measureSec.push(H2("DAX patterns used"));
measureSec.push(H3("Time intelligence on a marked date table"));
measureSec.push(code(`RevPAR LY = CALCULATE ( [RevPAR], SAMEPERIODLASTYEAR ( dim_date[date] ) )`));
measureSec.push(R("Because every fact relates to `dim_date`, the same pattern works for occupancy, ADR, revenue, GOP, direct share and airline seats. Pages filter `dim_date[is_closed_ytd] = TRUE` so both years compare January–September."));
measureSec.push(H3("Blank-safe comparisons"));
measureSec.push(code(`RevPAR vs LY % = DIVIDE ( [RevPAR] - [RevPAR LY], [RevPAR LY] )
Occupancy vs LY (pts) = IF ( NOT ISBLANK ( [Occupancy % LY] ), [Occupancy %] - [Occupancy % LY] )`));
measureSec.push(R("The first version used `DIVIDE([RevPAR], [RevPAR LY]) - 1`, which returned −100% when last year was blank (e.g. 2025 has no prior year). The rewritten form returns blank instead."));
measureSec.push(H3("Virtual relationship with TREATAS"));
measureSec.push(code(`Airline Seats =
CALCULATE (
    SUM ( fact_airport_seats[arriving_seats] ),
    TREATAS ( VALUES ( dim_hotel[airport_code] ), dim_airport[airport_code] )
)`));
measureSec.push(R("Pushes the hotel selection onto the airport dimension so seat growth can be shown next to each hotel, keeping the physical relationship single-direction."));
measureSec.push(H3("Rolling 24-hour live window"));
measureSec.push(code(`Bookings Last 24h (live) =
VAR cutoff = NOW () - 1
RETURN
    COALESCE (
        CALCULATE ( COUNTROWS ( live_pms_reservation ), live_pms_reservation[CreatedAt] >= cutoff ),
        0
    )`));
measureSec.push(R("Replaced an earlier `BookingDate = TODAY()` filter that left the Live page empty at the start of a new day. `NOW()` is evaluated in UTC in the service; `CreatedAt` is stored in UTC by the simulator."));
measureSec.push(H3("Weighted ratios instead of averages"));
measureSec.push(code(`Forecast Occupancy % =
DIVIDE ( SUM ( fact_occupancy_forecast[forecast_rooms_sold] ), SUM ( fact_occupancy_forecast[rooms_available] ) )

Seat Growth at Airport % =
DIVIDE (
    SUMX ( fact_occupancy_forecast, fact_occupancy_forecast[seat_growth] * fact_occupancy_forecast[rooms_available] ),
    SUM ( fact_occupancy_forecast[rooms_available] )
)`));
measureSec.push(R("Ratios are always re-computed from additive components (rooms sold ÷ rooms available), never averaged, so totals are correct at any grain. Seat growth is weighted by room capacity."));

// ---- DAX queries
const daxSec = [H1("DAX queries (validation and analysis)"),
  R("The queries below were executed against the deployed model through the Power BI REST API (`POST /groups/{ws}/datasets/{id}/executeQueries`) to validate measures and relationships. Results are the actual values returned on 7 October 2026.")];
for (const q of f2.queries) {
  daxSec.push(H2(q.title));
  daxSec.push(R(q.purpose, { size: 19, color: MUTED }));
  daxSec.push(code(q.dax, { accent: BLUE }));
  daxSec.push(sp(60));
  if (Array.isArray(q.result) && q.result.length) {
    const keys = Object.keys(q.result[0]);
    daxSec.push(table(keys, q.result.map(r => keys.map(k => fmtVal(k, r[k]))), keys.map(() => 1 / keys.length), { size: 15, headFill: TEAL }));
  }
}

// ---- report
const shot = n => path.join(SHOTS, n);
const reportSec = [H1("Power BI report"),
  R("**Kyanos Hotels - Commercial Performance** is deployed in **PBIR** format (definition.pbir, report.json, pages/, visuals/) bound to the semantic model by ID, with a custom theme registered as a static resource."),
  H2("Design system"),
  table(["Element", "Specification"], [
    ["Canvas", "1280 × 720, FitToPage, page background #EEF3F8"],
    ["Theme", `Custom "Kyanos Aegean" – data colours ${meta.theme.dataColors.slice(0, 5).join(", ")}; Segoe UI; navy ${"#0B3C5D"} callouts`],
    ["Header band", "Full-width navy textbox: brand line, page title (18pt), context subtitle (sources, period)"],
    ["KPI tiles", "White rounded container (textbox) + transparent card for the value + transparent card for the comparison (vs LY)"],
    ["Visual containers", "White background, 10px radius, light border, 11pt bold titles, optional subtitles carrying the insight"],
    ["Filters", "Page-level filters on dim_date (year, is_closed_ytd) so every visual compares the same months"],
  ], [0.22, 0.78]),
  H2("Pages"),
];
for (const p of meta.report_pages) {
  reportSec.push(H3(p.name));
  if (p.filters.length) reportSec.push(R("Page filters: " + p.filters.map(f => "`" + f + "`").join(", "), { size: 18 }));
  const vrows = [], kpis = [];
  const isSub = l => /^(vs |pts |last year|pace )/.test(l);
  for (const v of p.visuals.filter(v => v.fields.length)) {
    if (v.type === "card") { const l = v.fields[0]; if (isSub(l) && kpis.length) kpis[kpis.length - 1] += ` (${l})`; else kpis.push(l); continue; }
    vrows.push([v.type, v.title || "", v.fields.join(", ")]);
  }
  if (kpis.length) vrows.unshift([`card ×${kpis.length}`, "KPI tiles", kpis.join("; ")]);
  reportSec.push(table(["Visual", "Title", "Fields / measures"], vrows, [0.22, 0.3, 0.48], { size: 15 }));
}
const shotsList = [["report-executive-overview.png", "Executive Overview"], ["report-hotel-scorecard.png", "Hotel Scorecard"], ["report-channels-guests.png", "Channels & Guests"], ["report-2027-ai-outlook.png", "2027 Demand Outlook (AI)"], ["report-live-pms.png", "Live PMS Feed"]];
const reportShots = [H2("Screenshots")];
shotsList.forEach(([f, n], i) => { if (fs.existsSync(shot(f))) reportShots.push(...figure(shot(f), 620, `Figure ${4 + i} – ${n}`)); });

// ---- forecast
const fcRows = f2.forecast_by_hotel.map(r => [r[0], r[1], r[3] + "%", r[2] + "%", (Number(r[6]) >= 0 ? "+" : "") + r[6], (Number(r[4]) >= 0 ? "+" : "") + r[4] + "%", (Number(r[5]) >= 0 ? "+" : "") + r[5]]);
const fcSec = [H1("AI demand forecast"),
  H2("Business question"),
  R("\u201CHow full will each hotel be next season, given what is already on the books and what the airlines have scheduled?\u201D Revenue managers answer this every October when contracting tour operators and setting rates for the next summer."),
  H2("Approach"),
  bullet("**Target:** change in daily occupancy versus the same weekday last year (`delta_vs_ly = occ − ly_occ`). Predicting the change, not the level, stops the model from simply memorising each hotel."),
  bullet("**Training data:** every open hotel-day of 2026 up to the snapshot (4,534 rows) with its final occupancy, last year's occupancy and the drivers as they stood on 6 Oct 2025."),
  bullet("**Scoring data:** every open hotel-day of Jan–Sep 2027 (4,390 rows) with drivers as of the 6 Oct 2026 snapshot."),
  table(["Feature", "Definition", "Constraint"], [
    ["seat_growth_28d", "Scheduled arriving seats at the hotel's airport vs the same week last year, 28-day centred rolling mean", "Monotonic increasing"],
    ["pace_vs_ly_28d", "(rooms on the books − rooms on the books at the same point last year) ÷ rooms available, 28-day rolling mean", "Monotonic increasing"],
    ["headroom", "1 − last-year occupancy (how much room there is to grow)", "None"],
  ], [0.2, 0.62, 0.18], { monoCols: [0] }),
  bullet(`**Model:** scikit-learn HistGradientBoostingRegressor (max_iter ${fm.params.max_iter}, learning_rate ${fm.params.learning_rate}, max_leaf_nodes ${fm.params.max_leaf_nodes}, min_samples_leaf ${fm.params.min_samples_leaf}, l2 ${fm.params.l2_regularization}) with monotonic constraints so that more seats or a stronger pace can only raise the forecast.`),
  bullet("**Forecast:** `forecast_occ = clip(ly_occ + predicted change, otb_occ, 99.5%)` – never below what is already booked. Forecast room revenue = forecast rooms × last-year ADR × 1.04."),
  H2("Accuracy and tracking"),
  table(["Metric", "Value"], [
    ["Holdout MAE (20% random hotel-days)", `${fm.mae_pts} occupancy points`], ["Baseline: 'same as last year'", `${fm.naive_mae_pts} occupancy points`],
    ["Improvement", `${(100 * (1 - fm.mae_pts / fm.naive_mae_pts)).toFixed(0)}% lower error than the baseline`],
    ["MLflow experiment", "kyanos-occupancy-forecast (run pace-model-summer-2027; params, metrics, model, input example)"],
    ["Registered model", "kyanos-occupancy-forecast (Fabric ML model item, versioned)"],
  ], [0.4, 0.6]),
  H2("Results by hotel (Jan–Sep 2027)"),
  table(["Hotel", "Airport", "2026 occ.", "2027 fcst", "Change (pts)", "Seat growth", "Pace vs LY (pts)"], fcRows, [0.27, 0.09, 0.11, 0.11, 0.13, 0.13, 0.16], { size: 15 }),
  R("Reading: Olympia Riviera (Araxos +15% seats) and Chania (+12%) lead; Kos and Zakynthos stay flat because airlines are still reducing capacity. City hotels gain on Athens/Heraklion/Thessaloniki capacity growth.", { size: 18, color: MUTED }),
  H2("First attempt and lesson learned"),
  R("The first model predicted occupancy directly from on-the-books, last-year occupancy, seats, hotel attributes and calendar. It reproduced last year almost exactly and even forecast growth for Kos despite seat cuts – it had learned hotel identity. Re-framing the target as the change versus last year, smoothing the drivers and adding monotonic constraints produced an explainable model that beats the naive baseline."),
];

// ---- agent
const agentQA = [
  ["Which 3 hotels had the weakest RevPAR vs last year this season, and what happened to airline seats at their airports?",
    "Kos Psalidi Suites −8.1%, Kos Marmari −6.8%, Zakynthos Laganas −6.2%; seats −12.9% (KGS) and −10.2% (ZTH). Interpretation: occupancy-driven decline caused by reduced air capacity rather than price. (≈66 s)"],
  ["Ποια ξενοδοχεία αναμένεται να έχουν τη μεγαλύτερη αύξηση πληρότητας το 2027 και γιατί;",
    "Olympia Riviera +4.4, Chania Kalyves +3.8, Thessaloniki Center +3.4, Heraklion City +3.0, Rethymno Mare +2.8 pts – explained by double-digit growth in available airline seats, with booking pace a secondary factor. Answered in Greek. (≈70 s)"],
];
const agentSec = [H1("Fabric data agent"),
  table(["Property", "Value"], [
    ["Name", "Kyanos Revenue & Guest Assistant"], ["Data source", "Kyanos Hotels Model (type semantic_model) – all 11 tables, visible columns and all 53 measures selected"],
    ["Definition", "Files/Config/data_agent.json, draft/ and published/ stage_config.json + semantic-model datasource.json, publish_info.json"],
    ["Languages", "Greek and English (answers in the language of the question)"], ["Typical response time", "60–70 seconds (Standard runtime)"],
    ["Channels", "Fabric portal; publishable to Microsoft Teams and Microsoft 365 Copilot"],
  ], [0.25, 0.75]),
  H2("Agent instructions"),
  code(meta.agent_instructions.trim(), { size: 14, accent: TEAL }),
  H2("Tested questions"),
  table(["Question", "Answer (summary)"], agentQA, [0.4, 0.6]),
];
if (fs.existsSync(shot("data-agent-english.png"))) agentSec.push(...figure(shot("data-agent-english.png"), 600, "Figure 9 – Data agent answer (English)"));
if (fs.existsSync(shot("data-agent-greek.png"))) agentSec.push(...figure(shot("data-agent-greek.png"), 600, "Figure 10 – Data agent answer (Greek)"));

// ---- ontology
const ontoSec = [H1("Fabric IQ ontology"),
  R("`KyanosHotelsOntology` turns gold tables into connected business concepts that people and agents can navigate (e.g. \u201Cwhich Platinum guests arrive at a hotel with open air-conditioning cases?\u201D). It is deployed through the items API with entity types, data bindings to lakehouse tables (schema `gold`) and relationship contextualizations. Fabric automatically creates a companion lakehouse and graph model."),
  H2("Entity types"),
  table(["Entity", "Bound table", "Key", "Display property", "Properties"], meta.ontology.entities.map(e => [e.name, "gold." + e.table, e.key, e.display, String(e.properties)]), [0.18, 0.27, 0.18, 0.22, 0.15], { monoCols: [1, 2, 3] }),
  H2("Relationships"),
  table(["Relationship", "Source → target", "Binding table", "Join"], meta.ontology.relationships.map(r => [r.name, `${r.source} → ${r.target}`, "gold." + r.table, `${r.source_key} → ${r.fk}`]), [0.17, 0.3, 0.25, 0.28], { monoCols: [2, 3] }),
  H2("Entity tables (notebook 04)"),
  bullet("`iq_hotel` – hotel attributes plus 2026 occupancy, RevPAR, RevPAR vs LY, average case CSAT and open cases."),
  bullet("`iq_airport` – seat growth 2026 and 2027 per airport."),
  bullet(`\`iq_vip_guest\` – ${rows("gold.iq_vip_guest")} Gold/Platinum members with upcoming stays; \`iq_upcoming_stay\` – ${rows("gold.iq_upcoming_stay")} future stays of VIP guests.`),
  bullet(`\`iq_open_case\` – ${rows("gold.iq_open_case")} open Salesforce cases; \`iq_tour_operator\` – 6 tour operators with 2026 room nights and 2027 on-the-books.`),
];
if (fs.existsSync(shot("ontology-graph.png"))) ontoSec.push(...figure(shot("ontology-graph.png"), 600, "Figure 11 – Ontology graph around UpcomingStay"));
ontoSec.push(callout("Note", "The ontology editor shows a banner that a new ontology experience is available (the current one retires on 31 January 2027). The built-in **Ontology agent** (preview) did not respond to an automated test prompt; treat it as optional in demos.", CORAL));

// ---- simulator & ops
const opsSec = [H1("Live PMS simulator and demo operations"),
  H2("Simulator"),
  bullet("`src/pms_live_sim.py` connects to KyanosPMS with an Entra token and inserts realistic reservations (1–3 every ~6 s) with confirmation numbers starting `KL`."),
  bullet("Bookings respect hotel seasons (resorts get Summer 2027 arrivals, city hotels arrive within 75 days), channel mix, board types and rates derived from each hotel's recent Booking.com ADR."),
  bullet("`burst N HOTEL` inserts a tour-operator group block (N rooms × 7 nights) – the visible \"live moment\" in the demo."),
  bullet("The connection is re-established every 40 minutes and on errors, because Entra access tokens expire."),
  H2("Control script"),
  table(["Command", "Effect"], [
    ["./demo-control.ps1 warmup", "Reframe the semantic model, sync the lakehouse SQL endpoint metadata, run warm-up DAX queries"],
    ["./demo-control.ps1 start", "Start the simulator in the background (PID in .sim.pid, log in sim.log)"],
    ["./demo-control.ps1 burst 25 KYN-OLY", "Insert a 25-room group block at Kyanos Olympia Riviera"],
    ["./demo-control.ps1 status", "Process state and number/value of simulator bookings"],
    ["./demo-control.ps1 stop | reset", "Stop the simulator | stop and delete all simulator bookings"],
  ], [0.38, 0.62], { monoCols: [0] }),
  H2("Measured latency"),
  table(["Path", "Observed"], [
    ["INSERT in KyanosPMS → new Delta version in OneLake", "Seconds (new _delta_log entry immediately after insert)"],
    ["INSERT → visible in Direct Lake model (DAX)", "≈13 seconds for a 12-row burst"],
    ["INSERT → visible in lakehouse SQL endpoint via shortcut", "Not until a metadata sync (lazy for shortcut tables); refreshMetadata API forces it"],
  ], [0.55, 0.45]),
  H2("Demo run sheet (summary)"),
  numbered("10:30 – `reset`, `warmup`, `start`; open workspace, report, data agent, SQL query editor, notebook 03, ontology."),
  numbered("Mirroring story → `burst` → Live PMS Feed shows the bookings in ~15 s."),
  numbered("Lakehouse schemas and shortcut → notebook 02 (data quality, Copilot) → Direct Lake model and RLS."),
  numbered("Report: Executive Overview (Kos/Zakynthos), Hotel Scorecard (A/C cluster), Channels (direct strategy), Copilot prompts."),
  numbered("2027 AI outlook and MLflow → data agent in Greek → ontology → phased plan and next steps."),
  R("Full talk track: `docs/DEMO_SCRIPT.md` in the repository.", { size: 18, color: MUTED }),
];

// ---- build process
const procSec = [H1("Build and deployment process")];
const procFig = figure(path.join(IMG, "build-process.png"), 640, "Figure 12 – Build process");
const procSec2 = [
  table(["#", "Step", "Script / API", "What happens"], [
    ["1", "Generate data", "python src/gen_data.py", "Synthetic PMS, Salesforce, SAP and airline datasets (seeded) into data/"],
    ["2", "Provision", "deploy.py infra · POST /workspaces, /items", "Workspace on capacity; Lakehouse (enableSchemas); SQL database; connection details captured in .state.json"],
    ["3", "Load PMS", "python src/load_pms.py · TDS + Entra token", "DDL for pms schema; 483K reservations loaded"],
    ["4", "Mirror + shortcut", "deploy.py shortcut · POST …/shortcuts", "Automatic SQL → OneLake replication; Tables/pms schema shortcut"],
    ["5", "Land files", "deploy.py landing · OneLake DFS API", "Four CSVs to Files/landing/*"],
    ["6", "Notebooks", "deploy.py notebooks run · Jobs API RunNotebook", "Create/update notebooks (fabricGitSource) and run 01 → 02 → 03 (→ 04)"],
    ["7", "Semantic model", "deploy.py model · items API (format TMDL) + Power BI refreshes API", "Deploy TMDL, reframe, validate with executeQueries"],
    ["8", "Report", "deploy.py report · items API (PBIR)", "Deploy pages, visuals and custom theme"],
    ["9", "Data agent", "deploy.py agent · items API", "Instructions + semantic-model data source, draft and published"],
    ["10", "Ontology", "deploy.py run-nb4 ontology", "Entity tables, then ontology definition (entity types, bindings, relationships)"],
    ["11", "Simulator", "demo-control.ps1", "Live bookings; latency measured"],
    ["12", "Verify", "Playwright + DAX", "Portal screenshots of every page, agent tests, KPI checks"],
  ], [0.05, 0.15, 0.33, 0.47], { size: 15 }),
  H2("Authentication"),
  bullet("All REST calls use tokens from `az account get-access-token` (scoped with `--subscription` or `--tenant` from config.json) for the audiences Fabric (`api.fabric.microsoft.com`), Power BI (`analysis.windows.net/powerbi/api`), OneLake storage (`storage.azure.com`) and SQL (`database.windows.net`)."),
  bullet("Every step is idempotent: items are looked up by type and name and updated with `updateDefinition` when they exist."),
  H2("Repository structure"),
  table(["Path", "Content"], [
    ["config.json / .state.json", "Subscription, capacity, workspace name / IDs of deployed items and endpoints"],
    ["src/gen_data.py", "Synthetic data generator (hotels, reservations, guests, CRM, ERP, seats)"],
    ["src/load_pms.py, src/sqlconn.py", "PMS DDL + loader; Entra-token SQL connection helper"],
    ["src/fab.py, src/deploy.py", "Fabric REST helper (auth, LRO polling, definitions); step-based deployer"],
    ["src/notebooks.py", "Notebook sources 01–04"],
    ["src/model.py", "Semantic model: tables, columns, 53 measures, relationships, roles → TMDL"],
    ["src/report.py", "PBIR report builder (pages, visuals, theme)"],
    ["src/agent.py, src/ontology.py", "Data agent definition; ontology definition"],
    ["src/pms_live_sim.py, src/warmup.py, demo-control.ps1", "Live simulator, warm-up, demo control"],
    ["docs/", "DEMO_SCRIPT.md, screenshots, this documentation and its build scripts"],
  ], [0.38, 0.62], { monoCols: [0] }),
];

// ---- issues
const issues = [
  ["Package install via uv failed (TLS handshake)", "Used pip with system Python; mssql-python wheel installed"],
  ["No ODBC Driver 18 on the build machine", "mssql-python (bundled driver) with access token in attrs_before (1256)"],
  ["mssql-python rejected 'Connection Timeout' keyword", "Removed the keyword from the connection string"],
  ["bulkcopy opened a second connection without the token (login failed)", "Automatic fallback to executemany batches of 20K"],
  ["First forecast model ≈ 'same as last year'; Kos forecast to grow", "Target = change vs LY; pace and seat features smoothed; monotonic constraints (MAE 3.31 vs 4.09)"],
  ["Notebook 03 failed: indentation error at the start of a cell", "Fixed; every cell is now compile-checked before deployment"],
  ["Model deploy failed: measure 'Arrivals' clashes with column 'arrivals'", "Renamed to 'Guest Arrivals' (names are case-insensitive in a table)"],
  ["GOP margin unrealistic (56%)", "Recalibrated SAP cost drivers → ~40%"],
  ["vs LY measures showed −100% when LY was blank", "DIVIDE(x − LY, LY) and IF(NOT ISBLANK(LY), …) patterns"],
  ["Airline seats did not react to hotel filters", "TREATAS(VALUES(dim_hotel[airport_code]), dim_airport[airport_code])"],
  ["KPI comparison text clipped under cards", "Tile = container textbox + two transparent cards"],
  ["Channels & Guests visuals failed: duplicate guest_id on the one side", "De-duplicated 99 Privilege Club IDs in notebook 02"],
  ["Lakehouse SQL endpoint did not show new mirrored rows", "Delta and Direct Lake were already current; SQL endpoint metadata sync is lazy for shortcuts → refreshMetadata in warm-up"],
  ["Workspace folder names rejected ('·', '&', '.', '-')", "Simple alphanumeric names (e.g. '4 Power BI')"],
  ["Ontology lakehouse/graph could not be moved to a folder", "Child items move with their parent ontology"],
  ["Browser showed the previous report version after an update", "Hard reload with a cache-busting query parameter"],
  ["Live PMS page empty on a new day (TODAY() filter)", "Rolling 24-hour window with NOW() and COALESCE(…, 0)"],
  ["Ontology agent (preview) did not answer an automated prompt", "Kept optional in the demo"],
];
const issueSec = [H1("Issues encountered and resolutions"), R("Build log of problems found during implementation and testing, and how each was resolved."),
  table(["#", "Issue", "Resolution"], issues.map((r, i) => [String(i + 1), r[0], r[1]]), [0.05, 0.45, 0.5], { size: 15 })];

// ---- considerations
const consSec = [H1("Important considerations"),
  H2("Mirroring SQL Server (customer environment)"),
  bullet("SQL Server **2016–2022** mirroring uses **Change Data Capture**; SQL Server 2025 uses the Fabric change feed and requires Azure Arc."),
  bullet("Tables **must have a primary key** (2016–2022). Legacy PMS tables without keys cannot be mirrored directly – mirror the existing data warehouse instead, or use an incremental Copy job from a readable replica."),
  bullet("Mirroring runs only from the **primary replica** of an availability group; failover cluster instances are not supported."),
  bullet("A **DDL change** on a mirrored table stops mirroring until CDC is disabled and re-enabled for that table (vendor upgrades!)."),
  bullet("Long-running transactions hold back transaction-log truncation – monitor log growth."),
  bullet("Replication compute is free; mirrored storage is free up to a limit tied to capacity size; queries consume capacity. Up to 1,000 tables per mirrored database."),
  bullet("Source **RLS, object-level permissions and dynamic data masking are not propagated** to OneLake – re-apply security in Fabric (semantic model RLS/OLS, OneLake security)."),
  H2("Direct Lake and the semantic model"),
  bullet("No scheduled refresh is needed; framing happens automatically on Delta commits (keep 'Keep Direct Lake data up to date' on). A manual reframe is useful after bulk rebuilds."),
  bullet("Check the **Direct Lake guardrails** for the chosen SKU (rows per table, memory) when sizing production; exceeding them causes fallback or errors."),
  bullet("Calculated tables and calculated columns are not used – all shaping happens in notebooks, which keeps the model Direct Lake-friendly."),
  bullet("Measure names must be unique within a table regardless of case and must not collide with column names."),
  bullet("`NOW()` / `TODAY()` evaluate in **UTC** in the service – align timestamps (the simulator writes UTC)."),
  H2("Security and governance"),
  bullet("RLS roles exist but have no members – assign GMs/regional managers before sharing; test with 'Test as role'."),
  bullet("`dim_guest` contains personal data (names, emails). In production: hide or remove PII columns from broad models, apply object-level security, sensitivity labels and source-side masking."),
  bullet("The data agent and Copilot respect the user's model permissions and RLS."),
  H2("Capacity and licensing"),
  bullet("The whole demo runs on an **F8**; Copilot and data agents work from F2 upward."),
  bullet("Below F64, report consumers need Power BI Pro licences; from F64, viewers with a free licence can consume content."),
  bullet("Pause the capacity when the demo is not needed (a paused capacity makes the items unavailable)."),
  H2("Known limitations of the demo"),
  bullet("Data is synthetic and static apart from the live table; to roll the snapshot forward, change `AS_OF` and regenerate."),
  bullet("Salesforce, SAP and airline data arrive as CSV files rather than live connectors."),
  bullet("The forecast is trained on one season pair (2025 → 2026); production would use several years, weather/events and nightly retraining."),
  bullet("The data agent takes 60–70 seconds per answer; pre-asked questions are kept in the chat as a fallback."),
];

// ---- appendices
const itemRows = items.map(i => [i.folder, i.type, i.name]).sort((a, b) => (a[0] + a[1]).localeCompare(b[0] + b[1]));
const appA = [H1("Appendices"), H2("Appendix A – Fabric item inventory"),
  R("Workspace **Kyanos Hotels - Analytics & AI Demo**. Item IDs are generated per deployment and recorded locally in `.state.json`."),
  table(["Folder", "Type", "Item"], itemRows, [0.3, 0.2, 0.5], { size: 15 })];
const appB = [H2("Appendix B – Semantic model column dictionary")];
for (const t of meta.model_tables) {
  appB.push(H3(`${t.name}  (${t.schema}.${t.entity})`));
  appB.push(R(t.description, { size: 18, color: MUTED }));
  appB.push(table(["Column", "Type", "Visible", "Notes"], t.columns.map(c => [c.name, c.type, c.hidden ? "hidden" : "yes",
    [c.key ? "key (date table)" : "", c.sort ? `sort by ${c.sort}` : "", c.category ? `category ${c.category}` : "", c.format ? `format ${c.format}` : ""].filter(Boolean).join("; ")]),
    [0.32, 0.14, 0.12, 0.42], { monoCols: [0], size: 15 }));
}
const nbSrc = n => meta.notebooks[n].filter(c => c.kind === "code").map(c => c.src);
const appC = [H2("Appendix C – Key code excerpts"),
  H3("fact_hotel_day – stay explosion and hotel calendar (notebook 02)"), code(nbSrc("02_Build_Gold_Model")[3], { size: 14 }),
  H3("Rooms on the books at a snapshot date (notebook 03)"), code(nbSrc("03_AI_Demand_Forecast_2027")[1].split("def frame")[0].trim(), { size: 14 }),
  H3("Model training with MLflow (notebook 03)"), code(nbSrc("03_AI_Demand_Forecast_2027")[2], { size: 14 }),
  H3("Semantic model deployment and refresh (src/deploy.py)"), code(`state["model"] = upsert("SemanticModel", "Kyanos Hotels Model", MD.model_parts(WS, state["lh"]), "TMDL")
POST https://api.powerbi.com/v1.0/myorg/groups/{ws}/datasets/{model}/refreshes   {"type": "full"}
POST https://api.powerbi.com/v1.0/myorg/groups/{ws}/datasets/{model}/executeQueries {"queries":[{"query":"EVALUATE ..."}]}`, { size: 13 }),
];
const appD = [H2("Appendix D – Glossary"),
  table(["Term", "Meaning"], [
    ["ADR", "Average daily rate = room revenue ÷ rooms sold"], ["RevPAR", "Revenue per available room = room revenue ÷ rooms available (= ADR × occupancy)"],
    ["TRevPAR", "Total revenue (rooms + F&B + other) ÷ rooms available"], ["GOP / GOPPAR", "Gross operating profit = total revenue − operating costs; GOP per available room"],
    ["OTB / pace", "On-the-books business for future dates / OTB compared with the same point last year"], ["LY", "Last year, same period (SAMEPERIODLASTYEAR)"],
    ["Mirroring", "Fabric feature that continuously replicates a database into OneLake as Delta"], ["Shortcut", "OneLake pointer to data in another item or store, without copying"],
    ["Direct Lake", "Power BI storage mode that reads Delta tables in OneLake directly, without import refresh"], ["Framing", "Direct Lake step that points the model at the latest Delta version"],
    ["TMDL / PBIR", "Text-based definition formats for semantic models / Power BI reports"], ["MLflow", "Experiment tracking and model registry built into Fabric Data Science"],
    ["Data agent", "Fabric item that answers natural-language questions over selected data sources"], ["Ontology (Fabric IQ)", "Business entities and relationships bound to OneLake data, navigable as a graph"],
  ], [0.22, 0.78]),
];

// ---------------------------------------------------------------- document
const header = new Header({ children: [P([run("Kyanos Hotels & Resorts · Microsoft Fabric solution documentation", { size: 16, color: MUTED })], { align: AlignmentType.RIGHT, after: 0 })] });
const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [run("Page ", { size: 16, color: MUTED }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: MUTED }), run("  ·  fictional demo data", { size: 16, color: MUTED })] })] });
const portrait = { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } };
const landscape = { page: { size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE }, margin: { top: 1000, bottom: 1000, left: 1134, right: 1134 } } };
const sec = (props, children, withHeader = true) => ({ properties: props, headers: withHeader ? { default: header } : undefined, footers: { default: footer }, children });

const doc = new Document({
  creator: "Vangelis Misirlis", title: "Kyanos Hotels & Resorts – Microsoft Fabric solution documentation",
  description: "Architecture, data model, DAX, AI and build process of the Kyanos Fabric demo",
  styles: { default: { document: { run: { font: FONT, size: 20, color: INK } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 36, bold: true, color: NAVY }, paragraph: { spacing: { after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 27, bold: true, color: BLUE }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 23, bold: true, color: TEAL }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 } },
    ] },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: "bullet", text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 240 } } } },
                                { level: 1, format: "bullet", text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 240 } } } }] },
    { reference: "num", levels: [{ level: 0, format: "decimal", text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 300 } } } }] },
  ] },
  sections: [
    sec(portrait, cover, false),
    sec(portrait, [...execSummary]),
    sec(landscape, [...arch, ...archFig]),
    sec(portrait, [...archDetails, ...dataSec, ...ingest, ...lakehouse, ...lineageFig, ...nb, ...modelSec]),
    sec(landscape, [P([run("Table relationship diagram", { size: 24, bold: true, color: BLUE })], { after: 0 }), ...erdFig]),
    sec(portrait, [...modelSec2, ...measureSec, ...daxSec, ...reportSec, ...reportShots, ...fcSec, ...agentSec, ...ontoSec, ...opsSec, ...procSec, ...procFig, ...procSec2, ...issueSec, ...consSec, ...appA, ...appB, ...appC, ...appD]),
  ],
});
const out = path.join(DOCS, "Kyanos_Fabric_Solution_Documentation.docx");
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(out, buf); console.log("written", out, buf.length); });

