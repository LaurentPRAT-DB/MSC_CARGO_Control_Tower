# MSC Air Cargo Control Tower

**Protect revenue, retain VIP customers, and enforce SLA compliance during flight disruptions — powered by Databricks.**

[Live Application](https://msc-cargo-control-tower-7474645572615955.aws.databricksapps.com) | [Demo Walkthrough](https://docs.google.com/document/d/1etL6lg9Ne2TkjQkWBuNDTlXxHHcLSlevvXa-cL1ub24/edit)

---

## For Business Users

### The Problem

Air cargo operations face a compounding problem during disruptions: **a single delayed flight can put millions in revenue at risk, damage VIP customer relationships, and trigger SLA penalties** — all within hours.

Traditional operations teams monitor flights in isolation. They see delays, but lack the commercial context to prioritize: Which delayed flight carries $520K of pharmaceutical cargo for a Platinum customer whose sentiment score is already dropping? Which protected flight is 3 hours from breaching its contractual SLA?

### What the Control Tower Does

| Capability | What It Does | Business Outcome |
|-----------|-------------|-----------------|
| Revenue-at-Risk Scoring | Ranks delays by composite business-impact score | Ops teams focus on the highest-value disruptions first |
| VIP Crisis Detection | Auto-surfaces Platinum/VIP cargo on delayed flights, weighted by account health | Account managers get alerted before customers escalate |
| SLA Compliance Tracker | Monitors protected flights against contractual deadlines | Penalty costs are mitigated before breach occurs |
| AI Operations Advisor | Generates specific re-routing and escalation plans per crisis | Reduces decision time from hours to minutes |
| Natural Language Queries | Ask questions in plain English via Genie, get instant data answers with follow-up suggestions | No SQL expertise required for ad-hoc investigation |

### Crisis Ranking Formula

Crises are ranked by a composite score that combines three business signals:

```
Score = Revenue × (11 - Sentiment) × Delay_Minutes
```

- **Revenue**: Total USD value of shipments on the flight
- **Sentiment**: Customer account health (1-10 scale) — lower sentiment amplifies urgency
- **Delay**: Minutes of delay — longer delays compound impact

### Pages Overview

| Page | Purpose |
|------|---------|
| **Home** | KPI dashboard: active flights, on-time rate, revenue at risk, VIP alerts |
| **Flight Ops** | Interactive route map, delay heatmap, AI-generated operations advisory |
| **Shipments** | Revenue tracker with filters by commodity, priority, critical revenue flag |
| **Ask Genie** | Natural language Q&A with auto-generated charts and follow-up suggestions |
| **Priority** | Top VIP crises, SLA compliance, sentiment-watched flights with AI action plans |

---

## For Administrators

### Architecture

The entire stack runs on Databricks — no external services, no separate cloud infrastructure.

```
 ┌──────────────────────────────────────────────────────────────────────┐
 │                      DATABRICKS PLATFORM                            │
 │                                                                     │
 │  ┌─────────────────────────────────────────────────────────────┐    │
 │  │                    Databricks Apps                          │    │
 │  │   Streamlit application · OAuth M2M · Service Principal     │    │
 │  └──────┬──────────────────┬──────────────────┬────────────────┘    │
 │         │                  │                  │                     │
 │         ▼                  ▼                  ▼                     │
 │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐       │
 │  │ SQL Warehouse│  │ Genie Space  │  │  Model Serving     │       │
 │  │ (Serverless) │  │ (NL → SQL)   │  │  (Claude Sonnet 4) │       │
 │  └──────┬───────┘  └──────┬───────┘  └────────────────────┘       │
 │         │                 │                                        │
 │         ▼                 ▼                                        │
 │  ┌─────────────────────────────────────────────────────────────┐   │
 │  │                    Unity Catalog                            │   │
 │  │   Catalog: serverless_stable_3n0ihb_catalog                │   │
 │  │   Schema: msc_air_cargo                                    │   │
 │  │                                                             │   │
 │  │   Tables: msc_customers · msc_flights · msc_shipments      │   │
 │  │   Views:  v_kpi_summary · v_customer_risk                  │   │
 │  │           v_flight_operations · v_revenue_at_risk           │   │
 │  └─────────────────────────────────────────────────────────────┘   │
 └──────────────────────────────────────────────────────────────────────┘
```

### Component Roles

| Component | Role | Integration |
|-----------|------|-------------|
| **Databricks Apps** | Hosts Streamlit with managed compute and automatic OAuth | Calls all services via `WorkspaceClient` |
| **Unity Catalog** | Governed data layer — tables, views, lineage, access control | Queried by SQL Warehouse; metadata read by Genie |
| **Serverless SQL Warehouse** | Executes all SQL queries, zero infrastructure management | Statement Execution API |
| **Genie Space** | Natural language → SQL with domain-specific join hints and benchmarks | Genie Conversation API |
| **Model Serving** | LLM for operations advisory and follow-up question generation | Serving Endpoint API |

### Installation

**Prerequisites:**
- Databricks workspace with Unity Catalog enabled
- Serverless SQL Warehouse
- Model Serving endpoint (Claude Sonnet 4 or equivalent)
- Databricks CLI configured

**Step 1 — Generate and upload data:**

```bash
cd dataset && pip install faker pandas && python generate_data.py
databricks fs cp dataset/*.csv dbfs:/Volumes/YOUR_CATALOG/msc_air_cargo/data_files/ --overwrite
```

**Step 2 — Create tables and views:**

Run `dataset/databricks_ddl.sql` against your SQL Warehouse. This creates:
- 3 tables: `msc_customers`, `msc_flights`, `msc_shipments`
- 4 views: `v_kpi_summary`, `v_customer_risk`, `v_flight_operations`, `v_revenue_at_risk`

**Step 3 — Create the Genie Space:**

Create a Genie Space with all 7 tables/views. Add join hints and sample questions relevant to air cargo operations.

**Step 4 — Configure and deploy the app:**

Edit `streamlit_app/app.yaml` with your values:

```yaml
env:
  - name: GENIE_SPACE_ID
    value: "your-genie-space-id"
  - name: WAREHOUSE_ID
    value: "your-warehouse-id"
  - name: CATALOG
    value: "your_catalog"
  - name: SCHEMA
    value: "msc_air_cargo"
  - name: LLM_ENDPOINT
    value: "databricks-claude-sonnet-4"

resources:
  - name: sql-warehouse
    sql_warehouse:
      id: your-warehouse-id
      permission: CAN_USE
  - name: serving-endpoint
    serving_endpoint:
      name: databricks-claude-sonnet-4
      permission: CAN_QUERY
```

Deploy:

```bash
# Upload source code
databricks workspace import-dir streamlit_app /Workspace/Users/you@company.com/msc-cargo-control-tower

# Deploy the app
databricks apps create msc-cargo-control-tower \
  --source-code-path /Workspace/Users/you@company.com/msc-cargo-control-tower
```

### Security & Governance

- **Authentication**: OAuth M2M — no tokens or passwords in code
- **Authorization**: Service Principal with least-privilege grants (`SELECT` only)
- **Audit**: Every SQL query, Genie conversation, and LLM call logged with SP identity
- **Lineage**: Unity Catalog tracks data from volumes → tables → views → query results
- **Access Control**: Column-level security available for sensitive fields

---

## For Developers

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| UI Framework | Streamlit ≥1.30 | Multi-page app with chat, charts, maps |
| Maps | pydeck (bundled with Streamlit) | ArcLayer routes, HeatmapLayer delays |
| Auth | databricks-sdk ≥0.20 | `WorkspaceClient` for OAuth M2M |
| HTTP | requests ≥2.31 | REST calls to Genie and Model Serving APIs |
| Data | pandas ≥2.0 | DataFrame handling and numeric conversion |
| Hosting | Databricks Apps | Managed Streamlit with auto-scaling |

### Caching Strategy

The app uses three caching tiers to balance freshness with performance:

| Cache Type | Decorator | TTL | What It Caches |
|-----------|-----------|-----|----------------|
| **Resource cache** | `@st.cache_resource` | Session lifetime | `WorkspaceClient` instance (shared across reruns) |
| **Data version check** | `@st.cache_data(ttl=60)` | 60 seconds | Lightweight metadata query to detect table changes |
| **SQL results** | `@st.cache_data(ttl=300)` | 5 minutes | All SQL query results, keyed by (query + data_version) |

**How it works:**

1. Every SQL query first checks `_get_data_version()` (cached 60s) which queries table metadata
2. The data version string is passed as a parameter to `_execute_sql_cached()` — if data changes, the cache key changes and results refresh
3. The `WorkspaceClient` is created once per session and reused for all API calls

**Cache invalidation:** Data refreshes within 60s of underlying table changes. Manual invalidation is not needed — Streamlit's TTL handles expiry automatically.

### Genie Integration & LLM Follow-ups

The Ask Genie page combines two AI systems:

```
User Question
     │
     ▼
┌─────────────────┐     ┌──────────────────┐
│  Genie API      │────▶│  Tabular Results  │──── Auto-chart (bar/line)
│  (NL → SQL)     │     │  + Text Response  │
└─────────────────┘     └──────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  LLM Endpoint    │──── 3 Follow-up Suggestions
                        │  (Claude Sonnet) │     (SQL-answerable only)
                        └──────────────────┘
```

**Genie API behavior:**
- The Conversation API returns **tabular data only** — no charts, no follow-up suggestions
- Charts are rendered client-side: bar chart for ≤20 rows, line chart otherwise
- The API requires polling; status progresses through: `SUBMITTED` → `PENDING_WAREHOUSE` → `ASKING_AI` → `FETCHING_METADATA` → `FILTERING_CONTEXT` → `EXECUTING_QUERY` → `COMPLETED`
- Conversations maintain context — follow-ups in the same conversation inherit query context

**LLM-generated follow-ups:**
- After each successful Genie response, the LLM generates 3 follow-up questions
- Prompt constrains suggestions to **SQL-answerable questions only** (filtering, aggregating, comparing)
- This prevents "no response" failures from open-ended analytical questions Genie can't handle
- Follow-ups are displayed as clickable buttons below the response
- Only the most recent message shows follow-up buttons (history messages hide them)

**Key implementation details:**
- `ask_genie()` (line ~486): Handles conversation start/continue, polling, and result extraction
- `generate_followup_questions()` (line ~1266): LLM call with constrained prompt
- `display_genie_result()` (line ~1284): Renders text, table, auto-chart, SQL, and follow-up buttons
- Conversation reset: "New Conversation" button clears `genie_conv_id` to start fresh

### LLM Usage Summary

| Feature | Endpoint | Prompt Strategy | Output |
|---------|----------|----------------|--------|
| Operations Advisor | `databricks-claude-sonnet-4` | System prompt with all delayed flights + shipment data as context | Structured advisory with re-routing options |
| Crisis Response | `databricks-claude-sonnet-4` | Highest-impact VIP crisis data + composite score context | Immediate action plan |
| Follow-up Suggestions | `databricks-claude-sonnet-4` | Previous Q&A + data columns; constrained to SQL-answerable | 3 one-line questions |

### Project Structure

```
MSC_CARGO_Control_Tower/
├── streamlit_app/
│   ├── app.py              # Main application (~1600 lines, 5 pages)
│   ├── app.yaml            # Databricks App config (env vars + resources)
│   └── requirements.txt    # Python dependencies
├── dataset/
│   ├── generate_data.py    # Synthetic data generator (Faker + pandas)
│   ├── msc_customers.csv   # 30 customers (6 VIP/Platinum)
│   ├── msc_flights.csv     # 50 flights (10 delayed, 8 protected)
│   ├── msc_shipments.csv   # 152 shipments with revenue and priority
│   └── databricks_ddl.sql  # DDL for tables and views
├── README.md               # This file
└── DEVELOPER_GUIDE.md      # Detailed code patterns and permissions
```

---

## Links

| Resource | URL |
|----------|-----|
| Live App | [msc-cargo-control-tower](https://msc-cargo-control-tower-7474645572615955.aws.databricksapps.com) |
| GitHub | [LaurentPRAT-DB/MSC_CARGO_Control_Tower](https://github.com/LaurentPRAT-DB/MSC_CARGO_Control_Tower) |
| Demo Walkthrough | [Google Doc](https://docs.google.com/document/d/1etL6lg9Ne2TkjQkWBuNDTlXxHHcLSlevvXa-cL1ub24/edit) |
| Workspace | `fevm-serverless-stable-3n0ihb.cloud.databricks.com` |
