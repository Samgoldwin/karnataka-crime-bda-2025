import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = ROOT / "crime_karnataka_2025_csv"
DB_PATH = ROOT / "crime_analytics.db"

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

cur.executescript("""
DROP TABLE IF EXISTS crime_district_trends;
DROP TABLE IF EXISTS district_master_2025;
DROP TABLE IF EXISTS state_trend_2011_2025;
DROP TABLE IF EXISTS ipc_crime_heads_trend;
DROP TABLE IF EXISTS sll_crime_heads_trend;
DROP TABLE IF EXISTS violent_crime_heads_by_district_2025;
DROP TABLE IF EXISTS property_stolen_recovered_district_2023_2025;
DROP TABLE IF EXISTS property_by_nature_2025;
DROP TABLE IF EXISTS missing_children_district_2025;
DROP TABLE IF EXISTS missing_persons_district_2025;
DROP TABLE IF EXISTS recidivism_ipc_district_2025;
DROP TABLE IF EXISTS recidivism_sll_district_2025;

CREATE TABLE crime_district_trends (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  domain TEXT NOT NULL,
  table_id TEXT NOT NULL,
  district TEXT NOT NULL,
  year INTEGER NOT NULL,
  cases INTEGER DEFAULT 0,
  population_lakhs_2025 REAL DEFAULT 0.0,
  rate_2025 REAL DEFAULT 0.0,
  chargesheeting_rate_2025 REAL DEFAULT 0.0,
  UNIQUE(domain, table_id, district, year)
);

CREATE TABLE district_master_2025 (
  district TEXT PRIMARY KEY,
  ipc_bns_cases_2025 INTEGER,
  ipc_bns_occurrence_rate_2025 REAL,
  sll_cases_2025 INTEGER,
  sll_occurrence_rate_2025 REAL,
  total_cognizable_cases_2025 INTEGER,
  population_lakhs_2025 REAL,
  total_crime_rate_2025 REAL,
  total_chargesheeting_rate_2025 REAL,
  conviction_rate_ipc_bns_pct_2025 REAL,
  chargesheet_submission_pct_ipc_bns_2025 REAL,
  court_pendency_pct_ipc_bns_2025 REAL
);

CREATE TABLE state_trend_2011_2025 (
  year INTEGER PRIMARY KEY,
  population_lakhs REAL,
  ipc_bns_cases INTEGER,
  sll_cases INTEGER,
  total_cases INTEGER,
  ipc_bns_rate REAL,
  sll_rate REAL,
  total_rate REAL,
  ipc_share_of_total_pct REAL
);

CREATE TABLE ipc_crime_heads_trend (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  crime_head TEXT NOT NULL,
  cases_2023 INTEGER,
  rate_2023 REAL,
  cases_2024 INTEGER,
  rate_2024 REAL,
  cases_2025 INTEGER,
  rate_2025 REAL,
  pct_share_of_ipc_2025 REAL
);

CREATE TABLE sll_crime_heads_trend (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  crime_head TEXT NOT NULL,
  cases_2023 INTEGER,
  rate_2023 REAL,
  cases_2024 INTEGER,
  rate_2024 REAL,
  cases_2025 INTEGER,
  rate_2025 REAL,
  pct_share_of_sll_2025 REAL
);

CREATE TABLE violent_crime_heads_by_district_2025 (
  district TEXT PRIMARY KEY,
  murder_bns302 INTEGER,
  culpable_homicide_bns304 INTEGER,
  infanticide_bns315 INTEGER,
  foeticide_bns316 INTEGER,
  dowry_deaths_bns304b INTEGER,
  attempt_murder_bns307 INTEGER,
  attempt_culpable_homicide_bns308 INTEGER,
  grievous_hurt_bns325_326 INTEGER,
  attempt_rape INTEGER,
  rape INTEGER,
  kidnapping_abduction INTEGER,
  rioting INTEGER,
  robbery INTEGER,
  dacoity INTEGER,
  arson INTEGER,
  total_violent_crimes INTEGER
);

CREATE TABLE property_stolen_recovered_district_2023_2025 (
  district TEXT PRIMARY KEY,
  stolen_2023_cr REAL,
  recovered_2023_cr REAL,
  recovery_pct_2023 REAL,
  stolen_2024_cr REAL,
  recovered_2024_cr REAL,
  recovery_pct_2024 REAL,
  stolen_2025_cr REAL,
  recovered_2025_cr REAL,
  recovery_pct_2025 REAL
);

CREATE TABLE property_by_nature_2025 (
  nature_of_property TEXT PRIMARY KEY,
  cases_stolen_2025 INTEGER,
  pct_share_of_total_cases_stolen REAL,
  cases_recovered_2025 INTEGER,
  detection_pct REAL,
  value_stolen_cr_2025 REAL,
  pct_share_of_total_value_stolen REAL,
  value_recovered_cr_2025 REAL,
  recovery_pct REAL
);

CREATE TABLE missing_children_district_2025 (
  district TEXT PRIMARY KEY,
  prev_years_unrecovered_boys INTEGER,
  prev_years_unrecovered_girls INTEGER,
  prev_years_unrecovered_trans INTEGER,
  prev_years_unrecovered_total INTEGER,
  missing_2025_boys INTEGER,
  missing_2025_girls INTEGER,
  missing_2025_trans INTEGER,
  missing_2025_total INTEGER,
  total_boys INTEGER,
  total_girls INTEGER,
  total_trans INTEGER,
  grand_total INTEGER
);

CREATE TABLE missing_persons_district_2025 (
  district TEXT PRIMARY KEY,
  prev_years_unrecovered_males INTEGER,
  prev_years_unrecovered_females INTEGER,
  prev_years_unrecovered_total INTEGER,
  missing_2025_males INTEGER,
  missing_2025_females INTEGER,
  missing_2025_total INTEGER,
  total_persons_males INTEGER,
  total_persons_females INTEGER,
  grand_total INTEGER
);

CREATE TABLE recidivism_ipc_district_2025 (
  district TEXT PRIMARY KEY,
  persons_arrested INTEGER,
  juveniles_apprehended_convicted_past INTEGER,
  juveniles_apprehended_not_convicted_past INTEGER,
  juveniles_arrested_first_time_not_convicted INTEGER,
  adults_arrested_not_convicted_past INTEGER,
  adults_arrested_convicted_past INTEGER,
  adults_arrested_first_time_not_convicted INTEGER,
  recidivism_pct REAL
);

CREATE TABLE recidivism_sll_district_2025 (
  district TEXT PRIMARY KEY,
  persons_arrested INTEGER,
  juveniles_apprehended_convicted_past INTEGER,
  juveniles_apprehended_not_convicted_past INTEGER,
  juveniles_arrested_first_time_not_convicted INTEGER,
  adults_arrested_not_convicted_past INTEGER,
  adults_arrested_convicted_past INTEGER,
  adults_arrested_first_time_not_convicted INTEGER,
  recidivism_pct REAL
);
""")
con.commit()

def load_csv(name, table):
    fp = CSV_DIR / name
    if not fp.exists():
        print(f"Missing {fp}")
        return
    df = pd.read_csv(fp, encoding="utf-8-sig")
    df.to_sql(table, con, if_exists="append", index=False, chunksize=5000)
    print(f"Loaded {name} -> {table}: {len(df)} rows")

load_csv("master_district_trends_long.csv", "crime_district_trends")
load_csv("district_master_2025.csv", "district_master_2025")
load_csv("state_trend_2011_2025.csv", "state_trend_2011_2025")
load_csv("ipc_crime_heads_trend.csv", "ipc_crime_heads_trend")
load_csv("sll_crime_heads_trend.csv", "sll_crime_heads_trend")
load_csv("violent_crime_heads_by_district_2025.csv", "violent_crime_heads_by_district_2025")
load_csv("property_stolen_recovered_district_2023_2025.csv", "property_stolen_recovered_district_2023_2025")
load_csv("property_by_nature_2025.csv", "property_by_nature_2025")
load_csv("missing_children_district_2025.csv", "missing_children_district_2025")
load_csv("missing_persons_district_2025.csv", "missing_persons_district_2025")
load_csv("recidivism_ipc_district_2025.csv", "recidivism_ipc_district_2025")
load_csv("recidivism_sll_district_2025.csv", "recidivism_sll_district_2025")

con.close()
print(f"DB created: {DB_PATH}")
