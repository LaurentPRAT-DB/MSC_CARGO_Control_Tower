"""
MSC Air Cargo Control Tower — Synthetic Data Generator

Generates 3 interconnected tables:
  1. msc_customers.csv (30 rows) — Customer tiers, sentiment, revenue
  2. msc_flights.csv (50 rows) — Flight schedules, delays, protection flags
  3. msc_shipments.csv (~150 rows) — AWBs with revenue, tracking, priority

Baked-in demo scenarios:
  - VIP Crisis: Delayed flight with high-revenue Doc Charter for a Platinum customer
  - Protected Schedule: Protected flight with strict ETA and critical revenue
  - 5 Watched Flights: Sentiment-flagged flights with mixed delay profiles
"""

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

OUTPUT_DIR = Path(__file__).parent

# --- Constants ---
CARGO_HUBS = ["FRA", "MXP", "HKG", "ORD", "DXB", "SIN", "JFK", "LHR", "PVG", "NRT", "ICN", "DOH"]
HUB_CITIES = {
    "FRA": "Frankfurt", "MXP": "Milan", "HKG": "Hong Kong", "ORD": "Chicago",
    "DXB": "Dubai", "SIN": "Singapore", "JFK": "New York", "LHR": "London",
    "PVG": "Shanghai", "NRT": "Tokyo", "ICN": "Seoul", "DOH": "Doha",
}
AIRCRAFT_TYPES = ["B747-400F", "B777F", "A330-200F", "B767-300F", "A350F"]
COMMODITY_TYPES = ["General Cargo", "Pharma", "Perishables", "Doc Charter / High-Yield", "Dangerous Goods", "Live Animals"]
TRACKING_STATUSES = ["Booked", "Manifested", "Uplifted", "Arrived", "Delivered"]
FLIGHT_STATUSES = ["On-Time", "Delayed", "In-Air", "Delivered"]
REGIONS = ["EMEA", "APAC", "Americas"]

LOGISTICS_COMPANIES = [
    "GlobalFreight Solutions", "TransOcean Logistics", "AirBridge Cargo Partners",
    "SwiftCargo International", "PharmaFly Express", "FreshChain Logistics",
    "EliteForward GmbH", "PacificAir Freight", "MedTrans Global",
    "CargoLink Asia", "AtlasForward Ltd", "NovaCargo SA",
    "PrimeShip Logistics", "VelocityAir Freight", "Continental Cargo Co",
    "SkyBridge Partners", "OceanAir Express", "AlpineFreight AG",
    "TropicCargo Ltd", "NorthStar Logistics", "EagleWing Transport",
    "SilkRoute Cargo", "PolarExpress Freight", "SummitAir Logistics",
    "BayFreight International", "CrossContinental Cargo", "HorizonAir Logistics",
    "MeridianFreight Corp", "ZenithCargo Solutions", "ApexAir Transport",
]


def generate_customers(n: int = 30) -> pd.DataFrame:
    tiers = (["Platinum/VIP"] * 6) + (["Gold"] * 9) + (["Standard"] * 15)
    random.shuffle(tiers)

    customers = []
    for i in range(n):
        tier = tiers[i]
        if tier == "Platinum/VIP":
            revenue = random.uniform(5_000_000, 15_000_000)
            sentiment = random.randint(6, 10)
        elif tier == "Gold":
            revenue = random.uniform(1_000_000, 5_000_000)
            sentiment = random.randint(4, 9)
        else:
            revenue = random.uniform(200_000, 1_000_000)
            sentiment = random.randint(2, 8)

        customers.append({
            "Customer_ID": f"CUST-{i+1:03d}",
            "Company_Name": LOGISTICS_COMPANIES[i],
            "Customer_Tier": tier,
            "Account_Sentiment_Score": sentiment,
            "Annual_Revenue_USD": round(revenue, 2),
            "Primary_Contact": fake.name(),
            "Region": random.choice(REGIONS),
        })

    return pd.DataFrame(customers)


def generate_flights(n: int = 50) -> pd.DataFrame:
    base_date = datetime(2025, 6, 1, 6, 0)
    flights = []

    for i in range(n):
        origin = random.choice(CARGO_HUBS)
        dest = random.choice([h for h in CARGO_HUBS if h != origin])

        departure = base_date + timedelta(hours=random.randint(0, 168), minutes=random.choice([0, 15, 30, 45]))
        flight_hours = random.uniform(3, 14)
        scheduled_arrival = departure + timedelta(hours=flight_hours)

        status = random.choices(FLIGHT_STATUSES, weights=[40, 25, 20, 15], k=1)[0]
        delay_minutes = 0
        if status == "Delayed":
            delay_minutes = random.choice([30, 45, 60, 90, 120, 180, 240, 360])
        elif status == "In-Air":
            delay_minutes = random.choice([0, 0, 0, 15, 30, 45])

        eta = scheduled_arrival + timedelta(minutes=delay_minutes)

        flights.append({
            "Flight_ID": f"MSC-{800 + i}",
            "Origin": origin,
            "Destination": dest,
            "Origin_City": HUB_CITIES[origin],
            "Destination_City": HUB_CITIES[dest],
            "Scheduled_Departure": departure.strftime("%Y-%m-%d %H:%M"),
            "Scheduled_Arrival": scheduled_arrival.strftime("%Y-%m-%d %H:%M"),
            "ETA": eta.strftime("%Y-%m-%d %H:%M"),
            "Flight_Status": status,
            "Delay_Minutes": delay_minutes,
            "Schedule_Protection_Flag": False,
            "Sentiment_Analysis_Flag": False,
            "Aircraft_Type": random.choice(AIRCRAFT_TYPES),
            "Capacity_Tons": round(random.uniform(80, 140), 1),
        })

    df = pd.DataFrame(flights)

    # 15% protected flights (7-8 flights)
    protected_indices = random.sample(range(n), 8)
    for idx in protected_indices:
        df.at[idx, "Schedule_Protection_Flag"] = True

    # Exactly 5 sentiment-watched flights (mix of delayed and on-time)
    delayed_indices = df[df["Flight_Status"] == "Delayed"].index.tolist()
    ontime_indices = df[df["Flight_Status"] == "On-Time"].index.tolist()
    sentiment_picks = random.sample(delayed_indices, min(3, len(delayed_indices))) + random.sample(ontime_indices, min(2, len(ontime_indices)))
    sentiment_picks = sentiment_picks[:5]
    for idx in sentiment_picks:
        df.at[idx, "Sentiment_Analysis_Flag"] = True

    return df


def generate_shipments(customers_df: pd.DataFrame, flights_df: pd.DataFrame, target: int = 150) -> pd.DataFrame:
    shipments = []
    customer_ids = customers_df["Customer_ID"].tolist()
    flight_ids = flights_df["Flight_ID"].tolist()
    vip_ids = customers_df[customers_df["Customer_Tier"] == "Platinum/VIP"]["Customer_ID"].tolist()

    for i in range(target):
        flight_id = random.choice(flight_ids)
        flight_row = flights_df[flights_df["Flight_ID"] == flight_id].iloc[0]

        # VIP customers get more shipments
        if random.random() < 0.3:
            customer_id = random.choice(vip_ids)
        else:
            customer_id = random.choice(customer_ids)

        customer_row = customers_df[customers_df["Customer_ID"] == customer_id].iloc[0]
        tier = customer_row["Customer_Tier"]

        commodity = random.choices(
            COMMODITY_TYPES,
            weights=[35, 20, 15, 10, 12, 8],
            k=1,
        )[0]

        # Revenue scaling: VIP + Doc Charter = highest
        base_revenue = random.uniform(5_000, 50_000)
        if tier == "Platinum/VIP":
            base_revenue *= random.uniform(3, 8)
        elif tier == "Gold":
            base_revenue *= random.uniform(1.5, 3)
        if commodity == "Doc Charter / High-Yield":
            base_revenue *= random.uniform(4, 10)
        elif commodity == "Pharma":
            base_revenue *= random.uniform(2, 4)

        revenue = round(base_revenue, 2)
        critical = revenue > 100_000 or (tier == "Platinum/VIP" and commodity in ["Doc Charter / High-Yield", "Pharma"])

        if critical:
            priority = "Critical"
        elif tier in ["Platinum/VIP", "Gold"]:
            priority = "Priority"
        else:
            priority = "Standard"

        # Tracking status correlates with flight status
        flight_status = flight_row["Flight_Status"]
        if flight_status == "Delivered":
            tracking = random.choice(["Arrived", "Delivered"])
        elif flight_status == "In-Air":
            tracking = random.choice(["Uplifted", "Manifested"])
        elif flight_status == "Delayed":
            tracking = random.choice(["Booked", "Manifested", "Uplifted"])
        else:
            tracking = random.choice(TRACKING_STATUSES)

        shipments.append({
            "AWB_Number": f"618-{random.randint(10000000, 99999999)}",
            "Flight_ID": flight_id,
            "Customer_ID": customer_id,
            "Commodity_Type": commodity,
            "Revenue_Generated_USD": revenue,
            "Weight_KG": round(random.uniform(50, 5000), 1),
            "Tracking_Status": tracking,
            "Critical_Revenue_Flag": critical,
            "Priority_Level": priority,
            "Origin_City": flight_row["Origin_City"],
            "Destination_City": flight_row["Destination_City"],
        })

    return pd.DataFrame(shipments)


def bake_demo_scenarios(customers_df: pd.DataFrame, flights_df: pd.DataFrame, shipments_df: pd.DataFrame):
    """Ensure the 3 key demo scenarios exist in the data."""

    # Scenario 1: VIP Crisis — delayed flight with Doc Charter for Platinum customer
    vip_customer = customers_df[customers_df["Customer_Tier"] == "Platinum/VIP"].iloc[0]
    delayed_flights = flights_df[flights_df["Flight_Status"] == "Delayed"]
    if len(delayed_flights) > 0:
        crisis_flight = delayed_flights.iloc[0]
        crisis_flight_id = crisis_flight["Flight_ID"]

        # Ensure a high-revenue Doc Charter shipment on this flight for this VIP
        crisis_idx = len(shipments_df)
        crisis_shipment = {
            "AWB_Number": "618-99000001",
            "Flight_ID": crisis_flight_id,
            "Customer_ID": vip_customer["Customer_ID"],
            "Commodity_Type": "Doc Charter / High-Yield",
            "Revenue_Generated_USD": 520_000.00,
            "Weight_KG": 2800.0,
            "Tracking_Status": "Manifested",
            "Critical_Revenue_Flag": True,
            "Priority_Level": "Critical",
            "Origin_City": crisis_flight["Origin_City"],
            "Destination_City": crisis_flight["Destination_City"],
        }
        shipments_df = pd.concat([shipments_df, pd.DataFrame([crisis_shipment])], ignore_index=True)

        # Ensure flight has significant delay
        flight_idx = flights_df[flights_df["Flight_ID"] == crisis_flight_id].index[0]
        flights_df.at[flight_idx, "Delay_Minutes"] = 360
        flights_df.at[flight_idx, "Flight_Status"] = "Delayed"

    # Scenario 2: Protected Schedule — protected flight with strict ETA and high revenue
    protected_flights = flights_df[flights_df["Schedule_Protection_Flag"] == True]
    if len(protected_flights) > 0:
        protected_flight = protected_flights.iloc[0]
        protected_flight_id = protected_flight["Flight_ID"]

        # Add a high-value pharma shipment
        protected_shipment = {
            "AWB_Number": "618-99000002",
            "Flight_ID": protected_flight_id,
            "Customer_ID": customers_df[customers_df["Customer_Tier"] == "Gold"].iloc[0]["Customer_ID"],
            "Commodity_Type": "Pharma",
            "Revenue_Generated_USD": 380_000.00,
            "Weight_KG": 1500.0,
            "Tracking_Status": "Uplifted",
            "Critical_Revenue_Flag": True,
            "Priority_Level": "Critical",
            "Origin_City": protected_flight["Origin_City"],
            "Destination_City": protected_flight["Destination_City"],
        }
        shipments_df = pd.concat([shipments_df, pd.DataFrame([protected_shipment])], ignore_index=True)

    # Scenario 3: 5 Watched Flights — already handled in generate_flights
    # Verify we have exactly 5
    watched_count = flights_df["Sentiment_Analysis_Flag"].sum()
    if watched_count < 5:
        remaining = 5 - watched_count
        available = flights_df[flights_df["Sentiment_Analysis_Flag"] == False].index.tolist()
        for idx in random.sample(available, min(remaining, len(available))):
            flights_df.at[idx, "Sentiment_Analysis_Flag"] = True

    return customers_df, flights_df, shipments_df


def main():
    print("Generating MSC Air Cargo Control Tower synthetic data...")

    customers_df = generate_customers(30)
    flights_df = generate_flights(50)
    shipments_df = generate_shipments(customers_df, flights_df, 150)

    customers_df, flights_df, shipments_df = bake_demo_scenarios(customers_df, flights_df, shipments_df)

    # Save CSVs
    customers_df.to_csv(OUTPUT_DIR / "msc_customers.csv", index=False)
    flights_df.to_csv(OUTPUT_DIR / "msc_flights.csv", index=False)
    shipments_df.to_csv(OUTPUT_DIR / "msc_shipments.csv", index=False)

    print(f"  msc_customers.csv: {len(customers_df)} rows")
    print(f"  msc_flights.csv:   {len(flights_df)} rows")
    print(f"  msc_shipments.csv: {len(shipments_df)} rows")

    # Verify demo scenarios
    print("\nDemo Scenario Verification:")
    vip_crisis = shipments_df[shipments_df["AWB_Number"] == "618-99000001"]
    if len(vip_crisis) > 0:
        row = vip_crisis.iloc[0]
        flight = flights_df[flights_df["Flight_ID"] == row["Flight_ID"]].iloc[0]
        cust = customers_df[customers_df["Customer_ID"] == row["Customer_ID"]].iloc[0]
        print(f"  VIP Crisis: Flight {row['Flight_ID']} ({flight['Flight_Status']}, +{flight['Delay_Minutes']}min)")
        print(f"    Customer: {cust['Company_Name']} ({cust['Customer_Tier']})")
        print(f"    Revenue at risk: ${row['Revenue_Generated_USD']:,.0f}")

    protected = flights_df[flights_df["Schedule_Protection_Flag"] == True]
    print(f"  Protected Flights: {len(protected)} flights flagged")

    watched = flights_df[flights_df["Sentiment_Analysis_Flag"] == True]
    print(f"  Sentiment Watch: {len(watched)} flights monitored")
    for _, f in watched.iterrows():
        print(f"    {f['Flight_ID']}: {f['Flight_Status']} (delay: {f['Delay_Minutes']}min)")

    print("\nDone!")


if __name__ == "__main__":
    main()
