# Genie Space Setup — MSC Air Cargo Control Tower

## Tables to Include

Add these 3 tables to the Genie Space:

1. **msc_customers** — Customer master data with tier classification and revenue
2. **msc_flights** — Flight schedule, status, delays, and monitoring flags
3. **msc_shipments** — Air Waybill (AWB) records linking flights to customers with revenue

## Table Descriptions (paste into Genie Space config)

### msc_customers
Customer accounts for MSC Air Cargo. Each customer has a tier (Platinum/VIP, Gold, Standard) based on revenue. The Account_Sentiment_Score (1-10) reflects recent interaction quality. Platinum/VIP customers are the highest-value accounts generating $5M+ annually.

### msc_flights
Flight operations data. Each row is a cargo flight between major hubs. Key flags:
- Schedule_Protection_Flag: flights that must not be delayed (contractual obligation)
- Sentiment_Analysis_Flag: flights under intensive monitoring (exactly 5 at any time)
- Delay_Minutes: 0 for on-time, positive values indicate delay severity

### msc_shipments
Individual shipments (Air Waybills) on flights. Links to both customers and flights. Key fields:
- Commodity_Type: "Doc Charter / High-Yield" is the most lucrative cargo type
- Critical_Revenue_Flag: shipments representing significant revenue at risk
- Priority_Level: Critical > Priority > Standard

## Sample Questions

- Which VIP customers have cargo on delayed flights?
- What is the total revenue at risk from delayed flights?
- Show me all protected flights and their current status
- Which flights are under sentiment analysis monitoring?
- What is the on-time rate by origin hub?
- Show Doc Charter shipments sorted by revenue
- Which customer has the most critical shipments?
- What is the average delay for flights out of FRA?
- List all shipments for customer CUST-001
- Show revenue breakdown by commodity type

## Column Semantics

| Column | Meaning |
|--------|---------|
| Customer_Tier | Platinum/VIP = top 20%, Gold = next 30%, Standard = remaining |
| Schedule_Protection_Flag | True = flight must not be delayed, contractual SLA |
| Sentiment_Analysis_Flag | True = flight under intensive ops monitoring |
| Doc Charter / High-Yield | Premium document courier service, highest revenue per kg |
| Critical_Revenue_Flag | True = shipment revenue > $100K or VIP + premium commodity |
| Delay_Minutes | 0 = on-time; 30-360 = operational delay severity |
