CREATE DATABASE IF NOT EXISTS crime_analytics;
USE crime_analytics;

CREATE TABLE IF NOT EXISTS crime_district_trends (
  id INT AUTO_INCREMENT PRIMARY KEY,
  domain VARCHAR(60) NOT NULL,
  table_id VARCHAR(10) NOT NULL,
  district VARCHAR(80) NOT NULL,
  year INT NOT NULL,
  cases INT DEFAULT 0,
  population_lakhs DECIMAL(10,3) DEFAULT 0.000,
  crime_rate DECIMAL(10,3) DEFAULT 0.000,
  chargesheeting_rate DECIMAL(10,3) DEFAULT 0.000,
  INDEX idx_district_year (district, year),
  INDEX idx_domain_year (domain, year),
  INDEX idx_year (year),
  UNIQUE KEY uq_trend (domain, table_id, district, year)
);

CREATE TABLE IF NOT EXISTS district_master_2025 (
  district VARCHAR(80) PRIMARY KEY,
  ipc_bns_cases_2025 INT,
  ipc_bns_occurrence_rate_2025 DECIMAL(10,3),
  sll_cases_2025 INT,
  sll_occurrence_rate_2025 DECIMAL(10,3),
  total_cognizable_cases_2025 INT,
  population_lakhs_2025 DECIMAL(10,3),
  total_crime_rate_2025 DECIMAL(10,3),
  total_chargesheeting_rate_2025 DECIMAL(10,3),
  conviction_rate_ipc_bns_pct_2025 DECIMAL(10,3),
  chargesheet_submission_pct_ipc_bns_2025 DECIMAL(10,3),
  court_pendency_pct_ipc_bns_2025 DECIMAL(10,3)
);

CREATE TABLE IF NOT EXISTS state_trend_2011_2025 (
  year INT PRIMARY KEY,
  population_lakhs DECIMAL(10,3),
  ipc_bns_cases INT,
  sll_cases INT,
  total_cases INT,
  ipc_bns_rate DECIMAL(10,3),
  sll_rate DECIMAL(10,3),
  total_rate DECIMAL(10,3),
  ipc_share_of_total_pct DECIMAL(10,3)
);

CREATE TABLE IF NOT EXISTS ipc_crime_heads_trend (
  id INT AUTO_INCREMENT PRIMARY KEY,
  crime_head VARCHAR(200) NOT NULL,
  cases_2023 INT,
  rate_2023 DECIMAL(10,3),
  cases_2024 INT,
  rate_2024 DECIMAL(10,3),
  cases_2025 INT,
  rate_2025 DECIMAL(10,3),
  pct_share_of_ipc_2025 DECIMAL(10,3),
  INDEX idx_crime_head (crime_head(100))
);

CREATE TABLE IF NOT EXISTS sll_crime_heads_trend (
  id INT AUTO_INCREMENT PRIMARY KEY,
  crime_head VARCHAR(200) NOT NULL,
  cases_2023 INT,
  rate_2023 DECIMAL(10,3),
  cases_2024 INT,
  rate_2024 DECIMAL(10,3),
  cases_2025 INT,
  rate_2025 DECIMAL(10,3),
  pct_share_of_sll_2025 DECIMAL(10,3),
  INDEX idx_crime_head (crime_head(100))
);

CREATE TABLE IF NOT EXISTS violent_crime_heads_by_district_2025 (
  district VARCHAR(80) NOT NULL,
  murder_bns302 INT,
  culpable_homicide_bns304 INT,
  infanticide_bns315 INT,
  foeticide_bns316 INT,
  dowry_deaths_bns304b INT,
  attempt_murder_bns307 INT,
  attempt_culpable_homicide_bns308 INT,
  grievous_hurt_bns325_326 INT,
  attempt_rape INT,
  rape INT,
  kidnapping_abduction INT,
  rioting INT,
  robbery INT,
  dacoity INT,
  arson INT,
  total_violent_crimes INT,
  PRIMARY KEY (district)
);

CREATE TABLE IF NOT EXISTS property_stolen_recovered_district_2023_2025 (
  district VARCHAR(80) NOT NULL,
  stolen_2023_cr DECIMAL(12,3),
  recovered_2023_cr DECIMAL(12,3),
  recovery_pct_2023 DECIMAL(10,3),
  stolen_2024_cr DECIMAL(12,3),
  recovered_2024_cr DECIMAL(12,3),
  recovery_pct_2024 DECIMAL(10,3),
  stolen_2025_cr DECIMAL(12,3),
  recovered_2025_cr DECIMAL(12,3),
  recovery_pct_2025 DECIMAL(10,3),
  PRIMARY KEY (district)
);

CREATE TABLE IF NOT EXISTS property_by_nature_2025 (
  nature_of_property VARCHAR(120) PRIMARY KEY,
  cases_stolen_2025 INT,
  pct_share_of_total_cases_stolen DECIMAL(10,3),
  cases_recovered_2025 INT,
  detection_pct DECIMAL(10,3),
  value_stolen_cr_2025 DECIMAL(12,3),
  pct_share_of_total_value_stolen DECIMAL(10,3),
  value_recovered_cr_2025 DECIMAL(12,3),
  recovery_pct DECIMAL(10,3)
);

CREATE TABLE IF NOT EXISTS missing_children_district_2025 (
  district VARCHAR(80) PRIMARY KEY,
  prev_years_unrecovered_boys INT,
  prev_years_unrecovered_girls INT,
  prev_years_unrecovered_trans INT,
  prev_years_unrecovered_total INT,
  missing_2025_boys INT,
  missing_2025_girls INT,
  missing_2025_trans INT,
  missing_2025_total INT,
  total_boys INT,
  total_girls INT,
  total_trans INT,
  grand_total INT
);

CREATE TABLE IF NOT EXISTS missing_persons_district_2025 (
  district VARCHAR(80) PRIMARY KEY,
  prev_years_unrecovered_males INT,
  prev_years_unrecovered_females INT,
  prev_years_unrecovered_total INT,
  missing_2025_males INT,
  missing_2025_females INT,
  missing_2025_total INT,
  total_persons_males INT,
  total_persons_females INT,
  grand_total INT
);

CREATE TABLE IF NOT EXISTS recidivism_ipc_district_2025 (
  district VARCHAR(80) PRIMARY KEY,
  persons_arrested INT,
  juveniles_apprehended_convicted_past INT,
  juveniles_apprehended_not_convicted_past INT,
  juveniles_arrested_first_time_not_convicted INT,
  adults_arrested_not_convicted_past INT,
  adults_arrested_convicted_past INT,
  adults_arrested_first_time_not_convicted INT,
  recidivism_pct DECIMAL(10,3)
);

CREATE TABLE IF NOT EXISTS recidivism_sll_district_2025 (
  district VARCHAR(80) PRIMARY KEY,
  persons_arrested INT,
  juveniles_apprehended_convicted_past INT,
  juveniles_apprehended_not_convicted_past INT,
  juveniles_arrested_first_time_not_convicted INT,
  adults_arrested_not_convicted_past INT,
  adults_arrested_convicted_past INT,
  adults_arrested_first_time_not_convicted INT,
  recidivism_pct DECIMAL(10,3)
);
