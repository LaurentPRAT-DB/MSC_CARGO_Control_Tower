# MSC Air Cargo Control Tower — Demo Scenarios

## Overview

The Control Tower demo showcases how operational data (flight delays, ETAs) intersects with commercial data (customer tier, revenue) to enable **business-impact-driven prioritization** during disruptions.

**Key thesis:** Not all delays are equal. A 2-hour delay on a $520K Doc Charter for a Platinum/VIP customer demands immediate escalation, while the same delay on standard cargo may only require a status update.

### Data Summary

| Metric | Value |
|--------|-------|
| Total Flights | 50 |
| Delayed Flights | 10 (20%) |
| Total Shipments | 152 |
| Total Revenue | $23.3M |
| Revenue on Delayed Flights | $5.4M (23%) |
| VIP Customers | 6 (Platinum/VIP tier) |
| Protected Flights | 8 |
| Sentiment-Watched Flights | 5 |

---

## Scenario 1: VIP Crisis

> **The Story:** A major 6-hour delay on a London-Tokyo flight is putting $520K of premium Doc Charter cargo at risk for one of our highest-value accounts.

### Primary Alert

| Field | Value |
|-------|-------|
| **Flight** | MSC-807 |
| **Route** | LHR (London) → NRT (Tokyo) |
| **Delay** | +360 minutes (6 hours) |
| **Customer** | EliteForward GmbH |
| **Tier** | Platinum/VIP |
| **Sentiment Score** | 6/10 (at-risk) |
| **AWB** | 618-99000001 |
| **Commodity** | Doc Charter / High-Yield |
| **Revenue at Risk** | $520,000 |
| **Tracking Status** | Manifested |

### Why This Matters

- EliteForward GmbH is a Platinum/VIP account — one of our top 6 revenue generators
- Sentiment score is only 6/10 — this customer is already borderline dissatisfied
- Doc Charter is time-critical courier cargo (legal documents, contracts) — a 6-hour delay may breach the customer's downstream SLA
- $520K is a single shipment — total exposure for this customer across all delayed flights is higher

### Additional VIP Exposure on Delayed Flights

| Flight | Route | Delay | Customer | AWB | Commodity | Revenue |
|--------|-------|-------|----------|-----|-----------|---------|
| MSC-812 | LHR → JFK | +240min | NorthStar Logistics | 618-27584297 | Doc Charter | $1,176,754 |
| MSC-812 | LHR → JFK | +240min | ZenithCargo Solutions | 618-75876924 | Pharma | $371,907 |
| MSC-812 | LHR → JFK | +240min | MeridianFreight Corp | 618-49625201 | Pharma | $289,277 |
| MSC-824 | ORD → JFK | +120min | OceanAir Express | 618-68743530 | Dangerous Goods | $279,691 |
| MSC-808 | DOH → ORD | +360min | ZenithCargo Solutions | 618-44489940 | Live Animals | $218,611 |

### Demo Talking Points

1. **"The dashboard immediately surfaces this as Priority #1"** — not because the delay is the longest, but because revenue × customer tier × commodity type = highest business impact
2. **"Look at MSC-812"** — 4 VIP shipments on one flight totaling $1.9M+ at risk. One flight can cascade into a multi-customer crisis
3. **"Sentiment score of 6/10 tells us EliteForward is already unhappy"** — proactive outreach now prevents churn later

### Recommended Actions (for demo narrative)

1. Escalate to Account Director for EliteForward GmbH
2. Pre-emptive customer notification with revised ETA and recovery plan
3. Explore re-routing options for Doc Charter cargo (highest time-sensitivity)
4. Flag MSC-812 for ops manager attention (4 VIP shipments, $1.9M exposure)

---

## Scenario 2: Protected Schedule

> **The Story:** 8 flights carry "schedule protection" flags — contractual commitments where delays trigger SLA penalties. Two of them are currently at risk.

### Protected Fleet Status

| Flight | Route | Status | Delay | Shipments | Revenue |
|--------|-------|--------|-------|-----------|---------|
| **MSC-848** | **PVG → ORD** | **Delayed** | **+180min** | **5** | **$429K** |
| **MSC-847** | **ICN → FRA** | **In-Air** | **+45min** | **4** | **$403K** |
| MSC-817 | DXB → PVG | In-Air | +30min | 0 | $0 |
| MSC-849 | DOH → PVG | In-Air | +15min | 4 | $292K |
| MSC-815 | PVG → MXP | Delivered | 0 | 2 | $402K |
| MSC-831 | FRA → JFK | On-Time | 0 | 5 | $455K |
| MSC-833 | FRA → ORD | Delivered | 0 | 4 | $803K |
| MSC-840 | ICN → MXP | On-Time | 0 | 3 | $114K |

### Critical: MSC-848 (SLA Breach)

- **Route:** Shanghai (PVG) → Chicago (ORD)
- **Delay:** +180 minutes — likely breaches the SLA window
- **Revenue exposed:** $429K across 5 shipments
- **Includes VIP cargo:** EliteForward GmbH ($177K) + MeridianFreight Corp ($181K)

### Why Protected Flights Are Different

Protected flights have **contractual penalties** if ETA is missed:
- Financial penalties (typically 2-5% of cargo value per hour of SLA breach)
- Reputational damage with the shipper/forwarder
- Possible loss of future allocations from that customer

Unlike regular delays where the ops team balances resources, protected flights **must not be deprioritized** even if overall network load is high.

### Demo Talking Points

1. **"5 of 8 protected flights are on-time or delivered — 62% compliance"** — show the board the good news first
2. **"MSC-848 is our concern"** — 3 hours late, $429K at stake, SLA breach likely triggered
3. **"The Control Tower flags this automatically"** — ops managers don't need to memorize which flights are protected; the system surfaces violations in real time

### Recommended Actions (for demo narrative)

1. Notify customer ops contacts for MSC-848 cargo recipients
2. Check if MSC-831 (FRA → JFK, on-time) can accept re-routed cargo via connection
3. Document SLA breach for MSC-848 — initiate penalty calculation workflow
4. MSC-847 at +45min: monitor closely, no action yet (within buffer)

---

## Scenario 3: Sentiment Analysis Watch

> **The Story:** 5 specific flights are under intensive monitoring — "100 eyes on it" mode. The sentiment watch correlates operational performance with customer satisfaction impact.

### Watched Flights

| Flight | Route | Status | Delay | Shipments | VIP Cargo | Revenue |
|--------|-------|--------|-------|-----------|-----------|---------|
| **MSC-808** | **DOH → ORD** | **Delayed** | **+360min** | 3 | 2 VIP | $326K |
| **MSC-837** | **DXB → HKG** | **Delayed** | **+180min** | 0 | 0 | $0 |
| **MSC-814** | **PVG → LHR** | **Delayed** | **+45min** | 3 | 0 | $255K |
| MSC-819 | PVG → HKG | On-Time | 0 | 4 | 1 VIP | $481K |
| MSC-820 | ORD → LHR | On-Time | 0 | 3 | 2 VIP | $474K |

### Sentiment Correlation

The 5 watched flights show a **clear split** between good and bad performance:

- **3 flights delayed** (60%) — combined $581K revenue at risk
- **2 flights on-time** (40%) — combined $955K revenue flowing smoothly
- **MSC-808 is the worst case**: 6-hour delay with 2 VIP shipments ($326K)

### Why Sentiment Monitoring Matters

These flights were flagged because they carry cargo for customers who:
- Have recently expressed dissatisfaction (low sentiment scores)
- Are in contract renewal windows
- Have high strategic value beyond current revenue
- Represent "bellwether" accounts — their experience signals broader network health

### Demo Talking Points

1. **"3 out of 5 watched flights are delayed — that's a 60% failure rate on our most sensitive cargo"** — this is an early warning signal
2. **"MSC-808 and MSC-819 tell opposite stories"** — one is a crisis (6hr delay, VIP cargo), the other is smooth sailing (on-time, $481K delivered)
3. **"Correlating ops performance with customer sentiment gives us predictive power"** — we can see which accounts are about to churn before they tell us

### Recommended Actions (for demo narrative)

1. MSC-808: Same urgency as VIP Crisis — 2 VIP shipments on a 6-hour delayed flight
2. MSC-837: Low priority despite delay (no cargo currently manifested)
3. MSC-819 & MSC-820: Use as positive data points in customer QBRs — "your last 2 shipments arrived on time"
4. Overall: Flag the 60% delayed rate to network planning — sentiment-watched routes may need schedule buffer adjustments

---

## Demo Flow (Suggested)

### Opening (2 min)
> "This is the MSC Air Cargo Control Tower. It sits at the intersection of Operations and Commercial Revenue — showing us not just what's late, but what matters."

**Show:** Home page with KPIs — 10 delayed flights, $5.4M revenue on delayed flights, VIP alerts active.

### Scenario 1 — VIP Crisis (3 min)
> "Let's start with our highest-priority alert..."

**Show:** Priority Dashboard → VIP Crisis section. Click through to show flight MSC-807, customer EliteForward, $520K at risk.

**Key message:** "Traditional ops just sees 'flight is late.' We see '$520K for a Platinum customer whose satisfaction is already declining.'"

### Scenario 2 — Protected Schedule (2 min)
> "Now let's check our SLA-protected flights..."

**Show:** Priority Dashboard → Protected Schedule section. Highlight MSC-848 breach.

**Key message:** "Schedule protection is a contractual commitment. The system tells us exactly which flights cannot be delayed, before the penalty clock starts."

### Scenario 3 — Sentiment Watch (2 min)
> "Finally, our sentiment-monitored flights..."

**Show:** Priority Dashboard → Sentiment Watch. Compare MSC-808 (bad) vs MSC-819 (good).

**Key message:** "By watching specific flights tied to sensitive accounts, we get early warning of satisfaction issues before they become churn."

### AI Action Plan (1 min)
> "And here's where the AI comes in..."

**Show:** Click "Generate Action Plan" button. Claude produces prioritized recommendations.

**Key message:** "The AI synthesizes all three scenarios into a single action plan — what to do first, who to call, what to re-route."

### Ask Genie (2 min)
> "And if the ops manager wants to dig deeper..."

**Show:** Ask Genie tab. Ask "Which VIP customers have the most revenue at risk?" or "What is the average delay on protected flights?"

**Key message:** "Natural language SQL — no analyst needed. The ops manager asks questions in plain English, gets instant answers from the warehouse."

---

## Technical Notes

- All data is synthetic (generated with Faker + pandas)
- Data generation script: `dataset/generate_data.py`
- Demo scenarios are deterministically seeded (seed=42) — re-running produces identical data
- App reads from Databricks SQL Warehouse via REST API
- Genie Space requires separate setup (see `GENIE_SPACE_INSTRUCTIONS.md`)
