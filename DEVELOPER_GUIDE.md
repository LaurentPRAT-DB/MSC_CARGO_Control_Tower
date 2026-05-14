# Developer Guide — MSC Air Cargo Control Tower

Technical reference for developers and administrators. For business context and architecture overview, see [README.md](README.md).

---

## Table of Contents

- [Project Structure](#project-structure)
- [Key Code Patterns](#key-code-patterns)
- [Installation Guide](#installation-guide)
- [Permissions Reference](#permissions-reference)
- [Best Practices](#best-practices)
- [Local Development](#local-development)

---

## Project Structure

```
MSC_CARGO_Control_Tower/
├── streamlit_app/
│   ├── app.py              # Main application (5 pages)
│   ├── app.yaml            # Databricks App configuration
│   └── requirements.txt    # Python dependencies
├── dataset/
│   ├── generate_data.py    # Synthetic data generator (Faker + pandas)
│   ├── msc_customers.csv   # 30 customers (6 VIP/Platinum)
│   ├── msc_flights.csv     # 50 flights (10 delayed, 8 protected, 5 watched)
│   ├── msc_shipments.csv   # 152 shipments with revenue and priority
│   └── databricks_ddl.sql  # DDL reference
├── README.md               # Business & architecture overview
└── DEVELOPER_GUIDE.md      # This file
```

### Dependencies

```
streamlit>=1.30.0       # UI framework (includes pydeck for maps)
databricks-sdk>=0.20.0  # OAuth M2M authentication
requests>=2.31.0        # HTTP client for REST APIs
pandas>=2.0.0           # Data manipulation
```

---

## Key Code Patterns

### Authentication (OAuth M2M)

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
- Use `WorkspaceClient()` (not `Config()`) — handles full OAuth M2M token exchange
- The `HOME=/tmp` workaround is required because the Apps container lacks a home directory
- Never set `DATABRICKS_HOST` explicitly in app.yaml — the runtime provides it

### SQL Execution

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

### LLM Calls (Serving Endpoint)

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

### Genie Space Integration

```python
def ask_genie(question: str, conversation_id: str | None = None) -> dict:
    # POST to /api/2.0/genie/spaces/{SPACE_ID}/conversations (new) or
    # POST to /api/2.0/genie/spaces/{SPACE_ID}/conversations/{id}/messages (follow-up)
    # Then poll GET .../messages/{msg_id} until status is terminal
```

### Map Visualizations (pydeck)

```python
import pydeck as pdk

# City coordinates for the 12 cargo hubs
CITY_COORDS = {
    "Chicago": (41.978, -87.904), "Doha": (25.261, 51.565), ...
}

# ArcLayer for flight routes (color = status)
# HeatmapLayer for delay intensity (weight = delay minutes)
```

---

## Installation Guide

### Prerequisites

- Databricks workspace with Unity Catalog enabled
- Databricks CLI installed (`pip install databricks-cli` or `brew install databricks`)
- Python 3.10+ with `faker` and `pandas` for data generation
- Workspace permissions: CREATE CATALOG or access to an existing catalog

### Step 1: Generate Synthetic Data

```bash
cd dataset
pip install faker pandas
python generate_data.py
```

Produces deterministic data (seed=42) with baked-in demo scenarios:
1. **VIP Crisis:** Delayed flight with $520K Doc Charter for Platinum customer
2. **Protected Schedule:** 8 flights with `Schedule_Protection_Flag=true`
3. **Sentiment Watch:** 5 monitored flights with mixed delay profiles

### Step 2: Create Schema and Upload Data

```bash
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
for tbl in msc_customers msc_flights msc_shipments; do
  databricks api post /api/2.0/sql/statements --json "{
    \"warehouse_id\": \"YOUR_WAREHOUSE_ID\",
    \"statement\": \"CREATE TABLE YOUR_CATALOG.msc_air_cargo.${tbl} AS SELECT * FROM read_files('/Volumes/YOUR_CATALOG/msc_air_cargo/data_files/${tbl}.csv', format => 'csv', header => 'true', inferSchema => 'true')\",
    \"wait_timeout\": \"0s\"
  }"
done
```

### Step 4: Create Metric Views

```sql
-- v_flight_operations
CREATE OR REPLACE VIEW YOUR_CATALOG.msc_air_cargo.v_flight_operations AS
SELECT f.Flight_ID, f.Origin, f.Destination, f.Flight_Status, f.Delay_Minutes,
  f.Schedule_Protection_Flag, f.Sentiment_Analysis_Flag, f.Aircraft_Type,
  COUNT(s.AWB_Number) AS Shipment_Count,
  COALESCE(SUM(s.Revenue_Generated_USD), 0) AS Total_Revenue,
  SUM(CASE WHEN s.Critical_Revenue_Flag = 'true' THEN 1 ELSE 0 END) AS Critical_Shipments
FROM YOUR_CATALOG.msc_air_cargo.msc_flights f
LEFT JOIN YOUR_CATALOG.msc_air_cargo.msc_shipments s ON f.Flight_ID = s.Flight_ID
GROUP BY ALL;

-- v_customer_risk
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

-- v_revenue_at_risk
CREATE OR REPLACE VIEW YOUR_CATALOG.msc_air_cargo.v_revenue_at_risk AS
SELECT s.AWB_Number, s.Flight_ID, s.Customer_ID, s.Commodity_Type, s.Revenue_Generated_USD,
  s.Priority_Level, s.Critical_Revenue_Flag, f.Flight_Status, f.Delay_Minutes,
  c.Company_Name, c.Customer_Tier, c.Account_Sentiment_Score
FROM YOUR_CATALOG.msc_air_cargo.msc_shipments s
JOIN YOUR_CATALOG.msc_air_cargo.msc_flights f ON s.Flight_ID = f.Flight_ID
JOIN YOUR_CATALOG.msc_air_cargo.msc_customers c ON s.Customer_ID = c.Customer_ID
WHERE f.Flight_Status = 'Delayed' OR s.Critical_Revenue_Flag = 'true';

-- v_kpi_summary
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
databricks apps create msc-cargo-control-tower \
  --description "MSC Air Cargo Control Tower" --no-wait

# Wait for compute to become ACTIVE (~2-3 minutes)
databricks apps get msc-cargo-control-tower
```

### Step 6: Grant Permissions to the Service Principal

```bash
SP_APP_ID=$(databricks apps get msc-cargo-control-tower | jq -r '.service_principal_client_id')

# Warehouse CAN_USE
databricks api put /api/2.0/permissions/sql/warehouses/YOUR_WAREHOUSE_ID --json "{
  \"access_control_list\": [{
    \"service_principal_name\": \"$SP_APP_ID\",
    \"permission_level\": \"CAN_USE\"
  }]
}"
```

```sql
-- Unity Catalog grants
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
  "warehouse_id": "YOUR_WAREHOUSE_ID",
  "table_identifiers": [
    "YOUR_CATALOG.msc_air_cargo.msc_customers",
    "YOUR_CATALOG.msc_air_cargo.msc_flights",
    "YOUR_CATALOG.msc_air_cargo.msc_shipments",
    "YOUR_CATALOG.msc_air_cargo.v_customer_risk",
    "YOUR_CATALOG.msc_air_cargo.v_flight_operations",
    "YOUR_CATALOG.msc_air_cargo.v_kpi_summary",
    "YOUR_CATALOG.msc_air_cargo.v_revenue_at_risk"
  ]
}'

# Grant Genie CAN_RUN to the SP and users
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
| SQL Warehouse | CAN_USE | Permissions API |
| Catalog | USE CATALOG | SQL GRANT |
| Schema | USE SCHEMA | SQL GRANT |
| Tables (7) | SELECT | SQL GRANT per table/view |
| Genie Space | CAN_RUN | Permissions API |
| Serving Endpoint | CAN_QUERY | Declared in app.yaml `resources` (auto-granted) |

### Common Permission Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `cannot configure default credentials` | `DATABRICKS_HOST` set in app.yaml | Remove it — runtime injects automatically |
| `$HOME is not set` | Apps container lacks home directory | Add `os.environ.setdefault("HOME", "/tmp")` |
| `PERMISSION_DENIED` on SQL | SP lacks catalog/schema/table grants | Run GRANT statements |
| `403` on Genie Space | SP lacks CAN_RUN | Patch permissions via Genie API |
| `Warehouse not found` | Wrong ID or SP lacks CAN_USE | Verify ID and grant CAN_USE |

---

## Best Practices

### Authentication
- Always use `WorkspaceClient()` for Databricks Apps
- Never hardcode tokens — the SDK reads from runtime environment
- Cache the client with `@st.cache_resource`

### Data Architecture
- Use Unity Catalog for all tables — provides lineage, access control, and audit
- Pre-compute views for frequently accessed aggregations
- Store raw files in Volumes — they integrate with UC governance

### Application Design
- Serverless SQL Warehouses — zero management, instant startup
- Declare resources in app.yaml — auto-provisions permissions
- Keep the app stateless — all state lives in the database

### Genie Space
- Include metric views alongside base tables — better query results
- Write descriptive table/column descriptions — Genie uses these for NL understanding
- Add benchmarks — validates that Genie produces correct SQL

### Security
- Least-privilege grants — SELECT only on needed tables
- Use the SP application ID (UUID) in GRANT statements
- No secrets in code — all via environment variables

### Deployment
- Deploy from Workspace path — upload then point `--source-code-path`
- Redeploy after app.yaml changes
- Monitor via app logs (Databricks UI > Apps > Logs)

---

## Local Development

```bash
# Set environment variables
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

### Environment Variables (app.yaml)

| Variable | Description |
|----------|-------------|
| `GENIE_SPACE_ID` | Genie Space identifier |
| `WAREHOUSE_ID` | SQL Warehouse ID |
| `CATALOG` | Unity Catalog name |
| `SCHEMA` | Schema containing tables |
| `LLM_ENDPOINT` | Serving endpoint for AI features |
