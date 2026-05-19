import os

os.environ.setdefault("HOME", "/tmp")

import re
import time
import json
import requests
import streamlit as st
import pandas as pd
from databricks.sdk import WorkspaceClient

APP_VERSION = "1.1.0"
APP_BUILD = "20260519-1045"

st.set_page_config(
    page_title="MSC Air Cargo — Control Tower",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Configuration ---
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "")
GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID", "")
WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "")
CATALOG = os.getenv("CATALOG", "serverless_stable_3n0ihb_catalog")
SCHEMA = os.getenv("SCHEMA", "msc_air_cargo")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "databricks-claude-sonnet-4")

# --- Custom CSS — dark aviation/ops theme ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stSidebar {display: none;}
    .block-container {padding-top: 0 !important; max-width: 1200px;}

    .top-nav {
        position: fixed;
        top: 0; left: 0; right: 0;
        z-index: 999;
        background: #0a1628 !important;
        border-bottom: 1px solid #1e3a5f;
        padding: 0 2rem;
        height: 90px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .nav-top-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .nav-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .nav-brand-title {
        font-size: 18px;
        font-weight: 700;
        color: #f1f5f9 !important;
    }
    .nav-brand-subtitle {
        font-size: 12px;
        color: #94a3b8 !important;
    }
    .nav-badge {
        background: #fef3cd;
        color: #856404;
        border: 1px solid #f0d68a;
        border-radius: 16px;
        padding: 2px 12px;
        font-size: 11px;
        font-weight: 500;
        margin-left: 12px;
    }
    .nav-right {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .nav-link {
        color: #93c5fd !important;
        font-size: 13px;
        text-decoration: none;
    }
    .nav-user {
        background: #1e293b;
        border: 1px solid #475569;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 12px;
        color: #e2e8f0 !important;
    }

    .main-content { margin-top: 100px; }

    .hero-banner {
        background: linear-gradient(135deg, #0a1628 0%, #1a2d4a 60%, #2a4060 100%);
        border-radius: 16px;
        padding: 48px 48px 24px 48px;
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
        color: white;
    }
    .hero-banner::after {
        content: '';
        position: absolute;
        right: -80px; top: -80px;
        width: 400px; height: 400px;
        border-radius: 50%;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
    }
    .hero-category {
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 1.5px;
        color: #f59e0b;
        text-transform: uppercase;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .hero-category::before {
        content: '';
        display: inline-block;
        width: 32px; height: 2px;
        background: #f59e0b;
    }
    .hero-title {
        font-size: 32px;
        font-weight: 700;
        color: white;
        margin-bottom: 12px;
    }
    .hero-subtitle {
        font-size: 15px;
        color: rgba(255,255,255,0.85) !important;
        margin-bottom: 24px;
        max-width: 600px;
        line-height: 1.5;
    }
    .hero-date {
        font-size: 12px;
        color: rgba(255,255,255,0.5);
        padding-top: 16px;
        border-top: 1px solid rgba(255,255,255,0.1);
    }

    .section-title {
        font-size: 22px;
        font-weight: 700;
        color: #ffffff !important;
        margin-bottom: 4px;
    }
    .section-subtitle {
        font-size: 14px;
        color: #9ca3af !important;
        margin-bottom: 20px;
    }

    .kpi-card {
        background: #1e293b !important;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px 24px;
        position: relative;
        overflow: hidden;
        height: 140px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
    }
    .kpi-card.blue::before { background: #2563eb; }
    .kpi-card.amber::before { background: #f59e0b; }
    .kpi-card.red::before { background: #dc2626; }
    .kpi-card.green::before { background: #16a34a; }
    .kpi-label {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.8px;
        color: #94a3b8 !important;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 36px;
        font-weight: 700;
        color: #f1f5f9 !important;
        line-height: 1.1;
        margin-bottom: 8px;
    }
    .kpi-desc {
        font-size: 12px;
        color: #64748b !important;
    }

    .alert-card {
        background: #1e293b !important;
        border: 1px solid #dc2626;
        border-left: 4px solid #dc2626;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .alert-card.warning {
        border-color: #f59e0b;
        border-left-color: #f59e0b;
    }
    .alert-card.info {
        border-color: #2563eb;
        border-left-color: #2563eb;
    }
    .alert-title {
        font-size: 14px;
        font-weight: 600;
        color: #f1f5f9 !important;
        margin-bottom: 4px;
    }
    .alert-desc {
        font-size: 12px;
        color: #94a3b8 !important;
    }
    .alert-meta {
        font-size: 11px;
        color: #64748b !important;
        margin-top: 8px;
    }

    .activity-item {
        background: #1e293b !important;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }
    .activity-item-title {
        font-size: 14px;
        font-weight: 600;
        color: #f1f5f9 !important;
        margin-bottom: 4px;
    }
    .activity-item-desc {
        font-size: 12px;
        color: #94a3b8 !important;
    }
    .activity-tag {
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: 500;
        display: inline-block;
        margin-top: 6px;
        margin-right: 4px;
    }
    .activity-tag.red { background: #fecaca; color: #991b1b; border: 1px solid #f87171; }
    .activity-tag.amber { background: #fef3cd; color: #856404; border: 1px solid #f0d68a; }
    .activity-tag.green { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
    .activity-tag.blue { background: #dbeafe; color: #1e40af; border: 1px solid #93c5fd; }
    .activity-tag.gray { background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; }
    .activity-item-stat {
        text-align: right;
        min-width: 80px;
    }
    .activity-item-stat-value {
        font-size: 16px;
        font-weight: 700;
        color: #f1f5f9 !important;
    }
    .activity-item-stat-label {
        font-size: 11px;
        color: #64748b !important;
    }

    .priority-card {
        background: #1e293b !important;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
    }
    .priority-card-title {
        font-size: 16px;
        font-weight: 700;
        color: #f1f5f9 !important;
        margin-bottom: 8px;
    }
    .priority-card-value {
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .priority-card-value.red { color: #ef4444 !important; }
    .priority-card-value.amber { color: #f59e0b !important; }
    .priority-card-value.green { color: #10b981 !important; }
    .priority-card-desc {
        font-size: 13px;
        color: #94a3b8 !important;
        line-height: 1.5;
    }

    div[data-testid="stHorizontalBlock"] button[kind="secondary"],
    div[data-testid="stHorizontalBlock"] button[kind="primary"] {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #93c5fd !important;
        font-weight: 500;
        min-height: 56px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover,
    div[data-testid="stHorizontalBlock"] button[kind="primary"]:hover {
        background: #334155 !important;
        color: #bfdbfe !important;
    }
    div[data-testid="stHorizontalBlock"] button[kind="primary"] {
        border: 2px solid #3b82f6 !important;
        color: #ffffff !important;
    }
    div[data-testid="stHorizontalBlock"] button p { color: inherit !important; }

    .footer {
        text-align: center;
        color: #64748b !important;
        font-size: 12px;
        padding: 32px 0 16px 0;
        border-top: 1px solid #334155;
        margin-top: 48px;
    }

    div[data-testid="stVerticalBlock"] > div {gap: 0.5rem;}
    .stMetric { display: none; }

    .advisory-section {
        background: #1e293b !important;
        border: 1px solid #334155;
        border-left: 4px solid #3b82f6;
        border-radius: 10px;
        padding: 20px 24px;
        margin-bottom: 16px;
    }
    .advisory-section.urgent {
        border-left-color: #dc2626;
    }
    .advisory-section.warning {
        border-left-color: #f59e0b;
    }
    .advisory-section.info {
        border-left-color: #2563eb;
    }
    .advisory-section.success {
        border-left-color: #10b981;
    }
    .advisory-section-title {
        font-size: 15px;
        font-weight: 700;
        color: #f1f5f9 !important;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .advisory-section-body {
        font-size: 13px;
        color: #cbd5e1 !important;
        line-height: 1.7;
    }
    .advisory-section-body strong {
        color: #f1f5f9 !important;
    }
    .advisory-section-body ul {
        padding-left: 18px;
        margin: 8px 0;
    }
    .advisory-section-body li {
        margin-bottom: 8px;
    }
    .advisory-header {
        font-size: 18px;
        font-weight: 700;
        color: #f1f5f9 !important;
        margin-bottom: 4px;
    }
    .advisory-subtitle {
        font-size: 13px;
        color: #94a3b8 !important;
        margin-bottom: 20px;
    }

</style>
""", unsafe_allow_html=True)


# --- Backend Functions ---
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


def execute_sql(sql: str) -> list:
    host, headers = get_auth()
    resp = requests.post(
        f"{host}/api/2.0/sql/statements",
        headers=headers,
        json={"warehouse_id": WAREHOUSE_ID, "statement": sql, "wait_timeout": "30s"},
    )
    if resp.status_code >= 400:
        return []
    result = resp.json()
    if result.get("status", {}).get("state") == "FAILED":
        return []
    return result.get("result", {}).get("data_array", [])


def execute_sql_with_columns(sql: str) -> tuple[list, list]:
    host, headers = get_auth()
    resp = requests.post(
        f"{host}/api/2.0/sql/statements",
        headers=headers,
        json={"warehouse_id": WAREHOUSE_ID, "statement": sql, "wait_timeout": "30s"},
    )
    if resp.status_code >= 400:
        return [], []
    result = resp.json()
    if result.get("status", {}).get("state") == "FAILED":
        return [], []
    columns = [c.get("name", "") for c in result.get("manifest", {}).get("schema", {}).get("columns", [])]
    data = result.get("result", {}).get("data_array", [])
    return columns, data


def ask_genie(question: str, conversation_id: str | None = None) -> dict:
    host, headers = get_auth()
    base = f"{host}/api/2.0/genie/spaces/{GENIE_SPACE_ID}"

    if conversation_id:
        resp = requests.post(
            f"{base}/conversations/{conversation_id}/messages",
            headers=headers, json={"content": question},
        )
        if resp.status_code >= 400:
            return {"status": "FAILED", "error": f"API error: {resp.text[:200]}"}
        data = resp.json()
        msg_id = data.get("message_id") or data.get("id")
    else:
        resp = requests.post(
            f"{base}/start-conversation",
            headers=headers, json={"content": question},
        )
        if resp.status_code >= 400:
            return {"status": "FAILED", "error": f"API error: {resp.text[:200]}"}
        data = resp.json()
        conversation_id = data.get("conversation_id")
        msg_id = data.get("message_id")

    if not conversation_id or not msg_id:
        return {"status": "FAILED", "error": f"Missing IDs. Response: {data}"}

    PENDING_STATUSES = {"EXECUTING_QUERY", "FETCHING_METADATA", "ASKING_AI", "SUBMITTED", "FILTERING", "PENDING", ""}
    time.sleep(2)
    for _ in range(80):
        poll_resp = requests.get(
            f"{base}/conversations/{conversation_id}/messages/{msg_id}",
            headers=headers,
        )
        if poll_resp.status_code >= 400:
            time.sleep(2)
            continue
        msg = poll_resp.json()
        status = msg.get("status", "")
        if status not in PENDING_STATUSES:
            result = {
                "conversation_id": conversation_id,
                "status": status,
                "text_response": None,
                "sql": None,
                "columns": None,
                "data": None,
            }
            for att in msg.get("attachments", []):
                query = att.get("query")
                if query:
                    result["sql"] = query.get("query") or query.get("sql")
                    result["text_response"] = query.get("description")
                    att_id = att.get("id")
                    if status == "COMPLETED" and att_id:
                        qr_resp = requests.get(
                            f"{base}/conversations/{conversation_id}/messages/{msg_id}/query-result/{att_id}",
                            headers=headers,
                        )
                        if qr_resp.status_code < 400:
                            qr = qr_resp.json()
                            stmt = qr.get("statement_response", {})
                            cols = [c.get("name", "") for c in stmt.get("manifest", {}).get("schema", {}).get("columns", [])]
                            data_rows = stmt.get("result", {}).get("data_array", [])
                            if cols and data_rows:
                                result["columns"] = cols
                                result["data"] = data_rows
                text_att = att.get("text")
                if text_att:
                    if isinstance(text_att, dict):
                        result["text_response"] = text_att.get("content", "")
                    elif isinstance(text_att, str):
                        result["text_response"] = text_att

            if result["sql"] and not result["data"]:
                cols, rows = execute_sql_with_columns(result["sql"])
                if cols and rows:
                    result["columns"] = cols
                    result["data"] = rows

            if not result["text_response"]:
                content = msg.get("content", "")
                if content and content != question:
                    result["text_response"] = content

            return result
        time.sleep(2)
    return {"status": "TIMEOUT", "error": "Timed out", "conversation_id": conversation_id}


def call_llm(messages: list, max_tokens: int = 1024, temperature: float = 0.7) -> str:
    host, headers = get_auth()
    resp = requests.post(
        f"{host}/serving-endpoints/{LLM_ENDPOINT}/invocations",
        headers=headers,
        json={"messages": messages, "max_tokens": max_tokens, "temperature": temperature},
    )
    if resp.status_code >= 400:
        return f"Error: {resp.text[:200]}"
    return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")


# --- User info ---
user_email = ""
try:
    user_email = st.context.headers.get("X-Forwarded-Email", "")
except Exception:
    pass
user_display = user_email or "Ops Manager"

# --- Top Navigation ---
genie_url = f"https://fevm-serverless-stable-3n0ihb.cloud.databricks.com/genie/rooms/{GENIE_SPACE_ID}" if GENIE_SPACE_ID else "#"
st.markdown(f"""
<div class="top-nav">
    <div class="nav-top-row">
        <div class="nav-brand">
            <span style="font-size:24px;">✈️</span>
            <div>
                <div class="nav-brand-title">Control Tower</div>
                <div class="nav-brand-subtitle">MSC Air Cargo · Operations & Revenue</div>
            </div>
            <span class="nav-badge">Synthetic data — demo only</span>
        </div>
        <div class="nav-right">
            <a href="{genie_url}" target="_blank" class="nav-link">Genie space ↗</a>
            <span class="nav-user">{user_display}</span>
        </div>
    </div>
</div>
<div class="main-content"></div>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 90px'></div>", unsafe_allow_html=True)

# --- Page Navigation ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

params = st.query_params
if params.get("page"):
    st.session_state.current_page = params["page"]
    st.query_params.clear()

nav_pages = ["Home", "Flight Ops", "Shipments", "Ask Genie", "Priority"]
nav_icons = ["🏠", "🛫", "📦", "💬", "🚨"]
nav_cols = st.columns(len(nav_pages))
for i, (page_name, icon) in enumerate(zip(nav_pages, nav_icons)):
    with nav_cols[i]:
        is_active = st.session_state.current_page == page_name
        if st.button(
            f"{icon} {page_name}",
            key=f"nav_{page_name}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.current_page = page_name
            st.rerun()

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
current_page = st.session_state.current_page


# ============================================================
# PAGE: HOME
# ============================================================
if current_page == "Home":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-category">AIR CARGO · CONTROL TOWER</div>
        <div class="hero-title">Operations & Revenue Command Center</div>
        <div class="hero-subtitle">
            Prioritize high-value cargo and VIP customers during operational disruptions.
            Monitor flight delays, revenue at risk, and protected schedule compliance in real time.
        </div>
        <div class="hero-date">Synthetic demo data · 50 flights · 30 customers · 150+ shipments</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-title">Operations Overview</div>
    <div class="section-subtitle">Live KPIs from the data warehouse</div>
    """, unsafe_allow_html=True)

    # KPI Row
    kpi_defs = [
        ("Active Flights", f"SELECT COUNT(*) FROM {CATALOG}.{SCHEMA}.msc_flights WHERE Flight_Status IN ('In-Air','Delayed','On-Time')", "blue"),
        ("On-Time Rate", f"SELECT ROUND(100.0 * SUM(CASE WHEN Flight_Status='On-Time' THEN 1 ELSE 0 END) / COUNT(*), 1) FROM {CATALOG}.{SCHEMA}.msc_flights", "green"),
        ("Revenue at Risk", f"SELECT ROUND(SUM(s.Revenue_Generated_USD), 0) FROM {CATALOG}.{SCHEMA}.msc_shipments s JOIN {CATALOG}.{SCHEMA}.msc_flights f ON s.Flight_ID=f.Flight_ID WHERE f.Flight_Status='Delayed' AND s.Critical_Revenue_Flag=true", "red"),
        ("VIP Alerts", f"SELECT COUNT(DISTINCT s.Customer_ID) FROM {CATALOG}.{SCHEMA}.msc_shipments s JOIN {CATALOG}.{SCHEMA}.msc_flights f ON s.Flight_ID=f.Flight_ID JOIN {CATALOG}.{SCHEMA}.msc_customers c ON s.Customer_ID=c.Customer_ID WHERE f.Flight_Status='Delayed' AND c.Customer_Tier='Platinum/VIP'", "amber"),
        ("Protected Flights", f"SELECT COUNT(*) FROM {CATALOG}.{SCHEMA}.msc_flights WHERE Schedule_Protection_Flag=true", "blue"),
    ]

    kpi_cols = st.columns(5)
    for i, (name, sql, color) in enumerate(kpi_defs):
        with kpi_cols[i]:
            data = execute_sql(sql)
            value = data[0][0] if data and data[0] and data[0][0] else "0"

            if name == "On-Time Rate":
                fmt_value = f"{float(value):.1f}%"
            elif name == "Revenue at Risk":
                v = float(value)
                fmt_value = f"${v/1_000_000:.1f}M" if v >= 1_000_000 else f"${v/1_000:.0f}K"
            else:
                fmt_value = str(int(float(value)))

            st.markdown(f"""
            <div class="kpi-card {color}">
                <div class="kpi-label">{name}</div>
                <div class="kpi-value">{fmt_value}</div>
                <div class="kpi-desc">Current period</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Alerts Section
    st.markdown("""
    <div class="section-title">Priority Alerts</div>
    <div class="section-subtitle">Situations requiring immediate attention</div>
    """, unsafe_allow_html=True)

    # VIP Crisis Alert
    crisis_sql = f"""
        SELECT f.Flight_ID, f.Origin, f.Destination, f.Delay_Minutes,
               c.Company_Name, c.Customer_Tier, s.Revenue_Generated_USD, s.Commodity_Type
        FROM {CATALOG}.{SCHEMA}.msc_shipments s
        JOIN {CATALOG}.{SCHEMA}.msc_flights f ON s.Flight_ID=f.Flight_ID
        JOIN {CATALOG}.{SCHEMA}.msc_customers c ON s.Customer_ID=c.Customer_ID
        WHERE f.Flight_Status='Delayed' AND c.Customer_Tier='Platinum/VIP' AND s.Critical_Revenue_Flag=true
        ORDER BY (s.Revenue_Generated_USD * (11 - c.Account_Sentiment_Score) * f.Delay_Minutes) DESC LIMIT 3
    """
    crisis_rows = execute_sql(crisis_sql)
    for idx, row in enumerate(crisis_rows):
        flight_id, origin, dest, delay, company, tier, revenue, commodity = row
        rev_fmt = f"${float(revenue):,.0f}" if revenue else "$0"
        st.markdown(f"""
        <div class="alert-card">
            <div class="alert-title">VIP CRISIS — {company} ({tier})</div>
            <div class="alert-desc">
                Flight {flight_id} ({origin} → {dest}) delayed +{delay}min.
                {commodity} shipment worth {rev_fmt} at risk.
            </div>
            <div class="alert-meta">Action: Escalate to ops manager · Notify customer account team</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View details →", key=f"crisis_nav_{idx}", type="secondary"):
            st.session_state.current_page = "Priority"
            st.rerun()

    # Protected flight alerts
    protected_sql = f"""
        SELECT f.Flight_ID, f.Origin, f.Destination, f.Delay_Minutes, f.Flight_Status
        FROM {CATALOG}.{SCHEMA}.msc_flights f
        WHERE f.Schedule_Protection_Flag=true AND f.Delay_Minutes > 0
        ORDER BY f.Delay_Minutes DESC LIMIT 2
    """
    protected_rows = execute_sql(protected_sql)
    for idx, row in enumerate(protected_rows):
        flight_id, origin, dest, delay, status = row
        st.markdown(f"""
        <div class="alert-card warning">
            <div class="alert-title">PROTECTED SCHEDULE — Flight {flight_id}</div>
            <div class="alert-desc">
                {origin} → {dest} · Status: {status} · Delay: +{delay}min.
                This flight has schedule protection — SLA breach imminent.
            </div>
            <div class="alert-meta">Action: Coordinate with ground handling · Check connection cargo</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View details →", key=f"protected_nav_{idx}", type="secondary"):
            st.session_state.current_page = "Priority"
            st.rerun()

    if not crisis_rows and not protected_rows:
        st.info("No critical alerts at this time.")

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Flight Status Summary
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="section-title" style="font-size:18px">Flight Status Breakdown</div>', unsafe_allow_html=True)
        status_sql = f"""
            SELECT Flight_Status, COUNT(*) as cnt
            FROM {CATALOG}.{SCHEMA}.msc_flights
            GROUP BY Flight_Status ORDER BY cnt DESC
        """
        status_rows = execute_sql(status_sql)
        for row in status_rows:
            status_name, cnt = row[0], row[1]
            tag_color = {"On-Time": "green", "Delayed": "red", "In-Air": "blue", "Delivered": "gray"}.get(status_name, "gray")
            st.markdown(f"""
            <div class="activity-item">
                <div>
                    <div class="activity-item-title">{status_name}</div>
                    <span class="activity-tag {tag_color}">{status_name}</span>
                </div>
                <div class="activity-item-stat">
                    <div class="activity-item-stat-value">{cnt}</div>
                    <div class="activity-item-stat-label">flights</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="section-title" style="font-size:18px">Top Revenue Customers</div>', unsafe_allow_html=True)
        rev_sql = f"""
            SELECT c.Company_Name, c.Customer_Tier, ROUND(SUM(s.Revenue_Generated_USD), 0) as total_rev
            FROM {CATALOG}.{SCHEMA}.msc_shipments s
            JOIN {CATALOG}.{SCHEMA}.msc_customers c ON s.Customer_ID=c.Customer_ID
            GROUP BY c.Company_Name, c.Customer_Tier
            ORDER BY total_rev DESC LIMIT 5
        """
        rev_rows = execute_sql(rev_sql)
        for row in rev_rows:
            company, tier, total = row
            total_fmt = f"${float(total)/1000:.0f}K" if float(total) < 1_000_000 else f"${float(total)/1_000_000:.1f}M"
            tag_color = "amber" if tier == "Platinum/VIP" else "blue" if tier == "Gold" else "gray"
            st.markdown(f"""
            <div class="activity-item">
                <div>
                    <div class="activity-item-title">{company}</div>
                    <span class="activity-tag {tag_color}">{tier}</span>
                </div>
                <div class="activity-item-stat">
                    <div class="activity-item-stat-value">{total_fmt}</div>
                    <div class="activity-item-stat-label">revenue</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div class="footer">
        MSC Air Cargo Control Tower · Data on Databricks · Internal demo only
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# PAGE: FLIGHT OPERATIONS
# ============================================================
elif current_page == "Flight Ops":
    st.markdown("""
    <div class="section-title">Flight Operations</div>
    <div class="section-subtitle">All flights with status, delays, and monitoring flags</div>
    """, unsafe_allow_html=True)

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "On-Time", "Delayed", "In-Air", "Delivered"])
    with col2:
        protection_filter = st.selectbox("Protection", ["All", "Protected Only", "Unprotected Only"])
    with col3:
        sentiment_filter = st.selectbox("Monitoring", ["All", "Sentiment Watch Only"])

    where_clauses = []
    if status_filter != "All":
        where_clauses.append(f"Flight_Status='{status_filter}'")
    if protection_filter == "Protected Only":
        where_clauses.append("Schedule_Protection_Flag=true")
    elif protection_filter == "Unprotected Only":
        where_clauses.append("Schedule_Protection_Flag=false")
    if sentiment_filter == "Sentiment Watch Only":
        where_clauses.append("Sentiment_Analysis_Flag=true")

    where = " AND ".join(where_clauses) if where_clauses else "1=1"

    flights_sql = f"""
        SELECT Flight_ID, Origin, Destination, Origin_City, Destination_City,
               Scheduled_Departure, ETA, Flight_Status, Delay_Minutes,
               Schedule_Protection_Flag, Sentiment_Analysis_Flag, Aircraft_Type, Capacity_Tons
        FROM {CATALOG}.{SCHEMA}.msc_flights
        WHERE {where}
        ORDER BY Delay_Minutes DESC, Flight_ID
    """
    cols, data = execute_sql_with_columns(flights_sql)
    if cols and data:
        df = pd.DataFrame(data, columns=cols)
        for col in ["Delay_Minutes", "Capacity_Tons"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # --- Map Visualizations (shown first) ---
        import pydeck as pdk

        CITY_COORDS = {
            "Chicago": (41.978, -87.904), "Doha": (25.261, 51.565),
            "Dubai": (25.253, 55.366), "Frankfurt": (50.033, 8.571),
            "Hong Kong": (22.309, 113.915), "London": (51.470, -0.454),
            "Milan": (45.630, 8.723), "New York": (40.640, -73.779),
            "Seoul": (37.460, 126.440), "Shanghai": (31.143, 121.805),
            "Singapore": (1.350, 103.994), "Tokyo": (35.764, 140.386),
        }

        STATUS_COLORS = {
            "Delayed": [255, 80, 80],
            "In-Air": [80, 180, 255],
            "On-Time": [80, 220, 120],
            "Delivered": [160, 160, 160],
        }

        map_df = df.copy()
        map_df["origin_lat"] = map_df["Origin_City"].map(lambda c: CITY_COORDS.get(c, (0, 0))[0])
        map_df["origin_lon"] = map_df["Origin_City"].map(lambda c: CITY_COORDS.get(c, (0, 0))[1])
        map_df["dest_lat"] = map_df["Destination_City"].map(lambda c: CITY_COORDS.get(c, (0, 0))[0])
        map_df["dest_lon"] = map_df["Destination_City"].map(lambda c: CITY_COORDS.get(c, (0, 0))[1])
        map_df["color"] = map_df["Flight_Status"].map(lambda s: STATUS_COLORS.get(s, [200, 200, 200]))

        valid_map = map_df[(map_df["origin_lat"] != 0) & (map_df["dest_lat"] != 0)]

        if not valid_map.empty:
            st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
            st.markdown("#### ✈️ Flight Route Map")
            st.caption("Hover on routes for details — 🔴 Delayed · 🔵 In-Air · 🟢 On-Time · ⚪ Delivered")

            valid_map["tooltip_text"] = valid_map.apply(
                lambda r: f"{r['Flight_ID']}: {r['Origin_City']} → {r['Destination_City']} ({r['Flight_Status']})", axis=1)

            arc_layer = pdk.Layer(
                "ArcLayer",
                data=valid_map,
                get_source_position=["origin_lon", "origin_lat"],
                get_target_position=["dest_lon", "dest_lat"],
                get_source_color="color",
                get_target_color="color",
                get_width=2,
                get_height=0.3,
                pickable=True,
                auto_highlight=True,
            )

            scatter_data = []
            for _, row in valid_map.iterrows():
                scatter_data.append({"lat": row["origin_lat"], "lon": row["origin_lon"],
                                     "city": row["Origin_City"], "color": row["color"]})
                scatter_data.append({"lat": row["dest_lat"], "lon": row["dest_lon"],
                                     "city": row["Destination_City"], "color": row["color"]})
            scatter_df = pd.DataFrame(scatter_data).drop_duplicates(subset=["city"])

            scatter_layer = pdk.Layer(
                "ScatterplotLayer",
                data=scatter_df,
                get_position=["lon", "lat"],
                get_fill_color=[30, 144, 255, 200],
                get_radius=60000,
                pickable=True,
            )

            st.pydeck_chart(pdk.Deck(
                layers=[arc_layer, scatter_layer],
                initial_view_state=pdk.ViewState(latitude=30, longitude=30, zoom=1.3, pitch=30),
                map_style="mapbox://styles/mapbox/dark-v11",
                tooltip={"text": "{tooltip_text}"},
            ), use_container_width=True)

            # --- Delay Heatmap ---
            st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
            st.markdown("#### 🌡️ Delay & Service Degradation Heatmap")
            st.caption("Intensity weighted by delay minutes — hotspots indicate operational stress regions")

            heat_points = []
            for _, row in valid_map.iterrows():
                weight = max(float(row["Delay_Minutes"]), 10) if row["Flight_Status"] == "Delayed" else 0
                if weight > 0:
                    heat_points.append({"lat": row["origin_lat"], "lon": row["origin_lon"], "weight": weight})
                    heat_points.append({"lat": row["dest_lat"], "lon": row["dest_lon"], "weight": weight})

            if heat_points:
                heat_df = pd.DataFrame(heat_points)
                heat_df = heat_df.groupby(["lat", "lon"], as_index=False)["weight"].sum()

                heatmap_layer = pdk.Layer(
                    "HeatmapLayer",
                    data=heat_df,
                    get_position=["lon", "lat"],
                    get_weight="weight",
                    radius_pixels=80,
                    intensity=1,
                    threshold=0.1,
                    color_range=[
                        [255, 255, 178], [254, 204, 92], [253, 141, 60],
                        [240, 59, 32], [189, 0, 38],
                    ],
                )

                # Hover points grouped by hub — shows KPI + flight list
                delayed = valid_map[valid_map["Flight_Status"] == "Delayed"]
                hub_flights = {}
                for _, row in delayed.iterrows():
                    for lat, lon, city in [(row["origin_lat"], row["origin_lon"], row["Origin_City"]),
                                           (row["dest_lat"], row["dest_lon"], row["Destination_City"])]:
                        hub_flights.setdefault((lat, lon, city), []).append(
                            (row["Flight_ID"], row["Origin_City"], row["Destination_City"], int(row["Delay_Minutes"])))

                hover_data = []
                for (lat, lon, city), flights in hub_flights.items():
                    count = len(flights)
                    avg_delay = int(sum(f[3] for f in flights) / count)
                    lines = [f"{city} — {count} delayed · Avg +{avg_delay}min"]
                    for fid, orig, dest, delay in flights[:5]:
                        lines.append(f"  {fid}: {orig}→{dest} +{delay}min")
                    hover_data.append({"lat": lat, "lon": lon, "tooltip_text": "\n".join(lines)})
                hover_df = pd.DataFrame(hover_data)

                hover_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=hover_df,
                    get_position=["lon", "lat"],
                    get_fill_color=[255, 255, 255, 0],
                    get_radius=120000,
                    pickable=True,
                )

                st.pydeck_chart(pdk.Deck(
                    layers=[heatmap_layer, hover_layer],
                    initial_view_state=pdk.ViewState(latitude=30, longitude=30, zoom=1.1, pitch=0),
                    map_style="mapbox://styles/mapbox/dark-v11",
                    tooltip={"text": "{tooltip_text}"},
                ), use_container_width=True)

                with st.expander("📊 View delay details by hub"):
                    delay_details = valid_map[valid_map["Flight_Status"] == "Delayed"][
                        ["Flight_ID", "Origin_City", "Destination_City", "Delay_Minutes"]
                    ].sort_values("Delay_Minutes", ascending=False).reset_index(drop=True)
                    st.dataframe(delay_details, use_container_width=True, hide_index=True)
            else:
                st.info("No delays in current filter — heatmap not applicable.")

        # --- Data Table ---
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown("#### 📋 Flight Details")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Summary stats
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        stat_cols = st.columns(4)
        with stat_cols[0]:
            st.metric("Total Shown", len(df))
        with stat_cols[1]:
            delayed_count = len(df[df["Flight_Status"] == "Delayed"])
            st.metric("Delayed", delayed_count)
        with stat_cols[2]:
            avg_delay = df[df["Delay_Minutes"] > 0]["Delay_Minutes"].mean()
            st.metric("Avg Delay (min)", f"{avg_delay:.0f}" if pd.notna(avg_delay) else "0")
        with stat_cols[3]:
            protected_count = len(df[df["Schedule_Protection_Flag"] == "true"])
            st.metric("Protected", protected_count)

        # --- LLM Operations Advisor ---
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown("#### 🤖 Operations Advisor — AI Recommendations")

        delayed_flights = df[df["Flight_Status"] == "Delayed"]
        if not delayed_flights.empty:
            shipments_sql = f"""
                SELECT s.AWB_Number, s.Flight_ID, s.Commodity_Type, s.Revenue_Generated_USD,
                       s.Priority_Level, c.Company_Name, c.Customer_Tier, c.Account_Sentiment_Score
                FROM {CATALOG}.{SCHEMA}.msc_shipments s
                JOIN {CATALOG}.{SCHEMA}.msc_customers c ON s.Customer_ID = c.Customer_ID
                WHERE s.Flight_ID IN ({','.join(f"'{fid}'" for fid in delayed_flights['Flight_ID'].tolist())})
                ORDER BY s.Revenue_Generated_USD DESC
            """
            ship_cols, ship_data = execute_sql_with_columns(shipments_sql)
            ship_df = pd.DataFrame(ship_data, columns=ship_cols) if ship_cols and ship_data else pd.DataFrame()

            if st.button("🛡️ Generate Operations Advisory", use_container_width=True):
                flight_summary = "\n".join(
                    f"- {row['Flight_ID']} ({row['Origin']}→{row['Destination']}): {row['Origin_City']} to {row['Destination_City']}, "
                    f"Delay: {row['Delay_Minutes']}min, Status: {row['Flight_Status']}, "
                    f"Protected: {row['Schedule_Protection_Flag']}, Sentiment Watch: {row['Sentiment_Analysis_Flag']}"
                    for _, row in delayed_flights.iterrows()
                )
                shipment_summary = ""
                if not ship_df.empty:
                    shipment_summary = "\n".join(
                        f"- AWB {row['AWB_Number']} on flight {row['Flight_ID']}: {row['Commodity_Type']}, "
                        f"${float(row['Revenue_Generated_USD']):,.0f}, {row['Priority_Level']} priority, "
                        f"Customer: {row['Company_Name']} ({row['Customer_Tier']}, sentiment {row['Account_Sentiment_Score']}/10)"
                        for _, row in ship_df.iterrows()
                    )

                prompt = f"""You are an MSC Air Cargo operations advisor. Analyze the following delayed flights and their shipments, then provide actionable recommendations.

DELAYED FLIGHTS:
{flight_summary}

AFFECTED SHIPMENTS:
{shipment_summary if shipment_summary else "No shipment data available."}

CRITICAL DATA ACCURACY RULES:
- ONLY reference flight IDs, AWB numbers, customer names, revenue amounts, routes, and commodity types that appear EXACTLY in the data above.
- Do NOT invent, abbreviate, or modify any flight ID or AWB number. Copy them character-for-character.
- When referencing a flight, always include its full route (e.g. MSC-812 (LHR→JFK)) and delay duration.
- When referencing a shipment, always include its full AWB number and exact revenue amount.

Provide a structured operations advisory using EXACTLY these 5 section headers (one line each, no numbering):
## IMMEDIATE ACTIONS
## RE-ROUTING OPTIONS
## CUSTOMER ESCALATION
## SCHEDULE PROTECTION
## PRIORITY RE-RANKING

For each section use bullet points. Be concise and actionable. Frame recommendations as an ops manager would act on them."""

                with st.spinner("Analyzing flight disruptions and generating advisory..."):
                    response = call_llm([{"role": "user", "content": prompt}], max_tokens=2048, temperature=0.3)

                # Parse response into sections and render as cards
                section_pattern = re.compile(r'^##\s+(.+)$', re.MULTILINE)
                section_colors = {
                    "IMMEDIATE ACTIONS": "urgent",
                    "RE-ROUTING OPTIONS": "warning",
                    "CUSTOMER ESCALATION": "info",
                    "SCHEDULE PROTECTION": "success",
                    "PRIORITY RE-RANKING": "info",
                }
                sections = section_pattern.split(response)
                # sections[0] is preamble text (before first ##), then alternating title/body
                preamble = sections[0].strip() if sections[0].strip() else None
                total_delayed = len(delayed_flights)
                total_revenue = ship_df['Revenue_Generated_USD'].astype(float).sum() if not ship_df.empty else 0

                st.markdown(f"""
                <div class="advisory-header">MSC Air Cargo Operations Advisory</div>
                <div class="advisory-subtitle">{total_delayed} delayed flight{'s' if total_delayed != 1 else ''} affecting ${total_revenue:,.0f} in cargo</div>
                """, unsafe_allow_html=True)

                if preamble:
                    st.markdown(f"""<div class="advisory-section">
                        <div class="advisory-section-body">{preamble}</div>
                    </div>""", unsafe_allow_html=True)

                for i in range(1, len(sections), 2):
                    title = sections[i].strip()
                    body = sections[i + 1].strip() if i + 1 < len(sections) else ""
                    color_class = section_colors.get(title, "info")
                    # Convert markdown bullets to HTML list items
                    lines = body.split("\n")
                    has_bullets = any(line.strip().startswith(("- ", "* ")) for line in lines)
                    if has_bullets:
                        items = []
                        current_item = ""
                        for line in lines:
                            stripped = line.strip()
                            if stripped.startswith(("- ", "* ")):
                                if current_item:
                                    items.append(current_item)
                                current_item = stripped[2:]
                            elif stripped and current_item:
                                current_item += " " + stripped
                            elif stripped:
                                items.append(stripped)
                        if current_item:
                            items.append(current_item)
                        body_html = "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"
                    else:
                        body_html = body.replace("\n", "<br>")
                    body_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', body_html)
                    st.markdown(f"""<div class="advisory-section {color_class}">
                        <div class="advisory-section-title">{title}</div>
                        <div class="advisory-section-body">{body_html}</div>
                    </div>""", unsafe_allow_html=True)
        else:
            st.success("No delayed flights in current view — no advisory needed.")

    else:
        st.info("No flights match the current filters or data unavailable.")


# ============================================================
# PAGE: SHIPMENT TRACKING
# ============================================================
elif current_page == "Shipments":
    st.markdown("""
    <div class="section-title">Shipment Tracking</div>
    <div class="section-subtitle">Air Waybills with customer, revenue, and tracking status</div>
    """, unsafe_allow_html=True)

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        commodity_filter = st.selectbox("Commodity", ["All", "Doc Charter / High-Yield", "Pharma", "Perishables", "General Cargo", "Dangerous Goods", "Live Animals"])
    with col2:
        priority_filter = st.selectbox("Priority", ["All", "Critical", "Priority", "Standard"])
    with col3:
        critical_filter = st.selectbox("Revenue Flag", ["All", "Critical Revenue Only"])

    where_clauses = []
    if commodity_filter != "All":
        where_clauses.append(f"s.Commodity_Type='{commodity_filter}'")
    if priority_filter != "All":
        where_clauses.append(f"s.Priority_Level='{priority_filter}'")
    if critical_filter == "Critical Revenue Only":
        where_clauses.append("s.Critical_Revenue_Flag=true")

    where = " AND ".join(where_clauses) if where_clauses else "1=1"

    shipments_sql = f"""
        SELECT s.AWB_Number, s.Flight_ID, c.Company_Name, c.Customer_Tier,
               s.Commodity_Type, s.Revenue_Generated_USD, s.Weight_KG,
               s.Tracking_Status, s.Priority_Level, s.Origin_City, s.Destination_City,
               f.Flight_Status, f.Delay_Minutes
        FROM {CATALOG}.{SCHEMA}.msc_shipments s
        JOIN {CATALOG}.{SCHEMA}.msc_customers c ON s.Customer_ID=c.Customer_ID
        JOIN {CATALOG}.{SCHEMA}.msc_flights f ON s.Flight_ID=f.Flight_ID
        WHERE {where}
        ORDER BY s.Revenue_Generated_USD DESC
    """
    cols, data = execute_sql_with_columns(shipments_sql)
    if cols and data:
        df = pd.DataFrame(data, columns=cols)
        for col in ["Revenue_Generated_USD", "Weight_KG", "Delay_Minutes"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        st.dataframe(df, use_container_width=True, hide_index=True)

        # Revenue summary
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        stat_cols = st.columns(4)
        with stat_cols[0]:
            total_rev = df["Revenue_Generated_USD"].sum()
            st.metric("Total Revenue", f"${total_rev/1_000_000:.1f}M" if total_rev >= 1_000_000 else f"${total_rev/1_000:.0f}K")
        with stat_cols[1]:
            at_risk = df[df["Flight_Status"] == "Delayed"]["Revenue_Generated_USD"].sum()
            st.metric("Revenue at Risk", f"${at_risk/1_000_000:.1f}M" if at_risk >= 1_000_000 else f"${at_risk/1_000:.0f}K")
        with stat_cols[2]:
            st.metric("Shipments", len(df))
        with stat_cols[3]:
            critical_count = len(df[df["Priority_Level"] == "Critical"])
            st.metric("Critical Priority", critical_count)

        # Breakdown by commodity
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown("**Revenue by Commodity Type**")
        rev_by_commodity = df.groupby("Commodity_Type")["Revenue_Generated_USD"].sum().sort_values(ascending=False)
        st.bar_chart(rev_by_commodity)
    else:
        st.info("No shipments match the current filters or data unavailable.")


# ============================================================
# PAGE: ASK GENIE
# ============================================================
elif current_page == "Ask Genie":
    st.markdown("""
    <div class="section-title">Ask Genie</div>
    <div class="section-subtitle">Natural language queries on MSC Air Cargo operations data</div>
    """, unsafe_allow_html=True)

    if not GENIE_SPACE_ID:
        st.warning("Genie Space ID not configured. Set the GENIE_SPACE_ID environment variable.")

    if "genie_messages" not in st.session_state:
        st.session_state.genie_messages = []
    if "genie_conv_id" not in st.session_state:
        st.session_state.genie_conv_id = None

    def display_genie_result(result: dict):
        text = result.get("text_response")
        error = result.get("error")
        has_data = result.get("data") and result.get("columns")

        if text:
            st.markdown(text)
        elif error:
            st.error(error)
        elif not has_data:
            st.warning("No response")

        if result.get("data") and result.get("columns"):
            df = pd.DataFrame(result["data"], columns=result["columns"])
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass
            st.dataframe(df, use_container_width=True, hide_index=True)

            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            non_numeric_cols = [c for c in df.columns if c not in numeric_cols]
            if numeric_cols and non_numeric_cols and len(df) > 1:
                label_col = non_numeric_cols[0]
                chart_df = df.set_index(label_col)[numeric_cols]
                if len(df) <= 20:
                    st.bar_chart(chart_df)
                else:
                    st.line_chart(chart_df)

        if result.get("sql"):
            with st.expander("View SQL Query"):
                st.code(result["sql"], language="sql")

    for msg in st.session_state.genie_messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.write(msg["content"])
            else:
                display_genie_result(msg)

    if not st.session_state.genie_messages:
        st.markdown("""**Try asking:**
<style>
div[data-testid="stHorizontalBlock"]:last-of-type div[data-testid="column"] .stButton > button {
    height: 80px !important;
    white-space: normal !important;
    word-wrap: break-word !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    padding: 12px 16px !important;
    font-size: 14px !important;
}
</style>
""", unsafe_allow_html=True)
        suggestions = [
            "Which VIP customers have cargo on delayed flights?",
            "What is the total revenue at risk?",
            "Show all protected flights and their status",
        ]
        suggestion_cols = st.columns(len(suggestions))
        for i, s in enumerate(suggestions):
            if suggestion_cols[i].button(s, key=f"sug_{i}", use_container_width=True):
                st.session_state.genie_pending = s
                st.rerun()

    if "genie_pending" in st.session_state:
        prompt = st.session_state.pop("genie_pending")
        st.session_state.genie_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Querying Genie..."):
                result = ask_genie(prompt, st.session_state.genie_conv_id)
                st.session_state.genie_conv_id = result.get("conversation_id")
                display_genie_result(result)
                st.session_state.genie_messages.append({
                    "role": "assistant",
                    "content": result.get("text_response") or result.get("error") or "No response",
                    "text_response": result.get("text_response"),
                    "sql": result.get("sql"),
                    "columns": result.get("columns"),
                    "data": result.get("data"),
                    "error": result.get("error"),
                })

    if prompt := st.chat_input("Ask about flights, shipments, customers..."):
        st.session_state.genie_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Querying Genie..."):
                result = ask_genie(prompt, st.session_state.genie_conv_id)
                st.session_state.genie_conv_id = result.get("conversation_id")
                display_genie_result(result)
                st.session_state.genie_messages.append({
                    "role": "assistant",
                    "content": result.get("text_response") or result.get("error") or "No response",
                    "text_response": result.get("text_response"),
                    "sql": result.get("sql"),
                    "columns": result.get("columns"),
                    "data": result.get("data"),
                    "error": result.get("error"),
                })

    if st.session_state.genie_conv_id:
        if st.button("New Conversation"):
            st.session_state.genie_messages = []
            st.session_state.genie_conv_id = None
            st.rerun()


# ============================================================
# PAGE: PRIORITY DASHBOARD
# ============================================================
elif current_page == "Priority":
    st.markdown("""
    <div class="section-title">Priority Dashboard</div>
    <div class="section-subtitle">Critical scenarios requiring ops intervention</div>
    """, unsafe_allow_html=True)

    # --- Scenario 1: VIP Crisis ---
    st.markdown("#### VIP Crisis Scenarios")
    vip_sql = f"""
        SELECT f.Flight_ID, f.Origin, f.Destination, f.Delay_Minutes, f.Flight_Status,
               c.Company_Name, c.Customer_Tier, c.Account_Sentiment_Score,
               s.AWB_Number, s.Commodity_Type, s.Revenue_Generated_USD
        FROM {CATALOG}.{SCHEMA}.msc_shipments s
        JOIN {CATALOG}.{SCHEMA}.msc_flights f ON s.Flight_ID=f.Flight_ID
        JOIN {CATALOG}.{SCHEMA}.msc_customers c ON s.Customer_ID=c.Customer_ID
        WHERE f.Flight_Status='Delayed' AND c.Customer_Tier='Platinum/VIP' AND s.Critical_Revenue_Flag=true
        ORDER BY (s.Revenue_Generated_USD * (11 - c.Account_Sentiment_Score) * f.Delay_Minutes) DESC LIMIT 5
    """
    vip_rows = execute_sql(vip_sql)
    if vip_rows:
        for row in vip_rows:
            flight_id, origin, dest, delay, status, company, tier, sentiment, awb, commodity, revenue = row
            rev_fmt = f"${float(revenue):,.0f}" if revenue else "$0"
            st.markdown(f"""
            <div class="priority-card">
                <div class="priority-card-title">Flight {flight_id}: {origin} → {dest}</div>
                <div class="priority-card-value red">{rev_fmt} at risk</div>
                <div class="priority-card-desc">
                    <strong>Customer:</strong> {company} ({tier}) · Sentiment: {sentiment}/10<br>
                    <strong>Shipment:</strong> AWB {awb} · {commodity}<br>
                    <strong>Delay:</strong> +{delay} minutes · Status: {status}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # AI recommended actions for the top crisis
        top = vip_rows[0]
        top_flight_id, top_origin, top_dest, top_delay, top_status, top_company, top_tier, top_sentiment, top_awb, top_commodity, top_revenue = top
        top_rev_fmt = f"${float(top_revenue):,.0f}" if top_revenue else "$0"

        if st.button("🚨 Get AI Recommended Actions for Top Crisis", type="primary", use_container_width=True):
            crisis_prompt = f"""You are an MSC Air Cargo crisis response specialist. Provide immediate, specific recommended actions for this VIP crisis:

CRISIS DETAILS:
- Flight: {top_flight_id} ({top_origin} → {top_dest}), delayed +{top_delay} minutes
- Customer: {top_company} ({top_tier}), sentiment score: {top_sentiment}/10
- Shipment: AWB {top_awb}, commodity: {top_commodity}, value: {top_rev_fmt}

CRITICAL DATA ACCURACY RULES:
- ONLY reference the flight ID, AWB number, customer name, route, and revenue amount EXACTLY as provided above. Do NOT invent or modify any identifier.
- Always include the full flight route when referencing the flight.
- Always include the full AWB number when referencing the shipment.

Provide exactly 5 actions the ops team should take RIGHT NOW, in priority order.
Format each action as a single line starting with a bold title followed by a colon and the action details:
**Title (Timeframe):** Action details here.

Each action should be specific (name the flight, customer, or hub), actionable (who does what), and time-bound. Keep each to 1-2 sentences max. Focus on protecting revenue and customer relationship."""

            with st.spinner("Generating crisis response plan..."):
                response = call_llm([{"role": "user", "content": crisis_prompt}], max_tokens=1024, temperature=0.2)

            st.markdown(f"""
            <div class="advisory-header">Crisis Response — {top_flight_id} ({top_origin}→{top_dest})</div>
            <div class="advisory-subtitle">{top_company} ({top_tier}) · AWB {top_awb} · {top_rev_fmt} at risk</div>
            """, unsafe_allow_html=True)

            lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
            action_num = 0
            for line in lines:
                cleaned = re.sub(r'^\d+[\.)\]]\s*', '', line)
                if not cleaned:
                    continue
                action_num += 1
                card_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', cleaned)
                color_class = "urgent" if action_num <= 2 else "warning" if action_num <= 4 else "info"
                st.markdown(f"""<div class="advisory-section {color_class}">
                    <div class="advisory-section-body">{card_html}</div>
                </div>""", unsafe_allow_html=True)
    else:
        st.success("No VIP crisis scenarios active.")

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # --- Scenario 2: Protected Schedule ---
    st.markdown("#### Protected Schedule Compliance")
    protected_sql = f"""
        SELECT f.Flight_ID, f.Origin, f.Destination, f.Scheduled_Arrival, f.ETA,
               f.Delay_Minutes, f.Flight_Status,
               COUNT(s.AWB_Number) as shipment_count,
               ROUND(SUM(s.Revenue_Generated_USD), 0) as total_revenue
        FROM {CATALOG}.{SCHEMA}.msc_flights f
        LEFT JOIN {CATALOG}.{SCHEMA}.msc_shipments s ON f.Flight_ID=s.Flight_ID
        WHERE f.Schedule_Protection_Flag=true
        GROUP BY f.Flight_ID, f.Origin, f.Destination, f.Scheduled_Arrival, f.ETA, f.Delay_Minutes, f.Flight_Status
        ORDER BY f.Delay_Minutes DESC
    """
    protected_rows = execute_sql(protected_sql)
    if protected_rows:
        for row in protected_rows:
            flight_id, origin, dest, sched_arr, eta, delay, status, ship_count, total_rev = row
            delay_int = int(float(delay)) if delay else 0
            total_rev_fmt = f"${float(total_rev):,.0f}" if total_rev else "$0"
            color = "red" if delay_int > 60 else "amber" if delay_int > 0 else "green"
            status_text = "ON TRACK" if delay_int == 0 else f"DELAYED +{delay_int}min"

            st.markdown(f"""
            <div class="priority-card">
                <div class="priority-card-title">Flight {flight_id}: {origin} → {dest} (PROTECTED)</div>
                <div class="priority-card-value {color}">{status_text}</div>
                <div class="priority-card-desc">
                    <strong>Scheduled Arrival:</strong> {sched_arr} · <strong>ETA:</strong> {eta}<br>
                    <strong>Cargo:</strong> {ship_count} shipments · {total_rev_fmt} total revenue<br>
                    <strong>Status:</strong> {status}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No protected flights in the system.")

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # --- Scenario 3: Sentiment Watch ---
    st.markdown("#### Sentiment Analysis Watch (5 Flights)")
    sentiment_sql = f"""
        SELECT f.Flight_ID, f.Origin, f.Destination, f.Flight_Status, f.Delay_Minutes,
               COUNT(s.AWB_Number) as shipments,
               ROUND(SUM(s.Revenue_Generated_USD), 0) as revenue
        FROM {CATALOG}.{SCHEMA}.msc_flights f
        LEFT JOIN {CATALOG}.{SCHEMA}.msc_shipments s ON f.Flight_ID=s.Flight_ID
        WHERE f.Sentiment_Analysis_Flag=true
        GROUP BY f.Flight_ID, f.Origin, f.Destination, f.Flight_Status, f.Delay_Minutes
        ORDER BY f.Delay_Minutes DESC
    """
    sentiment_rows = execute_sql(sentiment_sql)
    if sentiment_rows:
        for row in sentiment_rows:
            flight_id, origin, dest, status, delay, ships, rev = row
            delay_int = int(float(delay)) if delay else 0
            rev_fmt = f"${float(rev):,.0f}" if rev else "$0"
            tag_color = "red" if status == "Delayed" else "green" if status == "On-Time" else "blue"

            delay_badge = f"<span class='activity-tag red'>+{delay_int}min</span>" if delay_int > 0 else ""
            delay_stat = f'<div class="activity-item-stat"><div class="activity-item-stat-value">{delay_int}m</div><div class="activity-item-stat-label">delay</div></div>' if delay_int > 0 else ""
            st.markdown(f'<div class="activity-item"><div><div class="activity-item-title">{flight_id}: {origin} → {dest}</div><div class="activity-item-desc">{ships} shipments · {rev_fmt} revenue</div><span class="activity-tag {tag_color}">{status}</span>{delay_badge}</div>{delay_stat}</div>', unsafe_allow_html=True)
    else:
        st.info("No sentiment-watched flights found.")



# --- Footer with version ---
st.markdown(f"""
<div style="position:fixed; bottom:8px; right:16px; font-size:11px; color:#475569; z-index:1000;">
    v{APP_VERSION} · build {APP_BUILD}
</div>
""", unsafe_allow_html=True)
