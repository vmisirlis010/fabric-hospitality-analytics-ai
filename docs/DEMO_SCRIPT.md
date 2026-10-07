# Demo script – Kyanos Hotels & Resorts on Microsoft Fabric

**Audience:** hotel group IT, BI/data and revenue-management teams.
**Duration:** 30 minutes of demo plus discussion.
**Data:** fictional group of 24 Greek hotels; snapshot date 6 October 2026.

## Before the session (30 minutes ahead)

```powershell
./demo-control.ps1 reset     # remove rehearsal bookings
./demo-control.ps1 warmup    # wake the capacity, reframe the model, sync the SQL endpoint
./demo-control.ps1 start     # live PMS bookings every ~6 s
```

Open these tabs (the `status` step prints the workspace, report and agent links):
1. The workspace, in **lineage view**
2. The report **Kyanos Hotels - Commercial Performance** (Executive Overview)
3. The data agent **Kyanos Revenue & Guest Assistant**
4. `KyanosPMS`: a query editor with
   `SELECT TOP 10 ConfirmationNo, HotelId, Channel, ArrivalDate, RoomRevenue, CreatedAt FROM pms.Reservation ORDER BY ReservationId DESC;`
5. Notebook `03_AI_Demand_Forecast_2027` and the ontology `KyanosHotelsOntology`

Each data-agent answer takes about 60–70 seconds. Ask while you talk, or keep earlier answers in the chat as a fallback.

---

## 1. "Our reports depend on a nightly batch" – Mirroring (5 min)

- **Workspace lineage:** SQL database → lakehouse → notebooks → semantic model → report / agent / ontology. Folders follow the same flow.
- **KyanosPMS:** it plays the PMS. Open **Replication → Monitor replication**: every table is replicated to OneLake as Delta automatically, with no ETL and no night window.
- **Live moment:** run `./demo-control.ps1 burst 25 KYN-OLY` (a tour-operator group block). Open **Live PMS Feed** and refresh the visuals. The bookings appear in about 15 seconds.
- **Bridge to their world:** an on-premises SQL Server uses the same Mirroring feature through the on-premises data gateway (CDC, a primary key per table). Often the simplest first step is to mirror the existing data warehouse.

## 2. "Many sources, a heavy model, numbers that don't match" – one lake, one model (6 min)

- **Lakehouse schemas:**
  - `pms` is a zero-copy shortcut to the mirrored PMS (show today's `KL…` bookings);
  - `crm` holds Salesforce data, `erp` holds SAP, `ext` holds airline seats;
  - `gold` is the star schema.
- **Notebook 02:** data quality is handled once for everyone, e.g. duplicate loyalty IDs between CRM and PMS. Show Copilot in the notebook: *"Explain this cell"*.
- **Semantic model:** Direct Lake, so there is no import refresh.
  - 53 governed measures, with descriptions and display folders.
  - RLS roles *Hotel General Manager* (own hotel) and *Crete Region Manager*.
  - The same model feeds the report, Copilot and the data agent.

## 3. Report (6 min)

- **Executive Overview:** revenue €385M (+6.2%), RevPAR €268 (+7.6%), GOP margin 40.2%, direct share 38.3% (34.5% last year).
- **The story:** only Kos and Zakynthos are below last year. Their airports lost 10–13% of airline seats.
- **Hotel Scorecard:** select *Kos Marmari*. Salesforce cases show an air-conditioning complaint cluster, with PMS, CRM and SAP on one page.
- **Channels & Guests:** the direct-booking strategy shows month by month; Privilege Club tiers and source markets.
- **Copilot in Power BI:**
  - *"Summarize this page for the executive committee"*
  - *"Why is RevPAR down at the Kos hotels?"*
  - *"Create a page with ADR and occupancy by month for the Crete hotels"*

## 4. AI forecast – Summer 2027 (4 min)

- **2027 Demand Outlook (AI):** forecast 86.0% vs 84.4% actual in 2026, with forecast room revenue of €320M (+5.4%).
  - Olympia Riviera +4.4 points (Araxos seats +15%) and Chania +3.8 points.
  - Kos stays flat because airlines are still cutting there.
- **Notebook 03 + MLflow experiment:** the model predicts the change versus last year from booking pace and published airline seats, with monotonic constraints.
  - Holdout MAE is 3.3 points, against 4.1 for "same as last year".
  - The model is registered, so it can be retrained every night.

## 5. "Ask instead of opening a report" – data agent (5 min)

Tested questions:
- *"Which 3 hotels had the weakest RevPAR vs last year this season, and what happened to airline seats at their airports?"*
- *"Ποια ξενοδοχεία αναμένεται να έχουν τη μεγαλύτερη αύξηση πληρότητας το 2027 και γιατί;"*
- *"Πόσες κρατήσεις έγιναν τις τελευταίες 24 ώρες και από ποια κανάλια;"* (uses the live PMS table)

Because the agent uses the same semantic model, its numbers match the report. It can be published to Teams and Microsoft 365 Copilot.

## 6. Fabric IQ ontology (2 min)

`KyanosHotelsOntology` links Hotel, Airport, VIP guest, Upcoming stay, Open case and Tour operator. These are business concepts that people and agents can navigate, e.g. VIP guests arriving at a hotel with open cases.

## 7. Close (2 min) – a phased path

1. **Phase 1:**
   - Mirror the existing SQL data warehouse.
   - Point the existing reports at a Direct Lake model.
   - Retire the morning batch window.
2. **Phase 2:** add CRM (Salesforce connector) and ERP data.
3. **Phase 3:** forecasting, the data agent in Teams, and the ontology.

## Q&A cheat sheet

- **Mirroring SQL Server 2016–2022:**
  - Needs CDC, a primary key per table, and the primary replica of an availability group (no failover cluster instance).
  - DDL changes need CDC to be re-enabled for the table.
  - Up to 1,000 tables per database.
  - Replication compute is free; mirrored storage is free up to a limit tied to capacity size.
- **SQL Server 2025** uses the Fabric change feed and needs Azure Arc.
- **Security:** source RLS, column permissions and masking are not propagated – re-apply them in Fabric (model RLS/OLS, OneLake security).
- **Licensing:** capacity is assigned per workspace; Copilot and data agents work from F2; report viewers need Pro below F64.

## After the session

```powershell
./demo-control.ps1 stop      # or reset to also delete the demo bookings
```
