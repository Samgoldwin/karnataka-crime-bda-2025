#!/bin/bash
# Upload extracted CSVs to HDFS
hdfs dfs -mkdir -p /crime/raw
hdfs dfs -mkdir -p /crime/processed
hdfs dfs -put ../crime_karnataka_2025_csv/master_district_trends_long.csv /crime/raw/
hdfs dfs -put ../crime_karnataka_2025_csv/district_master_2025.csv /crime/raw/
hdfs dfs -put ../crime_karnataka_2025_csv/state_trend_2011_2025.csv /crime/raw/
hdfs dfs -put ../crime_karnataka_2025_csv/ipc_crime_heads_trend.csv /crime/raw/
hdfs dfs -put ../crime_karnataka_2025_csv/sll_crime_heads_trend.csv /crime/raw/
hdfs dfs -put ../crime_karnataka_2025_csv/violent_crime_heads_by_district_2025.csv /crime/raw/
hdfs dfs -put ../crime_karnataka_2025_csv/property_stolen_recovered_district_2023_2025.csv /crime/raw/
hdfs dfs -put ../crime_karnataka_2025_csv/property_by_nature_2025.csv /crime/raw/
hdfs dfs -put ../crime_karnataka_2025_csv/missing_children_district_2025.csv /crime/raw/
hdfs dfs -put ../crime_karnataka_2025_csv/missing_persons_district_2025.csv /crime/raw/
hdfs dfs -put ../crime_karnataka_2025_csv/recidivism_ipc_district_2025.csv /crime/raw/
hdfs dfs -put ../crime_karnataka_2025_csv/recidivism_sll_district_2025.csv /crime/raw/
for f in ../crime_karnataka_2025_csv/district_trend_*.csv; do
  hdfs dfs -put "$f" /crime/raw/
done
echo "HDFS upload complete."
