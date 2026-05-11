-- MSC Air Cargo Control Tower — Table Creation DDL
-- Run in a Databricks SQL notebook.
-- Assumes CSVs are uploaded to a Unity Catalog volume at:
--   /Volumes/<catalog>/msc_air_cargo/raw/

CREATE SCHEMA IF NOT EXISTS msc_air_cargo;

CREATE OR REPLACE TABLE msc_air_cargo.msc_customers
  USING CSV OPTIONS (header 'true', inferSchema 'true')
  LOCATION '/Volumes/<catalog>/msc_air_cargo/raw/msc_customers.csv';

CREATE OR REPLACE TABLE msc_air_cargo.msc_flights
  USING CSV OPTIONS (header 'true', inferSchema 'true')
  LOCATION '/Volumes/<catalog>/msc_air_cargo/raw/msc_flights.csv';

CREATE OR REPLACE TABLE msc_air_cargo.msc_shipments
  USING CSV OPTIONS (header 'true', inferSchema 'true')
  LOCATION '/Volumes/<catalog>/msc_air_cargo/raw/msc_shipments.csv';

-- Verify row counts
SELECT 'msc_customers' AS tbl, COUNT(*) AS rows FROM msc_air_cargo.msc_customers
UNION ALL SELECT 'msc_flights', COUNT(*) FROM msc_air_cargo.msc_flights
UNION ALL SELECT 'msc_shipments', COUNT(*) FROM msc_air_cargo.msc_shipments;
