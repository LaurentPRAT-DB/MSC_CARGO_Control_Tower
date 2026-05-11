# MSC Air Cargo Control Tower

An operational command center for air cargo disruption management, built on Databricks. The application combines real-time flight operations data with commercial context (revenue, customer tier, sentiment) to enable **business-impact-driven prioritization** during disruptions.

**Live Application:** https://msc-cargo-control-tower-7474645572615955.aws.databricksapps.com

---

## Table of Contents

- [For Air Cargo Operators](#for-air-cargo-operators)
- [For Application Administrators](#for-application-administrators)
- [For Developers](#for-developers)
- [Installation Guide](#installation-guide)
- [Permissions Reference](#permissions-reference)
- [Databricks Best Practices](#databricks-best-practices)

---

## For Air Cargo Operators

### What This Application Does

The Control Tower replaces manual flight-monitoring workflows with an intelligent dashboard that:

1. **Surfaces what matters** — Delays are ranked by business impact (revenue x customer tier x cargo type), not just chronological order
2. **Localizes problems geographically** — Route maps and heatmaps show where in your network disruptions are concentrated
3. **Recommends actions** — AI-powered advisory generates prioritized response plans for delayed flights
4. **Answers ad-hoc questions** — Natural language queries ("Which VIP customers have cargo on delayed flights?") return instant SQL results

### Pages & How to Use Them

#### Home (Operations Overview)

Your shift starts here. The top KPI cards give you instant situational awareness:

| KPI | What It Tells You |
|-----|-------------------|
| Active Flights | Total fleet in motion |
| On-Time Rate | Network health at a glance |
| Revenue at Risk | Dollar impact of current delays |
| VIP Alerts | Platinum/VIP customers affected |
| Protected Flights | SLA-bound flights requiring attention |

The **Priority Alerts** section auto-surfaces the top 3 issues ranked by business impact. The **Top Revenue Customers** table shows which accounts have the most at stake right now.

#### Flight Ops

Your operational workbench for all 50 flights:

- **Filters**: Narrow by Status (On-Time/Delayed/In-Air/Delivered), Protection flag, or Sentiment monitoring
- **Data Table**: Full flight details with origin/destination cities, delays, and flags
- **Flight Route Map**: Arc visualization connecting origins to destinations, color-coded:
  - Red = Delayed
  - Blue = In-Air
  - Green = On-Time
  - Gray = Delivered
- **Delay Heatmap**: Intensity-weighted map showing regional concentration of delays. Hotspots indicate operational stress zones (weather, congestion, or systemic issues at specific hubs)
- **Operations Advisor**: Click "Generate Operations Advisory" to get AI-powered recommendations for managing the current disruptions — re-routing options, customer escalation priorities, and SLA protection steps

**How to read the maps:**
- Cluster of red arcs from one hub = ground-side issue (airport congestion, weather)
- Red arcs on a single corridor = route-specific problem (ATC, airspace closure)
- Heatmap hotspot at origin only = departure-side delay
- Heatmap hotspot at both ends = systemic route degradation

#### Shipments

Track individual Air Waybills (AWBs) with commercial context:

- Filter by commodity type (Doc Charter, Pharma, Perishables, etc.), priority level, or critical revenue flag
- Revenue-at-risk summary for all shipments on delayed flights
- Revenue breakdown by commodity type chart

#### Ask Genie

Natural language interface for ad-hoc data exploration. No SQL knowledge required.

**Example questions:**
- "Which VIP customers have the most revenue at risk?"
- "What is the average delay on protected flights?"
- "Show me all shipments for EliteForward GmbH"
- "Which routes have the highest delay frequency?"
- "List all Doc Charter shipments currently delayed"

The system translates your question into SQL, executes it against the warehouse, and returns structured results.

#### Priority Dashboard

The three pre-built crisis scenarios:

1. **VIP Crisis** — Identifies the highest-impact customer/shipment combinations on delayed flights
2. **Protected Schedule** — SLA compliance tracker for contractually bound flights
3. **Sentiment Watch** — Flights carrying cargo for customers with declining satisfaction scores

Click **"Generate Action Plan"** for an AI-synthesized response plan across all three scenarios.

### Operator Workflow

| Step | What to Do | Where |
|------|-----------|-------|
| 1. Start shift | Check KPIs and Priority Alerts | Home |
| 2. Assess geography | Look at route map and heatmap for patterns | Flight Ops |
| 3. Get AI advisory | Click "Generate Operations Advisory" for delayed flights | Flight Ops |
| 4. Investigate specifics | Filter flights/shipments or ask Genie | Flight Ops / Shipments / Ask Genie |
| 5. Escalate | Use Priority Dashboard for VIP/SLA/Sentiment actions | Priority |

---

## For Application Administrators

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                 Databricks Apps                       │
│  ┌───────────────────────────────────────────────┐  │
│  │  Streamlit Application (app.py)               │  │
│  │  - OAuth M2M via WorkspaceClient()            │  │
│  │  - Service Principal identity                 │  │
│  └───────────┬────────────────┬──────────────────┘  │
│              │                │                       │
│  ┌───────────▼───┐  ┌────────▼──────────┐          │
│  │ SQL Warehouse │  │ Serving Endpoint  │          │
│  │ (Serverless)  │  │ (Claude Sonnet 4) │          │
│  └───────┬───────┘  └──────────────────┘          │
│          │                                          │
│  ┌───────▼─────────────────────────────────┐       │
│  │          Unity Catalog                   │       │
│  │  Catalog: serverless_stable_3n0ihb_catalog│       │
│  │  Schema: msc_air_cargo                   │       │
│  │  Tables: msc_customers, msc_flights,     │       │
│  │          msc_shipments                   │       │
│  │  Views:  v_flight_operations,            │       │
│  │          v_customer_risk,                │       │
│  │          v_revenue_at_risk,              │       │
│  │          v_kpi_summary                   │       │
│  └─────────────────────────────────────────┘       │
│                                                     │
│  ┌─────────────────────────────────────────┐       │
│  │          Genie Space                     │       │
│  │  Natural language SQL interface          │       │
│  │  7 tables/views connected                │       │
│  └─────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

### Environment Variables (app.yaml)

| Variable | Description | Current Value |
|----------|-------------|---------------|
| `GENIE_SPACE_ID` | Genie Space identifier | `01f14d4f205e1e8dac116814dbf0264f` |
| `WAREHOUSE_ID` | SQL Warehouse ID | `b868e84cedeb4262` |
| `CATALOG` | Unity Catalog name | `serverless_stable_3n0ihb_catalog` |
| `SCHEMA` | Schema containing tables | `msc_air_cargo` |
| `LLM_ENDPOINT` | Serving endpoint for AI features | `databricks-claude-sonnet-4` |

Note: `DATABRICKS_HOST` is injected automatically by the Databricks Apps runtime. Do **not** set it manually in app.yaml — it causes authentication conflicts.

### Resources Declared (app.yaml)

```yaml
resources:
  - name: sql-warehouse
    sql_warehouse:
      id: b868e84cedeb4262
      permission: CAN_USE
  - name: serving-endpoint
    serving_endpoint:
      name: databricks-claude-sonnet-4
      permission: CAN_QUERY
```

### Service Principal

When the app is created, Databricks provisions a Service Principal (SP) automatically:

- **Name:** `app-3bk1xb msc-cargo-control-tower`
- **Application ID:** `87492a5a-a174-4e39-b414-6dd7074f835c`
- **Numeric ID:** `75620270025970`

This SP is the identity the app uses to access all Databricks resources.

### Data Pipeline

The application reads from pre-loaded tables. Data refresh workflow:

1. Generate synthetic data: `python dataset/generate_data.py`
2. Upload CSVs to volume: `/Volumes/serverless_stable_3n0ihb_catalog/msc_air_cargo/data_files/`
3. Recreate tables via CTAS (see Installation Guide below)

### Monitoring

- **App health:** Databricks UI > Apps > msc-cargo-control-tower > Logs
- **SQL queries:** Databricks UI > SQL > Query History (filter by warehouse)
- **Serving endpoint:** Databricks UI > Serving > databricks-claude-sonnet-4 > Metrics

---

## For Developers

### Project Structure

```
MSC_CARGO_Control_Tower/
├── streamlit_app/
│   ├── app.py              # Main application (1288 lines, 5 pages)
│   ├── app.yaml            # Databricks App configuration
│   └── requirements.txt    # Python dependencies
├── dataset/
│   ├── generate_data.py    # Synthetic data generator (Faker + pandas)
│   ├── msc_customers.csv   # 30 customers (6 VIP/Platinum)
│   ├── msc_flights.csv     # 50 flights (10 delayed, 8 protected, 5 watched)
│   ├── msc_shipments.csv   # 152 shipments with revenue and priority
│   ├── databricks_ddl.sql  # DDL reference (actual load uses read_files)
│   └── GENIE_SPACE_INSTRUCTIONS.md  # Genie Space setup guide
├── DEMO_SCENARIOS.md       # Detailed demo walkthrough with exact data
└── README.md               # This file
```

### Key Code Patterns

#### Authentication (OAuth M2M)

```python
import os
os.environ.setdefault("HOME", "/tmp")  # Required: Apps runtime lacks $HOME
from databricks.sdk import WorkspaceClient

@st.cache_resource
def get_workspace_client():
    return WorkspaceClient()

def get_auth():
    w = get_workspace_client()
    host = w.config.host
    if host and not host.startswith("http"):
        host = f"https://{host}"
    headers = w.config.authenticate()
    return host, headers
```

**Important:**
- Use `WorkspaceClient()` (not `Config()`) — it handles the full OAuth M2M token exchange
- The `HOME=/tmp` workaround is required because the Apps container lacks a home directory
- Never set `DATABRICKS_HOST` explicitly in app.yaml — the runtime provides it

#### SQL Execution

```python
def execute_sql(sql: str) -> list:
    host, headers = get_auth()
    resp = requests.post(
        f"{host}/api/2.0/sql/statements",
        headers=headers,
        json={"warehouse_id": WAREHOUSE_ID, "statement": sql, "wait_timeout": "30s"},
    )
    return resp.json().get("result", {}).get("data_array", [])
```

#### LLM Calls (Serving Endpoint)

```python
def call_llm(messages: list, max_tokens: int = 1024, temperature: float = 0.7) -> str:
    host, headers = get_auth()
    resp = requests.post(
        f"{host}/serving-endpoints/{LLM_ENDPOINT}/invocations",
        headers=headers,
        json={"messages": messages, "max_tokens": max_tokens, "temperature": temperature},
    )
    return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
```

#### Genie Space Integration

```python
def ask_genie(question: str, conversation_id: str | None = None) -> dict:
    # POST to /api/2.0/genie/spaces/{SPACE_ID}/conversations (new) or
    # POST to /api/2.0/genie/spaces/{SPACE_ID}/conversations/{id}/messages (follow-up)
    # Then poll GET .../messages/{msg_id} until status is terminal
```

#### Map Visualizations (pydeck)

```python
import pydeck as pdk

# City coordinates for the 12 cargo hubs
CITY_COORDS = {
    "Chicago": (41.978, -87.904), "Doha": (25.261, 51.565), ...
}

# ArcLayer for flight routes (color = status)
# HeatmapLayer for delay intensity (weight = delay minutes)
```

### Synthetic Data Generation

```bash
cd dataset
python generate_data.py
```

Produces deterministic data (seed=42) with baked-in demo scenarios:

1. **VIP Crisis:** MSC-807 (LHR→NRT), EliteForward GmbH, $520K Doc Charter, 6-hour delay
2. **Protected Schedule:** 8 flights with `Schedule_Protection_Flag=true`, 2 currently delayed
3. **Sentiment Watch:** 5 flights with `Sentiment_Analysis_Flag=true`, 3 delayed (60% failure rate)

### Dependencies

```
streamlit>=1.30.0       # UI framework (includes pydeck for maps)
databricks-sdk>=0.20.0  # OAuth M2M authentication
requests>=2.31.0        # HTTP client for REST APIs
pandas>=2.0.0           # Data manipulation
```

### Local Development

```bash
# Set environment variables for local testing
export DATABRICKS_HOST="https://fevm-serverless-stable-3n0ihb.cloud.databricks.com"
export WAREHOUSE_ID="b868e84cedeb4262"
export CATALOG="serverless_stable_3n0ihb_catalog"
export SCHEMA="msc_air_cargo"
export GENIE_SPACE_ID="01f14d4f205e1e8dac116814dbf0264f"
export LLM_ENDPOINT="databricks-claude-sonnet-4"

# Run locally (requires Databricks CLI auth configured)
cd streamlit_app
streamlit run app.py
```

Note: Local runs require `databricks configure` with a valid token/profile for the target workspace.

---

## Installation Guide

### Prerequisites

- Databricks workspace with Unity Catalog enabled
- Databricks CLI installed and configured (`pip install databricks-cli` or `brew install databricks`)
- Python 3.10+ with `faker` and `pandas` installed (for data generation)
- Workspace permissions: CREATE CATALOG or access to an existing catalog

### Step 1: Generate Synthetic Data

```bash
cd dataset
pip install faker pandas
python generate_data.py
```

This produces three CSV files in the `dataset/` directory.

### Step 2: Create Schema and Upload Data

```bash
# Set your profile
export DATABRICKS_CONFIG_PROFILE=YOUR_PROFILE

# Create schema
databricks api post /api/2.0/sql/statements --json '{
  "warehouse_id": "YOUR_WAREHOUSE_ID",
  "statement": "CREATE SCHEMA IF NOT EXISTS YOUR_CATALOG.msc_air_cargo",
  "wait_timeout": "30s"
}'

# Create volume for CSV storage
databricks api post /api/2.0/sql/statements --json '{
  "warehouse_id": "YOUR_WAREHOUSE_ID",
  "statement": "CREATE VOLUME IF NOT EXISTS YOUR_CATALOG.msc_air_cargo.data_files",
  "wait_timeout": "30s"
}'

# Upload CSVs
for f in msc_customers.csv msc_flights.csv msc_shipments.csv; do
  databricks fs cp dataset/$f dbfs:/Volumes/YOUR_CATALOG/msc_air_cargo/data_files/$f --overwrite
done
```

### Step 3: Create Tables

```bash
# Create tables using read_files (CTAS pattern)
for tbl in msc_customers msc_flights msc_shipments; do
  databricks api post /api/2.0/sql/statements --json "{
    \"warehouse_id\": \"YOUR_WAREHOUSE_ID\",
    \"statement\": \"CREATE TABLE YOUR_CATALOG.msc_air_cargo.${tbl} AS SELECT * FROM read_files('/Volumes/YOUR_CATALOG/msc_air_cargo/data_files/${tbl}.csv', format => 'csv', header => 'true', inferSchema => 'true')\",
    \"wait_timeout\": \"0s\"
  }"
done
```

Note: CTAS with `read_files` is async — poll `/api/2.0/sql/statements/{statement_id}` until `state=SUCCEEDED`.

### Step 4: Create Metric Views

```sql
-- v_flight_operations: Flights enriched with shipment aggregates
CREATE OR REPLACE VIEW YOUR_CATALOG.msc_air_cargo.v_flight_operations AS
SELECT f.Flight_ID, f.Origin, f.Destination, f.Flight_Status, f.Delay_Minutes,
  f.Schedule_Protection_Flag, f.Sentiment_Analysis_Flag, f.Aircraft_Type,
  COUNT(s.AWB_Number) AS Shipment_Count,
  COALESCE(SUM(s.Revenue_Generated_USD), 0) AS Total_Revenue,
  SUM(CASE WHEN s.Critical_Revenue_Flag = 'true' THEN 1 ELSE 0 END) AS Critical_Shipments
FROM YOUR_CATALOG.msc_air_cargo.msc_flights f
LEFT JOIN YOUR_CATALOG.msc_air_cargo.msc_shipments s ON f.Flight_ID = s.Flight_ID
GROUP BY ALL;

-- v_customer_risk: Customers with revenue exposure on delayed flights
CREATE OR REPLACE VIEW YOUR_CATALOG.msc_air_cargo.v_customer_risk AS
SELECT c.Customer_ID, c.Company_Name, c.Customer_Tier, c.Account_Sentiment_Score,
  c.Annual_Revenue_USD, COUNT(s.AWB_Number) AS Total_Shipments,
  SUM(CASE WHEN f.Flight_Status = 'Delayed' THEN s.Revenue_Generated_USD ELSE 0 END) AS Revenue_At_Risk,
  SUM(CASE WHEN f.Flight_Status = 'Delayed' THEN 1 ELSE 0 END) AS Delayed_Shipments,
  SUM(CASE WHEN s.Critical_Revenue_Flag = 'true' THEN 1 ELSE 0 END) AS Critical_Shipments
FROM YOUR_CATALOG.msc_air_cargo.msc_customers c
LEFT JOIN YOUR_CATALOG.msc_air_cargo.msc_shipments s ON c.Customer_ID = s.Customer_ID
LEFT JOIN YOUR_CATALOG.msc_air_cargo.msc_flights f ON s.Flight_ID = f.Flight_ID
GROUP BY ALL;

-- v_revenue_at_risk: All shipments on delayed flights or flagged critical
CREATE OR REPLACE VIEW YOUR_CATALOG.msc_air_cargo.v_revenue_at_risk AS
SELECT s.AWB_Number, s.Flight_ID, s.Customer_ID, s.Commodity_Type, s.Revenue_Generated_USD,
  s.Priority_Level, s.Critical_Revenue_Flag, f.Flight_Status, f.Delay_Minutes,
  c.Company_Name, c.Customer_Tier, c.Account_Sentiment_Score
FROM YOUR_CATALOG.msc_air_cargo.msc_shipments s
JOIN YOUR_CATALOG.msc_air_cargo.msc_flights f ON s.Flight_ID = f.Flight_ID
JOIN YOUR_CATALOG.msc_air_cargo.msc_customers c ON s.Customer_ID = c.Customer_ID
WHERE f.Flight_Status = 'Delayed' OR s.Critical_Revenue_Flag = 'true';

-- v_kpi_summary: Single-row KPI snapshot
CREATE OR REPLACE VIEW YOUR_CATALOG.msc_air_cargo.v_kpi_summary AS
SELECT COUNT(*) AS Total_Flights,
  SUM(CASE WHEN Flight_Status IN ('On-Time','Delivered') THEN 1 ELSE 0 END) AS On_Time_Flights,
  ROUND(100.0 * SUM(CASE WHEN Flight_Status IN ('On-Time','Delivered') THEN 1 ELSE 0 END) / COUNT(*), 1) AS On_Time_Rate_Pct,
  SUM(CASE WHEN Flight_Status = 'Delayed' THEN 1 ELSE 0 END) AS Delayed_Flights,
  ROUND(AVG(CASE WHEN Delay_Minutes > 0 THEN Delay_Minutes END), 0) AS Avg_Delay_Minutes,
  SUM(CASE WHEN Schedule_Protection_Flag = 'true' THEN 1 ELSE 0 END) AS Protected_Flights,
  SUM(CASE WHEN Sentiment_Analysis_Flag = 'true' THEN 1 ELSE 0 END) AS Sentiment_Watched_Flights
FROM YOUR_CATALOG.msc_air_cargo.msc_flights;
```

### Step 5: Create the Databricks App

```bash
# Create the app (provisions compute + service principal)
databricks apps create msc-cargo-control-tower \
  --description "MSC Air Cargo Control Tower" --no-wait

# Wait for compute to become ACTIVE (~2-3 minutes)
databricks apps get msc-cargo-control-tower
```

### Step 6: Grant Permissions to the Service Principal

```bash
# Get the SP application ID from app details
SP_APP_ID=$(databricks apps get msc-cargo-control-tower | jq -r '.service_principal_client_id')

# Warehouse CAN_USE
databricks api put /api/2.0/permissions/sql/warehouses/YOUR_WAREHOUSE_ID --json "{
  \"access_control_list\": [{
    \"service_principal_name\": \"$SP_APP_ID\",
    \"permission_level\": \"CAN_USE\"
  }]
}"

# Unity Catalog grants (run via SQL)
GRANT USE CATALOG ON CATALOG YOUR_CATALOG TO `<SP_APP_ID>`;
GRANT USE SCHEMA ON SCHEMA YOUR_CATALOG.msc_air_cargo TO `<SP_APP_ID>`;
GRANT SELECT ON TABLE YOUR_CATALOG.msc_air_cargo.msc_customers TO `<SP_APP_ID>`;
GRANT SELECT ON TABLE YOUR_CATALOG.msc_air_cargo.msc_flights TO `<SP_APP_ID>`;
GRANT SELECT ON TABLE YOUR_CATALOG.msc_air_cargo.msc_shipments TO `<SP_APP_ID>`;
GRANT SELECT ON TABLE YOUR_CATALOG.msc_air_cargo.v_flight_operations TO `<SP_APP_ID>`;
GRANT SELECT ON TABLE YOUR_CATALOG.msc_air_cargo.v_customer_risk TO `<SP_APP_ID>`;
GRANT SELECT ON TABLE YOUR_CATALOG.msc_air_cargo.v_revenue_at_risk TO `<SP_APP_ID>`;
GRANT SELECT ON TABLE YOUR_CATALOG.msc_air_cargo.v_kpi_summary TO `<SP_APP_ID>`;
```

### Step 7: Create Genie Space

```bash
databricks api post /api/2.0/genie/spaces --json '{
  "title": "MSC Air Cargo Control Tower",
  "description": "Air cargo operations intelligence...",
  "warehouse_id": "YOUR_WAREHOUSE_ID",
  "serialized_space": "{\"version\":2,\"data_sources\":{\"tables\":[{\"identifier\":\"YOUR_CATALOG.msc_air_cargo.msc_customers\"},{\"identifier\":\"YOUR_CATALOG.msc_air_cargo.msc_flights\"},{\"identifier\":\"YOUR_CATALOG.msc_air_cargo.msc_shipments\"},{\"identifier\":\"YOUR_CATALOG.msc_air_cargo.v_customer_risk\"},{\"identifier\":\"YOUR_CATALOG.msc_air_cargo.v_flight_operations\"},{\"identifier\":\"YOUR_CATALOG.msc_air_cargo.v_kpi_summary\"},{\"identifier\":\"YOUR_CATALOG.msc_air_cargo.v_revenue_at_risk\"}]}}",
  "sample_questions": [
    "Which VIP customers have the most revenue at risk on delayed flights?",
    "What is the total revenue at risk across all delayed flights?",
    "Show me all protected flights and their current delay status"
  ]
}'

# Grant Genie CAN_RUN to the SP
GENIE_SPACE_ID=<returned_space_id>
databricks api patch /api/2.0/permissions/genie/$GENIE_SPACE_ID --json "{
  \"access_control_list\": [
    {\"service_principal_name\": \"$SP_APP_ID\", \"permission_level\": \"CAN_RUN\"},
    {\"group_name\": \"users\", \"permission_level\": \"CAN_RUN\"}
  ]
}"
```

### Step 8: Deploy the Application

```bash
# Update app.yaml with your values (GENIE_SPACE_ID, WAREHOUSE_ID, CATALOG, SCHEMA)

# Upload source to workspace
databricks workspace mkdirs /Workspace/Users/you@company.com/msc-cargo-control-tower
for f in app.py app.yaml requirements.txt; do
  databricks workspace import /Workspace/Users/you@company.com/msc-cargo-control-tower/$f \
    --file streamlit_app/$f --format AUTO --overwrite
done

# Deploy
databricks apps deploy msc-cargo-control-tower \
  --source-code-path /Workspace/Users/you@company.com/msc-cargo-control-tower
```

### Step 9: Verify

1. Open the app URL (shown in `databricks apps get msc-cargo-control-tower`)
2. Check Home page loads KPIs
3. Check Flight Ops page renders maps
4. Check Ask Genie page responds to questions
5. Check Priority Dashboard generates AI action plans

---

## Permissions Reference

### Service Principal Permissions

| Resource | Permission | How to Grant |
|----------|-----------|--------------|
| SQL Warehouse | CAN_USE | Permissions API (`/api/2.0/permissions/sql/warehouses/{id}`) |
| Catalog | USE CATALOG | SQL GRANT statement |
| Schema | USE SCHEMA | SQL GRANT statement |
| Tables (7) | SELECT | SQL GRANT statement per table/view |
| Genie Space | CAN_RUN | Permissions API (`/api/2.0/permissions/genie/{id}`) |
| Serving Endpoint | CAN_QUERY | Declared in app.yaml `resources` section (auto-granted) |

### User Permissions (for Genie Space access)

| Permission | Level | Grants |
|-----------|-------|--------|
| CAN_READ | View space configuration only |
| CAN_RUN | Ask questions and run queries |
| CAN_EDIT | Modify space configuration |
| CAN_MANAGE | Full control including permissions |

Grant `CAN_RUN` to the `users` group for broad access.

### Common Permission Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `cannot configure default credentials` | `DATABRICKS_HOST` set in app.yaml | Remove it — runtime injects automatically |
| `$HOME is not set` | Apps container lacks home directory | Add `os.environ.setdefault("HOME", "/tmp")` |
| `PERMISSION_DENIED` on SQL | SP lacks catalog/schema/table grants | Run GRANT statements using SP application ID |
| `403` on Genie Space | SP lacks CAN_RUN | Patch permissions via `/api/2.0/permissions/genie/{id}` |
| `Warehouse not found` | Wrong warehouse ID or SP lacks CAN_USE | Verify ID and grant CAN_USE via Permissions API |

---

## Databricks Best Practices

### Authentication

- **Always use `WorkspaceClient()`** for Databricks Apps — it handles the full OAuth M2M flow automatically
- **Never hardcode tokens** — the SDK reads credentials from the runtime environment
- **Never set `DATABRICKS_HOST` in app.yaml** — the Apps runtime injects it; setting it manually causes conflicts
- **Cache the client** with `@st.cache_resource` to avoid re-authenticating on every Streamlit rerun

### Data Architecture

- **Use Unity Catalog** for all tables — provides lineage, access control, and audit
- **Pre-compute views** for frequently accessed aggregations (e.g., `v_kpi_summary`) rather than computing them at query time in the app
- **Use `read_files()` with CTAS** for loading CSVs into managed tables — it infers schema and handles type conversion
- **Store raw files in Volumes** (`/Volumes/catalog/schema/volume_name/`) — they integrate with Unity Catalog governance
- **Avoid `CREATE OR REPLACE TABLE`** — use `DROP TABLE IF EXISTS` + `CREATE TABLE` pattern instead

### Application Design

- **Serverless SQL Warehouses** — zero management, instant startup, ideal for interactive apps
- **Declare resources in app.yaml** — the `resources` section auto-provisions permissions for serving endpoints and warehouses
- **Keep the app stateless** — all state lives in the database; the app is a read-only interface
- **Use `st.cache_resource`** for expensive initializations (SDK client, static config)
- **Use `st.cache_data`** with `ttl` for query results that don't change every second

### Genie Space

- **Include metric views** alongside base tables — pre-computed aggregations produce better query results than forcing Genie to join and aggregate
- **Write descriptive `description`** with join keys and column semantics — Genie uses this to understand relationships
- **Add sample questions** — they calibrate the model's understanding of what users typically ask
- **Tables in `serialized_space` must be alphabetically sorted** — the API rejects unsorted lists
- **Grant both SP and users** — the SP needs access for in-app queries, users need access for direct Genie UI usage

### Security

- **Least-privilege grants** — grant SELECT only on tables the app needs, not the entire catalog
- **Use the SP application ID** (UUID format) in GRANT statements — the display name with spaces may not resolve
- **Audit via Unity Catalog** — all queries are logged with the SP identity as the actor
- **No secrets in code** — all configuration via environment variables in app.yaml

### Deployment

- **Deploy from Workspace path** — upload files to `/Workspace/Users/...` then point `--source-code-path` there
- **Redeploy after app.yaml changes** — `databricks apps deploy` picks up new env vars and resources
- **Stop/start for persistent errors** — if the app gets stuck, `databricks apps stop` then `databricks apps start` clears stale state
- **Monitor via app logs** — Databricks UI > Apps > [app name] > Logs shows Streamlit stdout/stderr
- **Pin dependency versions** in production — use exact versions in requirements.txt to avoid breaking changes

### Performance

- **SQL Warehouse auto-stop** — set to 10 minutes for dev, increase for production to avoid cold starts
- **Minimize round-trips** — batch related data into single SQL queries where possible
- **Use `wait_timeout: "30s"`** for interactive queries — fail fast rather than hang
- **Pydeck maps render client-side** — no server load for map visualizations after initial data transfer

---

## Repository

**GitHub:** https://github.com/LaurentPRAT-DB/MSC_CARGO_Control_Tower

**Workspace:** `fevm-serverless-stable-3n0ihb.cloud.databricks.com`

**Demo Walkthrough:** https://docs.google.com/document/d/1etL6lg9Ne2TkjQkWBuNDTlXxHHcLSlevvXa-cL1ub24/edit
